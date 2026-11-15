# 色

色はすべてエイリアスのトークン（`--colorNeutralBackground1` などの CSS 変数）で指定する。グローバルの値（`grey`、ブランドの段階、shared の色）は、部品の CSS に直接書かない。状態は状態ごとのトークン（`Hover`、`Pressed`、`Selected`）で表し、明度を計算で変えない。ブランドを替えるときは、ブランドの段階の 16 個（`--fui-brand-10`〜`--fui-brand-160`）だけを上書きする。

値の基準は `webLightTheme` と `webDarkTheme`（`packages/tokens/src/themes/web/lightTheme.ts:5`、`packages/tokens/src/themes/web/darkTheme.ts:5`）である。以下、`packages/tokens/src/` の下のファイルは、リポジトリからの相対パスで書く。

## 3 つのパレット

Fluent 2 の色は neutral、shared、brand の 3 つのパレットに分かれる（サイトの color のページの要約）。

| パレット | 役割 | グローバル（値の元） | エイリアス（部品が使う名前） |
|---|---|---|---|
| neutral | 黒、白、灰。面、文字、レイアウトの土台。状態の変化の多くは中立色の濃さの変化で表す | `grey`（2〜98 を 2 刻みと 99）、`white`、`black`、各 Alpha（`packages/tokens/src/global/colors.ts:6-126`） | `colorNeutral*`、`colorSubtle*`、`colorTransparent*`、`colorStrokeFocus*`、`colorBackgroundOverlay`、`colorScrollbarOverlay` |
| shared | Microsoft 365 のアプリで共通の色。アバター、カレンダー、バッジなど、製品をまたいで再利用する部品に使う。semantic の色（危険、注意、肯定）もここに含む | 49 色 × 12 段（`packages/tokens/src/global/colors.ts:144-877`、段は `packages/tokens/src/types.ts:506-519`） | `colorPalette*`、`colorStatus*` |
| brand | 製品の色。製品の識別と、いまどの製品にいるかの手がかり。ボタン、CTA、選択状態に使う | `BrandVariants` の 16 段（`packages/tokens/src/types.ts:521-523`、既定は `brandWeb`） | 名前に `Brand` を含む `color*`、`colorNeutralStrokeAccessibleSelected` |

- 名前に Neutral を含んでも、ブランドの段階を参照するトークンがある（`colorNeutralForeground2BrandHover` など）。
- グローバルの値は CSS 変数にならない（`--grey14` はない）。ブランドの段階だけは、差し替えのために補助の変数 `--fui-brand-*` として出している。これは Fluent の公開トークンではない、この設計書の独自の変数である。

中立色の段階（生成物）。番号 N は、sRGB の 1 チャンネルの値を 255 で割った百分率にほぼ等しい（**推論**。例: `grey[14]` は `#242424`）。番号が大きいほど明るい。

<!-- spec:ramp-grey -->

## エイリアストークンの名前の読み方

名前は、おおむね `color` + 系統 + 役割 + 番号 + 修飾 + 状態 の順に並ぶ。ただし語順は一定ではない（`colorNeutralStrokeOnBrand2Hover` は修飾の後に番号が来る）。**名前は規則から組み立てず、`packages/tokens/src/types.ts` から写す。**

| 部分 | 値 | 意味 |
|---|---|---|
| 系統 | `Neutral`、`Brand`、`CompoundBrand`、`Subtle`、`Transparent`、`Palette<色名>`、`Status<意味>` | パレットと用途のまとまり |
| 役割 | `Foreground`、`Background`、`Stroke`（palette と status では `Border`）、`Stencil`、`Shadow` | 文字とアイコン、面、線、スケルトン、影 |
| 番号 | `Foreground1`〜`5`、`Background1`〜`8`、`Stroke1`〜`4` など | 1 が基本。文字と線は番号が上がるほど弱い。面は階層 |
| 修飾 | `Inverted`、`OnBrand`、`OnLight`、`Static`、`Disabled`、`Alpha`、`Link`、`Accessible`、`Contrast`、`Brand` | 置く面や性質（後述） |
| 状態 | なし（rest）、`Hover`、`Pressed`、`Selected` | 操作の状態。状態を持たないトークンもある |

修飾の意味:

- `Inverted`: 反転した面（`colorNeutralBackgroundInverted`）の上。light では白、dark では暗い色に入れ替わる。
- `OnBrand`: ブランドの面の上。
- `Static`: テーマで変わらない。明るい固定の面や暗い固定の面に置く。
- `OnLight`: 明るい固定の面の上のブランド色。
- `Accessible`: 隣の色に対して 3:1 を満たす線。
- `Brand`（中立のトークンに付くもの）: rest は中立色で、操作したときだけブランド色になる。

## ファミリーごとの意味と使いどころ

使用例は v9 の styles から取った。値の参照先は `packages/tokens/src/alias/lightColor.ts` と `packages/tokens/src/alias/darkColor.ts`（両ファイルは同じ行に同じトークンがある）。

### 文字（Foreground）

| ファミリー | 意味と使いどころ |
|---|---|
| `colorNeutralForeground1` | 主要な文字とアイコン。状態で変わらない。Button の既定の文字（`packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:41`） |
| `colorNeutralForeground2` | 二次の文字。subtle と transparent の Button の rest。hover 以降は Foreground1 の値に上がる |
| `colorNeutralForeground2Brand*` | 中立の文字が操作したときだけブランド色になる。subtle の Button のアイコン、MenuItem、Nav の選択 |
| `colorNeutralForeground3` | 三次の文字。補助の説明、Field の説明、Presence の offline |
| `colorNeutralForeground4` | 最も弱い文字。Input、Textarea、Combobox の placeholder |
| `colorNeutralForegroundDisabled` | 無効の文字 |
| `colorBrandForegroundLink*` | リンク。subtle のリンクは `colorNeutralForeground2Link*`、反転した面の上は `colorNeutralForegroundInvertedLink*` |
| `colorNeutralForegroundOnBrand` | ブランドの面の上の文字。light、dark とも白。primary の Button |
| `colorNeutralForegroundInverted*` | 反転した面の上の文字。Toast、Checkbox のチェックの印 |
| `colorNeutralForeground1Static`、`colorNeutralForegroundStaticInverted` | テーマで変わらない暗い文字、白い文字。黄色の Badge、Tooltip の inverted |
| `colorBrandForeground1` | ブランド色の文字とアイコン。Badge の outline、Divider の brand |
| `colorBrandForeground2*` | 淡いブランドの面（`colorBrandBackground2`）の上の文字。Badge の tint、Tag |
| `colorCompoundBrandForeground1*` | 操作部品の選択やチェックを示す小さな印。Checkbox の mixed、Radio の checked、Tab の選択アイコン |

### 面（Background）

| ファミリー | 意味と使いどころ |
|---|---|
| `colorNeutralBackground1` | 既定の面（light は白、dark は `grey[16]`）。Button、Card |
| `colorNeutralBackground2`〜`5` | 面の階層。番号が上がるほど沈む（light は 98、96、94、92。dark は 12、8、4、黒）。Card の別の面（2）、filled-darker の Input と MessageBar（3）、Nav（4）、Badge の informative（5） |
| `colorNeutralBackground6` | 軌道として面と見分ける塗り。ProgressBar の軌道、Avatar。dark では Background1 より明るい |
| `colorNeutralBackground7*` | rest と selected は透明で、hover と pressed だけ塗る |
| `colorSubtleBackground*` | rest は透明で、操作すると中立の塗りが出る。subtle の Button、MenuItem、Table の行 |
| `colorTransparentBackground*` | light、dark ではすべての状態で透明。ハイコントラストでだけ hover 以降に色が付く。outline と transparent の Button |
| `colorNeutralBackgroundDisabled` | 無効の面 |
| `colorNeutralBackgroundInverted*`、`colorNeutralBackgroundStatic` | 反転した面（Toast）、テーマで変わらない暗い面（Tooltip の inverted） |
| `colorBackgroundOverlay` | Dialog と OverlayDrawer の背後の幕 |
| `colorBrandBackground*` | ブランドの大きな塗り。primary の Button（`useButtonStyles.styles.ts:152-166`） |
| `colorCompoundBrandBackground*` | 操作部品のオンの塗り。Checkbox と Switch の checked、Slider、ProgressBar |
| `colorBrandBackground2*` | 淡いブランドの面。Badge の tint、Table の選択行、Tag |
| `colorNeutralStencil1`、`2` | Skeleton の塗り |

### 線（Stroke）

| ファミリー | 意味と使いどころ |
|---|---|
| `colorNeutralStrokeAccessible*` | 3:1 を満たす必要がある線。Input の下線、Checkbox と Radio の未チェックの枠、Switch の軌道。selected だけブランド色 |
| `colorNeutralStroke1*` | 操作部品の既定の枠線。Button、Input の枠、Card、Menu |
| `colorNeutralStroke2` | 区切り線。Divider、Menu の区切り、Table の行 |
| `colorNeutralStroke3` | 最も淡い区切り線。Divider の subtle |
| `colorNeutralStrokeDisabled` | 無効の枠線 |
| `colorBrandStroke1`、`colorBrandStroke2*` | ブランド色の線、淡いブランドの線 |
| `colorCompoundBrandStroke*` | 操作部品のフォーカスとチェックの線。Input の focus の下線、Radio の checked |
| `colorTransparentStroke*` | light、dark では透明で、ハイコントラストでだけ色が付く線。Button の focus の outline、filled の Input の枠 |
| `colorStrokeFocus1`、`colorStrokeFocus2` | フォーカスの輪。Focus2 が外側の濃い線、Focus1 が内側の線（light は Focus1 が白で Focus2 が黒、dark は逆） |
| `colorNeutralShadow*`、`colorBrandShadow*` | 影の色。`shadow2`〜`shadow64` に合成する（`packages/tokens/src/utils/createLightTheme.ts:30-31`） |

面の階層と文字の階層の見本。テーマを切り替えると、同じ変数名のまま値が入れ替わる。

```html demo
<div style="display:flex;flex-wrap:wrap;gap:8px">
  <div style="background:var(--colorNeutralBackground1);border:1px solid var(--colorNeutralStroke1);padding:12px;min-width:112px"><span class="fui-Text fui-Caption1">Background1</span></div>
  <div style="background:var(--colorNeutralBackground2);border:1px solid var(--colorNeutralStroke1);padding:12px;min-width:112px"><span class="fui-Text fui-Caption1">Background2</span></div>
  <div style="background:var(--colorNeutralBackground3);border:1px solid var(--colorNeutralStroke1);padding:12px;min-width:112px"><span class="fui-Text fui-Caption1">Background3</span></div>
  <div style="background:var(--colorNeutralBackground4);border:1px solid var(--colorNeutralStroke1);padding:12px;min-width:112px"><span class="fui-Text fui-Caption1">Background4</span></div>
  <div style="background:var(--colorNeutralBackground5);border:1px solid var(--colorNeutralStroke1);padding:12px;min-width:112px"><span class="fui-Text fui-Caption1">Background5</span></div>
  <div style="background:var(--colorNeutralBackground6);border:1px solid var(--colorNeutralStroke1);padding:12px;min-width:112px"><span class="fui-Text fui-Caption1">Background6</span></div>
</div>
<div style="display:grid;gap:4px;margin-top:12px">
  <span class="fui-Text" style="color:var(--colorNeutralForeground1)">Foreground1 主要な文字</span>
  <span class="fui-Text" style="color:var(--colorNeutralForeground2)">Foreground2 二次の文字</span>
  <span class="fui-Text" style="color:var(--colorNeutralForeground3)">Foreground3 補助の説明</span>
  <span class="fui-Text" style="color:var(--colorNeutralForeground4)">Foreground4 プレースホルダー</span>
  <span class="fui-Text" style="color:var(--colorNeutralForegroundDisabled)">ForegroundDisabled 無効</span>
  <span class="fui-Text" style="color:var(--colorBrandForeground1)">BrandForeground1 ブランド色の文字</span>
</div>
```

## 状態の色の規則

### 中立の面と線

`grey[N]` の N の差で読むと、規則が見える（値は `packages/tokens/src/alias/lightColor.ts:8-160`、`darkColor.ts:8-160`）。

| トークン | light（rest → Hover / Pressed / Selected） | dark（rest → Hover / Pressed / Selected） |
|---|---|---|
| `colorNeutralBackground1` | 白 → 96 / 88 / 92 | 16 → 24 / 12 / 22 |
| `colorNeutralBackground2` | 98 → 94 / 86 / 90 | 12 → 20 / 8 / 18 |
| `colorNeutralBackground3` | 96 → 92 / 84 / 88 | 8 → 16 / 4 / 14 |
| `colorNeutralBackground4` | 94 → 98 / 96 / 白 | 4 → 12 / 黒 / 10 |
| `colorNeutralBackground5` | 92 → 96 / 94 / 98 | 黒 → 8 / 2 / 6 |
| `colorSubtleBackground` | 透明 → 96 / 88 / 92 | 透明 → 22 / 18 / 20 |
| `colorNeutralStroke1` | 82 → 78 / 70 / 74 | 40 → 46 / 42 / 44 |
| `colorNeutralStrokeAccessible` | 38 → 34 / 30 / brand 80 | 68 → 74 / 70 / brand 100 |
| `colorNeutralForeground2` | 26 → 14 / 14 / 14 | 84 → 白 / 白 / 白 |
| `colorNeutralForeground3` | 38 → 26 / 26 / 26 | 68 → 84 / 84 / 84 |

- light の面（Background1〜3、Subtle、Stroke1）は、hover で 4 暗く、pressed で 12 暗く、selected はその間（8 暗い）。
- light の Background4、5 は逆で、操作すると明るくなる。
- dark の面は、hover で 8 明るく、pressed で 4 暗く、selected で 6 明るい。light を裏返したものではない。
- 二次と三次の文字は、操作中に 1 段強い文字に上がる。Foreground1 は変わらない。
- このように向きが一様でないので、**明度の計算で状態を作らず、必ず状態のトークンを使う**。

### ブランドの状態

| トークン | light（rest → Hover / Pressed / Selected） | dark |
|---|---|---|
| `colorBrandBackground` | 80 → 70 / 40 / 60 | 70 → 80 / 40 / 60 |
| `colorCompoundBrandBackground` | 80 → 70 / 60 | 100 → 110 / 90 |
| `colorBrandForegroundLink` | 70 → 60 / 40 / 70 | 100 → 110 / 90 / 100 |
| `colorBrandBackground2` | 160 → 150 / 130 | 20 → 40 / 10 |

light では操作するほど番号を下げる（暗くする）。dark の `colorBrandBackground` は hover で明るくなり、pressed で 40 まで暗くなる。

### 状態の当て方

- **pressed**: v9 の Button は `':hover:active,:active:focus-visible'` に pressed の色を当てる（`useButtonStyles.styles.ts:55`）。キーボードで押したときも pressed の色になる。React を使わない CSS でも同じセレクターにする。
- **selected**: `aria-selected="true"`、`aria-pressed="true"`、`aria-checked="true"` などの ARIA で当てる。
- **disabled**: 状態のトークンではなく `*Disabled` のトークンに置き換え、hover と pressed でも同じ色にする。v9 の Button は `colorNeutralBackgroundDisabled`、`colorNeutralStrokeDisabled`、`colorNeutralForegroundDisabled` を使い、`cursor: not-allowed` にする（`useButtonStyles.styles.ts:322-369`）。
- **focus**: 色の状態を持たない。`colorStrokeFocus2` の輪で示す（「コンテンツデザインとアクセシビリティ」の章）。

```html demo
<div style="display:grid;grid-template-columns:auto repeat(4,1fr);gap:4px;align-items:center;max-width:560px">
  <span class="fui-Text fui-Caption1"></span>
  <span class="fui-Text fui-Caption1Strong">rest</span><span class="fui-Text fui-Caption1Strong">Hover</span><span class="fui-Text fui-Caption1Strong">Pressed</span><span class="fui-Text fui-Caption1Strong">Selected</span>
  <span class="fui-Text fui-Caption1">NeutralBackground1</span>
  <span style="height:32px;background:var(--colorNeutralBackground1);border:1px solid var(--colorNeutralStroke2)"></span>
  <span style="height:32px;background:var(--colorNeutralBackground1Hover)"></span>
  <span style="height:32px;background:var(--colorNeutralBackground1Pressed)"></span>
  <span style="height:32px;background:var(--colorNeutralBackground1Selected)"></span>
  <span class="fui-Text fui-Caption1">SubtleBackground</span>
  <span style="height:32px;background:var(--colorSubtleBackground);border:1px dashed var(--colorNeutralStroke2)"></span>
  <span style="height:32px;background:var(--colorSubtleBackgroundHover)"></span>
  <span style="height:32px;background:var(--colorSubtleBackgroundPressed)"></span>
  <span style="height:32px;background:var(--colorSubtleBackgroundSelected)"></span>
  <span class="fui-Text fui-Caption1">BrandBackground</span>
  <span style="height:32px;background:var(--colorBrandBackground)"></span>
  <span style="height:32px;background:var(--colorBrandBackgroundHover)"></span>
  <span style="height:32px;background:var(--colorBrandBackgroundPressed)"></span>
  <span style="height:32px;background:var(--colorBrandBackgroundSelected)"></span>
</div>
```

## ブランドの段階

`BrandVariants` は 10〜160 の 16 段で、10 が最も暗く、160 が最も明るい（`packages/tokens/src/types.ts:521-523`）。既定の Web のブランドは `brandWeb` で、基準の段階 80 は `#0f6cbd` である（`packages/tokens/src/global/brandColors.ts:3-20`、80 は `:11`）。

<!-- spec:ramp-brand -->

どの段階をどのトークンが参照するか（`lightColor.ts` と `darkColor.ts` の `brand[N]` を逆引きした）:

- light の中心は 80（塗り、文字、印、枠）と 70（hover、リンク）。淡い面は 150〜160、淡い線は 140。
- dark の中心は 100（文字、印、リンク）と 110（hover）。ただし `colorBrandBackground` は 70 で、白い文字（`colorNeutralForegroundOnBrand`）とのコントラストを保つ。淡い面は 10〜40 の暗い段階に移る。
- `colorBrandBackgroundStatic`、`colorBrandForegroundOnLight*`、`colorBrandBackground3Static`、`colorBrandBackground4Static`、`colorBrandBackgroundInverted*` は light と dark で同じ段階を使う。
- `fluent2.css` の既定（Fluent の `createLightTheme` と `createDarkTheme`）では、light で 10、20、90 を、dark で 120 を、どのトークンも参照しない。`scripts/brand_ramp.py` の既定の出力を読むと、dark の `colorBrandForeground2` が 120 を参照するようになる（下の「16 段の作り方」）。

**注意**: 生成された `packages/tokens/src/alias/lightColor.ts` の行末のコメントにある hex は、`brandWeb` の値ではない。たとえば `colorBrandBackground: brand[80]` のコメントは `#0078d4` だが（`lightColor.ts:124`）、`brandWeb[80]` は `#0f6cbd` である。値は必ず `brandColors.ts` から取る。

16 段の作り方: テーマデザイナー（`packages/react-components/theme-designer/src/utils/getBrandTokensFromPalette.ts:26-38`）は、キーの色を LCH に変換し、黒からキーの色、キーの色から白への 2 本のベジェ曲線を LAB 空間に作り、そこから 16 点を明度で取る。この方式では、キーの色そのものが 16 段のどれかに一致する保証はない。

1 つのキーの色から 16 段を作るには、`scripts/brand_ramp.py`（依存なしの Python 3.11 以降）を使う。Fluent UI のテーマデザイナー（`packages/react-components/theme-designer/src/utils/getBrandTokensFromPalette.ts`）と同じ計算で、テーマデザイナーの画面と同じ入力から同じ 16 段を出す。本物のテーマデザイナーのコードと 4,850 通りの入力（485 色 × 10 組の目盛り。全 360 の色相を含む）で照らし、全段が一致した。

```bash
python scripts/brand_ramp.py "#5b5fc7"
```

- 出力は CSS の規則 1 つで、指定のセレクター（既定 `:root`）に 16 個の `--fui-brand-*` と、ダークの切り替えの変数 `--fui-dark-mapping-designer` を宣言する。`fluent2.css` の後に読む CSS に貼る。`fluent2.css` の既定の 16 段は `:where(:root)`（詳細度 0）で宣言してあるので、どのセレクターでも上書きできる。
- `--vibrancy` と `--hue-torsion` は、テーマデザイナーの画面の「Vibrancy」と「Hue torsion」と同じ目盛り（-50〜50 の整数、既定 0）である。画面と同じく整数だけを受け付ける。
- ダークの文字のブランド色は、既定でテーマデザイナーの書き出しと同じ段にする（`colorBrandForeground1` を 110、`colorBrandForeground2` を 120。`theme-designer/src/utils/getOverridableTokenBrandColors.ts:70-76`）。仕組みは次のとおり。
  - `fluent2.css` のダークの規則は、`--fui-dark-designer-colorBrandForeground1: var(--fui-dark-mapping-designer) var(--fui-brand-110)` と、`--colorBrandForeground1: var(--fui-dark-designer-colorBrandForeground1, var(--fui-brand-100))` を宣言する（`colorBrandForeground2` も同じ形で 120 と 110）。
  - 切り替えの変数が空の値（`--fui-dark-mapping-designer: ;`）のときだけ 1 行目が有効になり、110 の段が使われる。宣言がないか `initial` なら 1 行目は無効になり、Fluent の `createDarkTheme` の段（100）に戻る。
  - 受け継がれるのは切り替えだけで、色はダークの規則を宣言する要素ごとに、その要素のブランドの段から決まる。そのため、規則が当たる要素の中の入れ子の `data-theme="dark"` と `data-theme="auto"`（OS がダークのとき）にも届き、内側で 16 段だけを差し替えた区画でも、その区画のブランドの段が使われる。
  - Fluent の `createDarkTheme` のまま（100 と 110）にするなら `--dark-mapping fluent` を付ける。このとき切り替えを `initial` にし、外側の区画がオンにしていても打ち消す。
- 区画だけを替えるときは `--selector ".my-section"` のように、`data-theme` を付けた要素を指すセレクターを渡す。カンマで区切った複数のセレクターも使える。`data-theme` のない要素を指しても、その要素ではトークンが宣言し直されないので効かない。
- `--format json` で、16 段とコントラストの確認の結果を JSON で出す。
- 標準エラーに、ライトとダークの 3 組ずつのコントラスト比を出す（ブランドの文字と背景、ブランドの文字と淡いブランドの面、ブランドの面と白い文字）。4.5:1 に届かない組があると、終了コード 2 で終わる。届かないときは、キーの色を濃く（ライト）か明るく（ダーク）するか、`--vibrancy` を変えて作り直す。
- テーマデザイナーの方式では、キーの色そのものが 16 段のどれかに入るとは限らない。Fluent の既定の `brandWeb` も、キーの色 `#0F6CBD` からこの計算で作ったものではない（手で調整した値）。

### ブランドの差し替え

`fluent2-tokens.css` は、ブランドの段階を `:root` の補助の変数 `--fui-brand-10`〜`--fui-brand-160` に置き、ブランドを参照するエイリアスを `var(--fui-brand-80)` の形で宣言している。ブランドを替えるときは、この 16 個だけを上書きする。

- **ページ全体**: `:root` で 16 個を上書きする。
- **一部の区画**: エイリアスを宣言し直す要素、つまり `data-theme` を付けた要素で 16 個を上書きする。エイリアスは宣言した要素で値が決まり、子はその結果を継ぐだけである。`data-theme` のない要素（`.fui-FluentProvider` だけの要素を含む）で `--fui-brand-80` を変えても、子孫のエイリアスは変わらない。`.fui-FluentProvider` は既定のスタイルだけを当て、トークンを宣言し直さない。
- **エイリアスの参照先は変えない**（light は 80 中心、dark は 100 中心、dark の `colorBrandBackground` は 70）。例外は、テーマデザイナーと同じくダークの文字のブランド色を 110 と 120 にすることで、これは切り替えの変数 `--fui-dark-mapping-designer` で行う（`scripts/brand_ramp.py` の既定）。
- 16 段は丸ごと替える。1 段だけ替えると、hover や淡い面との関係が崩れる。
- 替えたら、少なくとも `colorBrandForeground1` 対 `colorNeutralBackground1` と、`colorBrandForeground2` 対 `colorBrandBackground2` が 4.5:1 を満たすかを確かめる。テーマデザイナーが有効にしている検査はこの 2 組である（`packages/react-components/theme-designer/src/components/ColorTokens/AccessiblePairs.ts:47-48`）。白い文字を載せる `colorBrandBackground` と `colorNeutralForegroundOnBrand` の組も確かめる（この組の検査はテーマデザイナーではコメントアウトされている）。

```css
/* ページ全体のブランドを替える */
:root {
  --fui-brand-10: #061724;
  /* … 20〜150 … */
  --fui-brand-160: #ebf3fc;
}
```

次の例は、`brandTeams`（`packages/tokens/src/global/brandColors.ts:22-39`）の 16 段で、区画のブランドを差し替えたものである。左はライト、右はダークで、同じ 16 個から両方のテーマのエイリアスが決まる。

```html demo
<style>
  .demo-brand-teams {
    --fui-brand-10: #2b2b40; --fui-brand-20: #2f2f4a; --fui-brand-30: #333357; --fui-brand-40: #383966;
    --fui-brand-50: #3d3e78; --fui-brand-60: #444791; --fui-brand-70: #4f52b2; --fui-brand-80: #5b5fc7;
    --fui-brand-90: #7579eb; --fui-brand-100: #7f85f5; --fui-brand-110: #9299f7; --fui-brand-120: #aab1fa;
    --fui-brand-130: #b6bcfa; --fui-brand-140: #c5cbfa; --fui-brand-150: #dce0fa; --fui-brand-160: #e8ebfa;
  }
</style>
<div style="display:flex;flex-wrap:wrap;gap:12px">
  <div class="demo-brand-teams" data-theme="light" style="padding:16px;display:grid;gap:8px;min-width:220px">
    <span class="fui-Text fui-Body1Strong" style="background:var(--colorBrandBackground);color:var(--colorNeutralForegroundOnBrand);padding:6px 12px;border-radius:var(--borderRadiusMedium)">BrandBackground</span>
    <span class="fui-Text fui-Body1" style="color:var(--colorBrandForeground1)">BrandForeground1 の文字</span>
    <span class="fui-Text fui-Caption1Strong" style="background:var(--colorBrandBackground2);color:var(--colorBrandForeground2);padding:2px 8px;border-radius:var(--borderRadiusMedium)">BrandBackground2 と BrandForeground2</span>
  </div>
  <div class="demo-brand-teams" data-theme="dark" style="padding:16px;display:grid;gap:8px;min-width:220px">
    <span class="fui-Text fui-Body1Strong" style="background:var(--colorBrandBackground);color:var(--colorNeutralForegroundOnBrand);padding:6px 12px;border-radius:var(--borderRadiusMedium)">BrandBackground</span>
    <span class="fui-Text fui-Body1" style="color:var(--colorBrandForeground1)">BrandForeground1 の文字</span>
    <span class="fui-Text fui-Caption1Strong" style="background:var(--colorBrandBackground2);color:var(--colorBrandForeground2);padding:2px 8px;border-radius:var(--borderRadiusMedium)">BrandBackground2 と BrandForeground2</span>
  </div>
</div>
```

## shared の色

shared の色は 49 色で、各色が `shade50`〜`shade10`、`primary`、`tint10`〜`tint60` の 12 段を持つ（`packages/tokens/src/types.ts:506-519`）。エイリアスで使う色は名前の一覧で決まっている（`packages/tokens/src/sharedColorNames.ts`）。

| 集合 | 色 | 出典 |
|---|---|---|
| status（7 色） | red、green、darkOrange、yellow、berry、lightGreen、marigold | `sharedColorNames.ts:2-10` |
| persona（28 色） | darkRed、cranberry、pumpkin、peach、gold、brass、brown、forest、seafoam、darkGreen、lightTeal、teal、steel、blue、royalBlue、cornflower、navy、lavender、purple、grape、lilac、pink、magenta、plum、beige、mink、platinum、anchor | `sharedColorNames.ts:13-42` |
| semantic の写像先（3 色） | success → green、warning → orange、danger → cranberry | `packages/tokens/src/statusColorMapping.ts:3-7` |
| エイリアスで使わない色（14 色） | burgundy、bronze、orange（semantic の写像でだけ使う）、darkBrown、lime、darkTeal、cyan、lightBlue、darkBlue、darkPurple、orchid、hotPink、silver、charcoal | `sharedColorNames.ts:48-63` |

shared の色の全段（グローバル、生成物）:

<!-- spec:tokens-shared -->

### palette のトークン

`colorPalette<色名><役割>` は shared の色から作る。light は淡い tint を面、暗い shade を文字に使い、dark はこれを入れ替える（サイトの「dark では彩度と明度を変える」に当たる）。

| 役割 | light | dark | 持つ色 |
|---|---|---|---|
| `Background1` | tint60 | shade40 | status の 7 色 |
| `Background2` | tint40 | shade30 | status と persona |
| `Background3` | primary | primary | status の 7 色 |
| `Foreground1` | shade10 | tint30 | status の 7 色 |
| `Foreground2` | shade30 | tint40 | status と persona |
| `Foreground3` | primary | tint20 | status の 7 色 |
| `BorderActive` | primary | tint30 | status と persona |
| `Border1` | tint40 | primary | status の 7 色 |
| `Border2` | primary | tint20 | status の 7 色 |

出典は `packages/tokens/src/alias/lightColorPalette.ts:14-40`、`packages/tokens/src/alias/darkColorPalette.ts:16-55`。個別の上書きがある（light の `colorPaletteYellowForeground1` は shade30、dark の Red と DarkOrange の `Foreground3`・`Border2` は tint30 など）ので、値は生成物の表で確かめる。

<!-- spec:tokens-palette -->

### コンポーネントでの使い分け

同じ「警告」でも、部品ごとに使う色が違う。React を使わない CSS でも、元の styles のトークンをそのまま写す。

| 部品 | 使う色 | 出典 |
|---|---|---|
| MessageBar、Toast | `colorStatus*`（semantic） | `packages/react-components/react-message-bar/library/src/components/MessageBar/useMessageBarStyles.styles.ts:72-96` |
| Badge | danger → Red、severe → DarkOrange、success → Green、warning → Yellow | `packages/react-components/react-badge/library/src/components/Badge/useBadgeStyles.styles.ts:111-142` |
| Field の検証 | error → `colorPaletteRedForeground1`、warning → `colorPaletteDarkOrangeForeground1`、success → `colorPaletteGreenForeground1` | `packages/react-components/react-field/library/src/components/Field/useFieldStyles.styles.ts:112-118` |
| Presence | busy → Red、away → Marigold、available → LightGreen、out of office → Berry | `packages/react-components/react-badge/library/src/components/PresenceBadge/usePresenceBadgeStyles.styles.ts:51-67` |
| Avatar の色付き | persona の `Background2`（面）、`Foreground2`（文字）、`BorderActive`（輪） | `packages/react-components/react-avatar/library/src/components/Avatar/useAvatarStyles.styles.ts:262` 以下 |

## status の色

`colorStatus<Success、Warning、Danger><役割>` は、semantic の写像先（green、orange、cranberry）から作る（`packages/tokens/src/alias/lightColorPalette.ts:54-77`、`packages/tokens/src/alias/darkColorPalette.ts:65-90`）。役割は palette の status の色と同じ一式に `ForegroundInverted` を加えたもので、Danger だけが `Background3Hover` と `Background3Pressed` を持つ（`packages/tokens/src/types.ts:198-234`）。

- semantic の色は、フィードバック、状態、緊急度を伝える大事なメッセージにだけ使う。赤は危険、黄（橙）は注意、緑は肯定を表す。
- 色だけで意味を伝えず、必ずアイコンか文字を添える。
- semantic の色を飾りに使わない。

<!-- spec:tokens-status -->

色の組み方の見本（MessageBar そのものではない。面に `Background1`、枠に `Border1`、印の文字に `Foreground1` を使う組み合わせを示す）。

```html demo
<div style="display:grid;gap:8px;max-width:560px">
  <div style="background:var(--colorStatusDangerBackground1);border:1px solid var(--colorStatusDangerBorder1);border-radius:var(--borderRadiusMedium);padding:8px 12px">
    <span class="fui-Text fui-Body1Strong" style="color:var(--colorStatusDangerForeground1)">エラー</span>
    <span class="fui-Text fui-Body1">ファイルを保存できませんでした。ネットワークの接続を確かめてください。</span>
  </div>
  <div style="background:var(--colorStatusWarningBackground1);border:1px solid var(--colorStatusWarningBorder1);border-radius:var(--borderRadiusMedium);padding:8px 12px">
    <span class="fui-Text fui-Body1Strong" style="color:var(--colorStatusWarningForeground1)">警告</span>
    <span class="fui-Text fui-Body1">ストレージの残りが 10% を切りました。</span>
  </div>
  <div style="background:var(--colorStatusSuccessBackground1);border:1px solid var(--colorStatusSuccessBorder1);border-radius:var(--borderRadiusMedium);padding:8px 12px">
    <span class="fui-Text fui-Body1Strong" style="color:var(--colorStatusSuccessForeground1)">完了</span>
    <span class="fui-Text fui-Body1">3 件のファイルを共有しました。</span>
  </div>
</div>
```

## ダーク

- ダークは `webDarkTheme` の値で、エイリアスの名前は light と同じである。スタイルの規則は変えず、変数の値だけを入れ替える。
- `fluent2-tokens.css` では、`data-theme="dark"` を付けた要素でダークの値を宣言する。`data-theme="auto"` は `prefers-color-scheme` に従う。区画ごとに入れ子にしてよい。
- テーマを切り替える要素（`[data-theme]`）と `.fui-FluentProvider` には、`fluent2-base.css` が `color` と `background-color` を当て直す。変数だけを替えても、継承された `color` の計算値は親のままになるためである。
- ダークの要点:
    - 面は `grey[16]` を基準に、2〜5 で暗く沈む（16、12、8、4、黒）。`colorNeutralBackground6` は Background1 より明るい。
    - ブランドの文字と印は 100 中心に明るくなる。`colorBrandBackground` は 70 で、白い文字とのコントラストを保つ。
    - palette と status は shade を面、tint を文字にする。
    - 影の不透明度は light の約 2 倍になる（`colorNeutralShadowAmbient` は 0.12 から 0.24。`packages/tokens/src/alias/darkColor.ts:184-189`）。
    - `colorStrokeFocus1` と `colorStrokeFocus2` は light と逆になる（Focus2 が白）。

```html demo
<div style="display:flex;flex-wrap:wrap;gap:12px">
  <div data-theme="light" style="padding:16px;min-width:220px;display:grid;gap:4px;border:1px solid var(--colorNeutralStroke1)">
    <span class="fui-Text fui-Subtitle2">ライト</span>
    <span class="fui-Text" style="color:var(--colorNeutralForeground2)">二次の文字</span>
    <span class="fui-Text" style="color:var(--colorNeutralForeground3)">補助の説明</span>
    <span class="fui-Text" style="color:var(--colorBrandForegroundLink)">リンクの色</span>
    <span class="fui-Text fui-Caption1Strong" style="background:var(--colorPaletteRedBackground2);color:var(--colorPaletteRedForeground2);padding:2px 8px;justify-self:start">Red の Background2</span>
  </div>
  <div data-theme="dark" style="padding:16px;min-width:220px;display:grid;gap:4px;border:1px solid var(--colorNeutralStroke1)">
    <span class="fui-Text fui-Subtitle2">ダーク</span>
    <span class="fui-Text" style="color:var(--colorNeutralForeground2)">二次の文字</span>
    <span class="fui-Text" style="color:var(--colorNeutralForeground3)">補助の説明</span>
    <span class="fui-Text" style="color:var(--colorBrandForegroundLink)">リンクの色</span>
    <span class="fui-Text fui-Caption1Strong" style="background:var(--colorPaletteRedBackground2);color:var(--colorPaletteRedForeground2);padding:2px 8px;justify-self:start">Red の Background2</span>
  </div>
</div>
```

## ハイコントラスト

**Web の標準の経路は OS の強制カラー（`@media (forced-colors: active)`）であり、固定の色のテーマではない。**

- Web Components の文書は、ハイコントラストのテーマを使わないよう求めている。どのコンポーネントも、テーマに関係なく Windows のハイコントラストのモードに自動で対応するからで、固定の値のハイコントラストのテーマは旧式とされる（`packages/web-components/src/_docs/developer/theming.mdx:56-61`）。
- Web 用のハイコントラストのテーマは公開されていない。公開されているのは `teamsHighContrastTheme` だけである（`packages/tokens/src/themes/teams/highContrastTheme.ts:5-8`）。
- `createHighContrastTheme` のトークンは、**本来はシステムカラーを指す**。`packages/tokens/src/alias/highContrastColor.ts` のコメントには、各トークンが模すシステムカラーの名前（`CanvasText`、`Highlight` など）が書いてある。ただし値は固定の hex である（`hcCanvas` = `#000000`、`hcCanvasText` = `#ffffff`、`hcHighlight` = `#1aebff`、`hcHighlightText` = `#000000`、`hcHyperlink` = `#ffff00`、`hcDisabled` = `#3ff23f`、`hcButtonFace` = `#ffffff`、`hcButtonText` = `#000000`。`packages/tokens/src/global/colors.ts:128-142`）。黒い背景の配色を模したもので、利用者の OS の配色には追従しない。
- `fluent2-tokens.css` の `data-theme="high-contrast"` は、この固定の値である。見た目の確認や、Teams のように自前でハイコントラストを描くアプリのための**近似**として扱い、アクセシビリティの対応の代わりにしない。下の全値の表のハイコントラストの列には、値と、そのトークンが模すシステムカラーの名前を並べている。

トークンの写像の規則（`highContrastColor.ts`）と、強制カラーで部品の CSS が使うシステムカラーの対応:

| 役割 | 対応するシステムカラー | トークンの例 |
|---|---|---|
| 面の rest | `Canvas` | `colorNeutralBackground1`、`colorStrokeFocus1` |
| 文字と線の rest | `CanvasText` | `colorNeutralForeground1`、`colorNeutralStroke1`、`colorTransparentStroke` |
| 操作中の面、フォーカス、チェック | `Highlight` | `colorNeutralBackground1Hover`、`colorStrokeFocus2`、`colorCompoundBrandBackground` |
| 操作中の文字 | `HighlightText` | `colorNeutralForeground1Hover` |
| リンク | `LinkText` | `colorBrandForegroundLink` |
| 無効 | `GrayText` | `colorNeutralForegroundDisabled`、`colorNeutralStrokeDisabled` |
| ブランドの面とその上の文字 | `ButtonFace`、`ButtonText` | `colorBrandBackground`、`colorNeutralForegroundOnBrand` |

palette と status は、面が Canvas、文字と枠が CanvasText になり、色の区別がなくなる（`packages/tokens/src/alias/highContrastColorPalette.ts:14-61`）。だから色だけで意味を伝えてはならない。

部品の CSS の規則（各コンポーネントの節で写す）:

- `@media (forced-colors: active)` の中で、システムカラーのキーワード（`Canvas`、`CanvasText`、`Highlight`、`HighlightText`、`GrayText`、`ButtonText`、`ButtonFace`、`ButtonBorder`、`LinkText`）を直接書く。
- 状態の区別が消える所だけ書き直す。反転させる部品（hover の Button、primary の Button）には `forced-color-adjust: none` を付けて明示的に塗る（`useButtonStyles.styles.ts:83-101`、`168-185`）。
- light、dark で透明な線（`colorTransparentStroke*`）を枠と outline に入れておく。強制カラーでは透明の指定が置き換わり、枠として現れる。

## コントラストの要件と計算結果

要件（サイトの accessibility と color のページ）:

- 通常の文字は背景に対して 4.5:1 以上。
- 大きな文字（太字で約 18.5px を超えるもの、または標準の太さで 24px 以上）は 3:1 以上。
- アイコンや操作部品など、文字でない要素は、隣り合う色に対して 3:1 以上。
- 色だけで情報を伝えない。

既定のテーマで計算した比（**推論**、計算。`fluent2-tokens.css` と同じ値から WCAG 2.x の相対輝度で求め、小数第 2 位に丸めた）:

| 組み（前景 / 背景） | light | dark |
|---|---|---|
| `colorNeutralForeground1` / `colorNeutralBackground1` | 15.52 | 14.55 |
| `colorNeutralForeground2` / `colorNeutralBackground1` | 10.05 | 10.01 |
| `colorNeutralForeground3` / `colorNeutralBackground1` | 6.19 | 6.48 |
| `colorNeutralForeground4` / `colorNeutralBackground1` | 4.95 | 5.11 |
| `colorNeutralForegroundDisabled` / `colorNeutralBackgroundDisabled` | 1.65 | 2.76 |
| `colorNeutralStrokeAccessible` / `colorNeutralBackground1` | 6.19 | 6.48 |
| `colorNeutralStroke1` / `colorNeutralBackground1` | 1.53 | 2.53 |
| `colorNeutralStroke2` / `colorNeutralBackground1` | 1.32 | 1.86 |
| `colorBrandForeground1` / `colorNeutralBackground1` | 5.38 | 5.18 |
| `colorBrandForegroundLink` / `colorNeutralBackground1` | 6.66 | 5.18 |
| `colorBrandForeground2` / `colorBrandBackground2` | 5.95 | 6.62 |
| `colorNeutralForegroundOnBrand` / `colorBrandBackground` | 5.38 | 6.66 |
| `colorNeutralForegroundOnBrand` / `colorBrandBackgroundHover` | 6.66 | 5.38 |
| `colorCompoundBrandStroke` / `colorNeutralBackground1` | 5.38 | 5.18 |
| `colorPaletteRedForeground1` / `colorNeutralBackground1` | 5.85 | 5.20 |
| `colorPaletteDarkOrangeForeground1` / `colorNeutralBackground1` | 5.44 | 5.45 |
| `colorPaletteGreenForeground1` / `colorNeutralBackground1` | 6.28 | 5.34 |
| `colorStatusDangerForeground1` / `colorStatusDangerBackground1` | 6.55 | 4.96 |
| `colorStatusWarningForeground1` / `colorStatusWarningBackground1` | 4.85 | 6.97 |
| `colorStatusSuccessForeground1` / `colorStatusSuccessBackground1` | 5.89 | 6.06 |

読み取れること:

- 文字の Foreground1〜4 は、light、dark とも Background1 に対して 4.5:1 を満たす。最も低いのは placeholder の Foreground4（約 5:1）である。
- `colorNeutralStroke1`、`2` は 3:1 を満たさない。境界が操作に必要な線（入力欄の下線、チェックボックスの枠、スイッチの軌道）には `colorNeutralStrokeAccessible` を使う。これがこのトークンのある理由である。
- 無効の文字は 3:1 も満たさない。WCAG は無効の部品をコントラストの要件から外しているので、それに沿った設計と読める（**推論**）。
- Foreground2 以下を Background1 以外の面に載せると、比は下がる（例: light の Foreground3 と Background3 は 5.68）。面と文字の組を変えたら、計算し直す。

## Do / Don't

| Do | Don't |
|---|---|
| 主要な面には明るい中立色（light の Background1）を使い、階層を作る | 色だけで情報を伝える |
| brand はボタン、CTA、選択状態の強調に使う | brand を広い面に塗る、多用する |
| semantic の色は大事なメッセージにだけ使い、文字かアイコンを添える | semantic の色を飾りに使う |
| shared の色は控えめに、再利用する部品（アバター、バッジ）に使う | shared の色で独自の意味を作る |
| 状態は `Hover`、`Pressed`、`Selected` のトークンで表す | 明度の計算や `opacity` で状態を作る |
| 境界が操作に必要な線は `colorNeutralStrokeAccessible` にする | 入力欄の枠を `colorNeutralStroke2` だけで描く |
| ブランドの面の上は `OnBrand`、反転した面の上は `Inverted` の文字にする | ブランドの面の上に `colorNeutralForeground1` を置く |
| ブランドを替えたらコントラストを計算し直す | 16 段の一部だけを替える |
| 強制カラーはシステムカラーのキーワードで扱う | `data-theme="high-contrast"` でハイコントラストの対応を済ませる |

## 全トークンの値

ブランド、中立、Subtle、Transparent、フォーカス、影の色のトークン（生成物）。ブランドを参照するトークンには段階を、ハイコントラストの列には模すシステムカラーの名前を添えている。

<!-- spec:tokens-color -->

## v9 との差と未確認の点

- **selected と pressed**: サイトは「rest が最も明るく、selected が最も暗い」と書くが、トークンでは pressed が最も暗い。light の Background4、5 は操作で明るくなる。この設計書はトークン（コード）に従う。
- **Windows の例外**: サイトは「Windows では操作すると明るくなる」とするが、Web の部品に当てはまるかは書いていない。webLightTheme の Background1〜3 は暗くなる向きである。
- **Compound の意味**: `colorCompoundBrand*` の名前の由来と定義を書いた資料はない。「操作部品の小さな印と線のためのブランド色で、dark では明るい段階に移る」という説明は、値と使用例からの推論である。
- **テーマデザイナーとの差**: テーマデザイナーは独自のダークのテーマを書き出すとき、`colorBrandForeground1` を 110、`colorBrandForeground2` を 120 に差し替える（`packages/react-components/theme-designer/src/utils/getOverridableTokenBrandColors.ts:70-76`）。`webDarkTheme` は 100 と 110 のままで、この設計書もそれに従う。
- **使用例のないトークン**: `colorNeutralForeground5`、`colorNeutralBackground8`、`colorNeutralStroke4`、`colorNeutralStrokeSubtle`、`colorNeutralCardBackground*`、`colorBrandBackground3Static`、`colorBrandBackground4Static` は、手元の v9 の styles に使用例がない。v9 の Card は `colorNeutralCardBackground` ではなく `colorNeutralBackground1`、`2` を使う。
- **未確認**: Storybook の Theme/Colors のページ（トークンごとの公式の説明）は読めなかった。ファミリーの説明は、参照先、使用例、テーマデザイナーの `UsageList.ts` から組み立てた。フォーカスの表示に求めるコントラストの数値は、サイトのどのページにもない。Web で `teamsHighContrastTheme` を使うべき場面を明記した資料は見つけていない。
