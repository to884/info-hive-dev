"""元の条件5と同じ配置を、印と正誤の単位別件数から採点する。"""

from collections import defaultdict
from functools import cache
import itertools
import math
import statistics

from scipy.stats import t as student


@cache
def critical(n):
    return float(student.ppf(0.95, n - 1))


def cluster(pairs, upper):
    n = len(pairs)
    total = sum(x for _, x in pairs)
    if n < 2 or not total:
        return None
    ratio = sum(y for y, _ in pairs) / total
    variance = n / (n - 1) * sum((y - ratio * x) ** 2 for y, x in pairs) / total ** 2
    half = critical(n) * math.sqrt(variance)
    return round(float(ratio + half if upper else ratio - half), 4)


def unit_mean(pairs, upper):
    values = [y / x for y, x in pairs if x]
    n = len(values)
    if n < 2:
        return None, None
    mean = statistics.fmean(values)
    half = critical(n) * statistics.stdev(values) / math.sqrt(n)
    return round(mean, 4), round(mean + half if upper else mean - half, 4)


def measure(units, fixed):
    rows = tuple(units.values())
    flags = [r[1] for r in rows]
    caught_counts = [r[2] for r in rows]
    error_counts = [r[3] for r in rows]
    fp = [n - y for n, y in zip(flags, caught_counts)]
    tn_fp = [r[0] - r[3] for r in rows]
    flagged, caught, errors, correct, false = map(sum, (flags, caught_counts, error_counts, tn_fp, fp))
    a_pairs, b_pairs, c_pairs = (tuple(zip(m, n)) for m, n in ((caught_counts, flags),
                                                              (caught_counts, error_counts), (fp, tn_fp)))
    a_mean, a_low = unit_mean(a_pairs, False)
    b_mean, b_low = unit_mean(b_pairs, False)
    c_mean, c_high = unit_mean(c_pairs, True)
    recall_values = [a / b for a, b in b_pairs if b]
    return {**fixed, "flagged": flagged, "errors": errors, "correct": correct, "caught": caught, "false": false,
            "units": len(rows), "a": caught / flagged if flagged else None, "b": caught / errors if errors else None,
            "c": false / correct if correct else None, "a_lower": cluster(a_pairs, False),
            "b_lower": cluster(b_pairs, False), "c_upper": cluster(c_pairs, True),
            "units_a": sum(bool(n) for n in flags), "units_b": len(recall_values), "units_c": sum(bool(n) for n in tn_fp),
            "a_mean": a_mean, "a_mean_lower": a_low, "b_mean": b_mean, "b_mean_lower": b_low,
            "c_mean": c_mean, "c_mean_upper": c_high,
            "b_mean_raw": math.fsum(recall_values) / len(recall_values) if recall_values else None}


def robust(data, original, max_assignments=1000000, public_margin=False):
    rows, missed = data["lines"], data["missed"]
    groups = defaultdict(int)
    aggregate = {}
    eye = 0
    unknown = []
    for row in rows:
        unit, flag = row["unit"], bool(row["reasons"])
        record = aggregate.setdefault(unit, [0, 0, 0, 0])
        record[0] += 1
        record[1] += flag
        eye += bool(row.get("eye"))
        if row["rule"] != "exact":
            groups[unit, flag] += 1
            unknown.append(row)
        else:
            record[2] += flag and row["error"]
            record[3] += row["error"]
    for row in missed:
        aggregate.setdefault(row["unit"], [0, 0, 0, 0])
    grouped = sorted(groups.items())
    combinations = math.prod(n + 1 for _, n in grouped)
    result = {"unresolved": len(unknown), "assignments": combinations, "checked": 0, "pass": False, "gate": False}
    if combinations > max_assignments:
        return {**result, "measurable": False, "reason": "assignment-limit"}
    identities = {(r["unit"], r["key"], r["line_index"]) for r in rows}
    if len(identities) != len(rows):
        raise ValueError("採点する行の識別子が重複している")
    missing_share = len(missed) / data["truth_lines"] if data.get("truth_lines") else None
    fixed = {"pessimistic": 0, "eye": eye, "missed": len(missed), "missed_share": missing_share}
    affected = tuple((aggregate[unit], flag, n) for (unit, flag), n in grouped)
    gate = True
    for counts in itertools.product(*(range(n + 1) for _, _, n in affected)):
        for count, (row, flag, _) in zip(counts, affected):
            row[2] += count * flag
            row[3] += count
        row = measure(aggregate, fixed)
        judged = original.verdict(row)
        checked_gate = judged["pass"] and (not public_margin or (row["b"] >= .87 and row["b_mean_raw"] >= .87))
        gate &= checked_gate
        result["checked"] += 1
        if not judged["pass"]:
            errors = [{"unit": key, "flagged": flagged, "count": count, "total": n}
                      for count, ((key, flagged), n) in zip(counts, grouped)]
            return {**result, "measurable": True, "counterexample": {"errors": errors, "row": row, "verdict": judged}}
        for count, (entry, flag, _) in zip(counts, affected):
            entry[2] -= count * flag
            entry[3] -= count
    return {**result, "measurable": True, "pass": True, "gate": gate}
