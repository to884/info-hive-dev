"""単独の色付き項目丸と、小点・句点を画像で区別する追試。"""

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v41-paragraph-bullets-pilot/prepare.py"
spec = importlib.util.spec_from_file_location("paragraph_circle_transcription", BASE)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
pilot = old.pilot
old.HERE = pilot.HERE = HERE
pilot.OUT = pilot.OUT.with_name("reference-v46-paragraph-circle-pilot")
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"
old.SAMPLES = old.SAMPLES | {("disaster-p0107", 10): "hollow-stop-control"}
old.GUIDE = (
    "段落の行頭を確認します。文字の高さの半分ほどの色付きの円が独立して左端にあり、"
    "円の直後に空きがあって本文のまとまりが始まる場合、その項目の形は「●」です。"
    "同じ色の円が別の段落や行内の複数の項目にあるときも、本文項目の直前にある全部の円を確認します。"
    "行頭の黒丸は、他の項目のマーカーと位置・大きさがそろい、本文の文字間隔と離れているものが該当します。"
    "本文の並びにある単独の小点は形で判断します。450 DPIで内側に白または地色の穴を持つ輪は、"
    "小さくても「。」です。穴のない曖昧な小点は、横座標の中心を二度記録する round です。"
    "図表の系列だけを示す見本は本文の記号に含めません。"
)


def snapshot():
    plan = old.snapshot()
    files = (Path(__file__), BASE, BASE.parent / "lock.json")
    plan["files"].update({str(p): pilot.audit.sha(p) for p in files})
    return plan


if __name__ == "__main__":
    pilot.snapshot = snapshot
    pilot.main()
