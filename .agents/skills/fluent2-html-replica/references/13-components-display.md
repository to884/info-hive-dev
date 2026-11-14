# 表示の部品

人、まとまり、区切り、読み込み中を示す部品をまとめる。Avatar、AvatarGroup、Persona、Card（CardHeader、CardPreview、CardFooter）、Image、Divider、Skeleton、Spinner、ProgressBar、List である。CSS は `assets/fluent2.css` の `display` の部分、小さな振る舞いは `assets/fluent2.js` にある（開発用のリポジトリ（非公開）の原本は `src/components/display.css` と `display.js`）。

- 値は React v9（`@fluentui/react-components` 9.75.2）のスタイルのフックから写した。出典はリポジトリからの相対パスと行で書く。同じ節で 2 度目からは、ファイル名と行だけで書く。
- バリエーションは v9 の props 名を kebab-case にした data 属性で表す。既定値は属性を書かなくても当たる。
- data 属性と ARIA の条件は `:where()` に入れ、詳細度を Griffel の atomic class（0,1,0）にそろえた。親の状態で子のスロットを変える規則も `:where(<親の条件>) > .<スロット>` の形で (0,1,0) に保つ。
- 子の要素の有無で決まる v9 の状態（バッジの有無、description の有無、文字の有無、indeterminate）は、独自の属性を足さずに `:has()` と ARIA で判定する。
- 他の章の部品（PresenceBadge、Button、Checkbox、Label、PopoverSurface）を中に置く例は、その章の CSS が読み込まれている前提で書く。

## Avatar

### 概要と使い分け（Do / Don't）

Avatar は人またはグループを、画像か文字（イニシャル）かアイコンで表す。サイトの要点は次のとおり（要約）。

- 1 人（1 グループ）を表すときに使う。複数を並べるときは AvatarGroup を使う。
- 円（`circular`、既定）は個人、四角（`square`）はチーム、組織、会社を表す。
- プレゼンスのバッジで状態を、アクティビティのリング（`active`）で通話中の発言や文書の共同編集などの活動を示す。
- 既定では静的で、操作もフォーカスも持たない。操作できるようにするなら、状態とキーボード操作を定義し、`tabindex` を付ける。
- 32px 以下ではバッジのアイコンが読み取りにくいので、ツールチップなどの文字の状態を併用する。

サイトに Do / Don't の明示の一覧はない。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

DOM の順は root、initials、icon、image、badge である（`packages/react-components/react-avatar/library/src/components/Avatar/renderAvatar.tsx:12-19`）。

| スロット | 要素と class | 内容 |
|---|---|---|
| root | `span.fui-Avatar`、`role="img"` | 名前を `aria-label` に持つ（`packages/react-components/react-avatar/library/src/components/Avatar/useAvatar.tsx:80-88`、`142-170`） |
| initials | `span.fui-Avatar__initials` | 名前から作る 1〜2 文字。空なら描かない（`useAvatar.tsx:108-121`） |
| icon | `span.fui-Avatar__icon`、`aria-hidden="true"` | initials も表示できる画像もないときだけ描く。既定は `PersonRegular`（`useAvatar.tsx:49-52`、`123-133`） |
| image | `img.fui-Avatar__image`、`alt=""`、`role="presentation"`、`aria-hidden="true"` | `src` があるときだけ描く。読み込みに失敗したら `hidden` にしてアイコンを出す（`useAvatar.tsx:92-106`） |
| badge | `.fui-PresenceBadge.fui-Avatar__badge` | プレゼンスのバッジ（選択の部品の章の PresenceBadge） |

- 名前の決め方（`useAvatar.tsx:142-170`）: 利用者が `aria-label` も `aria-labelledby` も書かなければ、name を `aria-label` にする。バッジがあれば `aria-labelledby="<rootId> <badgeId>"` を足す。name がなく initials があれば、initials を `aria-labelledby` で指す。`active` と `inactive` では、文字列 "active" か "inactive" を隠した span か `aria-label` の末尾で足す（`useAvatar.tsx:12-15`）。
- キーボード操作はない。

**イニシャルの作り方**（`packages/react-components/react-avatar/library/src/utils/getInitials.ts`）

1. 括弧の組 `()`、`[]`、`{}` とその中身、閉じない括弧の残りを消す（`getInitials.ts:4`、`71`）。
2. 制御文字、空白以外の ASCII 記号、U+007B〜U+00BF、U+0250〜U+036F、U+E000〜U+FFFF を消す（`getInitials.ts:12`、`72`）。全角の英数字（U+FF01〜）もここで消える。
3. 連続する空白を 1 つにし、前後の空白を除く（`getInitials.ts:73-74`）。
4. 先頭の 1 文字がアラビア文字、ハングル、ひらがな、カタカナ、CJK 統合漢字なら、空文字を返す。電話番号の形も空文字にする（`getInitials.ts:32-33`、`111-117`）。
5. 空白で分け、1 語目の先頭を大文字にする。2 語なら 2 語目、3 語なら 3 語目の先頭を足す。4 語以上は 1 文字だけ。RTL では 2 文字を入れ替える（`getInitials.ts:44-68`）。size が 16 以下なら 1 文字だけにする（`useAvatar.tsx:42`）。

**日本語の名前ではイニシャルが空になる**。「山田 太郎」「やまだ」「タロウ」は、v9 ではイニシャルを出さず、人のアイコンになる。全角の「Ｔａｒｏ」も、手順 2 で文字が消えて空になる。一方、先頭が欧文なら漢字も拾われ、「Yamada 太郎」は「Y太」になる。`display.js` はこの挙動をそのまま再現する（v9 の `getInitials` と 19 通りの名前で出力が一致することを確かめた）。ローマ字のイニシャルを出したいときは、`.fui-Avatar__initials` を自分で書く（v9 の `initials` スロットを渡すのに当たる）。

**colorful の色の割り当て**（`useAvatar.tsx:31-35`、`200-242`）: `color="colorful"` のとき、`idForColor`、なければ name の文字列からハッシュを作り、30 色の配列の `hash % 30` 番目を使う。配列の順は dark-red、cranberry、red、pumpkin、peach、marigold、gold、brass、brown、forest、seafoam、dark-green、light-teal、teal、steel、blue、royal-blue、cornflower、navy、lavender、purple、grape、lilac、pink、magenta、plum、beige、mink、platinum、anchor である。

**display.js の使い方**: root に `data-fui-enhance` を付ける。`data-name` に名前を、必要なら `data-id-for-color` に色の鍵を書く。display.js は次のことをする。

- `data-color="colorful"` なら、選んだ色を `data-resolved-color` に書く。CSS は `data-color` と `data-resolved-color` のどちらでも同じ色の規則を当てる。
- initials が書かれていなければ、上の手順で作って `.fui-Avatar__initials` を足す。空ならアイコン（PersonRegular）を足す。
- 画像の読み込みに失敗したら、画像を `hidden` にしてアイコンを出す。
- `aria-label` と `aria-labelledby` がなければ、v9 と同じ規則で名前を付ける。

### バリエーション

| 属性 | 値 | 既定 | v9 の prop |
|---|---|---|---|
| `data-size` | `16`、`20`、`24`、`28`、`32`、`36`、`40`、`48`、`56`、`64`、`72`、`96`、`120`、`128` | `32` | `size`（`packages/react-components/react-avatar/library/src/components/Avatar/Avatar.types.ts:12`） |
| `data-shape` | `circular`、`square` | `circular` | `shape` |
| `data-color` | `neutral`、`brand`、`colorful`、30 色の名前 | `neutral` | `color` |
| `data-active` | `active`、`inactive`（なしは unset） | なし | `active` |
| `data-active-appearance` | `ring`、`shadow`、`ring-shadow` | `ring` | `activeAppearance` |
| `data-id-for-color` | 文字列（display.js が読む） | なし | `idForColor` |

### 寸法

`packages/react-components/react-avatar/library/src/components/Avatar/useAvatarStyles.styles.ts` から写した。閾値は 499-511（文字）、513-523（角丸）、534-540（リング）、545-553（影）、594-608（アイコン）、バッジの大きさは `useAvatar.tsx:184-198`、バッジの半径と隙間は `useAvatarStyles.styles.ts:201-224` である。

| size | 幅=高さ | 文字 | square の角丸 | icon | リング | 影 | バッジ | 半径 / 隙間 |
|---|---|---|---|---|---|---|---|---|
| 16 | 16px | `fontSizeBase100` | `borderRadiusSmall` | 12px | `strokeWidthThick` | `shadow4` | tiny | 3px / `strokeWidthThin` |
| 20 | 20px | `fontSizeBase100` | `borderRadiusSmall` | 16px | `strokeWidthThick` | `shadow4` | tiny | 3px / `strokeWidthThin` |
| 24 | 24px | `fontSizeBase100` | `borderRadiusSmall` | 16px | `strokeWidthThick` | `shadow4` | tiny | 3px / `strokeWidthThin` |
| 28 | 28px | `fontSizeBase200` | `borderRadiusMedium` | 20px | `strokeWidthThick` | `shadow4` | extra-small | 5px / `strokeWidthThin` |
| 32 | 32px | `fontSizeBase300` | `borderRadiusMedium` | 20px | `strokeWidthThick` | `shadow8` | extra-small | 5px / `strokeWidthThin` |
| 36 | 36px | `fontSizeBase300` | `borderRadiusMedium` | 20px | `strokeWidthThick` | `shadow8` | extra-small | 5px / `strokeWidthThin` |
| 40 | 40px | `fontSizeBase300` | `borderRadiusMedium` | 20px | `strokeWidthThick` | `shadow8` | small | 6px / `strokeWidthThin` |
| 48 | 48px | `fontSizeBase400` | `borderRadiusMedium` | 24px | `strokeWidthThick` | `shadow8` | small | 6px / `strokeWidthThin` |
| 56 | 56px | `fontSizeBase400` | `borderRadiusLarge` | 28px | `strokeWidthThicker` | `shadow16` | medium | 8px / `strokeWidthThin` |
| 64 | 64px | `fontSizeBase500` | `borderRadiusLarge` | 32px | `strokeWidthThicker` | `shadow16` | large | 10px / `strokeWidthThick` |
| 72 | 72px | `fontSizeBase500` | `borderRadiusLarge` | 32px | `strokeWidthThickest` | `shadow28` | large | 10px / `strokeWidthThick` |
| 96 | 96px | `fontSizeBase500` | `borderRadiusXLarge` | 48px | `strokeWidthThickest` | `shadow28` | extra-large | 14px / `strokeWidthThick` |
| 120 | 120px | `fontSizeBase600` | `borderRadiusXLarge` | 48px | `strokeWidthThickest` | `shadow28` | extra-large | 14px / `strokeWidthThick` |
| 128 | 128px | `fontSizeBase600` | `borderRadiusXLarge` | 48px | `strokeWidthThickest` | `shadow28` | extra-large | 14px / `strokeWidthThick` |

- 幅と高さ、アイコンの大きさ、バッジの半径は v9 の直書きである。
- root は `display: inline-block`、`vertical-align: middle`、`font-weight: fontWeightSemibold`（`useAvatarStyles.styles.ts:24-34`）。initials と icon は `line-height: 1` で、`strokeWidthThin` の透明な枠を持つ（`useAvatarStyles.styles.ts:72-89`）。
- リングは `::before`、影は `::after` である。どちらも `margin: calc(-2 * var(--fui-Avatar-ringWidth, 0px))` で外へ広がる。margin が太さの 2 倍なので、アバターとリングの間に太さ 1 本分の隙間ができる（`useAvatarStyles.styles.ts:36-57`）。
- バッジがあると、image、initials、icon に `mask-image` を掛け、バッジの周りに隙間を抜く（`useAvatarStyles.styles.ts:97-110`、`189-191`）。リングにも中心を `2 * ringWidth` ずらした同じマスクを掛ける（`useAvatarStyles.styles.ts:139-141`）。

### 色と状態

色は root ではなく、子の image、initials、icon に付く（`useAvatarStyles.styles.ts:252-381`、`570-619`）。

| `data-color` | 文字 | 背景 | リング（`::before` の `color`） |
|---|---|---|---|
| `neutral` | `colorNeutralForeground3` | `colorNeutralBackground6` | `colorBrandStroke1` |
| `brand` | `colorNeutralForegroundStaticInverted` | `colorBrandBackgroundStatic` | `colorBrandStroke1` |
| 30 色（例 `dark-red`） | `colorPalette<Name>Foreground2` | `colorPalette<Name>Background2` | `colorPalette<Name>BorderActive` |

`<Name>` は色の名前の PascalCase である（`royal-blue` は `RoyalBlue`）。hover、pressed、selected、disabled の色はない。

### フォーカス・動き・ハイコントラスト

- フォーカス: Avatar 自身にはフォーカスの表示がない。
- 動き（`useAvatarStyles.styles.ts:36-53`、`124-133`、`169-179`）:

| 対象 | 条件 | property | duration | timing-function |
|---|---|---|---|---|
| root | active か inactive | `transform`、`opacity` | `durationUltraSlow`、`durationFaster` | `curveEasyEaseMax`、`curveLinear` |
| root | inactive | 同上 | 同上 | `curveDecelerateMin`、`curveLinear` |
| `::before`、`::after` | 常に | `margin`、`opacity` | `durationUltraSlow`、`durationSlower` | `curveEasyEaseMax`、`curveLinear` |
| `::before`、`::after` | inactive | 同上 | 同上 | `curveDecelerateMin`、`curveLinear` |

- inactive では root が `opacity: 0.8`、`transform: scale(0.875)` になり、リングと影は margin 0、opacity 0 へ縮んで消える。active と inactive の root に付く `transform: perspective(1px)` は、動きの終わりの文字のずれを防ぐ回避策である（`useAvatarStyles.styles.ts:125`）。これが重なりの文脈を作り、`z-index: -1` の疑似要素は root の背面に描かれる。
- 縮小モーションでは transition-duration を `0.01ms` にする（`useAvatarStyles.styles.ts:50-52`、`130-132`）。keyframes はない。
- ハイコントラスト: v9 に `forced-colors` の規則はない。initials と icon の透明な枠が、強制色モードでは見える枠になる。
- RTL: バッジの位置の `right` と、マスクの位置を持つ `--fui-Avatar-badgeAlign` の値 `right` を、Griffel が反転する（`useAvatarStyles.styles.ts:195-197`）。CSS では `inset-inline-end` と `:dir(rtl)` で書いた。

### 実装の例

```html demo
<div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap">
  <span class="fui-Avatar" data-fui-enhance data-name="Kat Larsson" data-color="colorful" data-size="24"></span>
  <span class="fui-Avatar" data-fui-enhance data-name="Kat Larsson" data-color="colorful"></span>
  <span class="fui-Avatar" data-fui-enhance data-name="Kevin Sturgis" data-color="brand" data-size="40"></span>
  <span class="fui-Avatar" data-fui-enhance data-name="山田 太郎" data-color="colorful" data-size="48"></span>
  <span class="fui-Avatar" data-fui-enhance data-name="Contoso チーム" data-shape="square" data-size="56"></span>
  <span class="fui-Avatar" role="img" aria-label="山田 太郎" data-color="teal" data-size="64">
    <span class="fui-Avatar__initials">TY</span>
  </span>
</div>
```

1 つ目と 2 つ目は同じ名前なので、同じ色（lilac）になる。「山田 太郎」はイニシャルが空なので人のアイコンになる（色は navy）。「Contoso チーム」は先頭が欧文なので、2 語目のカタカナも拾われて「Cチ」になる（v9 と同じ）。最後の例はローマ字のイニシャルを自分で書いた。

```html demo
<div style="display:flex;gap:24px;align-items:center;flex-wrap:wrap;padding:8px">
  <span class="fui-Avatar" data-fui-enhance data-name="Mona Kane" data-color="colorful" data-size="48" data-active="active"></span>
  <span class="fui-Avatar" data-fui-enhance data-name="Mona Kane" data-color="colorful" data-size="48" data-active="active" data-active-appearance="shadow"></span>
  <span class="fui-Avatar" data-fui-enhance data-name="Mona Kane" data-color="colorful" data-size="48" data-active="active" data-active-appearance="ring-shadow"></span>
  <span class="fui-Avatar" data-fui-enhance data-name="Mona Kane" data-color="colorful" data-size="48" data-active="inactive"></span>
</div>
```

```html demo
<div style="display:flex;gap:12px;align-items:center">
  <span class="fui-Avatar" role="img" aria-label="風景の写真の人" data-size="56">
    <img class="fui-Avatar__image" alt="" role="presentation" aria-hidden="true" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 56 56'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='0' x2='0' y2='1'%3E%3Cstop offset='0' stop-color='%2396c6fa'/%3E%3Cstop offset='1' stop-color='%230f6cbd'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='56' height='56' fill='url(%23g)'/%3E%3Ccircle cx='28' cy='22' r='10' fill='%23ebf3fc'/%3E%3Cpath d='M8 56c2-12 10-18 20-18s18 6 20 18z' fill='%23ebf3fc'/%3E%3C/svg%3E">
  </span>
  <span class="fui-Avatar" role="img" aria-label="Kat Larsson" data-size="32" data-active="active">
    <span class="fui-Avatar__icon" aria-hidden="true"><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M10 2a4 4 0 1 0 0 8 4 4 0 0 0 0-8M7 6a3 3 0 1 1 6 0 3 3 0 0 1-6 0m-2 5a2 2 0 0 0-2 2c0 1.7.83 2.97 2.13 3.8A9 9 0 0 0 10 18c1.85 0 3.58-.39 4.87-1.2A4.4 4.4 0 0 0 17 13a2 2 0 0 0-2-2zm-1 2a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1c0 1.3-.62 2.28-1.67 2.95A8 8 0 0 1 10 17a8 8 0 0 1-4.33-1.05A3.4 3.4 0 0 1 4 13"/></svg></span>
  </span>
</div>
```

2 つ目は JS を使わずに書いた形である。アイコンの SVG は `width="1em" height="1em"` にし、icon スロットの font-size で大きさを決める（v9 の react-icons と同じ）。

プレゼンスのバッジを付けるときは、選択の部品の章の PresenceBadge を root の末尾に置く。CSS はバッジの有無を `:has(> .fui-Avatar__badge)` で判定し、隙間のマスクを掛ける。

```html
<span class="fui-Avatar" data-fui-enhance data-name="Kat Larsson" data-color="colorful" data-size="40">
  <span class="fui-PresenceBadge fui-Avatar__badge" role="img" aria-label="連絡可能" data-size="small" data-status="available">…</span>
</span>
```

### v9 との差と未確認の点

- **近似**: v9 はバッジのある Avatar に `PresenceBadge` の size を自動で渡す。この CSS は Avatar の size からバッジの半径と隙間を決めるので、バッジ自身の大きさ（`data-size`）は利用者が表のとおりに書く。v9 で badge の size を明示して変えた場合の半径の追従は再現していない。
- **独自の属性**: `data-resolved-color`、`data-name`、`data-id-for-color` は v9 にない。`data-name` がないとき、display.js は `aria-label` を名前として使う（v9 にはない代替）。
- v9 の icon スロットの `verticalAlign: 'center'`（`useAvatarStyles.styles.ts:85`）は CSS として無効な値なので写していない。
- Web Components v3 は、16〜24 で文字を Regular にする、リングの色を常に `colorBrandBackgroundStatic` にするなどの違いがある。v9 に合わせた。

## AvatarGroup

### 概要と使い分け（Do / Don't）

AvatarGroup は複数の人やグループを 1 つのまとまりで示す（サイトの要約）。

- `spread`（既定）は間隔を空けて並べる。`stack` は重ねて詰める。`pie` は 1 つの円に 2〜3 人を切り分けて入れ、場所がとても限られるとき（グループチャットの一覧など）に使う。
- 5 人を超えたら、5 つ目の位置にあふれの件数を出し、ポップオーバーで全員を一覧にできる。
- spread と stack はアクティビティのリングに対応し、spread はプレゼンスのバッジも出せる。pie はどちらも出さない。
- 32px 以下ではバッジに文字の状態を併用する。操作を足すならキーボード操作を定義する。

サイトに Do / Don't の明示の一覧はない。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

| スロット | 要素と class | 内容 |
|---|---|---|
| root | `div.fui-AvatarGroup`、`role="group"` | `packages/react-components/react-avatar/library/src/components/AvatarGroup/useAvatarGroup.tsx:37-52` |
| 項目 | `div.fui-AvatarGroupItem` | 中に `span.fui-Avatar.fui-AvatarGroupItem__avatar`。Avatar の色の既定は colorful（`packages/react-components/react-avatar/library/src/components/AvatarGroupItem/useAvatarGroupItem.ts:41-44`） |
| あふれのトリガー | `button.fui-AvatarGroupPopover__triggerButton`、`type="button"` | 件数は `+N`、100 以上は `99+`。size が 24 未満の既定は `MoreHorizontalRegular` のアイコン。pie では中身なし（`packages/react-components/react-avatar/library/src/components/AvatarGroupPopover/useAvatarGroupPopover.tsx:29-42`、`89-94`）。ツールチップ "View more people." がラベルになる（同 `142-148`） |
| 面 | `div.fui-AvatarGroupPopover__popoverSurface`、`aria-label="Overflow"`、`tabindex="0"` | 同 `135-141`。Popover は size small、trapFocus（同 `109-120`） |
| 一覧 | `ul.fui-AvatarGroupPopover__content`、`role="list"` | 同 `128-134` |
| あふれの項目 | `li.fui-AvatarGroupItem` | 中の Avatar は size 24（`useAvatarGroupPopoverContextValues.ts:10-16`）。名前は `span.fui-AvatarGroupItem__overflowLabel`（`aria-hidden="true"`。`useAvatarGroupItem.ts:95-102`） |

- あふれの分け方（`packages/react-components/react-avatar/library/src/utils/partitionAvatarGroupItems.ts:25-38`）: 既定の上限は 5。上限を超えるときは 1 つ減らした数を表示し、残りをあふれにする。表示するのは配列の末尾側である。pie は先頭の 3 つを表示し、全員をあふれにも入れる。React を使わない HTML では、この分け方を利用者がマークアップで行う。
- 中の Avatar にも group と同じ `data-size` を書く（v9 は context で渡す）。
- キーボード: トリガーは button。ポップオーバーの中ではフォーカスを閉じ込める。
- ポップオーバーは `popover` 属性と `popovertarget` で開ける。トリガーに `data-fui-enhance` を付けると、display.js が開閉を `aria-expanded` に写し、開いている間の色（selected）が当たる。

### バリエーション

| 属性 | 値 | 既定 | v9 の prop |
|---|---|---|---|
| `data-layout` | `spread`、`stack`、`pie` | `spread` | `layout`（`useAvatarGroup.tsx:41`） |
| `data-size` | Avatar と同じ 14 段階 | `32` | `size`（`useAvatarGroup.tsx:54`） |
| トリガーの中身 | 文字（count）か SVG（icon） | size < 24 で icon、それ以外 count | `AvatarGroupPopover.indicator` |

### 寸法

`packages/react-components/react-avatar/library/src/components/AvatarGroupItem/useAvatarGroupItemStyles.styles.ts:58-83`、`155-158`、`230-268` と `packages/react-components/react-avatar/library/src/components/AvatarGroupPopover/useAvatarGroupPopoverStyles.styles.ts:98-115`、`130-170` から写した。

| size | stack の重なり | stack の外周 | spread の間隔 | pie の切れ目 | トリガーの枠 | count の文字 | icon |
|---|---|---|---|---|---|---|---|
| 16 | `-spacingHorizontalXXS` | `strokeWidthThick` | `spacingHorizontalS` | `strokeWidthThick` | `strokeWidthThin` | caption2Strong | 12px |
| 20 | `-spacingHorizontalXXS` | `strokeWidthThick` | `spacingHorizontalMNudge` | `strokeWidthThick` | `strokeWidthThin` | caption2Strong | 16px |
| 24 | `-spacingHorizontalXS` | `strokeWidthThick` | `spacingHorizontalMNudge` | `strokeWidthThick` | `strokeWidthThin` | caption2Strong | 16px |
| 28 | `-spacingHorizontalXS` | `strokeWidthThick` | `spacingHorizontalMNudge` | `strokeWidthThick` | `strokeWidthThin` | caption1Strong | 20px |
| 32 | `-spacingHorizontalXS` | `strokeWidthThick` | `spacingHorizontalL` | `strokeWidthThick` | `strokeWidthThin` | body1Strong | 20px |
| 36 | `-spacingHorizontalXS` | `strokeWidthThick` | `spacingHorizontalL` | `strokeWidthThick` | `strokeWidthThick` | body1Strong | 20px |
| 40 | `-spacingHorizontalXS` | `strokeWidthThick` | `spacingHorizontalL` | `strokeWidthThick` | `strokeWidthThick` | body1Strong | 20px |
| 48 | `-spacingHorizontalS` | `strokeWidthThick` | `spacingHorizontalL` | `strokeWidthThick` | `strokeWidthThick` | subtitle2 | 24px |
| 56 | `-spacingHorizontalS` | `strokeWidthThicker` | `spacingHorizontalL` | `strokeWidthThicker` | `strokeWidthThicker` | subtitle2 | 28px |
| 64 | `-spacingHorizontalS` | `strokeWidthThicker` | `spacingHorizontalXL` | `strokeWidthThicker` | `strokeWidthThicker` | subtitle1 | 32px |
| 72 | `-spacingHorizontalS` | `strokeWidthThickest` | `spacingHorizontalXL` | `strokeWidthThickest` | `strokeWidthThickest` | subtitle1 | 32px |
| 96 | `-spacingHorizontalL` | `strokeWidthThickest` | `spacingHorizontalXL` | `strokeWidthThickest` | `strokeWidthThickest` | subtitle1 | 48px |
| 120 | `-spacingHorizontalL` | `strokeWidthThickest` | `spacingHorizontalXL` | `strokeWidthThickest` | `strokeWidthThickest` | title3 | 48px |
| 128 | `-spacingHorizontalL` | `strokeWidthThickest` | `spacingHorizontalXL` | `strokeWidthThickest` | `strokeWidthThickest` | title3 | 48px |

- 重なりと間隔は、2 つ目以降の項目とトリガーの `margin-inline-start` に付く（v9 は `&:not(:first-child)` の `marginLeft`）。
- stack の外周は `box-shadow: 0 0 0 <太さ> colorNeutralBackground2` で、重なった隣との境を描く（`useAvatarGroupItemStyles.styles.ts:59-67`）。
- 項目とトリガーの幅と高さは size である。項目の中の Avatar は `position: absolute` になる（同 `37-42`）。
- あふれの項目は `padding: spacingVerticalXS spacingHorizontalXS`、名前は `margin-inline-start: spacingHorizontalS`、body1（同 `30`、`47-53`）。
- 面は幅 220px、最大の高さ 220px、最小の高さ 80px、`overflow: hidden scroll`、`padding: spacingVerticalS spacingHorizontalS`（`useAvatarGroupPopoverStyles.styles.ts:35-43`）。面の色と影は PopoverSurface（オーバーレイの章）による。
- pie: group を size の大きさにして `clip-path: circle(50%)` で円に切る（`useAvatarGroupStyles.styles.ts:21-27`）。2 人は左右に、3 人は左の半分と右の 2 つの 4 分の 1（0.5 倍に縮小）に切り分ける。切れ目の太さは `--fuiAvatarGroupItem__divider--width` である（`useAvatarGroupItemStyles.styles.ts:88-158`）。項目は `:nth-of-type` で数えるので、項目は div にし、group の中に別の div を挟まない。

### 色と状態

トリガーの色（`useAvatarGroupPopoverStyles.styles.ts:48-96`）。

| 状態 | 文字 | 背景 | 枠 |
|---|---|---|---|
| rest | `colorNeutralForeground1` | `colorNeutralBackground1` | `colorNeutralStroke1` |
| hover | `colorNeutralForeground1Hover` | `colorNeutralBackground1Hover` | `colorNeutralStroke1Hover` |
| pressed（`:active`） | `colorNeutralForeground1Pressed` | `colorNeutralBackground1Pressed` | `colorNeutralStroke1Pressed` |
| 開いている（`aria-expanded="true"`） | `colorNeutralForeground1Selected` | `colorNeutralBackground1Selected` | `colorNeutralStroke1Selected` |
| pie | `transparent` | `colorTransparentBackground` | `colorTransparentStroke` |

pie では hover、pressed、開いている状態の色を付けない（同 `180-181`）。

### フォーカス・動き・ハイコントラスト

- フォーカス: トリガーは `createCustomFocusIndicatorStyle` で、枠を `strokeWidthThick solid colorStrokeFocus2` にし、`outline-style: none` にする（同 `74-77`）。`[data-fui-focus-visible]` を `:focus-visible` で近似した。
- 動き: AvatarGroup 固有の transition と keyframes はない。
- ハイコントラスト: pie の group の背景を `CanvasText` にして切れ目を線として見せる（`useAvatarGroupStyles.styles.ts:24-26`）。トリガーの枠は `CanvasText`（`useAvatarGroupPopoverStyles.styles.ts:62-65`）。
- RTL: 重なりと間隔は論理プロパティで反転する。pie の切り分けは v9 の RTL 用の規則（`useAvatarGroupItemStyles.styles.ts:128-154`）を `:dir(rtl)` で写した。

### 実装の例

```html demo
<div style="display:flex;flex-direction:column;gap:16px;padding:4px">
  <div class="fui-AvatarGroup" role="group" aria-label="参加者（spread）">
    <div class="fui-AvatarGroupItem"><span class="fui-Avatar fui-AvatarGroupItem__avatar" data-fui-enhance data-name="Kat Larsson" data-color="colorful"></span></div>
    <div class="fui-AvatarGroupItem"><span class="fui-Avatar fui-AvatarGroupItem__avatar" data-fui-enhance data-name="Kevin Sturgis" data-color="colorful"></span></div>
    <div class="fui-AvatarGroupItem"><span class="fui-Avatar fui-AvatarGroupItem__avatar" data-fui-enhance data-name="Mona Kane" data-color="colorful"></span></div>
    <div class="fui-AvatarGroupItem"><span class="fui-Avatar fui-AvatarGroupItem__avatar" data-fui-enhance data-name="Elliot Woodward" data-color="colorful"></span></div>
    <button type="button" class="fui-AvatarGroupPopover__triggerButton" data-fui-enhance popovertarget="display-ag-more" aria-label="View more people.">+3</button>
  </div>
  <div class="fui-AvatarGroup" role="group" aria-label="参加者（stack）" data-layout="stack" data-size="40">
    <div class="fui-AvatarGroupItem"><span class="fui-Avatar fui-AvatarGroupItem__avatar" data-fui-enhance data-name="Kat Larsson" data-color="colorful" data-size="40"></span></div>
    <div class="fui-AvatarGroupItem"><span class="fui-Avatar fui-AvatarGroupItem__avatar" data-fui-enhance data-name="Kevin Sturgis" data-color="colorful" data-size="40"></span></div>
    <div class="fui-AvatarGroupItem"><span class="fui-Avatar fui-AvatarGroupItem__avatar" data-fui-enhance data-name="Mona Kane" data-color="colorful" data-size="40"></span></div>
    <div class="fui-AvatarGroupItem"><span class="fui-Avatar fui-AvatarGroupItem__avatar" data-fui-enhance data-name="Elliot Woodward" data-color="colorful" data-size="40"></span></div>
    <button type="button" class="fui-AvatarGroupPopover__triggerButton" aria-label="View more people.">+3</button>
  </div>
</div>
<div id="display-ag-more" popover class="fui-PopoverSurface fui-AvatarGroupPopover__popoverSurface" data-size="small" aria-label="Overflow" tabindex="0">
  <ul class="fui-AvatarGroupPopover__content" role="list">
    <li class="fui-AvatarGroupItem"><span class="fui-Avatar fui-AvatarGroupItem__avatar" data-fui-enhance data-name="Allan Munger" data-color="colorful" data-size="24"></span><span class="fui-AvatarGroupItem__overflowLabel" aria-hidden="true">Allan Munger</span></li>
    <li class="fui-AvatarGroupItem"><span class="fui-Avatar fui-AvatarGroupItem__avatar" data-fui-enhance data-name="Daisy Phillips" data-color="colorful" data-size="24"></span><span class="fui-AvatarGroupItem__overflowLabel" aria-hidden="true">Daisy Phillips</span></li>
    <li class="fui-AvatarGroupItem"><span class="fui-Avatar fui-AvatarGroupItem__avatar" data-fui-enhance data-name="鈴木 花子" data-color="colorful" data-size="24"></span><span class="fui-AvatarGroupItem__overflowLabel" aria-hidden="true">鈴木 花子</span></li>
  </ul>
</div>
```

```html demo
<div style="display:flex;gap:16px;align-items:center">
  <div class="fui-AvatarGroup" role="group" aria-label="2 人のグループ" data-layout="pie" data-size="40">
    <div class="fui-AvatarGroupItem"><span class="fui-Avatar fui-AvatarGroupItem__avatar" data-fui-enhance data-name="Kat Larsson" data-color="colorful" data-size="40"></span></div>
    <div class="fui-AvatarGroupItem"><span class="fui-Avatar fui-AvatarGroupItem__avatar" data-fui-enhance data-name="Kevin Sturgis" data-color="colorful" data-size="40"></span></div>
  </div>
  <div class="fui-AvatarGroup" role="group" aria-label="3 人のグループ" data-layout="pie" data-size="56">
    <div class="fui-AvatarGroupItem"><span class="fui-Avatar fui-AvatarGroupItem__avatar" data-fui-enhance data-name="Kat Larsson" data-color="colorful" data-size="56"></span></div>
    <div class="fui-AvatarGroupItem"><span class="fui-Avatar fui-AvatarGroupItem__avatar" data-fui-enhance data-name="Kevin Sturgis" data-color="colorful" data-size="56"></span></div>
    <div class="fui-AvatarGroupItem"><span class="fui-Avatar fui-AvatarGroupItem__avatar" data-fui-enhance data-name="Mona Kane" data-color="colorful" data-size="56"></span></div>
  </div>
  <div class="fui-AvatarGroup" role="group" aria-label="小さいグループ" data-size="20">
    <div class="fui-AvatarGroupItem"><span class="fui-Avatar fui-AvatarGroupItem__avatar" data-fui-enhance data-name="Kat Larsson" data-color="colorful" data-size="20"></span></div>
    <div class="fui-AvatarGroupItem"><span class="fui-Avatar fui-AvatarGroupItem__avatar" data-fui-enhance data-name="Kevin Sturgis" data-color="colorful" data-size="20"></span></div>
    <button type="button" class="fui-AvatarGroupPopover__triggerButton" aria-label="View more people."><svg class="fui-Icon" width="1em" height="1em" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M6.25 10a1.25 1.25 0 1 1-2.5 0 1.25 1.25 0 0 1 2.5 0m5 0a1.25 1.25 0 1 1-2.5 0 1.25 1.25 0 0 1 2.5 0M15 11.25a1.25 1.25 0 1 0 0-2.5 1.25 1.25 0 0 0 0 2.5"/></svg></button>
  </div>
</div>
```

### v9 との差と未確認の点

- **近似**: v9 のトリガーのツールチップ（"View more people."）は Tooltip で付く。ここでは `aria-label` で名前だけを付けた。ツールチップの表示はオーバーレイの章の Tooltip による。
- **近似**: ポップオーバーの位置は、v9 では Popover がトリガーの近くに置く。`popover` 属性だけでは画面の中央に出る。位置合わせはオーバーレイの章の方法に従う。
- 面には PopoverSurface（オーバーレイの章）の class と `data-size="small"`（v9 の Popover の size）も付ける。まとめの CSS では overlays.css がこの章の CSS の後に並ぶので、`.fui-AvatarGroupPopover__popoverSurface` の規則は class を重ねて (0,2,0) にし、v9 と同じく PopoverSurface の padding に勝たせた。
- **近似**: indicator は中に SVG があるかどうか（`:has(> svg)`）で判定する。v9 は prop で決める。
- **未確認**: pie の 3 人目と 2 人目の `transform-origin: 0 0` を、Griffel が RTL で反転するかは確かめていない。CSS では反転させずに書いた。
- あふれの分け方（上限 5、末尾側を表示）は JS で行わず、マークアップで行う。
- Web Components v3 の手元の対象に AvatarGroup はない。

## Persona

### 概要と使い分け（Do / Don't）

Persona は人を表し、名前と文脈の情報を添える。アバター、プレゼンスのバッジ、最大 4 行の文字からなる（サイトの要約）。

- 既定は Avatar 付きの標準の Persona である。文字は狭いと次の行に折り返す。
- 混み合う場所や狭い場所では presenceOnly にし、アバターを外して名前の横にバッジだけを出す。
- 静的な部品である。操作を足すなら、状態とキーボード操作を定義し、フォーカスを createFocusOutlineStyle で示し、`tabindex` を付ける。
- 文字は短く（1 語か短い句）、文頭だけを大文字にし、句点を付けない。詳しい情報はポップオーバーなどで出す。

サイトに Do / Don't の明示の一覧はない。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

描画の順は、textPosition が after と below なら アバター（またはバッジ）→ 文字、before なら 文字 → アバターである（`packages/react-components/react-persona/library/src/components/Persona/renderPersona.tsx:15-26`）。

| スロット | 要素と class | 内容 |
|---|---|---|
| root | `div.fui-Persona` | role はない |
| avatar | `.fui-Avatar.fui-Persona__avatar` | name、presence をバッジ、size の対応値を渡す（`packages/react-components/react-persona/library/src/components/Persona/usePersona.ts:43-53`） |
| presence | `.fui-PresenceBadge.fui-Persona__presence` | presenceOnly のときだけ。avatar の代わりに描く（`usePersona.ts:54-61`） |
| primaryText | `span.fui-Persona__primaryText` | 既定は name（`usePersona.ts:78-84`） |
| secondaryText、tertiaryText、quaternaryText | `span.fui-Persona__secondaryText` など | 任意 |

- role と ARIA は Avatar と PresenceBadge が持つ。キーボード操作はない。
- presenceOnly は、avatar の代わりに `.fui-Persona__presence` を置くことで表す。CSS は `:has(> .fui-Persona__presence)` で判定する。

### バリエーション

| 属性 | 値 | 既定 | v9 の prop |
|---|---|---|---|
| `data-size` | `extra-small`、`small`、`medium`、`large`、`extra-large`、`huge` | `medium` | `size`（`usePersona.ts:19-27`） |
| `data-text-position` | `after`、`before`、`below` | `after` | `textPosition` |
| `data-text-alignment` | `start`、`center` | `start` | `textAlignment` |
| presence の有無 | `.fui-Persona__presence` を置く | なし | `presenceOnly` |

### 寸法

`usePersona.ts:113-129` と `packages/react-components/react-persona/library/src/components/Persona/usePersonaStyles.styles.ts:87-121`、`219-289` から写した。

| size | Avatar の `data-size` | presence の size | アバターと文字の間 | presenceOnly の間 | primaryText | 2 行目以降 |
|---|---|---|---|---|---|---|
| extra-small | 20 | tiny | `spacingHorizontalSNudge` | `spacingHorizontalSNudge` | body1（presenceOnly で 1 行だけなら caption1） | caption1 |
| small | 28 | extra-small | `spacingHorizontalS` | `spacingHorizontalSNudge` | body1 | caption1 |
| medium | 32 | small | `spacingHorizontalS` | `spacingHorizontalS` | body1 | caption1 |
| large | 36 | medium | `spacingHorizontalMNudge` | `spacingHorizontalMNudge` | body1 | caption1 |
| extra-large | 40 | large | `spacingHorizontalMNudge` | `spacingHorizontalMNudge` | subtitle2 | caption1 |
| huge | 56 | large | `spacingHorizontalM` | `spacingHorizontalM` | subtitle2 | body1（presenceOnly では caption1） |

- 中の Avatar と PresenceBadge の size は、この表のとおりに利用者が書く。
- 間隔は after で `margin-inline-end`、below で `margin-bottom`、before で `margin-inline-start` に付く（`usePersonaStyles.styles.ts:106-114`）。
- 2 行目は `margin-top: -2px`（v9 の直書き。同 `77-79`）。
- グリッド（同 `20-85`）: root は `display: inline-grid`、`grid-auto-flow: column`、`grid-template-columns: max-content [middle] auto`。アバターは 5 行にまたがる。textAlignment が center で below 以外のときは、上下に `1fr` の行を足し、アバターを 6 行にまたがらせて縦の中央に置く。
- presenceOnly で textAlignment が start、size が extra-large と huge 以外のときは、バッジを主テキストの行にそろえる（同 `66-75`、`129`）。

### 色と状態

| スロット | 色 |
|---|---|
| primaryText | `colorNeutralForeground1` |
| secondaryText、tertiaryText、quaternaryText | `colorNeutralForeground2` |

状態はない。

### フォーカス・動き・ハイコントラスト

Persona 自身にフォーカス、動き、`forced-colors` の規則はない。Avatar と PresenceBadge の規則による。RTL では間隔の margin が論理プロパティで反転する。

### 実装の例

```html demo
<div style="display:flex;gap:32px;align-items:flex-start;flex-wrap:wrap">
  <div class="fui-Persona">
    <span class="fui-Avatar fui-Persona__avatar" data-fui-enhance data-name="Kevin Sturgis" data-color="colorful"></span>
    <span class="fui-Persona__primaryText">Kevin Sturgis</span>
    <span class="fui-Persona__secondaryText">連絡可能</span>
  </div>
  <div class="fui-Persona" data-size="huge">
    <span class="fui-Avatar fui-Persona__avatar" data-fui-enhance data-name="山田 太郎" data-color="colorful" data-size="56"></span>
    <span class="fui-Persona__primaryText">山田 太郎</span>
    <span class="fui-Persona__secondaryText">ソフトウェア エンジニア</span>
    <span class="fui-Persona__tertiaryText">東京オフィス</span>
    <span class="fui-Persona__quaternaryText">連絡可能</span>
  </div>
  <div class="fui-Persona" data-size="extra-large" data-text-position="below">
    <span class="fui-Avatar fui-Persona__avatar" data-fui-enhance data-name="Mona Kane" data-color="colorful" data-size="40"></span>
    <span class="fui-Persona__primaryText">Mona Kane</span>
    <span class="fui-Persona__secondaryText">会議中</span>
  </div>
  <div class="fui-Persona" data-size="large" data-text-position="before" data-text-alignment="center">
    <span class="fui-Persona__primaryText">Elliot Woodward</span>
    <span class="fui-Persona__secondaryText">外出中</span>
    <span class="fui-Avatar fui-Persona__avatar" data-fui-enhance data-name="Elliot Woodward" data-color="colorful" data-size="36" data-shape="square"></span>
  </div>
</div>
```

presenceOnly はバッジ（選択の部品の章の PresenceBadge）を置いて作る。

```html
<div class="fui-Persona" data-size="small">
  <span class="fui-PresenceBadge fui-Persona__presence" role="img" aria-label="連絡可能" data-size="extra-small" data-status="available">…</span>
  <span class="fui-Persona__primaryText">Kat Larsson</span>
</div>
```

### v9 との差と未確認の点

- **近似**: v9 は Persona の size から Avatar と PresenceBadge の size を自動で決める。React を使わない HTML では、寸法の表のとおりに中の部品へ書く。
- presenceOnly を、prop ではなく `.fui-Persona__presence` の有無で判定する。
- Web Components v3 の手元の対象に Persona はない。

## Card

### 概要と使い分け（Do / Don't）

Card は、1 つの概念や物（文書、連絡先など）の情報と操作をまとめる容器である（サイトの要約）。

- 用途ごとに一貫した形で使い、予測できるパターンを作る。
- 縦（header、body、footer を上から）と横（header と body を左右に）の向きがある。どのスロットも省略できる。名前や題は CardHeader、画像は CardPreview、操作は CardFooter に置き、重要な順に並べる。
- 大きさは固定、内容に合わせる、親に合わせる、の組み合わせで決める。Card 固有の寸法はない。
- 操作が複数なら、中にボタンやリンクを置く。主な操作が 1 つなら、カード全体を押せるようにしてよい。チェックボックスのように選択できるカードにもできる。選択できることは既定では示さず、hover とフォーカスで示す。強く示したいときは floatingAction にチェックボックスを置く。
- focusMode: off（フォーカスを持たない）、no-tab（カードがフォーカスを受けて閉じ込め、Tab で中を巡回し、Esc で出る）、tab-exit（Tab と Esc で出る）、tab-only（閉じ込めない）。
- 選択できるカードには、意味のある名前（`aria-label`、`aria-labelledby`）と説明を付ける。内容は短く、行動につながるように書く。

サイトに Do / Don't の明示の一覧はない。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

| スロット | 要素と class | 内容 |
|---|---|---|
| root | `div.fui-Card`、`role="group"` | focusMode が off 以外なら `tabindex="0"`（`packages/react-components/react-card/library/src/components/Card/useCard.ts:95-98`、`167`） |
| checkbox | `input.fui-Card__checkbox[type=checkbox]` | 選択できて floatingAction がないとき。視覚的に隠す。CardHeader の header を `aria-labelledby` で指す（`packages/react-components/react-card/library/src/components/Card/useCardSelectable.ts:92-119`） |
| floatingAction | `div.fui-Card__floatingAction` | 右上に浮かせる操作（チェックボックスなど） |
| CardPreview | `div.fui-CardPreview`、`div.fui-CardPreview__logo` | 画像などを端まで広げる |
| CardHeader | `div.fui-CardHeader` と `__image`、`__header`、`__description`、`__action` | 題と説明と操作 |
| CardFooter | `div.fui-CardFooter`、`div.fui-CardFooter__action` | 操作 |

- interactive の判定（`useCard.ts:36-42`）: onClick などのポインターの処理があり、disabled でない。React を使わない HTML では `data-interactive` で表す。focusMode の既定は、interactive なら no-tab、それ以外は off（`useCard.ts:80`）。
- selectable の判定: selected、defaultSelected、onSelectionChange のどれかがある（`useCardSelectable.ts:53-55`）。React を使わない HTML では、隠しチェックボックスを置くか、floatingAction を使うときは `data-selectable` を付ける。選択の状態はチェックボックスの `:checked`、floatingAction のときは `data-selected` で表す。
- 選択の切り替え: クリックか Enter で切り替える。中のフォーカスできる要素の操作では切り替えない（`useCardSelectable.ts:62-90`、`useCard.ts:65-77`）。`data-fui-enhance` を付けると、display.js がこの振る舞いをする。
- disabled: `aria-disabled="true"` を付け、クリックの処理を外す（`useCard.ts:137-143`）。
- focusMode の閉じ込め（no-tab の Tab での巡回、Esc での脱出）は JS が要り、display.js には入れていない。

### バリエーション

| 属性 | 値 | 既定 | v9 の prop |
|---|---|---|---|
| `data-appearance` | `filled`、`filled-alternative`、`outline`、`subtle` | `filled` | `appearance`（`packages/react-components/react-card/library/src/components/Card/Card.types.ts:72`） |
| `data-orientation` | `vertical`、`horizontal` | `vertical` | `orientation`（同 `101`） |
| `data-size` | `small`、`medium`、`large` | `medium` | `size`（同 `108`） |
| `data-interactive` | 有無 | なし | onClick などの有無 |
| 隠しチェックボックス、`data-selectable` | 有無 | なし | selected などの有無 |
| `:checked`、`data-selected` | 有無 | なし | `selected` |
| `aria-disabled="true"` | 有無 | なし | `disabled` |

### 寸法

`packages/react-components/react-card/library/src/components/Card/useCardStyles.styles.ts:40-70`、`105-170`、`388-403` から写した。

| size | `--fui-Card--size`（padding と gap） | `--fui-Card--border-radius` |
|---|---|---|
| small | 8px | `borderRadiusSmall` |
| medium | 12px | `borderRadiusMedium` |
| large | 16px | `borderRadiusLarge` |

- root は `display: flex`、`overflow: hidden`、`box-sizing: border-box`、`padding` と `gap` に `--fui-Card--size`。px の値は v9 の直書きである。
- 枠は `::after` に `strokeWidthThin` の実線で描く。CardPreview を枠の下に入れるためである（同 `51-64`）。
- vertical: CardPreview の左右の margin を `calc(var(--fui-Card--size) * -1)` にして端まで広げる。先頭の CardPreview は上、末尾は下にも負の margin を付ける。floatingAction の直後の CardPreview も上を負にする（同 `132-157`）。先頭と末尾は `:first-of-type` と `:last-of-type` で数えるので、隠しチェックボックス（input）は数に入らない。
- horizontal: `flex-direction: row`、`align-items: center`。CardPreview は上下に負の margin、先頭なら始端、末尾なら終端にも付ける。末尾の CardHeader と CardFooter は `flex-grow: 1`（同 `105-131`）。
- floatingAction は `position: absolute`、上 4px、終端 4px、`z-index: zIndexContent`（同 `388-393`）。
- CardHeader（`packages/react-components/react-card/library/src/components/CardHeader/useCardHeaderStyles.styles.ts:25-94`）: `--fui-CardHeader--gap: 12px`、`align-items: center`。description があればグリッド（image は 1 列目で 2 行、header は 2 列目の 1 行目、description は 2 列目の 2 行目、action は 3 列目で 2 行）、なければ flex で header が伸びる。image は終端に、action は始端に gap の margin を持つ。
- CardPreview（`packages/react-components/react-card/library/src/components/CardPreview/useCardPreviewStyles.styles.ts:15-33`）: logo 以外の子を `display: block`、幅と高さ 100% にする。logo は下 12px、始端 12px、32px 角。
- CardFooter（`packages/react-components/react-card/library/src/components/CardFooter/useCardFooterStyles.styles.ts:15-34`）: `display: flex`、`gap: 12px`。action は `margin-inline-start: auto` で終端に寄せる。

### 色と状態

appearance ごとの色（`useCardStyles.styles.ts:178-352`）。「-」はその状態で上書きしない。hover と pressed は interactive か selectable で disabled でないときだけ付く。selected の規則は selected なら付く（同 `474-476`）。

| appearance | 状態 | 文字 | 背景 | 影 | 枠（`::after`） |
|---|---|---|---|---|---|
| filled | rest | `colorNeutralForeground1` | `colorNeutralBackground1` | `shadow4` | `colorTransparentStroke` |
| filled | hover | `colorNeutralForeground1Hover` | `colorNeutralBackground1Hover` | `shadow8` | - |
| filled | pressed | - | `colorNeutralBackground1Pressed` | - | - |
| filled | selected | - | `colorNeutralBackground1Selected` | - | `colorNeutralStroke1Selected` |
| filled | selected + hover | `colorNeutralForeground1Selected` | `colorNeutralBackground1Selected` | - | - |
| filled-alternative | rest | `colorNeutralForeground1` | `colorNeutralBackground2` | `shadow4` | `colorTransparentStroke` |
| filled-alternative | hover | `colorNeutralForeground2Hover` | `colorNeutralBackground2Hover` | `shadow8` | - |
| filled-alternative | pressed | - | `colorNeutralBackground2Pressed` | - | - |
| filled-alternative | selected | - | `colorNeutralBackground2Selected` | - | `colorNeutralStroke1Selected` |
| filled-alternative | selected + hover | `colorNeutralForeground2Selected` | `colorNeutralBackground2Selected` | - | - |
| outline | rest | `colorNeutralForeground1` | `colorTransparentBackground` | なし | `colorNeutralStroke1` |
| outline | hover | `colorNeutralForeground1Hover` | `colorTransparentBackgroundHover` | - | `colorNeutralStroke1Hover` |
| outline | pressed | - | `colorTransparentBackgroundPressed` | - | `colorNeutralStroke1Pressed` |
| outline | selected | - | `colorTransparentBackgroundSelected` | - | `colorNeutralStroke1Selected` |
| outline | selected + hover | `colorNeutralForeground1Selected` | `colorTransparentBackgroundSelected` | - | - |
| subtle | rest | `colorNeutralForeground1` | `colorSubtleBackground` | なし | `colorTransparentStroke` |
| subtle | hover | `colorNeutralForeground1Hover` | `colorSubtleBackgroundHover` | - | - |
| subtle | pressed | - | `colorSubtleBackgroundPressed` | - | - |
| subtle | selected | - | `colorSubtleBackgroundSelected` | - | `colorNeutralStroke1Selected` |
| subtle | selected + hover | `colorNeutralForeground1Selected` | `colorSubtleBackgroundSelected` | - | - |

- disabled（全 appearance。同 `72-90`、`405-408`）: `cursor: not-allowed`、`user-select: none`、文字 `colorNeutralForegroundDisabled`、背景 `colorNeutralBackgroundDisabled`、影 `shadow2`、枠 `colorNeutralStrokeDisabled`。hover と pressed でも同じ値。`::before` で中の操作を覆う。outline だけは背景を透明、影なしに戻す（同 `301-314`）。
- interactive か selectable のとき、`cursor: pointer` にし、中の `.fui-Text` の色を `currentColor` にする（同 `172-176`）。

### フォーカス・動き・ハイコントラスト

- フォーカス（同 `34-38`、`92-103`、`451-465`）: `createFocusOutlineStyle` に、輪の角丸 `var(--fui-Card--border-radius)`、太さ `strokeWidthThick`、offset `-2px` を渡す。Card はすでに枠の `::after` を持つので、フォーカス中は同じ `::after` が `2px solid colorStrokeFocus2` の輪に替わり、位置は `calc(0px - var(--strokeWidthThick) - -2px)`（つまり 0）になる。root の `outline-style` は none。`[data-fui-focus-visible]` を `:focus-visible` で近似した。
- 選択できるカードは、隠しチェックボックスにキーボードのフォーカスがあるときだけ輪を出す（`selector: 'focus-within'`。`useCardSelectable.ts:113-114`）。`:has(> .fui-Card__checkbox:focus-visible)` で近似した。disabled ではフォーカスの表示をしない。
- 動き: Card、CardHeader、CardPreview、CardFooter に transition と keyframes はない。hover の影と色はすぐに変わる。
- ハイコントラスト（`useCardStyles.styles.ts:354-386`）: interactive と selectable の hover と pressed、selected の常時に、`forced-color-adjust: none`、背景 `Highlight`、文字 `HighlightText`、枠 `Highlight` を当てる。CardPreview と CardFooter は `forced-color-adjust: auto` に戻す。フォーカスの輪は `Highlight`。CardHeader と CardFooter の action の中の `.fui-Button` と `.fui-Link` は、枠、文字、outline の色を `currentColor` にする（`useCardHeaderStyles.styles.ts:43-51`、`useCardFooterStyles.styles.ts:24-32`）。
- RTL: 負の margin、floatingAction、logo、CardHeader と CardFooter の間隔を論理プロパティで書いた。

### 実装の例

```html demo
<div style="display:flex;gap:16px;flex-wrap:wrap;align-items:flex-start;padding:4px">
  <div class="fui-Card" role="group" tabindex="0" data-interactive aria-labelledby="display-card1-h" style="width:280px">
    <div class="fui-CardPreview">
      <svg viewBox="0 0 280 140" aria-hidden="true"><defs><linearGradient id="display-card1-g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#cfe4fa"/><stop offset="1" stop-color="#0f6cbd"/></linearGradient></defs><rect width="280" height="140" fill="url(#display-card1-g)"/><path d="M0 110 Q70 70 140 100 T280 92 V140 H0Z" fill="#115ea3" opacity=".6"/></svg>
    </div>
    <div class="fui-CardHeader">
      <div class="fui-CardHeader__image"><span class="fui-Avatar" data-fui-enhance data-name="Kat Larsson" data-color="colorful"></span></div>
      <div class="fui-CardHeader__header" id="display-card1-h"><span class="fui-Text" data-weight="semibold">四半期レポート</span></div>
      <div class="fui-CardHeader__description"><span class="fui-Text" data-size="200">Kat Larsson が 2 時間前に更新</span></div>
    </div>
    <p class="fui-Text" style="margin:0">売上と利用状況の推移をまとめた。</p>
  </div>
  <div class="fui-Card" role="group" data-appearance="outline" data-size="small" style="width:240px">
    <div class="fui-CardHeader">
      <div class="fui-CardHeader__header"><span class="fui-Text" data-weight="semibold">outline、small</span></div>
    </div>
    <span class="fui-Text" data-size="200">フォーカスを持たないカード（focusMode が off）。</span>
  </div>
  <div class="fui-Card" role="group" aria-disabled="true" style="width:200px">
    <span class="fui-Text">disabled のカード</span>
  </div>
</div>
```

```html demo
<div style="display:flex;gap:16px;flex-wrap:wrap;padding:4px">
  <div class="fui-Card" role="group" data-fui-enhance data-appearance="filled-alternative" style="width:260px">
    <input type="checkbox" class="fui-Card__checkbox" aria-labelledby="display-card2-h">
    <div class="fui-CardHeader">
      <div class="fui-CardHeader__header" id="display-card2-h"><span class="fui-Text" data-weight="semibold">選択できるカード</span></div>
      <div class="fui-CardHeader__description"><span class="fui-Text" data-size="200">クリックか Enter で切り替える</span></div>
    </div>
  </div>
  <div class="fui-Card" role="group" data-fui-enhance data-appearance="outline" data-orientation="horizontal" style="width:320px">
    <input type="checkbox" class="fui-Card__checkbox" aria-labelledby="display-card3-h" checked>
    <div class="fui-CardPreview" style="width:72px">
      <svg viewBox="0 0 72 72" aria-hidden="true"><rect width="72" height="72" fill="#ebf3fc"/><rect x="18" y="14" width="36" height="44" rx="3" fill="#0f6cbd"/><rect x="24" y="24" width="24" height="3" fill="#ebf3fc"/><rect x="24" y="31" width="24" height="3" fill="#ebf3fc"/><rect x="24" y="38" width="16" height="3" fill="#ebf3fc"/></svg>
    </div>
    <div class="fui-CardHeader">
      <div class="fui-CardHeader__header" id="display-card3-h"><span class="fui-Text" data-weight="semibold">設計書.docx</span></div>
      <div class="fui-CardHeader__description"><span class="fui-Text" data-size="200">horizontal、選択済み</span></div>
    </div>
  </div>
</div>
```

1 つ目のカードは interactive なので、キーボードでフォーカスすると枠が 2px の輪に替わる。選択できるカードでは、Tab で隠しチェックボックスにフォーカスすると輪が出る。

### v9 との差と未確認の点

- **独自の属性**: `data-interactive`、`data-selectable`、`data-selected` は v9 の prop ではなく、v9 が props から決める状態を表す。隠しチェックボックスのある選択は、属性を足さずに `:has(> .fui-Card__checkbox)` と `:checked` で判定する。
- **近似**: フォーカスの `[data-fui-focus-visible]` は `:focus-visible`、`[data-fui-focus-within]:focus-within` は `:has(> .fui-Card__checkbox:focus-visible)` で近似した。
- **未実装**: focusMode の no-tab と tab-exit のフォーカスの閉じ込め（Tabster の groupper）は、display.js に入れていない。tabindex の付け外しは利用者が書く。
- CardPreview の中の画像の `alt` を、隠しチェックボックスの名前に使う v9 の仕組み（`packages/react-components/react-card/library/src/components/CardPreview/useCardPreview.ts:48-69`）は再現していない。チェックボックスには `aria-labelledby` を書く。
- 中の `.fui-Text`（テキストの章）と `.fui-Button`（ボタンの章）の見た目は、それぞれの章の CSS による。
- Web Components v3 の手元の対象に Card はない。

## Image

### 概要と使い分け（Do / Don't）

Image は写真やイラストを表示し、伝えたいことを補う（サイトの要約）。

- `shadow` で浮いて見せられるが、多用すると騒がしくなるので控えめにする。
- `alt` は短く正確に、1〜2 文で画像と文脈を説明する。機能を表す画像なら機能を書く。ページにすでにある情報は繰り返さない。
- 装飾だけの画像は `role="presentation"`（と `alt=""`）で支援技術から隠す。

サイトに Do / Don't の明示の一覧はない。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

`img.fui-Image` の 1 要素である（`packages/react-components/react-image/library/src/components/Image/useImage.ts:11-43`）。role と ARIA は利用者が付ける。キーボード操作はない。

### バリエーション

| 属性 | 値 | 既定 | v9 の prop |
|---|---|---|---|
| `data-shape` | `square`、`circular`、`rounded` | `square` | `shape` |
| `data-fit` | `none`、`center`、`contain`、`cover`、`default` | `default` | `fit` |
| `data-bordered` | 有無 | なし | `bordered` |
| `data-shadow` | 有無 | なし | `shadow` |
| `data-block` | 有無 | なし | `block` |

### 寸法

`packages/react-components/react-image/library/src/components/Image/useImageStyles.styles.ts:12-96` から写した。

| 項目 | 値 |
|---|---|
| 基本 | `border-color: colorNeutralStroke1`、`border-radius: borderRadiusNone`、`box-sizing: border-box`、`display: inline-block` |
| bordered | `border-style: solid`、`border-width: strokeWidthThin` |
| circular / rounded | `borderRadiusCircular` / `borderRadiusMedium` |
| shadow | `box-shadow: shadow4` |
| fit=none | `object-fit: none`、`object-position: left top` |
| fit=center | `object-fit: none`、`object-position: center` |
| fit=contain | `object-fit: contain`、`object-position: center` |
| fit=cover | `object-fit: cover`、`object-position: center` |
| fit が default 以外で `width` と `height` の属性がない | 幅と高さ 100%（同 `61-66`、`77-80`） |
| block | `width: 100%` |

### 色と状態

色は枠の `colorNeutralStroke1` だけである。状態はない。

### フォーカス・動き・ハイコントラスト

Image にフォーカス、動き、`forced-colors` の規則はない。fit=none の `object-position: left top` を Griffel が RTL で反転するかは**未確認**である。CSS では反転させずに書いた。

### 実装の例

```html demo
<div style="display:flex;gap:16px;align-items:center;flex-wrap:wrap">
  <img class="fui-Image" width="160" height="100" data-shape="rounded" data-bordered data-shadow alt="山と湖の風景のイラスト" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 320 200'%3E%3Cdefs%3E%3ClinearGradient id='s' x1='0' y1='0' x2='0' y2='1'%3E%3Cstop offset='0' stop-color='%23b4d6fa'/%3E%3Cstop offset='1' stop-color='%23ebf3fc'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='320' height='200' fill='url(%23s)'/%3E%3Cpath d='M0 150 L90 60 L150 120 L210 50 L320 150 Z' fill='%23115ea3'/%3E%3Crect y='150' width='320' height='50' fill='%2362abf5'/%3E%3C/svg%3E">
  <img class="fui-Image" width="80" height="80" data-shape="circular" alt="" role="presentation" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 80 80'%3E%3Cdefs%3E%3CradialGradient id='r'%3E%3Cstop offset='0' stop-color='%23ffd1b3'/%3E%3Cstop offset='1' stop-color='%23e3008c'/%3E%3C/radialGradient%3E%3C/defs%3E%3Crect width='80' height='80' fill='url(%23r)'/%3E%3C/svg%3E">
  <div style="width:120px;height:120px;border:1px dashed var(--colorNeutralStroke2)">
    <img class="fui-Image" data-fit="contain" alt="縦長の図形" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='90' viewBox='0 0 40 90'%3E%3Crect width='40' height='90' rx='6' fill='%230f6cbd'/%3E%3C/svg%3E">
  </div>
</div>
```

3 つ目は `data-fit="contain"` で、幅と高さの属性がないので親の大きさいっぱいに広がり、縦横比を保って収まる。

### v9 との差と未確認の点

- fitFill の条件の「width と height の props がない」を、`width` と `height` の属性の有無で判定する。CSS の `style` で大きさを決めた場合も 100% の規則は当たるが、インラインの `style` が勝つので結果は同じになる。
- Web Components v3 は bordered の色が `colorNeutralStroke2` で、最小の大きさ 8px を持つ。v9 に合わせた。

## Divider

### 概要と使い分け（Do / Don't）

Divider は内容を区切ってまとまりを作り、リズムと階層を作る（サイトの要約）。

- 余白や見出しと組み合わせる。長い文章でとくに役立つ。
- 容器の端まで届く区切りは項目をはっきり分ける。端まで届かない inset の区切りは、似た項目をまとめて近い関係を示す。
- Divider 自身は外側の余白を持たない。既定と文字付きは上下に 12px 以上、アイコン付きは上下に 8px を、レイアウトの側で取る。
- 文字は短く、次の節の内容を示し、文頭だけを大文字にする。
- 内容の区切りでなく見た目だけの区切りなら、`aria-hidden="true"` で隠す。
- Do: 見出しの上に置く。Don't: 見出しの下線として使う。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

| スロット | 要素と class | 内容 |
|---|---|---|
| root | `div.fui-Divider`、`role="separator"`、`aria-orientation="horizontal"` か `"vertical"` | 文字があれば wrapper を `aria-labelledby` で指す（`packages/react-components/react-divider/library/src/components/Divider/useDivider.ts:44-46`） |
| wrapper | `div.fui-Divider__wrapper` | 文字があるときだけ |

線は root の `::before` と `::after` である。キーボード操作はない。

### バリエーション

| 属性 | 値 | 既定 | v9 の prop |
|---|---|---|---|
| `data-align-content` | `start`、`center`、`end` | `center` | `alignContent`（`useDivider.ts:13`） |
| `data-appearance` | `default`、`subtle`、`brand`、`strong` | `default` | `appearance` |
| `data-inset` | 有無 | なし | `inset` |
| `data-vertical` | 有無（`aria-orientation="vertical"` も書く） | なし | `vertical` |

### 寸法

`packages/react-components/react-divider/library/src/components/Divider/useDividerStyles.styles.ts:13-249` から写した。内容との間 12px、inset 12px、端の上限 8px、下限 8px は v9 の直書きである（同 `13-16`）。

| 項目 | 横（既定） | 縦（`data-vertical`） |
|---|---|---|
| root | `display: flex`、`align-items: center`、`flex-grow: 1`、`width: 100%`、`text-align: center` | `flex-direction: column`、`min-height: 20px`。文字があれば `min-height: 84px` |
| 文字 | `fontFamilyBase`、`fontSizeBase200`、`fontWeightRegular`、`lineHeightBase200` | 同じ |
| 線 | `border-top: strokeWidthThin solid`、`min-width: 8px` | 終端側の `strokeWidthThin solid`、`min-height: 8px` |
| 線と文字の間 | `::before` の終端と `::after` の始端に 12px | `::before` の下と `::after` の上に 12px |
| start | `text-align: start`、`::before` を最大 8px | `::before` を最大の高さ 8px |
| end | `text-align: end`、`::after` を最大 8px | `::after` を最大の高さ 8px |
| inset | 始端と終端の padding 12px | 上下の margin 12px |
| 文字なし | 線と文字の間を 0 | 同じ |

- alignContent と向きのどの組み合わせでも、`::before` と `::after` の両方に `content: ""` が付く（同 `60-78`、`152-157`、`175-185`、`220-225`、`239-247`）。start と end は、片側の線を 8px に抑えて文字を寄せる。
- 文字の有無は `:has(> .fui-Divider__wrapper)` で判定する。

### 色と状態

`useDividerStyles.styles.ts:80-124` から写した。

| appearance | 文字 | 線 |
|---|---|---|
| default | `colorNeutralForeground2` | `colorNeutralStroke2` |
| subtle | `colorNeutralForeground3` | `colorNeutralStroke3` |
| brand | `colorBrandForeground1` | `colorBrandStroke1` |
| strong | `colorNeutralForeground1` | `colorNeutralStroke1` |

状態はない。

### フォーカス・動き・ハイコントラスト

Divider にフォーカス、動きの規則はない。v9 に `forced-colors` の規則はなく、線は border なので、強制色モードではシステムの色で描かれる。RTL では、Griffel が反転する `text-align`、線と文字の間の margin、inset の padding、縦の線の側を論理プロパティで書いた。

### 実装の例

```html demo
<div style="display:flex;flex-direction:column;gap:16px;width:100%">
  <div class="fui-Divider" role="separator" aria-orientation="horizontal"></div>
  <div class="fui-Divider" role="separator" aria-orientation="horizontal" aria-labelledby="display-dv1"><div class="fui-Divider__wrapper" id="display-dv1">中央の文字</div></div>
  <div class="fui-Divider" role="separator" aria-orientation="horizontal" aria-labelledby="display-dv2" data-align-content="start" data-appearance="brand"><div class="fui-Divider__wrapper" id="display-dv2">始端に寄せる（brand）</div></div>
  <div class="fui-Divider" role="separator" aria-orientation="horizontal" aria-labelledby="display-dv3" data-align-content="end" data-appearance="strong"><div class="fui-Divider__wrapper" id="display-dv3">終端に寄せる（strong）</div></div>
  <div class="fui-Divider" role="separator" aria-orientation="horizontal" data-appearance="subtle" data-inset></div>
  <div style="display:flex;height:96px;align-items:stretch">
    <span class="fui-Text">左</span>
    <div class="fui-Divider" role="separator" aria-orientation="vertical" data-vertical></div>
    <span class="fui-Text">中</span>
    <div class="fui-Divider" role="separator" aria-orientation="vertical" aria-labelledby="display-dv4" data-vertical><div class="fui-Divider__wrapper" id="display-dv4">縦</div></div>
    <span class="fui-Text">右</span>
  </div>
</div>
```

### v9 との差と未確認の点

- v9 は線の下限を `'8px;'` と書いている（`useDividerStyles.styles.ts:16`）。生成される CSS では末尾のセミコロンが空の宣言になるだけで、値は 8px になる（**推論**）。
- Web Components v3 は線を background で描き、縦の最小の高さを 10px（文字ありで 20px）にする。v9 に合わせた。

## Skeleton

### 概要と使い分け（Do / Don't）

Skeleton は区画の読み込み中を、ページの他の部分を止めずに示し、届く内容の構造をほのめかす（サイトの要約）。

- 読み込みが 1 秒を超える内容に使う。構造がわからないときは ProgressBar か Spinner を使う。所要時間を示さないので、長い処理には使わない。
- 動きは wave（既定、最も滑らか。多数を並べるときもこれ）と pulse がある。
- Do: データの取得をまとめ、段差のある読み込みを避ける。避けられないなら動きをそろえる。形は単純に保つ（persona ならアバター、題、副題だけ）。フォーカスできる読み込み要素には名前を付ける。読み込み後もフォーカスを動かさない。大きい区画には適切な強さの `aria-live` を検討する。同時に更新されない区画では `aria-busy` を読み込み中に true、完了で false にする。
- Don't: アプリバーのタブのような固定の部分に使わない。長い処理に使わない。ライブリージョンを多用しない。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

| スロット | 要素と class | 内容 |
|---|---|---|
| Skeleton | `div.fui-Skeleton`、`role="progressbar"`、`aria-busy="true"` | `packages/react-components/react-skeleton/library/src/components/Skeleton/useSkeleton.ts:48-56` |
| SkeletonItem | `div.fui-SkeletonItem` | 形と大きさを持つ。`::after` が動く帯 |

- Skeleton の animation と appearance は子の SkeletonItem に受け継がれ、子で上書きできる（`useSkeleton.ts:18-25`）。CSS では、項目の data 属性、なければ祖先の Skeleton の data 属性を見る。
- `span` で書いたときは `display: block` にする（`packages/react-components/react-skeleton/library/src/components/Skeleton/useSkeletonStyles.styles.ts:10-13`）。
- キーボード操作はない。読み込み中であることの名前（`aria-label`）を Skeleton に付ける。

### バリエーション

| 属性 | 値 | 既定 | 付ける所 |
|---|---|---|---|
| `data-animation` | `wave`、`pulse` | `wave` | Skeleton か SkeletonItem |
| `data-appearance` | `opaque`、`translucent` | `opaque` | Skeleton か SkeletonItem |
| `data-shape` | `rectangle`、`square`、`circle` | `rectangle` | SkeletonItem |
| `data-size` | `8`、`12`、`14`、`16`、`20`、`22`、`24`、`28`、`32`、`36`、`40`、`48`、`52`、`56`、`64`、`72`、`92`、`96`、`120`、`128` | `16` | SkeletonItem |

### 寸法

`packages/react-components/react-skeleton/library/src/components/SkeletonItem/useSkeletonItemStyles.styles.ts:99-153` から写した。px は v9 の直書きである。

| shape | 幅 | 高さ | 角丸 |
|---|---|---|---|
| rectangle | 100% | size | 4px |
| square | size | size | なし |
| circle | size | size | 50% |

### 色と状態

`useSkeletonItemStyles.styles.ts:52-93` から写した。

| animation / appearance | 項目の背景 | `::after` |
|---|---|---|
| wave / opaque | `colorNeutralStencil1` | `linear-gradient(to right, colorNeutralStencil1 0%, colorNeutralStencil2 50%, colorNeutralStencil1 100%)` |
| wave / translucent | `colorNeutralStencil1Alpha` | `linear-gradient(to right, transparent 0%, colorNeutralStencil1Alpha 50%, transparent 100%)` |
| pulse / opaque | なし | 背景 `colorNeutralStencil1` |
| pulse / translucent | なし | 背景 `colorNeutralStencil1Alpha` |

### フォーカス・動き・ハイコントラスト

- フォーカス: なし。
- 動き（`useSkeletonItemStyles.styles.ts:12-75`）: `::after` は `inset: 0` の帯で、`animation-iteration-count: infinite`、`animation-timing-function: ease-in-out`。

| animation | duration | keyframes |
|---|---|---|
| wave | 3s | `::after` を `translate(-100%)` から `translate(100%)` へ（`fui-SkeletonItem-wave`） |
| pulse | 1s | opacity を 1 → 0.4 → 1（`fui-SkeletonItem-pulse`） |

- 縮小モーション: `animation-duration: 0.01ms`、`animation-iteration-count: 1`（同 `46-49`）。
- ハイコントラスト: wave の `::after` の背景を `WindowText` にする（同 `64-66`）。

### 実装の例

```html demo
<div class="fui-Skeleton" role="progressbar" aria-busy="true" aria-label="連絡先を読み込んでいます" style="display:grid;grid-template-columns:min-content 1fr;gap:8px 12px;align-items:center;width:100%;max-width:320px">
  <div class="fui-SkeletonItem" data-shape="circle" data-size="40" style="grid-row:span 2"></div>
  <div class="fui-SkeletonItem" data-size="16"></div>
  <div class="fui-SkeletonItem" data-size="12" style="width:60%"></div>
</div>
```

```html demo
<div style="display:flex;flex-direction:column;gap:16px;width:100%;max-width:320px">
  <div class="fui-Skeleton" role="progressbar" aria-busy="true" aria-label="読み込み中（pulse）" data-animation="pulse" style="display:flex;gap:8px;align-items:center">
    <div class="fui-SkeletonItem" data-shape="square" data-size="32"></div>
    <div class="fui-SkeletonItem" data-size="20"></div>
  </div>
  <div style="padding:12px;background:var(--colorBrandBackground2)">
    <div class="fui-Skeleton" role="progressbar" aria-busy="true" aria-label="読み込み中（translucent）" data-appearance="translucent" style="display:flex;flex-direction:column;gap:8px">
      <div class="fui-SkeletonItem" data-size="24"></div>
      <div class="fui-SkeletonItem" data-size="24" data-animation="pulse"></div>
    </div>
  </div>
</div>
```

### v9 との差と未確認の点

- **近似**: 受け継ぎは「祖先のどれかの Skeleton」の属性で判定する。Skeleton を入れ子にして違う値を付けた場合、最も近い祖先を優先する v9 の context とは結果が変わることがある。
- v9 は pulse の translucent で `backgroundColor: 'none'`（無効な値）と書く（`useSkeletonItemStyles.styles.ts:87-93`）。mergeClasses が translucent の背景の宣言を取り除き、残る宣言は無効で捨てられるので、結果は背景なしになる。CSS では `transparent` と書いた。
- **未確認**: wave の `translate(-100%)` と keyframes を、Griffel が RTL で反転するかは確かめていない。CSS では RTL の規則を書いていない。
- Skeleton 自身の size と shape を子へ渡す使い方は再現していない。項目ごとに書く。
- Web Components v3 の手元の対象に Skeleton はない。

## Spinner

### 概要と使い分け（Do / Don't）

Spinner は処理中であることを示す（サイトの要約）。

- 1 秒を超える読み込みに使う。残り時間は示さないので、進み具合を示すなら determinate の ProgressBar を使う。
- 読み込む区画の中央に置く。1 区画だけの読み込みなら、ページの他の部分の操作を止めない。
- 3 秒を超えるならラベルを付ける。ラベルは `aria-labelledby` で読み上げられる。
- 文言はできるだけ具体的にし、きっかけの操作の動詞を反映する。操作がないときは背景の処理を明確に書く。「読み込み中」のような曖昧な語を避ける。英語では 3 語以下の -ing 形にし、空白の後に省略記号を付けて終える。文頭だけを大文字にする。

サイトの Do / Don't は画像の例だけで、文の一覧はない。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

| スロット | 要素と class | 内容 |
|---|---|---|
| root | `div.fui-Spinner`、`role="progressbar"` | ラベルがあれば `aria-labelledby` で指す（`packages/react-components/react-spinner/library/src/components/Spinner/useSpinner.tsx:51-58`、`87-88`） |
| spinner | `span.fui-Spinner__spinner` | 輪（トラックの色）と全体の回転 |
| spinnerTail | `span.fui-Spinner__spinnerTail` | 伸び縮みする弧 |
| label | `label.fui-Label.fui-Spinner__label` | labelPosition が above と before なら spinner の前、below と after なら後に置く（`packages/react-components/react-spinner/library/src/components/Spinner/renderSpinner.tsx:14-26`） |

- `delay`（ms）が正なら、その時間が過ぎるまで spinner とラベルを描かない（`useSpinner.tsx:65-77`）。React を使わない HTML では、表示を遅らせる処理を利用者が書く。
- キーボード操作はない。

### バリエーション

| 属性 | 値 | 既定 | v9 の prop |
|---|---|---|---|
| `data-size` | `extra-tiny`、`tiny`、`extra-small`、`small`、`medium`、`large`、`extra-large`、`huge` | `medium` | `size`（`useSpinner.tsx:20`） |
| `data-appearance` | `primary`、`inverted` | `primary` | `appearance` |
| `data-label-position` | `above`、`below`、`before`、`after` | `after` | `labelPosition`（`useSpinner.tsx:48`） |

### 寸法

`packages/react-components/react-spinner/library/src/components/Spinner/useSpinnerStyles.styles.ts:23-37`、`139-224` から写した。幅と高さは v9 の直書きである。

| size | 幅=高さ | 線の太さ（`--fui-Spinner--strokeWidth`） | ラベルの文字 |
|---|---|---|---|
| extra-tiny | 16px | `strokeWidthThick` | body1 |
| tiny | 20px | `strokeWidthThick` | body1 |
| extra-small | 24px | `strokeWidthThick` | body1 |
| small | 28px | `strokeWidthThick` | body1 |
| medium | 32px | `strokeWidthThicker` | subtitle2 |
| large | 36px | `strokeWidthThicker` | subtitle2 |
| extra-large | 40px | `strokeWidthThicker` | subtitle2 |
| huge | 44px | `strokeWidthThickest` | subtitle1 |

- root は `display: flex`、中央寄せ、`gap: 8px`、`line-height: 0`、`overflow: hidden`。above と below は縦に並べる。
- 輪の形は `mask-image: radial-gradient(closest-side, ...)` で作る（同 `43-48`）。弧は `conic-gradient(transparent 105deg, white 105deg)` のマスクの陰から、135 度の扇 2 枚を回し出して、見える弧を 30 度から 255 度まで伸び縮みさせる（同 `71-91`）。

### 色と状態

`useSpinnerStyles.styles.ts:50-51`、`124-127`、`188-191` から写した。

| appearance | トラック | 弧 | ラベル |
|---|---|---|---|
| primary | `colorBrandStroke2Contrast` | `colorBrandStroke1` | Label の既定（`colorNeutralForeground1`） |
| inverted | `colorNeutralStrokeAlpha2` | `colorNeutralStrokeOnBrand2` | `colorNeutralForegroundStaticInverted` |

### フォーカス・動き・ハイコントラスト

- フォーカス: なし。
- 動き（同 `58-121`）:

| 要素 | animation | keyframes |
|---|---|---|
| spinner | 1.5s linear infinite | `fui-Spinner-spin`: 0deg → 360deg |
| spinnerTail | 1.5s `curveEasyEase` infinite | `fui-Spinner-tail`: -135deg → 0deg → 225deg |
| spinnerTail の `::before` | 親から受け継ぐ | `fui-Spinner-tail-before`: 0deg → 105deg → 0deg |
| spinnerTail の `::after` | 親から受け継ぐ | `fui-Spinner-tail-after`: 0deg → 225deg → 0deg |

- 縮小モーション: spinner の回転は止めず 1.8s にする（同 `66-68`）。弧は伸び縮みをやめ、`conic-gradient(transparent 120deg, currentcolor 360deg)` のだんだん濃くなる弧が回るだけになる（同 `114-120`）。
- RTL（同 `129-137`）: 弧のマスクを `conic-gradient(white 255deg, transparent 255deg)`、扇を `conic-gradient(transparent 225deg, currentcolor 225deg)`、縮小モーションの弧を `conic-gradient(currentcolor 0deg, transparent 240deg)` にする。`:dir(rtl)` で写した。
- ハイコントラスト: spinner の背景を `HighlightText`、弧を `Highlight` にし、`forced-color-adjust: none` にする（同 `52-56`）。

### 実装の例

```html demo
<div style="display:flex;gap:32px;align-items:center;flex-wrap:wrap">
  <div class="fui-Spinner" role="progressbar" aria-label="読み込み中" data-size="tiny">
    <span class="fui-Spinner__spinner"><span class="fui-Spinner__spinnerTail"></span></span>
  </div>
  <div class="fui-Spinner" role="progressbar" aria-labelledby="display-sp1">
    <span class="fui-Spinner__spinner"><span class="fui-Spinner__spinnerTail"></span></span>
    <label class="fui-Label fui-Spinner__label" id="display-sp1">ファイルを読み込んでいます …</label>
  </div>
  <div class="fui-Spinner" role="progressbar" aria-labelledby="display-sp2" data-size="huge" data-label-position="below">
    <span class="fui-Spinner__spinner"><span class="fui-Spinner__spinnerTail"></span></span>
    <label class="fui-Label fui-Spinner__label" id="display-sp2">同期しています …</label>
  </div>
</div>
```

```html demo
<div style="display:flex;gap:24px;padding:16px;background:var(--colorBrandBackground)">
  <div class="fui-Spinner" role="progressbar" aria-labelledby="display-sp3" data-appearance="inverted" data-size="small" data-label-position="before">
    <label class="fui-Label fui-Spinner__label" id="display-sp3">保存しています …</label>
    <span class="fui-Spinner__spinner"><span class="fui-Spinner__spinnerTail"></span></span>
  </div>
</div>
```

### v9 との差と未確認の点

- `delay` は再現していない。表示を遅らせるには、利用者が `hidden` を外すなどの処理を書く。
- ラベルの色と既定の書体は、ボタンなどの章の Label の CSS による。Spinner の CSS は size ごとの書体と inverted の色だけを上書きする。
- 縮小モーションの `animation-iteration-count: 0` は v9 の値のまま写した。
- **推論**: spinner の土台は makeResetStyles なので、その `forced-colors` の規則は後の atomic class（inverted）より前に並ぶと読んだ。CSS でも inverted の前に置き、強制色モードでも inverted の色が勝つようにした。強制色モードでの描画は確かめていない。
- Web Components v3 は弧を border と overflow で描き、extra-tiny と縮小モーションの規則を持たない。v9 に合わせた。

## ProgressBar

### 概要と使い分け（Do / Don't）

ProgressBar はシステムの情報（ストレージの使用量など）やタスクの進み具合（ダウンロードの残りなど）を示す（サイトの要約）。

- 1 秒を超えるタスクだけに使う。構造のわかる内容の読み込みには Skeleton を使う。動かない棒は固定の割合を示す。
- できるだけ determinate を使う。indeterminate は短いタスクだけに使い、残りを見積もれるようになったら determinate に切り替える。残りが少なくなっても、いまの周回を途中で切らずに終える。
- 関係する段階は 1 本の棒にまとめ、段階ごとに戻さない。段階が変わったら状態の文言を変える。
- ドロワー、コールアウト、またはタスクを始めた UI の下に置く。取り消せるなら、閉じるボタンをラベルのベースラインにそろえて置く。
- ラベルは短く、文頭だけを大文字にし、句点を付けない。状態の文言は何をしているかと進み具合を意味のある単位で示し、時間の単位は避ける。失敗したら、何が起き、次に何をするかの具体的な文言に置き換える。
- Do: 1 秒を超えるタスクに使う。determinate を優先する。段階をまとめる。失敗時に文言を置き換える。Don't: ほぼ一瞬の操作に使う。長いタスクに indeterminate を使う。途中で切る。段階ごとに戻す。時間の単位を書く。ラベルに句点を付ける。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

| スロット | 要素と class | 内容 |
|---|---|---|
| root | `div.fui-ProgressBar`、`role="progressbar"` | determinate では `aria-valuemin="0"`、`aria-valuemax`、`aria-valuenow`（`packages/react-components/react-progress/library/src/components/ProgressBar/useProgressBar.tsx:73-90`） |
| bar | `div.fui-ProgressBar__bar` | v9 は determinate の bar の `style.width` に `<value / max × 100>%` を書く（`packages/react-components/react-progress/library/src/components/ProgressBar/useProgressBarStyles.styles.ts:126-132`）。React を使わない HTML では style 属性を使わず、根の `data-percent` か `display.js` で渡す（下記） |

- indeterminate（value なし）では aria-value を付けない。CSS は `aria-valuenow` のない ProgressBar を indeterminate とみなす。
- max は 0 以下なら 1 にし、value は 0 から max に丸める（`packages/react-components/react-progress/library/src/utils/clampMax.ts:1-11`、`packages/react-components/react-progress/library/src/utils/clampValue.ts:1-18`）。
- 幅の渡し方（独自）: CSS は bar の幅を根の `--fui-ProgressBar--value` から決める。値は次のどちらかで渡す。どちらも、インラインの style 属性を禁じる CSP（`style-src 'self'`）の下でも効く。
  - 根に `data-percent="0"`〜`"100"`（整数の百分率）を書く。CSS の規則だけで幅が決まり、JS は要らない。端数は丸める。
  - `data-fui-enhance` の中に置くと、`display.js` が `aria-valuenow` と `aria-valuemax` から v9 と同じ式で計算し、CSSOM で書く（端数も保つ）。値を変えたら、根の `--fui-ProgressBar--value` を CSSOM で書き直す。
- bar に `style="width:…"` を書いても効くが、CSP の下では無視されるので使わない。
- Field の中では、Field のラベルと検証の文言を `aria-labelledby` と `aria-describedby` で指す（`useProgressBar.tsx:86-96`）。
- キーボード操作はない。

### バリエーション

| 属性 | 値 | 既定 | v9 の prop |
|---|---|---|---|
| `aria-valuenow` | 数値 / なし（indeterminate） | なし | `value` |
| `aria-valuemax` | 数値 | `1` | `max` |
| `data-thickness` | `medium`、`large` | `medium` | `thickness` |
| `data-shape` | `rounded`、`square` | `rounded` | `shape` |
| `data-color` | `brand`、`success`、`warning`、`error` | `brand` | `color`（Field の validationState からも決まる） |

### 寸法

`useProgressBarStyles.styles.ts:17-60` から写した。

| 項目 | 値 |
|---|---|
| root | `display: block`、`width: 100%`、`overflow: hidden` |
| 高さ medium / large | 2px / 4px（v9 の直書き） |
| 角丸 rounded / square | `borderRadiusMedium` / `borderRadiusNone` |
| bar | `height: 100%`、`border-radius: inherit` |
| indeterminate の bar | `max-width: 33%`、`position: relative` |

### 色と状態

`useProgressBarStyles.styles.ts:28`、`69-93` から写した。

| 要素 | 値 |
|---|---|
| トラック（root） | `colorNeutralBackground6` |
| bar（brand） | `colorCompoundBrandBackground` |
| bar（error） | `colorPaletteRedBackground3` |
| bar（warning） | `colorPaletteDarkOrangeBackground3` |
| bar（success） | `colorPaletteGreenBackground3` |
| indeterminate の bar の重ね | `linear-gradient(to right, colorNeutralBackground6 0%, colorTransparentBackground 50%, colorNeutralBackground6 100%)`（地は brand） |

error、warning、success は determinate のときだけ付く（同 `121`）。indeterminate は常に brand である。

### フォーカス・動き・ハイコントラスト

- フォーカス: なし。
- determinate: value が 0.01 より大きいとき `transition: width 0.3s ease`。0 付近へ戻すときは動かさない（同 `13-15`、`61-65`、`120`）。
- indeterminate（`packages/react-components/react-progress/library/src/components/ProgressBar/progressBarMotions.ts:8-23`）: v9 は Web Animations で `translate: -100%` から `translate: 300%` へ、3000ms、`curveLinear`、無限に動かす。translate の % は bar 自身の幅（容器の約 33%）が基準なので、容器の左外から右外まで滑る。CSS では keyframes `fui-ProgressBar-indeterminate` で写した。
- 縮小モーション: opacity を 0.2 → 1 → 0.2 にする 3000ms の脈動にし、bar の `max-width` を 100% にする（`progressBarMotions.ts:18-22`、`useProgressBarStyles.styles.ts:75-78`）。reducedMotion は easing を持たないので、元の `curveLinear` を受け継ぐ（`packages/react-components/react-motion/library/src/hooks/useAnimateAtoms.ts:111-122`）。keyframes は `fui-ProgressBar-indeterminate-reduced`。
- ハイコントラスト: トラックを `CanvasText`、bar を `Highlight` にする（`useProgressBarStyles.styles.ts:32-34`、`55-57`）。

### 実装の例

```html demo
<div style="display:flex;flex-direction:column;gap:16px;width:100%;max-width:360px">
  <div>
    <div class="fui-Text" id="display-pb1">アップロードしています … 42%</div>
    <div class="fui-ProgressBar" role="progressbar" aria-labelledby="display-pb1" aria-valuemin="0" aria-valuemax="1" aria-valuenow="0.42" data-percent="42">
      <div class="fui-ProgressBar__bar"></div>
    </div>
  </div>
  <div class="fui-ProgressBar" role="progressbar" aria-label="ストレージの使用量" aria-valuemin="0" aria-valuemax="100" aria-valuenow="90" data-percent="90" data-thickness="large" data-color="warning">
    <div class="fui-ProgressBar__bar"></div>
  </div>
  <div class="fui-ProgressBar" role="progressbar" aria-label="完了" aria-valuemin="0" aria-valuemax="1" aria-valuenow="1" data-percent="100" data-color="success" data-shape="square">
    <div class="fui-ProgressBar__bar"></div>
  </div>
  <div class="fui-ProgressBar" role="progressbar" aria-label="接続しています">
    <div class="fui-ProgressBar__bar"></div>
  </div>
</div>
```

### v9 との差と未確認の点

- **近似**: 幅の transition の条件「value > 0.01」は属性で比べられないので、`aria-valuenow="0"` のときだけ外す。0 より大きく 0.01 以下の値でも動く。
- **近似**: v9 は indeterminate を Web Animations（`fill: forwards`）で動かす。CSS では同じ keyframes と時間を CSS の animation で書いた。
- **未確認**: v9 の indeterminate の keyframes は RTL でも符号を変えない（`progressBarMotions.ts:13`）。RTL では bar が終端（右）から始まるため、滑り方が LTR と変わると読める（**推論**）。CSS では v9 のとおり反転させていない。
- Web Components v3 は `attr()` で幅を計算し、max の既定を 100 にする。v9 に合わせた。

## List

### 概要と使い分け（Do / Don't）

List は同種の項目を縦に並べ、見渡しやすく、たどり着きやすくする（サイトの要約）。

- 項目は互いに独立している。列どうしが関係するなら Table か DataGrid、入れ子の階層が要るなら Tree を使う。
- 振る舞いの型は、単一の操作（クリック、Enter、Space で実行）、選択が主操作（どこを押しても選択）、選択が副操作（クリックと Enter は主操作、Space で選択）、複数の操作（右矢印で項目の中の操作へ移る）がある。
- キーボード: 上下の矢印で項目間を移り、Enter と Space で実行し、右矢印で項目の中の操作へ入り、左矢印か Esc で項目に戻る。
- 役割は、フォーカスできる要素も選択もないなら `list`、選択するなら `listbox` と `option` にする。行ごとに操作が違うと空のセルができるので、`grid` は避ける。
- Do: 目的を見出しか完全な文、またはコロンで終わる句で示す。項目を並列の構造にし、長さをそろえる。順序や階層があるなら番号を振る。
- Don't: 見出しの後にコロンや句点、説明文を付けない。完全な文でない項目に句点を付けない。項目をセミコロン、コンマ、接続詞で終えない。空の項目や無効な項目を入れない。翻訳する内容で、下の項目で完結する導入の断片を書かない。

### 構造とマークアップ（スロット、role、ARIA、キーボード操作）

| スロット | 要素と class | 内容 |
|---|---|---|
| List | `ul.fui-List`、`role="list"`、`"listbox"`、`"grid"` | navigationMode が composite なら grid、選択ありなら listbox、それ以外は list。multiselect では `aria-multiselectable="true"`（`packages/react-components/react-list/library/src/utils/calculateListRole.ts:10-21`） |
| ListItem | `li.fui-ListItem`、`role="listitem"`、`"option"`、`"row"` | フォーカスできるとき `tabindex="0"`、選択ありなら `aria-selected`（`packages/react-components/react-list/library/src/components/ListItem/useListItem.tsx:257-271`） |
| checkmark | `.fui-Checkbox.fui-ListItem__checkmark`、`tabindex="-1"` | 選択ありのとき。選択の部品の章の Checkbox |

- 項目がフォーカスできる条件は、選択あり、navigationMode あり、または `tabIndex=0` である（`useListItem.tsx:171`）。
- disabledSelection で onAction がない項目は `aria-disabled="true"`（`useListItem.tsx:264`、`298`）。
- 上下の矢印の移動（Tabster の mover）、Space と Enter の処理、項目の中への出入り（groupper）は JS が要り、display.js には入れていない。

### バリエーション

| 属性 | 値 | 既定 | v9 の prop |
|---|---|---|---|
| List の `role` | `list`、`listbox`、`grid` | `list` | navigationMode、selectionMode から決まる |
| `aria-multiselectable` | `true` | なし | `selectionMode="multiselect"` |
| ListItem の `tabindex="0"` | 有無 | なし | フォーカスできる項目 |
| ListItem の `aria-selected` | `true`、`false` | なし | 選択の状態 |
| ListItem の `aria-disabled="true"` | 有無 | なし | `disabledSelection` |

### 寸法

`packages/react-components/react-list/library/src/components/List/useListStyles.styles.ts:11-16` と `packages/react-components/react-list/library/src/components/ListItem/useListItemStyles.styles.ts:14-47` から写した。

| 対象 | 値 |
|---|---|
| List と ListItem | `padding: 0`、`margin: 0`、`text-indent: 0`、`list-style-type: none` |
| 選択できるかフォーカスできる項目 | `display: flex`、`cursor: pointer` |
| 選択できない項目 | `cursor: default` |
| checkmark | `align-self: center`。中の `.fui-Checkbox__indicator` に `margin: 4px`（v9 の直書き） |

### 色と状態

List と ListItem に、hover、pressed、selected の背景の指定はない。選択はチェックボックス（Checkbox の色）で示す。

### フォーカス・動き・ハイコントラスト

- フォーカス: `createCustomFocusIndicatorStyle` で、`outline: strokeWidthThick solid colorStrokeFocus2`、`border-radius: borderRadiusMedium` を当てる（`useListItemStyles.styles.ts:19-25`）。`[data-fui-focus-visible]` を `:focus-visible` で近似した。
- 動きとハイコントラストの規則はない（Checkbox の規則による）。

### 実装の例

```html demo
<ul class="fui-List" role="list" aria-label="チームの連絡先" style="display:flex;flex-direction:column;gap:8px;width:100%;max-width:280px">
  <li class="fui-ListItem" tabindex="0">
    <div class="fui-Persona">
      <span class="fui-Avatar fui-Persona__avatar" data-fui-enhance data-name="Kat Larsson" data-color="colorful"></span>
      <span class="fui-Persona__primaryText">Kat Larsson</span>
      <span class="fui-Persona__secondaryText">デザイナー</span>
    </div>
  </li>
  <li class="fui-ListItem" tabindex="0">
    <div class="fui-Persona">
      <span class="fui-Avatar fui-Persona__avatar" data-fui-enhance data-name="鈴木 花子" data-color="colorful"></span>
      <span class="fui-Persona__primaryText">鈴木 花子</span>
      <span class="fui-Persona__secondaryText">エンジニア</span>
    </div>
  </li>
  <li class="fui-ListItem" tabindex="0">
    <div class="fui-Persona">
      <span class="fui-Avatar fui-Persona__avatar" data-fui-enhance data-name="Kevin Sturgis" data-color="colorful"></span>
      <span class="fui-Persona__primaryText">Kevin Sturgis</span>
      <span class="fui-Persona__secondaryText">プロダクト マネージャー</span>
    </div>
  </li>
</ul>
```

Tab で項目にフォーカスすると、2px の輪が出る。上下の矢印の移動は JS が要る。

選択できる一覧は、`role="listbox"` と `role="option"` にし、選択の部品の章の Checkbox を checkmark に置く。

```html
<ul class="fui-List" role="listbox" aria-multiselectable="true" aria-label="参加者">
  <li class="fui-ListItem" role="option" tabindex="0" aria-selected="false">
    <span class="fui-Checkbox fui-ListItem__checkmark">…</span>
    <span>Kat Larsson</span>
  </li>
</ul>
```

### v9 との差と未確認の点

- **未実装**: 上下の矢印での移動、Space と Enter の選択と実行、右矢印と左矢印での項目の中への出入りは再現していない。
- **近似**: フォーカスできる項目と選択できる項目を、`tabindex="0"` と `aria-selected` の有無で判定する。
- Web Components v3 の手元の対象に List はない。
