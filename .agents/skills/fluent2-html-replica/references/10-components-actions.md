# ボタン、リンク、ツールバー、ラベル、フィールド

この章は、操作を起こす部品（Button、CompoundButton、MenuButton、SplitButton、ToggleButton、Toolbar）、移動のための Link、名前を付ける部品（Label、Field、InfoLabel）を、React を使わない HTML と CSS で v9 と同じ見た目にする方法を定める。

結論を先に書く。

- CSS は `assets/fluent2.css` の `actions` の部分、振る舞いは `assets/fluent2.js` にある（開発用のリポジトリ（非公開）の原本は `src/components/actions.css` と `actions.js`）。見た目は CSS だけで決まる。JS は、`data-fui-enhance` を付けた要素の中で、トグル、Toolbar の矢印キー、disabledFocusable の操作の抑止、popover の開閉に合わせた `aria-expanded` を受け持つ。
- class 名は v9 の静的な class 名（`fui-Button`、`fui-Button__icon` など）と同じにする。派生のボタンには、v9 と同じく 2 つの class を付ける（`class="fui-ToggleButton fui-Button"`）。
- バリエーションは data 属性（`data-appearance`、`data-size`、`data-shape`、`data-icon-position`、`data-icon-only` など）、状態はネイティブの擬似クラスと ARIA（`:disabled`、`aria-disabled`、`aria-pressed`、`aria-expanded`）で表す。属性を書かなければ v9 の既定値になる。
- 規則は Griffel と同じ詳細度にそろえ、v9 の `mergeClasses` の順に並べた。`@media` と `@supports` の規則は、Griffel が後のバケットに入れるので、ファイルの末尾にまとめた。
- フォーカスの表示は、v9 の `[data-fui-focus-visible]`（react-tabster のポリフィルが付ける属性）を `:focus-visible` で近似する。

この章の値の出典は、すべて microsoft/fluentui（commit `f9720c35ba893c9630f4c0389d07dc6d6fd6068d`）のリポジトリからの相対パスで書く。寸法と色の表の「行」は、各節の冒頭に挙げたスタイルのファイルの行番号である。

アイコンは、この章のすべての部品で次のように書く。

- v9 のボタンは、大きさのない `@fluentui/react-icons`（`1em` で `font-size` に従う）を前提に、スロットの `font-size`、`width`、`height` でアイコンの大きさを決める。`@fluentui/svg-icons` の SVG は固定の大きさなので、`actions.css` は `.fui-Button__icon > svg` と `.fui-MenuButton__menuIcon > svg` を `1em` にする（独自の規則）。SVG の `width` と `height` の属性は 20 のままでよい。
- 塗りに切り替わるアイコン（`bundleIcon`）は、Regular に `fui-Icon-regular`、Filled に `fui-Icon-filled` を付けて 2 つ並べる。どちらを見せるかは各コンポーネントの CSS が決める。
- 例の SVG は `@fluentui/svg-icons` の `calendar_month_20_*`、`chevron_down_20_regular`、`text_bold_20_*`、`text_italic_20_*`、`info_16_*`、`diamond_dismiss_12_filled`、`warning_12_filled`、`checkmark_circle_12_filled` を unpkg.com から取った（MIT License）。

## Button

### 概要と使い分け（Do / Don't）

ボタンは、送信、変更の確定、次の段階への移動など、1 つの操作を起こす。移動（ナビゲーション）にはリンクを使う。以下は fluent2.microsoft.design の Button の Usage の要約である。

- 種類: 1 つの操作は Button、主な操作と関連する操作のメニューを組にするなら SplitButton、メニューを開くだけなら MenuButton、主題と説明の 2 段なら CompoundButton、オンとオフの 2 状態なら ToggleButton を使う。
- primary は、画面で最も重要な操作の 1 つだけに使う。同じ重みの操作が 3 つ以上あれば、すべて中立（secondary）にする。小さな操作が多い場所では outline、subtle、transparent を使う。primary は先頭（上か左。RTL では右）に置く。
- 文字は背景に対して 4.5:1、アイコンは 3:1 のコントラストを、どの状態でも保つ（disabled は対象外）。この比はサイトの指針で、ソースの値ではない。
- disabled のボタンには、使えない理由をツールチップで示す。
- 文言は能動的で短い動詞にし、文頭だけを大文字にし（英語の場合）、末尾に句読点を付けない。

| Do | Don't |
|---|---|
| primary を 1 つに絞り、目立たせる | 補助の操作を primary と同じ重みにする |
| 補助の操作が多ければ outline、subtle、transparent を使う | エラーを「OK」だけで閉じさせる |
| 使えない理由をツールチップで示す | 「X」と Close ボタンを並べる。Close と Cancel を混同する |

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

スタイルの出典は `packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts` である。

| スロット | 要素 | class |
|---|---|---|
| root | `<button type="button">`（`as="a"` なら `<a>`） | `fui-Button` |
| icon（任意） | `<span>` | `fui-Button__icon` |

- 子の順は、`iconPosition` が `after` でなければ icon → 文字、`after` なら文字 → icon である（`packages/react-components/react-button/library/src/components/Button/renderButton.tsx:17-21`）。React を使わない HTML でも、この順に書く。
- アイコンだけのボタン（icon があり、文字がない）は v9 が `iconOnly` と判定する（`packages/react-components/react-button/library/src/components/Button/useButton.ts:48`）。CSS は文字のノードを見分けられないので、`data-icon-only` を書く。名前は `aria-label` で付ける。
- `disabled` は `<button>` の `disabled` 属性で表す。`disabledFocusable`（フォーカスを残す無効）は `aria-disabled="true"` で表す（`packages/react-components/react-aria/library/src/button/useARIAButtonProps.ts:110-121`）。
- `<a>` で描くとき、v9 は `href` がなければ `role="button"` と `tabindex="0"` を付け、disabled なら `href` を外して `role="link"` と `aria-disabled="true"` を付ける（同 125-149）。
- キーボード: `<button>` はネイティブのまま（Enter と Space で押す）。`role="button"` の `<a>` や `<span>` は、Enter を keydown で、Space を keyup で押す（同 81-85、103-106）。disabled のときは両方を止める（同 70-74、97-101）。`actions.js` は、`data-fui-enhance` の中で、この処理と `aria-disabled="true"` の操作の抑止を行う。

### バリエーション

| 属性 | 値（既定は太字） | v9 の props |
|---|---|---|
| `data-appearance` | **`secondary`**、`primary`、`outline`、`subtle`、`transparent` | `appearance` |
| `data-size` | `small`、**`medium`**、`large` | `size` |
| `data-shape` | **`rounded`**、`circular`、`square` | `shape` |
| `data-icon-position` | **`before`**、`after` | `iconPosition` |
| `data-icon-only` | 属性の有無 | `iconOnly`（v9 は自動で判定） |

### 寸法（size ごとの表）

v9 は `height` を書かない。高さは padding、line-height、上下の枠線 1px の合計で決まる。「高さ」の行は筆者の計算（推論）である。

| 項目 | small | medium（既定） | large | 行 |
|---|---|---|---|---|
| padding | `3px` `--spacingHorizontalS`（8px） | `5px` `--spacingHorizontalM`（12px） | `8px` `--spacingHorizontalL`（16px） | 17-21、63、293、309 |
| icon があるときの上下の padding | `1px` | `5px`（変わらない） | `7px` | 300-303、316-319 |
| min-width | `64px` | `96px` | `96px` | 64、292、308 |
| 文字 | `--fontSizeBase200` / `--lineHeightBase200` / Regular | `--fontSizeBase300` / `--lineHeightBase300` / Semibold | `--fontSizeBase400` / `--lineHeightBase400` / Semibold | 67-69、296-298、312-314 |
| 角丸（rest） | `--borderRadiusMedium` | `--borderRadiusMedium` | `--borderRadiusMedium` | 65、294、310 |
| 角丸（フォーカス時） | `--borderRadiusSmall` | `--borderRadiusMedium` | `--borderRadiusLarge` | 107、495、499 |
| アイコンの大きさ | 20px | 20px | 24px | 131-133、527-529、537-539 |
| アイコンと文字の間 | `--spacingHorizontalXS`（4px） | `--spacingHorizontalSNudge`（6px） | `--spacingHorizontalSNudge` | 135、531、541 |
| iconOnly の padding と幅 | `1px`、24px | `5px`、32px | `7px`、40px | 502-522 |
| 高さ（推論） | 3 + 16 + 3 + 2 = 24px | 5 + 20 + 5 + 2 = 32px | 8 + 22 + 8 + 2 = 40px | — |

- 共通: `display: inline-flex`、中央そろえ、`box-sizing: border-box`、`vertical-align: middle`、`overflow: hidden`、`border: var(--strokeWidthThin) solid var(--colorNeutralStroke1)`（29-45）。
- shape: `circular` は `--borderRadiusCircular`、`square` は `--borderRadiusNone`（284-288、466-470）。
- アイコンと文字の間は、CSS 変数 `--fui-Button__icon--spacing` に入れ、`before` は `margin-inline-end`、`after` は `margin-inline-start` に使う。文字があるときだけ付く（545-550、599）。

### 色と状態（トークン名の表）

pressed は `:hover:active` と `:active:focus-visible` である（55）。アイコンは、表にない限り文字色を継ぐ。

| appearance | 状態 | background | color | border-color | 行 |
|---|---|---|---|---|---|
| secondary | rest | `colorNeutralBackground1` | `colorNeutralForeground1` | `colorNeutralStroke1` | 40-42 |
| | hover | `colorNeutralBackground1Hover` | `colorNeutralForeground1Hover` | `colorNeutralStroke1Hover` | 47-53 |
| | pressed | `colorNeutralBackground1Pressed` | `colorNeutralForeground1Pressed` | `colorNeutralStroke1Pressed` | 55-61 |
| outline | rest / hover / pressed | `colorTransparentBackground` / `…Hover` / `…Pressed` | secondary と同じ | secondary と同じ | 140-150 |
| primary | rest / hover / pressed | `colorBrandBackground` / `…Hover` / `…Pressed` | `colorNeutralForegroundOnBrand` | `transparent` | 151-166 |
| subtle | rest | `colorSubtleBackground` | `colorNeutralForeground2` | `transparent` | 190-193 |
| | hover | `colorSubtleBackgroundHover` | `colorNeutralForeground2Hover`（アイコンは `colorNeutralForeground2BrandHover`、塗り） | `transparent` | 195-208 |
| | pressed | `colorSubtleBackgroundPressed` | `colorNeutralForeground2Pressed`（アイコンは `colorNeutralForeground2BrandPressed`、塗り） | `transparent` | 210-223 |
| transparent | rest | `colorTransparentBackground` | `colorNeutralForeground2` | `transparent` | 242-245 |
| | hover / pressed | `colorTransparentBackgroundHover` / `…Pressed` | `colorNeutralForeground2BrandHover` / `…BrandPressed`（アイコンは塗り） | `transparent` | 247-269 |
| すべて | disabled（rest、hover、pressed） | `colorNeutralBackgroundDisabled` | `colorNeutralForegroundDisabled`（アイコンも。線のアイコンに戻す） | `colorNeutralStrokeDisabled` | 322-369 |
| outline | disabled | `colorTransparentBackground` | 同上 | 同上 | 409-419 |
| primary | disabled | 同上 | 同上 | `transparent` | 420-430 |
| subtle、transparent | disabled | `colorTransparentBackground` | 同上 | `transparent` | 434-461 |

hover で `cursor: pointer`、disabled で `cursor: not-allowed` になる（52、329）。disabled の規則は `disabled` と `disabledFocusable` の両方に当たる（578-580）。

### フォーカス・動き・ハイコントラスト

- フォーカス（105-114）: `border-color: var(--colorStrokeFocus2)`、`border-width: 1px`、`outline: var(--strokeWidthThick) solid var(--colorTransparentStroke)`、`box-shadow: 0 0 0 var(--strokeWidthThin) var(--colorStrokeFocus2) inset`、`z-index: 1`。枠線 1px と内側の影 1px で、内側に 2px の濃い輪ができる。pressed の間は `outline-style: none`（60）。
- primary のフォーカス（473-481）: `box-shadow` に `var(--shadow2)`、濃い輪、その内側の `var(--colorNeutralForegroundOnBrand)` の 2px の inset を重ねる。フォーカス中に hover すると、白い線を外す。
- Firefox では inset の影の幅を `calc(var(--strokeWidthThin) + 0.25px)` にする（`@supports (-moz-appearance: button)`、23-27、116-123、483-491）。
- 動き: `transition-property: background, border, color`、`var(--durationFaster)`、`var(--curveEasyEase)`（73-75）。`@media screen and (prefers-reduced-motion: reduce)` で `transition-duration: 0.01ms`（77-79）。
- ハイコントラスト（83-101、168-185、225-240、271-280、372-405）: 根は `:focus` で `border-color: ButtonText`、hover と pressed で `HighlightText` の背景に `Highlight` の文字と枠（`forced-color-adjust: none`）。primary は rest で `Highlight` の背景に `HighlightText`。subtle と transparent は hover と pressed で文字を `Highlight`。disabled は `ButtonFace`、`GrayText`。

### 実装の例

```html demo
<div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center">
  <button type="button" class="fui-Button">既定</button>
  <button type="button" class="fui-Button" data-appearance="primary">保存</button>
  <button type="button" class="fui-Button" data-appearance="outline">アウトライン</button>
  <button type="button" class="fui-Button" data-appearance="subtle"><span class="fui-Button__icon" aria-hidden="true"><svg class="fui-Icon fui-Icon-regular" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M14.5 3A2.5 2.5 0 0 1 17 5.5v9a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 3 14.5v-9A2.5 2.5 0 0 1 5.5 3zm0 1h-9C4.67 4 4 4.67 4 5.5v9c0 .83.67 1.5 1.5 1.5h9c.83 0 1.5-.67 1.5-1.5v-9c0-.83-.67-1.5-1.5-1.5M7 11a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2M7 7a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2"/></svg><svg class="fui-Icon fui-Icon-filled" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M14.5 3A2.5 2.5 0 0 1 17 5.5v9a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 3 14.5v-9A2.5 2.5 0 0 1 5.5 3zM7 11a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2M7 7a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2"/></svg></span>予定</button>
  <button type="button" class="fui-Button" data-appearance="transparent"><span class="fui-Button__icon" aria-hidden="true"><svg class="fui-Icon fui-Icon-regular" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M14.5 3A2.5 2.5 0 0 1 17 5.5v9a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 3 14.5v-9A2.5 2.5 0 0 1 5.5 3zm0 1h-9C4.67 4 4 4.67 4 5.5v9c0 .83.67 1.5 1.5 1.5h9c.83 0 1.5-.67 1.5-1.5v-9c0-.83-.67-1.5-1.5-1.5M7 11a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2M7 7a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2"/></svg><svg class="fui-Icon fui-Icon-filled" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M14.5 3A2.5 2.5 0 0 1 17 5.5v9a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 3 14.5v-9A2.5 2.5 0 0 1 5.5 3zM7 11a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2M7 7a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2"/></svg></span>予定</button>
  <button type="button" class="fui-Button" data-icon-only aria-label="予定"><span class="fui-Button__icon" aria-hidden="true"><svg class="fui-Icon fui-Icon-regular" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M14.5 3A2.5 2.5 0 0 1 17 5.5v9a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 3 14.5v-9A2.5 2.5 0 0 1 5.5 3zm0 1h-9C4.67 4 4 4.67 4 5.5v9c0 .83.67 1.5 1.5 1.5h9c.83 0 1.5-.67 1.5-1.5v-9c0-.83-.67-1.5-1.5-1.5M7 11a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2M7 7a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2"/></svg><svg class="fui-Icon fui-Icon-filled" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M14.5 3A2.5 2.5 0 0 1 17 5.5v9a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 3 14.5v-9A2.5 2.5 0 0 1 5.5 3zM7 11a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2M7 7a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2"/></svg></span></button>
  <button type="button" class="fui-Button" disabled>無効</button>
  <button type="button" class="fui-Button" data-appearance="primary" aria-disabled="true">フォーカスできる無効</button>
</div>
```

```html demo
<div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center">
  <button type="button" class="fui-Button" data-size="small"><span class="fui-Button__icon" aria-hidden="true"><svg class="fui-Icon fui-Icon-regular" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M14.5 3A2.5 2.5 0 0 1 17 5.5v9a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 3 14.5v-9A2.5 2.5 0 0 1 5.5 3zm0 1h-9C4.67 4 4 4.67 4 5.5v9c0 .83.67 1.5 1.5 1.5h9c.83 0 1.5-.67 1.5-1.5v-9c0-.83-.67-1.5-1.5-1.5M7 11a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2M7 7a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2"/></svg><svg class="fui-Icon fui-Icon-filled" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M14.5 3A2.5 2.5 0 0 1 17 5.5v9a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 3 14.5v-9A2.5 2.5 0 0 1 5.5 3zM7 11a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2M7 7a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2"/></svg></span>small</button>
  <button type="button" class="fui-Button"><span class="fui-Button__icon" aria-hidden="true"><svg class="fui-Icon fui-Icon-regular" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M14.5 3A2.5 2.5 0 0 1 17 5.5v9a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 3 14.5v-9A2.5 2.5 0 0 1 5.5 3zm0 1h-9C4.67 4 4 4.67 4 5.5v9c0 .83.67 1.5 1.5 1.5h9c.83 0 1.5-.67 1.5-1.5v-9c0-.83-.67-1.5-1.5-1.5M7 11a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2M7 7a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2"/></svg><svg class="fui-Icon fui-Icon-filled" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M14.5 3A2.5 2.5 0 0 1 17 5.5v9a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 3 14.5v-9A2.5 2.5 0 0 1 5.5 3zM7 11a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2M7 7a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2"/></svg></span>medium</button>
  <button type="button" class="fui-Button" data-size="large"><span class="fui-Button__icon" aria-hidden="true"><svg class="fui-Icon fui-Icon-regular" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M14.5 3A2.5 2.5 0 0 1 17 5.5v9a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 3 14.5v-9A2.5 2.5 0 0 1 5.5 3zm0 1h-9C4.67 4 4 4.67 4 5.5v9c0 .83.67 1.5 1.5 1.5h9c.83 0 1.5-.67 1.5-1.5v-9c0-.83-.67-1.5-1.5-1.5M7 11a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2M7 7a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2"/></svg><svg class="fui-Icon fui-Icon-filled" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M14.5 3A2.5 2.5 0 0 1 17 5.5v9a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 3 14.5v-9A2.5 2.5 0 0 1 5.5 3zM7 11a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2M7 7a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2"/></svg></span>large</button>
  <button type="button" class="fui-Button" data-shape="circular">circular</button>
  <button type="button" class="fui-Button" data-shape="square">square</button>
  <button type="button" class="fui-Button" data-icon-position="after">次へ<span class="fui-Button__icon" aria-hidden="true"><svg class="fui-Icon fui-Icon-regular" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M14.5 3A2.5 2.5 0 0 1 17 5.5v9a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 3 14.5v-9A2.5 2.5 0 0 1 5.5 3zm0 1h-9C4.67 4 4 4.67 4 5.5v9c0 .83.67 1.5 1.5 1.5h9c.83 0 1.5-.67 1.5-1.5v-9c0-.83-.67-1.5-1.5-1.5M7 11a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2M7 7a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2"/></svg><svg class="fui-Icon fui-Icon-filled" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M14.5 3A2.5 2.5 0 0 1 17 5.5v9a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 3 14.5v-9A2.5 2.5 0 0 1 5.5 3zM7 11a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2M7 7a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2"/></svg></span></button>
  <a class="fui-Button" data-appearance="primary" href="#actions">リンクのボタン</a>
</div>
```

### v9 との差と未確認の点

- フォーカスは `:focus-visible` による近似である。v9 は react-tabster のポリフィルが `data-fui-focus-visible` を付け、その判定はブラウザーの `:focus-visible` と細部で異なりうる（未検証）。フォーカスが当たったときの見た目（枠、影、`::after` の輪）は、9.75.2 の描画と計算値が一致した（フォーカスの状態は属性と class で当てた。実際のキーボードの操作では確かめていない）。異なりうるのは、どの操作で当たるかである。
- iconOnly は v9 では自動の判定、React を使わない HTML では `data-icon-only` の手書きである。icon があるときの small と large の上下の padding は `:has(> .fui-Button__icon)` で判定する。
- アイコンの `1em` の規則は、react-icons の大きさのないアイコンを再現する独自の規則である。9.75.2 を描いて確かめたところ、react-icons の SVG は class に `fui-Icon` を持ち、`display: inline` と `line-height: 0` を当てる。`fluent2-base.css` の `.fui-Icon` も同じ値にしてある。
- Griffel のバケットの順（reset → 既定 → 擬似クラス → reset の at-rule → `@supports` → `@media`）は Griffel の仕様として知られる順で、手元のソースでは確かめていない（推論）。この順のため、at-rule をファイルの末尾にまとめた。
- 同じ詳細度で擬似クラスが違う規則どうしの勝ち負けは、v9 では CSS を差し込んだ順で決まり、描画の順に左右されうる。CSS では記述順に固定した。
- `<a>` の disabled は、v9 が自動で行う `href` の除去と `role="link"` の付与を、React を使わない HTML では手で書く。
- サイトの指針（コントラストの比など）はソースの値ではない。Web Components v3 は small と large の rest の角丸を `borderRadiusSmall` と `borderRadiusLarge` にし、フォーカスを外側の輪で描くが、この章は v9 に従う。

## CompoundButton

### 概要と使い分け（Do / Don't）

主題に説明文（secondaryContent）を添える 2 段のボタンである。説明が判断を助けるときに使う。説明がなくても分かる操作には Button を使う。

| Do | Don't |
|---|---|
| 説明文で、選んだ結果を短く示す | 主題と同じことを説明文で繰り返す |
| 選択肢を並べて比べさせる場面で使う | ツールバーのような密な場所に置く |

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

スタイルの出典は `packages/react-components/react-button/library/src/components/CompoundButton/useCompoundButtonStyles.styles.ts` である。

| スロット | 要素 | class |
|---|---|---|
| root | `<button>` | `fui-CompoundButton fui-Button` |
| icon（任意） | `<span>` | `fui-CompoundButton__icon fui-Button__icon` |
| contentContainer | `<span>`（常にある） | `fui-CompoundButton__contentContainer` |
| secondaryContent（任意） | `<span>` | `fui-CompoundButton__secondaryContent` |

- 子の順は icon（before）→ contentContainer [主題、secondaryContent] → icon（after）である（`packages/react-components/react-button/library/src/components/CompoundButton/renderCompoundButton.tsx:17-27`）。
- iconOnly は、icon があり、主題と説明文がないとき（`packages/react-components/react-button/library/src/components/CompoundButton/useCompoundButton.ts:37`）。
- role、ARIA、キーボードは Button と同じ。説明文はボタンの名前に含まれる。

### バリエーション

Button と同じ（`data-appearance`、`data-size`、`data-shape`、`data-icon-position`、`data-icon-only`）。

### 寸法（size ごとの表）

| 項目 | small | medium（既定） | large | 行 |
|---|---|---|---|---|
| height | `auto` | `auto` | `auto` | 19 |
| padding（上 右 下 左） | `--spacingHorizontalS` `--spacingHorizontalS` `--spacingHorizontalMNudge` `--spacingHorizontalS`（8 8 10 8px） | `14px` `--spacingHorizontalM` `--spacingHorizontalL` `--spacingHorizontalM`（14 12 16 12px） | `18px` `--spacingHorizontalL` `--spacingHorizontalXL` `--spacingHorizontalL`（18 16 20 16px） | 134-151 |
| 主題の文字 | `--fontSizeBase300` / `--lineHeightBase300`。太さは Button の small の Regular が残る | `--fontSizeBase300` / `--lineHeightBase300` / Semibold | `--fontSizeBase400` / `--lineHeightBase400` / Semibold | 137-150 |
| 説明文の文字 | `--fontSizeBase200`、`line-height: 100%`、Regular | 同じ | `--fontSizeBase300` | 242-259 |
| アイコン | 40px | 40px | 40px | 218-222 |
| アイコンと文字の間 | `--spacingHorizontalM`（12px） | 同じ | 同じ | 225-230 |
| iconOnly | padding `--spacingHorizontalXS`、幅 48px | `--spacingHorizontalSNudge`、52px | `--spacingHorizontalS`、56px | 194-214 |

contentContainer は `display: flex`、`flex-direction: column`、`text-align: start`（v9 は `left` で、RTL で反転する。233-240）。

### 色と状態（トークン名の表）

root の色、枠線、フォーカスは Button と同じ。説明文の色だけが変わる。

| appearance | rest | hover | pressed | 行 |
|---|---|---|---|---|
| secondary、outline | `colorNeutralForeground2` | `colorNeutralForeground2Hover` | `colorNeutralForeground2Pressed` | 18-36 |
| primary | `colorNeutralForegroundOnBrand` | 同じ | 同じ | 59-75 |
| subtle | `colorNeutralForeground2` | `colorNeutralForeground2Hover` | `colorNeutralForeground2Pressed` | 85-100 |
| transparent | `colorNeutralForeground2` | `colorNeutralForeground2BrandHover` | `colorNeutralForeground2BrandPressed` | 115-131 |
| disabled | `colorNeutralForegroundDisabled` | 同じ | 同じ | 154-170 |

### フォーカス・動き・ハイコントラスト

- フォーカスと動きは Button と同じ。
- ハイコントラスト: hover と pressed で説明文を `Highlight`（39-53）、primary の説明文を `HighlightText`（76-80）、subtle の hover と pressed の説明文を `Canvas`（102-113）、disabled の説明文を `GrayText`（172-191）にする。

### 実装の例

```html demo
<div style="display:flex;flex-wrap:wrap;gap:8px;align-items:flex-start">
  <button type="button" class="fui-CompoundButton fui-Button" data-appearance="primary"><span class="fui-CompoundButton__icon fui-Button__icon" aria-hidden="true"><svg class="fui-Icon fui-Icon-regular" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M14.5 3A2.5 2.5 0 0 1 17 5.5v9a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 3 14.5v-9A2.5 2.5 0 0 1 5.5 3zm0 1h-9C4.67 4 4 4.67 4 5.5v9c0 .83.67 1.5 1.5 1.5h9c.83 0 1.5-.67 1.5-1.5v-9c0-.83-.67-1.5-1.5-1.5M7 11a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2M7 7a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2"/></svg><svg class="fui-Icon fui-Icon-filled" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M14.5 3A2.5 2.5 0 0 1 17 5.5v9a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 3 14.5v-9A2.5 2.5 0 0 1 5.5 3zM7 11a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2M7 7a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2"/></svg></span><span class="fui-CompoundButton__contentContainer">予定を作成<span class="fui-CompoundButton__secondaryContent">会議の招待を送る</span></span></button>
  <button type="button" class="fui-CompoundButton fui-Button"><span class="fui-CompoundButton__icon fui-Button__icon" aria-hidden="true"><svg class="fui-Icon fui-Icon-regular" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M14.5 3A2.5 2.5 0 0 1 17 5.5v9a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 3 14.5v-9A2.5 2.5 0 0 1 5.5 3zm0 1h-9C4.67 4 4 4.67 4 5.5v9c0 .83.67 1.5 1.5 1.5h9c.83 0 1.5-.67 1.5-1.5v-9c0-.83-.67-1.5-1.5-1.5M7 11a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2M7 7a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2"/></svg><svg class="fui-Icon fui-Icon-filled" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M14.5 3A2.5 2.5 0 0 1 17 5.5v9a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 3 14.5v-9A2.5 2.5 0 0 1 5.5 3zM7 11a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2M7 7a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2"/></svg></span><span class="fui-CompoundButton__contentContainer">予定を作成<span class="fui-CompoundButton__secondaryContent">会議の招待を送る</span></span></button>
  <button type="button" class="fui-CompoundButton fui-Button" data-appearance="subtle" data-size="small"><span class="fui-CompoundButton__contentContainer">small<span class="fui-CompoundButton__secondaryContent">説明文</span></span></button>
  <button type="button" class="fui-CompoundButton fui-Button" disabled><span class="fui-CompoundButton__contentContainer">無効<span class="fui-CompoundButton__secondaryContent">説明文</span></span></button>
</div>
```

### v9 との差と未確認の点

- small の主題の太さは、CompoundButton が `font-weight` を書かないので、Button の small の Regular になる。ソースのとおりに再現した。
- subtle の hover の説明文が、ハイコントラストで `Canvas` になる（102-113）。背景も文字も `Canvas` 系になりうるが、ソースのとおりに書いた。実機での見え方は確かめていない。
- 説明文の要素は `<span>` で、contentContainer の中で縦に並ぶ。Web Components v3 はアイコンと文字の間を `gap: 12px` で取るが、この章は v9 の margin に従う。

## MenuButton

### 概要と使い分け（Do / Don't）

メニューを開閉するボタンである。自分では操作を持たない。主な操作があるなら SplitButton を使う。

| Do | Don't |
|---|---|
| 開く内容が分かる名前を付ける | 押すと操作も実行されるようにする |
| 下向きの山形でメニューがあることを示す | 山形を別のアイコンに替えて意味を変える |

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

スタイルの出典は `packages/react-components/react-button/library/src/components/MenuButton/useMenuButtonStyles.styles.ts` である。

| スロット | 要素 | class |
|---|---|---|
| root | `<button>` | `fui-MenuButton fui-Button` |
| icon（任意） | `<span>` | `fui-MenuButton__icon fui-Button__icon` |
| menuIcon | `<span>`（既定の中身は `ChevronDownRegular`） | `fui-MenuButton__menuIcon` |

- 子の順は icon → 文字 → menuIcon である（`packages/react-components/react-button/library/src/components/MenuButton/renderMenuButton.tsx:17-21`）。`iconPosition` は `before` に固定される（141）。
- 文字がなければ iconOnly になる。iconOnly で icon があれば menuIcon を出さず、icon もなければ山形だけを出す（同 20）。
- `aria-expanded` を常に付ける（`packages/react-components/react-button/library/src/components/MenuButton/useMenuButton.tsx:40-43`）。`aria-haspopup` と開閉は Menu（MenuTrigger）の担当で、この章では扱わない。React を使わない HTML では `aria-haspopup="menu"` を自分で書く。
- `popovertarget` でメニューを開くとき、`actions.js` は `data-fui-enhance` のボタンの `aria-expanded` を、popover の開閉に合わせる。

### バリエーション

Button と同じ。`data-icon-position` は効かない。

### 寸法（size ごとの表）

| 項目 | small | medium（既定） | large | 行 |
|---|---|---|---|---|
| menuIcon の大きさ | 12px、`line-height: var(--lineHeightBase200)` | 12px、`--lineHeightBase200` | 16px、`--lineHeightBase400` | 77-100 |
| menuIcon の前の間 | `--spacingHorizontalXS`（4px）。iconOnly では付けない | 同じ | 同じ | 103-105、136 |

menuIcon の土台は `line-height: 0`（78-80）。ほかの寸法は Button と同じ。

### 色と状態（トークン名の表）

展開時（`aria-expanded="true"`）の色である。アイコンは塗りに切り替える（17-24）。

| appearance | background | color | border | 行 |
|---|---|---|---|---|
| secondary | `colorNeutralBackground1Selected` | `colorNeutralForeground1Selected` | `colorNeutralStroke1Selected` | 35-39 |
| outline | Button のまま | `colorNeutralForeground1Selected` | `colorNeutralStroke1Selected`、幅 `--strokeWidthThicker`（3px） | 27-31 |
| primary | `colorBrandBackgroundSelected` | Button のまま | Button のまま | 32-34 |
| subtle | `colorSubtleBackgroundSelected` | `colorNeutralForeground2Selected` | Button のまま | 40-43 |
| transparent | `colorTransparentBackgroundSelected` | `colorNeutralForeground2BrandSelected` | Button のまま | 44-47 |

展開時の規則には擬似クラスがない。そのため、展開中に hover すると Button の hover の色が勝つ（v9 と同じ）。

### フォーカス・動き・ハイコントラスト

Button と同じ。展開時は、ハイコントラストで icon に hover したとき、icon を `Highlight` にする（67-74、125）。

### 実装の例

```html demo
<div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center">
  <button type="button" class="fui-MenuButton fui-Button" aria-haspopup="menu" aria-expanded="false">並べ替え<span class="fui-MenuButton__menuIcon" aria-hidden="true"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M15.85 7.65c.2.2.2.5 0 .7l-5.46 5.49a.55.55 0 0 1-.78 0L4.15 8.35a.5.5 0 1 1 .7-.7L10 12.8l5.15-5.16c.2-.2.5-.2.7 0"/></svg></span></button>
  <button type="button" class="fui-MenuButton fui-Button" aria-haspopup="menu" aria-expanded="true">展開中<span class="fui-MenuButton__menuIcon" aria-hidden="true"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M15.85 7.65c.2.2.2.5 0 .7l-5.46 5.49a.55.55 0 0 1-.78 0L4.15 8.35a.5.5 0 1 1 .7-.7L10 12.8l5.15-5.16c.2-.2.5-.2.7 0"/></svg></span></button>
  <button type="button" class="fui-MenuButton fui-Button" data-appearance="primary" aria-haspopup="menu" aria-expanded="false">新規<span class="fui-MenuButton__menuIcon" aria-hidden="true"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M15.85 7.65c.2.2.2.5 0 .7l-5.46 5.49a.55.55 0 0 1-.78 0L4.15 8.35a.5.5 0 1 1 .7-.7L10 12.8l5.15-5.16c.2-.2.5-.2.7 0"/></svg></span></button>
  <button type="button" class="fui-MenuButton fui-Button" data-appearance="subtle" aria-haspopup="menu" aria-expanded="true"><span class="fui-MenuButton__icon fui-Button__icon" aria-hidden="true"><svg class="fui-Icon fui-Icon-regular" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M14.5 3A2.5 2.5 0 0 1 17 5.5v9a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 3 14.5v-9A2.5 2.5 0 0 1 5.5 3zm0 1h-9C4.67 4 4 4.67 4 5.5v9c0 .83.67 1.5 1.5 1.5h9c.83 0 1.5-.67 1.5-1.5v-9c0-.83-.67-1.5-1.5-1.5M7 11a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2M7 7a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2"/></svg><svg class="fui-Icon fui-Icon-filled" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M14.5 3A2.5 2.5 0 0 1 17 5.5v9a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 3 14.5v-9A2.5 2.5 0 0 1 5.5 3zM7 11a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2M7 7a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2"/></svg></span>予定<span class="fui-MenuButton__menuIcon" aria-hidden="true"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M15.85 7.65c.2.2.2.5 0 .7l-5.46 5.49a.55.55 0 0 1-.78 0L4.15 8.35a.5.5 0 1 1 .7-.7L10 12.8l5.15-5.16c.2-.2.5-.2.7 0"/></svg></span></button>
  <button type="button" class="fui-MenuButton fui-Button" data-size="large" aria-haspopup="menu" aria-expanded="false">large<span class="fui-MenuButton__menuIcon" aria-hidden="true"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M15.85 7.65c.2.2.2.5 0 .7l-5.46 5.49a.55.55 0 0 1-.78 0L4.15 8.35a.5.5 0 1 1 .7-.7L10 12.8l5.15-5.16c.2-.2.5-.2.7 0"/></svg></span></button>
</div>
```

### v9 との差と未確認の点

- 展開時のアイコンの色は appearance ごとに宣言されている（52-66）が、125 行の `&&` の連鎖は最後の `iconExpandedStyles.highContrast` だけを返す。そのため実際には付かず、この CSS も付けない。Griffel は中身のない slot にも空でない class 名を返すと考え、primary にもハイコントラストの規則を当てた（推論）。
- 展開時の規則は Button の disabled より後に合成されるので、disabled で展開中なら展開時の背景が勝つ。ソースのとおりに再現した。
- `aria-haspopup` を v9 のどこが付けるかは、Menu のソースを読んでいないので確かめていない。

## SplitButton

### 概要と使い分け（Do / Don't）

主な操作のボタンと、関連する操作のメニューを開くボタンを 1 つにまとめる。

| Do | Don't |
|---|---|
| 主な操作をラベルにし、変形をメニューに入れる | 主な操作をメニューにも重ねて入れる |
| メニュー項目が主ラベルの語を省くなら `aria-describedby` で補う | 関係のない操作をメニューに混ぜる |

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

スタイルの出典は `packages/react-components/react-button/library/src/components/SplitButton/useSplitButtonStyles.styles.ts` である。

| スロット | 要素 | class |
|---|---|---|
| root | `<div>` | `fui-SplitButton` |
| primaryActionButton | Button | `fui-SplitButton__primaryActionButton fui-Button` |
| menuButton | MenuButton（文字なし、iconOnly） | `fui-SplitButton__menuButton fui-MenuButton fui-Button` |

- v9 は `appearance`、`shape`、`size`、`disabled`、`disabledFocusable` を両方のボタンに渡す（`packages/react-components/react-button/library/src/components/SplitButton/useSplitButton.ts:20-47、89-105`）。React を使わない HTML では、`data-appearance`、`data-size`、`data-shape` を root と 2 つのボタンに、`disabled` を 2 つのボタンに書く。root の disabled は、CSS が子のボタンから `:has()` で読む。
- menuButton に名前がなければ、v9 は主ボタンの id を `aria-labelledby` に入れる（同 109-116）。React を使わない HTML でも同じにする。

### バリエーション

Button と同じ（`data-appearance`、`data-size`、`data-shape`）。

### 寸法（size ごとの表）

| 対象 | 規則 | 行 |
|---|---|---|
| root | `display: inline-flex`、`justify-content: stretch`、`position: relative`、`vertical-align: middle` | 34-38 |
| 主ボタン | 終わり側（LTR で右）の上下の角丸を 0。フォーカス時も 0 | 20-23、40-43 |
| メニューのボタン | 始め側の枠線の幅を 0、始め側の上下の角丸を 0、`min-width: 24px`（WCAG の最小のターゲット） | 15-17、25-29、45-50 |

- メニューのボタンは iconOnly なので、Button の iconOnly の padding と `max-width` を受ける（medium で 5px、32px）。`min-width` は SplitButton の 24px が勝つ（root からの子孫の選択子で詳細度が高い）。
- 高さは、root の `inline-flex` の既定 `align-items: stretch` で主ボタンにそろう（CSS からの推論）。

### 色と状態（トークン名の表）

2 つのボタンの間の線は、主ボタンの終わり側の枠線の色である。hover と pressed は root（`.fui-SplitButton`）の状態で、どちらのボタンに乗っても線の色が変わる。

| appearance | rest | hover | pressed | 行 |
|---|---|---|---|---|
| secondary、outline | Button の枠線の色のまま | 同じ | 同じ | 54-56、92-94 |
| primary | `colorNeutralStrokeOnBrand` | 同じ | 同じ | 57-73 |
| subtle、transparent | `colorTransparentBackground` | `colorTransparentBackgroundHover` | `colorTransparentBackgroundPressed` | 95-128 |
| disabled | `colorNeutralStrokeDisabled` | 同じ | 同じ | 136-152 |

ボタン自身の色は Button（主ボタン）と MenuButton（メニューのボタン）に従う。

### フォーカス・動き・ハイコントラスト

- フォーカスと動きは、それぞれのボタンの Button の規則に従う。フォーカス中も、合わせ目の角丸と枠線は 0 のまま（19-30）。
- ハイコントラスト: primary の線を `HighlightText`、hover と pressed で `Highlight`（74-90）。disabled の線を `GrayText`（155-173）。

### 実装の例

```html demo
<div style="display:flex;flex-wrap:wrap;gap:12px;align-items:center">
  <div class="fui-SplitButton" data-appearance="primary">
    <button type="button" id="act-sb1" class="fui-SplitButton__primaryActionButton fui-Button" data-appearance="primary">送信</button>
    <button type="button" class="fui-SplitButton__menuButton fui-MenuButton fui-Button" data-appearance="primary" data-icon-only aria-labelledby="act-sb1" aria-haspopup="menu" aria-expanded="false"><span class="fui-MenuButton__menuIcon" aria-hidden="true"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M15.85 7.65c.2.2.2.5 0 .7l-5.46 5.49a.55.55 0 0 1-.78 0L4.15 8.35a.5.5 0 1 1 .7-.7L10 12.8l5.15-5.16c.2-.2.5-.2.7 0"/></svg></span></button>
  </div>
  <div class="fui-SplitButton">
    <button type="button" id="act-sb2" class="fui-SplitButton__primaryActionButton fui-Button"><span class="fui-Button__icon" aria-hidden="true"><svg class="fui-Icon fui-Icon-regular" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M14.5 3A2.5 2.5 0 0 1 17 5.5v9a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 3 14.5v-9A2.5 2.5 0 0 1 5.5 3zm0 1h-9C4.67 4 4 4.67 4 5.5v9c0 .83.67 1.5 1.5 1.5h9c.83 0 1.5-.67 1.5-1.5v-9c0-.83-.67-1.5-1.5-1.5M7 11a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2M7 7a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2"/></svg><svg class="fui-Icon fui-Icon-filled" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M14.5 3A2.5 2.5 0 0 1 17 5.5v9a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 3 14.5v-9A2.5 2.5 0 0 1 5.5 3zM7 11a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2M7 7a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2"/></svg></span>予定</button>
    <button type="button" class="fui-SplitButton__menuButton fui-MenuButton fui-Button" data-icon-only aria-labelledby="act-sb2" aria-haspopup="menu" aria-expanded="false"><span class="fui-MenuButton__menuIcon" aria-hidden="true"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M15.85 7.65c.2.2.2.5 0 .7l-5.46 5.49a.55.55 0 0 1-.78 0L4.15 8.35a.5.5 0 1 1 .7-.7L10 12.8l5.15-5.16c.2-.2.5-.2.7 0"/></svg></span></button>
  </div>
  <div class="fui-SplitButton" data-appearance="subtle">
    <button type="button" id="act-sb3" class="fui-SplitButton__primaryActionButton fui-Button" data-appearance="subtle">subtle</button>
    <button type="button" class="fui-SplitButton__menuButton fui-MenuButton fui-Button" data-appearance="subtle" data-icon-only aria-labelledby="act-sb3" aria-haspopup="menu" aria-expanded="false"><span class="fui-MenuButton__menuIcon" aria-hidden="true"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M15.85 7.65c.2.2.2.5 0 .7l-5.46 5.49a.55.55 0 0 1-.78 0L4.15 8.35a.5.5 0 1 1 .7-.7L10 12.8l5.15-5.16c.2-.2.5-.2.7 0"/></svg></span></button>
  </div>
  <div class="fui-SplitButton" data-appearance="primary">
    <button type="button" id="act-sb4" class="fui-SplitButton__primaryActionButton fui-Button" data-appearance="primary" disabled>無効</button>
    <button type="button" class="fui-SplitButton__menuButton fui-MenuButton fui-Button" data-appearance="primary" data-icon-only aria-labelledby="act-sb4" aria-haspopup="menu" aria-expanded="false" disabled><span class="fui-MenuButton__menuIcon" aria-hidden="true"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M15.85 7.65c.2.2.2.5 0 .7l-5.46 5.49a.55.55 0 0 1-.78 0L4.15 8.35a.5.5 0 1 1 .7-.7L10 12.8l5.15-5.16c.2-.2.5-.2.7 0"/></svg></span></button>
  </div>
</div>
```

### v9 との差と未確認の点

- root の disabled は、v9 では SplitButton の props、React を使わない HTML では子のボタンの `:disabled` か `aria-disabled="true"` から読む。
- 左右の角丸と枠線は、Griffel が RTL で反転するので、論理プロパティ（`border-start-end-radius`、`border-inline-start-width`、`border-inline-end-color`）で書いた。
- Web Components v3 には SplitButton がなく、`fluent-menu[split]` で作る。primary の線はリテラルの `white` で、v9 とは違う。

## ToggleButton

### 概要と使い分け（Do / Don't）

オンとオフの 2 状態を持つボタンである。ツールバーでよく使う。すぐに効く設定には Switch を使う。

| Do | Don't |
|---|---|
| 状態の変化を、文字に加えてアイコンや色でも示す | 色の違いだけで状態を示す |
| 書式のような、押すたびに切り替わる操作に使う | 設定画面のオンとオフに使う（Switch を使う） |

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

スタイルの出典は `packages/react-components/react-button/library/src/components/ToggleButton/useToggleButtonStyles.styles.ts` である。

| スロット | 要素 | class |
|---|---|---|
| root | `<button>` | `fui-ToggleButton fui-Button` |
| icon（任意） | `<span>` | `fui-ToggleButton__icon fui-Button__icon` |

- `checked` は `aria-pressed` に入る。role が `menuitemcheckbox` か `checkbox` なら `aria-checked` に入る（`packages/react-components/react-button/library/src/utils/useToggleState.ts:25、49`）。Toolbar の radio は `role="radio"` と `aria-checked` を使う。
- クリックで反転する。disabled と disabledFocusable では反転しない（同 27-38）。React を使わない HTML では、`data-fui-enhance` を付ければ `actions.js` が反転する。
- `isAccessible` は `data-is-accessible` で表す。rest との差が大きい、ブランドの色の checked のスタイルになる（`packages/react-components/react-button/library/src/components/ToggleButton/ToggleButton.types.ts:21-26`）。

### バリエーション

Button の属性に加えて、`aria-pressed="true|false"`（`checked`）と `data-is-accessible`（`isAccessible`、既定なし）。

### 寸法（size ごとの表）

Button と同じ。checked のときは `border-width: var(--strokeWidthThin)`（24）、outline の checked だけ `--strokeWidthThicker`（3px）にする（77）。`data-is-accessible` の outline は `--strokeWidthThin` に戻す（168-171）。

### 色と状態（トークン名の表）

checked（`isAccessible` なし）の色である。アイコンは塗りに切り替える（26-31）。

| appearance | rest | hover | pressed | 行 |
|---|---|---|---|---|
| secondary | 背景 `colorNeutralBackground1Selected`、文字 `colorNeutralForeground1Selected`、枠 `colorNeutralStroke1` | `colorNeutralBackground1Hover`、`colorNeutralForeground1Hover`、`colorNeutralStroke1Hover` | `colorNeutralBackground1Pressed`、`colorNeutralForeground1Pressed`、`colorNeutralStroke1Pressed` | 19-44 |
| outline | 背景 `colorTransparentBackgroundSelected`、枠 `colorNeutralStroke1`（3px）。フォーカス時も枠は `colorNeutralStroke1` | 背景 `colorTransparentBackgroundHover` | 背景 `colorTransparentBackgroundPressed` | 74-90 |
| primary | `colorBrandBackgroundSelected`、`colorNeutralForegroundOnBrand`、枠 `transparent` | `colorBrandBackgroundHover` | `colorBrandBackgroundPressed` | 91-107 |
| subtle | `colorSubtleBackgroundSelected`、`colorNeutralForeground2Selected`、枠 `transparent` | `colorSubtleBackgroundHover`、`colorNeutralForeground2Hover` | `colorSubtleBackgroundPressed`、`colorNeutralForeground2Pressed` | 111-127 |
| transparent | `colorTransparentBackgroundSelected`、`colorNeutralForeground2BrandSelected`、枠 `transparent` | `colorTransparentBackgroundHover`、`colorNeutralForeground2BrandHover` | `colorTransparentBackgroundPressed`、`colorNeutralForeground2BrandPressed` | 128-144 |

- subtle と transparent の checked のアイコンは `colorNeutralForeground2BrandSelected`（271-275、357-360）。
- `data-is-accessible` の checked は、どの appearance でも背景 `colorBrandBackground`（hover は `…Hover`、pressed は `…Pressed`）、文字 `colorNeutralForegroundOnBrand`、枠 `transparent`（149-165）。primary は `outline: var(--strokeWidthThin) solid var(--colorNeutralForegroundOnBrand)` を `outline-offset: -3px` で内側に引き、フォーカス時は `-4px` にする（173-183）。subtle は hover のアイコンを `colorNeutralForegroundOnBrand` にする（185-192）。
- disabled は Button と同じ背景、文字、枠に戻す。ただし subtle と transparent は、hover で `colorTransparentBackgroundHover`、pressed で `colorTransparentBackgroundPressed` の背景になる（203-268）。

### フォーカス・動き・ハイコントラスト

- フォーカスと動きは Button と同じ。
- ハイコントラスト: checked は背景と枠を `Highlight`、文字を `HighlightText`（`forced-color-adjust: none`）、hover と pressed で `HighlightText` の背景に `Highlight`、`:focus` で `border: 1px solid HighlightText` と `outline-color: Highlight`（47-70）。primary は checked でなくても Button の primary のハイコントラストを打ち消し、`ButtonFace`、`ButtonBorder`、`ButtonText` にする（295-316）。アイコンは `forced-color-adjust: auto` で、checked かつ disabled でないときは文字色を継ぐ（277-292）。

### 実装の例

```html demo
<div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center" data-fui-enhance>
  <button type="button" class="fui-ToggleButton fui-Button" aria-pressed="false">オフ</button>
  <button type="button" class="fui-ToggleButton fui-Button" aria-pressed="true">オン</button>
  <button type="button" class="fui-ToggleButton fui-Button" data-appearance="outline" aria-pressed="true">outline</button>
  <button type="button" class="fui-ToggleButton fui-Button" data-appearance="primary" aria-pressed="true">primary</button>
  <button type="button" class="fui-ToggleButton fui-Button" data-appearance="subtle" aria-pressed="true"><span class="fui-ToggleButton__icon fui-Button__icon" aria-hidden="true"><svg class="fui-Icon fui-Icon-regular" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M5.5 4.25C5.5 3.56 6.06 3 6.75 3h3.5a4 4 0 0 1 3.17 6.44c.9.7 1.58 1.8 1.58 3.31A4.23 4.23 0 0 1 10.75 17h-4c-.69 0-1.25-.56-1.25-1.25zM8 11v3.5h2.75c.81 0 1.75-.62 1.75-1.75S11.56 11 10.75 11zm0-2.5h2.25a1.5 1.5 0 1 0 0-3H8z"/></svg><svg class="fui-Icon fui-Icon-filled" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M5 4.5C5 3.67 5.67 3 6.5 3h3.88a4.12 4.12 0 0 1 3.44 6.39 4.2 4.2 0 0 1 1.43 3.24A4.36 4.36 0 0 1 10.88 17H6.5A1.5 1.5 0 0 1 5 15.5zM8 6v2.25h2.38a1.13 1.13 0 0 0 0-2.25zm0 5.25V14h2.88c.7 0 1.37-.54 1.37-1.37s-.69-1.38-1.37-1.38z"/></svg></span>太字</button>
  <button type="button" class="fui-ToggleButton fui-Button" data-appearance="transparent" aria-pressed="true"><span class="fui-ToggleButton__icon fui-Button__icon" aria-hidden="true"><svg class="fui-Icon fui-Icon-regular" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M16 3a.5.5 0 0 1 0 1h-3.16L8.23 16h3.27a.5.5 0 0 1 0 1H4a.5.5 0 0 1 0-1h3.16l4.61-12H8.5a.5.5 0 0 1 0-1z"/></svg><svg class="fui-Icon fui-Icon-filled" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M8 3.25c0-.41.34-.75.75-.75h7.5a.75.75 0 0 1 0 1.5h-3.23L8.59 15.5h2.66a.75.75 0 0 1 0 1.5h-7.5a.75.75 0 0 1 0-1.5h3.23L11.41 4H8.75A.75.75 0 0 1 8 3.25"/></svg></span>斜体</button>
  <button type="button" class="fui-ToggleButton fui-Button" data-is-accessible aria-pressed="true">isAccessible</button>
  <button type="button" class="fui-ToggleButton fui-Button" aria-pressed="true" disabled>無効</button>
</div>
```

### v9 との差と未確認の点

- checked は `aria-pressed="true"`（または `aria-checked="true"`）で表す。v9 の `checked` prop の代わりである。
- 規則は Button の後に置いた。v9 の ToggleButton の class は Button の `mergeClasses` の最後に入るので、同じ詳細度なら ToggleButton が勝つ。
- アイコンの規則は v9 ではアイコン自身の atomic な class なので、祖先の条件を `:where()` に入れて (0,1,0) にした。Button の disabled のアイコンの色（(0,2,0)）に負けるのも v9 と同じである。
- Web Components v3 は secondary の checked の文字色を `colorNeutralForeground1` にし、outline の枠を太くしない。`isAccessible` に当たるものもない。この章は v9 に従う。

## Link

### 概要と使い分け（Do / Don't）

リンクは、同じ体験の中や別のサイトへ移動するための、操作できる文字である。操作を起こすには使わない。目立たない補助の操作には、transparent か subtle のボタンを使う。以下は fluent2.microsoft.design の Link の Usage の要約である。

- default はテーマの色で、ほとんどの場合はこれを使う。subtle は本文と同じ色なので、アイコンなど別の手がかりを添える。暗い背景には inverted、ブランドの色の背景には brand の配色を使う。
- 操作できることを、色、下線、アイコン、フォーカスの表示、カーソルのうち 2 つ以上で示す。文中のリンク（inline）は rest でも下線を出す。
- リンク文字は前後の文脈なしで意味が通るようにする。URL や「ここをクリック」を使わない。新しいタブで開くなら、事前に知らせる。

| Do | Don't |
|---|---|
| 移動に使う | 操作（保存、削除など）に使う |
| 手がかりを 2 つ以上にする | 曖昧な文字や URL をリンク文字にする |
| 文中のリンクには `data-inline` で下線を出す | 同じページに同じリンクを重ねる |

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

スタイルの出典は `packages/react-components/react-link/library/src/components/Link/useLinkStyles.styles.ts` である。

- スロットは root だけで、class は `fui-Link`。`href` があれば `<a>`、なければ `<button type="button">` で描く（`packages/react-components/react-link/library/src/components/Link/useLink.ts:46-54`）。
- disabled（`packages/react-components/react-link/library/src/components/Link/useLinkState.ts`）: `<a>` は `href` を外し、`role="link"` と `aria-disabled="true"` を付け、`tabindex="0"` を残す（disabledFocusable のとき）（15-26、56）。`<button>` は `disabled` 属性を付ける（57-59）。
- キーボードはネイティブのまま。`<span role="button">` のときは Enter と Space で押す（47-50）。

### バリエーション

| 属性 | 値（既定は太字） | v9 の props |
|---|---|---|
| `data-appearance` | **`default`**、`subtle` | `appearance` |
| `data-inline` | 属性の有無 | `inline` |
| `data-background-appearance` | `inverted`、`brand`（リンク自身か祖先に付ける） | BackgroundAppearanceContext |

### 寸法（size ごとの表）

Link に size はない。

| 項目 | 値 | 行 |
|---|---|---|
| display | `inline` | 29 |
| 文字 | `--fontFamilyBase`、`--fontSizeBase300`、Regular。`href` のある `<a>` は `font-size: inherit`。line-height は書かない | 30-32、57-59 |
| margin、padding | `0` | 33-34 |
| 下線 | rest は `none`、太さ `--strokeWidthThin` | 37-38 |
| その他 | `background-color: transparent`、`box-sizing: border-box`、`cursor: pointer`、`overflow: inherit`、`text-align: start`（v9 は `left`）、`text-overflow: inherit`、`user-select: text` | 25-40 |
| `<button>` のとき | `border-style: none` | 53-55 |

### 色と状態（トークン名の表）

| 種類 | rest | hover | pressed（`:active`） | 行 |
|---|---|---|---|---|
| default | `colorBrandForegroundLink`、下線なし | `colorBrandForegroundLinkHover`、下線 | `colorBrandForegroundLinkPressed`、下線 | 27、42-50 |
| subtle | `colorNeutralForeground2Link` | `colorNeutralForeground2LinkHover`、下線 | `colorNeutralForeground2LinkPressed`、下線 | 61-73 |
| inline | 下線あり | 同じ | 同じ | 75-77 |
| 背景 inverted | `colorBrandForegroundInverted` | 同じ | 同じ | 107-115 |
| 背景 brand | `colorNeutralForegroundInvertedLink` | `colorNeutralForegroundInvertedLinkHover` | `colorNeutralForegroundInvertedLinkPressed` | 116-124 |
| disabled | `colorNeutralForegroundDisabled`、下線なし、`cursor: not-allowed` | 同じ | 同じ | 79-93 |

合成の順は root → フォーカス → href → button → subtle → inverted → brand → inline → disabled で、後ろが勝つ（132-144）。

### フォーカス・動き・ハイコントラスト

- フォーカス: 下線を二重にし、`text-decoration-color: var(--colorStrokeFocus2)` にする。outline は出さない（14-24）。
- 動き: v9 の Link には transition がない。
- ハイコントラスト: disabled で `color: GrayText`（95-105）。ほかの規則はない。

### 実装の例

```html demo
<p style="margin:0 0 8px">
  <a class="fui-Link" href="#actions">既定のリンク</a>
  <a class="fui-Link" data-appearance="subtle" href="#actions">subtle のリンク</a>
  <button type="button" class="fui-Link">ボタンで描くリンク</button>
  <a class="fui-Link" role="link" aria-disabled="true">無効のリンク</a>
</p>
<p style="margin:0 0 8px">詳しくは<a class="fui-Link" data-inline href="#actions">利用規約</a>を参照する。</p>
<p style="margin:0;padding:8px 12px;background:var(--colorBrandBackground);color:var(--colorNeutralForegroundOnBrand)" data-background-appearance="brand">ブランドの背景の上の<a class="fui-Link" data-inline href="#actions">リンク</a></p>
```

### v9 との差と未確認の点

- inverted と brand は、v9 では BackgroundAppearanceContext から得る。React を使わない HTML では `data-background-appearance` を付ける。
- フォーカスは `:focus-visible` による近似である。
- inverted が `colorBrandForegroundInverted`、brand が `colorNeutralForegroundInvertedLink` を使う組み合わせは、ソースのとおりに記した。
- Web Components v3 は、hover の色を `@media (hover: hover)` の中だけで変え、ハイコントラストで `LinkText` を使う。この章は v9 に従う。

## Toolbar

### 概要と使い分け（Do / Don't）

ツールバーは、いまの画面や作業に関わる、よく使う操作をすばやく出す（例: エディターの書式）。以下は fluent2.microsoft.design の Toolbar の Usage の要約である。

- 関連する操作をグループにまとめ、区切り線と余白で示す。破壊的な操作は、ほかから離す。
- ツールバーは容器いっぱいに広がり、2 行に折り返さない。入りきらない項目は、最後の項目をオーバーフローのメニューボタンにして入れる。
- 複数のツールバーがあれば、それぞれに `aria-label` か `aria-labelledby` を付ける。アイコンだけのボタンには、ツールチップと `aria-label` で名前を付ける。

| Do | Don't |
|---|---|
| よく使う操作だけを置き、グループに分ける | 2 行に折り返す |
| アイコンだけのボタンに名前とツールチップを付ける | 破壊的な操作をほかの操作と並べる |

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

スタイルの出典は `packages/react-components/react-toolbar/library/src/components/` の各 `use*Styles.styles.ts` である。

| 部品 | 要素と ARIA | class |
|---|---|---|
| Toolbar | `<div role="toolbar">`。vertical なら `aria-orientation="vertical"` | `fui-Toolbar` |
| ToolbarGroup | `<div role="presentation">` | `fui-ToolbarGroup` |
| ToolbarButton | Button（既定 `subtle`） | `fui-Button`（独自の class はない） |
| ToolbarToggleButton | ToggleButton（`aria-pressed`、既定 `subtle`） | `fui-ToggleButton fui-Button` |
| ToolbarRadioButton | ToggleButton に `role="radio"` と `aria-checked`。`aria-pressed` は付けない | `fui-ToggleButton fui-Button` |
| ToolbarDivider | Divider（向きは Toolbar と直交） | `fui-Divider fui-ToolbarDivider`（v9 の静的な class は `fui-Divider` だけ。`fui-ToolbarDivider` は再現版の目印） |

- 出典: `packages/react-components/react-toolbar/library/src/components/Toolbar/useToolbar.ts:60-68`、`ToolbarGroup/useToolbarGroup.ts:42`、`ToolbarButton/useToolbarButton.ts:22-31`、`ToolbarRadioButton/useToolbarRadioButton.ts:53、69`、`ToolbarDivider/useToolbarDivider.ts:47-48`。
- キーボード: 矢印キーで項目を移り、端で反対側に回る（上下左右とも。`useToolbar.ts:146-149` の `circular: true`、`axis: 'both'`）。Tab はツールバーの外へ出て、戻ると最後にフォーカスした項目に入る。React を使わない HTML では、1 つの項目だけを `tabindex="0"`、ほかを `-1` にする（ローヴィング）。`data-fui-enhance` を付ければ、`actions.js` が矢印キー、Home、End で `tabindex` を動かす。
- Toggle と Radio の選択は、v9 では Toolbar の `checkedValues` が管理する（`useToolbar.ts:92-101`）。`actions.js` は、`role="radio"` のボタンを同じ `data-name` の仲間の中で 1 つだけ `aria-checked="true"` にする。

### バリエーション

| 属性 | 値（既定は太字） | v9 の props |
|---|---|---|
| `data-size`（Toolbar） | `small`、**`medium`**、`large` | `size` |
| `data-vertical`（Toolbar） | 属性の有無 | `vertical` |
| `data-vertical`（ToolbarButton） | 属性の有無。アイコンを文字の上に置く | `vertical` |

Toolbar の size は ToolbarToggleButton と ToolbarRadioButton に渡る（`useToolbarToggleButton.ts:23-24`）。React を使わない HTML では、これらのボタンにも同じ `data-size` を書く。ToolbarButton は v9 で medium に固定される（`useToolbarButton.ts:27`）ので、`data-size` を書かない。

### 寸法（size ごとの表）

| 対象 | small | medium（既定） | large | 出典 |
|---|---|---|---|---|
| Toolbar の padding（横のとき） | `0px 4px` | `4px 8px` | `4px 20px` | `Toolbar/useToolbarStyles.styles.ts:14-27` |
| Toolbar vertical | `flex-direction: column`、`width: fit-content`、padding は `4px 8px` | 同じ | 同じ | 同 20-23、40-42 |
| ToolbarGroup | `display: flex`、`align-items: center`。vertical で縦に並べる | 同じ | 同じ | `ToolbarGroup/useToolbarGroupStyles.styles.ts:12-21` |
| ToolbarButton の vertical | root を縦に並べ、アイコンを `font-size: 24px`、`margin: 0` | 同じ | 同じ | `ToolbarButton/useToolbarButtonStyles.styles.ts:7-15` |
| ToolbarDivider | `max-width: 1px`、`padding: 0 12px`。Toolbar が vertical なら `max-width: initial` | 同じ | 同じ | `ToolbarDivider/useToolbarDividerStyles.styles.ts:7-31` |

Toolbar の値はすべて v9 の直書きである。区切り線そのもの（色 `colorNeutralStroke2`、縦の線の `min-height: 20px`）は Divider の規則による（表示の部品の章）。

### 色と状態（トークン名の表）

- ToolbarButton は Button の色に従う。既定は subtle なので `data-appearance="subtle"` を書く。
- ToolbarToggleButton と ToolbarRadioButton の選択時は、ToggleButton の checked の色に、背景 `colorSubtleBackgroundSelected`、文字 `colorNeutralForeground2Selected`、アイコン `colorNeutralForeground2BrandSelected` を重ねる（`ToolbarToggleButton/useToolbarToggleButtonStyles.styles.ts:8-18`、`ToolbarRadioButton/useToolbarRadioButtonStyles.styles.ts:8-18`）。この class は ToggleButton の class より後に合成されるので、appearance が primary でも rest の背景と文字色はこれになる。

### フォーカス・動き・ハイコントラスト

Toolbar 自身には、フォーカス、transition、ハイコントラストの規則がない。各ボタンは Button と ToggleButton の規則に従う。

### 実装の例

```html demo
<div class="fui-Toolbar" role="toolbar" aria-label="書式" data-fui-enhance>
  <div class="fui-ToolbarGroup" role="presentation">
    <button type="button" class="fui-ToggleButton fui-Button" data-appearance="subtle" data-icon-only aria-pressed="true" aria-label="太字" tabindex="0"><span class="fui-ToggleButton__icon fui-Button__icon" aria-hidden="true"><svg class="fui-Icon fui-Icon-regular" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M5.5 4.25C5.5 3.56 6.06 3 6.75 3h3.5a4 4 0 0 1 3.17 6.44c.9.7 1.58 1.8 1.58 3.31A4.23 4.23 0 0 1 10.75 17h-4c-.69 0-1.25-.56-1.25-1.25zM8 11v3.5h2.75c.81 0 1.75-.62 1.75-1.75S11.56 11 10.75 11zm0-2.5h2.25a1.5 1.5 0 1 0 0-3H8z"/></svg><svg class="fui-Icon fui-Icon-filled" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M5 4.5C5 3.67 5.67 3 6.5 3h3.88a4.12 4.12 0 0 1 3.44 6.39 4.2 4.2 0 0 1 1.43 3.24A4.36 4.36 0 0 1 10.88 17H6.5A1.5 1.5 0 0 1 5 15.5zM8 6v2.25h2.38a1.13 1.13 0 0 0 0-2.25zm0 5.25V14h2.88c.7 0 1.37-.54 1.37-1.37s-.69-1.38-1.37-1.38z"/></svg></span></button>
    <button type="button" class="fui-ToggleButton fui-Button" data-appearance="subtle" data-icon-only aria-pressed="false" aria-label="斜体" tabindex="-1"><span class="fui-ToggleButton__icon fui-Button__icon" aria-hidden="true"><svg class="fui-Icon fui-Icon-regular" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M16 3a.5.5 0 0 1 0 1h-3.16L8.23 16h3.27a.5.5 0 0 1 0 1H4a.5.5 0 0 1 0-1h3.16l4.61-12H8.5a.5.5 0 0 1 0-1z"/></svg><svg class="fui-Icon fui-Icon-filled" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M8 3.25c0-.41.34-.75.75-.75h7.5a.75.75 0 0 1 0 1.5h-3.23L8.59 15.5h2.66a.75.75 0 0 1 0 1.5h-7.5a.75.75 0 0 1 0-1.5h3.23L11.41 4H8.75A.75.75 0 0 1 8 3.25"/></svg></span></button>
  </div>
  <div class="fui-Divider fui-ToolbarDivider" role="separator" aria-orientation="vertical" data-vertical></div>
  <button type="button" class="fui-Button" data-appearance="subtle" data-icon-only aria-label="予定" tabindex="-1"><span class="fui-Button__icon" aria-hidden="true"><svg class="fui-Icon fui-Icon-regular" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M14.5 3A2.5 2.5 0 0 1 17 5.5v9a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 3 14.5v-9A2.5 2.5 0 0 1 5.5 3zm0 1h-9C4.67 4 4 4.67 4 5.5v9c0 .83.67 1.5 1.5 1.5h9c.83 0 1.5-.67 1.5-1.5v-9c0-.83-.67-1.5-1.5-1.5M7 11a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2M7 7a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2"/></svg><svg class="fui-Icon fui-Icon-filled" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M14.5 3A2.5 2.5 0 0 1 17 5.5v9a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 3 14.5v-9A2.5 2.5 0 0 1 5.5 3zM7 11a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2M7 7a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2"/></svg></span></button>
  <button type="button" class="fui-Button" data-appearance="subtle" tabindex="-1">共有</button>
</div>
```

```html demo
<div class="fui-Toolbar" role="toolbar" aria-label="表示" data-size="small" data-fui-enhance>
  <button type="button" class="fui-ToggleButton fui-Button" data-appearance="subtle" data-size="small" role="radio" data-name="act-view" aria-checked="true" tabindex="0">一覧</button>
  <button type="button" class="fui-ToggleButton fui-Button" data-appearance="subtle" data-size="small" role="radio" data-name="act-view" aria-checked="false" tabindex="-1">カード</button>
  <div class="fui-Divider fui-ToolbarDivider" role="separator" aria-orientation="vertical" data-vertical></div>
  <button type="button" class="fui-Button" data-appearance="subtle" data-vertical tabindex="-1"><span class="fui-Button__icon" aria-hidden="true"><svg class="fui-Icon fui-Icon-regular" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M14.5 3A2.5 2.5 0 0 1 17 5.5v9a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 3 14.5v-9A2.5 2.5 0 0 1 5.5 3zm0 1h-9C4.67 4 4 4.67 4 5.5v9c0 .83.67 1.5 1.5 1.5h9c.83 0 1.5-.67 1.5-1.5v-9c0-.83-.67-1.5-1.5-1.5M7 11a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2M7 7a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2"/></svg><svg class="fui-Icon fui-Icon-filled" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M14.5 3A2.5 2.5 0 0 1 17 5.5v9a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 3 14.5v-9A2.5 2.5 0 0 1 5.5 3zM7 11a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2M7 7a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2"/></svg></span>予定</button>
</div>
```

### v9 との差と未確認の点

- 矢印キーの移動は、v9 では Tabster の Mover が受け持つ。`actions.js` は同じ挙動（上下左右、端で回る、最後の項目を覚える）を小さく再現した。Home と End で端へ移るのは Tabster の Mover の既定と理解しているが、手元の Tabster 本体では確かめていない（推論）。無効の項目（`:disabled`）は飛ばし、`aria-disabled="true"` の項目には止まる。
- ToolbarDivider について、v9 は `display: inline-flex` も書くが、Divider の class が後に合成されて Divider の `display: flex` が勝つ（`ToolbarDivider/useToolbarDividerStyles.styles.ts:22-31`）。CSS ではこの結果に合わせ、`display` を書かない。区切り線の見た目は Divider の CSS（表示の部品の章）に頼る。
- ToolbarDivider のマークアップは Divider の章と食い違わない。v9 の ToolbarDivider は `vertical: !toolbarVertical` を渡した Divider で（`ToolbarDivider/useToolbarDivider.ts:47-48`）、子がなければ wrapper を描かない（`packages/react-components/react-divider/library/src/components/Divider/renderDivider.tsx:11-16`）。横の Toolbar では `aria-orientation="vertical"` と `data-vertical`、`data-vertical` の Toolbar では `aria-orientation="horizontal"` で `data-vertical` なしにする。`tools/verify/compare-b.html` の比較（2026-11-13）で、small・medium・large と vertical の Toolbar の区切り線が v9 と一致した。v9 の DOM に `fui-ToolbarDivider` の class はない（`useToolbarDividerStyles.styles.ts` は静的な class を定義しない）。CSS の目印として残す。
- 同じ比較で、`data-vertical` の ToolbarButton のアイコンの幅だけが違った。v9 はアイコンのスロットを Button の medium の 20px 四方のまま `font-size: 24px` にし、react-icons の SVG（`flex-shrink: 1`）が幅 20px に縮む。比較の当時、土台の `.fui-Icon` は `flex-shrink: 0` で、SVG が 24px のままはみ出ていた。土台を react-icons の計算値（`display: inline`、`flex-shrink: 1`）に合わせたので、再現版も 20px に縮む。
- ToolbarButton の説明（`ToolbarButton.tsx:12-13`）は Toolbar の size に従うと書くが、このコミットのコードは medium に固定する。コードに従った。
- ToolbarRadioGroup は調べていない。radio を並べるときの `role="radiogroup"` の要否は未確認である。
- Web Components v3 に Toolbar はない。

## Label

### 概要と使い分け（Do / Don't）

ラベルは、部品やその集まりに名前を付ける。以下は fluent2.microsoft.design の Label の Usage の要約である。

- 入力欄やチェックボックスと組にして情報を求める。部品の上に置き、レイアウトが許せば横でもよい。
- 長ければ折り返し、省略しない。必須はアスタリスクで示す。disabled は、ラベルを付けた部品が disabled のときに使う（コントラストの要件はない）。

| Do | Don't |
|---|---|
| 短く説明的にし、部品の上に置く | placeholder をラベルの代わりにする |
| 必須をアスタリスクで示す | 完全な文や手順の説明を入れる。末尾にコロンを付ける |

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

スタイルの出典は `packages/react-components/react-label/library/src/components/Label/useLabelStyles.styles.ts` である。

| スロット | 要素 | class |
|---|---|---|
| root | `<label>` | `fui-Label` |
| required（任意） | `<span aria-hidden="true">`。中身は `*` | `fui-Label__required` |

- 子の順は 文字 → required（`packages/react-components/react-label/library/src/components/Label/renderLabel.tsx:15-18`）。`required={true}` の中身は `*`（`packages/react-components/react-label/library/src/components/Label/useLabel.tsx:37`）。
- 印は `aria-hidden="true"` なので、必須の意味は部品の `required` か `aria-required="true"` で伝える。
- キーボード操作はない。

### バリエーション

| 属性 | 値（既定は太字） | v9 の props |
|---|---|---|
| `data-size` | `small`、**`medium`**、`large` | `size` |
| `data-weight` | **`regular`**、`semibold` | `weight` |
| `data-disabled` | 属性の有無（`<label>` は `:disabled` にならない） | `disabled` |

### 寸法（size ごとの表）

| 項目 | small | medium（既定） | large | 行 |
|---|---|---|---|---|
| 文字 | `--fontSizeBase200` / `--lineHeightBase200` | `--fontSizeBase300` / `--lineHeightBase300` | `--fontSizeBase400` / `--lineHeightBase400` / Semibold | 34-48 |
| 太さ（`data-weight="semibold"`） | `--fontWeightSemibold` | 同じ | 同じ | 50-52 |
| required の前の間 | `--spacingHorizontalXS`（4px） | 同じ | 同じ | 29-32 |

### 色と状態（トークン名の表）

| 対象 | 色 | 行 |
|---|---|---|
| 文字 | `colorNeutralForeground1`、`--fontFamilyBase` | 17-20 |
| required | `colorPaletteRedForeground3` | 29-32 |
| disabled（required も） | `colorNeutralForegroundDisabled` | 22-23、75 |

### フォーカス・動き・ハイコントラスト

フォーカス、動き、hover の規則はない。ハイコントラストでは disabled を `GrayText` にする（24-26）。

### 実装の例

```html demo
<div style="display:flex;flex-wrap:wrap;gap:16px;align-items:baseline">
  <label class="fui-Label" data-size="small">small</label>
  <label class="fui-Label">medium</label>
  <label class="fui-Label" data-size="large">large</label>
  <label class="fui-Label" data-weight="semibold">semibold</label>
  <label class="fui-Label">必須<span class="fui-Label__required" aria-hidden="true">*</span></label>
  <label class="fui-Label" data-disabled>無効<span class="fui-Label__required" aria-hidden="true">*</span></label>
</div>
```

### v9 との差と未確認の点

- disabled は `data-disabled` で表す。
- Web Components v3 は `display: inline-flex`、`cursor: pointer`、必須の印に `colorPaletteRedForeground1` を使う。この章は v9 に従う（`colorPaletteRedForeground3`、`padding-inline-start`）。
- 必須の印の前の間は、v9 は `padding-left`（RTL で反転）なので `padding-inline-start` で書いた。

## Field

### 概要と使い分け（Do / Don't）

Field は、ラベルとフォームの部品（Input、Select など）を組にし、補助の文（hint）と検証のメッセージを添える。以下は fluent2.microsoft.design の Field の Usage の要約である。

- 既定はラベルを上に置く。幅が足りず、部品の種類と幅がそろうときだけ、ラベルを左に置いてよい（horizontal）。
- 検証の状態は success、warning、error。メッセージには既定のアイコンが付く。
- 必須は個々の部品に付ける。すべてが必須なら、各部品に印を付けず、前置きで説明する。
- disabled では部品だけを disabled の見た目にし、ラベル、hint、メッセージは有効のままにする。

| Do | Don't |
|---|---|
| どの部品にも見えるラベルを付ける | placeholder だけに頼る |
| 必須を示すか、すべて必須と説明する | すべて必須のフォームで各部品に印を付ける |
| hint と検証メッセージを短くする | 長い手順の文をラベルにする |

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

スタイルの出典は `packages/react-components/react-field/library/src/components/Field/useFieldStyles.styles.ts` である。

| スロット | 要素 | class |
|---|---|---|
| root | `<div>` | `fui-Field` |
| label | Label | `fui-Field__label fui-Label` |
| （部品） | Input など | 部品の class |
| validationMessage | `<div>` | `fui-Field__validationMessage` |
| validationMessageIcon | `<span>` | `fui-Field__validationMessageIcon` |
| hint | `<div>` | `fui-Field__hint` |

- 子の順は label → 部品 → validationMessage [アイコン、文] → hint（`packages/react-components/react-field/library/src/components/Field/renderField.tsx:22-33`）。
- id と ARIA（`packages/react-components/react-field/library/src/components/Field/useFieldBase.tsx:16-33`、`packages/react-components/react-field/library/src/contexts/useFieldControlProps.ts:86-111`）: ラベルの `for` を部品の id に向ける。部品に `aria-describedby`（メッセージと hint の id）、error なら `aria-invalid="true"`、必須なら `required` か `aria-required="true"` を付ける。メッセージは error と warning のとき `role="alert"`。React を使わない HTML では、これらを手で書く。
- 既定の検証アイコンは、error が `DiamondDismiss12Filled`、warning が `Warning12Filled`、success が `CheckmarkCircle12Filled`（`packages/react-components/react-field/library/src/components/Field/useField.tsx:11-16`）。

### バリエーション

| 属性 | 値（既定は太字） | v9 の props |
|---|---|---|
| `data-orientation` | **`vertical`**、`horizontal` | `orientation` |
| `data-size` | `small`、**`medium`**、`large`（ラベルにも同じ値を書く） | `size` |
| `data-validation-state` | `error`、`warning`、`success`、`none`。書かなければ、メッセージがあるとき error | `validationState` |

### 寸法（size ごとの表）

| 対象 | small | medium（既定） | large | 行 |
|---|---|---|---|---|
| ラベル（vertical） | 上下 padding `--spacingVerticalXXS`（2px）、下 margin `--spacingVerticalXXS` | 同じ | 上下 padding `1px`、下 margin `--spacingVerticalXS`（4px） | 48-58 |
| ラベル（horizontal） | 上下 padding `--spacingVerticalXS`（4px） | 上下 padding `--spacingVerticalSNudge`（6px） | 上下 padding `9px`（40px の Input の中央にそろえる） | 60-78 |

- root は `display: grid`。horizontal は `grid-template-columns: 33% 1fr`、`grid-template-rows: auto auto auto 1fr` で、ラベルが 1 列目の全行を占め、終わり側に `--spacingHorizontalM` の margin を取る。ラベルがなければ、始め側に 33% の padding を取る（22-40、60-66）。
- ラベルは `max-width: max-content`、`max-height: max-content`（43-46）。
- hint と検証メッセージは、上 margin `--spacingVerticalXXS`、caption1（`--fontSizeBase200` / `--lineHeightBase200` / Regular）（81-85）。
- 検証アイコンは 12px、`display: inline-block`、始め側に `calc(-12px - var(--spacingHorizontalXS))`、終わり側に `--spacingHorizontalXS` の margin、`line-height: 0`、`vertical-align: -1px`。メッセージは始め側に `calc(12px + var(--spacingHorizontalXS))` の padding を取り、2 行目以降もアイコンの右にそろえる（92-108）。

### 色と状態（トークン名の表）

| 対象 | 色 | 行 |
|---|---|---|
| hint、メッセージ | `colorNeutralForeground3` | 83 |
| メッセージ（error） | `colorPaletteRedForeground1` | 88-90 |
| アイコン（error / warning / success） | `colorPaletteRedForeground1` / `colorPaletteDarkOrangeForeground1` / `colorPaletteGreenForeground1` | 110-120 |

メッセージの文字が赤くなるのは error だけで、warning と success はアイコンだけが色を持つ。

### フォーカス・動き・ハイコントラスト

Field 自身には、フォーカス、transition、ハイコントラストの規則がない。部品の規則に従う。

### 実装の例

部品には、テキストの入力の章の Input（`fui-Input`）を使う。

```html demo
<div style="display:grid;gap:16px;max-width:480px">
  <div class="fui-Field">
    <label class="fui-Field__label fui-Label" for="act-f1">メールアドレス<span class="fui-Label__required" aria-hidden="true">*</span></label>
    <span class="fui-Input"><input class="fui-Input__input" id="act-f1" type="email" required aria-invalid="true" aria-describedby="act-f1-msg act-f1-hint"></span>
    <div class="fui-Field__validationMessage" id="act-f1-msg" role="alert"><span class="fui-Field__validationMessageIcon" aria-hidden="true"><svg class="fui-Icon" width="12" height="12" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true"><path d="M4.59 1.09a2 2 0 0 1 2.82 0l3.5 3.5a2 2 0 0 1 0 2.82l-3.5 3.5a2 2 0 0 1-2.82 0l-3.5-3.5a2 2 0 0 1 0-2.83zm3.26 3.06a.5.5 0 0 0-.7 0L6 5.29 4.85 4.15a.5.5 0 0 0-.7.7L5.29 6 4.15 7.15a.5.5 0 0 0 .7.7L6 6.71l1.15 1.14a.5.5 0 1 0 .7-.7L6.71 6l1.14-1.15a.5.5 0 0 0 0-.7"/></svg></span>形式が正しくない</div>
    <div class="fui-Field__hint" id="act-f1-hint">例: name@example.com</div>
  </div>
  <div class="fui-Field" data-validation-state="warning">
    <label class="fui-Field__label fui-Label" for="act-f2">表示名</label>
    <span class="fui-Input"><input class="fui-Input__input" id="act-f2" type="text" aria-describedby="act-f2-msg"></span>
    <div class="fui-Field__validationMessage" id="act-f2-msg" role="alert"><span class="fui-Field__validationMessageIcon" aria-hidden="true"><svg class="fui-Icon" width="12" height="12" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true"><path d="M4.28 1.97a2 2 0 0 1 3.43 0l3 5A2 2 0 0 1 9 10H3A2 2 0 0 1 1.3 6.98zM6 6.75a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5M6 3.5a.5.5 0 0 0-.5.5v1.5a.5.5 0 0 0 1 0V4a.5.5 0 0 0-.5-.5"/></svg></span>ほかの人と同じ名前である</div>
  </div>
  <div class="fui-Field" data-orientation="horizontal" data-validation-state="success">
    <label class="fui-Field__label fui-Label" for="act-f3">ユーザー名</label>
    <span class="fui-Input"><input class="fui-Input__input" id="act-f3" type="text" aria-describedby="act-f3-msg"></span>
    <div class="fui-Field__validationMessage" id="act-f3-msg"><span class="fui-Field__validationMessageIcon" aria-hidden="true"><svg class="fui-Icon" width="12" height="12" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true"><path d="M1 6a5 5 0 1 1 10 0A5 5 0 0 1 1 6m7.35-.9a.5.5 0 1 0-.7-.7L5.5 6.54 4.35 5.4a.5.5 0 1 0-.7.7l1.5 1.5c.2.2.5.2.7 0z"/></svg></span>使える</div>
  </div>
</div>
```

### v9 との差と未確認の点

- 検証の状態の既定（メッセージがあれば error）は、`data-validation-state` を書かないときの CSS で再現した。
- id の採番と ARIA の付与は、v9 では Field が部品に渡す。React を使わない HTML では手で書く。
- サイトは error で部品の枠を赤くすると書くが、v9 の Field 自身は部品の枠を変えない。枠は部品の側（Input の `aria-invalid="true"`）が変える。
- 左右の padding と margin は、v9 の `padding-left` と `margin-right`（RTL で反転）を論理プロパティで書いた。
- Web Components v3 は `label-position` 属性でラベルの位置を選び、フォーカスが内にあるとき Field 全体に輪を描く。v9 にはない。

## InfoLabel

### 概要と使い分け（Do / Don't）

InfoLabel は、ラベルと info ボタンを組にする。ボタンを押すと、補足の情報をポップオーバーで出す。以下は fluent2.microsoft.design の InfoLabel の Usage の要約である。

- 作業に必須でない情報だけに使う。必須の情報は hint など常に見える場所に置く。補足が要らなければ普通の Label を使う。
- 内容は 1〜2 文か 1 つの句にとどめ、リンクは末尾に 1 つまでにする。
- ポップオーバーは、ほかを選ぶか Esc を押すまで開いたまま。フォーカスを閉じ込めない。info ボタンはタブ順に残す。

| Do | Don't |
|---|---|
| 補足の情報だけを短く入れる | 作業に必須の情報を入れる |
| リンクは末尾に 1 つ、具体的な文言にする | 1 か所に複数置く。「詳細」だけのリンクにする |

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

スタイルの出典は `packages/react-components/react-infolabel/library/src/components/InfoLabel/useInfoLabelStyles.styles.ts` と `packages/react-components/react-infolabel/library/src/components/InfoButton/useInfoButtonStyles.styles.ts` である。

| スロット | 要素 | class |
|---|---|---|
| root | `<span>` | `fui-InfoLabel` |
| label | Label | `fui-InfoLabel__label fui-Label` |
| infoButton | `<button type="button" aria-label="information">` | `fui-InfoLabel__infoButton fui-InfoButton` |
| info（ポップアップの面） | PopoverSurface（`role="note"`、`tabindex="-1"`） | `fui-InfoButton__info` |

- 子の順は label → infoButton（`packages/react-components/react-infolabel/library/src/components/InfoLabel/renderInfoLabel.tsx:15-18`）。v9 の Popover は既定で inline に描くので、面はボタンの直後に入る。
- ボタンの名前は、`aria-labelledby` に「ラベルの id、ボタン自身の id」を並べて作る（`packages/react-components/react-infolabel/library/src/components/InfoLabel/useInfoLabel.ts:81`）。面は自分自身の id を `aria-labelledby` に入れる（同 72-79）。開いている間、root に `aria-owns`（面の id）を付ける（同 83-85）。
- 中身のアイコンは size ごとに Info12、Info16、Info20 の Regular と Filled の組（`packages/react-components/react-infolabel/library/src/components/InfoButton/useInfoButton.tsx:18-22`）。
- 面の既定は、上・先頭側（`above-start`）、矢印付き、Popover の size は small / small / medium（同 24-28、65-73）。フォーカスがボタンと面の外へ出たら閉じる（同 95-107）。
- React を使わない HTML では、`popover` 属性と `popovertarget` で開閉する。Esc と外側のクリックで閉じるのはブラウザーが行う。`data-fui-enhance` を付ければ、`actions.js` が `aria-expanded`、`aria-owns`、位置、フォーカスが外へ出たときの閉じを受け持つ。

### バリエーション

| 属性 | 値（既定は太字） | v9 の props |
|---|---|---|
| `data-size` | `small`、**`medium`**、`large`。InfoLabel、Label、InfoButton に同じ値を書く | `size` |

### 寸法（size ごとの表）

| 項目 | small | medium（既定） | large | 出典 |
|---|---|---|---|---|
| InfoButton の padding | `--spacingVerticalXS` `--spacingHorizontalXS`（4px 4px） | 同じ | `--spacingVerticalXXS`（2px 2px） | `useInfoButtonStyles.styles.ts:36、94-96` |
| アイコン | Info12（12px） | Info16（16px） | Info20（20px） | `useInfoButton.tsx:18-22` |
| ボタンの大きさ（推論） | 12 + 8 = 20px | 16 + 8 = 24px | 20 + 4 = 24px | — |
| infoButton の上下の margin | `calc(0px - var(--spacingVerticalXXS))`（-2px） | 同じ | `-1px` | `useInfoLabelStyles.styles.ts:22-35` |
| 面の文字 | caption1 | caption1 | body1 | `useInfoButtonStyles.styles.ts:99-105` |
| 面の最大幅 | `264px` | 同じ | 同じ | 同 101 |

- InfoButton は `display: inline-flex`、中央そろえ、`box-sizing: border-box`、`position: relative`、`border-style: none`、`border-radius: var(--borderRadiusMedium)`、`margin: 0`（21-36）。
- InfoLabel のラベルは `vertical-align: top`、`cursor: inherit`、`color: inherit`（14-19）。Label の色より後に合成されるので、文字色は親から継ぐ。
- アイコンの実寸は、名前（Info12 など）からの推定である。small の 20px はサイトの「20×20」と一致する。

### 色と状態（トークン名の表）

| 状態 | background | color | アイコン | 行 |
|---|---|---|---|---|
| rest | `colorTransparentBackground` | `colorNeutralForeground2` | 線 | 30-43 |
| hover | `colorTransparentBackgroundHover` | `colorNeutralForeground2BrandHover` | 塗り | 45-56 |
| pressed（`:hover:active`） | `colorTransparentBackgroundPressed` | `colorNeutralForeground2BrandPressed` | 塗り | 57-60 |
| 開いている | `colorTransparentBackgroundSelected` | `colorNeutralForeground2BrandSelected` | 塗り | 63-73 |

disabled の規則はない。

### フォーカス・動き・ハイコントラスト

- フォーカス: `createFocusOutlineStyle()`（92。`packages/react-components/react-tabster/src/focus/createFocusOutlineStyle.ts:55-112`）。outline を消し、`::after` で要素の外側 2px に `colorStrokeFocus2` の輪（角丸 `--borderRadiusMedium`）を描く。
- 動き: transition はない。
- ハイコントラスト: 文字を `CanvasText`、hover と pressed で `Highlight` の背景に `Canvas`（`forced-color-adjust: none`）、開いているときも `Highlight` と `Canvas`、フォーカスの輪を `Highlight`（74-90。`createFocusOutlineStyle.ts:60-64`）。

### 実装の例

面の背景、影、角丸は、オーバーレイの章の PopoverSurface（`fui-PopoverSurface`）の CSS による。

```html demo
<div style="display:flex;flex-wrap:wrap;gap:24px;align-items:center">
  <span class="fui-InfoLabel">
    <label class="fui-InfoLabel__label fui-Label" id="act-il1-label" for="act-il1-input">送信元</label>
    <button type="button" class="fui-InfoLabel__infoButton fui-InfoButton" id="act-il1-btn" aria-label="information" aria-labelledby="act-il1-label act-il1-btn" popovertarget="act-il1-info" data-fui-enhance><svg class="fui-Icon fui-Icon-regular" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M8.5 7.5a.5.5 0 1 0-1 0v3a.5.5 0 0 0 1 0zm.25-2a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0M8 1a7 7 0 1 0 0 14A7 7 0 0 0 8 1M2 8a6 6 0 1 1 12 0A6 6 0 0 1 2 8"/></svg><svg class="fui-Icon fui-Icon-filled" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M8 1a7 7 0 1 1 0 14A7 7 0 0 1 8 1m0 5.25a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5m.5 1.25a.5.5 0 0 0-1 0v3a.5.5 0 0 0 1 0z"/></svg></button>
    <div class="fui-InfoButton__info fui-PopoverSurface" id="act-il1-info" popover role="note" tabindex="-1" aria-labelledby="act-il1-info" data-size="small">返信はこのアドレスに届く。</div>
  </span>
  <span class="fui-InfoLabel">
    <label class="fui-InfoLabel__label fui-Label" id="act-il2-label">開いた状態の見本</label>
    <button type="button" class="fui-InfoLabel__infoButton fui-InfoButton" id="act-il2-btn" aria-label="information" aria-labelledby="act-il2-label act-il2-btn" aria-expanded="true"><svg class="fui-Icon fui-Icon-regular" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M8.5 7.5a.5.5 0 1 0-1 0v3a.5.5 0 0 0 1 0zm.25-2a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0M8 1a7 7 0 1 0 0 14A7 7 0 0 0 8 1M2 8a6 6 0 1 1 12 0A6 6 0 0 1 2 8"/></svg><svg class="fui-Icon fui-Icon-filled" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M8 1a7 7 0 1 1 0 14A7 7 0 0 1 8 1m0 5.25a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5m.5 1.25a.5.5 0 0 0-1 0v3a.5.5 0 0 0 1 0z"/></svg></button>
  </span>
</div>
```

### v9 との差と未確認の点

- 開閉は、v9 の Popover の代わりにネイティブの `popover` を使う提案である。開いている状態の色は、`aria-expanded="true"` か、直後の面の `:popover-open` で付ける。v9 の PopoverTrigger が `aria-expanded` を付けるかは確かめていない。
- 位置は `actions.js` の近似である。上・先頭側に置き、上に入らなければ下に置く。ボタンとの間の 4px は v9 の値ではない（react-positioning の offset と矢印は再現しない）。JS がなければ、ブラウザーの既定（画面の中央）に出る。
- v9 は `<span>` の中に面の `<div>` を置く。HTML の内容モデルとしては厳密でないが、v9 の DOM に合わせた。
- InfoButton の Info12、Info16、Info20 の SVG の実寸は確かめていない（`@fluentui/svg-icons` の `info_16_*` は 16×16）。例では medium（16px）だけを使った。

## 土台への提案

- `fluent2-base.css` に、大きさのないアイコン（`1em`）を表す汎用の規則（例: `.fui-Icon[data-size="1em"]` や、スロットの直下の SVG を `1em` にする規則）を置くと、各コンポーネントの CSS が同じ規則を持たずに済む。いまは `actions.css` が `.fui-Button__icon > svg` と `.fui-MenuButton__menuIcon > svg` に独自に書いている。
