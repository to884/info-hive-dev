# 初期化していないディレクトリを wiki として扱わない（2026年11月13日、1 版目）

`/wiki:init` をしていないディレクトリに、ほかのコマンドを向けたときの扱いを決める設計である。「初期化された wiki」の判定を 1 か所に置き、wiki を読む入口と、wiki のために書く入口のすべてがその判定を通るようにする。未初期化なら、何も書かずに止まり、`/wiki:init` を案内する。判定の決定は [ADR-0019](../adr/0019-wiki-root-is-marked-by-schema.md) に記録する。

| 項目 | 内容 |
| --- | --- |
| 状態 | 案（作者の承認待ち） |
| 版 | 1 版目 |
| 対象 | `info-hive-wiki` 0.12.1（`origin/main` の `5326bf9`）から始める |
| 関連 | [ADR-0019](../adr/0019-wiki-root-is-marked-by-schema.md)、ADR-0004（Web ページの raw）、ADR-0008（作業領域の設定）、ADR-0010（browse）、ADR-0012（MCP サーバー）、ADR-0018（Python 3.12） |

## この変更で閉じることと、閉じないこと

- **閉じること**: `SCHEMA.md` のないディレクトリ（ほかの用途の `wiki/`、GitHub の wiki の写し、空のディレクトリ）に、lint、統計、検索、グラフ、判定、改善、閲覧、MCP のツールを向けると、何も書かずに終了コード 1（MCP ではツールのエラー）で止まり、理由と `/wiki:init` を示す。今は lint と統計が普通に報告し、検索の `--cache` がその中に `.wiki-cache/search-index.json` を書く。
- **閉じること**: Web ページの取得（`wiki_fetch.py`）が raw のルートを作らない。取り込み先の wiki を受け取り、初期化を確かめる。
- **閉じること**: `init_wiki.py --upgrade` が、`SCHEMA.md` のない wiki のディレクトリに一式を作らない（今は実質の init になる）。
- **閉じること**: 経験の記録（`wiki_evolve.py capture`）が、raw がないときにエージェントに raw を作らせる文を出さない。記録先の wiki の初期化を確かめる。
- **閉じること**: コマンドとスキルの文章をそろえる。どのコマンドも、`SCHEMA.md` がなければ何もせずに `/wiki:init` を提案する。`SKILL.md` の「下の初期化の手順を実行する」を「提案する」に直す。
- **閉じないこと**: 初期化そのもの（`init_wiki.py` を `--upgrade` なしで動かす）は、今までどおり、選んだ場所にあるディレクトリへ一式を加える。ほかの用途の `wiki/` がすでにあるときに初期化するかは、コマンドの文章でユーザーに聞く（「決めること」の 7）。スクリプトでは止めない。
- **閉じないこと**: 判定は「`SCHEMA.md` があるか」だけである。`SCHEMA.md` の中身、`index.md` や `log.md` の有無は見ない。`SCHEMA.md` だけを置いた別の用途のディレクトリは wiki とみなす。
- **閉じないこと**: ライブラリの関数（`wiki_lint.lint()`、`collect_pages()`、`compute_stats()`、`wiki_index.WikiIndex` など）は判定しない。判定は入口で行う（「決めること」の 3）。
- **閉じないこと**: 今までに未初期化のディレクトリについて作られた MCP の索引（データの場所の `index/<wiki_key>/`）と `.wiki-cache/` は、消さない。

## 背景

### 今の扱い（0.12.1）

各コマンドの手順 0 は、wiki の場所が指示や設定から見つからなければ `./wiki` に落ちる。そこに何もなければ、スクリプトと MCP のツールは止まり、何も作らない。問題は、`./wiki` に `SCHEMA.md` のないディレクトリがある場合と、書く側の入口である。

| 入口 | 何もないとき | `SCHEMA.md` のないディレクトリがあるとき |
| --- | --- | --- |
| `wiki_lint.py`、`wiki_stats.py` | 「wiki のディレクトリが見つからない」、終了コード 1 | 終了コード 0 で普通に報告する |
| `wiki_search.py --cache` | 同上 | `<dir>/.wiki-cache/search-index.json` を書く（`commands/query.md` の 4b の既定） |
| `wiki_graph_lint.py`、`wiki_graph_query.py`、`wiki_graph_extract.py` | 同上 | オントロジーがなければ止まる。`--ontology` で外のオントロジーを渡すと、extract は `<dir>/graph/` を作って書く |
| `wiki_decide.py shortlist`、`contradictions` | 同上 | 普通に動く |
| `setup_wiki.py` | 「wiki のディレクトリが見つからない」 | パースキャッシュと埋め込みを `<dir>/.wiki-cache/` に書く |
| `wiki_browse.py build`、`serve`、`core` | 「Wiki のルートがない」 | 閲覧の HTML を書き出す（書き出し先はデータの場所） |
| MCP の `query`、`stats`、`lint`、`get_page`、`list_index`、`graph` | 「wiki のルートが見つからない」 | 普通に答える。`query` と `stats` は、データの場所に索引を作る（コードから。試験で確かめる） |
| `wiki_fetch.py` | `raw_root.mkdir(parents=True, exist_ok=True)` で raw のルートを作る | 同じ |
| `init_wiki.py <base> --upgrade` | 基準のディレクトリがなければ止まる | 基準のディレクトリがあれば、`SCHEMA.md` がなくても wiki 一式を作り、実行環境を入れる |
| `wiki_evolve.py capture` | 「raw のディレクトリがない。先に作っておく」で止まる | wiki を見ない |
| `wiki_evolve.py` のほかの操作、`wiki_evolve_loop.py` | 「SCHEMA.md がない。初期化済みの wiki を指定する」 | 同じ |

文章の側では、`commands/query.md`、`lint.md`、`stats.md`、`graph.md`、`browse.md` に、wiki がないときの手順がない。`ingest.md` の末尾は「init を提案する」、`upgrade.md` の手順 1 は「ない場合は init を提案する」、`SKILL.md` の 21 行目は「下の初期化の手順を実行する」で、食い違っている。

### すでに `SCHEMA.md` で見分けている箇所

- `wiki_evolve.py` の `locked()`（改善の操作のすべてと `wiki_evolve_loop.py`）: `(wiki / 'SCHEMA.md').is_file()`。
- rag の `rag_config.py`: `wiki_root` の `SCHEMA.md` がなければ「先に wiki を初期化してください」で止まる。
- `init_wiki.py` は初期化で必ず `SCHEMA.md` を作り、上書きしない（`--upgrade` でも）。各コマンドの手順 1 は、まず `SCHEMA.md` を読む。

## 決めること

### 1. 判定

初期化された wiki は、ルートがディレクトリで、その直下の `SCHEMA.md` が通常のファイル（シンボリックリンクなら、リンクの先が通常のファイル）であるものとする。

| ルートの状態 | 判定 | 理由の文 |
| --- | --- | --- |
| ない（親がファイルのときも） | 未初期化 | `wiki のディレクトリが見つからない: <パス>` |
| ディレクトリでない | 未初期化 | `wiki のルートがディレクトリではない: <パス>` |
| ルートを調べられない（アクセス権など） | 未初期化 | `wiki のディレクトリを確かめられない: <パス>（<理由>）` |
| `SCHEMA.md` がない、壊れたリンク | 未初期化 | `初期化された wiki ではない（SCHEMA.md がない）: <パス>` |
| `SCHEMA.md` がディレクトリなど、通常のファイルでない | 未初期化 | `初期化された wiki ではない（SCHEMA.md が通常のファイルではない）: <パス>` |
| `SCHEMA.md` を調べられない | 未初期化 | `初期化された wiki か確かめられない（SCHEMA.md を調べられない: <理由>）: <パス>` |
| `SCHEMA.md` が通常のファイル | 初期化済み | — |

- 調べ方は `os.stat()`（リンクをたどる）の 1 回ずつで、`FileNotFoundError` と `NotADirectoryError` を「ない」、それ以外の `OSError` を「調べられない」とする。`Path.is_file()` は使わない。失敗の扱いが Python の版で違うためである（ADR-0018 の背景）。
- `SCHEMA.md` を開いて読むことはしない。中身は判定に使わない。
- 名前の大文字と小文字は、ファイルシステムに任せる。Windows と macOS の既定では、`schema.md` も `SCHEMA.md` として見つかる。rag と `wiki_evolve.py` も同じ調べ方をしている。

理由の文の次の行に、いつも次の案内を付ける。

```text
/wiki:init で初期化する（ユーザースコープの wiki は /wiki:init --user。スクリプトだけで使うときは init_wiki.py）。初期化した wiki が別の場所にあるなら、そのパスを指定する。
```

「見つからない」の文は、今のスクリプトの文（`wiki のディレクトリが見つからない: <パス>`）をそのまま使う。

### 2. 置き場所

判定は新しいモジュール `skills/info-hive/scripts/wiki_initialized.py` に置く。標準ライブラリだけを使い、次を公開する。

| 名前 | 中身 |
| --- | --- |
| `MARKER` | `"SCHEMA.md"` |
| `INIT_HINT` | 上の案内の文 |
| `problem(root) -> str \| None` | 未初期化なら理由の文、初期化済みなら `None` |
| `NotInitialized(ValueError)` | 理由の文と案内を持つ例外 |
| `require(root) -> Path` | 未初期化なら `NotInitialized` を送出し、初期化済みなら `root` をそのまま返す |
| `require_or_exit(root) -> Path` | 未初期化なら理由と案内を標準エラーに書き、終了コード 1 で止まる |

- `wiki_workspace.py` には置かない。log と rag と同じ規則を持つ共通の部分（ADR-0008）で、`tests/workspace/` が実装どうしの一致を確かめているからである。
- `wiki_pages.py` にも置かない。走査が OS を呼ぶ口を `tests/wiki/test_walk.py` が構文木で数えていて、判定の `os.stat()` がそこに混ざるからである。
- `wiki_mcp_common.SERVER_FILES` に足す。サーバーのコードの版が変わり、更新のあとに動いているサーバーが入れ替わる。
- `__main__` を持たない。読み込む入口は、どれも先に `wiki_text` を読み込む（ADR-0018 の版の確かめ）。

### 3. 判定する場所は入口だけ

判定は、利用者やエージェントが wiki のパスを渡す入口で行う。ライブラリの関数は判定しない。MCP のサーバーと既存の試験が、ライブラリの関数を素のディレクトリに対して呼んでいるためであり、入口で 1 回確かめれば、その後の処理は同じ wiki を扱う。

| 入口 | 変更後 |
| --- | --- |
| `wiki_lint.py`、`wiki_stats.py`、`wiki_graph_lint.py`、`wiki_graph_query.py`、`wiki_graph_extract.py` | 今の `exists()` の確かめを `require_or_exit()` に替える |
| `wiki_search.py` | 同じ。パースキャッシュのパスを決めるより前、`collect_pages()` より前に確かめる |
| `wiki_decide.py shortlist`、`contradictions` | 同じ。`ask`、`screen`、`check` は wiki を使わないので確かめない |
| `setup_wiki.py` | 今の `is_dir()` の確かめを `require_or_exit()` に替える。init と upgrade は `SCHEMA.md` を置いてから呼ぶので、影響しない |
| `wiki_evolve.py`（`capture` と `verify-bundle` 以外）、`wiki_evolve_loop.py` | `locked()` の `SCHEMA.md` の確かめを `require()` に替え、文をそろえる。`.evolution/` を作るのは、確かめのあとである（今と同じ） |
| `wiki_evolve.py capture` | 「決めること」の 5 |
| `wiki_browse.py build`、`serve`、`core` | `wiki_root()` で確かめる。`core` は今と同じく `{"ok": false, "error": "no_wiki"}` を返す（中核の契約の誤りの値を増やさない） |
| `wiki_browse.py stop` | 確かめない。動いているサーバーを止めるだけで、wiki を読みも書きもしない。`SCHEMA.md` をあとで消した wiki のサーバーも止められるようにする |
| MCP の `wiki_root()`（`query` の `wiki`、`get_page`、`list_index`、`lint`、`stats`、`graph`） | 今のパスの正規化（NFC、`resolve(strict=True)`）のあとで `require()` を呼ぶ。`NotInitialized` は `ValueError` なので、ツールのエラーになる。索引のキャッシュ（`State.wikis`）を引く前に毎回確かめるので、`SCHEMA.md` を消した wiki には答えない |
| MCP の `query` の `collection`、`index_chunks` | 確かめない。wiki を受け取らない（rag が使う） |
| `wiki_fetch.py` | 「決めること」の 4 |
| `init_wiki.py --upgrade` | 「決めること」の 6 |
| `wiki_workspace.default_wiki_or_exit()` | 変えない。場所を決めるだけで、判定は呼び出し元が続けて行う |
| `wiki_help.py`、`wiki_encoding.py`、MCP の入口と中継 | wiki を受け取らないので変えない |

### 4. Web ページの取得は、取り込み先の wiki を受け取る

raw のルートは wiki から決まった位置にない（既定は wiki と同じ階層の `raw/`、以前の既定は `wiki/raw/`、作業領域の設定では `dirs.raw`）。raw のルートだけを受け取る今の形では、取り込み先の wiki を確かめられない。そこで次のようにする。

- `--wiki <WIKI_ROOT>` を必須の引数として足し、`require_or_exit()` で確かめる。確かめるのは、引数を読んだ直後で、ネットにつなぐ前である。
- raw のルートは作らない。`--raw-root` がディレクトリでなければ、次の文で終了コード 1 で止まる。`raw のルートがない: <パス>。--raw-root が正しいかを確かめる。初期化した wiki の raw をなくしたときは、/wiki:upgrade で作り直せる。` raw のルートの下（`assets/<スラッグ>/`）は、今までどおり作る。
- `commands/ingest.md` と `references/ingest-workflow.md` のコマンドの例に `--wiki` を足す。

`--wiki` を省いた今までの呼び方は、引数の誤り（終了コード 2）になる。コマンドの文章とスクリプトは同じ版で配るので、文章に従うエージェントは影響を受けない。

### 5. 経験の記録は、記録先の wiki を確かめる

`wiki_evolve.py capture` は、raw の `experiences/` に記録を書き、エージェントがそれを wiki にソースとして取り込む（`/wiki:learn`）。記録先の wiki が未初期化なら、取り込めない記録だけが残る。そこで次のようにする。

- `capture` でも、ほかの操作と同じく wiki の場所を決め（`--wiki`、なければ作業領域の設定、なければ `./wiki`）、`require()` で確かめる。確かめは `main()` で、`capture()` を呼ぶ前に行う。`capture()` の関数は判定しない（`eval/evolution/test_evolution.py` が関数を直接呼ぶ）。
- raw のディレクトリがないときの文を、`raw のディレクトリがない: <パス>。--raw が正しいかを確かめる。初期化した wiki の raw をなくしたときは、/wiki:upgrade で作り直せる。` に替える。「先に作っておく」は使わない。
- `capture` で作業領域の設定を読まないという今の扱い（`main()` のコメント）は、やめる。`verify-bundle` は今までどおり wiki を使わない。

### 6. アップグレードは、初期化された wiki だけを対象にする

`init_wiki.py <base> --upgrade` は、基準のディレクトリの確かめ（今のまま）のあとで、`<base>/<--wiki-dir>` を `problem()` で確かめる。未初期化なら、ディレクトリもファイルも作らず、実行環境も入れずに、次の文で終了コード 1 で止まる。

```text
エラー: アップグレードする wiki がない。<理由の文>
/wiki:init で初期化する。既定と違う名前で作った wiki なら、--wiki-dir と --raw-dir で指す。
```

`SCHEMA.md` を消してしまった wiki は、アップグレードできない。`/wiki:init` を同じ場所で実行すると、今までどおり既存のファイルを上書きせずに `SCHEMA.md` を足すので、それで戻せる。

### 7. コマンドとスキルの文章

どのコマンドも、`<WIKI_ROOT>` を決めた直後に `SCHEMA.md` を確かめる。文は 1 つに決め、`commands/query.md`、`lint.md`、`stats.md`、`graph.md`、`browse.md`、`ingest.md`、`learn.md`、`evolve.md` に同じ形で入れる。

> `<WIKI_ROOT>/SCHEMA.md` がなければ、初期化された wiki ではない（ほかの用途の `wiki/` のこともある）。MCP のツールもスクリプトも呼ばず、何も書かずに止まり、ユーザースコープの wiki なら `/wiki:init --user`、プロジェクトの wiki なら `/wiki:init` を提案する。指示や設定で wiki の場所を探し直したり、`SCHEMA.md` を自分で作ったりしてはならない。ツールやスクリプトが「初期化された wiki ではない」と返したときも同じにする。

- `ingest.md`: 末尾の「wiki がまだない場合は……」を、上の手順に置き換える。Web ページの取得のコマンドに `--wiki "<WIKI_ROOT>"` を足す。
- `upgrade.md`: 手順 1 の「wiki があることを確認する」を「`<WIKI_ROOT>/SCHEMA.md` があることを確かめる」に替え、ない場合は init を提案して `init_wiki.py --upgrade` を実行しないと書く。
- `init.md`: 選んだ場所に `SCHEMA.md` のない `wiki/`（`--wiki-dir` の名前）があり、中にファイルがあるときは、ほかの用途のディレクトリかもしれないことを伝え、そこに初期化するか、`--wiki-dir` で別の名前にするかを聞く。
- `learn.md`、`evolve.md`: 上の手順に加え、`capture` に `--wiki "<WIKI_ROOT>"` を渡すと書く。
- `SKILL.md` の 21 行目: 「wiki がない場合は、下の初期化の手順を実行する」を、判定（`SCHEMA.md`）と「何もせずに初期化を提案し、ユーザーが望んだら下の初期化の手順を実行する」に替える。
- `references/ingest-workflow.md`、`references/evolution-workflow.md`、`references/mcp-server.md`: コマンドの例と、未初期化のときのエラーを足す。
- MCP のツールの説明（docstring）: `wiki` には初期化された wiki（`SCHEMA.md` のあるディレクトリ）のルートを渡すこと、そうでなければエラーになることを書く。
- `docs/commands.md` などの利用者向けの文書で、同じことに触れている箇所をそろえる。

### 8. 版

利用者に見える変更で、互換でない部分がある（今まで報告していたディレクトリを断る、`wiki_fetch.py` の `--wiki` が必須になる、`capture` が wiki を確かめる）。0.x の互換でない変更なので、minor を上げて **0.13.0** にする。版を決める直前に `origin/main` の `plugin.json` とタグを取り直す。CHANGELOG の `### Changed` に、互換でない点をはっきり書く。

## 試験

親リポジトリの `tests/wiki/test_uninitialized_wiki.py` に置く。実装の前に書いて、今の実装で落ちることを確かめる（MCP の `query` と `stats` が索引を作ることも、ここで確かめる）。

| 試験 | 中身 |
| --- | --- |
| 判定の表 | 「決めること」の 1 の表の各行を、`problem()` で確かめる。ない、ファイル、空のディレクトリ、Markdown のページだけのディレクトリ、`SCHEMA.md` がディレクトリ、壊れたリンク（作れる環境だけ）、`SCHEMA.md` がある |
| CLI の入口 | 各入口を、`SCHEMA.md` のない、ページのあるディレクトリに向けて子プロセスで動かす。終了コード 1、標準エラーに理由と `/wiki:init`、前後でディレクトリの木（基準のディレクトリの下のすべてのパス、大きさ、更新時刻）が変わらないこと。同じディレクトリに `SCHEMA.md` を置くと終了コード 0 になること（試験が空振りしていないことの確かめ） |
| `wiki_search.py --cache` | 上に加え、`.wiki-cache/` ができないこと |
| `wiki_graph_extract.py --ontology <外>` | `graph/` ができないこと |
| `wiki_fetch.py` | 届かない URL（`http://127.0.0.1:9/`）で、未初期化の `--wiki` は終了コード 1（取得の失敗の 2 ではない）で raw ができないこと。初期化済みの wiki と、ない `--raw-root` で、終了コード 1 で raw ができないこと。`--wiki` を省くと終了コード 2 |
| `init_wiki.py --upgrade` | 基準のディレクトリに `SCHEMA.md` のない `wiki/` があると、終了コード 1 で、何もできず、uv を呼ばないこと（`UV` を存在しないパスにして確かめる） |
| `wiki_evolve.py capture` | 未初期化の wiki で終了コード 1、`experiences/` ができないこと。raw がないときの文に「先に作っておく」がなく、`/wiki:upgrade` があること |
| `wiki_browse.py build`、`core` | 書き出し先とデータの場所（環境変数で一時ディレクトリに向ける）が変わらないこと。`core` が `no_wiki` を返すこと。`stop` は未初期化でも今と同じに動くこと |
| MCP | `test_mcp_server.py` に足す。`query`、`stats`、`lint`、`get_page`、`list_index`、`graph` が「初期化された wiki ではない」のエラーを返し、データの場所の `index/` に、その wiki のディレクトリができないこと。`collection` の `query` と `index_chunks` は今までどおり動くこと |
| 文章 | `commands/*.md` のうち wiki を扱うものがすべて同じ手順の文を含むこと、`SKILL.md` が「初期化の手順を実行する」と書いていないこと |

既存の試験の素材で `SCHEMA.md` のない wiki を CLI、MCP、browse に渡しているものは、素材に `SCHEMA.md` を足して直す。判定を緩めて通すことはしない。影響しそうなのは、`tests/workspace/cases.json` の cli の場合、`tests/wiki/test_browse*.py` と `tests/wiki/browse/*.mjs`（親の CI でだけ動く）、`tests/wiki/test_mcp_server.py`、`tests/wiki/test_wiki_index.py`、子の `eval/scripts/` と `eval/retrieval/` の試験である。

## 確かめの環境

Windows 11、Python 3.12（uv）と 3.14.6。CI は子の `wiki-tests.yml`（Ubuntu と Windows、3.12 と 3.14）と、親の `wiki-mcp.yml`、`wiki-browse.yml`、`wiki-walk.yml`。

## レビューの進め方

AGENTS.md に従い、この設計と、実装のそれぞれのあとに、ask-codex で Sol に敵対的レビューを頼む。記録は `docs/agent-runs/2026-11-13-wiki-uninitialized-root/` に置く。
