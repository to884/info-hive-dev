"""本文の中の大きい箇条書き丸と、小さい丸印を固定画像で比較する。"""

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v24-physical-transcription-pilot/run.py"
spec = importlib.util.spec_from_file_location("blind_transcription", BASE)
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)
pilot.HERE = HERE
pilot.OUT = pilot.OUT.with_name("reference-v29-typographic-round-pilot")
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"
pilot.SAMPLES = {
    ("defense-p0453", 46): "colored-bullet", ("defense-p0453", 49): "colored-bullet",
    ("defense-p0107", 22): "small-mark", ("disaster-p0133", 2): "small-mark",
    ("wp-summary-p0004", 8): "legend", ("wp-summary-p0010", 14): "arrow-and-small-mark",
}
pilot.DETAILS = ""
pilot.HORIZONTAL = (
    "固定450 DPIの枠なしを見て、丸い印を隣の文字の高さと、見出しや本文とそろう位置で比べます。"
    "本文と同じ行で項目の先頭に繰り返す、普通の文字の高さの半分ほどの均一な塗りつぶし丸は、"
    "色が付いていても、見える丸の字形を「●」として写します。"
    "字よりかなり小さく、全体から字種を区別できない点は色にかかわらず round です。"
    "凡例の図形見本は転記しません。箇条書きの先頭にそろう上が白く下が黒い右向き矢じりは「➢」と写します。"
)
base_snapshot = pilot.snapshot


def snapshot():
    data = base_snapshot()
    paths = (Path(__file__), BASE, HERE / "protocol.md")
    data["files"].update({str(p): pilot.audit.sha(p) for p in paths})
    return data


if __name__ == "__main__":
    pilot.snapshot = snapshot
    pilot.main()
