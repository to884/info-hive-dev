"""browse の書く側（設計の 6、7.1）の規則を写した、小さな試作。製品のコードではない。

規則を文章だけで決めると、規則どうしのぶつかりが残る。そこで、規則を動く形にし、OS の呼び出しの N 回目に
失敗か強制停止を入れる探索（write_sweep.py）をかけて、決めた状態で終わることを確かめる。

写している規則:
- 書き込みの口は、どれも、Wiki のルートと重なる場所への書き込みを拒む（6.1）。どこに書くかを列挙して確かめるの
  ではなく、口そのものが確かめる。
- 領分（作業用と状態のディレクトリ）の中は、browse のものとして扱う。消すときは、リンクをたどらず、属性を変えない。
- wiki_key から場所を決める領分は、目印に Wiki のルートの識別子を書き、使うたびに照らす（7.1）。
- `--out` の書き出し先は、ない、空、一覧と中身が合う世代、のどれかのときだけ置き換える（門）。既定の書き出し先は
  領分で、前の世代を読まない。
- 確定の点は、新しい世代を書き出し先の名前にする、名前の付け替えである。終了コードは、単位の真実だけで決める。
  確定のあとの失敗（片付け、知らせの出力）は、警告にする。
- サーバーの真実はロックで、記録は手がかりである。

写していないもの: 走査と中核、待ち受け、ロックを待つ時間、2 つのプロセスの同時の実行、入れ子の書き出しの拒否、
Windows の識別子の関数（win_file_id。ここでは os.stat の st_dev と st_ino で代える）。
"""
from __future__ import annotations

import errno
import hashlib
import json
import os
import stat

WORK_MARKER = ".browse-work"
SERVER_MARKER = ".browse-server"
MANIFEST = ".browse-generation"
LEGACY = ("seq", "build-report.json")
STATE_KNOWN = ("server.lock", "server.json", "server.json.new", SERVER_MARKER + ".new")
O_BINARY = getattr(os, "O_BINARY", 0)

MUTANTS: set = set()      # 対照（わざと破った規則）の名前
WARNINGS: list = []
STATE = {"committed": False}


class Unknown(Exception):
    """分からない。ないこととして扱わない。"""


class Absent(Exception):
    """ない。"""


class Stop(Exception):
    """何も変えずに止まり、利用者に知らせる。"""


_CREATE_NEW, _OPEN_ALWAYS = 1, 4


def _win_open(path, disposition, flags):
    """Windows で、最後の名前の再解析点をたどらずに、ファイルを作るか開く。開いたものが、通常のファイルでなければ失敗する。

    CreateFileW に FILE_FLAG_OPEN_REPARSE_POINT を付ける。名前がリンクなら、リンクそのものを開くので、先は作らない。
    開いたハンドルの属性で、再解析点とディレクトリを拒む（名前を調べてから開く形にしない）。
    """
    import ctypes
    import msvcrt
    from ctypes import wintypes

    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateFileW.restype = wintypes.HANDLE
    k32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
                                wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    k32.CloseHandle.argtypes = [wintypes.HANDLE]

    class Info(ctypes.Structure):
        _fields_ = [("attrs", wintypes.DWORD), ("c", wintypes.FILETIME), ("a", wintypes.FILETIME),
                    ("w", wintypes.FILETIME), ("vol", wintypes.DWORD), ("sh", wintypes.DWORD),
                    ("sl", wintypes.DWORD), ("links", wintypes.DWORD), ("ih", wintypes.DWORD), ("il", wintypes.DWORD)]
    k32.GetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.POINTER(Info)]

    access = 0x40000000 | (0x80000000 if flags == os.O_RDWR else 0)      # GENERIC_WRITE と GENERIC_READ
    handle = k32.CreateFileW(path, access, 0x7, None, disposition, 0x80 | 0x00200000, None)
    if handle == wintypes.HANDLE(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        info = Info()
        if not k32.GetFileInformationByHandle(handle, ctypes.byref(info)):
            raise ctypes.WinError(ctypes.get_last_error())
        if info.attrs & (0x400 | 0x10):       # 再解析点、ディレクトリ
            raise OSError(errno.EPERM, "開いた名前が、通常のファイルでない", path)
        return msvcrt.open_osfhandle(handle, flags | O_BINARY)
    except BaseException:
        k32.CloseHandle(handle)
        raise


class Os:
    """OS を呼ぶ口。探索は、この口の呼び出しの N 回目に手を入れる。"""

    def lstat(self, path):
        return os.lstat(path)

    def stat_id(self, path):
        st = os.stat(path)
        return st.st_dev, st.st_ino

    def realpath(self, path):
        return os.path.realpath(path, strict=True)

    def scandir_open(self, path):
        return os.scandir(path)

    def scandir_next(self, it):
        """項目を 1 つ取り出す。終わりなら None。閉じる操作は、失敗が見えないので口に入れない（設計の 3.1）。"""
        try:
            return next(it).name
        except StopIteration:
            return None

    def mkdir(self, path):
        os.mkdir(path)

    def open_excl(self, path):
        """排他で作る。最後の名前がリンクでも、たどらない（設計の 3.1。Windows の os.open は、O_EXCL を付けても、
        先のないリンクをたどって先を作る）。"""
        if "follow_on_open" in MUTANTS:
            return os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | O_BINARY, 0o644)    # 対照: 6 版目の形
        if os.name == "nt":
            return _win_open(path, _CREATE_NEW, os.O_WRONLY)
        return os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)

    def open_read(self, path):
        return os.open(path, os.O_RDONLY | O_BINARY)

    def open_lock(self, path):
        """ロックのファイルを開く。なければ作る。最後の名前がリンクなら、たどらずに失敗する。"""
        if "follow_on_open" in MUTANTS:
            return os.open(path, os.O_RDWR | os.O_CREAT | O_BINARY, 0o600)                  # 対照: 6 版目の形
        if os.name == "nt":
            return _win_open(path, _OPEN_ALWAYS, os.O_RDWR)
        fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            os.close(fd)
            raise OSError(errno.EPERM, "ロックのファイルが通常のファイルでない", path)
        return fd

    def write(self, fd, data):
        return os.write(fd, data)

    def read(self, fd, size):
        return os.read(fd, size)

    def close(self, fd):
        os.close(fd)

    def rename(self, src, dst):
        os.rename(src, dst)

    def replace(self, src, dst):
        os.replace(src, dst)

    def unlink(self, path):
        os.unlink(path)

    def rmdir(self, path):
        os.rmdir(path)

    def stdout_write(self, text):
        """知らせの出力。試作では書き先を持たない。"""
        return len(text)

    def chmod(self, path, mode):      # 対照だけが使う。規則では、属性を変えない
        os.chmod(path, mode)

    def try_lock(self, fd):
        """取れたら真、ほかが持っていれば偽。ロックの操作そのものの失敗は、OSError のまま出す。"""
        if os.name == "nt":
            import msvcrt
            try:
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                return True
            except OSError as e:
                if e.errno in (13, 36):      # EACCES、EDEADLOCK: ほかが持っている
                    return False
                raise
        import fcntl
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except BlockingIOError:
            return False

    def unlock(self, fd):
        if os.name == "nt":
            import msvcrt
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_UN)


X = Os()


def failure(cls, message, path=None):
    """失敗の例外に、対象のパスを持たせる。警告が、どの項目の失敗かを名指せるようにする（設計の 6.2）。"""
    e = cls(message)
    e.path = path
    return e


def x(name, *args):
    """失敗の読み替えは、ここだけで行う（設計の 3.2）。例外は、失敗した口と、その対象のパスを持つ。"""
    path = args[0] if args and isinstance(args[0], str) else None
    try:
        return getattr(X, name)(*args)
    except (FileNotFoundError, NotADirectoryError) as e:
        raise failure(Absent, f"{name}: {type(e).__name__}", path) from None
    except OSError as e:
        if e.errno == getattr(errno, "ELOOP", None) or getattr(e, "winerror", None) in (1921, 123):
            raise failure(Absent, f"{name}: {type(e).__name__}", path) from None
        raise failure(Unknown, f"{name}: {type(e).__name__}", path) from None


def warn(message):
    WARNINGS.append(message)


def listdir(path):
    it = x("scandir_open", path)
    try:
        names = []
        while True:
            name = x("scandir_next", it)
            if name is None:
                return sorted(names)
            names.append(name)
    finally:
        it.close()


# ---------------------------------------------------------------------------
# Wiki のルートと重ならないことの確かめ（6.1）。書き込みの口が、どれもこれを通す。
# ---------------------------------------------------------------------------

class Guard:
    """1 つの仕事の単位のあいだ、Wiki のルートの識別子と、確かめた場所を覚えておく。"""

    def __init__(self, root):
        self.root = root
        self.root_id = None
        self.root_chain = None
        self.ids = {}
        self.ok = set()

    def ident(self, path):
        if path not in self.ids:
            dev, ino = x("stat_id", path)
            if ino == 0:
                raise failure(Unknown, "stat_id: 識別子が 0", path)
            self.ids[path] = (dev, ino)
        return self.ids[path]

    def chain(self, path):
        """path（解いたもの）と、その親の識別子を、根まで。"""
        found = []
        while True:
            found.append(self.ident(path))
            parent = os.path.dirname(path)
            if parent == path:
                return found
            path = parent

    def _root(self):
        if self.root_chain is None:
            r = x("realpath", self.root)
            self.root_chain = set(self.chain(r))
            self.root_id = self.ident(r)

    def place(self, directory):
        """directory（今あるディレクトリ）の中に名前を足す、変える、消すことができるか。Wiki のルートかその下なら Stop。

        directory そのものを見て、祖先にはさかのぼらない。書き込みの口は、どれも親がなければ成り立たないので、
        「ない」の答えは、そのまま失敗にする。「ない」という答えから、あとの書き込みが安全だと決めない（設計の 6.1）。
        覚えるのは、あると見て、識別子を取ったディレクトリだけである。
        """
        if "no_root_guard" in MUTANTS or directory in self.ok:
            return
        self._root()
        p = directory
        if "climb_on_absent" in MUTANTS:
            # 対照: 6 版目の初めの形。「ない」なら祖先にさかのぼり、祖先で確かめた結論を、ないと答えた名前に残す
            while kind(p) == "absent":
                parent = os.path.dirname(p)
                if parent == p:
                    raise failure(Unknown, "今ある祖先がない", directory)
                p = parent
        else:
            k = kind(p)
            if k == "absent":
                raise failure(Absent, "lstat: 書き込む場所がない", p)
            if k not in ("dir", "link"):
                raise failure(Unknown, "lstat: 書き込む場所がディレクトリでない", p)
        r = x("realpath", p)
        if self.ident(r) != self.ident(p):
            raise failure(Unknown, "realpath: 解いたパスの識別子が違う", p)
        if self.root_id in self.chain(r):
            raise Stop(f"Wiki のルートの下には書かない: {os.path.basename(directory)}")
        self.ok.add(directory)

    def not_root_ancestor(self, path):
        """path（今あるディレクトリ）が、Wiki のルートか、その祖先なら Stop。"""
        if "no_root_guard" in MUTANTS:
            return
        self._root()
        if self.ident(x("realpath", path)) in self.root_chain:
            raise Stop(f"Wiki のルートか、その祖先は動かさない: {os.path.basename(path)}")


G = Guard(None)


def w(name, *paths_and_args):
    """書き込みの口。対象の場所を確かめてから、x() を呼ぶ。"""
    if name in ("mkdir", "open_excl", "open_lock", "unlink"):
        G.place(os.path.dirname(paths_and_args[0]))
    elif name == "rmdir":
        G.place(os.path.dirname(paths_and_args[0]))
        if kind(paths_and_args[0]) == "dir":
            G.not_root_ancestor(paths_and_args[0])
    elif name in ("rename", "replace"):
        src, dst = paths_and_args[:2]
        G.place(os.path.dirname(src))
        G.place(os.path.dirname(dst))
        if kind(src) == "dir":
            G.not_root_ancestor(src)
    return x(name, *paths_and_args)


# ---------------------------------------------------------------------------
# 種類、読み書き
# ---------------------------------------------------------------------------

def kind(path):
    """'absent'、'file'、'dir'、'link'（シンボリックリンクと、ジャンクションなどの再解析点）、'other'。"""
    try:
        st = x("lstat", path)
    except Absent:
        return "absent"
    if stat.S_ISLNK(st.st_mode) or getattr(st, "st_file_attributes", 0) & 0x400:
        if "follow_links" not in MUTANTS:
            return "link"
        try:
            st = os.stat(path)          # 対照: リンクの先を見る
        except OSError:
            return "link"
    if stat.S_ISDIR(st.st_mode):
        return "dir"
    if stat.S_ISREG(st.st_mode):
        return "file"
    if os.name == "nt" and stat.S_ISBLK(st.st_mode):
        raise failure(Unknown, "lstat: 属性を取れない（S_IFBLK）", path)      # 設計の 3.1
    return "other"


def read_file(path):
    fd = x("open_read", path)
    try:
        chunks = []
        while True:
            chunk = x("read", fd, 65536)
            if not chunk:
                return b"".join(chunks)
            chunks.append(chunk)
    finally:
        _close(fd)


def create_file(path, data):
    """排他で作る。今あるファイルは開かない。短い書き込みは、書き終わるまで続ける。"""
    fd = w("open_excl", path)
    try:
        view = memoryview(data)
        while view:
            written = x("write", fd, view)
            view = view[written:]
    except BaseException:
        _close(fd)
        raise
    if "swallow_close" in MUTANTS:
        _close(fd)
        return
    x("close", fd)      # 書いたあとの close の失敗は、書けなかったこととして扱う（設計の 3.2）


def _close(fd):
    try:
        X.close(fd)
    except OSError:
        pass


def remove_tree(path):
    """領分の中のものを消す。リンクはたどらず、リンクそのものを外す。属性は変えない。分からなければ止まる。"""
    k = kind(path)
    if k == "absent":
        return
    if k == "link":
        if "fallback_rmdir" in MUTANTS:
            try:
                w("unlink", path)
            except Unknown:
                w("rmdir", path)      # 対照: 0.10.0 と 6 版目の初めの規則の形（どの失敗も rmdir で試し直す）
            return
        # os.unlink は、Windows でもジャンクションとディレクトリのリンクを外す。失敗しても、別の口で試し直さない（設計の 3.2）
        w("unlink", path)
        return
    if k == "dir":
        # 世代の一覧は最後に消す（0.10.0 と同じ順）。途中で止まった世代が一覧を持ったまま残る形を、
        # わざと作る。del-N に付け替える規則が、その形を戻す候補から外すことを、探索で確かめるためである。
        for name in sorted(listdir(path), key=lambda n: n == MANIFEST):
            remove_tree(os.path.join(path, name))
        w("rmdir", path)
        return
    try:
        w("unlink", path)
    except Unknown:
        if "chmod_on_delete" not in MUTANTS:
            raise
        X.chmod(path, 0o666)          # 対照: 属性を変えて消す
        w("unlink", path)


def move(src, dst):
    """名前を付け替える。先があれば、付け替えない。"""
    if kind(dst) != "absent":
        raise failure(Unknown, "rename: 付け替える先がある", dst)
    w("rename", src, dst)


def replace_file(path, data):
    """領分の中のファイルを置き換える。前の残りの .new を消し、.new を排他で作り、置き換える。"""
    new = path + ".new"
    remove_tree(new)
    create_file(new, data)
    w("replace", new, path)


# ---------------------------------------------------------------------------
# 領分
# ---------------------------------------------------------------------------

def read_text(path):
    if kind(path) != "file":
        return None
    try:
        return read_file(path).decode("utf-8")
    except Absent:
        return None
    except UnicodeDecodeError:
        return None


def use_territory(path, marker, known=(), owner=None, lock_name=None):
    """目印があるか、空なら、領分として使う。目印がなく、空でもないディレクトリは、使わない。

    owner を渡すと、目印に Wiki のルートの識別子を書き、使うたびに照らす。違えば、領分のロックが空いて
    いるときだけ、警告を出して引き継ぐ。ロックが取られていれば（別の Wiki が使っている）、止まる。
    """
    k = kind(path)
    if k == "absent":
        w("mkdir", path)
        k = "dir"
    if k != "dir":
        raise Stop(f"ディレクトリでない: {os.path.basename(path)}")
    entries = listdir(path)
    marker_path = os.path.join(path, marker)
    content = (owner or "").encode("utf-8")
    if marker not in entries:
        if entries:
            raise Stop(f"目印がなく、空でもない: {os.path.basename(path)}")
        if "swallow_marker_failure" in MUTANTS:
            try:
                create_file(marker_path, content)
            except Unknown:
                if kind(marker_path) != "file":     # 5 版目の試作の形: ファイルがあれば失敗を捨てる
                    raise
        elif "warn_on_marker_close" in MUTANTS:
            try:
                create_file(marker_path, content)
            except Unknown as e:
                warn(f"目印を書けなかった（{e}）")      # 対照: 確定の前の失敗を、警告して続ける
        else:
            create_file(marker_path, content)
    elif "refuse_unknown_entries" in MUTANTS:
        # 3 版目の規則: 記録と、ロックと、目印のほかの項目があれば使わない（置き換えの一時ファイルも拒む）
        extra = [e for e in entries if e != marker and e not in known or e.endswith(".new")]
        if extra:
            raise Stop(f"決まった名前のほかの項目がある: {extra[0]}")
    if owner is not None and "skip_owner" not in MUTANTS:
        current = read_text(marker_path)
        if current != owner:
            probe = Lock(os.path.join(path, lock_name))
            if not probe.try_acquire():
                raise Stop("別の Wiki が、同じ場所を使っている")
            try:
                replace_file(marker_path, content)
                warn("別の Wiki が使っていた場所を引き継いだ")
            finally:
                probe.release()


class Lock:
    def __init__(self, path):
        self.path = path
        self.fd = None

    def try_acquire(self):
        # 領分の中のロックの名前に、利用者が置いたリンクがあれば、たどらずに外してから作る（設計の 6.2）。
        # 外すかどうかは、見た種類で決める。種類の答えが誤っていても、ロックの口がリンクをたどらずに失敗する。
        if kind(self.path) == "link":
            remove_tree(self.path)
        fd = w("open_lock", self.path)
        try:
            got = x("try_lock", fd)
        except BaseException:
            _close(fd)
            raise
        if not got:
            _close(fd)
            return False
        self.fd = fd
        return True

    def release(self):
        if self.fd is not None:
            try:
                X.unlock(self.fd)
            except OSError:
                pass          # 閉じれば、OS が外す
            _close(self.fd)
            self.fd = None


# ---------------------------------------------------------------------------
# 世代と門
# ---------------------------------------------------------------------------

def make_manifest(files, seq):
    entries = {name: {"size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
               for name, data in files.items()}
    dirs = sorted({"/".join(name.split("/")[:i]) for name in files for i in range(1, name.count("/") + 1)})
    return json.dumps({"published_seq": seq, "files": entries, "dirs": dirs}, sort_keys=True).encode("utf-8")


def read_manifest(directory):
    """一覧を読む。ないか、形が違えば None。読めなければ Unknown。"""
    text = read_text(os.path.join(directory, MANIFEST))
    if text is None:
        return None
    try:
        data = json.loads(text)
    except ValueError:
        return None
    if not isinstance(data, dict) or not isinstance(data.get("published_seq"), int):
        return None
    return data


def verify_generation(directory, manifest):
    """世代の全体を、読んである一覧と照らす。合えば None、合わなければ理由を返す。調べられなければ Unknown。"""
    if manifest is None:
        return "一覧がない"
    files, dirs = manifest.get("files"), manifest.get("dirs")
    if not isinstance(files, dict) or not isinstance(dirs, list):
        return "一覧に名前がない（0.10.0 の書き出し）"
    seen = set()

    def walk(rel):
        for name in listdir(os.path.join(directory, rel) if rel else directory):
            child = f"{rel}/{name}" if rel else name
            k = kind(os.path.join(directory, child))
            if child == MANIFEST:
                continue
            if k == "dir" and child in dirs:
                seen.add(child)
                reason = walk(child)
                if reason:
                    return reason
            elif k == "file" and child in files:
                data = read_file(os.path.join(directory, child))
                if hashlib.sha256(data).hexdigest() != files[child].get("sha256"):
                    return f"中身が違う: {child}"
                seen.add(child)
            else:
                return f"一覧にない、または種類が違う: {child}"
        return None

    reason = walk("")
    if reason:
        return reason
    missing = (set(files) | set(dirs)) - seen
    return f"一覧にあるものがない: {sorted(missing)[0]}" if missing else None


def out_state(out, verify):
    """('absent' | 'empty' | 'generation' | 'foreign' | 'present', 理由, 通し番号)。

    verify が偽（既定の書き出し先）なら、前の世代を読まない。'present' を返す。
    一覧は 1 度だけ読み、判定にも通し番号にも、その 1 度の結果を使う。
    """
    k = kind(out)
    if k == "absent":
        return "absent", None, 0
    if not verify and "default_verifies" not in MUTANTS:
        if k == "dir" and not listdir(out):
            return "empty", None, 0
        return "present", None, 0
    if k != "dir":
        return "foreign", "ディレクトリでない", 0
    if not listdir(out):
        return "empty", None, 0
    manifest = read_manifest(out)
    seq = manifest["published_seq"] if manifest is not None else 0
    reason = verify_generation(out, manifest)
    return ("generation", None, seq) if reason is None else ("foreign", reason, seq)


def _number(name):
    try:
        return int(name.split("-", 1)[1])
    except (IndexError, ValueError):
        return 0


def build(root, out, files, default=False, owner=None):
    """静的の書き出し。0 を返せば、書き出し先は新しい世代である。Stop と Unknown は、前のままで止まる。"""
    global G
    G = Guard(root)
    STATE["committed"] = False
    work = out + ".browse-work"
    if default:
        ensure_dirs(os.path.dirname(out))
    # 作る前に、書き出し先そのものを確かめる。書き込みの口も確かめるが、ここで止めれば作業用も作らない。
    G.place(os.path.dirname(out))
    if kind(out) == "dir":
        G.not_root_ancestor(out)
    use_territory(work, WORK_MARKER, owner=owner if default else None, lock_name="build.lock")
    lock = Lock(os.path.join(work, "build.lock"))
    if not lock.try_acquire():
        raise Stop("同じ書き出し先に、ほかの書き出しが動いている")
    try:
        return _build_locked(out, work, files, default)
    finally:
        lock.release()


def ensure_dirs(path):
    """ない祖先を、上から順に作る（既定の書き出し先の <data_dir>/browse）。"""
    missing = []
    p = path
    while kind(p) == "absent":
        missing.append(p)
        parent = os.path.dirname(p)
        if parent == p:
            raise failure(Unknown, "今ある祖先がない", path)
        p = parent
    for d in reversed(missing):
        w("mkdir", d)


def _discard(work, names):
    """領分の残りを消す。消せなければ、警告して残す。"""
    for name in names:
        path = os.path.join(work, name)
        try:
            if name.startswith("old-") and "delete_in_place" not in MUTANTS:
                target = os.path.join(work, "del-" + name[4:])
                move(path, target)
                path = target
            remove_tree(path)
        except (Unknown, Absent) as e:
            if "coarse_warning" in MUTANTS:
                warn(f"消せなかったので残す: {name}（{e}）")      # 対照: 6 版目の初めの形（付け替える前の名前だけ）
            elif "silent_post_commit" not in MUTANTS:
                # 残した項目の今の名前（付け替えたあとなら del-N）と、失敗した口とその対象を書く（設計の 6.2）
                failed = getattr(e, "path", None)
                target = os.path.relpath(failed, work).replace(os.sep, "/") if failed else "?"
                warn(f"消せなかったので残す: {os.path.basename(path)}（{target} の {e}）")


def _build_locked(out, work, files, default):
    entries = listdir(work)
    leftover = ("tmp-", "del-", "old-") if "discard_old_first" in MUTANTS else ("tmp-", "del-")   # 対照: 退避の世代も消す
    _discard(work, [n for n in entries if n.startswith(leftover) or n in LEGACY])
    olds = [n for n in listdir(work) if n.startswith("old-")]
    state, reason, out_seq = out_state(out, verify=not default)

    # 途中で止まった入れ替えから、最後に退避した世代を戻す。番号は、作業用にあるどの名前よりも大きく取るので、
    # 作業用にある old-N のあいだでは、番号の大きいほうが新しい。一覧（published_seq）には頼らない。
    if state in ("absent", "empty") and olds:
        if "recover_by_published_seq" in MUTANTS:
            seqs = {n: (read_manifest(os.path.join(work, n)) or {}).get("published_seq", 0) for n in olds}
            best = max(olds, key=lambda n: seqs[n])
        else:
            best = max(olds, key=_number)
        if state == "empty":
            w("rmdir", out)
        move(os.path.join(work, best), out)
        state, reason, out_seq = out_state(out, verify=not default)

    # 門: 書き出し先が browse の書き出しと確かめられなければ、止まる。既定の書き出し先は領分なので、通さない。
    if state == "foreign" and "skip_gate" not in MUTANTS:
        raise Stop(f"書き出し先に、browse が作っていないものがある（{reason}）")

    used = [_number(n) for n in listdir(work) if n.startswith(("tmp-", "old-", "del-"))]
    seq = max(used, default=0) + 1

    tmp = os.path.join(work, f"tmp-{seq}")
    try:
        w("mkdir", tmp)
        create_file(os.path.join(tmp, MANIFEST), make_manifest(files, seq))
        for name in sorted(files):
            parts = name.split("/")
            for i in range(1, len(parts)):
                sub = os.path.join(tmp, *parts[:i])
                if kind(sub) == "absent":
                    w("mkdir", sub)
            create_file(os.path.join(tmp, *parts), files[name])
        # 入れ替え
        old = None
        if state == "empty":
            w("rmdir", out)
        elif state != "absent":
            old = os.path.join(work, f"old-{seq}")
            move(out, old)
        try:
            move(tmp, out)              # 確定の点
            STATE["committed"] = True
        except (Unknown, Absent):
            if old is not None:
                try:
                    move(old, out)
                except (Unknown, Absent):
                    pass                # 次の書き出しが戻す
            raise
    except (Unknown, Absent, Stop):
        try:
            remove_tree(tmp)
        except (Unknown, Absent, Stop):
            pass
        raise

    # 確定のあと。失敗しても、単位を失敗にしない。
    leftovers = [n for n in x_or_empty(work) if n.startswith("old-")]
    before = len(WARNINGS)
    _discard(work, leftovers)
    if "commit_then_fail" in MUTANTS and len(WARNINGS) > before:
        raise Unknown("確定のあとの片付けに失敗した")
    report(json.dumps({"published_seq": seq}))
    return 0


def report(text):
    """知らせを出す。確定のあとなので、失敗しても終了コードを変えない（設計の 7）。"""
    try:
        x("stdout_write", text)
    except (Unknown, Absent) as e:
        if "report_fails_unit" in MUTANTS:
            raise
        warn(f"知らせを出せなかった（{e}）")


def x_or_empty(work):
    """確定のあとの一覧。作れなければ、片付けをあきらめて警告する（単位は失敗にしない）。"""
    try:
        return listdir(work)
    except (Unknown, Absent) as e:
        warn(f"作業用のディレクトリの一覧を作れない（{e}）")
        return []


# ---------------------------------------------------------------------------
# サーバーの記録
# ---------------------------------------------------------------------------

class Server:
    def __init__(self, state_dir, lock, instance, owner):
        self.state_dir, self.lock, self.instance, self.owner = state_dir, lock, instance, owner


def _enter_state(root, state_dir, owner, create=False):
    """状態のディレクトリに触れる前の確かめ。起動（create）だけは、ない祖先（<data_dir>/browse）を上から作る。"""
    global G
    G = Guard(root)
    if create:
        ensure_dirs(os.path.dirname(state_dir))
    use_territory(state_dir, SERVER_MARKER, STATE_KNOWN, owner=owner, lock_name="server.lock")


def read_record(state_dir):
    """記録を読む。ないか、形が違えば None。読めなければ Unknown。"""
    text = read_text(os.path.join(state_dir, "server.json"))
    if text is None:
        return None
    try:
        data = json.loads(text)
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def serve_start(root, state_dir, instance, owner):
    """起動。('started', Server) か、('reuse', 記録) を返す。使い回せなければ Stop。"""
    _enter_state(root, state_dir, owner, create=True)
    lock = Lock(os.path.join(state_dir, "server.lock"))
    if not lock.try_acquire():
        rec = read_record(state_dir)
        if rec is None or (rec.get("owner") != owner and "skip_owner" not in MUTANTS):
            raise Stop("動いているサーバーを使い回せない")
        return "reuse", rec
    try:
        replace_file(os.path.join(state_dir, "server.json"),
                     json.dumps({"instance": instance, "owner": owner}).encode("utf-8"))
    except Unknown as e:
        if "warn_on_record_failure" not in MUTANTS:
            lock.release()
            raise
        warn(f"記録を書けなかった（{e}）")              # 対照: 起動の失敗を、警告して続ける
    except BaseException:
        lock.release()
        raise
    return "started", Server(state_dir, lock, instance, owner)


def serve_finish(server):
    """終了。記録を消せなくても、ロックは離す。"""
    try:
        w("unlink", os.path.join(server.state_dir, "server.json"))
    except Absent:
        pass
    except (Unknown, Stop) as e:
        warn(f"記録を消せなかった（{e}）。次の起動が置き換える")
    finally:
        server.lock.release()


def stop(root, state_dir, owner):
    """'not-running' か、'stop-sent'（止める要求を送る相手が決まった）を返す。相手が違えば Stop。"""
    if kind(state_dir) == "absent":
        return "not-running"
    _enter_state(root, state_dir, owner)
    lock = Lock(os.path.join(state_dir, "server.lock"))
    if lock.try_acquire():
        lock.release()
        return "not-running"
    rec = read_record(state_dir)
    if rec is None:
        raise Stop("記録がないので、止める相手が分からない")
    if rec.get("owner") != owner and "skip_owner" not in MUTANTS:
        raise Stop("動いているのは、別の Wiki のサーバーである")
    return "stop-sent"


def is_running(root, state_dir, owner):
    """真実はロックである。記録の有無は見ない。"""
    return stop(root, state_dir, owner) == "stop-sent"
