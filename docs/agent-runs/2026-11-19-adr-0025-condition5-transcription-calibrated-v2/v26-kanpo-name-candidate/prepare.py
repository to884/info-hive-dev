"""官報の同じ表の字形を開発用に二読し、既存の画像正解を確かめる。"""

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v24-physical-transcription-pilot/run.py"
spec = importlib.util.spec_from_file_location("blind_transcription", BASE)
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)
pilot.HERE = HERE
pilot.OUT = pilot.OUT.with_name("reference-v26-kanpo-name-candidate")
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"
pilot.SAMPLES = {("kanpo1828-p3-p0001", i): "name" for i in (144, 145, 164, 166, 180, 196, 201, 206, 208)}
pilot.SAMPLES.update({("kanpo1828-p3-p0001", i): "control" for i in (147, 198, 199)})
pilot.DETAILS += (
    "複雑な字は右側の上部の短い縦画と、中心で交差する長いはらいを見分けます。"
    "左に離れた点が縦に並ぶ部首と、左から下へ回って右へ伸びる部首を区別します。"
    "縦列の並びや他の行の語を使って、目の前の字形を変えないでください。"
)
base_snapshot = pilot.snapshot


def snapshot():
    data = base_snapshot()
    data["jobs"] = {n: d for n, d in data["jobs"].items() if n.endswith("/new")}
    record = (Path(__file__), BASE, HERE / "protocol.md")
    data["files"].update({str(p): pilot.audit.sha(p) for p in record})
    return data


if __name__ == "__main__":
    pilot.snapshot = snapshot
    pilot.main()
