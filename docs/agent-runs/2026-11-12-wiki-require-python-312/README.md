# wiki の同梱のスクリプトを Python 3.12 以上にする変更のレビュー（2026年11月12日）

[ADR-0018](../../adr/0018-wiki-requires-python-312.md) の変更を、GPT-6.1 Sol（effort xhigh）の敵対的レビューにかけた記録である。

| ファイル | 中身 |
| --- | --- |
| `review-1.task.md` | 依頼文 |
| `py312.wiki.diff`、`py312.dev.diff` | レビューの対象にした差分（info-hive-wiki の `8addd33..4da26b6`、info-hive-dev の `aef824d..7dd8e76`）。このときは、版を 0.11.0 としていた |
| `review-1.md`（`.log`、`.status.json`、`.task.md`） | レビューの結果。判定は「条件付きで採用可」（確信度は中）、致命的・重大な欠陥はなし |

## レビューのあとで分かったこと

レビューの最中に、info-hive-wiki の main に 0.11.0（to884/info-hive-wiki#46、下限を 3.12 に上げた変更）と 0.11.1（#47、PDF の取り込みの手順）が入っていた。#46 は、PEP 723 の宣言、文書、CI、lint の NUL の修正を含み、`wiki_text.py` の版の確かめは含まない。

そこで、info-hive-wiki のブランチ `fix/walk-excluded-dirs` を main（`59af357`）の上に積み直し、#46 と重なるコミットを落とした。残したのは、走査の修正（0.10.2 として準備していたもの）、`DirEntry.is_junction()` への置き換え、版の確かめで、版は 0.11.2 にした。lint の NUL の修正は、main のもの（同じ扱い）を使う。積み直す前のブランチは、手元に `fix/walk-excluded-dirs-draft-0110` として残している。

## 指摘への対応

指摘はどれも軽微だった。1〜3 は、同じ前提（「3.10 の構文で読め、最初の wiki の読み込みが `wiki_text` なら、古い版でも版の確かめに届く」を、静的な検査で確かめられる）が崩れたものなので、前提をやめ、本物の古い Python で動かす試験に替えた。

| 指摘 | 対応 |
| --- | --- |
| 1. 3.6 以前では、`from __future__ import annotations` が構文の誤りになり、版の確かめに届かない | 確かめる範囲を、今までの対象だった 3.10 と 3.11 に限ると決め、ADR、CONTRIBUTING、変更履歴、試験の説明に書いた。3.9 以前は対象にしない |
| 2. 試験の入口の一覧（`DIRECT`）が、改善のワークフローなどの入口を漏らしていた | 手で書いた一覧をやめ、ファイルから集める（最上位に `__main__` の分岐を持ち、PEP 723 の宣言がないものと、文書が直接動かす `wiki_search.py`）。読み込んだときに wiki のモジュールを読まない 2 つ（`wiki_workspace.py`、関数の中で読み込む `wiki_evolve_claude.py`）は、試験の外であることを書いた |
| 3. 静的な検査では、`wiki_text` より前の `import tomllib` のような後退を見逃す | 静的な検査を消し、本物の 3.10 と 3.11 で各入口を `--help` つきで動かして、理由を書いて止まることを確かめる。`wiki_lint.py` に `import tomllib` をわざと入れると、3.10 で落ちることを確かめた。古い版は `uv python find` で探し、CI では `uv python install 3.10 3.11` のうえ、見つからなければ失敗にする |
| 4. 3.14 の CI では、索引の依存を入れた試験が飛ばされる | 依存を入れる段を、行列の両方の版で流す。3.14 で依存が入り、試験が通ることを手元で確かめた |

「崩れる前提」の 4 つ目（`UV_PYTHON=3.10` などを引き継いだときの uv の選び方）は、レビュアーが推測と書いたもので、確かめていないので採っていない。

## 確かめた試験（積み直したあと）

- Windows 11: `test_walk.py`、`test_page_set.py`、`test_wiki_lint.py`、info-hive-wiki の `eval/scripts`（3.12.13、3.13.7、3.14.6）。`test_python_version.py`（本物の 3.10 と 3.11 を必ず使う設定）。3.14 の `test_walk.UseTests`（索引の依存あり）。`test_mcp_server.py`、`test_wiki_index.py`、`test_browse*.py`（3.12、依存あり）
- Linux（WSL の Ubuntu 24.04）: `test_walk.py`、`test_page_set.py`、`test_wiki_lint.py`、`eval/scripts`（3.12、3.14）。`test_python_version.py`（3.10 と 3.11 がないので、古い版の試験は飛ばした）
