# wiki の MCP サーバーの試験と測定

`info-hive-wiki` の MCP サーバー（ADR-0012）と検索の基盤（ADR-0011）の試験と測定を置く。プラグインの本体には置かない。

| ファイル | 中身 |
| --- | --- |
| `test_wiki_index.py` | 検索の基盤（`wiki_index.py`）の試験。差分の更新、途中で止まったときのそろえ直し、Tantivy の commit のやり直し、fingerprint が変わったときの作り直し、書き手のロック、`index_chunks` の世代。MCP の `query` の結果の `tags` と `sources` が、値を 1 つだけ書いた frontmatter でも文字の配列になること（wiki 0.12.1）。`title` が値なしや配列のページがあっても索引が止まらず、`query` と `list_index` の題名が文字になること（wiki 0.12.2） |
| `test_mcp_server.py` | サーバーと中継の試験。トークンと Host ヘッダー、127.0.0.1 だけで待ち受けること、中継を 4 つ同時に起動してもサーバーが 1 つ、中継の終了後もサーバーが残ること、サーバーが止まった後や呼び出しの途中で止まったときの接続し直し、版の違うサーバーの入れ替え、要求がないときの停止。ツール `lint`、`stats`、`graph` が CLI の `--json` と同じ結果を返すこと |
| `test_wiki_lint.py` | lint の索引、出典、原本、タグの検査（0.7.0 の `index_type_mismatch`、`unresolved_sources`、`missing_raw`、`unknown_tags`）。標準ライブラリだけで動く |
| `test_source_claims.py` | 取り込みでソースの要約ページに残す `## 主張と行き先`（0.8.0、ADR-0015 の段階 2）。手順書、ページの規約、`SCHEMA.md` とページのひな形が同じ見出し、列、行き先の値を示すこと、作例の表の形、作例を入れた source のページが lint を通ること、`init_wiki.py --upgrade` が新しいセクションを案内すること、段階 3 の規定が混ざっていないこと。標準ライブラリだけで動く |
| `test_template_script_paths.py` | `init_wiki.py` が書き出す `SCHEMA.md` と `graph/README.md` のコマンドの例のスクリプトのパス（wiki 0.9.1）。ひな形に `<skill-root>/` の付かない `scripts/` がないこと、`<skill-root>` の説明があり、置き換えると実在するスクリプトを指すこと、パスが `"` で囲まれていること、`SCHEMA_SECTION_MARKERS` が変わっていないこと。書き出した `SCHEMA.md` の `--no-embed` の検索の例を、既定の名前と別の名前の wiki で実行する。スキルの `SKILL.md` と `references/*.md` のコマンドも同じ `"<skill-root>/scripts/..."` の書き方で、実在するスクリプトを指し、`SKILL.md` の「スクリプトのパス」が定義していること（wiki 0.9.3）。標準ライブラリだけで動く |
| `test_graph_duplicate_slugs.py` | グラフの抽出が、閲覧（browse）の関係表の契約を満たすこと（wiki 0.9.2）。別のディレクトリの同じスラッグのページ（`a/Foo.md` と `b/Foo.md`）で、主語がそのページ自身のノードになること、パスを付けたリンクの行き先、パスのないリンクと `sources:` をどちらにも寄せないこと。別のページの同じ内容の関係を 1 本にまとめないこと（NFC と NFD の名前の違いだけのファイルも）、同じ `graph.node_id` のページの関係を捨てず、その ID を目的語にした関係を曖昧として挙げること、パスと `[[...]]` で書いた `sources:` の解決と診断。`graph.sqlite`、JSONL、GraphML、グラフの lint、MCP のツール `graph` が使う問い合わせ。PyYAML が要る |
| `test_graph_frontmatter_values.py` | グラフの抽出が読む frontmatter の値が、wiki の lint と同じこと（wiki 0.9.5）。引用符のない真偽値、数、日付、`null` を書いた最上位の欄が lint の辞書と等しいこと、`sources: [true]` が lint と同じページに解決すること、`graph:` の参照の欄を書かれた文字で読むこと、読めなかった `graph:`（`unreadable_graph`）と lint のパーサーが読めない書き方の欄（`unread_fields`）の診断、オントロジーの `maps_from` の読み方。引用符で囲む規約どおりのページで、ノードとエッジが 0.9.3 の読み方と変わらないこと。PyYAML が要る |
| `test_wiki_fetch.py` | Web ページの取得（`wiki_fetch.py`）の、Medium の形の取りこぼし（info-hive-wiki#42）。`<picture>` の `<source srcset>` にだけ URL がある図を保存し、WebP でない `<source>` の幅のいちばん大きい候補を選ぶこと、`<img>` の URL があればそれを使うこと、`<pre>` の中の `<br>` を改行にし、`<pre>` の外の `<br>` は変えないこと。取得を差し替え、ネットにはつながない。標準ライブラリだけで動く |
| `test_frontmatter_parser.py` | frontmatter のパーサー（`wiki_text.parse_frontmatter_text`）が読む YAML の書き方（wiki 0.9.7）。字下げの違うブロックの配列、複数行にまたがる `[...]`、引用符つきのキーとコロンの前の空白、二重引用符の中の YAML のエスケープ、`\|` と `>` のブロックのスカラーの値が、PyYAML の `BaseLoader`（型に直さない）と等しいこと（値の表と、種を固定した無作為の入力）。YAML と違ってよいと決めた箇所と、読まないまま残す書き方の値。規約どおりのページと、読み方を変えない書き方で、値が 0.9.5 のパーサーそのものの出力（`frontmatter_parser_golden.json`）と等しいこと。`]` を書き忘れた配列が後ろの欄を取り込まないこと、YAML にないエスケープを含む値を今までどおり読むこと。書き手（`format_frontmatter`）との往復、lint・検索・統計が読めるようになった欄を読むこと、検索の古いパースキャッシュを使い続けないこと、制御文字のある値でも GraphML が読める XML になること。PyYAML が要る |
| `test_frontmatter_raw.py` | rag が返す PDF の絶対パスと SHA-256 を、ソースの要約ページの frontmatter に書いて読み戻す（ADR-0013）。手書きのパーサーと PyYAML が同じ値に読むこと、`\` を重ねていない Windows のパスの読み方。PyYAML が要る |
| `test_python_version.py` | 同梱のスクリプトの Python の版の扱い（3.12 以上、wiki 0.11.2、ADR-0018）。`python` で直接動かす入口（ファイルから機械的に集める）を、本物の 3.10 と 3.11 で `--help` つきで動かすと、どれも理由を書いて止まること。古い版を真似て `wiki_text.py` を読み込むと止まること、PEP 723 の宣言がどれも `>=3.12` であること。標準ライブラリだけで動く。3.10 と 3.11 は `uv python find` で探し、なければ飛ばす（`WIKI_TEST_REQUIRE_OLD_PYTHON=1` のときは失敗する） |
| `test_walk.py` | wiki をたどる経路（`wiki_pages.walk_markdown()`、wiki 0.11.2。設計は `docs/plans/wiki-walk-excluded-dirs-2026-11-11.md`）。木の表から計算した答えと等しいこと、info-hive-wiki のコミット `2756a4e`（0.10.1）の実装を git から取り出して照らし、違いが設計の表のものだけであること、OS を呼ぶ口のすべてに失敗を 1 つずつ入れる探索と、わざと決まりを破った対照、口の一覧の構文木の確かめ、統計と MCP の索引の印。標準ライブラリだけで動く（索引の試験は、依存がなければ飛ばす）。ジャンクション、識別子、大文字と小文字を区別するフォルダーの試験は Windows だけ |
| `test_mcp_spawn_flags.py` | 入口、中継、サーバーの子プロセスの起動が、すべて `child_creationflags` か `server_creationflags` を通し、`DETACHED_PROCESS` を使わないこと（info-hive-wiki#36）。子はコンソールがあれば引き継ぎ、なければ窓のないコンソールで起動すること、引き継いだコンソールの標準出力に書けること。サーバーを窓のない自分のコンソールと新しいプロセスグループで起動すること。依存は要らない |
| `test_uv_tls.py` | TLS を検査する社内ネットワークで uv が証明書を検証できないとき（info-hive-wiki#30）。`UV_SYSTEM_CERTS=true` での 1 回だけのやり直し、利用者の設定の尊重、入れ直しに進まないこと。自己署名の証明書の HTTPS の索引を手元に立て、入口が理由と対処を `logs/launch.log` に書いてすぐ止まることも確かめる（`--with cryptography` で動かす） |
| `run_mcp_gate.py`、`mcp_eval_search.py` | wiki の評価ゲート（`eval/retrieval/run_eval.py`）を新しい基盤で通す |
| `bench_mcp_latency.py` | 検索の速さ（今の CLI、中継経由の MCP、直接呼び出し） |
| `bench_mcp_startup.py` | 起動の速さ（入口から `initialize` と `tools/list` まで）。2 つの版のスクリプトを交互に起動して比べる。結果は `docs/research/wiki-mcp-startup-2026-11-07/` に置く |
| `measure_dense_threshold.py` | 意味の検索の距離の上限（`max_distance`）。評価セットの距離の分布と、上限を変えたときの成績。結果は `docs/research/wiki-dense-threshold-2026-11-07/` に置く |
| `check_claude_spawn.py` | Claude Code が中継とサーバーをどう起動し、セッションの後にサーバーが残るか（`claude -p` を 1 回実行する） |
| `check_server_console.py` | Windows でサーバーを起動したときに、画面（コンソールの窓）が出ないか（info-hive-wiki#36）。入口の `--ensure` で起動し、見える窓を前後で比べる。入口と中継が終わった後もサーバーが残り、terminate で止まるかも見る。結果は標準出力に書く |
| `check_commands_mcp.py` | コマンド（`/wiki:stats`、`/wiki:query`、`/wiki:lint`）がまず MCP のツールを使い、`.mcp.json` のないプラグインでは CLI に戻るか（`claude -p --plugin-dir` をコマンドの数だけ実行する。引数にコマンド名を渡すと、それだけを実行する） |
| `check_first_run_mcp.py` | 初めて使う人の最初のセッション。uv のキャッシュとデータの置き場所を空にして `claude -p` を実行し、サーバーの依存（約 1 GB）とモデル（約 530 MB）の取得のあいだにどう振る舞うかと、用意ができたあとの 2 回目のセッションを確かめる |
| `mcp_stdio.py` | 試験用の最小の stdio の MCP クライアント |

結果は、ことわりがなければ `docs/research/wiki-mcp-server-2026-11-06/` に置く。

## 動かし方

Python 3.12 以上で動かす（ADR-0018）。依存はサーバーのスクリプトの宣言と同じ版にそろえる。Windows では一時ディレクトリが遅いドライブにあると試験が遅くなるので、`TMP` を速いドライブに向けるとよい。

```bat
python -X utf8 -m unittest tests/wiki/test_wiki_lint.py -v
python -X utf8 -m unittest tests/wiki/test_source_claims.py -v
python -X utf8 -m unittest tests/wiki/test_template_script_paths.py -v
python -X utf8 -m unittest tests/wiki/test_wiki_fetch.py -v
python -X utf8 -B -m unittest tests/wiki/test_walk.py -v
python -X utf8 -B -m unittest tests/wiki/test_python_version.py -v
uv run --python 3.12 --with pyyaml==6.0.3 python -X utf8 -m unittest tests/wiki/test_graph_duplicate_slugs.py -v
uv run --python 3.12 --with pyyaml==6.0.3 python -X utf8 -m unittest tests/wiki/test_graph_frontmatter_values.py -v
uv run --python 3.12 --with pyyaml==6.0.3 python -X utf8 -m unittest tests/wiki/test_frontmatter_parser.py tests/wiki/test_frontmatter_raw.py -v
set DEPS=--with mcp==1.30.0 --with numpy==2.5.4 --with usearch==2.26.6 --with tantivy==0.27.0 --with fastembed==0.8.0 --with onnxruntime==1.31.1 --with pyyaml==6.0.3 --with psutil==7.2.2
uv run --python 3.12 %DEPS% python -X utf8 -m unittest tests/wiki/test_wiki_index.py -v
uv run --python 3.12 %DEPS% python -X utf8 -m unittest tests/wiki/test_mcp_server.py -v
python -X utf8 -m unittest tests/wiki/test_mcp_spawn_flags.py -v
uv run --python 3.12 --with cryptography python -X utf8 -m unittest tests/wiki/test_uv_tls.py -v
uv run --python 3.12 %DEPS% python -X utf8 tests/wiki/run_mcp_gate.py
uv run --python 3.12 %DEPS% python -X utf8 tests/wiki/bench_mcp_latency.py
uv run --python 3.12 %DEPS% python -X utf8 tests/wiki/measure_dense_threshold.py
uv run --python 3.12 %DEPS% python -X utf8 tests/wiki/check_claude_spawn.py
uv run --python 3.12 --with psutil==7.2.2 python -X utf8 tests/wiki/bench_mcp_startup.py 36a4089 work --rounds 7
uv run --python 3.12 --with psutil==7.2.2 python -X utf8 tests/wiki/check_server_console.py
uv run --python 3.12 --with psutil==7.2.2 python -X utf8 tests/wiki/check_commands_mcp.py
uv run --python 3.12 --with psutil==7.2.2 python -X utf8 tests/wiki/check_first_run_mcp.py
```

- `check_commands_mcp.py` と `check_first_run_mcp.py` は、`claude -p --plugin-dir` で手元の `info-hive-wiki` を読み込む。マーケットプレイスから `wiki@info-hive` を入れていても、`--plugin-dir` の側が優先され、その MCP のサーバーが使われる（Claude Code 2.1.316 で確かめた）。
- macOS と Linux では、`.github/workflows/wiki-mcp.yml`（手で起動するか、`info-hive-wiki` の参照か `tests/wiki/` を変えた PR で動く）が、lint、索引、サーバーの試験と、本物のモデルでの評価ゲートを動かす。

- 試験はテスト用の埋め込み（`INFO_HIVE_TEST_EMBEDDER=hash`）を使い、モデルを読み込まない。中継は `.mcp.json` と同じく `uv run --script` で起動するので、サーバーの依存を初めて取得するときは数分かかる。
- 評価ゲートと速さの測定は、本物のモデル（約 530 MB）を PoC データの `wiki-mcp-20261106/data/models/` に取得して使う。PoC データの置き場所は `poc/poc_data.py` が決める。既定はメインのチェックアウトの隣の `info-hive-dev-data/rag-poc-data` で、環境変数 `INFO_HIVE_POC_DATA` で変えられる。
