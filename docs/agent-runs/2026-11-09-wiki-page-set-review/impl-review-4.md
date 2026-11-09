## 判定

**却下。確信度：高。** コード内のリンクを拾う反例、本文のリンクを消す反例、既存ページを収集対象から落とす後退が残っています。セクション分割後だけコード内の言及が矛盾候補になる経路も再現しました。

## 致命的・重大な欠陥

比較実行にはローカルの markdown-it-py **4.2.0** を使用しました。以下の Markdown の期待動作は **3.0.0 の関連ソースにも照合**していますが、3.0.0 本体での実行は未確認です。収集・判定への波及は、ファイル入出力だけをメモリ上に置き換えて確認しました。

### 1. 【重大】引用の継続判定を誤り、字下げコードからリンクを拾う

反例。2行目の先頭は半角空白4個です。

```markdown
> > 引用
    - [[entity]]
```

実装は `["entity"]` を返します。閲覧側では2行目が引用外の字下げコードとなり、抽出結果は `[]` です。次の形でも再現します。

```markdown
> 引用
    >
    [[entity]]
```

`scan_blocks()` は、コンテナが一致しなくても、段落が開いていて `_starts_block()` が偽なら、その行を段落の遅延継続にします。字下げされた印をこの条件で処理すると、閲覧側が引用を終了する場面を見落とします。

この本文を持つ2ページで、lint・search・graph は各1リンク、stats は合計2リンクと数えました。`entities/entity.md` を加えると、**コード内でしか言及していない2ページから矛盾候補が1組できました**。

根拠：[wiki_pages.py:381](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:381)、[3.0.0 の引用処理](https://github.com/executablebooks/markdown-it-py/blob/v3.0.0/markdown_it/rules_block/blockquote.py)。タブや閉じないフェンスを使わない反例です。

### 2. 【重大】リンクのタイトル内のバッククォートが、外側のコード判定を壊す

反例：

```markdown
[資料](https://example.com "記号 `") と `[[entity]]`
```

実装は `["entity"]`、閲覧側は `[]` です。

`_mask_code_spans()` は、Markdown リンクのタイトルも通常の本文として走査します。タイトル中のバッククォートと、後続するコードスパンの開きバッククォートを対応させるため、実際のコード内にある `[[entity]]` が露出します。

逆方向の誤りもあります。

```markdown
[資料](https://example.com "記号 `") と [[entity]] と `code`
```

こちらは、実装が `[]`、閲覧側が `["entity"]` です。本文のリンクが消えます。

最初の反例を2ページに置くと、stats は2リンクと数え、矛盾候補も1組できました。設計が範囲外としている「リンクの文字の中の wikilink」とは異なり、**壊れるのは通常のリンクの外側**です。

根拠：[wiki_pages.py:562](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:562)、[同:623](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:623)。[3.0.0 のリンク処理](https://github.com/executablebooks/markdown-it-py/blob/v3.0.0/markdown_it/rules_inline/link.py)はタイトルを属性として読み、リンクのラベルだけをインライン解析します。

### 3. 【重大】Unicode の行区切り文字で、分割後とキャッシュ再利用後の本文が変わる

正確な入力を Python の表記で示します。

```python
body = "説明 `\u2028# 見出し\u2028[[entity]]\u2028終了`"
```

U+2028 は Markdown の改行ではありません。本文全体ではバッククォートが対応し、`extract_wikilinks(body)` は正しく `[]` になります。

しかし `split_sections()` は `str.splitlines()` を使うため、U+2028 でも分割します。架空の見出しで切られた次の本文を再解析すると、`["entity"]` になります。

```text
[[entity]]
終了`
```

確認した結果：

- 本文全体のリンクは、lint・search・graph とも `[]`、stats は0件。
- 同じ本文の2ページから、`contradiction_pairs()` は1組を生成。
- 初回収集の `body` から再抽出すると `[]`。
- キャッシュ再利用時は `cache_page_body()` が区切りを LF に変え、`body` からの再抽出が `["entity"]`。保存済みの `links` は `[]` のまま。

`splitlines()` の使用自体は基準版にもありますが、今回の「セクションに分けても同じリンクを拾う」という保証は成立していません。

根拠：[wiki_search.py:319](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_search.py:319)、[同:181](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_search.py:181)、[wiki_pages.py:67](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:67)。[3.0.0 の改行正規化](https://github.com/executablebooks/markdown-it-py/blob/v3.0.0/markdown_it/rules_core/normalize.py)も対象を CR・LF に限定しています。

### 4. 【重大】Windows で従来収集できた `.MD` のページが消える

既存の wiki に次がある場合です。

```text
concepts/Upper.MD
concepts/current.md
```

`current.md` が `[[Upper]]` を参照しているものとします。

Windows の既定のパスマッチでは `rglob("*.md")` は `Upper.MD` も列挙します。基準版の収集関数には、その後で拡張子の大小文字を制限する条件がありません。今回の `is_page_path()` は `.endswith(".md")` を追加しているため、列挙済みのページを捨てます。

Windows のパスマッチと列挙結果をメモリ上で再現し、基準版の `collect_pages()` が `concepts/Upper.MD` を返し、今回の版が返さないことを確認しました。リンク切れになり、検索・`get_page` の対象からも消えます。

根拠：[wiki_pages.py:41](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:41)、基準コミット `c23ae5b` の `wiki_search.collect_pages()`。[設計:34](/C:/Works/info-hive-dev/docs/plans/wiki-page-set-and-links-2026-11-09.md:34)の「変わるのは……だけ」という変更範囲の説明にも反します。

### 5. 【重大】参照定義の先読みがコンテナ境界を越え、次の引用を消す

反例：

```markdown
- [資料]:
> [[entity]]
```

閲覧側では、未完成の参照定義を含むリストと、その次の引用になります。抽出結果は `["entity"]`。実装は `[]` を返します。

`_refdef_lines()` はコンテナが一致しない行に対して、ブロック開始を調べる**前に** `.lstrip(" >")` を行います。そのため引用の印が消え、`[[entity]]` を参照定義の URL として消費します。

lint・search・graph のリンクはいずれも消え、2ページに置いても stats は0件でした。

根拠：[wiki_pages.py:524](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:524)、[同:535](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:535)。[3.0.0 の参照定義処理](https://github.com/executablebooks/markdown-it-py/blob/v3.0.0/markdown_it/rules_block/reference.py)と[ブロック規則](https://github.com/executablebooks/markdown-it-py/blob/v3.0.0/markdown_it/parser_block.py)では、引用は参照定義を終了させる規則です。

## 崩れる前提

- **コンテナ不一致後の行は、簡単なブロック開始判定で遅延継続と区別できる。** 引用の継続行に字下げされた印が来ると崩れます。
- **段落全体のバッククォートを対応させれば、コードスパンが決まる。** リンクの URL・タイトルなど、インライン解析されない領域にバッククォートがあると崩れます。
- **セクション分割とリンク抽出が同じ「行」を使っている。** U+2028 など、`splitlines()` だけが区切る文字で崩れます。
- **`.md` の明示的な末尾検査は、従来の列挙と同じである。** Windows の `.MD`・`.Md` で崩れます。
- **コンテナの印を取り除いてから参照定義の終了を調べてもよい。** 次の引用の印まで取り除くと、本文を定義として消費します。
- **固定語彙による大量比較が、通常の構文境界も保証する。** 今回の10試験は通りましたが、上記の反例は残りました。

## 見落としと軽微な問題

- **【軽微・既存差の残存】見出し内のリンクは判定レイヤーから落ちます。**  
  `# [[entity]]\n本文` を2ページに置くと、lint・search・graph は各1リンク、stats は2リンクですが、矛盾候補は0組です。[wiki_decide.py:553](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_decide.py:553)が見るのはセクション本文だけです。一方、[test_sections_keep_links:379](/C:/Works/info-hive-dev/tests/wiki/test_page_set.py:379)は見出しのリンクも足して比較するため、実際の判定経路との違いを隠しています。今回新しく生じた差ではありません。

- **【軽微】生成試験の入力範囲に今回の境界条件がありません。**  
  [LINE_KINDS:343](/C:/Works/info-hive-dev/tests/wiki/test_page_set.py:343)には、バッククォートを含む通常リンクのタイトル、Unicode の行区切り、引用に続く字下げされた印がありません。拡張子の大小文字もページ集合の固定例にありません。CI の実行環境は [Ubuntu のみ](/C:/Works/info-hive-dev/.github/workflows/wiki-mcp.yml:34)です。

- **【軽微】変更履歴と手順書の保証が実装を上回っています。**  
  [CHANGELOG.md:18](/C:/Works/info-hive-dev/info-hive-wiki/CHANGELOG.md:18)の「コード内を数えなくなった」と、[lint-workflow.md:36](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/lint-workflow.md:36)の「コードに入れればリンク切れとして挙がらない」は欠陥1・2で成立しません。記載された例外だけでは、この範囲を説明できません。

## 検証した事実

| 主張 | 結果 |
| --- | --- |
| サブモジュールの基準は `c23ae5b`、作業版は0.9.0 | 一致 |
| 固定比較例は52件 | 一致。`MARKDOWN_CASES` と `CODE_BODY` の合計 |
| 過去のレビューの固定反例が修正された | 今回の固定例試験では一致 |
| 意図した通常のページ集合 | メモリ上の全固定例で lint・search・graph が一致。stats も8ページ |
| 旧名の再輸出、`SERVER_FILES` への追加 | 確認した対象では一致 |
| lint・stats の標準ライブラリだけでの読み込み | `python -S` で成功 |
| schema 3 のパースキャッシュを破棄する | 一致。読み込み結果は `{}` |
| CI が markdown-it-py 3.0.0 を指定する | 一致 |
| グラフの再生成手順が記載されている | 一致 |

ファイルを作らない10試験は通過しました。Markdown 比較の4試験は、版によるスキップを手動解除して **4.2.0 に対して実行した結果**です。

3.0.0 本体での比較、全試験、評価ゲート、実際の MCP 接続は**確かめられず**。リポジトリのファイルは変更していません。

## 崩せなかった点

- 過去の固定反例である、区切り線後のコード、表セル境界、全角空白、複数行の参照タイトル、禁止 URL の復号。
- 固定例に含まれる複数行コードスパン、escape、長さの異なるフェンス。
- 確認した旧名の再輸出と、`SERVER_FILES` への `wiki_pages.py` の追加。
- NFC → `casefold()` → NFC の比較、および正規化だけが違う名前の扱い。
- 旧キャッシュの拒否と、既存グラフの再生成を利用者に伝える記載。

使用した MCP サーバー: codex_apps（GitHub）  
使用した Agent Skills: なし
