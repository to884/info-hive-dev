"""browse の書き出しと stop を、コマンドとして外から流し、失敗のないときの約束（設計の 9.1）を確かめる。

docs/plans/wiki-browse-structure-2026-11-11.md の 12 の 1 の段の道具である。実装の中に手を入れないので、直す前の
コード（0.10.0 から今の main まで）にも、直したあとのコードにも、同じに当てられる。口に手を入れる探索は、
browse_sweep.py が、直したあとの層に当てる。

確かめること（初期の状態のそれぞれで、手を入れない実行）:
- 世界の差分: 領分と、指した書き出し先の外が変わらない（browse_sandbox.world_same）。
- 止まるべき状態（browse の書き出しと確かめられない書き出し先、Wiki のルートと重なる書き出し先、名前そのものが
  リンクの書き出し先と領分）では、0 でなく終わり、書き出し先が変わらない。
- それ以外では、0 で終わり、書き出し先に一覧と index.html があり、次の実行も 0 で終わり、作業用に残りがない。
- stop: 領分の名前がリンクのとき、砂場が変わらない。

使い方:
    python -X utf8 tests/wiki/browse_blackbox.py [--quick] [--wiki <info-hive-wiki のパス>]
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

import browse_sandbox as bs  # noqa: E402


def run(script: Path, args, data_dir):
    env = dict(os.environ, INFO_HIVE_DATA_DIR=data_dir, PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
    p = subprocess.run([sys.executable, "-X", "utf8", "-B", str(script), *args], capture_output=True,
                       env=env, timeout=120, encoding="utf-8", errors="replace")
    return p.returncode, p.stdout, p.stderr


def key_fn(scripts: Path):
    sys.path.insert(0, str(scripts))
    import wiki_mcp_common  # noqa: PLC0415

    def key(wiki):
        return wiki_mcp_common.wiki_key(Path(os.path.realpath(wiki)))
    return key


def check_build(script, key, case):
    out_state, work_state, default = case
    sb = bs.Sandbox(out_state, work_state, default, key=key)
    label = f"{out_state}/{work_state}/{'default' if default else 'out'}"
    try:
        if sb.skipped:
            return label, None, [f"飛ばした: {sb.skipped}"]
        problems = []
        before_world, before_out = bs.world(sb), bs.tree(sb.out)
        args = ["build", sb.wiki] + ([] if default else ["--out", sb.out])
        rc, _out, err = run(script, args, sb.data)
        after_world = bs.world(sb)
        if not bs.world_same(sb, before_world, after_world):
            problems.append(f"書き出し先と領分の外が変わった: {bs.world_diff(sb, before_world, after_world)}")
        if sb.protected:
            if rc == 0:
                problems.append("止まるべき状態で 0 で終わった")
            if bs.tree(sb.out) != before_out:
                problems.append("止まるべき状態で、書き出し先が変わった")
            return label, rc, problems
        if rc != 0:
            problems.append(f"失敗のない実行が 0 で終わらなかった: {err.strip().splitlines()[-1:] }")
            return label, rc, problems
        t = bs.tree(sb.out) or {}
        if bs.MANIFEST not in t or "index.html" not in t:
            problems.append("0 で終わったのに、書き出し先に一覧か index.html がない")
        rc2, _o, err2 = run(script, args, sb.data)
        if rc2 != 0:
            problems.append(f"次の実行が 0 で終わらなかった: {err2.strip().splitlines()[-1:]}")
        elif os.path.isdir(sb.work):
            left = sorted(set(os.listdir(sb.work)) - {bs.WORK_MARKER, "build.lock"})
            if left and out_state != "gen+hardlink":
                problems.append(f"次の実行のあと、作業用に残りがある: {left}")
        final_world = bs.world(sb)
        if not bs.world_same(sb, before_world, final_world):
            problems.append(f"次の実行で、書き出し先と領分の外が変わった: {bs.world_diff(sb, before_world, final_world)}")
        return label, rc, problems
    finally:
        sb.close()


def check_stop(script, key, state):
    sb = bs.Sandbox(state if state in bs.ROOT_LINK else "absent", "asis", True, key=key)
    try:
        if sb.skipped:
            return f"stop {state}", None, [f"飛ばした: {sb.skipped}"]
        if state == "state-link":
            target = os.path.join(sb.root, "elsewhere-state")
            bs.write(os.path.join(target, bs.SERVER_MARKER), b"A")
            bs.write(os.path.join(target, "server.json"), b'{"instance": "x", "owner": "A"}')
            bs.junction(sb.state_dir, target)
        before = bs.tree(sb.root)
        rc, _o, _e = run(script, ["stop", sb.wiki], sb.data)
        problems = []
        if bs.tree(sb.root) != before:
            problems.append("砂場が変わった")
        if rc == 0:
            problems.append("領分の名前がリンクなのに、止まらずに 0 で終わった")
        return f"stop {state}", rc, problems
    finally:
        sb.close()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--wiki", default=str(HERE.parents[1] / "info-hive-wiki"))
    args = ap.parse_args(argv)
    scripts = Path(args.wiki) / "skills" / "info-hive" / "scripts"
    script = scripts / "wiki_browse.py"
    key = key_fn(scripts)
    started = time.time()
    total = 0
    print(f"Python {sys.version.split()[0]}、{sys.platform}、{script}")
    print("\n| 状態 | 終了コード | 破れた決まり |\n| --- | --- | --- |")
    for case in bs.build_cases(args.quick):
        label, rc, problems = check_build(script, key, case)
        total += sum(1 for p in problems if not p.startswith("飛ばした"))
        print(f"| {label} | {rc} | {'<br>'.join(problems) or 'なし'} |", flush=True)
    for state in (*bs.ROOT_LINK, "state-link"):
        label, rc, problems = check_stop(script, key, state)
        total += sum(1 for p in problems if not p.startswith("飛ばした"))
        print(f"| {label} | {rc} | {'<br>'.join(problems) or 'なし'} |", flush=True)
    print(f"\n破れた決まり {total} 件、{time.time() - started:.0f} 秒")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
