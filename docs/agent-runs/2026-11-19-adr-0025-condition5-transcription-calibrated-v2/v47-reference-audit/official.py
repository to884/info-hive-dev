"""固定した二系統の監査を、事前に確認した配布と出典の手順で実行する。"""

import argparse
from collections import Counter
from pathlib import Path
import sys

import audit

HERE, core = audit.HERE, audit.core
FINAL = HERE / "preflight-final.json"
REVIEW = HERE / "review-followup-opus.md"
tested_inputs = audit.inputs


def dependencies():
    parent = HERE.parent
    paths = (Path(__file__), HERE / "preflight.py", HERE / "protocol.md", core.PLAN, REVIEW,
             HERE / "audit.py", HERE / "run.py", HERE / "strict_points.py", audit.PREFLIGHT,
             Path(audit.previous.__file__), Path(audit.packets.__file__), Path(core.__file__),
             audit.draft.edge_file, audit.draft.bullet_file,
             parent / "v35-coordinate-pilot/ruler.py",
             parent / "v43-frame-rectangle-pilot/prepare.py", parent / "v40-frame-edge-pilot/prepare.py",
             parent / "v41-paragraph-bullets-pilot/prepare.py", parent / "v44-small-point-pixel-pilot/run.py",
             parent / "v24-physical-transcription-pilot/run.py")
    return {str(p.resolve()): core.sha(p) for p in paths}


def capacity(pools):
    """抽出する前に、母集団全体で必須画像が上限に収まることを寸法から確かめる。"""
    cards = audit.packets.old
    segments = cards.original.segments
    focus_segments = cards.layout.figure.v2.segments
    coverage = {}
    for side, rows in pools.items():
        counts, dimensions = Counter(), Counter()
        for row in rows:
            w, h = row["box"][2:]
            across, down = len(segments(3 * w)), len(segments(3 * h))
            mandatory = across * down + len(audit.required_supplements(row, "G01"))
            coords = across if row["allocation_axis"] == "x" else 0
            mandatory += coords
            if coords:
                mandatory += w <= 120 and 12 <= h <= 35
                if h <= 17:
                    # 450 DPIの座標への変換で端数が出る場合も上側の枚数を数える。
                    mandatory += len(focus_segments(3 * w + 2))
            excess = max(0, mandatory - audit.LIMIT)
            if 2 * excess > coords:
                raise ValueError("母集団に必須画像が上限に収まらない寸法がある")
            counts[mandatory] += 1
            dimensions["width"] = max(dimensions["width"], w)
            dimensions["height"] = max(dimensions["height"], h)
        coverage[side] = {"rows": sum(counts.values()), "mandatory_counts": counts,
                          "max_dimensions": dimensions}
    return coverage


def preflight():
    import preflight as dry

    if FINAL.exists():
        raise FileExistsError("確定した事前検査を上書きしない")
    if "Final Result: APPROVED" not in REVIEW.read_text(encoding="utf-8"):
        raise ValueError("修正後のOpusレビューが承認していない")
    related = dependencies()
    attachments, used = dry.check_packets()
    circles, proofs = dry.check_rounds()
    _, _, labels = core.methods()
    truth = labels / "public.json"
    _, flags = core.baseline.take_public_rows()
    coverage = capacity(core.baseline.populations(core.load(truth), flags))
    if related != dependencies():
        raise ValueError("事前検査の途中で実行する方法が変わった")
    related.update({str(p.resolve()): core.sha(p) for p in (*used, *proofs, truth)})
    core.save_once(FINAL, core.encoded({"scope": "development-only-before-sampling",
                                       "tested": attachments, "rounds": circles,
                                       "capacity": coverage, "inputs": related}))
    print(attachments, {side: v["rows"] for side, v in coverage.items()},
          {side: max(v["mandatory_counts"]) for side, v in coverage.items()}, flush=True)


def verify_preflight():
    evidence = core.load(FINAL)
    if (evidence["scope"] != "development-only-before-sampling"
            or any(evidence["inputs"].get(name) != value for name, value in dependencies().items())
            or any(core.sha(Path(name)) != value for name, value in evidence["inputs"].items())):
        raise ValueError("配布を試験した実行コードと最終の事前検査が結び付かない")
    return evidence


def inputs(plan, report, labels):
    evidence = verify_preflight()
    return tested_inputs(plan, report, labels) | evidence["inputs"] | {str(FINAL): core.sha(FINAL)}


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else None
    if action == "preflight":
        preflight()
        return
    if action is None or action in ("-h", "--help"):
        audit.main()
        return
    if action != "prepare":
        core.verify_methods()
        bound = core.load(core.LOCK)["inputs"]
        if (bound.get(str(Path(__file__).resolve())) != core.sha(Path(__file__))
                or bound.get(str(FINAL)) != core.sha(FINAL)):
            raise ValueError("正式の入口で作った固定がない")
    if action in ("initialize", "gpt", "claude"):
        cli = argparse.ArgumentParser(add_help=False)
        cli.add_argument("--sha256", required=True)
        args, _ = cli.parse_known_args(sys.argv[2:])
        audit.verify_delivery(args.sha256)
    audit.inputs = inputs
    audit.main()


if __name__ == "__main__":
    main()
