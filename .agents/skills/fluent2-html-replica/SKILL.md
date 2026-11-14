---
name: fluent2-html-replica
description: Microsoft の Fluent 2 の Web 版のデザイン言語を、React を使わない HTML と CSS で忠実に再現する非公式のスキル（公式の Fluent UI のライブラリではない）。トークン（色、書体、間隔、角丸、影、動き）の CSS 変数、FluentProvider に当たる土台、47 種類のコンポーネントの CSS と小さな JS、日本語の設計書を同梱する。「Fluent 2 の見た目にして」「Microsoft / Office / Teams 風のデザインで HTML を作って」「既存の HTML ページを Fluent 2 にして」「Fluent 2 のデザインシステムを作って」「Fluent のトークンで CSS を書いて」のような依頼で使う。React の @fluentui/react-components で実装するときは、このスキルではなく React 向けのスキルか公式の文書を使う。
---

# Fluent 2 Web（React を使わない HTML と CSS 版）

Fluent 2 の Web 版（基準: `@fluentui/react-components` 9.75.2、microsoft/fluentui commit `f9720c35`、2026-11-12）の見た目とふるまいを、React を使わない HTML と CSS で再現するためのスキルである。値はソースから抽出した。確かめた範囲は「検証の範囲」の節にある。非公式の再現であり、Microsoft の製品ではない。

## 同梱のファイル

| ファイル | 中身 |
|---|---|
| `assets/fluent2.css` | すべての CSS を 1 つにまとめたもの。使う側のプロジェクトに写して読み込む |
| `assets/fluent2.js` | CSS だけで表せない振る舞い（トグル、矢印キー、TabList の下線、Toast など）。`data-fui-enhance` を付けた要素だけを扱う |
| `references/*.md` | 設計の原稿。エージェントはここを読む |
| `references/tokens.md` | トークンの全値の表（Grep で引く） |
| `scripts/brand_ramp.py` | 1 つのキーの色から、ブランドの 16 段（`--fui-brand-*`）の CSS を作る（テーマデザイナーと同じ計算。依存なし） |
| `scripts/_hue_map.py` | `brand_ramp.py` が使う色相の表（生成物） |
| `LICENSE`、`THIRD-PARTY-NOTICES.txt` | このスキルと、元になった Fluent UI のライセンスの表示 |

`assets/fluent2.css` は、次の 4 つの部分をこの順に連結したものである。章の中では、この部分の名前（`fluent2-tokens.css` など）で呼ぶ。部分ごとに先頭に見出しのコメントがあるので、`fluent2.css` の中を Grep で探せる。

| 部分 | 中身 |
|---|---|
| トークン（`fluent2-tokens.css`） | トークンの CSS 変数（light、dark、auto、high-contrast）とブランドの段階 `--fui-brand-*` |
| 土台（`fluent2-base.css`） | FluentProvider に当たる既定のスタイル、日本語の書体の拡張、アイコンの既定 |
| 部品（`fluent2-components.css`） | 部品の CSS。群ごとに `text`、`layout`、`actions`、`text-entry`、`choice`、`display`、`navigation`、`overlays` の順に並ぶ |
| 書体（`fluent2-typography.css`） | 書体のプリセットの class（`fui-Body1`、`fui-Title1` など 17 個） |

どのファイルも生成物である。直さずに使う。人が読む設計書の HTML は、公開のリポジトリ to884/fluent2-html-replica の `docs/fluent2-web-spec.html` にある。部品ごとの CSS と JS の原本は、開発用のリポジトリ（非公開）にある。どちらもこのスキルのフォルダーには入っていない。

## 進め方

### ページを作る、既存のページに当てる

1. `assets/fluent2.css`（と、振る舞いが要るなら `assets/fluent2.js`）を、使う側のプロジェクトに写して読み込む。
2. `<html lang="ja" data-theme="light">` にする（`dark`、`auto`、`high-contrast` も選べる）。ページの外枠か `<body>` に `class="fui-FluentProvider"` を付ける。
3. 部品は、`references/` の該当する章のマークアップをそのまま使う。class 名は v9 と同じ（`fui-Button`、`fui-Button__icon`）、バリエーションは data 属性（`data-appearance="primary"`、`data-size="small"`）、状態はネイティブの属性と ARIA（`disabled`、`aria-pressed`、`aria-selected`、`aria-expanded`）で表す。
4. 既存のページでは、`references/08-plain-html.md` の「既存の HTML ページに当てる手順」と置き換えの対応表に従う。
5. 部品にない独自の装飾も、色、間隔、角丸、影、書体、時間は必ずトークンの CSS 変数で書く（`var(--colorNeutralBackground1)`、`var(--spacingHorizontalM)`）。hex や px を直に書かない。

### アクセントカラー（ブランドの色）を変える

1 つのキーの色から、`scripts/brand_ramp.py` で 16 段の CSS を作り、`fluent2.css` の後に読む CSS に貼る。16 段を推定で作らない。

```bash
python scripts/brand_ramp.py "#5b5fc7"
```

標準エラーのコントラストの確認に「NG」があれば（終了コード 2）、キーの色を変えるか `--vibrancy` を変えて作り直し、利用者に結果を伝える。オプションと注意は `references/02-color.md` の「16 段の作り方」にある。

### デザインシステムを作る

`references/01-overview.md` で全体の構造を、`02`〜`07` で基盤の規則を確かめ、`assets/fluent2.css` のトークンの部分を土台にする。ブランドの色は、`--fui-brand-10`〜`--fui-brand-160` の 16 個を上書きして差し替える（`references/02-color.md`）。

## どの章を読むか

| 知りたいこと | 章 |
|---|---|
| 全体像、基準の版、値の出どころ | `references/01-overview.md` |
| 色のトークンの意味、状態の色、ブランド、ダーク、ハイコントラスト | `references/02-color.md` |
| 書体の段階、日本語の書体、Text | `references/03-typography.md` |
| ブレークポイント、グリッド、間隔、角丸、線 | `references/04-layout-shape.md` |
| アイコン（SVG の入手と書き方） | `references/05-iconography.md` |
| 影、背景幕、動き | `references/06-elevation-motion.md` |
| 文言の書き方、アクセシビリティ | `references/07-content-accessibility.md` |
| 読み込み方、テーマ、フォーカス、強制カラー、RTL、既存のページへの適用、ライセンス | `references/08-plain-html.md` |
| Button、CompoundButton、MenuButton、SplitButton、ToggleButton、Link、Toolbar、Label、Field、InfoLabel | `references/10-components-actions.md` |
| Input、Textarea、Select、Combobox、Dropdown、SearchBox、SpinButton、TagPicker | `references/11-components-text-entry.md` |
| Checkbox、RadioGroup、Switch、Slider、Rating、Tag、Badge | `references/12-components-choice.md` |
| Avatar、AvatarGroup、Persona、Card、Image、Divider、Skeleton、Spinner、ProgressBar、List | `references/13-components-display.md` |
| TabList、Nav、Breadcrumb、Accordion、Tree、Carousel、Table | `references/14-components-navigation.md` |
| Dialog、Drawer、Popover、Menu、Tooltip、Toast、MessageBar | `references/15-components-overlays.md` |
| トークンの値 | `references/tokens.md`（Grep で引く） |

章は大きいので、全体を読まずに、`## <Component>` の見出しを Grep で探してその節だけを読む。

## 守る規則

- 見た目の基準は React v9 である。サイト（fluent2.microsoft.design）の記述とずれる所は、章の「v9 との差と未確認の点」に書いてある。
- 部品の高さは size で 24、32、40px（small、medium、large）にそろう。本文の既定は 14px / 20px（`fui-Body1`）。
- フォーカスの表示は消さない。`:focus-visible` で、各部品の章のとおりに出る。独自の部品には `references/08-plain-html.md` の共通のフォーカスの規則を使う。
- `@media (forced-colors: active)` の規則と、`prefers-reduced-motion` の規則を消さない。
- 日本語のページでは `lang="ja"` を付ける。土台が欧文の Segoe UI を保ったまま日本語の書体（Yu Gothic UI、Meiryo UI ほか）を足す。長い本文の行間を広げるのは独自の判断として行う（`references/03-typography.md`）。
- 部品の働きに要る値を、マークアップの style 属性で渡さない（ProgressBar は `data-percent`、ポップオーバーは `popovertarget` か `commandfor` の暗黙のアンカー）。インラインの style とインラインの `<script>` を禁じる CSP（`style-src 'self'; script-src 'self'`）のページでは、`fluent2.css` と `fluent2.js` をファイルとして読み込む（`references/08-plain-html.md` の「厳しい CSP の下で使う」）。
- 配布するページや CSS には、`references/08-plain-html.md` の「ライセンスと商標」の表示を入れる。Segoe UI を Web フォントとして配らない。Microsoft のロゴや製品名を、Microsoft の製品であるかのように使わない。

## 検証の範囲

確かめたこと（記録は開発用のリポジトリ（非公開）の `docs/verification/` にある）:

- **トークン**: 本物の `@fluentui/tokens` 1.0.0-alpha.24 を読み、生成した CSS が出す CSS 変数の計算値を、light、dark、high-contrast、auto（OS が light と dark の両方）、dark の中の `.fui-FluentProvider`、独自のブランドを当てた light と dark の 7 通りで、459 個すべて比べて一致した。日本語のページ（`lang="ja"`）では、意図した拡張として `fontFamilyBase` と `fontFamilyNumeric` だけが違う。
- **ブランドの 16 段**: `scripts/brand_ramp.py` の出力を、本物のテーマデザイナーの `getBrandTokensFromPalette` と 4,850 通りの入力（485 色 × 10 組の目盛り。全 360 の色相を含む）で比べ、全段が一致した。生成した CSS を読んだときのトークンの値（ライト、ダーク、`auto`、入れ子の区画、内側で 16 段だけを差し替えた区画、カンマ区切りのセレクター、`html` のセレクター、ハイコントラスト）も、本物のテーマの値とブラウザーで照らした。
- **部品**: 本物の React v9 を並べて描き、`getComputedStyle` で比べた。前半の群（Text、Button 系、Link、Label、Field、Input、Textarea、Select、Dropdown、SearchBox、SpinButton、Checkbox、Radio、Switch、Slider、Badge、Tag）は、light、dark、RTL の静的な状態と hover、押下、フォーカスで一致した。後半の群（Avatar〜MessageBar、Toolbar）は、light と dark の静的な状態で、既知の構造の差を除いて一致した。

確かめていないこと: 強制カラー（forced-colors）、縮小モーション、動きの途中の値、浮く面の画面上の位置、実際の Tab キーでのフォーカスの判定（v9 は tabster、ここでは `:focus-visible`）、Chromium 以外のブラウザー。比較に含めていない部品（InfoLabel、Combobox、TagPicker、Rating の操作）は、個別に確かめた点だけを章に書いてある。これらの範囲では、v9 と細部が違うことがありうる。

## 仕上げの確認

- light と dark の両方で、文字と背景のコントラストが崩れていないか。
- Tab キーで全部の操作部品にフォーカスが移り、輪が見えるか。
- 部品の高さ（24、32、40px）と角丸（4px）が混ざっていないか。
- 独自の CSS に hex や px の直書きが残っていないか（`#` と `px` を Grep する）。
- 幅 320px で横のスクロールが出ないか。
