# React を使わない HTML への適用

この章は、React を使わない HTML と CSS で Fluent 2 の見た目を当てる方法を定める。

結論を先に書く。

- CSS は `assets/fluent2.css` を 1 つ読む。中は、トークン、土台、部品、書体の順に並んでいる。書体のプリセットを最後に置くのは、v9 と同じく、プリセットの class が部品のスタイルに勝つようにするためである。
- テーマは `data-theme` 属性で選ぶ。値は `light`（既定）、`dark`、`auto`（OS の設定に従う）、`high-contrast` である。属性を付けた要素ごとに、テーマの変数と、文字の色、背景の色、書体が当て直される。v9 の FluentProvider に当たる。
- ブランドの色は、`--fui-brand-10` から `--fui-brand-160` の 16 個を、`data-theme` を付けた要素か `:root` で上書きして差し替える。
- フォーカスの表示は `:focus-visible` で近似する。Windows のハイコントラストは `@media (forced-colors: active)` で扱い、システムカラーのキーワードを使う。左右は論理プロパティで書き、`dir` は `<html>` に付ける。
- CSS 変数の名前は Fluent の内部の実装で、将来の版で変わりうる。追従する版を固定し、更新のたびに生成し直す。

## CSS の読み込み方

### ファイルの役割

`assets/fluent2.css` は、次の 4 つの部分をこの順に連結したものである（生成物。直さない）。章の中では、この部分の名前で呼ぶ。

| 部分 | 中身 |
|---|---|
| トークン（`fluent2-tokens.css`） | トークンの CSS 変数（light、dark、auto、high-contrast）とブランドの段階 `--fui-brand-*` |
| 土台（`fluent2-base.css`） | FluentProvider に当たる既定のスタイル、日本語の書体の拡張、アイコンの既定 |
| 部品（`fluent2-components.css`） | 部品の CSS。群ごとに `text`、`layout`、`actions`、`text-entry`、`choice`、`display`、`navigation`、`overlays` の順に並ぶ |
| 書体（`fluent2-typography.css`） | 書体のプリセットの class（`fui-Body1`、`fui-Title1` など 17 個） |

この順に並べてある。土台はトークンの変数（`--fontFamilyBase` など）を使い、部品の CSS は土台の既定（たとえば `.fui-Icon-filled { display: none; }`）を上書きする前提で書かれている。いまの規則の多くは詳細度でも勝つが、詳細度の等しい規則は後に書いたものが勝つので、順を変えると表示が変わるおそれがある。

### ページの骨組み

```html
<!doctype html>
<html lang="ja" dir="ltr" data-theme="light">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ページの題</title>
  <link rel="stylesheet" href="assets/fluent2.css">
</head>
<body>
  …
</body>
</html>
```

- `lang="ja"` を付ける。土台の日本語の書体の拡張は `:lang(ja)` で効く（`<html>` に `data-fui-cjk-fonts="off"` を付けると無効になる）。
- `dir` を `<html>` に付ける（RTL の節）。
- `data-theme` を `<html>` に付けると、ページ全体のテーマになり、ページの背景の色も決まる。

## FluentProvider に当たるもの

### v9 の FluentProvider がすること

| 働き | v9 の実装 | 出典 |
|---|---|---|
| トークンを CSS 変数にする | `<head>` に `<style id="fui-FluentProvider1">` を作り、`.fui-FluentProvider1 { --colorNeutralForeground1: #242424; … }` のように、テーマのすべてのトークンを `--<トークン名>` で書く。接頭辞もハッシュもない | `packages/react-components/react-provider/library/src/components/FluentProvider/createCSSRuleFromTheme.ts:46-64`、`packages/react-components/react-provider/library/src/components/FluentProvider/useFluentProviderThemeStyleTag.ts:15-30` |
| 根の要素 | `<div class="fui-FluentProvider fui-FluentProvider1" dir="ltr">`。`dir` を必ず付ける | `packages/react-components/react-provider/library/src/components/FluentProvider/useFluentProvider.ts:99`、同 `:101-115` |
| 既定のスタイル | 根の要素に、文字の色、背景の色、`text-align`、`body1` の書体を当てる | `packages/react-components/react-provider/library/src/components/FluentProvider/useFluentProviderStyles.styles.ts:13-20` |
| フォーカスの表示 | キーボード操作中だけ、フォーカスされた要素に `data-fui-focus-visible` を付ける | `packages/react-components/react-provider/library/src/components/FluentProvider/useFluentProvider.ts:112` |
| ポータル | `applyStylesToPortals`（既定は `true`）のとき、根の class 全体と `dir` を、body の直下に出すポップアップの差し込み先にも写す | `packages/react-components/react-provider/library/src/components/FluentProvider/useFluentProvider.ts:50`、`packages/react-components/react-portal/library/src/components/Portal/usePortalMountNode.ts:67-68` |
| 入れ子 | 子のプロバイダーは親のテーマと自分の `theme` を浅く合成し、合成した全部のトークンを書き出す。部分的なテーマも渡せる | `packages/react-components/react-provider/library/src/components/FluentProvider/useFluentProvider.ts:59`、同 `:127-138` |

### この設計書での対応

| v9 | React を使わない HTML |
|---|---|
| テーマの CSS 変数 | `fluent2-tokens.css` が、`:root`、`[data-theme="light"]`、`[data-theme="auto"]` に light の値を、`[data-theme="dark"]` に dark の値を、`[data-theme="high-contrast"]` にハイコントラストの値を宣言する。`[data-theme="auto"]` は、`@media (prefers-color-scheme: dark)` の中で dark の値になる |
| 根の要素の既定のスタイル | `fluent2-base.css` が、`.fui-FluentProvider` と `[data-theme]` に、下の表の宣言を当てる |
| `data-fui-focus-visible` | `:focus-visible` で近似する（フォーカスの節） |
| ポータル | `popover` 属性と `<dialog>` を使い、DOM の位置を変えない。変数と色をそのまま継ぐ |
| 入れ子 | `data-theme` を付けた要素を入れ子にする。`.fui-FluentProvider` はトークンを宣言し直さず、親のテーマを継ぐ |

既定のスタイル（`packages/react-components/react-provider/library/src/components/FluentProvider/useFluentProviderStyles.styles.ts:13-20`）:

| プロパティ | 値 | light の値 |
|---|---|---|
| `color` | `var(--colorNeutralForeground1)` | `#242424` |
| `background-color` | `var(--colorNeutralBackground1)` | `#ffffff` |
| `text-align` | `start`（v9 は `left` を Griffel が RTL で `right` に反転する。`start` が同じ結果になる） | — |
| `font-family` | `var(--fontFamilyBase)` | Segoe UI から始まるフォントスタック（日本語では土台が拡張する） |
| `font-size` | `var(--fontSizeBase300)` | 14px |
| `font-weight` | `var(--fontWeightRegular)` | 400 |
| `line-height` | `var(--lineHeightBase300)` | 20px |

### 入れ子

テーマを切り替える要素ごとに、変数だけでなく `color` と `background-color` と書体も当て直す。CSS 変数だけを差し替えても、継承された `color` の計算値は親の値のままだからである。`fluent2-base.css` は `[data-theme]` を付けた要素ごとにこれを当てるので、`data-theme` を付ければよい。

`.fui-FluentProvider` の class は、既定のスタイル（文字色、背景色、書体、揃え）だけを当て、トークンは宣言し直さない。v9 の入れ子のプロバイダーと同じく、親のテーマを継ぐ。テーマを変えたい要素には `data-theme` を明示する。

部分的なテーマ（一部のトークンだけを変える）は、`data-theme` を付けた要素に、後に読む CSS で個別のトークンを上書きして作る。

```html demo
<div data-theme="dark" style="padding: 16px;">
  <div class="f2-stack" data-gap="m">
    <span>dark の領域</span>
    <div data-theme="light" style="padding: 16px;">data-theme="light" の入れ子（light に切り替わる）</div>
    <div style="padding: 16px;">何も付けない子（dark を継ぐ）</div>
    <div class="fui-FluentProvider" style="padding: 16px;">.fui-FluentProvider だけの子（dark を継ぐ）</div>
  </div>
</div>
```

### ポップアップ

- `popover` 属性の要素と `<dialog>` は、最上位の層（top layer）に描かれても DOM の位置が変わらない。CSS 変数と文字の色を、置いた場所の祖先から継ぐ。
- JS でポップアップを `<body>` の直下へ移すときは、移した先の要素に、元の場所と同じ `data-theme` と `dir` を付ける。v9 のポータルが class と `dir` を写すのと同じである。

## テーマの切り替え

| `data-theme` | テーマ | 元のテーマ |
|---|---|---|
| なし（`:root`） | light | `webLightTheme` |
| `light` | light | `webLightTheme` |
| `dark` | dark | `webDarkTheme` |
| `auto` | OS の設定が dark なら dark、それ以外は light | 独自の追加（v9 は OS の設定に自動では従わない） |
| `high-contrast` | 固定の色のハイコントラスト | `createHighContrastTheme` の値（Teams のハイコントラストと同じ色） |

- 属性のない `<html>` は light である。OS の設定に従わせるには `data-theme="auto"` を明示する。
- テーマは `color-scheme` を宣言しない。v9 の FluentProvider も書かないので、ネイティブの部品の UA の色（文字色など）が v9 と同じになる。代わりに、dark でもスクロールバーやネイティブの `<select>` の一覧は light の色で描かれる。ブラウザーが描く部分をテーマに合わせたいときは、使う側で `[data-theme="dark"] { color-scheme: dark; }` を足す（v9 からの逸脱）。
- `high-contrast` は、固定の 16 進数でシステムカラーを近似したテーマで、ブランドの差し替えが効かない。Windows のハイコントラスト（強制カラー）とは別のものである。Web Components v3 の文書は、ハイコントラストのテーマを使わず、どのテーマでも強制カラーに自動で対応する立場を取る（`packages/web-components/src/_docs/developer/theming.mdx:56-61`）。この設計書でも、利用者のハイコントラストの設定には強制カラーで応え、`high-contrast` は見た目を確かめるためか、Teams に合わせるときだけに使う。

JS で切り替えるときは、属性を書き換えるだけでよい。

```html
<select id="theme">
  <option value="light">ライト</option>
  <option value="dark">ダーク</option>
  <option value="auto">OS に合わせる</option>
</select>
<script>
  // テーマの選択を <html> の data-theme に反映する
  document.getElementById('theme').addEventListener('change', (ev) => {
    document.documentElement.setAttribute('data-theme', ev.target.value);
  });
</script>
```

### 実装の例

```html demo
<div class="f2-grid">
  <div data-theme="light" data-span-large="6" data-span-xlarge="3" style="padding: 16px;">
    <div class="f2-stack" data-gap="s">
      <strong>light</strong>
      <span>本文の色と背景の色</span>
      <div class="f2-surface" data-background="brand">ブランドの背景</div>
      <button class="fui-Button" data-appearance="primary" type="button">保存</button>
    </div>
  </div>
  <div data-theme="dark" data-span-large="6" data-span-xlarge="3" style="padding: 16px;">
    <div class="f2-stack" data-gap="s">
      <strong>dark</strong>
      <span>本文の色と背景の色</span>
      <div class="f2-surface" data-background="brand">ブランドの背景</div>
      <button class="fui-Button" data-appearance="primary" type="button">保存</button>
    </div>
  </div>
  <div data-theme="auto" data-span-large="6" data-span-xlarge="3" style="padding: 16px;">
    <div class="f2-stack" data-gap="s">
      <strong>auto</strong>
      <span>OS の設定に従う</span>
      <div class="f2-surface" data-background="brand">ブランドの背景</div>
      <button class="fui-Button" data-appearance="primary" type="button">保存</button>
    </div>
  </div>
  <div data-theme="high-contrast" data-span-large="6" data-span-xlarge="3" style="padding: 16px;">
    <div class="f2-stack" data-gap="s">
      <strong>high-contrast</strong>
      <span>固定の色の近似</span>
      <div class="f2-surface" data-background="brand">ブランドの背景</div>
      <button class="fui-Button" data-appearance="primary" type="button">保存</button>
    </div>
  </div>
</div>
```

ボタンの見た目は「ボタン、リンク、ツールバー、ラベル、フィールド」の章の CSS が担う。

## ブランドの差し替え

- ブランドを参照する色のトークン（`colorBrandBackground` など）は、`fluent2-tokens.css` の中で `var(--fui-brand-80)` のように 16 段階の変数を参照する。この 16 個は Fluent の公開トークンではなく、この設計書の補助の変数である。
- `--fui-brand-*` を上書きするのは、トークンを宣言し直す要素、つまり `:root` と `data-theme` を付けた要素に限る。トークンは宣言した要素で値が決まり、子はその結果を継ぐだけなので、`data-theme` のない要素（`.fui-FluentProvider` だけの要素を含む）で `--fui-brand-*` を変えても効かない。区画のブランドを替えるときは、その要素に `data-theme` も付ける。
- ページ全体を替えるなら `:root` で上書きする。`fluent2.css` の後に読む CSS に書く。
- 段階の値は、v9 の `BrandVariants` と同じ 16 色（10 が最も暗く、160 が最も明るい）である。light では主に 80 を、dark では主に 100 を使う。1 色から 16 段を作るには `scripts/brand_ramp.py` を使う（「色」の章の「16 段の作り方」）。
- `high-contrast` のテーマはブランドを参照しないので、差し替えは効かない。

例として、v9 の `brandTeams`（`packages/tokens/src/global/brandColors.ts:22-39`）の 16 色に差し替える。

```html demo
<style>
  .ph-brand-teams {
    --fui-brand-10: #2b2b40;
    --fui-brand-20: #2f2f4a;
    --fui-brand-30: #333357;
    --fui-brand-40: #383966;
    --fui-brand-50: #3d3e78;
    --fui-brand-60: #444791;
    --fui-brand-70: #4f52b2;
    --fui-brand-80: #5b5fc7;
    --fui-brand-90: #7579eb;
    --fui-brand-100: #7f85f5;
    --fui-brand-110: #9299f7;
    --fui-brand-120: #aab1fa;
    --fui-brand-130: #b6bcfa;
    --fui-brand-140: #c5cbfa;
    --fui-brand-150: #dce0fa;
    --fui-brand-160: #e8ebfa;
  }
</style>
<div class="f2-grid">
  <div class="ph-brand-teams" data-theme="light" data-span-large="6" style="padding: 16px;">
    <div class="f2-stack" data-gap="s">
      <div class="f2-surface" data-background="brand">brandTeams（light）</div>
      <button class="fui-Button" data-appearance="primary" type="button">保存</button>
    </div>
  </div>
  <div class="ph-brand-teams" data-theme="dark" data-span-large="6" style="padding: 16px;">
    <div class="f2-stack" data-gap="s">
      <div class="f2-surface" data-background="brand">brandTeams（dark）</div>
      <button class="fui-Button" data-appearance="primary" type="button">保存</button>
    </div>
  </div>
</div>
```

## フォーカスの表示

### v9 の仕組みと近似

- v9 は、keyborg の判定でキーボード操作中のときだけ、フォーカスを受けた要素に `data-fui-focus-visible` を付ける（`packages/react-components/react-tabster/src/focus/constants.ts:7`、`packages/react-components/react-tabster/src/focus/focusVisiblePolyfill.ts:30-98`）。
- Checkbox、Radio、Switch、Slider などは、子孫がキーボードでフォーカスを受けたときに、根の要素に `data-fui-focus-within` を付ける（`packages/react-components/react-tabster/src/focus/constants.ts:12`）。
- この設計書は、`[data-fui-focus-visible]` を `:focus-visible` で、`[data-fui-focus-within]:focus-within` を `:has(:focus-visible)` で近似する。ブラウザーの `:focus-visible` の判定は keyborg と細部が違う。たとえば、テキストの入力欄はマウスで押しても `:focus-visible` に当たる。近似であることを前提にする。

### 共通の輪（createFocusOutlineStyle）

`createFocusOutlineStyle()` の既定（`packages/react-components/react-tabster/src/focus/createFocusOutlineStyle.ts:55-112`）を React を使わない CSS にしたものである。

| 項目 | 値 |
|---|---|
| 要素 | `position: relative`。`:focus` と `:focus-visible` で `outline-style: none` |
| 要素の枠 | フォーカス中は `border-color: transparent` |
| 輪 | `::after` に `content: ""`、`position: absolute`、`pointer-events: none`、`z-index: 1` |
| 輪の線 | `border: 2px solid var(--colorStrokeFocus2)`（2px は v9 の直書き。`strokeWidthThick` を使うと不具合があるという FIXME がある） |
| 輪の角丸 | `var(--borderRadiusMedium)` |
| 輪の位置 | `inset: -2px`。offset があるときは `calc(0px - 2px - <offset>)` |
| ハイコントラスト | `@media (forced-colors: active)` で輪の `border-color: Highlight` |

- `::after` の位置は、要素のパディングの縁から測る。要素の枠は透明になるだけで幅は残るので、1px の枠の要素では、輪は枠の 1px とその外側の 1px にまたがる。ブラウザーの `outline` では同じ位置にならない。
- `<input>` などの置換要素は `::after` を持てない。包む要素に、`focus-within` の版の輪を描く。
- Button、Link、Tab など、部品ごとに違う表示を持つものがある。たとえば Button は、枠の色を `colorStrokeFocus2` にし、`0 0 0 1px` の inset の `box-shadow` を重ねる（`packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:105-122`）。Link は二重の下線にする（`packages/react-components/react-link/library/src/components/Link/useLinkStyles.styles.ts:14-19`）。部品の CSS は各章の値に従い、共通の輪をすべてに使わない。

layout.css の `f2-focus-outline` と `f2-focus-outline-within`（独自）は、共通の輪を独自の部品や既存の要素に付けるための class である。

```html demo
<div class="f2-stack" data-direction="horizontal" data-gap="l">
  <button class="f2-surface f2-focus-outline" data-stroke="thin" type="button">Tab キーでフォーカス（f2-focus-outline）</button>
  <label class="f2-surface f2-focus-outline-within" data-stroke="thin">
    <input type="checkbox"> 包む要素に輪を描く（f2-focus-outline-within）
  </label>
</div>
```

## ハイコントラスト（forced-colors）

### 方針

- 専用のハイコントラストのテーマに頼らず、どのテーマでも `@media (forced-colors: active)` の中で、システムカラーのキーワードを直接書いて対応する。v9 の 50 のスタイルのファイル、Web Components v3 の 20 のファイルにこの media query がある。
- 既定の色の置き換えはブラウザーに任せる。状態の区別（ホバー、選択、主のボタン）が消えてしまう所だけ、システムカラーで書き直す。必要なら `forced-color-adjust: none` で強制を止める（例: v9 の Button のホバー、`packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:83-101`）。
- 部品の CSS は、v9 の規則をシステムカラーのキーワードのまま写す。`forced-color-adjust` も v9 のとおりに書く。
- 影は強制カラーで描かれない。浮く面には `colorTransparentStroke` の透明の枠を残し、縁として見えるようにする。

### システムカラーの使い分け

| システムカラー | 使う場面 | v9 の例 |
|---|---|---|
| `Canvas` | 背景 | フォーカスしていない輪を背景の色で隠す（Web Components v3 の Checkbox） |
| `CanvasText` | 本文、通常の枠線 | — |
| `Highlight` | フォーカスの輪、ホバーの枠と文字、主のボタンの背景、選択の印 | `packages/react-components/react-tabster/src/focus/createFocusOutlineStyle.ts:60-64`、`packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:168-171` |
| `HighlightText` | `Highlight` の上の文字 | 主のボタン。Button のホバーでは背景にして反転させる |
| `GrayText` | 無効の文字と枠 | `packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:373-402` |
| `ButtonText` | ボタンの文字、フォーカス中の Button の枠 | `packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:84-86` |
| `ButtonFace` | ボタンの背景、無効のボタンの背景 | — |
| `ButtonBorder` | Radio、ToggleButton の枠 | — |
| `LinkText` | リンク | v9 は明示しない（ブラウザーが `<a>` に当てる） |

v9 のスタイルで明示した回数は、`Highlight` 100、`GrayText` 66、`HighlightText` 46、`Canvas` 13、`CanvasText` 12、`ButtonText` 6、`ButtonFace` 6、`ButtonBorder` 2、`LinkText` 0 である。

確かめるには、Windows の「コントラスト テーマ」を有効にするか、Chromium の開発者ツールの「Rendering」で `forced-colors: active` をエミュレートする。

## RTL

- `dir` は `<html>` に付ける。一部だけ向きが違うときは、その区画の要素に付ける。
- 余白、位置、枠、角丸は論理プロパティで書く（`padding-inline-start`、`margin-inline-end`、`inset-inline-start`、`border-start-start-radius`、`text-align: start`）。v9 では Griffel が RTL のときに左右を反転するが、React を使わない CSS では論理プロパティが同じ結果になる（`packages/react-components/react-provider/library/src/components/FluentProvider/renderFluentProvider.tsx:42`）。
- v9 が `/* @noflip */` を付けているものは、物理プロパティのまま書く。
- 論理プロパティで書けない変形（矢印のアイコンの反転、スライダーの進む向き、山形のアイコンの回転）だけ、`:dir(rtl)` で書く。Web Components v3 も同じ方法を使う（`packages/web-components/src/slider/slider.styles.ts:67`）。
- 向きを持つアイコンは、`dir` だけでは反転しない（「アイコン」の章の RTL の節）。

```html demo
<div class="f2-stack" data-gap="m">
  <div class="f2-surface" data-stroke="thin" dir="ltr">
    <div class="f2-stack" data-direction="horizontal" data-gap="s">
      <svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true" focusable="false"><path d="M15.5 4A2.5 2.5 0 0 1 18 6.5v8a2.5 2.5 0 0 1-2.5 2.5h-11A2.5 2.5 0 0 1 2 14.5v-8A2.5 2.5 0 0 1 4.5 4zM17 7.96l-6.75 3.97a.5.5 0 0 1-.42.04l-.08-.04L3 7.96v6.54c0 .83.67 1.5 1.5 1.5h11c.83 0 1.5-.67 1.5-1.5zM15.5 5h-11C3.67 5 3 5.67 3 6.5v.3l7 4.12 7-4.12v-.3c0-.83-.67-1.5-1.5-1.5"/></svg>
      <span>dir="ltr": 始まりは左</span>
    </div>
  </div>
  <div class="f2-surface" data-stroke="thin" dir="rtl">
    <div class="f2-stack" data-direction="horizontal" data-gap="s">
      <svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true" focusable="false"><path d="M15.5 4A2.5 2.5 0 0 1 18 6.5v8a2.5 2.5 0 0 1-2.5 2.5h-11A2.5 2.5 0 0 1 2 14.5v-8A2.5 2.5 0 0 1 4.5 4zM17 7.96l-6.75 3.97a.5.5 0 0 1-.42.04l-.08-.04L3 7.96v6.54c0 .83.67 1.5 1.5 1.5h11c.83 0 1.5-.67 1.5-1.5zM15.5 5h-11C3.67 5 3 5.67 3 6.5v.3l7 4.12 7-4.12v-.3c0-.83-.67-1.5-1.5-1.5"/></svg>
      <span>dir="rtl": 始まりは右</span>
    </div>
  </div>
</div>
```

## 既存の HTML ページに当てる手順

1. **CSS を読み込む。** `<head>` に `fluent2.css` を 1 つ読む（読み込み方の節）。既存の CSS は、その後に読む。既存の CSS がトークンの変数名と同じ名前（`--colorNeutralBackground1` など）を使っていないか確かめる。
2. **`<html>` に属性を付ける。** `lang`、`dir`、`data-theme` を付ける。`<body>` に既存の背景の色や書体の指定があれば外す。
3. **既存のリセットの CSS を見直す。** `button`、`input` などの見た目を消すリセットは、部品の CSS と詳細度で競う。部品の CSS は `.fui-Button` のように class 1 つの詳細度（0,1,0）なので、`button.reset` のような強い規則があれば負ける。
4. **要素を置き換える。** 下の表に従って、要素に class とスロットの要素を足す。ネイティブの要素はそのまま使い、置き換えるのは class と包む要素だけにする。
5. **バリエーションと状態を属性で表す。** `data-appearance`、`data-size` などの data 属性と、`disabled`、`aria-pressed` などのネイティブの属性と ARIA を使う。
6. **アイコンをインライン SVG にする。** 画像や Web フォントのアイコンを、Fluent System Icons の SVG に置き換える（「アイコン」の章）。
7. **確かめる。** light と dark、キーボードでの操作、強制カラー、`dir="rtl"`、縮小モーションの設定で表示を確かめる。

### 置き換えの対応表

class 名は v9 の静的な class 名である。根の要素が `fui-<Component>`、スロットが `fui-<Component>__<slot>` になる。詳しいマークアップは各部品の章に従う。

| 既存の要素 | 置き換え（根の class と主なスロット） | 章 |
|---|---|---|
| `<button>` | `<button class="fui-Button">`。アイコンは `<span class="fui-Button__icon">` | ボタン、リンク、ツールバー、ラベル、フィールド |
| `<a>`（文中のリンク） | `<a class="fui-Link">` | 同上 |
| `<label>` | `<label class="fui-Label">`。必須の印は `fui-Label__required` | 同上 |
| フォームの 1 行（ラベル、入力、説明、検証） | `<div class="fui-Field">` と `fui-Field__label`、`fui-Field__hint`、`fui-Field__validationMessage` | 同上 |
| `<input type="text">` など | `<span class="fui-Input"><input class="fui-Input__input"></span>`。前後の飾りは `fui-Input__contentBefore`、`fui-Input__contentAfter` | テキストの入力と選択の一覧 |
| `<textarea>` | `<span class="fui-Textarea"><textarea class="fui-Textarea__textarea"></textarea></span>` | 同上 |
| `<select>` | `<span class="fui-Select">` と `fui-Select__select`、`fui-Select__icon` | 同上 |
| `<input type="checkbox">` | `fui-Checkbox` と `fui-Checkbox__input`、`fui-Checkbox__indicator`、`fui-Checkbox__label` | 選択の部品、タグ、バッジ |
| `<input type="radio">` | `fui-Radio` と `fui-Radio__input`、`fui-Radio__indicator`、`fui-Radio__label` | 同上 |
| `<input type="checkbox" role="switch">` | `fui-Switch` と `fui-Switch__input`、`fui-Switch__indicator`、`fui-Switch__label` | 同上 |
| `<input type="range">` | `fui-Slider` と `fui-Slider__input`、`fui-Slider__rail`、`fui-Slider__thumb` | 同上 |
| `<hr>` | `fui-Divider`（v9 は `role="separator"` の `<div>`） | 表示の部品 |
| `<progress>` | `fui-ProgressBar` と `fui-ProgressBar__bar`（v9 は `role="progressbar"` の `<div>`） | 同上 |
| `<table>` | `fui-Table` と、行、セルの class | ナビゲーションと表 |
| `<dialog>` | `fui-DialogSurface`（背景幕は `::backdrop`） | オーバーレイと通知 |
| `<h1>` から `<p>` | 書体のプリセット（`fui-Title1`、`fui-Body1` など） | タイポグラフィ |

置き換えた後の例を示す。ラベル、入力欄、説明、ボタンの並びである。

```html
<!-- 置き換える前 -->
<p>
  <label for="ph-name-before">表示名</label>
  <input id="ph-name-before" type="text">
  <small>ほかの人に表示されます</small>
</p>
<button type="submit">保存</button>
```

```html demo
<div class="f2-stack" data-gap="l">
  <div class="fui-Field">
    <label class="fui-Label fui-Field__label" for="ph-name">表示名</label>
    <span class="fui-Input"><input class="fui-Input__input" id="ph-name" type="text" aria-describedby="ph-name-hint"></span>
    <div class="fui-Field__hint" id="ph-name-hint">ほかの人に表示されます</div>
  </div>
  <div>
    <button class="fui-Button" data-appearance="primary" type="submit">保存</button>
  </div>
</div>
```

見た目は各部品の章の CSS が担う。

## 厳しい CSP の下で使う

インラインの style とインラインの script を禁じる CSP（例: `default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:`）のページでも、このスキルは使える。info-hive-wiki の browse と同じ CSP で、`file://` と `http://127.0.0.1` の両方を確かめた（開発用のリポジトリ（非公開）の `docs/verification/browse-csp.md`）。

- `fluent2.css` と `fluent2.js` は、`<link rel="stylesheet" href="…">` と `<script src="…">` でファイルとして読み込む。CSS には `url()`、`@import`、`@font-face` がなく、JS は `fetch`、モジュール、`eval`、`innerHTML` を使わないので、CSP の違反は出ない。外部への要求も 0 件である。
- JS が値を書くときは CSSOM（`element.style.setProperty`）を使う。CSSOM の書き込みは `style-src 'self'` の下でも効く。
- マークアップの style 属性と `<style>` 要素は、CSP の下では無視される。部品の働きに要る値は style 属性で渡さない。
  - ProgressBar の値: 根に `data-percent`（0〜100 の整数）を書くか、`data-fui-enhance` の中に置いて `display.js` に計算させる。
  - Popover と Menu の位置: `popovertarget` か `commandfor` で開けば、トリガーが暗黙のアンカーになる。Tooltip は `overlays.js` が CSSOM で結ぶ。
- 見本の中の配置のための style 属性（flex、gap、max-width）は、CSP の下では無視されて並びが変わる。ページの配置は、自分の CSS ファイルか `layout.css` の `f2-` の class で書く。
- 設計書の HTML（公開のリポジトリ to884/fluent2-html-replica の `docs/fluent2-web-spec.html`）は CSS と JS を埋め込んでいるので、この CSP の下では表示できない。

## ライセンスと商標の表示

| 対象 | 条件 | 出典 |
|---|---|---|
| microsoft/fluentui（React v9、Web Components、tokens） | MIT License。`Copyright (c) Microsoft Corporation.`。LICENSE の末尾に、Fluent UI React が参照する書体とアイコンの利用は別の条件（aka.ms/fluentui-assets-license）に従うという注記がある | microsoft/fluentui の `LICENSE`（3 行目と 22 行目）、各 `package.json` の `license` |
| Fluent System Icons | MIT License。`Copyright (c) 2020 Microsoft Corporation` | microsoft/fluentui-system-icons の `LICENSE` |
| Segoe UI | Windows などの Microsoft の製品に含まれる書体である。製品から取り出した書体を Web サーバーに置くことや、WOFF などに変換することは、その製品のライセンスでは許されない。Web フォントとして使いたいときは、書体の提供元から別途ライセンスを得る必要がある。フォントスタックに名前を書くのは自由である | Microsoft Learn の Segoe UI と Font redistribution FAQ |
| Microsoft の商標 | 製品を正しく説明するための参照的な使用は認められる。提携、推薦、承認をほのめかしてはならない。自分の製品名やドメイン名に入れてはならない | Microsoft の Trademark and Brand Guidelines |

この設計書の CSS や、それを使ったページを配布するときは、次を守る。

1. CSS の先頭のコメントか、同梱の LICENSE か NOTICE に、MIT の著作権表示と許諾の文を入れる。`assets/fluent2.css` と `assets/fluent2.js` は先頭のコメントに、設計書の HTML は末尾に、Fluent UI と Fluent UI System Icons の著作権表示と許諾の文を入れてある。1 ファイルだけを取り出して配布しても、表示が付いて回る。`fluent2.css` の一部だけを切り出して配るときも、`THIRD-PARTY-NOTICES.txt` を同梱する。
2. Microsoft が作ったものではなく、Microsoft の提携、推薦、承認を受けたものでもないと明記する。
3. 商標の帰属を書く。例: 「Fluent、Microsoft、Segoe は Microsoft Corporation の商標である。」
4. Segoe UI を同梱せず、変換しない。フォントスタックの先頭に名前を書くだけにし、Segoe UI のない環境では代わりの書体で表示されると書く。
5. 製品名やパッケージ名に「Fluent」や「Microsoft」を入れない。説明では「Fluent 2 のデザインに合わせた」のような参照的な表現にとどめる。
6. アイコンは Fluent System Icons だけを使い、その LICENSE を同梱する。Office のアイコンと Fabric のアイコン（MDL2）は使わない。

## 互換性の注意

- **CSS 変数の名前に保証はない。** `--colorNeutralBackground1` のような名前は、v9 の FluentProvider と Web Components v3 の `setTheme` が出す名前と同じだが、Fluent の内部の実装である。Web Components v3 の文書は、テーマの CSS 変数を直接使わないよう警告し、将来ハッシュ化や直接の値への置き換えがありうるとしている（`packages/web-components/src/_docs/developer/theming.mdx:43-45`）。
- **版を固定する。** この設計書は `@fluentui/react-components` 9.75.2、`@fluentui/tokens` 1.0.0-alpha.24、`@fluentui/web-components` 3.2.1（microsoft/fluentui commit `f9720c35ba89`、2026-11-12）に従う。Fluent を更新するときは、トークンを生成し直し、部品の値を確かめ直す。
- **独自の部分を区別する。** `--fui-brand-*`、`data-theme`、data 属性によるバリエーション（`data-appearance` など）、`f2-` の class は、この設計書の独自の仕組みで、v9 にはない。v9 は props で表し、class 名はハッシュ化された Griffel の class を併用する。
- **DOM は v9 と同じではない。** 静的な class 名（`fui-Button` など）は v9 に合わせたが、要素の構成、属性、詳細度は React を使わない CSS のために変えている。v9 の DOM を前提にしたテストやスクリプトがそのまま動くとは限らない。
- **本物の v9 と同じページで使わない。** 同じ `fui-` の class 名を使うので、React の v9 と同じページに読み込むと規則が衝突する。

## 検証の方法

本物の Fluent 2 を同じブラウザーで表示し、計算済みのスタイルを比べる。次の例は手順の案で、この設計書では実行していない。

- **Web Components v3**: jsDelivr の `https://cdn.jsdelivr.net/npm/@fluentui/web-components@3.2.1/dist/web-components.min.js` を `type="module"` で読み、`https://cdn.jsdelivr.net/npm/@fluentui/tokens@1.0.0-alpha.24/+esm` から `webLightTheme` を import して、`globalThis.Fluent.setTheme(webLightTheme)` を呼ぶ。
- **React v9**: esm.sh から `https://esm.sh/@fluentui/react-components@9.75.2?deps=react@18.3.1,react-dom@18.3.1` を import する。すべての import に同じ `deps` を付けないと、React が 2 つ読み込まれてフックが壊れる。表示すると、`<head>` に `<style id="fui-FluentProvider1">` が入り、根の `<div>` に `fui-FluentProvider fui-FluentProvider1` の class と `dir` が付く。

## v9 との差と未確認の点

- **入れ子のテーマ**: v9 の入れ子のプロバイダーは親のテーマを継いで部分的に上書きできる。この設計書の `.fui-FluentProvider` は親のテーマを継ぎ、`data-theme` はテーマを丸ごと選ぶ。部分的なテーマは個別のトークンの上書きで作る。
- **`data-theme="auto"`**: v9 は OS の配色に自動では従わない（`prefers-color-scheme` は v9 のスタイルに出てこない）。`auto` は独自の追加である。
- **フォーカスの判定**: `:focus-visible` と `:has(:focus-visible)` は、keyborg の判定の近似である。テキストの入力欄やプログラムによるフォーカスで、v9 と輪の出方が違うことがある。
- **ポータル**: v9 は body の直下に出すポップアップに、プロバイダーの class と `dir` を写す。この設計書は `popover` と `<dialog>` で DOM の位置を保つことで代える。JS で要素を移すときの写しは利用者に任せる。
- **Web Components v3 の `setTheme`**: 文書は body に設定すると書くが、コードは `html` の規則に書く（`packages/web-components/src/theme/set-theme.ts:116-120`）。継承の結果は同じである。
- **ライセンスの PDF**: aka.ms/fluentui-assets-license の転送先の PDF は、一部の段落を取り出せず、許諾の範囲を定める文に欠けがある。Fluent System Icons がこの対象に含まれないことは読み取れた。
- **「Fluent」の商標**: Microsoft の商標の一覧に「Fluent」があるかは確かめられなかった。帰属の表示には含めておく。
