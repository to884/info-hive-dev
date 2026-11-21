"""同じ開発19行で、図表の色見本を区別して点の目盛りを確認する。"""

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v24-physical-transcription-pilot/run.py"
spec = importlib.util.spec_from_file_location("combined_transcription_pilot", BASE)
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)
pilot.HERE = HERE
pilot.OUT = pilot.OUT.with_name("reference-v37-transcription-final-pilot")
pilot.LOCK, pilot.RESULT = HERE / "lock.json", HERE / "result.json"
V33 = HERE.parent / "v33-horizontal-guide-pilot"
V35 = HERE.parent / "v35-coordinate-pilot"
GUIDE = (
    "丸は、450 DPIの枠なしで、形、色、同じ行での繰り返しを確認します。"
    "青などの色付きで隣の字の半分ほどの大きさの塗り丸が、同じ行の中に複数並び、"
    "それぞれ独立した本文項目の直前にあると確かめた時に、その形を「●」と写します。"
    "黒い単独の塗り点は行の先頭や本文の中で字種が画像から決まらない場合、位置を ⟦round:X-X⟧ と書きます。"
    "形が塗り点で字種が決まらなければ、文中で中黒を置くのが自然に見える場合も座標を返します。"
    "単独の round は横座標で読んだ同じ中心値を2回書きます。"
    "本文の先頭に共通の位置で並ぶ、上が白く下が黒い右向きの矢じりは「➢」です。"
    "グラフの系列の色や模様を示す凡例の図形見本は本文から除きます。"
    "同じ高さに等間隔の小さい塗り点が3個以上続き、字の区切りが見えない場合は、一つの ⟦trail:X-Y⟧ とします。"
    "最初と最後の点は横座標で別々に読み、後の数字や本文を含めません。"
)
RULER_GUIDE = (
    "拡大した横座標の大目盛りに書かれた数字は枠の左からの値で、数字の間隔は10画素です。"
    "番号のない小目盛りは5画素の中間です。枠への入り方の目盛りとは分けて、印の座標は横座標で読みます。"
)


def snapshot():
    a = pilot.audit
    one, two = V33 / "lock.json", V35 / "lock.json"
    base, ruler = a.load(one), a.load(two)
    for manifest in (base, ruler):
        if any(a.sha(Path(f)) != h for f, h in manifest["files"].items()):
            raise ValueError("前の開発で固定した添付か方法が異なる")
    private = pilot.OUT.with_name("reference-" + V33.name)
    chosen = pilot.OUT / "display/selection.json"
    chosen.parent.mkdir(parents=True)
    source = private / "display/selection.json"
    a.save_once(chosen, source.read_bytes())
    pilot.SAMPLES = a.load(chosen)["selected"]
    jobs, mapping = {}, {}
    for label, task in base["jobs"].items():
        old_text = task["request"]["prompt"]
        guide_start = "紙面の本文と位置がそろう先頭の箇条書きは"
        left, separator, body = old_text.partition(guide_start)
        _, contract, right = body.partition(a.packets.FORMAT)
        if not separator or not contract:
            raise ValueError("前の開発指示の切り分けに失敗")
        entry = label.split("/")[0]
        raw = ruler["jobs"].get(label, task)
        request = raw["request"]
        prefix = left + GUIDE + (RULER_GUIDE if label in ruler["jobs"] else "")
        jobs[label] = {**raw, "request": {**request, "prompt": prefix + contract + right}}
        data = base["mapping"][entry]
        if entry in ruler["mapping"]:
            data = {**data, "image_reference": ruler["mapping"][entry]["image_reference"]}
        mapping[entry] = data
    files = (Path(__file__), BASE, HERE / "protocol.md", one, two, chosen, source)
    return {"jobs": jobs, "mapping": mapping,
            "files": base["files"] | ruler["files"] | {str(p): a.sha(p) for p in files}}


if __name__ == "__main__":
    pilot.snapshot = snapshot
    pilot.main()
