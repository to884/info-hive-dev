"""探索の状態にない、リンクの位置を、手を入れない実行で確かめる（8 版目の試作）。

それぞれの位置で、リンクの先の木と砂場の全体の木を、実行の前と後で比べる。2 回続けて流す（2 回目は次の実行）。
"""
import json
import os
import sys
import time

sys.path.insert(0, r"C:\Works\info-hive-dev\docs\agent-runs\2026-11-11-wiki-browse-structure")
import write_model as m  # noqa: E402
import write_sweep as s  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
started = time.time()
print(f"Python {sys.version.split()[0]}、{sys.platform}\n")


def diff(before, after):
    keys = sorted(set(before) | set(after))
    return [k for k in keys if before.get(k) != after.get(k)]


def make_link(kind_, link, target):
    if kind_ == "junction":
        s.junction(link, target)
    else:
        os.symlink(target, link, target_is_directory=True)


def run_two(sb):
    rcs, warns = [], []
    for _ in range(2):
        rcs.append(s.run_build(sb, s.Injector()))
        warns.append(list(m.WARNINGS))
    return rcs, warns


def report(label, sb, target, before_all, before_target, rcs, warns, extra=""):
    after_all, after_target = s.tree(sb.root), s.tree(target)
    out_kind = m.kind(sb.out)
    out_content = s.content(s.tree(sb.out)) if out_kind == "dir" else None
    is_n = out_content == s.expected(s.FILES_N)
    changed = diff(before_all, after_all)
    print(f"### {label}\n")
    print(f"- 終わり方: {rcs[0]}、次の実行: {rcs[1]}")
    print(f"- 警告: {warns[0]} / {warns[1]}")
    print(f"- リンクの先が変わったか: {'変わった ' + str(diff(before_target, after_target)) if before_target != after_target else '変わらない'}")
    print(f"- 書き出し先の名前の種類: {out_kind}、新しい世代か: {is_n}")
    print(f"- 砂場で変わった名前: {changed}")
    if extra:
        print(f"- {extra}")
    print()


# 1. 既定の書き出し先の名前そのものがリンク（その先は、利用者のファイルを持つディレクトリ）
for kind_ in ("junction", "symlink"):
    sb = s.Sandbox("absent", "asis", True)
    try:
        target = os.path.join(sb.root, "elsewhere-out")
        s.write(os.path.join(target, "private.txt"), b"keep me")
        make_link(kind_, sb.out, target)
        before_all, before_target = s.tree(sb.root), s.tree(target)
        rcs, warns = run_two(sb)
        report(f"既定の書き出し先の名前が {kind_}", sb, target, before_all, before_target, rcs, warns)
    finally:
        sb.close()

# 2. --out の名前そのものがリンク（その先は、利用者のファイル、または browse の世代）
for kind_ in ("junction", "symlink"):
    for content_ in ("userfiles", "generation"):
        sb = s.Sandbox("absent", "asis", False)
        try:
            target = os.path.join(sb.root, "elsewhere-out")
            if content_ == "userfiles":
                s.write(os.path.join(target, "private.txt"), b"keep me")
            else:
                s.put_generation(target, s.FILES_P, 3)
            make_link(kind_, sb.out, target)
            before_all, before_target = s.tree(sb.root), s.tree(target)
            rcs, warns = run_two(sb)
            report(f"--out の名前が {kind_}（先に {content_}）", sb, target, before_all, before_target, rcs, warns)
        finally:
            sb.close()

# 3. 書き出し先がなく、作業用の old-N そのものがリンク（復旧の道）
for default in (False, True):
    for kind_ in ("junction", "symlink"):
        for content_ in ("userfiles", "generation"):
            sb = s.Sandbox("absent", "asis", default)
            try:
                os.makedirs(sb.work)
                s.write(os.path.join(sb.work, m.WORK_MARKER), b"A" if default else b"")
                target = os.path.join(sb.root, "elsewhere-old")
                if content_ == "userfiles":
                    s.write(os.path.join(target, "private.txt"), b"keep me")
                else:
                    s.put_generation(target, s.FILES_P, 5)
                make_link(kind_, os.path.join(sb.work, "old-5"), target)
                before_all, before_target = s.tree(sb.root), s.tree(target)
                rcs, warns = run_two(sb)
                report(f"{'既定' if default else '--out'}、書き出し先がなく、old-5 が {kind_}（先に {content_}）",
                       sb, target, before_all, before_target, rcs, warns)
            finally:
                sb.close()

# 4. 作業用の tmp-N、del-N そのものがリンク
for default in (False, True):
    for name in ("tmp-7", "del-6"):
        for kind_ in ("junction", "symlink"):
            sb = s.Sandbox("gen", "asis", default)
            try:
                os.makedirs(sb.work)
                s.write(os.path.join(sb.work, m.WORK_MARKER), b"A" if default else b"")
                target = os.path.join(sb.root, "elsewhere-left")
                s.write(os.path.join(target, "private.txt"), b"keep me")
                make_link(kind_, os.path.join(sb.work, name), target)
                before_all, before_target = s.tree(sb.root), s.tree(target)
                rcs, warns = run_two(sb)
                report(f"{'既定' if default else '--out'}、前の世代があり、{name} が {kind_}",
                       sb, target, before_all, before_target, rcs, warns)
            finally:
                sb.close()


# 5. 状態のディレクトリの server.json、server.json.new がリンク（ファイルへのシンボリックリンク）
def server_ops(sb):
    results = []
    try:
        outcome, server = m.serve_start(sb.wiki, sb.state_dir, "new", "A")
        results.append(f"serve={outcome}")
        try:
            results.append(f"動いているあいだの stop={m.stop(sb.wiki, sb.state_dir, 'A')}")
        except m.Stop as e:
            results.append(f"動いているあいだの stop=Stop({e})")
        if outcome == "started":
            m.serve_finish(server)
    except (m.Stop, m.Unknown, m.Absent) as e:
        results.append(f"serve={type(e).__name__}({e})")
    for op in ("stop", "is_running"):
        try:
            r = m.stop(sb.wiki, sb.state_dir, "A") if op == "stop" else m.is_running(sb.wiki, sb.state_dir, "A")
            results.append(f"{op}={r}")
        except (m.Stop, m.Unknown, m.Absent) as e:
            results.append(f"{op}={type(e).__name__}({e})")
    return results


for name in ("server.json", "server.json.new"):
    sb = s.Sandbox("absent", "asis", True)
    try:
        d = sb.state_dir
        os.makedirs(d)
        s.write(os.path.join(d, m.SERVER_MARKER), b"A")
        s.write(os.path.join(d, "server.lock"), b"")
        target = os.path.join(sb.root, "elsewhere-rec")
        s.write(os.path.join(target, "rec.json"), json.dumps({"instance": "user", "owner": "A"}).encode())
        os.symlink(os.path.join(target, "rec.json"), os.path.join(d, name))
        before_all, before_target = s.tree(sb.root), s.tree(target)
        m.WARNINGS.clear()
        results = server_ops(sb)
        after_all, after_target = s.tree(sb.root), s.tree(target)
        print(f"### 状態のディレクトリの {name} が、利用者のファイルへのシンボリックリンク\n")
        print(f"- 結果: {results}")
        print(f"- 警告: {list(m.WARNINGS)}")
        print(f"- リンクの先が変わったか: {'変わった ' + str(diff(before_target, after_target)) if before_target != after_target else '変わらない'}")
        print(f"- 砂場で変わった名前: {diff(before_all, after_all)}")
        print(f"- 状態のディレクトリの中: {sorted(os.listdir(d))}、server.json の種類: {m.kind(os.path.join(d, 'server.json'))}\n")
    finally:
        sb.close()


# 6. <data_dir> そのものがジャンクションのときの、サーバー（状態のディレクトリ 12 種、手を入れない起動と終了）
class DataJunctionSandbox(s.Sandbox):
    def __init__(self, out_state, work_state, default):
        super().__init__("gen+datajunction" if out_state != "nodata" else out_state, work_state, default)


orig = s.Sandbox
s.Sandbox = DataJunctionSandbox
try:
    problems, runs = [], 0
    for state in s.STATE_STATES:
        if state == "nodata":
            continue
        for phase in ("start", "finish"):
            found, total = s.check_server(state, phase, None, None)
            problems += found
            runs += 1
    print(f"### <data_dir> がジャンクションのときの、サーバー（手を入れない起動と終了、状態 {runs // 2} 種）\n")
    print(f"- 実行 {runs} 回、破れた決まり {len(problems)} 件")
    for p in problems[:20]:
        print(f"  - {p}")
    print()
    # 根より下でのリンク: stop と動いているかの確かめ（動いているサーバーがある、ない）
    sb = DataJunctionSandbox("absent", "asis", True)
    try:
        before_all = s.tree(sb.root)
        results = server_ops(sb)
        print(f"- 起動、動いているあいだの stop、終了、stop、動いているかの確かめ: {results}")
        print(f"- 砂場で変わった名前: {diff(before_all, s.tree(sb.root))}\n")
    finally:
        sb.close()
finally:
    s.Sandbox = orig

# 7. 名前ごとに識別子を覚える対照を、手を入れずに流す（失敗のないときの約束を破るか）
m.MUTANTS.add("cache_ids_by_name")
try:
    print("### 対照 cache_ids_by_name を、手を入れずに流す\n")
    for o, w, dflt in (("gen+datajunction", "asis", True), ("gen+datajunction", "leftovers", True)):
        sb = s.Sandbox(o, w, dflt)
        try:
            found, _ = s.check_build(sb, None, None)
            print(f"- {o}/{w}/{'default' if dflt else 'out'}: 破れた決まり {len(found)} 件 {found[:3]}")
        finally:
            sb.close()
finally:
    m.MUTANTS.discard("cache_ids_by_name")


# 8. --out の親がリンク（利用者のディレクトリへのジャンクション、Wiki の中へのジャンクション）と、
#    既定の書き出し先の前の世代の中に、Wiki へのジャンクションがある（8 版目の、2 回目の位置の確かめで足した）
def out_parent_case(label, make, expect_stop):
    sb = s.Sandbox("absent", "asis", False)
    try:
        watch = make(sb)                     # 変わってはならない木の根（リンクの先）
        before_all, before_watch = s.tree(sb.root), s.tree(watch)
        rcs, warns = run_two(sb)
        after_all, after_watch = s.tree(sb.root), s.tree(watch)
        out_c = s.content(s.tree(sb.out)) if m.kind(sb.out) == "dir" else None
        left = sorted(os.listdir(sb.work)) if os.path.isdir(sb.work) else None
        print(f"### {label}\n")
        print(f"- 終わり方: {rcs[0]}、次の実行: {rcs[1]}（期待: {'止まる' if expect_stop else '0'}）")
        print(f"- 警告: {warns[0]} / {warns[1]}")
        print(f"- 書き出し先が新しい世代か: {out_c == s.expected(s.FILES_N)}、作業用の中: {left}")
        print(f"- 見張った木（{os.path.relpath(watch, sb.root)}）で変わった名前: {diff(before_watch, after_watch)}")
        print(f"- 砂場で変わった名前: {diff(before_all, after_all)}\n")
    finally:
        sb.close()


def parent_to_user(with_generation):
    def make(sb):
        real = os.path.join(sb.root, "userparent")
        s.write(os.path.join(real, "keep.txt"), b"keep")
        if with_generation:
            s.put_generation(os.path.join(real, "site"), s.FILES_P, 3)
        s.junction(os.path.join(sb.root, "linkparent"), real)
        sb.out = os.path.join(sb.root, "linkparent", "site")
        sb.work = sb.out + ".browse-work"
        return os.path.join(real, "keep.txt")
    return make


def parent_to_wiki(sb):
    s.junction(os.path.join(sb.root, "linkwiki"), sb.wiki)
    sb.out = os.path.join(sb.root, "linkwiki", "site")
    sb.work = sb.out + ".browse-work"
    return sb.wiki


out_parent_case("--out の親が、利用者のディレクトリへのジャンクション（書き出し先がない）", parent_to_user(False), False)
out_parent_case("--out の親が、利用者のディレクトリへのジャンクション（その先に前の世代がある）", parent_to_user(True), False)
out_parent_case("--out の親が、Wiki のルートへのジャンクション", parent_to_wiki, True)

sb = s.Sandbox("gen", "asis", True)
try:
    s.junction(os.path.join(sb.out, "concepts", "wikilink"), sb.wiki)
    before_wiki = s.tree(sb.wiki)
    rcs, warns = run_two(sb)
    print("### 既定の書き出し先の前の世代の中に、Wiki のルートへのジャンクションがある\n")
    print(f"- 終わり方: {rcs[0]}、次の実行: {rcs[1]}（期待: 0）")
    print(f"- 警告: {warns[0]} / {warns[1]}")
    print(f"- 書き出し先が新しい世代か: {s.content(s.tree(sb.out)) == s.expected(s.FILES_N)}、作業用の中: {sorted(os.listdir(sb.work))}")
    print(f"- Wiki で変わった名前: {diff(before_wiki, s.tree(sb.wiki))}\n")
finally:
    sb.close()

print(f"\n{time.time() - started:.0f} 秒")
