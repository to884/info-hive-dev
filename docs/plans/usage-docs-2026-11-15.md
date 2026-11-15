# info-hive の利用者向け文書：構成と作業の計画（6 版、2026-11-15）

| 項目 | 内容 |
| --- | --- |
| 状態 | 作者が承認した計画（2026-11-14）を写し、着手の確認（段階 1）の結果を足した。Sol の敵対的レビューを 4 回受けた（1 版は重大 6 件、2 版と 3 版は重大 1 件、4 版は重大 2 件。どれも条件付きで採用可）。4 回目の指摘を直したのが 5 版である（[レビューの記録](../agent-runs/2026-11-15-usage-docs-plan/README.md)）。5 版に、段階 2 の前の wiki 0.19.3 での読み直しを足したのが 6 版である |
| 関連 | [ADR-0022](../adr/0022-usage-docs-are-html-in-plugin-docs.md)（文書の置き場所と形式）、[ADR-0021](../adr/0021-wiki-browse-uses-fluent2-replica.md)（`/wiki:browse` の Fluent 2。承認）、移植計画 `docs/porting-plan.html` の P0、[段階 2 の確認表](../research/usage-docs-stage2-checklist-2026-11-15.md) |

## 背景

info-hive のプラグインの使い方を、まったく知らない人に説明する文書を作る。読者は Claude Code を使ったことはあるが、Python、uv、GitHub の認証には詳しくない。2026-11-14 に既存の文書を監査して構成案を出し、作者の返事と追加の質問の回答を反映したのがこの計画である。この計画だけで作業を進められるように書く。

監査の要点は次のとおり。

- `info-hive-wiki/docs/` は移植元の訳がもとで、チュートリアルが 1 本もない。`getting-started.md` は名前だけがチュートリアルで、中身は 9 種類のエージェントの導入の選択肢である。
- 前提条件の記述が実態と合わない。Python 3.12 以上が要る（wiki 0.11.0）こと、git が要ることが書かれていない。「リポジトリは非公開なので `gh auth login` が要る」とあるが、4 つのリポジトリはすべて PUBLIC である。
- `docs/commands.md` は `/wiki:help` が実行時に読む（`skills/info-hive/scripts/wiki_help.py`）。消したり移したりできない。
- `search.md` は、0.4.0 から先に使う MCP サーバーの検索（ruri-v3-130m、usearch、Tantivy）を書いていない。

## 着手の条件と、段階 1 の確認の結果（2026-11-15）

作者の指示で、wiki 0.15.0 のリリースが終わるまで作業をしなかった。条件と、確かめた結果は次のとおりである。

| 条件 | 結果 |
| --- | --- |
| to884/info-hive-dev#103 がマージされている | マージ済み |
| `info-hive-wiki` の main に 0.15.0 のコミットがある | ある。main はさらに 0.16.0（to884/info-hive-wiki#59、セッションの取り込み）まで進んでいる |
| `v0.15.0` のタグと GitHub リリースがある | ある（2026-11-14T14:48:56Z）。最新は v0.16.0 |
| マーケットプレイスから導入できる | 0.16.0 の導入を、別のセッションが確かめた（to884/info-hive-dev#110 のリリースの記録）。この PC に入っているのは 0.11.0 のままで、ここでは確かめていない |

材料は 0.16.0（info-hive-wiki の 8c400d7）で読み直した。この計画に関わる変更は次のとおりである。

- 0.15.0: URL の取り込みの raw を作る段（W1〜W8）を、プラグインのエージェント `wiki:web-raw`（`model: sonnet`）に任せるようにした。手順は `commands/ingest.md` から `skills/info-hive/references/web-raw.md` に移った。W4（Web ページの取り込み）はこの流れで書く。
- 0.16.0: `/wiki:ingest session` で、Claude Code のセッションの会話を取り込めるようにした（ADR-0020）。`docs/commands.md` の `/wiki:ingest` の節に段落が増えた。作者は、この取り込みのハウツーを足さないと決めた（「段階 1 で作者が決めたこと」の 1）。
- ローカルのファイルの取り込み（W1、W2 の練習用のソース）の手順は変わっていない。

ほかのセッションの作業との関係:

| 作業 | 状態 | この計画への影響 |
| --- | --- | --- |
| `/wiki:browse` の画面を Fluent 2 にする設計（to884/info-hive-dev#105、ADR-0021） | 開いている。プラグインの側はブランチ `feature/browse-fluent2` | `fluent2.css` を書き換えずに `skills/info-hive/scripts/browse_assets/` に写し、出どころ、版、SHA-256 を記録し、`fluent2.js` は使わない、と決めている。文書も同じ扱いにする（ADR-0022）。ADR の番号は 0021 が使われているので、文書の ADR は 0022 にした |
| browse の構造の直し（to884/info-hive-wiki#60、0.17.0、to884/info-hive-dev#108） | 開いている | W2 は `/wiki:browse` の画面を見せる。0.17.0 と、#105 の Fluent 2 の画面が入ってから、段階 2 の写しを取る |
| 「info-hive-wiki の Cowork 互換性」のセッション | 成果物（ブランチ、文書）は見つからなかった | 段階 2 で、Cowork を一から確かめる |
| 「Diátaxis ドキュメント構造設計」のセッション | 成果物は見つからなかった | なし |

## 決まったこと

| 項目 | 決定 |
| --- | --- |
| 範囲 | 共通と wiki の文書。rag の文書は今回は作らない（構成案は末尾に残す） |
| 置き場所 | `info-hive-wiki/docs/`（共通のページも置く） |
| 既存の文書 | `info-hive-wiki/docs/` をその場で作り直す。上級の機能の 4 本（`search.md`、`graph.md`、`decisions.md`、`evolution.md`）は今回は Markdown のまま残す |
| 原稿の形式 | HTML を直接書く。見た目は Fluent 2 の Web 版（`fluent2-html-replica` スキル）に寄せる。`commands.md` だけは `/wiki:help` のために Markdown の正本として残す |
| PDF | Vivliostyle を候補にして、試作で決める |
| 公開先 | 試作のあとで決める |
| 図 | 要る所だけ、埋め込みの SVG にする。Fluent 2 の Web 版のデザイン言語に従い、`diagram-design` と `plannotator-effective-html` のスキルで作る |
| Claude Code 以外 | 対象にしない。`agents.md` は手を入れずに残す |
| 基準の環境 | Windows 11 と Claude のデスクトップアプリ（Code タブ）。Cowork での違いはハウツー 1 本（C6）に分ける |
| wiki のスコープ | 空の練習用フォルダーに、プロジェクトの wiki を作る。ユーザースコープはハウツー（W3）にする |
| 練習用のソース | 文書に載せる短い Markdown |
| 文体 | すべてです・ます体。`commands.md` も書き直す |
| 認証 | 確かめてから決める（2-2） |

この形式の決定は、移植計画 `docs/porting-plan.html` の P0 の決定（docs は Markdown だけを残し、サイトの仕組みは削る）と、`info-hive-wiki/UPSTREAM.md` の「docs サイトを持たず、`docs/` の Markdown だけを残すため」を変える。決定と理由は [ADR-0022](../adr/0022-usage-docs-are-html-in-plugin-docs.md) に記録した。

## 段階 1 で作者が決めたこと（2026-11-15）

1. **セッションの会話の取り込み（0.16.0）のハウツーは足さない。** 初めての人の一本道に要らず、伏せる文字列を決める手順が長いので、ハウツー 1 本では済まない。`commands.md`（W6）の節と、`/wiki:help ingest` で引ける。
2. **W2 の写しは、browse の 0.17.0（to884/info-hive-wiki#60）と Fluent 2 の画面（to884/info-hive-dev#105）が入ってから取る。** 先に取ると、W2 の画面の写しを取り直すことになる。その代わり、W2 は段階 2 で最後に確かめる。
3. **ADR-0022 を承認した。**

## 段階 2 の前の読み直し（2026-11-15、wiki 0.19.3）

上の 2 の条件は、同じ日にそろった。to884/info-hive-dev#105（ADR-0021）と to884/info-hive-wiki#60（browse の 0.17.0）がマージされ、Fluent 2 の画面は 0.18.0 でリリースされた。最新は v0.19.3（`info-hive-wiki` の fb2de97）である。そのため、W2 は段階 2 の最後に回さず、W1 に続けて通す（下の段階 2 の 5 と、確認表の確認 5）。

0.16.0 から 0.19.3 までの変更のうち、この計画に関わるものは次のとおりである。

- 0.17.0〜0.19.3: `/wiki:browse` の作りを直し、画面を Fluent 2 にした。左の木、検索、索引のページの全ページの一覧と絞り込み、配色の切り替えが加わった。W2 の写しは、この画面で取る。
- 0.18.1: URL の取り込みの raw の段で、取り直したときの扱いと、W8 の `check --finish --json` を決めた。W4 はこの流れで書く。
- MCP サーバーの起動、`/wiki:init`、`/wiki:help`、ローカルのファイルの取り込み、`/wiki:query`、`/wiki:lint` の定義とスクリプトは変わっていない。2-3 の取得のきっかけ、2-5 の目印、確認表のパスと名前は、そのまま使える。

## 段階 1 で調べたことと、決まったこと

（2026-11-14 に作者の問いに答えた内容。番号は、そのときの問いの番号である。）

出典は wiki 0.14.1 と rag 0.5.3 の origin/main、Claude の公式の文書（code.claude.com、claude.com/docs/cowork、support.claude.com）である。2026-11-15 に wiki 0.16.0 で読み直し、この節に関わる変更がないことを確かめた（変わったのは、URL とセッションの取り込みだけである）。

### 2-1 uv のほかに要るソフトウェア

| もの | 要る場面 | 根拠と確かさ |
| --- | --- | --- |
| Claude のデスクトップアプリ | すべて | 基準の環境 |
| Git for Windows | GitHub のマーケットプレイスからプラグインを入れるとき | 公式の文書（plugins/host-marketplace）。デスクトップアプリに git が同梱されているかは未確認 |
| uv | MCP サーバーとスクリプトのすべて | `.mcp.json` が `uv run` で起動する。デスクトップアプリは PowerShell のプロファイルを読まないので、PATH はユーザーの環境変数に入れ、アプリを起動し直す |
| Python 3.12 以上 | MCP サーバーと、`python` を直接呼ぶコマンド | wiki 0.11.0。MCP サーバーの Python は uv が取ってくる。`init`、`ingest`、`query`、`lint`、`stats`、`graph`、`help`、`upgrade` のコマンドの定義は `python` を直接呼ぶ。Windows 11 の `python` が Microsoft Store を開く別名だけのときに失敗するかは未確認 |
| ブラウザ | `/wiki:browse` | デスクトップアプリではブラウザのペインで開く（`commands/browse.md:17`） |

C1 には、基準の環境で要るもの（Git for Windows、uv、必要なら Python 3.12）を入れる手順を含める。環境ごとの違いと社内のプロキシは C2 に置く。

社内のプロキシ（Zscaler など）の内側では、uv にシステムの証明書を使わせる。次のコマンドを PowerShell で 1 回実行し、アプリを起動し直す。C2 と C3 に書く。

```powershell
[Environment]::SetEnvironmentVariable("UV_SYSTEM_CERTS", "true", "User")
```

この設定は、uv の版に結びつけて書く。`UV_SYSTEM_CERTS` は新しい uv だけが読む名前で、古い uv はこれを黙って無視し、`UV_NATIVE_TLS` だけを読む。しかも、プラグインの MCP サーバーの起動処理は、どちらかの名前が設定されていると「利用者が決めた」とみなし、OS の証明書ストアでのやり直しをしない（`wiki_mcp_common.py` 452〜465 行）。そのため、古い uv に `UV_SYSTEM_CERTS` だけを設定すると、設定しないときより悪くなる（やり直せば通る環境で、`UvTlsError` で止まる）。C2 は次の順に書く。

1. `uv sync --help` の出力に `UV_SYSTEM_CERTS` があるかを確かめる（どちらの名前を読むかは、プラグインも同じ方法で決めている。`wiki_mcp_common.py` の `system_certs_env()`）。
2. なければ、先に uv を新しくする（C1 の入れ方なら `uv self update`）。新しくできないときだけ、`UV_SYSTEM_CERTS` の代わりに `UV_NATIVE_TLS` を設定する。
3. `UV_SYSTEM_CERTS` を設定し、アプリを起動し直す。

C1 では最新の uv を入れるので、チュートリアルの読者は 1 で `UV_SYSTEM_CERTS` があるはずである。どの版から読むかは、段階 2 で確かめる。

古い uv で `UV_SYSTEM_CERTS` が設定されているとやり直さない作りは、プラグインの側の問題でもある（設定された名前をこの uv が読まないなら、利用者の設定として扱わない、と直せる）。段階 2 の「プラグインの不具合が見つかったとき」と同じに扱い、直すかを作者に諮る。

### 2-2 GitHub の認証（確かめ直した結果）

- marketplace、wiki、rag の 3 つのリポジトリは PUBLIC である。認証情報を使わない `git ls-remote https://github.com/to884/<名前>.git` で main を読めた（2026-11-14）。
- 公式の文書によると、Claude Code は `owner/repo` をまず `ssh -T git@github.com` で試し、成功すれば SSH、失敗すれば HTTPS で取る。公開のリポジトリなら GitHub の認証は要らない。
- ただし、同じ文書を読むかぎり、`source: github` のプラグイン（wiki と rag はこれ）をセッションの中の `/plugin` で入れるときと更新するときは HTTPS に切り替わらない。そのため、GitHub の SSH の鍵がない利用者は失敗するおそれがある。回避の手段として、環境変数 `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1` が挙がっている。段階 2 でいちばん先に確かめる。
- 鍵のない環境で認証なしに入れば、認証のハウツーは書かない。失敗するなら、C1 と C2 に `CLAUDE_CODE_PLUGIN_PREFER_HTTPS` の設定を足す。GitHub の認証の設定はさせない。

### 2-3 なぜファイルが大きいのか（利用者への説明の方針）

wiki は、文章を外部のサービスに送らず、API キーも料金も使わずに、利用者の PC の中で検索する。そのために、文章の意味を数値（ベクトル）に変える日本語のモデルと、それを動かす道具を、最初に一度だけ PC に取ってくる。2 回目からは保存したものを使う。

取ってくるきっかけは、プラグインの中で起きる 3 つの出来事である。読者の手順とは 1 対 1 に結びつかない。とくに 3 つ目は、エージェントが検索を使うと決めたときに起きる。`/wiki:query` は、索引から候補が見つかれば検索をしない（`commands/query.md:15` の手順 2〜4）ので、W1 の質問で起きるとは限らない。

| きっかけ（プラグインの中の出来事） | 何を取ってくるか | 大きさ | 何のためか | 保存先 |
| --- | --- | --- | --- | --- |
| MCP サーバーの起動（`.mcp.json` の `uv run`。Claude Code がプラグインの MCP サーバーに接続しようとしたとき） | MCP サーバーの依存（onnxruntime、usearch、tantivy など） | 約 1 GB | 検索を数十ミリ秒で返す常駐のサーバー | uv のキャッシュ |
| `setup_wiki.py` の実行（`/wiki:init` と `/wiki:upgrade`） | 多言語の埋め込みモデル multilingual-e5-small と FastEmbed | 約 0.25 GB | スクリプトの検索。`"status": "ready"` はこの準備が済んだことを示す（`setup_wiki.py:27`） | `~/.cache/info-hive/fastembed` |
| MCP のツール `query` の最初の呼び出し（rag の `index_chunks` でも起きる） | 日本語の埋め込みモデル ruri-v3-130m | 約 530 MB | MCP サーバーの意味の検索。サーバーは起動したときにも、`stats` でも取らない（`wiki_mcp_server.py:397`）。`query` で裏で取り始め、取り終えるまでは語彙の検索だけで答える（同 205 行と 255 行以降） | `%LOCALAPPDATA%\info-hive\models` |

文書の書き方は、次のようにする。

- 1 つ目と 2 つ目は、手順で起きるので、その手順（C1、W1 の `/wiki:init`）に、何を取るか、待ち時間の目安、保存先を書く。
- 3 つ目は、手順に結びつけない。W7（解説）と C3（うまくいかないとき）に、「エージェントが wiki の検索を初めて使ったときに、日本語のモデルを裏で取る。取っているあいだも答えは返る」と書く。チュートリアルには、取り終えたことの目印を置かない。W1 の成功に要らないためである。

表の値は、コードと文書に書かれた目安である（ruri は `references/mcp-server.md` と README、e5-small は `wiki_search.py` と `commands/init.md`）。足すと約 1.8 GB になる。`tests/wiki/check_first_run_mcp.py:11` の「約 1.5 GB」はコメントで、計った値ではなく、`/wiki:init` の FastEmbed の準備も含まない。文書に書く大きさと時間は、段階 2 で計った値にする。

### 2-4 再接続の方法

- MCP サーバーの起動に失敗すると、Claude Code はその失敗を約 15 分覚えている。表示は `Skipping connection (recent failure cached; retries automatically in 15 min, ...)` である（公式の文書の errors のページ）。stdio のサーバーは、最初の接続に失敗しても自分では再試行しない。
- 利用者が再接続するには、`/mcp` でサーバーを選んで Reconnect を押すか、`/mcp reconnect all` を実行する（公式の文書の mcp のページ、`references/mcp-server.md:170`）。
- デスクトップアプリの Code タブと Cowork で `/mcp` が使えるかは未確認なので、段階 2 で確かめる。使えなければ、アプリを起動し直す方法だけを書く。
- サーバーが動くかは `wiki_mcp_launch.py --ensure` で手で確かめられる。ログは `%LOCALAPPDATA%\info-hive\logs\launch.log` と `server.log` にある。

### 2-5 ここでいう「成功」とは

チュートリアルの各手順が、意図したとおりに済んだことを指す。読者が自分の目で判断できるように、毎回同じに現れる「目印」を手順ごとに示す。

目印に使ってよいものは、次の 2 種類に限る。

- **スクリプトかコマンドの定義が決めるもの。** ファイルの名前と場所、決まった書式の行、スクリプトの出力の値。読者は、エクスプローラー、`/wiki:browse`、会話の中のツールの呼び出しの欄（実行したコマンドとその出力）で見る。
- **コマンドの定義が、出力をそのまま示すように命じているもの。** `/wiki:help` の一覧（`commands/help.md:16`）がこれに当たる。

次のものは、目印に使わない。

- エージェントの返答の文章（毎回変わる。「完了しました」も使わない）
- コマンドの定義が転載を命じていないスクリプトの出力（`/wiki:init` の JSON は、エージェントが要約して返してもよいので、返答の本文には出ないことがある。`commands/init.md:15`）
- エージェントが判断して作るもの（どのページを作るか、ページの数、ページどうしのリンク）。取り込みの手順は、主張をソースの要約に残すこと（`source_only`）を認め、表のためにページを作ることを禁じている（`references/ingest-workflow.md` 269、303〜311 行）

この規則で、目印は次のとおりにする。

| 手順 | 成功の目印 |
| --- | --- |
| プラグインを入れる | プラグインの一覧で `wiki@info-hive` が有効になる。`/wiki:help` が 11 本のコマンドを並べる |
| `/wiki:init` | ツールの呼び出しの欄に、`setup_wiki.py` の出力の JSON があり、`"status": "ready"` を示す（`ready` 以外の値はない。失敗は「エラー: …失敗した（終了コード N）」）。`wiki/SCHEMA.md` などのファイルは、実行環境の準備より先に作られるので、成功の目印にしない。ツールの呼び出しの欄がデスクトップアプリでどう見えるかは、段階 2 で確かめる |
| 取り込み | 読者は練習用のソースを `raw/味噌.md` の名前で置き、そのパスを渡す。ソースの要約のスラッグは raw のファイル名から決まる（`references/ingest-workflow.md` 39〜51 行）ので、`wiki/sources/味噌.md` ができる。`wiki/log.md` の末尾に、`## [<今日の日付>] ingest | ` で始まる行が 1 つ増える（同 337 行）。`wiki/index.md` には、味噌の要約へのリンクの行が増える。決まるのはリンク先だけで、書き方は決まらない（別名付きの `[[味噌\|味噌の要約]]` も規約で認められている。`references/page-conventions.md:56`）ので、文書では「`[[味噌` で始まるリンクの行が増える」と書き、`[[味噌]]` の文字列を目印にしない。ほかのページの行が増えることもある、と書く |
| 質問 | 答えに、`[[` で始まる出典が 1 つ以上付く。出典の数とページは指定しない |
| 2 本目の取り込み | `wiki/sources/醤油.md` ができ、`/wiki:browse` の索引に「味噌」と「醤油」の 2 つの要約が並ぶ |
| lint | 「問題がない」という結果は、検査できなかったときにも出る。読めなかったページはリンクの検査から外され（`wiki_lint.py` 437 行あたり）、一覧を取れなかったディレクトリのページは、検査の対象にも `read_errors` にも入らない（`wiki_pages.py:324`、`wiki_lint.py:333`）。そこで、目印は、問題がないことに加えて、検査したことを示す値で作る。ツールの呼び出しの欄の lint の結果で、調べたページの数（CLI の「調べたページ数」、`--json` と MCP の `summary` の `total_pages`。同 689 行）が 2 以上（`wiki/sources/` の味噌と醤油）であり、かつ、リンク切れの wikilink、孤立ページ、読めなかったページ（`read_errors`）の項目がない。結果の形は経路で違う。MCP のツール `lint` なら、その 3 つの一覧が空の JSON になる。CLI の `wiki_lint.py` は 0 件の項目を出さず、問題がなければ「問題は見つからなかった。」と出す（同 728 行以降）。返答の本文の「0 件」は目印にしない。どちらの経路になるかと、MCP の結果の形は、段階 2 で写して確かめる |

ページどうしのつながりは、W2 で見せたいことである。目印にはできないので、W2 では、読者がつながりを頼む形にする。取り込みの途中の話し合いの手順（`references/ingest-workflow.md` の「要点を話し合う」）で、読者が返す言葉を文書で決める。W1 では「『麹』のページを作ってください」、W2 では「『麹』のページに、醤油のことも書き足してください」と返す。そのうえで、`/wiki:browse` で「麹」のページを開き、2 つの要約からの被リンクを見る。これは目印ではなく「こうなるはずです」という案内にとどめ、ならなかったときに何をするか（「麹」のページを開いて、書き足すよう頼む）を添える。段階 2 で、頼んだとおりになるかを確かめる。

### 2-6 練習用のソースの提案

- 文書に載せる短い日本語の Markdown を 2 本、こちらで書く。題材は「味噌」と「醤油」にする。どちらも原料に大豆、麹、塩が出てくるので、2 本目を取り込むと、同じ「麹」や「大豆」のページに両方からリンクが付きやすく、W2 でつながりを目で見られる。
- 質問の例は「味噌と醤油に共通する原料は？」である。答えに付く出典の数とページは、エージェントが読んだページで決まるので、文書では指定しない（2-5）。
- 内容は一般的な事実だけにし、書いたあとに出典で確かめる。
- 代わりの案は、架空の町の図書館の利用案内 2 本である。事実を確かめる手間はないが、題材として興味を持ちにくい。

### 2-7 `/wiki:init` の質問に指定する答え

`references/retrieval-setup.md:27-30` の質問に、チュートリアルでは次のように答えさせる。

| 質問 | 答え |
| --- | --- |
| 範囲 | プロジェクト。Code タブで開いた練習用フォルダー（`%USERPROFILE%\info-hive-practice`。Windows 11 では「ドキュメント」が OneDrive に同期されていることがあるので、その下は使わない）の `wiki/` と `raw/` |
| モデルのキャッシュ | 既定の場所 |
| グラフ層 | 後回し |
| エージェントとの連携 | 練習用フォルダーの `CLAUDE.md` に追記する（承認する） |

空のフォルダーを使うので、`SCHEMA.md` のない `wiki/` があるときの追加の質問は出ない。

### 2-8 エージェントのメモリとの連携

Claude Code は、新しいセッションを始めるたびに、前のセッションの内容を覚えていない。その代わり、起動するときに `CLAUDE.md` を読む。`/wiki:init` は、この `CLAUDE.md` に、wiki の場所と使い方を書いた短い節（`## LLM Wiki`）を足すことを提案する。中身は「先に `wiki/index.md` を読む」「答えには `[[wikilink]]` で出典を付ける」「規約は `wiki/SCHEMA.md` にある」などである。

これがないと、`/wiki:*` のコマンドを使わずに「〜について教えて」と頼んだとき、エージェントは wiki を読まずに自分の知識で答えることが多い（`references/agent-memory-integration.md:3`）。プロジェクトの wiki ならプロジェクトの `CLAUDE.md` に、ユーザースコープの wiki ならグローバルな指示に書く。プラグインは承認なしには書き込まない。この説明は W7（解説）に置く。W1 の手順では「承認する」とだけ書き、W7 へリンクする。

Cowork は `CLAUDE.md` を同じようには扱わない。代わりに、Settings の Cowork にある Global instructions、フォルダーの指示、プロジェクトの指示を使う（公式の文書の cowork/guide/projects）。接続したフォルダーの `CLAUDE.md` を Cowork が読むかは未確認である。読まないなら、`/wiki:init` が提案する節を Cowork のどこに貼るかを C6 に書く。

### 2-9〜2-12

- 2-9: 用語は C5「用語集」1 ページにまとめる。
- 2-10: rag の情報を 1 ページ（rag の早見表）にまとめる。rag の文書を作るときに行う。今回は P0 に、rag とは何かを短く書き、rag の README へリンクするだけにする。
- 2-11: 更新の手順を C4 に書く。
  - 公式の文書の順序は、マーケットプレイスの一覧の更新（`/plugin marketplace update info-hive`）、プラグインの更新（`claude plugin update wiki@info-hive`）、`/reload-plugins` である。
  - 続けて `/wiki:upgrade` を実行する。
  - 独自のマーケットプレイスは、既定では自動で更新されない（`/plugin` の Marketplaces で Enable auto-update を選べる）。Cowork では Customize の Plugins で Check for updates を使う。
  - Code タブの GUI での操作は未確認で、段階 2 で確かめる。
- 2-12: すべてのページをです・ます体にする。`commands.md` も書き直す。`/wiki:help` の一覧と個別のヘルプの冒頭の説明と引数の説明は、`commands/*.md` の frontmatter（`description`、`argument-hint`、`argument-description`）から作られる（`wiki_help.py` 120〜190 行、520〜528 行）。`/wiki:help` をです・ます体にそろえるなら、この frontmatter も書き直す。frontmatter の `description` は Claude Code のコマンドの一覧にも出る。

### 4-9 「成功の出力を取る」とは

2-5 の目印が、実際の画面ではどう見えるかを、文書に載せるために記録する作業である。新しい環境で、チュートリアルの手順を書いてあるとおりに 1 つずつ実行し、各手順の出力を写し取る。写すのは、`/wiki:init` の JSON、作られたファイルの一覧、`/wiki:help` の一覧などである。文書には、この写しのうち目印の部分を載せる。開発用の PC には、すでにモデルや設定があり、初めての人と同じ出力にならないので使わない。

## 構成

読む順番は P0 → C1 → W1 → W2 の一本道にする。チュートリアルは Code タブで進め、Cowork での違いは C6 に分ける。すべて `info-hive-wiki/docs/` に、です・ます体の HTML で置く。各ページは、`docs/assets/` の `fluent2.css` と、新しく作る文書の配置と印刷の CSS を読む。`fluent2.js` は使わない（ADR-0021 と同じ理由で、要素の `style` に書き込むため。文書のページに要るふるまいはない）。

| # | ファイル（仮） | 種類 | 目的 | 主な材料 | 図 |
| --- | --- | --- | --- | --- | --- |
| P0 | `index.html` | 入口（4 種類の外） | wiki とは何か、何ができるか、rag とは何か、読む順番 | 既存の `index.md` の前半、`marketplace.json` の `description`、rag の README の冒頭 | ソース → wiki のページ → 出典つきの答え |
| C1 | `tutorial-install.html` | チュートリアル | Git for Windows と uv を入れ、プラグインを入れ、`/wiki:help` で 11 本のコマンドを見る | マーケットプレイスの README、既存の `getting-started.md` の Claude Code の節、`wiki_help.py` の出力、段階 2 の写し | なし |
| C2 | `howto-prepare.html` | ハウツー | 必要なソフトウェアの環境ごとの違い、`UV_SYSTEM_CERTS`、2-2 の結果しだいで `CLAUDE_CODE_PLUGIN_PREFER_HTTPS` | 2-1、2-2、CHANGELOG 0.11.0、uv の公式の手順 | なし |
| C3 | `howto-troubleshoot.html` | ハウツー | MCP サーバーが起動しない、15 分の記録、再接続、ログ、`--ensure` | wiki の README のトラブルシューティング、2-4 | なし |
| C4 | `howto-update.html` | ハウツー | プラグインの更新と、続く `/wiki:upgrade` | マーケットプレイスの README、2-11 | なし |
| C5 | `glossary.html` | リファレンス | 用語（wiki、raw、`SCHEMA.md`、取り込み、lint、シンセシス、wikilink、MCP、スコープなど） | 各文書、`SCHEMA.md` のテンプレート | なし |
| C6 | `howto-cowork.html` | ハウツー | Cowork で入れて使う。Customize からの導入、フォルダーの接続、指示の置き場所、使えない機能 | 公式の文書、段階 2 の確認 | なし |
| W1 | `tutorial-first-wiki.html` | チュートリアル | 練習用フォルダーにプロジェクトの wiki を作り（2-7）、「味噌」を取り込み、質問する | `commands/init.md`、`ingest.md`、`query.md`、`references/retrieval-setup.md`、`init_wiki.py` と `setup_wiki.py` の出力 | なし |
| W2 | `tutorial-second-source.html` | チュートリアル | 「醤油」を取り込み、`/wiki:browse` でつながりを見て、`/wiki:lint` をかける | `commands/browse.md`、`lint.md` | なし |
| W3 | `howto-user-wiki.html` | ハウツー | ユーザースコープの wiki を作り、グローバルな指示に場所を書く | 既存の `getting-started.md` の置き場所の節、`references/agent-memory-integration.md` | なし |
| W4 | `howto-web-page.html` | ハウツー | Web ページの取り込み（0.15.0 の流れで書く） | `commands/ingest.md`、既存の `commands.md` | なし |
| W5 | `howto-upgrade-wiki.html` | ハウツー | `/wiki:upgrade` と `SCHEMA.md` のマージ | `commands/upgrade.md`、既存の `upgrade.md` の手順の部分 | なし |
| W6 | `commands.md`（＋ `commands.html` を作るかは試作で決める） | リファレンス | `/wiki:*` の 11 本 | 既存の `commands.md`、`commands/*.md` の frontmatter | なし |
| W7 | `explanation-how-wiki-works.html` | 解説 | 取り込み、問い合わせ、lint で起きること、正本が Markdown である理由、メモリとの連携（2-8）、rag との違い | 既存の `workflows.md`、`index.md` の「仕組み」と FAQ | 取り込みの流れ |

既存のファイルの扱い:

- `index.md`、`getting-started.md`、`workflows.md`、`upgrade.md` は、上のページに中身を移して消す。README、`SKILL.md`、`references/query-workflow.md` からのリンクを、新しいページに張り替える。
- `upstream-changelog.md` は開発の記録なので、info-hive-dev の `docs/upstream/` に移す。`UPSTREAM.md` のリンクと表を直す。移植元から訳して取り込んだ文書を作り直したことを、`UPSTREAM.md` の表に 1 行足す。`docs/upstream/translation-hashes.txt` は取り込みの時点の記録なので、変えない。
- `agents.md` と、上級の機能の 4 本（`search.md`、`graph.md`、`decisions.md`、`evolution.md`）は、Markdown のまま残す。P0 と W6 から「上級の機能」としてリンクする。HTML にしてです・ます体にそろえるのは、別の作業にする。
- `docs/assets/` には、`fluent2-html-replica` の `assets/fluent2.css` を書き換えずに写す。browse（ADR-0021）と同じ版にし、出どころ、基準の版、SHA-256、写し直す手順を `docs/assets/README.md` に書き、ライセンスの文書を `docs/assets/licenses/` に置く。browse の `browse_assets/fluent2.css` を直接読まないのは、公開先（GitHub Pages の `/docs` など）では `docs/` の外を読めないためである。同じ 626KB を 2 か所に持つことになるので、SHA-256 が一致することを試験で確かめる。

プラグインが増えたら、そのプラグインのリポジトリの `docs/` に、チュートリアルを 1〜2 本、要るハウツー、コマンドのリファレンスを 1 本、要れば解説を 1 本置く。P0 に 1 節を足し、読む順番では依存先の後ろに置く。用語は C5 に足す。

開発用のもの（info-hive-dev に置く）:

- `tools/docs/`（仮）: Vivliostyle の設定、リンクの検査。`commands.html` を作る場合は、その変換
- `docs/research/usage-docs-facts-<日付>.md`: 段階 2 で取った出力の写しと、確かめた事実
- `docs/plans/usage-docs-<日付>.md`: この計画の写し（レビューの対象）

## 作業の段階

1. **着手の確認**（2026-11-15。条件と材料の読み直しは済み）
   - 「着手の条件」とほかのセッションを確かめ、材料を 0.16.0 で読み直す。
   - この計画を `docs/plans/` に写し、ADR-0022 を足す。
   - `ask-codex` で Sol の敵対的レビューにかけ、指摘を原因の構造で直す。
2. **事実の確認**
   - 実行するのは作者である。デスクトップアプリへのサインインと、新しい OS のユーザーや VM を作る作業は、エージェントにはできない。
   - エージェントが渡すものは 2 つある。1 つは、手順と確かめる点を並べた確認表（`docs/research/` に置く）。もう 1 つは、各手順で写してほしい出力の一覧である。
   - 環境は、開発用の PC ではない、新しい Windows 11 にする。同じ PC に新しいユーザーを作っただけでは、PC 全体に入っている git や Python を共有してしまい、2-1 を確かめられない。新しく作った VM か別の PC を使う。Cowork は PC の上の VM を使うので、入れ子の仮想化ができる環境が要る。Windows Sandbox では動かないおそれがある。
   - 試行は、どれも決まった初めの状態から始める。初めの状態は 2 つあり、ハウツーの確認のために 3 つ目（S2）を作る。
     - **素の状態（S0）**: OS とデスクトップアプリへのサインインだけを済ませ、git、uv、プラグインを入れていない状態。VM のスナップショットに取る。
     - **導入後の状態（S1）**: C1 を終えた状態。MCP サーバーの依存は取ってあるが、e5 と ruri のモデルはまだ取っていない（どの wiki も初期化しておらず、検索もしていない）。スナップショットに取る。S1 を作るために、`/wiki:init` や検索をしてはならない。e5 と ruri は PC で共有するキャッシュに入るので、一度取ると、W1 が初めての取得にならなくなる。
     - S1 は、プラグインの版に結びつく。スナップショットの名前に、入れた wiki の版を書く（`plugin.json` の `version`）。文書に書く版が変わったら、古い S1 に戻して W2 だけを確かめることはしない。S0 から C1 をやり直して新しい版の S1 を作り、W1 から通す。独自のマーケットプレイスは既定では自動で更新されないので、古い S1 に戻すと、古い版のプラグインのまま試すことになる。
     - **W2 のあとの状態（S2）**: W1 と W2 の 3 回目を終えた状態。練習用の wiki と、e5 と ruri のキャッシュがある。スナップショットに取る。ハウツーの確認（下の 6）と MCP の接続の確認（下の 7）は、S2 から始める。Cowork と社内のプロキシの確認は S1 に戻して行うので、S2 を取らないと、ハウツーで使う wiki が残らない。
   - 1 回の試行は、スナップショットに戻して始める。前の試行の wiki、`CLAUDE.md`、会話、PC で共有するモデルのキャッシュが残ったまま、次の試行をしない。S2 から始めたあとに、新しい練習用フォルダーと新しいセッションで足りるのは、モデルの取得を含まないハウツーの確認（下の 6）だけである。
   - 確かめる順は次のとおり。前の確認の結果に後の確認が左右されないように、要るソフトウェアから順に確かめる。
     1. S0 で、git の有無を確かめる（デスクトップアプリに git が同梱されているか、PATH にあるか）。なければ C1 の手順で Git for Windows を入れる。
     2. git がある状態で、SSH の鍵を置かずに、Code タブからマーケットプレイスを追加し、wiki を入れられるか（2-2）。入れるのは GUI か `/plugin` か。失敗したら、`CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1` で入るかを確かめる。
     3. 大きさと時間を、2-3 の 3 つのきっかけごとに、別々に計る。計測では、チュートリアルの手順がきっかけを起こすことを当てにせず、きっかけそのものを起こす操作をする。どれも、操作の直前と、取り終えた時点の両方で、uv のキャッシュ、`%LOCALAPPDATA%\info-hive\models`、`~/.cache/info-hive/fastembed` の大きさを記録する。
        - MCP サーバーの依存: S0 から C1 を通し、「プラグインを入れる直前」から「`wiki_mcp_launch.py --ensure` が終了コード 0 で終わった」まで。`--ensure` の終了コード 0 は、依存がそろい、サーバーが動いていることを示す（`wiki_mcp_relay.py:313`）。Claude Code の側がつながったことは示さないので、つながったかは 7 で別に確かめる。
        - e5: S1 から W1 の `/wiki:init` を実行し、「実行の直前」から「ツールの呼び出しの欄の `"status": "ready"`」まで。
        - ruri: e5 のあと、作った wiki に対して、MCP のツール `query` を呼ぶよう、エージェントにはっきり頼む（「wiki の MCP のツール `query` で『味噌』を検索して」）。ツールの呼び出しの欄で `query` が呼ばれたことを確かめ、「呼ぶ直前」から「`%LOCALAPPDATA%\info-hive\models` の ruri のフォルダーに `verified.json` ができた」まで。この計測は、W1 の試行とは別の回にする（W1 の質問の結果を変えないため）。
     4. 必要なソフトウェアの残り（2-1）。`python` が Microsoft Store の別名だけのときの動きと、uv の PATH。
     5. W1 と W2 を、S1 から、書く予定の手順のとおりに 3 回通す。各回は S1 のスナップショットに戻して始める（新しいフォルダーだけでは、e5 と ruri のキャッシュが残る）。各手順の出力を写し（4-9）、2-5 の目印が 3 回とも出ることと、2-5 の「頼む形」のつながりができるかを記録する。目印が 1 回でも出なかったら、その目印は使わず、2-5 の規則に合う別の目印を考え直す。
     6. ハウツー（C2〜C6、W3〜W5）のコマンドを実行する。実行できなかったものは、文書で未確認と書く。
     7. Code タブと Cowork で、MCP サーバーがつながったことを、読者がどこで見られるか（`/mcp` の一覧など）。`/mcp` の再接続が使えるか（2-4）。`/wiki:help` は MCP サーバーを使わず、uv がなくても 11 本を並べる（`commands/help.md:11`）ので、C1 の目印は MCP の接続を確かめない。つながったことを C1 の目印に足すかは、ここで見られる場所が分かってから決める。
     8. Cowork でマーケットプレイスを追加して wiki を入れ、MCP サーバーが動くか、`CLAUDE.md` を読むか（C6）。
     9. Zscaler の環境で、`UV_SYSTEM_CERTS` を設定する前と後の動き（使える環境があれば）。
   - プラグインの不具合が見つかったとき（`python` の別名で止まる、SSH の鍵なしで入らない、Cowork が `CLAUDE.md` を読まないなど）は、チュートリアルを壊れた手順のまま出さない。文書の回避策で一本道を保てるなら回避策を書き、保てないならプラグインを先に直す（別の作業として切り出し、直った版を待つ）。どちらにするかは、見つかった時点でユーザーに諮る。
3. **試作**
   - W1 を 1 ページだけ書く。部品は `fluent2-html-replica` の `references/` のマークアップを使い、独自の装飾もトークンの CSS 変数で書く。
   - `fluent2.css` には印刷の指定がないので、印刷用の CSS を足す。
   - P0 の図を 1 つ、`diagram-design` と `plannotator-effective-html:html-diagram` で、Fluent 2 のトークンの色と書体を使った SVG にし、HTML に埋め込む。
   - Vivliostyle で PDF を出す。確かめる点は、目次と前後のページへの移動、改ページ、コードブロック、リンク、日本語の書体の埋め込み、明るい表示と暗い表示、スマートフォンの幅である。
   - 作者が試作を見て、次の 3 つを決める。
     - PDF の道具
     - HTML の公開先: GitHub はリポジトリの中の `.html` をソースのまま表示するので、README と `/wiki:help` のリンクから読める場所が要る。案ごとに、次の 3 つにどう答えるかを示して決める。
       - 版の対応: 古い版のプラグインの `/wiki:help` のリンクを開いたとき、その版の文書が出るか。最新の版だけを配る公開先なら、ADR-0022 の「版がそろう」は、リポジトリの中の文書についてだけ言えることになる。そう決めるなら、ADR に書く
       - `wiki_help.py` の書き換えの規則: 今の規則は、`./tutorial-first-wiki.html#first-source` を `https://github.com/to884/info-hive-wiki/blob/v0.16.0/docs/tutorial-first-wiki.html#first-source` に書き換える（GitHub ではソースのまま表示される）。規則を変えるなら、`tests/wiki/test_help_command.py`（441〜480 行が GitHub のタグの URL を期待する）も一緒に直す
       - 公開の手順: リリースの手順のどこで公開し、何を確かめるか
     - `commands.html` の作り方: `commands.md` から変換するか、作らずに `commands.md` へリンクするか
   - 試作を Sol のレビューにかける。
4. **共通と wiki のページ**
   - P0、C1〜C6、W1〜W7 を書く。
   - `commands.md` と `commands/*.md` の frontmatter をです・ます体に書き直す。`commands.md` は、`` ## `/wiki:<名前> ...` `` の見出しとインラインのリンクの規則（`docs/commands.md:177`、`tests/wiki/test_help_command.py`）を守る。
   - 消すファイルと移すファイルへのリンクを、すべて張り替える。参照するファイルを並べて探すと漏れる（1 版で挙げなかった `CHANGELOG.md:467` が `docs/upstream-changelog.md` を指している）ので、消す・移すファイルの名前ごとに、`info-hive-wiki` の全体を Grep して、見つかったものをすべて直す。たとえば `search.md:7` は `./workflows.md#wiki-にクエリする` を指している。`CHANGELOG.md` の過去の版の項は書き換えず、リンク先だけを移した先に直す。
   - P0 を除く各ページを `diataxis` の classify にかけて 1 つの種類に収まるか確かめ、`natural-japanese` で推敲する。P0 は、作者が決めたとおり 4 種類の外の入口であり、分類の対象にしない。
   - Sol のレビューにかける。
   - wiki のパッチ版でリリースする。`/wiki:help` の出力が変わるので、利用者に見える変更である。
   - 段階 3 で決めた公開の手順で公開し、公開した URL で各ページが表示されること、`/wiki:help <コマンド>` の詳細のリンクが公開したページを開くことを確かめる。ここまで済んで、この段階を終えたとする。
5. **後始末**: CHANGELOG の日付を直し、プロジェクトの wiki に記録し、worktree とブランチを消す。

リリースは AGENTS.md の手順に従う。`git fetch` で版を確かめ、プラグインの PR を先にマージし、次に親のサブモジュールの参照を更新する。そのあとタグと GitHub リリースを作り、マーケットプレイスから導入できることを確かめる。

## 確かめ方

- `/wiki:help`: 変更した `info-hive-wiki` で、`python skills/info-hive/scripts/wiki_help.py --command=<名前>` を 11 本すべてで実行し、警告が出ないこと。`tests/wiki/test_help_command.py` は、試験のファイルの置き場所から `info-hive-wiki` を決める（31〜34 行）。そのため、変更したサブモジュールを checkout した、同じ作業ツリー（ワークツリー）の中の試験を走らせる。ほかの作業ツリー（main の checkout など）の試験を走らせると、変更していないプラグインを試験して合格してしまう。走らせる前に、`git -C info-hive-wiki rev-parse HEAD` が変更したコミットであることを確かめる。
- リンク: HTML と Markdown のすべての相対リンクが、実在するファイルを指すこと。アンカー（`#...`）が付くリンクは、リンク先のページにその `id` があること。消した・移したファイルの名前で `info-hive-wiki` の全体を Grep して、古い場所を指すリンクが 1 つも残っていないこと。
- `fluent2.css`: `docs/assets/fluent2.css` と `skills/info-hive/scripts/browse_assets/fluent2.css` の SHA-256 が一致すること（ADR-0021 が入ったあと）。
- 公開: 公開した URL で各ページが表示され、`/wiki:help` の詳細のリンクがそのページを開くこと。
- 見た目: ブラウザのペインで各ページを開き、明るい表示、暗い表示、スマートフォンの幅で崩れないこと。PDF を開き、改ページとコードブロックを確かめること。
- 手順: 新しい環境で、チュートリアルを書いてあるとおりに通し、2-5 の目印が出ること。ハウツーのコマンドを実行したこと（実行していないものは、文書に未確認と書いてあること）。
- 文章: 各ページを `natural-japanese` の lint にかけ、です・ます体にそろっていること。`diataxis` の classify で、P0 を除く各ページが 1 つの種類に収まること。

## 未確認のまま残っていること

- Code タブで、独自のマーケットプレイスを GUI と `/plugin` のどちらで追加できるか
- `source: github` のプラグインを、SSH の鍵なしで入れられるか
- Cowork で、uv をどこに入れればプラグインの MCP サーバーが動くか。`CLAUDE.md` を読むか
- デスクトップアプリに git が同梱されているか
- `python` が Microsoft Store の別名だけのときに、コマンドが失敗するか
- デスクトップアプリの会話で、ツールの呼び出しの欄（実行したコマンドとその出力）を読者が開いて読めるか（2-5 の `/wiki:init` の目印が、これに頼る）
- 読者が `raw/味噌.md` の名前でソースを置いたとき、ソースの要約が `wiki/sources/味噌.md` になるか（エージェントがスラッグを付け直さないか）

## 付録：rag の構成案（今回は作らない）

作ると決めたら、`info-hive-rag/docs/` に置く。

| # | ページ | 種類 | 目的 |
| --- | --- | --- | --- |
| R1 | PDF を 1 つ取り込んで、検索する | チュートリアル | `/wiki:ingest <PDF の絶対パス>` で取り込み、`/rag:status` で `completed` を見て、`/rag:search` でページ番号つきの本文を得る |
| R2 | 取り込みが終わらないとき、失敗したとき | ハウツー | 処理中の状態の読み方、`retry_job`、`cancel_job`、再接続での再開 |
| R3 | 保存先、埋め込みモデル、OCR を変える | ハウツー | `/rag:setup` と、入れ直しが要るとき |
| R4 | rag の早見表 | リファレンス | 下の 3 つと、コマンド 3 本、MCP のツール 8 つ、設定 |

R4 にまとめる 3 つ:

- いつ rag が要るか
- ジョブの 6 つの状態（`queued`、`running`、`paused`、`completed`、`failed`、`cancelled`）
- 受け付ける PDF の条件

練習用には、「甘酒」を題材にした 3 ページの PDF を自作する（文字のページを 2 枚と、OCR を見せるための文字を画像にしたページを 1 枚）。rag の依存（PyTorch の CPU 版、sentence-transformers、LanceDB、Sudachi の辞書、NDLOCR-Lite）の大きさは計っていない。NDLOCR-Lite は `git+https` で取るので、rag にも git が要ると推定している（`rag_ocr.py:3`）。
