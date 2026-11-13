## 判定

**却下。確信度：高。** 印の一致だけではリンクの構文と対応先を保証できず、再取得の判定を `stage` 時点で済ませる設計では既存 raw の上書きを防げません。現行 Converter の出力と、提案する単位・検査規則にも食い違いがあります。

`apply` は未実装のため、以下では現行コードで再現した事実と、設計仕様に対する反例を区別しています。

## 致命的・重大な欠陥

1. **【致命】印が完全に一致しても、リンクを消したり、別の文言に接続したりできる。**

   元の単位が `[manual]⟦U1⟧` のとき、訳文を `マニュアル⟦U1⟧` にしても印の検査は通ります。復元結果は `マニュアル(https://example.org/manual)` であり、リンクではありません。同梱の Markdown 解析器でもリンクにならないことを確認しました。

   また、`[A]⟦U1⟧ [B]⟦U2⟧` を `[A]⟦U2⟧ [B]⟦U1⟧` にすると、印の種類・個数を維持したままリンク先が逆になります。追加の英数字・記号もありません。「リンクの欠落を構造で防ぐ」という主張は成立しません。

   根拠：[設計案:90](C:/Works/info-hive-dev/docs/plans/wiki-web-ingest-deterministic-2026-11-13.md:90)、同128〜129行、193行。

2. **【重大】`Converter.blocks()` の境界は、提案する単位の境界ではない。**

   現行 Converter に次の HTML を渡すと、引用全体が一つの文字列になります。

   ```html
   <blockquote>
     <p>Before</p>
     <pre><code>x = 1
   # unchanged</code></pre>
     <p>After</p>
   </blockquote>
   ```

   出力は次の一要素です。

   ```markdown
   > Before
   >
   > ```
   > x = 1
   > # unchanged
   > ```
   >
   > After
   ```

   子リスト、コード、複数段落を含む `<li>` も一つの文字列になります。「この境目で切る」「リストは項目ごと」「引用は中の段落ごと」「コードは単位にしない」は、そのままでは同時に実現できません。文字列化後に構造を再解析する契約もありません。

   `<p>first<br>second</p>` は `first··\nsecond` になりますが、このハード改行を保護・検査する規定もありません。訳文が一行になっても、列挙された検査には違反しません。

   根拠：[設計案:77](C:/Works/info-hive-dev/docs/plans/wiki-web-ingest-deterministic-2026-11-13.md:77)、同81〜88行。[Converter:727](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py:727)、同749〜770行、667〜670行。上記の現行出力は実行で確認しました。

3. **【重大】表の `|` 禁止は、正しい原文維持を誤りとして止める。**

   `<td>A | B</td>` は現行 Converter によって `A \| B` になります。この文字列を維持したセルにも `|` があるため、設計の検査では拒否されます。エスケープ済みの `|` を認める例外は書かれていません。

   コードに含まれる `|` は印に隠せるとしても、通常の文章に含まれる `|` は保護対象にありません。「訳さず組み立てれば現行出力と一致する」という試験条件と、検査条件が食い違います。

   根拠：[設計案:130](C:/Works/info-hive-dev/docs/plans/wiki-web-ingest-deterministic-2026-11-13.md:130)、同210行。[Converter:829](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py:829)。現行出力を実行で確認しました。

4. **【重大】雑音判定が本文を削除し、文字列だけの削除記録では復元に必要な構造が定まらない。**

   現行処理では、次の本文が消えます。

   ```html
   <section id="cookie-example">
     <p>This is the API description.</p>
     <pre>set_cookie()</pre>
   </section>
   ```

   `cookie` が `NOISE_WORDS` にあるためです。実行すると本文・コードとも失われました。class/id の語は、サイトの部品名だけでなく記事の節名にも使われます。

   追加予定の文字列規則にも同じ問題があります。タグ API の説明で、本文中に独立した `[タグ一覧](https://example.org/tags/)` があれば、記載条件上は雑音になります。UI 操作の解説でボタンの文言を一段落として引用する場合も同様です。

   `restore` はありますが、保存すると明記されているのは「規則名と元の文字列」です。元の挿入位置、要素の種類、画像・コードとの対応、復元後の翻訳単位をどう扱うかは未定義です。復元できるという主張を、この記録形式からは確認できません。

   根拠：[設計案:149](C:/Works/info-hive-dev/docs/plans/wiki-web-ingest-deterministic-2026-11-13.md:149)、同153〜159行。[現行の判定:294](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py:294)、同217〜223行。

5. **【重大】`stage` 時点の存在確認では、`apply` による既存 raw の上書きを防げない。**

   次の手順が成立します。

   1. A がスラッグ `x` を `stage` する。この時点では raw がない。
   2. B が同じスラッグを取り込み、raw を確定する。
   3. A が翻訳を終えて `apply` する。

   設計では再取得判定を `stage` 時点で済ませます。確定時の再確認や排他の規定がないため、B の確定済み raw を保護する根拠がありません。現行 `write_outputs()` は `os.replace()` で保存先を置き換えます。

   また、本文と複数の画像を一時名から順に変更しても、全体が原子的になるわけではありません。画像の配置途中でプロセスが強制終了すると、本文と assets の整合は保証されません。現行の例外時ロールバックも、強制終了では実行されません。

   根拠：[設計案:121](C:/Works/info-hive-dev/docs/plans/wiki-web-ingest-deterministic-2026-11-13.md:121)、同123行。[保存処理:1019](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py:1019)、同1030〜1038行。[ADR-0004:28](C:/Works/info-hive-dev/docs/adr/0004-raw-holds-translated-web-pages.md:28)。

6. **【重大】分割した `fill` が、どの取得結果に対する訳なのかを識別できない。**

   単位 ID はページごとに `u0001` から振り直されます。一方、`fill` に取得世代や `source_sha256` を持たせて照合する規定がありません。

   再現条件は、原文 A の `fill-001.json` が残った状態で同じスラッグを原文 B として再 `stage` し、B の残りの単位を `fill-002.json` に書く場合です。ID と印の配置が同じなら、重複・未知 ID・欠落の検査だけでは、A と B の訳の混在を検出できません。

   **既存 `fill` が残ることは仮定です。** 再 `stage` 時の扱い自体が未定義で、実際の採否は未実装のため確かめられません。ただし、列挙された検査には取得世代の照合がありません。分割ファイル間で `language_override` や `translated_by` が異なる場合の統合規則もありません。

   根拠：[設計案:67](C:/Works/info-hive-dev/docs/plans/wiki-web-ingest-deterministic-2026-11-13.md:67)、同92行、98〜117行、127〜133行、163行。

7. **【重大】画像の出現と保存ファイルを同一視しており、削除と補足の対応が崩れる。**

   同じ URL の画像を二度置くと、現行処理は保存ファイルを共有します。実行では、二つの画像の `path` がともに `assets/review-example/review-example-01.png` となり、ファイルは一つでした。

   設計の `"images": {"01": ...}` が保存番号を指すなら、二つの出現に別々の判断を書けません。出現番号を指すとしても、一方を飾りとして「行とファイル」を削除すれば、残した出現の参照先が消えます。参照数による削除条件は書かれていません。

   引用やリスト内の画像についても、単純に直後へ `> ...` を挿入すると、元の引用の深さやリストの字下げと一致しません。

   根拠：[設計案:107](C:/Works/info-hive-dev/docs/plans/wiki-web-ingest-deterministic-2026-11-13.md:107)、同167〜169行。[画像の共有処理:1127](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py:1127)、同1156〜1162行。

8. **【重大】未取得画像に対して、正当な完了状態を表せない。**

   取得失敗、`--no-images`、`--max-images` 超過では、現行処理は画像を `images` に残し、`path: ""` と状態を返します。現行ワークフローは「見られないので補足を書かない」と明記しています。

   設計は全画像に「補足か飾り」の判断を要求します。未取得の本文図はどちらにも当てはまりません。規則を満たすには、見ていない図の補足を作るか、本文図を飾りとして削除することになります。

   根拠：[設計案:131](C:/Works/info-hive-dev/docs/plans/wiki-web-ingest-deterministic-2026-11-13.md:131)。[取得結果:1132](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py:1132)、同1141〜1149行。[現行手順:118](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/ingest-workflow.md:118)。

9. **【重大】防止対象の一部が、検出も拒否も保証されていない。**

   `Event Sourcing` の訳や `<>` の追加は、検出されても警告だけで書き込まれます。理由を書いて受け入れる判断をモデルに戻しているため、「モデルの能力に頼らず防ぐ」という目的を満たしません。

   検出範囲にも穴があります。比較で実際に問題となった `Unix`、`Greenwich`、`Brier` は、CamelCase でも複数の大文字開始語でもありません。記載された固有名詞検査の対象外です。元の単位に既に `<>` が一度あれば、同じ記号を別の箇所へ追加しても集合比較では増加を検出できません。

   根拠：[設計案:135](C:/Works/info-hive-dev/docs/plans/wiki-web-ingest-deterministic-2026-11-13.md:135)、同137〜143行。[比較レポート:50](C:/Works/info-hive-dev/docs/research/wiki-ingest-model-comparison-2026-11-13.md:50)。[ADR-0004:25](C:/Works/info-hive-dev/docs/adr/0004-raw-holds-translated-web-pages.md:25)。

## 崩れる前提

- **印の保持＝Markdown の保持。** 括弧の削除、印の入れ替え、訳文によるコードフェンスの追加で崩れます。
- **一ブロック＝一つの翻訳対象。** 引用やリストがコード・画像・子ブロックを内包すると崩れます。
- **class/id や URL の形から本文と雑音を区別できる。** 記事が Cookie、タグ API、UI 操作そのものを説明すると崩れます。
- **同じ単位 ID は同じ原文を指す。** 再取得や分割位置の変更で崩れます。
- **画像番号と保存ファイルが一対一。** 同じ画像 URL の再利用で崩れます。
- **取得時に保存先を確認すれば確定時も安全。** 翻訳中の別セッションの取り込みで崩れます。
- **raw の Markdown のハッシュで原本全体の不変性を確認できる。** `raw/assets/` の画像だけが変更・削除された場合は崩れます。設計の照合対象は Markdown ファイルだけです。

## 見落としと軽微な問題

- **【軽微】言語判定の「コードを除く」が入れ子では成立しません。** 現行 `strip_code()` は引用内のフェンスを除去できません。日本語の説明と英語コード100行からなる引用で、本文だけの `ja_ratio` は `1.0`、現行処理後は `0.002` となりました。`source_lang` が空なら、設計は日本語ページを翻訳対象にします。根拠：[現行処理:919](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py:919)、[設計案:163](C:/Works/info-hive-dev/docs/plans/wiki-web-ingest-deterministic-2026-11-13.md:163)。

- **【軽微】最上位の題名は `blocks()` に含まれません。** 現行処理は選んだ題名をスキップし、最後に `# {title}` として別途出力します。単位一覧だけを訳す場合、この見出しの翻訳経路がありません。根拠：[Converter:709](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py:709)、同1184行。

- **【軽微】作業場所の削除は成功時しか規定されていません。** 中断・失敗した取り込みの原文は無期限に残り得ます。一時保存そのものを ADR 違反とは断定しませんが、「取り込みのあいだだけ」という説明を保証する寿命の規定はありません。ADR の「原文を保存しない」を raw だけに限定する解釈も、既存 ADR の明文とは一致しません。根拠：[設計案:73](C:/Works/info-hive-dev/docs/plans/wiki-web-ingest-deterministic-2026-11-13.md:73)、[ADR-0004:23](C:/Works/info-hive-dev/docs/adr/0004-raw-holds-translated-web-pages.md:23)。

- **【軽微】成功時に削除判断の記録も消えます。** `drop`、`drop_marks`、`removed_by_rule` は削除対象の作業場所にあります。「記録で比べられる」とする一方、その記録を永続化する保存先はありません。根拠：設計案69〜73行、117行、157行、199行。

- **【軽微】印の検査条件の表現が矛盾しています。** 「集合として一致」だけでは二重使用を検出できません。括弧内と試験項目では二重使用を拒否しており、要求が一致していません。根拠：設計案128行、211行。

## 検証した事実

- **一致：** `Converter.blocks()` は文字列の配列を返します。ただし、リスト・引用は内部構造を含んだ一要素になります。
- **一致：** 表内の画像は、現行 Converter が既に表の下へ移します。表セル内の画像をその位置へ復元する問題は、現行出力にはありません。
- **食い違い：** 印の一致は、リンクの存在・文言との対応を保証しません。同梱 Markdown 解析器で確認しました。
- **食い違い：** 「コードを除いた言語比率」は引用内のコードでは成立しません。
- **一致：** `.wiki-cache` はページ集合から除外されます。ただし `iter_page_files()` 自体は `rglob()` で巡回してから除外するため、「走査しない」は正確には「ページとして採用しない」です。根拠：[wiki_pages.py:29](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:29)、同52〜59行。
- **確かめられず：** 新しい `apply` の実際の拒否動作。`wiki_webraw.py` は現時点の対象ディレクトリにありません。

実行検証はメモリ内で行い、取得と保存を差し替えました。リポジトリのファイルは変更していません。

## 崩せなかった点

- コードを翻訳入力から完全に除外できた場合、モデルがそのコード本文を直接翻訳する経路はありません。
- 元の画像行をモデルに書かせない構成では、図の説明を既存 alt に移す経路はありません。
- 印の欠落・未知の印・二重使用をそれぞれ検査する要求自体は明記されています。問題は、その検査だけでは構文と対応関係まで保証できない点です。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
