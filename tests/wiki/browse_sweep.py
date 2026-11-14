"""browse の書く側の層（wiki_browse_fs.py）に、口の呼び出しの N 回目に手を入れる探索をかける（設計の 9.2、9.3、9.5）。

設計の試作の探索（docs/agent-runs/2026-11-11-wiki-browse-structure/write_sweep.py）を、製品の層に移したもの。
砂場と世界の差分は browse_sandbox.py にあり、browse の実装に依らない。

探索:
- 手を入れない: 失敗のない実行が、決めた状態に着く（失敗のないときの約束）。
- 失敗: N 回目を PermissionError（分からない）か FileNotFoundError（ない）にする。書いたファイルの close の失敗は、
  遅れて出た書き込みの失敗として、ファイルの中身を失わせてから返す。
- 短い書き込み: N 回目が書き込みなら、半分だけ書いて、正常に戻る。
- 強制停止: N 回目で止まる。それ以降の口の呼び出しは 1 つも実行されず、開いていたファイルは閉じる
  （プロセスが止まり、OS がロックを外したのと同じ）。half は、N 回目が書き込みなら、半分だけ書いてから止まる。
- 正常に戻る異常: 識別子の口が識別子 0 で成功を返す。Windows で、種類の口がブロックデバイスで成功を返す。
- 2 つ目の失敗: 1 つ目の失敗のあとの呼び出し（片付け）にも、失敗を入れる。

基準（層の関数を使わずに、砂場の木を自分で読んで決める）は、設計の 9.1 と 9.2 のとおり。対照（設計の 9.5）は、
層の MUTANTS に名前を足して、わざと破った規則で同じ探索を流し、基準が失敗することを確かめる。

使い方:
    python -X utf8 tests/wiki/browse_sweep.py [--quick]     （全量は数十分かかる）
"""
from __future__ import annotations

import json
import os
import shutil
import stat
import sys
import time
import types
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[1] / "info-hive-wiki" / "skills" / "info-hive" / "scripts"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(SCRIPTS))
sys.dont_write_bytecode = True

import browse_sandbox as bs  # noqa: E402
import wiki_browse_fs as fs  # noqa: E402
from browse_sandbox import content, expected, real_dir, tree, world, world_same, write  # noqa: E402

FILES_P = bs.FILES_P
FILES_N = {"index.html": b"<p>new</p>" * 40, "concepts/a.html": b"<p>a v2</p>", "concepts/b.html": b"<p>b</p>",
           "assets/app.js": b"// v2"}
FILES_N2 = {"index.html": b"<p>newer</p>", "concepts/a.html": b"<p>a v3</p>"}
EXP_N = expected(FILES_N)

CALLS = ("lstat", "stat", "file_id", "realpath", "scandir_open", "scandir_next", "mkdir", "open_excl", "open_read",
         "open_lock", "write", "read", "close", "rename", "replace", "unlink", "rmdir", "stdout_write",
         "try_lock", "unlock")


class Crash(BaseException):
    pass


class Injector(fs.Os):
    """口の呼び出しを数え、N 回目に手を入れる。"""

    def __init__(self, at=None, mode=None, second=None):
        self.at, self.mode, self.second = at, mode, second
        self.count = 0
        self.crashed = False
        self.fds = set()
        self.writing = {}
        self.hit = None
        self.reads = []
        self.names = []
        self.calls = []
        self.failed = {}        # 手を入れずに失敗した呼び出し: {番号: 例外の型}
        self.targets = []       # 呼び出しの対象のパス（記述子と一覧は、開いたときのパス。付け替えは (元, 先)）
        self.fd_paths = {}
        self.it_paths = {}

    def _fail_close(self, fd):
        """close の失敗。書いたファイルなら、遅れて出た書き込みの失敗として、中身を失わせる。"""
        if fd in self.writing:
            try:
                os.ftruncate(fd, 0)
            except OSError:
                pass
        os.close(fd)
        self.fds.discard(fd)
        self.writing.pop(fd, None)

    def _before(self, name, args):
        if self.crashed:
            raise Crash()
        self.count += 1
        self.names.append(name)
        self.calls.append((name, args))
        if name in ("write", "read", "close", "try_lock", "unlock"):
            target = self.fd_paths.get(args[0])
        elif name == "scandir_next":
            target = self.it_paths.get(id(args[0]))
        elif name in ("rename", "replace"):
            target = (os.fspath(args[0]), os.fspath(args[1]))
        else:
            target = os.fspath(args[0]) if args and isinstance(args[0], str) else None
        self.targets.append(target)
        if name == "open_read":
            self.reads.append(os.fspath(args[0]))
        if self.count == self.at:
            # 書いたファイルの close は、書き込みの失敗なので別の名前にする（読んだファイルとロックの close と分ける）
            self.hit = "close-write" if name == "close" and args[0] in self.writing else name
            if name == "close" and self.mode in ("denied", "absent"):
                self._fail_close(args[0])
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
            if self.mode == "zero" and name == "file_id":
                real = fs.Os.file_id(self, args[0])                 # 識別子 0 の成功
                return (real[0], bytes(16)) if fs.NT else (real[0], 0)
            if self.mode == "blk" and name in ("lstat", "stat"):
                return types.SimpleNamespace(st_mode=stat.S_IFBLK | 0o666, st_file_attributes=0, st_ino=0,
                                             st_dev=0, st_size=0, st_mtime_ns=0)
        if self.second is not None and self.count == self.second:
            if name == "close":
                self._fail_close(args[0])
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
    real = getattr(fs.Os, name)

    def method(self, *args):
        early = self._before(name, args)
        if early is not None:
            return early
        if name == "stdout_write":
            return len(args[0])          # 知らせは、試験では書き先を持たない
        try:
            result = real(self, *args)
        except OSError as e:
            self.failed[self.count] = type(e)
            raise
        if name.startswith("open_"):
            self.fds.add(result)
            self.fd_paths[result] = os.fspath(args[0])
            if name == "open_excl":
                self.writing[result] = args[0]
        elif name == "close":
            self.fds.discard(args[0])
            self.writing.pop(args[0], None)
        elif name == "scandir_open":
            self.it_paths[id(result)] = os.fspath(args[0])
        return result
    return method


for _name in CALLS:
    setattr(Injector, _name, _wrap(_name))

OWNERS: dict = {}


def owner_fn(wiki):
    """砂場の Wiki の持ち主の値（実装の owner_of。手を入れずに取る）。"""
    if wiki not in OWNERS:
        saved, fs.X = fs.X, fs.Os()
        try:
            OWNERS[wiki] = fs.owner_of(wiki)
        finally:
            fs.X = saved
    return OWNERS[wiki]


def Sandbox(out_state, work_state, default):  # noqa: N802
    sb = bs.Sandbox(out_state, work_state, default, key="KEY", owner=owner_fn, initialized=False)
    sb.browse_root = os.path.join(sb.data, "browse")
    return sb


# ---------------------------------------------------------------------------
# 書き出しの探索
# ---------------------------------------------------------------------------

def run_build(sb, injector, files=None):
    fs.X = injector
    fs.WARNINGS.clear()
    try:
        return fs.build(sb.wiki, sb.out, files or FILES_N, sb.default, sb.owner, sb.browse_root,
                        report_text="{}\n", lock_wait=0)
    except fs.Stop:
        return "stop"
    except (fs.Unknown, fs.Absent):
        return "unknown"
    except Crash:
        return "crash"
    finally:
        fs.X = fs.Os()


def role_of(sb, injector, at, commit, leftovers):
    """N 回目の呼び出しの役目を、試験の側で決める。'post'（確定のあと）、'leftover'（前からあった残りの片付け）、'pre'。

    確定の点は、手を入れない実行の記録で、tmp-N を書き出し先の名前にした付け替えの番号である（層の申告ではない）。
    N 回目までの呼び出しは手を入れない実行と同じなので、N がそれより大きければ、確定は済んでいる。
    """
    if commit is not None and at > commit:
        return "post"
    target = injector.targets[at - 1] if at - 1 < len(injector.targets) else None
    paths = target if isinstance(target, tuple) else (target,)
    # 呼び出しの対象は、解く前の名前のことも、解いたパスのこともある（<data_dir> がジャンクションのとき）
    dirs = list(leftovers) + [sb.real(d) for d in leftovers]
    for path in paths:
        if path and any(path == d or path.startswith(d + os.sep) for d in dirs):
            return "leftover"
    return "pre"


def commit_index(sb, injector):
    for i, (name, target) in enumerate(zip(injector.names, injector.targets), 1):
        if (name == "rename" and isinstance(target, tuple) and os.path.normcase(target[1]) == os.path.normcase(sb.out)
                and os.path.basename(target[0]).startswith("tmp-")):
            return i
    return None


NOTES: set = set()
LAST_WARNINGS: Counter = Counter()      # check_build の 1 回目の実行の警告（手を入れない実行の警告を、基準の側で覚える）
LAST_FAILED: dict = {}                  # 同じく、1 回目の実行で、手を入れずに失敗した呼び出し
LAST_COMMIT: list = [None]              # 同じく、1 回目の実行の確定の点（呼び出しの番号）
SKIPPED: list = []                      # リンクを作れずに飛ばした状態


def check_build(sb, at, mode, second=None, baseline=None, natural=None, commit=None):
    """1 回の実行と、そのあとの手を入れない実行を確かめる。破れた決まりの一覧を返す。

    baseline は、同じ状態で手を入れない実行が出した警告（多重集合）。手を入れた実行の警告は、これと比べて、
    新しいものがなければならない。natural は、同じ状態で手を入れない実行が失敗した呼び出し（{番号: 例外の型}）。
    """
    problems = []
    before_world, before_out = world(sb), tree(sb.out)
    # 退避の世代は、名前そのものが実のディレクトリの old-N だけである（リンクの先は、browse が退避した世代でない）
    old5_path = os.path.join(sb.work, "old-5")
    old5 = content(tree(old5_path)) if real_dir(old5_path) else None
    leftovers = [os.path.join(sb.work, n) for n in (os.listdir(sb.work) if real_dir(sb.work) else [])
                 if n.startswith(("tmp-", "del-")) or n in bs.LEGACY]
    protected = sb.protected
    injector = Injector(at, mode, second)
    rc = run_build(sb, injector)
    warnings = Counter(fs.WARNINGS)
    LAST_WARNINGS.clear()
    LAST_WARNINGS.update(warnings)
    LAST_FAILED.clear()
    LAST_FAILED.update(injector.failed)
    LAST_COMMIT[0] = commit_index(sb, injector)
    new_warnings = warnings - (baseline or Counter())
    already_failing = mode == "denied" and (natural or {}).get(at) is PermissionError
    after_out = tree(sb.out)
    P = content(before_out)

    def where(label):
        return f"{label}（{sb.out_state}/{sb.work_state}/{'default' if sb.default else 'out'}、{mode}@{at}" \
               f"{'+' + str(second) if second else ''}、{injector.hit}、rc={rc}）"

    if not world_same(sb, before_world, world(sb), injected=at is not None):
        problems.append(where("書き出し先と領分の外が変わった"))
    if sb.default and sb.out_state not in bs.WHOLE:
        prefix = sb.out + os.sep
        if any(p.startswith(prefix) for p in injector.reads):
            problems.append(where("既定の書き出し先の前の世代を読んだ"))
    if (mode in ("denied", "zero", "blk") and injector.hit not in ("unlock", "close")
            and rc == 0 and not already_failing):
        # 9.2: 確定の前の失敗は、前からあった残りの片付けのほかは、失敗で終わる。警告があっても、0 で終わってはならない
        if role_of(sb, injector, at, commit, leftovers) == "pre":
            problems.append(where("確定の前の「分からない」の失敗を吸収して 0 で終わった"))
        elif not new_warnings:
            problems.append(where("「分からない」の失敗を、警告なしに吸収して 0 で終わった"))
    # 上で基準を当てない場所（手を入れなくても失敗する呼び出し）は、手を入れない実行の側で、警告があるかを確かめる
    if (at is None and rc == 0 and not warnings
            and any(t not in (FileNotFoundError, NotADirectoryError) for t in injector.failed.values())):
        problems.append(where("手を入れない実行で起きた「分からない」の失敗を、警告なしに吸収して 0 で終わった"))
    if protected:
        if after_out != before_out:
            problems.append(where("browse のものでない書き出し先か、Wiki のルートが変わった"))
        if rc == 0:
            problems.append(where("browse のものでない書き出し先か、Wiki のルートで 0 で終わった"))
    elif rc == 0:
        if content(after_out, manifest=False) != EXP_N or bs.MANIFEST not in (after_out or {}):
            problems.append(where("0 で終わったのに、書き出し先が新しい世代でない"))
    elif at is None:
        problems.append(where("失敗のない実行が 0 で終わらなかった"))
    else:
        # 9.2: 役目を先に決め、その役目が許す終わり方を、どの終わり方（0、0 でない、強制停止）にも当てる
        c = content(after_out)
        c_new = content(after_out, manifest=False) == EXP_N and bs.MANIFEST in (after_out or {})
        if role_of(sb, injector, at, commit, leftovers) == "post":
            if rc != "crash":
                problems.append(where("確定のあとの失敗で、0 でなく終わった"))
            elif not c_new:
                problems.append(where("確定のあとの強制停止で、書き出し先が新しい世代でない"))
        else:
            # 世代は、一覧（.browse-generation）も含めて比べる（設計の 11。一覧だけを失った退避の世代は戻せない）
            olds = [content(tree(os.path.join(sb.work, n)))
                    for n in (os.listdir(sb.work) if real_dir(sb.work) else [])
                    if n.startswith("old-") and real_dir(os.path.join(sb.work, n))]
            # 最後に公開した世代 G は、砂場の作りで決まる（書き出し先にあった世代か、作業用の old-5）。
            G = P if P not in (None, {}) else old5
            if G is None:
                ok = c in (None, {}) or after_out == before_out or (rc == "crash" and c_new)
            else:
                ok = c == G or G in olds or (rc == "crash" and c_new)
            if not ok:
                problems.append(where("0 でないのに、最後に公開した世代が、書き出し先にも作業用の退避にも残っていない"))

    # 次の実行（手を入れない）
    counter = Injector()
    rc2 = run_build(sb, counter)
    after2 = tree(sb.out)
    if not world_same(sb, before_world, world(sb), injected=at is not None):
        problems.append(where("次の実行で、書き出し先と領分の外が変わった"))
    if protected:
        if rc2 != "stop" or after2 != before_out:
            problems.append(where("次の実行が、browse のものでない書き出し先か、Wiki のルートで止まらなかった"))
    else:
        if rc2 != 0 or content(after2, manifest=False) != EXP_N:
            problems.append(where(f"次の実行が新しい世代に着かなかった（rc={rc2}）"))
        else:
            left = sorted(set(os.listdir(sb.work)) - {bs.WORK_MARKER, "build.lock"})
            if left and sb.out_state != "gen+hardlink":
                problems.append(where(f"作業用に残りがある: {left}"))
            if left and sb.out_state == "gen+hardlink":
                NOTES.add("読み取り専用のファイルは消せず、作業用に残る（属性を変えないため）: " + ", ".join(left))
    return problems, counter.count


def count_calls(make, names=False):
    sb = make()
    try:
        injector = Injector()
        run_build(sb, injector)
        return (injector.count, injector.names) if names else injector.count
    finally:
        sb.close()


ONLY = {"zero": ("file_id",), "blk": ("lstat", "stat")}     # 正常に戻る異常は、その名前の呼び出しにだけ入れる


def _skip_mode(mode, name):
    return mode in ONLY and ((not fs.NT and mode == "blk") or name not in ONLY[mode])


def sweep_build(out_state, work_state, default, modes, depth2=False):
    def make():
        return Sandbox(out_state, work_state, default)
    probe = make()
    skipped = probe.skipped
    probe.close()
    if skipped:
        SKIPPED.append(f"{out_state}/{work_state}/{'default' if default else 'out'}: {skipped}")
        return 0, 0, []
    total, names = count_calls(make, names=True)
    problems, runs = [], 0
    sb = make()
    try:
        found, _ = check_build(sb, None, None)        # 失敗のないときの約束
        problems += found
        runs += 1
        baseline, natural, commit = Counter(LAST_WARNINGS), dict(LAST_FAILED), LAST_COMMIT[0]
    finally:
        sb.close()
    for mode in modes:
        for at in range(1, total + 1):
            if _skip_mode(mode, names[at - 1]):
                continue
            sb = make()
            try:
                found, _ = check_build(sb, at, mode, baseline=baseline, natural=natural, commit=commit)
                problems += found
                runs += 1
            finally:
                sb.close()
    if depth2:
        for at in range(1, total + 1):
            sb = make()
            try:
                probe = Injector(at, "denied")
                run_build(sb, probe)
                last = probe.count
            finally:
                sb.close()
            for second in range(at + 1, min(last, at + SECOND_WINDOW) + 1):
                sb = make()
                try:
                    found, _ = check_build(sb, at, "denied", second, baseline=baseline, natural=natural, commit=commit)
                    problems += found
                    runs += 1
                finally:
                    sb.close()
    return total, runs, problems


# ---------------------------------------------------------------------------
# サーバーの記録の探索
# ---------------------------------------------------------------------------

STATE_STATES = ("absent", "stale-record", "leftover-new", "unmarked-empty", "stale+leftover", "other-owner", "nodata",
                "lock-dangling", "lock-symlink", "lock-hardlink", "marker-symlink", "marker-owner-link",
                "record-link", "record-new-link")


def make_state(sb, state):
    d = sb.state_dir
    owner = sb.owner.encode("utf-8")
    if state in ("absent", "nodata"):      # nodata は、<data_dir> そのものがない（砂場の作りで決まる）
        return None
    os.makedirs(d)
    if state == "unmarked-empty":
        return None
    if state in ("record-link", "record-new-link"):
        # 記録とその置き換えの一時ファイルの名前が、利用者のファイルへのシンボリックリンク。先は、正しい持ち主の値を
        # 持つ記録の形をしている
        write(os.path.join(d, bs.SERVER_MARKER), owner)
        write(os.path.join(d, "server.lock"), b"")
        target = os.path.join(sb.root, "elsewhere-rec", "rec.json")
        write(target, json.dumps({"instance": "user", "owner": sb.owner}).encode())
        try:
            os.symlink(target, os.path.join(d, "server.json" if state == "record-link" else "server.json.new"))
        except OSError as e:
            return f"リンクを作れない: {type(e).__name__}"
        return None
    if state in bs.LINK_STATES:
        if state not in ("marker-symlink", "marker-owner-link"):
            write(os.path.join(d, bs.SERVER_MARKER), owner)
        return bs.place_link(state, os.path.join(d, "server.lock"), os.path.join(d, bs.SERVER_MARKER), sb.wiki,
                             sb.owner)
    mark = b"B" if state == "other-owner" else owner
    write(os.path.join(d, bs.SERVER_MARKER), mark)
    write(os.path.join(d, "server.lock"), b"")
    if state in ("stale-record", "stale+leftover", "other-owner"):
        write(os.path.join(d, "server.json"), json.dumps({"instance": "old", "owner": mark.decode()}).encode())
    if state in ("leftover-new", "stale+leftover"):
        write(os.path.join(d, "server.json.new"), b'{"inst')
    return None


def start(sb, instance, owner=None):
    return fs.serve_start(sb.wiki, sb.browse_root, sb.state_dir, owner or sb.owner,
                          lambda: {"instance": instance})


def run_server(sb, injector, phase):
    """起動して終了する。phase='start' なら起動だけに、'finish' なら終了だけに手を入れる。"""
    fs.WARNINGS.clear()
    server = None
    try:
        fs.X = injector if phase == "start" else fs.Os()
        outcome, server = start(sb, "new")
        if outcome != "started":
            server = None
            return "reused"
        fs.X = injector if phase == "finish" else fs.Os()
        if phase == "finish":
            injector.fds.add(server.lock.fd)      # 強制停止で、ロックも外れる
        fs.serve_finish(server)
        return "ok"
    except fs.Stop:
        return "stop"
    except (fs.Unknown, fs.Absent):
        return "unknown"
    except Crash:
        return "crash"
    finally:
        fs.X = fs.Os()
        if isinstance(server, fs.Server) and phase == "start" and server.lock.fd is not None:
            server.lock.release()


def lock_held(path):
    """試験の側で、ロックが取られているかを確かめる（層の関数を使わない）。"""
    fd = os.open(path, os.O_RDWR | getattr(os, "O_BINARY", 0))
    try:
        if os.name == "nt":
            import msvcrt
            try:
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            except OSError:
                return True
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            return False
        import fcntl
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        fcntl.flock(fd, fcntl.LOCK_UN)
        return False
    finally:
        os.close(fd)


def check_server(state, phase, at, mode, baseline=None, natural=None, data_link=False):
    # data_link: <data_dir> そのものがジャンクション（解く前の名前と解いたパスが違う。6.1 の確かめの覚えを量る）
    sb = Sandbox("nodata" if state == "nodata" else bs.DATA_LINK[0] if data_link else "absent", "asis", True)
    problems = []
    try:
        skipped = make_state(sb, state) or sb.skipped
        if skipped:
            SKIPPED.append(f"サーバー {state}: {skipped}")
            return [], 0
        before_world = world(sb)
        injector = Injector(at, mode)
        rc = run_server(sb, injector, phase)
        warnings = Counter(fs.WARNINGS)
        if at is None:
            LAST_WARNINGS.clear()
            LAST_WARNINGS.update(warnings)
            LAST_FAILED.clear()
            LAST_FAILED.update(injector.failed)
        new_warnings = warnings - (baseline or Counter())
        already_failing = mode == "denied" and (natural or {}).get(at) is PermissionError

        def where(label):
            return f"{label}（状態 {state}、{phase}、{mode}@{at}、{injector.hit}、rc={rc}）"
        if at is None and rc != "ok":
            problems.append(where("失敗のない起動と終了が成功しなかった"))
        if rc == "reused":
            problems.append(where("動いていないのに、使い回した"))
        # 7.1: 起動の失敗は、失敗で終わる。終了で警告して続けてよいのは、記録を消せないときだけ（警告がある）
        effective = mode == "denied" or (mode in ONLY and injector.hit in ONLY[mode])
        if (at is not None and effective and injector.hit not in ("unlock", "close")
                and not already_failing and rc == "ok"):
            if phase == "start":
                problems.append(where("起動の「分からない」の失敗を吸収して、起動した"))
            elif not new_warnings:
                problems.append(where("終了の「分からない」の失敗を、警告なしに吸収した"))
        if not world_same(sb, before_world, world(sb)):
            problems.append(where("状態のディレクトリの外が変わった"))
        lock_path = os.path.join(sb.state_dir, "server.lock")
        if os.path.exists(lock_path) and lock_held(lock_path):      # 試験の側で確かめる（層の関数を使わない）
            problems.append(where("終わったあとも、ロックが残っている"))
        # 次の起動は成功する。動いているあいだ、もう 1 つは起動せず、使い回す。
        try:
            outcome, server = start(sb, "next")
        except (fs.Stop, fs.Unknown, fs.Absent) as e:
            problems.append(where(f"次の起動が失敗した: {e}"))
        else:
            with open(os.path.join(sb.state_dir, "server.json"), "rb") as f:
                if outcome != "started" or json.loads(f.read()).get("instance") != "next":
                    problems.append(where("次の起動のあと、記録が新しくない"))
            try:
                outcome2, rec = start(sb, "second")
                if outcome2 != "reuse" or (rec or {}).get("instance") != "next":
                    problems.append(where("動いているのに、使い回さなかった"))
            except (fs.Stop, fs.Unknown, fs.Absent) as e:
                problems.append(where(f"動いているサーバーを使い回せなかった: {e}"))
            fs.serve_finish(server)
            left = sorted(set(os.listdir(sb.state_dir)) - {bs.SERVER_MARKER, "server.lock"})
            if left:
                problems.append(where(f"終了のあと、状態のディレクトリに残りがある: {left}"))
        return problems, injector.count
    finally:
        sb.close()


def sweep_server(modes, data_link=False):
    problems, runs = [], 0
    for state in STATE_STATES:
        if data_link and state == "nodata":
            continue
        for phase in ("start", "finish"):
            found, total = check_server(state, phase, None, None, data_link=data_link)
            if not total:
                continue                      # 飛ばした状態
            baseline, natural = Counter(LAST_WARNINGS), dict(LAST_FAILED)
            problems += found
            runs += 1
            for mode in modes:
                for at in range(1, total + 1):
                    found, _ = check_server(state, phase, at, mode, baseline, natural, data_link=data_link)
                    problems += found
                    runs += 1
    return runs, problems


def probe(sb, owner=None):
    state, _rec = fs.probe_server(sb.wiki, sb.browse_root, sb.state_dir, owner or sb.owner)
    return "stop-sent" if state == "running" else "not-running"


def sweep_server_root(modes):
    """<data_dir>/browse か、状態のディレクトリの名前がリンクのとき、起動、stop、動いているかの確かめが、
    どれも砂場を変えずに止まる。stop と動いているかの確かめは、目印のない空の状態のディレクトリでも何も作らない
    （設計の 6.2、7.1。8 回目のレビューの C）。"""
    problems, runs = [], 0
    ops = ("serve", "stop")

    def attempt(sb, op, injector):
        fs.X = injector
        fs.WARNINGS.clear()
        server = None
        try:
            if op == "serve":
                outcome, server = start(sb, "new")
                return outcome
            return probe(sb)
        except fs.Stop:
            return "stop"
        except (fs.Unknown, fs.Absent):
            return "unknown"
        except Crash:
            return "crash"
        finally:
            fs.X = fs.Os()
            if isinstance(server, fs.Server):
                server.lock.release()

    def make(state):
        sb = Sandbox(state if state in bs.ROOT_LINK else "absent", "asis", True)
        if state == "state-link":
            target = os.path.join(sb.root, "elsewhere-state")
            write(os.path.join(target, bs.SERVER_MARKER), sb.owner.encode())
            write(os.path.join(target, "server.json"), json.dumps({"instance": "x", "owner": sb.owner}).encode())
            bs.junction(sb.state_dir, target)
        elif state == "unmarked-empty":
            os.makedirs(sb.state_dir)
        return sb
    for state in bs.ROOT_LINK + ("state-link", "unmarked-empty"):
        for op in ops:
            if state == "unmarked-empty" and op == "serve":
                continue                      # 起動は目印を置いてよい
            sb = make(state)
            try:
                if sb.skipped:
                    SKIPPED.append(f"サーバー {state}: {sb.skipped}")
                    continue
                counter = Injector()
                attempt(sb, op, counter)
                total, names = counter.count, list(counter.names)
            finally:
                sb.close()
            for mode in (None, *modes):
                for at in ([None] if mode is None else range(1, total + 1)):
                    if mode is not None and _skip_mode(mode, names[at - 1]):
                        continue
                    sb = make(state)
                    try:
                        before = tree(sb.root)
                        injector = Injector(at, mode)
                        result = attempt(sb, op, injector)
                        runs += 1
                        label = f"（{state}、{op}、{mode}@{at}、{injector.hit}、結果 {result}）"
                        if state == "unmarked-empty":
                            if mode is None and result != "not-running":
                                problems.append("目印のない空の状態のディレクトリで、「動いていない」と答えなかった" + label)
                        elif mode is None and result != "stop":
                            problems.append("失敗のない実行で、領分の名前のリンクで止まらなかった" + label)
                        # 「ない」の答えから、何も作らずに「動いていない」と答えるのは許す（設計の 6.2）。その先を使った結果だけを破れにする
                        if result in ("started", "reuse", "stop-sent"):
                            problems.append("領分の名前がリンクか空なのに、その先を使った" + label)
                        if tree(sb.root) != before:
                            problems.append("砂場が変わった" + label)
                    finally:
                        sb.close()
    return runs, problems


def sweep_shared(modes):
    """同じ wiki_key の別の Wiki（B）が、A の動いているサーバーを、使い回さず、止めないことを確かめる。"""
    problems, runs = [], 0
    for op in ("serve", "stop"):
        def attempt(sb, injector, op=op):
            fs.X = injector
            try:
                if op == "serve":
                    outcome, _ = start(sb, "b", owner="B")
                    return outcome
                return probe(sb, owner="B")
            except fs.Stop:
                return "stop"
            except (fs.Unknown, fs.Absent):
                return "unknown"
            except Crash:
                return "crash"
            finally:
                fs.X = fs.Os()
        sb = Sandbox("absent", "asis", True)
        try:
            _, a = start(sb, "a")
            counter = Injector()
            attempt(sb, counter)
            total = counter.count
            a.lock.release()
        finally:
            sb.close()
        for mode in (None, *modes):
            for at in ([None] if mode is None else range(1, total + 1)):
                sb = Sandbox("absent", "asis", True)
                try:
                    _, a = start(sb, "a")
                    before = tree(sb.root)
                    injector = Injector(at, mode)
                    result = attempt(sb, injector)
                    runs += 1
                    label = f"（B の {op}、{mode}@{at}、{injector.hit}、結果 {result}）"
                    if mode is None and result != "stop":
                        problems.append("失敗のない実行で、別の Wiki のサーバーだと知らせて止まらなかった" + label)
                    if result in ("reuse", "started", "stop-sent"):
                        problems.append("別の Wiki のサーバーを、使い回したか、止めようとした" + label)
                    if not lock_held(os.path.join(sb.state_dir, "server.lock")):
                        problems.append("A のロックが外れた" + label)
                    if tree(sb.root) != before:
                        problems.append("砂場が変わった" + label)
                    a.lock.release()
                finally:
                    sb.close()
    return runs, problems


def find_call(calls, predicate):
    for i, (name, args) in enumerate(calls, start=1):
        if predicate(name, args):
            return i
    return None


def _shadow(sb, files=None):
    """今の砂場の写しで、手を入れずに流した呼び出しの記録。"""
    shadow = Sandbox(sb.out_state, "asis", sb.default)
    try:
        shutil.rmtree(shadow.root)
        shutil.copytree(sb.root, shadow.root, symlinks=True)
        # 写しの目印は、元の砂場の Wiki の持ち主の値を持つ。同じ値を渡さないと、写しだけが「引き継ぐ」経路に入り、
        # 呼び出しの番号がずれる
        shadow.owner = sb.owner
        rec = Injector()
        run_build(shadow, rec, files)
        return rec.calls
    finally:
        shadow.close()


def scenario_rewind():
    """0.10.0 の既定の書き出し先から始め、1 つずつの失敗を 3 回の実行に分けて入れる。最後に公開した世代が残ること。"""
    problems = []
    for default in (True, False):
        sb = Sandbox("legacy" if default else "gen", "asis", default)
        try:
            # 1 回目: 新しい世代 G1 を公開する。確定のあとの old → del の付け替えだけを失敗させる
            at = find_call(_shadow(sb), lambda n, a: n == "rename" and os.path.basename(a[1]).startswith("del-"))
            rc1 = run_build(sb, Injector(at, "denied"))
            # 2 回目: G2 を作り、前の世代（G1）を old-N に退避した直後に、強制停止する
            at = find_call(_shadow(sb, FILES_N2), lambda n, a: n == "rename" and os.path.basename(a[1]).startswith("old-"))
            rc2 = run_build(sb, Injector(at + 1, "crash"), FILES_N2)
            # 3 回目: 復旧のあと、新しい世代を作り始めたところで失敗させる
            at = find_call(_shadow(sb, FILES_N2), lambda n, a: n == "mkdir" and os.path.basename(a[0]).startswith("tmp-"))
            rc3 = run_build(sb, Injector(at, "denied"), FILES_N2)
            got = content(tree(sb.out), manifest=False)
            if got != EXP_N:
                problems.append(f"最後に公開した世代（G1）が残っていない（{'既定' if default else '--out'}、"
                                f"rc={rc1},{rc2},{rc3}、書き出し先の中身 {sorted(got or {})[:3]}）")
        finally:
            sb.close()
    return problems


USER_DELETES = [("gen", "asis", False), ("gen", "leftovers", False), ("absent+old", "asis", False),
                ("gen", "asis", True)]


def sweep_user_deletes(cases, modes=("crash", "half")):
    """強制停止のあとで、利用者が書き出し先を消してから、手を入れずに書き出す。

    途中で消していた前の世代を、公開した世代として戻さないことを確かめる。次の実行の復旧の付け替えの直後に失敗を入れ、
    0 でなく終わったときに、書き出し先が、ないか空か、全体のそろった世代（前の世代か新しい世代）であることも確かめる。
    """
    problems, runs = [], 0
    whole = (expected(FILES_P), EXP_N)
    for out_state, work_state, default in cases:
        total = count_calls(lambda: Sandbox(out_state, work_state, default))
        for mode in modes:
            for at in range(1, total + 1):
                def after_delete():
                    """強制停止の実行と、利用者の削除までを作る。強制停止で書き出し先が残らなければ None。"""
                    sb = Sandbox(out_state, work_state, default)
                    before = world(sb)
                    injector = Injector(at, mode)
                    if run_build(sb, injector) != "crash" or not os.path.isdir(sb.out):
                        sb.close()
                        return None, None, None
                    shutil.rmtree(sb.out)          # 利用者が書き出し先を消す
                    return sb, before, injector
                sb, before_world, injector = after_delete()
                if sb is None:
                    continue
                label = f"（{out_state}/{work_state}/{'default' if default else 'out'}、{mode}@{at}、{injector.hit}）"
                try:
                    runs += 1
                    counter = Injector()
                    rc2 = run_build(sb, counter)
                    if rc2 != 0 or content(tree(sb.out), manifest=False) != EXP_N:
                        problems.append(f"書き出し先を消したあとの書き出しが、新しい世代に着かなかった（rc={rc2}）{label}")
                    if not world_same(sb, before_world, world(sb)):
                        problems.append(f"書き出し先を消したあとの書き出しで、領分の外が変わった{label}")
                    restore = next((i for i, (name, target) in enumerate(zip(counter.names, counter.targets), 1)
                                    if name == "rename" and isinstance(target, tuple)
                                    and os.path.normcase(target[1]) == os.path.normcase(sb.out)
                                    and os.path.basename(target[0]).startswith("old-")), None)
                finally:
                    sb.close()
                if restore is None:
                    continue
                sb, _, _ = after_delete()
                try:
                    runs += 1
                    rc3 = run_build(sb, Injector(restore + 1, "denied"))
                    c = content(tree(sb.out), manifest=False)
                    if rc3 != 0 and c not in (None, {}) and c not in whole:
                        problems.append(f"書き出し先を消したあとの、復旧の直後の失敗で、途中の世代が書き出し先に残った"
                                        f"（rc={rc3}）{label}")
                finally:
                    sb.close()
    return runs, problems


# ---------------------------------------------------------------------------
# 実行
# ---------------------------------------------------------------------------

MODES = ("denied", "absent", "short", "crash", "half", "zero", "blk")
SECOND_WINDOW = 30      # 2 つ目の失敗は、1 つ目のあとの 30 回の呼び出しまでに入れる（片付けと戻しは、すぐあとに来る）
CONTROLS = {
    "skip_gate": [("gen+extra", "asis", False), ("userdir", "asis", False)],
    "follow_links": [("gen", "junction", False)],
    "commit_then_fail": [("gen", "asis", False)],
    "chmod_on_delete": [("gen+hardlink", "asis", False)],
    "no_root_guard": [("wikiroot", "asis", False), ("insidewiki", "asis", False), ("datainwiki", "asis", True)],
    "climb_on_absent": [("insidewiki", "asis", False)],
    "default_verifies": [("gen", "asis", True)],
    "swallow_close": [("absent", "asis", False)],
    "silent_post_commit": [("gen", "asis", False), ("gen+hardlink", "asis", False)],
    "coarse_warning": [("gen+hardlink", "asis", False)],
    "report_fails_unit": [("absent", "asis", False)],
    "swallow_marker_failure": [("absent", "asis", False)],
    "fallback_rmdir": [("absent", "junction", False), ("gen+hardlink", "junction", True)],
    "follow_on_open": [("absent", "lock-dangling", False), ("gen", "lock-dangling", True)],
    "discard_old_first": [("empty+old", "asis", False), ("absent+old", "asis", True)],
    "warn_on_marker_close": [("absent", "asis", False)],
    "enter_root_unchecked": [("browse-junction", "asis", True), ("browse-junction", "asis", False)],
    "raise_post_listdir": [("gen", "asis", False)],
    "cache_ids_by_name": [("gen+datajunction", "asis", True)],
    "recover_unchecked": [("absent", "old-junction", False)],
    "accept_out_link": [("outlink-junction", "asis", True)],
}
SERVER_CONTROLS = (
    ("warn_on_record_failure", lambda: sweep_server(MODES)[1]),
    ("recover_by_published_seq", scenario_rewind),
    ("delete_in_place", lambda: sweep_user_deletes(USER_DELETES)[1]),
    ("refuse_unknown_entries", lambda: sweep_server(MODES)[1]),
    ("skip_owner", lambda: sweep_shared(MODES)[1]),
    ("enter_root_unchecked", lambda: sweep_server_root(MODES)[1]),
)


def run_control(mutant, run):
    fs.MUTANTS.add(mutant)
    try:
        return run()
    finally:
        fs.MUTANTS.discard(mutant)


def control_cases(mutant, modes=MODES):
    found = []
    for out_state, work_state, default in CONTROLS[mutant]:
        _, _, problems = sweep_build(out_state, work_state, default, modes)
        found += problems
    return found


def main(argv=None):
    """速く済むものから流し、節ごとにすぐ出す（途中で止まっても、そこまでの結果が残る）。"""
    argv = sys.argv[1:] if argv is None else argv
    quick = "--quick" in argv
    started = time.time()
    all_problems = []

    def out(text=""):
        print(text, flush=True)

    out(f"Python {sys.version.split()[0]}、{sys.platform}")
    for title, (runs, problems) in (
            ("サーバーの記録", sweep_server(MODES)),
            ("サーバーの記録（<data_dir> そのものがジャンクション）", sweep_server(MODES, data_link=True)),
            ("領分の名前がリンク、目印のない空の状態のディレクトリ（起動、stop と動いているかの確かめ）",
             sweep_server_root(MODES)),
            ("同じ場所を使う別の Wiki", sweep_shared(MODES)),
            ("強制停止のあとで、利用者が書き出し先を消す", sweep_user_deletes(USER_DELETES))):
        all_problems += problems
        out(f"\n## {title}\n\n実行 {runs} 回、破れた決まり {len(problems)} 件")
    rewind_problems = scenario_rewind()
    all_problems += rewind_problems
    out(f"\n## 番号の巻き戻りと復旧（3 回の実行に 1 つずつの失敗）\n\n破れた決まり {len(rewind_problems)} 件")

    out("\n## 対照\n\n| 対照 | 見つけた件数 | 最初の 1 件 |\n| --- | --- | --- |")
    missed = []
    for mutant in CONTROLS:
        found = run_control(mutant, lambda m=mutant: control_cases(m))
        if not found:
            missed.append(mutant)
        out(f"| {mutant} | {len(found)} | {found[0] if found else '見つからなかった'} |")
    for label, run in SERVER_CONTROLS:
        found = run_control(label, run)
        if not found:
            missed.append(label + "（サーバー）")
        out(f"| {label}（サーバーなど） | {len(found)} | {found[0] if found else '見つからなかった'} |")

    out("\n## 書き出し\n\n| 書き出し先の種類 | 書き出し先の状態 | 作業用の状態 | 口の呼び出し | 実行 | 破れた決まり |\n"
        "| --- | --- | --- | --- | --- | --- |")
    for out_state, work_state, default in bs.build_cases(quick):
        depth2 = (not quick) and not default and out_state in ("gen", "absent+old") and work_state in ("asis", "leftovers")
        total, runs, problems = sweep_build(out_state, work_state, default, MODES, depth2)
        all_problems += problems
        out(f"| {'既定' if default else '--out'} | {out_state} | {work_state} | {total} | {runs} | {len(problems)} |")

    if SKIPPED:
        out("\n## 飛ばした状態（合格にしていない）\n")
        for item in SKIPPED:
            out("- " + item)
    if NOTES:
        out("\n## 気づき\n")
        for note in sorted(NOTES):
            out("- " + note)
    if missed:
        out("\n## 見つからなかった対照\n")
        for m in missed:
            out("- " + m)
    if all_problems:
        out(f"\n## 破れた決まり（{len(all_problems)} 件。先頭 40 件）\n")
        seen = []
        for p in all_problems:
            if p not in seen:
                seen.append(p)
        for p in seen[:40]:
            out("- " + p)
    out(f"\n{time.time() - started:.0f} 秒")
    return 1 if all_problems or missed else 0


if __name__ == "__main__":
    sys.exit(main())
