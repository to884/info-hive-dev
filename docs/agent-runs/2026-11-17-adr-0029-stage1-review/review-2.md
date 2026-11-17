## 判定

**却下。確信度：高。** wiki 側に、リンクの記事を直接読んで置き換える経路と、拒否・判定不能の情報を消す経路が残る。raw 側や書き込み部品の未実装は、この判定に含めていない。

## 致命的・重大な欠陥

1. **重大・C：評価ループが、リンクの索引とログを読み、リンクそのものを置き換える。**

   `index.md`、`log.md` を外部ファイルへのリンクにして、`wiki_evolve_loop.py` の評価ループを実行する。`publish_learning()` は両方を直接 `read_text()` し、その本文を含むデータを同じ名前へ `atomic()` で置く。`article_path()` もリンク警告も通らない。

   メモリ上の再現では、両記事の本文が読み取られ、その本文を含む値が `atomic()` に渡され、標準エラーは空だった。`atomic()` は `os.replace()` を使うため、リンクの置き換えにもなる。前回修正した `propose()` とは別の入口で、I2 に違反する。

   根拠：[読み取りと更新](/C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_evolve_loop.py:467)、[実行経路](/C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_evolve_loop.py:537)、[atomic](/C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_evolve.py:95)。

2. **重大・B：一覧取得では、判定不能を「ない」に変える処理が残る。**

   `index.md` の属性取得が拒否される状態で、名前を指定せず `list_index()` を呼ぶ。`walk_index_files()` の `unknown` は捨てられ、`article_path()` の `denied` も返却時に消える。再現結果は次のとおりだった。

   ```json
   {"index": null, "indexes": [], "link_warnings": []}
   ```

   同様に、MCP の `_signature_and_links()` は `unknown` と `unlistable` を捨てる。収集から落ちたページをスラッグで `get_page("a")` と引くと、再検査せず `None` になり、サーバーは「見つからない」を返す。統計も同じ走査結果から、判定不能の知らせなしに `pages: 0` を返した。

   名前指定時の `Unverifiable` だけでは、前回重大 2 の「確かめられなかったことを消す」問題を閉じていない。

   根拠：[list_index](/C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_index.py:1003)、[印と警告の収集](/C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_index.py:841)、[スラッグの不一致処理](/C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_index.py:970)。

3. **重大・D：スキーマ検査は、リンクかを判定できなくても本文を開く。**

   `detect_schema_gaps()` は `is_link()` の状態を `_state` に受け取るが、確認するのは `kind` だけである。`("denied", None)` でも `read_text()` に進む。

   `exists()` を真、`is_link()` を `("denied", None)` に差し替える再現で、本文読み取りが 1 回呼ばれ、通常の不足項目が返り、警告は出なかった。実ファイルシステム上でこの属性・読み取り状態を作る検証は未実施だが、判定不能を無視する分岐は確認できた。

   根拠：[init_wiki.py](/C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/init_wiki.py:116)。

4. **重大・B：グラフ抽出と判定レイヤーでは、リンクの拒否情報が利用者に届かない。**

   - **グラフ抽出：前回重大 6 の該当部分が未修正。** 記事をハードリンクにして抽出すると、`collect_pages()` が除外した理由を出さず、通常の抽出完了を表示する。拒否を含む走査結果を与えた再現では、標準出力は「ノード 0 個、エッジ 0 本を抽出した」、標準エラーは空だった。[wiki_graph_extract.py](/C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:1149)。
   - **shortlist：検索の警告を二重に捨てる。** `search_candidates()` は検索子プロセスの標準エラーを捕捉して捨て、JSON からも `results` だけを取り出す。子がリンク警告を両方へ出しても、最終結果は警告なしの `candidates: []` になる。設定済みバックエンドを模した再現でも確認した。[wiki_decide.py](/C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_decide.py:487)。
   - `contradictions` も、収集されたページだけから組を作り、拒否情報を付けず結果を返す。[wiki_decide.py](/C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_decide.py:546)。

   いずれも、拒否された記事がある状態を、通常の空の集合へ変える I4 違反である。

5. **重大・C：`.md` で終わるディレクトリのリンクは、スラッグ取得時の知らせから落ちる。**

   `topics.md/` を `a.md` を含むディレクトリへのジャンクションにし、MCP で `get_page("a")` を呼ぶ。走査には `{"path":"topics.md","kind":"junction"}` が残るが、サーバーは `.md` で終わらない警告だけを「読まなかった場所」として添える。このため、単なる「ページが見つからない: a」になる。

   メモリ上で `get_page()` の戻り値が `None`、サーバーの `hidden` が空になることを確認した。パスで指定する場合の修正では閉じていない。

   根拠：[wiki_mcp_server.py](/C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_mcp_server.py:350)。

## 崩れる前提

- **記事を読む入口は移し終えた。** 評価ループの索引・ログ更新で崩れる。
- **`kind is None` なら安全に読める。** リンク判定の状態が `denied` のときに崩れる。
- **名前指定時の例外対応で、判定不能の区別が保たれる。** 一覧取得、スラッグ取得、統計では保たれない。
- **検索側が警告を返せば利用者まで届く。** 子プロセスの結果から `results` だけを取り出す処理で崩れる。
- **`.md` で終わる拒否項目はファイルである。** `.md` という名前のディレクトリのリンクで崩れる。

## 見落としと軽微な問題

- **軽微：記事でない `README.md` のハードリンクを違反として報告する。** `is_article_path("README.md")` は偽だが、走査のハードリンク分岐は除外せず `("README.md", "hardlink")` を返す。メモリ上で再現した。シンボリックリンク分岐との不一致である。[wiki_pages.py](/C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:308)。
- **軽微：`evolve` の回帰試験は、実際の提案処理を通していない。** `test_evolve_evidence_refuses_links()` は `article_path()` 単体の結果とソース文字列を確認するだけで、`propose()` を実行しない。評価ループの直接読み取りも検出しない。[test_wiki_links.py](/C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/tests/wiki/test_wiki_links.py:387)。

## 検証した事実

- 指定された実装・試験、親リポジトリの試験差分、ADR、設計、前回レビューを読んだ。
- 上記の読み取り経路と出力欠落を、実装の読み込みとメモリ上の差し替えで確認した。グラフ抽出の再現では、YAML 読み込み・書き込みを差し替えた。
- `ServerFilesTests` 2 件、`PortTests` 2 件は通過した。名前の代理ビットの判定試験も単独で通過した。
- 読み取り専用環境のため、実リンクを作る統合試験は実行していない。ファイルは変更していない。

使用した MCP サーバー：なし。使用した Agent Skills：`research`、`japanese-tech-writing`。

## 崩せなかった点

- 検証した絶対パス、ドライブ指定、`..`、空要素、ドットで始まる名前は、`article_path()` が OS 呼び出し前に拒否した。
- 許可されたリンクの根の下にあるハードリンクを、現在の `find_links()` は検出した。
- 降りる前にディレクトリがジャンクションへ変わった状態では、再検査が拒否し、子の一覧を取得しなかった。
- 現在の静的 import をたどる範囲では、`SERVER_FILES` の不足を見つけられなかった。
