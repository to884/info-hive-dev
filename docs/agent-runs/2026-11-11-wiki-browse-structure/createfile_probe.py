"""CreateFileW に FILE_FLAG_OPEN_REPARSE_POINT を付けて作る・開くと、最後の名前のリンクをたどらないかを確かめる。
あわせて、mkdir、os.rename、os.replace が、先のないリンクの名前でどう振る舞うかを確かめる。"""
import ctypes
import msvcrt
import os
import sys
import tempfile
from ctypes import wintypes

print("Python", sys.version.split()[0], sys.platform)
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.CreateFileW.restype = wintypes.HANDLE
k32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
                            wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
GENERIC_READ, GENERIC_WRITE = 0x80000000, 0x40000000
SHARE = 0x1 | 0x2 | 0x4
CREATE_NEW, OPEN_ALWAYS = 1, 4
FILE_ATTRIBUTE_NORMAL, OPEN_REPARSE = 0x80, 0x00200000
INVALID = wintypes.HANDLE(-1).value


class BHFI(ctypes.Structure):
    _fields_ = [("attrs", wintypes.DWORD), ("c", wintypes.FILETIME), ("a", wintypes.FILETIME),
                ("w", wintypes.FILETIME), ("vol", wintypes.DWORD), ("sh", wintypes.DWORD),
                ("sl", wintypes.DWORD), ("links", wintypes.DWORD), ("ih", wintypes.DWORD), ("il", wintypes.DWORD)]


k32.GetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.POINTER(BHFI)]


def create(path, disposition):
    h = k32.CreateFileW(path, GENERIC_READ | GENERIC_WRITE, SHARE, None, disposition,
                        FILE_ATTRIBUTE_NORMAL | OPEN_REPARSE, None)
    if h == INVALID:
        raise ctypes.WinError(ctypes.get_last_error())
    info = BHFI()
    if not k32.GetFileInformationByHandle(h, ctypes.byref(info)):
        err = ctypes.WinError(ctypes.get_last_error())
        k32.CloseHandle(h)
        raise err
    return msvcrt.open_osfhandle(h, os.O_RDWR), info.attrs


def show(label, fn):
    try:
        print(label, fn())
    except OSError as e:
        print(label, "失敗", type(e).__name__, getattr(e, "winerror", None))


with tempfile.TemporaryDirectory() as tmp:
    wiki = os.path.join(tmp, "wiki")
    work = os.path.join(tmp, "work")
    os.makedirs(wiki)
    os.makedirs(work)
    target = os.path.join(wiki, "created.md")
    link = os.path.join(work, "build.lock")
    os.symlink(target, link)

    def open_always_link():
        fd, attrs = create(link, OPEN_ALWAYS)
        os.close(fd)
        return f"開けた。属性 {hex(attrs)}（再解析点 {bool(attrs & 0x400)}）、先ができたか {os.path.exists(target)}"
    show("OPEN_ALWAYS（先のないリンク）:", open_always_link)
    show("CREATE_NEW（先のないリンク）:", lambda: (os.close(create(link, CREATE_NEW)[0]), os.path.exists(target)))

    regular = os.path.join(work, "real.lock")

    def open_always_new():
        fd, attrs = create(regular, OPEN_ALWAYS)
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        os.close(fd)
        return f"作れた。ロックも取れた。属性 {hex(attrs)}"
    show("OPEN_ALWAYS（ない名前）:", open_always_new)
    show("OPEN_ALWAYS（今ある通常のファイル）:", lambda: (os.close(create(regular, OPEN_ALWAYS)[0]), "開けた")[1])
    show("CREATE_NEW（今ある通常のファイル）:", lambda: create(regular, CREATE_NEW))

    # mkdir、rename、replace と、先のないリンクの名前
    dlink = os.path.join(work, "tmp-9")
    os.symlink(os.path.join(wiki, "newdir"), dlink, target_is_directory=True)
    show("mkdir（先のないディレクトリのリンクの名前）:", lambda: (os.mkdir(dlink), os.path.exists(os.path.join(wiki, "newdir"))))
    src = os.path.join(work, "src")
    os.makedirs(src)
    show("rename（先が先のないリンク）:", lambda: (os.rename(src, link), os.path.exists(target)))
    fsrc = os.path.join(work, "f.new")
    open(fsrc, "wb").close()
    show("replace（先が先のないリンク）:", lambda: (os.replace(fsrc, link), os.path.islink(link), os.path.exists(target)))
