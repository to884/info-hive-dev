"""PDFiumでページ上の文字オブジェクトを切り分け、丸印を独立に照合する。"""

from contextlib import closing
import ctypes
import hashlib
import io
import re

import numpy as np
from PIL import Image
from pypdf import PdfReader
import pypdfium2
import pypdfium2.raw as raw

POINT_CIDS = {638: 0x30FB, 668: 0x2026}
APPROVED = {0x30FB, 0x2022, 0x2026}


def sha(value):
    return hashlib.sha256(value).hexdigest()


def pointer(item):
    return ctypes.cast(item, ctypes.c_void_p).value


def font_name(obj):
    font = raw.FPDFTextObj_GetFont(obj)
    size = raw.FPDFFont_GetBaseFontName(font, None, 0)
    if not size or not raw.FPDFFont_GetIsEmbedded(font):
        raise ValueError("丸印の埋め込んだフォントを確認できない")
    name = ctypes.create_string_buffer(size)
    if raw.FPDFFont_GetBaseFontName(font, name, size) != size:
        raise ValueError("埋め込まれたフォントの名前が異なる")
    length = ctypes.c_size_t(0)
    if not raw.FPDFFont_GetFontData(font, None, 0, ctypes.byref(length)) or not length.value:
        raise ValueError("PDFiumが使用した埋め込みフォントを取得できない")
    data = (ctypes.c_ubyte * length.value)()
    if not raw.FPDFFont_GetFontData(font, data, length.value, ctypes.byref(length)) or length.value != len(data):
        raise ValueError("PDFiumが使用したフォントのデータが異なる")
    return name.value.decode("utf-8"), sha(bytes(data))


def embedded_map(bytestring):
    """明示フォントの16ビットのbfcharとbfrangeだけを読む。"""
    result = {}

    def remember(cid, pos):
        old = result.setdefault(cid, pos)
        if old != pos:
            raise ValueError("同じCIDに異なる符号が宣言されている")

    clean = re.sub(rb"%[^\r\n]*", b"", bytestring)
    for body in re.findall(rb"beginbfchar(.*?)endbfchar", clean, re.S):
        for a, value in re.findall(rb"<([a-f0-9]{4})>\s*<([a-f0-9]{4})>", body, re.I):
            remember(int(a, 16), int(value, 16))
    for body in re.findall(rb"beginbfrange(.*?)endbfrange", clean, re.S):
        pat = rb"<([a-f0-9]{4})>\s*<([a-f0-9]{4})>\s*(?:<([a-f0-9]{4})>|\[(.*?)\])"
        for a, b, starting, array in re.findall(pat, body, re.I | re.S):
            lower, upper = int(a, 16), int(b, 16)
            if not 0 <= lower <= upper <= 65535:
                raise ValueError("埋め込みToUnicodeの範囲が不明")
            if starting:
                first = int(starting, 16)
                for cid in range(lower, upper + 1):
                    remember(cid, first + cid - lower)
            elif array:
                values = re.findall(rb"<([a-f0-9]{4})>", array, re.I)
                if len(values) != upper - lower + 1:
                    continue
                for cid, value in enumerate(values, lower):
                    remember(cid, int(value, 16))
    return result


def resources(page, name, font_sha):
    records, seen = [], set()

    def visit(value, depth):
        if depth > 12 or id(value) in seen:
            return
        seen.add(id(value))
        dictionaries = value.get("/Font")
        if dictionaries is not None:
            for entry in dictionaries.get_object().values():
                font = entry.get_object()
                descendants = font.get("/DescendantFonts")
                if not descendants or font.get("/Encoding") != "/Identity-H" or "/ToUnicode" not in font:
                    continue
                descendant = descendants.get_object()[0].get_object()
                if str(descendant.get("/BaseFont")).lstrip("/") != name:
                    continue
                descriptor = descendant["/FontDescriptor"]
                streams = [descriptor[key].get_data() for key in ("/FontFile", "/FontFile2", "/FontFile3") if key in descriptor]
                if not any(sha(s) == font_sha for s in streams):
                    continue
                declaration = descendant["/CIDSystemInfo"]
                ros = str(declaration["/Registry"]), str(declaration["/Ordering"])
                stream = font["/ToUnicode"].get_data()
                records.append((ros, sha(stream), embedded_map(stream)))
        others = value.get("/XObject")
        if others is not None:
            for entry in others.get_object().values():
                nested = entry.get_object().get("/Resources")
                if nested is not None:
                    visit(nested.get_object(), depth + 1)

    visit(page["/Resources"], 0)
    return records


def glyph_cid(page, name, font_sha, code):
    maps = resources(page, name, font_sha)
    possibilities = {cid for _, _, mapping in maps for cid, val in mapping.items() if val == code}
    cid, = possibilities
    mapped = [(ros, digest, m[cid]) for ros, digest, m in maps if cid in m]
    if any((value != code or (ros == ("Adobe", "Japan1") and POINT_CIDS.get(cid, code) != code))
           for ros, _, value in mapped):
        raise ValueError("埋め込み符号とフォントの宣言に矛盾")
    return {"codepoint": f"{code:04X}", "cid": cid, "pdfium_font": name,
            "font_data_sha256": font_sha, "to_unicode_sha256": sorted({f for _, f, _ in mapped})}


def reproduce(page, fixed, area, objects):
    initial = []
    for item in objects:
        value = ctypes.c_long(0)
        if not raw.FPDFPageObj_GetIsActive(item, ctypes.byref(value)):
            raise ValueError("元の描画命令の表示状態が不明")
        if value.value:
            initial.append(item)

    def mask(group, active):
        for item in group:
            if not raw.FPDFPageObj_SetIsActive(item, active):
                raise ValueError("描画命令の切り分けに失敗")

    def visible():
        with closing(page.render(scale=150 / 72)) as bitmap:
            return np.array(bitmap.to_pil().convert("RGB"))[area]

    try:
        if not np.array_equal(visible(), fixed):
            raise ValueError("元の描画と固定した画素が異なる")
        mask(initial, False)
        blank = visible()
        if np.any(blank < 254):
            raise ValueError("同じ画素の位置に文字以外の描画がある")
        pending, owners = [initial], []
        while pending:
            group = pending.pop()
            mask(group, True)
            draw = visible()
            mask(group, False)
            if np.array_equal(draw, blank):
                continue
            if len(group) == 1:
                owners.extend(group)
            else:
                sep = len(group) // 2
                pending.extend((group[:sep], group[sep:]))
        if not owners:
            raise ValueError("点を描画するオブジェクトを確認できない")
        mask(owners, True)
        if not np.array_equal(visible(), fixed):
            raise ValueError("文字の描画だけで固定画素を再現できない")
        mask(owners, False)
        rest = [x for x in initial if x not in owners]
        mask(rest, True)
        if not np.array_equal(visible(), blank):
            raise ValueError("他の描画でも同じ位置にインクが残る")
        return owners
    finally:
        mask(initial, True)


def trace(pdf_bytes, page_number, rgb, bounds, flags):
    l, t, r, b = bounds
    area = np.s_[t - 1:b + 1, l - 1:r + 1]
    fixed = rgb[area]
    with closing(pypdfium2.PdfDocument(pdf_bytes)) as doc, closing(doc[page_number - 1]) as page:
        with closing(page.get_textpage()) as textpage:
            objects = list(page.get_objects(filter=[raw.FPDF_PAGEOBJ_TEXT], textpage=textpage))
            owners = reproduce(page, fixed, area, objects)
            by_font = {pointer(item.raw): font_name(item) for item in owners}
            origin, trans = np.asarray(flags["150_origin"]), np.asarray(flags["150_matrix"])
            tokens = set()
            for i in range(textpage.count_chars()):
                owner = pointer(raw.FPDFText_GetTextObject(textpage, i))
                if owner not in by_font or raw.FPDFText_IsGenerated(textpage, i):
                    continue
                x, y, a, c = textpage.get_charbox(i, loose=False)
                corners = np.array([trans @ (np.array(p) - origin) for p in ((x, y), (x, c), (a, y), (a, c))])
                if (corners[:, 0].min() < r and corners[:, 0].max() > l
                        and corners[:, 1].min() < b and corners[:, 1].max() > t):
                    code = raw.FPDFText_GetUnicode(textpage, i)
                    if code not in APPROVED:
                        raise ValueError("候補の丸印に許可対象外の符号が重なる")
                    cx, cy = ctypes.c_double(), ctypes.c_double()
                    if not raw.FPDFText_GetCharOrigin(textpage, i, ctypes.byref(cx), ctypes.byref(cy)):
                        raise ValueError("点を描いた文字の原点を確かめられない")
                    tokens.add((*by_font[owner], code, round(cx.value, 5), round(cy.value, 5)))
            (font, font_sha, code, _, _), = tokens
            modes = sorted(raw.FPDFTextObj_GetTextRenderMode(o) for o in owners)
            if modes not in ([0], [0, 1]):
                raise ValueError("同じ位置の文字を一つの塗りまたは塗りと輪郭に結び付けられない")
    pypdf_page = PdfReader(io.BytesIO(pdf_bytes)).pages[page_number - 1]
    proof = glyph_cid(pypdf_page, font, font_sha, code)
    return {"box": bounds, "modes": modes, "pixels_sha256": sha(fixed.tobytes()),
            "source_isolated": True, **proof}
