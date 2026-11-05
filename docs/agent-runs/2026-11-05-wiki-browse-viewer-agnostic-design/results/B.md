## 結論

**三案のどれを採っても壊れない設計の核は、「wiki を解釈するコンパイラを 1 つだけ持ち、三案はその出力を表示するアダプタにする」ことである。** コンパイラは Python でプラグインの中に置き、既存の `resolve_link()`、`canonical_meta()`、`collect_pages()`、被リンク、`graph.sqlite` の問い合わせを再利用して、**版番号つきの「ブラウズ・バンドル」**（JSON のマニフェスト＋ページごとの HTML 断片＋共通の CSS/JS）を出す。ローカル HTTP サーバー、静的 HTML、デスクトップアプリは、このバンドルを配る・書き出す・ウィンドウに載せるだけで、Markdown の変換やリンクの解決を二重に実装しない。

契約は、三案のうちもっとも制約が強い **「`file://` で開いても動く」** に合わせて決める。これを満たせば、サーバーとデスクトップアプリは自動的に満たす。具体的には次の 6 つを設計規則にする。

| # | 規則 | 理由 |
| --- | --- | --- |
| 1 | ページは 1 枚ずつ自立した HTML にし、リンクは相対パスだけで書く（`../concepts/foo.html`）。`/w/<wiki-id>/...` のような絶対の URL 接頭辞を本文に埋めない | `file://` では絶対パスが使えない。相対パスなら、サーバーがどの接頭辞（トークンや wiki の識別子）の下に載せても壊れない |
| 2 | 被リンク、未解決リンクの一覧、ページごとの型付き関係、ナビゲーション（`index.md` と `indexes/`）、見出し一覧は、閲覧時に計算せず、すべてバンドルに事前計算して入れる | `file://` では `fetch()` が使えない。事前計算すれば三案で同じ画面になり、決定行列で A が劣るとされた「グラフと被リンク」の差も消える |
| 3 | 検索だけは「ホストの能力」として段階を宣言する。`live`（`wiki_search.py --json` をその場で呼ぶ）、`embedded`（静的用の軽い索引を `<script>` で同梱）、`none` | 三案で唯一そろえられない機能なので、そろえない代わりに段階を契約に書く |
| 4 | バンドルに `wiki/assets/` の許可リストを持ち、mermaid のフェンスは `<pre class="mermaid">` としてエスケープして出す | ADR-0005 が記録した「サーバーがページ一覧のパスしか返さないので svg が配信されない」を、三案共通の仕組みで解決する。mermaid.js の同梱は三案共通のテンプレートの判断になる |
| 5 | コンパイラは wiki を一切書き換えず、書き出し先は `<WIKI_ROOT>/.wiki-cache/browse/` か利用者が指定したディレクトリに限る | F-G06 と ADR-0002 の「閲覧専用」を、ホストではなくコンパイラの契約として守る |
| 6 | wiki の本文は閲覧手段に依存しない（Obsidian 固有の記法、ビューワ固有の frontmatter、JavaScript がないと読めない要素を使わない） | 「どのビューワでも大丈夫」のもう半分は、コンテンツ側の規律で担保する |

デスクトップアプリの言語は今決めなくてよい。契約（バンドルの版と形式）を固定すれば、Rust（Tauri）、JavaScript（Electron）、Python（pywebview）のどれでも「WebView にバンドルの HTML を載せ、Python のコンパイラ（またはローカルサーバー）を子プロセスとして呼ぶ殻」として作れる。無理に 1 つを選ぶなら、移植性と配布物の小ささから Tauri 2 を推し、最初の試作は Python のまま作れる pywebview で済ませる。

この設計は ADR-0002（構成 B のローカルサーバー）を否定しない。サーバーは第 1 のアダプタとして最初に作る。ただし ADR-0002 の 2 行（「既定ではファイルに書き出さず、ページを開いたときに変換する」「複数 Wiki は URL に識別子を含めて切り替える」）は、本設計と両立させるために改訂の ADR が要る（「前提と不確実性」を参照）。

## 根拠

**1. ブラウズの実装はまだなく、設計はコードに縛られていない。** `info-hive-wiki/commands/` には evolve、graph、help、ingest、init、learn、lint、query、stats、upgrade の 10 本だけで、browse.md はない。`info-hive-wiki/docs/commands.md` の一覧も 10 本である。決めるべきは、ADR-0002 で選んだ構成 B の中の層の切り方である。

**2. 「コンパイラ」に要る部品は、すでにスクリプトの中に関数として存在する。** 閲覧画面に要る解釈はすべて既存関数で足り、新規に書くのは HTML への変換とバンドルの組み立てだけである。

| 必要な解釈 | 既存の関数（`info-hive-wiki/skills/info-hive/scripts/`） |
| --- | --- |
| ページの走査、slug、rel_path、frontmatter、本文、リンク、セクション、SHA-256 のキャッシュ | `wiki_search.py` の `collect_pages()`（L279〜）。`SCHEMA.md`、`index.md`、`log.md`、`indexes/`、`graph/`、`raw/`、`.wiki-cache`、`.evolution` を除外する |
| wikilink の解決（NFC、大文字小文字の区別、`dir/slug` は制約、`#見出し`、`|別名`、`.md`） | `wiki_lint.py` の `clean_link_target()`（L71）と `resolve_link()`（L84）。`wiki_search.py` L235〜274 に同じ関数がある |
| 日本語の別名キーと `type`・`kind` の値の正規化 | `wiki_text.py` の `canonical_meta()`（L103）、`normalize_tags()`（L134） |
| 被リンク | `wiki_search.py` の `cmd_backlinks()`（L1083）の照合ロジック（`link_key()` で比較） |
| ページごとの型付き関係 | `wiki_graph_query.py` の `edges_from()`（L60）、`edges_to()`（L70）。`graph/nodes.jsonl`、`edges.jsonl` はそのまま全体グラフの JSON になる |
| 検索の結果の形 | `wiki_search.py` の `json_result()`（L813）。`slug`、`rel_path`、`type`、`title`、`heading_path`、`score`、`snippet` など英語キー |

選択肢レポート §1 の 2 と §7.2 の手順 1 も、`resolve_link()` を共通モジュールに切り出すことを最初の作業にしている。本設計はその延長で、「切り出した共通部品の利用者をコンパイラ 1 つに限る」と言い換えたものである。

**3. `file://` の制約が三案の共通分母である。** 選択肢レポート §4 と §5 は、Docsify（36）、ブラウザ側の描画（40）、Pagefind（71）、JSON 索引（74）、`wiki_search.py`（75）が「ブラウザが別のファイルを取得する」ため `file://` では動かないと整理している。したがって、静的 HTML でも動く形にするには、取得が要る情報を事前計算してページに埋めるか、`<script src>` で読み込む形にするしかない（ブラウザが `file://` で `<script src>` を許し `fetch()` を拒む、という挙動は私の知識にもとづく推測で、本調査では未確認）。この形はサーバーでもデスクトップでもそのまま動くので、三案の交差点になる。

**4. 事前計算の費用は小さい。** 決定行列 §4.1 の実測（検証環境、合成 wiki）では、1 ページの HTML 変換が 1.3 ミリ秒、1,000 ページの全変換が 1.26 秒、静的 HTML の起動から全変換までが約 2.3 秒である。`collect_pages()` は SHA-256 で解析キャッシュを持つので、差分だけ作り直せる。サーバーは同じコンパイラを「要求のたびに更新時刻を確かめて 1 ページだけ変換する」モードで呼び、静的は「全ページを書き出す」モードで呼ぶ。入口が 2 つで、コードの経路は 1 つになる。

**5. ナビゲーションを各ページに埋め込むと静的出力が肥大するので、共有スクリプトにする。** `index.md` の 1 項目は「`- [[slug]]: 1 行の要約`」で、日本語の要約を含めて 1 項目約 100 バイトと見積もる（推定）。1,000 項目なら約 100 KB で、これを 1,000 ページすべてに埋めると 100 KB × 1,000 = 約 100 MB になる。ナビは `nav.js` のような共有ファイルに 1 つだけ置き、各ページは `<script src="../nav.js">` で読み、`<noscript>` には `index.html` へのリンクを残す。これなら本文の HTML は約 10〜20 KB × 1,000 = 10〜20 MB（推定）に収まる。

**6. 決定行列の論理に照らすと、本設計は「安い保険」である。** 決定行列 §5.3 によれば、B が A を上回る 1.24 点のうち 1.09 点（約 88%）が拡張性に由来する。§5.1 の拡張性の内訳は 4 方向（日本語の全文検索、グラフと被リンク、RAG 統合、複数 Wiki）の平均で、A は 4.0、B は 8.75 だった。被リンクとグラフをバンドルに事前計算すると、「グラフと被リンク」は三案で同じになる。残る差は、その場の検索、RAG の検索結果からの誘導、複数 wiki の切り替えの 3 つで、どれもサーバーまたはデスクトップが持つ「能力」として契約に書ける。B を選び直す話ではなく、B の中でコンパイラの境界を正しく引けば A と C が付いてくる、という話である。

**7. 検索の段階を契約に書く理由。** 選択肢レポート §1 の 4 は、全文検索を `wiki_search.py` 経由にする理由として、`/wiki:query` と同じ BM25 と埋め込み、日本語の bigram 分割をそのまま使えることを挙げている。静的 HTML でこれを JavaScript に移植すると、`tokenize()`（`wiki_search.py` L139）の規則が二重になり、lint と画面の食い違いと同じ種類の問題を検索に持ち込む。そこで、`embedded` の段階は「`index.md` の題名と要約、タグの照合」に限り、本文の全文検索は `live` の段階でだけ提供すると割り切る。postings を Python 側で作って JS は照合だけ、という中間案もあるが、クエリ側の分割は JS に要るので同じ問題が残る。

**8. RAG と複数 wiki はホストの能力である。** rag の MCP は `search(wiki_root, query, limit)`（`info-hive-rag/scripts/rag_server.py` L152）を持ち、結果は `chunk_id`、`doc_id`、`page`、`section`、`title`、`text`、`score`（`rag_index.py` L320〜349）である。原本への参照は `books:日本語資料.pdf` のような名前付き参照（rag の README）で、`file://` へのリンクはブラウザが開かない（選択肢レポート §6.8）。したがって RAG の結果は「表示して、パスと頁をコピーできる」までが三案共通の UI 部品になり、呼び出しそのものはサーバーとデスクトップだけが持つ。複数 wiki は ADR-0008 のとおり作業領域ごとに `wiki/` が 1 つなので、「wiki ルートごとに 1 バンドル。ホストが複数を載せる」で足り、URL の規約を契約にしなくてよい。別の wiki への相対リンクは、選択肢レポート §6.9 と同じく「外部の参照」として示す。

**9. サーバー固有の対策は、相対リンクの規則と両立する。** 選択肢レポート §6.8 の起動ごとのトークンは、`/t/<token>/concepts/foo.html` のようにパスの接頭辞に置けば、本文の相対リンクがそのまま接頭辞を引き継ぐので、HTML 断片を一切変えずに済む。Host ヘッダーの確認、CSP、127.0.0.1 への固定はハンドラ側の処理で、バンドルには影響しない。

**10. デスクトップアプリの言語を「後で決められる」ようにする契約。** アプリがやることは、(a) wiki ルートの一覧を持つ、(b) `uv run --script wiki_render.py <WIKI_ROOT> --out <dir>` を子プロセスで呼ぶか、ローカルサーバーを起動してその URL を開く、(c) WebView にバンドルを載せる、(d) ファイルの変更を監視して再コンパイルを頼む、の 4 つである。Markdown と wikilink の規則はアプリの言語に持ち込まない。Python と uv はプラグインの前提（`info-hive-wiki/README.md` の「前提として必要なのは `uv` だけ」）なので、アプリがそれに依存しても新しい前提は増えない。

| 候補 | 言語 | 描画エンジン | 長所 | 注意 |
| --- | --- | --- | --- | --- |
| Tauri 2 | Rust（UI は HTML/JS） | OS の WebView（Windows は WebView2、macOS は WKWebView、Linux は WebKitGTK） | 配布物が小さい。Windows・macOS・Linux に対応 | OS ごとにエンジンが違い、日本語のフォントと禁則の見え方が揃わない（`text-autospace` の対応差など、選択肢レポート §6.7 の方針で吸収する） |
| Electron | JavaScript | 同梱の Chromium | 描画が OS によらず同じ。Obsidian 自身がこの方式 | 配布物が大きい。Node.js の開発環境が要る |
| pywebview | Python | OS の WebView | 新しい言語が要らず、プラグインと同じスタックで試作できる | 配布には PyInstaller などが要る。Tauri と同じく OS でエンジンが違う |

いずれも「殻」なので、バンドルの版に固定（pin）して動く。デスクトップアプリは Claude Code のプラグインではないので、置き場所（別リポジトリ）と公開の周期は作者の判断になる。デスクトップと静的の 2 案は、研究で記録されたサーバー固有の悩み 2 つ、「Claude Code が終了時にバックグラウンドの処理を止める」（選択肢レポート §6.9）と「トークンと Host ヘッダーの対策」（§6.8）を回避できる。

**11. 「どれを採っても大丈夫」を証明する受け入れテスト。** `info-hive-wiki/eval/retrieval/ja/corpus/wiki/`（決定行列 §4.2 によれば 28 ページ）でバンドルを作り、次を確かめる。(a) 未解決リンクの一覧が `wiki_lint.py` の結果と一致する（選択肢レポート §7.2 の合格の目安と同じ）。(b) 各ページの HTML 断片が、サーバーが返すもの、静的に書き出したもの、デスクトップの殻が読み込むもので、バイト単位で同一である。(c) 静的出力を `file://` で開いて、コンソールにエラーがなく、リンクで移動できる。(d) サーバーは 127.0.0.1 以外への通信が 0 件。(b) が成り立てば、三案は構成上入れ替え可能である。

**12. バンドルの中身（キーは英語、本文は日本語）。** `bundle_version`、`wiki_root`、`generated_at`、`capabilities`（`search: live|embedded|none`、`rag: true|false`、`graph: true|false`）、`pages[]`（`slug`、`rel_path`、`title`、`type`、`kind`、`tags`、`created`、`updated`、`sources`、`headings[]`、`outlinks_resolved[]`、`outlinks_unresolved[]`、`backlinks[]`、`relations[]`、`sha256`、`html`）、`nav`（`index.md` と `indexes/<type>.md` を解釈した木。`collect_pages()` はこれらを除外するので、コンパイラが別に読む）、`assets[]`（`wiki/assets/` の許可リスト）、`graph`（`nodes.jsonl` と `edges.jsonl` の写し）、`search_index`（`embedded` のときだけ）。見出し ID は選択肢レポート §6.7 のとおり NFC のまま日本語で付け、`[[slug#見出し]]` の解決と一致させる。

## 検討した代替案

| 案 | 採らなかった理由 |
| --- | --- |
| 三案それぞれに Markdown 変換とリンク解決を持たせる（サーバーは Python、デスクトップはアプリの言語、静的は生成器） | 規則が 3 か所に分かれ、lint と画面の食い違い（ADR-0002 の「理由」）が 3 倍になる。決定行列 §4.2 の Obsidian の食い違い（大文字小文字、NFD、クリックでページが増える）は、まさに別実装の規則が招いた例である |
| サーバーを唯一の経路にし、デスクトップアプリはサーバーの URL を開くだけ、静的は作らない | 「どれを採っても」という依頼に反する。また、Claude Code のセッション終了でサーバーが止まる（選択肢レポート §6.9）ので、デスクトップアプリが自前でプロセスを管理する必要があり、結局コンパイラの CLI 契約が要る |
| 静的 HTML を主にし、サーバーは静的出力を配るだけにする | その場の検索と RAG を失う。決定行列 §5.3 のとおり、B の優位は拡張性にある。本設計では静的出力は同じコンパイラの別の入口なので、主従を決めなくてよい |
| 既製の静的サイト生成器（Quartz、MkDocs、Zensical、Docsify）を静的の経路に使う | 決定行列 §5.2 で 8 案中 5〜8 位。日本語の別名キーと型付きグラフを解釈せず、wikilink の規則も食い違う（ADR-0002「検討した選択肢」）。本設計の規則 6（コンテンツは閲覧手段に依存しない）とも相性が悪い |
| デスクトップアプリで Markdown をネイティブに描く（WebView を使わない） | HTML/CSS を共有できず、日本語の禁則と折り返しの CSS 方針（選択肢レポート §6.7）をアプリの言語で作り直すことになる |
| 静的 HTML に本文の全文検索を JavaScript で同梱する | `tokenize()` の規則の二重化。段階 `embedded` を題名・要約・タグに限り、全文は `live` に残す方が、規則の一元化と矛盾しない。需要が出たら、Python 側で postings を作る中間案を検討する |
| 多 wiki を URL の規約（`/w/<wiki-id>/<rel_path>`）で契約にする | `file://` で成り立たない。「wiki ルートごとに 1 バンドル」なら三案で同じ扱いになる |

## 前提と不確実性

- **サブモジュールの読み方。** このワークツリーではサブモジュールが空だったので、スクリプトと文書は主の作業コピー `C:/Works/info-hive-dev/info-hive-wiki/`（HEAD `3028923`）から読んだ。ワークツリーの gitlink（`302892390250…`）と一致することを `git submodule status` で確かめた。引用した行番号はこの版のものである。
- **ブラウザの `file://` の挙動。** 「`fetch()` は使えず、`<script src>` は読める」は私の知識にもとづく推測で、本調査で一次資料を確かめていない。選択肢レポート §8 も Docsify と Pagefind について「公式の記述は未確認」としている。設計規則 1〜3 はこの前提に立つ。
- **デスクトップの WebView のエンジンと対応 OS。** Tauri、Electron、pywebview の特徴は私の知識で、版と対応状況は未確認である。日本語の描画の差は、選択肢レポート §6.7 の CSS 方針で吸収できると見込んでいるが、Linux の WebKitGTK での実機確認が要る。
- **規模の見積もり。** ナビ 1 項目 100 バイト、本文 HTML 1 ページ 10〜20 KB は推定で、実際の wiki（1 ページ 4,000 字まで）で測り直す必要がある。決定行列 §4.1 の実測も合成ページによるものである。
- **ADR-0002 の改訂（作者の判断）。** 次の 2 行は、本設計と両立させるために置き換えの ADR が要る。(1)「既定ではファイルに書き出さず、ページを開いたときに変換する。静的 HTML の書き出しは副機能」→ 静的の書き出しはコンパイラの第一級の入口にし、サーバーの既定（その場で変換）は変えない。(2)「複数 Wiki は URL に識別子を含めて切り替える」（選択肢レポート §6.9）→ 相対リンクと「wiki ルートごとに 1 バンドル」に改める。あわせて §6.8 の「ページの一覧にある rel_path だけを返す」に `wiki/assets/` の許可リストを足す（ADR-0005 の「見直す条件」と整合する）。
- **作る順序（作者の判断）。** ADR-0002 は「第 1 段階で読む画面、次に日本語の全文検索」とする。本設計では、共通部品の切り出し → コンパイラと静的書き出し → サーバー（`live` の検索）→ デスクトップの殻、の順が最も安い。静的の書き出しはポートを開かずにテストでき、受け入れテスト (a)(b) をサーバーの前に通せる。読む画面を最初に届けるという ADR の意図は保てるが、順序の変更は作者が決める。
- **デスクトップアプリの置き場所と配布。** プラグインではないので、`info-hive-dev` のサブモジュールにするか、別の製品にするか、Python と uv を前提にしてよいかは未決である。本設計はバンドルの版で結び付けるだけなので、どちらでも成り立つ。
- **検索の `embedded` の範囲。** 題名・要約・タグに限る案は私の提案で、利用者が静的出力で本文検索を求めるかは分からない。
- **mermaid.js の同梱。** ADR-0005 は第一段階に含めないとしている。本設計は「出す形」（`<pre class="mermaid">`）だけを決め、同梱の時期は ADR-0005 の「見直す条件」に従う。

## 参照

- `docs/adr/README.md`、`docs/adr/0001-local-only-server-is-not-hosted-wiki.md`、`docs/adr/0002-wiki-browse-uses-on-demand-local-server.md`（決定、理由、検討した選択肢、見直す条件）、`docs/adr/0005-wiki-figures-use-mermaid-and-svg.md`（背景の制約、browse での表示、見直す条件）、`docs/adr/0007-rag-uses-mcp-core-and-persistent-jobs.md`、`docs/adr/0008-numbered-workspace-layout.md`（各ディレクトリの役割、設定と作業領域の見つけ方）、`docs/adr/0009-graph-layer-stays-in-wiki.md`
- `docs/research/llm-wiki-browse-options.md` §1、§2.2〜2.5、§3.1、§4（候補 1〜22、36、40、71、74、75）、§5、§6.5〜6.9、§7.1〜7.2、§8
- `docs/research/llm-wiki-browse-decision-matrix.md` §1、§2.3、§4.1、§4.2、§5.1〜5.3、§6、§7、§8
- `llm-wiki-product-concept-and-requirements-ja.md` D-03、F-G06、AC-D02、O-11（`grep` で該当行を確認）
- `docs/porting-plan.html` 方針 B、方針 G、Q4（本文を抽出して確認）
- `info-hive-wiki/.claude-plugin/plugin.json`、`README.md`（前提は uv のみ、10 本のコマンド）、`docs/commands.md`、`commands/graph.md`、`commands/query.md`、`commands/lint.md`、`skills/info-hive/SKILL.md`、`skills/info-hive/assets/`（テンプレート一覧）
- `info-hive-wiki/skills/info-hive/scripts/wiki_search.py`（`collect_pages` L279、`tokenize` L139、`resolve_link` L257、`json_result` L813、`cmd_backlinks` L1083）、`wiki_lint.py`（`clean_link_target` L71、`resolve_link` L84、除外一覧 L108〜109）、`wiki_text.py`（`canonical_meta` L103、`normalize_tags` L134）、`wiki_graph_query.py`（`edges_from` L60、`edges_to` L70、`--json` L221）、`init_wiki.py`（`.wiki-cache/.gitignore` L232）、`test_link_resolution.py`（モジュールの import の仕方）
- `info-hive-wiki/eval/check_encoding.py`（新しいスクリプトが従う encoding の検査）
- `info-hive-rag/.claude-plugin/plugin.json`、`.mcp.json`、`README.md`（MCP ツール一覧）、`scripts/rag_server.py`（`search` L152）、`scripts/rag_index.py`（検索結果の列 L320〜349）
- `~/info-hive/W0_Wiki/index.md`、`SCHEMA.md`（実際の wiki の索引の形と規約）

```text
使用した MCP サーバー: なし
使用した Agent Skills: なし
```
