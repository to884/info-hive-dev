"""browse の構造の直し（docs/plans/wiki-browse-structure-2026-11-11.md）の試験の道具: 砂場と世界の差分。

設計の 9.1 と 9.4 にあたる。基準は browse の実装の出力からではなく、試験の側の表（木の作り）から決める。
ここの関数は browse のモジュールを読み込まない（実装に依らない）。砂場の作りは、設計の試作の探索
（docs/agent-runs/2026-11-11-wiki-browse-structure/write_sweep.py）から移した。

- Sandbox: 1 つの初期の状態（書き出し先、作業用のディレクトリ、データの場所）を、一時のディレクトリに作る。
- tree / world: 木を自分で読む。名前、種類、中身の SHA-256、属性（書き込めるか、更新時刻）。リンクはたどらない。
- world_same: 領分と、その実行に指した書き出し先の外が変わっていないか（設計の 9.1 の「世界の差分」）。
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import tempfile

WORK_MARKER = ".browse-work"
SERVER_MARKER = ".browse-server"
MANIFEST = ".browse-generation"
LEGACY = ("seq", "build-report.json")
LOCK_NAMES = ("build.lock", "server.lock")

FILES_P = {"index.html": b"<p>previous</p>", "concepts/a.html": b"<p>a v1</p>", "assets/app.js": b"// v1"}

OUT_STATES = ("absent", "empty", "gen", "gen+extra", "gen+edited", "userdir", "legacy", "gen+hardlink",
              "absent+old", "empty+old", "wikiroot", "insidewiki", "nodata")
WORK_STATES = ("asis", "leftovers", "junction", "unmarked-empty")
# 作業用のロックと目印の名前に、利用者が置いたリンク（6 回目の設計のレビューの重大 1）
LINK_STATES = ("lock-dangling", "lock-symlink", "lock-hardlink", "marker-symlink", "marker-owner-link")
LINK_OUT_STATES = ("absent", "gen")
FOREIGN = ("gen+extra", "gen+edited", "userdir", "legacy")
WHOLE = ("wikiroot", "insidewiki", "datainwiki")     # 砂場の全体が変わってはならない（Wiki のルートと重なる）
# <data_dir>/browse の名前がリンク（7 回目の設計のレビューの重大 1）。どの実行も、砂場を変えずに止まる
ROOT_LINK = ("browse-junction", "browse-symlink")
# <data_dir> そのものがジャンクション（利用者が指した場所への道）。その先の実の browse を領分として使う
DATA_LINK = ("gen+datajunction",)
# 作業用のディレクトリの名前そのものが、目印を持つ利用者のディレクトリへのジャンクション。使わずに止まる
WORK_LINK = "work-link"
# 書き出し先の名前そのものが、browse の世代を持つディレクトリへのリンク。作業用も作らずに止まる（設計の 6.4 の 1）
OUT_LINK = ("outlink-junction", "outlink-symlink")
# 作業用の old-N、tmp-N、del-N の名前そのものがリンク。old-N は、書き出し先に戻さない（設計の 6.4 の 3）
ENTRY_LINK = ("old-junction", "old-symlink", "left-links")


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def make_manifest(files, seq):
    """世代の一覧（設計の 6.3）。名前、ファイルの大きさと SHA-256、ディレクトリの名前、通し番号。"""
    entries = {name: {"size": len(data), "sha256": hashlib.sha256(data).hexdigest()} for name, data in files.items()}
    dirs = sorted({"/".join(name.split("/")[:i]) for name in files for i in range(1, name.count("/") + 1)})
    return json.dumps({"published_seq": seq, "files": entries, "dirs": dirs}, sort_keys=True).encode("utf-8")


def put_generation(directory, files, seq):
    os.makedirs(directory)
    write(os.path.join(directory, MANIFEST), make_manifest(files, seq))
    for name, data in files.items():
        write(os.path.join(directory, *name.split("/")), data)


def junction(link, target):
    if os.name == "nt":
        import _winapi
        _winapi.CreateJunction(target, link)
    else:
        os.symlink(target, link, target_is_directory=True)


def link_dir(kind_, link, target):
    if kind_ == "junction":
        junction(link, target)
    else:
        os.symlink(target, link, target_is_directory=True)


def is_link_stat(st) -> bool:
    return stat.S_ISLNK(st.st_mode) or bool(getattr(st, "st_file_attributes", 0) & 0x400)


def real_dir(path):
    """名前そのものが、実のディレクトリか（リンクとジャンクションは違う）。"""
    try:
        st = os.lstat(path)
    except FileNotFoundError:
        return False
    return stat.S_ISDIR(st.st_mode) and not is_link_stat(st)


def place_link(state, lock, marker, wiki, owner):
    """ロックか目印の名前に、Wiki の中を指すリンクを置く。作れなければ、理由を返す（その状態は飛ばし、合格にしない）。"""
    try:
        if state == "lock-dangling":
            os.symlink(os.path.join(wiki, "created.md"), lock)
        elif state == "lock-symlink":
            os.symlink(os.path.join(wiki, "concepts", "a.md"), lock)
        elif state == "lock-hardlink":
            os.link(os.path.join(wiki, "concepts", "a.md"), lock)
        elif state == "marker-symlink":
            os.symlink(os.path.join(wiki, "concepts", "a.md"), marker)
        elif state == "marker-owner-link":
            # リンクの先が、正しい持ち主の値を持つ。browse は、リンクの先を持ち主の証にしない（設計の 6.2）
            owner_file = os.path.join(os.path.dirname(wiki), "user", "owner.txt")
            write(owner_file, owner.encode("utf-8"))
            os.symlink(owner_file, marker)
    except OSError as e:
        return f"リンクを作れない: {type(e).__name__}"
    return None


WIKI_FILES = {
    "SCHEMA.md": b"# schema\n",
    "index.md": b"# index\n\n- [[a]]\n",
    "concepts/a.md": b"---\ntitle: a\n---\n# a\n\nsee [[b]].\n",
    "assets/app.js": b"wiki asset",
}


class Sandbox:
    """1 つの初期の状態を、一時のディレクトリに作る。

    key は既定の書き出し先の名前（<data_dir>/browse/<key>）、owner は作業用と状態のディレクトリの目印に書く
    持ち主の値である。どちらも、試験の側が決めて渡す（実装の試験では、実装の wiki_key と持ち主の値を渡す）。
    """

    def __init__(self, out_state, work_state, default, key="KEY", owner="A", wiki_files=None, initialized=True):
        self.out_state, self.work_state, self.default = out_state, work_state, default
        self.root = os.path.realpath(tempfile.mkdtemp(prefix="bw-", dir=os.environ.get("BW_TMP")))
        r = self.root
        for name, data in (wiki_files or WIKI_FILES).items():
            write(os.path.join(r, "wiki", *name.split("/")), data)
        write(os.path.join(r, "user", "keep.txt"), b"keep")
        write(os.path.join(r, "user", "assets", "app.js"), b"user asset")
        put_generation(os.path.join(r, "exports", "other"), FILES_P, 4)
        self.skipped = None
        # key と owner は、関数でも渡せる（Wiki のルートのパスを受け取る）。実装の wiki_key と持ち主の値を使うため
        planned = os.path.join(r, "emptywiki" if (not default and out_state == "wikiroot")
                               else "data" if (default and out_state == "datainwiki") else "wiki")
        os.makedirs(planned, exist_ok=True)
        key = key(planned) if callable(key) else key
        owner = owner(planned) if callable(owner) else owner
        self.key = key
        self.owner = owner
        self.data = self.data_real = os.path.join(r, "data")
        if out_state in ROOT_LINK:
            # <data_dir>/browse が、利用者のディレクトリへのリンク。その先に、browse の名前と同じ
            # ディレクトリと、利用者のファイルがある
            os.makedirs(self.data)
            elsewhere = os.path.join(r, "elsewhere")
            write(os.path.join(elsewhere, key, "private.txt"), b"keep me")
            write(os.path.join(elsewhere, key + ".browse-work", WORK_MARKER), owner.encode("utf-8"))
            write(os.path.join(elsewhere, key + ".server", SERVER_MARKER), owner.encode("utf-8"))
            write(os.path.join(elsewhere, key + ".server", "server.json"),
                  json.dumps({"instance": "x", "owner": owner}).encode("utf-8"))
            try:
                if out_state == "browse-junction":
                    junction(os.path.join(self.data, "browse"), elsewhere)
                else:
                    os.symlink(elsewhere, os.path.join(self.data, "browse"), target_is_directory=True)
            except OSError as e:
                self.skipped = f"リンクを作れない: {type(e).__name__}"
        elif out_state in DATA_LINK:
            self.data_real = os.path.join(r, "udata")
            os.makedirs(os.path.join(self.data_real, "browse"))
            try:
                junction(self.data, self.data_real)
            except OSError as e:
                self.skipped = f"リンクを作れない: {type(e).__name__}"
        elif out_state != "nodata":
            os.makedirs(os.path.join(r, "data", "browse"))
        self.wiki = os.path.join(r, "wiki")
        if default:
            self.out = os.path.join(r, "data", "browse", key)
        elif out_state == "wikiroot":
            os.makedirs(os.path.join(r, "emptywiki"), exist_ok=True)
            if initialized:
                # 入口は SCHEMA.md のないディレクトリを断る（ADR-0019）。コマンドで流すときだけ置く（置くと空でない）
                write(os.path.join(r, "emptywiki", "SCHEMA.md"), b"# schema\n")
            self.wiki = os.path.join(r, "emptywiki")
            self.out = self.wiki
        elif out_state == "insidewiki":
            self.out = os.path.join(r, "wiki", "site")
        else:
            self.out = os.path.join(r, "exports", "site")
        if default and out_state == "datainwiki":
            # data_dir が Wiki のルートの下にある
            self.wiki = os.path.join(r, "data")
            if initialized:
                write(os.path.join(self.wiki, "SCHEMA.md"), b"# schema\n")
        self.work = self.out + ".browse-work"
        self.state_dir = os.path.join(r, "data", "browse", key + ".server")
        out, work = self.out, self.work
        marker_text = owner.encode("utf-8") if default else b""
        if out_state in OUT_LINK:
            elsewhere = os.path.join(r, "elsewhere-out")
            put_generation(elsewhere, FILES_P, 3)
            try:
                link_dir("junction" if out_state == "outlink-junction" else "symlink", out, elsewhere)
            except OSError as e:
                self.skipped = f"リンクを作れない: {type(e).__name__}"
        elif out_state == "empty":
            os.makedirs(out)
        elif out_state.startswith("gen"):
            put_generation(out, FILES_P, 3)
            if out_state == "gen+extra":
                write(os.path.join(out, "notes.txt"), b"my notes")
            elif out_state == "gen+edited":
                write(os.path.join(out, "index.html"), b"<p>edited by hand</p>")
            elif out_state == "gen+hardlink":
                os.link(os.path.join(out, "index.html"), os.path.join(r, "wiki", "hl.md"))
                os.chmod(os.path.join(out, "index.html"), stat.S_IREAD)
        elif out_state == "userdir":
            write(os.path.join(out, "report.docx"), b"user file")
        elif out_state == "legacy":
            write(os.path.join(out, MANIFEST), b'{"generation": "x", "published_seq": 3}\n')
            write(os.path.join(out, "index.html"), b"<p>0.10.0</p>")
        elif out_state.endswith("+old"):
            if out_state == "empty+old":
                os.makedirs(out)
            os.makedirs(work)
            write(os.path.join(work, WORK_MARKER), marker_text)
            put_generation(os.path.join(work, "old-5"), FILES_P, 5)
        if work_state not in ("asis", WORK_LINK) and not os.path.isdir(work):
            os.makedirs(work)
            if work_state not in ("unmarked-empty", "marker-symlink", "marker-owner-link"):
                write(os.path.join(work, WORK_MARKER), marker_text)
        if work_state in LINK_STATES:
            self.skipped = place_link(work_state, os.path.join(work, "build.lock"), os.path.join(work, WORK_MARKER),
                                      os.path.join(r, "wiki"), owner if default else "")
        if work_state == "leftovers":
            write(os.path.join(work, "tmp-7", "index.html"), b"<p>half")
            write(os.path.join(work, "del-6", "concepts", "a.html"), b"<p>a v0</p>")
            write(os.path.join(work, "seq"), b"7\n")
            write(os.path.join(work, "build-report.json"), b"{}")
        elif work_state in ENTRY_LINK:
            elsewhere = os.path.join(r, "elsewhere-entry")
            try:
                if work_state == "left-links":
                    write(os.path.join(elsewhere, "tmp", "private.txt"), b"keep me")
                    write(os.path.join(elsewhere, "del", "private.txt"), b"keep me")
                    link_dir("symlink", os.path.join(work, "tmp-7"), os.path.join(elsewhere, "tmp"))
                    link_dir("junction", os.path.join(work, "del-6"), os.path.join(elsewhere, "del"))
                else:
                    put_generation(elsewhere, FILES_P, 5)
                    link_dir("junction" if work_state == "old-junction" else "symlink",
                             os.path.join(work, "old-5"), elsewhere)
            except OSError as e:
                self.skipped = f"リンクを作れない: {type(e).__name__}"
        elif work_state == WORK_LINK:
            write(os.path.join(r, "elsewhere-work", WORK_MARKER), marker_text)
            write(os.path.join(r, "elsewhere-work", "keep.txt"), b"keep")
            try:
                junction(work, os.path.join(r, "elsewhere-work"))
            except OSError as e:
                self.skipped = f"リンクを作れない: {type(e).__name__}"
        elif work_state == "junction":
            os.makedirs(os.path.join(work, "tmp-8"))
            try:
                junction(os.path.join(work, "tmp-8", "assets"), os.path.join(r, "user", "assets"))
                junction(os.path.join(work, "tmp-8", "wiki"), os.path.join(r, "wiki"))
            except OSError as e:
                self.skipped = f"リンクを作れない: {type(e).__name__}"

    @property
    def protected(self) -> bool:
        """browse の書き出しと確かめられない書き出し先、Wiki のルートと重なる書き出し先、名前そのものがリンクの
        書き出し先と領分。手を入れない実行は、止まり、何も変えない（設計の 9.1）。"""
        return ((self.out_state in FOREIGN and not self.default) or self.out_state in WHOLE
                or self.out_state in ROOT_LINK or self.work_state == WORK_LINK or self.out_state in OUT_LINK)

    def real(self, path):
        """名前を、砂場の中の実の場所に直す。<data_dir> がジャンクションなら、その先の名前にする（世界の差分は
        リンクをたどらずに木を読むので、領分は実の場所で数える）。"""
        if self.data_real != self.data and (path == self.data or path.startswith(self.data + os.sep)):
            return self.data_real + path[len(self.data):]
        return path

    def close(self):
        def onerror(func, path, exc):
            try:
                os.chmod(path, stat.S_IWRITE)
                func(path)
            except OSError:
                pass
        for dirpath, dirnames, _files in os.walk(self.root):
            for d in list(dirnames):
                full = os.path.join(dirpath, d)
                if os.path.islink(full) or (os.name == "nt" and os.lstat(full).st_file_attributes & 0x400):
                    os.rmdir(full) if os.name == "nt" else os.unlink(full)
                    dirnames.remove(d)
        shutil.rmtree(self.root, onerror=onerror)


def _attrs(st):
    return bool(st.st_mode & stat.S_IWRITE), st.st_mtime_ns


def tree(path):
    """木を自分で読む。{相対パス: (種類, ハッシュ, 書き込みできるか, 更新時刻)}。根そのものは "."。リンクはたどらない。"""
    if not os.path.lexists(path):
        return None
    found = {}

    def walk(directory, prefix):
        for name in sorted(os.listdir(directory)):
            full, rel = os.path.join(directory, name), prefix + name
            st = os.lstat(full)
            if is_link_stat(st):
                found[rel] = ("link", None, *_attrs(st))
            elif stat.S_ISDIR(st.st_mode):
                found[rel] = ("dir", None, *_attrs(st))
                walk(full, rel + "/")
            else:
                try:
                    with open(full, "rb") as f:
                        digest = hashlib.sha256(f.read()).hexdigest()
                except PermissionError:
                    # 取られているロックは読めない（Windows の範囲のロック）。browse のロックの名前のときだけ、中身を量らない
                    if name not in LOCK_NAMES:
                        raise
                    digest = "lock"
                found[rel] = ("file", digest, *_attrs(st))
    st = os.lstat(path)
    if stat.S_ISDIR(st.st_mode) and not is_link_stat(st):
        found["."] = ("dir", None, *_attrs(st))
        walk(path, "")
    else:
        found["."] = ("link" if is_link_stat(st) else "file", None, *_attrs(st))
    return found


def content(t, manifest=True):
    """種類とハッシュだけにする（世代どうしを比べる）。根は除く。

    一覧（.browse-generation）も含めて比べる（設計の 11。8 回目のレビューの C。一覧だけを失った退避の世代は、
    6.4 の 3 の決まりで戻せないので、残ったと数えない）。manifest が偽なら一覧を除く（新しい世代を、描くべき
    ファイルの表と比べるとき。一覧の中身は通し番号を持つので、表からは計算しない）。
    """
    if t is None:
        return None
    return {k: v[:2] for k, v in t.items() if k != "." and (manifest or k != MANIFEST)}


def expected(files):
    """描くべきファイルの表から計算した木（一覧を除く）。"""
    t = {name: ("file", hashlib.sha256(data).hexdigest()) for name, data in files.items()}
    for name in files:
        parts = name.split("/")
        for i in range(1, len(parts)):
            t["/".join(parts[:i])] = ("dir", None)
    return t


def rel(sb, path):
    return os.path.relpath(path, sb.root).replace(os.sep, "/")


def world(sb):
    """砂場の全体の木。"""
    return tree(sb.root)


def _parent(k):
    return k.rsplit("/", 1)[0] if "/" in k else "."


def world_same(sb, before, after, injected=False, extra_territory=()):
    """領分と、指した書き出し先の外が変わっていないか（設計の 9.1）。

    browse が新しく作るディレクトリと、名前を付け替えるディレクトリの親だけは、更新時刻の変化を許す（設計の 2.1）。
    新しく作ってよいのは、領分と書き出し先そのものと、その祖先（data_dir がないとき）だけである。
    Wiki のルートと重なる状態では、手を入れない実行は、砂場の全体が変わらない（止まり、何も変えない）。
    失敗を入れた実行（とそのあとの実行）は、Wiki のルートの下が、ルートそのものの属性を含めて変わらず、
    ほかは上の規則に従う（Wiki のルートの外にある領分は、作ってよい）。
    """
    if sb.out_state in ROOT_LINK or sb.work_state == WORK_LINK:
        return before == after          # 領分に入る確かめで、何も作らずに止まる（手を入れた実行も）
    if sb.out_state in OUT_LINK and not injected:
        return before == after          # 書き出し先の名前の確かめで、作業用も作らずに止まる（設計の 6.4 の 1）
    if sb.out_state in WHOLE:
        if not injected:
            return before == after
        top = rel(sb, sb.wiki)

        def under(k):
            return k == top or k.startswith(top + "/")
        if {k: v for k, v in before.items() if under(k)} != {k: v for k, v in after.items() if under(k)}:
            return False
    skip = [rel(sb, sb.real(p)) for p in (sb.out, sb.work, sb.state_dir, os.path.join(sb.data, "browse"),
                                          *extra_territory)]

    def inside(k):
        return any(k == p or k.startswith(p + "/") for p in skip)

    def ancestor_of_skip(k):
        return any(p.startswith(k + "/") for p in skip)

    allowed_mtime = {_parent(rel(sb, sb.real(sb.out)))}
    for k in after:
        if k not in before and (inside(k) or ancestor_of_skip(k)):
            allowed_mtime.add(_parent(k))
    for k in set(before) | set(after):
        if inside(k):
            continue
        if k not in before:
            if not ancestor_of_skip(k):
                return False
            continue
        if k not in after:
            return False
        a, b = before[k], after[k]
        if k in allowed_mtime:
            a, b = a[:3], b[:3]
        if a != b:
            return False
    return True


def world_diff(sb, before, after):
    """world_same が偽のとき、どこが変わったかを短く返す（知らせのため）。"""
    keys = sorted(set(before) | set(after))
    changed = [k for k in keys if before.get(k) != after.get(k)]
    return changed[:8]


def build_cases(quick=False):
    """書き出しの初期の状態の一覧（設計の 9.4）。(書き出し先の状態, 作業用の状態, 既定の書き出し先か)。"""
    out_states = ("absent", "gen", "gen+extra", "absent+old", "wikiroot") if quick else OUT_STATES
    work_states = ("asis", "leftovers") if quick else WORK_STATES
    cases = []
    for default in (False, True):
        for out_state in out_states:
            if default and out_state in ("wikiroot", "insidewiki"):
                continue
            for work_state in work_states:
                if out_state.endswith("+old") and work_state == "unmarked-empty":
                    continue
                if out_state in ("wikiroot", "insidewiki") and work_state != "asis":
                    continue
                cases.append((out_state, work_state, default))
            if not quick and out_state in LINK_OUT_STATES:
                cases += [(out_state, ls, default) for ls in LINK_STATES + (WORK_LINK,) + ENTRY_LINK]
        if not quick:
            cases += [(s, "asis", default) for s in OUT_LINK]
        if default:
            cases.append(("datainwiki", "asis", True))
            if not quick:
                cases += [(s, "asis", True) for s in ROOT_LINK]
                cases += [(s, w, True) for s in DATA_LINK for w in ("asis", "leftovers")]
        if not default:
            # --out の書き出しも領分の根に入る（設計の 11。8 回目のレビューの C）。根がリンクなら止まる
            if not quick:
                cases += [(s, "asis", False) for s in ROOT_LINK]
    return cases
