"""2 つ目の読みの食い違いが、行の誤りをどれだけ当てるかを、選ぶ資料だけで調べる（後から見た試し。合否には使わない）。

使い方（rag の依存の環境で動かす）: python -X utf8 scripts/probe_analyze.py
corpus/probe/reads/ の読みと、正解（corpus/*/*.truth.json の side が tuning）を突き合わせる。
印は「確信度が t より低い、または食い違いがある」行。(a)〜(c) は score.py と同じ数え方（不利な側の行は、
印があれば誤りでない、なければ誤り）で数える。結果を results/probe-tuning.json に書く。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from score import CORPUS, RESULTS, joined, load_truths, normalize, page_records, reading_order  # noqa: E402

import score  # noqa: E402

# 後から見つけた正規化の漏れ: 白丸（U+25CB）と漢数字のゼロ（U+3007）は同じ字形なので、そろえる
score.SAME["○"] = "〇"
OTHER_DPI = 200

THRESHOLDS = [0.0, 0.2, 0.3, 0.4, 0.5]


def differs(line: dict, key: str) -> bool:
    read = (line.get("reads") or {}).get(key)
    return read is not None and normalize(read["text"]) != normalize(line["text"])


def other_dpi(line: dict) -> bool:
    """200 dpi で検出からやり直した読みと食い違うか（つながる行がなければ食い違いとする）。"""
    return line.get("dpi_text") is not None and normalize(line["dpi_text"]) != normalize(line["text"])


SIGNALS = {
    "none": lambda line: False,
    "r100": lambda line: differs(line, "r100"),
    "r50": lambda line: len(line["text"]) < 45 and differs(line, "r50"),
    "pad": lambda line: differs(line, "pad100"),
    "blur": lambda line: differs(line, "blur100"),
    "models": lambda line: differs(line, "r100") or (len(line["text"]) < 45 and differs(line, "r50")),
    "any": lambda line: (differs(line, "r100") or (len(line["text"]) < 45 and differs(line, "r50"))
                         or differs(line, "pad100") or differs(line, "blur100")),
    "dpi": other_dpi,
    "blur+dpi": lambda line: differs(line, "blur100") or other_dpi(line),
    "any+dpi": lambda line: (differs(line, "r100") or (len(line["text"]) < 45 and differs(line, "r50"))
                             or differs(line, "pad100") or differs(line, "blur100") or other_dpi(line)),
}


def attach_other_dpi(ocr_lines: list[dict], name: str, pdf_sha256: str) -> None:
    """ほかの dpi の読みの行を、箱を 150 dpi に縮めて対応させ、読む順につないだ本文を dpi_text に置く。"""
    scale = 150 / OTHER_DPI
    others = []
    for line in load_reads(f"reads-png{OTHER_DPI}", name, pdf_sha256):
        x, y, w, h = line["box"]
        others.append({**line, "box": [x * scale, y * scale, (x + w) * scale, (y + h) * scale]})
    for line in ocr_lines:
        matched = [o for o in others if joined(o["box"], line["box"])]
        vertical = bool(line.get("vertical"))
        line["dpi_text"] = "".join(o["text"] for o in reading_order(matched, vertical))


def load_reads(folder: str, key: str, pdf_sha256: str) -> list[dict]:
    """試しの読みを、描いた画像と元の PDF の SHA-256 で照らしてから返す（照らせなければ止まる）。"""
    png_folder = {"reads": "png", f"reads-png{OTHER_DPI}": f"png{OTHER_DPI}"}[folder]
    manifest = json.loads((CORPUS / "probe" / png_folder / "manifest.json").read_bytes().decode("utf-8"))
    entry = manifest[f"{key}.png"]
    reads = json.loads((CORPUS / "probe" / folder / f"{key}.json").read_bytes().decode("utf-8"))
    if entry["pdf_sha256"] != pdf_sha256 or reads.get("image_sha256") != entry["png_sha256"]:
        raise SystemExit(f"試しの読みの出典が、今の試料と違う: {folder}/{key}（描き直して読み直す）")
    return reads["lines"]


def eye_truth(side: str) -> dict[tuple[str, int], str]:
    """目で書き起こした正解（文字の層から決められない公開の OCR の行）。(ページの鍵, 行の番号) → 文字。"""
    folder = CORPUS / "public" / "eyetruth" / side
    path = folder / "truth.json"
    if not path.exists():
        return {}
    index = {x["file"]: (x["key"], x["line_index"]) for x in
             json.loads((folder / "index.json").read_bytes().decode("utf-8"))}
    return {index[name]: text for name, text in json.loads(path.read_bytes().decode("utf-8")).items()}


def apply_eye_truth(records: list[dict], key: str, truths: dict) -> None:
    """書き起こした正解がある行は、その正解と比べて誤りを決める（1 対 1 と同じく "exact" にする）。"""
    for r in records:
        text = truths.get((key, r["line_index"]))
        if text is not None and r["rule"] in ("pessimistic", "excluded"):
            r.update(rule="exact", error=normalize(text) != r["line_text"], eye=True)


def collect() -> dict:
    found = {"synthetic": {"lines": [], "missed": 0, "pages": []}, "public": {"lines": [], "missed": 0, "pages": []}}
    truths = eye_truth("tuning")
    for truth in load_truths():
        if truth["side"] != "tuning":
            continue
        stratum = truth["stratum"]
        for page in truth["pages"]:
            reads = load_reads("reads", f"{truth['name']}-p{page['page']:04d}", truth["pdf_sha256"])
            ocr_lines = [{**line, "box": [line["box"][0], line["box"][1], line["box"][0] + line["box"][2],
                                          line["box"][1] + line["box"][3]]} for line in reads]
            attach_other_dpi(ocr_lines, f"{truth['name']}-p{page['page']:04d}", truth["pdf_sha256"])
            records, missed = page_records(page["lines"], ocr_lines, stratum)
            if stratum == "public":
                apply_eye_truth(records, f"{truth['name']}-p{page['page']:04d}", truths)
            for r in records:
                r["line"] = ocr_lines[r["line_index"]]
            found[stratum]["lines"] += records
            found[stratum]["missed"] += len(missed)
            found[stratum]["pages"].append(ocr_lines)
    return found


def measure(data: dict, signal, t: float) -> dict:
    def flagged(line):
        return (line["confidence"] is not None and line["confidence"] < t) or signal(line)

    counted = [r for r in data["lines"] if r["rule"] != "excluded"]
    flags = [r for r in counted if flagged(r["line"])]

    def error(r):
        return r["error"] if r["rule"] == "exact" else not flagged(r["line"])

    errors = sum(error(r) for r in counted) + data["missed"]
    caught = sum(error(r) for r in flags)
    pages = sum(any(flagged(line) for line in page) for page in data["pages"])
    exact = [r for r in counted if r["rule"] == "exact" and r["shape"] == "1:1"]
    exact_errors = [r for r in exact if r["error"]]
    exact_correct = [r for r in exact if not r["error"]]
    return {"flagged": len(flags), "errors": errors, "caught": caught,
            "a": round(caught / len(flags), 3) if flags else None, "b": round(caught / errors, 3) if errors else None,
            "c": round(pages / len(data["pages"]), 3),
            "exact_b": round(sum(flagged(r["line"]) for r in exact_errors) / len(exact_errors), 3) if exact_errors else None,
            "exact_false_flag": round(sum(flagged(r["line"]) for r in exact_correct) / len(exact_correct), 4)
            if exact_correct else None}


def main() -> None:
    data = collect()
    report = {}
    for stratum, d in data.items():
        report[stratum] = {}
        print(stratum, "行", len(d["lines"]), "ページ", len(d["pages"]))
        for name, signal in SIGNALS.items():
            report[stratum][name] = {}
            for t in THRESHOLDS:
                row = measure(d, signal, t)
                report[stratum][name][str(t)] = row
                print(f"  {name:7s} t={t:.1f} 印 {row['flagged']:4d} (a) {row['a']} (b) {row['b']} (c) {row['c']}"
                      f"  1:1 の (b) {row['exact_b']} 正しい行に印 {row['exact_false_flag']}")
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "probe-tuning.json").write_bytes((json.dumps(report, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))


# 行を単位にした基準（作者の決定 2026-11-16）で、決めておいた組み合わせを数える。
# (a) 印の行のうち誤り、(b) 誤りの行のうち印（検出できなかった正解の行は入れない）、(c) 正しい行のうち印（誤報）。
# 不利な側の行は、印があれば誤りでない（(a) を下げ、(c) の誤報に入る）、印がなければ誤り（(b) を下げる）。
COMBOS = ["blur", "r100", "dpi", "blur+dpi", "any+dpi"]
# 公開の正解を目で作ったあと、試す前に決めた中間の 4 つ（200 dpi の食い違いを、ほかの信号で裏付けたときだけ使う）
SIGNALS["blur+dpi&c<0.9"] = lambda line: differs(line, "blur100") or (other_dpi(line) and (line["confidence"] or 0) < 0.9)
SIGNALS["blur+dpi&c<0.95"] = lambda line: differs(line, "blur100") or (other_dpi(line) and (line["confidence"] or 0) < 0.95)
SIGNALS["blur+dpi&r100"] = lambda line: differs(line, "blur100") or (other_dpi(line) and differs(line, "r100"))
SIGNALS["blur+dpi&pad"] = lambda line: differs(line, "blur100") or (other_dpi(line) and differs(line, "pad100"))
COMBOS += ["blur+dpi&c<0.9", "blur+dpi&c<0.95", "blur+dpi&r100", "blur+dpi&pad"]


def line_unit(data: dict, signal, t: float) -> dict:
    def flagged(line):
        return (line["confidence"] is not None and line["confidence"] < t) or signal(line)

    errors = correct = caught = false = flags = 0
    for r in data["lines"]:
        if r["rule"] == "excluded":
            continue
        f = flagged(r["line"])
        error = r["error"] if r["rule"] == "exact" else not f
        flags += f
        errors += error
        correct += not error
        caught += f and error
        false += f and not error
    return {"flagged": flags, "errors": errors, "a": round(caught / flags, 3) if flags else None,
            "b": round(caught / errors, 3) if errors else None, "c": round(false / correct, 4) if correct else None}


def line_main() -> None:
    data = collect()
    report = {}
    for t in (0.0, 0.3, 0.5):
        for name in COMBOS:
            row = {s: line_unit(d, SIGNALS[name], t) for s, d in data.items()}
            ok = all(r["a"] is not None and r["a"] >= 0.55 and r["b"] >= 0.85 and r["c"] <= 0.10 for r in row.values())
            report[f"{name}@{t}"] = {**row, "margin_ok": ok}
            print(f"{name:9s} t={t:.1f}", " ".join(f"{s}: (a) {r['a']} (b) {r['b']} (c) {r['c']}" for s, r in row.items()),
                  "余裕で満たす" if ok else "")
    (RESULTS / "probe-line-unit-tuning.json").write_bytes(
        (json.dumps(report, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))


if __name__ == "__main__":
    line_main() if len(sys.argv) > 1 and sys.argv[1] == "--line" else main()
