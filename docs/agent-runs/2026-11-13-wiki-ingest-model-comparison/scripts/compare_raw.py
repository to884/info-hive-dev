# -*- coding: utf-8 -*-
"""raw のファイルを、モデルが手を入れる前の取得（基準）と突き合わせる。

使い方: python compare_raw.py <基準の raw/xxx.md> <実行の raw/yyy.md> [--json]
"""
import difflib
import json
import re
import sys
from pathlib import Path

FENCE = re.compile(r"^(```|~~~)")
URL_RE = re.compile(r"\]\(([^)\s]+)")
CAPTION_RE = re.compile(r"^>\s*(.*?)\s*補足[:：]\s*(.*)$")
IMG_RE = re.compile(r"^!\[[^\]]*\]\(([^)\s]+)")
KANA_KANJI = re.compile(r"[぀-ヿ一-鿿]")
ASCII_WORD = re.compile(r"[A-Za-z]{3,}")
INLINE_CODE = re.compile(r"`[^`]*`")
LINK_TARGET = re.compile(r"\]\([^)]*\)")
MATH = re.compile(r"\$[^$]*\$")


def read(path):
    text = Path(path).read_bytes().decode("utf-8")
    return text.replace("\r\n", "\n")


def split_frontmatter(text):
    if text.startswith("---\n"):
        end = text.index("\n---\n", 4)
        fm_text = text[4:end]
        body = text[end + 5:]
    else:
        fm_text, body = "", text
    fm = {}
    for line in fm_text.splitlines():
        m = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"')
    return fm, body


def blocks(body):
    """本文を種類つきのブロックに分ける。"""
    out = []
    lines = body.split("\n")
    i = 0
    buf = []

    def flush():
        if buf:
            txt = "\n".join(buf).strip()
            if txt:
                first = buf[0].lstrip()
                if first.startswith("|"):
                    kind = "table"
                elif first.startswith(">"):
                    kind = "caption" if CAPTION_RE.match(first) else "quote"
                elif re.match(r"^([-*+]|\d+\.)\s", first):
                    kind = "list"
                else:
                    kind = "para"
                out.append((kind, txt))
            buf.clear()

    while i < len(lines):
        line = lines[i]
        if FENCE.match(line.lstrip()):
            flush()
            fence = line.lstrip()[:3]
            code = [line]
            i += 1
            while i < len(lines) and not lines[i].lstrip().startswith(fence):
                code.append(lines[i])
                i += 1
            if i < len(lines):
                code.append(lines[i])
            out.append(("code", "\n".join(code)))
            i += 1
            continue
        if re.match(r"^#{1,6}\s", line):
            flush()
            out.append(("heading", line))
        elif IMG_RE.match(line.strip()):
            flush()
            out.append(("image", line.strip()))
        elif line.strip() == "":
            flush()
        else:
            # 引用と通常の段落の切り替わりで区切る
            if buf and (buf[0].lstrip().startswith(">") != line.lstrip().startswith(">")):
                flush()
            buf.append(line)
        i += 1
    flush()
    return out


def prose(text):
    """訳の比率を見るための地の文（コード、リンク先、数式を除く）。"""
    t = INLINE_CODE.sub(" ", text)
    t = LINK_TARGET.sub("]", t)
    t = MATH.sub(" ", t)
    t = re.sub(r"https?://\S+", " ", t)
    return t


def unquote(txt):
    return "\n".join(re.sub(r"^>\s?", "", l) for l in txt.split("\n"))


def quoted_code(bl):
    """引用の中のフェンスつきコードを取り出す。"""
    out = []
    for kind, txt in bl:
        if kind != "quote":
            continue
        lines = unquote(txt).split("\n")
        i = 0
        while i < len(lines):
            if FENCE.match(lines[i].lstrip()):
                code = [lines[i]]
                i += 1
                while i < len(lines) and not FENCE.match(lines[i].lstrip()):
                    code.append(lines[i])
                    i += 1
                if i < len(lines):
                    code.append(lines[i])
                out.append("\n".join(code))
            i += 1
    return out


def table_shapes(bl):
    shapes = []
    for kind, txt in bl:
        if kind == "quote" and unquote(txt).lstrip().startswith("|"):
            kind, txt = "table", unquote(txt)
        if kind == "table":
            rows = [r for r in txt.split("\n") if r.strip().startswith("|")]
            cols = [r.count("|") - 1 for r in rows]
            shapes.append((len(rows), max(cols) if cols else 0))
    return shapes


def sections(bl):
    """見出しごとに、地の文のブロック（段落、リスト、引用、表）の数を数える。"""
    secs = [["(先頭)", 0]]
    for kind, txt in bl:
        if kind == "heading":
            secs.append([txt[:60], 0])
        elif kind in ("para", "list", "quote", "table"):
            # リストは項目の数で数える
            if kind == "list":
                secs[-1][1] += len([l for l in txt.split("\n") if re.match(r"^\s*([-*+]|\d+\.)\s", l)])
            else:
                secs[-1][1] += 1
    return secs


def analyze(base_path, run_path):
    b_fm, b_body = split_frontmatter(read(base_path))
    r_fm, r_body = split_frontmatter(read(run_path))
    bb, rb = blocks(b_body), blocks(r_body)

    res = {"base": str(base_path), "run": str(run_path)}
    # frontmatter
    fm_diff = {}
    for k in sorted(set(b_fm) | set(r_fm)):
        if k == "fetched_at":
            continue
        if b_fm.get(k) != r_fm.get(k):
            fm_diff[k] = [b_fm.get(k), r_fm.get(k)]
    res["frontmatter_diff"] = fm_diff
    res["translated_by"] = r_fm.get("translated_by")
    res["source_sha256_match"] = b_fm.get("source_sha256") == r_fm.get("source_sha256")

    # 見出し
    b_h = [len(t.split()[0]) for k, t in bb if k == "heading"]
    r_h = [len(t.split()[0]) for k, t in rb if k == "heading"]
    res["headings"] = {"base": len(b_h), "run": len(r_h), "levels_equal": b_h == r_h}

    # コード（引用の中のコードも、先頭の「> 」を外して数える）
    b_code = [t for k, t in bb if k == "code"] + quoted_code(bb)
    r_code = [t for k, t in rb if k == "code"] + quoted_code(rb)
    res["code_blocks"] = {
        "base": len(b_code),
        "run": len(r_code),
        "identical": sum(1 for c in b_code if c in r_code),
    }

    # URL
    b_urls, r_urls = set(URL_RE.findall(b_body)), set(URL_RE.findall(r_body))
    res["urls"] = {
        "base": len(b_urls),
        "run": len(r_urls),
        "missing": sorted(b_urls - r_urls),
        "added": sorted(r_urls - b_urls),
    }

    # 表
    res["tables"] = {"base": table_shapes(bb), "run": table_shapes(rb)}

    # 画像と補足
    b_img = [t for k, t in bb if k == "image"]
    r_img = [t for k, t in rb if k == "image"]
    caps = []
    for k, t in rb:
        if k == "caption":
            m = CAPTION_RE.match(t.split("\n")[0])
            body = " ".join(l.lstrip("> ").strip() for l in t.split("\n"))
            caps.append({"prefix": m.group(1) if m else None, "chars": len(body)})
    res["images"] = {
        "base": len(b_img),
        "run": len(r_img),
        "removed": [IMG_RE.match(t).group(1) for t in b_img if t not in r_img],
    }
    res["captions"] = caps
    asset_dir = Path(run_path).parent
    res["removed_assets_still_present"] = [
        p for p in res["images"]["removed"] if (asset_dir / p.split(" ")[0]).exists()
    ]

    # ブロックの数
    def count(bl, kinds):
        return sum(1 for k, _ in bl if k in kinds)

    res["blocks"] = {
        kind: [count(bb, {kind}), count(rb, {kind})]
        for kind in ("para", "list", "quote", "caption", "table", "code", "heading", "image")
    }
    b_sec, r_sec = sections(bb), sections(rb)
    res["sections_equal_count"] = len(b_sec) == len(r_sec)
    res["section_block_diff"] = [
        [bs[0], bs[1], rs[1]] for bs, rs in zip(b_sec, r_sec) if bs[1] != rs[1]
    ]

    # 地の文
    def prose_of(bl):
        return "\n".join(prose(t) for k, t in bl if k in ("para", "list", "quote", "table", "heading"))

    rp = prose_of(rb)
    letters = [c for c in rp if not c.isspace()]
    res["body_chars"] = {"base": len(b_body), "run": len(r_body)}
    res["run_prose_ja_ratio"] = round(len(KANA_KANJI.findall(rp)) / max(1, len(letters)), 3)
    res["run_prose_ascii_words"] = len(ASCII_WORD.findall(rp))

    # 行の差分（削除と追加）
    sm = difflib.SequenceMatcher(None, b_body.split("\n"), r_body.split("\n"), autojunk=False)
    removed, added = [], []
    bl_, rl_ = b_body.split("\n"), r_body.split("\n")
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("delete", "replace"):
            removed += [l for l in bl_[i1:i2] if l.strip()]
        if tag in ("insert", "replace"):
            added += [l for l in rl_[j1:j2] if l.strip()]
    res["line_diff"] = {"removed": len(removed), "added": len(added)}
    res["removed_lines"] = removed
    res["added_lines"] = added
    return res


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    res = analyze(args[0], args[1])
    if "--json" in sys.argv:
        sys.stdout.buffer.write(json.dumps(res, ensure_ascii=False, indent=1).encode("utf-8"))
        return
    short = {k: v for k, v in res.items() if k not in ("removed_lines", "added_lines")}
    sys.stdout.buffer.write(json.dumps(short, ensure_ascii=False, indent=1).encode("utf-8"))


if __name__ == "__main__":
    main()
