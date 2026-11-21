"""元PDFの一様な地色を残して、独立な丸印の描画だけを切り分ける。"""

from contextlib import closing
import ctypes
from pathlib import Path
import sys

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v19-reference-audit"))
import run as audit

source = audit.module("source_for_uniform_background", HERE.parent / "v19-reference-audit/source.py")
trace = source.proof


def background(plane):
    if plane.ndim != 3 or not plane.size or not np.all(plane == plane[0, 0]):
        raise ValueError("該当箇所の背景に同じ点を描ける別の形が残る")
    return tuple(map(int, plane[0, 0]))


def reproduce(page, fixed, area, objects):
    def toggle(group, active):
        for item in group:
            if not trace.raw.FPDFPageObj_SetIsActive(item, active):
                raise ValueError("元の描画を切り分けられない")

    def render():
        with closing(page.render(scale=150 / 72)) as bitmap:
            return np.array(bitmap.to_pil().convert("RGB"))[area]

    initially_visible = []
    for item in objects:
        active = ctypes.c_long()
        if not trace.raw.FPDFPageObj_GetIsActive(item, ctypes.byref(active)):
            raise ValueError("元の描画の表示状態を確認できない")
        if active.value:
            initially_visible.append(item)
    if not np.array_equal(render(), fixed):
        raise ValueError("全命令の描画が固定した画素と異なる")
    try:
        toggle(initially_visible, False)
        blank = render()
        background(blank)
        pending, owners = [initially_visible], []
        while pending:
            group = pending.pop()
            toggle(group, True)
            pixels = render()
            toggle(group, False)
            if np.array_equal(pixels, blank):
                continue
            if len(group) <= 1:
                owners.extend(group)
            else:
                middle = len(group) // 2
                pending.extend((group[:middle], group[middle:]))
        if not owners:
            raise ValueError("点を描いた文字オブジェクトを見つけられない")
        toggle(owners, True)
        if not np.array_equal(render(), fixed):
            raise ValueError("点の所有候補だけで固定画素を再現できない")
        toggle(owners, False)
        toggle([item for item in initially_visible if item not in owners], True)
        if not np.array_equal(render(), blank):
            raise ValueError("他の文字オブジェクトも点に寄与している")
        return owners
    finally:
        toggle(initially_visible, True)


def isolated(case, catalog, loaded):
    original = trace.reproduce
    trace.reproduce = reproduce
    try:
        return source.isolated(case, catalog, loaded)
    finally:
        trace.reproduce = original


def main():
    result = HERE / "result.json"
    if result.exists():
        raise FileExistsError("地色の開発試験は実行済み")
    pixel = np.full((8, 8, 3), (249, 235, 183), dtype=np.uint8)
    assert background(pixel) == (249, 235, 183)
    pixel[4, 4] = (30, 30, 30)
    try:
        background(pixel)
    except ValueError:
        pass
    else:
        raise ValueError("地色の検査が別の点を受理した")
    rows, _ = source.reference.cases()
    selection = {("defense-p0453", 46), ("wp-summary-p0010", 14), ("disaster-p0133", 2)}
    catalog, loaded, captured = audit.packets.old.lookup()[1], {}, []
    for case in rows:
        row = case["row"]
        if (row["key"], row["line_index"]) not in selection:
            continue
        fixed_png = audit.packets.old.CORPUS / "probe-v4/png" / (row["key"] + ".png")
        with Image.open(fixed_png) as image:
            color = list(image.convert("RGB").getpixel((row["box"][0] + 1, row["box"][1] + 1)))
        original = source.isolated(case, catalog, loaded)
        adjusted = isolated(case, catalog, loaded)
        seen = {"page": row["key"], "line_index": row["line_index"], "nearby_fixed_rgb": color,
                "before": bool(original), "after": bool(adjusted)}
        if adjusted:
            seen["evidence"] = adjusted[1]
            seen["without_initial_bullet"] = {side: adjusted[0]["text"] == audit.ref.NORMALIZE(v["text"]).lstrip("➢")
                                               for side, v in row["targets"].items() if v["known"]}
        captured.append(seen)
        print(seen, flush=True)
    if len(captured) != len(selection):
        raise ValueError("事前に確認した対照と対象の行がそろわない")
    audit.save_once(result, audit.encoded({
        "scope": "development-only", "cases": captured, "synthetic_controls": 2,
        "inputs": {str(p): audit.sha(p) for p in (Path(__file__), audit.ENDED, Path(source.__file__), Path(trace.__file__))},
    }))


if __name__ == "__main__":
    main()
