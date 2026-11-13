# ADR-0019：wiki とみなすのは、ルートに SCHEMA.md がある（初期化された）ディレクトリだけにする

| 項目 | 内容 |
| --- | --- |
| 状態 | 提案 |
| 決定日 | （承認の日を入れる） |
| 決定者 | info-hive の開発者（このリポジトリの作者） |
| 関連 | ADR-0008（作業領域の設定）、ADR-0012（MCP サーバー）、ADR-0013（rag の PDF の記録）、[初期化していないディレクトリを wiki として扱わない計画](../plans/wiki-uninitialized-root-2026-11-13.md) |

## 背景

wiki のコマンドは、wiki の場所が指示や設定から見つからなければ `./wiki` を使う。そこに `SCHEMA.md` のないディレクトリ（ほかの用途の `wiki/`、GitHub の wiki の写し）があると、lint と統計は普通に報告し、検索の `--cache` はその中にキャッシュを書き、`init_wiki.py --upgrade` は wiki 一式を作る。何をもって wiki とみなすかの決定がなく、入口ごとに「ディレクトリがあるか」だけを見ていた。

一方で、`SCHEMA.md` で見分けている箇所もすでにある。`wiki_evolve.py` の改善の操作は `SCHEMA.md` がなければ止まり、rag の `rag_config.py` は `wiki_root` に `SCHEMA.md` がなければ「先に wiki を初期化してください」で止まる。

## 決定

| 項目 | 決定 |
| --- | --- |
| 初期化された wiki | ルートがディレクトリで、その直下の `SCHEMA.md` が通常のファイル（リンクなら、先が通常のファイル）であるもの。中身は見ない |
| 判定の置き場所 | wiki の `skills/info-hive/scripts/wiki_initialized.py` の 1 か所。rag の `rag_config.py` は同じ規則を自分で持つ（rag は wiki のスクリプトを読み込まない） |
| 判定する場所 | wiki のパスを受け取る入口（CLI、MCP のツール、browse、Web ページの取得、経験の記録、アップグレード）で、wiki を読み始める前、パスを解決する前。長く動くプロセス（MCP のサーバー、閲覧のサーバー）は、要求のたびに確かめる。ライブラリの関数は判定しない。評価のランナーが受け取る事実情報のコーパスの写しは、利用者の wiki ではないので判定しない |
| 未初期化のとき | 何も書かずに止まり（CLI は終了コード 1、MCP はツールのエラー）、理由と `/wiki:init` を示す |
| 初期化 | `init_wiki.py`（`--upgrade` なし）だけが、未初期化のディレクトリを wiki にできる |

## 理由

- `init_wiki.py` は初期化で必ず `SCHEMA.md` を作り、`--upgrade` でも上書きしない。移植元の llm-wiki でも同じである。今ある wiki は、どれも `SCHEMA.md` を持つ。
- どのコマンドも、最初に `SCHEMA.md` を読む。`SCHEMA.md` のない wiki では、規約が分からないまま作業することになる。
- `wiki_evolve.py` と rag が、すでに同じ規則を使っている。規則を増やさずにそろえられる。

## 検討した選択肢

| 選択肢 | 採らなかった理由 |
| --- | --- |
| `index.md` で見分ける | 索引を `indexes/` に分けた wiki では、`index.md` は一覧のファイルになり、役割が変わる。ほかの用途の `wiki/` にも `index.md` はありうる（静的サイトの入口など） |
| 作業領域の設定（`.info-hive/workspace.json`）で見分ける | 設定は任意で、`init_wiki.py` は作らない。設定のない wiki が多い |
| 専用の印のファイル（`.info-hive-wiki` など）を作る | 今ある wiki に印がないので、移行が要る。`SCHEMA.md` で足りる |
| 中身で推し量る（frontmatter のあるページの割合など） | 結果が wiki の状態で揺れ、空の wiki を見分けられない |
| `SCHEMA.md` の中身（目印の見出し）まで確かめる | 利用者が書き換えてよいファイルなので、見出しが残っているとは限らない。アップグレードの検出（`SCHEMA_SECTION_MARKERS`）とは目的が違う |

## 影響

- `SCHEMA.md` のないディレクトリに向けた lint、統計、検索、グラフ、判定、閲覧、MCP のツールは、今まで答えていたものも断るようになる（wiki 0.13.0）。
- `wiki_fetch.py` は、取り込み先の wiki（`--wiki`）を必須で受け取り、raw のルートを作らなくなる。`wiki_evolve.py capture` は、記録先の wiki を確かめる。
- `SCHEMA.md` を消した wiki は、アップグレードできない。同じ場所で `/wiki:init` を実行すると、既存のファイルを上書きせずに `SCHEMA.md` を足して戻せる。
- 名前の大文字と小文字はファイルシステムに任せる。Windows と macOS の既定では `schema.md` も見つかる。
- 規則を変えるときは、wiki の `wiki_initialized.py` と rag の `rag_config.py` をそろえる。

## 参照

- [初期化していないディレクトリを wiki として扱わない計画](../plans/wiki-uninitialized-root-2026-11-13.md)
- `info-hive-wiki/skills/info-hive/scripts/wiki_initialized.py`
- `info-hive-rag/scripts/rag_config.py`（`SCHEMA.md` の確かめ）
- `tests/wiki/test_uninitialized_wiki.py`
