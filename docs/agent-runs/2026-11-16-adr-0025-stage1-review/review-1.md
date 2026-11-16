## 判定

**条件付きで採用可。** 部分取得でページ対応の不一致を見逃すことと、旧 rag 向けの代替手順に必要な情報が不足していることから、段階1の保証はまだ満たされていない。確信度は高。ただし、ページ対応の反例はスタブで再現したもので、実 PDF では未確認である。

## 致命的・重大な欠陥

1. **重大：部分取得・途中打ち切りでは、ページ数の不一致を検出せず、別ページの本文と判定を組み合わせる。**

   `analyze_pages` は、`stop < PDFium のページ数` のとき、pdfminer 側の総ページ数を検査しない。途中でジェネレーターを閉じた場合も、末尾の検査に到達しない。

   次の状態をスタブで再現した。

   - PDFium は原本のページ `[1, 2, 3]` を認識する。
   - pdfminer は原本のページ `[1, 3]` を認識し、連番 `[1, 2]` を付ける。
   - `analyze_pages(data, start=2, stop=2)` は、**PDFium の原本2ページ目の判定と、原本3ページ目の本文を、ページ2として正常に返す**。
   - 全件取得なら `RuntimeError` になる。

   `render` も文字数で途中 return するため、同じ検査漏れを通る。契約試験の部分取得テストは、両ライブラリが同じページを認識する正常系だけである。

   根拠：[rag_pdf_layer.py:240](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage1/info-hive-rag/scripts/rag_pdf_layer.py:240)、[wiki_pdf.py:100](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage1/info-hive-wiki/skills/info-hive/scripts/wiki_pdf.py:100)、[test_pdf_layer.py:107](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage1/tests/contract/test_pdf_layer.py:107)。同一内容の `wiki_pdf_layer.py` にも該当する。

2. **重大：旧 rag の空本文を報告する手順が、指定された出力だけでは実行できない。**

   手順は `wiki_pdf.py --json` を実行した後、「rag の本文が空で、wiki_pdf.py の本文が空でないページ」を報告する。しかし、既定の `--json` には、ページ本文も、本文の長さも、空本文の一覧もない。`page_details` は `--pages` を付けた場合だけである。

   ページ辞書の `text` と `text_sha256` だけを空文字列相当から非空相当に変えたスタブで、既定の `summary` が同じ出力になることを確認した。指定された情報からは、この条件を判定できない。

   通常の本文出力でも、`garbled` と `scan` は本文を隠す。たとえば合成試料の4ページ目には文字列 `p4` があるが、通常出力は説明文だけになる。出力上の空本文と、文字の層の空本文を同一視すると、報告対象を取り違える。

   根拠：[ingest-workflow.md:239](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage1/info-hive-wiki/skills/info-hive/references/ingest-workflow.md:239)、[wiki_pdf.py:151](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage1/info-hive-wiki/skills/info-hive/scripts/wiki_pdf.py:151)、[wiki_pdf.py:76](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage1/info-hive-wiki/skills/info-hive/scripts/wiki_pdf.py:76)、[pdf_fixtures.py:58](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage1/tests/contract/pdf_fixtures.py:58)。

## 崩れる前提

- **ジェネレーターを最後まで消費すればよい、という前提。** `stop` や `render` の途中 return では成立しない。重大指摘1に該当する。
- **同じパスの PDF は rag が処理した PDF と同じ、という前提。** 非同期処理後に原本が差し替わると崩れる。代替手順には、rag の `result.sha256` と今回の `--json` の `sha256` を照合する指示がない。
- **続きの位置を使う間、抽出方式が変わらないという前提。** トークンが検証するのは PDF のハッシュだけで、抽出の識別は含まない。更新で本文順が変わっても、古い文字位置を受理する。
- **呼び出し側が標準エラーを読むという前提。** 続きがあっても終了コードは0で、標準出力には継続情報がない。標準出力だけを返すラッパーでは途中終了と全文取得を区別できない。実際のエージェントによる読み落としは未確認であり、その発生については推測である。

## 見落としと軽微な問題

- **軽微：`--max-chars` は上限になっていない。** `text="ABC"` の1ページに上限1を指定すると、最初の出力は `## p. 1\n\nA` の10文字になる。空の2ページ目を単独で取得すると、上限1でも11文字出る。見出しを無条件に出し、本文も `max(1, room)` で最低1文字出すためである。試験は連結結果だけを検査し、各断片の長さを検査していない。根拠：[wiki_pdf.py:106](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage1/info-hive-wiki/skills/info-hive/scripts/wiki_pdf.py:106)、[test_pdf_layer.py:189](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage1/tests/contract/test_pdf_layer.py:189)。

- **軽微：試験7の対照実験は、「決め方を外すと違いが出る」を直接確かめていない。** `columns_first` も決定的な番号付けであり、実際の `id()` に戻した抽出ではない。番号順が本文に影響する証拠にはなるが、安定化を外した実装でプロセス間の差が検出される証拠にはならない。根拠：[test_pdf_layer.py:274](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage1/tests/contract/test_pdf_layer.py:274)、同ファイル304行目。

- **軽微：「測定の試作と同じ本文」は、文字列そのものでは一致しない。** 試作は末尾の `\f` だけを除去し、製品はすべての `\f` と前後の空白を除去する。たとえば converter の出力が `A\n\n\f` なら、試作は `A\n\n`、製品は `A` になる。比較試験は製品と同じ正規化を加えた別実装を参照しており、この差を隠す。根拠：[stable_text.py:59](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage1/docs/research/adr-0025-measurement-2026-11-15/scripts/stable_text.py:59)、[rag_pdf_layer.py:227](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage1/info-hive-rag/scripts/rag_pdf_layer.py:227)、[test_pdf_layer.py:297](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage1/tests/contract/test_pdf_layer.py:297)。

- **軽微：`stop` の次のページまで構築する。** `for` が次の `PDFPage` を受け取ってから上限を判定するため、`stop=1` でも2ページ目の構築例外が伝播する。1ページ目を yield し、次に例外を送出するスタブで再現した。pdfminer もページを構築してから yield する。[rag_pdf_layer.py:221](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage1/info-hive-rag/scripts/rag_pdf_layer.py:221)、[pdfminer の PDFPage 実装](https://raw.githubusercontent.com/pdfminer/pdfminer.six/20260107/pdfminer/pdfpage.py)。

- **軽微：OCR 設定について ADR と手順が食い違う。** ADR は設定を取得できない旧 rag では `ocr_mode` 不明を伝えるとしているが、代替手順にはない。また「確かめるべき text ページと blank は rag でも OCR されない」は `always` では誤りである。根拠：[ADR:122](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage1/docs/adr/0025-pdf-text-layer-with-pdfminer-vertical.md:122)、[ingest-workflow.md:235](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage1/info-hive-wiki/skills/info-hive/references/ingest-workflow.md:235)、[rag_pdf.py:61](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage1/info-hive-rag/scripts/rag_pdf.py:61)。

## 検証した事実

- **一致：** wiki と rag の共通ファイルは同じバイト列だった。対応する契約試験と、`rag_pdf.inspect_page` が共通関数そのものである試験の2件を実行し、通過した。
- **一致：** 直前コミットとの AST 比較で、rag の `ocr_page`、`extract_pages`、`chunks_for` は変更されていなかった。
- **一致：** 手元の公開7 PDF は、すべて記録された SHA-256 と一致した。
- **食い違い：** 「測定の試作と同じ本文」は、前後空白などの正規化まで含めると成立しない。
- **確かめられず：** 実 PDF を使う全18件、Python 3.12・3.13、Linux の実行結果。この環境は Python 3.14.6 で依存パッケージがなく、指定の uv キャッシュにもアクセスできなかった。
- CI の設定は **Linux・Python 3.12・合成 PDF のみ**。3.13・3.14 の依存導入成功は、これらの版での抽出結果の検証にはならない。根拠：[pdf-contract.yml:29](/C:/Works/info-hive-dev/.claude/worktrees/adr0025-stage1/.github/workflows/pdf-contract.yml:29)。

## 崩せなかった点

- `_stable_group_textboxes` は、番号付け以外では上流の距離計算、延期、縦横グループ選択、削除、再投入の手順と一致していた。`begin_page` の置き換えにも、ページクラス以外の差は見つからなかった。[上流 layout.py](https://raw.githubusercontent.com/pdfminer/pdfminer.six/20260107/pdfminer/layout.py)、[converter.py](https://raw.githubusercontent.com/pdfminer/pdfminer.six/20260107/pdfminer/converter.py)。
- 確認した範囲では、`Plane` は挿入順を保持し、`group_textlines` の集合は重複判定に使われていた。`all_texts=False` の `LTFigure` が未修正のグループ処理を呼ぶ反例も見つからなかった。[上流 utils.py](https://raw.githubusercontent.com/pdfminer/pdfminer.six/20260107/pdfminer/utils.py)、[layout.py](https://raw.githubusercontent.com/pdfminer/pdfminer.six/20260107/pdfminer/layout.py)。
- 実装の `render` に、空本文、全判定、改行、最終ページ、小さい上限を含むスタブを与えた1,600ケースでは、断片の連結は一括出力と一致した。文字数上限の違反とは別の結果である。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
