# browse の画面を Fluent 2 にする（2026年11月14日）

`/wiki:browse` の画面のレイアウトとデザインを、Fluent 2 の Web 版のデザインシステムに書き換える設計である。Fluent 2 は、React を使わない HTML と CSS で再現した非公式の CSS（スキル `fluent2-html-replica` の `fluent2.css`）で当てる。

| 項目 | 内容 |
| --- | --- |
| 状態 | 3 版目。試作の見た目は作者が承認した（2026年11月14日）。1 版目と 2 版目は、Sol の設計のレビュー（[design-review-1.md](../agent-runs/2026-11-14-wiki-browse-fluent2/design-review-1.md) は分類 A が 3 件、[design-review-2.md](../agent-runs/2026-11-14-wiki-browse-fluent2/design-review-2.md) は 1 件）で却下された |
| 対象 | `info-hive-wiki` の `browse_assets/`（`fluent2.css`、`style.css`、`app.js`、新しい `theme.js`）、`wiki_browse_core.py` の HTML の骨組み、開発リポジトリの `tests/wiki/` |
| 前提 | [browse の構造の直し](wiki-browse-structure-2026-11-11.md)が `info-hive-wiki` の main に入ってから実装する。F1 は[探しやすさの設計](wiki-browse-findability-2026-11-13.md)の実装と一緒に行う |
| 決定 | [ADR-0021](../adr/0021-wiki-browse-uses-fluent2-replica.md) |
| 試作 | `poc/browse-fluent2/`。撮った画面と確かめの結果は `docs/agent-runs/2026-11-14-wiki-browse-fluent2/shots/` にある |
| 同梱した資産 | `info-hive-wiki` のブランチ `feature/browse-fluent2` の `skills/info-hive/scripts/browse_assets/fluent2.css`（SHA-256 `0b393938…e8b4bb`）と `licenses/`、出どころの記録 `README.md` |

## 作者が決めたこと

| 日付 | 決定 |
| --- | --- |
| 2026年11月14日 | Fluent 2 化は、探しやすさの設計に組み込む。索引、サイドバー、検索と、全ページに共通の部分（土台、テーマ、スコープの札、注意の帯）は、探しやすさの実装で Fluent 2 の部品として作る（段 F1）。記事のページの部品は、そのあとの段で当てる（段 F2） |
| 同 | ライト、ダーク、OS に合わせる、を選べる配色の切り替えを足す |
| 同 | 必要ならプラグインのコードを変えてよい。実装はスキル `fluent2-html-replica` の場所に依存しない。要るファイルは写し、プラグインが自分で持つ |
| 同（試作を見たあと） | 試作の見た目で進める。プロジェクトの wiki の札は、中立の色（Badge の informative）にする。ユーザースコープの wiki の札は brand の色にする。木の字下げは 4 段目で止める |

## 2 回目のレビューで崩れた前提

| 分類 | 崩れた前提 | レビューの反例 | 3 版目 |
| --- | --- | --- | --- |
| A | 地が変わらない場所を、場所の名前で数え上げられる（メタ欄、関係表、被リンク） | Fluent の `fui-TableRow` は、操作できない表でもホバーで地を `colorSubtleBackgroundHover` に変える。暗い配色でメタ欄の「出典」の見出しのセルにポインターを置くと、同じ行のリンクが 4.18:1 になる | 場所を数え上げるのをやめた。地を状態で変えてよいのは操作できる要素だけにし、読むだけの入れ物（表の行、一覧の行）の操作の状態の地は打ち消す（4.2）。試験は、地が変わりうるすべての入れ物にポインターを置いて、中の文字を測る（6） |
| C | 状態ごとの測り方と、ライセンスの確かめの記録が十分である | 試作はホバーを各セレクターの 6 件までしか測らず、表の行を測っていなかった。ライセンスの確かめの結果を記録に書き残していなかった | 試作の `shoot.mjs` を、`#_main` と `#_nav` の `tr`、`li`、`a`、`summary`、`button`、ナビの項目、選択のすべてにポインターを置く形にした。LICENSE の全文の行が `style.css` にあることを確かめ、記録に残す |
| C | 長い種類の値で、種類のボタンの折り返しを確かめた | 試作は決まった 4 つの種類だけをボタンにしていた | 試作のボタンを、一覧にある種類の値から作る形（探しやすさ 4.1 と同じ）にした |

## 1 回目のレビューで崩れた前提

| 分類 | 崩れた前提 | レビューの反例 | 2 版目 |
| --- | --- | --- | --- |
| A | 止まっている状態の配色が 4.5:1 を満たせば、操作中も満たす | 暗い配色で検索の結果の行にポインターを置くと、地が `colorSubtleBackgroundHover` に変わり、brand のリンクの色の題名が 4.18:1 になる | 地が状態で変わる要素では、brand のリンクの色を使わず、中立の文字の色にする規則を足した（4.2）。試験は、止まっている状態だけでなく、ポインターを置いた状態と、選んだ状態も測る（6） |
| A | 親に折り返しを指定すれば、部品の中も折り返す | 200 文字のタグを持つページを幅 320 で開くと、`fui-Tag__primaryText` の `white-space: nowrap` で一覧が横にはみ出す | 利用者の文字を持つ Fluent の部品は、`nowrap` を外して折り返す規則を足した（4.3）。試験の材料に、長いタグ、種類の値、グループの名前を足した（6） |
| A | `fluent2.css` の先頭のコメントに、要る表示がすべて入っている | `fluent2.css` のコメントは Fluent UI と Fluent UI System Icons の表示だけで、`fluent2-html-replica` 自身の MIT の表示（Copyright (c) 2026 to884）がない。静的の書き出しだけを渡すと、その表示が欠ける | 出力に必ず入る `style.css` の先頭の `/*!` のコメントに、`fluent2-html-replica` の LICENSE の全文を写す（2.1）。試験で、出力の CSS に両方の表示があることを確かめる（6） |
| B | 試作の字下げは 4 段目で止まる | 試作は深さを 0 から数え、5 段目まで字下げしていた。索引の木には止める規則がなかった | 試作を直した。設計の文（4 節）は「1〜4 段目まで字下げし、5 段目より深い段は 4 段目と同じ位置」と書き直した |
| B | `ta-*` の配置が見出しのセルにも効く | 試作の `#_body th { text-align: start; }` が、詳細度で `th.ta-center` に勝つ | 試作の規則を `#_body .ta-*` にした。設計の 5 節に、配置の class が `#_body` の規則に負けないことを書いた |

## 1. 守ること

第 1 段階の設計の「守ること」、構造の直しの設計、探しやすさの設計の約束は、そのまま守る。この設計で特に関わるものと、足すものを挙げる。

| | 内容 |
| --- | --- |
| CSP | `default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'` を変えない。インラインの `style`、インラインのスクリプト、イベントの属性を出さない。`[style]` は 0 件、外への通信は 0 件 |
| 2 つの方式 | `file://` の静的版とサーバーで、同じ関数が同じ画面を描く（ADR-0010、ADR-0016） |
| スクリプトなし | 本文、メタ欄、被リンク、関係表、診断、索引の一覧が読める。配色は OS の設定に従う |
| 日本語の組版 | `line-break: strict`、`word-break: normal`、`overflow-wrap: anywhere` と、対応するブラウザでの `text-autospace` を、`#_main` と `#_nav` に当てる。`fluent2.css` にはこの指定がない |
| 画面の部品の名前 | ID は `_` で始める。`wl` で始まる class は、wikilink と、木と索引の行の状態つきの項目だけに使う（`test_browse.py` が `class="wl` の数を wikilink の数と照らす） |
| 画面の契約に足す例外 | `theme.js` と `app.js` は、`<html>` の `data-theme` を書き換えてよい。ほかは今と同じく、要素を作るほかに変えるのは class、`hidden`、`open`、`aria-*` だけで、要素の `style` には触らない |
| 独自の CSS | `style.css` の色、間隔、角丸、線、書体、時間は、トークンの CSS 変数で書く。hex と px を直に書かない（コメントを除く） |
| 同梱 | `fluent2.css` は書き換えずに使う。プラグインの実行と試験は、スキルの場所を読まない |

## 2. 資産

### 2.1 `fluent2.css`

スキル `fluent2-html-replica` の `assets/fluent2.css`（625,811 バイト）を、書き換えずに `browse_assets/fluent2.css` に写す。写した元、基準の版（`@fluentui/react-components` 9.75.2、`@fluentui/tokens` 1.0.0-alpha.24、microsoft/fluentui `f9720c35`）、SHA-256、写し直す手順は、`browse_assets/README.md` に記録する。前例は `_vendor/README.md` である。

部品の群を切り出さずに全体を写す。

- SHA-256 で、写した元と同じであることを確かめられる。
- 部品の群をまたぐ依存がある。Nav の区切り線は表示の群の Divider で描き、Toolbar は Button の CSS に頼る。actions の群は at-rule を群の末尾にまとめている。切り出す手順を作ると、その手順の誤りを確かめる手間が増える。
- 検索欄と並べ方の選択に、文字入力の群も要る。使わない群は、カルーセルやダイアログなど一部だけである。

ライセンスの文書（スキルの `LICENSE` と `THIRD-PARTY-NOTICES.txt`）は `browse_assets/licenses/` に置く。`fluent2.css` の先頭の `/*!` のコメントに Fluent UI と Fluent UI System Icons の著作権表示と許諾の文が入っているので、静的の書き出し（再配布物）に写した `fluent2.css` にも表示が付いて回る。`licenses/` は閲覧の出力に入れない。`asset_bytes` は名前の最後の要素だけで `browse_assets/` を引くので、下のディレクトリは資産にしない。

`fluent2.css` のコメントにない表示が 1 つある。`fluent2-html-replica` 自身の LICENSE（MIT、Copyright (c) 2026 to884）である。これは、出力に必ず入る `style.css` の先頭の `/*!` のコメントに全文を写す。`style.css` はプラグインのファイルなので、`fluent2.css` を書き換えずに済む。`licenses/` の `THIRD-PARTY-NOTICES.txt` のうち、three.js、css.land、CSS Color 4 の表示は、スキルの `brand_ramp.py` のもので、`fluent2.css` には入っていないので写さない。

Microsoft の製品ではないこと、商標の帰属、Segoe UI を同梱しないことは、`browse_assets/README.md` とプラグインの `README.md` に書く。

### 2.2 `fluent2.js` は積まない

スキルの `fluent2.js` は、要素の `style` に書き込む（`setProperty` ほか）。`[style]` が 0 件であることの試験と、画面の契約に反する。

この設計で使う部品は、見た目をどれも CSS だけで出せることを試作で確かめた（Nav の `<details>`、Badge、Tag、ToggleButton、SearchBox、Select、Table、MessageBar の multiline、Link、List）。`fluent2.js` が受け持つふるまいのうち、この設計で要るのは次の 2 つで、どちらも `app.js` が受け持つ。

| ふるまい | `app.js` の受け持ち方 |
| --- | --- |
| ToggleButton の `aria-pressed` | 種類の絞り込みのボタンで、押したものだけを `true` にする（探しやすさの 4.3 の絞り込み） |
| SearchBox の消去ボタン | 押すと値を空にして欄にフォーカスを戻す。`mousedown` の既定の動作を止め、フォーカスを外さない |

### 2.3 `theme.js`（新しい資産）

`<head>` で、2 つの CSS のあとに classic な `<script src>` で同期に読む。描く前に `data-theme` を決め、選んだ配色が一瞬だけ違う配色で描かれるのを防ぐ。3 節で書く。

### 2.4 `style.css`

閲覧の独自の CSS で、`fluent2.css` のあとに読む。今のファイルを元にし、色をトークンに替え、部品の独自の拡張を足す（4 節）。

### 2.5 中核で直す場所

| 場所 | 直すこと |
| --- | --- |
| `ASSETS` | `assets/fluent2.css` と `assets/theme.js` を足す。構造の直しのあとは、資産を起動のときに読み（構造の直し 3.3）、作ったファイルの一覧（ADR-0017）に入る |
| `_head` | `<html lang="ja" data-theme="auto" …>`。`<link>` を `fluent2.css`、`style.css` の順に置き、そのあとに `theme.js` の `<script src>` を置く。`<body class="fui-FluentProvider page-<種類>">` |
| `_scope_html` | 4 節の札にする |
| 注意の帯 | `#_stale` を MessageBar にする（4 節） |
| 記事のページの部品 | F2 で、`_meta_rows`、`_relations_html`、被リンク、診断に class を足す（5 節） |

サーバーの Content-Type は、`.js` なら JavaScript、それ以外は CSS の決まりで、足す資産はどちらかなので、直さない。

### 2.6 大きさ

サーバーは `Cache-Control: no-store` を付けるので、ページを移るたびに 625KB の `fluent2.css` を読む。127.0.0.1 からの読み込みなので、起動の速さの試験（1,000 ページで 5 秒）に収まる見込みだが、実装の段で測り、`fluent2.css` を読む時間と、ページを開いてから `navLoaded` になるまでの時間を記録する。目安を超えたら、資産だけのキャッシュの扱い（版を付けた名前と `max-age`）を別に設計する。

## 3. テーマと配色の切り替え

### 3.1 `data-theme`

中核が `<html lang="ja" data-theme="auto">` を書く。

- `fluent2.css` は、属性のない `<html>` を light に固定する。属性を付けないと、今の暗い配色への対応が退行する。`auto` なら、スクリプトなしでも OS の設定に従う。
- 土台は `[data-theme]` を付けた要素に、文字の色、地の色、書体、14px / 20px を当てる。`<html>` の文字の大きさが 14px になるので、長さの `rem` の基準も 14px になる。`style.css` は長さに `rem` を使わず、トークンと `em` で書く。media query の `rem` は初期値の 16px で決まるので、切り替えの幅（48rem = 768px）はそのまま使える。
- `style.css` で `color-scheme` を宣言する（`[data-theme="light"]`、`[data-theme="dark"]`、`auto` の dark の側）。スクロールバーや、ネイティブの選択の一覧を、配色に合わせるためである。v9 の FluentProvider は書かないが、スキルが使う側で足してよいとする逸脱である。
- Windows のハイコントラスト（強制カラー）は、`fluent2.css` の `forced-colors` の規則に任せる。独自の規則にも、今のページと絞っているグループの印をシステムの色で描く規則を足す。`data-theme="high-contrast"` は使わない。
- ブランドの色は、Fluent の既定のまま変えない。

### 3.2 切り替えの画面

`app.js` が、サイドバーの見出しの部分（スコープの札と「索引」の下）に、ラベル「配色」の `fui-Select`（small）を描く。選べるのは「OS に合わせる」（`auto`）、「ライト」、「ダーク」の 3 つで、選ぶとすぐ `data-theme` を変えて保存する。スクリプトなしでは描かない（配色は `auto` のまま）。

### 3.3 保存

| 方式 | 保存先 | 理由 |
| --- | --- | --- |
| http（サーバー） | cookie `info-hive-browse-theme`（`Path=/`、`Max-Age` 1 年、`SameSite=Strict`） | サーバーは起動ごとにポートが変わる（`port = 0`）。localStorage はオリジンごと、つまりポートごとに分かれるので、サーバーを起動し直すと消える。cookie はポートを区別しない |
| `file://`（静的版） | localStorage の同じキー | Chromium は `file://` で cookie を使わない |

- 値は `auto`、`light`、`dark` だけを読み、ほかの値は `auto` にする。
- 読み書きはすべて try/catch で包む。読めなければ `auto`、書けなければ今のページの配色だけを変える。
- 試作では、Chromium で次を確かめた（`docs/agent-runs/2026-11-14-wiki-browse-fluent2/shots/report.json`）。
  - `file://` でダークを選ぶと、ページを移っても `dark` が残る。
  - ポートの違う 2 つのサーバーで、一方で選んだ `dark` が他方でも効く。
  - localStorage が例外を出すとき、選んだページでは `dark` になり、読み直すと `auto` に戻り、ページのエラーは出ない。
  - スクリプトを切ると `auto` になる。

## 4. 部品の対応（F1）

探しやすさの設計の 3〜5 節と 7 節の画面の部品を、次の Fluent 2 の部品で描く。マークアップは、スキルの各部品の章のとおりにする。部品の章にない拡張は「独自」と書き、`style.css` にトークンで書く。

| browse の部分 | Fluent 2 の部品 | 補足 |
| --- | --- | --- |
| ページの外枠 | `body.fui-FluentProvider` と独自の 2 列のグリッド | ナビの幅は `--f2-nav-width`（260px、v9 の Nav の既定）。切り替えの幅は探しやすさの 48rem を保つ。Fluent の `f2-app`（1024px で 2 列）は使わない（独自）。ナビの列の地を、本文の下までのばす |
| `#_nav` | `nav.fui-NavDrawer` の中に `div.fui-NavDrawerHeader`（札、索引、配色）と `div.fui-NavDrawerBody`（検索欄、木） | 地は `colorNeutralBackground4`。広い幅では `position: sticky` で画面の高さに収め、中だけを送る |
| スコープ `#_scope` | `p#_scope.scope.scope-<kind>` の中の `span.fui-Badge`（tint、large、rounded） | ユーザースコープは brand、プロジェクトは informative（作者の決定）。文字は今と同じ「ユーザースコープの wiki」「プロジェクトの wiki」で、色だけで見分けさせない |
| 索引へのリンク `.nav-home` | `a.fui-NavItem.nav-home` | |
| 記事のページの検索欄 `#_q` | `span.fui-SearchBox.fui-Input`（small）、虫めがねと消去のインライン SVG | 下に `fui-Caption1` の「/ で検索欄に移る」。結果は `ul.fui-List`、行は `a.sr-link`（ホバーは `colorSubtleBackgroundHover`）。行の地が変わるので、題名は `colorNeutralForeground1` の semibold、階層は `colorNeutralForeground2` の `fui-Caption1`（4.2） |
| 記事のページの木（`<details>` の入れ子） | 各グループを `details.fui-NavCategory` と `summary.fui-NavCategoryItem`、中身を `div.fui-NavSubItemGroup`、ページを `a.fui-NavSubItem` | Nav の章は入れ子を 1 段までとし、深い階層には Tree を勧める。Tree は `role=tree` の `div` で、開閉に JS が要り、項目のリンクと競合するので使わない。NavCategory を各段に繰り返す独自の拡張にする |
| 木の深い段 | 独自 | 1 段目から 4 段目までは 1 段ごとに `spacingHorizontalL` だけ字下げし、5 段目より深い段は 4 段目と同じ位置に置く（作者の決定）。5 段目より深い段のグループには、左に `colorNeutralStroke2` の縦の線を引いて段を示す。索引のページの左の木も同じ規則にする。長い名前は折り返す。試作の 6 段の木で、260px の幅に収まることを確かめた |
| 今のページ | `aria-current="page"` と `is-current` | Nav の選択の印（`::after`）は、入れ子の NavSubItemGroup の中で切れて見えなかった（スキルの章も未確認の点に挙げる）。印は、`colorNeutralBackground4Selected` の地と、左の `colorCompoundBrandForeground1` の内側の影で描き、`::after` は消す（独自） |
| グループの件数 | `span.fui-Caption1.tree-count` | `colorNeutralForeground3` |
| グループの「一覧」のリンク | `a.fui-Link`（`tree-filter`） | `visibility` で出し入れする規則（探しやすさ 3.1）を保つ |
| 未解決と曖昧の項目 | `span.fui-NavSubItem.wl.wl-<状態>` | 今と同じく `wl` で始まる class |
| 狭い幅の「メニュー」（`details.drawer`） | `summary.fui-Button`（subtle）。Fluent のオーバーレイの Drawer は使わない | Nav の章はオーバーレイの Drawer を扱っていない。48rem より広いときは `app.js` が開き、`summary` を隠す |
| 索引のページの左の木 | `a.fui-NavItem` の入れ子と件数。先頭に「すべてのページ」 | 絞っているグループは `aria-current="true"` と `is-current`（探しやすさ 3.2） |
| 索引のページの見出し `#_ixhead` | `h1.fui-Title2`、件数は `p.fui-Caption1` | |
| 絞り込みの帯 `#_filters` | SearchBox（small）、種類の `button.fui-ToggleButton.fui-Button`（small、circular、`aria-pressed`）、並べ方の `span.fui-Select`（small） | 帯は `colorNeutralBackground2` の地と `colorNeutralStroke2` の線（独自）。広い幅では `position: sticky` |
| 件数 `#_count` | `p.fui-Caption1` | `aria-live="polite"` は今のとおり |
| 一覧の行 `.fx-row` | 独自（List の行に下の線） | 階層 `fx-path` は `fui-Caption1`、題名 `ix-title` は 16px の semibold で brand のリンクの色、要約は `colorNeutralForeground2` |
| 種類の印 `badge t-<type>` | `span.fui-Badge`（tint、small、rounded）と `t-<type>` | 4 つの種類の色は、パレットの `Background2` と `Foreground2` の組（Avatar の色の組）で当てる（独自）。ソースは Pumpkin、エンティティは Lavender、コンセプトは Teal、シンセシスは Cornflower、ほかは中立 |
| タグ `span.tag` | `span.tag.fui-Tag`（outline、extra-small）と `span.fui-Tag__primaryText` | `app.js` は今のとおり `span.tag` の文字を読む |
| `<mark>` | 独自 | 地は `colorPaletteYellowBackground2`、文字は `colorNeutralForeground1` |
| 状態の表示（探しやすさ 5.5）と、構造の直しの「不完全」「描けない」の印 | 欄の下や件数の横は `fui-Caption1`。ページ全体に関わるものは MessageBar（info か warning） | 色だけで伝えず、文を出す |
| `#_index_unresolved`（探しやすさ 4.4） | 見出しは `h2.fui-Subtitle2`、行は `span.wl.wl-<状態>` | |
| 注意の帯（`#_stale` と、`app.js` の `notice`） | `div.fui-MessageBar`（`data-layout="multiline"`、intent は warning か error）、アイコンはインライン SVG、題名は `fui-MessageBarTitle` | `notice-updated`、`notice-error`、`stale` の class は残す（`browse.test.mjs` が使う）。`fui-MessageBarActions` は空白を入れずに書く |
| フォーカス | 各部品の `:focus-visible` の規則。独自の要素（一覧の題名、木の「一覧」、`summary`、本文のリンク）には `colorStrokeFocus2` の 2px の輪 | |
| 書体 | 土台の `:lang(ja)` の拡張（Segoe UI、Yu Gothic UI、Meiryo UI ほか） | 等幅は `--fontFamilyMonospace` のあとに BIZ UDGothic と Noto Sans Mono CJK JP を足す（独自）。Linux で日本語のゴシックに落ちるかを実装の段で確かめ、足りなければ `--fontFamilyBase` に Noto Sans CJK JP を足す |

この表は、探しやすさの 7 節の class の一覧、3〜5 節の画面の部品、構造の直しの 10 節の印のすべてを覆う。実装の段で部品を足すときは、この表に行を足す。

### 4.1 F1 の時点の記事のページ

F1 では、`data-theme` と切り替えが全ページに入るが、記事のページの部品は F2 で当てる。F1 を単独で出しても、記事のページの配色が混ざらないように、F1 に次を含める。

- 今の `style.css` の色を、すべてトークンに置き換え、`prefers-color-scheme` の規則をなくす。今の規則は OS の配色で暗くなり、`data-theme="dark"` に従わない。OS が light のままダークを選ぶと、`pre`、表の線、注意の帯だけが明るく残る。対象は、本文、メタ欄、被リンク、関係表、診断、`wl-*`、`pre`、表の線である。
- 記事の本文の大きさと行間を、今の 16px（`fontSizeBase400`）/ 1.8 に保つ。土台の 14px / 20px にしない。
- 配置（`table` の `display: block` と横の送り、`pre` の横の送り、本文の幅）は変えない。

### 4.2 状態で地を変える要素と、文字の色

1 回目と 2 回目のレビューは、どちらも「地が状態で変わる場所で、brand のリンクの色が 4.5:1 を割る」反例だった。2 版目は、地が変わらない場所を名前で数え上げたが、Fluent の部品（`fui-TableRow`、`fui-ListItem` ほか）は、操作できなくてもホバーで地を変えることがある。場所を数え上げずに、次の 2 つの規則にする。

- **地を状態で変えてよいのは、操作できる要素だけにする。** 操作できる要素は、リンク（`a`）、ボタン、`summary`、選択と入力欄、ナビの項目である。読むだけの入れ物（`#_main` の中の表の行と一覧の行）は、Fluent の部品がホバーや押下で地を変えても、`style.css` で地を透明に戻す。操作できない入れ物が地を変えると、押せるように見えるという Fluent の指針にも合う。
- **操作できる要素のうち、自分の地が状態で変わるものは、文字に brand のリンクの色を使わない。** 検索の結果の行、ナビの項目、グループ、種類のボタン、選択では、文字を `colorNeutralForeground1`、補いを `colorNeutralForeground2` にする。Fluent の部品の状態の色は、部品の CSS に任せる。

brand のリンクの色（`colorBrandForegroundLink`）を使うのは、本文、索引の一覧の題名、メタ欄、被リンク、関係表のリンクで、どれも祖先の地が状態で変わらない（上の 1 つ目の規則）。リンク自身のホバーでは、Fluent の Link と同じく地を変えず、文字を `colorBrandForegroundLinkHover` にする。

暗い配色で、`colorBrandForegroundLink` と `colorSubtleBackgroundHover` の組は 4.18:1、`colorNeutralBackground1Hover` との組は 3.87:1 で、4.5:1 を割る。`colorNeutralForeground1` はどの地とも 10:1 以上、`colorNeutralForeground2` は 7.47:1 以上である（同梱した `fluent2.css` の値で計算した）。

この規則は試験で守る（6）。地が変わりうるすべての入れ物にポインターを置き、中の文字を測るので、新しい部品を足したときも、規則に外れれば試験が落ちる。

### 4.3 利用者の文字を持つ部品の折り返し

Fluent の部品のいくつかは、文字を折り返さない（`white-space: nowrap`）。Tag の `fui-Tag__primaryText`、Badge、Button、ToggleButton、Nav の項目である。利用者の文字（ページの題名、グループの名前、タグ、種類の値、未解決のリンクの行き先、検索の結果）を入れる部品では、`style.css` で `white-space: normal`、`overflow-wrap: anywhere`、`max-width: 100%`、`height: auto` にして折り返す。決まった文字だけを入れる部品（スコープの札、配色の選択、種類のボタンのうち 4 つの決まった種類）は、この規則がなくてもはみ出さないが、種類のボタンには利用者の種類の値も入る（探しやすさ 4.1）ので、ボタンにも当てる。

## 5. 記事のページ（F2）

F1 の上に、記事のページの部品を当てる。試作の記事のページは、この形で描いた。

- `#_body`（Markdown の出力。class は足さない）
  - 本文は 16px、行間は 1.8（独自の判断。スキルの `f2-prose` は 1.7）。幅は 48em。
  - 見出し: h1 は `fontSizeHero700`、h2 は `fontSizeBase600` で下に線、h3 は `fontSizeBase500`、h4 は `fontSizeBase400`。どれも semibold で、`lineHeight` は同じ段のトークン。
  - リンクは `colorBrandForegroundLink` で下線を付ける（文中のリンクの指針）。外部のリンクの「↗」、`wl-unresolved`（`colorPaletteRedForeground1` の点線）、`wl-ambiguous`（`colorPaletteMarigoldForeground2` の波線）、`wl-missing-heading` は残し、色だけで区別しない。
  - コード、`pre`、引用、`hr` は、`colorNeutralBackground3`、`borderRadiusMedium`、`colorNeutralStroke1` ほかのトークンで書く。
  - 表は今と同じく `display: block` で横に送り、線と余白をトークンで書く。`ta-*` は残し、`#_body .ta-left` のように書いて、`#_body th` の揃えの規則に詳細度で負けないようにする。
- 中核が描く部分には class を足す。
  - `#_meta`: `table.meta.fui-Table`（small）。行は `fui-TableRow`、見出しのセルは `fui-TableHeaderCell`（`scope="row"`）、値は `fui-TableCell`。幅は内容に合わせる（独自）。
  - `#_relations`: `table.relations.fui-Table`（small）を、`overflow-x: auto` の `div.table-scroll`（独自）で包む。9 列なので最小幅を 48em にし、セルの中で語を折らない。幅 360px でも `#_main` からはみ出さず、表だけを横に送る。
  - `#_backlinks`: `ul.fui-List` と、brand のリンクの色。
  - `#_diagnostics`: 見出しは `fui-Subtitle2`、一覧の印は `colorStatusWarningForeground3`。`li` の数え方は変えない。
- 見出し（被リンク、関係、診断）は `h2.fui-Subtitle2`。
- サーバーの 404 のページは範囲の外とする（探しやすさと同じ）。

## 6. 試験

探しやすさの 9 節の試験に、次を足す。

| 場所 | 確かめること |
| --- | --- |
| `test_browse.py` | `browse_assets/fluent2.css` の SHA-256 が `browse_assets/README.md` の記録と同じで、先頭に通知のコメントがあること。静的の書き出しに `assets/fluent2.css` と `assets/theme.js` があり、同梱のファイルとバイト列が同じであること。`licenses/` が出力にないこと |
| 同 | ページの `<html>` に `data-theme="auto"` があり、`<head>` の中で `fluent2.css`、`style.css`、`theme.js` の順に読むこと |
| 同 | `style.css` に hex の色と px の長さがないこと（コメントを除く） |
| `test_browse_server.py` | サーバーが `fluent2.css` と `theme.js` を返し、Content-Type が CSS と JavaScript で、静的版と同じバイト列であること |
| `browse.test.mjs` | `[style]`、ID の重複、CSP の違反、外への要求が 0 件のまま。配色を切り替えたあとと、探しやすさの操作のあとにも確かめる |
| 同 | スクリプトを切ると `data-theme` が `auto` で、索引の一覧が読めること |
| 同 | ダークを選ぶと、ページを移っても `dark` が残ること。`file://` と、サーバーを止めて起動し直したあと（ポートが変わる）の両方で確かめる |
| 同 | 保存先が例外を出すとき（localStorage を壊す、cookie を読めない）、配色は `auto` になり、ページのエラーが出ないこと |
| 同 | 主な要素（本文、見出し、本文のリンク、未解決と曖昧のリンク、スコープ、ナビの項目、今のページ、グループの名前と件数、メタ欄の見出し、注意の帯、4 つの種類の印、タグ、要約、索引の題名、グループの階層、被リンク、診断、検索の結果の題名と階層、種類のボタン、配色の選択）の文字と地のコントラスト比が、light と dark の両方で 4.5:1 以上であること。`getComputedStyle` で、一致するすべての見えている要素を測る。さらに、`#_main` と `#_nav` の中の地が変わりうるすべての入れ物（`tr`、`li`、`a`、`summary`、`button`、ナビの項目、選択）に 1 つずつポインターを置き、その入れ物の中の文字を測る。選んだ状態（今のページ、絞っているグループ、押した種類のボタン）でも測る |
| 同 | 長い値（200 文字のタグ、120 文字の種類の値、長いグループの名前と題名）を持つ Wiki を、幅 320 で索引と記事のページを開き、はみ出さないこと |
| `test_browse.py` | 静的の書き出しの CSS（`fluent2.css` と `style.css`）に、`Copyright (c) Microsoft Corporation` と、`fluent2-html-replica` の LICENSE の全文があること |
| 同 | `forcedColors: "active"` で開き、今のページの項目と絞っているグループに輪郭があること |
| 同 | 幅 320、360、600、1000 で、`#_main` とページが横にはみ出さず、禁則の違反が 0 件であること |
| `startup.test.mjs` | 5 秒の目安を保つ。`fluent2.css` を読む時間を記録する |

書き換える試験: `_scope` と `#_nav` の文字列の完全一致（`test_browse.py` の 969、971-972、992 行、`test_browse_server.py` の 600、723 行）。札の中身が `span.fui-Badge` になり、`#_nav` に class が付くためである。

## 7. 振る舞いが変わる点

| 変わる点 | 今 | 直したあと |
| --- | --- | --- |
| 画面のデザイン | GitHub に似た独自の CSS | Fluent 2 のトークンと部品 |
| 配色 | OS の設定に従う | 既定は OS の設定に従い、ライトとダークを選べる。選んだ値は残る |
| 書体 | system-ui から始まる並び | Segoe UI と日本語の書体の並び（`fontFamilyBase` の日本語の拡張） |
| スコープの札 | ユーザースコープは青、プロジェクトは緑 | ユーザースコープは brand の色、プロジェクトは中立の色。文字は同じ |
| 閲覧の出力 | `assets/` に 2 ファイル | `assets/fluent2.css` と `assets/theme.js` が増える（約 630KB） |

## 8. 順序

構造の直しが `info-hive-wiki` の main に入ってから始める。

1. F1: 探しやすさの設計の 10 節の順に進め、その中で次を行う。
   1. `feature/browse-fluent2` の同梱の資産を土台にして、`ASSETS`、`_head`、`theme.js`、`data-theme` を入れる。
   2. 4.1 のとおり、今の `style.css` の色をトークンに替える。
   3. サイドバー、索引、検索を、4 節の部品で描く。`style.css` は、試作の `poc/browse-fluent2/assets/style.css` の索引とサイドバーの規則を下敷きにする。
   4. 6 節の試験を足し、試作の `shoot.mjs` の確かめを `browse.test.mjs` に移す。
   5. Sol の実装のレビューを受け、マイナー版を上げて出す。
2. F2: 5 節を当てる。試験、レビュー、リリースは F1 と同じにする。

版は、利用者に見える変更なので、F1 と F2 のそれぞれでマイナー版を上げる。0.15.0 は main で使われているので、0.16.0 以上になる。番号はマージの前に `origin/main` とタグを見て決める。

## 9. 限界

- **CSS 変数の名前に保証はない。** `--colorNeutralBackground1` などの名前は Fluent の内部の実装で、版で変わりうる。同梱した `fluent2.css` の版に固定し、写し直すときは画面を確かめ直す。
- **Segoe UI は同梱しない。** Segoe UI のない環境（macOS、Linux）では、並びの次の書体で表示する。
- **配色の保存は、http では 127.0.0.1 のほかのサービスとも cookie を共有する。** 値は配色だけである。cookie を使えないブラウザでは、サーバーを起動し直すと OS の設定に戻る。
- **`file://` の localStorage の範囲は、ブラウザで違う。** Chromium は `file://` の全体で 1 つにするが、ほかのブラウザでは書き出したフォルダーごとに分かれうる。5 つのブラウザでの確かめは実装の段で行う。
- **v9 と細部が違う。** フォーカスの判定は `:focus-visible` の近似である。強制カラー、縮小モーション、Chromium 以外のブラウザは、スキルも確かめていない。
- **木の深い段は Fluent の部品にない。** 4 節の独自の拡張で描く。
- **サーバーは資産をキャッシュさせない。** ページを移るたびに `fluent2.css` を読む（2.6）。

## 範囲の外

- RTL（日本語の画面だけを描く）
- ブランドの色の差し替え（`brand_ramp.py`）
- `fluent2.js` が要る部品（Tooltip、Dialog、Popover、Toast など）
- サーバーの 404 のページ
- アプリ（Tauri など）で開いたときの見た目

## レビューの指摘と対応

### 2 回目（[design-review-2.md](../agent-runs/2026-11-14-wiki-browse-fluent2/design-review-2.md)、却下。分類 A が 1 件）

| 分類 | 指摘 | 対応 |
| --- | --- | --- |
| A | メタ欄と関係表の行のホバーで、同じ行のリンクが 4.18:1 | 4.2 を、場所の数え上げから、2 つの規則（読むだけの入れ物は地を変えない、地が変わる操作の要素は中立の文字）に改めた。試作で、33 の画面の地が変わりうる入れ物のすべてにポインターを置き、最小は 5.18:1 だった |
| C | ホバーの測り方が 6 件まで。ライセンスの確かめの結果が記録にない | 試作の `shoot.mjs` を直した |
| C | 長い種類の値のボタンを確かめていない | 試作のボタンを、一覧の種類の値から作るようにした |

### 1 回目（[design-review-1.md](../agent-runs/2026-11-14-wiki-browse-fluent2/design-review-1.md)、却下。分類 A が 3 件）

| 分類 | 指摘 | 対応 |
| --- | --- | --- |
| A | 暗い配色の検索の結果のホバーで、題名が 4.18:1 | 4.2 の規則と、状態ごとに測る試験（6）。試作を直し、ポインターを置いた状態の最小は 8.07:1 になった |
| A | 長いタグで索引が横にはみ出す | 4.3 の規則と、長い値の試験（6）。試作の材料に長い値を足し、幅 320 ではみ出さないことを確かめた |
| A | 出力に `fluent2-html-replica` 自身の著作権表示がない | 2.1 で `style.css` に写すと決め、試験（6）を足した。試作の出力の 3 つの案で、両方の表示があることを確かめた |
| B | 字下げを止める段がずれ、索引の木に止める規則がない | 試作を直し、4 節の文を書き直した |
| B | 表の見出しのセルの `ta-*` が負ける | 試作を直し、5 節に書いた |
| C | 確かめの記録が、最初の要素だけを測り、ホバーを測らず、コントラストを問題の判定に入れていない | 試作の `shoot.mjs` を、すべての要素、ポインターを置いた状態、コントラスト比を判定に入れる形に直した。禁則、強制カラーの輪郭、F1 だけの記事のページは、実装の試験（6）で確かめる |
