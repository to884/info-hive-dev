# wiki の取り込み手順を rag 0.5.1 の PDF のヘッダーの条件に合わせた変更の敵対的レビュー（2026-11-12）

rag 0.5.1（to884/info-hive-rag#7、記録は [2026-11-12-rag-pdf-header-offset](../2026-11-12-rag-pdf-header-offset/README.md)）で、`%PDF-` が先頭から 1024 バイトの範囲で始まれば PDF を受け付けるようになった。rag のレビューで、wiki の `skills/info-hive/references/ingest-workflow.md` が「先頭が `%PDF-`」のままだと指摘されたので、wiki 0.11.1 で直した。その変更を GPT-6.1 Sol（effort high、`ask-codex` の `review`）に 1 回レビューしてもらった。

- 依頼: `review-task.md`
- 対象: `info-hive-wiki` の `origin/main..HEAD`（コミット 014593f）。差分は `reviewed.diff`
- 結果: `review-sol.md`。判定は「条件付きで採用可」（確信度：高）。致命的・重大な欠陥はなし

## 指摘と対応

| 指摘 | 重大度 | 対応 |
| --- | --- | --- |
| 手順に rag の版の条件がない。wiki 0.11.1 と rag 0.5.0 を組み合わせると、前置きのある PDF のジョブは `failed` になる | 軽微 | rag 0.5.1 以降と 0.5.0 以前の違いを手順に書いた（コミット 6f8b688） |
| 「先頭から 1024 バイト目まで」を 1 始まりで読むと、実装より 1 バイト狭い。実装は `%PDF-` の開始位置（0 始まり）が 1024 でも受け付ける | 軽微 | wiki の手順と CHANGELOG を「`%PDF-` の前にあるバイトが 1024 バイト以下」に直した（6f8b688）。rag の README、CHANGELOG、v0.5.1 のリリースの本文は、前の書き方のまま |
| CHANGELOG の末尾の比較リンクが v0.7.0 で止まっていて、`CONTRIBUTING.md` の規約と食い違う | 軽微 | 0.8.0 から続く食い違いなので、この変更では直さない。PR に書いた |

## 判断

- ヘッダーは、登録のとき（`register_pdf` → `Config.pdf_path`）ではなく、ワーカーの処理（`Engine.ingest_pdf` → `read_pdf`）で確かめる。Sol の報告を、rag の main の `rag_server.py`、`rag_index.py`、`rag_worker.py` で確かめた。手順の文も、登録で拒むものと、処理でジョブが `failed` になるものに分けた。
- 版は 0.11.1（パッチ）。文書だけの修正である。

## 確かめたこと

- 親リポジトリの `tests/wiki/test_source_claims.py`（取り込み手順の記述の試験）: 11 件が通った。
- to884/info-hive-wiki#47 の CI（Linux と Windows、Python 3.12 と 3.14）: すべて通った。
- 差分に見えない文字が入っていないことを走査した。

## 確かめていないこと

- `tests/wiki` を全部流すと、`test_wiki_index`、`test_mcp_server`、`test_browse_server` などで 2 件が失敗し、16 件が例外で止まった。システムの Python（3.14）で流したので、依存（Tantivy など）がないためだと見ているが、変更前の main で同じになるかは確かめていない。
- CONTRIBUTING.md のリリースの手順のうち、同梱のスクリプトのスモークテストはしていない。
