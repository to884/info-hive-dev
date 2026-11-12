"""読めないページが 1 つあると、今の中核（wiki 0.10.0）の出力のどこが変わるかを確かめる。製品の試験ではない。

設計の 9.2 の基準を決めるために使う。比べる写しは、次の 4 つである。
- N: すべて読める。
- U: 対象のページだけ読めない（写しの中で、中身を捨てて error="os" にする。OS の読み取りの失敗と同じ形）。
- R: 対象のページを木から取り除いた（そのページがない Wiki）。基準の側の答えである。
- E: 対象のページの中身を空にした（代わりの値を入れる実装の対照）。

確かめること:
- U の未解決リンクが、同じ失敗を入れた lint の broken_links と同じ（4 回目の設計の基準）。
- U のリンクの解決（解決、曖昧、未解決と、行き先）、被リンク、未解決リンク、ページの HTML が、R と同じ。
  違ってよいのは、読み取りの印（診断と、索引の件数の表示）だけ（5 版目の基準）。
- E は R と違う（対照が基準で見つかる）。

使い方: python unreadable_probe.py
"""
from __future__ import annotations

import copy
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[3] / "info-hive-wiki" / "skills" / "info-hive" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import wiki_browse_core as core  # noqa: E402

WIKIS = {
    # 読めないページへのリンクが、未解決に変わる例
    "concepts/a.md": {
        "index.md": "# 索引\n\n## コンセプト\n\n- [[a]] — A の要約\n- [[b]] — B の要約\n- [[c]] — C の要約\n",
        "concepts/a.md": "---\ntitle: エー\ntype: concept\nsources: [missing-source]\ntags: [x]\n---\n# A\n\n[[b]] と [[missing]] と [[c#見出し]]\n",
        "concepts/b.md": "---\ntitle: ビー\ntype: concept\n---\n# B\n\n[[a]] を見る\n",
        "concepts/c.md": "---\ntitle: シー\ntype: concept\n---\n# C\n\n## 見出し\n\n本文\n",
    },
    # 曖昧だったリンクが、解決に変わる例（4 回目の設計のレビューの重大 5）
    "two/x.md": {
        "index.md": "# 索引\n",
        "one/x.md": "# X1\n",
        "two/x.md": "# X2\n",
        "b.md": "# B\n\n[[x]]\n",
    },
}


def build_wiki(root: Path, pages: dict) -> None:
    for rel, text in pages.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def variant(snap, target, mode):
    s = copy.copy(snap)
    s.inputs = []
    for f in snap.inputs:
        g = copy.copy(f)
        if g.disk_rel == target:
            if mode == "R":
                continue
            if mode == "U":
                g.text, g.sha, g.error = None, None, "os"
            elif mode == "E":
                g.text = ""
        s.inputs.append(g)
    if mode == "U":
        s.unreadable = True
    return s


def resolution(c):
    return {pid: [(r["target"], r["state"], r.get("id"), tuple(r.get("candidates", ()))) for r in rs]
            for pid, rs in sorted(c.links.items())}


def lint_broken(pages: dict, fail: "str | None") -> list:
    """lint を実物で呼ぶ。fail のページの読み取りを PermissionError にする。"""
    import wiki_lint
    real = Path.read_text

    def read_text(self, *args, **kwargs):
        if fail and self.as_posix().endswith("/" + fail):
            raise PermissionError(13, "injected")
        return real(self, *args, **kwargs)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "wiki"
        build_wiki(root, pages)
        Path.read_text = read_text
        try:
            collected = wiki_lint.collect_pages(root)
        finally:
            Path.read_text = real
        findings = wiki_lint.lint(collected, 10000, 25000, [], False, 3)
        return sorted((f["from_path"], f["to"]) for f in findings["broken_links"])


def main():
    print(f"Python {sys.version.split()[0]}、{sys.platform}")
    for target, pages in WIKIS.items():
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "wiki"
            build_wiki(root, pages)
            snap = core.take_snapshot(root)
            cores, files = {}, {}
            for mode in ("N", "U", "R", "E"):
                c = core.Core(variant(snap, target, mode))
                files[mode] = c.render_all("text", "2026-11-11T00:00:00+0900")
                cores[mode] = c
        print(f"\n## `{target}` を読めなくする\n")
        print("| | N（すべて読める） | U（読めない） | R（取り除いた木） | E（空にした。対照） |")
        print("| --- | --- | --- | --- | --- |")
        print("| 描くページ | " + " | ".join(str(sorted(cores[m].drawn)) for m in "NURE") + " |")
        print("| 未解決リンク | " + " | ".join(str(cores[m].unresolved()) for m in "NURE") + " |")
        print("| リンクの解決 | " + " | ".join(str(resolution(cores[m])) for m in "NURE") + " |")
        print("| 被リンク | " + " | ".join(str({k: v for k, v in sorted(cores[m].backlinks.items()) if v}) for m in "NURE") + " |")
        print()
        print(f"- lint の broken_links（読めなくしたとき）: {lint_broken(pages, target)}")
        for mode in ("U", "E"):
            same = (resolution(cores[mode]) == resolution(cores["R"]),
                    cores[mode].backlinks == cores["R"].backlinks,
                    cores[mode].unresolved() == cores["R"].unresolved())
            differing = sorted(n for n in set(files[mode]) | set(files["R"]) if files[mode].get(n) != files["R"].get(n))
            print(f"- {mode} と R: リンクの解決が同じ {same[0]}、被リンクが同じ {same[1]}、未解決リンクが同じ {same[2]}。"
                  f"中身が違う出力のファイル {differing}")


if __name__ == "__main__":
    main()
