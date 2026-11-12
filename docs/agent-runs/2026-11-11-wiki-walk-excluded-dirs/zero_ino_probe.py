"""os.stat が成功し、識別子（st_ino）が 0 で返る場合を確かめる（Windows だけ）。

Windows の os.stat は、ファイルを開けないとき（アクセス拒否、共有違反など）に、ディレクトリの一覧の情報で
「成功」を返す（CPython の win32_xstat_impl の attributes_from_dir）。そのとき st_ino は 0 である。
試作が、識別子を取る役割では「分からない」として unknown に入れて降りないこと、.md がファイルかどうかを
調べる役割では、ファイルとして返すこと（今の実装と同じ）を見る。

使い方: python zero_ino_probe.py <作業用のディレクトリ> [v3|v4]   （既定は v4。walk_v4.py を読み込む）
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if len(sys.argv) > 2 and sys.argv[2] == "v3":
    import walk_v3 as v3  # noqa: E402
else:
    import walk_v4 as v3  # noqa: E402 名前は v3 のまま使う


def with_zero_ino(wiki, zero_rel, function):
    """wiki の下の zero_rel への os.stat だけ、st_ino と st_dev を 0 にして返す。"""
    real = os.stat
    target = os.path.join(str(wiki), *zero_rel.split("/")) if zero_rel != "." else str(wiki)

    def fake(path, *args, **kwargs):
        st = real(path, *args, **kwargs)
        if os.fspath(path) == target:
            return os.stat_result((st.st_mode, 0, 0, st.st_nlink, st.st_uid, st.st_gid, st.st_size,
                                   st.st_atime, st.st_mtime, st.st_ctime))
        return st
    os.stat = fake
    try:
        return function(wiki)
    finally:
        os.stat = real


def ordered(first, function):
    """wiki の直下の一覧で、first という名前の項目を先に返すようにして、function を呼ぶ。"""
    real = os.scandir

    def fake(path):
        class Listing:
            def __enter__(self):
                self.it = real(path)
                entries = list(self.it.__enter__())
                entries.sort(key=lambda e: e.name != first)
                return iter(entries)

            def __exit__(self, *exc):
                return self.it.__exit__(*exc)
        return Listing()

    def run(wiki):
        os.scandir = fake
        try:
            return function(wiki)
        finally:
            os.scandir = real
    return run


def show(label, result, want_files, want_unknown):
    files = [f.rel for f in result.files]
    good = files == want_files and result.unknown == want_unknown and not result.unlistable
    print(f"  {label}: ページ {files}、unknown {result.unknown}、期待どおり: {good}")
    return good


def main(work):
    if os.name != "nt":
        print("  飛ばした（ジャンクションは Windows だけ）")
        return True
    ok = True
    base = Path(work) / "zero"
    v3.remove_tree(base)

    # 輪でないジャンクション junc -> ext。先の識別子が 0 なら、降りずに知らせる。
    spec = {"wiki": {"a.md": "a", "junc": ("junction", "ext")}, "ext": {"c.md": "c"}}
    v3.build(base / "t1", spec)
    wiki = base / "t1" / "wiki"
    ok &= show("失敗なし", v3.walk_pages(wiki), ["a.md", "junc/c.md"], [])
    ok &= show("ジャンクションの先の識別子が 0", with_zero_ino(wiki, "junc", v3.walk_pages), ["a.md"], ["junc"])
    ok &= show("起点（wiki）の識別子が 0", with_zero_ino(wiki, ".", v3.walk_pages), ["a.md"], ["junc"])

    # 循環 sub/loop -> wiki。道筋のディレクトリ（sub）の識別子が 0 なら、判定できないので、降りずに知らせる。
    spec = {"wiki": {"a.md": "a", "sub": {"b.md": "b", "loop": ("junction", "wiki")}}}
    v3.build(base / "t2", spec)
    wiki = base / "t2" / "wiki"
    ok &= show("循環、失敗なし", v3.walk_pages(wiki), ["a.md", "sub/b.md"], [])
    ok &= show("循環、道筋の sub の識別子が 0", with_zero_ino(wiki, "sub", v3.walk_pages), ["a.md", "sub/b.md"], ["sub/loop"])

    # ジャンクションのない wiki では、識別子が 0 でも、何も変わらない。
    spec = {"wiki": {"a.md": "a", "sub": {"b.md": "b"}}}
    v3.build(base / "t3", spec)
    wiki = base / "t3" / "wiki"
    ok &= show("ジャンクションなし、sub の識別子が 0", with_zero_ino(wiki, "sub", v3.walk_pages), ["a.md", "sub/b.md"], [])

    # ジャンクション j と、通常のディレクトリ plain が兄弟（3 回目のレビューの重大 1）。plain の識別子だけが 0。
    # plain への道筋はジャンクションを通らないので、どちらを先に列挙しても、plain/x.md は残り、知らせは出ない。
    spec = {"wiki": {"j": ("junction", "ext"), "plain": {"x.md": "x"}}, "ext": {"c.md": "c"}}
    v3.build(base / "t4", spec)
    wiki = base / "t4" / "wiki"
    for first in ("j", "plain"):
        run = ordered(first, lambda w: with_zero_ino(w, "plain", v3.walk_pages))
        ok &= show(f"兄弟、plain の識別子が 0、{first} を先に列挙", run(wiki), ["j/c.md", "plain/x.md"], [])

    # .md の項目への os.stat が、成功で識別子 0 を返す（Windows で開けないファイル）。ファイルとして返す（今と同じ）。
    spec = {"wiki": {"a.md": "a", "locked.md": "l"}}
    v3.build(base / "t5", spec)
    wiki = base / "t5" / "wiki"
    ok &= show(".md の項目の識別子が 0（開けないファイル）", with_zero_ino(wiki, "locked.md", v3.walk_pages),
               ["a.md", "locked.md"], [])
    v3.remove_tree(base)
    return ok


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    print(f"python {sys.version.split()[0]} {sys.platform}  zero_ino（{v3.__name__}）")
    done = main(sys.argv[1])
    print("  終了:", "よい" if done else "だめ")
    sys.exit(0 if done else 1)
