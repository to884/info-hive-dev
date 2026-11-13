## 判定

**却下。確信度：高。** Windows のパス解釈により、確定済み raw の画像を清掃対象にする経路があります。また、`drop_text` は正しい部分削除を表現できない場合があり、review-4 の指摘5を一般には解消していません。

新しい `wiki_webraw.py` は未実装です。以下では、実行確認した事実と、設計の規定から導いた結果を区別します。

## 致命的・重大な欠陥

1. **【重大】異なるスラッグが同じフォルダーを指し、確定済みの画像が清掃対象になる。**

   現行の `check_slug()` は `x` と `x.` を両方受け付けます。Windows の通常のパス解釈では、フォルダー名の末尾のピリオドが無視されるため、次のフォルダーはそれぞれ同じ場所を指します。

   ```text
   .wiki-cache/ingest/x/       .wiki-cache/ingest/x./
   raw/.ingest-tmp/x/          raw/.ingest-tmp/x./
   raw/assets/x/              raw/assets/x./
   ```

   一方、Markdown の名前は `x.md` と `x..md` になり、区別されます。フォルダーと確定判定の対応が崩れます。

   **反例の手順：**

   1. 画像を含むページをスラッグ `x` で確定する。`raw/x.md` と `raw/assets/x/` が存在する。
   2. スラッグ `x.` で別のページを stage する。前の作業場所は成功時に削除されているので、作業場所を作れる。
   3. `apply` は `raw/x..md` がないことを確認する。しかし、`raw/assets/x./` は既存の `raw/assets/x/` を指すため、「確定前の生成物」と判定して `clean` を案内する。
   4. 規定どおり `clean` すると、`raw/x.md` が参照する確定済みの画像フォルダーを削除する。

   同時実行も異常終了も不要です。同じ錠を順番に取得しても防げません。

   **前提：** 現行のスラッグ検査を維持し、設計に記載されたとおり、指定されたスラッグからパスを組み立てること。スラッグを正規化・拒否する追加規定は見つかりませんでした。

   **検証結果：食い違い。** `check_slug("x")` と `check_slug("x.")` の受理を実行確認しました。この環境で、既存ディレクトリ `info-hive-wiki` と `info-hive-wiki.` の `Path.samefile()` は `True` でした。清掃による削除自体は実行していません。

   根拠：[現行のスラッグ検査](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py:954)、[管理用パスの分離の主張](C:/Works/info-hive-dev/docs/plans/wiki-web-ingest-deterministic-2026-11-13.md:216)、[清掃対象の定義](C:/Works/info-hive-dev/docs/plans/wiki-web-ingest-deterministic-2026-11-13.md:249)、[清掃への誘導](C:/Works/info-hive-dev/docs/plans/wiki-web-ingest-deterministic-2026-11-13.md:256)。[root-causes-4.md の対応表9行](C:/Works/info-hive-dev/docs/agent-runs/2026-11-13-wiki-web-ingest-deterministic-review/root-causes-4.md:9)は、このパス同一性を扱っていません。

2. **【重大】本文にも現れる文言は、正しく雑音と判断しても `drop_text` で消せない。**

   次の日本語ページで、末尾の `共有` だけがサイトによって付加された共有文言であるとします。

   ```html
   <p>「共有」は操作名である。共有</p>
   ```

   正しい保存結果は次です。

   ```text
   「共有」は操作名である。
   ```

   この段落は一つの `text` です。`drop_text` に `共有` を指定すると、出現が2回あるため拒否されます。`共` と `有` に分割しても、それぞれ2回あり拒否されます。雑音部分だけに収まる、出現が1回の文字列はありません。

   本文側の文字まで含めれば一意にはできますが、必要な本文を削ります。ノード全体の削除でも本文を失います。タグがないため `drop_inline` は使えず、訳さないページなので訳文で置き換える経路もありません。

   **検証結果：食い違い。** 現行 Converter が上記を一つの段落として保持することと、雑音部分のすべての非空部分文字列が2回現れることをメモリ内で確認しました。拒否そのものは未実装ですが、設計はこの場合の拒否を明記しています。

   これは文字列検索の実装ミスではありません。削除対象の「出現」を指定できない判断形式の制約です。review-4 の元の反例は通せても、同じ構造の問題が残ります。

   根拠：[部分削除の規定](C:/Works/info-hive-dev/docs/plans/wiki-web-ingest-deterministic-2026-11-13.md:112)、[重複時に拒否する試験条件](C:/Works/info-hive-dev/docs/plans/wiki-web-ingest-deterministic-2026-11-13.md:339)、[root-causes-4.md の対応表12行](C:/Works/info-hive-dev/docs/agent-runs/2026-11-13-wiki-web-ingest-deterministic-review/root-causes-4.md:12)。現行の要求は、雑音を削り本文を残すことです：[ingest.md](C:/Works/info-hive-dev/info-hive-wiki/commands/ingest.md:36)。

## 崩れる前提

- **異なるスラッグ文字列は、異なるフォルダーを指す。** Windows で末尾がピリオドの場合に崩れます。文字列としての分離だけでは、ファイルシステム上の分離を保証できません。
- **対応する Markdown がなければ、その assets は未確定物である。** Markdown の名前は別でも、assets のフォルダーが別スラッグと同じ場所を指すと崩れます。
- **正しく削除したい雑音には、一意な部分文字列がある。** 本文が同じボタン名などを説明している場合に崩れます。
- **対象を一意に特定できない入力を拒否しても、必要な判断の表現能力は失われない。** 削除位置が分かっていても、その位置を判断データに書けないため崩れます。

## 見落としと軽微な問題

- **【軽微・試験仕様の未定義】HTML の表を読むパーサーが決まっていません。**

  設計は、ブロックを含むセルを HTML の表として保存し、「Markdown として読んだ結果」で構造の一致を確かめます。しかし、同梱の `wiki_pages.new_parser()` は `html=False` です。

  次を渡すと、表・段落・コードとして解釈されず、タグをエスケープした一つの段落になりました。

  ```html
  <table><tr><td><p>Before</p><pre><code>x = 1</code></pre></td></tr></table>
  ```

  HTML 対応の別の読み手なら成立し得るため、HTML 保存そのものの欠陥とは断定しません。ただし、既存パーサーを使う一致試験は失敗します。合否の意味が、読み手の未指定設定に依存しています。

  根拠：[HTML 表への描画](C:/Works/info-hive-dev/docs/plans/wiki-web-ingest-deterministic-2026-11-13.md:85)、[一致試験](C:/Works/info-hive-dev/docs/plans/wiki-web-ingest-deterministic-2026-11-13.md:328)、[同梱パーサーの設定](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:125)。

## 検証した事実

| 確かめた主張 | 結果 |
| --- | --- |
| 指定された設計、root-causes 全4本、review 全4本、ADR-0004、取り込みコマンド、ワークフロー、`wiki_fetch.py` の内容 | 読み取り済み |
| `x` と `x.` の受理、Windows 上の末尾ピリオドによるディレクトリ同一性 | 実行確認済み |
| 重複する雑音文言を含む段落と、その部分文字列の出現数 | メモリ内で確認済み |
| 同梱パーサーによる HTML 表の解釈 | 実行確認済み。タグが文字として表示される |
| `release_terms` と `drop_text` が永続記録に含まれる | 設計の記載と一致 |
| 旧 CLI の扱いについて、root-causes-3 と設計本文が一致する | 一致。どちらも stage と同じ動作 |
| 新しい `apply`・`clean`・錠・描画の実動作 | 確かめられず。`wiki_webraw.py` は存在しない |

実行検証は読み取りとメモリ内処理に限定し、ファイルは変更していません。

## 崩せなかった点

以下は、設計の契約を守って実装する前提です。

- review-4 の `x`／`x.lock` の衝突と、`x` のワイルドカードが `x.v2` を巻き込む直接の反例。
- `aria-hidden="true"` の可視式が、木に入る前に消える反例。
- 表セルの段落とコードブロックを保持できないという、review-4 の表現能力への指摘。5版には子ブロックを保持する契約があります。
- 一意に現れる末尾の共有文言は、`drop_text` で削除できます。
- `release_terms` と `drop_text` の判断が成功時に記録から失われる反例。
- 旧保存口による錠の迂回、錠の回収操作による競合、書きかけの Markdown の正式名での公開。
- 異なる `stage_id` の拒否、共有画像の参照に基づく保存、未取得画像への補足の強制回避。
- `Unix` の文頭への移動や、数字の列挙の句読点変更を誤りとして止める、過去の直接的な反例。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
