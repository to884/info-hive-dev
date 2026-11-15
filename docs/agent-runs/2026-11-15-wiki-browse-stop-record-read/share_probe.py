"""Windows で、置き換え（os.replace）と消す（os.unlink）の最中に、読む側が開いたときの失敗を数える。

使い方: python share_probe.py <作業用のディレクトリ> <読む形: osopen|share7> <書く形: replace|unlink> <秒>
書く側は子プロセスで、server.json.new を作って server.json に置き換える（または、server.json を消して作り直す）。
読む側は親で、server.json を開いて読んで閉じる。両方の失敗の winerror を数える。
"""
import ctypes
import json
import msvcrt
import os
import subprocess
import sys
import time
from collections import Counter
from ctypes import wintypes

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.CreateFileW.restype = wintypes.HANDLE
k32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
                            wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
INVALID = wintypes.HANDLE(-1).value


def open_share7(path):
    h = k32.CreateFileW(path, 0x80000000, 0x7, None, 3, 0x80, None)
    if h in (None, INVALID):
        code = ctypes.get_last_error()
        raise OSError(None, ctypes.FormatError(code).strip(), path, code)
    return msvcrt.open_osfhandle(h, os.O_RDONLY | os.O_BINARY)


def open_new_share7(path):
    # _win_open と同じ（GENERIC_WRITE、共有 7、CREATE_NEW、FILE_FLAG_OPEN_REPARSE_POINT）
    h = k32.CreateFileW(path, 0x40000000, 0x7, None, 1, 0x80 | 0x00200000, None)
    if h in (None, INVALID):
        code = ctypes.get_last_error()
        raise OSError(None, ctypes.FormatError(code).strip(), path, code)
    return msvcrt.open_osfhandle(h, os.O_WRONLY | os.O_BINARY)


def key(e):
    return f"{type(e).__name__}/{getattr(e, 'winerror', None)}"


def writer(d, mode, seconds):
    rec = os.path.join(d, "server.json")
    new = rec + ".new"
    errs = Counter()
    n = 0
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        n += 1
        step = "?"
        try:
            if mode == "unlink":
                step = "unlink"
                try:
                    os.unlink(rec)
                except FileNotFoundError:
                    pass
                step = "create"
                fd = open_new_share7(rec)
                os.write(fd, b'{"n": %d}' % n)
                os.close(fd)
            else:
                step = "unlink-new"
                try:
                    os.unlink(new)
                except FileNotFoundError:
                    pass
                step = "create-new"
                fd = open_new_share7(new)
                os.write(fd, b'{"n": %d}' % n)
                os.close(fd)
                step = "replace"
                os.replace(new, rec)
            errs["ok"] += 1
        except OSError as e:
            errs[step + ":" + key(e)] += 1
    print(json.dumps(dict(errs)))


def main():
    if sys.argv[1] == "--writer":
        writer(sys.argv[2], sys.argv[3], float(sys.argv[4]))
        return
    d, rmode, wmode, seconds = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
    os.makedirs(d, exist_ok=True)
    rec = os.path.join(d, "server.json")
    with open(rec, "wb") as f:
        f.write(b"{}")
    child = subprocess.Popen([sys.executable, __file__, "--writer", d, wmode, str(seconds)],
                             stdout=subprocess.PIPE, text=True)
    errs = Counter()
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        try:
            fd = os.open(rec, os.O_RDONLY | os.O_BINARY) if rmode == "osopen" else open_share7(rec)
            try:
                os.read(fd, 1 << 20)
            finally:
                os.close(fd)
            errs["ok"] += 1
        except OSError as e:
            errs[key(e)] += 1
    out, _ = child.communicate()
    print(json.dumps({"reader": rmode, "writer_mode": wmode, "reader_result": dict(errs),
                      "writer_result": json.loads(out)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
