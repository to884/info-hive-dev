# オーバーレイと通知

この章は、ページの上に重なる面（Dialog、Drawer、Popover、Menu、Tooltip）と、状態を知らせる部品（Toast、MessageBar）を定める。CSS は `assets/fluent2.css` の `overlays` の部分、CSS だけで表せない振る舞いは `assets/fluent2.js` にある（開発用のリポジトリ（非公開）の原本は `src/components/overlays.css` と `overlays.js`）。

結論を先に書く。

- 重なる面は、ネイティブの `<dialog>`（Dialog、OverlayDrawer）と `popover` 属性（Popover、Menu、Tooltip）で組む。v9 の class 名、余白、色、影、動きの値をそのまま写す。
- 開閉の動きは `transition` と `@starting-style`（`<dialog>`）、または `@keyframes`（popover の入場だけ）で書く。時間と曲線は v9 の motion の値である。
- 縮小モーションでは、v9 の motion と同じく時間だけを 1ms にし、遅延は残す（`packages/react-components/react-motion/library/src/hooks/useAnimateAtoms.ts:12-16`）。
- ハイコントラストでは、面の線の `colorTransparentStroke` が CanvasText になって輪郭が見える。`@media (forced-colors: active)` の規則を v9 が持つのは MenuItem とフォーカスの輪だけである。
- 位置決め（v9 の floating-ui）は CSS のアンカー位置決めで近似する。矢印と slide の向きは属性で決まり、画面端での反転に追従しない。
- 振る舞いの補助は、`data-fui-enhance` を付けた要素だけを `overlays.js` が扱う。JS がなくても、開いた状態の見た目は `data-static` の例で確かめられる。

### 共通の約束

- `data-static` は、この設計書のための補助の属性である。開いた状態の面を `position: relative` などでページの流れに置く。v9 にはない。
- 「v9 にない打ち消し」と注記した宣言は、`<dialog>` と `[popover]` の UA の既定（幅、margin、padding、border、overflow、inset）を消すためのものである。
- フォーカスの輪は `createFocusOutlineStyle()` の既定を React を使わない CSS で書く（`packages/react-components/react-tabster/src/focus/createFocusOutlineStyle.ts:55-112`）。v9 の `[data-fui-focus-visible]` は `:focus-visible` で近似している。
- 共通トークンの値（light / dark / HC）は、`colorBackgroundOverlay` が rgba(0,0,0,0.4) / rgba(0,0,0,0.5) / rgba(0,0,0,0.5)、`colorTransparentStroke` が transparent / transparent / CanvasText である（`packages/tokens/src/alias/lightColor.ts:122,177`、`packages/tokens/src/alias/darkColor.ts:122,177`、`packages/tokens/src/alias/highContrastColor.ts:132,187`）。

<!-- spec:tokens-shadow -->

<!-- spec:tokens-duration -->

<!-- spec:tokens-curve -->

## Dialog

### 概要と使い分け（Do / Don't）

Dialog は、先に進む前に応答を求める補助の面である。作業を中断させるので、重要な操作だけに使う。返答の要らない通知は Toast、流れを止めない補足は Popover を使う。

- 種類は 3 つある。modal は背後を暗くして遮る。non-modal は背後も操作でき、既定で閉じるボタンを持つ。alert は決定を求める modal で、未保存の変更や破壊的な操作に限る。
- Do: 閉じるまでの手順を少なくする。フォームは短くし、主目的に絞る。
- Do: タイトルは必須である。要点を具体的に書き、本文でタイトルを繰り返さない。ボタンはタイトルへの直接の応答とし、短い動詞にする。
- Don't: 重複した選択肢を置かない。Dialog を入れ子にしない。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

| 部品 | class | 要素と属性 | 出典 |
|---|---|---|---|
| DialogSurface | `fui-DialogSurface` | `<dialog>`（v9 は `div`）。`role="alertdialog"` は alert だけ。`aria-labelledby` はタイトルの id | `packages/react-components/react-dialog/library/src/components/DialogSurface/useDialogSurface.ts:122-138` |
| backdrop | `::backdrop`（静的な例では `fui-DialogSurface__backdrop`） | v9 は surface の兄弟の `div`、`aria-hidden="true"` | `packages/react-components/react-dialog/library/src/components/DialogSurface/useDialogSurface.ts:76-82` |
| DialogBody | `fui-DialogBody` | `div`。3 行 3 列の grid | `packages/react-components/react-dialog/library/src/components/DialogBody/useDialogBodyStyles.styles.ts:20-37` |
| DialogTitle | `fui-DialogTitle` | `h2` | `packages/react-components/react-dialog/library/src/components/DialogTitle/useDialogTitle.tsx:26-36` |
| DialogTitle の action | `fui-DialogTitle__action` | タイトルの直後の兄弟の `div`。non-modal で既定で描く | `packages/react-components/react-dialog/library/src/components/DialogTitle/renderDialogTitle.tsx:15-18` |
| DialogContent | `fui-DialogContent` | `div` | `packages/react-components/react-dialog/library/src/components/DialogContent/useDialogContentStyles.styles.ts:16-31` |
| DialogActions | `fui-DialogActions` | `div` | `packages/react-components/react-dialog/library/src/components/DialogActions/useDialogActionsStyles.styles.ts:15-55` |

開き方と閉じ方は次のとおりにする。

- modal と alert は `showModal()`、non-modal は `show()` で開く。JS なしで開くには、ボタンに `commandfor="<id>"` と `command="show-modal"` を書く。non-modal は `command="--show"` と `data-fui-enhance`（`overlays.js` が `show()` を呼ぶ）を使う。
- Esc で閉じる。v9 はどの modalType でも Esc で閉じ要求を出す（`packages/react-components/react-dialog/library/src/components/DialogSurface/useDialogSurface.ts:61-74`）。
- 外側（backdrop）のクリックで閉じるのは modal だけである（`packages/react-components/react-dialog/library/src/components/DialogSurface/useDialogSurface.ts:48-59`）。`<dialog closedby="any">` で書き、使えないブラウザーでは `data-fui-enhance` で `overlays.js` が代わりに閉じる。alert と non-modal には `closedby="closerequest"` を書く。
- `showModal()` は外側を inert にしてフォーカスを閉じ込める。v9 の `inertTrapFocus` を true にしたときと同じ方式である（`packages/react-components/react-dialog/library/src/components/Dialog/useDialog.ts:48-51`）。閉じるとフォーカスは開いた要素に戻る。
- modal の間は文書のスクロールを止める（`packages/react-components/react-dialog/library/src/utils/useDisableBodyScroll.styles.ts:6-13`）。CSS の `:root:has(:modal)` で近似している。

### バリエーション

| 属性 | 値 | 既定 | v9 の props と出典 |
|---|---|---|---|
| `data-modal-type` | `modal` / `non-modal` / `alert` | `modal` | `modalType`（`packages/react-components/react-dialog/library/src/components/Dialog/useDialog.ts:24`） |
| `data-backdrop-appearance` | `dimmed` / `transparent` | `dimmed`（入れ子は `transparent`） | backdrop の `appearance`（`packages/react-components/react-dialog/library/src/components/DialogSurface/DialogSurface.types.ts:11-20`） |
| `data-position`（DialogActions） | `start` / `end` | `end` | `position`（`packages/react-components/react-dialog/library/src/components/DialogActions/useDialogActionsStyles.styles.ts:28-48`） |
| `data-fluid`（DialogActions） | 有無 | なし | `fluid`（同 `:49-54`） |

### 寸法（size ごとの表）

値は抽出である。定数は `packages/react-components/react-dialog/library/src/contexts/constants.ts:1-6` にある。

| 対象 | 値 | 出典 |
|---|---|---|
| surface の配置 | `position: fixed; inset: 0; margin: auto; height: fit-content` | `packages/react-components/react-dialog/library/src/components/DialogSurface/useDialogSurfaceStyles.styles.ts:26-38` |
| surface の幅 | `max-width: 600px`。width の指定はなく、`inset: 0` と `margin: auto` で幅は min(600px, ビューポート) になる（推論） | 同 `:39` |
| surface の高さの上限 | `100vh`、`100dvh` | 同 `:40` |
| surface の padding | 24px | 同 `:27` |
| surface の線と角丸 | `1px solid colorTransparentStroke`、`borderRadiusXLarge`（8px） | 同 `:31-32` |
| surface の影 | `shadow64` | 同 `:46` |
| DialogBody | `gap: 8px`、`grid-template-rows: auto 1fr`、`grid-template-columns: 1fr 1fr auto`、`max-height: calc(100dvh - 48px)` | `packages/react-components/react-dialog/library/src/components/DialogBody/useDialogBodyStyles.styles.ts:20-27` |
| DialogTitle | `subtitle1`、1 行目、1〜2 列（action がなければ 1〜3 列） | `packages/react-components/react-dialog/library/src/components/DialogTitle/useDialogTitleStyles.styles.ts:17-30` |
| DialogContent | `body1`、padding 2px と margin -2px（輪が切れないため）、`min-height: 32px`、`overflow-y: auto` | `packages/react-components/react-dialog/library/src/components/DialogContent/useDialogContentStyles.styles.ts:16-27` |
| DialogActions | `display: flex; gap: 8px`、3 行目。end は 2〜3 列、start は 1 列 | `packages/react-components/react-dialog/library/src/components/DialogActions/useDialogActionsStyles.styles.ts:15-48` |

幅 480px 以下（`@media screen and (max-width: 480px)`）では並びを変える。

- surface と DialogBody の `max-width` は `100vw`、DialogBody の行は `auto 1fr auto` になる。
- DialogActions は縦並び（`flex-direction: column`）で横いっぱいに伸びる。end は 4 行目、start は 3 行目に移り、どちらも 1〜3 列を占める（同 `:22-48`）。

高さ 359px 以下では、surface 自体がスクロールし、右・上・下の線を 4px の透明の線にしてスクロールバーと角丸の干渉を避ける（`packages/react-components/react-dialog/library/src/components/DialogSurface/useDialogSurfaceStyles.styles.ts:52-60`）。

### 色と状態（トークン名の表）

| 対象 | トークン | 出典 |
|---|---|---|
| surface の背景 | `colorNeutralBackground1` | `packages/react-components/react-dialog/library/src/components/DialogSurface/useDialogSurfaceStyles.styles.ts:42` |
| surface の文字 | `colorNeutralForeground1` | 同 `:43` |
| surface の線 | `colorTransparentStroke` | 同 `:31` |
| backdrop（dimmed） | `colorBackgroundOverlay` | 同 `:63-67` |
| backdrop（transparent） | `colorTransparentBackground` | 同 `:70-72` |

### フォーカス・動き・ハイコントラスト

- フォーカス: surface と non-modal の既定の閉じるボタンが `createFocusOutlineStyle()` の輪を持つ（`packages/react-components/react-dialog/library/src/components/DialogSurface/useDialogSurfaceStyles.styles.ts:25`、`packages/react-components/react-dialog/library/src/components/DialogTitle/useDialogTitleStyles.styles.ts:47-62`）。輪は `::after` の 2px の `colorStrokeFocus2`、`inset: -2px`、角丸 `borderRadiusMedium` である。
- 動き（surface）: `Scale` の変種で、scale 0.85 → 1 と opacity 0 → 1 を同時に動かす。enter は 250ms（`durationGentle`）と `curveDecelerateMid`、exit は 250ms と `curveAccelerateMin`（`packages/react-components/react-dialog/library/src/components/DialogSurfaceMotion.ts:4-10`）。
- 動き（backdrop）: `FadeRelaxed` で、250ms と `curveEasyEase`（`packages/react-components/react-dialog/library/src/components/DialogBackdropMotion.ts:3`）。
- CSS では `<dialog>` の `[open]` の付け外しに `transition`（`display` と `overlay` は `allow-discrete`）と `@starting-style` で写す。曲線は、入るときに `[open]` の側、出るときに閉じた側の値が使われる。
- ハイコントラスト: v9 の Dialog に `forced-colors` の規則はない。線の `colorTransparentStroke` が CanvasText になる。輪は `Highlight` になる。

### 実装の例

開く Dialog。modal は外側のクリックと Esc で閉じ、non-modal はタイトルの右に閉じるボタンを持つ。

```html demo
<div style="display:flex;gap:8px;flex-wrap:wrap">
  <button type="button" class="fui-Button" data-appearance="primary" commandfor="ov-dlg-modal" command="show-modal" data-fui-enhance>削除の確認を開く</button>
  <button type="button" class="fui-Button" commandfor="ov-dlg-nonmodal" command="--show" data-fui-enhance>non-modal を開く</button>
</div>
<dialog id="ov-dlg-modal" class="fui-DialogSurface" data-modal-type="modal" closedby="any" aria-labelledby="ov-dlg-modal-title" data-fui-enhance>
  <div class="fui-DialogBody">
    <h2 class="fui-DialogTitle" id="ov-dlg-modal-title">このファイルを削除しますか</h2>
    <div class="fui-DialogContent">ごみ箱からも消え、元に戻せません。</div>
    <div class="fui-DialogActions">
      <button type="button" class="fui-Button" data-appearance="primary" commandfor="ov-dlg-modal" command="close" data-fui-enhance>削除</button>
      <button type="button" class="fui-Button" commandfor="ov-dlg-modal" command="close" data-fui-enhance>キャンセル</button>
    </div>
  </div>
</dialog>
<dialog id="ov-dlg-nonmodal" class="fui-DialogSurface" data-modal-type="non-modal" closedby="closerequest" aria-labelledby="ov-dlg-nonmodal-title" data-fui-enhance>
  <div class="fui-DialogBody">
    <h2 class="fui-DialogTitle" id="ov-dlg-nonmodal-title">検索と置換</h2>
    <div class="fui-DialogTitle__action">
      <button type="button" aria-label="閉じる" commandfor="ov-dlg-nonmodal" command="close" data-fui-enhance><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="m4.09 4.22.06-.07a.5.5 0 0 1 .63-.06l.07.06L10 9.29l5.15-5.14a.5.5 0 0 1 .63-.06l.07.06c.18.17.2.44.06.63l-.06.07L10.71 10l5.14 5.15c.18.17.2.44.06.63l-.06.07a.5.5 0 0 1-.63.06l-.07-.06L10 10.71l-5.15 5.14a.5.5 0 0 1-.63.06l-.07-.06a.5.5 0 0 1-.06-.63l.06-.07L9.29 10 4.15 4.85a.5.5 0 0 1-.06-.63l.06-.07z"/></svg></button>
    </div>
    <div class="fui-DialogContent">背後の文書を操作しながら使える。</div>
  </div>
</dialog>
```

開いた状態をページに置いた見本。backdrop の色、surface の影、DialogActions の start と end の並びを確かめられる。幅 480px 以下ではボタンが縦に並ぶ。

```html demo
<div class="fui-DialogSurface__backdrop" data-static>
  <div class="fui-DialogSurface" data-static role="dialog" aria-modal="true" aria-labelledby="ov-dlg-static-title">
    <div class="fui-DialogBody">
      <h2 class="fui-DialogTitle" id="ov-dlg-static-title">変更を保存しますか</h2>
      <div class="fui-DialogTitle__action">
        <button type="button" class="fui-Button" data-appearance="subtle" data-icon-only aria-label="閉じる"><span class="fui-Button__icon"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="m4.09 4.22.06-.07a.5.5 0 0 1 .63-.06l.07.06L10 9.29l5.15-5.14a.5.5 0 0 1 .63-.06l.07.06c.18.17.2.44.06.63l-.06.07L10.71 10l5.14 5.15c.18.17.2.44.06.63l-.06.07a.5.5 0 0 1-.63.06l-.07-.06L10 10.71l-5.15 5.14a.5.5 0 0 1-.63.06l-.07-.06a.5.5 0 0 1-.06-.63l.06-.07L9.29 10 4.15 4.85a.5.5 0 0 1-.06-.63l.06-.07z"/></svg></span></button>
      </div>
      <div class="fui-DialogContent">保存しないで閉じると、この 10 分間の編集が失われる。</div>
      <div class="fui-DialogActions" data-position="start">
        <button type="button" class="fui-Button">詳細</button>
      </div>
      <div class="fui-DialogActions" data-position="end">
        <button type="button" class="fui-Button" data-appearance="primary">保存</button>
        <button type="button" class="fui-Button">保存しない</button>
      </div>
    </div>
  </div>
</div>
```

### v9 との差と未確認の点

- v9 は surface を `div` で描き、backdrop は兄弟の `div` である。ここでは `<dialog>` と `::backdrop` を使う。`::backdrop` にトークンの CSS 変数が届くこと（`::backdrop` が元の要素から継承すること）を前提にしている。古いブラウザーでは backdrop の色が付かない。
- `command` と `commandfor`（Invoker Commands）、`closedby`、`requestClose()` の対応状況は、この作業では確かめていない。`data-fui-enhance` を付ければ `overlays.js` が代わりに動く。
- v9 の non-modal の既定の閉じるボタンは `aria-label="close"`（英語の固定値）である（`packages/react-components/react-dialog/library/src/components/DialogTitle/useDialogTitle.tsx:38-55`）。ここでは日本語のラベルを付ける。既定の閉じるボタンには静的な class がないため、action の直下の `fui-Button` でない `button` にスタイルを当てる。
- タイトルの列（action の有無）は `:has(+ .fui-DialogTitle__action)` で判定する。v9 は state で判定する。
- 文書のスクロールを止める規則は近似である。v9 は縦のスクロールバーがあるときだけ、入れ子でない modal のときだけ止める。
- サイトは alert をフッターのボタンでだけ閉じると説明するが、v9 のコードは alert も Esc で閉じる。ここではコードに従う。
- Web Components v3 は exit の曲線が `curveAccelerateMid`、backdrop が `curveLinear` である。v9 の値（`curveAccelerateMin`、`curveEasyEase`）を採った。
- `data-static` の backdrop の padding 24px は、見本を見やすくするための補助の値である（v9 にない）。

## Drawer

### 概要と使い分け（Do / Don't）

Drawer は、画面の一辺から出る補助の面である。主内容に関わる補足と簡単な操作を置く。短い情報なら Tooltip か Popover、データを失う操作の確認なら Dialog を使う。Drawer の中から Dialog を開いてよい。

- InlineDrawer は主内容の横に並び、両方を同時に見て操作するときに使う。OverlayDrawer はページを覆って注意を集め、既定で modal である。
- 配置は慣習に従う。ナビゲーションは start（左）、通知は end（右）に置く。
- 構成はヘッダー（タイトル、任意の閉じるボタンと上位の操作）、本文、任意のフッター（主ボタンを先頭に置く）である。
- Do: すぐ見て閉じられる情報に overlay を使う。作業は短くし、次の手順を明確にする。
- Don't: overlay を同時に複数開かない。規約のような長文に使わない。背後を見る必要があるときに full を使わない。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

| 部品 | class | 要素と属性 | 出典 |
|---|---|---|---|
| OverlayDrawer | `fui-OverlayDrawer` | `<dialog>`（v9 は Dialog の surface の `div`、`role="dialog"`、`aria-modal`）。`aria-labelledby` は見出しの id | `packages/react-components/react-drawer/library/src/components/OverlayDrawer/useOverlayDrawerStyles.styles.ts:12-15` |
| backdrop | `::backdrop`（静的な例では `fui-OverlayDrawer__backdrop`） | | `packages/react-components/react-drawer/library/src/components/OverlayDrawer/OverlayDrawerSurface/useOverlayDrawerSurfaceStyles.styles.ts:10-24` |
| InlineDrawer | `fui-InlineDrawer` | `div` か `aside`。閉じるときは `hidden` 属性 | `packages/react-components/react-drawer/library/src/components/InlineDrawer/useInlineDrawerStyles.styles.ts:10-17` |
| DrawerHeader | `fui-DrawerHeader` | `header`、`role="none"` | `packages/react-components/react-drawer/library/src/components/DrawerHeader/useDrawerHeaderStyles.styles.ts:18-29` |
| DrawerHeaderTitle | `fui-DrawerHeaderTitle`、`__heading`（`h2`）、`__action` | `div` | `packages/react-components/react-drawer/library/src/components/DrawerHeaderTitle/useDrawerHeaderTitleStyles.styles.ts:10-30` |
| DrawerHeaderNavigation | `fui-DrawerHeaderNavigation` | `nav` | `packages/react-components/react-drawer/library/src/components/DrawerHeaderNavigation/useDrawerHeaderNavigationStyles.styles.ts:16-18` |
| DrawerBody | `fui-DrawerBody` | `div`。スクロールする | `packages/react-components/react-drawer/library/src/components/DrawerBody/useDrawerBodyStyles.styles.ts:16-31` |
| DrawerFooter | `fui-DrawerFooter` | `footer`、`role="none"` | `packages/react-components/react-drawer/library/src/components/DrawerFooter/useDrawerFooterStyles.styles.ts:18-29` |

- OverlayDrawer は内部で Dialog を使う。Esc で閉じる、modal でフォーカスを閉じ込める、backdrop のクリックで閉じる、という振る舞いを引き継ぐ（`packages/react-components/react-drawer/library/src/components/OverlayDrawer/useOverlayDrawer.tsx:37,58-75`）。マークアップは Dialog と同じく `showModal()` と `closedby="any"` で書く。
- DrawerBody のスクロール状態（`none` / `top` / `middle` / `bottom`）で、ヘッダーの下とフッターの上の区切り線を出す（`packages/react-components/react-drawer/library/src/components/DrawerBody/useDrawerBody.ts:41-55`）。`data-fui-enhance` を付けると `overlays.js` が Drawer の根に `data-scroll-state` を書く。

### バリエーション

| 属性 | 値 | 既定 | v9 の props と出典 |
|---|---|---|---|
| `data-position` | `start` / `end` / `bottom` | `start` | `position`（`packages/react-components/react-drawer/library/src/shared/useDrawerDefaultProps.ts:9`） |
| `data-size` | `small` / `medium` / `large` / `full` | `small` | `size`（同） |
| `data-modal-type`（Overlay） | `modal` / `non-modal` / `alert` | `modal` | `modalType`（`packages/react-components/react-drawer/library/src/components/OverlayDrawer/useOverlayDrawer.tsx:37`） |
| `data-separator`（Inline） | 有無 | なし | `separator`（`packages/react-components/react-drawer/library/src/components/InlineDrawer/useInlineDrawer.ts:37`） |
| `data-inline`（Overlay） | 有無 | なし | mountNode を指定したとき `position: absolute`（`packages/react-components/react-drawer/library/src/components/OverlayDrawer/useOverlayDrawerStyles.styles.ts:37-39`） |

### 寸法（size ごとの表）

| size | 幅（start / end）と高さ（bottom） | 動きの時間 | 出典 |
|---|---|---|---|
| `small` | 320px | 250ms（`durationGentle`） | `packages/react-components/react-drawer/library/src/shared/useDrawerBaseStyles.styles.ts:57-59`、`packages/react-components/react-drawer/library/src/shared/drawerMotions.ts:14-19` |
| `medium` | 592px | 300ms（`durationSlow`） | 同 `:60-62` |
| `large` | 940px | 400ms（`durationSlower`） | 同 `:63-65` |
| `full` | 100vw（bottom は 100%） | 500ms（`durationUltraSlow`） | 同 `:66-68,82-84` |

| 対象 | 値 | 出典 |
|---|---|---|
| 面の共通 | `width: var(--fui-Drawer--size); max-width: 100vw; max-height: 100vh; display: flex; flex-direction: column; overflow: hidden` | `packages/react-components/react-drawer/library/src/shared/useDrawerBaseStyles.styles.ts:18-32` |
| OverlayDrawer | `position: fixed; top: 0; bottom: 0`。bottom は `height: var(--fui-Drawer--size); width: 100vw` | `packages/react-components/react-drawer/library/src/components/OverlayDrawer/useOverlayDrawerStyles.styles.ts:20-36` |
| 内側の辺の線 | start は終端側、end は始端側に `strokeWidthThin` の `colorTransparentStroke` | `packages/react-components/react-drawer/library/src/shared/useDrawerBaseStyles.styles.ts:39-50` |
| InlineDrawer の separator | `1px solid colorNeutralBackground3`。start は終端側、end は始端側、bottom は上 | `packages/react-components/react-drawer/library/src/components/InlineDrawer/useInlineDrawerStyles.styles.ts:22-27` |
| DrawerHeader | `padding: 24px 24px 8px`、`gap: 8px` | `packages/react-components/react-drawer/library/src/components/DrawerHeader/useDrawerHeaderStyles.styles.ts:18-29` |
| DrawerHeaderTitle | `display: flex; justify-content: space-between; column-gap: 8px`。見出しは `subtitle1`。action は終端側に -8px | `packages/react-components/react-drawer/library/src/components/DrawerHeaderTitle/useDrawerHeaderTitleStyles.styles.ts:19-30` |
| DrawerHeaderNavigation | `margin: -8px -16px` | `packages/react-components/react-drawer/library/src/components/DrawerHeaderNavigation/useDrawerHeaderNavigationStyles.styles.ts:16-18` |
| DrawerBody | `padding: 0 24px; flex: 1; overflow: auto`。最初の子なら上、最後の子なら下に 25px | `packages/react-components/react-drawer/library/src/components/DrawerBody/useDrawerBodyStyles.styles.ts:16-31` |
| DrawerFooter | `padding: 16px 24px 24px; column-gap: 8px` | `packages/react-components/react-drawer/library/src/components/DrawerFooter/useDrawerFooterStyles.styles.ts:18-29` |
| 区切り線 | 高さ 1px、`opacity` 0 → 1 を 200ms・`curveEasyEase` | `packages/react-components/react-drawer/library/src/shared/drawerSeparatorStyles.ts:4-15` |

### 色と状態（トークン名の表）

| 対象 | トークン | 出典 |
|---|---|---|
| 面の背景 | `colorNeutralBackground1` | `packages/react-components/react-drawer/library/src/shared/useDrawerBaseStyles.styles.ts:30` |
| 面の文字 | `colorNeutralForeground1` | 同 `:31` |
| 内側の辺の線 | `colorTransparentStroke` | 同 `:40,46` |
| InlineDrawer の separator | `colorNeutralBackground3` | `packages/react-components/react-drawer/library/src/components/InlineDrawer/useInlineDrawerStyles.styles.ts:22` |
| スクロール時の区切り線 | `colorNeutralStroke1` | `packages/react-components/react-drawer/library/src/shared/drawerSeparatorStyles.ts:10` |
| backdrop | `colorBackgroundOverlay`（入れ子は `colorTransparentBackground`） | `packages/react-components/react-drawer/library/src/components/OverlayDrawer/OverlayDrawerSurface/useOverlayDrawerSurfaceStyles.styles.ts:13-19` |

### フォーカス・動き・ハイコントラスト

- フォーカス: OverlayDrawer の根が `createFocusOutlineStyle()` の輪を持つ（`packages/react-components/react-drawer/library/src/components/OverlayDrawer/useOverlayDrawerStyles.styles.ts:21`）。v9 と同じく面の `overflow: hidden` の内側では輪が切れる。InlineDrawer に輪はない。
- 動き（OverlayDrawer）: `transform: translate3d(±size)` → 0、`box-shadow` なし → `shadow64`（v9 の最初の keyframe の `0px colorTransparentBackground` は box-shadow として無効なので、影なしとして書いた）、opacity 0 → 1。enter は `curveDecelerateMid`、exit は同じ時間で `curveAccelerateMin`。時間は size で決まる（`packages/react-components/react-drawer/library/src/shared/drawerMotions.ts:85-116`）。RTL では start と end の向きが入れ替わる（同 `:24-46`）。
- 動き（backdrop）: opacity のフェード、size 連動の時間、`curveLinear`（同 `:121-129`）。
- 動き（InlineDrawer）: transform と opacity だけで影はない（同 `:51-80`）。`hidden` 属性の付け外しに `transition` と `@starting-style` で写す。
- ハイコントラスト: v9 の Drawer に `forced-colors` の規則はない。内側の辺の `colorTransparentStroke` が CanvasText の線になる。

### 実装の例

開く OverlayDrawer（end、small）。

```html demo
<button type="button" class="fui-Button" data-appearance="primary" commandfor="ov-drawer-live" command="show-modal" data-fui-enhance>通知を開く</button>
<dialog id="ov-drawer-live" class="fui-OverlayDrawer" data-position="end" closedby="any" aria-labelledby="ov-drawer-live-title" data-fui-enhance>
  <header class="fui-DrawerHeader" role="none">
    <div class="fui-DrawerHeaderTitle">
      <h2 class="fui-DrawerHeaderTitle__heading" id="ov-drawer-live-title">通知</h2>
      <div class="fui-DrawerHeaderTitle__action">
        <button type="button" class="fui-Button" data-appearance="subtle" data-icon-only aria-label="閉じる" commandfor="ov-drawer-live" command="close" data-fui-enhance><span class="fui-Button__icon"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="m4.09 4.22.06-.07a.5.5 0 0 1 .63-.06l.07.06L10 9.29l5.15-5.14a.5.5 0 0 1 .63-.06l.07.06c.18.17.2.44.06.63l-.06.07L10.71 10l5.14 5.15c.18.17.2.44.06.63l-.06.07a.5.5 0 0 1-.63.06l-.07-.06L10 10.71l-5.15 5.14a.5.5 0 0 1-.63.06l-.07-.06a.5.5 0 0 1-.06-.63l.06-.07L9.29 10 4.15 4.85a.5.5 0 0 1-.06-.63l.06-.07z"/></svg></span></button>
      </div>
    </div>
  </header>
  <div class="fui-DrawerBody">
    <p>新しい通知はない。</p>
  </div>
  <footer class="fui-DrawerFooter" role="none">
    <button type="button" class="fui-Button" data-appearance="primary" commandfor="ov-drawer-live" command="close" data-fui-enhance>閉じる</button>
  </footer>
</dialog>
```

開いた状態を囲みの中に置いた見本。`data-scroll-state="middle"` で、ヘッダーとフッターの区切り線が見える。

```html demo
<div style="position:relative;height:360px;overflow:hidden;border-radius:4px">
  <div class="fui-OverlayDrawer__backdrop" data-static></div>
  <div class="fui-OverlayDrawer" data-static data-position="end" data-scroll-state="middle" role="dialog" aria-modal="true" aria-labelledby="ov-drawer-static-title">
    <header class="fui-DrawerHeader" role="none">
      <div class="fui-DrawerHeaderTitle">
        <h2 class="fui-DrawerHeaderTitle__heading" id="ov-drawer-static-title">フィルター</h2>
        <div class="fui-DrawerHeaderTitle__action">
          <button type="button" class="fui-Button" data-appearance="subtle" data-icon-only aria-label="閉じる"><span class="fui-Button__icon"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="m4.09 4.22.06-.07a.5.5 0 0 1 .63-.06l.07.06L10 9.29l5.15-5.14a.5.5 0 0 1 .63-.06l.07.06c.18.17.2.44.06.63l-.06.07L10.71 10l5.14 5.15c.18.17.2.44.06.63l-.06.07a.5.5 0 0 1-.63.06l-.07-.06L10 10.71l-5.15 5.14a.5.5 0 0 1-.63.06l-.07-.06a.5.5 0 0 1-.06-.63l.06-.07L9.29 10 4.15 4.85a.5.5 0 0 1-.06-.63l.06-.07z"/></svg></span></button>
        </div>
      </div>
    </header>
    <div class="fui-DrawerBody">
      <p>期間、種類、作成者で絞り込む。</p>
      <p>本文が長いときは、この領域だけがスクロールする。</p>
      <p>スクロールの途中では、上下の区切り線が両方見える。</p>
    </div>
    <footer class="fui-DrawerFooter" role="none">
      <button type="button" class="fui-Button" data-appearance="primary">適用</button>
      <button type="button" class="fui-Button">クリア</button>
    </footer>
  </div>
</div>
```

InlineDrawer（start、separator あり）。主内容の横に並ぶ。

```html demo
<div style="display:flex;height:240px;border:1px solid var(--colorNeutralStroke2);border-radius:4px;overflow:hidden">
  <aside class="fui-InlineDrawer" data-separator aria-labelledby="ov-inline-title">
    <header class="fui-DrawerHeader" role="none">
      <div class="fui-DrawerHeaderTitle">
        <h2 class="fui-DrawerHeaderTitle__heading" id="ov-inline-title">目次</h2>
      </div>
    </header>
    <div class="fui-DrawerBody">
      <p>1. はじめに</p>
      <p>2. 設定</p>
    </div>
  </aside>
  <div style="padding:24px">主内容</div>
</div>
```

### v9 との差と未確認の点

- v9 の OverlayDrawer は Dialog の surface（`div`）である。ここでは `<dialog>` を使い、UA の margin、padding、border を消している。
- 区切り線の出し入れは、v9 では DrawerBody のスクロール状態を context で渡す。ここでは `overlays.js` が根に `data-scroll-state` を書く。JS がないと区切り線は出ない（v9 の `none` と同じ見た目）。
- InlineDrawer の閉じ方は、v9 では退場の動きのあとで幅を 0 にする（`packages/react-components/react-drawer/library/src/components/InlineDrawer/useInlineDrawerStyles.styles.ts:37-50,103`）。ここでは `hidden` 属性で `display: none` にする。結果の見た目は同じである。
- 影は、v9 では motion の最後の keyframe が `fill: forwards` で残る。静的な `div` の例では、同じ `shadow64` を静的に付けている。
- `::backdrop` の時間を size ごとに書くのは、`::backdrop` が独自の CSS 変数を受け継がない環境への備えである。
- Web Components v3 は既定の幅が 592px、padding が 20px、時間が 250ms に固定である。v9 の値を採った。
- `data-static` の OverlayDrawer は `position: absolute` で、`position: relative` の囲みの中に置く（補助の規則）。
- `data-inline`（mountNode の指定）のとき、v9 は面だけでなく backdrop にも `position: absolute` を当てる（`packages/react-components/react-drawer/library/src/components/OverlayDrawer/useOverlayDrawerStyles.styles.ts:37-39,65`）。以前の CSS は backdrop を fixed のまま残していたので直した。`fui-OverlayDrawer__backdrop` にも `data-inline` を付ける。
- v9 の DrawerHeaderTitle は `useDialogTitleStyles_unstable` を通すので、見出しと action に `fui-DialogTitle`、`fui-DialogTitle__action` の class も付く（`packages/react-components/react-drawer/library/src/components/DrawerHeaderTitle/useDrawerHeaderTitleStyles.styles.ts:49-56`）。ここでは付けない。付けると Dialog の grid の規則が当たる。`tools/verify/compare-b.html` の比較（2026-11-13）で、付けない形の寸法・色・位置が v9 と一致した。

## Popover

### 概要と使い分け（Do / Don't）

Popover は、部品を操作したときに出る小さな面である。作業を遮らない補足の情報や、二次的な操作を置く。複雑なレイアウトや背後を遮りたいときは Dialog、短い書式なしの文は Tooltip を使う。

- 矢印は、何に関わる面かを示す。
- 大きさは内容に合わせて伸びる。はみ出すときは一方向だけスクロールさせる。
- Do: 何に関わるかがわかる位置に置く。短い文で書く。詳しい情報は末尾のリンクに逃がす。
- Don't: 入れ子にしない。作業に必須の内容を入れない。二方向のスクロールバーを出さない。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

| 部品 | class | 要素と属性 | 出典 |
|---|---|---|---|
| PopoverSurface | `fui-PopoverSurface` | `div[popover]`。`trapFocus` がなければ `role="group"` | `packages/react-components/react-popover/library/src/components/PopoverSurface/usePopoverSurface.ts:51-63` |
| 矢印 | `fui-PopoverSurface__arrow`（作った class） | 面の最初の子の `div`、`aria-hidden="true"` | `packages/react-components/react-popover/library/src/components/PopoverSurface/renderPopoverSurface.tsx:11-26` |

- トリガーに `popovertarget="<id>"` を書けば JS なしで開閉する。Esc と外側のクリックで閉じる（`popover="auto"`）。v9 も Esc で閉じる（`packages/react-components/react-popover/library/src/components/PopoverSurface/usePopoverSurface.ts:87-96`）。
- 位置はアンカー位置決めで決める。`popovertarget` か `commandfor` で開く面は、開いたトリガーがブラウザーの暗黙のアンカーになるので、`anchor-name` も `position-anchor` も書かない（Chromium 156 で確かめた）。インラインの style 属性を使わないので、CSP（`style-src 'self'`）の下でも位置が決まる。JS から `showPopover()` で開く面（Tooltip）は暗黙のアンカーができないので、`overlays.js` が開くときに CSSOM でトリガーと面を結ぶ。既定は above・center で、offset は 0（矢印ありは矢印の高さ）である（`packages/react-components/react-popover/library/src/components/Popover/usePopover.ts:266-282`）。
- `trapFocus` 相当（`role="dialog"` とフォーカスの閉じ込め）が要るときは、modal の `<dialog>` を使う。

### バリエーション

| 属性 | 値 | 既定 | v9 の props と出典 |
|---|---|---|---|
| `data-size` | `small` / `medium` / `large` | `medium` | `size`（`packages/react-components/react-popover/library/src/components/Popover/usePopover.ts:46`） |
| `data-appearance` | なし / `brand` / `inverted` | なし | `appearance`（`packages/react-components/react-popover/library/src/components/Popover/Popover.types.ts:33-37`） |
| `data-with-arrow` | 有無 | なし | `withArrow`（同 `:71-76`） |
| `data-positioning` | `above` / `above-start` / `above-end` / `below` / `below-start` / `below-end` / `before` / `before-top` / `before-bottom` / `after` / `after-top` / `after-bottom` | `above` | `positioning` の省略記法 |
| `data-inline` | 有無 | なし | `inline`（`z-index: 1`） |

### 寸法（size ごとの表）

| size | padding | 矢印の高さ | 矢印の一辺 | 出典 |
|---|---|---|---|---|
| `small` | 12px | 6px | 8.484px | `packages/react-components/react-popover/library/src/components/PopoverSurface/usePopoverSurfaceStyles.styles.ts:14-18,53` |
| `medium` | 16px | 8px | 11.312px | 同 `:14-18,55` |
| `large` | 20px | 8px | 11.312px | 同 `:14-18,57` |

- 角丸は `borderRadiusMedium`、線は `1px solid colorTransparentStroke`、文字は `body1` である（同 `:24-29`）。
- 影は `filter: drop-shadow(0 0 2px ambient) drop-shadow(0 8px 16px key)` で、`shadow16` と同じ組を矢印にも付ける（同 `:31-34`）。
- 矢印の一辺は高さ × 1.414、offset は一辺の半分の負数である（`packages/react-components/react-positioning/library/src/createArrowStyles.ts:131-140`）。矢印は 45° 回した正方形で、`::before` の線を三角に切り抜く（同 `:72-101`）。

### 色と状態（トークン名の表）

| appearance | 背景 | 文字 | 出典 |
|---|---|---|---|
| 既定 | `colorNeutralBackground1` | `colorNeutralForeground1` | `packages/react-components/react-popover/library/src/components/PopoverSurface/usePopoverSurfaceStyles.styles.ts:25-26` |
| `inverted` | `colorNeutralBackgroundStatic` | `colorNeutralForegroundStaticInverted` | 同 `:43-46` |
| `brand` | `colorBrandBackground` | `colorNeutralForegroundOnBrand` | 同 `:48-51` |

矢印は `background-color: inherit` で面の色に従う。

### フォーカス・動き・ハイコントラスト

- フォーカス: 面自体に輪はない。開くと最初のフォーカスできる要素へ移すのが v9 の振る舞いである（`packages/react-components/react-popover/library/src/components/Popover/usePopover.ts:175-194`）。
- 動き: enter だけで、exit はない。400ms（`durationSlower`）と `curveDecelerateMid` で、fade と 10px の slide を同時に動かす（`packages/react-components/react-popover/library/src/components/Popover/PopoverSurfaceMotion.ts:8-42`）。slide の向きは配置で決まる。top なら y = +1、bottom なら y = -1、right なら x = -1、left なら x = +1 で、面はアンカーから離れる向きに動く（`packages/react-components/react-positioning/library/src/usePositioningSlideDirection.ts:15-33`）。CSS では `:popover-open` の `@keyframes fui-PopoverSurface-enter` で写す。
- ハイコントラスト: `forced-colors` の規則はない。線の `colorTransparentStroke` が見える。

### 実装の例

開く Popover（矢印あり、below）。

```html demo
<button type="button" class="fui-Button" popovertarget="ov-pop-live">詳細を見る</button>
<div id="ov-pop-live" class="fui-PopoverSurface" popover role="group" aria-label="詳細" data-with-arrow data-positioning="below">
  <div class="fui-PopoverSurface__arrow" aria-hidden="true"></div>
  <div class="fui-Body1Strong">共有の設定</div>
  <div>リンクを知っている人は誰でも表示できる。</div>
</div>
```

開いた状態の見本。size、appearance、矢印の向きを並べる。

```html demo
<div style="display:flex;flex-wrap:wrap;gap:24px;align-items:flex-start;padding:12px">
  <div class="fui-PopoverSurface" data-static data-with-arrow data-size="small" role="group">
    <div class="fui-PopoverSurface__arrow" aria-hidden="true"></div>small・既定
  </div>
  <div class="fui-PopoverSurface" data-static data-with-arrow role="group">
    <div class="fui-PopoverSurface__arrow" aria-hidden="true"></div>medium・既定
  </div>
  <div class="fui-PopoverSurface" data-static data-with-arrow data-appearance="inverted" data-positioning="below" role="group">
    <div class="fui-PopoverSurface__arrow" aria-hidden="true"></div>inverted・below
  </div>
  <div class="fui-PopoverSurface" data-static data-with-arrow data-appearance="brand" data-size="large" data-positioning="after" role="group">
    <div class="fui-PopoverSurface__arrow" aria-hidden="true"></div>brand・large・after
  </div>
</div>
```

### v9 との差と未確認の点

- v9 は floating-ui で位置を決め、`data-popper-placement` で矢印の向きを決める。ここでは CSS のアンカー位置決め（`position-area`、`position-try-fallbacks`）で近似し、矢印と slide の向きは `data-positioning` から決める。画面端で反転すると、矢印と slide の向きが実際の配置と合わなくなる。そのため矢印つきでは反転させない（`position-try-fallbacks: none`）。
- アンカー位置決めが使えないブラウザーでは、`[popover]` の UA の既定（画面の中央）のまま出る。暗黙のアンカーは Chromium 156 で確かめた。Firefox と WebKit では確かめていない。暗黙のアンカーがないブラウザーで位置を決めたいときは、CSS の規則でトリガーに `anchor-name`、面に `position-anchor` を書く（style 属性に書くと CSP の下で無視される）。
- 矢印の交差軸の位置は、v9 では floating-ui が対象の中央に合わせる（`arrowPadding` 8px）。ここでは面の中央に置く（推論）。`-start` や `-end` の配置で面がトリガーより広いと、矢印がトリガーの中央からずれる。
- 矢印の class `fui-PopoverSurface__arrow` は作った名前である。v9 の矢印には静的な class がない（`packages/react-components/react-popover/library/src/components/PopoverSurface/usePopoverSurfaceStyles.styles.ts:83-86`）。
- `data-positioning` と `position-area` の対応は、Web Components v3 の Tooltip（`packages/web-components/src/tooltip/tooltip.styles.ts:72-107`）に倣った。
- v9 の `openOnHover`、`openOnContext`、`trapFocus` は扱わない。
- slide の向きの変数は `@property` で継承なしとして登録する。v9 の `CSS.registerProperty` と同じ扱いである（`packages/react-components/react-positioning/library/src/usePositioningSlideDirection.ts:87`）。

## Menu

### 概要と使い分け（Do / Don't）

Menu は、トリガーを操作すると出る選択肢の一覧である。選択肢は、すぐ実行する操作か、別の場所への移動である。入力を集めるなら Select、Dropdown、Combobox を使う。

- 種類は、既定（各項目が操作）、checkbox（複数選択）、radio（1 つを選ぶ）である。
- 幅の上限は 300px で、長い項目名は折り返す。
- Do: よく使う操作を先に、破壊的な操作を最後に並べる。項目名は短くし、操作は結果を表す動詞にする。副次の内容には、その項目と同じ動作のショートカットだけを置く。
- Don't: サブメニューを多用しない。開きにくく、元の文脈を見失いやすい。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

| 部品 | class | 要素と属性 | 出典 |
|---|---|---|---|
| MenuPopover | `fui-MenuPopover` | `div[popover]`、`role="presentation"` | `packages/react-components/react-menu/library/src/components/MenuPopover/useMenuPopover.ts:79` |
| MenuList | `fui-MenuList` | `role="menu"` | `packages/react-components/react-menu/library/src/components/MenuList/useMenuList.ts:173-174` |
| MenuItem | `fui-MenuItem`、`__icon`、`__checkmark`、`__content`、`__subText`、`__secondaryContent`、`__submenuIndicator` | `role="menuitem"`、`tabindex="-1"`。スロットは `span` | `packages/react-components/react-menu/library/src/components/MenuItem/useMenuItemBase.tsx:55-120` |
| MenuItemCheckbox | `fui-MenuItemCheckbox fui-MenuItem`。スロットにも `fui-MenuItemCheckbox__icon`、`__checkmark`、`__content` などを併記する | `role="menuitemcheckbox"`、`aria-checked` | `packages/react-components/react-menu/library/src/components/MenuItemCheckbox/useMenuItemCheckbox.tsx:40-50`、`MenuItemCheckbox/useMenuItemCheckboxStyles.styles.ts:10-17` |
| MenuItemRadio | `fui-MenuItemRadio fui-MenuItem`。スロットにも `fui-MenuItemRadio__checkmark`、`__content` などを併記する | `role="menuitemradio"`、`aria-checked` | `packages/react-components/react-menu/library/src/components/MenuItemRadio/useMenuItemRadioStyles.styles.ts:51-52` |
| MenuDivider | `fui-MenuDivider` | `role="presentation"` | `packages/react-components/react-menu/library/src/components/MenuDivider/useMenuDividerStyles.styles.ts:12-18` |
| MenuGroup | `fui-MenuGroup` | `role="group"`、`aria-labelledby` は見出しの id | `packages/react-components/react-menu/library/src/components/MenuGroup/useMenuGroupStyles.styles.ts:5-7` |
| MenuGroupHeader | `fui-MenuGroupHeader` | 見出しの id を持つ | `packages/react-components/react-menu/library/src/components/MenuGroupHeader/useMenuGroupHeaderStyles.styles.ts:12-23` |

- スロットの順は checkmark、icon、content（subText を含む）、secondaryContent、submenuIndicator である（`packages/react-components/react-menu/library/src/components/MenuItem/useMenuItemBase.tsx:104-119`）。
- checkbox と radio のチェックは `Checkmark16Filled` である。サブメニューの印は `ChevronRight` の Regular と Filled の組で、hover で Filled に切り替える（`packages/react-components/react-menu/library/src/components/MenuItem/useMenuItemStyles.styles.ts:47-52`）。
- キーボード（`data-fui-enhance` で `overlays.js` が扱う）: 上下の矢印で循環して移る、Home と End、先頭文字で探す（`packages/react-components/react-menu/library/src/components/MenuList/useMenuList.ts:49`、`packages/react-components/react-menu/library/src/components/MenuItem/useMenuItemBase.tsx:121`）。Enter と Space で選ぶ。Esc で閉じてトリガーへ戻る。Tab で閉じてトリガーへ戻る（`packages/react-components/react-menu/library/src/components/MenuPopover/useMenuPopover.ts:40-46,99-110`）。トリガーで下矢印を押すと開く（`packages/react-components/react-menu/library/src/components/MenuTrigger/useMenuTrigger.ts:84`）。
- マウスが乗った項目にフォーカスを移す（`packages/react-components/react-menu/library/src/components/MenuItem/useMenuItemBase.tsx:79-85`）。無効の項目は `aria-disabled="true"` で、フォーカスは受ける（同 `:70-71`）。
- 項目を選ぶと閉じる（`packages/react-components/react-menu/library/src/components/MenuItem/useMenuItemBase.tsx:87`）。checkbox は閉じない（`persistOnClick`、`packages/react-components/react-menu/library/src/components/MenuItemCheckbox/useMenuItemCheckbox.tsx:45`）。Menu の根に `data-persist-on-item-click` を書くと、どの項目でも閉じない。radio は同じ `role="group"` の中の同じ `data-name` で 1 つだけ選ぶ（v9 の `name`）。

### バリエーション

| 種類・状態 | 書き方 | 出典 |
|---|---|---|
| 既定の項目 | `role="menuitem"` | `packages/react-components/react-menu/library/src/components/MenuItem/useMenuItemBase.tsx` |
| checkbox | `role="menuitemcheckbox"`、`aria-checked` は `true` か `false` | `packages/react-components/react-menu/library/src/components/MenuItemCheckbox/useMenuItemCheckbox.tsx:44-47` |
| radio | `role="menuitemradio"`、`aria-checked` は `true` か `false` | `packages/react-components/react-menu/library/src/components/MenuItemRadio/useMenuItemRadio.tsx:54-55` |
| 無効 | `aria-disabled="true"` | `packages/react-components/react-menu/library/src/components/MenuItem/useMenuItemStyles.styles.ts:184-243` |
| サブメニューを開いている | `aria-expanded="true"` | 同 `:156-183` |
| 複数行 | `fui-MenuItem__subText` を置く（`:has()` で判定） | 同 `:256-269,282` |
| 位置 | `data-positioning`（既定 `below-start`、サブメニューは `after-top`） | `packages/react-components/react-menu/library/src/components/Menu/useMenu.tsx:113-120` |

### 寸法（size ごとの表）

| 部品 | 値 | 出典 |
|---|---|---|
| MenuPopover | `min-width: 138px; max-width: 300px; width: max-content; padding: 4px`、線 1px、角丸 `borderRadiusMedium`、影 `shadow16`、文字 `body1` | `packages/react-components/react-menu/library/src/components/MenuPopover/useMenuPopoverStyles.styles.ts:12-27` |
| MenuList | `display: flex; flex-direction: column; gap: 2px` | `packages/react-components/react-menu/library/src/components/MenuList/useMenuListStyles.styles.ts:11-20` |
| MenuItem | `padding: 6px`（`spacingVerticalSNudge`）、`max-width: 290px; min-height: 32px; gap: 4px`、`font-size: fontSizeBase300` | `packages/react-components/react-menu/library/src/components/MenuItem/useMenuItemStyles.styles.ts:24-41` |
| content | 左右 2px | 同 `:89-94` |
| secondaryContent | 左右 2px、`caption1` に `line-height: lineHeightBase300` | 同 `:96-108` |
| icon と submenuIndicator | 20px 四方 | 同 `:110-129` |
| subText | `caption2` | 同 `:131-134` |
| checkmark | 16px 四方、`margin-top: 2px`、未選択は `visibility: hidden` | `packages/react-components/react-menu/library/src/selectable/useCheckmarkStyles.styles.ts:7-18`、`packages/react-components/react-menu/library/src/components/MenuItem/useMenuItemStyles.styles.ts:137-139` |
| MenuDivider | `margin: 4px -5px`、下に `strokeWidthThin` の線 | `packages/react-components/react-menu/library/src/components/MenuDivider/useMenuDividerStyles.styles.ts:12-18` |
| MenuGroupHeader | `fontSizeBase200`、Semibold、左右 8px、高さ 32px | `packages/react-components/react-menu/library/src/components/MenuGroupHeader/useMenuGroupHeaderStyles.styles.ts:12-23` |

### 色と状態（トークン名の表）

| 状態 | 背景 | 文字 | icon | subText | 出典（`packages/react-components/react-menu/library/src/components/MenuItem/useMenuItemStyles.styles.ts`） |
|---|---|---|---|---|---|
| 既定 | `colorNeutralBackground1` | `colorNeutralForeground2` | 継承 | `colorNeutralForeground3` | `:27-28,131-134` |
| hover | `colorNeutralBackground1Hover` | `colorNeutralForeground2Hover` | `colorNeutralForeground2BrandSelected` | `colorNeutralForeground3Hover` | `:43-60` |
| hover かつ押下 | `colorNeutralBackground1Pressed` | `colorNeutralForeground2Pressed` | hover と同じ | `colorNeutralForeground3Pressed` | `:62-69` |
| サブメニューを開いている | `colorNeutralBackground1Hover` | `colorNeutralForeground2Hover` | `colorNeutralForeground2BrandSelected` | `colorNeutralForeground3Hover` | `:156-173` |
| 無効 | `colorNeutralBackground1`（hover でも同じ） | `colorNeutralForegroundDisabled` | `colorNeutralForegroundDisabled` | `colorNeutralForegroundDisabled` | `:184-216,246-254` |

- secondaryContent は `colorNeutralForeground3` で、それ自身の hover と focus で `colorNeutralForeground3Hover` になる（`:101-107`）。
- MenuPopover は背景 `colorNeutralBackground1`、文字 `colorNeutralForeground1`、線 `colorTransparentStroke` である。MenuDivider は `colorNeutralStroke2`、MenuGroupHeader は `colorNeutralForeground3` である。

### フォーカス・動き・ハイコントラスト

- フォーカス: MenuItem は `createFocusOutlineStyle()` の輪を持つ（`packages/react-components/react-menu/library/src/components/MenuItem/useMenuItemStyles.styles.ts:86`）。
- 動き: Popover と同じで、enter だけ、400ms と `curveDecelerateMid`、fade と 10px の slide（`packages/react-components/react-menu/library/src/components/Menu/MenuSurfaceMotion.ts:8-42`）。下に開くときは上から下へ動く。
- ハイコントラスト（`packages/react-components/react-menu/library/src/components/MenuItem/useMenuItemStyles.styles.ts:72-83,174-182,217-252`）: hover とサブメニューを開いた項目は `forced-color-adjust: none` で背景 `Highlight`、文字とスロットは `HighlightText` にする。輪は `Highlight` である。無効の項目は `GrayText` で、hover と押下とフォーカスでは背景を `Canvas` にする。

### 実装の例

開く Menu。`data-fui-enhance` で矢印キーと選択が動く。

```html demo
<button type="button" class="fui-Button" popovertarget="ov-menu-live" aria-haspopup="menu">編集</button>
<div id="ov-menu-live" class="fui-MenuPopover" popover role="presentation" data-fui-enhance>
  <div class="fui-MenuList" role="menu" aria-label="編集">
    <div class="fui-MenuItem" role="menuitem" tabindex="-1">
      <span class="fui-MenuItem__icon" aria-hidden="true"><svg class="fui-Icon fui-Icon-regular" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M5.92 2.23a.5.5 0 0 0-.84.54L9.4 9.43l-1.92 2.96a3 3 0 1 0 .78.64L10 10.35l1.74 2.68a3 3 0 1 0 .78-.64zM14 17a2 2 0 1 1 0-4 2 2 0 0 1 0 4M4 15a2 2 0 1 1 4 0 2 2 0 0 1-4 0m7.2-6.49-.6-.92 3.48-5.36a.5.5 0 0 1 .84.54z"/></svg><svg class="fui-Icon fui-Icon-filled" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="m14.88 3.16-3.1 4.77-.9-1.38 2.74-4.2a.75.75 0 0 1 1.26.8m-2.38 8.6a3.24 3.24 0 0 1 4.5 2.99 3.25 3.25 0 1 1-5.72-2.11L10 10.66l-1.28 1.98a3.25 3.25 0 1 1-1.21-.88l1.6-2.47-3.99-6.13a.75.75 0 0 1 1.26-.82zm.2 1.6a1.75 1.75 0 1 0 .01-.02zM6.24 13a1.75 1.75 0 1 0 0 3.5 1.75 1.75 0 0 0 0-3.5"/></svg></span>
      <span class="fui-MenuItem__content">切り取り</span>
      <span class="fui-MenuItem__secondaryContent">Ctrl+X</span>
    </div>
    <div class="fui-MenuItem" role="menuitem" tabindex="-1">
      <span class="fui-MenuItem__icon" aria-hidden="true"><svg class="fui-Icon fui-Icon-regular" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7 7H5a2 2 0 0 0-2 2v6c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2h1a3 3 0 0 1-3 3H5a3 3 0 0 1-3-3V9a3 3 0 0 1 3-3h2zm8-5a3 3 0 0 1 3 3v6a3 3 0 0 1-3 3h-4a3 3 0 0 1-3-3V5a3 3 0 0 1 3-3zm-4 1a2 2 0 0 0-2 2v6c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2z"/></svg><svg class="fui-Icon fui-Icon-filled" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7 11a4 4 0 0 0 4 4h1a3 3 0 0 1-3 3H5a3 3 0 0 1-3-3V9a3 3 0 0 1 3-3h2zm8-9a3 3 0 0 1 3 3v6a3 3 0 0 1-3 3h-4a3 3 0 0 1-3-3V5a3 3 0 0 1 3-3z"/></svg></span>
      <span class="fui-MenuItem__content">コピー</span>
      <span class="fui-MenuItem__secondaryContent">Ctrl+C</span>
    </div>
    <div class="fui-MenuItem" role="menuitem" tabindex="-1" aria-disabled="true">
      <span class="fui-MenuItem__icon" aria-hidden="true"></span>
      <span class="fui-MenuItem__content">貼り付け</span>
      <span class="fui-MenuItem__secondaryContent">Ctrl+V</span>
    </div>
    <div class="fui-MenuDivider" role="presentation"></div>
    <div class="fui-MenuItemCheckbox fui-MenuItem" role="menuitemcheckbox" aria-checked="true" tabindex="-1">
      <span class="fui-MenuItem__checkmark fui-MenuItemCheckbox__checkmark" aria-hidden="true"><svg class="fui-Icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M14.05 3.49c.28.3.27.77-.04 1.06l-7.93 7.47A.85.85 0 0 1 4.9 12L2.22 9.28a.75.75 0 1 1 1.06-1.06l2.24 2.27 7.47-7.04a.75.75 0 0 1 1.06.04"/></svg></span>
      <span class="fui-MenuItem__icon fui-MenuItemCheckbox__icon" aria-hidden="true"></span>
      <span class="fui-MenuItem__content fui-MenuItemCheckbox__content">ルーラーを表示</span>
    </div>
  </div>
</div>
```

開いた状態の見本。グループの見出し、radio、無効、複数行、サブメニューを開いた項目を並べる。

```html demo
<div class="fui-MenuPopover" data-static role="presentation">
  <div class="fui-MenuList" role="menu" aria-label="表示">
    <div class="fui-MenuGroup" role="group" aria-labelledby="ov-menu-g1">
      <div class="fui-MenuGroupHeader" id="ov-menu-g1">並び順</div>
      <div class="fui-MenuItemRadio fui-MenuItem" role="menuitemradio" aria-checked="true" data-name="sort" tabindex="-1">
        <span class="fui-MenuItem__checkmark fui-MenuItemRadio__checkmark" aria-hidden="true"><svg class="fui-Icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M14.05 3.49c.28.3.27.77-.04 1.06l-7.93 7.47A.85.85 0 0 1 4.9 12L2.22 9.28a.75.75 0 1 1 1.06-1.06l2.24 2.27 7.47-7.04a.75.75 0 0 1 1.06.04"/></svg></span>
        <span class="fui-MenuItem__content fui-MenuItemRadio__content">名前</span>
      </div>
      <div class="fui-MenuItemRadio fui-MenuItem" role="menuitemradio" aria-checked="false" data-name="sort" tabindex="-1">
        <span class="fui-MenuItem__checkmark fui-MenuItemRadio__checkmark" aria-hidden="true"><svg class="fui-Icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M14.05 3.49c.28.3.27.77-.04 1.06l-7.93 7.47A.85.85 0 0 1 4.9 12L2.22 9.28a.75.75 0 1 1 1.06-1.06l2.24 2.27 7.47-7.04a.75.75 0 0 1 1.06.04"/></svg></span>
        <span class="fui-MenuItem__content fui-MenuItemRadio__content">更新日時</span>
      </div>
    </div>
    <div class="fui-MenuDivider" role="presentation"></div>
    <div class="fui-MenuItem" role="menuitem" tabindex="-1">
      <span class="fui-MenuItem__content">共有<span class="fui-MenuItem__subText">リンクを知っている人が表示できる</span></span>
    </div>
    <div class="fui-MenuItem" role="menuitem" tabindex="-1" aria-haspopup="menu" aria-expanded="true">
      <span class="fui-MenuItem__content">エクスポート</span>
      <span class="fui-MenuItem__submenuIndicator" aria-hidden="true"><svg class="fui-Icon fui-Icon-regular" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7.65 4.15c.2-.2.5-.2.7 0l5.49 5.46c.21.22.21.57 0 .78l-5.49 5.47a.5.5 0 0 1-.7-.71L12.8 10 7.65 4.85a.5.5 0 0 1 0-.7"/></svg><svg class="fui-Icon fui-Icon-filled" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7.73 4.2a.75.75 0 0 1 1.06.03l5 5.25c.28.3.28.75 0 1.04l-5 5.25a.75.75 0 1 1-1.08-1.04L12.2 10l-4.5-4.73a.75.75 0 0 1 .02-1.06"/></svg></span>
    </div>
    <div class="fui-MenuItem" role="menuitem" tabindex="-1" aria-disabled="true">
      <span class="fui-MenuItem__content">印刷</span>
      <span class="fui-MenuItem__secondaryContent">Ctrl+P</span>
    </div>
  </div>
</div>
```

### v9 との差と未確認の点

- MenuPopover は `popover` 属性で開き、位置はアンカー位置決めで近似する（Popover の節を参照）。v9 の既定の位置（below・start、サブメニューは after・top）は `position-area` に写した。
- サブメニューの開閉（hover の 500ms の遅延、右矢印で開く、左矢印で閉じる、safe zone）は `overlays.js` では扱わない。見た目（`aria-expanded="true"`）だけを用意した。
- 複数行の判定は `:has(.fui-MenuItem__subText)` で行う。v9 は `subText` の有無を state で見る。
- v9 で空の icon と checkmark を描いて揃えるのは、MenuList（または Menu）に `hasIcons`、`hasCheckmarks` を渡したときだけである（既定は false、`packages/react-components/react-menu/library/src/components/MenuList/useMenuList.ts:180-181`、`MenuItem/useMenuItemBase.tsx:104`）。ここではマークアップに空の `span` を書いて揃える。最初の見本は `hasIcons` を渡した v9 と同じ形である。MenuItemCheckbox と MenuItemRadio の checkmark は v9 が常に描く（`MenuItemCheckbox/useMenuItemCheckbox.tsx:49`）。
- `tools/verify/compare-b.html` の比較（2026-11-13）では、v9 の DOM のスロットに `fui-MenuItemCheckbox__*` と `fui-MenuItemRadio__*` も付くことを確かめ、見本に足した。アイコンの `display` だけが違う（土台の `.fui-Icon` が `inline-block`、v9 の react-icons は `inline`）。位置と大きさは一致した。
- MenuItemLink、MenuItemSwitch、MenuSplitGroup は扱っていない。
- Web Components v3 は `min-inline-size: 160px`、押下の背景 `colorNeutralBackground1Selected`、無効の背景 `colorNeutralBackgroundDisabled` である。v9 の値を採った。

## Tooltip

### 概要と使い分け（Do / Don't）

Tooltip は、対象の近くに出す短い補足である。役立つが必須でない、書式なしの文に限る。書式のある情報は Popover を使う。

- 対象の hover か focus で出て、離れるか blur で消える。対象から 4px 離す。
- Do: 有効な部品には何ができるかを短く書く。無効な部品には有効にする方法を書く。ラベルのない部品には名詞句を書く。
- Don't: システムからのフィードバックに使わない。完全な文でない限り句点を付けない。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

| 部品 | class | 要素と属性 | 出典 |
|---|---|---|---|
| content | `fui-Tooltip__content` | `div[popover="manual"]`、`role="tooltip"`、`id` | `packages/react-components/react-tooltip/library/src/components/Tooltip/useTooltipBase.tsx:77` |
| 矢印 | `fui-Tooltip__arrow`（作った class） | content の最初の子の `div` | `packages/react-components/react-tooltip/library/src/components/Tooltip/renderTooltip.tsx:12-28` |

- 対象とのつなぎ方は `relationship` で決まる。`description` なら対象に `aria-describedby`、`label` なら `aria-labelledby`（文字列なら `aria-label`）を付ける（`packages/react-components/react-tooltip/library/src/components/Tooltip/useTooltipBase.tsx:279-297`）。
- 表示の遅延 250ms、非表示の遅延 250ms である。別の Tooltip が出ていれば遅延 0 で出す。blur ではすぐ消し、Esc で消す（同 `:56-57,141-157,203,245-248`）。`data-fui-enhance` を付けると `overlays.js` がこの振る舞いを再現する。
- 位置の既定は above・center、offset 4px、矢印ありは 4 + 6 = 10px である（同 `:94-106`、`packages/react-components/react-tooltip/library/src/components/Tooltip/private/constants.ts:4`）。

### バリエーション

| 属性 | 値 | 既定 | v9 の props と出典 |
|---|---|---|---|
| `data-appearance` | `normal` / `inverted` | `normal` | `appearance`（`packages/react-components/react-tooltip/library/src/components/Tooltip/useTooltip.tsx:17`） |
| `data-with-arrow` | 有無 | なし | `withArrow`（`packages/react-components/react-tooltip/library/src/components/Tooltip/useTooltipBase.tsx:52`） |
| `data-positioning` | Popover と同じ | `above` | `positioning`（同 `:53`） |
| `data-show-delay`、`data-hide-delay` | ms | 250、250 | `showDelay`、`hideDelay`（同 `:56-57`） |

### 寸法（size ごとの表）

Tooltip の size は 1 つだけである（`packages/react-components/react-tooltip/library/src/components/Tooltip/useTooltipStyles.styles.ts:18-37`）。

| 対象 | 値 |
|---|---|
| 幅の上限 | 240px |
| 文字 | `fontSizeBase200`、`lineHeightBase200`、`overflow-wrap: break-word` |
| padding | `4px 11px 6px 11px`（5px 12px 7px 12px から線 1px を引いた値） |
| 線と角丸 | `1px solid colorTransparentStroke`、`borderRadiusMedium` |
| 影 | `drop-shadow(0 0 2px ambient) drop-shadow(0 4px 8px key)`（`shadow8` と同じ組） |
| 矢印 | 高さ 6px、一辺 8.484px（`:53`） |

### 色と状態（トークン名の表）

| appearance | 背景 | 文字 | 出典 |
|---|---|---|---|
| `normal` | `colorNeutralBackground1` | `colorNeutralForeground1` | `packages/react-components/react-tooltip/library/src/components/Tooltip/useTooltipStyles.styles.ts:30-31` |
| `inverted` | `colorNeutralBackgroundStatic` | `colorNeutralForegroundStaticInverted` | 同 `:48-51` |

### フォーカス・動き・ハイコントラスト

- フォーカス: Tooltip はフォーカスを受けない。輪は対象の部品が持つ。
- 動き: v9 の Tooltip には motion がない。`display` の切り替えだけで、その場で出し入れする（`packages/react-components/react-tooltip/library/src/components/Tooltip/useTooltipStyles.styles.ts:19,39-41`）。
- ハイコントラスト: `forced-colors` の規則はない。線の `colorTransparentStroke` が見える。

### 実装の例

hover と focus で出る Tooltip（`overlays.js` が必要）。

```html demo
<button type="button" class="fui-Button" aria-describedby="ov-tip-live">保存</button>
<div id="ov-tip-live" class="fui-Tooltip__content" popover="manual" role="tooltip" data-with-arrow data-fui-enhance><div class="fui-Tooltip__arrow" aria-hidden="true"></div>変更をこの端末に保存する</div>
```

開いた状態の見本。normal と inverted、矢印の有無。

```html demo
<div style="display:flex;flex-wrap:wrap;gap:24px;align-items:flex-start;padding:8px">
  <div class="fui-Tooltip__content" data-static role="tooltip">矢印なし</div>
  <div class="fui-Tooltip__content" data-static data-with-arrow role="tooltip"><div class="fui-Tooltip__arrow" aria-hidden="true"></div>矢印あり・above</div>
  <div class="fui-Tooltip__content" data-static data-with-arrow data-appearance="inverted" data-positioning="below" role="tooltip"><div class="fui-Tooltip__arrow" aria-hidden="true"></div>inverted・below</div>
</div>
```

### v9 との差と未確認の点

- `popover="manual"` で開き、`overlays.js` が遅延と blur と Esc を扱う。`popover="hint"` や `interestfor` のような新しい仕組みは、対応状況を確かめていないので使っていない。JS がないと Tooltip は出ない。
- 対象が画面から見えなくなったとき（v9 の `referenceHidden`）の `visibility: hidden` は、`data-hidden` 属性で写した。`overlays.js` はこの判定をしない。
- 位置と矢印は Popover と同じ近似である。
- Web Components v3 は padding が `4px 10px 6px` で、横が v9 より 1px 狭い。v9 の値を採った。

## Toast

### 概要と使い分け（Do / Don't）

Toast は、操作の結果や別の場所で起きたことを伝える一時的な面である。役に立つが重要ではない情報に使う。重要な通知は modal の Dialog か MessageBar、フィールドのエラーはフィールドに出す。

- 種類は、確認（操作の直後の成功、エラー、警告、情報）、進行（処理の状態）、コミュニケーション（メンションや返信など）である。
- 操作のない Toast は時間で消え、キーボードのフォーカスを受けない。位置はアプリ全体で揃える（多くは右上か右下）。
- Do: タイトルは短く要点に絞る。ボタンはタイトルに具体的に応える。
- Don't: 主内容を隠さない。4 つを超えて積まない。スピナーと進捗バーを同時に出さない。assertive な Toast を多用しない。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

| 部品 | class | 要素と属性 | 出典 |
|---|---|---|---|
| Toaster | `fui-Toaster` | `div`、`role="list"`。位置ごとに 1 つ | `packages/react-components/react-toast/library/src/components/Toaster/useToaster.tsx:50-72` |
| ToastContainer | `fui-ToastContainer`、`__timer` | `div`、`role="listitem"`、`tabindex="0"`、`aria-labelledby`（タイトル）、`aria-describedby`（本文） | `packages/react-components/react-toast/library/src/components/ToastContainer/useToastContainer.ts:206-209` |
| Toast | `fui-Toast` | `div`。`auto 1fr auto` の grid | `packages/react-components/react-toast/library/src/components/Toast/useToastStyles.styles.ts:12-24` |
| ToastTitle | `fui-ToastTitle`、`__media`、`__action` | media、タイトル、action を Toast の grid の直接の子として並べる | `packages/react-components/react-toast/library/src/components/ToastTitle/renderToastTitle.tsx:14-20` |
| ToastBody | `fui-ToastBody`、`__subtitle` | `div`。subtitle は ToastBody の中ではなく、直後の兄弟として Toast の grid に並べる | `packages/react-components/react-toast/library/src/components/ToastBody/renderToastBody.tsx:11-20`、`useToastBodyStyles.styles.ts:13-32` |
| ToastFooter | `fui-ToastFooter` | `div` | `packages/react-components/react-toast/library/src/components/ToastFooter/useToastFooterStyles.styles.ts:14-21` |
| 読み上げ | `fui-AriaLive__polite`、`fui-AriaLive__assertive` | `aria-live`。視覚的に隠す | `packages/react-components/react-toast/library/src/components/AriaLive/useAriaLiveStyles.styles.ts:15-23` |

- intent のアイコンは、success が `CheckmarkCircleFilled`、error が `DiamondDismissFilled`、warning が `WarningFilled`、info が `InfoFilled` である（`packages/react-components/react-toast/library/src/components/ToastTitle/useToastTitle.tsx:63-77`）。
- 読み上げは info だけ polite、ほかは assertive である（`packages/react-components/react-toast/library/src/components/ToastContainer/useToastContainer.ts:14-19`）。
- 既定は位置 `bottom-end`、timeout 3000ms、`pauseOnHover` false、上限なしである（`packages/react-components/react-toast/library/src/state/vanilla/createToaster.ts:20-31`）。bottom は末尾に、top は先頭に足す（`packages/react-components/react-toast/library/src/state/useToaster.ts:194-211`）。
- 時間は、見えない `span` に opacity 0 → 0 の animation を付け、その長さを timeout にして `animationend` で閉じる（`packages/react-components/react-toast/library/src/components/Timer/Timer.tsx`、`packages/react-components/react-toast/library/src/components/Timer/useTimerStyles.styles.ts:5-14`）。
- キーボード: Toaster で Esc を押すとすべて閉じ、上下の矢印で ToastContainer の間を移る（`packages/react-components/react-toast/library/src/components/Toaster/useToaster.tsx:36-46`、`packages/react-components/react-toast/library/src/components/Toaster/useToasterFocusManagement.ts:45-60`）。
- `overlays.js` の使い方: `<template>` に `.fui-Toast` を書き、ボタンに `data-fui-toast="<template の id>"`、`data-fui-toaster="<Toaster の id>"`、`data-fui-enhance` を付ける。ToastContainer、id、時間の `span`、読み上げは JS が作る。閉じるボタンには `data-fui-toast-dismiss` を付ける。

### バリエーション

| 属性 | 値 | 既定 | v9 と出典 |
|---|---|---|---|
| `data-intent`（Toast） | `info` / `success` / `error` / `warning` | なし | `intent`（`packages/react-components/react-toast/library/src/state/types.ts:11`） |
| `data-appearance`（Toast） | なし / `inverted` | なし | `appearance`（`packages/react-components/react-toast/library/src/components/Toast/useToastStyles.styles.ts:26-31,43`） |
| `data-position`（Toaster） | `top` / `bottom` / `top-start` / `top-end` / `bottom-start` / `bottom-end` | `bottom-end` | `position`（`packages/react-components/react-toast/library/src/state/vanilla/getPositionStyles.ts:25-66`） |
| `data-inline`（Toaster） | 有無 | なし | `inline`（`position: absolute`） |
| `data-timeout`（ボタンか Toaster） | ms（負の値は消えない） | 3000 | `timeout` |
| `data-pause-on-hover`、`data-limit`（Toaster） | 有無、数 | なし、無制限 | `pauseOnHover`、`limit` |

### 寸法（size ごとの表）

| 部品 | 値 | 出典 |
|---|---|---|
| Toaster | `position: fixed; width: 292px; pointer-events: none` | `packages/react-components/react-toast/library/src/components/Toaster/useToasterStyles.styles.ts:15-25` |
| Toaster の位置 | 上下から 16px、`*-start` は始端から 20px、`*-end` は終端から 20px、`top` と `bottom` は中央 | `packages/react-components/react-toast/library/src/state/vanilla/getPositionStyles.ts:17-66` |
| ToastContainer | `margin-top: 16px`、角丸 `borderRadiusMedium` | `packages/react-components/react-toast/library/src/components/ToastContainer/useToastContainerStyles.styles.ts:14-22` |
| Toast | `padding: 12px`、線 1px、角丸 `borderRadiusMedium`、影 `shadow8`、`fontSizeBase300`、`line-height: 20px`、Semibold | `packages/react-components/react-toast/library/src/components/Toast/useToastStyles.styles.ts:12-24` |
| media | 上 2px、終端側 8px、`font-size: 16px`、1 列目 | `packages/react-components/react-toast/library/src/components/ToastTitle/useToastTitleStyles.styles.ts:21-28` |
| action | 始端側 12px、3 列目 | 同 `:30-36` |
| ToastBody | 2 列目、上 6px、`body1` 相当（Regular） | `packages/react-components/react-toast/library/src/components/ToastBody/useToastBodyStyles.styles.ts:13-22` |
| subtitle | 上 4px、`fontSizeBase200`、`line-height: fontSizeBase200` | 同 `:24-32` |
| ToastFooter | 2 列目、上 16px、`gap: 14px` | `packages/react-components/react-toast/library/src/components/ToastFooter/useToastFooterStyles.styles.ts:14-21` |

### 色と状態（トークン名の表）

| 対象 | 通常 | inverted | 出典 |
|---|---|---|---|
| Toast の背景 | `colorNeutralBackground1` | `colorNeutralBackgroundInverted` | `packages/react-components/react-toast/library/src/components/Toast/useToastStyles.styles.ts:23,27-30` |
| Toast とタイトルと本文の文字 | `colorNeutralForeground1` | `colorNeutralForegroundInverted2` | 同 `:22,28`、`packages/react-components/react-toast/library/src/components/ToastTitle/useToastTitleStyles.styles.ts:17,39-41`、`packages/react-components/react-toast/library/src/components/ToastBody/useToastBodyStyles.styles.ts:20,35-37` |
| action | `colorBrandForeground1` | `colorBrandForegroundInverted` | `packages/react-components/react-toast/library/src/components/ToastTitle/useToastTitleStyles.styles.ts:35,43-45` |
| media（intent なし） | `colorNeutralForeground1` | `colorNeutralForegroundInverted` | 同 `:27,47-49` |
| subtitle | `colorNeutralForeground2` | `colorNeutralForegroundInverted2` | `packages/react-components/react-toast/library/src/components/ToastBody/useToastBodyStyles.styles.ts:31,38-40` |

| intent | media（通常） | media（inverted） | 出典 |
|---|---|---|---|
| `success` | `colorStatusSuccessForeground1` | `colorStatusSuccessForegroundInverted` | `packages/react-components/react-toast/library/src/components/ToastTitle/useToastTitleStyles.styles.ts:52-80` |
| `error` | `colorStatusDangerForeground1` | `colorStatusDangerForegroundInverted` | 同 |
| `warning` | `colorStatusWarningForeground1` | `colorStatusWarningForegroundInverted` | 同 |
| `info` | `colorNeutralForeground2` | `colorNeutralForegroundInverted2` | 同 |

intent は背景を変えない。変わるのはアイコンの色だけである。

<!-- spec:tokens-status -->

### フォーカス・動き・ハイコントラスト

- フォーカス: ToastContainer は輪ではなく `outline: strokeWidthThick solid colorStrokeFocus2` を持つ（`packages/react-components/react-toast/library/src/components/ToastContainer/useToastContainerStyles.styles.ts:19-21`）。
- 動き: ToastContainer を `CollapseDelayed` で包む（`packages/react-components/react-toast/library/src/components/ToastContainer/renderToastContainer.tsx:24`、`packages/react-components/react-motion-components-preview/library/src/components/Collapse/Collapse.ts:112-126`）。enter は高さを 200ms で広げ、200ms 遅れて opacity を 400ms で上げる。exit は opacity を 400ms で下げ、400ms 遅れて高さを 200ms で畳む。曲線はどちらも `curveEasyEase` である。高さと縦の margin・padding を 0 から動かす（`packages/react-components/react-motion-components-preview/library/src/components/Collapse/collapse-atoms.ts:24-127`）。
- CSS では `@keyframes` で写し、高さは `overlays.js` が測った `scrollHeight` を `--fui-ToastContainer--scroll-height` で渡す。
- 縮小モーションでは時間だけ 1ms にし、遅延は残す。退場は 400ms 待ってから畳む（v9 と同じ）。
- ハイコントラスト: `forced-colors` の規則はない。Toast の線が CanvasText になる。

### 実装の例

ボタンで Toast を出す（`overlays.js` が必要）。Toaster は画面の右下に固定される。

```html demo
<button type="button" class="fui-Button" data-appearance="primary" data-fui-toast="ov-toast-tpl" data-fui-toaster="ov-toaster" data-fui-enhance>保存する</button>
<template id="ov-toast-tpl">
  <div class="fui-Toast" data-intent="success">
    <div class="fui-ToastTitle__media" aria-hidden="true"><svg class="fui-Icon" width="16" height="16" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M10 2a8 8 0 1 1 0 16 8 8 0 0 1 0-16m3.36 5.65a.5.5 0 0 0-.64-.06l-.07.06L9 11.3 7.35 9.65l-.07-.06a.5.5 0 0 0-.7.7l.07.07 2 2 .07.06c.17.11.4.11.56 0l.07-.06 4-4 .07-.08a.5.5 0 0 0-.06-.63"/></svg></div>
    <div class="fui-ToastTitle">ファイルを保存しました</div>
    <div class="fui-ToastTitle__action"><button type="button" class="fui-Link" data-fui-toast-dismiss>閉じる</button></div>
  </div>
</template>
<div id="ov-toaster" class="fui-Toaster" role="list" data-position="bottom-end" data-fui-enhance></div>
```

開いた状態の見本。intent、本文と副題、フッター、inverted を並べる。

```html demo
<div class="fui-Toaster" data-static role="list">
  <div class="fui-ToastContainer" role="listitem" tabindex="0" aria-labelledby="ov-toast-s1-t" aria-describedby="ov-toast-s1-b">
    <div class="fui-Toast" data-intent="success">
      <div class="fui-ToastTitle__media" aria-hidden="true"><svg class="fui-Icon" width="16" height="16" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M10 2a8 8 0 1 1 0 16 8 8 0 0 1 0-16m3.36 5.65a.5.5 0 0 0-.64-.06l-.07.06L9 11.3 7.35 9.65l-.07-.06a.5.5 0 0 0-.7.7l.07.07 2 2 .07.06c.17.11.4.11.56 0l.07-.06 4-4 .07-.08a.5.5 0 0 0-.06-.63"/></svg></div>
      <div class="fui-ToastTitle" id="ov-toast-s1-t">報告書を送信しました</div>
      <div class="fui-ToastTitle__action"><button type="button" class="fui-Link">元に戻す</button></div>
      <div class="fui-ToastBody" id="ov-toast-s1-b">3 人に送った。</div>
      <div class="fui-ToastBody__subtitle">たった今</div>
      <div class="fui-ToastFooter"><button type="button" class="fui-Link">開く</button><button type="button" class="fui-Link">共有</button></div>
    </div>
  </div>
  <div class="fui-ToastContainer" role="listitem" tabindex="0" aria-labelledby="ov-toast-s2-t">
    <div class="fui-Toast" data-intent="error">
      <div class="fui-ToastTitle__media" aria-hidden="true"><svg class="fui-Icon" width="16" height="16" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7.88 1.88a3 3 0 0 1 4.24 0l6 6a3 3 0 0 1 0 4.24l-6 6a3 3 0 0 1-4.24 0l-6-6a3 3 0 0 1 0-4.24zM13.1 6.9a.5.5 0 0 0-.7 0L10 9.3 7.6 6.9a.5.5 0 0 0-.7.7L9.3 10l-2.4 2.4a.5.5 0 0 0 .7.7l2.4-2.4 2.4 2.4a.5.5 0 0 0 .7-.7L10.7 10l2.4-2.4a.5.5 0 0 0 0-.7"/></svg></div>
      <div class="fui-ToastTitle" id="ov-toast-s2-t">アップロードできませんでした</div>
    </div>
  </div>
  <div class="fui-ToastContainer" role="listitem" tabindex="0" aria-labelledby="ov-toast-s3-t">
    <div class="fui-Toast" data-intent="info" data-appearance="inverted" data-background-appearance="inverted">
      <div class="fui-ToastTitle__media" aria-hidden="true"><svg class="fui-Icon" width="16" height="16" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M18 10a8 8 0 1 0-16 0 8 8 0 0 0 16 0M9.5 8.91a.5.5 0 0 1 1 0v4.69a.5.5 0 0 1-1 0V8.9m-.25-2.16a.75.75 0 1 1 1.5 0 .75.75 0 0 1-1.5 0"/></svg></div>
      <div class="fui-ToastTitle" id="ov-toast-s3-t">新しい版があります</div>
      <div class="fui-ToastTitle__action"><button type="button" class="fui-Link">更新</button></div>
    </div>
  </div>
</div>
```

### v9 との差と未確認の点

- v9 の Toaster は React の状態で Toast を出し入れする。ここでは `overlays.js` が `<template>` を複製する。`data-state`（`entering` / `visible` / `exiting`）は JS が付ける補助の属性である。
- アイコンは v9 の大きさなしのアイコン（20 の形を 1em で描く）に合わせ、20 の SVG を 16px で描いている。
- `ToastTrigger`、進行の表示（ProgressBar と Spinner）、`pauseOnWindowBlur`、`priority`、ToastContainer の Tab と Enter の扱いは再現していない。
- 読み上げは、Toaster の後ろに `fui-AriaLive__*` の領域を作り、表示から 50ms 後に文字を入れる。v9 の announce の時機（`packages/react-components/react-toast/library/src/components/ToastContainer/useToastContainer.ts:175-182`）とは同じではない（推論）。
- サイトは操作のない Toast を 7 秒で消すと書くが、v9 の既定は 3000ms である。コードに従った。
- `data-static` の Toaster は流れの中に置く補助の規則である。Toast の action の `fui-Link` は actions の章の部品である。
- v9 の inverted の Toast は、中の Link に `BackgroundAppearanceContext` で inverted を伝える（Link は `colorBrandForegroundInverted` になる）。React を使わない HTML では、inverted の Toast に `data-background-appearance="inverted"` も書く。Link の CSS（第 10 章）がこの属性を祖先から読む。
- 以前の見本は `fui-ToastBody__subtitle` を ToastBody の中に入れていた。v9 は兄弟として描く（`packages/react-components/react-toast/library/src/components/ToastBody/renderToastBody.tsx:16-17`）ので直した。中に入れると ToastBody の高さが subtitle の分だけ増える。

## MessageBar

### 概要と使い分け（Do / Don't）

MessageBar は、製品全体か、それが置かれた面（ページ、Drawer、Dialog、カード）の状態について重要な情報を伝える帯である。破壊的な操作を防ぐなら Dialog、時間に敏感で別の場所の出来事なら Toast を使う。

- intent は info、success、warning、error である。warning と error にはボタンかリンクを置く。
- 内容は切り詰めず、幅が足りないと操作を本文の下に回す。複数あるときは error、warning、success、info の順に積む。
- Do: 最重要の情報を短く具体的なタイトルにする。本文は 1〜2 文にする。成功の通知は何が変わったかを書く。リンクは動詞で始め、行き先を表す。
- Don't: URL や「ここをクリック」をリンクの文にしない。重要な通知を出しすぎない。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

| 部品 | class | 要素と属性 | 出典 |
|---|---|---|---|
| MessageBar | `fui-MessageBar` | `div`、`role="group"`、`aria-labelledby` はタイトルの id | `packages/react-components/react-message-bar/library/src/components/MessageBar/useMessageBar.ts:50-58` |
| icon | `fui-MessageBar__icon` | `div`（既定で描く） | 同 `:59-62` |
| 下の余白 | `fui-MessageBar__bottomReflowSpacer` | 複数行のとき末尾に置く | 同 `:63-66` |
| MessageBarBody | `fui-MessageBarBody` | `div` | `packages/react-components/react-message-bar/library/src/components/MessageBarBody/useMessageBarBodyStyles.styles.ts:12-16` |
| MessageBarTitle | `fui-MessageBarTitle` | 本文の中の `span`（id を持つ） | `packages/react-components/react-message-bar/library/src/components/MessageBarTitle/useMessageBarTitleStyles.styles.ts:15-20` |
| MessageBarActions | `fui-MessageBarActions` | ボタンの群れ。ボタンは small | `packages/react-components/react-message-bar/library/src/components/MessageBarActions/useMessageBarActionsContextValues.ts:9` |
| containerAction | `fui-MessageBarActions__containerAction` | 閉じるボタンの置き場。複数行では Actions の前、単一行では後に描く | `packages/react-components/react-message-bar/library/src/components/MessageBarActions/renderMessageBarActions.tsx:24-26` |
| MessageBarGroup | `fui-MessageBarGroup` | 出入りの動きの範囲 | `packages/react-components/react-message-bar/library/src/components/MessageBarGroup/useMessageBarGroupStyles.styles.ts:5-7` |

- grid の領域は、単一行で `icon body secondaryActions actions`、複数行で `icon body actions` と `secondaryActions`（3 列にまたがる）である。
- intent のアイコンは、info が `InfoFilled`、warning が `WarningFilled`、error が `DiamondDismissFilled`、success が `CheckmarkCircleFilled` である（`packages/react-components/react-message-bar/library/src/components/MessageBar/getIntentIcon.tsx:6-19`）。
- 読み上げは、info なら polite、ほかは assertive で、本文と操作の文字を読む（`packages/react-components/react-message-bar/library/src/components/MessageBar/useMessageBar.ts:22-42`）。React を使わない HTML では、別の `aria-live` の領域に文字を入れる。
- MessageBar 自体はフォーカスを受けない。

### バリエーション

| 属性 | 値 | 既定 | v9 の props と出典 |
|---|---|---|---|
| `data-intent` | `info` / `success` / `warning` / `error` | `info` | `intent`（`packages/react-components/react-message-bar/library/src/components/MessageBar/useMessageBar.ts:22`） |
| `data-layout` | `auto` / `singleline` / `multiline` | `auto` | `layout`（同 `:22-26`）。`auto` は `data-fui-enhance` で `overlays.js` が `data-computed-layout` を付ける（`packages/react-components/react-message-bar/library/src/components/MessageBar/useMessageBarReflow.ts:19-63`） |
| `data-shape` | `rounded` / `square` | `rounded` | `shape`（`packages/react-components/react-message-bar/library/src/components/MessageBar/useMessageBar.ts:86`） |
| `data-animate`（MessageBarGroup） | `exit-only` / `both` | `exit-only` | `animate`（`packages/react-components/react-message-bar/library/src/components/MessageBarGroup/useMessageBarGroup.ts:45`） |

### 寸法（size ごとの表）

| 部品 | 値 | 出典 |
|---|---|---|
| MessageBar | `display: grid; grid-template-columns: auto 1fr auto auto`、始端側 12px、線 1px、角丸 `borderRadiusMedium`、`min-height: 36px`、`white-space: nowrap` | `packages/react-components/react-message-bar/library/src/components/MessageBar/useMessageBarStyles.styles.ts:14-27` |
| 複数行 | `white-space: normal; align-items: start; padding-top: 10px; grid-template-columns: auto 1fr auto` | 同 `:44-53` |
| square | `border-radius: 0` | 同 `:62-64` |
| icon | `fontSizeBase500`（20px）、終端側 8px | 同 `:29-36` |
| 下の余白 | `margin-bottom: 8px` | 同 `:38-41` |
| MessageBarTitle | `body1Strong`、後ろに空白 1 文字（`::after`） | `packages/react-components/react-message-bar/library/src/components/MessageBarTitle/useMessageBarTitleStyles.styles.ts:15-20` |
| MessageBarBody | `body1`、終端側 12px | `packages/react-components/react-message-bar/library/src/components/MessageBarBody/useMessageBarBodyStyles.styles.ts:12-16` |
| MessageBarActions | `display: flex; column-gap: 12px`、終端側 12px | `packages/react-components/react-message-bar/library/src/components/MessageBarActions/useMessageBarActionsStyles.styles.ts:16-21` |
| 複数行の Actions | 終端に寄せ、上 10px、下 8px、終端側の padding 12px | 同 `:28-35` |
| containerAction | 終端側 12px | 同 `:23-26` |

### 色と状態（トークン名の表）

| intent | 背景 | 線 | icon | 出典（`packages/react-components/react-message-bar/library/src/components/MessageBar/useMessageBarStyles.styles.ts`） |
|---|---|---|---|---|
| `info` | `colorNeutralBackground3` | `colorNeutralStroke1` | `colorNeutralForeground3` | `:21,26,33` |
| `error` | `colorStatusDangerBackground1` | `colorStatusDangerBorder1` | `colorStatusDangerForeground1` | `:71-73,86-89` |
| `warning` | `colorStatusWarningBackground1` | `colorStatusWarningBorder1` | `colorStatusWarningForeground3` | `:74-76,90-93` |
| `success` | `colorStatusSuccessBackground1` | `colorStatusSuccessBorder1` | `colorStatusSuccessForeground1` | `:77-79,94-97` |

文字色は MessageBar に指定がなく、親から受け継ぐ。

### フォーカス・動き・ハイコントラスト

- フォーカス: 中のボタンとリンクがそれぞれの輪を持つ。
- 動き: MessageBarGroup の中だけで動く。exit は opacity 1 → 0、enter は `data-animate="both"` のときだけ opacity と `translate: 0 -100%` → 0。どちらも 250ms（`durationGentle`）で、曲線の指定はなく atom の既定の `curveLinear` になる（`packages/react-components/react-message-bar/library/src/components/MessageBarGroup/MessageBarGroup.motions.tsx:11-26`）。CSS では `data-state="entering"` と `"exiting"` の `@keyframes` で写す。閉じるボタンに `data-fui-dismiss` を付けると、`overlays.js` が退場の動きのあとで外す。
- ハイコントラスト: `forced-colors` の規則はない。線の `colorNeutralStroke1` が CanvasText になる。

### 実装の例

4 つの intent（単一行）。

```html demo
<div style="display:flex;flex-direction:column;gap:8px">
  <div class="fui-MessageBar" role="group" aria-labelledby="ov-mb-1" data-layout="singleline">
    <div class="fui-MessageBar__icon" aria-hidden="true"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M18 10a8 8 0 1 0-16 0 8 8 0 0 0 16 0M9.5 8.91a.5.5 0 0 1 1 0v4.69a.5.5 0 0 1-1 0V8.9m-.25-2.16a.75.75 0 1 1 1.5 0 .75.75 0 0 1-1.5 0"/></svg></div>
    <div class="fui-MessageBarBody"><span class="fui-MessageBarTitle" id="ov-mb-1">お知らせ</span>今夜 22 時から保守を行う。</div>
    <div class="fui-MessageBarActions"><button type="button" class="fui-Button" data-size="small">詳細</button></div>
    <div class="fui-MessageBarActions__containerAction"><button type="button" class="fui-Button" data-appearance="transparent" data-size="small" data-icon-only aria-label="閉じる"><span class="fui-Button__icon"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="m4.09 4.22.06-.07a.5.5 0 0 1 .63-.06l.07.06L10 9.29l5.15-5.14a.5.5 0 0 1 .63-.06l.07.06c.18.17.2.44.06.63l-.06.07L10.71 10l5.14 5.15c.18.17.2.44.06.63l-.06.07a.5.5 0 0 1-.63.06l-.07-.06L10 10.71l-5.15 5.14a.5.5 0 0 1-.63.06l-.07-.06a.5.5 0 0 1-.06-.63l.06-.07L9.29 10 4.15 4.85a.5.5 0 0 1-.06-.63l.06-.07z"/></svg></span></button></div>
  </div>
  <div class="fui-MessageBar" role="group" aria-labelledby="ov-mb-2" data-intent="success" data-layout="singleline">
    <div class="fui-MessageBar__icon" aria-hidden="true"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M10 2a8 8 0 1 1 0 16 8 8 0 0 1 0-16m3.36 5.65a.5.5 0 0 0-.64-.06l-.07.06L9 11.3 7.35 9.65l-.07-.06a.5.5 0 0 0-.7.7l.07.07 2 2 .07.06c.17.11.4.11.56 0l.07-.06 4-4 .07-.08a.5.5 0 0 0-.06-.63"/></svg></div>
    <div class="fui-MessageBarBody"><span class="fui-MessageBarTitle" id="ov-mb-2">共有を有効にしました</span>チームの全員が編集できる。</div>
    <div class="fui-MessageBarActions"></div>
  </div>
  <div class="fui-MessageBar" role="group" aria-labelledby="ov-mb-3" data-intent="warning" data-layout="singleline">
    <div class="fui-MessageBar__icon" aria-hidden="true"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7.37 3.56a3 3 0 0 1 5.26 0l5.5 10A3 3 0 0 1 15.5 18h-11a3 3 0 0 1-2.63-4.44zM10 12.75a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5m0-6.25a.5.5 0 0 0-.5.5v4a.5.5 0 0 0 1 0V7a.5.5 0 0 0-.5-.5"/></svg></div>
    <div class="fui-MessageBarBody"><span class="fui-MessageBarTitle" id="ov-mb-3">接続が不安定です</span>変更が保存されない場合がある。</div>
    <div class="fui-MessageBarActions"><button type="button" class="fui-Button" data-size="small">再接続</button></div>
  </div>
  <div class="fui-MessageBar" role="group" aria-labelledby="ov-mb-4" data-intent="error" data-layout="singleline">
    <div class="fui-MessageBar__icon" aria-hidden="true"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7.88 1.88a3 3 0 0 1 4.24 0l6 6a3 3 0 0 1 0 4.24l-6 6a3 3 0 0 1-4.24 0l-6-6a3 3 0 0 1 0-4.24zM13.1 6.9a.5.5 0 0 0-.7 0L10 9.3 7.6 6.9a.5.5 0 0 0-.7.7L9.3 10l-2.4 2.4a.5.5 0 0 0 .7.7l2.4-2.4 2.4 2.4a.5.5 0 0 0 .7-.7L10.7 10l2.4-2.4a.5.5 0 0 0 0-.7"/></svg></div>
    <div class="fui-MessageBarBody"><span class="fui-MessageBarTitle" id="ov-mb-4">支払いに失敗しました</span>カードの有効期限を確かめる。</div>
    <div class="fui-MessageBarActions"><button type="button" class="fui-Button" data-size="small">更新</button></div>
  </div>
</div>
```

複数行と square。複数行では操作が本文の下に回り、閉じるボタンは右上に残る。

```html demo
<div class="fui-MessageBar" role="group" aria-labelledby="ov-mb-5" data-intent="warning" data-layout="multiline" data-shape="square" style="max-width:420px">
  <div class="fui-MessageBar__icon" aria-hidden="true"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M7.37 3.56a3 3 0 0 1 5.26 0l5.5 10A3 3 0 0 1 15.5 18h-11a3 3 0 0 1-2.63-4.44zM10 12.75a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5m0-6.25a.5.5 0 0 0-.5.5v4a.5.5 0 0 0 1 0V7a.5.5 0 0 0-.5-.5"/></svg></div>
  <div class="fui-MessageBarBody"><span class="fui-MessageBarTitle" id="ov-mb-5">ストレージの残りが少なくなっています</span>残りは 5% である。古いファイルを削除するか、容量を追加する。</div>
  <div class="fui-MessageBarActions__containerAction"><button type="button" class="fui-Button" data-appearance="transparent" data-size="small" data-icon-only aria-label="閉じる"><span class="fui-Button__icon"><svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="m4.09 4.22.06-.07a.5.5 0 0 1 .63-.06l.07.06L10 9.29l5.15-5.14a.5.5 0 0 1 .63-.06l.07.06c.18.17.2.44.06.63l-.06.07L10.71 10l5.14 5.15c.18.17.2.44.06.63l-.06.07a.5.5 0 0 1-.63.06l-.07-.06L10 10.71l-5.15 5.14a.5.5 0 0 1-.63.06l-.07-.06a.5.5 0 0 1-.06-.63l.06-.07L9.29 10 4.15 4.85a.5.5 0 0 1-.06-.63l.06-.07z"/></svg></span></button></div>
  <div class="fui-MessageBarActions"><button type="button" class="fui-Button" data-size="small">容量を追加</button><button type="button" class="fui-Button" data-size="small">ファイルを整理</button></div>
  <div class="fui-MessageBar__bottomReflowSpacer"></div>
</div>
```

### v9 との差と未確認の点

- `layout="auto"` の折り返しは、`data-fui-enhance` で `overlays.js` の ResizeObserver が判定する。JS がないと、属性なしの MessageBar は単一行のままである。
- 操作がないときの `display: none` は、v9 では children の有無で決める。ここでは `:empty` で判定する。空白の文字だけがあると `:empty` に当たらないので、空の Actions は `<div class="fui-MessageBarActions"></div>` と書く。
- 読み上げは v9 の共有の announce を使う。React を使わない HTML の例では `aria-live` の領域を置いていない。
- MessageBarGroup の入場の動きは、JS で足した MessageBar に `data-state="entering"` を付けたときだけ動く。`overlays.js` は入場の属性を自動では付けない。
- Web Components v3 は role が `status`、文字が `fontSizeBase200`、warning と error がパレットのトークン（DarkOrange、Red）である。v9 の値（`group`、`body1`、状態のトークン）を採った。

## 共通の土台に取り入れたこと

`tools/verify/compare-b.html` の比較（2026-11-13）で見つかった、土台の 2 つの違いを v9 に合わせた。

- `.fui-Icon` を react-icons の SVG の計算値（`display: inline`、`line-height: 0`、`flex-shrink: 1`）に合わせた。縦の ToolbarButton のアイコンが 24px のまま はみ出る違い（第 10 章）がなくなる。
- テーマの `color-scheme` の宣言を外した。v9 の FluentProvider は書かないので、ネイティブの `button` と `input` の UA の文字色が v9 と同じになる。
