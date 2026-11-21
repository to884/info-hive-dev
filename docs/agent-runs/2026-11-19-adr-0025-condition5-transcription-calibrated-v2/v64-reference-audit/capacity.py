"""母集団全体で必須の固定画素が24画像に収まることを寸法から検査する。"""

from collections import Counter
from math import ceil

import render

audit = render.audit


def capacity(pools):
    cards = audit.packets.old
    segments = cards.original.segments
    focus_segments = cards.layout.figure.v2.segments
    result = {}
    for domain, rows in pools.items():
        mandatory_counts, paired_counts = Counter(), Counter()
        for row in rows:
            w, h = row["box"][2:]
            across, down = len(segments(3 * w)), len(segments(3 * h))
            # 両端の細部を数える。一枚に収まる場合も上界として二枚を取る。
            mandatory = across * down + len(audit.required_supplements(row, "G01")) + 2
            coords = across if row["allocation_axis"] == "x" else 0
            if coords:
                mandatory += coords + (w <= 120 and 12 <= h <= 35)
                if h <= 17:
                    mandatory += len(focus_segments(3 * w + 2))
                if render.narrow(row):
                    mandatory += 2
                if render.short_frame(row):
                    mandatory += 1
                if w >= 90 and h <= 35:
                    # 実際に帯が二本あるかに関わらず、追加する場合を数える。
                    mandatory += 1
                if w > 1200 and h <= 35:
                    mandatory += 1
            else:
                # 450 DPIへの変換と上下に付ける9画素の余白を含む上界。
                mandatory += ceil(ceil((3 * h + 24) / 220) / 5) + (h <= 120)
            excess = max(0, mandatory - audit.LIMIT)
            if 2 * excess > coords:
                raise ValueError("添付上限で必須画像を落とす寸法が母集団にある")
            mandatory_counts[mandatory] += 1
            paired_counts[excess] += 1
        result[domain] = {"rows": len(rows), "mandatory_counts": mandatory_counts,
                          "coordinate_pairs_to_fit": paired_counts}
    return result
