"""自分を指すシンボリックリンクで、今の実装と 5 版目の試作を比べる。pathlib が無視する失敗の一覧も出す。"""
import inspect
import os
import pathlib
import shutil
import sys
from pathlib import Path

for d in (r"C:\Works\info-hive-dev\docs\agent-runs\2026-11-11-wiki-walk-excluded-dirs",
          "/mnt/c/Works/info-hive-dev/docs/agent-runs/2026-11-11-wiki-walk-excluded-dirs"):
    sys.path.insert(0, d)
sys.stdout.reconfigure(encoding="utf-8")
import walk_v5 as v5  # noqa: E402

print(f"python {sys.version.split()[0]} {sys.platform}")
for name in ("_IGNORED_ERRNOS", "_IGNORED_WINERRORS", "_IGNORED_ERRORS"):
    for mod in (pathlib, getattr(pathlib, "_local", None), getattr(pathlib, "_abc", None)):
        if mod is not None and hasattr(mod, name):
            print(f"  pathlib の {name}: {getattr(mod, name)}")
print("  Path.is_file の実装:", "os.path.isfile" if "isfile" in inspect.getsource(Path.is_file) else "self.stat() と _ignore_error")

base = Path(sys.argv[1]) / "loop"
if base.exists():
    shutil.rmtree(base)
wiki = base / "wiki"
(wiki / "sub").mkdir(parents=True)
(wiki / "a.md").write_text("a", encoding="utf-8")
(wiki / "sub" / "b.md").write_text("b", encoding="utf-8")
cases = []
try:
    os.symlink("loop.md", wiki / "loop.md")              # 自分を指すファイルのリンク
    os.symlink("dloop", wiki / "sub" / "dloop", target_is_directory=True)  # 自分を指すディレクトリのリンク
    cases.append("作れた")
except OSError as exc:
    cases.append(f"作れなかった {exc}")
print("  リンク:", cases)
try:
    old = [p.relative_to(wiki).as_posix() for p in v5.wiki_pages.iter_page_files(wiki)]
    print("  今の iter_page_files():", old)
except OSError as exc:
    print("  今の iter_page_files(): 送出", type(exc).__name__, getattr(exc, "errno", None), getattr(exc, "winerror", None))
try:
    found = v5.walk_pages(wiki)
    print("  5 版目の walk_pages():", [f.rel for f in found.files], found.unlistable, found.unknown)
except OSError as exc:
    print("  5 版目の walk_pages(): 送出", type(exc).__name__, getattr(exc, "errno", None), getattr(exc, "winerror", None))
for entry in os.scandir(wiki):
    if entry.name == "loop.md":
        try:
            entry.is_dir()
            print("  DirEntry.is_dir(): 送出しなかった")
        except OSError as exc:
            print("  DirEntry.is_dir(): 送出", type(exc).__name__, exc.errno, getattr(exc, "winerror", None))
        try:
            os.stat(entry.path)
        except OSError as exc:
            print("  os.stat(): 送出", type(exc).__name__, exc.errno, getattr(exc, "winerror", None))
shutil.rmtree(base)
