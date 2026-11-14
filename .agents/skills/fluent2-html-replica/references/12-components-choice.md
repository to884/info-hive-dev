# 選択の部品、タグ、バッジ

この章は、Checkbox、RadioGroup（Radio）、Switch、Slider、Rating（RatingDisplay）、Tag（InteractionTag、TagGroup）、Badge（CounterBadge、PresenceBadge）を、React を使わない HTML と CSS で再現する方法を書く。CSS は `assets/fluent2.css` の `choice` の部分、小さな振る舞いは `assets/fluent2.js` にある（開発用のリポジトリ（非公開）の原本は `src/components/choice.css` と `choice.js`）。

- 基準は `@fluentui/react-components` 9.75.2 のコードである。値の出典は、microsoft/fluentui のリポジトリからの相対パスと行で書く。
- Checkbox、Radio、Switch、Slider、Rating は、ネイティブの `<input>` を透明にして見た目の要素に重ねる。v9 と同じ作りで、キーボード操作とフォームへの送信はブラウザに任せる。
- バリエーションは data 属性、状態はネイティブの疑似クラスと ARIA で表す。data 属性の条件は `:where()` に入れ、v9 の Griffel と同じ詳細度にそろえる。
- `choice.css` は Label の CSS（`actions.css`）より後に読み込む。`.fui-Checkbox__label { color: inherit }` と Label の根の `color` は同じ詳細度で、後に来た方が勝つからである。`tools/build_spec.py` の結合の順（actions → choice）は、この条件を満たしている。
- `fluent2-base.css` の `.fui-Icon` と `.fui-Icon-filled` の既定に依存する。InteractionTag の outline の hover では、この既定を上書きして Filled のアイコンを出す。
- 出典のパスは、節の冒頭で全体を書き、以降は `…/` で略す。「同」は直前に書いたファイルを指す。
- `choice.js` が扱うのは、`data-fui-enhance` を付けた要素だけである。Checkbox の mixed の初期値、Slider の進み具合、Rating の表示値の 3 つを受け持つ。

## Checkbox

出典: `packages/react-components/react-checkbox/library/src/components/Checkbox/useCheckboxStyles.styles.ts`（以下、行番号だけのものはこのファイル）、`…/Checkbox/useCheckbox.tsx`、`…/Checkbox/Checkbox.types.ts`。

### 概要と使い分け（Do / Don't）

Checkbox は、複数の選択肢から複数を選ぶとき、または 1 つの項目をオンとオフで切り替えるときに使う。選んだ結果は、送信のボタンなどを押すまで反映しない。すぐに反映する設定には Switch を使う。1 つだけを選ばせるなら RadioGroup か Dropdown にする。

親の Checkbox で子をまとめて操作し、子の一部だけが選ばれているときは、親を不確定（mixed）にする。

- Do: ラベルは短く、走査しやすい断片にする。チェックが「はい」を意味する言い方にする。sentence case にし、1 文なら句点を付けない。グループにはラベルを付け、選び方の条件もそこに書く。
- Do: 選択肢の文の構造をそろえ、繰り返す語はグループのラベルに移す。並びは小さい順や安全な順など、論理的な順にする。
- Don't: 否定文のラベル、長い複数文のラベルにしない。1 つのグループに 7 つ程度を超える選択肢を詰めない。多ければグループを分けるか、Combobox や Dropdown にする。
- Don't: 単一選択や即時反映の設定に Checkbox を使わない。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

| スロット | 要素 | class | 役割 |
|---|---|---|---|
| root | `span` | `fui-Checkbox` | 全体。`position: relative` で input を重ねる |
| input | `input type="checkbox"` | `fui-Checkbox__input` | 透明で、indicator と余白の上に重なる |
| indicator | `div aria-hidden="true"` | `fui-Checkbox__indicator` | 見た目の箱。中にチェックの印を置く |
| label | `label for="…"` | `fui-Label fui-Checkbox__label` | Label の `size="medium"` |

- 並びは input、（`before` のとき）label、indicator、（`after` のとき）label の順である（`…/Checkbox/renderCheckbox.tsx:13-16`）。
- mixed は、ネイティブの `indeterminate` で表す。v9 も layout effect で `input.indeterminate` を設定する（`useCheckbox.tsx:167-169`）。`aria-checked` は付けない。`indeterminate` が支援技術に「mixed」として伝わる。
- `indeterminate` は HTML の属性で書けない。根に `data-checked="mixed"` と `data-fui-enhance` を付けると、`choice.js` が読み込み時に `indeterminate` を立てる。利用者がクリックすると、ネイティブの動作で `indeterminate` は外れる。
- v9 は状態に合うアイコンだけを描く（`useCheckbox.tsx:44-55`）。React を使わない HTML では、indicator の中に `data-icon="checked"` と `data-icon="mixed"` の 2 つの SVG を置き、CSS で出し分ける。

| 状態 | medium | large | circular の mixed |
|---|---|---|---|
| checked | `checkmark_12_filled`（12×12） | `checkmark_16_filled`（16×16） | — |
| mixed | `square_12_filled` | `square_16_filled` | `circle_20_filled` を `1em` で描く |

- キーボード: ネイティブの checkbox と同じである。Tab で移り、Space で切り替える。

### バリエーション

| prop | data 属性 | 値 | 既定 | 出典 |
|---|---|---|---|---|
| `size` | `data-size` | `medium`、`large` | `medium` | `Checkbox.types.ts:88`、`useCheckbox.tsx:35` |
| `shape` | `data-shape` | `square`、`circular` | `square` | `Checkbox.types.ts:81`、`useCheckbox.tsx:35` |
| `labelPosition` | `data-label-position` | `before`、`after` | `after` | `Checkbox.types.ts:65` |
| `checked` | ネイティブの `checked`、`indeterminate` | `true`、`false`、`'mixed'` | `false` | `Checkbox.types.ts:48` |
| `disabled` | ネイティブの `disabled` | — | — | — |

### 寸法

| 項目 | medium | large | 出典 |
|---|---|---|---|
| indicator の幅と高さ | 16px（直書き） | 20px（直書き） | :24-25、:144-152 |
| indicator の `font-size`（アイコンの大きさ） | 12px（直書き） | 16px（直書き） | :143、:150 |
| indicator の線 | `strokeWidthThin` solid | 同じ | :136-137 |
| indicator の角丸 | `borderRadiusSmall`。circular は `borderRadiusCircular` | 同じ | :138、:155 |
| indicator の margin | `spacingVerticalS spacingHorizontalS`（8px 8px） | 同じ | :139 |
| input の幅 | `calc(16px + 2 * spacingHorizontalS)` = 32px（推論で算出） | `calc(20px + 2 * …)` = 36px（推論で算出） | :107、:119 |
| label の padding | `spacingVerticalS spacingHorizontalS`。indicator の側だけ `spacingHorizontalXS` | 同じ | :164-172 |
| label の上下の margin | `calc((16px - lineHeightBase300) / 2)` = -2px（推論で算出） | `calc((20px - lineHeightBase300) / 2)` = 0 | :176-183 |
| label の文字 | `fontSizeBase300` / `lineHeightBase300`（Label medium） | 同じ | `packages/react-components/react-label/library/src/components/Label/useLabelStyles.styles.ts:39-42` |

根の高さは、indicator と上下の margin で 32px（medium）、36px（large）になる（推論で算出）。

### 色と状態（トークン名の表）

v9 は根に 3 つの CSS 変数を置き、indicator がそれを読む（:17-21、:133-135）。`--fui-Checkbox__indicator--color` がアイコンの色、`--fui-Checkbox__indicator--backgroundColor` が箱の塗り、`--fui-Checkbox__indicator--borderColor` が線の色である。線の変数が無いときは `colorNeutralStrokeAccessible` になる。

| 状態 | 根の `color`（ラベル） | 箱の塗り | 箱の線 | アイコン | 出典 |
|---|---|---|---|---|---|
| unchecked | `colorNeutralForeground3` | なし | `colorNeutralStrokeAccessible` | — | :33、:135 |
| unchecked hover | `colorNeutralForeground2` | なし | `colorNeutralStrokeAccessibleHover` | — | :39-42 |
| unchecked pressed | `colorNeutralForeground1` | なし | `colorNeutralStrokeAccessiblePressed` | — | :44-47 |
| checked | `colorNeutralForeground1` | `colorCompoundBrandBackground` | 塗りと同じ | `colorNeutralForegroundInverted` | :51-54 |
| checked hover | 同上 | `colorCompoundBrandBackgroundHover` | 塗りと同じ | 同上 | :56-59 |
| checked pressed | 同上 | `colorCompoundBrandBackgroundPressed` | 塗りと同じ | 同上 | :61-64 |
| mixed | `colorNeutralForeground1` | なし | `colorCompoundBrandStroke` | `colorCompoundBrandForeground1` | :68-70 |
| mixed hover | 同上 | なし | `colorCompoundBrandStrokeHover` | `colorCompoundBrandForeground1Hover` | :72-75 |
| mixed pressed | 同上 | なし | `colorCompoundBrandStrokePressed` | `colorCompoundBrandForeground1Pressed` | :77-80 |
| disabled（checked と mixed を含む） | `colorNeutralForegroundDisabled`、`cursor: default` | なし | `colorNeutralStrokeDisabled` | `colorNeutralForegroundDisabled` | :84-88 |

- 状態は排他で、disabled、mixed、checked、unchecked の順に優先する（:195-206）。CSS では `:has()` で input の状態を読み、同じ優先になるよう条件を書く。
- hover と pressed は根の `:hover` と `:active` で判定するので、ラベルの上でも効く。
- disabled の checked は塗りが消え、線とチェックの印だけが無効の色になる。

### フォーカス・動き・ハイコントラスト

- フォーカス: 根に `createFocusOutlineStyle({ style: {}, selector: 'focus-within' })` が付く（:34）。根の全体（箱とラベル）を囲む。値は `packages/react-components/react-tabster/src/focus/createFocusOutlineStyle.ts:55-112` の既定で、`::after` に `2px solid colorStrokeFocus2`、角丸 `borderRadiusMedium`、`inset: calc(2px * -1)` である。`[data-fui-focus-within]:focus-within` は `:has(:focus-visible)` で近似した。
- 動き: transition は無い。
- ハイコントラスト: disabled だけに規則がある。根の `color` とアイコンの色が `GrayText` になる（:90-93）。checked の塗りはブラウザの強制色に任せる。フォーカスの枠は `Highlight` になる。

### 実装の例

```html demo
<div style="display:flex; flex-wrap:wrap; gap:8px 16px">
  <span class="fui-Checkbox">
    <input class="fui-Checkbox__input" type="checkbox" id="choice-cb-1">
    <div class="fui-Checkbox__indicator" aria-hidden="true"><svg class="fui-Icon" data-icon="checked" width="12" height="12" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true"><path d="M9.76 3.2c.3.29.32.76.04 1.06l-4.25 4.5a.75.75 0 0 1-1.08.02L2.22 6.53a.75.75 0 0 1 1.06-1.06l1.7 1.7L8.7 3.24a.75.75 0 0 1 1.06-.04"/></svg><svg class="fui-Icon" data-icon="mixed" width="12" height="12" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true"><path d="M2 4c0-1.1.9-2 2-2h4a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2z"/></svg></div>
    <label class="fui-Label fui-Checkbox__label" for="choice-cb-1">メールで通知</label>
  </span>
  <span class="fui-Checkbox">
    <input class="fui-Checkbox__input" type="checkbox" id="choice-cb-2" checked>
    <div class="fui-Checkbox__indicator" aria-hidden="true"><svg class="fui-Icon" data-icon="checked" width="12" height="12" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true"><path d="M9.76 3.2c.3.29.32.76.04 1.06l-4.25 4.5a.75.75 0 0 1-1.08.02L2.22 6.53a.75.75 0 0 1 1.06-1.06l1.7 1.7L8.7 3.24a.75.75 0 0 1 1.06-.04"/></svg><svg class="fui-Icon" data-icon="mixed" width="12" height="12" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true"><path d="M2 4c0-1.1.9-2 2-2h4a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2z"/></svg></div>
    <label class="fui-Label fui-Checkbox__label" for="choice-cb-2">チャットで通知</label>
  </span>
  <span class="fui-Checkbox" data-checked="mixed" data-fui-enhance>
    <input class="fui-Checkbox__input" type="checkbox" id="choice-cb-3">
    <div class="fui-Checkbox__indicator" aria-hidden="true"><svg class="fui-Icon" data-icon="checked" width="12" height="12" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true"><path d="M9.76 3.2c.3.29.32.76.04 1.06l-4.25 4.5a.75.75 0 0 1-1.08.02L2.22 6.53a.75.75 0 0 1 1.06-1.06l1.7 1.7L8.7 3.24a.75.75 0 0 1 1.06-.04"/></svg><svg class="fui-Icon" data-icon="mixed" width="12" height="12" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true"><path d="M2 4c0-1.1.9-2 2-2h4a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2z"/></svg></div>
    <label class="fui-Label fui-Checkbox__label" for="choice-cb-3">すべての通知</label>
  </span>
  <span class="fui-Checkbox">
    <input class="fui-Checkbox__input" type="checkbox" id="choice-cb-4" disabled>
    <div class="fui-Checkbox__indicator" aria-hidden="true"><svg class="fui-Icon" data-icon="checked" width="12" height="12" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true"><path d="M9.76 3.2c.3.29.32.76.04 1.06l-4.25 4.5a.75.75 0 0 1-1.08.02L2.22 6.53a.75.75 0 0 1 1.06-1.06l1.7 1.7L8.7 3.24a.75.75 0 0 1 1.06-.04"/></svg><svg class="fui-Icon" data-icon="mixed" width="12" height="12" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true"><path d="M2 4c0-1.1.9-2 2-2h4a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2z"/></svg></div>
    <label class="fui-Label fui-Checkbox__label" for="choice-cb-4">無効</label>
  </span>
  <span class="fui-Checkbox">
    <input class="fui-Checkbox__input" type="checkbox" id="choice-cb-5" checked disabled>
    <div class="fui-Checkbox__indicator" aria-hidden="true"><svg class="fui-Icon" data-icon="checked" width="12" height="12" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true"><path d="M9.76 3.2c.3.29.32.76.04 1.06l-4.25 4.5a.75.75 0 0 1-1.08.02L2.22 6.53a.75.75 0 0 1 1.06-1.06l1.7 1.7L8.7 3.24a.75.75 0 0 1 1.06-.04"/></svg><svg class="fui-Icon" data-icon="mixed" width="12" height="12" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true"><path d="M2 4c0-1.1.9-2 2-2h4a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2z"/></svg></div>
    <label class="fui-Label fui-Checkbox__label" for="choice-cb-5">無効で選択済み</label>
  </span>
</div>
```

```html demo
<div style="display:flex; flex-wrap:wrap; gap:8px 16px">
  <span class="fui-Checkbox" data-size="large">
    <input class="fui-Checkbox__input" type="checkbox" id="choice-cb-6" checked>
    <div class="fui-Checkbox__indicator" aria-hidden="true"><svg class="fui-Icon" data-icon="checked" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M14.05 3.49c.28.3.27.77-.04 1.06l-7.93 7.47A.85.85 0 0 1 4.9 12L2.22 9.28a.75.75 0 1 1 1.06-1.06l2.24 2.27 7.47-7.04a.75.75 0 0 1 1.06.04"/></svg><svg class="fui-Icon" data-icon="mixed" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M2 4.5A2.5 2.5 0 0 1 4.5 2h7A2.5 2.5 0 0 1 14 4.5v7a2.5 2.5 0 0 1-2.5 2.5h-7A2.5 2.5 0 0 1 2 11.5z"/></svg></div>
    <label class="fui-Label fui-Checkbox__label" for="choice-cb-6">large</label>
  </span>
  <span class="fui-Checkbox" data-shape="circular">
    <input class="fui-Checkbox__input" type="checkbox" id="choice-cb-7" checked>
    <div class="fui-Checkbox__indicator" aria-hidden="true"><svg class="fui-Icon" data-icon="checked" width="12" height="12" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true"><path d="M9.76 3.2c.3.29.32.76.04 1.06l-4.25 4.5a.75.75 0 0 1-1.08.02L2.22 6.53a.75.75 0 0 1 1.06-1.06l1.7 1.7L8.7 3.24a.75.75 0 0 1 1.06-.04"/></svg><svg class="fui-Icon" data-icon="mixed" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M10 2a8 8 0 1 0 0 16 8 8 0 0 0 0-16"/></svg></div>
    <label class="fui-Label fui-Checkbox__label" for="choice-cb-7">circular</label>
  </span>
  <span class="fui-Checkbox" data-shape="circular" data-checked="mixed" data-fui-enhance>
    <input class="fui-Checkbox__input" type="checkbox" id="choice-cb-8">
    <div class="fui-Checkbox__indicator" aria-hidden="true"><svg class="fui-Icon" data-icon="checked" width="12" height="12" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true"><path d="M9.76 3.2c.3.29.32.76.04 1.06l-4.25 4.5a.75.75 0 0 1-1.08.02L2.22 6.53a.75.75 0 0 1 1.06-1.06l1.7 1.7L8.7 3.24a.75.75 0 0 1 1.06-.04"/></svg><svg class="fui-Icon" data-icon="mixed" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M10 2a8 8 0 1 0 0 16 8 8 0 0 0 0-16"/></svg></div>
    <label class="fui-Label fui-Checkbox__label" for="choice-cb-8">circular の mixed</label>
  </span>
  <span class="fui-Checkbox" data-label-position="before">
    <input class="fui-Checkbox__input" type="checkbox" id="choice-cb-9">
    <label class="fui-Label fui-Checkbox__label" for="choice-cb-9">ラベルが前</label>
    <div class="fui-Checkbox__indicator" aria-hidden="true"><svg class="fui-Icon" data-icon="checked" width="12" height="12" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true"><path d="M9.76 3.2c.3.29.32.76.04 1.06l-4.25 4.5a.75.75 0 0 1-1.08.02L2.22 6.53a.75.75 0 0 1 1.06-1.06l1.7 1.7L8.7 3.24a.75.75 0 0 1 1.06-.04"/></svg><svg class="fui-Icon" data-icon="mixed" width="12" height="12" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true"><path d="M2 4c0-1.1.9-2 2-2h4a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2z"/></svg></div>
  </span>
</div>
```

### v9 との差と未確認の点

- 状態の class を JS で付ける代わりに、`:has()` で input の状態を読む。詳細度は `:where()` で v9 にそろえた。
- アイコンを状態で描き分ける代わりに、2 つの SVG を置いて `display` を切り替える。size と shape に合う形は、書き手が選んで置く。
- 根の `span` の中に `div` を置くのは、v9 の DOM のとおりである。
- `data-checked="mixed"` は初期値だけを表す。その後の状態はネイティブの `indeterminate` が持つ。
- SVG の形の出どころは次のとおりである。`checkmark_12_filled`、`checkmark_16_filled`、`square_16_filled` は `@fluentui/svg-icons` の最新版を unpkg から取った。`square_12_filled` は v9 のスナップショット `packages/react-components/react-checkbox/library/src/components/Checkbox/__snapshots__/Checkbox.test.tsx.snap:115`、circular の mixed の `CircleFilled` は `packages/react-components/react-menu/library/src/components/MenuItemSwitch/__snapshots__/MenuItemSwitch.test.tsx.snap:31` から写した。unpkg の `checkmark_12_filled` は、Checkbox のスナップショットの path と一致した。v9 が使う `@fluentui/react-icons` の版と unpkg の最新版の差は、ほかの形では確かめていない。
- サイトは size、shape、labelPosition を扱っていない。

## RadioGroup

出典: `packages/react-components/react-radio/library/src/components/Radio/useRadioStyles.styles.ts`（以下、行番号だけのものはこのファイル）、`…/RadioGroup/useRadioGroupStyles.styles.ts`、`…/Radio/useRadio.tsx`、`…/RadioGroup/useRadioGroup.ts`。

### 概要と使い分け（Do / Don't）

RadioGroup は、短い一覧から 1 つを選ばせる。選択肢が 5 つ程度までで、すべてを一度に見せたいときに使う。場所が狭ければ Dropdown、複数を選ぶなら Checkbox、オンとオフをすぐ反映するなら Switch にする。

- Do: 妥当な既定値があれば先に選んでおき、先頭に置く。縦に並べるのを基本にする（走査しやすく、翻訳に強い）。
- Do: ラベルは短い断片にし、長ければ折り返す。sentence case にする。選ばない人がいるなら「なし」の選択肢を足す。
- Do: 説明文は、すべての選択肢に要るときだけ付ける。一部だけなら InfoLabel のツールチップにする。
- Don't: ラベルを省略記号で切らない。選択肢の末尾に句点、グループのラベルの末尾にコロンを付けない。
- Don't: 複数選択や即時反映の設定に使わない。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

| スロット | 要素 | class | 役割 |
|---|---|---|---|
| RadioGroup の root | `div role="radiogroup"` | `fui-RadioGroup` | グループ。`aria-labelledby` でラベルを関連付ける |
| Radio の root | `span` | `fui-Radio` | 1 つの選択肢 |
| input | `input type="radio"` | `fui-Radio__input` | 同じ `name` を持つ |
| indicator | `div aria-hidden="true"` | `fui-Radio__indicator` | 円。checked のとき `::after` で点を描く |
| label | `label for="…"` | `fui-Label fui-Radio__label` | Label（size の既定は medium） |

- `role="radiogroup"` は `useRadioGroup.ts:52`、input の `type="radio"` と並び（input、indicator、label）は `useRadio.tsx` と `renderRadio.tsx` による。
- indicator に子を置くと、未選択のときに子を `opacity: 0` にし、点は描かない（:142-153）。
- RadioGroup の `disabled` は、React を使わない HTML では各 input に `disabled` を書くか、`fieldset disabled` で囲む。
- キーボード: ネイティブの radio と同じである。Tab でグループに入り、矢印キーで選択を移す。何も選ばれていなければ最初の選択肢に入る。

### バリエーション

| 対象 | prop | data 属性 | 値 | 既定 | 出典 |
|---|---|---|---|---|---|
| RadioGroup | `layout` | `data-layout` | `vertical`、`horizontal`、`horizontal-stacked` | `vertical` | `RadioGroup.types.ts:44` |
| Radio | `labelPosition` | `data-label-position` | `after`、`below` | `after`。`horizontal-stacked` のグループの中では `below` | `Radio.types.ts:50`、`useRadio.tsx:54` |

Radio に size は無い。`horizontal-stacked` のグループの中では、`data-label-position` を書かない Radio が `below` になるよう CSS で書いた。

### 寸法

| 項目 | 値 | 出典 |
|---|---|---|
| indicator | 16px × 16px（直書き）、`font-size: 12px`、`strokeWidthThin` solid、`borderRadiusCircular` | :17、:156-171 |
| indicator の margin | `spacingVerticalS spacingHorizontalS` | :171 |
| checked の点 | 16px の円を `scale(0.625)` で 10px に縮める（10px は推論で算出）。色は `currentColor` | :175-184 |
| input | 幅 `calc(16px + 2 * spacingHorizontalS)` = 32px（推論で算出）、高さ 100% | :32-40 |
| input（below） | 幅 100%、高さ `calc(16px + 2 * spacingVerticalS)` = 32px（推論で算出） | :136-139 |
| label | `padding: spacingVerticalS spacingHorizontalS`、`align-self: center` | :189-192 |
| label（after） | `padding-inline-start: spacingHorizontalXS`、上下の margin `calc((16px - lineHeightBase300) / 2)` | :194-201 |
| label（below） | `padding-top: spacingVerticalXS`、`text-align: center`。根は縦並びで中央寄せ | :26-29、:203-206 |
| RadioGroup | `display: flex`、`align-items: flex-start`。vertical は `flex-direction: column` | `useRadioGroupStyles.styles.ts:11-20` |

RadioGroup に gap は無い。各 Radio の 8px の margin と padding が、項目の間隔になる。

### 色と状態（トークン名の表）

すべて input の兄弟セレクター（`.fui-Radio__input:enabled:checked ~ .fui-Radio__indicator` など）で付く。v9 のセレクターをそのまま写した。

| 状態 | ラベルの `color` | indicator の線 | 点の色 | 出典 |
|---|---|---|---|---|
| unchecked | `colorNeutralForeground3` | `colorNeutralStrokeAccessible` | — | :50-59 |
| unchecked hover | `colorNeutralForeground2` | `colorNeutralStrokeAccessibleHover` | — | :61-68 |
| unchecked pressed（`:hover:active`） | `colorNeutralForeground1` | `colorNeutralStrokeAccessiblePressed` | — | :70-77 |
| checked | `colorNeutralForeground1` | `colorCompoundBrandStroke` | `colorCompoundBrandForeground1` | :81-87 |
| checked hover | 同上 | `colorCompoundBrandStrokeHover` | `colorCompoundBrandForeground1Hover` | :97-102 |
| checked pressed | 同上 | `colorCompoundBrandStrokePressed` | `colorCompoundBrandForeground1Pressed` | :104-109 |
| disabled（checked を含む） | `colorNeutralForegroundDisabled`、`cursor: default` | `colorNeutralStrokeDisabled` | `colorNeutralForegroundDisabled` | :113-123 |

- indicator の中は塗らない。
- hover は `input:hover` で判定する。ラベルの上を指しても、ラベルが指す input が `:hover` になるので同じ色になる。

### フォーカス・動き・ハイコントラスト

- フォーカス: Radio の根に `createFocusOutlineStyle({ style: {}, selector: 'focus-within' })` が付く（:22）。値は Checkbox と同じで、`:has(:focus-visible)` で近似した。
- 動き: transition は無い。
- ハイコントラスト: unchecked の線は `ButtonBorder`、checked は線と点が `Highlight`、disabled はラベルと線と点が `GrayText` になる（:56-58、:88-94、:117-130）。

### 実装の例

```html demo
<div style="display:flex; flex-wrap:wrap; gap:24px">
  <div>
    <span class="fui-Label" id="choice-rg-1-label">配送の方法</span>
    <div class="fui-RadioGroup" role="radiogroup" aria-labelledby="choice-rg-1-label">
      <span class="fui-Radio">
        <input class="fui-Radio__input" type="radio" name="choice-rg-1" id="choice-rg-1-a" value="standard" checked>
        <div class="fui-Radio__indicator" aria-hidden="true"></div>
        <label class="fui-Label fui-Radio__label" for="choice-rg-1-a">通常配送</label>
      </span>
      <span class="fui-Radio">
        <input class="fui-Radio__input" type="radio" name="choice-rg-1" id="choice-rg-1-b" value="express">
        <div class="fui-Radio__indicator" aria-hidden="true"></div>
        <label class="fui-Label fui-Radio__label" for="choice-rg-1-b">お急ぎ配送</label>
      </span>
      <span class="fui-Radio">
        <input class="fui-Radio__input" type="radio" name="choice-rg-1" id="choice-rg-1-c" value="pickup" disabled>
        <div class="fui-Radio__indicator" aria-hidden="true"></div>
        <label class="fui-Label fui-Radio__label" for="choice-rg-1-c">店頭で受け取る（準備中）</label>
      </span>
    </div>
  </div>
  <div>
    <span class="fui-Label" id="choice-rg-2-label">文字の大きさ</span>
    <div class="fui-RadioGroup" role="radiogroup" data-layout="horizontal-stacked" aria-labelledby="choice-rg-2-label">
      <span class="fui-Radio">
        <input class="fui-Radio__input" type="radio" name="choice-rg-2" id="choice-rg-2-a" value="s">
        <div class="fui-Radio__indicator" aria-hidden="true"></div>
        <label class="fui-Label fui-Radio__label" for="choice-rg-2-a">小</label>
      </span>
      <span class="fui-Radio">
        <input class="fui-Radio__input" type="radio" name="choice-rg-2" id="choice-rg-2-b" value="m" checked>
        <div class="fui-Radio__indicator" aria-hidden="true"></div>
        <label class="fui-Label fui-Radio__label" for="choice-rg-2-b">中</label>
      </span>
      <span class="fui-Radio">
        <input class="fui-Radio__input" type="radio" name="choice-rg-2" id="choice-rg-2-c" value="l">
        <div class="fui-Radio__indicator" aria-hidden="true"></div>
        <label class="fui-Label fui-Radio__label" for="choice-rg-2-c">大</label>
      </span>
    </div>
  </div>
</div>
```

### v9 との差と未確認の点

- v9 は RadioGroup の文脈から各 Radio の `labelPosition` を決める。React を使わない CSS では、`horizontal-stacked` のグループの直下で属性の無い Radio を `below` として扱った。
- 中身の無い indicator の判定は `:not(:has(*))` で書いた。v9 は子の有無で class を選ぶ（:232）。
- サイトに明示の Do / Don't の一覧は無い。上の Do / Don't はサイトの説明の要約である。

## Switch

出典: `packages/react-components/react-switch/library/src/components/Switch/useSwitchStyles.styles.ts`（以下、行番号だけのものはこのファイル）、`…/Switch/useSwitch.tsx`、`…/Switch/Switch.types.ts`。

### 概要と使い分け（Do / Don't）

Switch は、オンとオフのように相反する 2 つから選ばせ、操作するとすぐに反映する。送信の操作が要る変更や、不確定の状態が要るときは Checkbox を使う。

- Do: ほとんどの場合にラベルを付け、関連が分かる近さに置く。ラベルを省けるのは、表の列見出しのように文脈が明らかなときだけである。
- Do: ラベルは設定を表す名詞か短い名詞句にする。名詞が曖昧なら、有効な状態を表す動詞を足す。sentence case にし、句点を付けない。
- Do: アイコンだけで示すときは、スクリーンリーダー向けの見えないラベルを付ける。
- Don't: ラベルに「オンにする」「オフにする」を入れない。質問の形のラベルにしない。曖昧な名詞を使わない。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

| スロット | 要素 | class | 役割 |
|---|---|---|---|
| root | `div` | `fui-Switch` | 全体 |
| input | `input type="checkbox" role="switch"` | `fui-Switch__input` | 透明で、トラックと余白の上に重なる |
| indicator | `div aria-hidden="true"` | `fui-Switch__indicator` | トラック。中のアイコンがつまみになる |
| label | `label for="…"` | `fui-Label fui-Switch__label` | Label の `size="medium"` |

- input の `role="switch"` と `type="checkbox"` は `useSwitch.tsx:89-90` にある。
- つまみは `CircleFilled`（viewBox `0 0 20 20`）を `1em` で描く。path は `packages/react-components/react-menu/library/src/components/MenuItemSwitch/__snapshots__/MenuItemSwitch.test.tsx.snap:31` から写した（unpkg からは取っていない）。
- 並びは input、（`before` と `above` のとき）label、indicator、（`after` のとき）label の順である（`…/Switch/renderSwitch.tsx:17-20`）。
- `disabledFocusable` は、`disabled` の代わりに `aria-disabled="true"` を付ける（`useSwitch.tsx:93`）。v9 はクリックと Space、Enter を `preventDefault` で止める。この振る舞いは `choice.js` に入れていない。CSS の見た目だけを再現する。
- キーボード: ネイティブの checkbox と同じで、Space で切り替える。

### バリエーション

| prop | data 属性 | 値 | 既定 | 出典 |
|---|---|---|---|---|
| `size` | `data-size` | `small`、`medium` | `medium` | `Switch.types.ts:81` |
| `labelPosition` | `data-label-position` | `above`、`after`、`before` | `after` | `Switch.types.ts:74` |
| `checked` | ネイティブの `checked` | — | `false` | `Switch.types.ts:52` |
| `disabled`、`disabledFocusable` | `disabled`、`aria-disabled="true"` | — | — | `Switch.types.ts:60` |

### 寸法

| 項目 | medium | small | 出典 |
|---|---|---|---|
| トラックの幅 × 高さ | 40px × 20px（直書き） | 32px × 16px（直書き） | :21-30、:54-61、:89-93 |
| つまみ（indicator の `font-size`） | 18px（20 − 2） | 14px（16 − 2） | :22-30、:54、:90 |
| つまみの見える円の直径 | 14.4px（推論。円は 20 の箱の中の半径 8） | 11.2px（推論） | — |
| checked のつまみの移動 | `translateX(20px)`（40 − 18 − 2） | `translateX(16px)`（32 − 14 − 2） | :108-115、:247-256 |
| トラックの線と角丸 | `1px solid`（直書き）、`borderRadiusCircular` | 同じ | :48-49 |
| トラックの margin | `spacingVerticalS spacingHorizontalS`。label が上なら `margin-top: 0` | 同じ | :56、:86-88 |
| input の幅 | `calc(40px + 2 * spacingHorizontalS)` = 56px（推論で算出） | `calc(32px + 2 * …)` = 48px | :106、:248 |
| input（above） | 幅 100%、高さ `calc(20px + spacingVerticalS)` = 28px（推論で算出） | small の幅で上書きされる | :242-246 |
| label の文字 | `fontSizeBase300` / `lineHeightBase300` | `fontSizeBase200` / `lineHeightBase200` | :270-272 |
| label の padding | `spacingVerticalS spacingHorizontalS`。トラックの側は `spacingHorizontalXS`。above は上下が `spacingVerticalXS` | 同じ | :268、:276-286 |
| label の上下の margin | `calc((20px - lineHeightBase300) / 2)` = 0 | `calc((16px - lineHeightBase200) / 2)` = 0 | :266-274 |

input の順は labelPosition → small である（:321-327）。このため small の幅は、above の `width: 100%` も上書きする。CSS でも同じ順に書いた。

### 色と状態（トークン名の表）

つまみの色は indicator の `color` である（アイコンが `fill: currentColor`）。

| 状態 | トラックの塗り | トラックの線 | つまみ | ラベル | 出典 |
|---|---|---|---|---|---|
| unchecked | なし | `colorNeutralStrokeAccessible` | `colorNeutralStrokeAccessible` | `colorNeutralForeground1` | :132-140 |
| unchecked hover | なし | `colorNeutralStrokeAccessibleHover` | 線と同じ | 同上 | :142-147 |
| unchecked pressed（`:hover:active`） | なし | `colorNeutralStrokeAccessiblePressed` | 線と同じ | 同上 | :149-154 |
| checked | `colorCompoundBrandBackground` | `colorTransparentStroke` | `colorNeutralForegroundInverted` | 同上 | :158-163 |
| checked hover | `colorCompoundBrandBackgroundHover` | `colorTransparentStrokeInteractive` | 同上 | 同上 | :165-170 |
| checked pressed | `colorCompoundBrandBackgroundPressed` | `colorTransparentStrokeInteractive` | 同上 | 同上 | :172-177 |
| disabled、unchecked | なし | `colorNeutralStrokeDisabled` | `colorNeutralForegroundDisabled` | `colorNeutralForegroundDisabled`、`cursor: default` | :118-129、:181-185 |
| disabled、checked | `colorNeutralBackgroundDisabled` | `colorTransparentStrokeDisabled` | 同上 | 同上 | :188-193 |

disabled の規則は `:disabled` と `[aria-disabled="true"]` の両方に当たる。つまみの移動は disabled でも付く。

### フォーカス・動き・ハイコントラスト

- フォーカス: 根に `createFocusOutlineStyle({ style: {}, selector: 'focus-within' })` が付く（:38）。値は Checkbox と同じである。
- 動き: トラックは `background, border, color`、つまみは `transform` を、どちらも `durationNormal` と `curveEasyEase` で変える（:58-60、:74-78）。`prefers-reduced-motion: reduce` では `transition-duration: 0.01ms` にする（:63-65、:79-81）。
- ハイコントラスト: トラックの `color` は `CanvasText`（:67-72）。checked は塗り `Highlight`、つまみ `Canvas`（:212-229）。disabled はトラックとラベルが `GrayText`（:196-205）。

### 実装の例

```html demo
<div style="display:flex; flex-wrap:wrap; gap:8px 24px">
  <div class="fui-Switch">
    <input class="fui-Switch__input" type="checkbox" role="switch" id="choice-sw-1">
    <div class="fui-Switch__indicator" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M10 2a8 8 0 1 0 0 16 8 8 0 0 0 0-16"/></svg></div>
    <label class="fui-Label fui-Switch__label" for="choice-sw-1">機内モード</label>
  </div>
  <div class="fui-Switch">
    <input class="fui-Switch__input" type="checkbox" role="switch" id="choice-sw-2" checked>
    <div class="fui-Switch__indicator" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M10 2a8 8 0 1 0 0 16 8 8 0 0 0 0-16"/></svg></div>
    <label class="fui-Label fui-Switch__label" for="choice-sw-2">Wi-Fi</label>
  </div>
  <div class="fui-Switch">
    <input class="fui-Switch__input" type="checkbox" role="switch" id="choice-sw-3" disabled>
    <div class="fui-Switch__indicator" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M10 2a8 8 0 1 0 0 16 8 8 0 0 0 0-16"/></svg></div>
    <label class="fui-Label fui-Switch__label" for="choice-sw-3">無効</label>
  </div>
  <div class="fui-Switch">
    <input class="fui-Switch__input" type="checkbox" role="switch" id="choice-sw-4" checked disabled>
    <div class="fui-Switch__indicator" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M10 2a8 8 0 1 0 0 16 8 8 0 0 0 0-16"/></svg></div>
    <label class="fui-Label fui-Switch__label" for="choice-sw-4">無効でオン</label>
  </div>
</div>
```

```html demo
<div style="display:flex; flex-wrap:wrap; align-items:flex-start; gap:8px 24px">
  <div class="fui-Switch" data-size="small">
    <input class="fui-Switch__input" type="checkbox" role="switch" id="choice-sw-5" checked>
    <div class="fui-Switch__indicator" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M10 2a8 8 0 1 0 0 16 8 8 0 0 0 0-16"/></svg></div>
    <label class="fui-Label fui-Switch__label" for="choice-sw-5">small</label>
  </div>
  <div class="fui-Switch" data-label-position="before">
    <input class="fui-Switch__input" type="checkbox" role="switch" id="choice-sw-6">
    <label class="fui-Label fui-Switch__label" for="choice-sw-6">ラベルが前</label>
    <div class="fui-Switch__indicator" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M10 2a8 8 0 1 0 0 16 8 8 0 0 0 0-16"/></svg></div>
  </div>
  <div class="fui-Switch" data-label-position="above">
    <input class="fui-Switch__input" type="checkbox" role="switch" id="choice-sw-7" checked>
    <label class="fui-Label fui-Switch__label" for="choice-sw-7">ラベルが上</label>
    <div class="fui-Switch__indicator" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M10 2a8 8 0 1 0 0 16 8 8 0 0 0 0-16"/></svg></div>
  </div>
</div>
```

### v9 との差と未確認の点

- RTL では、つまみの移動を `translateX(-20px)`（small は `-16px`）に反転した。v9 のソースは `translateX(20px)` だけを書いている。Griffel の RTL 変換が `translateX` を反転するという前提の推論で、実物では確かめていない。
- v9 は label が無いとき、input の位置の規則と、above のトラックの `margin-top: 0` を付けない（:315、:324）。above の規則は `:has(> .fui-Switch__label)` で同じ条件にした。after の位置（`inset-inline-start: 0; top: 0`）は label が無くても付けるが、input の静的な位置と同じなので見た目は変わらない（推論）。
- `disabledFocusable` の操作の抑止は再現していない。
- サイトは size を扱っていない。

## Slider

出典: `packages/react-components/react-slider/library/src/components/Slider/useSliderStyles.styles.ts`（以下、行番号だけのものはこのファイル）、`…/Slider/useSliderState.tsx`、`…/Slider/useSlider.ts`、`…/Slider/Slider.types.ts`。

### 概要と使い分け（Do / Don't）

Slider は、範囲の中から値を選ばせる。音量のようにすぐ反映する使い方も、フォームのように送信を待つ使い方もある。目盛りの無い形と、ステップに区切って最も近い目盛りに吸い付く形がある。縦にも横にも置ける。

- Do: おおよその値を選ぶときに使う。範囲が表すものを短いラベルで書き、最小と最大の値を示す。数値でない範囲は「低／高」のような対の語にする。
- Do: 見た目で隠してもよいので、必ずラベルを付ける。現在値をツールチップで出すなら、スクリーンリーダーにも伝える。
- Don't: 範囲がとても狭いか広いときに使わない。金額のような正確な値は入力欄にする。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

| スロット | 要素 | class | 役割 |
|---|---|---|---|
| root | `div` | `fui-Slider` | 3×3 の grid。中央のセルにレールとつまみを置く |
| input | `input type="range"` | `fui-Slider__input` | 透明で、grid の全体に広がる |
| rail | `div` | `fui-Slider__rail` | レール。背景の gradient で進み具合を描く |
| thumb | `div` | `fui-Slider__thumb` | つまみ |

- input の `type="range"` と、縦のときの `orient="vertical"` は `useSlider.ts:71-72`、`aria-orientation` は `useSlider.ts:81-82` にある。
- v9 は根の style に 3 つの変数を入れる（`useSliderState.tsx:36-51`）。`--fui-Slider--progress` は値の百分率、`--fui-Slider--steps-percent` は `step` を渡したときの `step * 100 / (max - min)` %、`--fui-Slider--direction` は gradient の向きである。
- React を使わない HTML では、`--fui-Slider--direction` を CSS の既定値（横 90deg、RTL 270deg、縦 0deg）で出す。`--fui-Slider--progress` の初期値は、根の `data-percent`（0〜100 の整数）で渡す（独自）。style 属性を使わないので、インラインの style を禁じる CSP（`style-src 'self'`）の下でも、JS がなくても塗りが出る。`data-fui-enhance` を付けると、`choice.js` が input の値から `--fui-Slider--progress` と `--fui-Slider--steps-percent` を CSSOM で書き直す（端数も保つ）。
- キーボード: ネイティブの range と同じである（矢印、Home、End、PageUp、PageDown）。

### バリエーション

| prop | data 属性 / 属性 | 値 | 既定 | 出典 |
|---|---|---|---|---|
| `size` | `data-size` | `small`、`medium` | `medium` | `Slider.types.ts:73` |
| `vertical` | `data-vertical` | 真偽 | なし | `Slider.types.ts:92` |
| `min`、`max` | `min`、`max` | 数 | 0、100 | `useSliderState.tsx:12` |
| `step` | `step` | 数 | 目盛りは `step` を書いたときだけ描く | `useSliderState.tsx:36` |
| `disabled` | `disabled` | — | — | `Slider.types.ts:55` |

### 寸法

| 項目 | small | medium | 出典 |
|---|---|---|---|
| つまみの直径（`--fui-Slider__thumb--size`） | 16px | 20px | :44-56 |
| 端でのつまみの中心の位置（`--fui-Slider__inner-thumb--radius`） | 5px | 6px | :44-56 |
| レールの太さ（`--fui-Slider__rail--size`） | 2px | 4px | :44-56 |
| 根の最小の高さ | 24px | 32px | :44-56 |
| 横の最小の幅、縦の最小の高さ | 120px | 120px | :58-70 |
| つまみの白い環（inset の影 `calc(thumb * .2)`） | 3.2px（推論で算出） | 4px（推論で算出） | :205 |
| つまみの外周の線（`calc(thumb * .05)`、`colorNeutralStroke1`） | 0.8px（推論で算出） | 1px（推論で算出） | :207-217 |
| レールの角丸 | `borderRadiusXLarge` | 同じ | :122 |
| 目盛り | 各ステップの終わり 1px を `colorNeutralBackground1` で塗る | 同じ | :140-150 |

根の順は root → focus → size → 向き → enabled / disabled である（:283-291）。縦の `min-height: 120px` は size の値を上書きする。

### 色と状態（トークン名の表）

| 状態 | レール | 進み具合 | つまみ | 出典 |
|---|---|---|---|---|
| rest | `colorNeutralStrokeAccessible` | `colorCompoundBrandBackground` | `colorCompoundBrandBackground` | :72-75 |
| hover（根の `:hover`） | 同じ | `colorCompoundBrandBackgroundHover` | `colorCompoundBrandBackgroundHover` | :76-79 |
| pressed（根の `:active`） | 同じ | `colorCompoundBrandBackgroundPressed` | `colorCompoundBrandBackgroundPressed` | :80-83 |
| disabled | `colorNeutralBackgroundDisabled` | `colorNeutralForegroundDisabled` | `colorNeutralForegroundDisabled`。外周の線も同じ色 | :95-98、:219-223 |

つまみの白い環は常に `colorNeutralBackground1`、外周の線は `colorNeutralStroke1` である。

### フォーカス・動き・ハイコントラスト

- フォーカス: 根に `createFocusOutlineStyle` が付き、オフセットを渡している（:106-114）。`getOutlinePosition` の式 `calc(0px - 2px - offset)`（`createFocusOutlineStyle.ts:35-46`）に通すと、横は上下 0、左右 2px、縦は上下 0、左右 -6px になる（推論で算出）。CSS には式のまま書いた。つまみ自体は `outline-style: none`（:202）。
- 動き: transition は無い。
- ハイコントラスト: 有効のときレールは `CanvasText`、つまみと進み具合は `Highlight`（:84-92）。無効はすべて `GrayText`（:99-103）。目盛りは `HighlightText`（:152-160）。レールとつまみは `forced-color-adjust: none`（:129、:203）。

### 実装の例

```html demo
<div style="display:flex; flex-direction:column; gap:8px; max-width:320px">
  <label class="fui-Label" for="choice-sl-1">音量</label>
  <div class="fui-Slider" data-fui-enhance data-percent="40">
    <input class="fui-Slider__input" type="range" id="choice-sl-1" min="0" max="100" value="40" aria-orientation="horizontal">
    <div class="fui-Slider__rail"></div>
    <div class="fui-Slider__thumb"></div>
  </div>
  <label class="fui-Label" for="choice-sl-2">明るさ（small、10 ごとの目盛り）</label>
  <div class="fui-Slider" data-size="small" data-fui-enhance data-percent="70">
    <input class="fui-Slider__input" type="range" id="choice-sl-2" min="0" max="100" step="10" value="70" aria-orientation="horizontal">
    <div class="fui-Slider__rail"></div>
    <div class="fui-Slider__thumb"></div>
  </div>
  <label class="fui-Label" for="choice-sl-3">無効</label>
  <div class="fui-Slider" data-fui-enhance data-percent="30">
    <input class="fui-Slider__input" type="range" id="choice-sl-3" min="0" max="100" value="30" disabled aria-orientation="horizontal">
    <div class="fui-Slider__rail"></div>
    <div class="fui-Slider__thumb"></div>
  </div>
</div>
```

```html demo
<div class="fui-Slider" data-vertical data-fui-enhance data-percent="60">
  <input class="fui-Slider__input" type="range" min="0" max="100" value="60" orient="vertical" aria-orientation="vertical" aria-label="縦の Slider">
  <div class="fui-Slider__rail"></div>
  <div class="fui-Slider__thumb"></div>
</div>
```

### v9 との差と未確認の点

- `--fui-Slider--direction` は、v9 が JS（FluentProvider の `dir`）で決める。ここでは CSS の `:dir(rtl)` で決めた。
- RTL では、つまみの `left` と `translateX(-50%)` を論理プロパティと `translateX(50%)` に置き換えた。Griffel の RTL 変換が `translateX` も反転するという前提の推論である。
- 縦の input の書き方（`writing-mode: vertical-lr` と `-webkit-appearance: slider-vertical` の出し分け）は v9 の `@supports` のとおり（:258-268）。
- サイトは size と状態を扱っていない。

## Rating

出典: `packages/react-components/react-rating/library/src/components/RatingItem/useRatingItemStyles.styles.ts`（以下、行番号だけのものはこのファイル）、`…/Rating/useRatingStyles.styles.ts`、`…/RatingDisplay/useRatingDisplayStyles.styles.ts`、`…/RatingItem/useRatingItem.tsx`、`…/Rating/useRating.tsx`、`…/RatingDisplay/useRatingDisplay.tsx`。

### 概要と使い分け（Do / Don't）

Rating は評価を示し、製品やサービスの価値の判断を助ける。対話できる Rating は輪郭の星で、押して評価を送れることを示す。RatingDisplay は送信済みの評価を示し、星の列に点数と件数を添える。RatingDisplay の compact は、星 1 つに点数と件数を添える狭い場所向けの形である。

- Do: 前景と背景、選んだ星と選んでいない星の間に 3:1 以上のコントラストを保つ。値（例 3.5）を文字で示すなら、図を支援技術から隠してよい。
- Do: 入力を求めるときは大きめの size（extra-large）を使う。
- Don't: 図だけで値を伝えない。

サイトに明示の Do / Don't と文言の指針は無い。上はサイトの説明の要約である。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

| 部品 | 要素 | class | 役割 |
|---|---|---|---|
| Rating の root | `div role="radiogroup"` | `fui-Rating` | `aria-label` などで名前を付ける |
| RatingDisplay の root | `div role="img"` | `fui-RatingDisplay` | `aria-labelledby` に値と件数の id を入れる |
| RatingItem の root | `span` | `fui-RatingItem` | 星 1 つ。RatingDisplay では `aria-hidden="true"` |
| halfValueInput | `input type="radio"` | `fui-RatingItem__halfValueInput` | `step` が 0.5 のときだけ。左半分 |
| fullValueInput | `input type="radio"` | `fui-RatingItem__fullValueInput` | Rating のときだけ。half があれば右半分 |
| unselectedIcon | `div aria-hidden="true"` | `fui-RatingItem__unselectedIcon` | 選んでいない星 |
| selectedIcon | `div aria-hidden="true"` | `fui-RatingItem__selectedIcon` | 選んだ星 |
| valueText、countText | `span aria-hidden="true"` | `fui-RatingDisplay__valueText`、`fui-RatingDisplay__countText` | 点数と件数 |

- 並びは half、full、unselected、selected の順である（`…/RatingItem/renderRatingItem.tsx:16-19`）。input の `aria-label` の既定は値の数字である。
- v9 は塗りの割合（`iconFillWidth`）を 1、0.5、0 で決め、1 未満なら unselectedIcon を、0 より大きければ selectedIcon を描く（`useRatingItem.tsx:55-92`）。表示値は、hover 中は hover した値、そうでなければ 0.5 単位に丸めた値である（`useRatingItem.tsx:49-51`）。
- React を使わない HTML では、v9 が描かないアイコンを置かないか、RatingItem に `data-icon-fill-width="0|0.5|1"` を付ける。0.5 の項目には属性が必須である（左右の切り分けに使う）。対話できる Rating は、`data-fui-enhance` を付けると `choice.js` が選択と hover に合わせて属性を書き換える。
- 星は Rating の既定の `StarRegular` / `StarFilled`（`star_20_regular`、`star_20_filled`）を `1em` で描く。RatingDisplay は両方に `StarFilled` を使う。
- キーボード: ネイティブの radio と同じで、矢印キーで値が動く。

### バリエーション

| 対象 | prop | data 属性 | 値 | 既定 | 出典 |
|---|---|---|---|---|---|
| Rating | `size` | `data-size` | `small`、`medium`、`large`、`extra-large` | `extra-large` | `useRating.tsx:28` |
| Rating | `color` | `data-color` | `brand`、`marigold`、`neutral` | `neutral` | `useRating.tsx:27` |
| Rating | `step` | half の input の有無 | `0.5`、`1` | `1` | `useRating.tsx:60` |
| Rating | `max` | RatingItem の数 | 数 | 5 | `useRating.tsx:31` |
| RatingDisplay | `size` | `data-size` | 同上 | `medium` | `useRatingDisplay.tsx:27` |
| RatingDisplay | `color` | `data-color` | 同上 | `neutral` | `useRatingDisplay.tsx:27` |
| RatingDisplay | `compact` | RatingItem を 1 つにする | 真偽 | `false` | `useRatingDisplay.tsx:64` |

### 寸法

| 項目 | small | medium | large | extra-large | 出典 |
|---|---|---|---|---|---|
| RatingItem の幅、高さ、`font-size` | 12px | 16px | 20px | 28px | :25-47（直書き） |
| RatingDisplay の文字 | `caption1`（`fontSizeBase200` / `lineHeightBase200`） | 同じ | `fontSizeBase300` / `lineHeightBase300` | `fontSizeBase400` / `lineHeightBase400` | `useRatingDisplayStyles.styles.ts:24-40` |
| 文字の前の余白（`margin-inline-start`） | `spacingHorizontalXS` | `spacingHorizontalXS` | `spacingHorizontalSNudge` | `spacingHorizontalS` | 同上 |

- Rating と RatingDisplay の根は `display: flex`、`flex-wrap: wrap` で、星の間に gap は無い。RatingDisplay は `align-items: center` も付ける。
- valueText は `fontWeightSemibold` である。valueText があるとき、countText の前に `"· "` を足す（`useRatingDisplayStyles.styles.ts:41-48`）。
- 半分の表示では、selectedIcon を `inset-inline-end: 50%` で左半分に切り、svg を `flex: 0 0 auto` で縮めない。unselectedIcon は `inset-inline-start: 50%` と `margin-inline-start: -50%` で全幅に戻し、その上に selectedIcon を重ねる（:85-95）。

### 色と状態（トークン名の表）

| アイコン | neutral | brand | marigold | 出典 |
|---|---|---|---|---|
| 選んだ星（Rating、RatingDisplay） | `colorNeutralForeground1` | `colorBrandForeground1` | `colorPaletteMarigoldBorderActive` | :75、:96-101 |
| 選んでいない星（Rating、輪郭） | `colorNeutralForeground1` | `colorBrandForeground1` | `colorPaletteMarigoldBorderActive` | :163-164 |
| 選んでいない星（RatingDisplay、塗り） | `colorNeutralBackground6`、`stroke: colorTransparentStroke` | `colorBrandBackground2` | `colorPaletteMarigoldBackground2` | :102-120 |

hover は色を変えず、表示する値を変える。disabled の仕組みは無い。

### フォーカス・動き・ハイコントラスト

- フォーカス: RatingItem の根に `createFocusOutlineStyle({ style: {}, selector: 'focus-within' })` が付く（:23）。星 1 つを囲む。値は Checkbox と同じである。
- 動き: transition は無い。
- ハイコントラスト: RatingDisplay の選んでいない星は `color: Canvas`、`stroke: CanvasText`（:105-113）。Griffel ではメディアの規則が後に来るので、CSS でも color の規則の後に置いた。

### 実装の例

```html demo
<div style="display:flex; flex-direction:column; gap:12px">
  <div class="fui-Rating" role="radiogroup" aria-label="この記事の評価" data-fui-enhance>
    <span class="fui-RatingItem" data-icon-fill-width="1"><input class="fui-RatingItem__fullValueInput" type="radio" name="choice-rt-1" value="1" aria-label="1"><div class="fui-RatingItem__unselectedIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63zm.9.44L8.07 7.25a1 1 0 0 1-.75.55L3 8.43l3.12 3.04a1 1 0 0 1 .3.89l-.75 4.3 3.87-2.03a1 1 0 0 1 .93 0l3.86 2.03-.74-4.3a1 1 0 0 1 .29-.89L17 8.43l-4.32-.63a1 1 0 0 1-.75-.55z"/></svg></div><div class="fui-RatingItem__selectedIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63z"/></svg></div></span>
    <span class="fui-RatingItem" data-icon-fill-width="1"><input class="fui-RatingItem__fullValueInput" type="radio" name="choice-rt-1" value="2" aria-label="2"><div class="fui-RatingItem__unselectedIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63zm.9.44L8.07 7.25a1 1 0 0 1-.75.55L3 8.43l3.12 3.04a1 1 0 0 1 .3.89l-.75 4.3 3.87-2.03a1 1 0 0 1 .93 0l3.86 2.03-.74-4.3a1 1 0 0 1 .29-.89L17 8.43l-4.32-.63a1 1 0 0 1-.75-.55z"/></svg></div><div class="fui-RatingItem__selectedIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63z"/></svg></div></span>
    <span class="fui-RatingItem" data-icon-fill-width="1"><input class="fui-RatingItem__fullValueInput" type="radio" name="choice-rt-1" value="3" aria-label="3" checked><div class="fui-RatingItem__unselectedIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63zm.9.44L8.07 7.25a1 1 0 0 1-.75.55L3 8.43l3.12 3.04a1 1 0 0 1 .3.89l-.75 4.3 3.87-2.03a1 1 0 0 1 .93 0l3.86 2.03-.74-4.3a1 1 0 0 1 .29-.89L17 8.43l-4.32-.63a1 1 0 0 1-.75-.55z"/></svg></div><div class="fui-RatingItem__selectedIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63z"/></svg></div></span>
    <span class="fui-RatingItem" data-icon-fill-width="0"><input class="fui-RatingItem__fullValueInput" type="radio" name="choice-rt-1" value="4" aria-label="4"><div class="fui-RatingItem__unselectedIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63zm.9.44L8.07 7.25a1 1 0 0 1-.75.55L3 8.43l3.12 3.04a1 1 0 0 1 .3.89l-.75 4.3 3.87-2.03a1 1 0 0 1 .93 0l3.86 2.03-.74-4.3a1 1 0 0 1 .29-.89L17 8.43l-4.32-.63a1 1 0 0 1-.75-.55z"/></svg></div><div class="fui-RatingItem__selectedIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63z"/></svg></div></span>
    <span class="fui-RatingItem" data-icon-fill-width="0"><input class="fui-RatingItem__fullValueInput" type="radio" name="choice-rt-1" value="5" aria-label="5"><div class="fui-RatingItem__unselectedIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63zm.9.44L8.07 7.25a1 1 0 0 1-.75.55L3 8.43l3.12 3.04a1 1 0 0 1 .3.89l-.75 4.3 3.87-2.03a1 1 0 0 1 .93 0l3.86 2.03-.74-4.3a1 1 0 0 1 .29-.89L17 8.43l-4.32-.63a1 1 0 0 1-.75-.55z"/></svg></div><div class="fui-RatingItem__selectedIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63z"/></svg></div></span>
  </div>
  <div class="fui-Rating" role="radiogroup" aria-label="0.5 刻みの評価" data-size="large" data-color="marigold" data-fui-enhance>
    <span class="fui-RatingItem" data-icon-fill-width="1"><input class="fui-RatingItem__halfValueInput" type="radio" name="choice-rt-2" value="0.5" aria-label="0.5"><input class="fui-RatingItem__fullValueInput" type="radio" name="choice-rt-2" value="1" aria-label="1"><div class="fui-RatingItem__unselectedIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63zm.9.44L8.07 7.25a1 1 0 0 1-.75.55L3 8.43l3.12 3.04a1 1 0 0 1 .3.89l-.75 4.3 3.87-2.03a1 1 0 0 1 .93 0l3.86 2.03-.74-4.3a1 1 0 0 1 .29-.89L17 8.43l-4.32-.63a1 1 0 0 1-.75-.55z"/></svg></div><div class="fui-RatingItem__selectedIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63z"/></svg></div></span>
    <span class="fui-RatingItem" data-icon-fill-width="1"><input class="fui-RatingItem__halfValueInput" type="radio" name="choice-rt-2" value="1.5" aria-label="1.5"><input class="fui-RatingItem__fullValueInput" type="radio" name="choice-rt-2" value="2" aria-label="2"><div class="fui-RatingItem__unselectedIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63zm.9.44L8.07 7.25a1 1 0 0 1-.75.55L3 8.43l3.12 3.04a1 1 0 0 1 .3.89l-.75 4.3 3.87-2.03a1 1 0 0 1 .93 0l3.86 2.03-.74-4.3a1 1 0 0 1 .29-.89L17 8.43l-4.32-.63a1 1 0 0 1-.75-.55z"/></svg></div><div class="fui-RatingItem__selectedIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63z"/></svg></div></span>
    <span class="fui-RatingItem" data-icon-fill-width="1"><input class="fui-RatingItem__halfValueInput" type="radio" name="choice-rt-2" value="2.5" aria-label="2.5"><input class="fui-RatingItem__fullValueInput" type="radio" name="choice-rt-2" value="3" aria-label="3"><div class="fui-RatingItem__unselectedIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63zm.9.44L8.07 7.25a1 1 0 0 1-.75.55L3 8.43l3.12 3.04a1 1 0 0 1 .3.89l-.75 4.3 3.87-2.03a1 1 0 0 1 .93 0l3.86 2.03-.74-4.3a1 1 0 0 1 .29-.89L17 8.43l-4.32-.63a1 1 0 0 1-.75-.55z"/></svg></div><div class="fui-RatingItem__selectedIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63z"/></svg></div></span>
    <span class="fui-RatingItem" data-icon-fill-width="0.5"><input class="fui-RatingItem__halfValueInput" type="radio" name="choice-rt-2" value="3.5" aria-label="3.5" checked><input class="fui-RatingItem__fullValueInput" type="radio" name="choice-rt-2" value="4" aria-label="4"><div class="fui-RatingItem__unselectedIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63zm.9.44L8.07 7.25a1 1 0 0 1-.75.55L3 8.43l3.12 3.04a1 1 0 0 1 .3.89l-.75 4.3 3.87-2.03a1 1 0 0 1 .93 0l3.86 2.03-.74-4.3a1 1 0 0 1 .29-.89L17 8.43l-4.32-.63a1 1 0 0 1-.75-.55z"/></svg></div><div class="fui-RatingItem__selectedIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63z"/></svg></div></span>
    <span class="fui-RatingItem" data-icon-fill-width="0"><input class="fui-RatingItem__halfValueInput" type="radio" name="choice-rt-2" value="4.5" aria-label="4.5"><input class="fui-RatingItem__fullValueInput" type="radio" name="choice-rt-2" value="5" aria-label="5"><div class="fui-RatingItem__unselectedIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63zm.9.44L8.07 7.25a1 1 0 0 1-.75.55L3 8.43l3.12 3.04a1 1 0 0 1 .3.89l-.75 4.3 3.87-2.03a1 1 0 0 1 .93 0l3.86 2.03-.74-4.3a1 1 0 0 1 .29-.89L17 8.43l-4.32-.63a1 1 0 0 1-.75-.55z"/></svg></div><div class="fui-RatingItem__selectedIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63z"/></svg></div></span>
  </div>
</div>
```

```html demo
<div style="display:flex; flex-direction:column; gap:8px">
  <div class="fui-RatingDisplay" role="img" aria-labelledby="choice-rd-1-value choice-rd-1-count">
    <span class="fui-RatingItem" aria-hidden="true"><div class="fui-RatingItem__selectedIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63z"/></svg></div></span><span class="fui-RatingItem" aria-hidden="true"><div class="fui-RatingItem__selectedIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63z"/></svg></div></span><span class="fui-RatingItem" aria-hidden="true"><div class="fui-RatingItem__selectedIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63z"/></svg></div></span><span class="fui-RatingItem" aria-hidden="true" data-icon-fill-width="0.5"><div class="fui-RatingItem__unselectedIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63z"/></svg></div><div class="fui-RatingItem__selectedIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63z"/></svg></div></span><span class="fui-RatingItem" aria-hidden="true"><div class="fui-RatingItem__unselectedIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63z"/></svg></div></span>
    <span class="fui-RatingDisplay__valueText" id="choice-rd-1-value" aria-hidden="true">3.5</span>
    <span class="fui-RatingDisplay__countText" id="choice-rd-1-count" aria-hidden="true">1,160</span>
  </div>
  <div class="fui-RatingDisplay" role="img" data-size="large" data-color="brand" aria-labelledby="choice-rd-2-value">
    <span class="fui-RatingItem" aria-hidden="true"><div class="fui-RatingItem__selectedIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63z"/></svg></div></span><span class="fui-RatingItem" aria-hidden="true"><div class="fui-RatingItem__selectedIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63z"/></svg></div></span><span class="fui-RatingItem" aria-hidden="true"><div class="fui-RatingItem__selectedIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63z"/></svg></div></span><span class="fui-RatingItem" aria-hidden="true"><div class="fui-RatingItem__selectedIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63z"/></svg></div></span><span class="fui-RatingItem" aria-hidden="true"><div class="fui-RatingItem__unselectedIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63z"/></svg></div></span>
    <span class="fui-RatingDisplay__valueText" id="choice-rd-2-value" aria-hidden="true">4</span>
  </div>
  <div class="fui-RatingDisplay" role="img" data-color="marigold" aria-labelledby="choice-rd-3-value choice-rd-3-count">
    <span class="fui-RatingItem" aria-hidden="true"><div class="fui-RatingItem__selectedIcon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63z"/></svg></div></span>
    <span class="fui-RatingDisplay__valueText" id="choice-rd-3-value" aria-hidden="true">4.5</span>
    <span class="fui-RatingDisplay__countText" id="choice-rd-3-count" aria-hidden="true">87</span>
  </div>
</div>
```

3 つ目は compact の形である。v9 は compact のとき、値に関わらず星を塗る（`useRatingItem.tsx:56`）。

### v9 との差と未確認の点

- 描くアイコンの切り替えは、`data-icon-fill-width` と `display: none` で再現した。v9 のスタイルではなく、DOM の差を埋める仕組みである。
- hover の扱いは v9 と同じく、radio の input への `mouseover` で値を取り、根からの `mouseleave` で戻す（`useRating.tsx:106-116`）。
- 星の形は unpkg から取った `@fluentui/svg-icons` の最新版の `star_20_filled` と `star_20_regular` で、v9 が使う `@fluentui/react-icons` の版の形とは照合していない。
- サイトは既定の大きさを、対話用に extra-large とする箇所と、既定 16、最大 20 とする箇所で食い違って書いている。コードの既定（Rating は extra-large、RatingDisplay は medium）に従った。

## Tag

出典: `packages/react-components/react-tags/library/src/components/Tag/useTagStyles.styles.ts`（以下、行番号だけのものはこのファイル）、`…/InteractionTag/useInteractionTagStyles.styles.ts`、`…/InteractionTagPrimary/useInteractionTagPrimaryStyles.styles.ts`、`…/InteractionTagSecondary/useInteractionTagSecondaryStyles.styles.ts`、`…/TagGroup/useTagGroupStyles.styles.ts`、`…/Tag/useTag.tsx`。

### 概要と使い分け（Do / Don't）

Tag は、利用者が選んだ値（メールの宛先、分類など）を表す。できる操作は削除だけである。システムが作る読み取り専用のデータには Badge を使う。InteractionTag は、Tag が表す対象の詳しい情報や、関連する操作を出せるときに使う。副の操作は常に削除である。

- Do: Tag には必ず文字を入れる。最も大事な情報（別名ではなく名前など）を出す。一致しない入力（外部のメールアドレスなど）はそのまま出す。
- Do: 主の操作は、Tag が表す対象に直接関わる操作にする。
- Do: 隠れた Tag があるなら、数を示す「+n」の InteractionTag を同じ大きさで置ける。すべてを見る必要があるなら折り返す。
- Don't: 文字を省略記号で切らない。作業と関係ない操作や、作業を妨げる操作を InteractionTag に付けない。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

Tag:

| スロット | 要素 | class | 役割 |
|---|---|---|---|
| root | 削除できないとき `span`、削除できるとき `button type="button"` | `fui-Tag` | 全体。grid の領域 `"media primary dismissIcon" / "media secondary dismissIcon"` |
| media | `span` | `fui-Tag__media` | Avatar などを置く |
| icon | `span` | `fui-Tag__icon` | アイコン |
| primaryText | `span` | `fui-Tag__primaryText` | 主の文字 |
| secondaryText | `span` | `fui-Tag__secondaryText` | 副の文字 |
| dismissIcon | `span` | `fui-Tag__dismissIcon` | 削除の印（`DismissRegular`） |

- 選べる Tag は `aria-pressed` を付ける。TagGroup が `role="listbox"` なら、Tag に `role="option"` と `aria-selected` を付ける（`useTag.tsx:57`、`useTag.tsx:77-78`）。
- media に置く Avatar の大きさは、medium 28、small 20、extra-small 16 である（`useTag.tsx:10-14`）。
- 削除できる Tag は、クリックか Delete、Backspace で削除する。この振る舞いは利用する側で書く。

InteractionTag と TagGroup:

| 部品 | 要素 | class | 役割 |
|---|---|---|---|
| InteractionTag の root | `div` | `fui-InteractionTag` | appearance、shape、size、selected をここに書く |
| Primary | `button` | `fui-InteractionTagPrimary`（スロットは `__media`、`__icon`、`__primaryText`、`__secondaryText`） | 主の操作。TagGroup で選べるときは `aria-pressed` |
| Secondary | `button type="button"` | `fui-InteractionTagSecondary` | 削除。`aria-labelledby` に Primary と自分の id を入れる |
| TagGroup | `div role="toolbar"`（または `listbox`） | `fui-TagGroup` | 並べる入れ物。無効なら `aria-disabled="true"` |

- TagGroup のキーボード操作は、tabster の矢印のナビゲーション（循環、縦横、最後の位置を覚える）である（`…/TagGroup/useTagGroup.ts:97-101`）。React を使わない HTML では roving tabindex の JS が要る。`choice.js` には入れていない。
- v9 は TagGroup の size と appearance を子に配る。React を使わない HTML では、各 Tag と InteractionTag にも `data-size` と `data-appearance` を書く。TagGroup の `data-size` は gap だけを決める。

### バリエーション

| prop | data 属性 | 値 | 既定 | 出典 |
|---|---|---|---|---|
| `appearance` | `data-appearance` | `filled`、`outline`、`brand` | `filled` | `useTag.tsx:121` |
| `shape` | `data-shape` | `rounded`、`circular` | `rounded` | `useTag.tsx:121` |
| `size` | `data-size` | `medium`、`small`、`extra-small` | `medium` | `useTagGroup.ts:92` |
| `selected` | `aria-pressed="true"`、`aria-selected="true"`。InteractionTag は `data-selected` も可 | 真偽 | `false` | `Tag.types.ts:67`、`InteractionTag.types.ts:44` |
| `dismissible` | root を `button` にし、dismissIcon を置く | 真偽 | `false` | `useTag.tsx:40` |
| `disabled` | `disabled`、`aria-disabled="true"` | 真偽 | `false` | `Tag.types.ts:52` |

### 寸法

Tag:

| 項目 | medium | small | extra-small | 出典 |
|---|---|---|---|---|
| 高さ | 32px | 24px | 20px | :127-136（直書き） |
| media と icon が無いときの左端の余白 | 7px | 5px | 5px | :22-24、:181-191（直書き） |
| dismissIcon が無いときの右端の余白 | 7px | 5px | 5px | :195-205（直書き） |
| icon の幅と `font-size` | 20px | 16px | 12px | :26-28、:213-230 |
| icon の左右の padding | 7px、`spacingHorizontalXS` | 5px、`spacingHorizontalXXS` | 5px、`spacingHorizontalXXS` | :213-230 |
| media の左右の padding | 1px、`spacingHorizontalS` | 1px、`spacingHorizontalSNudge` | 1px、`spacingHorizontalSNudge` | :233-249 |
| dismissIcon の `font-size` と左右の padding | 20px、`spacingHorizontalXS`、7px | 16px、`spacingHorizontalXXS`、5px | 12px、`spacingHorizontalXXS`、5px | :267-281 |
| primaryText の文字 | `body1` | `caption1` | `caption1` | :327-335 |
| primaryText（secondaryText あり） | `caption1`、`margin-top: -2px` | 同じ | 同じ | :343-348 |
| secondaryText の文字 | `caption2` | 同じ | 同じ | :351-357 |
| TagGroup の `column-gap` | `spacingHorizontalS`（8px） | `spacingHorizontalSNudge`（6px） | `spacingHorizontalXS`（4px） | `useTagGroupStyles.styles.ts:19-27` |

- 根は `display: inline-grid`、`border: strokeWidthThin solid colorTransparentStroke`、角丸は rounded が `borderRadiusMedium`、circular が `borderRadiusCircular` である（:30-52、:78）。
- extra-small は、強制色でないとき根の上下に 2px の擬似要素を足し、押せる範囲を WCAG 2.2 の大きさにする（:133-154）。

InteractionTag:

| 項目 | medium | small | extra-small | 出典 |
|---|---|---|---|---|
| 高さ | 32px | 24px | 20px | `useInteractionTagStyles.styles.ts:23-31` |
| Primary の右の padding（Secondary なし） | 7px | 5px | 5px | `useInteractionTagPrimaryStyles.styles.ts:223-229` |
| Primary の右の padding（Secondary あり） | `spacingHorizontalS` | `spacingHorizontalSNudge` | `spacingHorizontalSNudge` | 同 :305-313 |
| Secondary の `font-size` と左右の padding | 20px、5px | 16px、3px | 12px、5px | `useInteractionTagSecondaryStyles.styles.ts:156-169` |

Primary は Secondary があるとき、右の角丸を `borderRadiusNone` にし、右の線を消す（同 :290-304）。Secondary は左の線を仕切り（`colorNeutralStroke1`）にし、左の角丸を `borderRadiusNone` にする（`useInteractionTagSecondaryStyles.styles.ts:35-41`）。

### 色と状態（トークン名の表）

Tag（根に hover の色は無い。dismissIcon だけが hover で変わる）:

| 状態 | 塗り | 文字 | 線 | 出典 |
|---|---|---|---|---|
| filled | `colorNeutralBackground3` | `colorNeutralForeground2` | `colorTransparentStroke` | :103-106 |
| outline | `colorSubtleBackground` | `colorNeutralForeground2` | `colorNeutralStroke1` | :107-111 |
| brand | `colorBrandBackground2` | `colorBrandForeground2` | `colorTransparentStroke` | :112-115 |
| selected | `colorBrandBackground` | `colorNeutralForegroundOnBrand` | `colorBrandStroke1` | :116-120 |
| disabled filled、brand | `colorNeutralBackgroundDisabled` | `colorNeutralForegroundDisabled` | `colorTransparentStrokeDisabled` | :158-175 |
| disabled outline | `colorSubtleBackground` | `colorNeutralForegroundDisabled` | `colorNeutralStrokeDisabled` | :164-169 |
| dismissIcon の hover / pressed | — | `colorCompoundBrandForeground1Hover` / `…Pressed`（selected は `colorNeutralForegroundOnBrand`） | — | :283-317 |

disabled はすべて `cursor: not-allowed` である。

InteractionTagPrimary:

| appearance | rest の塗り / 文字 | hover | pressed | 出典 |
|---|---|---|---|---|
| filled | `colorNeutralBackground3` / `colorNeutralForeground2` | `colorNeutralBackground3Hover` / `colorNeutralForeground2Hover` | `colorNeutralBackground3Pressed` / `colorNeutralForeground2Pressed` | `useInteractionTagPrimaryStyles.styles.ts:110-121` |
| outline（線 `colorNeutralStroke1`） | `colorSubtleBackground` / `colorNeutralForeground2` | `colorSubtleBackgroundHover` / `colorNeutralForeground2Hover`。Filled のアイコンを `colorNeutralForeground2BrandHover` で出す | `colorSubtleBackgroundPressed` / `colorNeutralForeground2Pressed`。Filled のアイコンは `…BrandPressed` | 同 :131-159 |
| brand | `colorBrandBackground2` / `colorBrandForeground2` | `colorBrandBackground2Hover` / `colorCompoundBrandForeground1Hover` | `colorBrandBackground2Pressed` / `colorCompoundBrandForeground1Pressed` | 同 :169-180 |
| selected（線 `colorBrandStroke1`） | `colorBrandBackground` / `colorNeutralForegroundOnBrand` | `colorBrandBackgroundHover` / 同じ | `colorBrandBackgroundPressed` / 同じ | 同 :190-222 |
| disabled | Tag の disabled と同じ | — | — | 同 :252-271 |

InteractionTagSecondary:

| appearance | rest の塗り / 文字 / 仕切り | hover | pressed | 出典 |
|---|---|---|---|---|
| filled（上下の線の幅 0） | `colorNeutralBackground3` / `colorNeutralForeground2` / `colorNeutralStroke1` | `colorNeutralBackground3Hover` / `colorNeutralForeground2BrandHover` | `colorNeutralBackground3Pressed` / `colorNeutralForeground2BrandPressed` | `useInteractionTagSecondaryStyles.styles.ts:44-57` |
| outline（線 `colorNeutralStroke1`） | `colorSubtleBackground` / `colorNeutralForeground2` / 同じ | `colorSubtleBackgroundHover` / `colorNeutralForeground2BrandHover` | `colorSubtleBackgroundPressed` / `colorNeutralForeground2BrandPressed` | 同 :69-81 |
| brand（上下の線の幅 0） | `colorBrandBackground2` / `colorBrandForeground2` / `colorBrandStroke2` | `colorBrandBackground2Hover` / `colorCompoundBrandForeground1Hover` | `colorBrandBackground2Pressed` / `colorCompoundBrandForeground1Pressed` | 同 :91-105 |
| selected（線 `colorBrandStroke1`） | `colorBrandBackground` / `colorNeutralForegroundOnBrand` / `colorNeutralStrokeOnBrand2` | `colorBrandBackgroundHover` | `colorBrandBackgroundPressed` | 同 :117-145 |
| disabled filled、brand | `colorNeutralBackgroundDisabled` / `colorNeutralForegroundDisabled` / `colorNeutralStrokeDisabled` | — | — | 同 :190-209 |
| disabled outline | `colorSubtleBackground` / `colorNeutralForegroundDisabled`、線 `colorNeutralStrokeDisabled` | — | — | 同 :197-202 |

### フォーカス・動き・ハイコントラスト

- フォーカス: Tag、Primary、Secondary は `createCustomFocusIndicatorStyle` で、要素自身に `outline: strokeWidthThick solid colorStrokeFocus2` を付ける（`useTagStyles.styles.ts:53-56`、`useInteractionTagPrimaryStyles.styles.ts:44-47`、`useInteractionTagSecondaryStyles.styles.ts:31-33`）。Tag は角丸も shape に合わせ、Primary は `z-index: 1` を足す。既定の selector は `focus`（`[data-fui-focus-visible]`）なので、`:focus-visible` で近似した。
- 動き: transition は無い。
- ハイコントラスト: Tag は `::before` で上の線を描く（副の文字の負の margin が線を隠すため。:58-72）。circular は左右の線も描く。selected は `forced-color-adjust: none` で `Highlight` / `HighlightText` にする（:121-125）。dismissIcon の hover と pressed は `Highlight`（:258-265）。InteractionTag の hover と pressed の塗りは `HighlightText`、selected は `Highlight`。

### 実装の例

```html demo
<div style="display:flex; flex-direction:column; gap:12px; align-items:flex-start">
  <div class="fui-TagGroup" role="toolbar" aria-label="宛先">
    <span class="fui-Tag"><span class="fui-Tag__primaryText">山田 太郎</span></span>
    <span class="fui-Tag" data-appearance="outline"><span class="fui-Tag__primaryText">佐藤 花子</span></span>
    <span class="fui-Tag" data-appearance="brand"><span class="fui-Tag__primaryText">開発チーム</span></span>
    <button class="fui-Tag" type="button" aria-label="鈴木 一郎、削除">
      <span class="fui-Tag__primaryText">鈴木 一郎</span>
      <span class="fui-Tag__dismissIcon"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="m4.09 4.22.06-.07a.5.5 0 0 1 .63-.06l.07.06L10 9.29l5.15-5.14a.5.5 0 0 1 .63-.06l.07.06c.18.17.2.44.06.63l-.06.07L10.71 10l5.14 5.15c.18.17.2.44.06.63l-.06.07a.5.5 0 0 1-.63.06l-.07-.06L10 10.71l-5.15 5.14a.5.5 0 0 1-.63.06l-.07-.06a.5.5 0 0 1-.06-.63l.06-.07L9.29 10 4.15 4.85a.5.5 0 0 1-.06-.63l.06-.07z"/></svg></span>
    </button>
    <button class="fui-Tag" type="button" disabled>
      <span class="fui-Tag__primaryText">無効</span>
      <span class="fui-Tag__dismissIcon"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="m4.09 4.22.06-.07a.5.5 0 0 1 .63-.06l.07.06L10 9.29l5.15-5.14a.5.5 0 0 1 .63-.06l.07.06c.18.17.2.44.06.63l-.06.07L10.71 10l5.14 5.15c.18.17.2.44.06.63l-.06.07a.5.5 0 0 1-.63.06l-.07-.06L10 10.71l-5.15 5.14a.5.5 0 0 1-.63.06l-.07-.06a.5.5 0 0 1-.06-.63l.06-.07L9.29 10 4.15 4.85a.5.5 0 0 1-.06-.63l.06-.07z"/></svg></span>
    </button>
  </div>
  <div class="fui-TagGroup" role="toolbar" aria-label="分類">
    <span class="fui-Tag" data-shape="circular">
      <span class="fui-Tag__icon"><svg class="fui-Icon fui-Icon-regular" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M14.5 3A2.5 2.5 0 0 1 17 5.5v9a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 3 14.5v-9A2.5 2.5 0 0 1 5.5 3zm0 1h-9C4.67 4 4 4.67 4 5.5v9c0 .83.67 1.5 1.5 1.5h9c.83 0 1.5-.67 1.5-1.5v-9c0-.83-.67-1.5-1.5-1.5M7 11a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2M7 7a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2"/></svg></span>
      <span class="fui-Tag__primaryText">予定</span>
      <span class="fui-Tag__secondaryText">来週</span>
    </span>
    <button class="fui-Tag" type="button" aria-pressed="true">
      <span class="fui-Tag__primaryText">選択中</span>
      <span class="fui-Tag__dismissIcon"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="m4.09 4.22.06-.07a.5.5 0 0 1 .63-.06l.07.06L10 9.29l5.15-5.14a.5.5 0 0 1 .63-.06l.07.06c.18.17.2.44.06.63l-.06.07L10.71 10l5.14 5.15c.18.17.2.44.06.63l-.06.07a.5.5 0 0 1-.63.06l-.07-.06L10 10.71l-5.15 5.14a.5.5 0 0 1-.63.06l-.07-.06a.5.5 0 0 1-.06-.63l.06-.07L9.29 10 4.15 4.85a.5.5 0 0 1-.06-.63l.06-.07z"/></svg></span>
    </button>
  </div>
  <div class="fui-TagGroup" role="toolbar" aria-label="大きさ" data-size="small">
    <span class="fui-Tag" data-size="small"><span class="fui-Tag__primaryText">small</span></span>
    <span class="fui-Tag" data-size="extra-small"><span class="fui-Tag__primaryText">extra-small</span></span>
  </div>
</div>
```

```html demo
<div class="fui-TagGroup" role="toolbar" aria-label="会議の参加者">
  <div class="fui-InteractionTag">
    <button class="fui-InteractionTagPrimary" id="choice-it-1-p">
      <span class="fui-InteractionTagPrimary__primaryText">山田 太郎</span>
    </button>
    <button class="fui-InteractionTagSecondary" type="button" id="choice-it-1-s" aria-label="削除" aria-labelledby="choice-it-1-p choice-it-1-s"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="m4.09 4.22.06-.07a.5.5 0 0 1 .63-.06l.07.06L10 9.29l5.15-5.14a.5.5 0 0 1 .63-.06l.07.06c.18.17.2.44.06.63l-.06.07L10.71 10l5.14 5.15c.18.17.2.44.06.63l-.06.07a.5.5 0 0 1-.63.06l-.07-.06L10 10.71l-5.15 5.14a.5.5 0 0 1-.63.06l-.07-.06a.5.5 0 0 1-.06-.63l.06-.07L9.29 10 4.15 4.85a.5.5 0 0 1-.06-.63l.06-.07z"/></svg></button>
  </div>
  <div class="fui-InteractionTag" data-appearance="outline">
    <button class="fui-InteractionTagPrimary" id="choice-it-2-p">
      <span class="fui-InteractionTagPrimary__icon"><svg class="fui-Icon fui-Icon-regular" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M14.5 3A2.5 2.5 0 0 1 17 5.5v9a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 3 14.5v-9A2.5 2.5 0 0 1 5.5 3zm0 1h-9C4.67 4 4 4.67 4 5.5v9c0 .83.67 1.5 1.5 1.5h9c.83 0 1.5-.67 1.5-1.5v-9c0-.83-.67-1.5-1.5-1.5M7 11a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2M7 7a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2"/></svg><svg class="fui-Icon fui-Icon-filled" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M14.5 3A2.5 2.5 0 0 1 17 5.5v9a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 3 14.5v-9A2.5 2.5 0 0 1 5.5 3zM7 11a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2M7 7a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2m3 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2"/></svg></span>
      <span class="fui-InteractionTagPrimary__primaryText">定例会</span>
    </button>
    <button class="fui-InteractionTagSecondary" type="button" id="choice-it-2-s" aria-label="削除" aria-labelledby="choice-it-2-p choice-it-2-s"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="m4.09 4.22.06-.07a.5.5 0 0 1 .63-.06l.07.06L10 9.29l5.15-5.14a.5.5 0 0 1 .63-.06l.07.06c.18.17.2.44.06.63l-.06.07L10.71 10l5.14 5.15c.18.17.2.44.06.63l-.06.07a.5.5 0 0 1-.63.06l-.07-.06L10 10.71l-5.15 5.14a.5.5 0 0 1-.63.06l-.07-.06a.5.5 0 0 1-.06-.63l.06-.07L9.29 10 4.15 4.85a.5.5 0 0 1-.06-.63l.06-.07z"/></svg></button>
  </div>
  <div class="fui-InteractionTag" data-appearance="brand" data-shape="circular">
    <button class="fui-InteractionTagPrimary">
      <span class="fui-InteractionTagPrimary__primaryText">+3</span>
    </button>
  </div>
  <div class="fui-InteractionTag" data-selected>
    <button class="fui-InteractionTagPrimary" id="choice-it-3-p">
      <span class="fui-InteractionTagPrimary__primaryText">選択中</span>
    </button>
    <button class="fui-InteractionTagSecondary" type="button" id="choice-it-3-s" aria-label="削除" aria-labelledby="choice-it-3-p choice-it-3-s"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="m4.09 4.22.06-.07a.5.5 0 0 1 .63-.06l.07.06L10 9.29l5.15-5.14a.5.5 0 0 1 .63-.06l.07.06c.18.17.2.44.06.63l-.06.07L10.71 10l5.14 5.15c.18.17.2.44.06.63l-.06.07a.5.5 0 0 1-.63.06l-.07-.06L10 10.71l-5.15 5.14a.5.5 0 0 1-.63.06l-.07-.06a.5.5 0 0 1-.06-.63l.06-.07L9.29 10 4.15 4.85a.5.5 0 0 1-.06-.63l.06-.07z"/></svg></button>
  </div>
</div>
```

### v9 との差と未確認の点

- primaryText は v9 が常に描くスロットなので、文字は `fui-Tag__primaryText` の中に入れる。
- v9 は media と icon の有無、secondaryText の有無、Secondary の有無を、描くスロットから決める。React を使わない CSS では `:has()` で同じ条件にした。
- InteractionTag の selected は、v9 では InteractionTag の `selected` か TagGroup の選択値から決まる。React を使わない HTML では根の `data-selected` か、Primary の `aria-pressed="true"` で表す。
- InteractionTag の selected は `background` の一括指定、appearance は `backgroundColor` で書かれている。React を使わない CSS では後に来る selected の一括指定が塗りを決める。Griffel が一括指定と個別の指定の優先をどう解決するかは確かめていない。
- サイトは「削除できる Tag は hover とフォーカスが全体に効く」と書くが、v9 の Tag の根に hover の塗りは無い。コードに従った。
- Tag の shape の JSDoc は `'round'` と書くが、コードの既定は `'rounded'` である。コードに従った。
- TagGroup の矢印キーの移動と、削除のあとのフォーカスの移動は再現していない。

## Badge

出典: `packages/react-components/react-badge/library/src/components/Badge/useBadgeStyles.styles.ts`（以下、行番号だけのものはこのファイル）、`…/CounterBadge/useCounterBadgeStyles.styles.ts`、`…/PresenceBadge/usePresenceBadgeStyles.styles.ts`、`…/Badge/useBadge.ts`、`…/CounterBadge/useCounterBadge.ts`、`…/PresenceBadge/usePresenceBadge.tsx`。

### 概要と使い分け（Do / Don't）

Badge は、関連する部品の状態や説明を示す小さな印である。短い文字、色、アイコンで素早く伝え、説明する対象の近くか上に置く。最大幅は無く、中身に合わせて伸びる。CounterBadge は数を、PresenceBadge は在席状態を示す。

- Do: 次の行動を示す意味の色を使う。警告や危険には、可能なら解決の手段を添える。
- Do: 文字は 1〜2 語で、sentence case にする。追加の情報はツールチップで出す。
- Do: アイコンだけの Badge には `aria-label` を付ける。別の部品に付く Badge は、その部品の名前で情報を伝える。
- Don't: 同じ文脈で大きさを混ぜない。文字を詰め込まない。切れるラベルにしない。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

| 部品 | 要素 | class | 役割 |
|---|---|---|---|
| Badge の root | `div`（文中なら `span` でよい） | `fui-Badge` | role は無い |
| icon | `span` | `fui-Badge__icon` | `data-icon-position` に従い、文字の前か後に置く |
| CounterBadge の root | 同上 | `fui-Badge fui-CounterBadge` | 中身は数。`count > overflowCount` なら `99+` のように書く |
| PresenceBadge の root | `span role="img" aria-label="…"` | `fui-PresenceBadge` | Badge のスタイルは使わない |
| PresenceBadge の icon | `span` | `fui-PresenceBadge__icon` | 状態と大きさに合うアイコンを置く |

- Badge は既定でフォーカスを受けない。ツールチップなどで対話するなら、フォーカスを受けられるようにする。
- CounterBadge の数の文字列は、利用する側で作る。v9 は `count` が 0 で `showZero` でなければ中身を描かない（`useCounterBadge.ts:48-50`）。中身が無く dot でもなければ、CSS が隠す。
- PresenceBadge の `aria-label` の既定は、状態の英語の文言である（`usePresenceBadge.tsx:46-55`）。日本語の画面では「連絡可能」などに置き換える。
- PresenceBadge のアイコンは状態と outOfOffice で決まる（`usePresenceBadge.tsx:25-44`）。

| status | 通常 | outOfOffice のとき |
|---|---|---|
| `available` | `presence_available_*_filled` | `presence_available_*_regular` |
| `away` | `presence_away_*_filled` | `presence_oof_*_regular` |
| `busy` | `presence_busy_*_filled` | `presence_unknown_*_regular` |
| `do-not-disturb` | `presence_dnd_*_filled` | `presence_dnd_*_regular` |
| `offline` | `presence_offline_*_regular` | `presence_oof_*_regular` |
| `out-of-office` | `presence_oof_*_regular` | 同じ |
| `unknown` | `presence_unknown_*_regular` | 同じ |
| `blocked` | `presence_blocked_*_regular` | 同じ |

`*` は大きさで、tiny と extra-small は 10、small は 12、medium は 16、large と extra-large は 20 である（`…/PresenceBadge/presenceIcons.ts:50-74` など）。

### バリエーション

| 対象 | prop | data 属性 | 値 | 既定 | 出典 |
|---|---|---|---|---|---|
| Badge | `appearance` | `data-appearance` | `filled`、`ghost`、`outline`、`tint` | `filled` | `useBadge.ts:11` |
| Badge | `color` | `data-color` | `brand`、`danger`、`important`、`informative`、`severe`、`subtle`、`success`、`warning` | `brand` | 同上 |
| Badge | `shape` | `data-shape` | `circular`、`rounded`、`square` | `circular` | 同上 |
| Badge | `size` | `data-size` | `tiny`、`extra-small`、`small`、`medium`、`large`、`extra-large` | `medium` | 同上 |
| Badge | `iconPosition` | `data-icon-position` | `before`、`after` | `before` | `useBadge.ts:31` |
| Badge | （アイコンだけ） | `data-icon-only` | 真偽 | なし | 独自（v9 は子の有無を見る） |
| CounterBadge | `appearance`、`color`、`shape` | 同上 | `filled`、`ghost` / `brand`、`danger`、`important`、`informative` / `circular`、`rounded` | `filled` / `brand` / `circular` | `useCounterBadge.ts:16` |
| CounterBadge | `dot` | `data-dot` | 真偽 | なし | `useCounterBadge.ts:39` |
| PresenceBadge | `status` | `data-status` | `available`、`away`、`busy`、`do-not-disturb`、`offline`、`out-of-office`、`unknown`、`blocked` | `available` | `usePresenceBadge.tsx:65` |
| PresenceBadge | `outOfOffice` | `data-out-of-office` | 真偽 | なし | `usePresenceBadge.tsx:64` |
| PresenceBadge | `size` | `data-size` | Badge と同じ 6 段 | `medium` | `usePresenceBadge.tsx:64` |

### 寸法

Badge:

| size | 高さ | 最小の幅 | 左右の padding | 文字 | icon の `font-size` | 出典 |
|---|---|---|---|---|---|---|
| tiny | 6px（幅も 6px） | `unset` | `unset` | `font-size: 4px; line-height: 4px` | 6px | :53-60、:279-281 |
| extra-small | 10px（幅も 10px） | `unset` | `unset` | `6px / 6px` | 10px | :61-68、:282-284 |
| small | 16px | 16px | `calc(spacingHorizontalXXS + spacingHorizontalXXS)` = 4px | `caption2Strong` | 12px | :47-49、:69-73 |
| medium | 20px | 20px | `calc(spacingHorizontalXS + spacingHorizontalXXS)` = 6px | `caption1Strong` | 12px | :18-28、:259 |
| large | 24px | 24px | 6px | `caption1Strong` | 16px | :77-81 |
| extra-large | 32px | 32px | `calc(spacingHorizontalSNudge + spacingHorizontalXXS)` = 8px | `caption1Strong` | 20px | :82-86 |

- 角丸: circular は `borderRadiusCircular`、rounded は `borderRadiusMedium`（tiny、extra-small、small は `borderRadiusSmall`）、square は `borderRadiusNone`（:28、:90-95）。
- 線: 根の `border-color` を `colorTransparentStroke` にし、`::after` に `strokeWidthThin` の線を描く。レイアウトに影響しない。ghost は `::after` を消す（:29-43、:98-104）。
- icon: `margin: 0 calc(-1 * spacingHorizontalXXS)` で根の文字用の余白を打ち消す。文字があるとき、文字の側の margin を `calc(spacingHorizontalXXS + spacingHorizontalXXS)`（extra-large は `calc(spacingHorizontalXS + spacingHorizontalXXS)`）にする（:255-275）。
- CounterBadge の dot: `min-width: auto; width: 6px; height: 6px; padding: 0`（`useCounterBadgeStyles.styles.ts:15-20`）。

PresenceBadge（`usePresenceBadgeStyles.styles.ts`）:

| size | アイコン | 大きさの強制 | 出典 |
|---|---|---|---|
| tiny | 10 | 6px（`aspect-ratio: 1`、svg を `!important` で 6px、`background-clip: unset`） | `usePresenceBadgeStyles.styles.ts:85-96` |
| extra-small | 10 | なし | — |
| small | 12 | なし | — |
| medium | 16 | なし | — |
| large | 20 | 20px | 同 :97-107 |
| extra-large | 20 | 28px（20px のアイコンを引き伸ばす） | 同 :108-118 |

根は `border-radius: borderRadiusCircular`、`background-color: colorNeutralBackground1`、`padding: 1px`、`background-clip: content-box` で、アイコンは `margin: -1px` で戻す（`usePresenceBadgeStyles.styles.ts:28-48`）。アイコンの縁で背景がにじむのを防ぐためである。

### 色と状態（トークン名の表）

Badge は対話しないので、hover や pressed は無い。表の「—」は v9 が値を書かないことを表す（塗りは無く、線は根の `colorTransparentStroke`）。

| color | filled（塗り / 文字） | ghost（文字） | outline（文字 / 線） | tint（塗り / 文字 / 線） |
|---|---|---|---|---|
| brand | `colorBrandBackground` / `colorNeutralForegroundOnBrand` | `colorBrandForeground1` | `colorBrandForeground1` / `currentColor` | `colorBrandBackground2` / `colorBrandForeground2` / `colorBrandStroke2` |
| danger | `colorPaletteRedBackground3` / `colorNeutralForegroundOnBrand` | `colorPaletteRedForeground3` | `colorPaletteRedForeground3` / `colorPaletteRedBorder2` | `colorPaletteRedBackground1` / `colorPaletteRedForeground1` / `colorPaletteRedBorder1` |
| important | `colorNeutralForeground1` / `colorNeutralBackground1` | `colorNeutralForeground1` | `colorNeutralForeground3` / `colorNeutralStrokeAccessible` | `colorNeutralForeground3` / `colorNeutralBackground1` / `colorTransparentStroke` |
| informative | `colorNeutralBackground5` / `colorNeutralForeground3` | `colorNeutralForeground3` | `colorNeutralForeground3` / `colorNeutralStroke2` | `colorNeutralBackground4` / `colorNeutralForeground3` / `colorNeutralStroke2` |
| severe | `colorPaletteDarkOrangeBackground3` / `colorNeutralForegroundOnBrand` | `colorPaletteDarkOrangeForeground3` | `colorPaletteDarkOrangeForeground3` / `currentColor` | `colorPaletteDarkOrangeBackground1` / `colorPaletteDarkOrangeForeground1` / `colorPaletteDarkOrangeBorder1` |
| subtle | `colorNeutralBackground1` / `colorNeutralForeground1` | `colorNeutralForegroundStaticInverted` | `colorNeutralForegroundStaticInverted` / `currentColor` | `colorNeutralBackground1` / `colorNeutralForeground3` / `colorNeutralStroke2` |
| success | `colorPaletteGreenBackground3` / `colorNeutralForegroundOnBrand` | `colorPaletteGreenForeground3` | `colorPaletteGreenForeground3` / `colorPaletteGreenBorder2` | `colorPaletteGreenBackground1` / `colorPaletteGreenForeground1` / `colorPaletteGreenBorder1` |
| warning | `colorPaletteYellowBackground3` / `colorNeutralForeground1Static` | `colorPaletteYellowForeground2` | `colorPaletteYellowForeground2` / `currentColor` | `colorPaletteYellowBackground1` / `colorPaletteYellowForeground1` / `colorPaletteYellowBorder1` |

出典は filled が :111-142、ghost が :149-172、outline が :176-206、tint が :213-252 である。

PresenceBadge のアイコンの色（根の `color`）:

| status | 通常 | outOfOffice のとき | 出典 |
|---|---|---|---|
| `available` | `colorPaletteLightGreenForeground3` | 同じ | `usePresenceBadgeStyles.styles.ts:57-59`、:72-74 |
| `busy`、`do-not-disturb`、`blocked` | `colorPaletteRedBackground3` | 同じ | 同 :51-53、:75-77 |
| `away` | `colorPaletteMarigoldBackground3` | `colorPaletteBerryForeground3` | 同 :54-56、:142-144 |
| `offline` | `colorNeutralForeground3` | `colorPaletteBerryForeground3` | 同 :60-62、:142-144 |
| `out-of-office` | `colorPaletteBerryForeground3` | 同じ | 同 :63-65 |
| `unknown` | `colorNeutralForeground3` | 同じ | 同 :66-68、:78-80 |

### フォーカス・動き・ハイコントラスト

- フォーカス: Badge 系にフォーカスの規則は無い。
- 動き: transition は無い。
- ハイコントラスト: Badge、CounterBadge、PresenceBadge に forced-colors の規則は無い。Badge は線を「なし」ではなく透明にしておき、強制色のときに線が見えるようにしている（:29-30 のコメント）。

### 実装の例

```html demo
<div style="display:grid; grid-template-columns:auto repeat(8, auto); gap:8px; align-items:center; justify-content:start">
  <span></span><span>brand</span><span>danger</span><span>important</span><span>informative</span><span>severe</span><span>subtle</span><span>success</span><span>warning</span>
  <span>filled</span><span><span class="fui-Badge" data-appearance="filled" data-color="brand">新着</span></span><span><span class="fui-Badge" data-appearance="filled" data-color="danger">新着</span></span><span><span class="fui-Badge" data-appearance="filled" data-color="important">新着</span></span><span><span class="fui-Badge" data-appearance="filled" data-color="informative">新着</span></span><span><span class="fui-Badge" data-appearance="filled" data-color="severe">新着</span></span><span><span class="fui-Badge" data-appearance="filled" data-color="subtle">新着</span></span><span><span class="fui-Badge" data-appearance="filled" data-color="success">新着</span></span><span><span class="fui-Badge" data-appearance="filled" data-color="warning">新着</span></span>
  <span>ghost</span><span><span class="fui-Badge" data-appearance="ghost" data-color="brand">新着</span></span><span><span class="fui-Badge" data-appearance="ghost" data-color="danger">新着</span></span><span><span class="fui-Badge" data-appearance="ghost" data-color="important">新着</span></span><span><span class="fui-Badge" data-appearance="ghost" data-color="informative">新着</span></span><span><span class="fui-Badge" data-appearance="ghost" data-color="severe">新着</span></span><span><span class="fui-Badge" data-appearance="ghost" data-color="subtle">新着</span></span><span><span class="fui-Badge" data-appearance="ghost" data-color="success">新着</span></span><span><span class="fui-Badge" data-appearance="ghost" data-color="warning">新着</span></span>
  <span>outline</span><span><span class="fui-Badge" data-appearance="outline" data-color="brand">新着</span></span><span><span class="fui-Badge" data-appearance="outline" data-color="danger">新着</span></span><span><span class="fui-Badge" data-appearance="outline" data-color="important">新着</span></span><span><span class="fui-Badge" data-appearance="outline" data-color="informative">新着</span></span><span><span class="fui-Badge" data-appearance="outline" data-color="severe">新着</span></span><span><span class="fui-Badge" data-appearance="outline" data-color="subtle">新着</span></span><span><span class="fui-Badge" data-appearance="outline" data-color="success">新着</span></span><span><span class="fui-Badge" data-appearance="outline" data-color="warning">新着</span></span>
  <span>tint</span><span><span class="fui-Badge" data-appearance="tint" data-color="brand">新着</span></span><span><span class="fui-Badge" data-appearance="tint" data-color="danger">新着</span></span><span><span class="fui-Badge" data-appearance="tint" data-color="important">新着</span></span><span><span class="fui-Badge" data-appearance="tint" data-color="informative">新着</span></span><span><span class="fui-Badge" data-appearance="tint" data-color="severe">新着</span></span><span><span class="fui-Badge" data-appearance="tint" data-color="subtle">新着</span></span><span><span class="fui-Badge" data-appearance="tint" data-color="success">新着</span></span><span><span class="fui-Badge" data-appearance="tint" data-color="warning">新着</span></span>
</div>
```

```html demo
<div style="display:flex; flex-direction:column; gap:12px">
  <div style="display:flex; flex-wrap:wrap; gap:8px; align-items:center">
    <span class="fui-Badge" data-size="tiny" aria-label="新着"></span>
    <span class="fui-Badge" data-size="extra-small" aria-label="新着"></span>
    <span class="fui-Badge" data-size="small">1</span>
    <span class="fui-Badge">2</span>
    <span class="fui-Badge" data-size="large">3</span>
    <span class="fui-Badge" data-size="extra-large">4</span>
  </div>
  <div style="display:flex; flex-wrap:wrap; gap:8px; align-items:center">
    <span class="fui-Badge" data-shape="circular">circular</span>
    <span class="fui-Badge" data-shape="rounded">rounded</span>
    <span class="fui-Badge" data-shape="square">square</span>
    <span class="fui-Badge" data-appearance="tint"><span class="fui-Badge__icon"><svg class="fui-Icon fui-Icon-regular" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M14.5 3A2.5 2.5 0 0 1 17 5.5v9a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 3 14.5v-9A2.5 2.5 0 0 1 5.5 3zm0 1h-9C4.67 4 4 4.67 4 5.5v9c0 .83.67 1.5 1.5 1.5h9c.83 0 1.5-.67 1.5-1.5v-9c0-.83-.67-1.5-1.5-1.5M7 11a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2M7 7a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2"/></svg></span>予定</span>
    <span class="fui-Badge" data-appearance="tint" data-icon-position="after">予定<span class="fui-Badge__icon"><svg class="fui-Icon fui-Icon-regular" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M14.5 3A2.5 2.5 0 0 1 17 5.5v9a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 3 14.5v-9A2.5 2.5 0 0 1 5.5 3zm0 1h-9C4.67 4 4 4.67 4 5.5v9c0 .83.67 1.5 1.5 1.5h9c.83 0 1.5-.67 1.5-1.5v-9c0-.83-.67-1.5-1.5-1.5M7 11a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2M7 7a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2"/></svg></span></span>
    <span class="fui-Badge" data-icon-only aria-label="予定"><span class="fui-Badge__icon"><svg class="fui-Icon fui-Icon-regular" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M14.5 3A2.5 2.5 0 0 1 17 5.5v9a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 3 14.5v-9A2.5 2.5 0 0 1 5.5 3zm0 1h-9C4.67 4 4 4.67 4 5.5v9c0 .83.67 1.5 1.5 1.5h9c.83 0 1.5-.67 1.5-1.5v-9c0-.83-.67-1.5-1.5-1.5M7 11a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2M7 7a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2m3 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2"/></svg></span></span>
  </div>
  <div style="display:flex; flex-wrap:wrap; gap:8px; align-items:center">
    <span class="fui-Badge fui-CounterBadge">5</span>
    <span class="fui-Badge fui-CounterBadge" data-color="danger">99+</span>
    <span class="fui-Badge fui-CounterBadge" data-appearance="ghost" data-color="informative">12</span>
    <span class="fui-Badge fui-CounterBadge" data-dot aria-label="未読あり"></span>
    <span class="fui-Badge fui-CounterBadge"></span>
  </div>
</div>
```

最後の CounterBadge は中身が無いので隠れる（count が 0 の形）。

```html demo
<div style="display:flex; flex-direction:column; gap:12px">
  <div style="display:flex; flex-wrap:wrap; gap:12px; align-items:center">
    <span class="fui-PresenceBadge" role="img" aria-label="連絡可能"><span class="fui-PresenceBadge__icon"><svg class="fui-Icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16m3.7-9.3-4 4a1 1 0 0 1-1.41 0l-2-2a1 1 0 1 1 1.42-1.4L7 8.58l3.3-3.3a1 1 0 0 1 1.4 1.42"/></svg></span></span>
    <span class="fui-PresenceBadge" role="img" aria-label="一時退席中" data-status="away"><span class="fui-PresenceBadge__icon"><svg class="fui-Icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16m.5-11.5v3.02l2.12 1.7a1 1 0 1 1-1.24 1.56l-2.5-2A1 1 0 0 1 6.5 8V4.5a1 1 0 0 1 2 0"/></svg></span></span>
    <span class="fui-PresenceBadge" role="img" aria-label="取り込み中" data-status="busy"><span class="fui-PresenceBadge__icon"><svg class="fui-Icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0"/></svg></span></span>
    <span class="fui-PresenceBadge" role="img" aria-label="応答不可" data-status="do-not-disturb"><span class="fui-PresenceBadge__icon"><svg class="fui-Icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16M5.25 7h5.5a1 1 0 1 1 0 2h-5.5a1 1 0 1 1 0-2"/></svg></span></span>
    <span class="fui-PresenceBadge" role="img" aria-label="オフライン" data-status="offline"><span class="fui-PresenceBadge__icon"><svg class="fui-Icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M10.7 5.3a1 1 0 0 1 0 1.4L9.42 8l1.3 1.3a1 1 0 0 1-1.42 1.4L8 9.42l-1.3 1.3a1 1 0 0 1-1.4-1.42L6.58 8l-1.3-1.3a1 1 0 0 1 1.42-1.4L8 6.58l1.3-1.3a1 1 0 0 1 1.4 0M0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8m8-6a6 6 0 1 0 0 12A6 6 0 0 0 8 2"/></svg></span></span>
    <span class="fui-PresenceBadge" role="img" aria-label="不在" data-status="out-of-office"><span class="fui-PresenceBadge__icon"><svg class="fui-Icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M8.2 6.2a1 1 0 1 0-1.4-1.4L4.3 7.3a1 1 0 0 0 0 1.4l2.5 2.5a1 1 0 0 0 1.4-1.4L7.42 9H11a1 1 0 1 0 0-2H7.41zM8 0a8 8 0 1 0 0 16A8 8 0 0 0 8 0M2 8a6 6 0 1 1 12 0A6 6 0 0 1 2 8"/></svg></span></span>
    <span class="fui-PresenceBadge" role="img" aria-label="不明" data-status="unknown"><span class="fui-PresenceBadge__icon"><svg class="fui-Icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M8 2a6 6 0 1 0 0 12A6 6 0 0 0 8 2M0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8"/></svg></span></span>
    <span class="fui-PresenceBadge" role="img" aria-label="ブロック中" data-status="blocked"><span class="fui-PresenceBadge__icon"><svg class="fui-Icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0m-2 0c0-1.3-.41-2.5-1.1-3.48L4.51 12.9A6 6 0 0 0 14 8m-2.52-4.9a6 6 0 0 0-8.37 8.37z"/></svg></span></span>
  </div>
  <div style="display:flex; flex-wrap:wrap; gap:12px; align-items:center">
    <span class="fui-PresenceBadge" role="img" aria-label="連絡可能、不在" data-out-of-office><span class="fui-PresenceBadge__icon"><svg class="fui-Icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M11.7 6.7a1 1 0 0 0-1.4-1.4L7 8.58l-1.3-1.3a1 1 0 0 0-1.4 1.42l2 2a1 1 0 0 0 1.4 0zM0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8m8-6a6 6 0 1 0 0 12A6 6 0 0 0 8 2"/></svg></span></span>
    <span class="fui-PresenceBadge" role="img" aria-label="一時退席中、不在" data-status="away" data-out-of-office><span class="fui-PresenceBadge__icon"><svg class="fui-Icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M8.2 6.2a1 1 0 1 0-1.4-1.4L4.3 7.3a1 1 0 0 0 0 1.4l2.5 2.5a1 1 0 0 0 1.4-1.4L7.42 9H11a1 1 0 1 0 0-2H7.41zM8 0a8 8 0 1 0 0 16A8 8 0 0 0 8 0M2 8a6 6 0 1 1 12 0A6 6 0 0 1 2 8"/></svg></span></span>
    <span class="fui-PresenceBadge" role="img" aria-label="取り込み中、不在" data-status="busy" data-out-of-office><span class="fui-PresenceBadge__icon"><svg class="fui-Icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M8 2a6 6 0 1 0 0 12A6 6 0 0 0 8 2M0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8"/></svg></span></span>
    <span class="fui-PresenceBadge" role="img" aria-label="オフライン、不在" data-status="offline" data-out-of-office><span class="fui-PresenceBadge__icon"><svg class="fui-Icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M8.2 6.2a1 1 0 1 0-1.4-1.4L4.3 7.3a1 1 0 0 0 0 1.4l2.5 2.5a1 1 0 0 0 1.4-1.4L7.42 9H11a1 1 0 1 0 0-2H7.41zM8 0a8 8 0 1 0 0 16A8 8 0 0 0 8 0M2 8a6 6 0 1 1 12 0A6 6 0 0 1 2 8"/></svg></span></span>
  </div>
  <div style="display:flex; flex-wrap:wrap; gap:12px; align-items:center">
    <span class="fui-PresenceBadge" role="img" aria-label="連絡可能" data-size="tiny"><span class="fui-PresenceBadge__icon"><svg class="fui-Icon" width="10" height="10" viewBox="0 0 10 10" fill="currentColor" aria-hidden="true"><path d="M5 10A5 5 0 1 0 5 0a5 5 0 0 0 0 10m2.1-5.9L4.85 6.35a.5.5 0 0 1-.7 0l-1-1a.5.5 0 0 1 .7-.7l.65.64 1.9-1.9a.5.5 0 0 1 .7.71"/></svg></span></span>
    <span class="fui-PresenceBadge" role="img" aria-label="連絡可能" data-size="extra-small"><span class="fui-PresenceBadge__icon"><svg class="fui-Icon" width="10" height="10" viewBox="0 0 10 10" fill="currentColor" aria-hidden="true"><path d="M5 10A5 5 0 1 0 5 0a5 5 0 0 0 0 10m2.1-5.9L4.85 6.35a.5.5 0 0 1-.7 0l-1-1a.5.5 0 0 1 .7-.7l.65.64 1.9-1.9a.5.5 0 0 1 .7.71"/></svg></span></span>
    <span class="fui-PresenceBadge" role="img" aria-label="連絡可能" data-size="small"><span class="fui-PresenceBadge__icon"><svg class="fui-Icon" width="12" height="12" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true"><path d="M6 12A6 6 0 1 0 6 0a6 6 0 0 0 0 12m2.53-6.72L5.78 8.03c-.3.3-.77.3-1.06 0l-1-1a.75.75 0 0 1 1.06-1.06l.47.47 2.22-2.22a.75.75 0 0 1 1.06 1.06"/></svg></span></span>
    <span class="fui-PresenceBadge" role="img" aria-label="連絡可能"><span class="fui-PresenceBadge__icon"><svg class="fui-Icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16m3.7-9.3-4 4a1 1 0 0 1-1.41 0l-2-2a1 1 0 1 1 1.42-1.4L7 8.58l3.3-3.3a1 1 0 0 1 1.4 1.42"/></svg></span></span>
    <span class="fui-PresenceBadge" role="img" aria-label="連絡可能" data-size="large"><span class="fui-PresenceBadge__icon"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M10 20a10 10 0 1 0 0-20 10 10 0 0 0 0 20m4.2-11.8-4.5 4.5a1 1 0 0 1-1.4 0l-2-2a1 1 0 1 1 1.4-1.4L9 10.58l3.8-3.8a1 1 0 1 1 1.4 1.42"/></svg></span></span>
    <span class="fui-PresenceBadge" role="img" aria-label="連絡可能" data-size="extra-large"><span class="fui-PresenceBadge__icon"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M10 20a10 10 0 1 0 0-20 10 10 0 0 0 0 20m4.2-11.8-4.5 4.5a1 1 0 0 1-1.4 0l-2-2a1 1 0 1 1 1.4-1.4L9 10.58l3.8-3.8a1 1 0 1 1 1.4 1.42"/></svg></span></span>
  </div>
</div>
```

### v9 との差と未確認の点

- v9 は、icon と文字の間隔を付けるかどうかを、子の数で決める（:327）。CSS では文字の有無を判定できないので、アイコンだけの Badge に `data-icon-only` を付けて外す。独自の属性である。
- color が `subtle` の ghost と outline は、文字が `colorNeutralForegroundStaticInverted`（白）なので、明るい背景では見えない。v9 のとおりで、暗い背景の上で使う前提の組み合わせである。
- CounterBadge の「中身が無ければ隠す」は `:empty` で近似した。空白の文字があると当たらない。
- PresenceBadge のアイコンのうち、取って確かめたのは 16 の `available`、`away`、`busy`、`do-not-disturb`（Filled）、`offline`、`out-of-office`、`unknown`、`blocked`、`available`（Regular）と、`available` の 10、12、20（Filled）である。`presence_dnd_*_regular` と、ほかの状態の 10、12、20 の形は未確認である。形は unpkg から取った `@fluentui/svg-icons` の最新版である。`presence_available_16_filled` は v9 のスナップショット `packages/react-components/react-badge/library/src/components/PresenceBadge/__snapshots__/PresenceBadge.test.tsx.snap:23` の path と一致した。Tag の `dismiss_20_regular` も、`packages/react-components/react-search/library/src/components/SearchBox/__snapshots__/SearchBox.test.tsx.snap:52` の `DismissRegular` と一致した。
- サイトは CounterBadge、PresenceBadge、size、shape、appearance、color を扱っていない。

