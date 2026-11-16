"""RapidOCR の読みとの食い違いを、今の行の印に足したときの値を数える（試し。開発用の資料だけを使う）。

使い方（rag の依存の環境で動かす）: python -X utf8 scripts/probe_rapid_analyze.py
開発用の資料は、選ぶ資料（tuning）と、2 回目に使い切った確かめる資料（evaluation）である。数え方は score_v2 と同じ
（不利な側の行は、印があれば誤りでない、なければ誤り）。行で重みを付けた比と、単位ごとの比の平均の両方を出す。
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import score_v2  # noqa: E402
from rag_ocr_flags import normalize  # noqa: E402
from score import CORPUS  # noqa: E402

# 2 つの認識器の読みを比べるときだけ、見た目の同じ文字をそろえる（カタカナと漢字、長音とダッシュ）
LOOKALIKE = {"卜": "ト", "口": "ロ", "力": "カ", "工": "エ", "夕": "タ", "二": "ニ", "八": "ハ", "才": "オ",
             "一": "ー", "-": "ー", "へ": "ヘ", "べ": "ベ", "ぺ": "ペ", "り": "リ"}


def skeleton(text: str) -> str:
    return "".join(LOOKALIKE.get(c, c) for c in normalize(text))


def attach(data: dict) -> None:
    cache = {}
    for r in data["lines"]:
        if r["key"] not in cache:
            path = CORPUS / "probe" / "rapid" / f"{r['key']}.json"
            ocr2 = CORPUS / "ocr2" / f"{r['key']}.json"
            record = json.loads(path.read_bytes().decode("utf-8"))
            import hashlib
            if record["ocr2_sha256"] != hashlib.sha256(ocr2.read_bytes()).hexdigest():
                raise SystemExit(f"RapidOCR の読みの出典が、今の OCR の結果と違う: {r['key']}")
            cache[r["key"]] = record["reads"]
        read = cache[r["key"]][r["line_index"]]
        r["rapid"] = read
        text = json.loads((CORPUS / "ocr2" / f"{r['key']}.json").read_bytes().decode("utf-8"))["lines"][r["line_index"]]["text"] \
            if "primary" not in r else r["primary"]
        r["primary"] = text


SIGNALS = {
    "今の印": lambda r: bool(r["reasons"]),
    "今の印 + RapidOCR": lambda r: bool(r["reasons"]) or (r["rapid"] is not None and skeleton(r["rapid"]["text"]) != skeleton(r["primary"])),
    "今の印 + RapidOCR（確信度 0.95 未満）": lambda r: bool(r["reasons"]) or (
        r["rapid"] is not None and skeleton(r["rapid"]["text"]) != skeleton(r["primary"]) and (r["confidence"] or 0) < 0.95),
    "今の印 + RapidOCR（RapidOCR の点 0.99 未満）": lambda r: bool(r["reasons"]) or (
        r["rapid"] is not None and skeleton(r["rapid"]["text"]) != skeleton(r["primary"])
        and (r["rapid"]["score"] is None or r["rapid"]["score"] < 0.99)),
}


def symbol_diff(a: str, b: str) -> bool:
    """2 つの読みの違いに、英数字か記号（文字でも数字でもない文字）が関わるか。漢字とかなだけの違いは数えない。"""
    import difflib

    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        changed = a[i1:i2] + b[j1:j2]
        if any((c.isascii() and c.isalnum()) or not c.isalnum() for c in changed):
            return True
    return False


def rapid_symbol(r) -> bool:
    return r["rapid"] is not None and symbol_diff(skeleton(r["primary"]), skeleton(r["rapid"]["text"]))


SIGNALS["今の印 + RapidOCR（英数字か記号の違いだけ）"] = lambda r: bool(r["reasons"]) or rapid_symbol(r)
SIGNALS["今の印 + RapidOCR（英数字か記号の違い、または確信度 0.95 未満の違い）"] = lambda r: bool(r["reasons"]) or rapid_symbol(r) or (
    r["rapid"] is not None and skeleton(r["rapid"]["text"]) != skeleton(r["primary"]) and (r["confidence"] or 0) < 0.95)


def added_symbol(a: str, b: str, edges: bool) -> bool:
    """RapidOCR の読み b が、製品の読み a にない英数字か記号を足すか置き換えたか（b が文字を落としただけは数えない）。

    edges が真なら、行の端に "I" か "|" を 1 つ足しただけの違い（行の枠の線を読んだもの）も数えない。
    """
    import difflib

    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag in ("equal", "delete"):
            continue
        added = b[j1:j2]
        if edges and tag == "insert" and added in ("I", "|") and (j1 == 0 or j2 == len(b)):
            continue
        if any((c.isascii() and c.isalnum()) or not c.isalnum() for c in added + a[i1:i2]):
            return True
    return False


SIGNALS["今の印 + RapidOCR（足した英数字か記号）"] = lambda r: bool(r["reasons"]) or (
    r["rapid"] is not None and added_symbol(skeleton(r["primary"]), skeleton(r["rapid"]["text"]), False))
SIGNALS["今の印 + RapidOCR（足した英数字か記号、端の I は除く）"] = lambda r: bool(r["reasons"]) or (
    r["rapid"] is not None and added_symbol(skeleton(r["primary"]), skeleton(r["rapid"]["text"]), True))


def measure(data: dict, signal) -> str:
    units: dict[str, list[int]] = {}
    for r in data["lines"]:
        flagged = signal(r)
        error = r["error"] if r["rule"] == "exact" else not flagged
        u = units.setdefault(r["unit"], [0, 0, 0, 0, 0])
        u[0] += flagged
        u[1] += error
        u[2] += flagged and error
        u[3] += flagged and not error
        u[4] += not error
    f, e, c, fa, ok = (sum(u[i] for u in units.values()) for i in range(5))
    b_mean = statistics.fmean(u[2] / u[1] for u in units.values() if u[1])
    return f"(a) {c / f:.3f} (b) {c / e:.3f}（単位の平均 {b_mean:.3f}） (c) {fa / ok:.3f}"


def main() -> None:
    for side in ("tuning", "evaluation"):
        for stratum, data in score_v2.collect(side).items():
            attach(data)
            print(side, stratum)
            for name, signal in SIGNALS.items():
                print(f"  {name}: {measure(data, signal)}")


if __name__ == "__main__":
    main()
