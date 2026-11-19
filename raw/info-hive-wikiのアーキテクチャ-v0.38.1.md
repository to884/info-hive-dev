# info-hive-wiki v0.38.1 のアーキテクチャの根拠

Git タグ v0.38.1、コミット b8596d1888035769528cb74e35bda51c9d9c40a0（2026-11-19）。
各抜粋は指定したコミットの Git オブジェクトから取得した。リンク先の行番号も同じ版を指す。

## ホストの入口

- [.mcp.json 1 行目から](https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/.mcp.json#L1-L13)

````
{
  "mcpServers": {
    "wiki": {
      "command": "uv",
      "args": [
        "run",
        "--quiet",
        "--script",
        "${CLAUDE_PLUGIN_ROOT}/skills/info-hive/scripts/wiki_mcp_launch.py"
      ]
    }
  }
}
````

- [.codex-plugin/plugin.json 1 行目から](https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/.codex-plugin/plugin.json#L1-L17)

````
{
  "name": "wiki",
  "version": "0.38.1",
  "description": "日本語の Markdown の wiki を構築・保守し、ローカル検索、出典つきの回答、グラフ、閲覧、経験の記録を提供する。",
  "author": { "name": "to884" },
  "license": "MIT",
  "homepage": "https://github.com/to884/info-hive-wiki",
  "repository": "https://github.com/to884/info-hive-wiki",
  "skills": "./skills/",
  "mcpServers": {
    "wiki": {
      "command": "uv",
      "args": ["run", "--quiet", "--script", "skills/info-hive/scripts/wiki_mcp_launch.py"],
      "cwd": ".",
      "env": { "PYTHONUTF8": "1" },
      "env_vars": [
        "INFO_HIVE_DATA_DIR", "INFO_HIVE_MCP_IDLE_SECONDS", "INFO_HIVE_EMBED_THREADS",
````

- [skills/info-hive/scripts/wiki_codex.py 54 行目から](https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/skills/info-hive/scripts/wiki_codex.py#L54-L72)

````
def adapt(text: str) -> str:
    """ホストの呼び出し名とパスの表記を変える。コマンドの引数の値は扱わない。"""
    text = text.replace("${CLAUDE_PLUGIN_ROOT}/skills/info-hive", "<skill-root>")
    text = text.replace("${CLAUDE_PLUGIN_ROOT}", "<plugin-root>")
    text = text.replace("skills/info-hive/references/", "<skill-root>/references/")
    text = text.replace("$ARGUMENTS", "<利用者の引数>")
    text = re.sub(r"/wiki:([a-z]*)", lambda m: "$wiki:info-hive" + (" " + m[1] if m[1] else ""), text)
    return text.replace("Claude Code のデスクトップアプリ", "Codex のデスクトップアプリ")


def workflow(root: Path, operation: str) -> str:
    """正本から本文を読む。操作名は固定の一覧に限定してパスの脱出を防ぐ。"""
    if operation not in wiki_help.PREFERRED_ORDER or operation == "help":
        raise ValueError(f"使えない操作: {operation}")
    text = (root / "commands" / f"{operation}.md").read_text(encoding="utf-8")
    match = wiki_help.FRONTMATTER_RE.match(text)
    if match is None:
        raise ValueError(f"操作手順の frontmatter がない: {operation}")
    return HEADER + adapt(text[match.end():].lstrip())
````

- [hooks/hooks.json 1 行目から](https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/hooks/hooks.json#L1-L16)

````
{
  "description": "指示に関係しそうなwikiの候補を知らせる（ADR-0034）。プロジェクトの環境を作らず、既存のPython 3.12〜3.14を独立モードで使う。起動に失敗しても末尾のexit 0で利用者の指示を止めない。",
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "uv run --no-project --no-config --quiet --quiet --offline --no-python-downloads --python \">=3.12,<3.15\" python -I -S \"${CLAUDE_PLUGIN_ROOT}/skills/info-hive/scripts/wiki_prompt_hook.py\"; exit 0",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
````

## 3 つの層と書き込み

- [skills/info-hive/references/architecture.md 5 行目から](https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/skills/info-hive/references/architecture.md#L5-L42)

````
## 3つの層

### raw ソース

raw ソースは、ユーザーが選んだ入力資料である。`raw/`（またはプロジェクトの `SCHEMA.md` が指定する場所）に置く。raw ソースは**変更不可**である。LLM は読むだけで、変更しない。この変更不可という性質は重要である。wiki が壊れても raw ソースからいつでも導き直せるし、ユーザーが独立して確かめられる、変わらない正しい情報源にもなる。

`raw/` に置くもの: PDF、Web ページ（`wiki_fetch.py` で本文を Markdown にしたもの。日本語でなければその訳文と、本文の画像と画像の補足。Obsidian Web Clipper で保存した markdown でもよい）、文字起こし、コードリポジトリ、データセットの説明、スクリーンショット、ユーザーが wiki に取り込んでほしい手書きのメモ。`raw/` に置かないもの: LLM が生成したもの。それらはすべて wiki の層に属する。例外は Web ページの訳文と画像の補足で、原本から機械とモデルが作ったものとして raw に置き、保存したあとは原本と同じく変更しない（ADR-0004）。原文の HTML は保存せず、frontmatter に URL と原文の SHA-256 を記録する。

便利な規約として、1つのソースを1つのファイルにする（論文と付録のように複数の部分からなるソースなら、1つのディレクトリにする）。ファイル名はページのスラッグと同じ規則で付け（日本語を使ってよい。英字は小文字にし、空白は使わない）、wiki のソースの要約ページのスラッグとそろえる（`raw/インボイス制度の手引き.pdf` と `wiki/sources/インボイス制度の手引き.md`）。こうすると、wiki から raw ソースへの参照が簡単になる。

### wiki

wiki は、LLM が生成した markdown ファイルのディレクトリである。この層はすべて LLM が受け持つ。ページを作り、新しいソースが届けば更新し、相互参照を保守し、全体の一貫性を保つ。ユーザーは wiki を読み（たいていは Obsidian で読むが、どの markdown ビューアーでもよい）、LLM が書く。

wiki のディレクトリは、慣例として**ページの種類**ごとのサブディレクトリに分ける。

- `wiki/sources/`: 取り込んだソースごとの要約ページ。ソースが何を言っていたかを、LLM の言葉で、raw ファイルへの出典つきで記録する。ほぼ追加するだけのページで、ソースを取り込むときに1つ書き、そのあとはめったに変更しない。
- `wiki/entities/`: 具体的なもののページ。人、製品、論文、場所、企業、出来事などで、固有名詞を持つもの、または Wikipedia の記事の題材になりそうなものすべてである。新しいソースがそのエンティティに触れるたびに更新が積み重なる。
- `wiki/concepts/`: 考え方、手法、フレームワーク、抽象概念のページ。もっとも多く相互参照されるページで、理解が深まるにつれてもっとも変わりやすい。
- `wiki/synthesis/`: 横断的な分析、比較、保存したクエリの回答。調べた内容が積み重なる場所である。ユーザーが求めた比較が、次のクエリの土台になるページになる。

`SCHEMA.md` で、ほかの種類を追加してもよい（エンジニアリングチームなら `wiki/decisions/`、ファンの wiki なら `wiki/characters/`、研究室なら `wiki/experiments/` など）。新しい種類を追加するのに手間はかからない。ディレクトリを作り、スキーマに書き、インデックスのテンプレートを更新すればよい。

### スキーマ

`SCHEMA.md` は wiki のルートに置く**設定ファイル**で、汎用の LLM を、このナレッジベースを決まった規約で保守する担当者にする。使っているページの種類、タグの体系、命名の規約（日本語と英語のどちらの名前にするか迷うページの扱いなど）、独自のワークフローの手順、ユーザーの書き方の好み（「コンセプトのページには必ず `## なぜ重要か` のセクションを入れる」「要約では箇条書きを使わない」など）を記す。

スキーマはユーザーと一緒に**改訂していく**。初期化のときは `assets/SCHEMA.md.template` の既定のテンプレートから始まるが、ユーザーは自分の分野に合うものが分かってくるにつれて、それぞれカスタマイズしていく。ユーザーの編集やフィードバックに、スキーマに書かれていない繰り返しのパターンを見つけたら、追加を提案する。スキーマが自己矛盾を起こし始めたり、扱いにくいほど大きくなったりしたら、整理を提案する。

既存の wiki に入るときは、最初にスキーマを読む。スキーマの規約は、スキルに書いた既定値より優先される。

### グラフ（コンパイルで生成する任意の層）

wiki には、`wiki/graph/` に4つ目の層を置ける。ページの frontmatter にある型付きの `graph:` メタデータと、本文の wikilink を、コンパイルしてクエリできるようにしたものである。手で編集する `ontology.yaml`（どのノードの種類と述語があるかを決める取り決め）と、`wiki_graph_extract.py` が生成する成果物（`nodes.jsonl`、`edges.jsonl`、`graph.sqlite`、`graph.graphml`）を含む。**正本は Markdown である。**グラフは削除して markdown から生成し直しても、知識は失われない。

グラフの目的は、出典の裏づけを持つ型付きの関係を、markdown の編集しやすさや人の読みやすさを手放さずに、機械でクエリできるようにすることである。たとえば「誰が何を創業したか」「あるライブラリは何に依存しているか」「A から B への最短経路」といったクエリである。型付きエッジには、明示的な `source`（ソースページのスラッグ）と `evidence` の引用（ソースの文をそのまま写したもの）が必要で、抽出スクリプトがそれをでっち上げることはない。本文の通常の wikilink（`[[slug]]`）からは確信度の低い `mentions` エッジが生まれる。これはナビゲーションには役立つが、証拠にはならない。

ユーザーの質問の多くが関係を問うもので、型付きメタデータを保守する手間に見合う効果があるときに、グラフ層を使う。テキストだけの wiki では使わない。詳しいリファレンスは `graph-workflow.md` である。
````

- [skills/info-hive/scripts/wiki_initialized.py 1 行目から](https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/skills/info-hive/scripts/wiki_initialized.py#L1-L9)

````
"""wiki_initialized.py — 初期化された wiki かを決める（info-hive-dev の ADR-0019）。

初期化された wiki は、ルートがディレクトリで、その直下の `SCHEMA.md` が通常のファイル（シンボリックリンクなら、
リンクの先が通常のファイル）であるものとする。`SCHEMA.md` は `init_wiki.py` が初期化で必ず作り、上書きしない。
中身は読まない。

wiki のパスを受け取る入口（CLI、MCP のツール、閲覧、Web ページの取得、経験の記録、アップグレード）は、どれも
ここで確かめる。ライブラリの関数（lint や索引の関数）は確かめない。

````

- [commands/ingest.md 15 行目から](https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/commands/ingest.md#L15-L21)

````
2. **ソースが `session`、`session:<ID>`、`session:<パス>`、`codex:<ID>`、または `.jsonl` のファイルなら、下の「セッションの取り込み」の S1〜S10 に進む（手順 3〜8 は、S3〜S10 の中で行う）。** 引数が既存のファイルのパスなら、キーワードより先にファイルとして扱う。`.jsonl` は、セッションの記録と認められなければ止まり、ユーザーが明示して頼んだときだけ、ふつうのソースとして取り込む。**PDF で `rag` の MCP ツールが使える場合は、原本を移動・複製せず、次の PDF 登録手順を先に実行する。** **ソースが YouTube の URL（ホストが `youtube.com` か `youtu.be`）なら、Web ページより先に、下の「YouTube の動画の取り込み」の V1〜V10 に進む（手順 3〜8 は、V6〜V10 の中で行う）。** **ソースが `http` か `https` の URL なら、下の「Web ページの取り込み」のとおりに、raw の段（W1〜W8）を `wiki:web-raw` に任せて `<RAW_ROOT>/` に保存してから、W9 で手順 3 に進む。** その他のソースは、下の「ローカル資料の保存」に進む。ファイル名は `skills/info-hive/references/page-conventions.md` の命名の規則で付け、ソースの要約ページのスラッグとそろえる。日本語の題名なら日本語のファイル名でよい（`インボイス制度の手引き-2023.pdf`）。
   保存と版の検査が成功してから、受け取った raw を手順 3 で読む。
3. ソースを読む。大きい場合（約 1 万文字を超える、英語なら約 5,000 語を超える、または長い PDF）は分割して読む。コンテキストウィンドウの約 25% を超えるなら、全体を一度にコンテキストに読み込んではならない。
4. wiki に何かを書く前に、要点をユーザーと簡単に話し合う。目立つ点、既存のページとつながる点、意外な点を挙げる。
5. wiki を調べて、このソースが関係する既存のページを洗い出す。候補のページはそれぞれ読んで確かめる。
6. `<WIKI_ROOT>/sources/` にソースの要約ページを書く。関係するエンティティやコンセプトのページは、`str_replace` で必要な箇所だけを更新する。新しいエンティティやコンセプトには新しいページを作り、それぞれに少なくとも1つの被リンクを付ける。ページの更新と作成を終えたら、要約ページの `## 関係するページ` の直前に `## 取り込んだ内容と載せたページ` の表を置き、抜き出した主張ごとに、番号、取り込んだ内容、出典の該当箇所、掲載方法（`create`、`update`、`source_only` のどれか）、掲載ページと理由を残す（`skills/info-hive/references/ingest-workflow.md` の手順 7b）。表は実際にしたことの記録であり、表のためにページを作ったり更新したりしない。インデックスを更新し、`log.md` に `## [YYYY-MM-DD] ingest | <ソースの題名>` の形で1行追記する。操作名の `ingest` は英語のまま書く。
7. `<WIKI_ROOT>/graph/ontology.yaml` があり、今回の取り込みで型付きの `graph.relationships[]` を追加した、または追加できる場合は、ソースが明示的に裏づけている場合に限って型付きのエッジを追加する（述語、ソースページのスラッグ、証拠となる引用、確信度、ステータスを付ける）。次にグラフの lint をかける。wiki の MCP サーバーのツール `lint` が使える場合は、`wiki=<WIKI_ROOT の絶対パス>` を渡し、結果の `graph.findings` を見る。使えない場合は `uv run --script "${CLAUDE_PLUGIN_ROOT}/skills/info-hive/scripts/wiki_graph_lint.py" "<WIKI_ROOT>"` を実行する。検出結果をユーザーと一緒に仕分けてから、`uv run --script "${CLAUDE_PLUGIN_ROOT}/skills/info-hive/scripts/wiki_graph_extract.py" "<WIKI_ROOT>"` を実行する。`log.md` の取り込みの行の下に、`   グラフ: ノード +N、型付きエッジ +M` というサブ行を追記する。
````

- [commands/ingest.md 78 行目から](https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/commands/ingest.md#L78-L84)

````
## PDF の登録（rag が有効な場合）

1. `python "${CLAUDE_PLUGIN_ROOT}/skills/info-hive/scripts/wiki_raw_ingest.py" pdf --wiki "<WIKI_ROOT>" --raw-root "<RAW_ROOT>" --source "<ユーザーが指定した PDF>"` を実行する。失敗したら理由を伝えて止まる。成功したら要約ページのスラッグを決め、`rag` MCP サーバーの `register_pdf` に `wiki_root=<WIKI_ROOT の絶対パス>`、`source=<検査の JSON が返した source>`、`source_page="sources/<スラッグ>.md"`、`title=<題名>` を渡す。`source` はスクリプトが返したパスの綴りを使う。ユーザーが指定していない PDF は登録しない。ツール名は接続に表示されたものを使う。別プラグインの内部パスを組み立ててスクリプトを実行しない。PDF を閲覧するだけの場合は登録しない。
2. 応答の `job_id` を記録する。`queued`、`running`、`paused` は受付・処理中であり、索引化や wiki の取り込み完了と報告しない。原本を `<RAW_ROOT>` へコピーしない。登録を拒まれたら、理由（絶対パスでない、PDF でない、UNC パス、rag の派生データの中にある、など）をそのまま伝える。
3. `job_status(wiki_root, job_id)` で進捗を確認する。短時間待つ場合は `wait_seconds=30` を使い、細かい連続呼び出しを避ける。処理中に会話を終える場合はジョブ ID と再開待ちの状態を報告し、ここで手順を止める。次回 rag の MCP 接続時に未完了ジョブは自動再開する。キャンセル済みのジョブは自動再開しない。
4. `completed` のときだけ `result.extracted_markdown` を分割して読み、通常の手順 4〜8 に進む。要約ページの `raw` には `result.raw`（`/` 区切りの絶対パス）を、`raw_sha256` には `result.sha256` を、`rag_job_id` にはジョブ ID を書く。値は二重引用符で囲み、`\` は `\\`、`"` は `\"` と書く。内容を読む前に要約を作らない。
5. `failed` は理由を報告し、修正後は `retry_job` で再試行する。`cancelled` の再試行は明示的に依頼された場合だけ行う。
````

## MCP のプロセスと検索

- [skills/info-hive/scripts/wiki_mcp_launch.py 6 行目から](https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/skills/info-hive/scripts/wiki_mcp_launch.py#L6-L19)

````
"""wiki の MCP の中継（wiki_mcp_relay.py）を起動する入口。プラグインの .mcp.json から起動する。

標準ライブラリだけで書き、依存を持たない。.mcp.json から `uv run --script wiki_mcp_relay.py` で中継を
直接起動すると、uv が中継の依存を入れている途中でホストに止められたとき（セッションの終わりなど）、
環境が作りかけのまま残り、それ以降の起動がすべて失敗する。この入口には壊れる依存がない。
中継の環境を確かめ、壊れていれば入れ直してから、その python で中継を動かす。

- 標準入力と標準出力は MCP の通信に使うので、そのまま中継に渡す。uv の出力は標準エラーに書く。
- 引数はそのまま中継に渡す（`--ensure` など）。終了コードは中継のものを返す。
- 中継の環境を用意できなかったときは、理由を標準エラーと `<データの置き場所>/logs/launch.log` に書いて止まる。
  uv が TLS 証明書を検証できなかったとき（TLS を検査する社内ネットワーク）は、OS の証明書ストアを使って
  1 回だけやり直す（wiki_mcp_common._uv_sync）。

CLAUDE_PLUGIN_ROOT を持たないホスト（Codex など）は、このファイルのパスを指定して起動する。
````

- [skills/info-hive/scripts/wiki_mcp_relay.py 9 行目から](https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/skills/info-hive/scripts/wiki_mcp_relay.py#L9-L19)

````
"""wiki の MCP サーバーへの stdio の中継（ADR-0012）。プラグインの .mcp.json から起動する。

ホストは中継を stdio の MCP サーバーとして起動する。中継は、127.0.0.1 の wiki の MCP サーバーにツールの一覧と
呼び出しをそのまま渡す。ツールの定義はサーバーから受け取るので、中継には書かない。

- server.lock を取り、server.json の指すサーバーが生きていて版が同じならそれを使う。なければ起動する。
  同時に起動された中継があっても、サーバーは 1 つしか起動しない。
- サーバーは要求がない時間が続くと止まる。中継はセッションの間ずっと動くので、呼び出しが失敗したら
  サーバーを確かめ直し（必要なら起動し）、接続し直して 1 回だけやり直す。
- サーバーは中継の子として、Windows では窓のない自分のコンソール（CREATE_NO_WINDOW）と新しいプロセスグループで、
  POSIX では新しいセッションで起動する。中継やホストが終わってもサーバーは残り、次のセッションの中継が使う。
````

- [skills/info-hive/scripts/wiki_index.py 1 行目から](https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/skills/info-hive/scripts/wiki_index.py#L1-L17)

````
"""wiki の MCP サーバーが持つ検索の基盤（ADR-0011）。

- 埋め込み: cl-nagoya/ruri-v3-130m の ONNX fp32 を fastembed（onnxruntime）で動かす
- ベクトル索引: usearch の HNSW（f16、コサイン、connectivity 16、expansion_add 256、expansion_search 1,024）
- 語彙検索: Tantivy の BM25。wiki の索引には wiki_search.tokenize() の bigram のトークンを入れる
- 融合: RRF（k 30、語彙の重み 0.5、候補は片側 200 件）
- wiki の距離の上限: 0.208

索引の集まり（Collection）は、台帳（SQLite）、usearch のファイル、Tantivy のディレクトリの 3 つでできている。
台帳を正とし、usearch と Tantivy は台帳から作り直せる派生物として扱う。更新の途中で止まったときは、
台帳の dirty の印を見て、次に開いたときに 3 つをそろえ直す（reconcile）。

書き手はこのプロセス（wiki の MCP サーバー）だけである。同じプロセスの中の検索とは、書き手を優先する
読み書きロックで分ける。usearch は一時ファイルに保存してから os.replace で置き換える。Tantivy の commit が
失敗したら rollback し、同じ変更を入れ直す。

MCP には依存しない。テストと測定から直接呼べる。
````

- [skills/info-hive/references/mcp-server.md 31 行目から](https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/skills/info-hive/references/mcp-server.md#L31-L45)

````
## ツール

| ツール | 中身 |
| --- | --- |
| `query` | ハイブリッド検索（BM25 と埋め込みを RRF で融合）。結果の形は `wiki_search.py --json` と同じ |
| `get_page` | 1 ページの frontmatter（日本語の別名のキーを英語にそろえたもの）と本文 |
| `list_index` | `index.md` の本文と `indexes/` の一覧。`name` を渡すと `indexes/` のそのファイル |
| `lint` | 構造の lint（`wiki_lint.py --json` と同じ結果）と、オントロジーがあればグラフの lint（`wiki_graph_lint.py --json`）。検査するだけで直さない |
| `stats` | 規模、構成、リンク密度の集計（`wiki_stats.py --json` と同じ結果）と、索引の状態とサーバーの版 |
| `graph` | グラフ（`graph/graph.sqlite`）への問い合わせ（`wiki_graph_query.py --json` と同じ結果）。DB は読み取り専用で開く |
| `index_chunks` | rag などからチャンクを受け取り、wiki の外の索引に加える |

**拒んだリンクの知らせ（`link_warnings`）。** wiki の記事か記事までの道がリンク（シンボリックリンク、ジャンクション、名前の代理のリパースポイント、ハードリンク）なら、どのツールもその記事を読まない（info-hive-dev の ADR-0029）。`query`、`get_page`、`list_index`、`lint`、`stats`、`graph` の結果には、読まなかったものを `link_warnings`（`{"path", "kind"}` の並び。なければ空）で必ず付ける。`get_page` と `list_index` の `name` で、リンクなので読まない記事を名前で引くと、「見つからない」ではなく「リンクなので読まない」のエラーを返す。

`index_chunks` 以外のツールには、`wiki` に wiki のルートの絶対パスを渡す。渡すのは初期化された wiki（ルートに `SCHEMA.md` がある）のルートである。`SCHEMA.md` のないディレクトリには、どのツールも「初期化された wiki ではない」のエラーを返し、索引も作らない。そのときは CLI でやり直さず、`/wiki:init` を提案する。`lint`、`stats`、`graph` は、同じ名前のスクリプトの関数をサーバーの中で呼ぶ。結果のキーも CLI の `--json` と同じ英語のままである。
````

- [skills/info-hive/references/mcp-server.md 104 行目から](https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/skills/info-hive/references/mcp-server.md#L104-L136)

````
### index_chunks

rag がチャンクを渡すためのツールである。wiki の Markdown は変えない。索引は collection ごとに分け、wiki の索引とは混ぜない。

| 引数 | 説明 |
| --- | --- |
| `collection` | 索引の名前。英小文字、数字、`_`、`-` の 1〜64 文字 |
| `tokenizer` | 語彙検索のトークンの作り方の名前（例: `sudachi-c-normalized-v1`）。collection を作ったときの値と違えば失敗する |
| `generation` | 世代。整数 |
| `chunks` | 各要素に `id`（collection の中で一意）、`text`、`tokens`（文字列の配列）、`doc`（文書の識別子）、任意の `metadata`、任意の `vector` か `vector_b64`（ruri-v3-130m の 512 次元。リトルエンディアンの float32 を base64 にしたもの） |
| `delete_docs` | 丸ごと消す文書の識別子 |
| `reset` | 真なら collection を作り直す（`tokenizer` を変えるとき） |

- 語彙検索のトークンは呼び出し側が作る。サーバーは分かち書きの辞書を持たない。検索するときも、`query` に同じ作り方の `query_tokens` を渡す。
- ベクトルがないチャンクは、サーバーが「検索文書: 」の接頭辞を付けて埋め込む。
- 渡したチャンクの `doc` ごとに、`generation` より古い世代の行を消す。同じ `id` を渡すと置き換える。
- 1 回の要求の本文は 64 MiB まで。ベクトルつきなら 1,000〜2,000 件ずつに分けて渡す。
- 同じ `id` と `generation` で渡し直しても結果は変わらない。中継は、サーバーが呼び出しの途中で止まると、つなぎ直して同じ呼び出しを 1 回だけやり直す。

## 置き場所

| OS | 場所 |
| --- | --- |
| Windows | `%LOCALAPPDATA%\info-hive\` |
| macOS、Linux | `$XDG_DATA_HOME/info-hive/`（未設定なら `~/.local/share/info-hive/`） |

その下に次を置く。

- `server.json`: 動いているサーバーのポート、トークン、pid、コードの版。中継だけが読む。
- `index/<wiki のハッシュ>/`: wiki ごとの索引。wiki のルートの絶対パスから作る。ユーザースコープとプロジェクトスコープの wiki は別の索引になる。wiki の中の `.wiki-cache/` には置かない。
- `index/collections/<名前>/`: `index_chunks` の索引
- `models/`: 埋め込みモデルのファイル（固定の revision から取得し、sha256 を確かめる）
- `logs/server.log`: サーバーのログ
````

- [skills/info-hive/references/mcp-server.md 148 行目から](https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/skills/info-hive/references/mcp-server.md#L148-L156)

````
## MCP が使えないとき

サーバーの依存を取得できない、uv がない、などで MCP が使えないときは、今の CLI がそのまま使える。

```bash
uv run --script "<skill-root>/scripts/wiki_search.py" "<検索語>" --wiki "<WIKI_ROOT>" --json
python "<skill-root>/scripts/wiki_search.py" "<検索語>" --wiki "<WIKI_ROOT>" --json --no-embed
```

````

- [skills/info-hive/scripts/wiki_search.py 8 行目から](https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/skills/info-hive/scripts/wiki_search.py#L8-L13)

````
# ///
"""
wiki_search.py — wiki のページを対象にした、セクション単位の BM25 とローカルのハイブリッド検索。

既定のセマンティック検索には FastEmbed と sqlite-vec を使う。BM25 は、--no-embed を付ければ
依存パッケージなしで使え、安全な代替手段としても残っている。
````

## ページの解釈とグラフ

- [skills/info-hive/scripts/wiki_pages.py 1 行目から](https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/skills/info-hive/scripts/wiki_pages.py#L1-L19)

````
"""
wiki_pages.py — wiki のページの集合と、wikilink の抜き出しと解決の規則。

lint、検索（とそれを使う MCP の索引）、グラフ、統計、判定レイヤーが共通で使う。のちに閲覧（browse）の
中核も使う。規則を 1 か所に置くのは、スクリプトごとに規則を書くと食い違うからである（ADR-0010 の決定の 1）。
標準ライブラリ、wiki_text、同梱した markdown-it-py（_vendor/）だけで書き、単独では実行しない。

- ページは、wiki のルートからの相対パスが `.md`（大文字と小文字は問わない）で終わり、最上位の SCHEMA.md、
  index.md、log.md、README.md と、最上位の indexes/、graph/、raw/、assets/、.evolution/、.wiki-cache/ に
  当たらず、どの要素の名前も `.` で始まらないファイルである。
- wiki の側の記事（is_article_path）は、ページと、最上位の index.md、log.md、SCHEMA.md と、indexes の下の .md である。
  記事と記事までの道のリンクは、読まず、たどらず、Walk.links と article_path() の結果で知らせる（info-hive-dev の
  ADR-0029）。リンクの判定は wiki_links.link_kind() の 1 か所にある。
- wikilink は、閲覧が使う markdown-it（commonmark、html は無効、表は有効）が本文の文字とするところだけから
  拾う。コードブロックの中、インラインのコードの中、参照リンクの定義の中のものは数えない。
- パスとリンクの行き先は NFC にそろえて比べ、大文字と小文字を区別する。
- wiki をたどる経路は walk_markdown() の 1 つで、ページ（walk_pages）と索引のファイル（walk_index_files）は、
  起点を変えて同じたどり方を使う。最上位の除く名前の項目と、名前が `.` で始まる項目には、どの OS の呼び出しもしない。
  OS の呼び出しの失敗は、read_os() の 1 か所で「ない」「分からない」「そのほか（送出）」に分ける。設計は info-hive-dev の
````

- [skills/info-hive/scripts/wiki_graph_extract.py 8 行目から](https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/skills/info-hive/scripts/wiki_graph_extract.py#L8-L19)

````
"""
wiki_graph_extract.py — Markdown の wiki を、クエリできるグラフにコンパイルする。

正本は Markdown のままである。このスクリプトは wiki のすべてのページを読み、ノードとエッジ
（`graph.relationships` から作る型付きの意味のエッジと、暗黙の `mentions`、`sourced_from`、
`summarizes_raw` のエッジ）を導き、`<wiki>/graph/` の下に成果物を出力する。成果物はいつでも削除して作り直せる。

PyYAML の固定した依存を持つので、`uv run --script` で実行する。

オントロジーがないときは、グラフ層を導入する前の wiki として扱い、何も書き出さずに
終了コード 1 で止まる。生成物はすべて一時ファイルに書き終えてから置き換えるので、書いている
途中で止まっても前の生成物が残る。同じ出力先の extract は、ロックで 1 つずつ動かす。
````

- [skills/info-hive/references/graph-workflow.md 87 行目から](https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/skills/info-hive/references/graph-workflow.md#L87-L100)

````
## 型付きエッジを追加するか、ふつうの `[[wikilink]]` にするか

次の場合は、型付きエッジを追加する。

- 特定のソースが、その関係を明示的に述べている。
- 証拠として引用できる文がある。
- その述語が、あとのクエリで意味を持つ（「誰が何を創業したか」「山田太郎は何を提案したか」）。

次の場合は、ふつうの `[[wikilink]]` を使う。

- 関係が暗黙的である、雰囲気でしかない、または留保を付けたい。
- その主張を、1つのソースの引用に結びつけられない。
- どちらにしても述語が `mentions` になる。

````

- [skills/info-hive/references/graph-workflow.md 145 行目から](https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/skills/info-hive/references/graph-workflow.md#L145-L161)

````
### 問い合わせ（query）

```bash
python "<skill-root>/scripts/wiki_graph_query.py" wiki/ neighbors --node company:やまだ製作所
python "<skill-root>/scripts/wiki_graph_query.py" wiki/ edges    --subject person:山田太郎 [--predicate founded]
python "<skill-root>/scripts/wiki_graph_query.py" wiki/ path     --from person:山田太郎 --to concept:消費税 [--max-depth 6]
python "<skill-root>/scripts/wiki_graph_query.py" wiki/ facts    --about company:やまだ製作所
```

`--json` は、lint と query のどちらでも使える。query は標準ライブラリだけで動くので、`python` で実行する。

ツールの `graph` では、`command` に `neighbors`、`edges`、`path`、`facts` のどれかを渡し、引数は `node`、`subject`（と任意の `predicate`）、`from_node` と `to_node`（と任意の `max_depth`）、`about` を使う。結果は `--json` と同じ形である。ツールは `graph.sqlite` を読み取り専用で開き、作らない。オントロジーがない wiki、`graph.sqlite` がない wiki、見つからないノードはエラーになる。

関係を問う質問（「X とつながっているものは？」「Y を提案したのは誰？」「A から B への経路をたどって」）では、次のようにする。

1. いつもどおりインデックスを読む。
2. `graph.sqlite` が古い（`log.md` にある最新の `## [YYYY-MM-DD] ingest |` の行より前に作られた）なら、先に extract で作り直す。
````

## browse の閲覧経路

- [skills/info-hive/scripts/wiki_browse.py 8 行目から](https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/skills/info-hive/scripts/wiki_browse.py#L8-L20)

````
"""
wiki_browse.py — wiki の閲覧（browse）の入口。

    uv run --script wiki_browse.py build <WIKI_ROOT> [--out DIR] [--raw text|link|basename|none] [--scope user|project]
    uv run --script wiki_browse.py serve <WIKI_ROOT> [--raw-root DIR] [--page SLUG] [--no-open] [--idle-timeout 秒] [--scope user|project]
    uv run --script wiki_browse.py stop <WIKI_ROOT>
    uv run --script wiki_browse.py core          （標準入力から 1 行に 1 つの JSON の要求を読む）

build は静的の HTML を書き出す（既定の書き出し先は <data_dir>/browse/<wiki_key>/）。serve は 127.0.0.1 だけで
待ち受けるサーバーを起動し、動いていれば使い回す。stop はサーバーを止める。core は、中核を Python 以外から
呼ぶための JSON の入出力である。どれも Wiki のファイルを変えず、Wiki のルートの下には何も作らない。browse は、
領分（<data_dir>/browse/ と、--out の書き出し先の隣の作業用のディレクトリ）の外では、自分が作ったものだけを
置き換え、消す。設計は `docs/plans/wiki-browse-stage1-2026-11-09.md` と
````

- [skills/info-hive/scripts/wiki_browse_core.py 1 行目から](https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/skills/info-hive/scripts/wiki_browse_core.py#L1-L16)

````
"""
wiki_browse_core.py — 閲覧（browse）の中核。

Wiki を読んで写し（Snapshot）を作り、そこからページ、リンク、被リンク、関係表、ナビゲーション、診断を組み立て
（Core）、ページの HTML を描く。入出力は呼ばない（読むのは wiki_browse_fs.py の口を通す）。静的の書き出しと
サーバーは、どちらもこのモジュールの同じ関数でページを描く（守ること 6）。設計は
`docs/plans/wiki-browse-stage1-2026-11-09.md` の 2〜5 と、`docs/plans/wiki-browse-structure-2026-11-11.md` の
4、5、8 にある。

ページの集合、リンクの解決、`sources:` の解決は、lint と同じ wiki_pages の関数で決める（守ること 2）。
関係表だけが PyYAML（グラフの抽出）を使う。PyYAML がなければ、関係表は「使えない」になる。

写しは、内容（入力ごとの種類、相対パス、文字か読めない理由、世代）だけを持ち、Path と、機械の絶対パス（Wiki の
ルート、ホーム、data_dir）を持たない。Core は、内容だけを受け取る（設計の 8）。
"""

````

- [skills/info-hive/scripts/wiki_browse_core.py 1328 行目から](https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/skills/info-hive/scripts/wiki_browse_core.py#L1328-L1341)

````
            except Exception:  # noqa: BLE001  本文のリンクを取り出せないページは、リンクなしで続ける
                links = []
                problems = list(problems) + [{"kind": "unreadable_graph", "reason": "unexpected"}]
            gpages.append({"path": p["rel_path"], "rel_path": p["rel_path"],
                           "disk_rel_path": disk, "slug": p["slug"], "meta": meta, "body": p["body"],
                           "links": links, "fm_problems": problems})
        try:
            _nodes, page_node_ids, _aliases = wiki_graph_extract.build_nodes(gpages, ontology, diag)
            edges = wiki_graph_extract.build_edges(gpages, page_node_ids, diag, link_warnings=self.link_warnings)
        except Exception:  # noqa: BLE001  オントロジーの中の形が誤っている（node_types が配列など）
            self.relations_state = "error"
            self.diagnostics.append({"kind": "relations_error", "reason": "invalid"})
            return
        self.relations_state = "ok"
````

- [CHANGELOG.md 9 行目から](https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/CHANGELOG.md#L9-L24)

````
## [0.38.1] - 2026-11-19

### 修正

- サーバー版 browse の Mermaid 描画枠は、同じオリジンのタブをまたいで一度に 1 つだけ動かす。埋め込みや開き元のあるページには原稿を表示する。URL を直接開いた場合と同じタブでの記事移動では、従来どおり図を表示する。

## [0.38.0] - 2026-11-19

### 追加

- Codex セッションの取り込みでは、原本の raw と、ツール通知を省いた会話版を保存する。両方に同じ伏せ字と削除指定を適用し、発言番号をそろえる。両方の版を承認してから保存し、browse の raw から開ける。

## [0.37.0] - 2026-11-19

### 追加

````

- [skills/info-hive/references/overview-workflow.md 1 行目から](https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/skills/info-hive/references/overview-workflow.md#L1-L14)

````
# ページの概要を作る

`wiki_overview.py prepare` が返す `page_copy` を入力とする。読むのはこのページの写しだけである。
ページにない事実を足したり、リンク先のページを読んで内容を加えたりしない。

## 目的

SVG と Mermaid を使って、このページの内容を理解しやすいようにしてください。重要な詳細を省くことなく、大きな画像と簡潔な文章で説明してください。独自のセンスを活かし、手抜きなデザインは避け、必要に応じてアイコンとビジュアルを組み込んでください。写真は使いません。利用できるスキルの一覧に、図を作るスキルがあって用途に合うものだけを、厳選して使ってください。文章や詳細を記述する際は、明確かつ簡潔・端的にし、専門用語は避けてください。閲覧者がこの分野の初心者であるかのように説明してください。

## 下書きの形

`draft_dir` の直下に、frontmatter のない `overview.md` と、参照する `<名前>.svg` を Write ツールで置く。
名前は半角の英小文字・数字から始め、その後も英小文字・数字・ハイフンだけを使い、40文字以下にする。
SVG は12個以下、1つ2 MiB以下、本文は UTF-8 で64 KiB以下、組み立てた概要は8 MiB以下にする。
````
