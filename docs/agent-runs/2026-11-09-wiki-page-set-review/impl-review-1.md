## 判定

**却下。確信度：高。** 字下げコードをリンクとして数える反例が残り、lint の偽のリンク切れと、コード例だけを根拠にした矛盾候補を再現した。表や全角空白を含む本文でも、閲覧とリンク抽出が一致しない。

## 致命的・重大な欠陥

1. **【致命】区切り線をリストと誤認し、字下げコードからリンクを拾う。**

   反例：

   ```text
   - - -
       [[entity]]
   ```

   `extract_wikilinks()` は `["entity"]` を返す。正しくは、区切り線に続く字下げコードなので `[]`。`* * *` でも再現する。

   原因は、[wiki_pages.py:181](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:181) でリストのコンテナを開いてから、同ファイル216行の `_THEMATIC_RE` を調べる順序にある。markdown-it-py 3.0.0 は [区切り線の規則をリストより先に適用する](https://raw.githubusercontent.com/executablebooks/markdown-it-py/v3.0.0/markdown_it/parser_block.py)。

   同じ本文を持つ `concepts/a.md` と `concepts/b.md`、参照先 `entities/entity.md` をメモリ上のファイルとして収集すると、lint・search・graph は両方から `entity` を抽出し、stats はリンク数を2と数えた。さらに [wiki_decide.py:553](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_decide.py:553) を通じて、**コード例しかない2ページが矛盾候補になった**。参照先を除くと、lint は偽のリンク切れを2件返した。

   **検証結果：食い違い。** 初回レビューの「コード内リンクを除外する」という必須条件は、別の入力で引き続き破れる。

2. **【重大】表のセル境界を越えてコードスパンを閉じ、実在するリンクを消す。**

   反例：

   ```markdown
   | ` | [[a]] | ` |
   | --- | --- | --- |
   ```

   実装は `[]`、markdown-it の抽出結果は `["a"]`。左右のバッククォートは別セルの文字であり、中央セルをコードにできない。

   [wiki_pages.py:295](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:295) は表全体を同じ段落として連結し、`_mask_code_spans()` に渡す。一方、[markdown-it-py 3.0.0 の表処理](https://raw.githubusercontent.com/executablebooks/markdown-it-py/v3.0.0/markdown_it/rules_block/table.py) はセルごとに独立した `inline` トークンを作る。

   次のように別行にバッククォートがある場合も、実装は `["b"]`、閲覧側は `["a", "b"]` になる。

   ```markdown
   | A | B |
   | --- | --- |
   | ` | [[a]] |
   | ` | [[b]] |
   ```

   **検証結果：食い違い。** 設計に列挙された「残る食い違い」に表の境界は含まれていない。

3. **【重大】全角空白だけの行を空行とみなし、本文のリンクをコードとして捨てる。**

   正確な入力を Python の文字列表現で示す：

   ```python
   "説明\n\u3000\n    [[visible]]"
   ```

   実装は `[]`、markdown-it は `["visible"]`。全角空白の行は段落を終わらせないため、最後の字下げは段落の継続になる。

   [wiki_pages.py:198](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:198) の `not rest.strip()` が U+3000 も空行扱いし、`para = False` にする。直後の行が202行でコード扱いされる。CommonMark の空行は空白 U+0020 とタブだけで構成される行であり、[3.0.0 の空白判定も両者に限定される](https://raw.githubusercontent.com/executablebooks/markdown-it-py/v3.0.0/markdown_it/common/utils.py)。

   **検証結果：食い違い。** 日本語入力で混入しうる全角空白によって、通常のリンクが被リンク・検索結果の `links`・グラフから消える。

4. **【重大】参照リンク定義のタイトルを本文として数える。**

   反例：

   ```markdown
   [ref]: https://example.com "[[hidden]]"

   [[visible]]
   ```

   実装は `["hidden", "visible"]`、閲覧側は `["visible"]`。定義のタイトルは本文の `text` トークンではない。

   [wiki_pages.py:222](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:222) は参照リンク定義を区別せず通常の段落として扱う。[markdown-it-py 3.0.0 の参照定義処理](https://raw.githubusercontent.com/executablebooks/markdown-it-py/v3.0.0/markdown_it/rules_block/reference.py) は、通常設定では本文トークンを生成せず定義を環境に保存する。

   **検証結果：食い違い。** 本文に現れないリンクから、リンク切れや `mentions` が生成される。

5. **【重大】文字参照を復号しないため、閲覧と異なるページへ解決する。**

   | 入力 | 実装の抽出 | 閲覧側の抽出 |
   | --- | --- | --- |
   | `[[R&amp;D]]` | `["R&amp;D"]` | `["R&D"]` |
   | `&#91;&#91;a]]` | `[]` | `["a"]` |

   [wiki_pages.py:319](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:319) はバックスラッシュの escape だけを除き、文字参照はそのまま残す。[CommonMark の文字参照](https://spec.commonmark.org/0.30/#entity-and-numeric-character-references) は `html=False` でも本文の文字として復号される。

   `R&D.md` が存在すると、閲覧は解決できるのに lint は `R&amp;D` をリンク切れとして扱う。これは設計に明記された強調・画像などの除外事項には当たらない。

   **検証結果：食い違い。**

## 崩れる前提

- **「引用・リスト・段落を追えば、コード範囲も一致する」**  
  区切り線とリストの優先順位で崩れる。誤ったコンテナが後続行の字下げを消費する。

- **「同じ段落番号の行は、まとめてインライン解析できる」**  
  表のセル・行は独立した解析範囲であり、相互にコードスパンを閉じられない。

- **「`str.strip()` で空になる行は Markdown の空行である」**  
  全角空白や NBSP で崩れる。Python と CommonMark の空行判定は異なる。

- **「コードを除いて escape を外せば、本文の `text` トークンを再現できる」**  
  参照リンク定義と文字参照で崩れる。

- **「ランダム比較の食い違いが0.1%未満なら、通常の本文にも適合する」**  
  入力分布にない構文には保証が及ばない。今回の反例がある実装でも、既存のランダム比較テストは通った。

## 見落としと軽微な問題

- **【軽微】ファイルとディレクトリをまたぐ衝突について、設計と実装が逆。**  
  [計画70行](/C:/Works/info-hive-dev/docs/plans/wiki-page-set-and-links-2026-11-09.md:70) は `Foo.md` と `foo.MD/` を挙げないと明記する。しかし、

  ```python
  case_only_duplicates(["Foo.md", "foo.MD/x.md"])
  ```

  は `{"kind": "dir", "paths": ["Foo.md", "foo.MD"]}` を返した。[wiki_pages.py:399](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:399) は異種の組も報告する。

- **【軽微】検索の収集処理のコメントが実装と矛盾する。**  
  [wiki_search.py:253](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_search.py:253) は「`.` で始まるディレクトリは含めない」とするが、実装と設計は `.NET/` や `.archive/` を含める。

- **試験の見落とし。**  
  [test_page_set.py:247](/C:/Works/info-hive-dev/tests/wiki/test_page_set.py:247) の生成語彙には、全角空白・文字参照・参照リンク定義がない。表もセル境界を確かめる固定例がなく、ランダム比較は最大4件の不一致を許容する。`contradiction_pairs()` の実呼び出しも新しい試験にはない。

- [CHANGELOG.md:18](/C:/Works/info-hive-dev/info-hive-wiki/CHANGELOG.md:18) と [upgrade.md:24](/C:/Works/info-hive-dev/info-hive-wiki/commands/upgrade.md:24) の「コード内を数えなくなった」という説明は、欠陥1の入力では成立しない。

## 検証した事実

- サブモジュールの HEAD は `c23ae5b`、作業ツリーの `plugin.json` は0.9.0。**一致**。
- 上記の実装出力と、lint・search・graph・stats・矛盾候補への波及を、ファイル入出力をメモリ上に置き換えて確認した。リポジトリは変更していない。
- ローカルで利用できた markdown-it-py は **4.2.0**。本文のトークン比較はこの版で実行し、3.0.0 の関連ソースと仕様にも照合した。**3.0.0 自体での実行は確かめられず**。
- 新しい試験のうち、MarkdownIt比較2件、再輸出2件、ファイルを作らない重複判定3件の計7件は通った。全試験・評価ゲートは未実行。
- 通常の UTF-8 ページでは、lint・search・graph の収集集合と stats のページ数は一致した。
- 隔離した標準ライブラリ環境で `wiki_lint` と `wiki_stats` を import できた。

## 崩せなかった点

- 初回レビューの固定反例である、複数行コードスパン、4連フェンス、引用・入れ子リスト内フェンス。
- `PARSE_CACHE_SCHEMA = 4` による旧キャッシュの破棄。メモリ上で schema 3 から再解析させ、次回のキャッシュ利用でもリンクとセクションが一致した。
- 確認した既存名の再輸出と、`SERVER_FILES` への `wiki_pages.py` の追加。
- NFC → `casefold()` → NFC の比較、および正規化だけが違うファイルを `case_only_duplicates` に混ぜない処理。
- 既存グラフの再生成が必要であることは、変更履歴とアップグレード手順に記載されている。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
