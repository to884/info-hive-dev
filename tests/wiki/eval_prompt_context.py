#!/usr/bin/env python3
"""プロンプトのフック（ADR-0032）のゲートを、評価のデータで測る。

使い方:
    python tests/wiki/eval_prompt_context.py [--split dev|test|all] [--show] [--gate] [--set NAME=VALUE ...]

評価のデータは tests/wiki/fixtures/prompt_context/prompts.json にある。題材の wiki は、データに書いた
コミットの wiki/ を git archive で一時ディレクトリに取り出して使う（wiki が育っても結果が変わらない）。
--set は wiki_prompt_context の定数を、その回だけ書き換える（しきい値を探すため）。
--gate を付けると、合否の基準（ADR-0032）に届かないときに終了コード 1 で終わる。

git の履歴が要るので、手元の道具として使う（CI の浅い取得では動かない）。
"""
from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "info-hive-wiki" / "skills" / "info-hive" / "scripts"
DATA = Path(__file__).resolve().parent / "fixtures" / "prompt_context" / "prompts.json"
sys.path.insert(0, str(SCRIPTS))

import wiki_initialized  # noqa: E402
import wiki_prompt_context as context  # noqa: E402

# 合否の基準（ADR-0032）
CRITERIA = {"N1_fire_max": 0.05, "N2_fire_max": 0.0, "N3_fire_max": 0.05, "precision_min": 0.8, "recall_min": 0.4}


def split_of(position: int) -> str:
    return "test" if position % 5 in (3, 4) else "dev"


def materialize(commit: str, target: Path) -> Path:
    """コミットの wiki/ を target の下に取り出し、プロジェクトのルートとして使う target を返す。"""
    archive = subprocess.run(["git", "-C", str(ROOT), "archive", "--format=tar", commit, "wiki"],
                             capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(target, filter="data")
    return target


def run(args) -> dict:
    data = json.loads(DATA.read_bytes().decode("utf-8"))
    for item in args.set or []:
        name, _, value = item.partition("=")
        current = getattr(context, name)
        setattr(context, name, type(current)(value))
    sets = {
        "P": [(i, e["prompt"], set(e["relevant"])) for i, e in enumerate(data["P"])],
        "N1": [(i, p, set()) for i, p in enumerate(data["N1"])],
        "N2": [(i, p, set()) for i, p in enumerate(data["N2"])],
        "N3": [(i, p, set()) for i, p in enumerate(data["N3"])],
    }
    report = {"split": args.split, "sets": {}, "misses": [], "fires": [], "wrong": []}
    times = []
    with tempfile.TemporaryDirectory() as tmp:
        project = materialize(data["wiki_commit"], Path(tmp))

        def is_wiki(root) -> bool:
            return wiki_initialized.check(root) is None

        for name, items in sets.items():
            counts = {"n": 0, "fired": 0, "hit": 0, "shown": 0, "relevant_shown": 0}
            for position, prompt, relevant in items:
                if args.split != "all" and split_of(position) != args.split:
                    continue
                hook_input = {"prompt": prompt, "cwd": str(project), "hook_event_name": "UserPromptSubmit"}
                started = time.monotonic()
                picked = context.select(hook_input, env={}, is_wiki=is_wiki, deadline=started + 30)
                rendered = context.render(picked.chosen, picked.roots) if picked else None
                times.append(time.monotonic() - started)
                chosen = rendered.shown if rendered else []
                slugs = [c.page.slug for c in chosen]
                counts["n"] += 1
                if chosen:
                    counts["fired"] += 1
                if name == "P":
                    for cand in chosen:
                        row = report.setdefault("kinds", {}).setdefault(cand.kind, {"right": 0, "wrong": 0})
                        row["right" if cand.page.slug in relevant else "wrong"] += 1
                    good = [s for s in slugs if s in relevant]
                    counts["shown"] += len(slugs)
                    counts["relevant_shown"] += len(good)
                    if good:
                        counts["hit"] += 1
                    else:
                        report["misses"].append({"prompt": prompt, "shown": slugs})
                    bad = [(c.page.slug, c.kind, c.reason) for c in chosen if c.page.slug not in relevant]
                    if bad:
                        report["wrong"].append({"prompt": prompt, "wrong": bad})
                elif chosen:
                    report["fires"].append({"set": name, "prompt": prompt[:60],
                                            "shown": [(c.page.slug, c.kind, c.reason) for c in chosen]})
            report["sets"][name] = counts
    p = report["sets"]["P"]
    report["metrics"] = {
        "recall": round(p["hit"] / p["n"], 3) if p["n"] else None,
        "precision": round(p["relevant_shown"] / p["shown"], 3) if p["shown"] else None,
        **{f"{k}_fire": round(v["fired"] / v["n"], 3) if v["n"] else None
           for k, v in report["sets"].items() if k != "P"},
        "max_ms": round(max(times) * 1000, 1) if times else None,
    }
    m = report["metrics"]
    report["passed"] = bool(
        m["recall"] is not None and m["recall"] >= CRITERIA["recall_min"]
        and (m["precision"] or 0) >= CRITERIA["precision_min"]
        and all((m[f"{k}_fire"] or 0) <= CRITERIA[f"{k}_fire_max"] for k in ("N1", "N2", "N3"))
    )
    return report


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--split", choices=("dev", "test", "all"), default="dev")
    parser.add_argument("--show", action="store_true", help="外れ、誤り、発火を並べる")
    parser.add_argument("--gate", action="store_true", help="合否の基準に届かなければ終了コード 1")
    parser.add_argument("--set", action="append", help="NAME=VALUE。wiki_prompt_context の定数を書き換える")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = run(args)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"split": report["split"], "metrics": report["metrics"], "kinds": report.get("kinds"),
                          "passed": report["passed"]}, ensure_ascii=False))
        if args.show:
            for key in ("misses", "wrong", "fires"):
                print(f"--- {key} ({len(report[key])})")
                for row in report[key]:
                    print(json.dumps(row, ensure_ascii=False))
    if args.gate and not report["passed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
