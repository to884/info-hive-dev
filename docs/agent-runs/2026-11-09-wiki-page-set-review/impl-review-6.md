## 判定

**却下。確信度：高。** 新たにページとして扱う `.MD` ファイルを、Linux の MCP 索引が変更検出できない。ページの集合を統一しても、その更新が MCP に届かない。

## 致命的・重大な欠陥

### 1. 【重大】Linux では `.MD` ページの追加・更新・削除が MCP 索引に反映されない

新しい `iter_page_files()` は `*.[mM][dD]` を走査するが、MCP の `stat_signature()` は `*.md` のままである。

再現条件・手順：

1. Linux で MCP から wiki を検索し、初回の `refresh()` を済ませる。
2. `concepts/New.MD` を追加する。他の `.md` ファイルは変更しない。
3. 再び MCP から検索する。

署名が変わらず、`refresh()` は `{"changed": False}` で終了する。新ページは検索にも `get_page` にも現れない。既存の `.MD` を編集した場合も索引とリンク情報が古いままになる。`get_page()` は本文だけをディスクから読み直すため、**新しい本文と古い `links`・メタデータ・セクション情報を混ぜて返す**。削除の場合は、収集済みページが残り、本文の読み出しが失敗する。

根拠：

- [wiki_pages.py:52](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:52)：新しい走査パターン。
- [wiki_index.py:817](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_index.py:817)：変更検出は `*.md`。
- [wiki_index.py:848](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_index.py:848)：署名が同じなら収集しない。
- [wiki_index.py:941](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_index.py:941)：本文は再読込し、他の情報は収集済みデータを返す。

**検証結果：食い違いを確認。** Linux の大文字・小文字を区別する glob を模したメモリ上の root で、実際の `WikiIndex.refresh()` を実行した。`.MD` 追加後も `changed: False`、収集関数の呼び出し回数は初回の1回のままだった。Linux 実機での実行ではない。

設計の「`stat_signature` は変えない」という判断自体が、この反例と衝突する。

## 崩れる前提

- **「収集するページの変更は、既存の署名で検出できる」**  
  Linux で `.MD`・`.Md`・`.mD` だけを変更すると崩れる。新しい走査対象が、変更検出の対象に包含されていない。

- **「`heading_line_mask` が真なら、検索もそこで分割する」**  
  空の ATX 見出しで崩れる。詳細は次節。

- **「同梱コードの変更による再起動だけで、解析結果も更新される」**  
  版番号を変えずに同梱コードを修正した場合、`code_version` は変わるが、版番号だけから作る `PARSER_ID` は変わらない。パースキャッシュは引き継がれる。README の版更新手順に従う通常の更新では、この条件には当たらない。

## 見落としと軽微な問題

### 【軽微】空の ATX 見出しでセクション境界が食い違う

入力：

```markdown
# A
first [[x]]
#
second [[y]]
```

`heading_line_mask()` は `[True, False, True, False]` を返す。一方、`split_sections()` は途中の `#` で分割せず、`first` と `second` を同じ `A` セクションに入れる。

`_splits_section()` は空の見出しを認めるが、検索側の `HEADING_RE` は本文に `(.+?)` を要求するためである。

根拠：[wiki_pages.py:109](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:109)、[wiki_search.py:89](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_search.py:89)、[wiki_search.py:349](C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_search.py:349)。

**検証結果：食い違いを実行確認。** この反例ではリンクの総数は変わらない。現在のセクション試験はリンクの `Counter` だけを比較するため、境界の不一致を検出できない（[test_page_set.py:388](C:/Works/info-hive-dev/tests/wiki/test_page_set.py:388)）。

### 【軽微】設計書と試験の説明に、撤回した処理が残っている

設計書の「使う側の変更」の `wiki_decide.py` 行と `SectionTests` の説明は、セクション本文を読み直してリンクを拾うと記載している。実装は `section["links"]` を使う。5回目の指摘への対応表とは食い違う。

根拠：[設計書:60](C:/Works/info-hive-dev/docs/plans/wiki-page-set-and-links-2026-11-09.md:60)、[test_page_set.py:367](C:/Works/info-hive-dev/tests/wiki/test_page_set.py:367)、`wiki_decide.py` の `contradiction_pairs()`。

## 検証した事実

- **一致**：プラグインの版と変更履歴は、ともに `0.9.0`。
- **一致**：同梱版の読み込み場所、版、ライセンス3文書の存在を確認した。
- **一致**：既存の純粋な検証8テストが成功した。セクションのランダム比較6,000件を含む。固定の Markdown 52例も別途すべて成功した。
- **一致**：`mdurl/_url.py` の読み取り結果だけをメモリ上で変更すると、`code_version()` が変わった。
- **確かめられず**：PyPI 公表ハッシュと同梱ファイルの独立照合、実際の MCP・uv 環境での起動、大規模 wiki の性能測定。これらは成功したとは判断していない。

リポジトリのファイルは変更していない。

## 崩せなかった点

- 外部由来として扱った実際の `markdown_it`・`mdurl` のモジュール群を先に読み込ませても、同梱版へ置き換わった。この条件では、外部版が残って解析を変える経路は崩せなかった。
- 固定例とランダム例では、セクションの `links` の合計と `extract_wikilinks(headings=False)` は一致した。
- 同梱ファイルの変更を `code_version` が取りこぼす反例は得られなかった。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
