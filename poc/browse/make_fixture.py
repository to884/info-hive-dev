"""ADR-0010 の PoC で使う試験用の Wiki を out/fixture-wiki/ に作る。

リポジトリには入れない名前（長い日本語の名前など）も作るので、毎回ここで生成する。
配布対象ではない。
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE / "out" / "fixture-wiki"
RAW_DIR = HERE / "out" / "raw"

# 1 つの名前の要素が 85 文字を超えると、UTF-8 で 255 バイトを超える（ext4、APFS の上限）。
LONG_NAME = "長い名前のページ" * 12  # 96 文字、288 バイト


def page(path: str, text: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    if ROOT.exists():
        shutil.rmtree(ROOT)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    pdf = RAW_DIR / "報告書 2026.pdf"
    pdf.write_bytes(b"%PDF-1.4\n% PoC\n")
    raw_abs = pdf.resolve().as_posix()

    page("SCHEMA.md", "# SCHEMA\n\n試験用。\n")
    page("index.md", "# 索引\n\n- [[ナレッジグラフ]]\n- [[オントロジー]]\n")
    page("log.md", "# 記録\n\n- 2026-11-07 作成\n")
    page("README.md", "# README\n\nlint は除き、search は含む。\n")
    page("indexes/概念.md", "# 概念の索引\n\n- [[ナレッジグラフ]]\n")

    page("concepts/ナレッジグラフ.md", """---
type: "concept"
title: "ナレッジグラフ"
summary: "実体と関係をグラフで表す知識の表現。"
tags: ["知識表現", "グラフ"]
created: 2026-11-07
updated: 2026-11-07
---

# ナレッジグラフ

ナレッジグラフは [[オントロジー]] の語彙で実体を結ぶ。定義は [[オントロジー#定義]] を見る。

人物の例は [[entities/山田 太郎]]、出典は [[sources/報告書 2026|報告書]] にある。

未作成のページへのリンク: [[存在しないページ]]。重複したスラッグへのリンク: [[重複]]。
パスを付けた重複へのリンク: [[concepts/重複]]。

長い名前のページ: [[{long}]]。

<script>alert("生の HTML は出さない")</script>

外部へのリンク: [例](https://example.com/)。

禁則の確認用の長い行。「かぎかっこ」、句読点。ーー長音、っャュョ小書き文字、（括弧）が行頭に来ないこと。ＡＢＣ全角英字とABC半角英字、2026年11月7日、URL https://example.com/very/long/path/that/should/wrap/without/overflowing/the/column/width を含む。
""".replace("{long}", LONG_NAME))

    page("concepts/オントロジー.md", """---
type: "concept"
title: "オントロジー"
summary: "概念と関係の語彙を定める仕様。"
tags: ["知識表現"]
---

# オントロジー

## 定義

概念と関係の語彙。[[ナレッジグラフ]] で使う。

## 例

最初の例。

## 例

同じ名前の見出し（ID に連番が付く）。
""")

    page("entities/山田 太郎.md", """---
type: "entity"
title: "山田 太郎"
tags: ["人物"]
---

# 山田 太郎

空白を含む名前のページ。[[ナレッジグラフ]] から参照される。
""")

    page("concepts/重複.md", "---\ntype: \"concept\"\ntitle: \"重複（概念）\"\n---\n\n# 重複（概念）\n")
    page("entities/重複.md", "---\ntype: \"entity\"\ntitle: \"重複（実体）\"\n---\n\n# 重複（実体）\n")

    page("sources/報告書 2026.md", f"""---
type: "source"
title: "報告書 2026"
raw: "{raw_abs}"
raw_sha256: "0000000000000000000000000000000000000000000000000000000000000000"
tags: ["出典"]
---

# 報告書 2026

PDF の出典。`raw:` は絶対パス（ADR-0013）。
""")

    page(f"concepts/{LONG_NAME}.md", f"---\ntype: \"concept\"\ntitle: \"長い名前\"\n---\n\n# 長い名前\n\n[[ナレッジグラフ]]\n")

    # lint と search の集合の違いを見るためのファイル
    page("assets/メモ.md", "# assets のメモ\n\nlint は除き、search は含む。\n")
    page(".wiki-cache/キャッシュ.md", "# キャッシュ\n\nsearch は除く。lint は？\n")
    page(".evolution/e.md", "# evolution\n")
    page("concepts/.隠し.md", "# 隠し\n")
    print(ROOT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
