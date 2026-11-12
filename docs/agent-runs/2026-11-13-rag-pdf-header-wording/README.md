# rag 0.5.2 の PDF のヘッダーの境界の書き方の敵対的レビュー（2026-11-13）

rag 0.5.1（to884/info-hive-rag#7、記録は [2026-11-12-rag-pdf-header-offset](../2026-11-12-rag-pdf-header-offset/README.md)）の README、CHANGELOG の 0.5.1 の項、`rag_index.py` のコメントは、PDF のヘッダーの条件を「`%PDF-` が先頭から 1024 バイト目までに始まれば」と書いていた。1 始まりで読むと、実装（`%PDF-` の開始位置が 0 始まりで 0〜1024）より 1 バイト狭い。wiki 0.11.1 のレビュー（[2026-11-12-wiki-rag-pdf-header-docs](../2026-11-12-wiki-rag-pdf-header-docs/README.md)）で指摘され、wiki 側だけ先に直していた。rag 0.5.2（to884/info-hive-rag#9）で、rag の文書と親の ADR-0013 を「`%PDF-` の前にあるバイトが 1024 バイト以下なら受け付ける」にそろえ、GPT-6.1 Sol（effort high、`ask-codex` の `review`）に 1 回レビューしてもらった。

- 依頼: `review-sol.md.task.md`。対象は差分 `reviewed.diff`（前半が `info-hive-rag`、後半が親の ADR）と、変更後の rag の README、CHANGELOG、`rag_index.py`、`plugin.json`、ADR-0013
- 結果: `review-sol.md`（採用可、確信度 高）
- レビュアーは、`has_pdf_header` に前置き 0〜1100 バイトを与えて 0〜1024 だけが通ること、docstring を除く `rag_index.py` の AST が変更前と同じことを確かめた。pypdfium2 が入っていないので、PDFium との一致は再検証していない

## 指摘と対応

| 指摘 | 重大度 | 対応 |
| --- | --- | --- |
| ADR-0013 の「`%PDF-` の前に 1024 バイトを超えるバイトがあるファイルを拒み」は、`%PDF-` が範囲の内と外に 1 つずつあると、実装より厳しく読める（`b"%PDF-" + b" " * 1020 + b"%PDF-"` を実装は受け付ける） | 軽微 | 「最初の `%PDF-` の前に」と、対象の出現を限定した |
| CHANGELOG の 0.5.2 の項に「1024 バイト目まで」が残る | 指摘ではない | 直す前の書き方を引用している箇所なので、そのままにした |

## 意図して残したもの

- `read_pdf` のエラーメッセージ「先頭の 1024 バイトに %PDF- がない」。同じ曖昧さを持つが、実行時の文字列で、`tests/rag/test_jobs.py` が正規表現で固定している。文書だけの修正から外し、別の変更で直す。
- 未マージの to884/info-hive-dev#80 の wiki のページ（`wiki/sources/取り込み手順の追従とリリース-wiki-0.11.1.md`）は「rag の README、CHANGELOG は前の書き方のまま」と書いている。この変更で古くなるが、別のブランチなのでここでは直さない。

## 確かめたこと

- `tests/rag/test_jobs.py` の `test_pdf_header_may_start_up_to_1024_bytes_in` が通った（Python 3.12、CI と同じ依存）。
- 公開済みの v0.5.1 の GitHub リリースの本文も、作者の了承を得て 2026-11-13 に直した。「`%PDF-` が先頭から 1024 バイト目までに始まれば受け付けます」を「`%PDF-` の前にあるバイトが 1024 バイト以下なら受け付けます（0.5.2 で、この書き方を直しました）」に替え、ほかの文は変えていない。
- 2026-11-13 に、CHANGELOG に 0.5.2 の日付を入れて（2ad7a93）to884/info-hive-rag#9 をマージした（f70385d）。v0.5.1 と同じく、注釈なしのタグ `v0.5.2` を f70385d に付け、GitHub リリース v0.5.2 を作った。本文は CHANGELOG の 0.5.2 の節と「更新のしかた」である。
- 使い捨ての設定フォルダー（`CLAUDE_CONFIG_DIR`）で、マーケットプレイスから `rag@info-hive` を入れた。`claude plugin list` は rag 0.5.2（依存の wiki は 0.11.2）を示した。キャッシュの README と CHANGELOG に新しい書き方があり、README と `rag_index.py` に前の書き方が残っていないことを確かめてから、フォルダーを消した。
- `git grep "1024 バイト目"` で、rag と親（`docs/agent-runs/` を除く）に、今の条件として書いた箇所が残っていないことを確かめた。
