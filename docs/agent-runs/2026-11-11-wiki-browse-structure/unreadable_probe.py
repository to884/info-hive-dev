"""読めないページが 1 つあると、今の中核（wiki 0.10.0）の出力のどこが変わるかを数える。製品の試験ではない。

3 回目の設計のレビューの重大 5 は、「1 つの入力の中身の欠けは、その入力の表示にしか響かない」という前提が
崩れると指摘した。設計の 8.2 の「読めないとき、N との違いが、そのページの表示、診断、不完全の表示だけ」という
基準を、どう書き直すかを決めるために、違いが出る場所を実物で確かめる。

比べる 3 つ:
- N: すべて読める。
- U: a.md だけ、読めない（写しの中で、中身を捨てて error="os" にする。OS の読み取りの失敗と同じ形）。
- E: a.md の中身を空にする（代わりの値を入れる実装の対照。frontmatter に依るものまで消える）。

使い方: python unreadable_probe.py
"""
from __future__ import annotations

import copy
import os
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[3] / "info-hive-wiki" / "skills" / "info-hive" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import wiki_browse_core as core  # noqa: E402

PAGES = {
    "index.md": "# 索引\n\n## コンセプト\n\n- [[a]] — A の要約\n- [[b]] — B の要約\n- [[c]] — C の要約\n",
    "concepts/a.md": "---\ntitle: エー\ntype: concept\nsources: [missing-source]\ntags: [x]\n---\n# A\n\n[[b]] と [[missing]] と [[c#見出し]]\n",
    "concepts/b.md": "---\ntitle: ビー\ntype: concept\n---\n# B\n\n[[a]] を見る\n",
    "concepts/c.md": "---\ntitle: シー\ntype: concept\n---\n# C\n\n## 見出し\n\n本文\n",
}


def build_wiki(root: Path) -> None:
    for rel, text in PAGES.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def variant(snap, mode):
    s = copy.copy(snap)
    s.inputs = []
    for f in snap.inputs:
        g = copy.copy(f)
        if g.disk_rel == "concepts/a.md":
            if mode == "U":
                g.text, g.sha, g.error = None, None, "os"
            elif mode == "E":
                g.text = ""
        s.inputs.append(g)
    if mode == "U":
        s.unreadable = True
    return s


def summary(c, files):
    return {
        "drawn": sorted(c.drawn),
        "unresolved": c.unresolved(),
        "backlinks": {k: v for k, v in sorted(c.backlinks.items()) if v},
        "diagnostics": sorted((d.get("kind"), d.get("page")) for d in c.diagnostics),
        "files": sorted(files),
    }


def main():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "wiki"
        build_wiki(root)
        snap = core.take_snapshot(root)
        results = {}
        outputs = {}
        for mode in ("N", "U", "E"):
            c = core.Core(variant(snap, mode))
            files = c.render_all("text", "2026-11-11T00:00:00+0900")
            results[mode] = summary(c, files)
            outputs[mode] = files
    print(f"Python {sys.version.split()[0]}、{sys.platform}\n")
    for key in ("drawn", "unresolved", "backlinks", "diagnostics", "files"):
        print(f"## {key}")
        for mode in ("N", "U", "E"):
            print(f"- {mode}: {results[mode][key]}")
        print()
    print("## N と比べて、中身が変わった出力のファイル")
    for mode in ("U", "E"):
        changed = sorted(name for name in set(outputs["N"]) | set(outputs[mode])
                         if outputs["N"].get(name) != outputs[mode].get(name))
        print(f"- {mode}: {changed}")
    print()
    print("## lint の broken_links（a.md の読み取りを失敗させる）")
    print(f"- N: {lint_broken(False)}")
    print(f"- U: {lint_broken(True)}")


def lint_broken(fail_a: bool) -> list:
    """lint を実物で呼ぶ。fail_a なら、a.md の読み取りを PermissionError にする。"""
    import wiki_lint
    real = Path.read_text

    def read_text(self, *args, **kwargs):
        if fail_a and self.name == "a.md":
            raise PermissionError(13, "injected")
        return real(self, *args, **kwargs)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "wiki"
        build_wiki(root)
        Path.read_text = read_text
        try:
            pages = wiki_lint.collect_pages(root)
        finally:
            Path.read_text = real
        findings = wiki_lint.lint(pages, 10000, 25000, [], False, 3)
        return sorted((f["from_path"], f["to"]) for f in findings["broken_links"])


if __name__ == "__main__":
    main()
