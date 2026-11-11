"""write_model.py に、OS の呼び出しの N 回目に手を入れる探索をかける。製品の試験ではない。

探索:
- 失敗: N 回目を PermissionError（分からない）か FileNotFoundError（ない）にする。
- 短い書き込み: N 回目が書き込みなら、半分だけ書いて、正常に戻る。
- 強制停止: N 回目で止まる。それ以降の OS の呼び出しは 1 つも実行されず、開いていたファイルは閉じる
  （プロセスが止まり、OS がロックを外したのと同じ）。half は、N 回目が書き込みなら、半分だけ書いてから止まる。
- 2 つ目の失敗: 1 つ目の失敗のあとの呼び出し（片付け）にも、失敗を入れる。

基準（試作の関数を使わずに、砂場の木を自分で読んで決める）:
- 世界の差分: 書き出し先、作業用、状態のディレクトリの外は、実行の前後で変わらない。
- 書き出し: 0 で終われば、書き出し先の木は N。0 でなければ、前のまま（P）。入れ替えの途中で止まったときは、
  書き出し先がなく、作業用に P がそのまま残っている。
- browse の書き出しと確かめられない書き出し先（--out）は、どの場合も変わらない。
- 次の実行: 手を入れずにもう一度実行すると、決めた状態に着く。作業用に残りがない。
- サーバー: 終了、失敗、強制停止のあとは「動いていない」。次の起動は成功する。

使い方: python write_sweep.py [--quick]
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import sys
import tempfile
import time

import write_model as m

FILES_P = {"index.html": b"<p>previous</p>", "concepts/a.html": b"<p>a v1</p>", "assets/app.js": b"// v1"}
FILES_N = {"index.html": b"<p>new</p>" * 40, "concepts/a.html": b"<p>a v2</p>", "concepts/b.html": b"<p>b</p>",
           "assets/app.js": b"// v2"}


class Crash(BaseException):
    pass


class Injector(m.Os):
    """口の呼び出しを数え、N 回目に手を入れる。"""

    def __init__(self, at=None, mode=None, second=None):
        self.at, self.mode, self.second = at, mode, second
        self.count = 0
        self.crashed = False
        self.fds = set()
        self.hit = None

    def _before(self, name, args):
        if self.crashed:
            raise Crash()
        self.count += 1
        if self.count == self.at:
            self.hit = name
            if name == "close" and self.mode in ("denied", "absent"):
                # close は、失敗を返すときも、記述子を手放す。手放さない失敗は、OS では起きない。
                os.close(args[0])
                self.fds.discard(args[0])
            if self.mode == "denied":
                raise PermissionError(13, "injected")
            if self.mode == "absent":
                raise FileNotFoundError(2, "injected")
            if self.mode in ("crash", "half"):
                if self.mode == "half" and name == "write":
                    os.write(args[0], bytes(args[1])[: max(1, len(args[1]) // 2)])
                self._crash()
            if self.mode == "short" and name == "write":
                return os.write(args[0], bytes(args[1])[: max(1, len(args[1]) // 2)])
        if self.second is not None and self.count == self.second:
            if name == "close":
                os.close(args[0])
                self.fds.discard(args[0])
            raise PermissionError(13, "injected (second)")
        return None

    def _crash(self):
        self.crashed = True
        for fd in list(self.fds):
            try:
                os.close(fd)
            except OSError:
                pass
        self.fds.clear()
        raise Crash()


def _wrap(name):
    real = getattr(m.Os, name)

    def method(self, *args):
        early = self._before(name, args)
        if early is not None:
            return early
        result = real(self, *args)
        if name.startswith("open_"):
            self.fds.add(result)
        elif name == "close":
            self.fds.discard(args[0])
        return result
    return method


for _name in ("lstat", "listdir", "mkdir", "open_excl", "open_read", "open_lock", "write", "read", "close",
              "rename", "replace", "unlink", "rmdir", "try_lock", "unlock"):
    setattr(Injector, _name, _wrap(_name))


# ---------------------------------------------------------------------------
# 砂場
# ---------------------------------------------------------------------------

def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def put_generation(directory, files, seq):
    os.makedirs(directory)
    write(os.path.join(directory, m.MANIFEST), m.make_manifest(files, seq))
    for name, data in files.items():
        write(os.path.join(directory, *name.split("/")), data)


def junction(link, target):
    if os.name == "nt":
        import _winapi
        _winapi.CreateJunction(target, link)
    else:
        os.symlink(target, link, target_is_directory=True)


OUT_STATES = ("absent", "empty", "gen", "gen+extra", "gen+edited", "userdir", "legacy", "gen+hardlink",
              "absent+old", "empty+old")
WORK_STATES = ("asis", "leftovers", "junction", "unmarked-empty")
FOREIGN = ("gen+extra", "gen+edited", "userdir", "legacy")


class Sandbox:
    def __init__(self, out_state, work_state, default):
        self.out_state, self.work_state, self.default = out_state, work_state, default
        self.root = tempfile.mkdtemp(prefix="bw-", dir=os.environ.get("BW_TMP"))
        r = self.root
        write(os.path.join(r, "wiki", "a.md"), b"# a\n")
        write(os.path.join(r, "wiki", "assets", "app.js"), b"wiki asset")
        write(os.path.join(r, "user", "keep.txt"), b"keep")
        write(os.path.join(r, "user", "assets", "app.js"), b"user asset")
        put_generation(os.path.join(r, "exports", "other"), FILES_P, 4)
        os.makedirs(os.path.join(r, "data", "browse"))
        self.out = os.path.join(r, "data", "browse", "KEY") if default else os.path.join(r, "exports", "site")
        self.work = self.out + ".browse-work"
        self.state_dir = os.path.join(r, "data", "browse", "KEY.server")
        out, work = self.out, self.work
        if out_state == "empty":
            os.makedirs(out)
        elif out_state.startswith("gen"):
            put_generation(out, FILES_P, 3)
            if out_state == "gen+extra":
                write(os.path.join(out, "notes.txt"), b"my notes")
            elif out_state == "gen+edited":
                write(os.path.join(out, "index.html"), b"<p>edited by hand</p>")
            elif out_state == "gen+hardlink":
                os.link(os.path.join(out, "index.html"), os.path.join(r, "wiki", "hl.md"))
                os.chmod(os.path.join(out, "index.html"), stat.S_IREAD)
        elif out_state == "userdir":
            write(os.path.join(out, "report.docx"), b"user file")
        elif out_state == "legacy":
            write(os.path.join(out, m.MANIFEST), b'{"generation": "x", "published_seq": 3}\n')
            write(os.path.join(out, "index.html"), b"<p>0.10.0</p>")
        elif out_state.endswith("+old"):
            if out_state == "empty+old":
                os.makedirs(out)
            os.makedirs(work)
            write(os.path.join(work, m.WORK_MARKER), b"")
            put_generation(os.path.join(work, "old-5"), FILES_P, 5)
        if work_state != "asis" and not os.path.isdir(work):
            os.makedirs(work)
            if work_state != "unmarked-empty":
                write(os.path.join(work, m.WORK_MARKER), b"")
        if work_state == "leftovers":
            write(os.path.join(work, "tmp-7", "index.html"), b"<p>half")
            write(os.path.join(work, "del-6", "concepts", "a.html"), b"<p>a v0</p>")
            write(os.path.join(work, "seq"), b"7\n")
            write(os.path.join(work, "build-report.json"), b"{}")
        elif work_state == "junction":
            os.makedirs(os.path.join(work, "tmp-8"))
            junction(os.path.join(work, "tmp-8", "assets"), os.path.join(r, "user", "assets"))
            junction(os.path.join(work, "tmp-8", "wiki"), os.path.join(r, "wiki"))

    def close(self):
        def onerror(func, path, exc):
            try:
                os.chmod(path, stat.S_IWRITE)
                func(path)
            except OSError:
                pass
        for dirpath, dirnames, _files in os.walk(self.root):
            for d in list(dirnames):
                full = os.path.join(dirpath, d)
                if os.path.islink(full) or (os.name == "nt" and os.lstat(full).st_file_attributes & 0x400):
                    os.rmdir(full) if os.name == "nt" else os.unlink(full)
                    dirnames.remove(d)
        shutil.rmtree(self.root, onerror=onerror)


def tree(path):
    """木を自分で読む。{相対パス: (種類, ハッシュ, 書き込みできるか, 更新時刻)}。リンクはたどらない。"""
    found = {}
    if not os.path.lexists(path):
        return None

    def walk(directory, prefix):
        for name in sorted(os.listdir(directory)):
            full, rel = os.path.join(directory, name), prefix + name
            st = os.lstat(full)
            if stat.S_ISLNK(st.st_mode) or getattr(st, "st_file_attributes", 0) & 0x400:
                found[rel] = ("link",)
            elif stat.S_ISDIR(st.st_mode):
                found[rel] = ("dir",)
                walk(full, rel + "/")
            else:
                with open(full, "rb") as f:
                    digest = hashlib.sha256(f.read()).hexdigest()
                found[rel] = ("file", digest, bool(st.st_mode & stat.S_IWRITE), st.st_mtime_ns)
    if os.path.isdir(path) and not os.path.islink(path):
        walk(path, "")
    return found


def content(t):
    """一覧のファイルを除き、種類とハッシュだけにする（世代どうしを比べる）。"""
    if t is None:
        return None
    return {k: v[:2] for k, v in t.items() if k != m.MANIFEST}


def expected(files):
    t = {name: ("file", hashlib.sha256(data).hexdigest()) for name, data in files.items()}
    for name in files:
        parts = name.split("/")
        for i in range(1, len(parts)):
            t["/".join(parts[:i])] = ("dir",)
    return t


def world(sb):
    """書き出し先、作業用、状態のディレクトリの外の木。"""
    t = tree(sb.root)
    skip = [os.path.relpath(p, sb.root).replace(os.sep, "/") for p in (sb.out, sb.work, sb.state_dir)]
    return {k: v for k, v in t.items() if not any(k == s or k.startswith(s + "/") for s in skip)}


# ---------------------------------------------------------------------------
# 書き出しの探索
# ---------------------------------------------------------------------------

def run_build(sb, injector):
    m.X = injector
    m.WARNINGS.clear()
    try:
        return m.build(sb.out, FILES_N, sb.default)
    except m.Stop:
        return "stop"
    except (m.Unknown, m.Absent):
        return "unknown"
    except Crash:
        return "crash"
    finally:
        m.X = m.Os()


def check_build(sb, at, mode, second=None):
    """1 回の実行と、そのあとの手を入れない実行を確かめる。破れた決まりの一覧を返す。"""
    problems = []
    before_world, before_out = world(sb), tree(sb.out)
    old5 = content(tree(os.path.join(sb.work, "old-5")))
    protected = sb.out_state in FOREIGN and not sb.default
    injector = Injector(at, mode, second)
    rc = run_build(sb, injector)
    after_out = tree(sb.out)
    N, P = expected(FILES_N), content(before_out)

    def where(label):
        return f"{label}（{sb.out_state}/{sb.work_state}/{'default' if sb.default else 'out'}、{mode}@{at}" \
               f"{'+' + str(second) if second else ''}、{injector.hit}、rc={rc}）"

    if world(sb) != before_world:
        problems.append(where("書き出し先と領分の外が変わった"))
    if protected:
        if after_out != before_out:
            problems.append(where("browse のものでない書き出し先が変わった"))
        if rc == 0:
            problems.append(where("browse のものでない書き出し先で 0 で終わった"))
    elif rc == 0:
        if content(after_out) != N:
            problems.append(where("0 で終わったのに、書き出し先が新しい世代でない"))
    else:
        c = content(after_out)
        olds = [content(tree(os.path.join(sb.work, n))) for n in (os.listdir(sb.work) if os.path.isdir(sb.work) else [])
                if n.startswith("old-")]
        ok = (after_out == before_out
              or (old5 is not None and c == old5)                       # 途中で止まっていた世代を戻した
              or (c in (None, {}) and P in (None, {}))                  # ない、または空のまま
              or (c in (None, {}) and (P in olds or (old5 is not None and old5 in olds)))   # 作業用に P が残っている
              or (rc == "crash" and c == N))                            # 確定のあとで止まった
        if not ok:
            problems.append(where("0 でないのに、書き出し先が前のままでも、戻せる形でもない"))

    # 次の実行（手を入れない）
    counter = Injector()
    rc2 = run_build(sb, counter)
    after2 = tree(sb.out)
    if world(sb) != before_world:
        problems.append(where("次の実行で、書き出し先と領分の外が変わった"))
    if protected:
        if rc2 != "stop" or after2 != before_out:
            problems.append(where("次の実行が、browse のものでない書き出し先で止まらなかった"))
    else:
        if rc2 != 0 or content(after2) != N:
            problems.append(where(f"次の実行が新しい世代に着かなかった（rc={rc2}）"))
        else:
            left = sorted(set(os.listdir(sb.work)) - {m.WORK_MARKER, "build.lock"})
            if left and sb.out_state != "gen+hardlink":
                problems.append(where(f"作業用に残りがある: {left}"))
            if left and sb.out_state == "gen+hardlink":
                NOTES.add("読み取り専用のファイルは消せず、作業用に残る（属性を変えないため）: " + ", ".join(left))
    return problems, counter.count


NOTES: set = set()


def count_calls(make):
    sb = make()
    try:
        injector = Injector()
        run_build(sb, injector)
        return injector.count
    finally:
        sb.close()


def sweep_build(out_state, work_state, default, modes, depth2=False):
    def make():
        return Sandbox(out_state, work_state, default)
    total = count_calls(make)
    problems, runs = [], 0
    for mode in modes:
        for at in range(1, total + 1):
            sb = make()
            try:
                found, _ = check_build(sb, at, mode)
                problems += found
                runs += 1
            finally:
                sb.close()
    if depth2:
        for at in range(1, total + 1):
            # 1 つ目の失敗のあとに何回呼ぶかを数える
            sb = make()
            try:
                probe = Injector(at, "denied")
                run_build(sb, probe)
                last = probe.count
            finally:
                sb.close()
            for second in range(at + 1, last + 1):
                sb = make()
                try:
                    found, _ = check_build(sb, at, "denied", second)
                    problems += found
                    runs += 1
                finally:
                    sb.close()
    return total, runs, problems


# ---------------------------------------------------------------------------
# サーバーの記録の探索
# ---------------------------------------------------------------------------

STATE_STATES = ("absent", "stale-record", "leftover-new", "unmarked-empty", "stale+leftover")


def make_state(sb, state):
    d = sb.state_dir
    if state == "absent":
        return
    os.makedirs(d)
    if state == "unmarked-empty":
        return
    write(os.path.join(d, m.SERVER_MARKER), b"")
    write(os.path.join(d, "server.lock"), b"")
    if state in ("stale-record", "stale+leftover"):
        write(os.path.join(d, "server.json"), b'{"instance": "old"}')
    if state in ("leftover-new", "stale+leftover"):
        write(os.path.join(d, "server.json.new"), b'{"inst')


def run_server(sb, injector, phase):
    """起動して終了する。phase='start' なら起動だけに、'finish' なら終了だけに手を入れる。"""
    m.WARNINGS.clear()
    server = None
    try:
        m.X = injector if phase == "start" else m.Os()
        server = m.serve_start(sb.state_dir, "new")
        m.X = injector if phase == "finish" else m.Os()
        if phase == "finish":
            injector.fds.add(server.lock.fd)      # 強制停止で、ロックも外れる
        m.serve_finish(server)
        return "ok"
    except m.Stop:
        return "stop"
    except (m.Unknown, m.Absent):
        return "unknown"
    except Crash:
        return "crash"
    finally:
        m.X = m.Os()
        if server is not None and phase == "start" and server.lock.fd is not None:
            server.lock.release()


def check_server(state, phase, at, mode):
    sb = Sandbox("absent", "asis", True)
    problems = []
    try:
        make_state(sb, state)
        before_world = world(sb)
        injector = Injector(at, mode)
        rc = run_server(sb, injector, phase)

        def where(label):
            return f"{label}（状態 {state}、{phase}、{mode}@{at}、{injector.hit}、rc={rc}）"
        if world(sb) != before_world:
            problems.append(where("状態のディレクトリの外が変わった"))
        try:
            if m.is_running(sb.state_dir):
                problems.append(where("終わったあとも、ロックが残っている"))
        except (m.Stop, m.Unknown, m.Absent) as e:
            problems.append(where(f"動いているかを確かめられない: {e}"))
            return problems, injector.count
        # 次の起動は成功する。動いているあいだ、もう 1 つは起動しない。
        try:
            server = m.serve_start(sb.state_dir, "next")
        except (m.Stop, m.Unknown, m.Absent) as e:
            problems.append(where(f"次の起動が失敗した: {e}"))
        else:
            with open(os.path.join(sb.state_dir, "server.json"), "rb") as f:
                if json.loads(f.read()).get("instance") != "next":
                    problems.append(where("次の起動のあと、記録が新しくない"))
            try:
                m.serve_start(sb.state_dir, "second")
                problems.append(where("動いているのに、もう 1 つ起動した"))
            except m.Stop:
                pass
            m.serve_finish(server)
            left = sorted(set(os.listdir(sb.state_dir)) - {m.SERVER_MARKER, "server.lock"})
            if left:
                problems.append(where(f"終了のあと、状態のディレクトリに残りがある: {left}"))
        return problems, injector.count
    finally:
        sb.close()


def sweep_server(modes):
    problems, runs = [], 0
    for state in STATE_STATES:
        for phase in ("start", "finish"):
            _, total = check_server(state, phase, None, None)
            for mode in modes:
                for at in range(1, total + 1):
                    found, _ = check_server(state, phase, at, mode)
                    problems += found
                    runs += 1
    return runs, problems


# ---------------------------------------------------------------------------
# 実行
# ---------------------------------------------------------------------------

USER_DELETES = [("gen", "asis", False), ("gen", "leftovers", False), ("absent+old", "asis", False),
                ("gen", "asis", True)]


def sweep_user_deletes(cases, modes=("crash", "half")):
    """強制停止のあとで、利用者が書き出し先を消してから、手を入れずに書き出す。

    途中で消していた前の世代を、公開した世代として戻さないことを確かめる。
    """
    problems, runs = [], 0
    for out_state, work_state, default in cases:
        total = count_calls(lambda: Sandbox(out_state, work_state, default))
        for mode in modes:
            for at in range(1, total + 1):
                sb = Sandbox(out_state, work_state, default)
                try:
                    before_world = world(sb)
                    injector = Injector(at, mode)
                    rc = run_build(sb, injector)
                    if rc != "crash" or not os.path.isdir(sb.out):
                        continue
                    runs += 1
                    shutil.rmtree(sb.out)          # 利用者が書き出し先を消す
                    rc2 = run_build(sb, Injector())
                    if rc2 != 0 or content(tree(sb.out)) != expected(FILES_N):
                        problems.append(f"書き出し先を消したあとの書き出しが、新しい世代に着かなかった（rc={rc2}）"
                                        f"（{out_state}/{work_state}/{'default' if default else 'out'}、{mode}@{at}、"
                                        f"{injector.hit}）")
                    if world(sb) != before_world:
                        problems.append(f"書き出し先を消したあとの書き出しで、領分の外が変わった（{out_state}、{mode}@{at}）")
                finally:
                    sb.close()
    return runs, problems


MODES = ("denied", "absent", "short", "crash", "half")
CONTROLS = {
    "skip_gate": [("gen+extra", "asis", False), ("userdir", "asis", False)],
    "follow_links": [("gen", "junction", False)],
    "commit_then_fail": [("gen", "asis", False)],
    "chmod_on_delete": [("gen+hardlink", "asis", False)],
    "delete_in_place": [("gen", "asis", False)],
}


def main():
    quick = "--quick" in sys.argv
    started = time.time()
    lines, all_problems = [], []
    out_states = ("absent", "gen", "gen+extra", "absent+old") if quick else OUT_STATES
    work_states = ("asis", "leftovers") if quick else WORK_STATES
    for default in (False, True):
        for out_state in out_states:
            for work_state in work_states:
                if out_state.endswith("+old") and work_state == "unmarked-empty":
                    continue
                depth2 = (not quick) and not default and out_state in ("gen", "absent+old") and work_state in ("asis", "leftovers")
                total, runs, problems = sweep_build(out_state, work_state, default, MODES, depth2)
                all_problems += problems
                lines.append(f"| {'既定' if default else '--out'} | {out_state} | {work_state} | {total} | {runs} | {len(problems)} |")
    server_runs, server_problems = sweep_server(MODES)
    all_problems += server_problems
    deletes_runs, deletes_problems = sweep_user_deletes(USER_DELETES)
    all_problems += deletes_problems

    control_lines = []
    for mutant, cases in CONTROLS.items():
        m.MUTANTS.add(mutant)
        try:
            found = []
            for out_state, work_state, default in cases:
                _, _, problems = sweep_build(out_state, work_state, default, MODES)
                found += problems
            if mutant == "delete_in_place":
                found += sweep_user_deletes(USER_DELETES)[1]
        finally:
            m.MUTANTS.discard(mutant)
        control_lines.append(f"| {mutant} | {len(found)} | {found[0] if found else '見つからなかった'} |")
    m.MUTANTS.add("refuse_unknown_entries")
    try:
        _, found = sweep_server(MODES)
    finally:
        m.MUTANTS.discard("refuse_unknown_entries")
    control_lines.append(f"| refuse_unknown_entries | {len(found)} | {found[0] if found else '見つからなかった'} |")

    print(f"Python {sys.version.split()[0]}、{sys.platform}、{time.time() - started:.0f} 秒")
    print("\n## 書き出し\n\n| 書き出し先の種類 | 書き出し先の状態 | 作業用の状態 | 口の呼び出し | 実行 | 破れた決まり |\n| --- | --- | --- | --- | --- | --- |")
    print("\n".join(lines))
    print(f"\n## サーバーの記録\n\n実行 {server_runs} 回、破れた決まり {len(server_problems)} 件")
    print(f"\n## 強制停止のあとで、利用者が書き出し先を消す\n\n実行 {deletes_runs} 回、破れた決まり {len(deletes_problems)} 件")
    print("\n## 対照\n\n| 対照 | 見つけた件数 | 最初の 1 件 |\n| --- | --- | --- |")
    print("\n".join(control_lines))
    if NOTES:
        print("\n## 気づき\n")
        for note in sorted(NOTES):
            print("- " + note)
    if all_problems:
        print(f"\n## 破れた決まり（{len(all_problems)} 件。先頭 40 件）\n")
        seen = []
        for p in all_problems:
            if p not in seen:
                seen.append(p)
        for p in seen[:40]:
            print("- " + p)
    return 1 if all_problems else 0


if __name__ == "__main__":
    sys.exit(main())
