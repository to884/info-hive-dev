## 判定

**条件付きで採用可。確信度：高。** 8回目の重大な反例は再発を確認できなかった。ただし、再開時の写しの同一性判定、`freeze.images` のalt、表内の診断位置には具体的な不一致が残る。

## 致命的・重大な欠陥

なし。今回の検証では、該当する重大度の反例は得られなかった。

## 崩れる前提

- **同じ画像パスなら、取得記録のどの出現を使ってもよい。** 同じ画像URLを異なるaltで複数回使うと崩れる。出現ごとのaltが、最後の出現のaltに置き換わる。
- **取得日時と原文ハッシュを含むfrontmatterが同じなら、同じ取得結果である。** 同じ秒に同じHTMLを、画像取得などの条件を変えて再取得すると崩れる。本文が違ってもfrontmatterが一致する。
- **表のセル内の診断にも、ファイルの行番号を付けられる。** 通常の`td_open`には`map`がなく、`inline`の`map`も木に引き継がないため、セル内の誤りは`line: null`になる。

## 見落としと軽微な問題

### 1. 【軽微】`freeze.images` が、残った画像に削除済みの出現のaltを付ける

実物の`wiki_fetch.build()`から、次のHTMLを取得した。

```html
<img src="i.png" alt="Before treatment" width="300" height="200">
<p>Middle.</p>
<img src="i.png" alt="After treatment" width="300" height="200">
```

取得結果では、同じ保存先を参照する2件が、それぞれ正しいaltを持つ。

```text
16行目: Before treatment
20行目: After treatment
```

無編集で`freeze`すると、出力は次になる。

```text
16行目: After treatment
20行目: After treatment
```

さらに後者の画像行だけを削除すると、`freeze`は終了コード0になり、**残した前者を`alt: "After treatment"`として返す。** W7が参照する一覧に、削除した出現のaltが残る。

根拠：

- `info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:233`：取得記録を`path`で辞書化し、最後の出現で上書きする。
- 同`:236–239`：木に残った画像の`_alt`を使わず、その辞書の記録を返す。
- `info-hive-wiki/commands/ingest.md`のW7：この一覧を補足の入力にする。
- `tests/wiki/test_wiki_web_check.py:1001`：画像一覧の試験は異なるパスの画像であり、共有パス・異なるaltを確かめていない。

### 2. 【軽微】同じ秒の再取得では、rawと異なる写しを再開可能と判定する

取得時刻を同じ秒に固定し、実物の`build()`で次を再現した。ファイル入出力だけをメモリに置き換えている。

1. 画像を含むHTMLを通常取得し、ローカル画像を参照するrawを作る。
2. 同じHTMLを`--force --no-images`で取り直す。
3. 写しの完成後、`write_outputs()`を失敗させる。
4. 同じHTMLを通常取得する。

手順3の後は、rawがローカル画像、写しが外部画像と`（未取得）`を持つ。しかし手順4は次を返した。

```json
{
  "unchanged": true,
  "work_dir": true,
  "work_stage": "fetched"
}
```

**rawと`fetched.md`の本文は不一致、frontmatterは一致。** 続く`freeze`は終了コード1になる。8回目で直した「別の取得の写しでは再開させない」は、原文ハッシュが変わる場合には成立するが、この場合には成立しない。

根拠：

- `info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py:1363`：取得日時は秒精度。
- 同`:1360–1369`：画像取得条件はfrontmatterに含まれない。
- `info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:260–269`：同一性をfrontmatterだけで判定する。
- `tests/wiki/test_wiki_web_check.py:1132`：再開の回帰試験は、HTML自体が異なる2世代だけを扱う。

### 3. 【軽微】通常の表セル内の誤りには行番号が出ない

次を無編集で`freeze`した。

```markdown
| A | B |
|---|---|
| 1 | `SELECT 1;` [safe](https://safe.example/) |
```

訳の段で`SELECT 1;`だけを`DROP TABLE users;`に変更すると、検出はするが、診断は次になる。

```json
{
  "kind": "code_span",
  "line": null,
  "source": " safe",
  "raw": " safe"
}
```

変更したコード自体も診断の`source`・`raw`には出ない。この例では、コードを変えたセルの位置と内容の両方を出力から特定できない。「長いページの訳し方」の、診断行番号を使ってrawを直す手順が、通常の表セルには適用できない。

根拠：

- `_vendor/markdown_it/rules_block/table.py:206–214`：行の`map`は`inline`に付き、`td_open`には付かない。
- `wiki_rawcheck.py:291`、`:316`：節点の行番号は開始トークンから取り、`inline`からは引き継がない。
- 同`:749`、`:767–774`：位置はセル節点から、表示内容はコードを除いた文字列から取る。
- `tests/wiki/test_wiki_web_check.py:987`：行番号の試験は段落であり、表セルを扱わない。

## 検証した事実

- **一致：** `impl-9.submodule.diff`に含まれる`wiki_rawcheck.py`は、実ファイルと一致した。
- **一致：** `wiki_pages.new_parser()`は同梱のmarkdown-it-pyを使い、`commonmark`、HTML無効、表有効である。
- **一致：** 表の余剰セル内でも、インラインのコードと参照形式のリンクが解析される。引用内のリスト、リスト内の引用に置いた表でも確認した。
- **一致：** 8回目の反例であるエスケープ削除、行頭パイプ省略による余剰セル追加、別の列数の表を使った対応の取り違えは拒否された。リスト間の雑音削除は通った。
- **一致：** 警告のある`check --finish`は写しを残し、修正後に再検査できる。`--finish --accept-warnings`は写しを消す。
- **食い違い：** 「番号付きリストの2項目目以降の番号は`info`として照らす」は、`freeze`には当てはまるが`check`には当てはまらない。`2. Two`を`999. Two`に変えても、`check`は誤り・警告なしだった。ただし、閲覧時の番号表示は変わらない。
- **試験結果：** 指定された2ファイルの111試験を、ファイル入出力をメモリに置き換えて実行し、110件成功。実ジャンクションを作る1件は除外した。通常のファイル入出力、物理的な名前変更の原子性、実ネットワーク取得は、この読み取り専用環境では確かめていない。
- リポジトリのファイルは変更していない。

## 崩せなかった点

- 表の行のセル数を、木の対応の中で守る処理。見出し列数を超えるセルと、不足するセルも含む。
- 表規則の差し替えによる、今回試した範囲のトークン順序・レベル・入れ物内の行抽出・参照リンク解析。
- リストを項目に開いたことによる、削除段階の入れ子変更・項目の並べ替えの見逃し。
- 引用・リスト内の補足、原文の補足形式の引用の保持、補足内の画像拒否、複数段落の補足。
- 既存の雑音規則の対照例、`--html-file`の相対URL解決と非UTF-8拒否。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
