"""browse の書く側（設計の 5、6）の規則を写した、小さな試作。製品のコードではない。

規則を文章だけで決めると、規則どうしのぶつかりが残る（3 回目のレビューの重大 3）。そこで、規則を動く形にし、
OS の呼び出しの N 回目に失敗か強制停止を入れる探索（write_sweep.py）をかけて、決めた状態で終わることを確かめる。

写している規則:
- 領分（目印のある作業用と状態のディレクトリ）の中は、browse のものとして扱う。消すときは、リンクをたどらず、
  属性を変えない。
- 書き出し先は、ない、空、一覧と中身が合う世代、のどれかのときだけ置き換える（門）。既定の書き出し先は領分で、
  門を通さない。
- 確定の点は、新しい世代を書き出し先の名前にする、名前の付け替えである。
- サーバーの真実はロックで、記録は手がかりである。
"""
from __future__ import annotations

import hashlib
import json
import os
import stat

WORK_MARKER = ".browse-work"
SERVER_MARKER = ".browse-server"
MANIFEST = ".browse-generation"
LEGACY = ("seq", "build-report.json")
O_BINARY = getattr(os, "O_BINARY", 0)

MUTANTS: set = set()      # 対照（わざと破った規則）の名前
WARNINGS: list = []


class Unknown(Exception):
    """分からない。ないこととして扱わない。"""


class Absent(Exception):
    """ない。"""


class Stop(Exception):
    """何も変えずに止まり、利用者に知らせる。"""


class Os:
    """OS を呼ぶ口。探索は、この口の呼び出しの N 回目に手を入れる。"""

    def lstat(self, path):
        return os.lstat(path)

    def listdir(self, path):
        with os.scandir(path) as it:
            return sorted(entry.name for entry in it)

    def mkdir(self, path):
        os.mkdir(path)

    def open_excl(self, path):
        return os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | O_BINARY, 0o644)

    def open_read(self, path):
        return os.open(path, os.O_RDONLY | O_BINARY)

    def open_lock(self, path):
        return os.open(path, os.O_RDWR | os.O_CREAT | O_BINARY, 0o600)

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


def x(name, *args):
    """失敗の読み替えは、ここだけで行う。"""
    try:
        return getattr(X, name)(*args)
    except (FileNotFoundError, NotADirectoryError) as e:
        raise Absent(str(e)) from None
    except OSError as e:
        raise Unknown(f"{name}: {type(e).__name__}") from None


def warn(message):
    WARNINGS.append(message)


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
    fd = x("open_excl", path)
    try:
        view = memoryview(data)
        while view:
            written = x("write", fd, view)
            view = view[written:]
    except BaseException:
        _close(fd)
        raise
    x("close", fd)      # 書いたあとの close の失敗は、書けなかったこととして扱う（握りつぶさない）


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
        try:
            x("unlink", path)
        except Unknown:
            x("rmdir", path)      # Windows のジャンクションとディレクトリのリンクは rmdir で外す
        return
    if k == "dir":
        for name in x("listdir", path):
            remove_tree(os.path.join(path, name))
        x("rmdir", path)
        return
    try:
        x("unlink", path)
    except Unknown:
        if "chmod_on_delete" not in MUTANTS:
            raise
        X.chmod(path, 0o666)          # 対照: 属性を変えて消す
        x("unlink", path)


def move(src, dst):
    """名前を付け替える。先があれば、付け替えない。"""
    if kind(dst) != "absent":
        raise Unknown(f"付け替える先がある: {os.path.basename(dst)}")
    x("rename", src, dst)


# ---------------------------------------------------------------------------
# 領分
# ---------------------------------------------------------------------------

def use_territory(path, marker, known=()):
    """目印があるか、空なら、領分として使う。目印がなく、空でもないディレクトリは、使わない。"""
    k = kind(path)
    if k == "absent":
        x("mkdir", path)
        k = "dir"
    if k != "dir":
        raise Stop(f"ディレクトリでない: {os.path.basename(path)}")
    entries = x("listdir", path)
    if marker not in entries:
        if entries:
            raise Stop(f"目印がなく、空でもない: {os.path.basename(path)}")
        try:
            create_file(os.path.join(path, marker), b"")
        except Unknown:
            if kind(os.path.join(path, marker)) != "file":
                raise
    elif "refuse_unknown_entries" in MUTANTS:
        extra = [e for e in entries if e != marker and e not in known]
        if extra:
            raise Stop(f"決まった名前のほかの項目がある: {extra[0]}")


class Lock:
    def __init__(self, path):
        self.path = path
        self.fd = None

    def try_acquire(self):
        fd = x("open_lock", self.path)
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
    path = os.path.join(directory, MANIFEST)
    if kind(path) != "file":
        return None
    try:
        data = json.loads(read_file(path).decode("utf-8"))
    except Absent:
        return None
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
        for name in x("listdir", os.path.join(directory, rel) if rel else directory):
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


def out_state(out):
    """('absent' | 'empty' | 'generation' | 'foreign', 理由, 通し番号)。

    一覧は 1 度だけ読み、判定にも通し番号にも、その 1 度の結果を使う。読み直すと、2 度目が違うことがある。
    """
    k = kind(out)
    if k == "absent":
        return "absent", None, 0
    if k != "dir":
        return "foreign", "ディレクトリでない", 0
    if not x("listdir", out):
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


def build(out, files, default=False):
    """静的の書き出し。0 を返せば、書き出し先は新しい世代である。Stop と Unknown は、前のままで止まる。"""
    work = out + ".browse-work"
    use_territory(work, WORK_MARKER)
    lock = Lock(os.path.join(work, "build.lock"))
    if not lock.try_acquire():
        raise Stop("同じ書き出し先に、ほかの書き出しが動いている")
    try:
        return _build_locked(out, work, files, default)
    finally:
        lock.release()


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
            warn(f"消せなかったので残す: {name}（{e}）")


def _build_locked(out, work, files, default):
    entries = x("listdir", work)
    _discard(work, [n for n in entries if n.startswith(("tmp-", "del-")) or n in LEGACY])
    olds = [n for n in x("listdir", work) if n.startswith("old-")]
    state, reason, out_seq = out_state(out)

    # 途中で止まった入れ替えから、最後に公開した世代を戻す。
    if state in ("absent", "empty") and olds:
        seqs = {}
        for name in olds:
            manifest = read_manifest(os.path.join(work, name))      # 読めなければ Unknown で止まる
            if manifest is not None:
                seqs[name] = manifest["published_seq"]
        if seqs:
            best = max(seqs, key=seqs.get)
            if state == "empty":
                x("rmdir", out)
            move(os.path.join(work, best), out)
            state, reason, out_seq = out_state(out)

    # 門: 書き出し先が browse の書き出しと確かめられなければ、止まる。既定の書き出し先は領分なので、通さない。
    if state == "foreign" and not default and "skip_gate" not in MUTANTS:
        raise Stop(f"書き出し先に、browse が作っていないものがある（{reason}）")

    used = [_number(n) for n in x("listdir", work) if n.startswith(("tmp-", "old-", "del-"))]
    used.append(out_seq)
    seq = max(used, default=0) + 1

    tmp = os.path.join(work, f"tmp-{seq}")
    try:
        x("mkdir", tmp)
        create_file(os.path.join(tmp, MANIFEST), make_manifest(files, seq))
        for name in sorted(files):
            parts = name.split("/")
            for i in range(1, len(parts)):
                sub = os.path.join(tmp, *parts[:i])
                if kind(sub) == "absent":
                    x("mkdir", sub)
            create_file(os.path.join(tmp, *parts), files[name])
        # 入れ替え
        old = None
        if state == "empty":
            x("rmdir", out)
        elif state != "absent":
            old = os.path.join(work, f"old-{seq}")
            move(out, old)
        try:
            move(tmp, out)              # 確定の点
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
        except (Unknown, Absent):
            pass
        raise

    # 確定のあと。失敗しても、単位を失敗にしない。
    leftovers = [n for n in x_or_empty(work) if n.startswith("old-")]
    before = len(WARNINGS)
    _discard(work, leftovers)
    if "commit_then_fail" in MUTANTS and len(WARNINGS) > before:
        raise Unknown("確定のあとの片付けに失敗した")
    return 0


def x_or_empty(work):
    """確定のあとの一覧。作れなければ、片付けをあきらめて警告する（単位は失敗にしない）。"""
    try:
        return x("listdir", work)
    except (Unknown, Absent) as e:
        warn(f"作業用のディレクトリの一覧を作れない（{e}）")
        return []


# ---------------------------------------------------------------------------
# サーバーの記録
# ---------------------------------------------------------------------------

STATE_KNOWN = ("server.lock", "server.json", "server.json.new")


class Server:
    def __init__(self, state_dir, lock, instance):
        self.state_dir, self.lock, self.instance = state_dir, lock, instance


def serve_start(state_dir, instance):
    """起動。ロックを取り、記録を置き換える。動いていれば Stop。失敗したら、ロックを離して終わる。"""
    use_territory(state_dir, SERVER_MARKER, STATE_KNOWN)
    lock = Lock(os.path.join(state_dir, "server.lock"))
    if not lock.try_acquire():
        raise Stop("動いているサーバーがある")
    try:
        new = os.path.join(state_dir, "server.json.new")
        remove_tree(new)                                   # 前の起動が置き換えの途中で止まった残り
        create_file(new, json.dumps({"instance": instance}).encode("utf-8"))
        x("replace", new, os.path.join(state_dir, "server.json"))
    except BaseException:
        lock.release()
        raise
    return Server(state_dir, lock, instance)


def serve_finish(server):
    """終了。記録を消せなくても、ロックは離す。"""
    try:
        x("unlink", os.path.join(server.state_dir, "server.json"))
    except Absent:
        pass
    except Unknown as e:
        warn(f"記録を消せなかった（{e}）。次の起動が置き換える")
    finally:
        server.lock.release()


def is_running(state_dir):
    """真実はロックである。記録の有無は見ない。"""
    if kind(state_dir) == "absent":
        return False
    lock = Lock(os.path.join(state_dir, "server.lock"))
    if lock.try_acquire():
        lock.release()
        return False
    return True
