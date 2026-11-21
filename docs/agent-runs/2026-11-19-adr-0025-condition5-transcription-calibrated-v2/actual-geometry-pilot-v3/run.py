"""固定した12行で、回答基準を共通にして字形と所属の照合順を比べる。"""

from collections import Counter
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
V2 = HERE.parent / "actual-geometry-pilot-v2/run.py"
spec = importlib.util.spec_from_file_location("actual_v2", V2)
v2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v2)
base = v2.base
original_material = v2.material
old_summarize = v2.summarize
v2_lock = V2.parent / "lock.json"
new_out = v2.OUT.parent / HERE.name
shared = (
    "枠に所属する文字が確実に一字もないときだけ、statusはempty、textは空文字にしてください。"
    "所属する字の判読や所属自体を一字でも決められないときは部分転記せず、行全体を"
    "statusはunreadable、textは半角の?一字としてください。"
    "行全体を転記できた場合だけstatusをreadableとし、textに改行を入れないでください。\n"
)
guide = (
    "450 DPIの枠なしで、隣の字の断片を分け、離れた点や線がどの字の一部かを確認してください。"
    "次に150 DPIの枠あり・枠なしを対照し、字形ごとに指定軸の重なりと直交方向の中心を確認してください。"
    "所属する字を選んでから、縦書きの複数列は右の列から、各列は上から下へ転記してください。\n"
)


def material():
    targets, pictures, fixed = original_material()
    previous = base.load(v2_lock)
    for side, pack in fixed["packs"].items():
        if pack["inputs"] != previous["packs"][side]["inputs"] or fixed["targets"][side] != previous["targets"][side]:
            raise ValueError("前試験の元画像または対象記録が変化")
        for arm in v2.ARMS:
            for k in ("images", "image_sha256", "ids"):
                if pack["arms"][arm][k] != previous["packs"][side]["arms"][arm][k]:
                    raise ValueError("前試験の画像・順序・対象が変化")
        control = pack["arms"]["control"]["prompt"]
        geometry = pack["arms"]["geometry"]["prompt"]
        if geometry.count(guide) != 1 or geometry.replace(guide, "", 1) != control:
            raise ValueError("二つの指示の差が照合順に限定されない")
    fixed["v2_lock_sha256"] = base.sha(v2_lock)
    fixed["contrast_script_sha256"] = base.sha(Path(__file__))
    return targets, pictures, fixed


def summarize(targets, ballots):
    result = old_summarize(targets, ballots)
    counts = result["counts"]["unresolved"]
    for side, rows in result["rows"].items():
        for ident, row in rows.items():
            if row["previous"] != "unresolved":
                continue
            for arm in v2.ARMS:
                if all(ballots[side, arm, model][ident] == "" for model in v2.pilot.MODELS):
                    if row["arms"][arm] != "candidate-agreement":
                        raise ValueError("文字なしの判定が元の採点と異なる")
                    row["arms"][arm] = "agreed-empty"
                    counts[arm]["candidate-agreement"] -= 1
                    counts[arm]["agreed-empty"] += 1
    old, new = (result["counts"]["known"][a] for a in v2.ARMS)
    a, b = (counts[arm]["candidate-agreement"] for arm in v2.ARMS)
    result["advance"] = (
        b >= a + 2 and new["matches-previous"] >= old["matches-previous"]
        and new["differs-from-previous"] <= old["differs-from-previous"]
    )
    return result


if __name__ == "__main__":
    v2.HERE = HERE
    v2.OUT = new_out
    v2.ASSETS = new_out / "cards"
    v2.LOCK = HERE / "lock.json"
    v2.v1.INTRO += shared
    v2.v1.GUIDE = guide
    v2.material, v2.summarize = material, summarize
    v2.main()
