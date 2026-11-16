"""OCR の行と正解の行を対応させ、閾値ごとに (a)〜(c) を数える（測り方は ../../adr-0025-condition5-2026-11-16.md）。

使い方（rag の依存の環境で動かす）:
    python -X utf8 scripts/score.py dev          # 試しの原稿の対応と数を表示する（測り方の不具合を直すため）
    python -X utf8 scripts/score.py tuning       # 選ぶ資料で閾値を選び、results/tuning.json に書く
    python -X utf8 scripts/score.py evaluation   # results/tuning.json の閾値で、確かめる資料を 1 回だけ数える

正解は corpus/synthetic/*.truth.json と corpus/public/*.truth.json、OCR の結果は corpus/ocr/<tag>-p<ページ>.json。
(a) と (b) は OCR の行ごとに数える。正解と 1 対 1 に対応しない行は、条件を満たしにくい側（不利な側）に数える。
"""

from __future__ import annotations

import functools
import json
import math
import sys
import unicodedata
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
ROOT = BENCH.parents[2]
sys.path.insert(0, str(ROOT / "info-hive-rag" / "scripts"))

from rag_pdf import OCR_KINDS  # noqa: E402
from rag_review import is_low  # noqa: E402

CORPUS = BENCH / "corpus"
RESULTS = BENCH / "results"
GRID = [round(0.01 * i, 2) for i in range(1, 100)]
MIN_COUNT = 20
Z_ONE_SIDED = 1.6449  # 片側 95%
SAME = {**{c: "-" for c in "‐‑‒–—―−－"}, "〜": "~", "～": "~",
        **{c: "'" for c in "‘’‚‛"}, **{c: '"' for c in "“”„‟"},
        "･": "・", "·": "・"}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    return "".join(SAME.get(c, c) for c in text if not c.isspace())


def distance(a: str, b: str) -> int:
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ca != cb)))
        previous = current
    return previous[-1]


def area(box) -> float:
    return max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1])


def joined(ocr_box, truth_box) -> bool:
    """重なりの面積が、小さい方の箱の面積の半分以上なら、つながる。"""
    inter = [max(ocr_box[0], truth_box[0]), max(ocr_box[1], truth_box[1]),
             min(ocr_box[2], truth_box[2]), min(ocr_box[3], truth_box[3])]
    smaller = min(area(ocr_box), area(truth_box))
    return smaller > 0 and area(inter) >= 0.5 * smaller


def reading_order(lines: list[dict], vertical: bool) -> list[dict]:
    def overlap(a, b, lo, hi) -> float:
        inter = min(a[hi], b[hi]) - max(a[lo], b[lo])
        return inter / max(1e-9, min(a[hi] - a[lo], b[hi] - b[lo]))

    def compare(p, q) -> int:
        a, b = p["box"], q["box"]
        if not vertical:
            if overlap(a, b, 1, 3) >= 0.5:  # 同じ高さ: 左から右
                return -1 if a[0] < b[0] else 1
            return -1 if a[1] + a[3] < b[1] + b[3] else 1  # 上から下
        if overlap(a, b, 0, 2) >= 0.5:  # 同じ列: 上から下
            return -1 if a[1] < b[1] else 1
        return -1 if a[0] + a[2] > b[0] + b[2] else 1  # 右から左

    return sorted(lines, key=functools.cmp_to_key(compare))


def page_records(truth_lines: list[dict], ocr_lines: list[dict], stratum: str) -> tuple[list[dict], list[dict]]:
    """OCR の行ごとの記録と、読み落とした正解の行の記録を返す。

    OCR の行の rule は、誤りの決め方: "exact"（error が決まっている）、"pessimistic"（低い行は誤りでない、
    低くない行は誤り。閾値で決まる）、"excluded"（正解から除いた行とつながる。数えない）。
    """
    nodes = [("t", i) for i in range(len(truth_lines))] + [("o", j) for j in range(len(ocr_lines))]
    parent = {node: node for node in nodes}

    def find(node):
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for j, o in enumerate(ocr_lines):
        for i, t in enumerate(truth_lines):
            if joined(o["box"], t["box"]):
                parent[find(("o", j))] = find(("t", i))
    groups: dict = {}
    for node in nodes:
        groups.setdefault(find(node), []).append(node)
    records, missed = [], []
    for members in groups.values():
        truth = [truth_lines[i] for kind, i in members if kind == "t"]
        ocr = [ocr_lines[j] for kind, j in members if kind == "o"]
        excluded = sorted({x["excluded"] for x in truth if x.get("excluded")})
        vertical = sum(bool(x.get("vertical")) for x in truth + ocr) * 2 > len(truth) + len(ocr)
        truth_text = normalize("".join(x["text"] for x in reading_order(truth, vertical)))
        ocr_text = normalize("".join(x["text"] for x in reading_order(ocr, vertical)))
        shape = f"{len(truth)}:{len(ocr)}"
        if not ocr:
            if not excluded:
                missed.append({"shape": shape, "truth_chars": len(truth_text), "truth_text": truth_text})
            continue
        dist = distance(truth_text, ocr_text)
        for line in ocr:
            record = {"shape": shape, "confidence": line["confidence"], "distance": dist,
                      "truth_chars": len(truth_text), "truth_text": truth_text, "ocr_text": ocr_text,
                      "line_text": normalize(line["text"])}
            if excluded:
                record.update(rule="excluded", excluded=excluded)
            elif truth and len(truth) == 1 and len(ocr) == 1:
                record.update(rule="exact", error=dist >= 1)
            elif truth:
                # 1 対 1 でない対応: 誤りがなければ誤りでない。誤りがあれば、不利な側に数える
                record.update(rule="exact", error=False) if dist == 0 else record.update(rule="pessimistic")
            elif stratum == "synthetic":
                record.update(rule="exact", error=bool(record["line_text"]))  # 正解は空
            else:
                record.update(rule="pessimistic")  # 公開: 文字の層にない文字を読んだ行かもしれない
            records.append(record)
    return records, missed


def load_truths() -> list[dict]:
    truths = []
    for path in sorted((CORPUS / "synthetic").glob("*.truth.json")) + sorted((CORPUS / "public").glob("*.truth.json")):
        truth = json.loads(path.read_bytes().decode("utf-8"))
        truth.setdefault("stratum", "synthetic" if path.parent.name == "synthetic" else "public")
        truths.append(truth)
    return truths


def collect(side: str) -> dict:
    """その側の、種類ごとの OCR の行、読み落とした行、ページを集める。"""
    found = {"synthetic": {"lines": [], "missed": [], "pages": []}, "public": {"lines": [], "missed": [], "pages": []}}
    for truth in load_truths():
        if truth["side"] != side:
            continue
        stratum = truth["stratum"]
        for page in truth["pages"]:
            path = CORPUS / "ocr" / f"{truth['name']}-p{page['page']:04d}.json"
            if not path.exists():
                raise SystemExit(f"OCR の結果がない: {path.name}")
            ocr = json.loads(path.read_bytes().decode("utf-8"))
            ocr_lines = [{**line, "box": [line["box"][0], line["box"][1], line["box"][0] + line["box"][2],
                                          line["box"][1] + line["box"][3]]} for line in ocr["lines"]]
            label = {"name": truth["name"], "page": page["page"], "variant": page.get("variant"),
                     "kind": page["kind"], "pdf_sha256": ocr["pdf_sha256"]}
            records, missed = page_records(page["lines"], ocr_lines, stratum)
            found[stratum]["lines"] += [{**label, **r} for r in records]
            found[stratum]["missed"] += [{**label, **m} for m in missed]
            found[stratum]["pages"].append({**label, "confidence_min": ocr["confidence_min"],
                                            "confidence_revision": ocr["confidence_revision"],
                                            "lines": len(ocr_lines)})
    return found


def wilson(k: int, n: int, z: float) -> list[float] | None:
    if n == 0:
        return None
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(centre - half, 4), round(centre + half, 4)]


def is_error(record: dict, t: float) -> bool:
    if record["rule"] == "exact":
        return record["error"]
    return record["confidence"] >= t  # 不利な側: 低い行は誤りでない、低くない行は誤り


def page_share(pages: list[dict], t: float) -> dict:
    known = [p for p in pages if is_low(p, t) is not None]
    low = sum(bool(is_low(p, t)) for p in known)
    return {"pages": len(known), "low_pages": low, "c": low / len(known) if known else None,
            "unknown_pages": len(pages) - len(known), "c_upper": (wilson(low, len(known), Z_ONE_SIDED) or [None, None])[1]}


def measure(data: dict, t: float) -> dict:
    counted = [r for r in data["lines"] if r["rule"] != "excluded"]
    low = [r for r in counted if r["confidence"] < t]
    errors = [r for r in counted if is_error(r, t)]
    caught = [r for r in low if is_error(r, t)]
    missed = len(data["missed"])
    every = page_share(data["pages"], t)
    auto = page_share([p for p in data["pages"] if p["kind"] in OCR_KINDS], t)
    return {"threshold": t, "lines": len(counted), "low": len(low), "errors": len(errors) + missed,
            "missed": missed, "caught": len(caught),
            "a": len(caught) / len(low) if low else None,
            "b": len(caught) / (len(errors) + missed) if errors or missed else None,
            "a_lower": (wilson(len(caught), len(low), Z_ONE_SIDED) or [None])[0],
            "b_lower": (wilson(len(caught), len(errors) + missed, Z_ONE_SIDED) or [None])[0],
            "always": every, "auto": auto,
            "pessimistic_lines": sum(r["rule"] == "pessimistic" for r in counted)}


def points_ok(row: dict, margin: float = 0.0) -> bool:
    """点の値で (a)〜(c) を満たすか。auto で OCR するページがなければ、always だけで判断する。"""
    if row["a"] is None or row["b"] is None or row["always"]["c"] is None:
        return False
    shares = [row["always"]["c"]] + ([row["auto"]["c"]] if row["auto"]["pages"] else [])
    return row["a"] >= 0.5 + margin and row["b"] >= 0.8 + margin and all(c <= 0.2 - margin for c in shares)


def describe(data: dict) -> dict:
    counted = [r for r in data["lines"] if r["rule"] != "excluded"]
    exact = [r for r in counted if r["rule"] == "exact" and r["shape"] == "1:1"]
    chars = sum(r["truth_chars"] for r in exact)
    shapes: dict = {}
    for r in data["lines"]:
        shapes[r["shape"]] = shapes.get(r["shape"], 0) + 1
    return {"pages": len(data["pages"]), "ocr_lines": len(data["lines"]), "counted": len(counted),
            "one_to_one": len(exact), "one_to_one_errors": sum(r["error"] for r in exact),
            "cer_one_to_one": round(sum(r["distance"] for r in exact) / chars, 4) if chars else None,
            "missed": len(data["missed"]), "pessimistic": sum(r["rule"] == "pessimistic" for r in counted),
            "excluded": sum(r["rule"] == "excluded" for r in data["lines"]), "shapes": shapes}


def subset(data: dict, keep) -> dict:
    return {key: [x for x in values if keep(x)] for key, values in data.items()}


def line_rows(data: dict, stratum: str) -> list[dict]:
    """OCR の行ごとの数値。公開の PDF の本文は書かない。"""
    rows = []
    for r in data["lines"]:
        row = {k: r.get(k) for k in ("name", "page", "variant", "kind", "pdf_sha256", "shape", "rule", "excluded",
                                       "confidence", "distance", "error", "truth_chars")}
        if stratum == "synthetic":
            row.update(truth_text=r["truth_text"], ocr_text=r["ocr_text"])
        rows.append(row)
    for m in data["missed"]:
        row = {k: m.get(k) for k in ("name", "page", "variant", "kind", "pdf_sha256", "shape", "truth_chars")}
        row["rule"] = "missed"
        if stratum == "synthetic":
            row["truth_text"] = m["truth_text"]
        rows.append(row)
    return rows


def write(name: str, value) -> None:
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / name).write_bytes((json.dumps(value, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))


def short(row: dict) -> str:
    f = lambda v: "-" if v is None else f"{v:.3f}"  # noqa: E731
    return (f"t={row['threshold']:.2f} 低い行 {row['low']} 誤り {row['errors']}（読み落とし {row['missed']}） "
            f"捕えた {row['caught']} (a) {f(row['a'])} (b) {f(row['b'])} "
            f"(c) always {f(row['always']['c'])}（{row['always']['low_pages']}/{row['always']['pages']}） "
            f"auto {f(row['auto']['c'])}（{row['auto']['low_pages']}/{row['auto']['pages']}）")


def main() -> None:
    mode = sys.argv[1]
    if mode == "dev":
        data = collect("dev")
        for stratum, d in data.items():
            if not d["pages"]:
                continue
            print(stratum, json.dumps(describe(d), ensure_ascii=False))
            for r in d["lines"]:
                if r["shape"] != "1:1":
                    print("  1:1 でない", r["page"], r["shape"], r["rule"], r["confidence"], repr(r["line_text"][:40]))
            for t in (0.1, 0.3, 0.5, 0.7, 0.9):
                print(" ", short(measure(d, t)))
        return
    if mode == "tuning":
        data = collect("tuning")
        rows = {s: [measure(d, t) for t in GRID] for s, d in data.items()}
        chosen, used_margin, candidates = None, None, []
        for margin in (0.05, 0.0):
            candidates = [t for i, t in enumerate(GRID) if all(points_ok(rows[s][i], margin) for s in rows)]
            if candidates:
                chosen = candidates[(len(candidates) - 1) // 2]  # 中央値（偶数なら小さい方）
                used_margin = margin
                break
        write("tuning.json", {"chosen": chosen, "margin": used_margin, "candidates": candidates,
                              "describe": {s: describe(d) for s, d in data.items()}, "grid": rows})
        for s, d in data.items():
            write(f"tuning-lines-{s}.json", line_rows(d, s))
        print("選んだ閾値:", chosen, "余裕:", used_margin, "候補:", candidates)
        for s, d in data.items():
            print(s, json.dumps(describe(d), ensure_ascii=False))
            for t in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
                print(" ", short(rows[s][GRID.index(t)]))
        return
    if mode == "evaluation":
        tuning = json.loads((RESULTS / "tuning.json").read_bytes().decode("utf-8"))
        if tuning["chosen"] is None:
            raise SystemExit("選ぶ資料で閾値が決まっていない。確かめる資料は測らない")
        if (RESULTS / "evaluation.json").exists():
            raise SystemExit("確かめる資料は、もう測った（1 回だけ）")
        t = tuning["chosen"]
        data = collect("evaluation")
        verdict = {}
        for s, d in data.items():
            row = measure(d, t)
            bounds = (row["a_lower"] is not None and row["a_lower"] >= 0.5 and row["b_lower"] is not None
                      and row["b_lower"] >= 0.8 and row["always"]["c_upper"] is not None
                      and row["always"]["c_upper"] <= 0.2
                      and (row["auto"]["c_upper"] is not None and row["auto"]["c_upper"] <= 0.2))
            enough = (row["low"] >= MIN_COUNT and row["errors"] >= MIN_COUNT
                      and row["always"]["pages"] >= MIN_COUNT and row["auto"]["pages"] >= MIN_COUNT)
            leave_one_out = None
            if s == "synthetic":
                names = sorted({p["name"] for p in d["pages"]})
                leave_one_out = {n: points_ok(measure(subset(d, lambda x, n=n: x["name"] != n), t)) for n in names}
            passed = points_ok(row) and bounds and enough and (leave_one_out is None or all(leave_one_out.values()))
            by = "variant" if s == "synthetic" else "name"
            groups = sorted({p[by] for p in d["pages"]})
            verdict[s] = {"row": row, "points": points_ok(row), "bounds": bounds, "enough": enough,
                          "leave_one_out": leave_one_out, "pass": passed, "describe": describe(d),
                          "by": {g: measure(subset(d, lambda x, g=g: x[by] == g), t) for g in groups}}
        write("evaluation.json", {"threshold": t, "verdict": verdict,
                                  "grid": {s: [measure(d, x) for x in GRID] for s, d in data.items()}})
        for s, d in data.items():
            write(f"evaluation-lines-{s}.json", line_rows(d, s))
        for s, v in verdict.items():
            print(s, "合格" if v["pass"] else "不合格", "点", v["points"], "区間", v["bounds"], "数", v["enough"],
                  "1 つ除く", v["leave_one_out"], short(v["row"]))
        return
    raise SystemExit(f"不明なモード: {mode}")


if __name__ == "__main__":
    main()
