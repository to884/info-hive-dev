"""走査の計画の 6 版目の試作と探索。5 版目の試作（walk_v5.py）の失敗の分け方を、作者の決定で直したもの。

5 版目から変えたこと:
- 失敗の分け方を、今の実装（pathlib の _ignore_error、3.14 の glob と os.path.isfile）が何をどう扱うかの表から決める。
  木の状態として、障害なしに必ず起きる失敗を、障害と分ける。
  - ない: FileNotFoundError、NotADirectoryError、解けないリンク（ELOOP、Windows のエラー 1921）、正しくない名前（123）
  - 分からない: PermissionError、NoFileId、FileId が 0、EBADF、準備のできていないドライブ（Windows のエラー 21）
  - そのほか: 送出する
  5 版目は、自分を指すシンボリックリンクが 1 つあるだけで、走査ごと送出していた（今の実装は、そのリンクを飛ばす）。
- 木に、解けないリンク（自分を指すファイルとディレクトリのリンク、互いに指し合うリンク）を足した。
- 探索が入れる失敗の種類を、上の表の行から取る。失敗のない実行が送出したら、違反とする。
- 5 版目の試作を、対照に足した。

以下は、5 版目の説明のまま。


4 版目から変えたこと:
- ディレクトリの識別子を、os.stat() からではなく、Win32 の呼び出しから直接取る（win_file_id()。作者の決定）。
  os.stat() は、Python 3.12 以降、FileIdInfo の取得の失敗を捨てて、識別子の形を変える（重大 1）。
  win_file_id() は、CreateFileW、GetFileInformationByHandleEx(FileIdInfo)、CloseHandle の失敗を、すべて OSError で
  送出する。ファイルシステムが FileIdInfo を返さないときは NoFileId を送出し、読み替えの関数が「分からない」にする。
- 探索の口に win_file_id() を足し、識別子の役割の呼び出しの名前を "file_id" にした。
- 今の index_files() の集合を、今の関数の規則（index.md がファイルなら、そのあと indexes を起点に rglob("*.md") が
  返す名前のすべて）で、木から直接計算する（重大 2）。新しい集合から違いを戻す形をやめた。
- 索引の下に、ふつうのファイルでない項目（先のないリンク、ディレクトリへのリンク、.md で終わる名前のディレクトリ、
  FIFO）を置いた木を足した。FIFO は Linux と macOS だけ。

以下は、4 版目の説明のまま。

4 版目の説明:

3 版目から変えたこと:
- 道筋の識別子は、そのジャンクションのためだけに取る。同じディレクトリの兄弟に引き継がない（重大 1）。
- 探索は、走査が呼ぶはずの口の呼び出しの集合と、それぞれの役割を、木から計算する。失敗のない実行で、
  走査の呼び出しの集合が、それと等しいことを確かめる。失敗を入れたときの答えも、役割から計算する。
  走査が実際にした呼び出しから、答えを作らない（重大 1、前提 C）。
- 今の実装との照合は、今の関数の並びの鍵で同じになる組の中の順だけを、違ってよいものとする。ページは
  posix_rel、索引は Path の比較（Windows は大文字と小文字を区別しない）が、今の鍵である（重大 2）。
- 一覧を閉じる呼び出しは、数えない。CPython が閉じるときの失敗を捨てるので、失敗を入れても意味がない（重大 3）。

以下は、3 版目の説明のまま。

- 口は、os.scandir（開く、項目を 1 つ取り出す、閉じる）、項目の is_symlink、is_dir、stat、os.stat だけ。
  os.path.realpath も、パスの文字列の比較も使わない。
- 同じディレクトリかどうかは、os.stat の st_dev と st_ino だけで決める。取れなければ「分からない」。
- 循環は、道筋のディレクトリの識別子と比べて見つける。
- 並びの鍵、ページかどうかの規則、除く名前は、実物の wiki_text、wiki_pages から読み込む（写しを持たない）。
- 今の実装との照合は、実物の wiki_pages.iter_page_files() と wiki_lint.index_files() を呼ぶ。
- 探索の答えは、木の作り（SPEC）から計算し、走査の結果と等しいことを確かめる。

使い方:
    python walk_v3.py check <作業用のディレクトリ>     木ごとに、答えとの一致と、今の実装との照合を見る
    python walk_v3.py explore <作業用のディレクトリ>   口の呼び出しの N 回目に失敗を入れ、答えと等しいかを見る
    python walk_v3.py wikis <wiki>...                  実物の wiki で、今の実装と照合する
"""
import errno
import os
import shutil
import stat
import subprocess
import sys
import unicodedata
from pathlib import Path, PurePath
from typing import NamedTuple

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[2] / "info-hive-wiki" / "skills" / "info-hive" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import wiki_lint  # noqa: E402 実物（今の index_files()）
import wiki_pages  # noqa: E402 実物（今の iter_page_files()、is_page_path()、SKIP_TOP_LEVEL_DIRS）
import wiki_text  # noqa: E402 実物（並びの鍵の posix_rel()）
sys.path.insert(0, str(HERE))
import walk_v3  # noqa: E402 3 版目の試作（対照に使う）
import walk_v4  # noqa: E402 4 版目の試作（対照に使う）
import walk_v5  # noqa: E402 5 版目の試作（対照に使う）

ABSENT = (FileNotFoundError, NotADirectoryError)
NT = os.name == "nt"


class MdFile(NamedTuple):
    rel: str
    size: int
    mtime_ns: int


class Walk(NamedTuple):
    files: list
    unlistable: list
    unknown: list


def sort_key(rel):
    """並びの鍵。今の iter_page_files() の鍵（posix_rel）に、同じ鍵のときの決め方（綴り）を足したもの。"""
    return (wiki_text.posix_rel(rel), rel)


class NoFileId(OSError):
    """ファイルシステムが、識別子（FileIdInfo）を返さない。"""


# 失敗の分け方。今の実装の扱い（3.10〜3.12 の pathlib の _ignore_error は ENOENT、ENOTDIR、EBADF、ELOOP と
# Windows のエラー 21、123、1921 を無視する。3.14 の glob と os.path.isfile は、どの OSError も無視する）と並べて決めた。
UNRESOLVABLE_ERRNOS = (errno.ELOOP,)          # 解けないリンク。木の状態として必ず起きる。ページにならない
UNRESOLVABLE_WINERRORS = (1921, 123)          # ERROR_CANT_RESOLVE_FILENAME、ERROR_INVALID_NAME
UNKNOWN_ERRNOS = (errno.EBADF,)               # 木の状態としては起きないはずだが、今の実装は無視する。送出はしない
UNKNOWN_WINERRORS = (21,)                     # ERROR_NOT_READY。準備のできていないドライブ。中身があるかが分からない


def read_os(call, *args, **kwargs):
    """口の呼び出しの結果を (状態, 値) で返す。失敗の読み替えは、ここだけで行う。"""
    try:
        return "ok", call(*args, **kwargs)
    except ABSENT:
        return "absent", None
    except (PermissionError, NoFileId):
        return "denied", None
    except OSError as exc:
        winerror = getattr(exc, "winerror", None)
        if winerror in UNRESOLVABLE_WINERRORS or (winerror is None and exc.errno in UNRESOLVABLE_ERRNOS):
            return "absent", None
        if winerror in UNKNOWN_WINERRORS or (winerror is None and exc.errno in UNKNOWN_ERRNOS):
            return "denied", None
        raise


# ---------------------------------------------------------------------------
# Windows の識別子（ctypes。標準ライブラリだけ）
# ---------------------------------------------------------------------------

UNSUPPORTED_WINERRORS = (1, 50, 87)  # ERROR_INVALID_FUNCTION、ERROR_NOT_SUPPORTED、ERROR_INVALID_PARAMETER
_KERNEL32 = None


def _kernel32():
    global _KERNEL32
    if _KERNEL32 is None:
        import ctypes
        from ctypes import wintypes
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
                                  wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        k.CreateFileW.restype = wintypes.HANDLE
        k.GetFileInformationByHandleEx.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        k.GetFileInformationByHandleEx.restype = wintypes.BOOL
        k.CloseHandle.argtypes = [wintypes.HANDLE]
        k.CloseHandle.restype = wintypes.BOOL

        class FileIdInfo(ctypes.Structure):
            _fields_ = [("VolumeSerialNumber", ctypes.c_ulonglong), ("FileId", ctypes.c_ubyte * 16)]
        _KERNEL32 = (ctypes, k, FileIdInfo)
    return _KERNEL32


def win_file_id(path):
    """(VolumeSerialNumber, FileId) を返す。リンクの先をたどる。どの失敗も OSError で送出し、読み替えない。

    ないパスは FileNotFoundError、拒まれたパスは PermissionError（OSError の第 4 引数に Windows のエラーの番号を
    渡すと、Python が分ける）。FileIdInfo を返さないファイルシステムは NoFileId。
    """
    ctypes, k, FileIdInfo = _kernel32()

    def error(cls=OSError):
        code = ctypes.get_last_error()
        return cls(None, ctypes.FormatError(code).strip(), path, code)
    handle = k.CreateFileW(path, 0x80, 0x7, None, 3, 0x02000000, None)  # FILE_READ_ATTRIBUTES、共有、OPEN_EXISTING、BACKUP_SEMANTICS
    if handle in (None, ctypes.c_void_p(-1).value):
        raise error()
    try:
        info = FileIdInfo()
        if not k.GetFileInformationByHandleEx(handle, 18, ctypes.byref(info), ctypes.sizeof(info)):  # 18 は FileIdInfo
            code = ctypes.get_last_error()
            if code in UNSUPPORTED_WINERRORS:
                raise NoFileId(None, ctypes.FormatError(code).strip(), path, code)
            raise error()
        return info.VolumeSerialNumber, bytes(info.FileId)
    finally:
        if not k.CloseHandle(handle):
            raise error()


def list_dir(directory):
    with os.scandir(directory) as it:
        return list(it)


def identity(path):
    """(状態, 識別子)。識別子は win_file_id() の値。FileId がすべて 0 なら、分からない（"denied" と同じ扱い）。

    ジャンクションは Windows にしかないので、この関数は Windows でだけ呼ばれる。
    """
    state, value = read_os(win_file_id, path)
    if state != "ok":
        return state, None
    if not any(value[1]):
        return "denied", None
    return "ok", value


def chain_identities(chain):
    """(状態, 識別子の並び)。chain の各ディレクトリの識別子を、起点から順に取る。"""
    found = []
    for path in chain:
        state, one = identity(path)
        if state != "ok":
            return state, None
        found.append(one)
    return "ok", tuple(found)


def is_junction(entry):
    """(状態, ジャンクションか)。Windows のほかでは、呼び出しをせずに偽を返す。"""
    if not NT:
        return "ok", False
    state, st = read_os(entry.stat, follow_symlinks=False)
    if state != "ok":
        return state, False
    return "ok", bool(st.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT) \
        and st.st_reparse_tag == stat.IO_REPARSE_TAG_MOUNT_POINT


def walk(start, prefix="", skip_top=False):
    """start の下をたどり、Walk を返す。

    起点には、リンクであっても降りる。途中のディレクトリのシンボリックリンクには降りない。ジャンクションには降りる。
    ジャンクションを通った道筋では、入ろうとするディレクトリの識別子が、起点からそこまでのどれかと同じなら降りない。
    """
    files, unlistable, unknown = [], [], []
    # スタックの項目: (ディレクトリのパス, 相対パスの接頭辞, 起点からここまでのパスの並び, 識別子の並びか None)
    start = str(start)
    stack = [(start, prefix, (start,), None)]
    while stack:
        directory, pre, chain, ids = stack.pop()
        state, entries = read_os(list_dir, directory)
        if state == "absent":
            continue
        if state == "denied":
            unlistable.append(pre.rstrip("/") or ".")
            continue
        for entry in entries:
            name = entry.name
            rel = pre + name
            if skip_top and pre == prefix and name in wiki_pages.SKIP_TOP_LEVEL_DIRS:
                continue
            state, is_link = read_os(entry.is_symlink)
            if state == "ok":
                state, is_dir = read_os(entry.is_dir)
            if state == "ok" and is_dir and not is_link:
                state, junction = is_junction(entry)
            if state == "absent":
                continue
            if state == "denied":
                unknown.append(rel)
                continue
            if is_dir:
                if is_link:
                    continue  # ディレクトリのシンボリックリンク。降りず、ファイルでもない
                child_ids = None
                if junction or ids is not None:
                    state, child = identity(entry.path)
                    path_ids = ids
                    if state == "ok" and path_ids is None:
                        # このジャンクションで、道筋に初めて識別子が要る。起点からここまでの識別子を、
                        # このジャンクションのためだけに取る。兄弟の項目には引き継がない（3 版目の誤り）。
                        state, path_ids = chain_identities(chain)
                    if state == "absent":
                        continue
                    if state == "denied":
                        unknown.append(rel)  # 同じ場所を回っていないかを、調べられなかった
                        continue
                    if child in path_ids:
                        continue  # 道筋の上のディレクトリに戻る。降りない
                    child_ids = path_ids + (child,)
                stack.append((entry.path, rel + "/", chain + (entry.path,), child_ids))
                continue
            if name.lower().endswith(".md"):
                state, st = read_os(os.stat, entry.path)
                if state == "absent":
                    continue  # 先のないリンク
                if state == "denied":
                    unknown.append(rel)
                    continue
                if stat.S_ISREG(st.st_mode):
                    files.append(MdFile(rel, st.st_size, st.st_mtime_ns))
    files.sort(key=lambda f: sort_key(f.rel))
    return Walk(files, sorted(unlistable, key=sort_key), sorted(unknown, key=sort_key))


def walk_pages(root):
    found = walk(root, skip_top=True)
    return Walk([f for f in found.files if wiki_pages.is_page_path(f.rel)], found.unlistable, found.unknown)


def walk_index_files(root):
    files, unknown = [], []
    state, st = read_os(os.stat, os.path.join(str(root), "index.md"))
    if state == "denied":
        unknown.append("index.md")
    elif state == "ok" and stat.S_ISREG(st.st_mode):
        files.append(MdFile("index.md", st.st_size, st.st_mtime_ns))
    below = walk(os.path.join(str(root), "indexes"), prefix="indexes/")
    unlistable = ["indexes" if u == "." else u for u in below.unlistable]
    return Walk(files + below.files, unlistable, unknown + below.unknown)


def iter_page_files(root):
    return [f.rel for f in walk_pages(root).files]


def index_files(root):
    """今と同じ並び（index.md、そのあと indexes の下を Path の順）。"""
    found = [f.rel for f in walk_index_files(root).files]
    rest = sorted(Path(root) / rel for rel in found if rel != "index.md")
    return [rel for rel in found if rel == "index.md"] + [p.relative_to(root).as_posix() for p in rest]


# ---------------------------------------------------------------------------
# 木の作り（SPEC）と、そこから計算する答え
# ---------------------------------------------------------------------------
#
# 値が str ならファイル、dict ならディレクトリ、タプルならリンク。リンクの先は、木の根（wiki の親）からの相対パス。
#   ("dlink", 先)     ディレクトリのシンボリックリンク
#   ("flink", 先)     ファイルのシンボリックリンク
#   ("broken",)       先のないシンボリックリンク
#   ("junction", 先)  ジャンクション（Windows だけ）

NFD = unicodedata.normalize("NFD", "ガイド")
E_NFC = unicodedata.lookup("LATIN SMALL LETTER E WITH ACUTE")
E_NFD = unicodedata.normalize("NFD", E_NFC)

TREES = {
    "リンクを置いた木": {
        "wiki": {
            "a.md": "a", "Upper.MD": "u", ".hidden.md": "h", "index.md": "i", "SCHEMA.md": "s", "notes.txt": "n",
            "real": {"b.md": "b", "notes.txt": "n"},
            "concepts": {".NET": {"c.md": "c"}, "raw": {"cr.md": "cr"}},
            ".obsidian": {"o.md": "o"},
            "dir.md": {"in.md": "in"},
            "graph": {"README.md": "g"},
            "assets": {"x": {"as.md": "as"}},
            NFD: {NFD + ".md": "nfd"},
            "が.md": "ga", "か.md": "ka",
            "indexes": {"sources.md": "s", "Upper.MD": "u", "A.md": "a", ".hidden.md": "h", "i.md": "i",
                        "sub": {"deep.md": "d", "dir.md": {"in.md": "in"}}, "raw": {"r.md": "r"}},
            "raw": ("junction", "ext") if NT else ("dlink", "ext"),
            "dlink": ("dlink", "ext"),
            "flink.md": ("flink", "ext/c.md"),
            "broken.md": ("broken",),
            "dirlink.md": ("dlink", "ext"),
            **({"junc": ("junction", "ext")} if NT else {}),
        },
        "ext": {"c.md": "c", "deep": {"d.md": "d"}},
    },
    "indexes がシンボリックリンク": {
        "wiki": {"concepts": {"c.md": "c"}, "indexes": ("dlink", "ext")},
        "ext": {"sources.md": "s"},
    },
    "indexes がページのディレクトリを指す": {
        "wiki": {"index.md": "i", "concepts": {"c.md": "c"},
                 "indexes": ("junction", "wiki/concepts") if NT else ("dlink", "wiki/concepts")},
    },
    "indexes がファイル": {"wiki": {"indexes": "x", "a.md": "a"}},
    "空の wiki": {"wiki": {}},
    # NFC で同じになる 2 つの名前。Windows（NTFS）も、名前を正規化しないので、両方を置ける。
    "NFC と NFD の名前": {"wiki": {E_NFC + ".md": "1", E_NFD + ".md": "2",
                                   "indexes": {E_NFC + ".md": "1", E_NFD + ".md": "2"}}},
    # 解けないリンク（5 版目のあとに見つけた後退）。失敗を入れなくても、DirEntry.is_dir() と os.stat() が送出する。
    "解けないリンク": {
        "wiki": {"a.md": "a", "loop.md": ("rawlink", "loop.md"), "m1.md": ("rawlink", "m2.md"),
                 "m2.md": ("rawlink", "m1.md"), "sub": {"b.md": "b", "dloop": ("rawlink", "dloop", "dir")},
                 "indexes": {"ok.md": "o", "iloop.md": ("rawlink", "iloop.md")}}},
    # 索引の下の、ふつうのファイルでない項目（4 回目のレビューの重大 2）。今の index_files() は、どれも返す。
    "索引の下の、ふつうのファイルでない項目": {
        "wiki": {"index.md": "i", "real": {"r.md": "r"},
                 "indexes": {"ok.md": "o", "broken.md": ("broken",), "dirlink.md": ("dlink", "wiki/real"),
                             "dir.md": {"in.md": "i"}, **({} if NT else {"pipe.md": ("fifo",)})},
                 **({} if NT else {"pipe.md": ("fifo",)})}},
    # ジャンクションと、ジャンクションでないディレクトリが兄弟（3 回目のレビューの重大 1）
    **({"ジャンクションと通常のディレクトリが兄弟": {
        "wiki": {"j": ("junction", "ext"), "plain": {"x.md": "x", "deep": {"y.md": "y"}}, "z.md": "z"},
        "ext": {"c.md": "c"}}} if NT else {}),
}
if NT:
    TREES.update({
        "輪でないジャンクションの別名": {"wiki": {"a": {"x.md": "x"}, "alias": ("junction", "wiki/a")}},
        "下を指すジャンクション": {"wiki": {"a": {"b": {"c.md": "c"}, "j": ("junction", "wiki/a/b")}}},
        "循環: sub/loop と indexes が wiki を指す": {
            "wiki": {"a.md": "a", "sub": {"b.md": "b", "loop": ("junction", "wiki")}, "indexes": ("junction", "wiki")}},
        "循環: a/b/j が a を、a/me が a を指す": {
            "wiki": {"a": {"top.md": "t", "b": {"c.md": "c", "j": ("junction", "wiki/a")}, "me": ("junction", "wiki/a")}}},
        "循環: 2 つのジャンクション": {
            "wiki": {"x": {"p.md": "p", "j1": ("junction", "ext")}},
            "ext": {"q.md": "q", "j2": ("junction", "wiki/x")}},
        "循環: wiki の親を指す": {
            "wiki": {"a.md": "a", "up": ("junction", "")},
            "side": {"s.md": "s"}},
    })
else:
    TREES["名前に \\ を含む"] = {"wiki": {"a\\b.md": "1", "a0.md": "2", "c": {"d.md": "3"}}}
    TREES["鍵が同じになる名前"] = {"wiki": {"a\\b.md": "1", "a": {"b.md": "2"}, "a0.md": "3"}}

# 今の実装と、失敗のないときの結果が違ってよい木（設計が挙げた違い）。
CYCLIC = {name for name in TREES if name.startswith("循環")}
SAME_KEY = {"鍵が同じになる名前"}


def build(base, spec):
    """SPEC を、ディスクの上に作る。リンクは、ふつうの項目を作り終えてから作る。"""
    links = []

    def make(directory, node):
        directory.mkdir(parents=True, exist_ok=True)
        for name, value in node.items():
            path = directory / name
            if isinstance(value, dict):
                make(path, value)
            elif isinstance(value, str):
                path.write_text(value, encoding="utf-8")
            else:
                links.append((path, value))
    make(base, spec)
    for path, value in links:
        kind = value[0]
        if kind == "fifo":
            os.mkfifo(path)
            continue
        if kind == "rawlink":
            # 先を、リンクのあるディレクトリからの相対パスのまま書く（自分を指す、互いに指し合うリンクを作る）
            try:
                os.symlink(value[1], path, target_is_directory=(len(value) > 2 and value[2] == "dir"))
            except OSError:
                return False
            continue
        target = base / value[1] if len(value) > 1 else base / "no-such-target"
        if kind == "junction":
            done = subprocess.run(["cmd", "/c", "mklink", "/J", str(path), str(target)], capture_output=True).returncode == 0
        else:
            try:
                os.symlink(target, path, target_is_directory=(kind == "dlink"))
                done = True
            except OSError:
                done = False
        if not done:
            return False
    return True


def remove_tree(base):
    """リンクの先を消さずに、木を消す。"""
    if not base.exists():
        return
    for directory, dirs, files in os.walk(base, topdown=True):
        for name in list(dirs) + list(files):
            p = os.path.join(directory, name)
            if os.path.islink(p) or getattr(os.lstat(p), "st_reparse_tag", 0):
                if name in dirs:
                    dirs.remove(name)
                try:
                    os.unlink(p)
                except OSError:
                    os.rmdir(p)
    shutil.rmtree(base)


def resolve(spec, parts):
    """木の根からのパスを、リンクを解いて、(種類, 実体のパス) にする。種類は "dir"、"file"、None（ない）。"""
    node, real = spec, ()
    for part in parts:
        if not isinstance(node, dict) or part not in node:
            return None, None
        value = node[part]
        if isinstance(value, tuple):
            if value[0] == "broken":
                return None, None
            if value[0] == "fifo":
                return "fifo", real + (part,)
            if value[0] == "rawlink":
                return None, None  # 試作の木では、解けないリンクにだけ使う
            kind, real = resolve(spec, tuple(p for p in value[1].split("/") if p))
            if kind is None:
                return None, None
            node = spec
            for p in real:
                node = node[p]
        else:
            node, real = value, real + (part,)
    return ("dir" if isinstance(node, dict) else "file"), real


def node_at(spec, real):
    node = spec
    for part in real:
        node = node[part]
    return node


def model(spec, start, prefix="", skip_top=False):
    """SPEC から、失敗のないときの .md のファイルの相対パス（並びも）を計算する。走査のコードを使わない。"""
    kind, real = resolve(spec, start)
    found = []
    if kind != "dir":
        return found

    def descend(real, pre, path):
        for name, value in node_at(spec, real).items():
            rel = pre + name
            if skip_top and pre == prefix and name in wiki_pages.SKIP_TOP_LEVEL_DIRS:
                continue
            if isinstance(value, dict):
                child = real + (name,)
                if child not in path:
                    descend(child, rel + "/", path + (child,))
            elif isinstance(value, str):
                if name.lower().endswith(".md"):
                    found.append(rel)
            elif value[0] == "junction":
                kind, child = resolve(spec, tuple(p for p in value[1].split("/") if p))
                if kind == "dir" and child not in path:
                    descend(child, rel + "/", path + (child,))
            elif value[0] == "flink":
                kind, _real = resolve(spec, tuple(p for p in value[1].split("/") if p))
                if kind == "file" and name.lower().endswith(".md"):
                    found.append(rel)
            # dlink と broken は、降りず、ファイルでもない
    descend(real, prefix, (real,))
    return sorted(found, key=sort_key)


def model_pages(spec):
    return [rel for rel in model(spec, ("wiki",), skip_top=True) if wiki_pages.is_page_path(rel)]


def model_index(spec):
    kind, _real = resolve(spec, ("wiki", "index.md"))
    top = ["index.md"] if kind == "file" else []
    return top + model(spec, ("wiki", "indexes"), prefix="indexes/")


# ---------------------------------------------------------------------------
# 木ごとの確かめ
# ---------------------------------------------------------------------------


def old_pages(wiki):
    return [p.relative_to(wiki).as_posix() for p in wiki_pages.iter_page_files(Path(wiki))]


def old_index(wiki):
    return [p.relative_to(wiki).as_posix() for p in wiki_lint.index_files(Path(wiki))]


def expected_old_index(spec):
    """今の index_files() の集合を、今の規則で木から計算する。新しい集合からは作らない。

    今の規則: 最上位の index.md がファイルなら、それ。そのあと、indexes を起点に rglob("*.md") が返す名前のすべて。
    rglob は、名前が合えば、種類を確かめない（ディレクトリ、ディレクトリへのリンク、先のないリンク、FIFO も返す）。
    ふつうのディレクトリとジャンクションには降り、ディレクトリのシンボリックリンクには降りない。名前の合わせ方は、
    Windows では大文字と小文字を区別せず、Linux と macOS では区別する。
    """
    rels = []
    kind, _real = resolve(spec, ("wiki", "index.md"))
    if kind == "file":
        rels.append("index.md")
    kind, real = resolve(spec, ("wiki", "indexes"))
    if kind != "dir":
        return rels
    match = (lambda n: n.lower().endswith(".md")) if NT else (lambda n: n.endswith(".md"))

    def descend(real, pre, path):
        for name, value in node_at(spec, real).items():
            rel = pre + name
            if match(name):
                rels.append(rel)
            child = None
            if isinstance(value, dict):
                child = real + (name,)
            elif isinstance(value, tuple) and value[0] == "junction":
                target_kind, target = resolve(spec, tuple(p for p in value[1].split("/") if p))
                child = target if target_kind == "dir" else None
            if child is not None and child not in path:
                descend(child, rel + "/", path + (child,))
    descend(real, "indexes/", (real,))
    return rels


def same_up_to_ties(old, new, key):
    """old と new が、key で同じになる組の中の順だけ違うか（集合が同じで、各位置の鍵が同じ）。"""
    return sorted(old) == sorted(new) and len(old) == len(new) and all(key(a) == key(b) for a, b in zip(old, new))


def cmd_check(work):
    base_dir = Path(work) / "v6"
    ok = True
    for number, (label, spec) in enumerate(TREES.items()):
        base = base_dir / f"t{number}"
        remove_tree(base)
        if not build(base, spec):
            print(f"  {label}: リンクを作れなかったので飛ばした")
            continue
        wiki = base / "wiki"
        pages, index = walk_pages(wiki), walk_index_files(wiki)
        answer_pages, answer_index = model_pages(spec), model_index(spec)
        same_answer = [f.rel for f in pages.files] == answer_pages and [f.rel for f in index.files] == answer_index \
            and not (pages.unlistable or pages.unknown or index.unlistable or index.unknown)
        line = f"  {label}: ページ {len(answer_pages)} 個、索引 {len(answer_index)} 個、答えと一致: {same_answer}"
        if label in CYCLIC:
            line += "。今の実装との照合はしない（循環）"
            same_old = True
        else:
            got_old, got_new = old_pages(wiki), iter_page_files(wiki)
            old_idx, new_idx = old_index(wiki), index_files(wiki)
            # 今の index_files() の集合は、挙げた 2 つの違いを戻した答えと同じである
            index_set = sorted(old_idx) == sorted(expected_old_index(spec))
            cmp_old = [r for r in old_idx if r in new_idx]
            cmp_new = [r for r in new_idx if r in old_idx]
            pages_ok = same_up_to_ties(got_old, got_new, wiki_text.posix_rel)
            index_ok = index_set and same_up_to_ties(cmp_old, cmp_new, PurePath)
            line += f"。今の実装と、今の鍵で同じになる組の順を除いて一致: ページ {pages_ok}、索引 {index_ok}"
            if got_old != got_new or cmp_old != cmp_new:
                line += f"（組の順が違った: ページ 今 {got_old} 案 {got_new}、索引 今 {cmp_old} 案 {cmp_new}）"
            same_old = pages_ok and index_ok
        print(line)
        if not same_answer:
            print("    答え:", answer_pages, answer_index)
            print("    走査:", [f.rel for f in pages.files], [f.rel for f in index.files], pages.unlistable, pages.unknown)
        if label in CYCLIC or "別名" in label or "指す" in label or "兄弟" in label:
            print("    ページ:", answer_pages, "索引:", answer_index)
        ok = ok and same_answer and same_old
        remove_tree(base)
    return ok


def check_case_sensitive(work):
    """Windows で、大文字と小文字を区別するフォルダーに a.md と A.md を置き、今の実装と比べる。"""
    if not NT:
        return True
    base = Path(work) / "v6cs"
    remove_tree(base)
    wiki = base / "wiki"
    folders = [wiki / "indexes", wiki / "p"]
    for folder in folders:
        folder.mkdir(parents=True)
        done = subprocess.run(["fsutil", "file", "setCaseSensitiveInfo", str(folder), "enable"], capture_output=True)
        if done.returncode != 0:
            message = done.stdout.decode("cp932", "replace").strip().splitlines()
            print("  大文字と小文字を区別するフォルダーを作れなかったので飛ばした:", (message or [""])[-1][:80])
            remove_tree(base)
            return True
        (folder / "a.md").write_text("1", encoding="utf-8")
        (folder / "A.md").write_text("2", encoding="utf-8")
    old_p, new_p = old_pages(wiki), iter_page_files(wiki)
    old_i, new_i = old_index(wiki), index_files(wiki)

    def dropped_by_old_rglob(old, new):
        """Python 3.10 の rglob は、返したパスを Path の比較で重複除去する（_RecursiveWildcardSelector の yielded）。
        Windows では大文字と小文字だけが違う名前が同じになり、片方が落ちる。落ちたものが、どれも残ったもののどれかと
        Path で同じなら、その違いだけである。"""
        lost = set(new) - set(old)
        return set(old) < set(new) and all(any(PurePath(m) == PurePath(o) for o in old) for m in lost)

    pages_same = old_p == new_p  # ページの今の鍵（posix_rel）は大文字と小文字を区別するので、並びまで同じはず
    index_same = same_up_to_ties(old_i, new_i, PurePath)
    note = ""
    if not (pages_same and index_same) and sys.version_info < (3, 12) \
            and dropped_by_old_rglob(old_p, new_p) and dropped_by_old_rglob(old_i, new_i):
        note = "（今の実装は、Python 3.10 の rglob が Path の比較で重複を除くので、片方を落とした。挙げた違い）"
        pages_same = index_same = True
    pages_ok, index_ok = pages_same, index_same
    print(f"  大文字と小文字を区別するフォルダー: ページ 今 {old_p} 案 {new_p} 一致 {pages_ok}。"
          f"索引 今 {old_i} 案 {new_i}、今の鍵で同じになる組の順を除いて一致 {index_ok}{note}")
    remove_tree(base)
    return pages_ok and index_ok


# ---------------------------------------------------------------------------
# 探索: 口の呼び出しの N 回目に失敗を入れ、木から計算した答えと比べる
# ---------------------------------------------------------------------------

# 入れる失敗の種類と、走査に期待する読み方（読み替えの表の行から取る）
FAILURES = {
    "absent": lambda: FileNotFoundError(errno.ENOENT, "入れた失敗"),
    "denied": lambda: PermissionError(errno.EACCES, "入れた失敗"),
    "eio": lambda: OSError(errno.EIO, "入れた失敗"),
    "loop": (lambda: OSError(None, "入れた失敗", None, 1921)) if NT else (lambda: OSError(errno.ELOOP, "入れた失敗")),
    "ebadf": lambda: OSError(errno.EBADF, "入れた失敗"),
}
if NT:
    FAILURES["badname"] = lambda: OSError(None, "入れた失敗", None, 123)
    FAILURES["notready"] = lambda: OSError(None, "入れた失敗", None, 21)
EXPECT = {"absent": "absent", "denied": "denied", "eio": "raise", "loop": "absent", "ebadf": "denied",
          "badname": "absent", "notready": "denied"}
ENTRY_OPS = ("is_symlink", "is_dir", "entry.stat")
LIST_OPS = ("scandir", "scandir.next")


class Injector:
    """口の呼び出しを数え、N 回目に失敗を入れる。一覧は、開く、取り出す、閉じるを別々に数える。"""

    def __init__(self, root, fail_at=None, kind=None):
        self.root = os.path.abspath(str(root))
        self.fail_at, self.kind = fail_at, kind
        self.count = 0
        self.failed = None  # 失敗を入れた呼び出しの (名前, wiki からの相対パス)
        self.calls = []     # 呼び出しの (名前, wiki からの相対パス) の並び
        self.real = {"scandir": os.scandir, "stat": os.stat, "file_id": globals()["win_file_id"]}

    def rel(self, path):
        text = os.fspath(path)
        if text == self.root:
            return "."
        if text.startswith(self.root + os.sep):
            return text[len(self.root) + 1:].replace(os.sep, "/") if NT else text[len(self.root) + 1:]
        raise AssertionError(f"走査が、wiki の外のパスを口に渡した: {text}")

    def hit(self, name, path):
        index = self.count
        self.count += 1
        rel = self.rel(path)
        self.calls.append((name, rel))
        if index == self.fail_at:
            self.failed = (name, rel)
            raise FAILURES[self.kind]()

    def scandir(self, path):
        self.hit("scandir", path)
        injector = self

        class Entry:
            def __init__(self, entry):
                self._entry = entry
                self.name, self.path = entry.name, entry.path

            def is_symlink(self):
                injector.hit("is_symlink", self.path)
                return self._entry.is_symlink()

            def is_dir(self, **kwargs):
                injector.hit("is_dir", self.path)
                return self._entry.is_dir(**kwargs)

            def stat(self, **kwargs):
                injector.hit("entry.stat", self.path)
                return self._entry.stat(**kwargs)

        class Listing:
            def __enter__(self):
                self.it = injector.real["scandir"](path)
                self.it.__enter__()
                return self

            def __iter__(self):
                return self

            def __next__(self):
                injector.hit("scandir.next", path)
                return Entry(next(self.it))

            def __exit__(self, *exc):
                # 閉じるときの失敗は、CPython が捨てる（ScandirIterator_closedir は FindClose と closedir の
                # 戻り値を見ない）。走査は閉じる前に項目を全部取り出しているので、結果は変わらない。数えない。
                self.it.__exit__(*exc)
                return False

        return Listing()

    def stat(self, path, *args, **kwargs):
        self.hit("stat", path)
        return self.real["stat"](path, *args, **kwargs)

    def file_id(self, path):
        self.hit("file_id", path)
        return self.real["file_id"](path)

    def __enter__(self):
        os.scandir, os.stat = self.scandir, self.stat
        globals()["win_file_id"] = self.file_id
        return self

    def __exit__(self, *exc):
        os.scandir, os.stat = self.real["scandir"], self.real["stat"]
        globals()["win_file_id"] = self.real["file_id"]


def expected_calls(spec, start, prefix="", skip_top=False, top_index=False):
    """木から、走査が呼ぶはずの口の呼び出しと、その役割を計算する。走査のコードを使わない。

    戻り値は {(名前, wiki からの相対パス): 役割の集合}。役割は次のどれかである。
      ("list", X)   ディレクトリ X の一覧。失敗すると、X の下が欠ける
      ("entry", E)  項目 E の種類。失敗すると、E とその下が欠ける
      ("file", X)   .md の項目 X がファイルかどうか。失敗すると、X が欠ける
      ("self", X)   ディレクトリ X の識別子。失敗すると、X とその下が欠ける
      ("chain", J)  ジャンクション J のための、道筋のディレクトリの識別子。失敗すると、J とその下が欠ける
    """
    calls = {}

    def add(op, rel, role):
        calls.setdefault((op, rel), set()).add(role)

    if top_index:
        add("stat", "index.md", ("file", "index.md"))
    start_rel = prefix.rstrip("/") or "."
    kind, real = resolve(spec, start)
    add("scandir", start_rel, ("list", start_rel))
    if kind != "dir":
        return calls  # 起点がないか、ファイルである。一覧を開く呼び出しだけをする

    def chain_rels(pre):
        rels = [start_rel]
        parts = [p for p in pre[len(prefix):].split("/") if p]
        for i in range(1, len(parts) + 1):
            rels.append(prefix + "/".join(parts[:i]))
        return rels

    def descend(real, pre, path, through):
        rel_dir = pre.rstrip("/") or "."
        add("scandir", rel_dir, ("list", rel_dir))
        add("scandir.next", rel_dir, ("list", rel_dir))
        for name, value in node_at(spec, real).items():
            rel = pre + name
            if skip_top and pre == prefix and name in wiki_pages.SKIP_TOP_LEVEL_DIRS:
                continue  # 名前だけで飛ばす。どの呼び出しもしない
            add("is_symlink", rel, ("entry", rel))
            add("is_dir", rel, ("entry", rel))
            junction = isinstance(value, tuple) and value[0] == "junction"
            child = None
            if isinstance(value, dict):
                child = real + (name,)
            elif junction:
                target_kind, target = resolve(spec, tuple(p for p in value[1].split("/") if p))
                child = target if target_kind == "dir" else None
            if child is not None:
                if NT:
                    add("entry.stat", rel, ("entry", rel))
                if junction or through:
                    add("file_id", rel, ("self", rel))
                    if junction and not through:
                        for c in chain_rels(pre):
                            add("file_id", c, ("chain", rel))
                if child not in path:
                    descend(child, rel + "/", path + (child,), through or junction)
            elif not (isinstance(value, tuple) and value[0] in ("dlink", "rawlink")) and name.lower().endswith(".md"):
                # 解けないリンクは、is_dir() が送出し、そこで「ない」になるので、os.stat() を呼ばない
                add("stat", rel, ("file", rel))
    if start_rel == ".":
        descend(real, prefix, (real,), False)
    else:
        # 起点は、リンクでも降りる。起点そのものの一覧は、上で足してある
        descend(real, prefix, (real,), False)
    return calls


def answers_with_failure(answer, roles, kind):
    """失敗を入れた呼び出しの役割から、ありうる答え (files, unlistable, unknown) の並びを計算する。

    1 つの呼び出しが、いくつかのジャンクションの道筋に共通する（chain）ときは、そのどれか 1 つが欠ける。
    """
    out = []
    for what, place in sorted(roles):
        if what == "list":
            files = [rel for rel in answer if not (place == "." or rel.startswith(place + "/"))]
            notices = ([place], [])
        else:
            files = [rel for rel in answer if not (rel == place or rel.startswith(place + "/"))]
            notices = ([], [place])
        out.append((files, [], []) if kind == "absent" else (files, notices[0], notices[1]))
    return out


def explore(wiki, function, answer, expected, label, quiet=False):
    """function(wiki) -> Walk に、口の呼び出しのそれぞれで 3 つの失敗を入れ、木から計算した答えと比べる。"""
    violations = []
    with Injector(wiki) as base_run:
        try:
            baseline = function(wiki)
        except OSError as exc:
            violations.append(f"失敗なし: 送出した（{type(exc).__name__}、errno {exc.errno}、winerror {getattr(exc, 'winerror', None)}）")
            if not quiet:
                print(f"  {label}: 失敗なしで送出した")
            return violations, 0
    if [f.rel for f in baseline.files] != answer or baseline.unlistable or baseline.unknown:
        violations.append(f"失敗なし: 答えと違う {[f.rel for f in baseline.files]}")
    made = set(base_run.calls)
    extra, missing = sorted(made - set(expected)), sorted(set(expected) - made)
    if extra:
        violations.append(f"失敗なし: 木から決まらない呼び出しをした {extra[:4]}")
    if missing:
        violations.append(f"失敗なし: 木から決まる呼び出しをしなかった {missing[:4]}")
    runs = 0
    for index in range(base_run.count):
        for kind in FAILURES:
            runs += 1
            with Injector(wiki, index, kind) as run:
                try:
                    result, raised = function(wiki), None
                except OSError as exc:
                    result, raised = None, exc
            if run.failed is None:
                violations.append(f"{index} 回目の呼び出しに届かなかった（{kind}）")
                continue
            where = f"{run.failed[0]}({run.failed[1]}) に {kind}"
            behavior = EXPECT[kind]
            if behavior == "raise":
                if raised is None or raised.errno != errno.EIO:
                    violations.append(f"{where}: 送出しなかった")
                continue
            if raised is not None:
                violations.append(f"{where}: 送出した（{type(raised).__name__}）")
                continue
            roles = expected.get(run.failed)
            if not roles:
                violations.append(f"{where}: 木から決まらない呼び出し")
                continue
            wants = answers_with_failure(answer, roles, behavior)
            got = ([f.rel for f in result.files], result.unlistable, result.unknown)
            if got not in wants:
                violations.append(f"{where}: 答えと違う。答え {wants[0]}" + (f" ほか {len(wants) - 1} 通り" if len(wants) > 1 else "")
                                  + f"、走査 {got}")
    if not quiet:
        print(f"  {label}: 口の呼び出し {base_run.count} 回、失敗を入れた実行 {runs} 回、答えと違った実行 {len(violations)} 件")
    return violations, runs


# 対照: わざと決まりを破った実装。探索が、どれも見つけることを確かめる。


def swapped(name, replacement, function):
    def run(root):
        original = globals()[name]
        globals()[name] = replacement
        try:
            return function(root)
        finally:
            globals()[name] = original
    return run


def read_os_swallow(call, *args, **kwargs):
    try:
        return "ok", call(*args, **kwargs)
    except OSError:
        return "absent", None


def identity_ignores_zero(path):
    """識別子を取れなかったとき、パスの文字列を識別子の代わりにする（文字列の比較への逃げ道）。"""
    try:
        st = os.stat(path)
    except OSError:
        return "ok", ("path", os.path.normcase(path))
    return "ok", (st.st_dev, st.st_ino)


def control_silent(root):
    found = walk_pages(root)
    return Walk(found.files, [], [])


def control_discard_all(root):
    """知らせがあったら、知らせを 1 つにして全ページを捨てる（2 回目のレビューの軽微 1 の対照）。"""
    found = walk_pages(root)
    if found.unlistable or found.unknown:
        return Walk([], ["."], [])
    return found


def control_nfc_key(root):
    """並びの鍵を、NFC だけにする（2 版目と同じ誤り）。"""
    found = walk_pages(root)
    files = sorted(found.files, key=lambda f: (unicodedata.normalize("NFC", f.rel), f.rel))
    return Walk(files, found.unlistable, found.unknown)


CONTROLS = [
    ("どの失敗も「ない」にする", swapped("read_os", read_os_swallow, walk_pages)),
    ("権限を知らせずに飛ばす", control_silent),
    ("知らせがあったら全ページを捨てる", control_discard_all),
]
if NT:
    # 識別子を使うのは、ジャンクションのある道筋だけである。ジャンクションのない OS では、違いが出ない。
    CONTROLS.append(("識別子を取れないとき、パスの文字列で比べる", swapped("identity", identity_ignores_zero, walk_pages)))
    CONTROLS.append(("3 版目の試作（道筋の識別子が兄弟に漏れる）", walk_v3.walk_pages))
    CONTROLS.append(("4 版目の試作（識別子を os.stat() から取る）", walk_v4.walk_pages))
CONTROLS.append(("5 版目の試作（解けないリンクで送出する）", walk_v5.walk_pages))
if not NT:
    # Windows では、名前に区切りの文字を置けないので、今の鍵と NFC だけの鍵の違いが、この木では出ない。
    CONTROLS.append(("並びの鍵を NFC だけにする", control_nfc_key))


def cmd_explore(work):
    base_dir = Path(work) / "v6"
    ok = True
    total = 0
    built = {}
    for number, (label, spec) in enumerate(TREES.items()):
        base = base_dir / f"t{number}"
        remove_tree(base)
        if not build(base, spec):
            print(f"  {label}: リンクを作れなかったので飛ばした")
            continue
        wiki = base / "wiki"
        built[label] = (wiki, spec)
        targets = (("ページ", walk_pages, model_pages(spec), expected_calls(spec, ("wiki",), "", True)),
                   ("索引", walk_index_files, model_index(spec),
                    expected_calls(spec, ("wiki", "indexes"), "indexes/", False, True)))
        for name, function, answer, expected in targets:
            found, runs = explore(wiki, function, answer, expected, f"{label}、{name}")
            total += runs
            ok = ok and not found
            for line in found[:4]:
                print("    ", line[:300])
    print(f"  失敗を入れた実行の合計: {total} 回")
    print("  対照（どの木かで、答えと違った実行が 1 件以上あれば、探索が働いている）:")
    for name, function in CONTROLS:
        caught, where = 0, None
        for label, (wiki, spec) in built.items():
            found, _runs = explore(wiki, function, model_pages(spec), expected_calls(spec, ("wiki",), "", True),
                                   label, quiet=True)
            if found and where is None:
                where = (label, found[0])
            caught += len(found)
        print(f"  対照「{name}」: 答えと違った実行 {caught} 件" + (f"（例: {where[0]}、{where[1][:120]}）" if where else ""))
        ok = ok and caught > 0
    for label, (wiki, _spec) in built.items():
        remove_tree(wiki.parent)
    return ok


def cmd_identity(work):
    """識別子を取る役割の確かめ（Windows だけ）。FileId が 0、識別子を持たないファイルシステム、兄弟、.md の項目。"""
    if not NT:
        print("  飛ばした（ジャンクションは Windows だけ）")
        return True
    base = Path(work) / "v6id"
    remove_tree(base)
    ok = True
    real = globals()["win_file_id"]

    def show(label, result, files, unknown):
        nonlocal ok
        got = [f.rel for f in result.files]
        good = got == files and result.unknown == unknown and not result.unlistable
        ok = ok and good
        print(f"  {label}: ページ {got}、unknown {result.unknown}、期待どおり: {good}")

    def patched(fake, function, wiki):
        globals()["win_file_id"] = fake
        try:
            return function(wiki)
        finally:
            globals()["win_file_id"] = real

    def zero_for(target):
        def fake(path):
            value = real(path)
            return (value[0], bytes(16)) if os.fspath(path) == target else value
        return fake

    def noid_for(target):
        def fake(path):
            if os.fspath(path) == target:
                raise NoFileId(None, "識別子を返さない（入れた失敗）", path, 50)
            return real(path)
        return fake

    build(base / "t1", {"wiki": {"a.md": "a", "junc": ("junction", "ext")}, "ext": {"c.md": "c"}})
    wiki = base / "t1" / "wiki"
    show("失敗なし", walk_pages(wiki), ["a.md", "junc/c.md"], [])
    show("ジャンクションの FileId が 0", patched(zero_for(str(wiki / "junc")), walk_pages, wiki), ["a.md"], ["junc"])
    show("ジャンクションの先が識別子を持たない", patched(noid_for(str(wiki / "junc")), walk_pages, wiki), ["a.md"], ["junc"])
    show("起点の FileId が 0", patched(zero_for(str(wiki)), walk_pages, wiki), ["a.md"], ["junc"])

    build(base / "t2", {"wiki": {"a.md": "a", "sub": {"b.md": "b", "loop": ("junction", "wiki")}}})
    wiki = base / "t2" / "wiki"
    show("循環、失敗なし", walk_pages(wiki), ["a.md", "sub/b.md"], [])
    show("循環、道筋の sub が識別子を持たない", patched(noid_for(str(wiki / "sub")), walk_pages, wiki), ["a.md", "sub/b.md"], ["sub/loop"])

    build(base / "t3", {"wiki": {"j": ("junction", "ext"), "plain": {"x.md": "x"}}, "ext": {"c.md": "c"}})
    wiki = base / "t3" / "wiki"
    calls = []

    def recording(path):
        calls.append(os.fspath(path))
        return real(path)
    show("兄弟", patched(recording, walk_pages, wiki), ["j/c.md", "plain/x.md"], [])
    plain = str(wiki / "plain")
    good = plain not in calls
    ok = ok and good
    print(f"  兄弟: 通常のディレクトリ plain に、識別子を取る呼び出しをしなかった: {good}（呼んだ先 {len(calls)} 個）")

    # .md の項目への os.stat が、成功で識別子 0 を返す（Windows で開けないファイル）。ファイルとして返す。
    build(base / "t4", {"wiki": {"a.md": "a", "locked.md": "l"}})
    wiki = base / "t4" / "wiki"
    real_stat = os.stat
    locked = str(wiki / "locked.md")

    def zero_stat(path, *args, **kwargs):
        st = real_stat(path, *args, **kwargs)
        if os.fspath(path) == locked:
            return os.stat_result((st.st_mode, 0, 0, st.st_nlink, st.st_uid, st.st_gid, st.st_size,
                                   st.st_atime, st.st_mtime, st.st_ctime))
        return st
    os.stat = zero_stat
    try:
        show(".md の項目の識別子が 0（開けないファイル）", walk_pages(wiki), ["a.md", "locked.md"], [])
    finally:
        os.stat = real_stat
    remove_tree(base)
    return ok


def cmd_wikis(paths):
    ok = True
    for path in paths:
        wiki = Path(path)
        same_pages = old_pages(wiki) == iter_page_files(wiki)
        old_idx = [rel for rel in old_index(wiki) if (wiki / rel).is_file()]
        new_idx = [rel for rel in index_files(wiki) if NT or rel == "index.md" or rel.endswith(".md")]
        print(f"  {wiki.name}: ページ {len(iter_page_files(wiki))} 個、並びまで一致: {same_pages}。"
              f"索引 {len(new_idx)} 個、挙げた違いを除いて一致: {old_idx == new_idx}")
        ok = ok and same_pages and old_idx == new_idx
    return ok


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    print(f"python {sys.version.split()[0]} {sys.platform}  {sys.argv[1]}")
    if sys.argv[1] == "wikis":
        done = cmd_wikis(sys.argv[2:])
    else:
        if sys.argv[1] == "check":
            done = cmd_check(sys.argv[2])
            done = check_case_sensitive(sys.argv[2]) and done
            done = cmd_identity(sys.argv[2]) and done
        else:
            done = cmd_explore(sys.argv[2])
    print("  終了:", "よい" if done else "だめ")
    sys.exit(0 if done else 1)
