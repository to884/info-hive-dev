# browse に Mermaid の図と svg を出す（2026年11月17日）

`/wiki:browse` のページに、本文の ```` ```mermaid ```` のフェンスを図として描き、`![説明](../assets/<名前>.svg)` の svg を表示する設計である。

| 項目 | 内容 |
| --- | --- |
| 状態 | 2 版目（案）。1 版目は Sol の設計のレビュー（[design-review-1.md](../agent-runs/2026-11-17-wiki-browse-figures/design-review-1.md)）で却下された（致命 1、重大 3）。2 節の前提を改め、2 回目の PoC で確かめた |
| 対象 | `info-hive-wiki` の `skills/info-hive/scripts/`（`wiki_pages.py`、`wiki_browse_fs.py`、`wiki_browse_core.py`、`wiki_browse.py`、`wiki_lint.py`、`browse_assets/`）、開発リポジトリの `tests/wiki/` |
| 決定 | [ADR-0030](../adr/0030-wiki-browse-shows-figures-as-images.md)（提案） |
| 試作と結果 | `poc/browse-figures/`、[PoC の記録](../research/wiki-browse-figures-poc-2026-11-17.md) |
| 基準の版 | info-hive-wiki 0.25.2（`e8886d6`） |

## 1. 背景

ADR-0005 は、知識ページの図を mermaid のフェンスと `wiki/assets/<スラッグ>-NN.svg` で書くと決め、browse での表示を将来の作業にした。見直す条件は「mermaid.js の同梱と `wiki/assets/` の配信を足す」である。作者が、この表示を足すことを求めた（2026年11月17日）。

今の browse では、次のとおりである。

- フェンスは markdown-it-py が `<pre><code class="language-mermaid">` として出す（`wiki_browse_core.py` の `body_html`）。
- 画像は、`_transform_inline` が代替テキストの文字に置き換える。`wiki/assets/` は入力に入らず、配信もされない。
- ページの CSP は `default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'` で、HTTP ヘッダーと `<meta>` の両方で付ける。試験は、`[style]` と CSP の違反が 0 件であることを数える。

Mermaid は、描いた SVG に `<style>` 要素と `style` 属性を入れ、CSP 向けの設定（nonce など）を持たない。ページの中でそのまま描くと、今の CSP の下ではスタイルが止まる。図のソースから CSS やスクリプトを注入できる欠陥も、何度も見つかっている。wiki の本文は Web から取り込んだ信頼しない入力を含む。

## 2. 1 回目のレビューで崩れた前提

| 1 版目の前提 | 崩した反例 | 2 版目の形 |
| --- | --- | --- |
| 枠の CSP で fetch、画像、フォームを止めれば、枠の中で任意のスクリプトが動いても外へ送れない | WebRTC の ICE サーバーの名前（DNS）は、CSP の `default-src` では止まらない | 外への口を数えて塞ぐのをやめる。枠が秘密を何も知らない形にする（7.1）。送れても、漏れるのは攻撃者自身が書いた図だけになる |
| 不透明なオリジンの枠は、wiki の情報に届かない | 枠の URL は表示のトークンを含み、`script-src` が配信元の全体を許すので、`data/search.js`（全ページの題、要約、見出し）を classic script として読める。返す SVG と `alt` にトークンを入れて、親の画面に持ち出せる | 枠は、トークンのない `/_frame/<版>/` の下から配り、`script-src` をそのパスに限る（7.2）。2 回目の PoC で、5 つのブラウザについて、枠が配信元のほかのスクリプトを `<script>` でも `fetch` でも読めないことを確かめた |
| 枠に送るのは図のソースと配色だけなので、知られて困るものはない | 1 つの枠がページのすべての図を受け取る。攻撃者の図が、同じページのほかの図（ほかのソースから書いたもの）を読める | 図 1 つにつき枠を 1 つ作り、その図だけを送り、描き終えたら消す（7.3） |
| svg のバイト列をそのまま書いても、公開の前の検査は今と同じに働く | `scan_machine_info` は UTF-8 で読む。UTF-16 の svg の中の絶対パスとトークンを見つけない | svg は UTF-8 に限る。そうでなければ読めない入力として扱い、出力に書かない（6.2） |
| 走査のときに 2 MiB 以下なら、読むのも 2 MiB 以下である | 走査と読み取りのあいだに、大きなファイルに替えられる。今の `read_file` は終わりまで読む | 読む口が上限を強制する（6.2） |
| 走査のときにリンクでなければ、リンクの先を読まない | 読む間だけリンクに替えて戻すと、2 回の走査は同じになる | 守る範囲を書き直す（6.1）。止めるのは木に置かれたリンクで、読む間に替える同時の書き手は対象にしない |

軽微な指摘のうち、lint の `missing_assets` が文字参照（`&amp;`）を解かずに探すずれは、lint を直してそろえる（6.4）。試験の「枠の違反 0 件」は、外の画像を使う図を除く（10.2）。PoC の既定の手順と SHA-256 の照合は直した。

## 3. 作者が決めたこと

| 日付 | 決定 |
| --- | --- |
| 2026年11月17日 | 描画は、同梱の枠の文書を見えない sandbox の iframe で読んで描き、ページには `<img>` で出す。ページの CSP は緩めない |
| 同 | 同梱する Mermaid は `@mermaid-js/tiny` 12.3.0。全部入りの `mermaid.min.js` は elkjs（EPL-2.0 OR GPL-3.0-or-later）を含むので替えた。マインドマップ、アーキテクチャ図、KaTeX、`layout: elk` は描けず、コードのまま出す |
| 同 | 見た目に決めることがあれば、`fluent2-html-replica` のデザインシステム（同梱の `fluent2.css` の部品とトークン）を使う |
| 同（承認した計画の既定） | svg の範囲は ADR-0005 の `![説明](../assets/<名前>.svg)` だけ。出力の名前は `assets/wiki/<16 桁>.svg`、上限は 1 ファイル 2 MiB、リンクの svg は読まない。SVG と Mermaid を 2 本の PR に分ける |

## 4. 範囲

- **入れる**: mermaid のフェンスの描画（サーバーの方式だけ）。`wiki/assets/` の直下の svg の表示（サーバーと静的の 2 方式）。明るい配色と暗い配色。lint の `missing_assets` の文字参照の扱い。
- **入れない**: Markdown に書いた生の `<svg>`（`html: False` を変えない）、```` ```svg ````、png などのラスター画像、`raw/assets/` の画像、`![[x.svg]]`、`wiki/assets/` の下位のディレクトリ、図の中の文字の選択とリンク、静的の書き出しでの Mermaid、アプリの方式（`core_loop`）で svg を渡す口。

## 5. 方式の全体

| | サーバーの方式 | 静的の書き出し（`file://`） |
| --- | --- | --- |
| svg | `<img>` で出す。svg は `image/svg+xml` と `CSP_SVG` で返す | `<img>` で出す。svg のファイルを出力に書く |
| Mermaid | `figures.js` が図ごとに枠を作って描き、`<img>` で出す | 描かない。今と同じコードを出す |
| 枠の同梱物 | トークンのない `/_frame/<版>/` から配る | 出力に書かない |

PoC で、`file://` では 5 つのブラウザすべてが sandbox の枠に隣のファイルのスクリプトを読ませないことを確かめた。ADR-0016 が 2 方式の一致を求めるのは、リンクの移動、被リンク、診断である。図は 2 方式で違うことを、ADR-0030 と利用者向けの文書に書く。

## 6. svg

### 6.1 入力

- `wiki_pages.walk_assets(wiki_root) -> Walk` を足す。`wiki/assets/` の直下だけを見て、名前の末尾が `.svg`（大文字と小文字を区別しない）で、`.` で始まらない、ふつうのファイルを `MdFile` で返す。OS の呼び出しは `walk_markdown` と同じ口（`read_os`、`_list_dir`、`_stat_entry`、`_is_junction`）を通す。
- `assets` そのものがシンボリックリンクかジャンクションなら、たどらない（何も返さない）。ファイルのシンボリックリンクも返さない。ハードリンクは見分けない。
- 守る範囲: 止めるのは、走査の時点で木に置かれたリンクである（利用者が `assets` を別の場所へ向けた、など）。読む間だけリンクに替えて戻す同時の書き手は、対象にしない。その書き手は wiki に直接バイト列を置けるので、リンクを止めても守れるものが増えない。ページの読み取りも同じ前提で、2 回の走査は「読んでいるあいだに変わった」ことを見つけるためのものである。
- `assets` がないなら空、一覧を作れないなら `unlistable`、種類を調べられない項目は `unknown` に入れる。`walk_inputs` は今と同じく、知らせがあれば全体を採らない。
- `walk_inputs` は、ページ、索引、オントロジーのあとに `("asset", rel, size, mtime_ns)` を足す。svg のない wiki では、入力の一覧と印が今と同じになる。

### 6.2 写し

- `InputFile` に `data: bytes | None` を足す。`kind` の値に `"asset"` を足す。
- `wiki_browse_fs.read_input_capped(root, rel, limit) -> bytes` を足す。`limit + 1` バイトまでしか読まず、超えたら `TooLarge` を送出する。`take_snapshot` は、`asset` をこれで読む（`ASSET_MAX_BYTES` は 2 MiB）。走査の大きさが上限を超えていれば、読まずに `too_large` にする。
- `asset` は UTF-8（BOM はあってもよい）として読めなければならない。読めなければ `error = "decode"`。先頭の XML 宣言に `encoding` があり、その値が `utf-8` でなければ（大文字と小文字を区別しない）、これも `decode` にする。`data` は読んだバイト列のまま持つ（BOM と改行を保つ）。こうすると、公開の前の検査（`scan_machine_info`）が svg の中身を今と同じ読み方で調べられる。
- 世代には、今と同じく種類、相対パス、sha（か読めない理由）が入る。
- `Core.__init__` は、`_build_pages` のあとに `_build_assets()` を呼ぶ。`self.assets`（NFC の相対パス → `InputFile`）と、出力の名前の表 `self.asset_out`、`self.asset_by_out` を作る。NFC にして同じ綴りになる svg が 2 つあれば、どちらも描かず、診断 `asset_collision` を足す。

### 6.3 出力の名前

`assets/wiki/<short_hash(disk_rel, 16)>.svg` にする。

- 最上位の `assets` は予約済み（`RESERVED_TOP`）なので、ページの出力は `assets/` の下に来ない。画面の部品は `assets/` の直下にあり、`assets/wiki/` と重ならない。
- 名前は 16 桁の 16 進なので、大文字と小文字、Windows の予約名、長さの問題が起きない。
- 新しい最上位の名前は予約しない。予約すると、同じ名前のディレクトリを持つ既存の wiki で、ページの出力の名前が変わる。

`knows(name)` は `asset_by_out` も見る。`asset_bytes(name) -> bytes` を足し、`render_all` は svg を bytes のまま返す（`wiki_browse.build` は bytes を受け付ける）。

### 6.4 参照の解決と HTML

純粋な関数 `figure_target(page_disk_rel, src) -> str | None` を中核に足す。lint の `missing_assets` と同じ順で、文字の上だけで解く。

1. markdown-it の `src`（文字参照を解き、パーセントエンコードしたもの）が、空、`/`、`\`、`#` で始まるか、URL のスキームを持てば None。
2. `#` と `?` から後を落とし、unquote する（失敗、NUL、`\` を含めば None）。
3. `posixpath.normpath(<ページのディレクトリ>/<参照>)` が `..` で始まれば None。
4. NFC にして、`assets/<1 つの要素>` で、末尾が `.svg`（大文字と小文字を区別しない）なら返す。

lint の `missing_assets` は、参照先を Markdown のエスケープを外してから unquote するが、文字参照（`&amp;` など）を解かない。markdown-it は解く。`![a](../assets/a&amp;b.svg)` で、browse は `a&b.svg` を描き、lint は `a&amp;b.svg` がないと報告する。lint の側で、エスケープを外したあとに `html.unescape` を当ててそろえる。

`_transform_inline` の image の分岐は、次のように描く。

| 参照 | 出力 |
| --- | --- |
| `figure_target` が返し、写しに読めるものがある | `html_inline` で `<span class="wiki-fig fui-Card" data-fig="svg" data-theme="light"><img class="fui-Image" src="…" alt="…" loading="lazy"></span>` を出す。`src` は `rel_href(ページの出力, svg の出力)`、`alt` は代替テキスト（`html.escape`） |
| `figure_target` が返すが、ない、読めない、大きすぎる、綴りが重なる | 今と同じ代替テキスト。ページの診断に `missing_asset` か `asset_unreadable` を足す |
| それ以外（外の URL、`data:`、png、`assets/` の外、下位のディレクトリ） | 今と同じ代替テキスト。診断は足さない（lint の領分） |

- 入れ物は `<span>` にする。画像はインラインの字句なので、段落（`<p>`）の中に置かれる。`<figure>` や `<div>` は `<p>` の中に置けない。`display: block` にするのは `style.css` の役目である。
- `<img>` をリンクで包まない。静的版で svg を直接開くと、中のスクリプトが `file://` で動く。
- 診断は `_prepass` で作る。描くときにもう一度 `figure_target` を呼ぶ。解決に状態がないので、wikilink のような数え（`counter`）は要らない。
- `inline_text`（見出しの ID、導入文、検索の文字）は変えない。画像は代替テキストのままである。

### 6.5 配信

- `wiki_browse.py` の `_send` に引数 `csp` と `cache` を足し、ヘッダーは `csp or core.CSP` と `cache or "no-store"` にする。`_text`、`_json`、404、`send_error` は今のまま。
- `_view` は、svg の出力の名前なら `image/svg+xml` と `core.CSP_SVG`（`default-src 'none'; style-src 'unsafe-inline'; sandbox`）で返す。直接開かれても、中のスクリプトは動かない。
- 静的の書き出しは、svg を出力に書く。公開の前の検査は、svg も今と同じく調べる（入力の中身なので）。

## 7. Mermaid

### 7.1 枠が知ってよいもの

枠の中で Mermaid の欠陥を突かれ、任意のスクリプトが動くことを前提にする。外への口（fetch、画像、WebRTC、DNS など）を数えて塞ぐことはしない。CSP がすべての口を閉じる保証がないからである。代わりに、枠が知りうるものを次に限る。

| 枠が知りうるもの | 理由 |
| --- | --- |
| 自分が描く 1 つの図のソース | 図ごとに枠を作り、その図だけを送る。攻撃者の図の枠が知るのは、攻撃者自身が書いたものである |
| 配色（Fluent のトークンから作った色と書体の名前） | 秘密ではない |
| 自分の URL（`/_frame/<版>/mermaid-frame.html`） | トークンを含まない |
| `/_frame/<版>/` の下の 3 つのファイル | 同梱の固定のファイルで、だれにも同じである |

枠が知りえないもの: 表示と操作のトークン、ほかの図、ページの本文、`nav.js` と `data/*.js`、cookie と localStorage、親の URL。理由は次のとおりである。

- 枠は sandbox（`allow-same-origin` なし）で不透明なオリジンになり、親の DOM、cookie、localStorage に届かない。
- 枠の `script-src` は `/_frame/<版>/` だけを許し、`connect-src` は `default-src 'none'` で閉じる。トークンの付いたパスは、知っていても読めない。2 回目の PoC で、5 つのブラウザについて確かめた。
- ページは `Referrer-Policy: no-referrer` なので、枠の `document.referrer` は空である（PoC で確かめた）。

枠ができることのうち、残るものと扱いは次のとおりである。

| 残ること | 扱い |
| --- | --- |
| 自分の図のソースを外へ送る | 攻撃者がすでに知っているものなので、新しく漏れるものはない |
| 好きな SVG と題を親へ返す | 図を書いた人は、正しい図でも好きな文字を描ける。画像はページの本文と同じく、信頼しない内容として見せる。親は SVG を DOM に入れず `<img>` の `data:` にだけ使い（画像の svg ではスクリプトが動かない）、題は 200 字で切って `setAttribute` で `alt` に入れる |
| 自分を別の URL へ移す | 親の CSP の `frame-src 'self'` が、ほかのオリジンへの移動を止める。同じオリジンのトークンの付いたパスは、トークンを知らないので指せない |
| 応答しない、知らせを送り続ける | 親は 20 秒で枠を消す。型と `seq` の合わない知らせを捨てる |

### 7.2 同梱物と配り方

`browse_assets/` に次を足す。

| ファイル | 役目 |
| --- | --- |
| `mermaid.tiny.js` | `@mermaid-js/tiny` 12.3.0 の `dist/mermaid.tiny.js` を書き換えずに写す（2,852,578 バイト、SHA-256 `c41f5236…2a9a`） |
| `mermaid-frame.html` | 枠の文書。`<meta>` の CSP を置かない。classic の `<script src>` で `mermaid.tiny.js` と `mermaid-frame.js` を読む（相対の名前） |
| `mermaid-frame.js` | 枠の側の処理（7.5） |
| `figures.js` | 親の側の処理（7.4） |

- 中核に `FRAME_ASSETS = ("mermaid-frame.html", "mermaid-frame.js", "mermaid.tiny.js")` と `FRAME_VERSION`（例 `mermaid-12.3.0-1`）を置く。`FRAME_VERSION` は、3 つのどれかを変えたら上げる（`browse_assets/README.md` の写し直す手順に書き、試験が README の SHA-256 と組で確かめる）。
- サーバーは、`/_frame/<FRAME_VERSION>/<FRAME_ASSETS の名前>` を、トークンなしで返す。Host の確かめ（`127.0.0.1:<ポート>`）、GET と HEAD だけ、は今と同じに当てる。ほかの名前や版は 404。`Cache-Control: private, max-age=86400` を付ける（URL にトークンがないので、ディスクのキャッシュに残してよい。版がパスにあるので、更新したら別の URL になる）。
- ADR-0001 は「起動ごとのトークン」を条件にしている。`/_frame/` は、その例外として ADR-0030 に書く。返すのは同梱の固定のファイルだけで、wiki の中身と状態を返さない。
- `ASSETS`（`assets/<名前>` で配るもの）には `figures.js` だけを足す。枠の 3 つは `ASSETS` に入れず、静的の書き出しに書かない。`load_assets` は枠の 3 つも読む（サーバーが配るため）。
- `scan_machine_info` は、同梱物を調べない。生成器の同梱物は入力の中身を含まない。
- `.gitattributes` で `mermaid.tiny.js` を `-text`、枠と親の JS と HTML を `eol=lf` にする。Windows の checkout で CRLF になると、README の SHA-256 と、配った中身のバイトの一致の試験が落ちる。
- ライセンス: tiny は MIT で、束の中に DOMPurify（MPL-2.0 OR Apache-2.0）、lodash（MIT）などの表示がある。`browse_assets/licenses/` に Mermaid の `LICENSE` と、束の中の第三者の表示をまとめた文書を置く。`mermaid-frame.js` の先頭のコメントに Mermaid の MIT の表示を入れる。束の中の表示の一覧は、実装のときに `@license` と `Copyright` を数えて作る。
- `browse_assets/README.md` に Mermaid の表（写した元、版、tarball の integrity、大きさ、SHA-256、写した日、ライセンス、`FRAME_VERSION`）と、写し直す手順を足す。

### 7.3 CSP

| 応答 | CSP |
| --- | --- |
| ページ（ヘッダーと `<meta>`） | 今の値に `frame-src 'self'` を足す |
| 枠の文書（ヘッダーだけ） | `default-src 'none'; script-src http://127.0.0.1:<ポート>/_frame/<版>/; style-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'; sandbox allow-scripts` |
| 枠の JS | 今の `CSP`（JS には効かないが、すべての応答に付ける今の決まりに合わせる） |
| svg | `default-src 'none'; style-src 'unsafe-inline'; sandbox` |
| そのほかの応答 | 今の `CSP`（`frame-src 'self'` を足したもの） |

- 枠の CSP は、ポートを入れて `core.frame_csp(port)` で作る。`_view` が `app.port` を渡す。`'self'` を使わないのは、WebKit が sandbox で不透明になった文書の `'self'` を配信元に一致させないからである（PoC）。
- 枠の文書には `<meta>` の CSP を置かない。置くと、WebKit が `<meta>` の `'self'` でスクリプトを止める。
- `sandbox allow-scripts` は、ヘッダーと iframe の属性の両方に付ける。ヘッダーの側は、枠の文書を直接開かれたときにも効く。
- `style-src 'unsafe-inline'` は枠の文書にだけ許す。Mermaid が描く途中で `<style>` と `style` 属性を使うためである。

### 7.4 親の側（`figures.js`）

`_tail` で、全ページの `app.js` のあとに読む（`<script src>`）。`app.js` とは別のファイルにする。`app.js` は契約の版が違うときなどに途中で抜けるので、図の処理をそれに縛らない。

1. `location.protocol` が `http:` でも `https:` でもなければ、何もしない（静的の書き出し）。
2. `#_body pre > code.language-mermaid` がなければ、何もしない。枠も `mermaid.tiny.js` も読まない。
3. 図を順に描く。同時に動かす枠は 2 つまでにする。図 1 つにつき、見えない `<iframe class="fig-frame" sandbox="allow-scripts" title="図の描画" aria-hidden="true" tabindex="-1" width="1200" height="800">` を `<body>` の末尾に作る。`src` は `location.origin + "/_frame/<FRAME_VERSION>/mermaid-frame.html"`（`FRAME_VERSION` は `figures.js` の定数。試験が中核の値と一致を確かめる）。大きさは属性で決める（`style` を使わない）。画面の外に置くのは `style.css` の `.fig-frame` の役目である。
4. 枠の `ready` を待ち（20 秒で打ち切る）、その図のソースと配色を `render` の知らせで送る。宛先のオリジンは `"*"` にする（枠は不透明なオリジンで、名前で指せない。送るのはその図のソースと配色だけである）。`done` か時間切れで、枠を消す。
5. 枠からの知らせは、`event.source` がその枠の `contentWindow` のものだけを受ける。`seq` が今の描画のものでなければ結果を使わない。`result` は、`svg` が `<svg` で始まる 5 MB 以下の文字で、`w` と `h` が 0 より大きく 20,000 以下の数のときだけ使う。
6. 描けた図は、`<pre>` の前に入れ物と画像を置き、`<pre>` を Accordion に移す（8 節）。画像の `src` は `data:image/svg+xml;charset=utf-8,<encodeURIComponent した svg>`、`alt` は枠が返した題（200 字まで）か「図」、`width` と `height` は属性で付ける。SVG のマークアップを DOM に入れない。
7. 描けなかった図と時間切れの図は、`<pre>` の前に警告（8 節）を置き、コードを開いたまま残す。
8. 配色が変わったら、全図を描き直す。`<html>` の `data-theme` の MutationObserver と、`matchMedia("(prefers-color-scheme: dark)")` の change で拾い、トークンを読み直して前と違うときだけ描く。描き直しも図ごとに新しい枠で行う。
9. 触るのは、自分で作った要素（入れ物、画像、Accordion、警告、枠）の属性と、`<pre>` の置き場所だけである。要素の `style` には触らない（`el.style.x = …` も、`style` 属性を作り、`[style]` 0 件の試験を崩すので使わない）。

### 7.5 枠の側（`mermaid-frame.js`）

- 親（`window.parent`）からの `render` だけを受ける。描き終えたら `result` と `done` を返す。読み込みのあとに `ready` を返す。
- `mermaid.initialize` の設定は、`startOnLoad: false`、`securityLevel: "strict"`、`suppressErrorRendering: true`、`htmlLabels: false`、`flowchart.htmlLabels: false`、`theme: "base"`、`themeVariables`（親が送った値）、`fontFamily`、`secure` に既定の 6 つと `theme`、`themeVariables`、`themeCSS`、`fontFamily`、`htmlLabels`、`darkMode`、`look` を足したもの。PoC で、図の側の `%%{init}%%` がこれらを変えられないことを確かめた。
- 描いた SVG は、枠の中の入れ物に入れて `viewBox` から `width` と `height` を決め、根の `style` を外し、`XMLSerializer` で文字にして返す。`<title>` があれば、その文字を題として返す。
- 失敗（構文の誤り、tiny にない図、外の画像を読めない図）は、`result` の `ok: false` で返す。理由の文字は 300 字で切る。親は理由を画面に出さない。
- `done` には、枠の中で数えた CSP の違反を添える（試験が使う）。

## 8. デザイン（fluent2-html-replica）

`fluent2.css` の部品とトークンだけで組む。独自の色と大きさは足さない。

| 場面 | 部品とマークアップ |
| --- | --- |
| 図の入れ物 | `fui-Card`（appearance は既定の filled。地は `colorNeutralBackground1`、影は `shadow4`）。Mermaid は `<figure class="wiki-fig fui-Card" data-fig="mermaid">`、svg は段落の中の `<span class="wiki-fig fui-Card" data-fig="svg" data-theme="light">` |
| 画像 | `<img class="fui-Image">`。`width` と `height` は属性で付け、`style.css` で `max-width: 100%; height: auto` にする |
| コード | Accordion の形 A。`<details class="fui-AccordionItem wiki-fig-source">`、`<summary class="fui-AccordionHeader__button">` の中に `fui-AccordionHeader__expandIcon` の山形のアイコン（スキルの例と同じインラインの SVG）と「図のコード」、`<div class="fui-AccordionPanel">` の中に元の `<pre>`。開閉は CSS だけ（`fluent2.js` は使わない） |
| 描けなかった | `fui-MessageBar`（`data-intent="warning"`、`data-layout="singleline"`、`role="group"`、`aria-labelledby`）。アイコンは中核の `ICON_WARNING` と同じ形。文は「図を描けなかった。コードを表示している。」 |
| Mermaid の色と書体 | `base` テーマの `themeVariables` を、親が `getComputedStyle(document.documentElement)` で読んだトークンから作る（下の表）。Mermaid は 16 進の色しか読まないので、`#rgb`、`#rrggbb`、`rgb()` を `#rrggbb` にそろえる。読めないトークンは送らない（Mermaid の既定が使われる）。`darkMode` は `colorNeutralBackground1` の輝度で決める |
| 手書きの svg の暗い配色 | 入れ物に `data-theme="light"` を付け、`fluent2.css` の明るい配色のトークン（`[data-theme="light"]` の規則）を入れ物の中だけに効かせる。手書きの svg は色を決め打ちしていて、暗い地では読めなくなりうるからである |

| Mermaid の変数 | トークン |
| --- | --- |
| `background`、`edgeLabelBackground` | `--colorNeutralBackground1` |
| `primaryColor`、`mainBkg` | `--colorBrandBackground2` |
| `primaryBorderColor`、`nodeBorder` | `--colorBrandStroke1` |
| `primaryTextColor`、`secondaryTextColor`、`tertiaryTextColor`、`textColor`、`titleColor`、`noteTextColor` | `--colorNeutralForeground1` |
| `secondaryColor` | `--colorNeutralBackground3` |
| `secondaryBorderColor`、`noteBorderColor` | `--colorNeutralStroke1` |
| `tertiaryColor`、`clusterBkg` | `--colorNeutralBackground2` |
| `tertiaryBorderColor`、`clusterBorder` | `--colorNeutralStroke2` |
| `lineColor` | `--colorNeutralForeground2` |
| `noteBkgColor` | `--colorPaletteYellowBackground1` |
| `fontFamily`、`fontSize` | `--fontFamilyBase`、`--fontSizeBase300` |

`style.css` に足すのは、配置だけである（トークンで書き、px と 16 進の色を書かない）。

- `.wiki-fig`: `display: block; width: fit-content; max-width: 100%; margin-block: var(--spacingVerticalM); overflow-x: auto`。
- `.wiki-fig > img`: `display: block; max-width: 100%; height: auto`。
- `.wiki-fig-source`: `margin-block-end: var(--spacingVerticalL)`。
- `.fig-frame`: `position: absolute; inset-block-start: 0; inset-inline-start: -200vw; border: 0`。

## 9. 版

- `CORE_VERSION` を、PR 1（svg）で `browse-core-3`、PR 2（Mermaid）で `browse-core-4` に上げる。どちらも、同じ入力でページの HTML が変わる（PR 2 は `<meta>` の CSP と `_tail`）。世代は `CORE_VERSION` と入力から作るので、上げないと、静的の書き出しが前の世代のページを残しうる。
- `PROTOCOL_VERSION` は据え置く。データ（`nav.js` など）の形は変わらない。
- `FRAME_VERSION` は 7.2 のとおり。
- プラグインの版は、リリースのときに origin の最新を見て決める（0.26.0 は to884/info-hive-wiki#71 が名乗っている）。

## 10. 試験

### 10.1 unittest

| ファイル | 試験 |
| --- | --- |
| `test_browse_fs.py` | `walk_inputs` が `assets/*.svg` を `asset` で返す。下位のディレクトリ、`.` で始まる名前、`.png`、ファイルのシンボリックリンク、`assets` がリンクのときは入らない。`assets` がない。一覧を作れなければ problem。svg のない wiki の一覧と印が今と同じ。`read_input_capped` が上限 + 1 バイトで止まる |
| `test_browse.py`（写し） | svg の変更で印と世代が変わる。UTF-16 の svg と、`encoding="Shift_JIS"` の宣言の svg は `decode`。2 MiB を超える svg と、走査のあとに大きくなった svg は `too_large`。bytes が BOM と改行を保つ |
| `test_browse.py`（描画） | `figure_target` の表（`../assets/x.svg`、`assets/x.svg`、`%20`、`&amp;`、`#frag`、`?q`、`..` で外、`\`、URL、`data:`、png、下位のディレクトリ、NFD と NFC）。`<img>` の `src` が階層の違うページで正しい。`alt` の escape。ない svg は代替テキストと診断。見出しの中の画像で見出しの ID が変わらない。`style=` がない |
| `test_browse.py`（名前） | svg の出力の名前が、どのページの出力の名前とも、生成器のファイルとも重ならない |
| `test_browse.py`（同梱物） | `mermaid.tiny.js` の SHA-256 と大きさが README と一致する。`FRAME_VERSION` が README と `figures.js` の定数と一致する。`mermaid-frame.html` に `<meta>` の CSP、インラインのスクリプト、`style` がない。ライセンスの表示が `mermaid-frame.js` にある。静的の書き出しに枠の 3 つが入らない。`scan_machine_info` が同梱物を調べず、svg は調べる |
| `test_browse_server.py` | 同梱物ごとの `Content-Type` と CSP。`/_frame/<版>/` の 3 つはトークンなしで 200、枠の文書は `frame_csp(port)`、`Cache-Control: private, max-age=86400`。違う版、ほかの名前、`/_frame/` の下の `..`、Host の違いは 404 か 421。svg は 200、`image/svg+xml`、`CSP_SVG`。ない svg の名前は 404。HEAD。svg を変えると作り直す |
| `test_lint.py` か lint の試験 | `missing_assets` が `&amp;` を解いて探す |

変わる既存の試験: `test_browse_server.py` の CSP の一致（応答ごとの CSP）、`test_browse.py` の `img-src 'self' data:` の検査（`frame-src 'self'` を足す）と、同梱物の名前の並び。

### 10.2 Playwright

`tests/wiki/browse/figures.test.mjs` を新しく作る（`MODES` と `BROWSERS` は既存と同じ。CI は Chromium）。試験用の wiki に、図の種類ごとのフェンス、壊れたフェンス、tiny にない図（mindmap）、外の画像を使う図、svg の参照（ある、ない、png）、図のないページを置く。

- サーバーの方式: 図の数と描けた数、`naturalWidth > 0`、画像の中のスタイルが効いていること（決まった位置の画素の色が配色ごとの期待の色）、親の CSP の違反 0 件、枠の CSP の違反 0 件（外の画像を使う図の `img-src` を除く）、`[style]` 0 件、ID の重複 0 件、外への要求 0 件、描き終えたあとに iframe が残らない、図のないページに iframe がない、配色を変えると `src` が変わる、警告とコードが残る。
- 枠を閉じ込めていること: 試験が作った枠の中から、トークンの付いたページ、`nav.js`、`data/search.js` を `<script>` と `fetch` で読めない。枠の `document.referrer` が空。枠の文書を直接開いてもスクリプトが動かない（ヘッダーの `sandbox`）。svg を直接開いてもスクリプトが動かない。
- 静的の方式: iframe がない、`mermaid.tiny.js` を要求しない、コードが今と同じに出る、svg の `naturalWidth > 0`。
- 既存の `browse.test.mjs` と `findability.test.mjs` は変えない。既存のコーパスには mermaid も svg もないので、結果は変わらないはずである。
- CI（`.github/workflows/wiki-browse.yml`）に `figures.test.mjs` を足す。

## 11. 限界

- 静的の書き出しでは Mermaid を描かない。
- 図の中の文字は選べず、ページ内の検索に当たらず、図の中のリンクは効かない。ADR-0005 の「補足」の引用が文字の側を受け持つ。
- tiny にない図（マインドマップ、アーキテクチャ図、KaTeX、`layout: elk`）と、外の画像を使う図は描けない。コードと警告が出る。
- 図ごとに Mermaid を読み直すので、図の多いページでは描き終えるまでが長い。PoC では 13 個で 1.8〜3.4 秒だった（最初の図は 0.25〜0.5 秒。その回で最初に起動したブラウザは 1.9 秒）。
- 起動のたびに同梱物（約 3.5 MB）を読んで常駐させる。
- `wiki/assets/` の一覧を作れないと、入力の全体が採られず、閲覧が古い表示になる（今の決まりどおり）。
- 読む間だけ svg をリンクに替える同時の書き手は止めない（6.1）。
- lint は Windows で大文字と小文字の違う参照を通すが、browse は写しの綴りと一致するものだけを描く。
- 手書きの svg は配色に従わず、ハイコントラストでも色が変わらない。Mermaid の図も、ハイコントラストの色には従わない。
- 印刷、実機の Safari、Linux の WebKitGTK、アプリの方式は確かめていない。

## 12. 段取り

1. この設計と ADR-0030 を Sol にレビューしてもらい、直す。
2. PR 1（svg）: 6 節、`_send` の `csp` と `cache`、lint の文字参照、9 節の `browse-core-3`、10 節の svg の試験。
3. PR 2（Mermaid）: 7 節、8 節、`browse-core-4`、10 節の Mermaid の試験、利用者向けの文書（`README.md`、`docs/commands.md`、`commands/browse.md`、`references/page-conventions.md`）。
4. それぞれ実装のあとに Sol のレビューを受け、リリースする。
5. ADR-0005（将来の作業の行）、ADR-0010（範囲の外の行）、ADR-0002（見直す条件）、ADR-0001（トークンの例外）に追記し、`AGENTS.md` の「strict CSP (ADR-0010)」を ADR-0030 にも向ける。
