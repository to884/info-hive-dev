## 判定

**採用可**。前回の性能レビュー以降のコードの変更は、main の取り込みと ADR 番号のコメントの書き換えだけでした。リリースを止める欠陥は見つかりませんでした。次の点は確かめて一致しました。

- 統合点（遅延初期化、`markdown_module`、`wiki_tokens`、読み取りの場所の目録、モデル表の照合）
- `validation.json` に記録されたハッシュと数値
- CI の 4 件

確信度は中です。全 739 件の試験とベンチマークは再実行していません。

## 致命的・重大な欠陥

なし。

## 崩れる前提

- **親リポジトリのサブモジュールの参照は、プラグインの main を指す**: 今の親の `HEAD` は `info-hive-wiki` の参照を PR #91 の head `6e8f2c2` にしています。これまでの main は、子 PR のマージコミットを指していました。
  - 例: 親の `origin/main` の参照は `d761c62` で、これは #90 のマージコミットです（`git cat-file -p d761c62` で親が 2 つ）。
  - #91 をマージコミットで入れた場合、親を `6e8f2c2` のまま入れると、プラグインの main（とタグ `v0.33.0`）とは別のコミットを記録することになります。
  - squash や rebase でマージした場合は、`6e8f2c2` は main から辿れなくなり、ブランチの削除のあとに消える可能性があります。リポジトリの設定ではどちらも許されています。
  - 手順上の注意で、コードの欠陥ではありません（軽微）。
- **読み取りの場所の目録の WALKED は、走査から開くまでの間にファイルが差し替わらないことを前提にしている**: `wiki_prompt_context.read_text` は、走査の結果の `rel` を `(root / rel).open("rb")` で開き直します。リンクを辿らない開き方ではありません。走査のあとでページがシンボリックリンクに差し替えられれば、その先を読みます。
  - フックの出力は題、パス、見出し、要約だけです。ただし、題と見出しは本文から取ります。
  - wiki に書き込める者でなければ起こせません。lint や検索の WALKED の読み取りと同じ扱いで、既存の方針（ADR-0029）の範囲です。今回の統合で新しく生じた欠陥ではありません（推測、軽微）。
- **Codex の環境ではフックを読まない**: `.codex-plugin/plugin.json` に hooks の宣言はありません。Codex CLI がプラグインの `hooks/hooks.json` を自動で探すかどうかは確かめられませんでした。探す場合でも `${CLAUDE_PLUGIN_ROOT}` が展開されず、起動に失敗して `; exit 0` で終わると見ています（推測）。

## 見落としと軽微な問題

- **【軽微】`threading` の import の重複**: `wiki_pages.py` は、main 由来の `import threading`（36 行目）と、今回足した `from threading import RLock` を両方持っています。害はありません。
- **【軽微・既知の限界】負荷の条件の間で、遅さの順序が逆になっている**: 今回の `names-16.json`（16 本の負荷、題の一致）は p95 が 1,189.7ms で、同じ 16 本の明示参照（1,265.9ms）より速い値でした。前の世代の `review2-names-corrected-8.json`（8 本の負荷）は p95 が 3,178.7ms でした。負荷が少ないほうが 2.7 倍遅いことになり、周りの負荷の変動が支配的だとわかります。条件を比べる材料にはなりません。報告は合算も改善率も主張していないので、食い違いはありません。
- **【軽微】`wiki_browse_core.CORE_VERSION` が `browse-core-5` のまま**: `Token` の取得のしかたが変わりましたが、機能は同じなので、版を上げる必要は見当たりません。指摘というより確認です。

## 検証した事実

- **フックのコードの差分**: 前回の採用時の `wiki_prompt_hook.py` は `27abff…`、`wiki_prompt_context.py` は `b00a5e…` でした。これは rebase 後の `262b538` と同じです。`262b538` と `6e8f2c2` の差は、docstring とコメントの `ADR-0032` を `ADR-0034` に変えた 3 行だけです。**一致**。期限、終了コード 0、出力の 2,000 文字、出力のあとに既出を保存する順序、優先度の `creationflags` は変わっていません。
- **`wiki_pages.py` の統合**: main に対する差分は、前回レビューした遅延初期化、`__getattr__`、`markdown_module` だけでした。走査、記事のリンク拒否、概要の追加はそのまま残っています。`wiki_pages.py` の中で `_MD`、`markdown_it`、`_md_utils`、`PARSER_ID` を裸の名前で参照する箇所はありません（モジュールの `__getattr__` は外からの属性の参照にしか効かない）。**一致**。
- **新しい Python での import**: `python -I -S` で `wiki_*.py` を全部 import しました。失敗したのは、PyYAML が必要な `wiki_graph_extract` と `wiki_graph_lint` の 2 つだけで、どちらも既知の依存です。`markdown_it` の欠落はありませんでした。`wiki_browse_core` が `wiki_overview` を import したあとでも、`markdown_module("token")` で同梱の `Token` を取っています。
- **`markdown_it` を直接読む経路**: submodule の全体を検索しました。`markdown_it` と `mdurl` を直接 import する箇所は残っていません。`import_module` は `wiki_mcp_common.require_env` の 1 箇所だけです。**一致**。
- **`wiki_tokens`**: `SCRIPT_RUN_RE` と `tokenize` は、main の `wiki_search` にあったものと字句まで同じで、`wiki_search` は同じ名前で読み直しています。`SERVER_FILES` に `wiki_tokens.py` が入りました。**一致**。
- **読み取りの場所の目録**: `test_wiki_links.ReadSiteInventoryTests` に `wiki_prompt_context` の 5 関数がありました。
  - `read_text`、`read_page`、`read_index` は WALKED。
  - `load_state`、`state_lock` は NOT_ARTICLE。
- **狭い範囲の試験**: 次の 2 回の実行が成功しました。
  - `ReadSiteInventoryTests` と `test_prompt_hook` の全体: 67 件。
  - `test_reader_measurement.ProductDecisionTests`: 成功。
- **リンクを開かない試験**: 開いたかどうかの見張りは `Path.open` を、パスの等値で見ています。ふつうのページで試すと、この比較は実際に開いたときに一致しました（10 回開いたうちの対象のパスで `True`）。見張りは空振りしていません。
- **モデル表の照合**: `agents/wiki-reader.md` の `262b538` からの差分は、`description` の `ADR-0032` を `ADR-0034` にした 1 行だけです。fixture の `reader_sha256_without_defaults`（`f19634…`）は `a982d2a` の前後で変わっていません。照合は、`ADR-0034` がちょうど 1 回だけ出ることを確かめてから置き換えます。ほかの変更を隠す経路は見つかりませんでした。**一致**。
- **`validation.json`**: 17 ファイルの SHA-256 は、`git diff --name-only origin/main...HEAD` の 17 ファイルと一致し、すべて現在の内容とも一致しました。
  - `unit.log`、`integration.log`、並列 3 ファイルのハッシュも一致しました。
  - ログの末尾は `Ran 440 tests … OK (skipped=1)` と `Ran 299 tests … OK (skipped=14)` です。
  - 並列の 3 ファイルは、それぞれ 20 回すべてが exit 0、stderr が空で、候補が届いています。hook、context、pages のハッシュも現在のファイルと一致し、負荷の反復数は最小で 9 です。
  - 逐次の検索は p95 551.0ms、10/10 です。
  - 依頼文の数値と**一致**。
- **PR #91 の状態**: OPEN、`MERGEABLE`、head は `6e8f2c2` です。`python (3.12/3.14)` と `python-windows (3.12/3.14)` の 4 件が SUCCESS でした。**一致**。
- **版の番号と ADR の番号**: `git fetch` のあとも、`origin/main` は base の `d761c62`（0.32.0）のままです。タグ `v0.33.0` はまだありません。親の `docs/adr/` では 0032 が Codex の会話履歴、0033 が概要、0034 が本件で、submodule の中の参照も 0034 にそろっています（CHANGELOG の 0.29 の節の `ADR-0032` は Codex のことを指していて正しい）。親の `HEAD` は `origin/main`（`105fd0b`）を含んでいます。

## 崩せなかった点

- **遅延初期化と `markdown_module` を main に当てたこと**: rawcheck の新しい翻訳の検査も、閲覧の概要も壊していません。
- **フックが走査の結果から記事を読むこと**: シンボリックリンクとハードリンクのページは、候補にならず、本文も開かれません（Windows で実行して成功）。
- **モデル決定の不変**: モデル決定、158 回の回答、採点のハッシュは変わっていません。reader の本文の変更は ADR の番号の 1 箇所だけです。
- **フックの契約**: 内部 2.5 秒、外側 5 秒、失敗時に 0、2,000 文字、実際に出したあとの既出の保存は、前回の採用時のコードと同じです（コメントの差だけ）。

---

- 次の作業（#91 をマージコミットでマージし、親のサブモジュールの参照をプラグインの main のマージコミットに更新し、タグ、GitHub リリース、マーケットプレイスからの導入の確認まで進める）に適したモデルとエフォート: Sonnet、medium
- 今回の統合レビューに適したモデルとエフォート: Opus、high

使用した MCP サーバー: なし
使用した Agent Skills: なし
