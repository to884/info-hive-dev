"""固定画像と隔離描画で確かめた丸印の訂正を、既定の採点で検査する。"""

import hashlib
import importlib.util
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
V15 = HERE.parent / "v15-reference-audit"


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


audit = module("frozen_v15", V15 / "run.py")
v14 = audit.prior.population
from verify_candidate_prediction import evaluate

OUT = v14.CANDIDATE.parent / HERE.name
TARGET = "defense-p0107", 22
SOURCE = HERE.parent / "v18-point-source-pilot/result.json"
load, sha, save_once, encoded = audit.load, audit.sha, audit.save_once, audit.encoded


def check_source():
    saved = load(SOURCE)
    if any(sha(Path(k)) != h for k, h in saved["inputs"].items()):
        raise ValueError("保存した隔離描画の検証に違いがある")
    chosen, = (r for r in saved["cases"] if r["page"] == TARGET[0] and r["line_index"] == TARGET[1])
    if chosen["outcome"] != "source-confirmed" or chosen["same_as_existing_label"] != {"image": False}:
        raise ValueError("既存正解との一字の相違が確定していない")
    proof, = chosen["evidence"]
    if not proof["others_have_no_ink"] or proof["codepoint"] != "30FB" or proof["cid"] != 638:
        raise ValueError("ある丸印が中黒の一字であることを確認できない")
    return proof


def confirmed_text(proof):
    ref = audit.reference
    ref.OUT = audit.OUT
    atlas = ref.DELIVERY = audit.OUT / "delivery"
    ref.PACKS, ref.READ, ref.START = (atlas / f for f in ("packages.json", "received.json", "delivery-started.json"))
    ref.receive = audit.receive
    rows, _ = ref.cases()
    case, = (v for v in rows if (v["row"]["key"], v["row"]["line_index"]) == TARGET)
    answer = case["answer"]["text"]
    entry, = ref.MARK.finditer(answer)
    if entry.start() != 0 or entry[1] != "round":
        raise ValueError("二票が記録した行頭の丸印に当たらない")
    l, _, r, _ = proof["box"]
    coords, = case["coordinates"]
    center = (l + r) / 2 - case["row"]["box"][0]
    if any(abs(center - v) > 10 for v in coords):
        raise ValueError("独立な二票と隔離した丸印の位置が異なる")
    return ref.NORMALIZE(ref.MARK.sub(chr(int(proof["codepoint"], 16)), answer))


def main():
    if OUT.exists() or (HERE / "result.json").exists():
        raise FileExistsError("この訂正と採点は実行済み")
    old_records = load(v14.CANDIDATE / "public.json")
    v14.prepared()
    matched = check_source()
    corrected = confirmed_text(matched)
    record, = (r for r in old_records if (r["key"], r["line_index"]) == TARGET)
    old = record["effective"]
    if not record["image_population"] or record["raw_region"] is not None or not old.startswith("●") or corrected != "・" + old[1:]:
        raise ValueError("画像補充正解の行頭の一字だけを訂正できない")
    error = hashlib.sha256(corrected.encode("utf-8")).hexdigest() != record["ocr_normalized_sha256"]
    old_error = record["ocr_error"]
    scores = v14.old.score.unpack_scoring(load(v14.CANDIDATE / "scoring.json"))
    line, = (r for r in scores[record["group"]]["lines"] if (r["key"], r["line_index"]) == TARGET)
    if line["rule"] != "exact" or line["error"] != old_error:
        raise ValueError("差し替える行と既定の採点の来歴が異なる")
    line.update(error=error, label_source="visible-source-point-v19")
    record.update(effective=corrected, ocr_error=error, source="visible-source-point-v19",
                  development_proof={"stage": SOURCE.parent.name, "trace": matched})
    with np.load(v14.old.PREDICTIONS, allow_pickle=False) as raw:
        prediction = raw["probabilities"]
    v = evaluate(scores, prediction)
    OUT.mkdir()
    save_once(OUT / "public.json", encoded(old_records))
    save_once(OUT / "scoring.json", encoded(v14.old.score.pack_scoring(scores)))
    files = (Path(__file__), SOURCE, v14.RESULT, v14.CANDIDATE / "public.json", v14.CANDIDATE / "scoring.json",
             v14.old.PREDICTIONS, V15 / "result.json", audit.OUT / "delivery/received.json")
    changed = [{"page": TARGET[0], "line_index": TARGET[1], "before_error": old_error, "after_error": error}]
    results = {"scope": "development-only", "changed": changed, "evaluation": v,
               "inputs": {str(p): sha(p) for p in files}, "artifacts": {f.name: sha(f) for f in OUT.iterdir()},
               "same_predictions_sha256": sha(v14.old.PREDICTIONS)}
    save_once(HERE / "result.json", encoded(results))
    print("開発6組", v["all_pass"], "公開3組", v["all_gates"], flush=True)


if __name__ == "__main__":
    main()
