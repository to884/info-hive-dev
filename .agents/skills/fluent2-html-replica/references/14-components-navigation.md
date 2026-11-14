# ナビゲーションと表

この章は、画面の中を移動する部品と、表の部品を扱う。TabList、Nav、Breadcrumb、Accordion、Tree、Carousel、Table（DataGrid を含む）の 7 つである。

CSS は `assets/fluent2.css` の `navigation` の部分、振る舞いは `assets/fluent2.js` にある（開発用のリポジトリ（非公開）の原本は `src/components/navigation.css` と `navigation.js`）。JavaScript は `data-fui-enhance` を付けた要素だけを扱う。付けなければ、見た目だけの静的な部品として使える。

数値の基準は React v9（`@fluentui/react-components` 9.75.2、microsoft/fluentui commit `f9720c35ba89`）である。出典はリポジトリからの相対パスと行で示す。長いパスは各節の初めに略記を決める。

共通の決まり:

- class 名は v9 の静的な class 名に合わせる。バリエーションは、v9 の props 名を kebab-case にした data 属性で表す。既定値の属性は書かなくてよい。
- 文脈で決まる props（TabList の `size`、Table の `size`、Tree の `appearance` など）は、v9 と同じく親の要素に付け、子は CSS の `:where()` で受け取る。
- `[data-fui-focus-visible]` は `:focus-visible` で、`[data-fui-focus-within]:focus-within` は `:has(:focus-visible)` で近似する。v9 は Tabster がキーボードでの操作を判定して属性を付ける（`packages/react-components/react-tabster/src/focus/createCustomFocusIndicatorStyle.ts:69-76`）。ブラウザーの `:focus-visible` の判定とは、マウスで押したあとの扱いなどが少し異なる。
- アイコンは `@fluentui/svg-icons` の SVG をそのまま置く。v9 が `font-size` でアイコンの大きさを決める部品では、CSS が SVG を `1em` にそろえる。

## TabList

略記: `[tabs]` = `packages/react-components/react-tabs/library/src/components/`

### 概要と使い分け（Do / Don't）

TabList は、ページを離れずに、関連する内容のカテゴリーを切り替える。内容の多いページを区切るときや、密接に関係する少数のページの間の移動に使う。

- Do: ラベルを短い名詞か句にし、文法と概念をそろえる。最初の表示で 1 つ（ふつうは先頭）を選んでおく。アイコンだけのタブには、アクセシブルな名前と見えるツールチップを付ける。
- Do: 横のタブが入りきらないときは、オーバーフローのメニューを足す。狭い画面で多くがあふれるなら、Accordion か Dropdown にする。
- Don't: 横のタブを折り返したり、スクロールさせたりする。関係の薄いページへの移動や、操作の実行に使う（移動はリンク、操作はボタン）。
- Don't: テキストだけ、アイコンとテキスト、アイコンだけを混ぜる。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

| 部品 | 要素 | role・ARIA | class | 出典 |
|---|---|---|---|---|
| TabList | `div` | `role="tablist"`、縦は `aria-orientation="vertical"` | `fui-TabList` | `[tabs]TabList/useTabList.ts:127-128` |
| Tab | `button type="button"` | `role="tab"`、`aria-selected="true"/"false"`（disabled のときは付けない） | `fui-Tab` | `[tabs]Tab/useTab.ts:95-99` |
| icon | `span` | なし | `fui-Tab__icon` | `[tabs]Tab/useTabStyles.styles.ts:10-14` |
| content | `span` | なし | `fui-Tab__content` | 同上 |
| 場所取り | `span`（非表示） | なし | `fui-Tab__content--reserved-space` | `[tabs]Tab/useTabStyles.styles.ts:16-18`。v9 は選択中のタブと icon だけのタブには描かない（`[tabs]Tab/useTab.ts:40-44`） |

- 子の順は icon、content、場所取りである（`[tabs]Tab/renderTab.tsx:14-18`）。場所取りは、選択時の太字の幅を先に確保する span で、content と同じグリッドのセルに `visibility: hidden` で重なる。v9 は選択していないタブにだけ描くが、選択中に残しても見た目は変わらない。React を使わない HTML では常に置いてよい。
- アイコンは Regular（`fui-Icon-regular`）と Filled（`fui-Icon-filled`）の 2 つを置く。選ぶと Filled に替わる（`[tabs]Tab/useTabStyles.styles.ts:531-536, 555-562`）。
- タブパネル（`role="tabpanel"`）は部品に含まれない。利用者が置き、`aria-controls` と `aria-labelledby` で結ぶ。
- disabled かつ選択中のタブは、v9 では `aria-selected` を持たない。React を使わない HTML では `data-selected` で表す。
- キーボード: 矢印キーで移動し、端で反対側へ回る。縦は上下、横は左右である。Tab キーで入ると、選ばれているタブにフォーカスが来る（`[tabs]TabList/useTabList.ts:154-158`）。フォーカスしただけでは選ばない。`selectTabOnFocus`（既定 `false`、`[tabs]TabList/TabList.types.ts:82`）に当たる `data-select-tab-on-focus` を付けると、フォーカスで選ぶ。`navigation.js` はこれに Home と End を加える。

### バリエーション

| 属性（TabList に付ける） | 値 | 既定 | v9 の prop | 出典 |
|---|---|---|---|---|
| `data-appearance` | `transparent` / `subtle` / `subtle-circular` / `filled-circular` | `transparent` | `appearance` | `[tabs]TabList/TabList.types.ts:49-51`、`TabList/useTabList.ts:27` |
| `data-size` | `small` / `medium` / `large` | `medium` | `size` | `[tabs]TabList/TabList.types.ts:94-96` |
| `data-vertical` | 有無 | なし | `vertical` | `[tabs]TabList/TabList.types.ts:100-102` |
| `data-select-tab-on-focus` | 有無（JS） | なし | `selectTabOnFocus` | `[tabs]TabList/TabList.types.ts:82` |

- `transparent` と `subtle` は、選択を下線（インジケーター）で示す。違いは背景のトークンだけである。
- `subtle-circular` と `filled-circular` は、下線を持たず、丸い背景と枠で選択を示す（`[tabs]Tab/useTabStyles.styles.ts:630`）。タブの間に gap が付く。

### 寸法（size ごとの表）

Tab の共通: `display: grid; grid-auto-flow: column`、`border-radius: var(--borderRadiusMedium)`、`line-height: var(--lineHeightBase300)`、`overflow: hidden`（`[tabs]Tab/useTabStyles.styles.ts:41-57`）。content の padding は `0 var(--spacingHorizontalXXS)`（573）。

| size・向き | padding（block / inline） | アイコンと文字の間 | アイコン | 文字（通常 / 選択） | 高さ（計算） | 出典 |
|---|---|---|---|---|---|---|
| small・横 | 6px / 6px（`spacingVerticalSNudge` / `spacingHorizontalSNudge`） | 2px（`spacingHorizontalXXS`） | 20px | `body1` / `body1Strong` | 32px | 64-67, 540-544 |
| small・縦 | 2px / 6px | 2px | 20px | 同上 | 24px | 68-72 |
| medium・横 | 12px / 10px（`spacingVerticalM` / `spacingHorizontalMNudge`） | 6px（`spacingHorizontalSNudge`） | 20px | 同上 | 44px | 73-76, 545-549 |
| medium・縦 | 6px / 10px | 6px | 20px | 同上 | 32px | 77-81 |
| large・横 | 16px / 10px（`spacingVerticalL`） | 6px | 24px | `body2` / `subtitle2` | 56px（アイコンなし 54px） | 82-85, 550-554, 578-583 |
| large・縦 | 8px / 10px（`spacingVerticalS`） | 6px | 24px | 同上 | 40px（アイコンなし 38px） | 86-90 |

アイコンの大きさは v9 の直書きで、small と medium は同じである（538-539 のコメント）。高さはアイコンの行の高さから求めた計算値である。

下線（`::after` が選択、`::before` がホバー・押下の保留）:

| size・向き | 太さ | 位置 | 出典（`::after` / `::before`） |
|---|---|---|---|
| small・横 | `strokeWidthThick` 2px | 下端、左右から `spacingHorizontalSNudge` 6px | 470-477 / 384-391 |
| small・縦 | `strokeWidthThicker` 3px | 先頭の端、上下から `spacingVerticalXS` 4px | 478-485 / 392-399 |
| medium・横 | 3px | 下端、左右から `spacingHorizontalM` 12px | 486-493 / 400-407 |
| medium・縦 | 3px | 先頭の端、上下から `spacingVerticalS` 8px | 494-501 / 408-415 |
| large・横 | 3px | 下端、左右から 12px | 502-509 / 416-423 |
| large・縦 | 3px | 先頭の端、上下から `spacingVerticalMNudge` 10px | 510-517 / 424-431 |

- medium・横では、左右の 12px が「padding 10px と content の padding 2px」の和と一致し、下線は文字の幅にそろう（計算）。
- circular の 2 つ: 角丸は `borderRadiusCircular`、枠は `1px solid colorTransparentStroke`（181-183）。padding-block は枠の 1px を引いた small 1px、medium 5px、large 7px（191-199）。高さは small 24px、medium 32px、large 40px になる（計算）。TabList の gap は small が `spacingHorizontalSNudge` 6px、他が `spacingHorizontalS` 8px（`[tabs]TabList/useTabListStyles.styles.ts:31-36, 54`）。

### 色と状態（トークン名の表）

transparent と subtle（`[tabs]Tab/useTabStyles.styles.ts:91-177, 345-469`）。ホバーと押下は `:enabled` のときだけ当たる。

| 状態 | 背景（transparent / subtle） | アイコン | 文字 | 下線 |
|---|---|---|---|---|
| rest | `colorTransparentBackground` / `colorSubtleBackground` | `colorNeutralForeground2` | `colorNeutralForeground2` | なし |
| hover | `colorTransparentBackgroundHover` / `colorSubtleBackgroundHover` | `colorNeutralForeground2Hover` | `colorNeutralForeground2Hover` | 保留 `colorNeutralStroke1Hover` |
| pressed | `colorTransparentBackgroundPressed` / `colorSubtleBackgroundPressed` | `colorNeutralForeground2Pressed` | `colorNeutralForeground2Pressed` | 保留 `colorNeutralStroke1Pressed` |
| selected | appearance のまま | `colorCompoundBrandForeground1`（Filled） | `colorNeutralForeground1`、太字 | `colorCompoundBrandStroke` |
| selected・hover | appearance の hover | `colorCompoundBrandForeground1Hover` | `colorNeutralForeground1Hover` | `colorCompoundBrandStrokeHover`（下に保留） |
| selected・pressed | appearance の pressed | `colorCompoundBrandForeground1Pressed` | `colorNeutralForeground1Pressed` | `colorCompoundBrandStrokePressed` |
| disabled | `colorTransparentBackground` | `colorNeutralForegroundDisabled` | `colorNeutralForegroundDisabled` | 保留は `colorTransparentStroke` |
| disabled・selected | 同上 | 同上 | 同上、太字 | `colorNeutralForegroundDisabled` |

subtle-circular（200-243）と filled-circular（244-303）:

| 状態 | subtle-circular（背景 / 枠 / 文字） | filled-circular（背景 / 文字） |
|---|---|---|
| rest | `colorSubtleBackground` / `colorTransparentStroke` / `colorNeutralForeground2` | `colorNeutralBackground3` / `colorNeutralForeground2` |
| hover | `colorSubtleBackgroundHover` / `colorNeutralStroke1Hover` / `colorNeutralForeground2Hover` | `colorNeutralBackground3Hover` / `colorNeutralForeground2Hover` |
| pressed | `colorSubtleBackgroundPressed` / `colorNeutralStroke1Pressed` / `colorNeutralForeground2Pressed` | `colorNeutralBackground3Pressed` / `colorNeutralForeground2Pressed` |
| selected | `colorBrandBackground2` / `colorCompoundBrandStroke` / `colorBrandForeground2` | `colorBrandBackground` / `colorNeutralForegroundOnBrand` |
| selected・hover | `colorBrandBackground2Hover` / `colorCompoundBrandStrokeHover` / `colorBrandForeground2Hover` | `colorBrandBackgroundHover` / `colorNeutralForegroundOnBrand` |
| selected・pressed | `colorBrandBackground2Pressed` / `colorCompoundBrandStrokePressed` / `colorBrandForeground2Pressed` | `colorBrandBackgroundPressed` / `colorNeutralForegroundOnBrand` |
| disabled | `colorSubtleBackground` / （rest のまま） / `colorNeutralForegroundDisabled` | `colorNeutralBackgroundDisabled` / `colorNeutralForegroundDisabled` |
| disabled・selected | `colorNeutralBackgroundDisabled` / `colorNeutralStrokeDisabled` / `colorNeutralForegroundDisabled` | `colorNeutralBackgroundDisabled`、枠 `colorNeutralStrokeDisabled` / `colorNeutralForegroundDisabled` |

circular のアイコンと文字は `color: inherit` で、タブの色を受け継ぐ（184-189）。

### フォーカス・動き・ハイコントラスト

- フォーカス: Tab は下線に `::after` を使うので、既定の `::after` の輪ではなく box-shadow で描く（310-312 のコメント）。`border-color: transparent`、透明の 2px の outline、`box-shadow: var(--shadow4), 0 0 0 2px var(--colorStrokeFocus2)`、`z-index: 1`（313-326）。circular は内側に `0 0 0 1px var(--colorNeutralStrokeOnBrand) inset` を足す（327-341）。
- 下線のスライド: v9 は新しく選んだタブで前のタブの矩形を測り、`--fui-Tab__indicator--offset`（位置の差）と `--fui-Tab__indicator--scale`（幅の比）を入れる。次のフレームで 0 と 1 に戻し、`transform` を `durationSlow`（300ms）、`curveDecelerateMax` で動かす（`[tabs]Tab/useTabAnimatedIndicator.styles.ts:18-50, 88-137`）。下線は前のタブの位置へ跳び、そこから縮みながら滑る。React を使わない HTML では `navigation.js` が同じことをする。跳ぶ間は `data-fui-indicator-jump` で transition を外す。
- 縮小モーション: `@media (prefers-reduced-motion: reduce)` で `transition-property: none; transition-duration: 0.01ms`（29-34）。
- 背景と文字の色には transition がない。
- ハイコントラスト: 保留の下線は `Highlight`、選択の下線は `ButtonText`（359-366, 453-463）。subtle-circular の枠は `Canvas`、選択中は `Highlight`（213-215, 231-233）。filled-circular のホバーは背景 `Highlight` と文字 `HighlightText`、選択中は背景 `ButtonText` と文字 `ButtonFace`（255-293）。

### 実装の例

```html demo
<div class="fui-TabList" role="tablist" aria-label="予定の表示" data-fui-enhance>
  <button class="fui-Tab" role="tab" type="button" id="n14-tab-1" aria-controls="n14-panel-1" aria-selected="true">
    <span class="fui-Tab__icon"><svg class="fui-Icon fui-Icon-regular" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7 11a1 1 0 1 0 0-2 1 1 0 0 0 0 2m1 2a1 1 0 1 1-2 0 1 1 0 0 1 2 0m2-2a1 1 0 1 0 0-2 1 1 0 0 0 0 2m1 2a1 1 0 1 1-2 0 1 1 0 0 1 2 0m2-2a1 1 0 1 0 0-2 1 1 0 0 0 0 2m4-5.5A2.5 2.5 0 0 0 14.5 3h-9A2.5 2.5 0 0 0 3 5.5v9A2.5 2.5 0 0 0 5.5 17h9a2.5 2.5 0 0 0 2.5-2.5zM4 7h12v7.5c0 .83-.67 1.5-1.5 1.5h-9A1.5 1.5 0 0 1 4 14.5zm1.5-3h9c.83 0 1.5.67 1.5 1.5V6H4v-.5C4 4.67 4.67 4 5.5 4"/></svg><svg class="fui-Icon fui-Icon-filled" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M5.5 3A2.5 2.5 0 0 0 3 5.5V6h14v-.5A2.5 2.5 0 0 0 14.5 3zM17 7H3v7.5A2.5 2.5 0 0 0 5.5 17h9a2.5 2.5 0 0 0 2.5-2.5zm-9 3a1 1 0 1 1-2 0 1 1 0 0 1 2 0m-1 4a1 1 0 1 1 0-2 1 1 0 0 1 0 2m4-4a1 1 0 1 1-2 0 1 1 0 0 1 2 0m-1 4a1 1 0 1 1 0-2 1 1 0 0 1 0 2m4-4a1 1 0 1 1-2 0 1 1 0 0 1 2 0"/></svg></span>
    <span class="fui-Tab__content">予定</span><span class="fui-Tab__content--reserved-space" aria-hidden="true">予定</span>
  </button>
  <button class="fui-Tab" role="tab" type="button" id="n14-tab-2" aria-controls="n14-panel-2" aria-selected="false">
    <span class="fui-Tab__icon"><svg class="fui-Icon fui-Icon-regular" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9 2.39a1.5 1.5 0 0 1 2 0l5.5 4.94c.32.28.5.69.5 1.12v7.05c0 .83-.67 1.5-1.5 1.5H13a1.5 1.5 0 0 1-1.5-1.5V12a.5.5 0 0 0-.5-.5H9a.5.5 0 0 0-.5.5v3.5c0 .83-.67 1.5-1.5 1.5H4.5A1.5 1.5 0 0 1 3 15.5V8.45c0-.43.18-.84.5-1.12zm1.33.74a.5.5 0 0 0-.66 0l-5.5 4.94a.5.5 0 0 0-.17.38v7.05c0 .28.22.5.5.5H7a.5.5 0 0 0 .5-.5V12c0-.83.67-1.5 1.5-1.5h2c.83 0 1.5.67 1.5 1.5v3.5c0 .28.22.5.5.5h2.5a.5.5 0 0 0 .5-.5V8.45a.5.5 0 0 0-.17-.38z"/></svg><svg class="fui-Icon fui-Icon-filled" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M11 2.39a1.5 1.5 0 0 0-2 0L3.5 7.33c-.32.28-.5.69-.5 1.12v7.05c0 .83.67 1.5 1.5 1.5h2c.83 0 1.5-.67 1.5-1.5v-4c0-.28.22-.5.5-.5h3c.28 0 .5.22.5.5v4c0 .83.67 1.5 1.5 1.5h2c.83 0 1.5-.67 1.5-1.5V8.45c0-.43-.18-.84-.5-1.12z"/></svg></span>
    <span class="fui-Tab__content">ホーム</span><span class="fui-Tab__content--reserved-space" aria-hidden="true">ホーム</span>
  </button>
  <button class="fui-Tab" role="tab" type="button" id="n14-tab-3" aria-controls="n14-panel-3" aria-selected="false">
    <span class="fui-Tab__icon"><svg class="fui-Icon fui-Icon-regular" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M1.91 7.38A8.5 8.5 0 0 1 3.7 4.3a.5.5 0 0 1 .54-.13l1.92.68a1 1 0 0 0 1.32-.76l.36-2a.5.5 0 0 1 .4-.4 9 9 0 0 1 3.55 0q.32.08.38.4l.37 2a1 1 0 0 0 1.32.76l1.92-.68a.5.5 0 0 1 .54.13 8.5 8.5 0 0 1 1.78 3.08q.08.31-.15.54l-1.56 1.32a1 1 0 0 0 0 1.52l1.56 1.32a.5.5 0 0 1 .15.54 8.5 8.5 0 0 1-1.78 3.08.5.5 0 0 1-.54.13l-1.92-.68a1 1 0 0 0-1.32.76l-.37 2a.5.5 0 0 1-.38.4 8.5 8.5 0 0 1-3.56 0 .5.5 0 0 1-.39-.4l-.36-2a1 1 0 0 0-1.32-.76l-1.92.68a.5.5 0 0 1-.54-.13 8.5 8.5 0 0 1-1.78-3.08.5.5 0 0 1 .15-.54l1.56-1.32a1 1 0 0 0 0-1.52L2.06 7.92a.5.5 0 0 1-.15-.54m1.06 0 1.3 1.1a2 2 0 0 1 0 3.04l-1.3 1.1q.45 1.19 1.25 2.16l1.6-.58a2 2 0 0 1 2.63 1.53l.3 1.67a8 8 0 0 0 2.5 0l.3-1.67a2 2 0 0 1 2.64-1.53l1.6.58a8 8 0 0 0 1.24-2.16l-1.3-1.1a2 2 0 0 1 0-3.04l1.3-1.1a8 8 0 0 0-1.25-2.16l-1.6.58a2 2 0 0 1-2.63-1.53l-.3-1.67a8 8 0 0 0-2.5 0l-.3 1.67A2 2 0 0 1 5.81 5.8l-1.6-.58a8 8 0 0 0-1.24 2.16M7.5 10a2.5 2.5 0 1 1 5 0 2.5 2.5 0 0 1-5 0m1 0a1.5 1.5 0 1 0 3 0 1.5 1.5 0 0 0-3 0"/></svg><svg class="fui-Icon fui-Icon-filled" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M1.91 7.38A8.5 8.5 0 0 1 3.7 4.3a.5.5 0 0 1 .54-.13l1.92.68a1 1 0 0 0 1.32-.76l.36-2a.5.5 0 0 1 .4-.4 9 9 0 0 1 3.55 0q.32.08.38.4l.37 2a1 1 0 0 0 1.32.76l1.92-.68a.5.5 0 0 1 .54.13 8.5 8.5 0 0 1 1.78 3.08q.08.31-.15.54l-1.56 1.32a1 1 0 0 0 0 1.52l1.56 1.32a.5.5 0 0 1 .15.54 8.5 8.5 0 0 1-1.78 3.08.5.5 0 0 1-.54.13l-1.92-.68a1 1 0 0 0-1.32.76l-.37 2a.5.5 0 0 1-.38.4 8.5 8.5 0 0 1-3.56 0 .5.5 0 0 1-.39-.4l-.36-2a1 1 0 0 0-1.32-.76l-1.92.68a.5.5 0 0 1-.54-.13 8.5 8.5 0 0 1-1.78-3.08.5.5 0 0 1 .15-.54l1.56-1.32a1 1 0 0 0 0-1.52L2.06 7.92a.5.5 0 0 1-.15-.54M8 10a2 2 0 1 0 4 0 2 2 0 0 0-4 0"/></svg></span>
    <span class="fui-Tab__content">設定</span><span class="fui-Tab__content--reserved-space" aria-hidden="true">設定</span>
  </button>
  <button class="fui-Tab" role="tab" type="button" disabled>
    <span class="fui-Tab__content">アーカイブ</span><span class="fui-Tab__content--reserved-space" aria-hidden="true">アーカイブ</span>
  </button>
</div>
<div role="tabpanel" id="n14-panel-1" aria-labelledby="n14-tab-1" style="padding: 12px 10px">今週の予定を表示する。</div>
<div role="tabpanel" id="n14-panel-2" aria-labelledby="n14-tab-2" style="padding: 12px 10px" hidden>ホームの内容を表示する。</div>
<div role="tabpanel" id="n14-panel-3" aria-labelledby="n14-tab-3" style="padding: 12px 10px" hidden>設定の内容を表示する。</div>
```

```html demo
<div style="display: grid; gap: 16px">
  <div class="fui-TabList" role="tablist" aria-label="subtle-circular" data-appearance="subtle-circular" data-fui-enhance>
    <button class="fui-Tab" role="tab" type="button" aria-selected="true"><span class="fui-Tab__content">すべて</span><span class="fui-Tab__content--reserved-space" aria-hidden="true">すべて</span></button>
    <button class="fui-Tab" role="tab" type="button" aria-selected="false"><span class="fui-Tab__content">未読</span><span class="fui-Tab__content--reserved-space" aria-hidden="true">未読</span></button>
    <button class="fui-Tab" role="tab" type="button" aria-selected="false"><span class="fui-Tab__content">メンション</span><span class="fui-Tab__content--reserved-space" aria-hidden="true">メンション</span></button>
  </div>
  <div class="fui-TabList" role="tablist" aria-label="filled-circular" data-appearance="filled-circular" data-size="small" data-fui-enhance>
    <button class="fui-Tab" role="tab" type="button" aria-selected="true"><span class="fui-Tab__content">日</span><span class="fui-Tab__content--reserved-space" aria-hidden="true">日</span></button>
    <button class="fui-Tab" role="tab" type="button" aria-selected="false"><span class="fui-Tab__content">週</span><span class="fui-Tab__content--reserved-space" aria-hidden="true">週</span></button>
    <button class="fui-Tab" role="tab" type="button" aria-selected="false"><span class="fui-Tab__content">月</span><span class="fui-Tab__content--reserved-space" aria-hidden="true">月</span></button>
  </div>
</div>
```

```html demo
<div class="fui-TabList" role="tablist" aria-label="縦のタブ" aria-orientation="vertical" data-vertical data-appearance="subtle" data-fui-enhance style="width: 200px">
  <button class="fui-Tab" role="tab" type="button" aria-selected="false"><span class="fui-Tab__content">全般</span><span class="fui-Tab__content--reserved-space" aria-hidden="true">全般</span></button>
  <button class="fui-Tab" role="tab" type="button" aria-selected="true"><span class="fui-Tab__content">通知</span><span class="fui-Tab__content--reserved-space" aria-hidden="true">通知</span></button>
  <button class="fui-Tab" role="tab" type="button" aria-selected="false"><span class="fui-Tab__content">プライバシー</span><span class="fui-Tab__content--reserved-space" aria-hidden="true">プライバシー</span></button>
</div>
```

### v9 との差と未確認の点

- フォーカスの判定は `:focus-visible` の近似である。
- RTL での下線のスライドの向き（`transform-origin: left` と translateX）は確かめていない。Griffel が `transform-origin` の left を反転するかどうかも未確認である。
- `navigation.js` は Home と End での移動を足している。v9 の Tabster の矢印キーのグループが Home と End を扱うかは確かめていない。
- Web Components v3 の TabList は CSS の Anchor Positioning で下線を動かし、太さはすべて 3px である（`packages/web-components/src/tablist/tablist.styles.ts:100-113, 212-255`）。ここでは v9 の FLIP を採った。
- サイトの Usage は appearance と size に触れていない。
- 場所取りの `span` を、v9 は選択中のタブに描かない（`[tabs]Tab/useTab.ts:40-44`）。ここでは選択を JS で動かしても幅が変わらないよう、すべてのタブに置く。選択中のタブでは中身と同じ太さなので、幅は変わらない。`tools/verify/compare-b.html` の比較（2026-11-13）で、選択中のタブから外した形と寸法・色・位置が一致した。

## Nav

略記: `[nav]` = `packages/react-components/react-nav/library/src/components/`、`[drawer]` = `packages/react-components/react-drawer/library/src/`

### 概要と使い分け（Do / Don't）

Nav は、アプリやサイトの主な区画へ移動するリンクの一覧である。いつでも届く場所に置き、畳んで場所を空けられる。

- Do: 単純な形は NavItem を 1 段並べる。複雑な形は NavCategory（開閉する見出しで、リンクではない）の中に NavSubItem を置く。入れ子は 1 段までにする。
- Do: 現在のページを選択のインジケーターで示す。子が選ばれていてカテゴリーが閉じているときは、インジケーターをカテゴリーに移す。
- Do: カテゴリーのラベルにはアイコンを付ける。付けられないなら、すべてのカテゴリーで外す。
- Don't: 2 段より深い階層を Nav で表す（Tree を使う）。検索やピン留めをナビゲーションの代わりにする。
- Don't: フッターに多くを置く。本文を隠すおそれがある。400% の拡大で確かめる。
- 幅は既定で 260px のインラインのドロワーにする。サイトの指針では、640px 以下ではオーバーレイのドロワーにする。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

| 部品 | 要素 | role・ARIA | class | 出典 |
|---|---|---|---|---|
| NavDrawer | `nav`（v9 は InlineDrawer の `div` に `role="navigation"`） | `aria-label` | `fui-NavDrawer` | `[nav]NavDrawer/useNavDrawer.ts:39, 45` |
| NavDrawerHeader・Body・Footer | `div` | なし | `fui-NavDrawerHeader`・`fui-NavDrawerBody`・`fui-NavDrawerFooter` | `[nav]NavDrawerBody/useNavDrawerBody.ts:23-26` |
| NavItem | `href` があれば `a`、なければ `button` | 選択中は `aria-current="page"`、他は `"false"` | `fui-NavItem`、`fui-NavItem__icon` | `[nav]NavItem/useNavItem.ts:48, 66` |
| NavCategory | `details`（v9 は DOM を持たない） | なし | `fui-NavCategory` | `[nav]NavCategory/renderNavCategory.tsx:15` |
| NavCategoryItem | `summary`（v9 は `button`） | v9 は `aria-expanded`。閉じていて子が選ばれていれば `aria-current="page"` | `fui-NavCategoryItem`、`__icon`、`__expandIcon` | `[nav]NavCategoryItem/useNavCategoryItem.tsx:89-92, 104-112` |
| NavSubItemGroup | `div` | なし | `fui-NavSubItemGroup` | `[nav]NavSubItemGroup/useNavSubItemGroup.ts:39-45` |
| NavSubItem | `a` または `button` | `aria-current="page"` / `"false"` | `fui-NavSubItem` | `[nav]NavSubItem/useNavSubItem.ts:51, 69` |
| NavSectionHeader | `h3` | なし | `fui-NavSectionHeader` | `[nav]NavSectionHeader/useNavSectionHeader.ts:27` |
| NavDivider | `div`（Divider、`role="separator"`、`data-appearance="strong"`） | `aria-orientation="horizontal"` | `fui-Divider fui-NavDivider` | `[nav]NavDivider/useNavDivider.ts:17`、`[nav]NavDivider/useNavDividerStyles.styles.ts:5-11` |

- カテゴリーは `<details>` と `<summary>` で作る。v9 の既定 `multiple: true`（複数のカテゴリーを同時に開ける、`[nav]Nav/Nav.types.ts:68-72`）は `<details>` の既定と同じである。1 つだけ開くなら、同じ `name` 属性を付ける。
- `<summary>` は開閉のボタンとして読み上げられるので、`aria-expanded` は要らない。
- `aria-current` は `"false"` の値でも付く。CSS は `[aria-current="page"]` だけを選択の条件にしている。
- 閉じたカテゴリーの選択の見た目は、CSS が `:has()` で「閉じていて、子に `aria-current="page"` がある」ことから決める。読み上げにも伝えるには、`navigation.js` がその間だけ `summary` に `aria-current="page"` を付ける。
- キーボード: NavDrawerBody は縦の、端で回る矢印キーのグループである（`[nav]NavDrawerBody/useNavDrawerBody.ts:23-26`）。`navigation.js` は上下の矢印で項目を移る。Enter と Space はリンクと `summary` の既定の動きのままである。

### バリエーション

| 属性（NavDrawer に付ける） | 値 | 既定 | v9 の prop | 出典 |
|---|---|---|---|---|
| `data-density` | `small` / `medium` | `medium` | `density` | `[nav]Nav/Nav.types.ts:14, 79-83` |

NavDrawer の幅は、v9 の `size` を指定しなければ 260px である（`[nav]NavDrawer/useNavDrawerStyles.styles.ts:14-16, 27`）。他の幅にするときは `width` を上書きする。

### 寸法（size ごとの表）

項目（NavItem、NavCategoryItem、NavSubItem）の共通（`[nav]sharedNavStyles.styles.ts:33-73`）:

| 項目 | medium | small | 出典 |
|---|---|---|---|
| padding（上 / 右 / 下 / 左） | 10px / 8px / 10px / 10px（`spacingVerticalMNudge` / `spacingHorizontalS` / 同 / `spacingHorizontalMNudge`） | 4px / 8px / 4px / 10px（`spacingVerticalXS`） | 41, 69-73 |
| 高さ（1 行、計算） | 40px | 28px | — |
| アイコンと文字の間 | 16px（`spacingVerticalL`） | 同左 | 40 |
| 角丸 | `borderRadiusMedium` | 同左 | 43 |
| 文字 | `body1`（選択中は `body1Strong`） | 同左 | 57, 79-81 |
| NavSubItem の先頭の padding | 46px | 46px（下の注） | `[nav]NavSubItem/useNavSubItemStyles.styles.ts:13-47` |

- NavSubItem: v9 は small に 40px を用意しているが、その後ろに 46px を結合するので、small でも 46px になる（`[nav]NavSubItem/useNavSubItemStyles.styles.ts:37-47` の結合の順）。CSS も 46px にしている。

| 部品 | 値 | 出典 |
|---|---|---|
| 選択のインジケーター（`::after`） | 幅 4px、高さ 20px、`margin-inline-start: -16px`、`border-radius: var(--borderRadiusCircular)`、`position: absolute`。top と left は書かない | `[nav]sharedNavStyles.styles.ts:9-13, 87-103` |
| インジケーターの位置（計算） | flex の中の静的な位置（内容の左上）に置かれる。上端は padding-top（medium 10px、small 4px）、左端は 10 − 16 = 項目の外へ 6px | — |
| NavSubItem のインジケーター | `margin-inline-start: -52px`（−(16 + 36)px）。左端は 46 − 52 = 外へ 6px（計算） | `[nav]NavSubItem/useNavSubItemStyles.styles.ts:20-24` |
| NavCategoryItem のシェブロン | `margin-inline-start: auto; height: 20px`。`ChevronDown20Regular` | `[nav]NavCategoryItem/useNavCategoryItem.styles.ts:23-27`、`useNavCategoryItem.tsx:50-56` |
| NavDrawer | 幅 260px、背景 `colorNeutralBackground4`、`align-items: unset`。土台は InlineDrawer（`display: flex; flex-direction: column; overflow: hidden`） | `[nav]NavDrawer/useNavDrawerStyles.styles.ts:7-17`、`[drawer]shared/useDrawerBaseStyles.styles.ts:10-23` |
| NavDrawerHeader | 土台の DrawerHeader に `margin: unset; padding-inline-start: 14px; padding-block: 5px` を重ねる。末尾の padding は DrawerHeader の 24px が残る | `[nav]NavDrawerHeader/useNavDrawerHeaderStyles.styles.ts:7-13`、`[drawer]components/DrawerHeader/useDrawerHeaderStyles.styles.ts:7-18` |
| NavDrawerBody | `padding: 0 4px 0 10px`、`display: flex; flex-direction: column; row-gap: 2px`。土台の DrawerBody の `:first-child` と `:last-child` の padding（25px）は詳細度が高く、残る | `[nav]NavDrawerBody/useNavDrawerBodyStyles.styles.ts:7-15`、`[drawer]components/DrawerBody/useDrawerBodyStyles.styles.ts:7-20` |
| NavDrawerFooter | `display: flex; flex-direction: column; row-gap: 2px`。padding は下の注 | `[nav]NavDrawerFooter/useNavDrawerFooterStyles.styles.ts:16-23` |
| NavSectionHeader | `margin-inline-start: 10px; margin-block: 8px`、`caption1Strong` | `[nav]NavSectionHeader/useNavSectionHeaderStyles.styles.ts:7-13` |
| NavDivider | `flex-grow: 0; margin-top: 4px; margin-bottom: 4px` | `[nav]NavDivider/useNavDividerStyles.styles.ts:5-11` |
| NavSubItemGroup | `flex-shrink: 0; transform: translateZ(0); overflow: hidden` | `[nav]NavSubItemGroup/useNavSubItemGroupStyles.styles.ts:7-13` |

- NavDrawerFooter の padding は、v9 のソースに値が 5 つ書かれている（`[nav]NavDrawerFooter/useNavDrawerFooterStyles.styles.ts:18`）。CSS の `padding` は 4 つまでなので、ブラウザーはこの宣言を捨て、土台の DrawerFooter の `16px 24px 24px` が残る（推論）。CSS は土台の値を書いている。

### 色と状態（トークン名の表）

| 状態 | 背景 | 文字 | インジケーター | アイコン | 出典 |
|---|---|---|---|---|---|
| rest | `colorNeutralBackground4` | `colorNeutralForeground2` | なし | Regular | `[nav]sharedNavStyles.styles.ts:14, 42-44, 118-136` |
| hover | `colorNeutralBackground4Hover` | 変わらない | — | — | 15, 58-60 |
| pressed | 指定なし（hover のまま） | — | — | — | — |
| selected | 変わらない | 変わらない、太字 | `colorCompoundBrandForeground1` | Filled を `colorNeutralForeground2BrandSelected` で | 79-81, 87-103, 137-165 |

- `colorNeutralBackground4Pressed` は定義されているが、項目には使われない（`[nav]sharedNavStyles.styles.ts:16`）。Hamburger の押下だけが使う（`[nav]Hamburger/useHamburgerStyles.styles.ts:18-30`）。
- NavCategoryItem のアイコンは、子が選ばれていれば、開閉によらず Filled になる（`[nav]NavCategoryItem/useNavCategoryItem.styles.ts:72-79`）。インジケーターと太字は、閉じているときだけ付く（55-63）。
- disabled の見た目はない。

### フォーカス・動き・ハイコントラスト

- フォーカス: 補助関数を使わず、`:focus-visible` に内側の 2px の線を書く。`outline: 2px solid var(--colorStrokeFocus2); outline-offset: -2px`（`[nav]sharedNavStyles.styles.ts:62-66`）。ここだけは v9 自身が `:focus-visible` を使っている。
- 背景のホバー: `transition: background` を `durationFaster`（100ms）、`curveLinear` で（52-54）。
- インジケーター: 選ぶと、`::after` の背景が透明から `colorCompoundBrandForeground1` へ 100ms、linear で現れる（89-95）。アイコンは Filled が opacity 0→1、Regular が 1→0 で入れ替わる（137-165）。
- シェブロン: 開くと 180° 回る。開くときは `durationFast`（150ms）、`curveEasyEase`、閉じるときは同じ 150ms で `curveAccelerateMax`（`[nav]NavCategoryItem/useNavCategoryItem.tsx:18-24`、`packages/react-components/react-motion-components-preview/library/src/components/Rotate/Rotate.ts`）。
- サブ項目の開閉: v9 は Collapse（高さと opacity を 200ms、`curveEasyEaseMax`）。CSS は `::details-content` と `interpolate-size` で近似する。対応しないブラウザーでは動かずに開閉する。
- 縮小モーション: v9 の Nav には規則がない。`::details-content` の近似にだけ `prefers-reduced-motion` を足している。
- ハイコントラスト: インジケーターに `outline: solid 2px var(--colorTransparentStroke); outline-offset: -2px` を付け、背景だけで描いた棒が強制色で消えないようにする（`[nav]sharedNavStyles.styles.ts:104-109`）。

### 実装の例

```html demo
<nav class="fui-NavDrawer" aria-label="アプリのナビゲーション" data-fui-enhance style="height: 400px">
  <div class="fui-NavDrawerBody">
    <h3 class="fui-NavSectionHeader">ワークスペース</h3>
    <a class="fui-NavItem" href="#" aria-current="page">
      <span class="fui-NavItem__icon"><svg class="fui-Icon fui-Icon-regular" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9 2.39a1.5 1.5 0 0 1 2 0l5.5 4.94c.32.28.5.69.5 1.12v7.05c0 .83-.67 1.5-1.5 1.5H13a1.5 1.5 0 0 1-1.5-1.5V12a.5.5 0 0 0-.5-.5H9a.5.5 0 0 0-.5.5v3.5c0 .83-.67 1.5-1.5 1.5H4.5A1.5 1.5 0 0 1 3 15.5V8.45c0-.43.18-.84.5-1.12zm1.33.74a.5.5 0 0 0-.66 0l-5.5 4.94a.5.5 0 0 0-.17.38v7.05c0 .28.22.5.5.5H7a.5.5 0 0 0 .5-.5V12c0-.83.67-1.5 1.5-1.5h2c.83 0 1.5.67 1.5 1.5v3.5c0 .28.22.5.5.5h2.5a.5.5 0 0 0 .5-.5V8.45a.5.5 0 0 0-.17-.38z"/></svg><svg class="fui-Icon fui-Icon-filled" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M11 2.39a1.5 1.5 0 0 0-2 0L3.5 7.33c-.32.28-.5.69-.5 1.12v7.05c0 .83.67 1.5 1.5 1.5h2c.83 0 1.5-.67 1.5-1.5v-4c0-.28.22-.5.5-.5h3c.28 0 .5.22.5.5v4c0 .83.67 1.5 1.5 1.5h2c.83 0 1.5-.67 1.5-1.5V8.45c0-.43-.18-.84-.5-1.12z"/></svg></span>
      ホーム
    </a>
    <a class="fui-NavItem" href="#" aria-current="false">
      <span class="fui-NavItem__icon"><svg class="fui-Icon fui-Icon-regular" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7 11a1 1 0 1 0 0-2 1 1 0 0 0 0 2m1 2a1 1 0 1 1-2 0 1 1 0 0 1 2 0m2-2a1 1 0 1 0 0-2 1 1 0 0 0 0 2m1 2a1 1 0 1 1-2 0 1 1 0 0 1 2 0m2-2a1 1 0 1 0 0-2 1 1 0 0 0 0 2m4-5.5A2.5 2.5 0 0 0 14.5 3h-9A2.5 2.5 0 0 0 3 5.5v9A2.5 2.5 0 0 0 5.5 17h9a2.5 2.5 0 0 0 2.5-2.5zM4 7h12v7.5c0 .83-.67 1.5-1.5 1.5h-9A1.5 1.5 0 0 1 4 14.5zm1.5-3h9c.83 0 1.5.67 1.5 1.5V6H4v-.5C4 4.67 4.67 4 5.5 4"/></svg><svg class="fui-Icon fui-Icon-filled" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M5.5 3A2.5 2.5 0 0 0 3 5.5V6h14v-.5A2.5 2.5 0 0 0 14.5 3zM17 7H3v7.5A2.5 2.5 0 0 0 5.5 17h9a2.5 2.5 0 0 0 2.5-2.5zm-9 3a1 1 0 1 1-2 0 1 1 0 0 1 2 0m-1 4a1 1 0 1 1 0-2 1 1 0 0 1 0 2m4-4a1 1 0 1 1-2 0 1 1 0 0 1 2 0m-1 4a1 1 0 1 1 0-2 1 1 0 0 1 0 2m4-4a1 1 0 1 1-2 0 1 1 0 0 1 2 0"/></svg></span>
      予定表
    </a>
    <details class="fui-NavCategory">
      <summary class="fui-NavCategoryItem">
        <span class="fui-NavCategoryItem__icon"><svg class="fui-Icon fui-Icon-regular" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M1.91 7.38A8.5 8.5 0 0 1 3.7 4.3a.5.5 0 0 1 .54-.13l1.92.68a1 1 0 0 0 1.32-.76l.36-2a.5.5 0 0 1 .4-.4 9 9 0 0 1 3.55 0q.32.08.38.4l.37 2a1 1 0 0 0 1.32.76l1.92-.68a.5.5 0 0 1 .54.13 8.5 8.5 0 0 1 1.78 3.08q.08.31-.15.54l-1.56 1.32a1 1 0 0 0 0 1.52l1.56 1.32a.5.5 0 0 1 .15.54 8.5 8.5 0 0 1-1.78 3.08.5.5 0 0 1-.54.13l-1.92-.68a1 1 0 0 0-1.32.76l-.37 2a.5.5 0 0 1-.38.4 8.5 8.5 0 0 1-3.56 0 .5.5 0 0 1-.39-.4l-.36-2a1 1 0 0 0-1.32-.76l-1.92.68a.5.5 0 0 1-.54-.13 8.5 8.5 0 0 1-1.78-3.08.5.5 0 0 1 .15-.54l1.56-1.32a1 1 0 0 0 0-1.52L2.06 7.92a.5.5 0 0 1-.15-.54m1.06 0 1.3 1.1a2 2 0 0 1 0 3.04l-1.3 1.1q.45 1.19 1.25 2.16l1.6-.58a2 2 0 0 1 2.63 1.53l.3 1.67a8 8 0 0 0 2.5 0l.3-1.67a2 2 0 0 1 2.64-1.53l1.6.58a8 8 0 0 0 1.24-2.16l-1.3-1.1a2 2 0 0 1 0-3.04l1.3-1.1a8 8 0 0 0-1.25-2.16l-1.6.58a2 2 0 0 1-2.63-1.53l-.3-1.67a8 8 0 0 0-2.5 0l-.3 1.67A2 2 0 0 1 5.81 5.8l-1.6-.58a8 8 0 0 0-1.24 2.16M7.5 10a2.5 2.5 0 1 1 5 0 2.5 2.5 0 0 1-5 0m1 0a1.5 1.5 0 1 0 3 0 1.5 1.5 0 0 0-3 0"/></svg><svg class="fui-Icon fui-Icon-filled" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M1.91 7.38A8.5 8.5 0 0 1 3.7 4.3a.5.5 0 0 1 .54-.13l1.92.68a1 1 0 0 0 1.32-.76l.36-2a.5.5 0 0 1 .4-.4 9 9 0 0 1 3.55 0q.32.08.38.4l.37 2a1 1 0 0 0 1.32.76l1.92-.68a.5.5 0 0 1 .54.13 8.5 8.5 0 0 1 1.78 3.08q.08.31-.15.54l-1.56 1.32a1 1 0 0 0 0 1.52l1.56 1.32a.5.5 0 0 1 .15.54 8.5 8.5 0 0 1-1.78 3.08.5.5 0 0 1-.54.13l-1.92-.68a1 1 0 0 0-1.32.76l-.37 2a.5.5 0 0 1-.38.4 8.5 8.5 0 0 1-3.56 0 .5.5 0 0 1-.39-.4l-.36-2a1 1 0 0 0-1.32-.76l-1.92.68a.5.5 0 0 1-.54-.13 8.5 8.5 0 0 1-1.78-3.08.5.5 0 0 1 .15-.54l1.56-1.32a1 1 0 0 0 0-1.52L2.06 7.92a.5.5 0 0 1-.15-.54M8 10a2 2 0 1 0 4 0 2 2 0 0 0-4 0"/></svg></span>
        設定
        <span class="fui-NavCategoryItem__expandIcon" aria-hidden="true"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M15.85 7.65c.2.2.2.5 0 .7l-5.46 5.49a.55.55 0 0 1-.78 0L4.15 8.35a.5.5 0 1 1 .7-.7L10 12.8l5.15-5.16c.2-.2.5-.2.7 0"/></svg></span>
      </summary>
      <div class="fui-NavSubItemGroup">
        <a class="fui-NavSubItem" href="#" aria-current="false">アカウント</a>
        <a class="fui-NavSubItem" href="#" aria-current="false">通知</a>
      </div>
    </details>
    <div class="fui-Divider fui-NavDivider" role="separator" aria-orientation="horizontal" data-appearance="strong"></div>
    <a class="fui-NavItem" href="#" aria-current="false">ヘルプ</a>
  </div>
</nav>
```

```html demo
<nav class="fui-NavDrawer" aria-label="密度 small" data-density="small" data-fui-enhance style="height: 260px">
  <div class="fui-NavDrawerBody">
    <a class="fui-NavItem" href="#" aria-current="false">受信トレイ</a>
    <details class="fui-NavCategory" open>
      <summary class="fui-NavCategoryItem">
        フォルダー
        <span class="fui-NavCategoryItem__expandIcon" aria-hidden="true"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M15.85 7.65c.2.2.2.5 0 .7l-5.46 5.49a.55.55 0 0 1-.78 0L4.15 8.35a.5.5 0 1 1 .7-.7L10 12.8l5.15-5.16c.2-.2.5-.2.7 0"/></svg></span>
      </summary>
      <div class="fui-NavSubItemGroup">
        <a class="fui-NavSubItem" href="#" aria-current="page">下書き</a>
        <a class="fui-NavSubItem" href="#" aria-current="false">送信済み</a>
      </div>
    </details>
  </div>
</nav>
```

### v9 との差と未確認の点

- カテゴリーは `<details>` で作った。v9 は `button` の `aria-expanded` と、閉じると DOM から外す Collapse である。
- NavSubItemGroup は `overflow: hidden` で、NavSubItem のインジケーターは項目の外へ 6px 出る。この CSS をブラウザーで描くと、NavSubItem のインジケーターは切れて見えない（閉じたカテゴリーへ移ったインジケーターは見える）。v9 の値をそのまま写した結果だが、v9 の実際の描画では確かめていない。v9 で見えているなら、Collapse の動きの要素など、ここで写していない規則が関わっている。
- NavDrawerFooter の 5 値の padding を Griffel がどう出力するかは確かめていない。
- NavDrawerHeader の Hamburger は Button の部品である。CSS には `fui-Hamburger` の背景の規則だけを置いた（`[nav]Hamburger/useHamburgerStyles.styles.ts:18-30`）。Button の CSS（第 10 章）と `fui-Button fui-Hamburger` の形で併用する。
- NavDivider は v9 では `appearance: 'strong'` の Divider である（`[nav]NavDivider/useNavDivider.ts:17`）。線は Divider の CSS（第 13 章）が引き、`colorNeutralStroke1` になる。マークアップは `div.fui-Divider.fui-NavDivider` に `data-appearance="strong"` を付ける。以前の `<hr class="fui-NavDivider">` も近似の線（`colorNeutralStroke2`）で描けるが、v9 の色と違う。`tools/verify/compare-b.html` の比較（2026-11-13）で、Divider の形が線の色・太さ・位置で一致した。
- v9 の NavDrawer は InlineDrawer、NavDrawerBody は DrawerBody の上に作られ、DOM には `fui-InlineDrawer`、`fui-Drawer`、`fui-DrawerBody` の class も付く。ここでは `fui-NavDrawer` と `fui-NavDrawerBody` だけを書く。寸法と色は一致した（`tools/verify/compare-b.html` の比較（2026-11-13））。
- NavCategoryItem のシェブロンの span に、v9 は `display` を書かない（`[nav]NavCategoryItem/useNavCategoryItem.styles.ts:23-27`）。flex の子なので block になり、中の SVG はインラインのままである。CSS もこれに合わせた（以前は `inline-flex`）。
- AppItem、SplitNavItem、NavDrawer のオーバーレイと開閉の動きは扱っていない。

## Breadcrumb

略記: `[bc]` = `packages/react-components/react-breadcrumb/library/src/components/`、`[btn]` = `packages/react-components/react-button/library/src/components/Button/`

### 概要と使い分け（Do / Don't）

Breadcrumb は、サイトやアプリの階層での現在地を示し、上の階層へすぐ戻れるようにする二次的なナビゲーションである。

- Do: 他のナビゲーションと必ず併用する。名前はページのタイトルに合わせ、閲覧の履歴ではなく階層を示す。
- Do: 入りきらないときは、2 番目から中間の項目をオーバーフローのメニューにまとめ、最初と最後を残す。
- Do: 幅は面の 30〜50% を目安にする（ドロワーなど二次的な面では全幅でよい）。ラベルが長いときは省略し、全体をツールチップで示す（サイトの指針）。
- Don't: 唯一のナビゲーションにする。文字を折り返す。ツールチップに長い文を入れる。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

| 部品 | 要素 | ARIA | class | 出典 |
|---|---|---|---|---|
| Breadcrumb | `nav` | `aria-label`（v9 の既定は `"breadcrumb"`） | `fui-Breadcrumb` | `[bc]Breadcrumb/useBreadcrumb.ts:49-58` |
| list | `ol` | `role="list"` | `fui-Breadcrumb__list` | `[bc]Breadcrumb/useBreadcrumb.ts:50, 60` |
| BreadcrumbItem | `li` | なし | `fui-BreadcrumbItem` | `[bc]BreadcrumbItem/useBreadcrumbItem.ts:47-53` |
| BreadcrumbDivider | `li` | `aria-hidden="true"` | `fui-BreadcrumbDivider` | `[bc]BreadcrumbDivider/useBreadcrumbDivider.tsx:49-66` |
| BreadcrumbButton | `href` があれば `a`、なければ `button` | 現在の項目は `aria-current="page"` と `aria-disabled="true"` | `fui-BreadcrumbButton`、`fui-BreadcrumbButton__icon` | `[bc]BreadcrumbButton/useBreadcrumbButton.ts:46-71` |

- 区切りは `ChevronRightRegular`（RTL は `ChevronLeftRegular`）である（`[bc]BreadcrumbDivider/useBreadcrumbDivider.tsx:73-75`）。CSS は RTL で右向きの形を左右反転する。
- 現在の項目の `aria-disabled="true"` は、disabled の見た目にしない。v9 は Button の `disabled` を渡していないからである。disabled の見た目にするのは、`:disabled` か、`aria-current` のない `aria-disabled="true"`（v9 の `disabledFocusable`）である。
- キーボード: 既定の `focusMode="tab"` は Tab キーで項目を移る。`focusMode="arrow"` は矢印キーのグループになる（`[bc]Breadcrumb/Breadcrumb.types.ts:33-35`）。`navigation.js` は arrow を扱わない。

### バリエーション

| 属性（Breadcrumb に付ける） | 値 | 既定 | v9 の prop | 出典 |
|---|---|---|---|---|
| `data-size` | `small` / `medium` / `large` | `medium` | `size` | `[bc]Breadcrumb/Breadcrumb.types.ts:40-42` |

BreadcrumbButton は、Button の `appearance="subtle"`、`shape="rounded"`、Breadcrumb の size で描く（`[bc]BreadcrumbButton/useBreadcrumbButton.ts:28-36`）。CSS は Button の CSS に頼らず、Button の規則に Breadcrumb の規則を後ろから重ねた結果を、`fui-BreadcrumbButton` だけで書いている。

### 寸法（size ごとの表）

| 項目 | small | medium | large | 出典 |
|---|---|---|---|---|
| ボタンの高さ | 24px | 32px | 40px | `[bc]BreadcrumbButton/useBreadcrumbButtonStyles.styles.ts:72-86` |
| padding（全辺） | 6px（`spacingHorizontalSNudge`） | 6px | 8px（`spacingHorizontalS`） | 同 75, 80, 85 |
| 文字（通常） | `caption1` | `body1` | `body2` | 同 74, 79, 84 |
| 文字（現在） | `caption1Strong` | `body1Strong` | `subtitle2` | 同 98-106 |
| アイコン | 12px、line-height `lineHeightBase200` | 16px、`lineHeightBase400` | 20px、`lineHeightBase600` | 同 26-46 |
| アイコンの後ろの余白 | 4px（`spacingHorizontalXS`） | 同左 | 同左 | 同 32 |
| 区切りのアイコン | 12px | 16px | 20px | `[bc]BreadcrumbDivider/useBreadcrumbDividerStyles.styles.ts:18-28` |
| 角丸 | `borderRadiusMedium` | 同左 | 同左 | `[btn]useButtonStyles.styles.ts:65, 294, 310` |
| フォーカスの角丸 | `borderRadiusSmall` | `borderRadiusMedium` | `borderRadiusLarge` | `[btn]useButtonStyles.styles.ts:105-114, 495-499` |

- ボタンは `min-width: unset; text-wrap: nowrap`（`[bc]BreadcrumbButton/useBreadcrumbButtonStyles.styles.ts:68-71`）。Button の 1px の枠は subtle で透明になり、高さに含まれる。
- list は `display: flex; align-items: center` で、項目の間に gap はない（`[bc]Breadcrumb/useBreadcrumbStyles.styles.ts:12-18`）。

### 色と状態（トークン名の表）

| 状態 | 背景 | 文字 | アイコン | 出典 |
|---|---|---|---|---|
| rest | `colorSubtleBackground` | `colorNeutralForeground2` | （文字と同じ） | `[btn]useButtonStyles.styles.ts:190-193` |
| hover | `colorSubtleBackgroundHover` | `colorNeutralForeground2Hover` | `colorNeutralForeground2BrandHover`、Filled に替わる | 同 195-208 |
| pressed | `colorSubtleBackgroundPressed` | `colorNeutralForeground2Pressed` | `colorNeutralForeground2BrandPressed` | 同 210-223 |
| 現在 | rest は通常と同じ（太字）。hover・pressed も `colorTransparentBackground` のまま | `colorNeutralForeground2`、`cursor: auto` | `color: unset`、Regular のまま | `[bc]BreadcrumbButton/useBreadcrumbButtonStyles.styles.ts:48-65, 87-97` |
| disabled | `colorTransparentBackground`、枠も透明 | `colorNeutralForegroundDisabled`、`cursor: not-allowed` | `colorNeutralForegroundDisabled` | `[btn]useButtonStyles.styles.ts:322-369, 434-447` |

BreadcrumbItem の文字は `colorNeutralForeground2`（`[bc]BreadcrumbItem/useBreadcrumbItemStyles.styles.ts:12-18`）。区切りの色はこれを受け継ぐ。

### フォーカス・動き・ハイコントラスト

- フォーカス: Button の規則を受け継ぐ。`border-color: var(--colorStrokeFocus2)`、`border-width: 1px`、透明の 2px の outline、`box-shadow: 0 0 0 1px var(--colorStrokeFocus2) inset`、`z-index: 1`（`[btn]useButtonStyles.styles.ts:105-114`）。Firefox では box-shadow の太さを 0.25px 足す（116-123）。
- 動き: `transition-property: background, border, color` を `durationFaster`、`curveEasyEase` で。`@media screen and (prefers-reduced-motion: reduce)` で 0.01ms（73-79）。
- ハイコントラスト: ホバーと押下で文字とアイコンを `Highlight` にする（225-240）。disabled は背景 `ButtonFace`、枠と文字 `GrayText`（372-405）。

### 実装の例

```html demo
<nav class="fui-Breadcrumb" aria-label="パンくずリスト">
  <ol class="fui-Breadcrumb__list" role="list">
    <li class="fui-BreadcrumbItem">
      <a class="fui-BreadcrumbButton" href="#">
        <span class="fui-BreadcrumbButton__icon"><svg class="fui-Icon fui-Icon-regular" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9 2.39a1.5 1.5 0 0 1 2 0l5.5 4.94c.32.28.5.69.5 1.12v7.05c0 .83-.67 1.5-1.5 1.5H13a1.5 1.5 0 0 1-1.5-1.5V12a.5.5 0 0 0-.5-.5H9a.5.5 0 0 0-.5.5v3.5c0 .83-.67 1.5-1.5 1.5H4.5A1.5 1.5 0 0 1 3 15.5V8.45c0-.43.18-.84.5-1.12zm1.33.74a.5.5 0 0 0-.66 0l-5.5 4.94a.5.5 0 0 0-.17.38v7.05c0 .28.22.5.5.5H7a.5.5 0 0 0 .5-.5V12c0-.83.67-1.5 1.5-1.5h2c.83 0 1.5.67 1.5 1.5v3.5c0 .28.22.5.5.5h2.5a.5.5 0 0 0 .5-.5V8.45a.5.5 0 0 0-.17-.38z"/></svg><svg class="fui-Icon fui-Icon-filled" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M11 2.39a1.5 1.5 0 0 0-2 0L3.5 7.33c-.32.28-.5.69-.5 1.12v7.05c0 .83.67 1.5 1.5 1.5h2c.83 0 1.5-.67 1.5-1.5v-4c0-.28.22-.5.5-.5h3c.28 0 .5.22.5.5v4c0 .83.67 1.5 1.5 1.5h2c.83 0 1.5-.67 1.5-1.5V8.45c0-.43-.18-.84-.5-1.12z"/></svg></span>
        ホーム
      </a>
    </li>
    <li class="fui-BreadcrumbDivider" aria-hidden="true"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7.65 4.15c.2-.2.5-.2.7 0l5.49 5.46c.21.22.21.57 0 .78l-5.49 5.47a.5.5 0 0 1-.7-.71L12.8 10 7.65 4.85a.5.5 0 0 1 0-.7"/></svg></li>
    <li class="fui-BreadcrumbItem"><a class="fui-BreadcrumbButton" href="#">ドキュメント</a></li>
    <li class="fui-BreadcrumbDivider" aria-hidden="true"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7.65 4.15c.2-.2.5-.2.7 0l5.49 5.46c.21.22.21.57 0 .78l-5.49 5.47a.5.5 0 0 1-.7-.71L12.8 10 7.65 4.85a.5.5 0 0 1 0-.7"/></svg></li>
    <li class="fui-BreadcrumbItem"><button class="fui-BreadcrumbButton" type="button" aria-disabled="true">共有</button></li>
    <li class="fui-BreadcrumbDivider" aria-hidden="true"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7.65 4.15c.2-.2.5-.2.7 0l5.49 5.46c.21.22.21.57 0 .78l-5.49 5.47a.5.5 0 0 1-.7-.71L12.8 10 7.65 4.85a.5.5 0 0 1 0-.7"/></svg></li>
    <li class="fui-BreadcrumbItem"><button class="fui-BreadcrumbButton" type="button" aria-current="page" aria-disabled="true">報告書</button></li>
  </ol>
</nav>
```

```html demo
<div style="display: grid; gap: 8px">
  <nav class="fui-Breadcrumb" aria-label="small のパンくずリスト" data-size="small">
    <ol class="fui-Breadcrumb__list" role="list">
      <li class="fui-BreadcrumbItem"><a class="fui-BreadcrumbButton" href="#">ホーム</a></li>
      <li class="fui-BreadcrumbDivider" aria-hidden="true"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7.65 4.15c.2-.2.5-.2.7 0l5.49 5.46c.21.22.21.57 0 .78l-5.49 5.47a.5.5 0 0 1-.7-.71L12.8 10 7.65 4.85a.5.5 0 0 1 0-.7"/></svg></li>
      <li class="fui-BreadcrumbItem"><button class="fui-BreadcrumbButton" type="button" aria-current="page" aria-disabled="true">設定</button></li>
    </ol>
  </nav>
  <nav class="fui-Breadcrumb" aria-label="large のパンくずリスト" data-size="large">
    <ol class="fui-Breadcrumb__list" role="list">
      <li class="fui-BreadcrumbItem"><a class="fui-BreadcrumbButton" href="#">ホーム</a></li>
      <li class="fui-BreadcrumbDivider" aria-hidden="true"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7.65 4.15c.2-.2.5-.2.7 0l5.49 5.46c.21.22.21.57 0 .78l-5.49 5.47a.5.5 0 0 1-.7-.71L12.8 10 7.65 4.85a.5.5 0 0 1 0-.7"/></svg></li>
      <li class="fui-BreadcrumbItem"><button class="fui-BreadcrumbButton" type="button" aria-current="page" aria-disabled="true">設定</button></li>
    </ol>
  </nav>
</div>
```

### v9 との差と未確認の点

- v9 の DOM では、BreadcrumbButton は `fui-Button` と `fui-BreadcrumbButton` の両方を持つ。アイコンの span には `fui-Button__icon` が付き、`fui-BreadcrumbButton__icon` は定義だけで付かない（`[bc]BreadcrumbButton/useBreadcrumbButtonStyles.styles.ts:13-16, 131-134`）。React を使わない HTML では約束の名付けに合わせ、`fui-BreadcrumbButton__icon` を使う。
- ハイコントラストのホバーで、Button の土台は背景を `HighlightText` にするが、subtle の背景の規則がこれに勝つ（Griffel の重ね順からの推論）。CSS もこの順に書いた。ブラウザーで確かめていない。
- オーバーフローのメニュー、ツールチップでの省略、`focusMode="arrow"` は扱っていない。

## Accordion

略記: `[acc]` = `packages/react-components/react-accordion/library/src/components/`

### 概要と使い分け（Do / Don't）

Accordion は、関連する内容を開閉できる区画にまとめる。見る内容を利用者が選べる（FAQ のような使い方）。

- Do: 補足や任意の情報に使う。既定ではすべて閉じ、自動で見せたい項目だけ最初から開く。
- Do: 見出しは短く、中身を示す。シェブロンの位置（先頭か末尾）を体験の全体でそろえる。
- Don't: 今の作業に必須の情報を入れる。ある項目から別の項目の情報を参照させる。見出しを折り返す。シェブロンの位置を混ぜる。
- 既定では 1 つ開くと他が閉じる。複数を開けるのは、利用者が混乱しない場合だけにする。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

| 部品 | 要素 | ARIA | class | 出典 |
|---|---|---|---|---|
| Accordion | `div` | なし | `fui-Accordion` | `[acc]Accordion/useAccordion.ts:78-85` |
| AccordionItem | `div`（形 A は `details`） | なし | `fui-AccordionItem` | `[acc]AccordionItem/useAccordionItem.ts:30-38` |
| AccordionHeader | `div` または `h1`〜`h6`（形 A にはない） | なし | `fui-AccordionHeader` | `[acc]AccordionHeader/useAccordionHeader.tsx:100-110` |
| button | `button type="button"`（形 A は `summary`） | `aria-expanded` | `fui-AccordionHeader__button` | `[acc]AccordionHeader/useAccordionHeader.tsx:77-82` |
| expandIcon | `span`、`aria-hidden`。`ChevronRightRegular` を回す | なし | `fui-AccordionHeader__expandIcon` | 同 13, 42-51, 113-119 |
| icon | `div` | なし | `fui-AccordionHeader__icon` | 同 103, 112 |
| AccordionPanel | `div`。閉じている間は `inert` | なし | `fui-AccordionPanel` | `[acc]AccordionPanel/useAccordionPanel.ts:67-78` |

2 つの形を使える。

- 形 A（推奨）: `<details class="fui-AccordionItem">` の `<summary class="fui-AccordionHeader__button">`。CSS だけで開閉する。修飾の属性は `summary` に付ける。`summary` の中の見出しは、支援技術によっては見出しとして伝わらない。
- 形 B（v9 と同じ構造）: `<h3 class="fui-AccordionHeader">` の中の `<button class="fui-AccordionHeader__button" aria-expanded aria-controls>` と、`hidden` のパネル。修飾は AccordionHeader に付ける。開閉は `navigation.js` が行う。見出しの意味が要るときはこちらを使う。

子の順は、start のシェブロン、icon、文字、end のシェブロンである（`[acc]AccordionHeader/renderAccordionHeader.tsx:26-29`）。v9 は `aria-controls` と `role="region"` を付けない。

キーボード: ボタンの既定（Tab で移り、Enter と Space で開閉）である。矢印キーの `navigation` は非推奨（`[acc]Accordion/Accordion.types.ts:45-48`）。

開閉の決まり: v9 の既定は `multiple: false`（1 つ開くと他が閉じる）、`collapsible: false`（開いている唯一の項目は閉じられない）である（`[acc]Accordion/useAccordion.ts:55-56`）。形 A では同じ `name` を付けると 1 つだけ開く。`collapsible: false` は `<details>` では表せないので、Accordion に `data-fui-enhance` を付けると `navigation.js` が再現する。閉じられるようにするには `data-collapsible`、複数を開くには `data-multiple` を付ける。

### バリエーション

| 属性 | 値 | 既定 | v9 の prop | 出典 |
|---|---|---|---|---|
| `data-size` | `small` / `medium` / `large` / `extra-large` | `medium` | `size` | `[acc]AccordionHeader/AccordionHeader.types.ts:5`、`useAccordionHeader.tsx:28` |
| `data-expand-icon-position` | `start` / `end` | `start` | `expandIconPosition` | `[acc]AccordionHeader/AccordionHeader.types.ts:6` |
| `data-inline` | 有無 | なし | `inline` | `[acc]AccordionHeader/useAccordionHeader.tsx:28` |
| `data-multiple`（Accordion、JS） | 有無 | なし | `multiple` | `[acc]Accordion/useAccordion.ts:55` |
| `data-collapsible`（Accordion、JS） | 有無 | なし | `collapsible` | `[acc]Accordion/useAccordion.ts:56` |

### 寸法（size ごとの表）

出典は `[acc]AccordionHeader/useAccordionHeaderStyles.styles.ts`。

| size | 最小の高さ | 文字の大きさ / 行の高さ | 行 |
|---|---|---|---|
| small | 32px | `fontSizeBase200` 12px / `lineHeightBase300` 20px（行の高さは変えない） | 56-59 |
| medium | 44px | `fontSizeBase300` 14px / `lineHeightBase300` 20px（`body1`） | 49, 53 |
| large | 44px | `fontSizeBase400` 16px / `lineHeightBase400` 22px | 60-63 |
| extra-large | 44px | `fontSizeBase500` 20px / `lineHeightBase500` 28px | 64-67 |

| 項目 | 値 | 行 |
|---|---|---|
| button の padding | 先頭 10px（`spacingHorizontalMNudge`）、末尾 12px（`spacingHorizontalM`）、上下 0 | 48 |
| end のとき | 末尾 10px。icon がなければ先頭 12px | 71-76, 126-127 |
| expandIcon | 20px（`fontSizeBase500`）、`line-height: var(--lineHeightBase500)`。start は後ろに 8px（`spacingHorizontalS`）、end は前に 8px で末尾に寄せる | 80-97 |
| icon | 20px、後ろに 8px | 98-105 |
| header の角丸 | `borderRadiusMedium` | 35 |
| inline | header は `inline-block`、button は `inline-flex` | 41-43, 68-70 |
| Panel | 左右の margin 12px（`spacingHorizontalM`） | `[acc]AccordionPanel/useAccordionPanelStyles.styles.ts:8-12` |

### 色と状態（トークン名の表）

| 状態 | 背景 | 文字 | 出典 |
|---|---|---|---|
| rest | `colorTransparentBackground` | `colorNeutralForeground1` | 31-36 |
| hover・pressed | 指定なし（変わらない） | 指定なし | — |
| disabled | `background-image: none` | `colorNeutralForegroundDisabled`、`cursor: not-allowed` | 37-40, 77-79 |

形 A にはヘッダーの root がないので、文字の色は親から受け継ぐ（ふつうは `colorNeutralForeground1`）。disabled の色は `summary` に直接付ける。

### フォーカス・動き・ハイコントラスト

- フォーカス: 引数なしの `createFocusOutlineStyle()` である（30）。`::after` に 2px の `colorStrokeFocus2` の枠を、要素の外へ 2px 広げて描く。角丸は `borderRadiusMedium`（`packages/react-components/react-tabster/src/focus/createFocusOutlineStyle.ts:55-112`）。
- シェブロン: v9 はインラインの style で `transform: rotate()` と `transition: transform 200ms ease-out` を付ける（`ease-out` は直書き。`[acc]AccordionHeader/useAccordionHeader.tsx:32-51`）。start は閉 0°（RTL は 180°）から開 90°、end は閉 90° から開 −90° である。
- パネル: v9 は Collapse（高さと opacity を 200ms、`curveEasyEaseMax`、`[acc]AccordionPanel/useAccordionPanel.ts:42-48`）。形 A では `::details-content` と `interpolate-size` で近似する。形 B は動かない。
- ハイコントラスト: フォーカスの枠を `Highlight` にする規則だけがある。

### 実装の例

```html demo
<div class="fui-Accordion" data-fui-enhance>
  <details class="fui-AccordionItem" name="n14-faq" open>
    <summary class="fui-AccordionHeader__button">
      <span class="fui-AccordionHeader__expandIcon" aria-hidden="true"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7.65 4.15c.2-.2.5-.2.7 0l5.49 5.46c.21.22.21.57 0 .78l-5.49 5.47a.5.5 0 0 1-.7-.71L12.8 10 7.65 4.85a.5.5 0 0 1 0-.7"/></svg></span>
      料金について
    </summary>
    <div class="fui-AccordionPanel"><p>月ごとの料金と、年ごとの割引を説明する。</p></div>
  </details>
  <details class="fui-AccordionItem" name="n14-faq">
    <summary class="fui-AccordionHeader__button">
      <span class="fui-AccordionHeader__expandIcon" aria-hidden="true"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7.65 4.15c.2-.2.5-.2.7 0l5.49 5.46c.21.22.21.57 0 .78l-5.49 5.47a.5.5 0 0 1-.7-.71L12.8 10 7.65 4.85a.5.5 0 0 1 0-.7"/></svg></span>
      解約の手続き
    </summary>
    <div class="fui-AccordionPanel"><p>設定の画面からいつでも解約できる。</p></div>
  </details>
  <details class="fui-AccordionItem" name="n14-faq">
    <summary class="fui-AccordionHeader__button" aria-disabled="true">
      <span class="fui-AccordionHeader__expandIcon" aria-hidden="true"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7.65 4.15c.2-.2.5-.2.7 0l5.49 5.46c.21.22.21.57 0 .78l-5.49 5.47a.5.5 0 0 1-.7-.71L12.8 10 7.65 4.85a.5.5 0 0 1 0-.7"/></svg></span>
      準備中の項目
    </summary>
    <div class="fui-AccordionPanel"><p>まだ内容がない。</p></div>
  </details>
</div>
```

```html demo
<div class="fui-Accordion" data-fui-enhance data-multiple data-collapsible>
  <details class="fui-AccordionItem">
    <summary class="fui-AccordionHeader__button" data-expand-icon-position="end" data-size="large">
      末尾のシェブロン（large）
      <span class="fui-AccordionHeader__expandIcon" aria-hidden="true"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7.65 4.15c.2-.2.5-.2.7 0l5.49 5.46c.21.22.21.57 0 .78l-5.49 5.47a.5.5 0 0 1-.7-.71L12.8 10 7.65 4.85a.5.5 0 0 1 0-.7"/></svg></span>
    </summary>
    <div class="fui-AccordionPanel"><p>複数を同時に開け、すべて閉じることもできる。</p></div>
  </details>
  <details class="fui-AccordionItem">
    <summary class="fui-AccordionHeader__button" data-expand-icon-position="end" data-size="small">
      末尾のシェブロン（small）
      <span class="fui-AccordionHeader__expandIcon" aria-hidden="true"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7.65 4.15c.2-.2.5-.2.7 0l5.49 5.46c.21.22.21.57 0 .78l-5.49 5.47a.5.5 0 0 1-.7-.71L12.8 10 7.65 4.85a.5.5 0 0 1 0-.7"/></svg></span>
    </summary>
    <div class="fui-AccordionPanel"><p>small は最小の高さが 32px になる。</p></div>
  </details>
</div>
```

```html demo
<div class="fui-Accordion" data-fui-enhance data-collapsible>
  <div class="fui-AccordionItem">
    <h3 class="fui-AccordionHeader">
      <button class="fui-AccordionHeader__button" type="button" id="n14-acc-b1" aria-expanded="false" aria-controls="n14-acc-p1">
        <span class="fui-AccordionHeader__expandIcon" aria-hidden="true"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7.65 4.15c.2-.2.5-.2.7 0l5.49 5.46c.21.22.21.57 0 .78l-5.49 5.47a.5.5 0 0 1-.7-.71L12.8 10 7.65 4.85a.5.5 0 0 1 0-.7"/></svg></span>
        見出しの意味を持つ形（形 B）
      </button>
    </h3>
    <div class="fui-AccordionPanel" id="n14-acc-p1" hidden><p>h3 の中の button が aria-expanded で開閉を伝える。</p></div>
  </div>
</div>
```

### v9 との差と未確認の点

- 形 A は `<details>` の動きを使うので、v9 の `inert` と Collapse の代わりに、ブラウザーの開閉と `::details-content` の近似を使う。
- 形 B では、`h3` の既定の margin と文字の大きさを `fui-AccordionHeader` が `margin: 0` で消すが、`font-size` は button の規則が決める。
- `disabledFocusable`（最後の 1 つを閉じられないときのボタンの状態、`[acc]AccordionHeader/useAccordionHeader.tsx` の `useAccordionHeaderBase_unstable`）の見た目は再現していない。`navigation.js` は閉じる操作を止めるだけである。
- Web Components v3 は見出しの高さを 44px に固定し、左右の padding が v9 と逆である（`packages/web-components/src/accordion-item/accordion-item.styles.ts:36-39`）。ここでは v9 を採った。

## Tree

略記: `[tree]` = `packages/react-components/react-tree/library/src/`

### 概要と使い分け（Do / Don't）

Tree は、入れ子の階層のデータ（メニュー、フォルダー、入れ子のカテゴリー）を一目で示す。

- Do: 親になれる項目（枝）と末端の項目（葉）を組み合わせる。ラベルは短く、兄弟の間で文法をそろえる。Tree には `aria-label` で名前を付ける。
- Do: アイコンは単純で分かりやすいものにする。クイック操作は 1〜2 個にし、ツールバーやメニューからも使えるようにする。
- Don't: 階層に関係なく内容を開閉するだけのために使う（Accordion を使う）。入れ子のない情報に使う（List か Table を使う）。
- 長いラベルは既定で折り返す。省略するなら、区別できる語を先頭に置き、ツールチップで全体を示す。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

| 部品 | 要素 | role・ARIA | class | 出典 |
|---|---|---|---|---|
| Tree（ルート） | `div` | `role="tree"`、`aria-label` | `fui-Tree` | `[tree]hooks/useRootTree.ts:101` |
| Tree（子の木） | `div` | `role="group"` | `fui-Tree` | `[tree]hooks/useSubtree.ts:38` |
| TreeItem | `div`、ローヴィングで 1 つだけ `tabindex="0"` | `role="treeitem"`、`aria-level`、枝は `aria-expanded` | `fui-TreeItem` | `[tree]components/TreeItem/useTreeItem.tsx:331-340` |
| TreeItemLayout | `div` | なし | `fui-TreeItemLayout` | `[tree]components/TreeItemLayout/useTreeItemLayoutStyles.styles.ts:11-20` |
| expandIcon | `div`、`aria-hidden`。枝だけ。`ChevronRight12Regular` | なし | `fui-TreeItemLayout__expandIcon` | `[tree]components/TreeItemLayout/useTreeItemLayout.tsx:287-292`、`[tree]components/TreeItemChevron.tsx:5, 16` |
| iconBefore・main・iconAfter・aside | `div`／`span` | なし | `fui-TreeItemLayout__iconBefore` ほか | 同 11-20 |
| actions | `div` | `role="toolbar"` | `fui-TreeItemLayout__actions` | `[tree]components/TreeItemLayout/useTreeItemLayout.tsx:310-314` |

- TreeItem の中に、TreeItemLayout と子の Tree を並べる。フォーカスを受けるのは TreeItem で、フォーカスの線は子の TreeItemLayout に描く。
- 枝と葉は `aria-expanded` の有無で分ける。CSS はこれで字下げとシェブロンを決める。
- 段は `aria-level` に書く。CSS は 1〜10 段を `--fluent-TreeItem--level` に変える（v9 も 1〜10 段を class で付ける、`[tree]components/TreeItem/useTreeItemStyles.styles.ts:53-60, 72-89`）。11 段以上は、要素の style に `--fluent-TreeItem--level` を書く。
- キーボード: 上下の矢印、左右の矢印（開閉と親子の移動）、Home、End、Enter と、先頭の文字での移動である（`[tree]utils/tokens.ts:1, 11-25`）。`navigation.js` がこれを行う。
- 選択（`selectionMode`）は Checkbox や Radio で示し、Tree 自身の色は変わらない。この章では扱わない。

### バリエーション

| 属性（ルートの Tree に付ける） | 値 | 既定 | v9 の prop | 出典 |
|---|---|---|---|---|
| `data-appearance` | `subtle` / `subtle-alpha` / `transparent` | `subtle` | `appearance` | `[tree]components/Tree/Tree.types.ts:108-115`、`useTree.ts:31` |
| `data-size` | `small` / `medium` | `medium` | `size` | `[tree]components/Tree/Tree.types.ts:116-120` |

### 寸法（size ごとの表）

出典は `[tree]components/TreeItemLayout/useTreeItemLayoutStyles.styles.ts`。

| 項目 | medium | small | 行 |
|---|---|---|---|
| 行の最小の高さ | 32px | 24px | 25, 59-62 |
| 文字 | `body1` | `caption1` | 56-62 |
| iconBefore の後ろの余白 | 4px（`spacingHorizontalXS`） | 2px（`spacingHorizontalXXS`） | 140-147 |
| iconAfter の前の余白 | 4px | 2px | 149-156 |

| 項目 | 値 | 出典 |
|---|---|---|
| 字下げ（葉） | 先頭の padding = 段 × 24px（`spacingHorizontalXXL`） | 50-52 |
| 字下げ（枝） | 先頭の padding = (段 − 1) × 24px。シェブロンの幅 24px の分で葉と文字がそろう（計算） | 53-55 |
| expandIcon | 最小の幅 24px、上下の padding 4px、`colorNeutralForeground3`、アイコン 12px | 111-120 |
| main | 左右の padding 2px | 125-127 |
| iconBefore・iconAfter | 20px（`fontSizeBase500`）、`colorNeutralForeground2` | 132-138 |
| aside | 先頭を `auto` で寄せ、左右 12px、gap 4px | 98-106 |
| actions | 先頭を `auto` で寄せ、左右 8px、`z-index: 1` | 87-94 |
| Tree | `display: flex; flex-direction: column; row-gap: 2px`。子の木は上に 2px | `[tree]components/Tree/useTreeStyles.styles.ts:8-18` |

字下げは size で変わらない。

### 色と状態（トークン名の表）

| 状態 | 背景（subtle / subtle-alpha / transparent） | 文字 | シェブロン | 出典 |
|---|---|---|---|---|
| rest | TreeItem の `colorSubtleBackground` / 同 / Layout が `colorTransparentBackground` | `colorNeutralForeground2` | `colorNeutralForeground3` | `[tree]components/TreeItem/useTreeItemStyles.styles.ts:23-24`、Layout 73-74, 117 |
| hover | `colorSubtleBackgroundHover` / `colorSubtleBackgroundLightAlphaHover` / `colorTransparentBackgroundHover` | `colorNeutralForeground2Hover` | `colorNeutralForeground3Hover` | Layout 28-35, 65-68, 75-77 |
| pressed | `colorSubtleBackgroundPressed` / `colorSubtleBackgroundLightAlphaPressed` / `colorTransparentBackgroundPressed` | `colorNeutralForeground2Pressed` | `colorNeutralForeground3Pressed` | Layout 36-43, 69-71, 78-80 |

選択と disabled の色はない。行の角丸は、フォーカスのときだけ付く。

### フォーカス・動き・ハイコントラスト

- フォーカス: TreeItem 自身の outline は消し、子の TreeItemLayout に `outline: 2px solid var(--colorStrokeFocus2)` と `border-radius: var(--borderRadiusMedium)` を付ける（`[tree]components/TreeItem/useTreeItemStyles.styles.ts:27-47`）。
- シェブロン: v9 はインラインの style で回す。閉 0°（RTL は 180°）から開 90°、`transition: transform 200ms curveEasyEaseMax`（`[tree]components/TreeItemChevron.tsx:14-30`）。
- 子の木: v9 は Collapse（200ms、`curveEasyEaseMax`、`[tree]components/Tree/useTree.ts:35-46`）で開閉し、閉じると DOM から外す。CSS は閉じた枝の子の木を `display: none` にするだけで、動きはない。
- 縮小モーションとハイコントラストの規則は、v9 の Tree にはない。

### 実装の例

```html demo
<div class="fui-Tree" role="tree" aria-label="ファイル" data-fui-enhance style="max-width: 320px">
  <div class="fui-TreeItem" role="treeitem" aria-level="1" aria-expanded="true" tabindex="0">
    <div class="fui-TreeItemLayout">
      <div class="fui-TreeItemLayout__expandIcon" aria-hidden="true"><svg class="fui-Icon" width="12" height="12" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true"><path d="M4.65 2.15a.5.5 0 0 0 0 .7L7.79 6 4.65 9.15a.5.5 0 1 0 .7.7l3.5-3.5a.5.5 0 0 0 0-.7l-3.5-3.5a.5.5 0 0 0-.7 0"/></svg></div>
      <div class="fui-TreeItemLayout__iconBefore"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M4.5 3A2.5 2.5 0 0 0 2 5.5v9A2.5 2.5 0 0 0 4.5 17h11a2.5 2.5 0 0 0 2.5-2.5v-7A2.5 2.5 0 0 0 15.5 5H9.7L8.23 3.51A1.8 1.8 0 0 0 6.98 3zM3 5.5C3 4.67 3.67 4 4.5 4h2.48q.32 0 .53.22L8.8 5.5 7.44 6.85a.5.5 0 0 1-.35.15H3zM3 8h4.09c.4 0 .78-.16 1.06-.44L9.7 6h5.79c.83 0 1.5.67 1.5 1.5v7c0 .83-.67 1.5-1.5 1.5h-11A1.5 1.5 0 0 1 3 14.5z"/></svg></div>
      <div class="fui-TreeItemLayout__main">ドキュメント</div>
      <div class="fui-TreeItemLayout__aside">3 件</div>
    </div>
    <div class="fui-Tree" role="group">
      <div class="fui-TreeItem" role="treeitem" aria-level="2" tabindex="-1">
        <div class="fui-TreeItemLayout">
          <div class="fui-TreeItemLayout__iconBefore"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M6 2a2 2 0 0 0-2 2v12c0 1.1.9 2 2 2h8a2 2 0 0 0 2-2V7.41c0-.4-.16-.78-.44-1.06l-3.91-3.91A1.5 1.5 0 0 0 10.59 2zM5 4a1 1 0 0 1 1-1h4v3.5c0 .83.67 1.5 1.5 1.5H15v8a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1zm9.8 3h-3.3a.5.5 0 0 1-.5-.5V3.2z"/></svg></div>
          <div class="fui-TreeItemLayout__main">報告書.docx</div>
        </div>
      </div>
      <div class="fui-TreeItem" role="treeitem" aria-level="2" aria-expanded="false" tabindex="-1">
        <div class="fui-TreeItemLayout">
          <div class="fui-TreeItemLayout__expandIcon" aria-hidden="true"><svg class="fui-Icon" width="12" height="12" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true"><path d="M4.65 2.15a.5.5 0 0 0 0 .7L7.79 6 4.65 9.15a.5.5 0 1 0 .7.7l3.5-3.5a.5.5 0 0 0 0-.7l-3.5-3.5a.5.5 0 0 0-.7 0"/></svg></div>
          <div class="fui-TreeItemLayout__main">古い資料</div>
        </div>
        <div class="fui-Tree" role="group">
          <div class="fui-TreeItem" role="treeitem" aria-level="3" tabindex="-1">
            <div class="fui-TreeItemLayout"><div class="fui-TreeItemLayout__main">2025 年度.xlsx</div></div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="fui-TreeItem" role="treeitem" aria-level="1" tabindex="-1">
    <div class="fui-TreeItemLayout"><div class="fui-TreeItemLayout__main">メモ.txt</div></div>
  </div>
</div>
```

```html demo
<div class="fui-Tree" role="tree" aria-label="small と transparent" data-size="small" data-appearance="transparent" data-fui-enhance style="max-width: 320px">
  <div class="fui-TreeItem" role="treeitem" aria-level="1" aria-expanded="true" tabindex="0">
    <div class="fui-TreeItemLayout">
      <div class="fui-TreeItemLayout__expandIcon" aria-hidden="true"><svg class="fui-Icon" width="12" height="12" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true"><path d="M4.65 2.15a.5.5 0 0 0 0 .7L7.79 6 4.65 9.15a.5.5 0 1 0 .7.7l3.5-3.5a.5.5 0 0 0 0-.7l-3.5-3.5a.5.5 0 0 0-.7 0"/></svg></div>
      <div class="fui-TreeItemLayout__main">プロジェクト</div>
    </div>
    <div class="fui-Tree" role="group">
      <div class="fui-TreeItem" role="treeitem" aria-level="2" tabindex="-1"><div class="fui-TreeItemLayout"><div class="fui-TreeItemLayout__main">計画</div></div></div>
      <div class="fui-TreeItem" role="treeitem" aria-level="2" tabindex="-1"><div class="fui-TreeItemLayout"><div class="fui-TreeItemLayout__main">議事録</div></div></div>
    </div>
  </div>
</div>
```

### v9 との差と未確認の点

- actions は、v9 ではホバーかフォーカスの間だけ描かれ、その間は aside を描かない（`[tree]components/TreeItemLayout/useTreeItemLayout.tsx:150-376` の `isActionsVisible`）。CSS は `:hover` と `:focus-visible` で表示を切り替える近似である。
- 子の木の開閉に動きはない。v9 の Collapse は再現していない。
- 字下げについて、サイトの指針と Web Components v3 は small で 12px とする（`packages/web-components/src/tree-item/tree-item.styles.ts:41, 49, 140`）。v9 は size によらず 24px である。ここでは v9 を採った。
- FlatTree、TreeItemPersonaLayout、`selectionMode` の選択の部品（`fui-TreeItemLayout__selector` の中身）は扱っていない。

## Carousel

略記: `[car]` = `packages/react-components/react-carousel/library/src/components/`

### 概要と使い分け（Do / Don't）

Carousel は、ページを離れずに、注目の記事、製品、サービスなどを順に見せる。ページ、アプリ、ドロワー、ダイアログに置け、その移動はページの他の部分から独立している。

- Do: 自動で送るときは、必ず一時停止の手段を付ける。中の内容に応じるかどうかは利用者が選べるようにする。
- Do: 画像と動画は縦横比を保つ。400% の拡大でリフローさせる。サイトの指針では幅 600px 以下で全幅にし、320px まで縮められるようにする。
- ナビゲーションは、前後のボタンとステップの表示（点）か、画像のサムネイルを使う。配置はカード、全幅のバナー、画像のギャラリーがある。
- サイトに Do / Don't の一覧はない。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

| 部品 | 要素 | role・ARIA | class | 出典 |
|---|---|---|---|---|
| Carousel | `div` | `role="region"` | `fui-Carousel` | `[car]Carousel/useCarousel.ts:128` |
| CarouselViewport | `div` | `role="presentation"` | `fui-CarouselViewport` | `[car]CarouselViewport/useCarouselViewport.ts:72` |
| CarouselSlider | `div` | `role="group"` | `fui-CarouselSlider` | `[car]CarouselSlider/useCarouselSlider.ts:43` |
| CarouselCard | `div` | `role="tabpanel"`。見えていないカードは `aria-hidden="true"` と `inert` | `fui-CarouselCard` | `[car]CarouselCard/useCarouselCard.ts:55-60, 111` |
| CarouselNavContainer | `div` | なし | `fui-CarouselNavContainer`、`__prev`、`__next`、`__autoplay` | `[car]CarouselNavContainer/useCarouselNavContainerStyles.styles.ts` |
| CarouselNav | `div` | `role="tablist"` | `fui-CarouselNav` | `[car]CarouselNav/useCarouselNav.ts:55` |
| CarouselNavButton | `button` | `role="tab"`、`aria-selected` | `fui-CarouselNavButton` | `[car]CarouselNavButton/useCarouselNavButton.ts:65-67` |
| CarouselNavImageButton | `button` と `img` | `role="tab"`、`aria-selected` | `fui-CarouselNavImageButton`、`__image` | `[car]CarouselNavImageButton/useCarouselNavImageButton.ts:58-60` |
| CarouselButton（前・次） | Button の subtle、アイコンだけ。循環しないときは端で `disabled` | `aria-disabled` | `fui-CarouselButton`、`__icon` | `[car]CarouselButton/useCarouselButton.tsx:80-117` |

- 前後のボタンには `data-direction="prev"` と `data-direction="next"` を付け、`fui-CarouselNavContainer__prev`・`__next` の class も付ける。`navigation.js` はこの属性でボタンを見分ける。
- v9 の移動は Embla Carousel（JavaScript）が行う。React を使わない HTML では、Viewport をスクロールスナップにし、`navigation.js` が前後のボタンと点でスクロール位置を動かし、表示中のカードに合わせて `aria-selected`、`aria-hidden`、`inert` を書き換える。
- 循環させるには Carousel に `data-circular` を付ける（v9 の `circular`）。

### バリエーション

| 属性 | 値 | 既定 | v9 の prop | 出典 |
|---|---|---|---|---|
| `data-appearance`（Carousel） | `flat` / `elevated` | `flat` | `appearance` | `[car]Carousel/Carousel.types.ts:46` |
| `data-layout`（NavContainer） | `inline` / `inline-wide` / `overlay` / `overlay-wide` / `overlay-expanded` | `inline` | `layout` | `[car]CarouselNavContainer/CarouselNavContainer.types.ts:20-34` |
| `data-appearance`（CarouselNav） | `brand` | なし | `appearance` | `[car]CarouselNav/CarouselNav.types.ts:17` |
| `data-auto-size`（CarouselCard） | 有無 | なし | `autoSize` | `[car]CarouselCard/useCarouselCardStyles.styles.ts:16-32` |
| `data-circular`（Carousel、JS） | 有無 | なし | `circular` | — |

### 寸法（size ごとの表）

Carousel に size はない。

| 対象 | 値 | 出典 |
|---|---|---|
| Carousel | `overflow-x: hidden; position: relative`。elevated は margin と padding が 16px（`spacingVerticalL`） | `[car]Carousel/useCarouselStyles.styles.ts:16-28` |
| Slider | `display: flex`。elevated は gap 24px（`spacingHorizontalXXL`） | `[car]CarouselSlider/useCarouselSliderStyles.styles.ts:17-25` |
| Card | `flex: 0 0 100%`。elevated は角丸 8px（`borderRadiusXLarge`）、`shadow16` | `[car]CarouselCard/useCarouselCardStyles.styles.ts:16-32` |
| Nav | 角丸 8px、左右の margin 8px、背景 `colorNeutralBackgroundAlpha` | `[car]CarouselNav/useCarouselNavStyles.styles.ts:17-33` |
| NavButton | 点は 8×8px の円、押せる範囲は 24×24px（8px の内容と 8px の padding、計算） | `[car]CarouselNavButton/useCarouselNavButtonStyles.styles.ts:17-43` |
| NavButton（選択） | 点の幅 16px（`spacingHorizontalL`）、角丸 4px（直書き）、左右の padding 4px | 同 65-77 |
| NavImageButton | 40×40px、選択は 48×48px、角丸 2px（`borderRadiusSmall`）、左右の margin 4px | `[car]CarouselNavImageButton/useCarouselNavImageButtonStyles.styles.ts:13-41` |
| NavContainer | inline は上に 12px（`spacingVerticalM`）。overlay は `position: absolute; bottom: 12px` | `[car]CarouselNavContainer/useCarouselNavContainerStyles.styles.ts:24-45` |
| CarouselButton | 32×32px（Button の medium のアイコンだけ）、`margin-block: auto` | `[car]CarouselButton/useCarouselButtonStyles.styles.ts:17-28`、`packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:510-515` |

### 色と状態（トークン名の表）

CarouselNavButton の点（`[car]CarouselNavButton/useCarouselNavButtonStyles.styles.ts`）:

| 状態 | 色 | opacity | 行 |
|---|---|---|---|
| 未選択・rest | `colorNeutralForeground1` | 0.6 | 34, 51-53 |
| 未選択・hover | 同上 | 0.75 | 54-58 |
| 未選択・pressed | 同上 | 1 | 59-63 |
| 選択・rest | 同上 | 1 | 74-77 |
| 選択・hover | 同上 | 0.75 | 78-82 |
| 選択・pressed | 同上 | 0.65 | 83-87 |
| brand・選択 | `colorCompoundBrandBackground`、hover `colorCompoundBrandBackgroundHover`、pressed `colorCompoundBrandBackgroundPressed` | 1 | 89-106 |
| brand・未選択 | `colorNeutralForeground1` | 0.6 / 0.75 / 1 | 107-122 |

前後のボタンは Button の subtle の色（rest `colorSubtleBackground`・`colorNeutralForeground2`、hover `colorSubtleBackgroundHover`、pressed `colorSubtleBackgroundPressed`、アイコンは hover で `colorNeutralForeground2BrandHover`）を使う。

### フォーカス・動き・ハイコントラスト

- フォーカス: CarouselNav は `outline: 2px solid var(--colorStrokeFocus2)` と角丸 4px（`[car]CarouselNav/useCarouselNavStyles.styles.ts:24-28`）。NavButton は 2px の `colorStrokeFocus2` の枠を、margin −2px で外側に描く（`[car]CarouselNavButton/useCarouselNavButtonStyles.styles.ts:46-50, 69-73`）。前後のボタンは Button の規則である。
- 動き: v9 の移動は Embla の速さの値（既定 25、ms ではない）で決まる（`[car]useEmblaCarousel.ts:81, 101`）。CSS の transition はない。React を使わない CSS では `scroll-behavior: smooth` で近似し、縮小モーションの設定では即座に移る。
- ハイコントラスト: 点に `forced-color-adjust: none; background-color: white; mix-blend-mode: difference` を付け、強制色で消えないようにする（同 36-41）。NavButton には透明の 1px の outline を付け、強制色で枠が見えるようにする（45, 68）。

### 実装の例

```html demo
<div class="fui-Carousel" role="region" aria-label="お知らせ" data-fui-enhance style="max-width: 480px">
  <div class="fui-CarouselViewport" role="presentation">
    <div class="fui-CarouselSlider" role="group">
      <div class="fui-CarouselCard" role="tabpanel" id="n14-car-1" aria-label="1 / 3"><div style="height: 160px; display: grid; place-items: center; background: var(--colorBrandBackground2); color: var(--colorBrandForeground2)">新しい機能の紹介</div></div>
      <div class="fui-CarouselCard" role="tabpanel" id="n14-car-2" aria-label="2 / 3"><div style="height: 160px; display: grid; place-items: center; background: var(--colorNeutralBackground3)">メンテナンスのお知らせ</div></div>
      <div class="fui-CarouselCard" role="tabpanel" id="n14-car-3" aria-label="3 / 3"><div style="height: 160px; display: grid; place-items: center; background: var(--colorPaletteGreenBackground1, var(--colorNeutralBackground2))">アンケートのお願い</div></div>
    </div>
  </div>
  <div class="fui-CarouselNavContainer">
    <button class="fui-CarouselButton fui-CarouselNavContainer__prev" type="button" data-direction="prev" aria-label="前のカード">
      <span class="fui-CarouselButton__icon"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M12.35 15.85a.5.5 0 0 1-.7 0L6.16 10.4a.55.55 0 0 1 0-.78l5.49-5.46a.5.5 0 1 1 .7.7L7.2 10l5.16 5.15c.2.2.2.5 0 .7"/></svg></span>
    </button>
    <div class="fui-CarouselNav" role="tablist" aria-label="カードの選択">
      <button class="fui-CarouselNavButton" type="button" role="tab" aria-selected="true" aria-controls="n14-car-1" aria-label="カード 1"></button>
      <button class="fui-CarouselNavButton" type="button" role="tab" aria-selected="false" aria-controls="n14-car-2" aria-label="カード 2"></button>
      <button class="fui-CarouselNavButton" type="button" role="tab" aria-selected="false" aria-controls="n14-car-3" aria-label="カード 3"></button>
    </div>
    <button class="fui-CarouselButton fui-CarouselNavContainer__next" type="button" data-direction="next" aria-label="次のカード">
      <span class="fui-CarouselButton__icon"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7.65 4.15c.2-.2.5-.2.7 0l5.49 5.46c.21.22.21.57 0 .78l-5.49 5.47a.5.5 0 0 1-.7-.71L12.8 10 7.65 4.85a.5.5 0 0 1 0-.7"/></svg></span>
    </button>
  </div>
</div>
```

### v9 との差と未確認の点

- 移動の動きは、Embla の減速ではなく、ブラウザーのスムーズスクロールである。ドラッグの力で進む動き、`motion="fade"`、自動再生のボタン（`fui-CarouselAutoplayButton`）は再現していない。
- 前後のボタンの背景: v9 は Carousel の `colorNeutralBackgroundAlpha` を Button の class より前に結合するので、Button の subtle の背景（透明）が勝つと読める（`[car]CarouselButton/useCarouselButtonStyles.styles.ts:38-43`。Griffel の `mergeClasses` の順からの推論）。CSS は subtle の背景にした。ブラウザーで確かめていない。
- `aria-roledescription="carousel"` は v9 のソースにない。WAI-ARIA の APG に沿うなら足してよい。
- v9 はキーボードの左右の矢印で点を移る。`navigation.js` は Tab キーでの移動とクリックだけを扱う。

## Table

略記: `[table]` = `packages/react-components/react-table/library/src/components/`

### 概要と使い分け（Do / Don't）

Table は表の見た目の部品で、ネイティブの `table`、`thead`、`tbody`、`tr`、`th`、`td` に当てる。DataGrid は Table に、並べ替え、行の選択、キーボードでのセルの移動、列の幅の変更を足したもので、`div` と `role="grid"` で描く（`[table]DataGrid/useDataGrid.ts:112-116`）。サイトに Web の Usage のページはないので、ソースから分かる使い分けを書く。

- Do: 読むだけの表は、ネイティブの `table` で Table にする。行の選択やセルの移動が要るときは DataGrid にする。
- Do: 並べ替えできる列の見出しには `aria-sort` を付け、見出しの中をボタンにする。
- Don't: 選択の状態を色だけで伝える。DataGrid では行に `aria-selected` を付ける。
- Don't: 行の中の操作（TableCellActions）を、ホバーでしか見つけられない唯一の手段にする。v9 もフォーカスで出す。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

| 部品 | 要素（Table / DataGrid） | role | class | 出典 |
|---|---|---|---|---|
| Table | `table` / `div` | なし / `grid`（Table の `noNativeElements` は `table`） | `fui-Table`（DataGrid は `fui-DataGrid` も） | `[table]Table/useTable.ts:15, 27`、`[table]DataGrid/useDataGridStyles.styles.ts` |
| TableHeader | `thead` / `div` | なし / `rowgroup` | `fui-TableHeader` | `[table]TableHeader/useTableHeader.ts:20, 31` |
| TableBody | `tbody` / `div` | なし / `rowgroup` | `fui-TableBody` | `[table]TableBody/useTableBody.ts:19, 31` |
| TableRow | `tr` / `div` | なし / `row`。DataGrid の選択できる行は `aria-selected` | `fui-TableRow`（`fui-DataGridRow`） | `[table]TableRow/useTableRow.ts:21, 36`、`[table]DataGridRow/useDataGridRow.ts:62` |
| TableHeaderCell | `th` / `div` | なし / `columnheader`。並べ替えできれば `aria-sort` | `fui-TableHeaderCell`、`__button`、`__sortIcon`、`__aside` | `[table]TableHeaderCell/useTableHeaderCell.tsx:33-70` |
| TableCell | `td` / `div` | なし / `cell`（DataGrid は `gridcell`） | `fui-TableCell` | `[table]TableCell/useTableCell.ts:20, 32` |
| TableSelectionCell | セルと Checkbox・Radio | なし | `fui-TableSelectionCell` | `[table]TableSelectionCell/useTableSelectionCell.tsx:41-52` |
| TableCellLayout | `div` | なし | `fui-TableCellLayout`、`__media`、`__content`、`__main`、`__description` | `[table]TableCellLayout/useTableCellLayoutStyles.styles.ts:9-15` |
| TableCellActions | `div` | なし | `fui-TableCellActions` | `[table]TableCellActions/useTableCellActionsStyles.styles.ts:7-9` |
| TableResizeHandle | `div` | なし | `fui-TableResizeHandle` | `[table]TableResizeHandle/useTableResizeHandleStyles.styles.ts:8-12` |

- 見出しの中の `fui-TableHeaderCell__button` は、並べ替えできないとき `div`、できるときは ARIA のボタンになる（`[table]TableHeaderCell/useTableHeaderCell.tsx:35-42, 69`）。React を使わない HTML では `<button type="button">` を使ってよい（CSS がボタンの既定を消す）。並べ替えの矢印は `ArrowUpRegular`・`ArrowDownRegular` の 12px（12-15）。
- 見出しの行は、行のホバーの色を持たない。CSS は `.fui-TableHeader` の直下の行を見出しの行とみなす。
- キーボード: Table にはない。DataGrid の `focusMode` は `none` / `cell`（既定）/ `row_unstable` / `composite` で（`[table]DataGrid/DataGrid.types.ts:17, 29`）、矢印キーでセルを移る。`navigation.js` は DataGrid のキーボード操作を扱わない。

### バリエーション

| 属性 | 値 | 既定 | v9 の prop | 出典 |
|---|---|---|---|---|
| `data-size`（Table） | `extra-small` / `small` / `medium` | `medium` | `size` | `[table]Table/Table.types.ts:10-12`、`useTable.ts:32` |
| `data-no-native-elements`（Table） | 有無 | なし（DataGrid は常に有り） | `noNativeElements` | `[table]Table/Table.types.ts:17`、`DataGrid/useDataGrid.ts:116` |
| `data-appearance`（TableRow） | `brand` / `neutral` / `none` | `none` | `appearance` | `[table]TableRow/TableRow.types.ts:15-17` |
| `aria-selected="true"`（DataGridRow） | — | — | 選択。`data-appearance` がなければ `brand`（`selectionAppearance` の既定） | `[table]DataGrid/DataGrid.types.ts:47` |
| `data-subtle-selection`（DataGrid） | 有無 | なし | `subtleSelection` | `[table]DataGrid/DataGrid.types.ts:41` |
| `data-appearance`（TableCellLayout） | `primary` | なし | `appearance` | `[table]TableCellLayout/TableCellLayout.types.ts:42-44` |
| `data-truncate`（TableCellLayout） | 有無 | なし | `truncate` | `[table]TableCellLayout/useTableCellLayoutStyles.styles.ts:28-66` |
| `data-subtle`・`data-hidden`（TableSelectionCell） | 有無 | なし | `subtle`・`hidden` | `[table]TableSelectionCell/useTableSelectionCellStyles.styles.ts:55-67, 84-85` |

### 寸法（size ごとの表）

| 対象 | 項目 | extra-small | small | medium | 出典 |
|---|---|---|---|---|---|
| TableCell（table のとき） | `height` | 24px | 34px | 44px | `[table]TableCell/useTableCellStyles.styles.ts:20-30` |
| TableCell（DataGrid のとき） | `min-height` | 24px | 34px | 44px | 同 41-51 |
| TableRow | 下の線 | なし | 1px の `colorNeutralStroke2` | 同左 | `[table]TableRow/useTableRowStyles.styles.ts:91-93` |
| TableRow | 文字の大きさ | `fontSizeBase200` | 受け継ぐ | 受け継ぐ | 同 95-97 |
| TableCellLayout の media | 大きさ | 16px | 20px | 20px（primary は 24px） | `[table]TableCellLayout/useTableCellLayoutStyles.styles.ts:41-56, 90-104` |

| 対象 | 値 | 出典 |
|---|---|---|
| Table | `display: table; width: 100%; table-layout: fixed; border-collapse: collapse`、背景 `colorSubtleBackground`。DataGrid は `display: block` | `[table]Table/useTableStyles.styles.ts` |
| TableCell・TableHeaderCell | 左右の padding 8px（`spacingHorizontalS`）、`vertical-align: middle` | `[table]TableCell/useTableCellStyles.styles.ts:57-66`、`TableHeaderCell/useTableHeaderCellStyles.styles.ts:35-44` |
| 見出しのボタン | `display: flex; gap: 4px; min-height: 32px; width: 100%` | `[table]TableHeaderCell/useTableHeaderCellStyles.styles.ts:57-82` |
| 並べ替えの矢印 | 上の padding 2px（`spacingVerticalXXS`）、12px | 同 88-92 |
| TableCellLayout | `display: flex; gap: 8px`。description は `caption1` と `colorNeutralForeground2`。primary の main は太字 | `[table]TableCellLayout/useTableCellLayoutStyles.styles.ts:20-71` |
| TableSelectionCell | 幅 44px、`padding: 0; text-align: center` | `[table]TableSelectionCell/useTableSelectionCellStyles.styles.ts:9, 17-46` |
| TableCellActions | 末尾に `position: absolute`、縦の中央、ふだんは `opacity: 0` | `[table]TableCellActions/useTableCellActionsStyles.styles.ts:14-23` |
| TableResizeHandle | 幅 16px、`margin: 0 -8px`、`cursor: col-resize`、線は 1px の `colorNeutralStroke1` | `[table]TableResizeHandle/useTableResizeHandleStyles.styles.ts:18-51` |

見出しの行の高さは、セルに高さがないので、見出しのボタンの `min-height: 32px` で決まる（推論）。文字の大きさは Table では指定せず、受け継ぐ。

### 色と状態（トークン名の表）

TableRow（見出しの行を除く。`[table]TableRow/useTableRowStyles.styles.ts:53-134`）:

| 状態 | 背景 | 文字 | 線の色 | 行 |
|---|---|---|---|---|
| rest | （Table の `colorSubtleBackground`） | `colorNeutralForeground1` | `colorNeutralStroke2` | 34, 91 |
| hover | `colorSubtleBackgroundHover` | `colorNeutralForeground1Hover` | — | 72-74 |
| pressed | `colorSubtleBackgroundPressed` | `colorNeutralForeground1Pressed` | — | 62-64 |
| brand・rest | `colorBrandBackground2` | `colorNeutralForeground1` | `colorTransparentStrokeInteractive` | 99-101 |
| brand・hover | `colorSubtleBackgroundHover`（推論） | `colorNeutralForeground1Hover` | — | 72-74 |
| brand・pressed | `colorBrandBackground2` | `colorNeutralForeground1` | — | 102-105 |
| neutral・rest | `colorSubtleBackgroundSelected` | `colorNeutralForeground1Hover` | `colorNeutralStrokeOnBrand` | 126-133 |
| neutral・hover | `colorSubtleBackgroundHover`（推論） | `colorNeutralForeground1Hover` | — | 72-74 |
| neutral・pressed | `colorSubtleBackgroundSelected` | `colorNeutralForeground1Pressed` | — | 62-64, 129-131 |

- brand と neutral は `:hover` の色を上書きしないので、ホバー中は通常の行のホバーの色になる。Griffel の原子クラスで `:hover` の規則が既定の規則より強いことからの推論で、ブラウザーで確かめていない。
- 行のホバー、押下、フォーカスで、TableCellActions と TableSelectionCell を `opacity: 1` にする（36-81）。
- 並べ替えできる見出し: hover は `colorSubtleBackgroundHover`・`colorNeutralForeground1Hover`、pressed は `colorSubtleBackgroundPressed`・`colorNeutralForeground1Pressed`、`cursor: pointer`（`[table]TableHeaderCell/useTableHeaderCellStyles.styles.ts:46-55, 84-86`）。
- disabled の状態はない。

### フォーカス・動き・ハイコントラスト

- フォーカス: TableRow、TableCell、TableSelectionCell は `outline: 2px solid var(--colorStrokeFocus2)` と `border-radius: var(--borderRadiusMedium)`。TableHeaderCell は中にフォーカスがあるとき同じ線を出す（`[table]TableRow/useTableRowStyles.styles.ts:47-50`、`TableCell/useTableCellStyles.styles.ts:62-65`、`TableHeaderCell/useTableHeaderCellStyles.styles.ts:39-42`）。
- 動き: TableResizeHandle の `transition: opacity .2s`（直書き、`[table]TableResizeHandle/useTableResizeHandleStyles.styles.ts:27-28`）だけである。行の背景には transition がない。
- ハイコントラスト: 行のホバーで文字と線を `Highlight` にする（83-88）。brand と neutral の行は `border: 2px solid transparent` と角丸を付け、強制色でも選択の枠が出るようにする。フォーカスの outline は内側へ 4px 寄せる（107-125）。

### 実装の例

```html demo
<table class="fui-Table" aria-label="ファイルの一覧">
  <thead class="fui-TableHeader">
    <tr class="fui-TableRow">
      <th class="fui-TableHeaderCell" scope="col" aria-sort="ascending">
        <button class="fui-TableHeaderCell__button" type="button">ファイル<span class="fui-TableHeaderCell__sortIcon"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M3.13 9.16a.5.5 0 1 0 .74.68L9.5 3.67V17.5a.5.5 0 1 0 1 0V3.67l5.63 6.17a.5.5 0 0 0 .74-.68l-6.32-6.92a.75.75 0 0 0-1.1 0z"/></svg></span></button>
      </th>
      <th class="fui-TableHeaderCell" scope="col" aria-sort="none">
        <button class="fui-TableHeaderCell__button" type="button">更新者</button>
      </th>
      <th class="fui-TableHeaderCell" scope="col">
        <div class="fui-TableHeaderCell__button">更新日</div>
      </th>
    </tr>
  </thead>
  <tbody class="fui-TableBody">
    <tr class="fui-TableRow">
      <td class="fui-TableCell">
        <div class="fui-TableCellLayout">
          <span class="fui-TableCellLayout__media"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M6 2a2 2 0 0 0-2 2v12c0 1.1.9 2 2 2h8a2 2 0 0 0 2-2V7.41c0-.4-.16-.78-.44-1.06l-3.91-3.91A1.5 1.5 0 0 0 10.59 2zM5 4a1 1 0 0 1 1-1h4v3.5c0 .83.67 1.5 1.5 1.5H15v8a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1zm9.8 3h-3.3a.5.5 0 0 1-.5-.5V3.2z"/></svg></span>
          <div class="fui-TableCellLayout__content"><span class="fui-TableCellLayout__main">議事録.docx</span></div>
        </div>
      </td>
      <td class="fui-TableCell">佐藤</td>
      <td class="fui-TableCell">昨日</td>
    </tr>
    <tr class="fui-TableRow" data-appearance="brand">
      <td class="fui-TableCell">
        <div class="fui-TableCellLayout">
          <span class="fui-TableCellLayout__media"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M4.5 3A2.5 2.5 0 0 0 2 5.5v9A2.5 2.5 0 0 0 4.5 17h11a2.5 2.5 0 0 0 2.5-2.5v-7A2.5 2.5 0 0 0 15.5 5H9.7L8.23 3.51A1.8 1.8 0 0 0 6.98 3zM3 5.5C3 4.67 3.67 4 4.5 4h2.48q.32 0 .53.22L8.8 5.5 7.44 6.85a.5.5 0 0 1-.35.15H3zM3 8h4.09c.4 0 .78-.16 1.06-.44L9.7 6h5.79c.83 0 1.5.67 1.5 1.5v7c0 .83-.67 1.5-1.5 1.5h-11A1.5 1.5 0 0 1 3 14.5z"/></svg></span>
          <div class="fui-TableCellLayout__content"><span class="fui-TableCellLayout__main">設計資料</span><span class="fui-TableCellLayout__description">12 個のファイル</span></div>
        </div>
      </td>
      <td class="fui-TableCell">鈴木</td>
      <td class="fui-TableCell">3 日前</td>
    </tr>
    <tr class="fui-TableRow" data-appearance="neutral">
      <td class="fui-TableCell"><div class="fui-TableCellLayout"><div class="fui-TableCellLayout__content"><span class="fui-TableCellLayout__main">予算.xlsx</span></div></div></td>
      <td class="fui-TableCell">高橋</td>
      <td class="fui-TableCell">先週</td>
    </tr>
  </tbody>
</table>
```

```html demo
<div style="display: grid; gap: 16px">
  <table class="fui-Table" data-size="small" aria-label="small の表">
    <thead class="fui-TableHeader"><tr class="fui-TableRow"><th class="fui-TableHeaderCell" scope="col"><div class="fui-TableHeaderCell__button">項目</div></th><th class="fui-TableHeaderCell" scope="col"><div class="fui-TableHeaderCell__button">値</div></th></tr></thead>
    <tbody class="fui-TableBody">
      <tr class="fui-TableRow"><td class="fui-TableCell">CPU</td><td class="fui-TableCell">42%</td></tr>
      <tr class="fui-TableRow"><td class="fui-TableCell">メモリー</td><td class="fui-TableCell">6.1 GB</td></tr>
    </tbody>
  </table>
  <table class="fui-Table" data-size="extra-small" aria-label="extra-small の表">
    <thead class="fui-TableHeader"><tr class="fui-TableRow"><th class="fui-TableHeaderCell" scope="col"><div class="fui-TableHeaderCell__button">項目</div></th><th class="fui-TableHeaderCell" scope="col"><div class="fui-TableHeaderCell__button">値</div></th></tr></thead>
    <tbody class="fui-TableBody">
      <tr class="fui-TableRow"><td class="fui-TableCell">CPU</td><td class="fui-TableCell">42%</td></tr>
      <tr class="fui-TableRow"><td class="fui-TableCell">メモリー</td><td class="fui-TableCell">6.1 GB</td></tr>
    </tbody>
  </table>
</div>
```

```html demo
<div class="fui-Table fui-DataGrid" role="grid" aria-label="DataGrid の見た目" aria-multiselectable="true">
  <div class="fui-TableHeader fui-DataGridHeader" role="rowgroup">
    <div class="fui-TableRow fui-DataGridRow" role="row">
      <div class="fui-TableHeaderCell fui-DataGridHeaderCell" role="columnheader"><div class="fui-TableHeaderCell__button">名前</div></div>
      <div class="fui-TableHeaderCell fui-DataGridHeaderCell" role="columnheader"><div class="fui-TableHeaderCell__button">状態</div></div>
    </div>
  </div>
  <div class="fui-TableBody fui-DataGridBody" role="rowgroup">
    <div class="fui-TableRow fui-DataGridRow" role="row" aria-selected="true">
      <div class="fui-TableCell fui-DataGridCell" role="gridcell" tabindex="0">ジョブ A</div>
      <div class="fui-TableCell fui-DataGridCell" role="gridcell" tabindex="-1">完了</div>
    </div>
    <div class="fui-TableRow fui-DataGridRow" role="row" aria-selected="false">
      <div class="fui-TableCell fui-DataGridCell" role="gridcell" tabindex="-1">ジョブ B</div>
      <div class="fui-TableCell fui-DataGridCell" role="gridcell" tabindex="-1">実行中</div>
    </div>
  </div>
</div>
```

### v9 との差と未確認の点

- TableSelectionCell の中の Checkbox と Radio は、第 12 章の部品である。この章の見本には入れていない。subtle の選択セルを隠す条件（v9 は `checked === false`）は、CSS ではセルの中の `:checked` と `aria-checked` で近似する。
- TableCellActions の中の Button も他の章の部品である。v9 の `visible` に当たる `data-visible` を用意した。
- DataGrid の並べ替え、選択、列の幅の変更、`focusMode` のキーボード操作は、JavaScript が要るので扱っていない。
- 見出しのボタンの `resize: horizontal` は v9 のまま写した。`overflow: visible` のため、ブラウザーは取っ手を出さない。

## 共通の土台への提案

なし。この章の CSS は `fluent2-base.css` の `.fui-Icon` と `.fui-Icon-filled` の既定だけを使う。
