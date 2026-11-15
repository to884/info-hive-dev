# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["pdfminer.six==20260107"]
# ///
"""pdfminer の本文が走らせるたびに変わる原因を除いて、本文が毎回同じになるかを確かめる。

使い方: uv run --script stable_text.py <PDF> <結果の名前に付ける接尾辞>
結果（ページごとの本文の SHA-256）を results/stable-<PDF の名前><接尾辞>.json に書く。本文そのものは書かない。

原因: pdfminer.layout.LTLayoutContainer.group_textboxes は、テキストボックスの組をヒープで距離の順に
まとめる。距離が同じ組の順は id(obj)（オブジェクトのメモリーの番地）で決まる。番地はプロセスごとに
変わるので、距離の同じ組があるページでは、まとめる順、つまり本文の並びが変わることがある。

ここでは group_textboxes を呼ぶあいだだけ、モジュールの中の id を「初めて見た順の番号」に置きかえる。
番号はページの中で決まった順に振られるので、同じ距離の組の順も毎回同じになる。
"""

from __future__ import annotations

import builtins
import hashlib
import io
import json
import sys
from pathlib import Path

import pdfminer.layout as layout

_original_group = layout.LTLayoutContainer.group_textboxes


def _stable_group(self, laparams, boxes):
    seen: dict[int, tuple[object, int]] = {}

    def stable_id(obj):
        key = builtins.id(obj)
        if key not in seen:
            seen[key] = (obj, len(seen))  # obj を持っておき、番地が使い回されないようにする
        return seen[key][1]

    layout.id = stable_id
    try:
        return _original_group(self, laparams, boxes)
    finally:
        del layout.id


def pass_pages(path: Path) -> list[str]:
    from pdfminer.converter import TextConverter
    from pdfminer.layout import LAParams
    from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
    from pdfminer.pdfpage import PDFPage
    texts, output, manager = [], io.StringIO(), PDFResourceManager()
    with path.open("rb") as handle, TextConverter(manager, output, codec="utf-8",
                                                  laparams=LAParams(detect_vertical=True)) as device:
        interpreter = PDFPageInterpreter(manager, device)
        for page in PDFPage.get_pages(handle):
            interpreter.process_page(page)
            texts.append(output.getvalue().rstrip(chr(12)))
            output.seek(0)
            output.truncate(0)
    return texts


def main() -> None:
    path = Path(sys.argv[1]).resolve()
    layout.LTLayoutContainer.group_textboxes = _stable_group
    texts = pass_pages(path)
    found = {"pdf": path.name, "pages": len(texts),
             "pass_sha256": [hashlib.sha256(t.encode("utf-8")).hexdigest() for t in texts]}
    out = Path(__file__).resolve().parent.parent / "results" / f"stable-{path.stem}{sys.argv[2]}.json"
    out.write_bytes(json.dumps(found, ensure_ascii=False, indent=1).encode("utf-8"))
    print(path.name, len(texts), "pages")


if __name__ == "__main__":
    main()
