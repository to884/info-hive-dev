"""Windows で、ディレクトリの識別子を Win32 の呼び出しから直接取れるかを確かめる（ctypes、標準ライブラリだけ）。

os.stat() は、Python 3.12 以降、GetFileInformationByHandleEx(FileIdInfo) の失敗を捨てて、識別子の形を変えて
返す（4 回目のレビューの重大 1）。ここでは、CreateFileW と GetFileInformationByHandleEx(FileIdInfo) を自分で呼び、
失敗をすべて OSError として受け取る関数を作り、次を見る。

- 同じディレクトリを、ふつうのパスとジャンクションのパスで指したとき、識別子が同じになるか
- 別のディレクトリで、識別子が違うか
- ないパスで FileNotFoundError、アクセスを拒まれるパスで PermissionError になるか
- os.stat() の識別子と、形がどう違うか

使い方: python file_id_probe.py <作業用のディレクトリ>
"""
import ctypes
import os
import shutil
import subprocess
import sys
from ctypes import wintypes
from pathlib import Path

FILE_READ_ATTRIBUTES = 0x80
FILE_SHARE_ALL = 0x1 | 0x2 | 0x4
OPEN_EXISTING = 3
FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
FILE_ID_INFO_CLASS = 18  # FileIdInfo
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value


class FILE_ID_INFO(ctypes.Structure):
    _fields_ = [("VolumeSerialNumber", ctypes.c_ulonglong), ("FileId", ctypes.c_ubyte * 16)]


def load():
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
                                     wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel32.CreateFileW.restype = wintypes.HANDLE
    kernel32.GetFileInformationByHandleEx.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel32.GetFileInformationByHandleEx.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    return kernel32


def win_error(path):
    code = ctypes.get_last_error()
    # OSError の第 4 引数に Windows のエラーの番号を渡すと、FileNotFoundError や PermissionError に分かれる。
    return OSError(None, ctypes.FormatError(code).strip(), path, code)


def file_id(kernel32, path):
    """(VolumeSerialNumber, FileId) を返す。どの失敗も OSError で送出する。リンクの先をたどる。"""
    handle = kernel32.CreateFileW(path, FILE_READ_ATTRIBUTES, FILE_SHARE_ALL, None, OPEN_EXISTING,
                                  FILE_FLAG_BACKUP_SEMANTICS, None)
    if handle in (None, INVALID_HANDLE_VALUE):
        raise win_error(path)
    try:
        info = FILE_ID_INFO()
        if not kernel32.GetFileInformationByHandleEx(handle, FILE_ID_INFO_CLASS, ctypes.byref(info), ctypes.sizeof(info)):
            raise win_error(path)
        return info.VolumeSerialNumber, bytes(info.FileId)
    finally:
        if not kernel32.CloseHandle(handle):
            raise win_error(path)


def main(work):
    if os.name != "nt":
        print("  飛ばした（Windows だけ）")
        return True
    kernel32 = load()
    base = Path(work) / "fileid"
    if base.exists():
        for p in (base / "wiki" / "sub" / "loop", base / "wiki" / "j"):
            try:
                os.rmdir(p)
            except OSError:
                pass
        shutil.rmtree(base)
    (base / "wiki" / "sub").mkdir(parents=True)
    (base / "ext").mkdir()
    for name, target in (("wiki/sub/loop", "wiki"), ("wiki/j", "ext")):
        done = subprocess.run(["cmd", "/c", "mklink", "/J", str(base / name), str(base / target)], capture_output=True)
        assert done.returncode == 0, name
    ok = True

    def show(label, value, expected):
        nonlocal ok
        good = value == expected
        ok = ok and good
        print(f"  {label}: {value}、期待どおり: {good}")

    wiki = file_id(kernel32, str(base / "wiki"))
    loop = file_id(kernel32, str(base / "wiki" / "sub" / "loop"))
    sub = file_id(kernel32, str(base / "wiki" / "sub"))
    ext = file_id(kernel32, str(base / "ext"))
    j = file_id(kernel32, str(base / "wiki" / "j"))
    show("wiki と sub/loop（wiki を指すジャンクション）が同じ", wiki == loop, True)
    show("ext と j（ext を指すジャンクション）が同じ", ext == j, True)
    show("wiki と sub が違う", wiki != sub, True)
    for label, path, kind in (("ないパス", str(base / "none"), FileNotFoundError),
                              ("アクセスを拒まれるパス", "C:/System Volume Information", PermissionError)):
        try:
            file_id(kernel32, path)
            show(label, "成功した", kind.__name__)
        except OSError as exc:
            show(label, type(exc).__name__, kind.__name__)
    st = os.stat(base / "wiki")
    print(f"  参考: os.stat の st_dev {st.st_dev:#x}、FileIdInfo の VolumeSerialNumber {wiki[0]:#x}、"
          f"低い 32 ビットが同じ: {(st.st_dev & 0xFFFFFFFF) == (wiki[0] & 0xFFFFFFFF)}")
    for p in (base / "wiki" / "sub" / "loop", base / "wiki" / "j"):
        os.rmdir(p)
    shutil.rmtree(base)
    return ok


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    print(f"python {sys.version.split()[0]} {sys.platform}  file_id")
    done = main(sys.argv[1])
    print("  終了:", "よい" if done else "だめ")
    sys.exit(0 if done else 1)
