"""browse の読む側（走査、入力の読み取り、解釈）に、呼び出しの N 回目に手を入れる探索（設計の 9.2、9.3）。

書く側の探索（browse_sweep.py）は、描き終えたファイルの表を層に渡すので、走査と中核を通らない（実装の 1 回目の
レビューの重大 4）。ここでは、書き出しの全体（wiki_browse.build）を試験のプロセスの中で流し、次の口を 1 つの
数え方で数えて、N 回目に手を入れる。

- 層の口（wiki_browse_fs.X）。browse_sweep.Injector と同じ。
- 走査の計画の関数（wiki_pages.walk_markdown）が呼ぶ口: os.scandir（開く、項目を 1 つ取り出す）、項目の
  is_symlink、is_dir、is_junction、os.stat、wiki_pages.win_file_id。wiki_pages は、呼ぶたびに os から引くので、
  差し替えられる（設計の 3.4）。閉じる操作には手を入れない（設計の 3.1）。
- 解釈の入口（設計の 9.3 の「解釈」）: Markdown の解析（パーサーの parse）、frontmatter の解釈
  （wiki_lint.parse_frontmatter_raw）、1 ページの描画（Core.render_page）。

役目と、許す結果（試験の側が、手を入れない実行の記録から決める。設計の 9.2）:

| 手を入れた呼び出しの対象 | 許す結果 |
| --- | --- |
| 入力の名前の集合（走査の口） | 「分からない」なら、0 でなく、書き出し先は前のまま。「ない」なら、それに加えて、0 で新しい世代（やり直しで読み直す） |
| 入力の中身の読み取り（ある入力 X） | 0 で、X を読めないときの世代（手を入れずに X だけを読めなくして得た世代）と同じ。読み取りの印の警告がある |
| 画面の部品、Wiki のルートの識別子 | 0 でなく、書き出し先は前のまま |
| 公開の前の検査（入力の実体の場所、記録のトークン） | 0 で新しい世代。新しい警告がある |
| 解釈の入口 | 0 で、書き出し先に一覧と index.html がある（部分の失敗は全体を止めない） |
| 書き込み（書き出しの手順） | browse_sweep.py の基準。ここでは、0 なら新しい世代、0 でなければ前のままか、退避の世代が残る |

使い方:
    python -X utf8 tests/wiki/browse_read_sweep.py [--quick]
"""
from __future__ import annotations

import contextlib
import io
import os
import stat
import sys
import time
import types
from collections import Counter
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[1] / "info-hive-wiki" / "skills" / "info-hive" / "scripts"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(SCRIPTS))
sys.dont_write_bytecode = True

import browse_sandbox as bs  # noqa: E402
import browse_sweep as sweep  # noqa: E402
import wiki_browse  # noqa: E402
import wiki_browse_fs as fs  # noqa: E402
import wiki_lint  # noqa: E402
import wiki_pages  # noqa: E402

wiki_browse._load()
core = wiki_browse.core

WIKI = {
    "SCHEMA.md": b"# schema\n",
    "index.md": b"# index\n\n- [[a]]\n- [[indexes/more]]\n",
    "indexes/more.md": b"# more\n\n- [[b]]\n",
    "concepts/a.md": b"---\ntitle: a\ntype: concept\n---\n# a\n\nsee [[b]] and [[c#h]].\n",
    "concepts/b.md": b"---\ntitle: b\n---\n# b\n\nback to [[a]]. [[missing]]\n",
    "concepts/c.md": b"# c\n\n## h\n",
    "graph/ontology.yaml": b"node_types: {concept: {}}\npredicates: {}\n",
    "raw/x.md": b"not an input\n",
}
WALK_CALLS = ("w_scandir_open", "w_next", "w_is_symlink", "w_is_dir", "w_is_junction", "w_stat", "w_file_id")
PARSE_CALLS = ("i_parse", "i_frontmatter", "i_render_page")
MODES = ("denied", "absent", "zero", "blk", "raise")


class Crash(BaseException):
    pass


class ReadInjector(sweep.Injector):
    """層の口に加えて、走査の口と解釈の入口も、同じ数え方で数える。"""

    def outer(self, name, target, real, *args, **kwargs):
        early = self._before_outer(name, target)
        if early is not None:
            return early
        return real(*args, **kwargs)

    def _before_outer(self, name, target):
        if self.crashed:
            raise Crash()
        self.count += 1
        self.names.append(name)
        self.targets.append(target)
        self.calls.append((name, (target,)))
        if self.count != self.at:
            return None
        self.hit = name
        if name in PARSE_CALLS:
            if self.mode == "raise":
                raise ValueError("injected")
            return None
        if self.mode == "denied":
            raise PermissionError(13, "injected")
        if self.mode == "absent":
            raise FileNotFoundError(2, "injected")
        return None


class _Entry:
    def __init__(self, entry, inj):
        self._e, self._inj = entry, inj
        self.name, self.path = entry.name, entry.path

    def is_symlink(self):
        return self._inj.outer("w_is_symlink", self.path, self._e.is_symlink)

    def is_dir(self, *, follow_symlinks=True):
        return self._inj.outer("w_is_dir", self.path, self._e.is_dir, follow_symlinks=follow_symlinks)

    def is_junction(self):
        return self._inj.outer("w_is_junction", self.path, self._e.is_junction)

    def stat(self, *, follow_symlinks=True):
        return self._e.stat(follow_symlinks=follow_symlinks)


class _Scandir:
    def __init__(self, it, inj, path):
        self._it, self._inj, self._path = it, inj, path

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self._it.close()
        return False

    def __iter__(self):
        return self

    def __next__(self):
        def take():
            return next(self._it)
        return _Entry(self._inj.outer("w_next", self._path, take), self._inj)

    def close(self):
        self._it.close()


@contextlib.contextmanager
def instrumented(inj):
    """走査の口と解釈の入口を、inj の数え方に乗せる。層の口は fs.X で差し替える。"""
    real_scandir, real_stat, real_id = os.scandir, os.stat, wiki_pages.win_file_id
    real_parser, real_fm, real_render = wiki_pages.new_parser, wiki_lint.parse_frontmatter_raw, core.Core.render_page
    in_layer = {"on": False}

    def scandir(path="."):
        if in_layer["on"]:
            return real_scandir(path)
        it = inj.outer("w_scandir_open", os.fspath(path), real_scandir, path)
        return _Scandir(it, inj, os.fspath(path))

    def stat_(path, *a, **k):
        if in_layer["on"]:
            return real_stat(path, *a, **k)
        if inj.count + 1 == inj.at and inj.mode == "blk" and not inj.crashed:
            inj._before_outer("w_stat", os.fspath(path))
            return types.SimpleNamespace(st_mode=stat.S_IFBLK | 0o666, st_file_attributes=0, st_ino=0, st_dev=0,
                                         st_size=0, st_mtime_ns=0)
        return inj.outer("w_stat", os.fspath(path), real_stat, path, *a, **k)

    def file_id(path):
        if in_layer["on"]:
            return real_id(path)       # 層の file_id の口の中（層の口として数えてある）
        if inj.count + 1 == inj.at and inj.mode == "zero" and not inj.crashed:
            value = real_id(path)
            inj._before_outer("w_file_id", os.fspath(path))
            return value[0], bytes(16)
        return inj.outer("w_file_id", os.fspath(path), real_id, path)

    def new_parser():
        parser = real_parser()
        original = parser.parse

        def parse(text, env=None):
            return inj.outer("i_parse", None, original, text, env)
        parser.parse = parse
        return parser

    def frontmatter(text):
        return inj.outer("i_frontmatter", None, real_fm, text)

    def render_page(self_, pid, raw_mode="text", stale=None):
        return inj.outer("i_render_page", pid, real_render, self_, pid, raw_mode, stale)

    class Layer(type(inj)):
        pass

    # 層の口が呼ぶ os.stat や os.scandir は、層の口として数えるので、走査の口として数え直さない
    def layered(name):
        real = getattr(type(inj), name)

        def call(self_, *args):
            in_layer["on"] = True
            try:
                return real(self_, *args)
            finally:
                in_layer["on"] = False
        return call
    for name in sweep.CALLS:
        setattr(Layer, name, layered(name))
    inj.__class__ = Layer
    with mock.patch.object(os, "scandir", scandir), mock.patch.object(os, "stat", stat_), \
            mock.patch.object(wiki_pages, "win_file_id", file_id), \
            mock.patch.object(wiki_pages, "new_parser", new_parser), \
            mock.patch.object(wiki_lint, "parse_frontmatter_raw", frontmatter), \
            mock.patch.object(core.Core, "render_page", render_page):
        yield


def make(out_state):
    sb = bs.Sandbox("absent", "asis", False, key="KEY", wiki_files=WIKI)
    if out_state == "prev":
        # 前の世代を、少し違う Wiki から作っておく
        run(sb, sweep.Injector())
        bs.write(os.path.join(sb.wiki, "concepts", "c.md"), b"# c\n\n## h\n\nchanged.\n")
    return sb


def run(sb, inj, unreadable=None):
    """書き出しの全体を流す。終了コード（0、"stop"、"unknown"、"failed"、"crash"）と警告を返す。"""
    saved = fs.X
    fs.X = inj
    fs.WARNINGS.clear()
    err = io.StringIO()
    try:
        # 生成日時を固定する（比べる世代どうしで、manifest.js の生成日時だけが違わないように）
        with mock.patch.dict(os.environ, {"INFO_HIVE_DATA_DIR": sb.data}), contextlib.redirect_stderr(err), \
                contextlib.redirect_stdout(io.StringIO()), \
                mock.patch.object(wiki_browse.time, "strftime", lambda *a, **k: "2026-01-01T00:00:00+0900"):
            ctx = instrumented(inj) if isinstance(inj, ReadInjector) else contextlib.nullcontext()
            with ctx, (_unreadable(sb, unreadable) if unreadable else contextlib.nullcontext()):
                wiki_browse.build(Path(sb.wiki), sb.out, None)
        return 0, err.getvalue()
    except fs.Stop:
        return "stop", err.getvalue()
    except (fs.Unknown, fs.Absent, core.InputsUnknown):
        return "unknown", err.getvalue()
    except wiki_browse.Failed:
        return "failed", err.getvalue()
    except Crash:
        return "crash", err.getvalue()
    finally:
        fs.X = saved


def _unreadable(sb, rel):
    real = fs.read_input

    def read(root, r):
        if r == rel:
            raise fs.failure(fs.Unknown, "open_read: PermissionError", r)
        return real(root, r)
    return mock.patch.object(fs, "read_input", read)


def gen(sb):
    return bs.content(bs.tree(sb.out), manifest=False)


def role(name, target, sb, assets):
    if name in WALK_CALLS:
        return "walk"
    if name in PARSE_CALLS:
        return "parse"
    if not isinstance(target, str):
        return "other"
    if target and target.startswith(sb.wiki + os.sep) and name in ("open_read", "read", "close", "stat"):
        rel = os.path.relpath(target, sb.wiki).replace(os.sep, "/")
        return "read:" + rel
    if target and any(target == a or target.startswith(a + os.sep) for a in assets):
        return "assets"
    return "other"


def sweep_read(out_state, modes, only_roles=None):
    """1 つの初期の状態で、読む側の探索を流す。(実行の数, 破れた決まり) を返す。"""
    problems, runs = [], 0
    sb = make(out_state)
    try:
        probe = ReadInjector()
        rc, _err = run(sb, probe)
        assert rc == 0, rc
        expected_new = gen(sb)
        calls = list(zip(probe.names, probe.targets))
    finally:
        sb.close()
    assets = [core.ASSET_DIR]
    # 入力ごとに、その入力を読めないときの世代を、手を入れずに作る
    unreadable_gen = {}
    for name, target in calls:
        r = role(name, target, sb, assets)
        if r.startswith("read:") and r[5:] not in unreadable_gen:
            s2 = make(out_state)
            try:
                rc, _e = run(s2, sweep.Injector(), unreadable=r[5:])
                unreadable_gen[r[5:]] = gen(s2) if rc == 0 else ("rc", rc)
            finally:
                s2.close()
    for mode in modes:
        for at, (name, target) in enumerate(calls, 1):
            r = role(name, target, sb, assets)
            if only_roles and not any(r.startswith(x) for x in only_roles):
                continue
            if mode == "raise" and r != "parse":
                continue
            if name in ("close", "unlock"):
                continue      # 読み終えたファイルとロックの close と、ロックの解放は、基準の外（設計の 9.2）
            if mode != "raise" and r == "parse":
                continue
            if mode == "zero" and name not in ("w_file_id", "file_id"):
                continue
            if mode == "blk" and (not fs.NT or name not in ("w_stat", "lstat", "stat")):
                continue
            s3 = make(out_state)
            try:
                before_world, before_out = bs.world(s3), bs.tree(s3.out)
                inj = ReadInjector(at, mode)
                rc, err = run(s3, inj)
                runs += 1
                after = gen(s3)
                label = f"（{out_state}、{mode}@{at}、{inj.hit}、{r}、rc={rc}）"
                if not bs.world_same(s3, before_world, bs.world(s3), injected=True):
                    problems.append("書き出し先と領分の外が変わった" + label)
                unknown = mode in ("denied", "zero", "blk")
                if r == "walk":
                    if unknown and rc == 0:
                        problems.append("名前の集合が分からないのに、新しい世代を採った" + label)
                    if rc == 0 and after != expected_new:
                        problems.append("名前の集合の失敗のあとに、欠けた世代を採った" + label)
                    if rc != 0 and bs.tree(s3.out) != before_out:
                        problems.append("名前の集合の失敗で、書き出し先が変わった" + label)
                elif r.startswith("read:") and name in ("open_read", "read"):
                    want = unreadable_gen.get(r[5:])
                    if rc != 0:
                        problems.append("入力の中身を読めないだけで、書き出しが失敗した" + label)
                    elif after != want:
                        problems.append("入力の中身を読めないときの世代が、その入力を読めない Wiki の世代と違う" + label)
                    elif "読めない" not in err:
                        problems.append("入力の中身を読めないのに、読み取りの印の警告がない" + label)
                elif r == "assets":
                    if rc == 0:
                        problems.append("画面の部品を読めないのに、0 で終わった" + label)
                    if bs.tree(s3.out) != before_out:
                        problems.append("画面の部品を読めないのに、書き出し先が変わった" + label)
                elif r == "parse":
                    t = bs.tree(s3.out) or {}
                    if rc != 0 or "index.html" not in t or bs.MANIFEST not in t:
                        problems.append("1 つの入力の解釈の失敗で、書き出しの全体が止まった" + label)
                else:
                    if rc == 0 and after != expected_new:
                        problems.append("0 で終わったのに、新しい世代でない" + label)
                    if rc == 0 and unknown and inj.hit not in ("close", "unlock") and "警告" not in err \
                            and inj.hit not in ("stdout_write",):
                        pass   # 書き込みの役目の判定は browse_sweep.py が受け持つ
            finally:
                s3.close()
    return runs, problems


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    quick = "--quick" in argv
    started = time.time()
    total = []
    print(f"Python {sys.version.split()[0]}、{sys.platform}")
    print("\n| 書き出し先の状態 | 実行 | 破れた決まり |\n| --- | --- | --- |")
    for out_state in ("absent",) if quick else ("absent", "prev"):
        runs, problems = sweep_read(out_state, ("denied", "raise") if quick else MODES,
                                    only_roles=("walk", "read:", "assets", "parse") if quick else None)
        total += problems
        print(f"| {out_state} | {runs} | {len(problems)} |", flush=True)
    # 対照: 層の中で、一覧の失敗を空にする（走査の知らせを捨てる）。読めない入力の中身を空にして使う
    print("\n## 対照\n\n| 対照 | 見つけた件数 | 最初の 1 件 |\n| --- | --- | --- |")
    for mutant in ("drop_unlistable",):
        fs.MUTANTS.add(mutant)
        try:
            _runs, found = sweep_read("absent", ("denied",), only_roles=("walk",))
        finally:
            fs.MUTANTS.discard(mutant)
        print(f"| {mutant} | {len(found)} | {found[0] if found else '見つからなかった'} |")
        if not found:
            total.append(f"対照 {mutant} が見つからなかった")
    real_snapshot = core.take_snapshot

    def empty_on_failure(root, entries=None):
        real = fs.read_input

        def read(r, rel):
            try:
                return real(r, rel)
            except (fs.Unknown, fs.Absent):
                return b""
        with mock.patch.object(fs, "read_input", read):
            return real_snapshot(root, entries)
    with mock.patch.object(core, "take_snapshot", empty_on_failure):
        _runs, found = sweep_read("absent", ("denied",), only_roles=("read:",))
    print(f"| read_empty_on_failure | {len(found)} | {found[0] if found else '見つからなかった'} |")
    if not found:
        total.append("対照 read_empty_on_failure が見つからなかった")
    if total:
        print(f"\n## 破れた決まり（{len(total)} 件。先頭 30 件）\n")
        for p in list(dict.fromkeys(total))[:30]:
            print("- " + p)
    print(f"\n{time.time() - started:.0f} 秒")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
