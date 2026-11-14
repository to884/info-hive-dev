# テキストの入力と選択の一覧

この章は、文字を入れる部品（Input、Textarea、SearchBox、SpinButton）と、一覧から選ぶ部品（Select、Combobox、Dropdown、TagPicker）を扱う。一覧の中身の Listbox、Option、OptionGroup は Dropdown の節にまとめる。

CSS は `assets/fluent2.css` の `text-entry` の部分、振る舞いは `assets/fluent2.js` にある（開発用のリポジトリ（非公開）の原本は `src/components/text-entry.css` と `text-entry.js`）。JS が扱うのは、`data-fui-enhance` を付けた要素とその中だけである。

出典の書き方: 各節の「出典のファイル」に、`packages/react-components/` からの相対パスを一度だけ書く。表と本文では `useInputStyles.styles.ts:57` のようにファイル名と行で示す。

## 章の全体に関わる約束

### 共通の下線

Input、Textarea、Combobox、Dropdown、SpinButton、TagPickerControl は、フォーカスが入ると下に 2px のブランドの線が中央から左右へ伸びる。作りは同じである。

- 根の `::after` に `border-bottom: 2px solid colorCompoundBrandStroke` を置き、高さを角丸と同じ `max(2px, borderRadiusMedium)` にする。下の 2 つの角だけを丸め、`clip-path: inset(calc(100% - 2px) 0 0 0)` で端の「つの」を切る（`useInputStyles.styles.ts:61-85`）。
- 位置は `left/right/bottom: -1px` で、根の 1px の枠に重ねる。枠を `::before` に描く SpinButton は 0 にする。
- 休止は `transform: scaleX(0)`、`:focus-within` で `scaleX(1)`。入りは `durationNormal`（200ms）、出は `durationUltraFast`（50ms）。
- フォーカス中にもう一度押すと、線の色が `colorCompoundBrandStrokePressed` になる。
- Select だけは作りが違う。根に枠がないので位置は 0、線は `linear-gradient` で 4px の下半分を塗る（`useSelectStyles.styles.ts:68-105`）。押したときの色の変化もない。

**v9 の誤りと、この CSS の扱い**: v9 は曲線のトークンを `transition-delay` に入れている（`useInputStyles.styles.ts:90,102` ほか全部品）。`cubic-bezier()` は遅延の値として不正なので、計算値の時点で無効になり、遅延は 0、timing-function は既定の `ease` になる。この CSS はその描画に合わせ、`transition-timing-function: ease; transition-delay: 0s` と書く。設計の意図は「入りは curveDecelerateMid、出は curveAccelerateMid」と読めるが、採らない。

### 重なりの順（hover とフォーカスのどちらが勝つか）

Griffel は、規則のキーの先頭の擬似クラスで出力の順を決める。順は「既定 → `:focus-within` → `:focus` → `:focus-visible` → `:hover` → `:active` → `@supports` → `@media`」である（`@griffel/core` の `getStyleBucketName` と `styleBucketOrdering`。unpkg の最新版で確かめた）。この違いで、部品ごとに勝ち方が変わる。

| 部品 | v9 のキーの書き方 | hover とフォーカスが重なったときの枠 |
|---|---|---|
| Input、SpinButton | `':active,:focus-within'` を 1 つのキーにする（先頭が `:active`） | フォーカスの色（Pressed）が勝つ |
| Textarea、Combobox、Dropdown、TagPickerControl | `:hover`、`:active`、`:focus-within` を別のキーにする | hover の色が勝つ |

この CSS は、擬似クラスを詳細度に数え、v9 と同じ順に規則を並べてこれを再現する。

### アイコン

この章の部品は、スロットの `font-size` でアイコンの大きさを変える。そのため SVG は v9 のスナップショットと同じく `width="1em" height="1em"` にする（`react-combobox/library/src/components/Combobox/__snapshots__/Combobox.test.tsx.snap:19-27`）。約束の `width="20"` のままにすると、small と large で大きさが変わらない。大きさが決まっている `Checkmark12Filled` と `ChevronUp16Regular` などだけは数値で書く。

## Input

### 概要と使い分け（Do / Don't）

短い自由形式の文字を 1 行で入れてもらう部品である。複数行が要るなら Textarea を使う。`type` で書式を付けられるが、Fluent は種類ごとの装飾をしない。`date` などはブラウザー既定の見た目が混ざる。

- Do: 見えるラベルを添える。プレースホルダーは短い補助にとどめる。幅を想定する入力の長さに合わせる。
- Don't: 欠かせない情報をプレースホルダーに置く（入力を始めると消える）。プレースホルダーの末尾に句点を付ける。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

```text
span.fui-Input                      根: 枠、背景、下線の ::after
├─ span.fui-Input__contentBefore    任意。アイコンなど
├─ input.fui-Input__input           主スロット。type="text" が既定
└─ span.fui-Input__contentAfter     任意
```

- role、ARIA、キーボードはネイティブの `<input>` に任せる。無効は `input` の `disabled`、不正は `aria-invalid="true"` で表す。CSS は根から `:has()` で読む。
- `className` と `style` は根に、それ以外の属性は `input` に付ける（v9 の `Input.types.ts:5-21` と同じ分け方）。

出典のファイル: `react-input/library/src/components/Input/useInputStyles.styles.ts`、`react-input/library/src/components/Input/useInput.ts`、`react-input/library/src/components/Input/Input.types.ts`

### バリエーション

| 属性 | 値 | 既定 | 出典 |
|---|---|---|---|
| `data-appearance` | `outline`、`underline`、`filled-darker`、`filled-lighter`（非推奨の `filled-darker-shadow`、`filled-lighter-shadow` も受ける） | `outline` | `Input.types.ts:53-59`、`useInput.ts:24` |
| `data-size` | `small`、`medium`、`large` | `medium` | `Input.types.ts:45`、`useInput.ts:23` |

### 寸法（size ごとの表）

| 項目 | small | medium | large | 出典 |
|---|---|---|---|---|
| 根の `min-height` | 24px | 32px | 40px | `useInputStyles.styles.ts:16-20,53,120,127`（直書き） |
| 文字 | `caption1`（12/16） | `body1`（14/20） | `body2`（16/22） | `useInputStyles.styles.ts:54,121,128` |
| 根の `gap` | `spacingHorizontalXXS`（2px） | 2px | `spacingHorizontalSNudge`（6px） | `useInputStyles.styles.ts:46,129` |
| input の左右の余白（content なし） | `spacingHorizontalS`（8px） | `spacingHorizontalM`（12px） | `calc(M + SNudge)`（18px） | `useInputStyles.styles.ts:35-39,244,264-274` |
| 根の余白（content がある側） | `SNudge`（6px） | `MNudge`（10px） | `M`（12px） | `useInputStyles.styles.ts:24-29,218-235` |
| input の余白（content がある側） | `XXS`（2px） | `XXS`（2px） | `SNudge`（6px） | `useInputStyles.styles.ts:30-34,275-292` |
| content のアイコン | 16px | 20px | 24px | `useInputStyles.styles.ts:309,317-325`（直書き） |
| 角丸 | `borderRadiusMedium`（4px）。underline は 0 | 同 | 同 | `useInputStyles.styles.ts:47,147` |
| 枠 | 1px（直書き） | 同 | 同 | `useInputStyles.styles.ts:58` |

content がないときは、左右の余白を合計して input に持たせ、押せる範囲を広げる（`useInputStyles.styles.ts:22-23`）。content があるときは根と input に分ける。

### 色と状態（トークン名の表）

| 状態 | outline | underline | filled-darker / filled-lighter |
|---|---|---|---|
| 背景 | `colorNeutralBackground1` | `colorTransparentBackground` | `colorNeutralBackground3` / `colorNeutralBackground1` |
| 枠 | `colorNeutralStroke1`、下だけ `colorNeutralStrokeAccessible` | 下だけ 1px `colorNeutralStrokeAccessible` | `colorTransparentStroke` |
| hover | `colorNeutralStroke1Hover`、下 `colorNeutralStrokeAccessibleHover` | 下 `colorNeutralStrokeAccessibleHover` | `colorTransparentStrokeInteractive` |
| 押下とフォーカス | `colorNeutralStroke1Pressed`、下 `colorNeutralStrokeAccessiblePressed` | 下 `colorNeutralStrokeAccessiblePressed` | `colorTransparentStrokeInteractive` |
| invalid（フォーカスなし） | 全周 `colorPaletteRedBorder2` | 同（見えるのは下だけ） | 同 |
| disabled | 背景 `colorTransparentBackground`、枠 `colorNeutralStrokeDisabled`、`cursor: not-allowed`、下線なし | 同 | 同（背景も透明になる） |

| 部分 | 通常 | disabled |
|---|---|---|
| 入力文字 | `colorNeutralForeground1` | `colorNeutralForegroundDisabled` |
| placeholder | `colorNeutralForeground4`、`opacity: 1` | `colorNeutralForegroundDisabled` |
| content のアイコン | `colorNeutralForeground3` | `colorNeutralForegroundDisabled` |

出典: `useInputStyles.styles.ts:57-59,131-217,245-252,293-315`。hover、押下、invalid の規則は無効でないときだけ付く（`useInputStyles.styles.ts:349-353`）。非推奨の `*-shadow` は背景に `shadow2` を足す（`useInputStyles.styles.ts:193-201`）。

### フォーカス・動き・ハイコントラスト

- フォーカスは共通の下線だけで示し、輪郭の focus ring は描かない。input 自身は `outline-style: none`（`useInputStyles.styles.ts:254`）。
- 根の `:focus-within` に `outline: 2px solid transparent` を置く。強制色のモードでは、これがフォーカスの輪郭として見える（`useInputStyles.styles.ts:113-115`）。
- 強制色のモードでは、disabled の枠を `GrayText` にする（`useInputStyles.styles.ts:206-208`）。
- 動きを減らす設定では、下線の `transition-duration` と `transition-delay` を `0.01ms` にする（`useInputStyles.styles.ts:92-95,104-107`）。

### 実装の例

```html demo
<div style="display:flex;flex-direction:column;gap:12px;align-items:flex-start">
  <span class="fui-Input" data-size="small">
    <span class="fui-Input__contentBefore"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M10 2a4 4 0 1 0 0 8 4 4 0 0 0 0-8M7 6a3 3 0 1 1 6 0 3 3 0 0 1-6 0m-2 5a2 2 0 0 0-2 2c0 1.7.83 2.97 2.13 3.8A9 9 0 0 0 10 18c1.85 0 3.58-.39 4.87-1.2A4.4 4.4 0 0 0 17 13a2 2 0 0 0-2-2zm-1 2a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1c0 1.3-.62 2.28-1.67 2.95A8 8 0 0 1 10 17a8 8 0 0 1-4.33-1.05A3.4 3.4 0 0 1 4 13"/></svg></span>
    <input class="fui-Input__input" type="text" placeholder="small" aria-label="small の例">
  </span>
  <span class="fui-Input">
    <span class="fui-Input__contentBefore"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M10 2a4 4 0 1 0 0 8 4 4 0 0 0 0-8M7 6a3 3 0 1 1 6 0 3 3 0 0 1-6 0m-2 5a2 2 0 0 0-2 2c0 1.7.83 2.97 2.13 3.8A9 9 0 0 0 10 18c1.85 0 3.58-.39 4.87-1.2A4.4 4.4 0 0 0 17 13a2 2 0 0 0-2-2zm-1 2a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1c0 1.3-.62 2.28-1.67 2.95A8 8 0 0 1 10 17a8 8 0 0 1-4.33-1.05A3.4 3.4 0 0 1 4 13"/></svg></span>
    <input class="fui-Input__input" type="text" placeholder="medium（既定）" aria-label="medium の例">
  </span>
  <span class="fui-Input" data-size="large">
    <span class="fui-Input__contentBefore"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M10 2a4 4 0 1 0 0 8 4 4 0 0 0 0-8M7 6a3 3 0 1 1 6 0 3 3 0 0 1-6 0m-2 5a2 2 0 0 0-2 2c0 1.7.83 2.97 2.13 3.8A9 9 0 0 0 10 18c1.85 0 3.58-.39 4.87-1.2A4.4 4.4 0 0 0 17 13a2 2 0 0 0-2-2zm-1 2a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1c0 1.3-.62 2.28-1.67 2.95A8 8 0 0 1 10 17a8 8 0 0 1-4.33-1.05A3.4 3.4 0 0 1 4 13"/></svg></span>
    <input class="fui-Input__input" type="text" placeholder="large" aria-label="large の例">
  </span>
</div>
```

```html demo
<div style="display:flex;flex-wrap:wrap;gap:12px">
  <span class="fui-Input"><input class="fui-Input__input" type="text" placeholder="outline" aria-label="outline の例"></span>
  <span class="fui-Input" data-appearance="underline"><input class="fui-Input__input" type="text" placeholder="underline" aria-label="underline の例"></span>
  <span class="fui-Input" data-appearance="filled-darker"><input class="fui-Input__input" type="text" placeholder="filled-darker" aria-label="filled-darker の例"></span>
  <span class="fui-Input" data-appearance="filled-lighter"><input class="fui-Input__input" type="text" placeholder="filled-lighter" aria-label="filled-lighter の例"></span>
</div>
```

```html demo
<div style="display:flex;flex-wrap:wrap;gap:12px">
  <span class="fui-Input"><input class="fui-Input__input" type="text" value="不正な値" aria-invalid="true" aria-label="invalid の例"></span>
  <span class="fui-Input"><input class="fui-Input__input" type="text" placeholder="disabled" disabled aria-label="disabled の例"></span>
</div>
```

### v9 との差と未確認の点

- 状態の読み方: v9 は `input` の `disabled` と `aria-invalid` を見て根に class を付ける。この CSS は根から `:has(> .fui-Input__input:disabled)` などで読む。詳細度は v9 と同じ (0,1,0) にそろえた。
- Field の中では v9 が Field の size を引き継ぐ（`useInput.ts:23`）。React を使わない HTML では `data-size` を手で合わせる。
- `inputDefaultAppearance`（プロバイダーの上書き）は再現しない。
- 下線の動きは、v9 の誤りを含む実際の描画（遅延なし、ease）に合わせた。9.75.2 の描画と並べて比べ、`::after` の `transition` の計算値が、rest で `transform 0.05s ease 0s`、フォーカス中で `transform 0.2s ease 0s` と一致することを確かめた。

## Textarea

### 概要と使い分け（Do / Don't）

コメントのような長い自由形式の文字を入れてもらう部品である。1 行で足りるなら Input を使う。既定では大きさを変えられず、あふれた分はスクロールする。`data-resize` で利用者が大きさを変えられるようにできる。

- Do: ラベルを付け、プレースホルダーはそれを補う程度にする。入力量に見合う大きさにする。
- Don't: プレースホルダーに情報を詰め込む。欠かせない情報をプレースホルダーに置く。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

```text
span.fui-Textarea                  根: 枠、背景、下線の ::after
└─ textarea.fui-Textarea__textarea 主スロット
```

role、ARIA、キーボードはネイティブの `<textarea>` に任せる。無効は `disabled`、不正は `aria-invalid="true"`。

出典のファイル: `react-textarea/library/src/components/Textarea/useTextareaStyles.styles.ts`、`react-textarea/library/src/components/Textarea/Textarea.types.ts`、`react-textarea/library/src/components/Textarea/useTextarea.ts`

### バリエーション

| 属性 | 値 | 既定 | 出典 |
|---|---|---|---|
| `data-appearance` | `outline`、`filled-darker`、`filled-lighter`（非推奨の `*-shadow` も受ける）。underline はない | `outline` | `Textarea.types.ts:29-33`、`useTextarea.ts:24` |
| `data-size` | `small`、`medium`、`large` | `medium` | `Textarea.types.ts:56-58` |
| `data-resize` | `none`、`horizontal`、`vertical`、`both` | `none` | `Textarea.types.ts:49-51`、`useTextareaStyles.styles.ts:204-217` |

### 寸法（size ごとの表）

| 項目 | small | medium | large | 出典 |
|---|---|---|---|---|
| textarea の `min-height` | 40px | 52px | 64px | `useTextareaStyles.styles.ts:182,188,194`（直書き） |
| textarea の `max-height` | 200px | 260px | 320px | `useTextareaStyles.styles.ts:184,190,196`（直書き） |
| 上下の余白 | `spacingVerticalXS`（4px） | `spacingVerticalSNudge`（6px） | `spacingVerticalS`（8px） | `useTextareaStyles.styles.ts:183,189,195` |
| 左右の余白 | `calc(SNudge + XXS)`（8px） | `calc(MNudge + XXS)`（12px） | `calc(M + XXS)`（14px） | 同上 |
| 文字 | `caption1` | `body1` | `body2` | 同上 |
| 根の余白 | 下だけ `strokeWidthThick`（2px）。下線とリサイズの持ち手が重ならないようにする | 同 | 同 | `useTextareaStyles.styles.ts:21-22` |

余白を根ではなく textarea に持たせるのは、根の余白がリサイズの持ち手に効かないためである（`useTextareaStyles.styles.ts:179-180`）。

### 色と状態（トークン名の表）

| 状態 | outline | filled-darker / filled-lighter |
|---|---|---|
| 通常 | 背景 `colorNeutralBackground1`、枠 `colorNeutralStroke1`、下 `colorNeutralStrokeAccessible` | 背景 `colorNeutralBackground3` / `colorNeutralBackground1`、枠 `colorTransparentStroke` |
| hover | 枠 `colorNeutralStroke1Hover`、下 `colorNeutralStrokeAccessibleHover` | 枠 `colorTransparentStrokeInteractive` |
| 押下 | 枠 `colorNeutralStroke1Pressed`、下 `colorNeutralStrokeAccessiblePressed` | 規則なし |
| フォーカス | 枠 `colorNeutralStroke1Pressed`、**下 `colorCompoundBrandStroke`** | 枠 `colorTransparentStrokeInteractive` |
| invalid（フォーカスなし） | 全周 `colorPaletteRedBorder2` | 同 |
| disabled | 背景 `colorTransparentBackground`、枠 1px `colorNeutralStrokeDisabled`。appearance の規則と下線は付かない | 同 |
| 文字 / placeholder | `colorNeutralForeground1` / `colorNeutralForeground4`。disabled は両方 `colorNeutralForegroundDisabled`、`cursor: not-allowed` | 同 |

出典: `useTextareaStyles.styles.ts:28-35,97-146,158-177,230-240`。

### フォーカス・動き・ハイコントラスト

- 共通の下線。高さの計算に `strokeWidthThick` を使うが、値は同じ 2px（`useTextareaStyles.styles.ts:52,60-61`）。
- フォーカス中に hover すると、hover の枠の色が勝つ（章の冒頭の表）。
- 根の `:focus-within` に `strokeWidthThick` の透明な輪郭（`useTextareaStyles.styles.ts:90-94`）。強制色のモードで disabled の枠を `GrayText`（`useTextareaStyles.styles.ts:32-34`）。

### 実装の例

```html demo
<div style="display:flex;flex-wrap:wrap;gap:12px;align-items:flex-start">
  <span class="fui-Textarea" data-size="small"><textarea class="fui-Textarea__textarea" placeholder="small" aria-label="small の例"></textarea></span>
  <span class="fui-Textarea"><textarea class="fui-Textarea__textarea" placeholder="medium（既定）" aria-label="medium の例"></textarea></span>
  <span class="fui-Textarea" data-size="large" data-resize="vertical"><textarea class="fui-Textarea__textarea" placeholder="large、縦に変えられる" aria-label="large の例"></textarea></span>
</div>
```

```html demo
<div style="display:flex;flex-wrap:wrap;gap:12px;align-items:flex-start">
  <span class="fui-Textarea" data-appearance="filled-darker"><textarea class="fui-Textarea__textarea" placeholder="filled-darker" aria-label="filled-darker の例"></textarea></span>
  <span class="fui-Textarea"><textarea class="fui-Textarea__textarea" aria-invalid="true" aria-label="invalid の例">不正な値</textarea></span>
  <span class="fui-Textarea"><textarea class="fui-Textarea__textarea" placeholder="disabled" disabled aria-label="disabled の例"></textarea></span>
</div>
```

### v9 との差と未確認の点

- 状態は根から `:has(> .fui-Textarea__textarea:disabled)` などで読む。
- `data-resize` は v9 の `resize` の prop を根の属性に写したもの。v9 は textarea の class で切り替える。

## Select

### 概要と使い分け（Do / Don't）

4 つ以上の選択肢から 1 つを選ばせる。一覧はブラウザーのネイティブの見た目で、フォームの送信やモバイルに向く。選択肢の見た目を整えたいなら Dropdown、絞り込みや自由入力が要るなら Combobox を使う。

- Do: ラベルを短く中身を表すものにする。選択肢の形（名詞なら名詞）をそろえる。妥当なら「なし」を入れる。
- Don't: 選択肢を同じ語で書き出す。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

```text
span.fui-Select              根: 下線の ::after だけを持つ。枠はない
├─ select.fui-Select__select 主スロット。枠と背景はここ
└─ span.fui-Select__icon     ChevronDownRegular。pointer-events: none
```

role とキーボードはネイティブの `<select>` に任せる。`.fui-Select__select` は包みなしでも medium と outline の見た目になる。

出典のファイル: `react-select/library/src/components/Select/useSelectStyles.styles.ts`、`react-select/library/src/components/Select/useSelect.tsx`、`react-select/library/src/components/Select/Select.types.ts`

### バリエーション

| 属性（根に付ける） | 値 | 既定 | 出典 |
|---|---|---|---|
| `data-appearance` | `outline`、`underline`、`filled-darker`、`filled-lighter` | `outline` | `Select.types.ts:23-25` |
| `data-size` | `small`、`medium`、`large` | `medium` | `Select.types.ts:36-38` |

### 寸法（size ごとの表）

| 項目 | small | medium | large | 出典 |
|---|---|---|---|---|
| select の `height` | 24px | 32px | 40px | `useSelectStyles.styles.ts:21-25,147,153,159`（直書き） |
| 始端の余白 | `calc(SNudge + XXS)` = 8px | `calc(MNudge + XXS)` = 12px | `calc(M + SNudge)` = 18px | `useSelectStyles.styles.ts:51-55` |
| 終端の余白 | `calc(SNudge + 16px + XXS + XXS)` = 26px | `calc(MNudge + 20px + XXS + XXS)` = 34px | `calc(M + 24px + SNudge + SNudge)` = 48px | `useSelectStyles.styles.ts:34-47` |
| 文字 | `caption1` | `body1` | `body2` | `useSelectStyles.styles.ts:150,156,162` |
| アイコンの大きさ | 16px | 20px | 24px | `useSelectStyles.styles.ts:14-18,226-243` |
| アイコンの終端からの位置 | `SNudge`（6px） | `MNudge`（10px） | `M`（12px） | `useSelectStyles.styles.ts:229,235,241` |

`<select>` は子を持てないので、終端の余白に「根の余白 + アイコン + 間隔 + 内側の余白」を足し込む（`useSelectStyles.styles.ts:27-33`）。アイコンは `top` を持たず、根の `align-items: center` で縦の中央に来る（推論）。

### 色と状態（トークン名の表）

| 状態 | outline | underline | filled-darker / filled-lighter |
|---|---|---|---|
| 通常 | 背景 `colorNeutralBackground1`、枠 `colorNeutralStroke1`、下 `colorNeutralStrokeAccessible` | 背景 `colorTransparentBackground`、下だけ `colorNeutralStrokeAccessible`、角丸 0 | 背景 `colorNeutralBackground3` / `colorNeutralBackground1`、枠は透明 |
| hover | `colorNeutralStroke1Hover`、**下は変えない** | 規則なし | 規則なし |
| 押下 | `colorNeutralStroke1Pressed`、下は変えない | 規則なし | 規則なし |
| invalid（フォーカスなし） | 全周 `colorPaletteRedBorder2` | 下だけ | 全周 |
| disabled | 背景 `colorTransparentBackground`、枠 `colorNeutralStrokeDisabled`、文字 `colorNeutralForegroundDisabled` | 上と左右 `colorTransparentStrokeDisabled`、下 `colorNeutralStrokeDisabled` | 背景が透明になる |
| アイコン | `colorNeutralStrokeAccessible`。disabled は `colorNeutralForegroundDisabled` | 同 | 同 |

underline では、暗いテーマで読めるよう `option` の背景を `colorNeutralBackground1` にする（`useSelectStyles.styles.ts:184-187`）。出典: `useSelectStyles.styles.ts:109-244`。

### フォーカス・動き・ハイコントラスト

- 根の下線（共通の節の Select の作り）。select の `:focus` に `outline: 2px solid transparent`（`useSelectStyles.styles.ts:123-127`）。
- 強制色のモードで、disabled の枠とアイコンを `GrayText`（`useSelectStyles.styles.ts:134-136,222-224`）。

### 実装の例

```html demo
<div style="display:flex;flex-direction:column;gap:12px;max-width:280px">
  <span class="fui-Select" data-size="small">
    <select class="fui-Select__select" aria-label="small の例"><option>赤</option><option>緑</option><option>青</option></select>
    <span class="fui-Select__icon"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M15.85 7.65c.2.2.2.5 0 .7l-5.46 5.49a.55.55 0 0 1-.78 0L4.15 8.35a.5.5 0 1 1 .7-.7L10 12.8l5.15-5.16c.2-.2.5-.2.7 0"/></svg></span>
  </span>
  <span class="fui-Select">
    <select class="fui-Select__select" aria-label="medium の例"><option>赤</option><option>緑</option><option>青</option></select>
    <span class="fui-Select__icon"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M15.85 7.65c.2.2.2.5 0 .7l-5.46 5.49a.55.55 0 0 1-.78 0L4.15 8.35a.5.5 0 1 1 .7-.7L10 12.8l5.15-5.16c.2-.2.5-.2.7 0"/></svg></span>
  </span>
  <span class="fui-Select" data-size="large" data-appearance="underline">
    <select class="fui-Select__select" aria-label="large と underline の例"><option>赤</option><option>緑</option><option>青</option></select>
    <span class="fui-Select__icon"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M15.85 7.65c.2.2.2.5 0 .7l-5.46 5.49a.55.55 0 0 1-.78 0L4.15 8.35a.5.5 0 1 1 .7-.7L10 12.8l5.15-5.16c.2-.2.5-.2.7 0"/></svg></span>
  </span>
</div>
```

```html demo
<div style="display:flex;flex-direction:column;gap:12px;max-width:280px">
  <span class="fui-Select" data-appearance="filled-darker">
    <select class="fui-Select__select" aria-label="filled-darker の例"><option>filled-darker</option></select>
    <span class="fui-Select__icon"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M15.85 7.65c.2.2.2.5 0 .7l-5.46 5.49a.55.55 0 0 1-.78 0L4.15 8.35a.5.5 0 1 1 .7-.7L10 12.8l5.15-5.16c.2-.2.5-.2.7 0"/></svg></span>
  </span>
  <span class="fui-Select">
    <select class="fui-Select__select" aria-invalid="true" aria-label="invalid の例"><option>invalid</option></select>
    <span class="fui-Select__icon"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M15.85 7.65c.2.2.2.5 0 .7l-5.46 5.49a.55.55 0 0 1-.78 0L4.15 8.35a.5.5 0 1 1 .7-.7L10 12.8l5.15-5.16c.2-.2.5-.2.7 0"/></svg></span>
  </span>
  <span class="fui-Select">
    <select class="fui-Select__select" disabled aria-label="disabled の例"><option>disabled</option></select>
    <span class="fui-Select__icon"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M15.85 7.65c.2.2.2.5 0 .7l-5.46 5.49a.55.55 0 0 1-.78 0L4.15 8.35a.5.5 0 1 1 .7-.7L10 12.8l5.15-5.16c.2-.2.5-.2.7 0"/></svg></span>
  </span>
</div>
```

### v9 との差と未確認の点

- 既定の値を `.fui-Select__select` 自身に持たせた。v9 は size と appearance の class を select に付けるので、包みの有無で見た目は変わらない。
- 開いた一覧はブラウザーのネイティブの描画で、Fluent の見た目にはならない（v9 も同じ）。

## Combobox

### 概要と使い分け（Do / Don't）

一覧から選ぶか、つながった入力欄に打ち込んで候補を探すための部品である。選択肢がとても多いときに使う。短い一覧や自由入力を受けないときは Dropdown か Select を使う。

- Do: プレースホルダーを選ぶまでの手がかりにする。複雑な選択肢には読み上げ用の文字（v9 の `text`、この CSS では `data-text`）を付ける。
- Don't: プレースホルダーをラベルの代わりにする。
- 複数選択では、選んだものがプレースホルダーを置き換えないので、タグなど別の場所で示す。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

```text
div.fui-Combobox                         根: 枠、背景、下線の ::after。inline-grid
├─ input.fui-Combobox__input             role="combobox"、aria-expanded、開いたとき aria-controls と aria-activedescendant
├─ span.fui-Combobox__clearIcon          任意。aria-hidden="true"。出さないときは hidden 属性
├─ span.fui-Combobox__expandIcon         role="button"、tabindex="0"、aria-expanded、aria-label="Open"
└─ div.fui-Listbox.fui-Combobox__listbox role="listbox"（複数選択は role="menu"）、popover
```

- role と ARIA: `useTriggerSlot.ts:53-61`、`useCombobox.tsx:83,92`、`useComboboxExpandIconSlot.ts:38-44,56-67`。
- フォーカスは入力欄に残し、強調中の選択肢は `aria-activedescendant` で示す。キーボードで動かしたときだけ、選択肢に `data-activedescendant-focusvisible` を付ける（`react-aria/library/src/activedescendant/useActiveDescendant.ts:53-64`）。
- キーボード（`dropdownKeyActions.ts:31-90`）:

| キー | 閉じているとき | 開いているとき |
|---|---|---|
| ArrowDown、ArrowUp | 開く | 次、前へ |
| Enter | 開く | 選んで閉じる |
| Space | 開く | 単一選択は選んで閉じる。複数選択は選ぶだけ |
| Alt + ArrowUp | — | 選んで閉じる |
| Escape | — | 閉じる |
| Home、End | — | 最初、最後へ |
| PageUp、PageDown | — | 10 個ずつ動く |
| Tab | — | 単一選択なら強調中を選ぶ |

- 一覧の位置（`useComboboxPositioning.ts:17-27`）: 根の下、始端にそろえ、2px 離す。幅を根に合わせる。入らなければ上、後、前の順に試す。

出典のファイル: `react-combobox/library/src/components/Combobox/useComboboxStyles.styles.ts`、`react-combobox/library/src/components/Combobox/useCombobox.tsx`、`react-combobox/library/src/components/Combobox/useComboboxExpandIconSlot.ts`、`react-combobox/library/src/utils/useTriggerSlot.ts`、`react-combobox/library/src/utils/dropdownKeyActions.ts`、`react-combobox/library/src/utils/useComboboxPositioning.ts`、`react-combobox/library/src/utils/internalTokens.ts`

### バリエーション

| 属性 | 値 | 既定 | 出典 |
|---|---|---|---|
| `data-appearance` | `outline`、`underline`、`filled-darker`、`filled-lighter` | `outline` | `react-combobox/library/src/utils/ComboboxBase.types.ts:20-22` |
| `data-size` | `small`、`medium`、`large` | `medium` | `ComboboxBase.types.ts:80-82` |
| 複数選択 | 選択肢を `role="menuitemcheckbox"`、一覧を `role="menu"` にする | 単一選択 | `react-combobox/library/src/components/Option/useOption.tsx:115-117`、`react-combobox/library/src/components/Listbox/useListbox.ts:223` |

### 寸法（size ごとの表）

| 項目 | small | medium | large | 出典 |
|---|---|---|---|---|
| 根の `height`（固定） | 24px | 32px | 40px | `useComboboxStyles.styles.ts:18-22,104-116`（直書き） |
| 根の終端の余白 | `SNudge`（6px） | `MNudge`（10px） | `M`（12px） | `useComboboxStyles.styles.ts:106,110,115` |
| 根の `column-gap` | `XXS`（2px） | 2px | `SNudge`（6px） | `useComboboxStyles.styles.ts:32,113` |
| input の始端の余白 | `calc(SNudge + XXS)` = 8px | `calc(MNudge + XXS)` = 12px | `calc(M + SNudge)` = 18px | `useComboboxStyles.styles.ts:193-204` |
| 文字 | `caption1` | `body1` | `body2` | 同上 |
| アイコン | 16px、始端の間隔 2px | 20px、2px | 24px、6px | `internalTokens.ts:1-5`、`useComboboxStyles.styles.ts:256-276` |
| 根の最小幅 | 250px | 同 | 同 | `useComboboxStyles.styles.ts:36`（直書き） |
| 一覧 | `shadow16`、`borderRadiusMedium`、`max-height: 80vh` | 同 | 同 | `useComboboxStyles.styles.ts:86-91` |

アイコンの `::after` は、根の終端の余白の分だけ押せる範囲を広げる（`useComboboxStyles.styles.ts:230-240,259-275`）。

### 色と状態（トークン名の表）

| 状態 | outline | underline | filled-darker / filled-lighter |
|---|---|---|---|
| 通常 | 背景 `colorNeutralBackground1`、枠 `colorNeutralStroke1`、下 `colorNeutralStrokeAccessible` | 背景 `colorTransparentBackground`、下だけ `colorNeutralStrokeAccessible`、角丸 0 | 背景 `colorNeutralBackground3` / `colorNeutralBackground1`、枠 `colorTransparentStroke` |
| hover | `colorNeutralStroke1Hover`、下 `colorNeutralStrokeAccessibleHover` | 規則なし | 規則なし |
| 押下、フォーカス | `colorNeutralStroke1Pressed`、下 `colorNeutralStrokeAccessiblePressed` | 規則なし（下線は出る） | 規則なし（下線は出る） |
| invalid（フォーカスなし） | 全周 `colorPaletteRedBorder2` | 下だけ | 全周 |
| disabled | 背景 `colorTransparentBackground`、枠 `colorNeutralStrokeDisabled`、`cursor: not-allowed` | 同 | 同 |

| 部分 | 通常 | disabled |
|---|---|---|
| 入力文字 / placeholder | `colorNeutralForeground1` / `colorNeutralForeground4` | `colorNeutralForegroundDisabled` |
| アイコン | `colorNeutralStrokeAccessible`、`cursor: pointer` | `colorNeutralForegroundDisabled`、`not-allowed` |

消去アイコンを出すときは、開くアイコンを視覚的に隠す（`useComboboxStyles.styles.ts:245-253,334`）。出典: `useComboboxStyles.styles.ts:119-213,277-280`。

### フォーカス・動き・ハイコントラスト

- 共通の下線（`useComboboxStyles.styles.ts:47-83`）。根の `:focus-within` に `outline: 2px solid transparent`（`useComboboxStyles.styles.ts:40-45`）。
- フォーカス中に hover すると hover の枠の色が勝つ（章の冒頭の表）。
- 一覧の中の強調は Option の節を見る。強制色のモードで disabled の枠を `GrayText`（`useComboboxStyles.styles.ts:168-170`）。

### 実装の例

一覧は `popover` 属性で開閉する。JS がないと開かないので、2 つ目の例は開いた状態の一覧を単独で示す。

```html demo
<div style="display:flex;flex-direction:column;gap:12px;align-items:flex-start">
  <div class="fui-Combobox" data-fui-enhance>
    <input class="fui-Combobox__input" type="text" role="combobox" aria-expanded="false" placeholder="色を選ぶ" aria-label="色">
    <span class="fui-Combobox__clearIcon" aria-hidden="true" hidden><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="m4.09 4.22.06-.07a.5.5 0 0 1 .63-.06l.07.06L10 9.29l5.15-5.14a.5.5 0 0 1 .63-.06l.07.06c.18.17.2.44.06.63l-.06.07L10.71 10l5.14 5.15c.18.17.2.44.06.63l-.06.07a.5.5 0 0 1-.63.06l-.07-.06L10 10.71l-5.15 5.14a.5.5 0 0 1-.63.06l-.07-.06a.5.5 0 0 1-.06-.63l.06-.07L9.29 10 4.15 4.85a.5.5 0 0 1-.06-.63l.06-.07z"/></svg></span>
    <span class="fui-Combobox__expandIcon" role="button" tabindex="0" aria-expanded="false" aria-label="Open"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M15.85 7.65c.2.2.2.5 0 .7l-5.46 5.49a.55.55 0 0 1-.78 0L4.15 8.35a.5.5 0 1 1 .7-.7L10 12.8l5.15-5.16c.2-.2.5-.2.7 0"/></svg></span>
    <div class="fui-Listbox fui-Combobox__listbox" id="te-cb-list" role="listbox" popover="manual">
      <div class="fui-Option" id="te-cb-o1" role="option" aria-selected="false"><span class="fui-Option__checkIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7.03 13.9 3.56 10a.75.75 0 0 0-1.12 1l4 4.5c.29.32.79.34 1.09.03l10.5-10.5a.75.75 0 0 0-1.06-1.06z"/></svg></span>赤</div>
      <div class="fui-Option" id="te-cb-o2" role="option" aria-selected="false"><span class="fui-Option__checkIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7.03 13.9 3.56 10a.75.75 0 0 0-1.12 1l4 4.5c.29.32.79.34 1.09.03l10.5-10.5a.75.75 0 0 0-1.06-1.06z"/></svg></span>緑</div>
      <div class="fui-Option" id="te-cb-o3" role="option" aria-selected="false"><span class="fui-Option__checkIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7.03 13.9 3.56 10a.75.75 0 0 0-1.12 1l4 4.5c.29.32.79.34 1.09.03l10.5-10.5a.75.75 0 0 0-1.06-1.06z"/></svg></span>青</div>
    </div>
  </div>
  <div class="fui-Combobox" data-size="large" data-appearance="filled-darker">
    <input class="fui-Combobox__input" type="text" role="combobox" aria-expanded="false" value="緑" aria-label="large と filled-darker の例">
    <span class="fui-Combobox__clearIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="m4.09 4.22.06-.07a.5.5 0 0 1 .63-.06l.07.06L10 9.29l5.15-5.14a.5.5 0 0 1 .63-.06l.07.06c.18.17.2.44.06.63l-.06.07L10.71 10l5.14 5.15c.18.17.2.44.06.63l-.06.07a.5.5 0 0 1-.63.06l-.07-.06L10 10.71l-5.15 5.14a.5.5 0 0 1-.63.06l-.07-.06a.5.5 0 0 1-.06-.63l.06-.07L9.29 10 4.15 4.85a.5.5 0 0 1-.06-.63l.06-.07z"/></svg></span>
    <span class="fui-Combobox__expandIcon" role="button" tabindex="0" aria-expanded="false" aria-label="Open"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M15.85 7.65c.2.2.2.5 0 .7l-5.46 5.49a.55.55 0 0 1-.78 0L4.15 8.35a.5.5 0 1 1 .7-.7L10 12.8l5.15-5.16c.2-.2.5-.2.7 0"/></svg></span>
  </div>
  <div class="fui-Combobox" data-size="small">
    <input class="fui-Combobox__input" type="text" role="combobox" aria-expanded="false" placeholder="disabled" disabled aria-label="disabled の例">
    <span class="fui-Combobox__expandIcon" role="button" tabindex="-1" aria-expanded="false" aria-disabled="true" aria-label="Open"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M15.85 7.65c.2.2.2.5 0 .7l-5.46 5.49a.55.55 0 0 1-.78 0L4.15 8.35a.5.5 0 1 1 .7-.7L10 12.8l5.15-5.16c.2-.2.5-.2.7 0"/></svg></span>
  </div>
</div>
```

```html demo
<div class="fui-Listbox fui-Combobox__listbox" role="listbox" aria-label="開いた一覧の例" style="width:250px">
  <div class="fui-Option" role="option" aria-selected="false"><span class="fui-Option__checkIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7.03 13.9 3.56 10a.75.75 0 0 0-1.12 1l4 4.5c.29.32.79.34 1.09.03l10.5-10.5a.75.75 0 0 0-1.06-1.06z"/></svg></span>赤</div>
  <div class="fui-Option" role="option" aria-selected="true" data-activedescendant-focusvisible><span class="fui-Option__checkIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7.03 13.9 3.56 10a.75.75 0 0 0-1.12 1l4 4.5c.29.32.79.34 1.09.03l10.5-10.5a.75.75 0 0 0-1.06-1.06z"/></svg></span>緑（選択中、キーボードで強調中）</div>
  <div class="fui-Option" role="option" aria-selected="false" aria-disabled="true"><span class="fui-Option__checkIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7.03 13.9 3.56 10a.75.75 0 0 0-1.12 1l4 4.5c.29.32.79.34 1.09.03l10.5-10.5a.75.75 0 0 0-1.06-1.06z"/></svg></span>青（無効）</div>
</div>
```

### v9 との差と未確認の点

- v9 は一覧を既定で Portal に描き、Floating UI で位置を決める。この JS は `popover="manual"` と `position: fixed` の座標で置き、入らないときの代わりは「上」だけを試す。`after`、`before` などへの退避と、v9 の `autoSize` の正確な高さの計算は再現していない（`max-height` を `min(80vh, 空いている高さ)` にするのは推論）。
- 打ち込みは、値で始まる最初の選択肢を強調するだけで、一覧を絞り込まない。v9 でも絞り込みは利用者のコードの責任である。`freeform` と、フォーカスが外れたときに値を選択に戻す処理は再現していない。
- invalid の規則は、v9 でも無効かどうかを見ない（`useComboboxStyles.styles.ts:301-302`）。`:not(:focus-within)` を含む詳細度 (0,2,0) が disabled の (0,1,0) に勝つので、無効かつ不正のときは赤い枠になると読める（推論。描画では確かめていない）。
- `aria-autocomplete` は v9 のスナップショットにないので付けない。
- inline の一覧（v9 の `inlinePopup`）の `z-index: 1` は、popover で最上層に出すので書いていない。

## Dropdown

### 概要と使い分け（Do / Don't）

一覧から 1 つ以上を選ばせる部品である。選択肢に独自の見た目が要るフォームや、情報の絞り込みと並べ替えに使う。フォーム、とくにモバイルでは Select の方がアクセシビリティを備える。自由入力や絞り込みが要るなら Combobox を使う。

- Do: 1 語か短い句の説明的なラベルを付ける。選択肢の形をそろえる。妥当なら「なし」を入れる。
- Don't: 各選択肢を同じ語で書き出す。
- 単一選択は選ぶと閉じる。複数選択は外を押すか Escape まで開いたまま。選択が入りきらないときは選んだ数を示す。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

```text
div.fui-Dropdown                          根: 枠、背景、下線の ::after。inline-flex
├─ button.fui-Dropdown__button            role="combobox"、type="button"、aria-expanded、開いたとき aria-controls と aria-activedescendant
│   ├─ span                               選択値またはプレースホルダーの文字
│   └─ span.fui-Dropdown__expandIcon      ChevronDownRegular
├─ button.fui-Dropdown__clearButton       任意。aria-label="Clear selection"。出さないときは hidden 属性
└─ div.fui-Listbox.fui-Dropdown__listbox  role="listbox"（複数選択は role="menu"）、popover
    ├─ div.fui-Option                     role="option" と aria-selected（複数選択は role="menuitemcheckbox" と aria-checked）
    │   └─ span.fui-Option__checkIcon     aria-hidden="true"
    └─ div.fui-OptionGroup                role="group"、aria-labelledby
        └─ span.fui-OptionGroup__label    role="presentation"
```

- 描画の順: `renderDropdown.tsx:20-42`（開くアイコンは button の中、消去ボタンは外）。DOM の実例: `Dropdown.test.tsx.snap:5-57`。
- プレースホルダーを出している間は、button に `data-placeholder-visible` を付ける。v9 の内部の状態 `placeholderVisible`（`useDropdownStyles.styles.ts:261,285`）を写す独自の属性である。JS は button の `data-placeholder` の文字をプレースホルダーとして使う。
- キーボードは Combobox と同じ表（`dropdownKeyActions.ts:31-90`）。Dropdown では、打った文字で始まる選択肢へ移る。フォーカスは button に残る。
- 選択肢のチェック: 単一選択は `CheckmarkFilled`（20 の形を 1em で）を選ばれたときだけ見せる。複数選択は 16px の枠の中に `Checkmark12Filled` を置く（`useOption.tsx:48-50`）。

出典のファイル: `react-combobox/library/src/components/Dropdown/useDropdownStyles.styles.ts`、`react-combobox/library/src/components/Dropdown/useDropdown.tsx`、`react-combobox/library/src/components/Dropdown/renderDropdown.tsx`、`react-combobox/library/src/components/Dropdown/__snapshots__/Dropdown.test.tsx.snap`、`react-combobox/library/src/components/Listbox/useListboxStyles.styles.ts`、`react-combobox/library/src/components/Option/useOptionStyles.styles.ts`、`react-combobox/library/src/components/Option/useOption.tsx`、`react-combobox/library/src/components/OptionGroup/useOptionGroupStyles.styles.ts`、`react-combobox/library/src/components/OptionGroup/useOptionGroup.ts`

### バリエーション

| 属性 | 値 | 既定 | 出典 |
|---|---|---|---|
| `data-appearance` | `outline`、`underline`、`filled-darker`、`filled-lighter` | `outline` | `ComboboxBase.types.ts:20-22` |
| `data-size` | `small`、`medium`、`large` | `medium` | `ComboboxBase.types.ts:80-82` |
| 複数選択 | 選択肢を `role="menuitemcheckbox"`、一覧を `role="menu"` にする | 単一選択 | `useOption.tsx:115-117` |

### 寸法（size ごとの表）

Dropdown

| 項目 | small | medium | large | 出典 |
|---|---|---|---|---|
| button の余白（上下 / 終端 / 始端） | 3px / 6px / 8px | 5px / 10px / 12px | 7px / 12px / 18px | `useDropdownStyles.styles.ts:125-143`（上下は直書き） |
| 文字 | `caption1` | `body1` | `body2` | 同上 |
| 高さ（計算） | 3 + 16 + 3 + 枠 2 = 24px | 5 + 20 + 5 + 2 = 32px | 7 + 22 + 7 + 2 = 40px | 推論（上の値から計算） |
| button の `column-gap` | 2px | 2px | 6px | `useDropdownStyles.styles.ts:106,138` |
| アイコン / 始端の間隔 | 16px / 2px | 20px / 2px | 24px / 6px | `useDropdownStyles.styles.ts:224-236` |
| 根の最小幅 | 250px | 同 | 同 | `useDropdownStyles.styles.ts:26`（直書き） |
| 消去ボタンの終端の間隔 | `MNudge`（10px） | 同 | 同 | `useDropdownStyles.styles.ts:250` |

Listbox、Option、OptionGroup（size によらない）

| 項目 | 値 | 出典 |
|---|---|---|
| Listbox | 背景 `colorNeutralBackground1`、縦の flex、`min-width: 160px`、`overflow-y: auto`、`outline: 1px solid colorTransparentStroke`、余白 `spacingHorizontalXS`（4px）、行の間隔 `spacingHorizontalXXS`（2px） | `useListboxStyles.styles.ts:16-26` |
| 一覧のスロット（Dropdown、Combobox、TagPicker） | `shadow16`、`borderRadiusMedium`、`max-height: 80vh` | `useDropdownStyles.styles.ts:83-88` |
| Option | 余白 `spacingVerticalSNudge spacingHorizontalS`（6px 8px）、`column-gap: 4px`、`borderRadiusMedium`、`fontSizeBase300` / `lineHeightBase300`。高さは 6 + 20 + 6 = 32px（推論） | `useOptionStyles.styles.ts:18-30` |
| 単一選択のチェック | `fontSizeBase400`（16px）、始端 -2px、終端 2px、選ばれていないときは `visibility: hidden` | `useOptionStyles.styles.ts:74-90` |
| 複数選択のチェック | 16 × 16px、`font-size: 12px`、枠 1px `colorNeutralStrokeAccessible`、角丸 `borderRadiusSmall` | `useOptionStyles.styles.ts:92-106` |
| OptionGroup | 縦の flex、行の間隔 2px。最後以外は下に 1px `colorNeutralStroke2` の区切り線（左右 -4px、下 4px） | `useOptionGroupStyles.styles.ts:17-28` |
| OptionGroup のラベル | `colorNeutralForeground3`、`fontSizeBase200` / `lineHeightBase200`、`fontWeightSemibold`、余白 8px 6px | `useOptionGroupStyles.styles.ts:31-39` |

### 色と状態（トークン名の表）

Dropdown の根の色は Combobox と同じ表である（`useDropdownStyles.styles.ts:146-197`）。違いは次のとおり。

| 項目 | 値 | 出典 |
|---|---|---|
| button の文字 | `colorNeutralForeground1`。プレースホルダー中は `colorNeutralForeground4` | `useDropdownStyles.styles.ts:105,120-122` |
| disabled の文字 | `colorNeutralForegroundDisabled`、`cursor: not-allowed` | `useDropdownStyles.styles.ts:199-202` |
| 消去ボタンを出すとき | 開くアイコンを `display: none`（Combobox は視覚的に隠す） | `useDropdownStyles.styles.ts:204-206,308` |

Option

| 状態 | 背景 | 文字 | チェック | 出典 |
|---|---|---|---|---|
| 通常 | なし（Listbox の背景が見える） | `colorNeutralForeground1` | 単一選択は隠す | `useOptionStyles.styles.ts:21` |
| hover | `colorNeutralBackground1Hover` | `colorNeutralForeground1Hover` | 複数選択の枠 `colorNeutralForeground1Hover` | `useOptionStyles.styles.ts:33-37` |
| 押下 | `colorNeutralBackground1Pressed` | `colorNeutralForeground1Pressed` | 枠は `colorNeutralForeground1Hover` のまま | `useOptionStyles.styles.ts:39-43` |
| 選択（単一） | 変化なし | 変化なし | 見せる | `useOptionStyles.styles.ts:88-90` |
| 選択（複数） | 変化なし | 変化なし | 背景と枠 `colorCompoundBrandBackground`、色 `colorNeutralForegroundInverted` | `useOptionStyles.styles.ts:108-112` |
| disabled（`aria-disabled="true"`） | hover と押下なし | `colorNeutralForegroundDisabled`、`cursor: default` | 色と複数選択の枠 `colorNeutralForegroundDisabled` | `useOptionStyles.styles.ts:63-70,114-121` |

hover の枠の規則は詳細度 (0,3,0) なので、選ばれた複数選択のチェックでも hover 中は枠が `colorNeutralForeground1Hover` になる（v9 と同じ）。

### フォーカス・動き・ハイコントラスト

- Dropdown の根は共通の下線。消去ボタンにフォーカスがあるときは、`@supports selector(:has(*))` の中で下線を消す（`useDropdownStyles.styles.ts:75-80`）。
- 消去ボタン自身は `createFocusOutlineStyle()` の focus ring（2px `colorStrokeFocus2`、外側 2px、`borderRadiusMedium`）を持つ（`useDropdownStyles.styles.ts:254`、`react-tabster/src/focus/createFocusOutlineStyle.ts:55-112`）。v9 の `[data-fui-focus-visible]` は `:focus-visible` で近似した。
- キーボードで強調中の選択肢は、`::after` に 2px `colorStrokeFocus2` の枠を外側 2px に描く（`useOptionStyles.styles.ts:46-61`）。
- 選択肢の背景の変化に transition はない。
- 強制色のモードで、Dropdown の disabled の枠、Option の disabled の文字とチェックを `GrayText`、消去ボタンの focus ring を `Highlight` にする（`useDropdownStyles.styles.ts:194-196`、`useOptionStyles.styles.ts:67-69,117-119`）。

### 実装の例

```html demo
<div style="display:flex;flex-direction:column;gap:12px;align-items:flex-start">
  <div class="fui-Dropdown" data-fui-enhance>
    <button class="fui-Dropdown__button" type="button" role="combobox" aria-expanded="false" aria-label="果物" data-placeholder="果物を選ぶ" data-placeholder-visible>
      <span>果物を選ぶ</span>
      <span class="fui-Dropdown__expandIcon"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M15.85 7.65c.2.2.2.5 0 .7l-5.46 5.49a.55.55 0 0 1-.78 0L4.15 8.35a.5.5 0 1 1 .7-.7L10 12.8l5.15-5.16c.2-.2.5-.2.7 0"/></svg></span>
    </button>
    <div class="fui-Listbox fui-Dropdown__listbox" id="te-dd-list" role="listbox" popover="manual">
      <div class="fui-Option" id="te-dd-o1" role="option" aria-selected="false"><span class="fui-Option__checkIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7.03 13.9 3.56 10a.75.75 0 0 0-1.12 1l4 4.5c.29.32.79.34 1.09.03l10.5-10.5a.75.75 0 0 0-1.06-1.06z"/></svg></span>りんご</div>
      <div class="fui-Option" id="te-dd-o2" role="option" aria-selected="false"><span class="fui-Option__checkIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7.03 13.9 3.56 10a.75.75 0 0 0-1.12 1l4 4.5c.29.32.79.34 1.09.03l10.5-10.5a.75.75 0 0 0-1.06-1.06z"/></svg></span>みかん</div>
      <div class="fui-Option" id="te-dd-o3" role="option" aria-selected="false"><span class="fui-Option__checkIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7.03 13.9 3.56 10a.75.75 0 0 0-1.12 1l4 4.5c.29.32.79.34 1.09.03l10.5-10.5a.75.75 0 0 0-1.06-1.06z"/></svg></span>ぶどう</div>
    </div>
  </div>
  <div class="fui-Dropdown" data-size="small" data-appearance="underline">
    <button class="fui-Dropdown__button" type="button" role="combobox" aria-expanded="false" aria-label="small と underline の例">
      <span>みかん</span>
      <span class="fui-Dropdown__expandIcon"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M15.85 7.65c.2.2.2.5 0 .7l-5.46 5.49a.55.55 0 0 1-.78 0L4.15 8.35a.5.5 0 1 1 .7-.7L10 12.8l5.15-5.16c.2-.2.5-.2.7 0"/></svg></span>
    </button>
  </div>
  <div class="fui-Dropdown" data-size="large">
    <button class="fui-Dropdown__button" type="button" role="combobox" aria-expanded="false" aria-label="large と消去ボタンの例">
      <span>ぶどう</span>
      <span class="fui-Dropdown__expandIcon"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M15.85 7.65c.2.2.2.5 0 .7l-5.46 5.49a.55.55 0 0 1-.78 0L4.15 8.35a.5.5 0 1 1 .7-.7L10 12.8l5.15-5.16c.2-.2.5-.2.7 0"/></svg></span>
    </button>
    <button class="fui-Dropdown__clearButton" type="button" aria-label="Clear selection"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="m4.09 4.22.06-.07a.5.5 0 0 1 .63-.06l.07.06L10 9.29l5.15-5.14a.5.5 0 0 1 .63-.06l.07.06c.18.17.2.44.06.63l-.06.07L10.71 10l5.14 5.15c.18.17.2.44.06.63l-.06.07a.5.5 0 0 1-.63.06l-.07-.06L10 10.71l-5.15 5.14a.5.5 0 0 1-.63.06l-.07-.06a.5.5 0 0 1-.06-.63l.06-.07L9.29 10 4.15 4.85a.5.5 0 0 1-.06-.63l.06-.07z"/></svg></button>
  </div>
  <div class="fui-Dropdown">
    <button class="fui-Dropdown__button" type="button" role="combobox" aria-expanded="false" aria-label="disabled の例" disabled>
      <span>disabled</span>
      <span class="fui-Dropdown__expandIcon"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M15.85 7.65c.2.2.2.5 0 .7l-5.46 5.49a.55.55 0 0 1-.78 0L4.15 8.35a.5.5 0 1 1 .7-.7L10 12.8l5.15-5.16c.2-.2.5-.2.7 0"/></svg></span>
    </button>
  </div>
</div>
```

開いた一覧を単独で示す（OptionGroup、選択、キーボードの強調、無効）。

```html demo
<div class="fui-Listbox fui-Dropdown__listbox" role="listbox" aria-label="開いた一覧の例" style="width:250px">
  <div class="fui-OptionGroup" role="group" aria-labelledby="te-og1">
    <span class="fui-OptionGroup__label" id="te-og1" role="presentation">暖色</span>
    <div class="fui-Option" role="option" aria-selected="true"><span class="fui-Option__checkIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7.03 13.9 3.56 10a.75.75 0 0 0-1.12 1l4 4.5c.29.32.79.34 1.09.03l10.5-10.5a.75.75 0 0 0-1.06-1.06z"/></svg></span>赤</div>
    <div class="fui-Option" role="option" aria-selected="false" data-activedescendant-focusvisible><span class="fui-Option__checkIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7.03 13.9 3.56 10a.75.75 0 0 0-1.12 1l4 4.5c.29.32.79.34 1.09.03l10.5-10.5a.75.75 0 0 0-1.06-1.06z"/></svg></span>橙</div>
  </div>
  <div class="fui-OptionGroup" role="group" aria-labelledby="te-og2">
    <span class="fui-OptionGroup__label" id="te-og2" role="presentation">寒色</span>
    <div class="fui-Option" role="option" aria-selected="false"><span class="fui-Option__checkIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7.03 13.9 3.56 10a.75.75 0 0 0-1.12 1l4 4.5c.29.32.79.34 1.09.03l10.5-10.5a.75.75 0 0 0-1.06-1.06z"/></svg></span>青</div>
    <div class="fui-Option" role="option" aria-selected="false" aria-disabled="true"><span class="fui-Option__checkIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7.03 13.9 3.56 10a.75.75 0 0 0-1.12 1l4 4.5c.29.32.79.34 1.09.03l10.5-10.5a.75.75 0 0 0-1.06-1.06z"/></svg></span>藍（無効）</div>
  </div>
</div>
```

複数選択の一覧。

```html demo
<div class="fui-Listbox fui-Dropdown__listbox" role="menu" aria-label="複数選択の一覧の例" style="width:250px">
  <div class="fui-Option" role="menuitemcheckbox" aria-checked="true"><span class="fui-Option__checkIcon" aria-hidden="true"><svg class="fui-Icon" width="12" height="12" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true"><path d="M9.76 3.2c.3.29.32.76.04 1.06l-4.25 4.5a.75.75 0 0 1-1.08.02L2.22 6.53a.75.75 0 0 1 1.06-1.06l1.7 1.7L8.7 3.24a.75.75 0 0 1 1.06-.04"/></svg></span>月曜日</div>
  <div class="fui-Option" role="menuitemcheckbox" aria-checked="false"><span class="fui-Option__checkIcon" aria-hidden="true"><svg class="fui-Icon" width="12" height="12" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true"><path d="M9.76 3.2c.3.29.32.76.04 1.06l-4.25 4.5a.75.75 0 0 1-1.08.02L2.22 6.53a.75.75 0 0 1 1.06-1.06l1.7 1.7L8.7 3.24a.75.75 0 0 1 1.06-.04"/></svg></span>火曜日</div>
  <div class="fui-Option" role="menuitemcheckbox" aria-checked="true" aria-disabled="true"><span class="fui-Option__checkIcon" aria-hidden="true"><svg class="fui-Icon" width="12" height="12" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true"><path d="M9.76 3.2c.3.29.32.76.04 1.06l-4.25 4.5a.75.75 0 0 1-1.08.02L2.22 6.53a.75.75 0 0 1 1.06-1.06l1.7 1.7L8.7 3.24a.75.75 0 0 1 1.06-.04"/></svg></span>水曜日（無効）</div>
</div>
```

### v9 との差と未確認の点

- 一覧の位置と開閉は Combobox の節と同じ近似である。
- 複数選択の表示の文字は、選んだものを「, 」でつないだものにした。v9 の既定の `value` の作り方とは突き合わせていない。
- v9 は複数選択で選ばれていないとき、チェックの SVG を描かない（`useOption.tsx:48-50`）。React を使わない HTML では SVG を置いたまま、CSS で `display: none` にする（v9 にない追加）。
- 打った文字で選択肢を探す処理（500ms で区切る）は、v9 の実装と突き合わせていない近似である。
- Listbox の `outline: 1px solid colorTransparentStroke` は、強制色のモードで一覧の輪郭を見せるための透明な線と読める（推論。v9 にコメントはない）。
- `popover` の UA の既定（`border`、`margin: auto`、`inset: 0`、`color: CanvasText`）を打ち消す規則と、閉じた一覧を `display: none` にする規則は、v9 にない追加である。

## SearchBox

### 概要と使い分け（Do / Don't）

情報にすばやくたどり着くための入力欄である。消去と絞り込みができる。

- Do: 検索のフォームの並びを一定にする。入れ物に合わせて伸縮させ、400% の拡大でも機能を保つ。結果は求めるものに近い順に出す。
- Don't: 狭い画面で無理に全幅を保つ。虫眼鏡のアイコンに畳み、押すと全幅に広げてよい。
- 消去ボタンは中身があるときだけ出す、とサイトは書く（v9 の実装との差は下の未確認の点）。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

```text
span.fui-SearchBox.fui-Input                                   根。Input の根に SearchBox の class を重ねる
├─ span.fui-SearchBox__contentBefore.fui-Input__contentBefore  既定で SearchRegular
├─ input.fui-SearchBox__input.fui-Input__input                 type="search"
└─ span.fui-SearchBox__contentAfter.fui-Input__contentAfter
    └─ span.fui-SearchBox__dismiss                             role="button"、aria-label="clear"、tabindex="-1"。DismissRegular
```

- SearchBox は Input の状態とスタイルの上に作る。SearchBox の class は Input の mergeClasses の最後に入るので、Input の規則に勝つ（`useSearchBoxStyles.styles.ts:171`）。
- 消去ボタンは Tab で止まらない（`tabindex="-1"`）。押すと値を空にして入力欄にフォーカスを戻す（`useSearchBox.tsx:125-159`。この JS が再現する）。
- フォーカスの状態は v9 では React の state（根の onFocus と onBlur）で持つ。この CSS は `:focus-within` で表す。

出典のファイル: `react-search/library/src/components/SearchBox/useSearchBoxStyles.styles.ts`、`react-search/library/src/components/SearchBox/useSearchBox.tsx`、`react-search/library/src/components/SearchBox/renderSearchBox.tsx`

### バリエーション

| 属性 | 値 | 既定 | 出典 |
|---|---|---|---|
| `data-appearance` | Input と同じ | `outline` | `useSearchBox.tsx:33` |
| `data-size` | `small`、`medium`、`large` | `medium` | `useSearchBox.tsx:33` |

### 寸法（size ごとの表）

Input の値を上書きするものだけを示す。高さ、文字、枠は Input と同じ。

| 項目 | small | medium | large | 出典 |
|---|---|---|---|---|
| 根の左右の余白 | `SNudge`（6px） | `S`（8px） | `MNudge`（10px） | `useSearchBoxStyles.styles.ts:20-41` |
| 根の `column-gap` | 0 | 0 | 0 | 同上 |
| 根の `max-width` | 468px | 同 | 同 | 同上（直書き） |
| フォーカスなしの根の終端の余白 | 0 | 0 | 0 | `useSearchBoxStyles.styles.ts:56-58,128` |
| input の始端 / 終端の余白 | 6px / フォーカス中 0、なし 6px | 6px / 0、8px | 6px / 0、10px | `useSearchBoxStyles.styles.ts:43-45,61-71,135` |
| contentAfter | 始端の余白 `spacingHorizontalM`（12px）、`column-gap: spacingHorizontalXS`（4px） | 同 | 同 | `useSearchBoxStyles.styles.ts:74-77` |
| フォーカスなしの contentAfter | 幅と高さ 0、`overflow: hidden` | 同 | 同 | `useSearchBoxStyles.styles.ts:78-83,162` |
| 消去ボタンのアイコン | 16px | 20px | 24px | `useSearchBoxStyles.styles.ts:86-110` |

### 色と状態（トークン名の表）

- 根、入力欄、contentBefore の色は Input と同じ。
- 消去ボタンは `colorNeutralForeground3`、disabled は `colorNeutralForegroundDisabled`（`useSearchBoxStyles.styles.ts:88,97-99`）。hover の規則はない。

### フォーカス・動き・ハイコントラスト

- Input と同じ（共通の下線、透明な輪郭、disabled の `GrayText`）。
- フォーカスで消去ボタンが現れる。現れ方に transition はない。
- `::-webkit-search-decoration` と `::-webkit-search-cancel-button` を消す（`useSearchBoxStyles.styles.ts:47-53`）。

### 実装の例

```html demo
<div style="display:flex;flex-direction:column;gap:12px;align-items:flex-start">
  <span class="fui-SearchBox fui-Input" data-size="small" data-fui-enhance>
    <span class="fui-SearchBox__contentBefore fui-Input__contentBefore"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M13.73 14.44a6.5 6.5 0 1 1 .7-.7l3.42 3.4a.5.5 0 0 1-.63.77l-.07-.06zm-.71-.71A5.5 5.5 0 0 0 15 9.5a5.5 5.5 0 1 0-1.98 4.23"/></svg></span>
    <input class="fui-SearchBox__input fui-Input__input" type="search" placeholder="検索" aria-label="small の検索">
    <span class="fui-SearchBox__contentAfter fui-Input__contentAfter"><span class="fui-SearchBox__dismiss" role="button" aria-label="clear" tabindex="-1"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="m4.09 4.22.06-.07a.5.5 0 0 1 .63-.06l.07.06L10 9.29l5.15-5.14a.5.5 0 0 1 .63-.06l.07.06c.18.17.2.44.06.63l-.06.07L10.71 10l5.14 5.15c.18.17.2.44.06.63l-.06.07a.5.5 0 0 1-.63.06l-.07-.06L10 10.71l-5.15 5.14a.5.5 0 0 1-.63.06l-.07-.06a.5.5 0 0 1-.06-.63l.06-.07L9.29 10 4.15 4.85a.5.5 0 0 1-.06-.63l.06-.07z"/></svg></span></span>
  </span>
  <span class="fui-SearchBox fui-Input" data-fui-enhance>
    <span class="fui-SearchBox__contentBefore fui-Input__contentBefore"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M13.73 14.44a6.5 6.5 0 1 1 .7-.7l3.42 3.4a.5.5 0 0 1-.63.77l-.07-.06zm-.71-.71A5.5 5.5 0 0 0 15 9.5a5.5 5.5 0 1 0-1.98 4.23"/></svg></span>
    <input class="fui-SearchBox__input fui-Input__input" type="search" placeholder="検索（フォーカスで消去ボタンが出る）" aria-label="medium の検索">
    <span class="fui-SearchBox__contentAfter fui-Input__contentAfter"><span class="fui-SearchBox__dismiss" role="button" aria-label="clear" tabindex="-1"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="m4.09 4.22.06-.07a.5.5 0 0 1 .63-.06l.07.06L10 9.29l5.15-5.14a.5.5 0 0 1 .63-.06l.07.06c.18.17.2.44.06.63l-.06.07L10.71 10l5.14 5.15c.18.17.2.44.06.63l-.06.07a.5.5 0 0 1-.63.06l-.07-.06L10 10.71l-5.15 5.14a.5.5 0 0 1-.63.06l-.07-.06a.5.5 0 0 1-.06-.63l.06-.07L9.29 10 4.15 4.85a.5.5 0 0 1-.06-.63l.06-.07z"/></svg></span></span>
  </span>
  <span class="fui-SearchBox fui-Input" data-size="large" data-appearance="filled-darker">
    <span class="fui-SearchBox__contentBefore fui-Input__contentBefore"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M13.73 14.44a6.5 6.5 0 1 1 .7-.7l3.42 3.4a.5.5 0 0 1-.63.77l-.07-.06zm-.71-.71A5.5 5.5 0 0 0 15 9.5a5.5 5.5 0 1 0-1.98 4.23"/></svg></span>
    <input class="fui-SearchBox__input fui-Input__input" type="search" placeholder="disabled" disabled aria-label="disabled の検索">
    <span class="fui-SearchBox__contentAfter fui-Input__contentAfter"><span class="fui-SearchBox__dismiss" role="button" aria-label="clear" tabindex="-1" aria-disabled="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="m4.09 4.22.06-.07a.5.5 0 0 1 .63-.06l.07.06L10 9.29l5.15-5.14a.5.5 0 0 1 .63-.06l.07.06c.18.17.2.44.06.63l-.06.07L10.71 10l5.14 5.15c.18.17.2.44.06.63l-.06.07a.5.5 0 0 1-.63.06l-.07-.06L10 10.71l-5.15 5.14a.5.5 0 0 1-.63.06l-.07-.06a.5.5 0 0 1-.06-.63l.06-.07L9.29 10 4.15 4.85a.5.5 0 0 1-.06-.63l.06-.07z"/></svg></span></span>
  </span>
</div>
```

### v9 との差と未確認の点

- サイトは消去ボタンを「中身があるときだけ出す」と書くが、v9 のコードはフォーカス中なら値の有無によらず出す（`useSearchBoxStyles.styles.ts:162`）。この CSS はコードに従う。
- large の `column-gap: 0` は、Input の large の `gap`（6px）と別の atomic class になる。どちらが勝つかは Griffel の差し込み順で決まる。9.75.2 の描画では 0 が勝つ（計算値の `column-gap` は 0px）。この CSS も 0 にした。
- 消去ボタンの出し入れを、v9 は React の状態 `focused`（`onFocus` と `onBlur` で切り替える。`useSearchBox.tsx:74-85`）で決める。この CSS は `:focus-within` で決める。根の中にフォーカスがある間だけ出す点は同じで、フォーカス中の計算値は一致した。
- 消去ボタンを押したときにフォーカスが外れないよう、この JS は `mousedown` の既定の動作を止める。v9 にこの処理があるかは確かめていない。

## SpinButton

### 概要と使い分け（Do / Don't）

決まった範囲の値を増減させる入力欄である。小さな範囲で細かく刻むとき（月の日付など）に使う。範囲がとても大きいか、3 値未満なら Input を、大まかな値で範囲を図で見せたいなら Slider を使う。

- Do: 最小か最大に達したら、その側のボタンだけを無効にする。単位があればプレースホルダーに含める（「0 cm」など）。ラベルを短くする。
- Don't: ボタンと一緒に入力欄まで無効にする（押せる大きさを保つため）。範囲が極端なときに使う。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

```text
span.fui-SpinButton                        根: inline-grid。枠は ::before、下線は ::after
├─ input.fui-SpinButton__input             role="spinbutton"、type="text"、autocomplete="off"、aria-valuemin / max / now
├─ button.fui-SpinButton__incrementButton  type="button"、tabindex="-1"、aria-label="Increment value"。ChevronUp16Regular
└─ button.fui-SpinButton__decrementButton  type="button"、tabindex="-1"、aria-label="Decrement value"。ChevronDown16Regular
```

- 既定の属性と、端に達したボタンの無効: `useSpinButton.tsx:300-342`。ARIA の値: `useSpinButton.tsx:350-356`。
- キーボード（`useSpinButton.tsx:190-231`。この JS が再現する）: ArrowUp / ArrowDown で 1 ステップ、PageUp / PageDown で大きなステップ、Home / End で最小 / 最大（Shift なし）、Enter で確定、Escape で打ちかけを戻す。キーを押している間は対応するボタンに `fui-SpinButton__button_active` を付けて押した見た目にする。
- ボタンを押し続けると繰り返す。最初は 300ms、1000ms かけて 80ms まで縮める（`useSpinButton.tsx:39-46,139-150`）。
- ステップは根の `data-step` と `data-step-page`（v9 の `step` と `stepPage`。既定 1）で与える。

出典のファイル: `react-spinbutton/library/src/components/SpinButton/useSpinButtonStyles.styles.ts`、`react-spinbutton/library/src/components/SpinButton/useSpinButton.tsx`、`react-spinbutton/library/src/components/SpinButton/SpinButton.types.ts`

### バリエーション

| 属性 | 値 | 既定 | 出典 |
|---|---|---|---|
| `data-appearance` | `outline`、`underline`、`filled-darker`、`filled-lighter` | `outline` | `SpinButton.types.ts:40-42` |
| `data-size` | `small`、`medium`（large はない） | `medium` | `SpinButton.types.ts:96-98` |
| `data-step` / `data-step-page` | 数値 | 1 / 1 | `SpinButton.types.ts:104-113` |

### 寸法（size ごとの表）

| 項目 | small | medium | 出典 |
|---|---|---|---|
| 根の `min-height` | 24px | 32px | `useSpinButtonStyles.styles.ts:19-22,35,123`（直書き） |
| 根の始端の余白 | `S`（8px） | `MNudge`（10px） | `useSpinButtonStyles.styles.ts:36,125` |
| 文字 | `caption1` | 指定なし（親から継ぐ） | `useSpinButtonStyles.styles.ts:124` |
| 格子 | 列 `1fr 24px`、行 `1fr 1fr`、`column-gap: spacingHorizontalXS`（4px） | 同 | `useSpinButtonStyles.styles.ts:25-29` |
| ボタン | 幅 24px、高さ 12px。増 `3px 6px 0 4px`、減 `0 6px 3px 4px` | 幅 24px、高さ 16px。左右 5px、増は上 4px 下 1px、減は上 1px 下 4px | `useSpinButtonStyles.styles.ts:250-268,297-323`（直書き） |

枠を `::before` に描くのは、ボタンの上に枠を重ね、拡大率が 2 で割り切れないときの隙間を防ぐためである（`useSpinButtonStyles.styles.ts:39-48`）。ボタンの余白は、図の小数を丸めた手作業の値である（`useSpinButtonStyles.styles.ts:309-314`）。

### 色と状態（トークン名の表）

根と枠（`::before`）

| 状態 | outline | underline | filled-darker / filled-lighter |
|---|---|---|---|
| 背景 | `colorNeutralBackground1` | `colorNeutralBackground1` のまま（透明にしない） | `colorNeutralBackground3` / `colorNeutralBackground1` |
| 枠 | `colorNeutralStroke1`、下 `colorNeutralStrokeAccessible` | 下だけ 1px、角丸 `borderRadiusNone` | `colorTransparentStroke` |
| hover | `colorNeutralStroke1Hover`、下 `colorNeutralStrokeAccessibleHover` | 下 `colorNeutralStrokeAccessibleHover` | `colorTransparentStrokeInteractive` |
| 押下、フォーカス | `colorNeutralStroke1Pressed`、下 `colorNeutralStrokeAccessiblePressed` | 下 `colorNeutralStrokeAccessiblePressed` | `colorTransparentStrokeInteractive` |
| invalid（フォーカスなし） | 全周 `colorPaletteRedBorder2` | 同 | 同 |
| disabled | 背景 `colorTransparentBackground`、枠 `colorNeutralStrokeDisabled`、`cursor: not-allowed` | 同 | 同 |

ボタン

| 状態 | outline、underline | filled-darker | filled-lighter |
|---|---|---|---|
| 通常 | 背景 transparent、色 `colorNeutralForeground3` | 同 | 同 |
| hover | 色 `colorNeutralForeground3Hover`、背景 `colorSubtleBackgroundHover` | 背景 `colorNeutralBackground3Hover` | 背景 `colorNeutralBackground1Hover` |
| 押下（`:active` か `fui-SpinButton__button_active`） | 色 `colorNeutralForeground3Pressed`、背景 `colorSubtleBackgroundPressed` | 背景 `colorNeutralBackground3Pressed` | 背景 `colorNeutralBackground1Pressed` |
| disabled | 色 `colorNeutralForegroundDisabled`、`cursor: not-allowed` | 同 | 同 |

入力文字 / placeholder は `colorNeutralForeground1` / `colorNeutralForeground4`、disabled は `colorNeutralForegroundDisabled`。出典: `useSpinButtonStyles.styles.ts:121-248,250-390`。

### フォーカス・動き・ハイコントラスト

- 共通の下線（位置は 0、`z-index: 20`）。ボタンは Tab で止まらず、輪郭もない（`useSpinButtonStyles.styles.ts:258,270-272`）。
- 背景と色の変化に transition はない。
- 強制色のモードで、disabled の `::before` の枠を `GrayText`。根の `:focus-within` に透明な輪郭（`useSpinButtonStyles.styles.ts:116-118,209-211`）。

### 実装の例

```html demo
<div style="display:flex;flex-wrap:wrap;gap:12px;align-items:center">
  <span class="fui-SpinButton" data-size="small" data-fui-enhance>
    <input class="fui-SpinButton__input" type="text" role="spinbutton" autocomplete="off" value="3" aria-valuemin="0" aria-valuemax="20" aria-valuenow="3" aria-label="small の例">
    <button class="fui-SpinButton__incrementButton" type="button" tabindex="-1" aria-label="Increment value"><svg class="fui-Icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M3.15 10.35c.2.2.5.2.7 0L8 6.21l4.15 4.14a.5.5 0 0 0 .7-.7l-4.5-4.5a.5.5 0 0 0-.7 0l-4.5 4.5a.5.5 0 0 0 0 .7"/></svg></button>
    <button class="fui-SpinButton__decrementButton" type="button" tabindex="-1" aria-label="Decrement value"><svg class="fui-Icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M3.15 5.65c.2-.2.5-.2.7 0L8 9.79l4.15-4.14a.5.5 0 0 1 .7.7l-4.5 4.5a.5.5 0 0 1-.7 0l-4.5-4.5a.5.5 0 0 1 0-.7"/></svg></button>
  </span>
  <span class="fui-SpinButton" data-fui-enhance>
    <input class="fui-SpinButton__input" type="text" role="spinbutton" autocomplete="off" value="10" aria-valuemin="0" aria-valuemax="20" aria-valuenow="10" aria-label="medium の例">
    <button class="fui-SpinButton__incrementButton" type="button" tabindex="-1" aria-label="Increment value"><svg class="fui-Icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M3.15 10.35c.2.2.5.2.7 0L8 6.21l4.15 4.14a.5.5 0 0 0 .7-.7l-4.5-4.5a.5.5 0 0 0-.7 0l-4.5 4.5a.5.5 0 0 0 0 .7"/></svg></button>
    <button class="fui-SpinButton__decrementButton" type="button" tabindex="-1" aria-label="Decrement value"><svg class="fui-Icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M3.15 5.65c.2-.2.5-.2.7 0L8 9.79l4.15-4.14a.5.5 0 0 1 .7.7l-4.5 4.5a.5.5 0 0 1-.7 0l-4.5-4.5a.5.5 0 0 1 0-.7"/></svg></button>
  </span>
  <span class="fui-SpinButton" data-appearance="filled-darker" data-fui-enhance>
    <input class="fui-SpinButton__input" type="text" role="spinbutton" autocomplete="off" value="20" aria-valuemin="0" aria-valuemax="20" aria-valuenow="20" aria-label="最大に達した例">
    <button class="fui-SpinButton__incrementButton" type="button" tabindex="-1" aria-label="Increment value" disabled><svg class="fui-Icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M3.15 10.35c.2.2.5.2.7 0L8 6.21l4.15 4.14a.5.5 0 0 0 .7-.7l-4.5-4.5a.5.5 0 0 0-.7 0l-4.5 4.5a.5.5 0 0 0 0 .7"/></svg></button>
    <button class="fui-SpinButton__decrementButton" type="button" tabindex="-1" aria-label="Decrement value"><svg class="fui-Icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M3.15 5.65c.2-.2.5-.2.7 0L8 9.79l4.15-4.14a.5.5 0 0 1 .7.7l-4.5 4.5a.5.5 0 0 1-.7 0l-4.5-4.5a.5.5 0 0 1 0-.7"/></svg></button>
  </span>
</div>
```

```html demo
<div style="display:flex;flex-wrap:wrap;gap:12px;align-items:center">
  <span class="fui-SpinButton" data-appearance="underline">
    <input class="fui-SpinButton__input" type="text" role="spinbutton" autocomplete="off" value="5" aria-valuenow="5" aria-label="underline の例">
    <button class="fui-SpinButton__incrementButton" type="button" tabindex="-1" aria-label="Increment value"><svg class="fui-Icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M3.15 10.35c.2.2.5.2.7 0L8 6.21l4.15 4.14a.5.5 0 0 0 .7-.7l-4.5-4.5a.5.5 0 0 0-.7 0l-4.5 4.5a.5.5 0 0 0 0 .7"/></svg></button>
    <button class="fui-SpinButton__decrementButton" type="button" tabindex="-1" aria-label="Decrement value"><svg class="fui-Icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M3.15 5.65c.2-.2.5-.2.7 0L8 9.79l4.15-4.14a.5.5 0 0 1 .7.7l-4.5 4.5a.5.5 0 0 1-.7 0l-4.5-4.5a.5.5 0 0 1 0-.7"/></svg></button>
  </span>
  <span class="fui-SpinButton">
    <input class="fui-SpinButton__input" type="text" role="spinbutton" autocomplete="off" value="99" aria-invalid="true" aria-valuenow="99" aria-label="invalid の例">
    <button class="fui-SpinButton__incrementButton" type="button" tabindex="-1" aria-label="Increment value"><svg class="fui-Icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M3.15 10.35c.2.2.5.2.7 0L8 6.21l4.15 4.14a.5.5 0 0 0 .7-.7l-4.5-4.5a.5.5 0 0 0-.7 0l-4.5 4.5a.5.5 0 0 0 0 .7"/></svg></button>
    <button class="fui-SpinButton__decrementButton" type="button" tabindex="-1" aria-label="Decrement value"><svg class="fui-Icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M3.15 5.65c.2-.2.5-.2.7 0L8 9.79l4.15-4.14a.5.5 0 0 1 .7.7l-4.5 4.5a.5.5 0 0 1-.7 0l-4.5-4.5a.5.5 0 0 1 0-.7"/></svg></button>
  </span>
  <span class="fui-SpinButton">
    <input class="fui-SpinButton__input" type="text" role="spinbutton" autocomplete="off" value="1" disabled aria-valuenow="1" aria-label="disabled の例">
    <button class="fui-SpinButton__incrementButton" type="button" tabindex="-1" aria-label="Increment value" disabled><svg class="fui-Icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M3.15 10.35c.2.2.5.2.7 0L8 6.21l4.15 4.14a.5.5 0 0 0 .7-.7l-4.5-4.5a.5.5 0 0 0-.7 0l-4.5 4.5a.5.5 0 0 0 0 .7"/></svg></button>
    <button class="fui-SpinButton__decrementButton" type="button" tabindex="-1" aria-label="Decrement value" disabled><svg class="fui-Icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M3.15 5.65c.2-.2.5-.2.7 0L8 9.79l4.15-4.14a.5.5 0 0 1 .7.7l-4.5 4.5a.5.5 0 0 1-.7 0l-4.5-4.5a.5.5 0 0 1 0-.7"/></svg></button>
  </span>
</div>
```

### v9 との差と未確認の点

- 表示の書式（v9 の `displayValue`）と、制御された値（`value` と `onChange`）は再現していない。JS は数値を `step` の小数の桁で丸めて表示する。
- 打った値を確定するときは、v9 と同じく範囲に収めない（`useSpinButton.tsx:240-264`）。
- underline のボタンの規則は、基本と同じ値を書き直すだけなので CSS では省いた（`useSpinButtonStyles.styles.ts:329-349`）。

## TagPicker

### 概要と使い分け（Do / Don't）

入力欄と一覧を組み合わせ、一覧から選ぶか自分で入れてもらう部品である。選んだものはタグで示す。ファイル、人、会議などを選ぶのに向く。

- Do: `TagPickerInput` に `aria-label` で名前を付ける。入力欄で Backspace を押すと最後のタグに移る（消える）ことを利用者に伝える。補助の操作（「すべて消す」など）は secondaryAction に置く。
- Don't: 長いタグを切り詰めずに並べ続ける。切り詰めは組み込まれていないので、最大幅を決めて自分で切る。
- サイトには使い分けの基準と Do / Don't の一覧がない。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

```text
div.fui-TagPickerControl                    根: 枠、背景、下線の ::after。flex、折り返し
├─ div.fui-TagPickerGroup                   role="listbox"。選んだタグ（fui-Tag）
├─ input.fui-TagPickerInput                 role="combobox"、type="text"、aria-expanded、開いたとき aria-controls
│   または button.fui-TagPickerButton       入力しない形
└─ span.fui-TagPickerControl__aside         絶対配置で終端に置く
    ├─ span.fui-TagPickerControl__secondaryAction
    └─ span.fui-TagPickerControl__expandIcon  role="button"、aria-expanded
div.fui-Listbox.fui-TagPickerList           role="listbox"、popover
└─ div.fui-Option.fui-TagPickerOption       role="option"、aria-selected
    ├─ span.fui-TagPickerOption__media
    └─ span.fui-TagPickerOption__secondaryContent
```

- 描画: `renderTagPickerControl.tsx:19-27`。input は Combobox と同じ trigger の作り（`useTagPickerInput.tsx:20,81`）なので、キーボードは Combobox の表と同じ。
- 空の入力欄で Backspace を押すと最後のタグにフォーカスが移り、タグの上の Backspace で消える（`react-tag-picker/library/src/components/TagPicker/TagPicker.cy.tsx:346,364`）。
- タグの size は TagPicker の size から決まる（medium → `extra-small`、large → `small`、extra-large → `medium`）。appearance は filled-darker → タグの `outline`、それ以外 → `filled`（`tagPicker2Tag.ts:5-38`）。

出典のファイル: `react-tag-picker/library/src/components/TagPickerControl/useTagPickerControlStyles.styles.ts`、`…/TagPickerControl/renderTagPickerControl.tsx`、`…/TagPicker/TagPicker.types.ts`、`…/TagPicker/useTagPicker.ts`、`…/TagPickerInput/useTagPickerInput.tsx`、`…/TagPickerInput/useTagPickerInputStyles.styles.ts`、`…/TagPickerButton/useTagPickerButtonStyles.styles.ts`、`…/TagPickerGroup/useTagPickerGroupStyles.styles.ts`、`…/TagPickerList/useTagPickerListStyles.styles.ts`、`…/TagPickerOption/useTagPickerOptionStyles.styles.ts`、`react-tag-picker/library/src/utils/tagPicker2Tag.ts`、`react-tag-picker/library/src/utils/tokens.ts`（`…` は `react-tag-picker/library/src/components`）

### バリエーション

| 属性（根に付ける） | 値 | 既定 | 出典 |
|---|---|---|---|
| `data-size` | `medium`、`large`、`extra-large`（small はない） | `medium` | `TagPicker.types.ts:16`、`useTagPicker.ts:123` |
| `data-appearance` | `outline`、`underline`、`filled-lighter`、`filled-darker` | `outline` | `useTagPicker.ts:123`、`useTagPickerControlStyles.styles.ts:106-140` |

### 寸法（size ごとの表）

| 項目 | medium | large | extra-large | 出典 |
|---|---|---|---|---|
| 根の `min-height` | 32px | 40px | 44px | `useTagPickerControlStyles.styles.ts:95-103`（直書き） |
| 根の余白 | 始端 `M`（12px）、終端 `calc(M + aside の幅)` | 同 | 同 | `useTagPickerControlStyles.styles.ts:27-28` |
| aside | 終端から 12px、高さ 100%、`min-height` 32 / 40 / 44px | | | `useTagPickerControlStyles.styles.ts:162-181` |
| 開くアイコン | 16px、始端 2px | 20px、2px | 24px、6px | `useTagPickerControlStyles.styles.ts:205-219` |
| 入力欄の上下の余白 | `spacingVerticalSNudge`（6px） | `spacingVerticalMNudge`（10px） | `spacingVerticalM`（12px） | `useTagPickerInputStyles.styles.ts:45-56` |
| 入力欄の文字 | `body1` | `body1` | `body1` | 同上 |
| タグの並びの上下の余白 / 間隔 | 6px / `spacingHorizontalXS`（4px） | 8px / `spacingHorizontalSNudge`（6px） | 8px / 6px | `useTagPickerGroupStyles.styles.ts:24-35` |
| button の余白と文字 | 3px 6px 3px 8px、`caption1` | 5px 10px 5px 12px、`body1` | 7px 12px 7px 18px、`body2` | `useTagPickerButtonStyles.styles.ts:39-57` |

- aside の幅は v9 が JS で測り、`--fui-TagPickerControl-aside-width` に入れる（`useTagPickerControlStyles.styles.ts:19`）。`text-entry.js` も `data-fui-enhance` の中で同じく測り、CSSOM で書く（CSP の下でも効く）。JS がないときは 0 になり、右の余白が aside の分だけ狭くなる。入力欄の幅は `--fluent-TagPickerInput__width`（既定 0）で、v9 が JS で計算する（`tokens.ts:5-11`）。この JS は計算しない。
- 入力欄は `min-width: 24px; width: 0; flex-grow: 1` なので、JS がなくても行の残りに伸びる。

### 色と状態（トークン名の表）

- 根は Combobox の根と同じトークン（`useTagPickerControlStyles.styles.ts:106-159`）。hover、押下、フォーカスの枠は outline だけ。invalid と disabled の付け方も Combobox と同じ。
- 入力欄: 文字 `colorNeutralForeground1`、placeholder `colorNeutralForeground4`。disabled は `colorNeutralForegroundDisabled`（`useTagPickerInputStyles.styles.ts:13-25,57-64`）。
- 開くアイコン: `colorNeutralStrokeAccessible`。disabled は `colorNeutralForegroundDisabled`、`not-allowed`（`useTagPickerControlStyles.styles.ts:192,220-223`）。
- 選択肢: Option の見た目を、選択なし、無効なしで当てる。チェックの印はなく、hover、押下、キーボードの強調の枠だけが効く（`useTagPickerOptionStyles.styles.ts:53-60`）。secondaryContent があると 2 列の格子にし、secondaryContent は `caption1` で 2 行目に置く。

### フォーカス・動き・ハイコントラスト

- 共通の下線（`useTagPickerControlStyles.styles.ts:44-80`）。根の `:focus-within` に透明な輪郭（同 37-42）。フォーカス中に hover すると hover の枠の色が勝つ。
- 強制色のモードで disabled の枠を `GrayText`（`useTagPickerControlStyles.styles.ts:156-158`）。

### 実装の例

タグ（`fui-Tag`）の見た目は Tag の CSS が担う（12 章）。aside の幅は、`data-fui-enhance` の中なら `text-entry.js` が v9 と同じく測って `--fui-TagPickerControl-aside-width` に書く。

```html demo
<div style="display:flex;flex-direction:column;gap:12px;max-width:360px">
  <div class="fui-TagPickerControl" data-fui-enhance>
    <div class="fui-TagPickerGroup" role="listbox" aria-label="選んだ担当者">
      <button class="fui-Tag" type="button" data-size="extra-small" data-appearance="filled" data-dismissible><span class="fui-Tag__primaryText">佐藤</span><span class="fui-Tag__dismissIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="m4.09 4.22.06-.07a.5.5 0 0 1 .63-.06l.07.06L10 9.29l5.15-5.14a.5.5 0 0 1 .63-.06l.07.06c.18.17.2.44.06.63l-.06.07L10.71 10l5.14 5.15c.18.17.2.44.06.63l-.06.07a.5.5 0 0 1-.63.06l-.07-.06L10 10.71l-5.15 5.14a.5.5 0 0 1-.63.06l-.07-.06a.5.5 0 0 1-.06-.63l.06-.07L9.29 10 4.15 4.85a.5.5 0 0 1-.06-.63l.06-.07z"/></svg></span></button>
      <button class="fui-Tag" type="button" data-size="extra-small" data-appearance="filled" data-dismissible><span class="fui-Tag__primaryText">鈴木</span><span class="fui-Tag__dismissIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="m4.09 4.22.06-.07a.5.5 0 0 1 .63-.06l.07.06L10 9.29l5.15-5.14a.5.5 0 0 1 .63-.06l.07.06c.18.17.2.44.06.63l-.06.07L10.71 10l5.14 5.15c.18.17.2.44.06.63l-.06.07a.5.5 0 0 1-.63.06l-.07-.06L10 10.71l-5.15 5.14a.5.5 0 0 1-.63.06l-.07-.06a.5.5 0 0 1-.06-.63l.06-.07L9.29 10 4.15 4.85a.5.5 0 0 1-.06-.63l.06-.07z"/></svg></span></button>
    </div>
    <input class="fui-TagPickerInput" type="text" role="combobox" aria-expanded="false" aria-label="担当者を選ぶ">
    <span class="fui-TagPickerControl__aside">
      <span class="fui-TagPickerControl__expandIcon" role="button" aria-expanded="false" aria-label="Open"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M15.85 7.65c.2.2.2.5 0 .7l-5.46 5.49a.55.55 0 0 1-.78 0L4.15 8.35a.5.5 0 1 1 .7-.7L10 12.8l5.15-5.16c.2-.2.5-.2.7 0"/></svg></span>
    </span>
  </div>
  <div class="fui-TagPickerControl" data-size="large" data-appearance="filled-darker" data-fui-enhance>
    <div class="fui-TagPickerGroup" role="listbox" aria-label="選んだ担当者"></div>
    <input class="fui-TagPickerInput" type="text" role="combobox" aria-expanded="false" placeholder="名前で探す" aria-label="large の例">
    <span class="fui-TagPickerControl__aside">
      <span class="fui-TagPickerControl__expandIcon" role="button" aria-expanded="false" aria-label="Open"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M15.85 7.65c.2.2.2.5 0 .7l-5.46 5.49a.55.55 0 0 1-.78 0L4.15 8.35a.5.5 0 1 1 .7-.7L10 12.8l5.15-5.16c.2-.2.5-.2.7 0"/></svg></span>
    </span>
  </div>
</div>
```

開いた一覧を単独で示す（media と secondaryContent のある選択肢）。

```html demo
<div class="fui-Listbox fui-TagPickerList" role="listbox" aria-label="担当者の候補" style="width:300px">
  <div class="fui-Option fui-TagPickerOption" role="option" aria-selected="false">
    <span class="fui-TagPickerOption__media"><svg class="fui-Icon" width="32" height="32" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M10 2a4 4 0 1 0 0 8 4 4 0 0 0 0-8M7 6a3 3 0 1 1 6 0 3 3 0 0 1-6 0m-2 5a2 2 0 0 0-2 2c0 1.7.83 2.97 2.13 3.8A9 9 0 0 0 10 18c1.85 0 3.58-.39 4.87-1.2A4.4 4.4 0 0 0 17 13a2 2 0 0 0-2-2zm-1 2a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1c0 1.3-.62 2.28-1.67 2.95A8 8 0 0 1 10 17a8 8 0 0 1-4.33-1.05A3.4 3.4 0 0 1 4 13"/></svg></span>
    高橋
    <span class="fui-TagPickerOption__secondaryContent">開発部</span>
  </div>
  <div class="fui-Option fui-TagPickerOption" role="option" aria-selected="false" data-activedescendant-focusvisible>
    <span class="fui-TagPickerOption__media"><svg class="fui-Icon" width="32" height="32" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M10 2a4 4 0 1 0 0 8 4 4 0 0 0 0-8M7 6a3 3 0 1 1 6 0 3 3 0 0 1-6 0m-2 5a2 2 0 0 0-2 2c0 1.7.83 2.97 2.13 3.8A9 9 0 0 0 10 18c1.85 0 3.58-.39 4.87-1.2A4.4 4.4 0 0 0 17 13a2 2 0 0 0-2-2zm-1 2a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1c0 1.3-.62 2.28-1.67 2.95A8 8 0 0 1 10 17a8 8 0 0 1-4.33-1.05A3.4 3.4 0 0 1 4 13"/></svg></span>
    田中（キーボードで強調中）
    <span class="fui-TagPickerOption__secondaryContent">営業部</span>
  </div>
</div>
```

### v9 との差と未確認の点

- TagPicker の開閉、選択、タグの追加と削除、Backspace の扱いは、この JS では再現していない。CSS の見た目だけである。
- `--fluent-TagPickerInput__width` は v9 が JS で計算する。この JS は計算しない。
- TagPickerGroup には、v9 が TagGroup の class（`fui-TagGroup`）も付ける。この CSS は TagGroup の `display: inline-flex` を `.fui-TagPickerGroup` に写したので、React を使わない HTML では `fui-TagGroup` を付けない。付けると、Tag の CSS の `column-gap` との順序で間隔が変わるおそれがある。
- 中のタグの寸法と色は確かめていない（Tag の CSS の担当）。
- TagPickerButton の選択があるときの隠し方は、v9 の `hasSelectedOption` を「タグの並びに子があること」で近似した。
- 例の media に置いた 32px の人のアイコンは、v9 の例の Avatar の代わりである（大きさは推論）。

## 土台への提案

土台（`fluent2-base.css`）は変更していない。提案はない。

設計書の HTML は `fluent2.js` を埋め込むので、この章の Combobox、Dropdown、SpinButton、SearchBox の例は設計書の中でも動く。
