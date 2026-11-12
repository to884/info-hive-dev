"""ロックのファイルが、先のないファイルのシンボリックリンクのとき、O_CREAT で開くと先にファイルができるかを確かめる。
あわせて、O_CREAT | O_EXCL ならリンクの名前で失敗するかを確かめる。"""
import os
import stat
import sys
import tempfile

print("Python", sys.version.split()[0], sys.platform)
O_BINARY = getattr(os, "O_BINARY", 0)
with tempfile.TemporaryDirectory() as tmp:
    wiki = os.path.join(tmp, "wiki")
    work = os.path.join(tmp, "site.browse-work")
    os.makedirs(wiki)
    os.makedirs(work)
    target = os.path.join(wiki, "created.md")
    lock = os.path.join(work, "build.lock")
    os.symlink(target, lock)
    st = os.lstat(lock)
    print("lstat: S_ISLNK", stat.S_ISLNK(st.st_mode), "attrs", hex(getattr(st, "st_file_attributes", 0)))
    try:
        fd = os.open(lock, os.O_RDWR | os.O_CREAT | O_BINARY, 0o600)
        os.close(fd)
        print("O_CREAT: 開けた。先ができたか:", os.path.exists(target))
    except OSError as e:
        print("O_CREAT: 失敗", type(e).__name__, e)
    if os.path.exists(target):
        os.unlink(target)
    try:
        fd = os.open(lock, os.O_RDWR | os.O_CREAT | os.O_EXCL | O_BINARY, 0o600)
        os.close(fd)
        print("O_CREAT|O_EXCL: 開けた。先ができたか:", os.path.exists(target))
    except OSError as e:
        print("O_CREAT|O_EXCL: 失敗", type(e).__name__, "先ができたか:", os.path.exists(target))
    os.unlink(lock)
