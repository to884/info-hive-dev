## 判定

**却下。確信度：高。** 新しいパス設計に、正当なスラッグの取り込みを妨げる衝突と、別の取り込みの一時ファイルを清掃する経路があります。また、中間表現に入る前の本文欠落と、正しい削除判断を表現できない経路が残っています。

`wiki_webraw.py` は未実装です。以下では、現行コードでの実行確認と、設計仕様から導ける反例を区別します。

## 致命的・重大な欠陥

1. **【重大】`x` の錠ファイルと、`x.lock` の作業ディレクトリが衝突する。**

   現行の `check_slug()` は、`x` と `x.lock` の両方を受け付けます。しかし、設計上の保存先は次のようになります。

   ```text
   x の錠          .wiki-cache/ingest/x.lock
   x.lock の作業場 .wiki-cache/ingest/x.lock/
   ```

   `x` を一度取り込むと、仕様に従って錠ファイルが残ります。その後の `--stage --slug x.lock` は、作業ディレクトリを作れません。逆に `x.lock` の作業場が先にあれば、`x` は錠ファイルを開けません。並行実行や異常終了を必要としない衝突です。

   **検証結果：一致。** 両スラッグの受理と、生成されるパスの一致をメモリ内で確認しました。新コマンドの実動作は未確認です。

   根拠：[設計案・作業場所と錠](/C:/Works/info-hive-dev/docs/plans/wiki-web-ingest-deterministic-2026-11-13.md:216)（216〜226行）、[スラッグ検査](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py:954)（954〜959行）。

2. **【重大】`clean x` が、別スラッグ `x.v2` の確定中の一時ファイルを削除できる。**

   同じ wiki、同じ機械で、次の順序が成立します。

   1. A が `apply x.v2` を実行し、`raw/.x.v2.md.<stage_id>.tmp` を書き終える。
   2. Markdown を `os.link` で公開する直前に、B が `clean x` を実行する。`raw/x.md` は存在しないものとする。
   3. `clean x` の削除対象 `raw/.x.*.tmp` が、A の一時ファイルに一致する。
   4. A の `os.link` は、結ぶ元のファイルがなくなったため失敗する。

   A と B は別スラッグの錠を取るので、どちらも正当に実行できます。`apply x` の残存物検査も同じパターンなら、実行中の `x.v2` を古い残存物と誤認し、清掃へ誘導します。

   assets でも、`x.tmp-y` の一時ディレクトリ `.x.tmp-y.tmp-<stage_id>` が、`x` 用の `.x.tmp-*` に一致します。

   **検証結果：一致。** スラッグの受理と、上記すべてのパターン一致を確認しました。削除操作そのものは実行していません。

   根拠：[設計案・清掃](/C:/Works/info-hive-dev/docs/plans/wiki-web-ingest-deterministic-2026-11-13.md:224)（224〜229行）、[確定前の生成物と公開手順](/C:/Works/info-hive-dev/docs/plans/wiki-web-ingest-deterministic-2026-11-13.md:241)（241〜246行）。

3. **【重大】`aria-hidden="true"` を非表示の保証として扱い、可視本文を復元不能にする。**

   反例は、視覚表示と支援技術向けの説明を分けた式です。

   ```html
   <p>Equation:
     <span role="img" aria-label="x equals one">
       <span aria-hidden="true">x = 1</span>
     </span>
   </p>
   ```

   `aria-hidden` はアクセシビリティ API への露出を制御する属性です。可視内容に付ける用法も仕様上認められており、画面から消える保証にはなりません。[WAI-ARIA の定義](https://www.w3.org/TR/wai-aria-1.2/#aria-hidden)

   現行 Converter では、この入力から `Equation:` だけが残ることを実行確認しました。4 版も `aria-hidden="true"` の要素を木に入れないため、式は `review` に現れず、`restore` できません。「推測による除外を印にする」という変更の外側に、内容を失う経路が残っています。

   根拠：[設計案・木から除外する要素](/C:/Works/info-hive-dev/docs/plans/wiki-web-ingest-deterministic-2026-11-13.md:82)、[現行の除外判定](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py:294)（294〜300行）。

4. **【重大・仕様上の表現欠落】表セル内の段落とコードブロックを、中間表現が保持できない。**

   反例：

   ```html
   <table><tr><td>
     <p>Before</p>
     <pre><code>a = 1
   # keep</code></pre>
     <p>After</p>
   </td></tr></table>
   ```

   HTML の `td` は段落やコードブロックを含められます。[HTML Standard の内容モデル](https://html.spec.whatwg.org/multipage/tables.html#the-td-element)

   一方、設計は `table_cell` を「インラインの並びを持つ文章のノード」と定義しています。その並びには、段落やブロックの `code` がありません。この入力の二段落とコードブロックを、記載されたセル構造では表せません。

   現行 Converter では、次のように段落境界とコードの改行が失われることを確認しました。

   ```markdown
   | Before `a = 1 # keep` After |
   |---|
   ```

   新設計でも、この形を保持する契約はありません。セルの文章を一つの翻訳対象にすれば、コードブロックを翻訳対象から除外する保証も導けません。これは「今の出力との一致」を外しただけでは解消しない、表現能力の不足です。

   根拠：[設計案・ブロックと文章のノード](/C:/Works/info-hive-dev/docs/plans/wiki-web-ingest-deterministic-2026-11-13.md:83)（83〜85行）、[HTML との一致条件](/C:/Works/info-hive-dev/docs/plans/wiki-web-ingest-deterministic-2026-11-13.md:314)、[現行のセル変換](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py:794)（794〜802行）。

5. **【重大・明記された機能欠落】訳さないページでは、正しい部分削除を表現できない。**

   例えば、次の段落の末尾がサイトによって追加された共有文言であると、モデルが正しく判断した場合です。

   ```html
   <p>これは本文の説明である。この記事を共有する</p>
   ```

   求める結果は「これは本文の説明である。」です。しかし、4 版は訳さないページでノードの部分削除を禁止しています。

   段落を残せば雑音が残り、段落ごと消せば本文を失います。通常の日本語ページなので、翻訳用 `fill` を使う経路もありません。判断が正しくても、その結果を保存できません。これは未実装による不確実性ではなく、仕様に明記された制限です。

   根拠：[設計案・部分削除の禁止](/C:/Works/info-hive-dev/docs/plans/wiki-web-ingest-deterministic-2026-11-13.md:112)、[翻訳時だけの fill](/C:/Works/info-hive-dev/docs/plans/wiki-web-ingest-deterministic-2026-11-13.md:165)。現行手順は、日本語ページも含めて雑音を削り、本文を残すよう要求しています：[ingest.md](/C:/Works/info-hive-dev/info-hive-wiki/commands/ingest.md:36)。

## 崩れる前提

- **別スラッグの管理パスは衝突しない。** `x` と `x.lock` で、錠と作業場が同じパスになります。
- **スラッグの錠を取れば、その清掃対象を独占できる。** `x` のワイルドカードが `x.v2` の一時ファイルにも一致すると崩れます。
- **`aria-hidden="true"` の内容は可視本文ではない。** 支援技術向けの代替説明と可視表示を分けたページで崩れます。
- **表セルはインラインだけで表せる。** セル内に段落、リスト、コードブロックがあると崩れます。
- **翻訳しないページの雑音は、ノード単位で除去できる。** 本文と共有文言などが一つのテキストノードに混在すると崩れます。

## 見落としと軽微な問題

- **【軽微】公開直後の停止は、清掃の定義から漏れています。**  
  `os.link` の成功後、一時ファイルの削除前に停止すると、正式 Markdown と一時名の両方が残ります。しかし「確定前の生成物」は正式 Markdown がない場合だけなので、記載された `clean` と lint の対象になりません。「どの段で止まっても、残るのは確定前の生成物だけ」という説明は成立しません。本文の破損ではなく、清掃漏れです。根拠：[設計案](/C:/Works/info-hive-dev/docs/plans/wiki-web-ingest-deterministic-2026-11-13.md:241)（241〜249行）。

- **【軽微】`release_terms` の判断が永続記録から抜けています。**  
  保存項目にあるのは `keep` と `translate` だけです。`Rust` を `keep` にし、一出現を正当に解除しても、成功時に `fill` が消えると、解除対象と理由を保持する規定がありません。根拠：[解除の仕様](/C:/Works/info-hive-dev/docs/plans/wiki-web-ingest-deterministic-2026-11-13.md:125)、[保存する記録](/C:/Works/info-hive-dev/docs/plans/wiki-web-ingest-deterministic-2026-11-13.md:255)（255〜260行）、[作業場の削除](/C:/Works/info-hive-dev/docs/plans/wiki-web-ingest-deterministic-2026-11-13.md:247)。

- **【軽微】原因分類と設計本文で、旧 CLI の動作が食い違います。**  
  [root-causes-3.md の10行](/C:/Works/info-hive-dev/docs/agent-runs/2026-11-13-wiki-web-ingest-deterministic-review/root-causes-3.md:10)は、`--stage` なしでも既定判断で `apply` を呼ぶとしています。[設計本文の76行](/C:/Works/info-hive-dev/docs/plans/wiki-web-ingest-deterministic-2026-11-13.md:76)は、作業場を作る `--stage` と同じ動きです。自動確定するかどうかが一致していません。

## 検証した事実

| 主張 | 結果 |
| --- | --- |
| 指定された設計案、原因分類3本、レビュー3本、ADR、コマンド、ワークフロー、現行スクリプトを読む | 確認済み |
| `x.lock`、`x.v2`、`x.tmp-y` は正当なスラッグとして受理される | 実行確認済み |
| 清掃パターンは別スラッグの一時パスにも一致する | メモリ内の照合で確認済み |
| 現行変換は、上記の可視式と表セル構造を失う | 実行確認済み |
| 新しい `apply`、`clean`、タグ検査が実際に動く | 確かめられず。`wiki_webraw.py` は存在しない |
| OS の錠と公開処理の並行実行 | 未実行。指摘1・2はパス定義上の反例 |

検証は読み取りとメモリ内処理で行い、ファイルは変更していません。

## 崩せなかった点

- 現行出力との一致を合格条件から外したことで、review-3 の「既存の情報損失を維持しなければならない」という矛盾は成立しません。
- 設計本文どおり旧保存経路を廃止するなら、review-3 の従来 CLI による上書き経路は成立しません。
- 消さない錠ファイルに OS の錠を掛ける契約なら、古い錠の回収操作が新しい錠を消す反例は成立しません。
- 同じスラッグの `apply`・`clean`・`--restage` が、同じ錠を操作終了まで保持する間の直接競合は防げます。
- 書き終えた一時ファイルを `os.link` で公開する契約なら、書きかけの Markdown を正式名で公開する経路はありません。
- `release_terms` により、同じ綴りの固有名詞と普通名詞を区別した訳を表現できます。
- 最終の `content_root` で判断不足を調べる要求は明記されました。
- コードの翻訳対象からの除外、alt の直接編集禁止、異なる `stage_id` の拒否、画像の出現と asset の分離について、過去の直接的な反例は成立しません。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
