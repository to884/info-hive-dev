# エレベーション、マテリアル、モーション

この章は、面の高さ（影）、面の材質、動き（時間、曲線、プリセット、部品ごとの動き、縮小モーション）を定める。

結論を先に書く。

- 影は `shadow2`、`shadow4`、`shadow8`、`shadow16`、`shadow28`、`shadow64` の 6 段階だけを使う。どれも「環境光の影（ambient）」と「主光源の影（key）」の 2 層の `box-shadow` である。独自の影を作らない。
- ダークでは影の形を変えず、色の不透明度だけが約 2 倍になる。テーマごとの値は `fluent2-tokens.css` が持つ。
- Web の v9 の面は不透明（Solid）だけである。Acrylic と Mica は v9 にない。モーダルの背景幕は `colorBackgroundOverlay` を使う。
- 時間は `duration*` の 8 つ、曲線は `curve*` の 9 つのトークンだけを使う。入場は Decelerate、退場は Accelerate、行って戻る状態の変化は EasyEase、不透明度だけの変化とループは Linear にする。
- 縮小モーションは、v9 と同じく時間だけを縮める。部品の CSS は v9 が書いている所だけに `@media screen and (prefers-reduced-motion: reduce)` を書く。

## エレベーション

### 影の式

`createShadowTokens(ambientColor, keyColor, tokenSuffix)` が 6 段階の影を作る（`packages/tokens/src/utils/shadows.ts:6-14`）。値は抽出である。

| トークン | ambient の層 | key の層 | 出典 |
|---|---|---|---|
| `shadow2` | `0 0 2px <ambient>` | `0 1px 2px <key>` | `packages/tokens/src/utils/shadows.ts:8` |
| `shadow4` | `0 0 2px <ambient>` | `0 2px 4px <key>` | `packages/tokens/src/utils/shadows.ts:9` |
| `shadow8` | `0 0 2px <ambient>` | `0 4px 8px <key>` | `packages/tokens/src/utils/shadows.ts:10` |
| `shadow16` | `0 0 2px <ambient>` | `0 8px 16px <key>` | `packages/tokens/src/utils/shadows.ts:11` |
| `shadow28` | `0 0 8px <ambient>` | `0 14px 28px <key>` | `packages/tokens/src/utils/shadows.ts:12` |
| `shadow64` | `0 0 8px <ambient>` | `0 32px 64px <key>` | `packages/tokens/src/utils/shadows.ts:13` |

- key の層は「Y のずれ = n / 2、ぼかし = n」である（n は段階の数）。ambient の層はずれがなく、ぼかしは 2〜16 で 2px、28 と 64 で 8px である。
- 末尾に `Brand` の付く版（`shadow2Brand` から `shadow64Brand`）は、同じ式で色だけが違う。
- CSS 変数名は `--shadow2` から `--shadow64`、`--shadow2Brand` から `--shadow64Brand` である（`packages/tokens/src/tokens.ts:499-512`）。

<!-- spec:tokens-shadow -->

### 影の色（テーマ別）

| トークン | light | dark | ハイコントラスト |
|---|---|---|---|
| `colorNeutralShadowAmbient` | `rgba(0,0,0,0.12)` | `rgba(0,0,0,0.24)` | `rgba(0,0,0,0.24)` |
| `colorNeutralShadowKey` | `rgba(0,0,0,0.14)` | `rgba(0,0,0,0.28)` | `rgba(0,0,0,0.28)` |
| `colorBrandShadowAmbient` | `rgba(0,0,0,0.30)` | `rgba(0,0,0,0.30)` | `rgba(0,0,0,0.30)` |
| `colorBrandShadowKey` | `rgba(0,0,0,0.25)` | `rgba(0,0,0,0.25)` | `rgba(0,0,0,0.25)` |

出典は `packages/tokens/src/alias/lightColor.ts:184-191`、`packages/tokens/src/alias/darkColor.ts:184-191`、`packages/tokens/src/alias/highContrastColor.ts:194-201`。

- ダークでは影の形はそのままで、Neutral の不透明度が約 2 倍になる。
- Brand の影の色は、どのテーマでも同じ黒である。
- `colorNeutralShadowAmbientLighter` などの `Lighter` と `Darker` の色は、影のトークンの生成に使われず、v9 の部品でも使われていない。
- `fluent2-tokens.css` は、影のトークンを色の変数を介さずに展開した値で書いている。そのため、テーマを切り替える要素ごとに影の値も宣言し直される。部分木で `--colorNeutralShadowKey` だけを上書きしても、`--shadow*` は変わらない。影の色を変えるときは `--shadow*` を書き直す。

### 段階ごとの用途

Web の v9 の部品での使い方を正とする。

| 段階 | 部品と状態 | 出典 |
|---|---|---|
| `shadow2` | disabled の Card、primary の Button のフォーカスの印 | `packages/react-components/react-card/library/src/components/Card/useCardStyles.styles.ts:77`、`packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:476-488` |
| `shadow4` | `filled` と `filled-alternative` の Card の静止時、Tab のフォーカスの印、Image の `shadow` | `packages/react-components/react-card/library/src/components/Card/useCardStyles.styles.ts:180`、`packages/react-components/react-tabs/library/src/components/Tab/useTabStyles.styles.ts:320`、`packages/react-components/react-image/library/src/components/Image/useImageStyles.styles.ts:37` |
| `shadow8` | interactive の Card のホバー（4 から 8 へ）、Toast、Tooltip（`drop-shadow` で同じ式） | `packages/react-components/react-card/library/src/components/Card/useCardStyles.styles.ts:198`、`packages/react-components/react-toast/library/src/components/Toast/useToastStyles.styles.ts:18`、`packages/react-components/react-tooltip/library/src/components/Tooltip/useTooltipStyles.styles.ts:34-36` |
| `shadow16` | Menu のポップオーバー、Combobox と Dropdown のリストボックス、Popover（`drop-shadow` で同じ式） | `packages/react-components/react-menu/library/src/components/MenuPopover/useMenuPopoverStyles.styles.ts:22`、`packages/react-components/react-combobox/library/src/components/Combobox/useComboboxStyles.styles.ts:87`、`packages/react-components/react-popover/library/src/components/PopoverSurface/usePopoverSurfaceStyles.styles.ts:32-34` |
| `shadow28` | 大きい Avatar の active（`shadow` か `ring-shadow` のとき。28px 以下は 4、48px 以下は 8、64px 以下は 16、それより大きいと 28） | `packages/react-components/react-avatar/library/src/components/Avatar/useAvatarStyles.styles.ts:156-167`、同 `:544-553` |
| `shadow64` | DialogSurface、OverlayDrawer（動きの最後に付ける） | `packages/react-components/react-dialog/library/src/components/DialogSurface/useDialogSurfaceStyles.styles.ts:46`、`packages/react-components/react-drawer/library/src/shared/drawerMotions.ts:98` |

- Card のホバーの影は `transition` を持たず、瞬時に切り替わる。
- `shadow*Brand` は、v9 の部品での使用が見つからなかった。色付きの面（ブランド色の背景）に影を付けるときに使う。

### box-shadow と drop-shadow

Tooltip と PopoverSurface は、矢印を含めて影を落とすために、`box-shadow` ではなく `filter: drop-shadow()` を 2 つ重ねる。式は `shadow8` と `shadow16` と同じである（`packages/react-components/react-tooltip/library/src/components/Tooltip/useTooltipStyles.styles.ts:34-36`、`packages/react-components/react-popover/library/src/components/PopoverSurface/usePopoverSurfaceStyles.styles.ts:32-34`）。`--shadow*` は `box-shadow` の構文なので `filter` に使えない。v9 にも、filter で使える影のトークンを足す必要があるという TODO がある。

```css
/* Tooltip（shadow8 相当） */
filter: drop-shadow(0 0 2px var(--colorNeutralShadowAmbient)) drop-shadow(0 4px 8px var(--colorNeutralShadowKey));
/* PopoverSurface（shadow16 相当） */
filter: drop-shadow(0 0 2px var(--colorNeutralShadowAmbient)) drop-shadow(0 8px 16px var(--colorNeutralShadowKey));
```

矢印を持たない Menu とリストボックスは `box-shadow: var(--shadow16)` を使う。

### ハイコントラスト

- 強制カラー（`forced-colors: active`）では `box-shadow` が描かれない。浮く面の縁は、透明の枠 `colorTransparentStroke` に頼る（「レイアウト、間隔、形状、線」の章の「透明の枠」）。
- `data-theme="high-contrast"` のテーマでも、影の色は dark と同じ値が入る。

### 実装の例

同じ影を light と dark で並べた。dark では不透明度が上がるが、暗い背景の上では影が目立ちにくい。dark で面の高さを示すには、影に加えて背景の明るさの段階（`colorNeutralBackground1` から `3`）も使う。

```html demo
<div class="f2-grid">
  <div data-theme="light" data-span-large="6" style="padding: 24px;">
    <div class="f2-stack" data-gap="xl">
      <div class="f2-surface" data-elevation="4">shadow4: カードの静止時</div>
      <div class="f2-surface" data-elevation="16">shadow16: Menu、Popover</div>
      <div class="f2-surface" data-elevation="64">shadow64: Dialog</div>
    </div>
  </div>
  <div data-theme="dark" data-span-large="6" style="padding: 24px;">
    <div class="f2-stack" data-gap="xl">
      <div class="f2-surface" data-elevation="4">shadow4: カードの静止時</div>
      <div class="f2-surface" data-elevation="16">shadow16: Menu、Popover</div>
      <div class="f2-surface" data-elevation="64">shadow64: Dialog</div>
    </div>
  </div>
</div>
```

## マテリアル

### 4 つの材質（サイトの指針）

サイト（fluent2.microsoft.design/material）は、材質を 4 つ挙げる。

| 材質 | 性質 | 使う所 |
|---|---|---|
| Solid | 不透明。最もよく使う | 色とエレベーションで領域を分ける |
| Mica | ウィンドウ用の不透明な材質。アクティブなウィンドウではデスクトップの背景から色をわずかに取り、非アクティブでは中立の色になる | Windows のウィンドウの下地 |
| Acrylic | すりガラスのような半透明 | ポップオーバーやメニューのように、一時的で外側のクリックで閉じる面 |
| Smoke | 背後の UI を暗くする透明の層 | モーダル（ダイアログなど）の下が操作できないことを示す |

- Mica と Acrylic は、操作できる部品の下に敷く下地である。Smoke は UI の上にかぶせる。
- Solid、Mica、Acrylic はライトとダークの両方に対応する。Smoke は常に半透明の黒である。
- サイトは、プラットフォームごとの対応と Web での扱いを明示していない。

### Web での扱い

- **Web の v9 の面は Solid だけである。** v9 と Web Components v3 のスタイルに `backdrop-filter` と Acrylic、Mica の実装はない（検索して 0 件。サイトが Web での使用を禁じているわけではない）。
- Menu、Popover、Tooltip、Dialog の面は、すべて不透明の `colorNeutralBackground1` を使う（`packages/react-components/react-popover/library/src/components/PopoverSurface/usePopoverSurfaceStyles.styles.ts:26`、`packages/react-components/react-tooltip/library/src/components/Tooltip/useTooltipStyles.styles.ts:30`、`packages/react-components/react-dialog/library/src/components/DialogSurface/useDialogSurfaceStyles.styles.ts:42`、`packages/react-components/react-menu/library/src/components/MenuPopover/useMenuPopoverStyles.styles.ts:15`）。
- この設計書の決定: 面は Solid と影で表す。Acrylic を使うなら、独自の拡張として明示する。

### 背景幕と半透明のトークン

Smoke に当たるのは `colorBackgroundOverlay` である。サイトはトークン名を示さないので、この対応は推論である。Dialog の背景幕と OverlayDrawer の背景幕が使う（`packages/react-components/react-dialog/library/src/components/DialogSurface/useDialogSurfaceStyles.styles.ts:65`、`packages/react-components/react-drawer/library/src/components/OverlayDrawer/OverlayDrawerSurface/useOverlayDrawerSurfaceStyles.styles.ts:13`）。入れ子のダイアログでは、背景幕を `colorTransparentBackground` にして暗さを重ねない（`packages/react-components/react-dialog/library/src/components/DialogSurface/useDialogSurfaceStyles.styles.ts:70-71`）。

| トークン | light | dark | 用途 | 出典 |
|---|---|---|---|---|
| `colorBackgroundOverlay` | `rgba(0,0,0,0.4)` | `rgba(0,0,0,0.5)` | モーダルの背景幕（Smoke） | `packages/tokens/src/alias/lightColor.ts:122`、`packages/tokens/src/alias/darkColor.ts:122` |
| `colorNeutralBackgroundAlpha` | `rgba(255,255,255,0.5)` | `rgba(26,26,26,0.5)` | 画像の上に置く Carousel のボタンとナビ | `packages/tokens/src/alias/lightColor.ts:98` |
| `colorSubtleBackgroundLightAlphaHover` | 白 0.7 | `rgba(36,36,36,0.8)` | Tree の項目のホバー | `packages/tokens/src/alias/lightColor.ts:104` |
| `colorNeutralStencil1Alpha`、`colorNeutralStencil2Alpha` | 黒 0.1、0.05 | 白 0.1、0.05 | Skeleton | `packages/tokens/src/alias/lightColor.ts:120-121` |

layout.css の `f2-scrim` は、`colorBackgroundOverlay` を背景にする独自の class である。

### 実装の例

背景幕（`f2-scrim`）の上に、`shadow64` の面を置いた。背景幕の下の内容は暗くなり、操作できないことを示す。

```html demo
<div style="position: relative; padding: 24px; min-height: 160px;">
  <div class="f2-stack" data-gap="s">
    <span>背景の内容 1</span>
    <span>背景の内容 2</span>
    <span>背景の内容 3</span>
  </div>
  <div class="f2-scrim" style="position: absolute; inset: 0; display: grid; place-items: center;">
    <div class="f2-surface" data-elevation="64" data-radius="xlarge" style="padding: 24px;">Solid の面（shadow64、角丸 8px）</div>
  </div>
</div>
```

## モーション

### 原則（サイトの指針）

サイト（fluent2.microsoft.design/motion）は、原則を 4 つ挙げる。

- 機能的: 次の一歩を示し、UI の変化を知らせ、達成を伝える。
- 自然: 慣性、重力、重さ、速度といった物理に従う。
- 一貫: 共通の型で、製品の間の動きをそろえる。
- 魅力: 楽しさで記憶に残す。

時間は、遅すぎず、唐突すぎない長さにする。大きい要素と長い距離ほど長くするが、待たせない。遷移の型として、入場と退場、エレベーション（奥行きの変化）、トップレベル（主要な行き先の間は、大きい要素を滑らせず短いフェードにする）、コンテナーの変形を挙げる。多数の項目は開始を少しずつずらし（stagger）、項目が非常に多いときは同時に動かす。重要な要素ほど目立つ動きと長い時間にする。

サイトは、ms の値と曲線の名前を載せていない。以下の値はコードから取った。

### 時間のトークン

`packages/tokens/src/global/durations.ts:3-12`。`@fluentui/react-motion` は同じ値を ms の数で持つ（`packages/react-components/react-motion/library/src/motions/motionTokens.ts:4-13`）。

<!-- spec:tokens-duration -->

### 曲線のトークン

`packages/tokens/src/global/curves.ts:3-13`。CSS 変数名は `packages/tokens/src/tokens.ts:546-564`。

<!-- spec:tokens-curve -->

| トークン | 性格 |
|---|---|
| `curveDecelerateMax`、`curveDecelerateMid`、`curveDecelerateMin` | 速く出て減速する（強、中、弱）。入場に使う |
| `curveAccelerateMax`、`curveAccelerateMid`、`curveAccelerateMin` | ゆっくり始めて加速する（強、中、弱）。退場に使う |
| `curveEasyEaseMax`、`curveEasyEase` | 加速して減速する（強、標準）。行って戻る状態の変化に使う |
| `curveLinear` | 等速。不透明度だけの変化とループに使う |

### 使い分け

サイトに明文はない。以下は、v9 の既定値と部品の使い方から読み取った規則（推論）である。

- 入場は Decelerate、退場は Accelerate。Scale と Rotate は Max と Max、Slide は Mid と Mid、Blur は Min と Min、Dialog と Drawer は DecelerateMid と AccelerateMin の組である。
- EasyEase は、行って戻る対称な変化に使う。Fade の既定、Button と Switch の色の変化、Collapse（`curveEasyEaseMax`）、Tree の山形のアイコンの回転である。
- Linear は、不透明度だけの変化（Drawer の背景幕）、無限のループ（ProgressBar）、atom の既定に使う。
- 退場は入場と同じか短くする。Scale は入場 250ms、退場 200ms である。
- 面が大きく、移動の距離が長いほど時間を長くする（Drawer の大きさごとの時間）。

| 時間 | 主な用途 |
|---|---|
| 50ms（`durationUltraFast`） | 入力欄の下線がフォーカスを失うとき |
| 100ms（`durationFaster`） | Button の色、Stagger の項目の間の遅れ |
| 150ms（`durationFast`） | FadeSnappy、Nav の展開のアイコン |
| 200ms（`durationNormal`） | Fade、Slide、Collapse の既定、Switch、下線がフォーカスを得るとき |
| 250ms（`durationGentle`） | Scale、Dialog、small の Drawer、FadeRelaxed |
| 300ms（`durationSlow`） | Tab の選択の印、Blur、medium の Drawer |
| 400ms（`durationSlower`） | Popover と Menu の入場、large の Drawer |
| 500ms（`durationUltraSlow`） | full の Drawer、Avatar の active のリング |

### プリセット

`@fluentui/react-motion-components-preview` 0.15.10 のプリセットである（`packages/react-components/react-motion-components-preview/library/src/components/`）。複合のプリセットで重ねる fade は、主の動きと同じ時間、曲線、遅延を使う。退場は入場のキーフレームを逆順にしたものである。

| プリセット | キーフレーム（入場。退場は逆順） | 入場（時間、曲線） | 退場（時間、曲線） | 派生 | 出典 |
|---|---|---|---|---|---|
| `Fade` | `opacity: 0 → 1` | 200ms、`curveEasyEase` | 入場と同じ | `FadeSnappy`（150ms）、`FadeRelaxed`（250ms） | `packages/react-components/react-motion-components-preview/library/src/components/Fade/Fade.ts:18-46` |
| `Scale` | `scale: 0.9 → 1` と fade | 250ms、`curveDecelerateMax` | 200ms、`curveAccelerateMax` | `ScaleSnappy`（200ms と 150ms）、`ScaleRelaxed`（300ms と 250ms） | `packages/react-components/react-motion-components-preview/library/src/components/Scale/Scale.ts:20-66` |
| `Slide` | `translate: <outX> <outY> → 0 0`（既定は 0px 0px）と fade | 200ms、`curveDecelerateMid` | 200ms、`curveAccelerateMid` | `SlideSnappy`（曲線を `curveDecelerateMax` と `curveAccelerateMax` に）、`SlideRelaxed`（250ms） | `packages/react-components/react-motion-components-preview/library/src/components/Slide/Slide.ts:22-71` |
| `Blur` | `filter: blur(10px) → blur(0px)` と fade | 300ms、`curveDecelerateMin` | 300ms、`curveAccelerateMin` | — | `packages/react-components/react-motion-components-preview/library/src/components/Blur/Blur.ts:20-56` |
| `Rotate` | `rotate: z -90deg → z 0deg` と fade | 250ms、`curveDecelerateMax` | 250ms、`curveAccelerateMax` | — | `packages/react-components/react-motion-components-preview/library/src/components/Rotate/Rotate.ts:21-69` |
| `Collapse` | 縦の大きさ（`max-height: 0 → scrollHeight → unset`）、上下の余白、fade を同時に | 200ms、`curveEasyEaseMax` | 入場と同じ | `CollapseSnappy`（150ms）、`CollapseRelaxed`（400ms）、`CollapseDelayed`（下記） | `packages/react-components/react-motion-components-preview/library/src/components/Collapse/Collapse.ts:27-109` |
| `CollapseDelayed` | 開くときは大きさ 200ms のあと不透明度 400ms（200ms 遅れ）。閉じるときは不透明度 400ms のあと大きさ 200ms（400ms 遅れ） | 合計 600ms、`curveEasyEase` | 合計 600ms、`curveEasyEase` | — | `packages/react-components/react-motion-components-preview/library/src/components/Collapse/Collapse.ts:112-126` |
| `Stagger` | 子の動きの開始を順にずらす | 項目の間 100ms、項目 200ms | — | — | `packages/react-components/react-motion-components-preview/library/src/choreography/Stagger/utils/constants.ts:8`、同 `:11` |

- 変形には `transform` ではなく、独立したプロパティ `scale`、`translate`、`rotate` を使う。位置決めが付ける `transform` と干渉しない。
- `rotateAtom` の JSDoc は既定の軸を `'y'` と書くが、コードの既定は `'z'` である（`packages/react-components/react-motion-components-preview/library/src/atoms/rotate-atom.ts:25`、同 `:36`）。コードに従う。
- Collapse は JS で `scrollHeight` を測る。CSS だけでは近似になる（`display: grid` と `grid-template-rows: 0fr ↔ 1fr` の transition か、`interpolate-size: allow-keywords` と `height: 0 ↔ auto`）。

キーフレームで書くときの形を示す。名前は `fui-<プリセット>-<動き>` とし、入場と退場で名前を分ける。CSS の animation は `animation-name` で同一視されるので、同じ名前のまま `animation-direction: reverse` に替えても、退場が最初から再生されないことがある。

```css
@keyframes fui-Fade-in    { from { opacity: 0; } to { opacity: 1; } }
@keyframes fui-Fade-out   { from { opacity: 1; } to { opacity: 0; } }
@keyframes fui-Scale-in   { from { scale: 0.9; } to { scale: 1; } }
@keyframes fui-Scale-out  { from { scale: 1; } to { scale: 0.9; } }
@keyframes fui-Slide-in   { from { translate: var(--fui-Slide-out-x, 0px) var(--fui-Slide-out-y, 0px); } to { translate: 0 0; } }
@keyframes fui-Slide-out  { from { translate: 0 0; } to { translate: var(--fui-Slide-out-x, 0px) var(--fui-Slide-out-y, 0px); } }
@keyframes fui-Blur-in    { from { filter: blur(10px); } to { filter: blur(0px); } }
@keyframes fui-Blur-out   { from { filter: blur(0px); } to { filter: blur(10px); } }
@keyframes fui-Rotate-in  { from { rotate: z -90deg; } to { rotate: z 0deg; } }
@keyframes fui-Rotate-out { from { rotate: z 0deg; } to { rotate: z -90deg; } }

/* Scale の入場と退場。fade を同じ時間と曲線で重ねる */
.example[data-state="entering"] {
  animation: fui-Scale-in var(--durationGentle) var(--curveDecelerateMax) both,
             fui-Fade-in var(--durationGentle) var(--curveDecelerateMax) both;
}
.example[data-state="exiting"] {
  animation: fui-Scale-out var(--durationNormal) var(--curveAccelerateMax) both,
             fui-Fade-out var(--durationNormal) var(--curveAccelerateMax) both;
}
```

キーフレームで退場させるときは、`animationend` のあとで要素を隠す（JS が要る）。JS を使わないなら、次の節の transition の方法を使う。

### React を使わない CSS での入場と退場

`popover` 属性の要素と `<dialog>` は、CSS だけで入場と退場を再生できる。Web Components v3 の dialog も同じ方法を使う（`packages/web-components/src/dialog/dialog.styles.ts:55-95`）。

1. 開いた状態の値を書き、`@starting-style` に入場の開始の値を書く。
2. 閉じた状態に退場の行き先の値を書く。
3. `transition-property` に `display` と `overlay` を入れ、`transition-behavior: allow-discrete` にする。退場が終わるまで要素が表示に残る。
4. CSS の transition は、変化した後の状態の `transition-*` を使う。退場の時間と曲線は閉じた状態に、入場のものは開いた状態に書く。

layout.css の `f2-motion`（独自）は、この方法でプリセットを `popover` と `<dialog>` に当てる class である。`data-motion` で `fade`、`fade-snappy`、`fade-relaxed`、`scale`、`scale-snappy`、`scale-relaxed`、`slide`、`slide-snappy`、`slide-relaxed`、`blur`、`rotate` を選ぶ。Slide の開始の位置は `--f2-motion-out-translate`、Scale の開始の倍率は `--f2-motion-out-scale` で変えられる。

### 実装の例

ボタンを押すとポップオーバーが開き、外側を押すか Esc で閉じる。入場と退場で時間と曲線が違うことを確かめられる。Slide は Popover と同じ 10px を開始の位置にした。

```html demo
<div class="f2-stack" data-direction="horizontal" data-gap="s">
  <button class="fui-Button" type="button" popovertarget="em-motion-fade">Fade</button>
  <button class="fui-Button" type="button" popovertarget="em-motion-scale">Scale</button>
  <button class="fui-Button" type="button" popovertarget="em-motion-slide">Slide</button>
  <button class="fui-Button" type="button" popovertarget="em-motion-blur">Blur</button>
  <button class="fui-Button" type="button" popovertarget="em-motion-rotate">Rotate</button>
</div>
<div id="em-motion-fade" popover class="f2-motion f2-surface" data-motion="fade" data-elevation="16">Fade: 200ms、curveEasyEase</div>
<div id="em-motion-scale" popover class="f2-motion f2-surface" data-motion="scale" data-elevation="16">Scale: 入場 250ms curveDecelerateMax、退場 200ms curveAccelerateMax</div>
<div id="em-motion-slide" popover class="f2-motion f2-surface" data-motion="slide" data-elevation="16" style="--f2-motion-out-translate: 0px 10px;">Slide: 200ms、curveDecelerateMid と curveAccelerateMid</div>
<div id="em-motion-blur" popover class="f2-motion f2-surface" data-motion="blur" data-elevation="16">Blur: 300ms、curveDecelerateMin と curveAccelerateMin</div>
<div id="em-motion-rotate" popover class="f2-motion f2-surface" data-motion="rotate" data-elevation="16">Rotate: 250ms、curveDecelerateMax と curveAccelerateMax</div>
```

曲線の違いを、同じ 500ms で並べた。ポインターを載せるか、中のボタンにフォーカスすると点が右へ動く。

```html demo
<style>
  .em-curves__row { display: grid; grid-template-columns: 11em minmax(0, 1fr); align-items: center; gap: 12px; }
  .em-curves__track { container-type: inline-size; height: 16px; border-radius: var(--borderRadiusCircular); background-color: var(--colorNeutralBackground3); }
  .em-curves__dot { width: 16px; height: 16px; border-radius: var(--borderRadiusCircular); background-color: var(--colorBrandBackground); transition: translate var(--durationUltraSlow) var(--em-curve); }
  .em-curves:is(:hover, :focus-within) .em-curves__dot { translate: calc(100cqi - 16px) 0; }
  @media screen and (prefers-reduced-motion: reduce) { .em-curves__dot { transition-duration: 0.01ms; } }
</style>
<div class="em-curves f2-stack" data-gap="s">
  <button class="fui-Button" type="button">ここにフォーカスして再生</button>
  <div class="em-curves__row" style="--em-curve: var(--curveDecelerateMax);"><code>curveDecelerateMax</code><div class="em-curves__track"><div class="em-curves__dot"></div></div></div>
  <div class="em-curves__row" style="--em-curve: var(--curveDecelerateMid);"><code>curveDecelerateMid</code><div class="em-curves__track"><div class="em-curves__dot"></div></div></div>
  <div class="em-curves__row" style="--em-curve: var(--curveAccelerateMid);"><code>curveAccelerateMid</code><div class="em-curves__track"><div class="em-curves__dot"></div></div></div>
  <div class="em-curves__row" style="--em-curve: var(--curveEasyEase);"><code>curveEasyEase</code><div class="em-curves__track"><div class="em-curves__dot"></div></div></div>
  <div class="em-curves__row" style="--em-curve: var(--curveEasyEaseMax);"><code>curveEasyEaseMax</code><div class="em-curves__track"><div class="em-curves__dot"></div></div></div>
  <div class="em-curves__row" style="--em-curve: var(--curveLinear);"><code>curveLinear</code><div class="em-curves__track"><div class="em-curves__dot"></div></div></div>
</div>
```

### 部品ごとの動き

入場と退場（presence）:

| 部品 | 動き | 入場 | 退場 | 出典 |
|---|---|---|---|---|
| Dialog の面 | Scale の派生（`outScale: 0.85`）。scale と fade | 250ms、`curveDecelerateMid` | 250ms、`curveAccelerateMin` | `packages/react-components/react-dialog/library/src/components/DialogSurfaceMotion.ts:4-10` |
| Dialog の背景幕 | `FadeRelaxed` | 250ms、`curveEasyEase` | 250ms、`curveEasyEase` | `packages/react-components/react-dialog/library/src/components/DialogBackdropMotion.ts:3` |
| OverlayDrawer の面 | `transform: translate3d(±大きさ) → 0`、`box-shadow: 0px transparent → shadow64`、`opacity: 0 → 1` | small 250ms、medium 300ms、large 400ms、full 500ms、`curveDecelerateMid` | 同じ時間、`curveAccelerateMin` | `packages/react-components/react-drawer/library/src/shared/drawerMotions.ts:14-19`、同 `:85-116` |
| OverlayDrawer の背景幕 | fade | 大きさごとの時間、`curveLinear` | 同じ | `packages/react-components/react-drawer/library/src/shared/drawerMotions.ts:121-129` |
| InlineDrawer | transform と opacity（影なし） | 大きさごとの時間、`curveDecelerateMid` | 同じ時間、`curveAccelerateMin` | `packages/react-components/react-drawer/library/src/shared/drawerMotions.ts:51-80` |
| Popover の面 | fade と slide（向きは配置で決まる。距離 10px） | 400ms、`curveDecelerateMid` | **なし**（即座に隠す） | `packages/react-components/react-popover/library/src/components/Popover/PopoverSurfaceMotion.ts:9-42` |
| Menu の面 | Popover と同じ | 400ms、`curveDecelerateMid` | なし | `packages/react-components/react-menu/library/src/components/Menu/MenuSurfaceMotion.ts:9-42` |
| Toast | `CollapseDelayed` | 大きさ 200ms、不透明度 400ms（200ms 遅れ）、`curveEasyEase` | 不透明度 400ms、大きさ 200ms（400ms 遅れ）、`curveEasyEase` | `packages/react-components/react-toast/library/src/components/ToastContainer/renderToastContainer.tsx:24` |
| MessageBar（MessageBarGroup の中） | `animate="both"` のときだけ、fade と slide（`outY: -100%`） | 250ms、`curveLinear` | fade 250ms、`curveLinear` | `packages/react-components/react-message-bar/library/src/components/MessageBarGroup/MessageBarGroup.motions.tsx:11-26` |
| AccordionPanel、Tree の子、NavSubItemGroup | `Collapse` の既定 | 200ms、`curveEasyEaseMax` | 200ms、`curveEasyEaseMax` | `packages/react-components/react-accordion/library/src/components/AccordionPanel/useAccordionPanel.ts:36`、同 `:43` |
| NavCategoryItem の展開のアイコン | Rotate の派生（0° → 180°、fade なし） | 150ms、`curveEasyEase` | 150ms、`curveAccelerateMax`（派生が退場の曲線を指定しないので Rotate の既定が残る） | `packages/react-components/react-nav/library/src/components/NavCategoryItem/useNavCategoryItem.tsx:18-24` |
| Tooltip | **動きはない**。`display` を切り替えるだけ。表示と非表示の遅延は 250ms | — | — | `packages/react-components/react-tooltip/library/src/components/Tooltip/useTooltipStyles.styles.ts:39-41`、`packages/react-components/react-tooltip/library/src/components/Tooltip/useTooltipBase.tsx:56-57` |

- Popover と Menu の向きは、位置決めが `--fui-positioning-slide-direction-x` と `-y` に `-1px`、`0px`、`1px` を入れて決める。上に開くなら y = 1、下なら y = -1、右なら x = -1、左なら x = 1 である。これに 10 を掛けて開始の位置にする（`packages/react-components/react-positioning/library/src/usePositioningSlideDirection.ts:15-33`）。面はアンカーの側から離れる向きに 10px 動く。
- Drawer の start は、LTR で左から、RTL で右から入る。end はその逆である。

状態の変化（CSS の transition）:

| 部品 | 対象 | 時間、曲線 | 出典 |
|---|---|---|---|
| Button | background、border、color | 100ms、`curveEasyEase` | `packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:73-79` |
| Switch | 色と、つまみの transform | 200ms、`curveEasyEase` | `packages/react-components/react-switch/library/src/components/Switch/useSwitchStyles.styles.ts:58-80` |
| Tab の選択の印 | transform（translateX と scaleX） | 300ms、`curveDecelerateMax` | `packages/react-components/react-tabs/library/src/components/Tab/useTabAnimatedIndicator.styles.ts:23-34` |
| Input などの下線 | `transform: scaleX(0 ↔ 1)` | フォーカスを得るとき 200ms、失うとき 50ms。曲線は下記 | `packages/react-components/react-input/library/src/components/Input/useInputStyles.styles.ts:86-106` |
| Accordion の山形のアイコン | transform（回転） | 200ms、`ease-out`（v9 の直書き） | `packages/react-components/react-accordion/library/src/components/AccordionHeader/useAccordionHeader.tsx:47` |
| Tree の山形のアイコン | transform（0°、90°、RTL では 180°） | 200ms、`curveEasyEaseMax` | `packages/react-components/react-tree/library/src/components/TreeItemChevron.tsx:14`、同 `:19` |
| Spinner | 回転のループ | 1.5s、linear（v9 の直書き） | `packages/react-components/react-spinner/library/src/components/Spinner/useSpinnerStyles.styles.ts:58-67` |
| Skeleton | きらめきのループ | 3s、`ease-in-out`（v9 の直書き） | `packages/react-components/react-skeleton/library/src/components/SkeletonItem/useSkeletonItemStyles.styles.ts:44-47` |
| ProgressBar（不確定） | `translate: -100% → 300%` | 3000ms、無限、`curveLinear` | `packages/react-components/react-progress/library/src/components/ProgressBar/progressBarMotions.ts:8-23` |

### 入力欄の下線の transition-delay

Input、Textarea、Combobox、Dropdown、Select、SpinButton、TagPicker の下線は、曲線のトークンを `transition-timing-function` ではなく `transition-delay` に入れている（Input の例: `packages/react-components/react-input/library/src/components/Input/useInputStyles.styles.ts:90`、同 `:102`）。

- 値が `var(--curve…)` なので、宣言は計算値の時点で無効になり、`transition-delay` は初期値の 0s になる。曲線の指定もないので、描画は既定の `ease` になる。
- コメントからわかる意図は、フォーカスを得るときに 200ms と `curveDecelerateMid`、失うときに 50ms と `curveAccelerateMid` である。
- この設計書の決定（約束に従う）: CSS では実際の描画（遅延なし、`ease`）を再現し、`/* v9 は transition-delay に曲線を入れており、実際の描画は遅延なし・ease になる */` と注記する。

### 縮小モーション

v9 には仕組みが 2 つある。

1. `@fluentui/react-motion`（Web Animations API）は、`screen and (prefers-reduced-motion: reduce)` を監視する（`packages/react-components/react-motion/library/src/hooks/useIsReducedMotion.ts:7`）。有効なら、atom ごとの `reducedMotion` の定義を使い、定義がなければ時間だけを 1ms にする（`packages/react-components/react-motion/library/src/hooks/useAnimateAtoms.ts:12-16`）。遅延、繰り返し、曲線は残る。たとえば Toast の退場は、400ms 待ってから瞬時に畳む。無限のループに 1ms を当てると高速に繰り返すので、ProgressBar は明滅（`opacity: 0.2 → 1 → 0.2`）に差し替える（`packages/react-components/react-progress/library/src/components/ProgressBar/progressBarMotions.ts:18-22`）。
2. 部品の CSS（Griffel）は、`@media screen and (prefers-reduced-motion: reduce)` で `transition-duration: 0.01ms` にする（Button、Switch、入力欄の下線、Avatar など）。Tab の選択の印は `transition-property: none` にする（`packages/react-components/react-tabs/library/src/components/Tab/useTabAnimatedIndicator.styles.ts:29-33`）。Skeleton は `animation-duration: 0.01ms`、Spinner は止めずに 1.8s に遅くするだけである（`packages/react-components/react-spinner/library/src/components/Spinner/useSpinnerStyles.styles.ts:66-67`）。

Web Components v3 は、動きを `@media (prefers-reduced-motion: no-preference)` の中だけで定義する（`packages/web-components/src/dialog/dialog.styles.ts:57`）。

この設計書の決定:

- 部品の CSS は v9 に合わせ、v9 が書いている部品だけに `@media screen and (prefers-reduced-motion: reduce)` を書く。値も v9 のとおり（0.01ms、`none`、1.8s など）にする。
- 入場と退場の動き（`f2-motion` と、部品の章の presence の動き）は、`@fluentui/react-motion` に合わせて時間だけを 1ms にし、遅延は残す。
- `--duration*` のトークンを丸ごと 0 にする方法は使わない。CollapseDelayed のように遅延にも時間のトークンを使う部品があり、遅延まで消えて v9 と挙動が変わる。
- ループは個別に代わりの表現を定める（ProgressBar は明滅、Skeleton は 0.01ms、Spinner は 1.8s）。

サイトの指針: 「動きなし」の設定を用意する。時間を短くし、動きを自然にする。点滅や唐突な動きで発作を誘発しない。動きをフォーカス中の要素に絞る。動きで伝える情報は、ARIA のライブリージョンなどの別の手段でも伝える。v9 はページの設定で動きを止める `MotionBehaviourProvider`（`'skip'`）を持つ（`packages/react-components/react-motion/library/src/contexts/MotionBehaviourContext.ts:8-14`）。この設計書の CSS には、それに当たる切り替えをまだ用意していない。

## v9 との差と未確認の点

- **サイトの影の式**: サイトの elevation のページは要約を経て読んだもので、原文の表を直接は確かめていない。読み取れた式は、低い段階（2〜16）で 2 層を同じ形（ぼかし n、Y 0.5n）に書き、高い段階（28、64）で別の不透明度（24% と 20%）を挙げる。コードの ambient の層はずれがなく、不透明度は全段階で一定（light 0.12 と 0.14、dark 0.24 と 0.28）で、一致しない。この設計書はコードに従う。
- **サイトの Brand の影の式**: サイトは、ブランド色の輝度から影の不透明度を求める式を示す。コードの Brand の影の色は、輝度によらず固定（0.30 と 0.25）である。コードに従う。
- **サイトの段階の用途**: サイトの用途の例（2 は縁のないカード、8 は FAB、28 はボトムシートなど）は、Web の部品の使い方と一部しか一致しない。Web の Tooltip は 8 相当、Popover は 16 相当、Dialog は 64 で、サイトの dark 側の記述に近い。light の shadow16 の用途が shadow2 と同じ文になっていて、誤記か要約の誤りかを区別できなかった。
- **Dialog と Drawer の値**: React（退場 `curveAccelerateMin`、背景幕 EasyEase、Drawer は大きさごとの時間）と Web Components v3（退場 `curveAccelerateMid`、背景幕 linear、Drawer は 250ms に固定）が食い違う。約束に従い React の値を採る。
- **`f2-motion` の近似**: v9 の presence の動きは Web Animations API のキーフレームで、`f2-motion` は CSS の transition である。始点と終点、時間、曲線は同じだが、途中で開閉を切り替えたときの振る舞い（v9 は動きを置き換える。transition は現在の値から戻る）は違う。
- **`::backdrop` と CSS 変数**: `::backdrop` が元の要素から CSS 変数を継承するかは、ブラウザーの版による。背景幕に `var()` を使うときは代替の値を書く（Web Components v3 も `packages/web-components/src/dialog/dialog.styles.ts:27` で代替の値を書く）。
- **検索で 0 件だったもの**: `shadow*Brand` の部品での使用と、Acrylic と Mica（`backdrop-filter`）の実装は、react-components、tokens、web-components を検索して 0 件だった。v8 など、ほかの部分は調べていない。
- **モーションの文書**: react-motion と react-motion-components-preview の文書（.mdx）は読んでいない。使い分けの節は、コードの使われ方からの推論である。
- **Web Components v3 の progress-bar**: 縮小モーションのときに止めるというコメントがあるが、`no-preference` の中で止めていて、論理が逆に見える。不具合か意図かは確かめていない。
