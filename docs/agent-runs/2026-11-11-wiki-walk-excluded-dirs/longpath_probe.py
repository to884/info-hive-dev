"""Windows で、パスが MAX_PATH（260 文字）を超えるページを、今の実装と 6 版目の試作が返すかを確かめる。

使い方: python longpath_probe.py <作業用のディレクトリ>
"""
import os
import shutil
import sys
import winreg
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import walk_v6 as v6  # noqa: E402


def main(work):
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\FileSystem") as key:
            enabled = winreg.QueryValueEx(key, "LongPathsEnabled")[0]
    except OSError:
        enabled = None
    print("  LongPathsEnabled:", enabled)
    base = Path(work) / "long"
    if base.exists():
        shutil.rmtree("\\\\?\\" + str(base.resolve()))
    wiki = base / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "a.md").write_text("a", encoding="utf-8")
    deep = "\\\\?\\" + str(wiki.resolve())
    rel = []
    for i in range(6):
        name = f"d{i}-" + "x" * 50
        rel.append(name)
        os.mkdir(os.path.join(deep, *rel))
    with open(os.path.join(deep, *rel, "deep.md"), "w", encoding="utf-8") as f:
        f.write("d")
    full = os.path.join(str(wiki.resolve()), *rel, "deep.md")
    print("  深いページのパスの長さ:", len(full))
    try:
        old = [p.relative_to(wiki).as_posix().split("/")[-1] for p in v6.wiki_pages.iter_page_files(wiki)]
        print("  今の iter_page_files():", old)
    except OSError as exc:
        print("  今の iter_page_files(): 送出", type(exc).__name__, getattr(exc, "winerror", None))
    try:
        found = v6.walk_pages(wiki)
        print("  6 版目の walk_pages():", [f.rel.split("/")[-1] for f in found.files], "unlistable", len(found.unlistable),
              "unknown", len(found.unknown))
    except OSError as exc:
        print("  6 版目の walk_pages(): 送出", type(exc).__name__, getattr(exc, "winerror", None))
    shutil.rmtree("\\\\?\\" + str(base.resolve()))


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    print(f"python {sys.version.split()[0]} {sys.platform}  longpath")
    main(sys.argv[1])
