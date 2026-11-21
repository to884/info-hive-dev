"""画像と所属計測が合った開発用の訂正の感度を測る。"""

import hashlib
from pathlib import Path
import sys

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "v13-layout-generalization"
sys.path.insert(0, str(HERE.parent / "v10-reference-audit"))
from cards import CORPUS, PACKS, SOURCE, load, score, sha
from readers import encoded, receive, save_once
from selection import CANDIDATE, LOCK, SCORE, PREDICTIONS, take_public_rows
from verify_candidate_prediction import evaluate

PILOT = CORPUS / "reference-v13-layout-generalization"
OUT = CANDIDATE.parent / HERE.name
TARGET = "kanpo1827-p2-p0001", 49


def confirmed():
    locked, receipt = load(PREVIOUS / "lock.json"), load(PREVIOUS / "result.json")
    started = load(PILOT / "started.json")
    expected = sha(PREVIOUS / "lock.json")
    if receipt["lock_sha256"] != expected or started["lock_sha256"] != expected:
        raise ValueError("開発の受領と画像の固定が一致しない")
    if any(sha(Path(p)) != digest for p, digest in locked["inputs"].items()):
        raise ValueError("開発の配布と方法が変化")
    name, item = next((k, v) for k, v in receipt["rows"].items() if (v["key"], v["line_index"]) == TARGET)
    if item["outcome"] != "agreed-different-label" or item["kind"] != "fresh-vertical":
        raise ValueError("新規の開発行の一致がない")
    pack = locked["packs"][name]
    request = pack["request"]
    folder = PILOT / "cards" / name
    first, = request["ids"]
    opinions, evidence = [], {}
    for role, model in locked["models"].items():
        source = PILOT / "reads" / name / role
        raw = receive(source, role, model, request, folder, started["runtime"][role])
        if {k: v for k, v in raw.items() if k != "answers"} != item["receipts"][role]:
            raise ValueError("保存した二票を再現できない")
        a = raw["answers"][first]
        if a["status"] != "readable":
            raise ValueError("新しい二票の本文が確定していない")
        opinions.append(score.audit.normalize(a["text"]))
        evidence.update({str(p): sha(p) for p in source.iterdir()})
    if opinions[0] != opinions[1] or item["receipts"]["gpt"]["session"] == item["receipts"]["claude"]["session"]:
        raise ValueError("独立した二票の一致を確認できない")
    row = load(SOURCE)["selected"][pack["entry"]]
    if (row["key"], row["line_index"]) != TARGET or set(row["targets"]) != {"image"}:
        raise ValueError("割当の対象が画像補充の行ではない")
    fixed = load(PACKS)["sources"][row["key"]]["150_dpi"]
    image = CORPUS / "probe-v4/png" / (row["key"] + ".png")
    value = row["targets"]["image"]["text"]
    previous = score.audit.normalize(value)
    corrected = opinions[0]
    if not corrected.startswith(previous) or len(corrected) != len(previous) + 1:
        raise ValueError("画像の端の一字だけの変更ではない")
    return row, image, fixed, corrected, evidence


def pixels(row, path, expected):
    if sha(path) != expected or row["allocation_axis"] != "y":
        raise ValueError("固定した画像または割当軸が異なる")
    x, y, w, h = row["box"]
    with Image.open(path) as im:
        gray = np.asarray(im.convert("L"))
    left, top, right, bottom = x - 3, y + h - 9, x + w + 3, y + h + 8
    window = gray[top:bottom, left:right]
    trace = []
    for threshold in (128, 160, 192):
        ys, xs = np.nonzero(window < threshold)
        l, t, r, b = int(xs.min()) + left, int(ys.min()) + top, int(xs.max()) + left + 1, int(ys.max()) + top + 1
        if l <= left or r >= right:
            raise ValueError("測定窓が字の左右の画を切っている")
        within = min(b, y + h) - max(t, y)
        if 2 * within < b - t or not x <= (l + r) / 2 < x + w:
            raise ValueError("固定画素上で字の所属を確認できない")
        trace.append({"threshold": threshold, "ink_box": [l, t, r, b], "in_frame": within, "length": b - t})
    return trace


def main():
    if OUT.exists() or (HERE / "result.json").exists():
        raise FileExistsError("感度の証跡を上書きしない")
    row, image, expected, corrected, evidence = confirmed()
    measured = pixels(row, image, expected)
    public, flags = take_public_rows()
    label = next(r for r in public if (r["key"], r["line_index"]) == TARGET)
    if not label["image_population"] or label["raw_region"] is not None or label["effective"] != row["targets"]["image"]["text"]:
        raise ValueError("画像補充正解の元の状態が異なる")
    data = score.unpack_scoring(load(CANDIDATE / "scoring.json"))
    scored = next(r for r in data[label["group"]]["lines"] if (r["key"], r["line_index"]) == TARGET)
    old_error = label["ocr_error"]
    new_error = hashlib.sha256(corrected.encode("utf-8")).hexdigest() != label["ocr_normalized_sha256"]
    if bool(scored["error"]) != old_error or scored["rule"] != "exact":
        raise ValueError("既存の採点の正誤と画像の本文が違う")
    scored.update(error=new_error, label_source="fixed-image-boundary-v14")
    label.update(effective=corrected, ocr_error=new_error, source="fixed-image-boundary-v14",
                 development_proof={"stage": PREVIOUS.name, "boundary_ink": measured})
    with np.load(PREDICTIONS, allow_pickle=False) as archive:
        probabilities = archive["probabilities"]
    result = evaluate(data, probabilities)
    if len(public) != 8822 or len(flags) != len(public):
        raise ValueError("評価行の分母を維持できない")
    OUT.mkdir()
    score.audit.save(OUT / "public.json", public)
    score.audit.save(OUT / "scoring.json", score.pack_scoring(data))
    paths = [Path(__file__), HERE / "protocol.md", SOURCE, PACKS, LOCK, SCORE, PREDICTIONS, image,
             PREVIOUS / "lock.json", PREVIOUS / "result.json", PILOT / "started.json",
             CANDIDATE / "public.json", CANDIDATE / "scoring.json"]
    report = {"scope": "development-only", "changed": [{"page": TARGET[0], "line_index": TARGET[1],
              "before_error": old_error, "after_error": new_error, "fixed_pixels": measured}],
              "same_predictions_sha256": sha(PREDICTIONS), "inputs": {str(p): sha(p) for p in paths},
              "raw_receipts": evidence, "artifacts": {p.name: sha(p) for p in OUT.iterdir()}, "evaluation": result}
    save_once(HERE / "result.json", encoded(report))
    print(f"開発6組={result['all_pass']} 公開3組={result['all_gates']}", flush=True)


if __name__ == "__main__":
    main()
