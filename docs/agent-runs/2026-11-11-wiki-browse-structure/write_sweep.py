"""write_model.py に、OS の呼び出しの N 回目に手を入れる探索をかける。製品の試験ではない。

探索:
- 手を入れない: 失敗のない実行が、決めた状態に着く（失敗のないときの約束）。
- 失敗: N 回目を PermissionError（分からない）か FileNotFoundError（ない）にする。書いたファイルの close の失敗は、
  遅れて出た書き込みの失敗として、ファイルの中身を失わせてから返す。
- 短い書き込み: N 回目が書き込みなら、半分だけ書いて、正常に戻る。
- 強制停止: N 回目で止まる。それ以降の OS の呼び出しは 1 つも実行されず、開いていたファイルは閉じる
  （プロセスが止まり、OS がロックを外したのと同じ）。half は、N 回目が書き込みなら、半分だけ書いてから止まる。
- 2 つ目の失敗: 1 つ目の失敗のあとの呼び出し（片付け）にも、失敗を入れる。

基準（試作の関数を使わずに、砂場の木を自分で読んで決める）:
- 世界の差分: 領分と、その実行に指した書き出し先の外は、実行の前後で、名前、種類、中身、属性（読み取り専用か、
  更新時刻）が変わらない。ディレクトリも量る。中に項目を足し引きする書き出し先の親だけは、更新時刻の変化を許す。
- 書き出し: 0 で終われば、書き出し先の木は、描くべきファイルの表から計算した木と同じ。0 でなければ前のまま
  （P）か、入れ替えの途中の形。
- browse の書き出しと確かめられない書き出し先（--out）と、Wiki のルートは、どの場合も変わらない。
- 既定の書き出し先では、前の世代を読まない。
- 「分からない」の失敗を入れて 0 で終わったら、確定の前でも後でも、同じ状態で手を入れない実行にない、新しい警告がある。
  手を入れなくても同じ呼び出しが同じ型で失敗する場所に入れたときは、新しい失敗ではないので、この基準を当てない。
  その代わり、手を入れない実行で「分からない」の失敗が起きて 0 で終わったなら、警告がある。
- 次の実行: 手を入れずにもう一度実行すると、決めた状態に着く。作業用に残りがない。
- サーバー: 終了、失敗、強制停止のあとは「動いていない」。次の起動は成功する。別の Wiki のサーバーを、
  使い回さず、止めない。

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
from collections import Counter

import write_model as m

FILES_P = {"index.html": b"<p>previous</p>", "concepts/a.html": b"<p>a v1</p>", "assets/app.js": b"// v1"}
FILES_N = {"index.html": b"<p>new</p>" * 40, "concepts/a.html": b"<p>a v2</p>", "concepts/b.html": b"<p>b</p>",
           "assets/app.js": b"// v2"}

CALLS = ("lstat", "stat_id", "realpath", "scandir_open", "scandir_next", "mkdir", "open_excl", "open_read",
         "open_lock", "write", "read", "close", "rename", "replace", "unlink", "rmdir", "stdout_write",
         "try_lock", "unlock")


class Crash(BaseException):
    pass


class Injector(m.Os):
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
            if self.mode == "zero" and name == "stat_id":
                return (os.stat(args[0]).st_dev, 0)          # 識別子 0 の成功（Windows の os.stat の形）
            if self.mode == "blk" and name == "lstat":
                import types                                 # 属性を取れずにブロックデバイスと返る形
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
    real = getattr(m.Os, name)

    def method(self, *args):
        early = self._before(name, args)
        if early is not None:
            return early
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
              "absent+old", "empty+old", "wikiroot", "insidewiki", "nodata")
WORK_STATES = ("asis", "leftovers", "junction", "unmarked-empty")
# 作業用のロックと目印の名前に、利用者が置いたリンク（7 版目。6 回目の設計のレビューの重大 1）
LINK_STATES = ("lock-dangling", "lock-symlink", "lock-hardlink", "marker-symlink", "marker-owner-link")
LINK_OUT_STATES = ("absent", "gen")
FOREIGN = ("gen+extra", "gen+edited", "userdir", "legacy")
WHOLE = ("wikiroot", "insidewiki", "datainwiki")     # 砂場の全体が変わってはならない（Wiki のルートと重なる）
# <data_dir>/browse の名前がリンク（8 版目。7 回目の設計のレビューの重大 1）。どの実行も、砂場を変えずに止まる
ROOT_LINK = ("browse-junction", "browse-symlink")
# <data_dir> そのものがジャンクション（利用者が指した場所への道）。browse は、その先の実の browse を領分として使う
DATA_LINK = ("gen+datajunction",)
# 領分のディレクトリそのものの名前がジャンクション（作業用は書き出し、状態はサーバーの探索）。使わずに止まる
WORK_LINK = "work-link"


def place_link(state, lock, marker, wiki):
    """ロックか目印の名前に、Wiki の中を指すリンクを置く。作れなければ、理由を返す（その状態は飛ばし、合格にしない）。"""
    try:
        if state == "lock-dangling":
            os.symlink(os.path.join(wiki, "created.md"), lock)
        elif state == "lock-symlink":
            os.symlink(os.path.join(wiki, "a.md"), lock)
        elif state == "lock-hardlink":
            os.link(os.path.join(wiki, "a.md"), lock)
        elif state == "marker-symlink":
            os.symlink(os.path.join(wiki, "a.md"), marker)
        elif state == "marker-owner-link":
            # リンクの先が、正しい持ち主の値（A）を持つ。試作は、リンクの先を持ち主の証にしない（設計の 6.2）
            owner_file = os.path.join(os.path.dirname(wiki), "user", "owner.txt")
            write(owner_file, b"A")
            os.symlink(owner_file, marker)
    except OSError as e:
        return f"リンクを作れない: {type(e).__name__}"
    return None


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
        self.skipped = None
        self.data = self.data_real = os.path.join(r, "data")
        if out_state in ROOT_LINK:
            # レビューの反例: <data_dir>/browse が、利用者のディレクトリへのリンク。その先に、browse の名前と同じ
            # ディレクトリと、利用者のファイルがある
            os.makedirs(self.data)
            elsewhere = os.path.join(r, "elsewhere")
            write(os.path.join(elsewhere, "KEY", "private.txt"), b"keep me")
            write(os.path.join(elsewhere, "KEY.browse-work", m.WORK_MARKER), b"A")
            write(os.path.join(elsewhere, "KEY.server", m.SERVER_MARKER), b"A")
            write(os.path.join(elsewhere, "KEY.server", "server.json"), b'{"instance": "x", "owner": "A"}')
            try:
                if out_state == "browse-junction":
                    junction(os.path.join(self.data, "browse"), elsewhere)
                else:
                    os.symlink(elsewhere, os.path.join(self.data, "browse"), target_is_directory=True)
            except OSError as e:
                self.skipped = f"リンクを作れない: {type(e).__name__}"
        elif out_state in DATA_LINK:
            self.data_real = os.path.join(r, "udata")
            os.makedirs(os.path.join(self.data_real, "browse"))
            junction(self.data, self.data_real)
        elif out_state != "nodata":
            os.makedirs(os.path.join(r, "data", "browse"))
        self.wiki = os.path.join(r, "wiki")
        if default:
            self.out = os.path.join(r, "data", "browse", "KEY")
        elif out_state == "wikiroot":
            os.makedirs(os.path.join(r, "emptywiki"))
            self.wiki = os.path.join(r, "emptywiki")
            self.out = self.wiki
        elif out_state == "insidewiki":
            self.out = os.path.join(r, "wiki", "site")
        else:
            self.out = os.path.join(r, "exports", "site")
        if default and out_state == "datainwiki":
            self.wiki = os.path.join(r, "data")         # data_dir が Wiki のルートの下にある
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
            write(os.path.join(work, m.WORK_MARKER), b"A" if default else b"")
            put_generation(os.path.join(work, "old-5"), FILES_P, 5)
        if work_state not in ("asis", WORK_LINK) and not os.path.isdir(work):
            os.makedirs(work)
            if work_state not in ("unmarked-empty", "marker-symlink", "marker-owner-link"):
                write(os.path.join(work, m.WORK_MARKER), b"A" if default else b"")
        if work_state in LINK_STATES:
            self.skipped = place_link(work_state, os.path.join(work, "build.lock"), os.path.join(work, m.WORK_MARKER),
                                      os.path.join(r, "wiki"))
        if work_state == "leftovers":
            write(os.path.join(work, "tmp-7", "index.html"), b"<p>half")
            write(os.path.join(work, "del-6", "concepts", "a.html"), b"<p>a v0</p>")
            write(os.path.join(work, "seq"), b"7\n")
            write(os.path.join(work, "build-report.json"), b"{}")
        elif work_state == WORK_LINK:
            # 作業用のディレクトリの名前が、目印を持つ利用者のディレクトリへのジャンクション
            write(os.path.join(r, "elsewhere-work", m.WORK_MARKER), b"A" if default else b"")
            write(os.path.join(r, "elsewhere-work", "keep.txt"), b"keep")
            junction(work, os.path.join(r, "elsewhere-work"))
        elif work_state == "junction":
            os.makedirs(os.path.join(work, "tmp-8"))
            junction(os.path.join(work, "tmp-8", "assets"), os.path.join(r, "user", "assets"))
            junction(os.path.join(work, "tmp-8", "wiki"), os.path.join(r, "wiki"))

    def real(self, path):
        """名前を、砂場の中の実の場所に直す。<data_dir> がジャンクションなら、その先の名前にする（世界の差分は
        リンクをたどらずに木を読むので、領分は実の場所で数える）。"""
        if self.data_real != self.data and (path == self.data or path.startswith(self.data + os.sep)):
            return self.data_real + path[len(self.data):]
        return path

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


LOCK_NAMES = ("build.lock", "server.lock")


def _attrs(st):
    return bool(st.st_mode & stat.S_IWRITE), st.st_mtime_ns


def tree(path):
    """木を自分で読む。{相対パス: (種類, ハッシュ, 書き込みできるか, 更新時刻)}。根そのものは "."。リンクはたどらない。"""
    if not os.path.lexists(path):
        return None
    found = {}

    def walk(directory, prefix):
        for name in sorted(os.listdir(directory)):
            full, rel = os.path.join(directory, name), prefix + name
            st = os.lstat(full)
            if stat.S_ISLNK(st.st_mode) or getattr(st, "st_file_attributes", 0) & 0x400:
                found[rel] = ("link", None, *_attrs(st))
            elif stat.S_ISDIR(st.st_mode):
                found[rel] = ("dir", None, *_attrs(st))
                walk(full, rel + "/")
            else:
                try:
                    with open(full, "rb") as f:
                        digest = hashlib.sha256(f.read()).hexdigest()
                except PermissionError:
                    # 取られているロックは読めない（Windows の範囲のロック）。browse のロックの名前のときだけ、中身を量らない
                    if name not in LOCK_NAMES:
                        raise
                    digest = "lock"
                found[rel] = ("file", digest, *_attrs(st))
    st = os.lstat(path)
    if os.path.isdir(path) and not os.path.islink(path):
        found["."] = ("dir", None, *_attrs(st))
        walk(path, "")
    return found


def content(t):
    """一覧のファイルと根を除き、種類とハッシュだけにする（世代どうしを比べる）。"""
    if t is None:
        return None
    return {k: v[:2] for k, v in t.items() if k not in (m.MANIFEST, ".")}


def expected(files):
    t = {name: ("file", hashlib.sha256(data).hexdigest()) for name, data in files.items()}
    for name in files:
        parts = name.split("/")
        for i in range(1, len(parts)):
            t["/".join(parts[:i])] = ("dir", None)
    return t


def rel(sb, path):
    return os.path.relpath(path, sb.root).replace(os.sep, "/")


def world(sb):
    """砂場の全体の木。"""
    return tree(sb.root)


def _parent(k):
    return k.rsplit("/", 1)[0] if "/" in k else "."


def world_same(sb, before, after, injected=False):
    """領分と、指した書き出し先の外が変わっていないか（設計の 9.1）。

    browse が新しく作るディレクトリと、名前を付け替えるディレクトリの親だけは、更新時刻の変化を許す（設計の 2.1）。
    新しく作ってよいのは、領分と書き出し先そのものと、その祖先（data_dir がないとき）だけである。
    Wiki のルートと重なる状態では、手を入れない実行は、砂場の全体が変わらない（止まり、何も変えない）。
    失敗を入れた実行（とそのあとの実行）は、Wiki のルートの下が、ルートそのものの属性を含めて変わらず、
    ほかは上の規則に従う（Wiki のルートの外にある領分は、作ってよい）。
    """
    if sb.out_state in ROOT_LINK or sb.work_state == WORK_LINK:
        return before == after          # 領分に入る確かめで、何も作らずに止まる（手を入れた実行も）
    if sb.out_state in WHOLE:
        if not injected:
            return before == after
        top = rel(sb, sb.wiki)

        def under(k):
            return k == top or k.startswith(top + "/")
        if {k: v for k, v in before.items() if under(k)} != {k: v for k, v in after.items() if under(k)}:
            return False
    skip = [rel(sb, sb.real(p)) for p in (sb.out, sb.work, sb.state_dir, os.path.join(sb.data, "browse"))]

    def inside(k):
        return any(k == p or k.startswith(p + "/") for p in skip)

    def ancestor_of_skip(k):
        return any(p.startswith(k + "/") for p in skip)

    allowed_mtime = {_parent(rel(sb, sb.real(sb.out)))}
    for k in after:
        if k not in before and (inside(k) or ancestor_of_skip(k)):
            allowed_mtime.add(_parent(k))
    for k in set(before) | set(after):
        if inside(k):
            continue
        if k not in before:
            if not ancestor_of_skip(k):
                return False
            continue
        if k not in after:
            return False
        a, b = before[k], after[k]
        if k in allowed_mtime:
            a, b = a[:3], b[:3]
        if a != b:
            return False
    return True


# ---------------------------------------------------------------------------
# 書き出しの探索
# ---------------------------------------------------------------------------

def run_build(sb, injector, files=None):
    m.X = injector
    m.WARNINGS.clear()
    try:
        return m.build(sb.wiki, sb.out, files or FILES_N, sb.default, owner="A")
    except m.Stop:
        return "stop"
    except (m.Unknown, m.Absent):
        return "unknown"
    except Crash:
        return "crash"
    finally:
        m.X = m.Os()


def role_of(sb, injector, at, commit, leftovers):
    """N 回目の呼び出しの役目を、試験の側で決める。'post'（確定のあと）、'leftover'（前からあった残りの片付け）、'pre'。

    確定の点は、手を入れない実行の記録で、tmp-N を書き出し先の名前にした付け替えの番号である（試作の申告ではない）。
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


def check_build(sb, at, mode, second=None, baseline=None, natural=None, commit=None):
    """1 回の実行と、そのあとの手を入れない実行を確かめる。破れた決まりの一覧を返す。

    baseline は、同じ状態で手を入れない実行が出した警告（多重集合）。手を入れた実行の警告は、これと比べて、
    新しいものがなければならない。別の理由の警告（読み取り専用のファイルを消せない、など）で、
    入れた失敗の警告を代えさせない。
    natural は、同じ状態で手を入れない実行が失敗した呼び出し（{番号: 例外の型}）。N 回目までの呼び出しは、
    手を入れない実行と同じなので、N 回目が同じ型で失敗しているなら、入れた失敗は新しい失敗ではない。
    """
    problems = []
    before_world, before_out = world(sb), tree(sb.out)
    old5 = content(tree(os.path.join(sb.work, "old-5")))
    leftovers = [os.path.join(sb.work, n) for n in (os.listdir(sb.work) if os.path.isdir(sb.work) else [])
                 if n.startswith(("tmp-", "del-")) or n in m.LEGACY]
    protected = ((sb.out_state in FOREIGN and not sb.default) or sb.out_state in WHOLE or sb.out_state in ROOT_LINK
                 or sb.work_state == WORK_LINK)
    injector = Injector(at, mode, second)
    rc = run_build(sb, injector)
    warnings = Counter(m.WARNINGS)
    LAST_WARNINGS.clear()
    LAST_WARNINGS.update(warnings)
    LAST_FAILED.clear()
    LAST_FAILED.update(injector.failed)
    LAST_COMMIT[0] = commit_index(sb, injector)
    new_warnings = warnings - (baseline or Counter())
    already_failing = mode == "denied" and (natural or {}).get(at) is PermissionError
    after_out = tree(sb.out)
    N, P = expected(FILES_N), content(before_out)

    def where(label):
        return f"{label}（{sb.out_state}/{sb.work_state}/{'default' if sb.default else 'out'}、{mode}@{at}" \
               f"{'+' + str(second) if second else ''}、{injector.hit}、rc={rc}）"

    if not world_same(sb, before_world, world(sb), injected=at is not None):
        problems.append(where("書き出し先と領分の外が変わった"))
    if sb.default and sb.out_state not in WHOLE:
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
        if content(after_out) != N:
            problems.append(where("0 で終わったのに、書き出し先が新しい世代でない"))
    elif at is None:
        problems.append(where("失敗のない実行が 0 で終わらなかった"))
    else:
        # 9.2: 役目を先に決め、その役目が許す終わり方を、どの終わり方（0、0 でない、強制停止）にも当てる
        c = content(after_out)
        if role_of(sb, injector, at, commit, leftovers) == "post":
            # 確定のあとの失敗は、0 で終わり、書き出し先は新しい世代である。強制停止でも、書き出し先は新しい世代である
            if rc != "crash":
                problems.append(where("確定のあとの失敗で、0 でなく終わった"))
            elif c != N:
                problems.append(where("確定のあとの強制停止で、書き出し先が新しい世代でない"))
        else:
            olds = [content(tree(os.path.join(sb.work, n)))
                    for n in (os.listdir(sb.work) if os.path.isdir(sb.work) else []) if n.startswith("old-")]
            # 最後に公開した世代 G は、砂場の作りで決まる（書き出し先にあった世代か、作業用の old-5）。
            # 確定の前は、G はいつも、書き出し先か、作業用の old-N のどれかにある（設計の 6.4、7）
            G = P if P not in (None, {}) else old5
            if G is None:
                ok = c in (None, {}) or after_out == before_out or (rc == "crash" and c == N)
            else:
                ok = c == G or G in olds or (rc == "crash" and c == N)
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
LAST_WARNINGS: Counter = Counter()      # check_build の 1 回目の実行の警告（手を入れない実行の警告を、基準の側で覚える）
LAST_FAILED: dict = {}                  # 同じく、1 回目の実行で、手を入れずに失敗した呼び出し
LAST_COMMIT: list = [None]              # 同じく、1 回目の実行の確定の点（呼び出しの番号）
SKIPPED: list = []                      # リンクを作れずに飛ばした状態


def count_calls(make, names=False):
    sb = make()
    try:
        injector = Injector()
        run_build(sb, injector)
        return (injector.count, injector.names) if names else injector.count
    finally:
        sb.close()


ONLY = {"zero": "stat_id", "blk": "lstat"}     # 正常復帰の異常は、その名前の呼び出しにだけ入れる


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
            if mode in ONLY and (os.name != "nt" and mode == "blk" or names[at - 1] != ONLY[mode]):
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
                "lock-dangling", "lock-symlink", "lock-hardlink", "marker-symlink", "marker-owner-link")


def make_state(sb, state):
    d = sb.state_dir
    if state in ("absent", "nodata"):      # nodata は、<data_dir> そのものがない（砂場の作りで決まる）
        return
    os.makedirs(d)
    if state == "unmarked-empty":
        return
    if state in LINK_STATES:
        if state not in ("marker-symlink", "marker-owner-link"):
            write(os.path.join(d, m.SERVER_MARKER), b"A")
        return place_link(state, os.path.join(d, "server.lock"), os.path.join(d, m.SERVER_MARKER), sb.wiki)
    owner = b"B" if state == "other-owner" else b"A"
    write(os.path.join(d, m.SERVER_MARKER), owner)
    write(os.path.join(d, "server.lock"), b"")
    if state in ("stale-record", "stale+leftover", "other-owner"):
        write(os.path.join(d, "server.json"), json.dumps({"instance": "old", "owner": owner.decode()}).encode())
    if state in ("leftover-new", "stale+leftover"):
        write(os.path.join(d, "server.json.new"), b'{"inst')


def run_server(sb, injector, phase):
    """起動して終了する。phase='start' なら起動だけに、'finish' なら終了だけに手を入れる。"""
    m.WARNINGS.clear()
    server = None
    try:
        m.X = injector if phase == "start" else m.Os()
        outcome, server = m.serve_start(sb.wiki, sb.state_dir, "new", "A")
        if outcome != "started":
            server = None
            return "reused"
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


def check_server(state, phase, at, mode, baseline=None, natural=None):
    sb = Sandbox("nodata" if state == "nodata" else "absent", "asis", True)
    problems = []
    try:
        skipped = make_state(sb, state)
        if skipped:
            SKIPPED.append(f"サーバー {state}: {skipped}")
            return [], 0
        before_world = world(sb)
        injector = Injector(at, mode)
        rc = run_server(sb, injector, phase)
        warnings = Counter(m.WARNINGS)
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
        # 手を入れたことが効いた実行だけに当てる（識別子 0 は stat_id に、ブロックデバイスは lstat にだけ効く）
        effective = mode == "denied" or (mode in ONLY and injector.hit == ONLY[mode])
        if (at is not None and effective and injector.hit not in ("unlock", "close")
                and not already_failing and rc == "ok"):
            if phase == "start":
                problems.append(where("起動の「分からない」の失敗を吸収して、起動した"))
            elif not new_warnings:
                problems.append(where("終了の「分からない」の失敗を、警告なしに吸収した"))
        if not world_same(sb, before_world, world(sb)):
            problems.append(where("状態のディレクトリの外が変わった"))
        lock_path = os.path.join(sb.state_dir, "server.lock")
        if os.path.exists(lock_path) and lock_held(lock_path):      # 試験の側で確かめる（試作の関数を使わない）
            problems.append(where("終わったあとも、ロックが残っている"))
        # 次の起動は成功する。動いているあいだ、もう 1 つは起動せず、使い回す。
        try:
            outcome, server = m.serve_start(sb.wiki, sb.state_dir, "next", "A")
        except (m.Stop, m.Unknown, m.Absent) as e:
            problems.append(where(f"次の起動が失敗した: {e}"))
        else:
            with open(os.path.join(sb.state_dir, "server.json"), "rb") as f:
                if outcome != "started" or json.loads(f.read()).get("instance") != "next":
                    problems.append(where("次の起動のあと、記録が新しくない"))
            try:
                outcome2, rec = m.serve_start(sb.wiki, sb.state_dir, "second", "A")
                if outcome2 != "reuse" or rec.get("instance") != "next":
                    problems.append(where("動いているのに、使い回さなかった"))
            except (m.Stop, m.Unknown, m.Absent) as e:
                problems.append(where(f"動いているサーバーを使い回せなかった: {e}"))
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
            found, total = check_server(state, phase, None, None)
            if not total:
                continue                      # 飛ばした状態
            baseline, natural = Counter(LAST_WARNINGS), dict(LAST_FAILED)
            problems += found
            runs += 1
            for mode in modes:
                for at in range(1, total + 1):
                    found, _ = check_server(state, phase, at, mode, baseline, natural)
                    problems += found
                    runs += 1
    return runs, problems


def sweep_server_root(modes):
    """<data_dir>/browse か、状態のディレクトリの名前がリンクのとき、起動、stop、動いているかの確かめが、
    どれも砂場を変えずに止まる（8 版目）。"""
    problems, runs = [], 0
    ops = ("serve", "stop", "is_running")

    def attempt(sb, op, injector):
        m.X = injector
        m.WARNINGS.clear()
        server = None
        try:
            if op == "serve":
                outcome, server = m.serve_start(sb.wiki, sb.state_dir, "new", "A")
                return outcome
            if op == "stop":
                return m.stop(sb.wiki, sb.state_dir, "A")
            return "running" if m.is_running(sb.wiki, sb.state_dir, "A") else "not-running"
        except m.Stop:
            return "stop"
        except (m.Unknown, m.Absent):
            return "unknown"
        except Crash:
            return "crash"
        finally:
            m.X = m.Os()
            if isinstance(server, m.Server):
                server.lock.release()
    def make(state):
        sb = Sandbox(state if state in ROOT_LINK else "absent", "asis", True)
        if state == "state-link":
            target = os.path.join(sb.root, "elsewhere-state")
            write(os.path.join(target, m.SERVER_MARKER), b"A")
            write(os.path.join(target, "server.json"), b'{"instance": "x", "owner": "A"}')
            junction(sb.state_dir, target)
        return sb
    for state in ROOT_LINK + ("state-link",):
        for op in ops:
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
                    if mode in ONLY and (os.name != "nt" and mode == "blk" or names[at - 1] != ONLY[mode]):
                        continue
                    sb = make(state)
                    try:
                        before = tree(sb.root)
                        injector = Injector(at, mode)
                        result = attempt(sb, op, injector)
                        runs += 1
                        label = f"（{state}、{op}、{mode}@{at}、{injector.hit}、結果 {result}）"
                        if mode is None and result != "stop":
                            problems.append("失敗のない実行で、領分の名前のリンクで止まらなかった" + label)
                        # 「ない」の答えから、何も作らずに「動いていない」と答えるのは許す（設計の 6.2）。その先を使った結果だけを破れにする
                        if result in ("started", "reuse", "stop-sent", "running"):
                            problems.append("領分の名前がリンクなのに、その先を使った" + label)
                        if tree(sb.root) != before:
                            problems.append("砂場が変わった" + label)
                    finally:
                        sb.close()
    return runs, problems


def lock_held(path):
    """試験の側で、ロックが取られているかを確かめる（試作の関数を使わない）。"""
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


def sweep_shared(modes):
    """同じ wiki_key の別の Wiki（B）が、A の動いているサーバーを、使い回さず、止めないことを確かめる。"""
    problems, runs = [], 0
    for op in ("serve", "stop"):
        def attempt(injector):
            m.X = injector
            try:
                if op == "serve":
                    outcome, _ = m.serve_start(sb.wiki, sb.state_dir, "b", "B")
                    return outcome
                return m.stop(sb.wiki, sb.state_dir, "B")
            except m.Stop:
                return "stop"
            except (m.Unknown, m.Absent):
                return "unknown"
            except Crash:
                return "crash"
            finally:
                m.X = m.Os()
        # 呼び出しの数を数える
        sb = Sandbox("absent", "asis", True)
        try:
            _, a = m.serve_start(sb.wiki, sb.state_dir, "a", "A")
            counter = Injector()
            attempt(counter)
            total = counter.count
            a.lock.release()
        finally:
            sb.close()
        for mode in (None, *modes):
            for at in ([None] if mode is None else range(1, total + 1)):
                sb = Sandbox("absent", "asis", True)
                try:
                    _, a = m.serve_start(sb.wiki, sb.state_dir, "a", "A")
                    before = tree(sb.root)
                    injector = Injector(at, mode)
                    result = attempt(injector)
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


FILES_N2 = {"index.html": b"<p>newer</p>", "concepts/a.html": b"<p>a v3</p>"}


def find_call(injector_names_args, predicate):
    for i, (name, args) in enumerate(injector_names_args, start=1):
        if predicate(name, args):
            return i
    return None


class Recorder(Injector):
    """呼び出しの名前と引数を記録する（手は入れない）。"""

    def __init__(self):
        super().__init__()
        self.calls = []

    def _before(self, name, args):
        self.calls.append((name, args))
        return super()._before(name, args)


def scenario_rewind():
    """0.10.0 の既定の書き出し先から始め、1 つずつの失敗を 3 回の実行に分けて入れる。最後に公開した世代が残ること。"""
    problems = []
    for default in (True, False):
        sb = Sandbox("legacy" if default else "gen", "asis", default)
        try:
            # 1 回目: 新しい世代 G1 を公開する。確定のあとの old → del の付け替えだけを失敗させる
            rec = Recorder()
            sb2 = Sandbox(sb.out_state, "asis", default)
            try:
                run_build(sb2, rec)
            finally:
                sb2.close()
            at = find_call(rec.calls, lambda n, a: n == "rename" and os.path.basename(a[1]).startswith("del-"))
            rc1 = run_build(sb, Injector(at, "denied"))
            # 2 回目: G2 を作り、前の世代（G1）を old-N に退避した直後に、強制停止する
            rec = Recorder()
            # 呼び出しの順は、今の砂場の写しで、手を入れずに流して得る
            shadow = Sandbox(sb.out_state, "asis", default)
            try:
                shutil.rmtree(shadow.root)
                shutil.copytree(sb.root, shadow.root, symlinks=True)
                run_build(shadow, rec, FILES_N2)
            finally:
                shadow.close()
            at = find_call(rec.calls, lambda n, a: n == "rename" and os.path.basename(a[1]).startswith("old-"))
            rc2 = run_build(sb, Injector(at + 1, "crash"), FILES_N2)
            # 3 回目: 復旧のあと、新しい世代を作り始めたところで失敗させる
            rec = Recorder()
            shadow = Sandbox(sb.out_state, "asis", default)
            try:
                shutil.rmtree(shadow.root)
                shutil.copytree(sb.root, shadow.root, symlinks=True)
                run_build(shadow, rec, FILES_N2)
            finally:
                shadow.close()
            at = find_call(rec.calls, lambda n, a: n == "mkdir" and os.path.basename(a[0]).startswith("tmp-"))
            rc3 = run_build(sb, Injector(at, "denied"), FILES_N2)
            got = content(tree(sb.out))
            if got != expected(FILES_N):
                problems.append(f"最後に公開した世代（G1）が残っていない（{'既定' if default else '--out'}、"
                                f"rc={rc1},{rc2},{rc3}、書き出し先の中身 {sorted(got or {})[:3]}）")
        finally:
            sb.close()
    return problems


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
                    if not world_same(sb, before_world, world(sb)):
                        problems.append(f"書き出し先を消したあとの書き出しで、領分の外が変わった（{out_state}、{mode}@{at}）")
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
    # 2 つ目は、手を入れなくても消せないファイルがある状態（手を入れない実行の側の確かめで見つかる）
    "silent_post_commit": [("gen", "asis", False), ("gen+hardlink", "asis", False)],
    "coarse_warning": [("gen+hardlink", "asis", False)],
    "report_fails_unit": [("absent", "asis", False)],
    "swallow_marker_failure": [("absent", "asis", False)],
    # 2 つ目は、手を入れない実行も警告を出す状態（読み取り専用のファイル）。警告の基準を、新しい警告で量ることを確かめる
    "fallback_rmdir": [("absent", "junction", False), ("gen+hardlink", "junction", True)],
    # 7 版目（6 回目の設計のレビュー）
    "follow_on_open": [("absent", "lock-dangling", False), ("gen", "lock-dangling", True)],
    "discard_old_first": [("empty+old", "asis", False), ("absent+old", "asis", True)],
    "warn_on_marker_close": [("absent", "asis", False)],
    # 8 版目（7 回目の設計のレビュー）
    "enter_root_unchecked": [("browse-junction", "asis", True)],
    "raise_post_listdir": [("gen", "asis", False)],
    # 8 版目の探索で見つけた（6.1 の確かめが、名前ごとに識別子を覚えていた）
    "cache_ids_by_name": [("gen+datajunction", "asis", True)],
}


def build_cases(quick):
    out_states = ("absent", "gen", "gen+extra", "absent+old", "wikiroot") if quick else OUT_STATES
    work_states = ("asis", "leftovers") if quick else WORK_STATES
    cases = []
    for default in (False, True):
        for out_state in out_states:
            if default and out_state in ("wikiroot", "insidewiki"):
                continue
            for work_state in work_states:
                if out_state.endswith("+old") and work_state == "unmarked-empty":
                    continue
                if out_state in ("wikiroot", "insidewiki") and work_state != "asis":
                    continue
                cases.append((out_state, work_state, default))
            if not quick and out_state in LINK_OUT_STATES:
                cases += [(out_state, ls, default) for ls in LINK_STATES + (WORK_LINK,)]
        if default:
            cases.append(("datainwiki", "asis", True))
            if not quick:
                cases += [(s, "asis", True) for s in ROOT_LINK]
                cases += [(s, w, True) for s in DATA_LINK for w in ("asis", "leftovers")]
    return cases


def main():
    """速く済むものから流し、節ごとにすぐ出す（途中で止まっても、そこまでの結果が残る）。"""
    quick = "--quick" in sys.argv
    started = time.time()
    all_problems = []

    def out(text=""):
        print(text, flush=True)

    out(f"Python {sys.version.split()[0]}、{sys.platform}")
    server_runs, server_problems = sweep_server(MODES)
    all_problems += server_problems
    out(f"\n## サーバーの記録\n\n実行 {server_runs} 回、破れた決まり {len(server_problems)} 件")
    root_runs, root_problems = sweep_server_root(MODES)
    all_problems += root_problems
    out(f"\n## 領分の名前がリンク（データの場所と状態のディレクトリ。起動、stop、動いているかの確かめ）\n\n実行 {root_runs} 回、破れた決まり {len(root_problems)} 件")
    shared_runs, shared_problems = sweep_shared(MODES)
    all_problems += shared_problems
    out(f"\n## 同じ場所を使う別の Wiki\n\n実行 {shared_runs} 回、破れた決まり {len(shared_problems)} 件")
    deletes_runs, deletes_problems = sweep_user_deletes(USER_DELETES)
    all_problems += deletes_problems
    out(f"\n## 強制停止のあとで、利用者が書き出し先を消す\n\n実行 {deletes_runs} 回、破れた決まり {len(deletes_problems)} 件")
    rewind_problems = scenario_rewind()
    all_problems += rewind_problems
    out(f"\n## 番号の巻き戻りと復旧（3 回の実行に 1 つずつの失敗）\n\n破れた決まり {len(rewind_problems)} 件")

    out("\n## 対照\n\n| 対照 | 見つけた件数 | 最初の 1 件 |\n| --- | --- | --- |")
    for mutant, cases in CONTROLS.items():
        m.MUTANTS.add(mutant)
        try:
            found = []
            for out_state, work_state, default in cases:
                _, _, problems = sweep_build(out_state, work_state, default, MODES)
                found += problems
        finally:
            m.MUTANTS.discard(mutant)
        out(f"| {mutant} | {len(found)} | {found[0] if found else '見つからなかった'} |")
    for label, mutant, run in (("warn_on_record_failure", "warn_on_record_failure", lambda: sweep_server(MODES)[1]),
                               ("recover_by_published_seq", "recover_by_published_seq", scenario_rewind),
                               ("delete_in_place", "delete_in_place", lambda: sweep_user_deletes(USER_DELETES)[1]),
                               ("refuse_unknown_entries", "refuse_unknown_entries", lambda: sweep_server(MODES)[1]),
                               ("skip_owner", "skip_owner", lambda: sweep_shared(MODES)[1]),
                               ("enter_root_unchecked（サーバー）", "enter_root_unchecked",
                                lambda: sweep_server_root(MODES)[1])):
        m.MUTANTS.add(mutant)
        try:
            found = run()
        finally:
            m.MUTANTS.discard(mutant)
        out(f"| {label} | {len(found)} | {found[0] if found else '見つからなかった'} |")

    out("\n## 書き出し\n\n| 書き出し先の種類 | 書き出し先の状態 | 作業用の状態 | 口の呼び出し | 実行 | 破れた決まり |\n| --- | --- | --- | --- | --- | --- |")
    for out_state, work_state, default in build_cases(quick):
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
    if all_problems:
        out(f"\n## 破れた決まり（{len(all_problems)} 件。先頭 40 件）\n")
        seen = []
        for p in all_problems:
            if p not in seen:
                seen.append(p)
        for p in seen[:40]:
            out("- " + p)
    out(f"\n{time.time() - started:.0f} 秒")
    return 1 if all_problems else 0


if __name__ == "__main__":
    sys.exit(main())
