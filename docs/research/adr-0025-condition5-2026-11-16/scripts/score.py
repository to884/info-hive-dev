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
from rag_config import OCR_CONFIDENCE_REVISION  # noqa: E402


def is_low(entry: dict, threshold: float) -> bool | None:
    """1 回目の測定のときの製品の決まり（rag_review.is_low。行の印に見直して is_flagged になった）。

    確信度の数え方の版が違うか、最小値がなければ None（不明）。最小値が閾値より低ければ低い。
    """
    if entry.get("confidence_revision") != OCR_CONFIDENCE_REVISION:
        return None
    minimum = entry.get("confidence_min")
    if minimum is None:
        return None
    return minimum < threshold

CORPUS = BENCH / "corpus"
RESULTS = BENCH / "results"
GRID = [round(0.01 * i, 2) for i in range(1, 100)]
MIN_COUNT = 20
# 3 回目のレビューの 1（限界が、比のそろった単位で点の値と同じになる）を直して、4 回目のレビューを通したら真にする
BOUND_FIXED = False
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
    """読む順に並べる。横書きは上から下、同じ高さは左から右。縦書きは右から左、同じ列は上から下。

    入力の順によらない全順序にするため、先に行を帯（横書きは高さの帯、縦書きは列）にまとめる。行の中心の順に
    見ていき、今の帯の範囲と、行の高さ（縦書きは幅）の半分以上が重なれば同じ帯に入れ、帯の範囲を広げる。
    帯の中は、横書きは左端、縦書きは上端の順に並べる。同じ値は、箱と本文で決める。
    """
    if vertical:
        across = lambda b: (-b[2], -b[0])  # noqa: E731  列を右から並べるための、横の範囲（符号を返して右を先に）
        along = lambda b: b[1]  # noqa: E731
    else:
        across = lambda b: (b[1], b[3])  # noqa: E731  高さの範囲
        along = lambda b: b[0]  # noqa: E731

    def tie(line):
        return (tuple(line["box"]), str(line.get("text", "")))

    ordered = sorted(lines, key=lambda x: ((across(x["box"])[0] + across(x["box"])[1]) / 2, along(x["box"]), tie(x)))
    bands: list[list] = []
    for line in ordered:
        lo, hi = across(line["box"])
        if bands:
            band_lo, band_hi, members = bands[-1]
            inter = min(hi, band_hi) - max(lo, band_lo)
            if inter >= 0.5 * max(1e-9, min(hi - lo, band_hi - band_lo)):
                bands[-1] = [min(lo, band_lo), max(hi, band_hi), members + [line]]
                continue
        bands.append([lo, hi, [line]])
    return [line for _, _, members in bands for line in sorted(members, key=lambda x: (along(x["box"]), tie(x)))]


def page_records(truth_lines: list[dict], ocr_lines: list[dict], stratum: str) -> tuple[list[dict], list[dict]]:
    """OCR の行ごとの記録と、読み落とした正解の行の記録を返す。

    OCR の行の rule は、誤りの決め方: "exact"（error が決まっている）、"pessimistic"（低い行は誤りでない、
    低くない行は誤り。閾値で決まる）、"excluded"（正解から除いた行と直接つながる。数えない）。
    除いた正解の行を含むまとまりの、その行と直接つながらない OCR の行は、正解が分からないので "pessimistic" にする。
    """
    nodes = [("t", i) for i in range(len(truth_lines))] + [("o", j) for j in range(len(ocr_lines))]
    parent = {node: node for node in nodes}

    def find(node):
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    direct_excluded = set()  # 除いた正解の行と直接つながる OCR の行
    for j, o in enumerate(ocr_lines):
        for i, t in enumerate(truth_lines):
            if joined(o["box"], t["box"]):
                parent[find(("o", j))] = find(("t", i))
                if t.get("excluded"):
                    direct_excluded.add(j)
    groups: dict = {}
    for node in nodes:
        groups.setdefault(find(node), []).append(node)
    records, missed = [], []
    for members in groups.values():
        truth = [truth_lines[i] for kind, i in members if kind == "t"]
        ocr_ids = [j for kind, j in members if kind == "o"]
        ocr = [ocr_lines[j] for j in ocr_ids]
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
        for j, line in zip(ocr_ids, ocr):
            record = {"shape": shape, "confidence": line["confidence"], "distance": dist,
                      "truth_chars": len(truth_text), "truth_text": truth_text, "ocr_text": ocr_text,
                      "line_text": normalize(line["text"]), "line_index": j}
            if j in direct_excluded:
                record.update(rule="excluded", excluded=excluded)
            elif excluded:
                record.update(rule="pessimistic")  # まとまりの正解の一部が分からない
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
            if ocr["pdf_sha256"] != truth["pdf_sha256"]:
                raise SystemExit(f"OCR の結果の PDF が正解と違う: {path.name}（OCR し直す）")
            ocr_lines = [{**line, "box": [line["box"][0], line["box"][1], line["box"][0] + line["box"][2],
                                          line["box"][1] + line["box"][3]]} for line in ocr["lines"]]
            label = {"name": truth["name"], "page": page["page"], "variant": page.get("variant"),
                     "kind": page["kind"], "pdf_sha256": ocr["pdf_sha256"], "stratum": stratum}
            records, missed = page_records(page["lines"], ocr_lines, stratum)
            found[stratum]["lines"] += [{**label, **r} for r in records]
            found[stratum]["missed"] += [{**label, **m} for m in missed]
            found[stratum]["pages"].append({**label, "confidence_min": ocr["confidence_min"],
                                            "confidence_revision": ocr["confidence_revision"],
                                            "lines": len(ocr_lines)})
    return found


def cluster_bound(pairs: list[tuple[float, float]], side: str) -> float | None:
    """単位（合成は原稿、公開はページ）ごとの (分子, 分母) から、比の片側 95% の限界を返す。

    比 R = Σy / Σx の分散を、単位ごとの残差 y − R·x で線形化して見積もり（n/(n−1) を掛ける）、自由度 n − 1 の
    t 分布の 95% 点を使う。分母が 0 の単位も数える。単位が 2 つ未満なら None。
    """
    from scipy.stats import t as student

    n = len(pairs)
    total_x = sum(x for _, x in pairs)
    if n < 2 or total_x == 0:
        return None
    ratio = sum(y for y, _ in pairs) / total_x
    variance = n / (n - 1) * sum((y - ratio * x) ** 2 for y, x in pairs) / total_x ** 2
    half = float(student.ppf(0.95, n - 1)) * math.sqrt(variance)
    return round(float(ratio - half if side == "lower" else ratio + half), 4)


def cluster_of(record: dict) -> str:
    return record["name"] if record["stratum"] == "synthetic" else f"{record['name']}-p{record['page']}"


def is_error(record: dict, t: float) -> bool:
    if record["rule"] == "exact":
        return record["error"]
    return record["confidence"] >= t  # 不利な側: 低い行は誤りでない、低くない行は誤り


def page_share(pages: list[dict], t: float) -> dict:
    known = [p for p in pages if is_low(p, t) is not None]
    low = sum(bool(is_low(p, t)) for p in known)
    clusters: dict = {}
    for p in known:
        y, x = clusters.get(cluster_of(p), (0, 0))
        clusters[cluster_of(p)] = (y + bool(is_low(p, t)), x + 1)
    return {"pages": len(known), "low_pages": low, "c": low / len(known) if known else None,
            "unknown_pages": len(pages) - len(known), "clusters": len(clusters),
            "c_upper": cluster_bound(list(clusters.values()), "upper")}


def measure(data: dict, t: float) -> dict:
    counted = [r for r in data["lines"] if r["rule"] != "excluded"]
    low = [r for r in counted if r["confidence"] < t]
    errors = [r for r in counted if is_error(r, t)]
    caught = [r for r in low if is_error(r, t)]
    missed = len(data["missed"])
    every = page_share(data["pages"], t)
    auto = page_share([p for p in data["pages"] if p["kind"] in OCR_KINDS], t)
    # 単位ごとの (分子, 分母)。OCR したページのある単位は、行がなくても (0, 0) として数える
    units = {cluster_of(p): {"low": 0, "caught": 0, "errors": 0} for p in data["pages"]}
    for r in counted:
        u = units[cluster_of(r)]
        u["low"] += r["confidence"] < t
        u["caught"] += r["confidence"] < t and is_error(r, t)
        u["errors"] += is_error(r, t)
    for m in data["missed"]:
        units[cluster_of(m)]["errors"] += 1
    return {"threshold": t, "lines": len(counted), "low": len(low), "errors": len(errors) + missed,
            "missed": missed, "caught": len(caught), "clusters": len(units),
            "a": len(caught) / len(low) if low else None,
            "b": len(caught) / (len(errors) + missed) if errors or missed else None,
            "a_lower": cluster_bound([(u["caught"], u["low"]) for u in units.values()], "lower"),
            "b_lower": cluster_bound([(u["caught"], u["errors"]) for u in units.values()], "lower"),
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
            f"auto {f(row['auto']['c'])}（{row['auto']['low_pages']}/{row['auto']['pages']}） "
            f"限界 (a) {f(row['a_lower'])} (b) {f(row['b_lower'])} (c) {f(row['always']['c_upper'])}")


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
        if not BOUND_FIXED:
            raise SystemExit("限界の数え方（3 回目のレビューの 1）を直すまで、確かめる資料は測らない")
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
            passed = points_ok(row) and bounds and enough
            by = "variant" if s == "synthetic" else "name"
            groups = sorted({p[by] for p in d["pages"]})
            verdict[s] = {"row": row, "points": points_ok(row), "bounds": bounds, "enough": enough,
                          "pass": passed, "describe": describe(d),
                          "by": {g: measure(subset(d, lambda x, g=g: x[by] == g), t) for g in groups}}
        write("evaluation.json", {"threshold": t, "verdict": verdict,
                                  "grid": {s: [measure(d, x) for x in GRID] for s, d in data.items()}})
        for s, d in data.items():
            write(f"evaluation-lines-{s}.json", line_rows(d, s))
        for s, v in verdict.items():
            print(s, "合格" if v["pass"] else "不合格", "点", v["points"], "区間", v["bounds"], "数", v["enough"],
                  short(v["row"]))
        return
    raise SystemExit(f"不明なモード: {mode}")


if __name__ == "__main__":
    main()
