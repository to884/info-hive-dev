"""索引のファイルの集め方と、ファイルかどうかの調べ方を、版ごとに確かめる（走査の計画の 2 版目のための実測）。

使い方:
    python index_probe.py index <作業用のディレクトリ>     今の wiki_lint.index_files() と同じ集め方が返すもの
    python index_probe.py isfile <作業用のディレクトリ>    os.stat が失敗したときの Path.is_file() と DirEntry
    python index_probe.py realpath                         os.path.realpath の strict の有無
"""
import errno
import inspect
import os
import shutil
import subprocess
import sys
from pathlib import Path
from unittest import mock


def index_files(wiki_root):
    """info-hive-wiki 0.10.0 の wiki_lint.index_files() と同じ。"""
    files = []
    top = wiki_root / "index.md"
    if top.is_file():
        files.append(top)
    split_dir = wiki_root / "indexes"
    if split_dir.is_dir():
        files.extend(sorted(split_dir.rglob("*.md")))
    return files


def link(kind, path, target):
    try:
        if kind == "junction":
            if os.name != "nt":
                return False
            return subprocess.run(["cmd", "/c", "mklink", "/J", str(path), str(target)],
                                  capture_output=True).returncode == 0
        os.symlink(target, path, target_is_directory=(kind == "dir"))
        return True
    except OSError:
        return False


def unlink_links(base):
    for directory, dirs, files in os.walk(base):
        for name in list(dirs) + files:
            p = os.path.join(directory, name)
            if os.path.islink(p) or getattr(os.lstat(p), "st_reparse_tag", 0):
                if name in dirs:
                    dirs.remove(name)
                try:
                    os.unlink(p)
                except OSError:
                    os.rmdir(p)


def fresh(base):
    if base.exists():
        unlink_links(base)
        shutil.rmtree(base)
    base.mkdir(parents=True)
    return base


def cmd_index(work):
    base = fresh(Path(work) / "index")
    # 1. ふつうの indexes
    wiki = base / "plain" / "wiki"
    (wiki / "indexes" / "sub" / "dir.md").mkdir(parents=True)
    for f in ("index.md", "indexes/sources.md", "indexes/Upper.MD", "indexes/b.md", "indexes/A.md",
              "indexes/.hidden.md", "indexes/sub/deep.md", "indexes/sub/dir.md/in.md", "indexes/notes.txt"):
        (wiki / f).write_text("x", encoding="utf-8")
    print("  ふつうの indexes:", [p.relative_to(wiki).as_posix() for p in index_files(wiki)])
    # 2. indexes がディレクトリのシンボリックリンク
    wiki = base / "symlink" / "wiki"
    ext = base / "symlink" / "ext"
    wiki.mkdir(parents=True)
    ext.mkdir(parents=True)
    (ext / "sources.md").write_text("x", encoding="utf-8")
    made = link("dir", wiki / "indexes", ext)
    print(f"  indexes がシンボリックリンク（作れた: {made}）:", [p.relative_to(wiki).as_posix() for p in index_files(wiki)])
    # 3. indexes がページのディレクトリを指す（Windows はジャンクション）
    wiki = base / "alias" / "wiki"
    (wiki / "concepts").mkdir(parents=True)
    (wiki / "concepts" / "c.md").write_text("x", encoding="utf-8")
    kind = "junction" if os.name == "nt" else "dir"
    made = link(kind, wiki / "indexes", wiki / "concepts")
    print(f"  indexes が concepts を指す（{kind}、作れた: {made}）:",
          [p.relative_to(wiki).as_posix() for p in index_files(wiki)],
          "rglob が返すページ:", sorted(p.relative_to(wiki).as_posix() for p in wiki.rglob("*.[mM][dD]")))
    # 4. indexes がファイル
    wiki = base / "file" / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "indexes").write_text("x", encoding="utf-8")
    print("  indexes がファイル:", [p.relative_to(wiki).as_posix() for p in index_files(wiki)])
    unlink_links(base)
    shutil.rmtree(base)


def cmd_isfile(work):
    base = fresh(Path(work) / "isfile")
    target = base / "a.md"
    target.write_text("x", encoding="utf-8")
    real_stat = os.stat

    def failing(exc):
        def fake(path, *args, **kwargs):
            if str(path).endswith("a.md"):
                raise exc
            return real_stat(path, *args, **kwargs)
        return fake

    cases = (("PermissionError", PermissionError(errno.EACCES, "x")), ("EIO", OSError(errno.EIO, "x")),
             ("FileNotFoundError", FileNotFoundError(errno.ENOENT, "x")))
    for name, exc in cases:
        with mock.patch("os.stat", failing(exc)):
            try:
                result = repr(target.is_file())
            except OSError as caught:
                result = f"送出 {type(caught).__name__}"
        print(f"  os.stat が {name} のとき、Path.is_file(): {result}")
    print("  Path.is_file の実装:", "os.path.isfile を呼ぶ" if "isfile" in inspect.getsource(Path.is_file) else "self.stat() を呼ぶ")
    with os.scandir(base) as it:
        entry = next(e for e in it if e.name == "a.md")
        st = entry.stat()
        print("  DirEntry.stat() の st_ino:", st.st_ino, " os.stat() の st_ino が 0 でない:", real_stat(target).st_ino != 0)
    shutil.rmtree(base)


def cmd_realpath():
    print("  os.path.realpath に strict がある:", "strict" in inspect.signature(os.path.realpath).parameters)
    missing = os.path.join(os.path.dirname(os.path.abspath(__file__)), "no-such-dir", "x")
    try:
        os.path.realpath(missing, strict=True)
        print("  strict=True で、ない先: 返した")
    except OSError as caught:
        print("  strict=True で、ない先: 送出", type(caught).__name__)
    print("  strict なしで、ない先: 返した", os.path.realpath(missing).endswith("x"))


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    print(f"python {sys.version.split()[0]} {sys.platform}  {sys.argv[1]}")
    if sys.argv[1] == "index":
        cmd_index(sys.argv[2])
    elif sys.argv[1] == "isfile":
        cmd_isfile(sys.argv[2])
    else:
        cmd_realpath()
