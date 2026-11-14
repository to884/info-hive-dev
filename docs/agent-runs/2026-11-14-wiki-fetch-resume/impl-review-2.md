## 判定

**却下。確信度：高。** 設計が守るとした「ファイルを丸ごと別の取得のものへ置き換える」範囲で、不整合な写しを再開する反例を2件再現した。共通化した報告計算ではなく、報告に使うファイルの対応関係が崩れている。

## 致命的・重大な欠陥

1. **重大：別の取得の `cleaned.md` を受け入れ、未検査の組み合わせを `frozen` として再開する。**

   再現手順：

   - 08:00 に取得 A を行い、`freeze` を通す。A の `cleaned.md` を保存する。
   - 09:00 に同じ URL・スラッグを、本文の異なる取得 B で `--force` により取り直す。
   - **`cleaned.md` だけを A のファイルへ丸ごと戻す。** raw・`fetched.md`・`fetch.json` は B のままにする。
   - URL だけで再実行する。

   実コードは、**取得呼び出し0回、終了コード0、`fetch_skipped: true`、`work_stage: frozen`** を返した。`cleaned.md` の frontmatter が B と異なっていても受け入れた。同じ長さの別本文では、再生成した報告の警告も空だった。

   さらに、W6 の長文翻訳手順に従って A の `cleaned.md` から frontmatter と訳文を組み立てると、**B の取得記録が残った状態で `check` が誤り・警告ともなしで通った。** 後段で必ず止まるともいえない。

   `resumable_fetch` は `cleaned.md` を照合せず、`resume_fields` はその存在だけで `frozen` を決める。これは取得時刻を1時間離した反例であり、承知済みの「frontmatter が同じ別版の raw」には依存しない。

   根拠：`info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:321–339,374–384,936–1008`、`info-hive-wiki/skills/info-hive/references/ingest-workflow.md:140–142`。

2. **重大：`fetched.md` が同一バイト列になる別取得では、`fetch.json` の差し替えで警告と削除記録が消える。**

   再現用 HTML は、MediaWiki の generator 指定を持ち、次の配置とする。`P` は同じ700文字の段落である。

   ```html
   <table><tr><td class="metadata">
     <article><h1>Article</h1><p>P</p></article>
   </td></tr></table>
   <div><h1>Article</h1><p>P</p></div>
   ```

   - 取得 A：通常設定。表が規則で除かれ、`div` を推定して取得する。`content_root: guess`、本文を推定した警告、表の削除記録が残る。
   - 取得 B：同じ原文を `--keep-noise --force` で取得する。`article` が選ばれ、`content_root: article`、警告・削除記録は空になる。
   - 両取得を同じ秒に行うと、**生成される `fetched.md` は完全に同一**になる。
   - A の raw と `fetched.md` を戻し、`fetch.json` だけ B のものにして再開する。

   実コードは、**終了コード0、`fetch_skipped: true`、`content_root: article`、`warnings: []`、`removed_by_rule: []`** を返した。A の注意と削除記録が失われる。

   これはハッシュ衝突ではない。異なる診断結果が同じ Markdown を生成するため、その Markdown のハッシュでは取得記録を識別できない。raw 自体も同一バイト列なので、承知済みの「同じ frontmatter を持つ別本文の raw」とは異なる。

   根拠：`wiki_rawcheck.py:315–318,332–339`、`info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py:574–607,1270–1275,1405–1408`。CHANGELOG 14行目の「同じページを別の設定で取った `fetch.json` でも続けない」という保証と食い違う。

## 崩れる前提

- **`cleaned.md` が存在すれば、現在の取得について `freeze` が成功している。**  
  別取得の `cleaned.md` だけを復元すると崩れる。存在と、現在の取得との対応は別である。

- **同じ原文を別設定で取れば、`fetched.md` も異なる。**  
  別の要素を選んでも同じ Markdown になる場合に崩れる。警告や削除記録は Markdown に含まれない。

- **同じ関数で報告を再生成すれば、元の `freeze` 報告を再現できる。**  
  入力が同じ取得に属する場合に限る。別取得の `cleaned.md` を渡した場合、元のどの `freeze` も出していない報告になる。

## 見落としと軽微な問題

- **軽微：試験が、上記2種類のファイル混在を検査していない。**  
  `test_another_take_of_the_same_page_is_not_resumed` は、設定変更で Markdown が変わる入力だけを使う。`test_frozen_resume_returns_freeze_report` は、対応の正しい `cleaned.md` だけを使う。そのため、今回の反例を通してしまう。根拠：`tests/wiki/test_wiki_web_check.py:1640–1658,1684–1706`。

- **軽微：DOM による取り直しのコマンド例に `--force` がない。**  
  `references/ingest-workflow.md:88` の本文は取り直しに必要と説明するが、直後の91–92行目の例には付いていない。URL で取得済みのページをこの例で取り直すと、終了コード3で止まる。`commands/ingest.md` の W3 とは一致していない。

## 検証した事実

- **一致：** サブモジュールの `origin/main..HEAD` の差分は、指定された `impl-2.diff` の該当部分と一致した。試験ファイルも差分に記録された blob `6045373` と一致した。
- **一致：** 行全体の削除・行の一部削除・無変更の3例で、切り出し前後の `freeze` 出力は一致した。対応する再開時の削除報告と画像一覧も一致した。
- **一致：** `fetched_sha256` を除いた模擬0.14.0記録は、取得を1回行ってから `fetched` として再開した。
- **一致：** 辞書でない JSON、必須キー欠落、画像・警告・削除記録の型不正など7例は、例外にならず取得へ進み、`work_dir: false` を返した。
- **食い違い：** 別取得のファイルを受け入れないという設計上の保証と、CHANGELOG の取得記録に関する保証は、上記反例では成立しない。
- 検証はファイル操作をメモリに差し替え、実際の `build`・変換器・`freeze`・`check` を実行した。リポジトリは変更していない。既存試験一式は実行していない。

## 崩せなかった点

- 対応の正しい写しに対する `deletion_report` の切り出しによる出力変化。
- 検証した型不正の取得記録を、再開可能として受け入れる反例。
- `--force`・`--html-file` を取得前の再開へ吸い込む経路。条件分岐では明示的に除外されている。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
