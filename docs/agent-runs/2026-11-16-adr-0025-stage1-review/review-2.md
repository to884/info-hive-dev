## 判定

**採用可（段階1に限る）。** 初回の重大指摘2件の反例は成立しなくなった。新たな重大欠陥は再現できなかったが、部分取得の保証と試験7には以下の限界が残る。確信度は**中**。

## 致命的・重大な欠陥

なし。

## 崩れる前提

- **ページ数が一致すれば、ページの対応も一致するという前提。** PDFium が `[A, B]`、pdfminer が `[B, A]` を返す場合、現在の検査は通り、別ページの本文と判定を組み合わせる。実PDFでの反例は未確認であり、コードにも限界が明記されている。[rag_pdf_layer.py:259](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage1/info-hive-rag/scripts/rag_pdf_layer.py:259)
- **続きの位置を呼び出し側が受け取れるという前提。** 終了コード3で未完了は分かるが、位置そのものは依然として標準エラーにしかない。標準エラーを捨てるラッパーでは再開できない。対象内にそのような実呼び出し側は見つからず、発生は**推測**である。[wiki_pdf.py:234](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage1/info-hive-wiki/skills/info-hive/scripts/wiki_pdf.py:234)

## 見落としと軽微な問題

1. **軽微：後続ページを構築しない保証は、`analyze_pages` では成立しない。**

   PDFium のページ数を2とし、`PDFPage.get_pages` が最初のページを返した後、2ページ目の構築で例外を投げる状態をスタブで再現した。`next(analyze_pages(data, start=1, stop=1))` は、1ページ目を返す前にその例外で失敗する。

   原因は、事前の `pdfminer_page_count` が全ページを列挙することである。追加試験は `pdfminer_pages` を直接呼び、この事前検査を通らない。「次のページが壊れていても、前のページは読める」という試験の説明は、利用側の経路には当てはまらない。

   根拠：[rag_pdf_layer.py:252](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage1/info-hive-rag/scripts/rag_pdf_layer.py:252)、[test_pdf_layer.py:126](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage1/tests/contract/test_pdf_layer.py:126)。上流の `get_pages` も、ページオブジェクトを構築してから返している。[pdfminer の実装](https://raw.githubusercontent.com/pdfminer/pdfminer.six/20260107/pdfminer/pdfpage.py)

2. **軽微：分割取得の費用は、今回の事前検査によって増えるが、その測定がない。**

   NページをK回に分けて読むと、ページ数検査だけでK回の全ページ列挙になる。抽出側も、再開ページに到達するまで先頭から列挙する。したがって、ページ列挙の費用は少なくとも `O(KN)` となる。

   また、本文取得1回につきPDFiumの文書を、`render` の件数確認、`analyze_pages` の件数確認、実際の判定で計3回開く。ページ途中からの再開でも繰り返す。時間制限を超えることは**未確認**だが、単回のストリーミング抽出の測定を、そのまま分割取得全体の費用には使えない。

   根拠：[wiki_pdf.py:116](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage1/info-hive-wiki/skills/info-hive/scripts/wiki_pdf.py:116)、[rag_pdf_layer.py:268](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage1/info-hive-rag/scripts/rag_pdf_layer.py:268)。

3. **軽微：試験7の新しい対照試験は、メモリー割り当てに依存する。落ちる頻度は未確認。**

   試験は、元の `id()` による出力と安定化後の出力が、少なくとも1ページで違うことを必須にしている。元の番地順が結果的に安定化後と同じ読み順になる実行では、製品に欠陥がなくても失敗する。20ページ化はその条件を排除していない。

   「8回とも違った」は観測結果であり、別OS・Python・割り当て状態での失敗率は分からない。実際にこの試験がフレークするという判断は**推測**である。また、この試験単独で確かめるのは「安定化後との差」であり、「元の実装がプロセス間で変動すること」ではない。

   根拠：[test_pdf_layer.py:356](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage1/tests/contract/test_pdf_layer.py:356)。

## 検証した事実

- **一致：** ページ数不一致のスタブでは、部分取得でも最初の本文を返す前に停止した。
- **一致：** 空本文と非空本文のスタブで、`empty_text` と `lists.empty_text` が区別された。手順にはSHA-256照合、`ocr_mode` 不明の報告、`always` の説明がある。
- **一致：** 実装の `render` を5,000ケースで実行した。全判定、空本文、改行、ページ境界、ページ途中の継続を含め、各出力の上限、継続の進行、連結結果の一致を確認した。
- **一致：** CLI入口をスタブで実行すると、出力長500・500・9文字、終了コード3・3・0となり、連結結果も一致した。
- **一致：** PDFまたは抽出識別が違うトークンは終了コード2で拒否された。
- **一致：** 共通ファイルの同一性と、ragが共通の判定関数を使う試験2件は通過した。ragの `ocr_page`、`extract_pages`、`chunks_for` は指定基準コミットとのAST比較で変更なしだった。
- **一致：** 公開7 PDFのSHA-256は記録と一致した。CI設定はWindows／Linux × Python 3.12／3.13／3.14の6組である。ただし公開PDFはCI対象外。
- **コード上は一致：** 試作との比較は、正規化前の本文から末尾の改ページ文字だけを除く形に変更されている。
- **確かめられず：** 依存パッケージがないため、実PDFによる22件全体、実際の試験7、分割取得の所要時間は再検証できなかった。

## 崩せなかった点

- 初回の「部分取得でページ数不一致を見逃す」「旧ragの空本文を判定する情報がない」という反例。
- 現在の固定見出しと500文字以上の上限で、空本文、最終ページ、`--from` を含む出力上限と連結の保証。
- `_stable_group_textboxes` の番号付け以外の処理に、上流との相違は見つからなかった。`Plane` の順序保持と、既定の `all_texts=False` で図内のグループ処理を避ける構造も崩せなかった。[上流 layout.py](https://raw.githubusercontent.com/pdfminer/pdfminer.six/20260107/pdfminer/layout.py)、[utils.py](https://raw.githubusercontent.com/pdfminer/pdfminer.six/20260107/pdfminer/utils.py)

使用した MCP サーバー: なし  
使用した Agent Skills: なし
