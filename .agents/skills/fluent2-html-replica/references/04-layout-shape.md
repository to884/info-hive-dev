# レイアウト、間隔、形状、線

この章は、ページの組み方（ブレークポイント、グリッド、余白、タッチターゲット）と、部品の形を決めるトークン（間隔、角丸、線の太さ）を定める。

結論を先に書く。

- 間隔、角丸、線は、v9 のトークン（`--spacingHorizontalM`、`--borderRadiusMedium`、`--strokeWidthThin` など）だけで書く。値は `@fluentui/tokens` 1.0.0-alpha.24 を正とする。
- 基本単位は 4px である。2px、6px、10px は、アイコンの余白の補正と部品の内側に限って使う。
- ブレークポイントはサイトの 6 段階に従う。ただし v9 はブレークポイントをトークンとして持たない。グリッドのガターとページの余白は Fluent に数値がないので、この設計書が独自に決めた（`assets/fluent2.css` の `layout` の部分）。
- 角丸は、標準の部品で 4px（`borderRadiusMedium`）にする。円とピルは `borderRadiusCircular`（10000px）で描き、50% は使わない。サイトの角丸の表はコードと食い違うので、コードに従う。

## 値の出どころ

| 対象 | 出どころ | 出典 |
|---|---|---|
| 間隔のトークン | 抽出 | `packages/tokens/src/global/spacings.ts:4-44`、CSS 変数名は `packages/tokens/src/tokens.ts:520-543` |
| 角丸のトークン | 抽出 | `packages/tokens/src/global/borderRadius.ts:3-15`、CSS 変数名は `packages/tokens/src/tokens.ts:451-461` |
| 線のトークン | 抽出 | `packages/tokens/src/global/strokeWidths.ts:3-8`、CSS 変数名は `packages/tokens/src/tokens.ts:515-518` |
| ブレークポイント、グリッド、タッチターゲット | サイトの指針 | fluent2.microsoft.design/layout |
| 形の種類と角丸の使い分け | サイトの指針 | fluent2.microsoft.design/shapes |
| ガター、ページの余白、ページの最大幅 | 独自（推論） | この章の「補助の CSS」 |

## レイアウト

### 基本単位

サイトは、基本単位を 4px とする。値は 4 の倍数を基本にし、アイコンの余白を補正するために 2、6、10 も使う。単位は、Web では px、iOS では pt、Android では dp である。余白は要素のバウンディングボックスから測る。

近い要素ほど関連して見える。余白でまとまりを示せば、罫線を引かずに内容を区切れる。周りに余白のある要素ほど重要に見える。部品の中では小さな間隔で結びつきを強め、パターンでは一定の間隔でリズムを作る。

### ブレークポイント

サイトの表（Size class と幅の範囲）は次のとおりである。サイトは、これをよくある機器の幅を代表する目安と説明している。

| Size class | 幅の範囲 | media query の書き方（この設計書） |
|---|---|---|
| small | 320〜479px | 既定（指定なし） |
| medium | 480〜639px | `@media (min-width: 480px)` |
| large | 640〜1023px | `@media (min-width: 640px)` |
| x-large | 1024〜1365px | `@media (min-width: 1024px)` |
| xx-large | 1366〜1919px | `@media (min-width: 1366px)` |
| xxx-large | 1920px 以上 | `@media (min-width: 1920px)` |

- v9 のコードは、この表をトークンとして持たない。部品ごとに個別の media query を書く。
- 例として、Dialog は `@media screen and (max-width: 480px)` で `max-width: 100vw` にし、`@media screen and (max-height: 359px)` で縦にスクロールさせる（`packages/react-components/react-dialog/library/src/contexts/constants.ts:1-2`、`packages/react-components/react-dialog/library/src/components/DialogSurface/useDialogSurfaceStyles.styles.ts:48-60`）。境界の 480px はサイトの表と 1px ずれる。部品の中ではコードの値を写す。
- CSS 変数は media query の条件に使えない。幅の値は直接書く。
- 1 つの流動的なレイアウト（Responsive）と、幅ごとに固定のレイアウト（Adaptive）は、どちらを使ってもよく、併用してもよい。

### グリッド

- グリッドは、列、ガター（列の間）、マージン（両端の余白）からなる。
- サイトは 12 列を一般的な形とする。12 列は 1/2、1/3、1/4、1/6 に分けられる。
- ガターは基本単位の倍数で、ブレークポイントごとに変えてよい。マージンは固定値か割合で、これもブレークポイントごとに変えてよい。**ガターとマージンの具体的な数値は、サイトにもコードにもない。**
- グリッドの種類は、baseline（文字の縦のリズム）、column（Web アプリで一般的な 12 列）、manuscript（読みやすい行の長さの 1 列）、modular（格子状のモジュール）がある。内容に合わせて、固定、伸縮、その混成を選ぶ。

この設計書の決定（独自）:

| 幅 | ページの左右の余白（`--f2-page-margin`） | ガター（`--f2-grid-gutter`） |
|---|---|---|
| 640px 未満 | 16px（`spacingHorizontalL`） | 16px（`spacingHorizontalL`） |
| 640〜1023px | 24px（`spacingHorizontalXXL`） | 24px（`spacingHorizontalXXL`） |
| 1024px 以上 | 32px（`spacingHorizontalXXXL`） | 24px（`spacingHorizontalXXL`） |

ページの最大幅（`--f2-page-max-width`）は 1366px とした。xx-large の下限に合わせた推論の値である。

### 揃えと領域

- 前景の要素を予測できる形に揃え、階層と関係をはっきりさせる。テキストは左揃え（RTL では右揃え。CSS では `text-align: start`）、単独のオブジェクトは中央揃えを基本にする。中央揃えは、注目を一点に集めたいときに使う。
- 列、行、モジュールをまとめて、構成の領域（region）を作る。最も重要な要素に、グリッドの最も大きな部分を割り当てる。
- サイトは、ヘッダー、ナビゲーション、本文といった画面の領域の寸法を定めていない。v9 の部品にある寸法は次のとおりである。

| 領域 | 値 | 出典 |
|---|---|---|
| Nav（左のナビゲーション）の既定の幅 | 260px | `packages/react-components/react-nav/library/src/components/sharedNavStyles.styles.ts:10` |
| Nav の選択の印 | 幅 4px、高さ 20px | `packages/react-components/react-nav/library/src/components/sharedNavStyles.styles.ts:11-13` |
| Drawer の幅 | small 320px、medium 592px、large 940px、full 100vw | `packages/react-components/react-drawer/library/src/shared/useDrawerBaseStyles.styles.ts:57-68` |
| Dialog | 最大幅 600px、内側の余白 24px、本文の gap 8px | `packages/react-components/react-dialog/library/src/components/DialogSurface/useDialogSurfaceStyles.styles.ts:39`、`packages/react-components/react-dialog/library/src/contexts/constants.ts:3-4` |

### レスポンシブの手法

サイトは、次の 5 つの手法を挙げる。

- 位置を変える（Reposition）: 縦に積んだものを横に並べる。
- 大きさを変える（Resize）: 大きさと余白を調整する。
- 流し直す（Reflow）: 1 列を 2 列にするなど。
- 表示を絞る（Show/hide）: 小さい画面では情報を減らす。
- 構成を変える（Re-architect）: 一覧と詳細を並べるか、畳む。

### 密度と操作部品の高さ

- サイトのレイアウトのページに、密度の記述はない。
- v9 は密度を部品の `size`（small、medium、large）で表す。操作部品の高さは 24px、32px、40px の 3 段階にそろう。
    - Input の高さは small 24px、medium 32px、large 40px（`packages/react-components/react-input/library/src/components/Input/useInputStyles.styles.ts:16-20`）。Select も同じ（`packages/react-components/react-select/library/src/components/Select/useSelectStyles.styles.ts:21-25`）。
    - Button の高さは「上下の余白 × 2 + 行の高さ + 枠 1px × 2」で同じ段階になる。small は 3px × 2 + 16px + 2px = 24px、medium は 5px × 2 + 20px + 2px = 32px、large は 8px × 2 + 22px + 2px = 40px である（余白は `packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:17-21`、行の高さは `packages/tokens/src/global/fonts.ts:19-21`）。この計算は推論で、各部品の章でコードの値を確かめる。
    - MenuItem の最小の高さは 32px（`packages/react-components/react-menu/library/src/components/MenuItem/useMenuItemStyles.styles.ts:35`）。

### タッチターゲット

- サイトは、最小のタッチターゲットを Web と iOS で 44 × 44、Android で 48 × 48 とする。
- v9 の部品は、この大きさを自動では確保しない。medium の部品の高さは 32px で、44px に届かない。
- この設計書の決定（独自）: タッチが主な操作の画面では、`data-size="large"`（40px）を選び、隣の部品との間に 4px 以上の間隔を取るか、部品の外側に余白を足して、押せる範囲を 44 × 44px 以上にする。部品の見た目の寸法は変えない。

### 補助の CSS（layout.css、独自）

`assets/fluent2.css` の `layout` の部分（開発用のリポジトリ（非公開）では `src/components/layout.css`）は、React を使わない HTML でページを組むための補助である。Fluent 2 の公式の部品ではないので、class 名は `fui-` ではなく `f2-` で始める。

| class | 働き | 属性 |
|---|---|---|
| `f2-page` | 最大幅で中央に置き、左右に `--f2-page-margin` の余白を取る | なし |
| `f2-app` | 1024px 以上で、ナビゲーション（`--f2-nav-width`、既定 260px）と本文の 2 列にする | なし |
| `f2-grid` | 12 列のグリッド。ガターは `--f2-grid-gutter` | 子に `data-span`、`data-span-large`（640px 以上）、`data-span-xlarge`（1024px 以上）で 1〜12 |
| `f2-stack` | 縦に積む。`data-direction="horizontal"` で横に並べて折り返す | `data-gap`（`none`、`xxs`、`xs`、`s-nudge`、`s`、`m-nudge`、`m`（既定）、`l`、`xl`、`xxl`、`xxxl`） |
| `f2-surface` | 不透明の面。影、角丸、線、背景の見本にも使う | `data-elevation`、`data-elevation-brand`、`data-radius`、`data-stroke`、`data-background` |
| `f2-scrim` | モーダルの背景幕（`colorBackgroundOverlay`） | なし |

サイトの Global spacing ramp には、v9 のトークンにない 36px 以上の段階（`size360` から `size560`）がある。layout.css では `--f2-size360`、`--f2-size400`、`--f2-size480`、`--f2-size520`、`--f2-size560` として定義した。部品の中では使わず、ページの領域の間隔にだけ使う。

12 列のグリッドの例を示す。幅を狭めると 1 列、640px 以上で 2 列、1024px 以上で 3 列になる。

```html demo
<div class="f2-grid">
  <div class="f2-surface" data-stroke="thin" data-span-large="6" data-span-xlarge="4">span 12 / 6 / 4</div>
  <div class="f2-surface" data-stroke="thin" data-span-large="6" data-span-xlarge="4">span 12 / 6 / 4</div>
  <div class="f2-surface" data-stroke="thin" data-span-large="12" data-span-xlarge="4">span 12 / 12 / 4</div>
  <div class="f2-surface" data-stroke="thin" data-span="3">span 3</div>
  <div class="f2-surface" data-stroke="thin" data-span="9">span 9</div>
</div>
```

## 間隔

### トークン

横（`spacingHorizontal*`）と縦（`spacingVertical*`）の 2 系統があり、値は同じである（`packages/tokens/src/global/spacings.ts:18-44`）。名前は軸を表す。基になる段階（`spacings.ts:4-16`）は公開されていない。

<!-- spec:tokens-spacing -->

| 段階 | 値 | 主な用途 |
|---|---|---|
| `None` | 0 | 余白を消す |
| `XXS` | 2px | 部品の中の最小の間（Input の中の gap、MenuList の項目の間） |
| `XS` | 4px | small のボタンのアイコンと文字の間、MenuItem の gap |
| `SNudge` | 6px | アイコンの補正。medium と large のボタンのアイコンと文字の間 |
| `S` | 8px | 部品の中の標準の間。small のボタンの左右の余白 |
| `MNudge` | 10px | アイコンの補正。Input の左右の余白（medium） |
| `M` | 12px | medium のボタンの左右の余白、Toast の余白 |
| `L` | 16px | 部品の間。large のボタンの左右の余白、Popover の余白（medium） |
| `XL` | 20px | 部品の間（大きめ） |
| `XXL` | 24px | Dialog の余白、領域の間 |
| `XXXL` | 32px | 領域の間（最大） |

### 軸の使い分け

- 左右の `padding` と `margin`、`column-gap`、横に並べたときの `gap` には `spacingHorizontal*` を使う。
- 上下の `padding` と `margin`、`row-gap` には `spacingVertical*` を使う。
- 軸は CSS のプロパティの向きで選ぶ。v9 の Tab には、縦に並んだタブでも、アイコンと文字の間（横の gap）には横のトークンを使うという趣旨のコメントがある（`packages/react-components/react-tabs/library/src/components/Tab/useTabStyles.styles.ts:69`、同 `:78`、同 `:87`）。
- コードには軸の取り違えもある。MenuItem は左右の余白に `spacingVerticalSNudge` を使う（`packages/react-components/react-menu/library/src/components/MenuItem/useMenuItemStyles.styles.ts:29-30`）。値が同じなので見た目は変わらない。部品の CSS ではコードの名前を写してよいが、新しく書く CSS では軸の規則を守る。

### 段階の使い分け

- 部品の中は小さい段階（2〜12px）、部品の間とレイアウトは大きい段階（16〜32px）を使う。v9 の部品のスタイルでは、横の `SNudge`、`S`、`M`、`XXS`、`XS` がそれぞれ 50 回以上使われ、`L` 以上は少ない。
- Nudge（6px、10px）は、アイコンの余白の補正に使う。サイトが 2、6、10 を補正の値とする説明に対応する。
- 36px 以上は v9 のトークンにない。ページの領域の間だけに、layout.css の `--f2-size360` などを使う。

### トークンにない直書きの値

v9 自身が、トークンで表せない値を px で直接書いている所がある。その px をそのまま写し、トークンに丸めない。CSS では `/* v9 の直書き */` と注記する。

| 部品 | 値 | 出典 |
|---|---|---|
| Button の上下の余白 | 1px、3px、5px、7px、8px（アイコンの有無と大きさで変わる） | `packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:17-21` |
| Tooltip の余白 | `4px 11px 6px 11px`（枠の 1px を引いた値）、最大幅 240px | `packages/react-components/react-tooltip/library/src/components/Tooltip/useTooltipStyles.styles.ts:21`、同 `:29` |
| Field のラベルの上下 | 9px（9px のトークンがないというコメントがある） | `packages/react-components/react-field/library/src/components/Field/useFieldStyles.styles.ts:74-77` |

### 部品の中の間隔の例

| 部品 | 間隔 | 出典 |
|---|---|---|
| Button（medium） | 余白 5px 12px、最小幅 96px | `packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:63-64` |
| Button（small） | 余白 3px 8px、最小幅 64px | `packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:291-293` |
| Button（large） | 余白 8px 16px、最小幅 96px | `packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:307-309` |
| Input | 左右の余白 small 6px、medium 10px、large 12px。中の gap 2px | `packages/react-components/react-input/library/src/components/Input/useInputStyles.styles.ts:24-46` |
| MenuPopover | 余白 4px、最大幅 300px | `packages/react-components/react-menu/library/src/components/MenuPopover/useMenuPopoverStyles.styles.ts:19-23` |
| MenuList | 項目の間の gap 2px | `packages/react-components/react-menu/library/src/components/MenuList/useMenuListStyles.styles.ts:15` |
| MenuItem | 余白 6px、gap 4px | `packages/react-components/react-menu/library/src/components/MenuItem/useMenuItemStyles.styles.ts:29-32` |
| PopoverSurface | 余白 small 12px、medium 16px、large 20px | `packages/react-components/react-popover/library/src/components/PopoverSurface/usePopoverSurfaceStyles.styles.ts:53-57` |
| Card | 余白 small 8px、medium 12px、large 16px | `packages/react-components/react-card/library/src/components/Card/useCardStyles.styles.ts:158-169` |
| Dialog | 余白 24px、gap 8px | `packages/react-components/react-dialog/library/src/contexts/constants.ts:3-4` |
| Toast | 余白 12px | `packages/react-components/react-toast/library/src/components/Toast/useToastStyles.styles.ts:15` |
| Tab（medium、横） | 余白 12px 10px、アイコンとの gap 6px | `packages/react-components/react-tabs/library/src/components/Tab/useTabStyles.styles.ts:73-76` |

### 実装の例

`f2-stack` の `data-gap` で、同じ並びの間隔を変えた例である。上から 4px（`xs`）、12px（`m`）、24px（`xxl`）。

```html demo
<div class="f2-stack" data-gap="l">
  <div class="f2-stack" data-direction="horizontal" data-gap="xs">
    <div class="f2-surface" data-stroke="thin">xs</div>
    <div class="f2-surface" data-stroke="thin">4px</div>
    <div class="f2-surface" data-stroke="thin">spacingHorizontalXS</div>
  </div>
  <div class="f2-stack" data-direction="horizontal" data-gap="m">
    <div class="f2-surface" data-stroke="thin">m</div>
    <div class="f2-surface" data-stroke="thin">12px</div>
    <div class="f2-surface" data-stroke="thin">spacingHorizontalM</div>
  </div>
  <div class="f2-stack" data-direction="horizontal" data-gap="xxl">
    <div class="f2-surface" data-stroke="thin">xxl</div>
    <div class="f2-surface" data-stroke="thin">24px</div>
    <div class="f2-surface" data-stroke="thin">spacingHorizontalXXL</div>
  </div>
</div>
```

## 角丸

### トークン

<!-- spec:tokens-radius -->

`borderRadius2XLarge` から `borderRadius6XLarge` は型とトークンにあるが、v9 の部品のスタイルでは一度も使われていない。v9 の部品での使用回数は、`Medium` 122、`Circular` 45、`None` 25、`Small` 10、`XLarge` 7、`Large` 3 である。

### 形の種類（サイトの指針）

サイト（fluent2.microsoft.design/shapes）は、形を 4 つに分ける。

| 形 | 使う所 | 角丸 |
|---|---|---|
| 長方形（Rectangle） | ボタン、テキストエリア、メニュー、カード、画像 | 標準は 4px。32px 未満の小さい形は 2px。大きい部品は大きめ |
| 円（Circle） | アバターなど、人を表す部品 | `borderRadiusCircular` |
| ピル（Pill） | スライダーのトラック、トグルのチャネル、タグ、一覧の中の選択の印 | `borderRadiusCircular` |
| くちばし（Beak） | 1 つの対象に結びつくコールアウトやポップオーバーの矢印 | — |

形は、塗りか枠で周りと区別する。

角丸を付けない所: 複数の要素を 1 つの入れ物に収めて、角丸が不要な隙間を作るとき（スプリットボタンの両側の内側の角など）と、画面の端まで届く部品（ナビゲーションバー、タブバー）。

### 部品ごとの角丸（コード）

| 角丸 | 部品 | 出典（抜粋） |
|---|---|---|
| `borderRadiusNone`（0） | Button と Badge の square、Image の既定、ProgressBar の square、Input などの underline 表示 | `packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:288`、`packages/react-components/react-image/library/src/components/Image/useImageStyles.styles.ts:16`、`packages/react-components/react-input/library/src/components/Input/useInputStyles.styles.ts:147` |
| `borderRadiusSmall`（2px） | Checkbox の四角、small の Card、24px 以下の Avatar の square、Option のチェックの印 | `packages/react-components/react-checkbox/library/src/components/Checkbox/useCheckboxStyles.styles.ts:138`、`packages/react-components/react-card/library/src/components/Card/useCardStyles.styles.ts:161`、`packages/react-components/react-combobox/library/src/components/Option/useOptionStyles.styles.ts:94` |
| `borderRadiusMedium`（4px） | Button（全サイズ）、Input、Textarea、Select、Combobox、Dropdown、MenuPopover、MenuItem、PopoverSurface、Tooltip、Toast、MessageBar、Tag の rounded、Tab、Nav の項目、medium の Card、ProgressBar | `packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:65`、`packages/react-components/react-input/library/src/components/Input/useInputStyles.styles.ts:47`、`packages/react-components/react-popover/library/src/components/PopoverSurface/usePopoverSurfaceStyles.styles.ts:27`、`packages/react-components/react-tooltip/library/src/components/Tooltip/useTooltipStyles.styles.ts:27`、`packages/react-components/react-toast/library/src/components/Toast/useToastStyles.styles.ts:16` |
| `borderRadiusLarge`（6px） | large の Card、49〜72px の Avatar の square、large の Button のフォーカスの枠 | `packages/react-components/react-card/library/src/components/Card/useCardStyles.styles.ts:169`、`packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:499` |
| `borderRadiusXLarge`（8px） | DialogSurface、Slider のトラック、CarouselCard、73px 以上の Avatar の square | `packages/react-components/react-dialog/library/src/components/DialogSurface/useDialogSurfaceStyles.styles.ts:32`、`packages/react-components/react-slider/library/src/components/Slider/useSliderStyles.styles.ts:122`、`packages/react-components/react-carousel/library/src/components/CarouselCard/useCarouselCardStyles.styles.ts:28` |
| `borderRadiusCircular`（10000px） | Avatar の既定、PresenceBadge、Badge の既定、Button と Tag の circular、Radio、Switch、Slider のつまみ、Tab と Nav の選択の印 | `packages/react-components/react-avatar/library/src/components/Avatar/useAvatarStyles.styles.ts:29`、`packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:284`、`packages/react-components/react-radio/library/src/components/Radio/useRadioStyles.styles.ts:170`、`packages/react-components/react-switch/library/src/components/Switch/useSwitchStyles.styles.ts:48` |

補足:

- Button の `shape` は rounded（既定）、circular、square の 3 つである（`packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:283-288`）。v9 では rounded は 3 サイズとも 4px である。
- Button のフォーカスの枠の角丸は small で 2px、large で 6px で、本体の 4px と違う（`packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:495-499`）。
- Avatar の square は大きさで角丸を変える。24px 以下は 2px、48px 以下は 4px、72px 以下は 6px、それより大きいと 8px（`packages/react-components/react-avatar/library/src/components/Avatar/useAvatarStyles.styles.ts:513-522`）。
- Input などの下線のフォーカスの印は、下の 2 つの角を `borderRadiusMedium` にし、高さを `max(2px, borderRadiusMedium)` にする（`packages/react-components/react-input/library/src/components/Input/useInputStyles.styles.ts:74-77`）。

### Circular と 50%

- `borderRadiusCircular` は 50% ではなく 10000px である（`packages/tokens/src/global/borderRadius.ts:14`）。
- 長方形にかけるとピル（両端が半円）になり、正方形にかけると円になる。50% を長方形にかけると楕円になるので、ピルのボタンやタグには使えない。
- 円（アバター）にもピル（タグ、circular のボタン、スイッチ）にも `var(--borderRadiusCircular)` を使う。

### 実装の例

`f2-surface` の `data-radius` で角丸の段階を並べた。最後の 2 つは、同じ `borderRadiusCircular` が正方形では円、長方形ではピルになる例である。

```html demo
<div class="f2-stack" data-direction="horizontal" data-gap="l">
  <div class="f2-surface" data-stroke="thin" data-radius="none">None 0</div>
  <div class="f2-surface" data-stroke="thin" data-radius="small">Small 2px</div>
  <div class="f2-surface" data-stroke="thin" data-radius="medium">Medium 4px</div>
  <div class="f2-surface" data-stroke="thin" data-radius="large">Large 6px</div>
  <div class="f2-surface" data-stroke="thin" data-radius="xlarge">XLarge 8px</div>
  <div class="f2-surface" data-stroke="thin" data-radius="2xlarge">2XLarge 12px</div>
  <div class="f2-surface" data-stroke="thin" data-radius="circular" style="width: 64px; height: 64px; display: grid; place-items: center; box-sizing: border-box;">円</div>
  <div class="f2-surface" data-stroke="thin" data-radius="circular">ピル（Circular）</div>
</div>
```

## 線

### トークン

<!-- spec:tokens-stroke -->

Web の値はサイトとコードで一致する。サイトの Mobile の値（Thicker 4px、Thickest 6px）は Web では使わない。

### 用途

v9 の部品での使用回数は、`Thin` 116、`Thick` 73、`Thicker` 41、`Thickest` 15 である。

| トークン | 主な用途 | 出典（抜粋） |
|---|---|---|
| `strokeWidthThin`（1px） | 部品の枠（Button、MessageBar、Drawer の境界）、Button のフォーカスの内側の線 | `packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:42`、`packages/react-components/react-message-bar/library/src/components/MessageBar/useMessageBarStyles.styles.ts:21` |
| `strokeWidthThick`（2px） | フォーカスの outline（Button、Nav）、48px 以下の Avatar のリング、small 以下の Spinner、Textarea などの下線のフォーカスの印 | `packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:109`、`packages/react-components/react-textarea/library/src/components/Textarea/useTextareaStyles.styles.ts:52` |
| `strokeWidthThicker`（3px） | Tab の選択の印（small の横向きの下線だけ 2px）、ToggleButton の outline の選択、49〜64px の Avatar のリング、medium〜extra-large の Spinner | `packages/react-components/react-tabs/library/src/components/Tab/useTabStyles.styles.ts:384-390`、同 `:397-429` |
| `strokeWidthThickest`（4px） | 65px 以上の Avatar のリング、huge の Spinner、AvatarGroup の区切り | `packages/react-components/react-avatar/library/src/components/Avatar/useAvatarStyles.styles.ts:148-149` |

サイトの指針:

- 要素の大きさに合わせて太さを選ぶ。例として、アバターの活動のリングは、小さいアバターで 2px、大きいアバターで 4px にする。
- 破線は、ダッシュと隙間の 2 つの値で指定し、線の太さに比例して拡大縮小する。具体的な式はページの画像にあり、本文にない。
- 線の端は角丸のトークンで丸め、角ばった端を避ける。

### 透明の枠

Popover、Menu、Tooltip、Toast、Dialog は、`1px solid` の `colorTransparentStroke`（light と dark では `transparent`）の枠を持つ（`packages/react-components/react-popover/library/src/components/PopoverSurface/usePopoverSurfaceStyles.styles.ts:28`、`packages/react-components/react-menu/library/src/components/MenuPopover/useMenuPopoverStyles.styles.ts:24`、`packages/react-components/react-tooltip/library/src/components/Tooltip/useTooltipStyles.styles.ts:28`、`packages/react-components/react-toast/library/src/components/Toast/useToastStyles.styles.ts:17`、`packages/react-components/react-dialog/library/src/contexts/constants.ts:5`）。

ふだんは見えないが、強制カラー（Windows のハイコントラスト）では枠の色がシステムの色に置き換わり、面の縁として現れる。影は強制カラーで描かれないので、この枠が唯一の縁になる。React を使わない HTML でも、浮く面にはこの枠を残す。`f2-surface` も既定でこの枠を持つ。

### 実装の例

```html demo
<div class="f2-stack" data-direction="horizontal" data-gap="l">
  <div class="f2-surface" data-stroke="thin">Thin 1px</div>
  <div class="f2-surface" data-stroke="thick">Thick 2px</div>
  <div class="f2-surface" data-stroke="thicker">Thicker 3px</div>
  <div class="f2-surface" data-stroke="thickest">Thickest 4px</div>
</div>
```

## v9 との差と未確認の点

- **サイトの角丸の表とコードの食い違い**: サイトの表とコードの値が一致しない。この設計書はコードに従う（下の表）。サイトがより新しい指針か、別のプラットフォームの指針を反映している可能性があるが、確かめていない。
- **サイトの `size*` の段階**: サイトの Global spacing ramp の `size20` から `size560` という名前のトークンは、v9 のソースにない。v9 の Web で使えるのは `spacingHorizontal*` と `spacingVertical*`（0〜32px）だけである。36px 以上は layout.css の独自の変数にした。Figma の変数か、ほかのプラットフォームにだけある可能性があるが、確かめていない。
- **ブレークポイントの境界**: サイトの small は 479px まで、medium は 480px からである。v9 の Dialog は `max-width: 480px` で切り替えるので、480px ちょうどの幅で 1px ずれる。部品ではコードの値を写す。
- **ガター、余白、最大幅、タッチの対応**: Fluent に数値がない。この章の値は独自の決定である。
- **`borderRadius2XLarge` から `6XLarge`**: v9 の部品で使われていない。どの部品のための値かを示す資料は見つからなかった。
- **密度**: サイトに密度の指針はなく、v9 は部品の `size` で表すだけである。ページ全体の密度を切り替える仕組みは定めない。

角丸のサイトの表とコードの対応:

| 項目 | サイト | コード |
|---|---|---|
| Large | 8px | `borderRadiusLarge` は 6px（`packages/tokens/src/global/borderRadius.ts:7`） |
| X-Large | 12px | `borderRadiusXLarge` は 8px（`packages/tokens/src/global/borderRadius.ts:8`）。12px は `borderRadius2XLarge`（`packages/tokens/src/global/borderRadius.ts:9`） |
| Circle | 50% | `borderRadiusCircular` は 10000px（`packages/tokens/src/global/borderRadius.ts:14`） |
| 大きいボタン | 8px | large の Button は `borderRadiusMedium` の 4px（`packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:310`） |
| ポップオーバー | 12px | PopoverSurface は `borderRadiusMedium` の 4px（`packages/react-components/react-popover/library/src/components/PopoverSurface/usePopoverSurfaceStyles.styles.ts:27`） |
