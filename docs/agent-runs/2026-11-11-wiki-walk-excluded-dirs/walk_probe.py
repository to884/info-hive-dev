"""wiki をたどる経路の設計のための実測。

今の `Path.rglob()` と、設計の案のたどり方（`os.scandir()` で、除く最上位のディレクトリに降りない）を、
同じ木で比べる。標準ライブラリだけで動く。作業用のディレクトリの下に木を作り、最後に消す。

使い方:
    python walk_probe.py tree <作業用のディレクトリ>     リンクとジャンクションを置いた木で比べる
    python walk_probe.py loop <作業用のディレクトリ>     循環するリンクを置いた木で、止まり方を見る
    python walk_probe.py cycles <作業用のディレクトリ>   循環の検出を入れた案を、循環の形ごとに確かめる（Windows だけ）
    python walk_probe.py denied <作業用のディレクトリ>   一覧を作れないディレクトリの扱いを見る（POSIX だけ）
    python walk_probe.py wikis <wiki>...                 実物の wiki で比べる
"""
import os
import shutil
import stat
import subprocess
import sys
import time
import unicodedata
from pathlib import Path, PurePosixPath

# info-hive-wiki 0.10.0 の wiki_pages.py と同じ値。
SKIP_TOP_LEVEL_FILES = frozenset({"SCHEMA.md", "index.md", "log.md", "README.md"})
SKIP_TOP_LEVEL_DIRS = frozenset({"indexes", "graph", "raw", "assets", ".evolution", ".wiki-cache"})

SCANNED = []  # 案のたどり方が os.scandir() を呼んだディレクトリ（wiki からの相対パス）


def is_page_path(rel):
    parts = PurePosixPath(str(rel).replace("\\", "/")).parts
    if not parts or not parts[-1].lower().endswith(".md") or parts[-1].startswith("."):
        return False
    if len(parts) == 1:
        return parts[0] not in SKIP_TOP_LEVEL_FILES
    return parts[0] not in SKIP_TOP_LEVEL_DIRS


def posix_rel(rel):
    return unicodedata.normalize("NFC", rel)


def old_iter_page_files(root):
    """今の wiki_pages.iter_page_files() と同じ。NFC の相対パスの順に並べた、ディスク上の綴りの相対パス。"""
    found = []
    for md_path in root.rglob("*.[mM][dD]"):
        rel = md_path.relative_to(root).as_posix()
        if is_page_path(rel) and md_path.is_file():
            found.append((posix_rel(rel), rel))
    found.sort(key=lambda item: item[0])
    return [rel for _key, rel in found]


def old_all_md(root):
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*.[mM][dD]"))


def is_junction(entry):
    """Windows のジャンクションか。Python 3.10 でも使える見分け方（DirEntry.is_junction は 3.12 から）。"""
    if os.name != "nt":
        return False
    st = entry.stat(follow_symlinks=False)
    return bool(st.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)         and st.st_reparse_tag == stat.IO_REPARSE_TAG_MOUNT_POINT


def same_or_ancestor(target, directory):
    """target が、directory と同じディレクトリか、その祖先か。os.path.samefile で 1 階層ずつ比べる。"""
    here = directory
    while True:
        try:
            a, b = os.stat(target), os.stat(here)
            if a.st_ino and b.st_ino:
                same = (a.st_dev, a.st_ino) == (b.st_dev, b.st_ino)
            else:
                same = None  # 識別子を返さないファイルシステム
        except OSError:
            same = None
        if same is None:
            # 識別子で比べられないときは、実体のパスの文字列で比べる（ジャンクションは Windows だけなので normcase）。
            same = os.path.normcase(os.path.realpath(target)) == os.path.normcase(os.path.realpath(here))
        if same:
            return True
        parent = os.path.dirname(here)
        if parent == here:
            return False
        here = parent


def walk_markdown(root, unlistable=None, detect_cycles=False):
    """設計の案。名前が .md で終わる項目の相対パス（/ 区切り、ディスク上の綴り）を、NFC の順、同じなら綴りの順で返す。

    最上位の除く名前の項目は、種類を調べずに飛ばす。シンボリックリンクのディレクトリには降りず、
    ジャンクションには降りる（どちらも今の rglob と同じ）。権限がなくて一覧を作れないディレクトリと、
    たどる間になくなったディレクトリは飛ばし、unlistable にリストを渡せば、その相対パスを足す。
    そのほかの OSError は送出する。
    """
    out = []
    # hops: ここに来るまでに通ったジャンクションのそれぞれについて、それを置いていたディレクトリの実体。
    stack = [(str(root), "", ())]
    while stack:
        directory, prefix, hops = stack.pop()
        SCANNED.append(prefix.rstrip("/") or ".")
        try:
            with os.scandir(directory) as it:
                entries = list(it)
        except (PermissionError, FileNotFoundError, NotADirectoryError):
            if unlistable is not None:
                unlistable.append(prefix.rstrip("/") or ".")
            continue
        for entry in entries:
            name = entry.name
            rel = prefix + name
            if not prefix and name in SKIP_TOP_LEVEL_DIRS:
                continue  # 名前だけで決める。リンクかどうかも、ディレクトリかどうかも調べない
            is_link = entry.is_symlink()
            is_dir = entry.is_dir()  # リンクの先で判定する（rglob と同じ）
            if is_dir and not is_link:
                child_hops = hops
                if detect_cycles and is_junction(entry):
                    target = os.path.realpath(entry.path)
                    here = os.path.realpath(directory)
                    if any(same_or_ancestor(target, d) for d in (here, *hops)):
                        continue  # 循環するジャンクション。降りず、名前も返さない
                    child_hops = hops + (here,)
                stack.append((entry.path, rel + "/", child_hops))
            if name.lower().endswith(".md"):
                out.append(rel)
    out.sort(key=lambda rel: (posix_rel(rel), rel))
    return out


def new_iter_page_files(root):
    return [rel for rel in walk_markdown(root) if is_page_path(rel) and (root / rel).is_file()]


def compare(root):
    root = Path(root)
    t = time.perf_counter()
    old = old_iter_page_files(root)
    t_old = time.perf_counter() - t
    del SCANNED[:]
    t = time.perf_counter()
    new = new_iter_page_files(root)
    t_new = time.perf_counter() - t
    print(f"{root.name}: 今 {len(old)} ページ（{t_old * 1000:.1f} ms、rglob が返す .md は {len(old_all_md(root))} 個）、"
          f"案 {len(new)} ページ（{t_new * 1000:.1f} ms、scandir {len(SCANNED)} 回）、並びも一致: {old == new}")
    if old != new:
        print("  今だけ:", sorted(set(old) - set(new))[:10])
        print("  案だけ:", sorted(set(new) - set(old))[:10])
    return old == new


def link(kind, path, target):
    """リンクを作る。作れたかどうかを返す。"""
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


def remove_tree(base):
    """リンクの先を消さずに、木を消す。"""
    if not base.exists():
        return
    for directory, dirs, files in os.walk(base, topdown=True):
        for name in list(dirs):
            p = os.path.join(directory, name)
            st = os.lstat(p)
            if os.path.islink(p) or getattr(st, "st_reparse_tag", 0):
                dirs.remove(name)
                try:
                    os.unlink(p)
                except OSError:
                    os.rmdir(p)
        for name in files:
            p = os.path.join(directory, name)
            if os.path.islink(p):
                os.unlink(p)
    shutil.rmtree(base)


def make_tree(base):
    wiki, ext = base / "wiki", base / "ext"
    nfd = unicodedata.normalize("NFD", "ガイド")
    for d in ("real", "concepts/.NET", ".obsidian", "concepts/raw", "indexes", "assets/x", "dir.md", "graph", nfd):
        (wiki / d).mkdir(parents=True)
    (ext / "deep").mkdir(parents=True)
    files = ["a.md", "Upper.MD", ".hidden.md", "index.md", "SCHEMA.md", "real/b.md", "concepts/.NET/c.md",
             ".obsidian/o.md", "concepts/raw/cr.md", "indexes/i.md", "assets/x/as.md", "dir.md/in.md",
             "graph/README.md", "real/notes.txt", f"{nfd}/{nfd}.md", "が.md", "か.md"]
    for f in files:
        (wiki / f).write_text("x", encoding="utf-8")
    (ext / "c.md").write_text("c", encoding="utf-8")
    (ext / "deep" / "d.md").write_text("d", encoding="utf-8")
    made = {
        # 除く名前のディレクトリが、外を指すリンクである場合（この設計の動機）。
        "raw -> ext（Windows はジャンクション、ほかはシンボリックリンク）":
            link("junction", wiki / "raw", ext) if os.name == "nt" else link("dir", wiki / "raw", ext),
        "junc -> ext（ジャンクション）": link("junction", wiki / "junc", ext),
        "dlink -> ext（ディレクトリのシンボリックリンク）": link("dir", wiki / "dlink", ext),
        "flink.md -> ext/c.md（ファイルのシンボリックリンク）": link("file", wiki / "flink.md", ext / "c.md"),
        "broken.md -> ない先": link("file", wiki / "broken.md", ext / "none.md"),
        "dirlink.md -> ext（.md で終わる名前のディレクトリのリンク）": link("dir", wiki / "dirlink.md", ext),
    }
    return wiki, made


def cmd_tree(work):
    base = Path(work) / "tree"
    remove_tree(base)
    wiki, made = make_tree(base)
    for name, ok in made.items():
        print(f"  作れた: {ok}  {name}")
    same = compare(wiki)
    print("  ページ:", old_iter_page_files(wiki))
    print("  今の rglob が返し、案が見ない .md:", sorted(set(old_all_md(wiki)) - set(walk_markdown(wiki))))
    del SCANNED[:]
    walk_markdown(wiki)
    print("  案が scandir を呼んだディレクトリ:", sorted(SCANNED))
    print("  案が除く名前のディレクトリに降りない:", not any(s.split("/")[0] in SKIP_TOP_LEVEL_DIRS for s in SCANNED))
    remove_tree(base)
    return same


def cmd_loop(work):
    base = Path(work) / "loop"
    remove_tree(base)
    wiki = base / "wiki"
    (wiki / "sub").mkdir(parents=True)
    (wiki / "a.md").write_text("x", encoding="utf-8")
    (wiki / "sub" / "b.md").write_text("x", encoding="utf-8")
    kind = "junction" if os.name == "nt" else "dir"
    print(f"  作れた: {link(kind, wiki / 'sub' / 'loop', wiki)}  sub/loop -> wiki（{kind}）")
    for label, func in (("今（rglob）", old_iter_page_files), ("案（scandir）", new_iter_page_files)):
        t = time.perf_counter()
        try:
            pages = func(wiki)
            depth = max(p.count("/") for p in pages)
            print(f"  {label}: {len(pages)} ページ、もっとも深いパスは {depth} 階層、{time.perf_counter() - t:.2f} 秒")
        except Exception as exc:  # noqa: BLE001 止まり方を見るための実測
            print(f"  {label}: {exc.__class__.__name__} で止まった（{time.perf_counter() - t:.2f} 秒）")
    remove_tree(base)
    return True


def cmd_cycles(work):
    if os.name != "nt":
        print("  飛ばした（ジャンクションは Windows だけ）")
        return True
    ok = True

    def pages(wiki):
        return [r for r in walk_markdown(wiki, detect_cycles=True) if is_page_path(r) and (wiki / r).is_file()]

    def case(label, build, expected):
        nonlocal ok
        base = Path(work) / "cycles"
        remove_tree(base)
        wiki = base / "wiki"
        wiki.mkdir(parents=True)
        build(base, wiki)
        t = time.perf_counter()
        got = pages(wiki)
        good = got == sorted(expected, key=lambda rel: (posix_rel(rel), rel))
        ok = ok and good
        print(f"  {label}: {got}（{time.perf_counter() - t:.3f} 秒）期待どおり: {good}")
        remove_tree(base)

    def write(path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x", encoding="utf-8")

    def self_loop(base, wiki):
        write(wiki / "a.md"); write(wiki / "sub" / "b.md")
        link("junction", wiki / "sub" / "loop", wiki)
    case("sub/loop -> wiki", self_loop, ["a.md", "sub/b.md"])

    def up_loop(base, wiki):
        write(wiki / "a" / "top.md"); write(wiki / "a" / "b" / "c.md")
        link("junction", wiki / "a" / "b" / "j", wiki / "a")
    case("a/b/j -> a", up_loop, ["a/top.md", "a/b/c.md"])

    def two_hops(base, wiki):
        write(wiki / "x" / "p.md"); write(base / "ext" / "q.md")
        link("junction", wiki / "x" / "j1", base / "ext")
        link("junction", base / "ext" / "j2", wiki / "x")
    case("x/j1 -> 外、外/j2 -> x", two_hops, ["x/p.md", "x/j1/q.md"])

    def down(base, wiki):
        write(wiki / "a" / "b" / "c.md")
        link("junction", wiki / "a" / "j", wiki / "a" / "b")
    case("a/j -> a/b（循環でない）", down, ["a/b/c.md", "a/j/c.md"])

    def outside(base, wiki):
        write(wiki / "a.md"); write(base / "ext" / "deep" / "d.md")
        link("junction", wiki / "junc", base / "ext")
    case("junc -> 外（循環でない）", outside, ["a.md", "junc/deep/d.md"])

    def self_target(base, wiki):
        write(wiki / "a" / "p.md")
        link("junction", wiki / "a" / "me", wiki / "a")
    case("a/me -> a（自分のいるディレクトリ）", self_target, ["a/p.md"])
    return ok


def cmd_denied(work):
    if os.name == "nt" or os.geteuid() == 0:
        print("  飛ばした（Windows か root では、権限で一覧を止められない）")
        return True
    base = Path(work) / "denied"
    if base.exists():
        os.chmod(base / "wiki" / "locked", 0o700)
        shutil.rmtree(base)
    wiki = base / "wiki"
    (wiki / "locked").mkdir(parents=True)
    (wiki / "a.md").write_text("x", encoding="utf-8")
    (wiki / "locked" / "b.md").write_text("x", encoding="utf-8")
    os.chmod(wiki / "locked", 0o000)
    try:
        try:
            print("  今（rglob）:", old_iter_page_files(wiki))
        except Exception as exc:  # noqa: BLE001
            print("  今（rglob）:", exc.__class__.__name__, "で止まった")
        unlistable = []
        print("  案（scandir）:", sorted(r for r in walk_markdown(wiki, unlistable=unlistable) if is_page_path(r)),
              "一覧を作れなかった:", unlistable)
    finally:
        os.chmod(wiki / "locked", 0o700)
        shutil.rmtree(base)
    return True


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    print(f"python {sys.version.split()[0]} {sys.platform}  {sys.argv[1]}")
    mode, args = sys.argv[1], sys.argv[2:]
    if mode == "wikis":
        ok = all([compare(p) for p in args])
    else:
        ok = {"tree": cmd_tree, "loop": cmd_loop, "denied": cmd_denied, "cycles": cmd_cycles}[mode](args[0])
    sys.exit(0 if ok else 1)
