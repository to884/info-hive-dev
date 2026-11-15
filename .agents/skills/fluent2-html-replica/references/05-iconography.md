# アイコン

この章は、Fluent 2 のアイコンを React を使わない HTML で使うための規則を定める。

結論を先に書く。

- UI のアイコンは Fluent System Icons（`@fluentui/svg-icons`、MIT License）だけを使い、インラインの SVG で置く。`<svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true" focusable="false">` の形にする。
- 標準の大きさは 20px である。small の入力欄は 16px、large の部品は 24px にする。12px は情報の表示だけに使う。部品の大きさに合う素材（`_16_`、`_20_`、`_24_`）を選び、別の大きさの素材を拡大縮小しない。
- 既定は Regular である。Filled は、選択の状態（Tab の選択、ToggleButton の押下）と、subtle と transparent のボタンや MenuItem のホバーに使う。切り替えは、Regular と Filled の 2 つの SVG を並べ、CSS の `display` で入れ替える。
- 色は文字の色（`currentColor`）を継ぐ。色を足すときは 1 色だけにする。

## アイコンの種類

サイト（fluent2.microsoft.design/iconography）は、アイコンを 3 種類に分ける。

| 種類 | 使う所 | この設計書での扱い |
|---|---|---|
| システムアイコン | コマンドバー、ナビゲーション、状態の表示など、UI の中 | Fluent System Icons を使う |
| プロダクトの起動アイコン | Microsoft のアプリを表す | 使わない。使うときは Microsoft の規定に従う（ライセンスの節） |
| ファイルの種類のアイコン | 文書や形式を表す（多色） | この設計書では扱わない |

## Regular と Filled

- Regular は道案内に使う。ダウンロード、購入、起動のように、使える操作を見つけて選ぶ場面である。
- Filled は、選択の状態の強調と、重みと読みやすさが要る小さな場面に使う。
- 修飾子（modifier）は、関連する操作など、より具体的な意味を足すための小さな記号である。常に Filled を使い、アイコンの右下に置く。意味が複雑になるなら使わない。
- 名前は機能ではなく形や物で付ける（「セキュリティ」ではなく「盾」）。
- 文化で意味が変わる記号があるので、使う地域で意味を確かめる。

### 実装の例

左が Regular、右が Filled である。単独で Filled を見せるときは、`fui-Icon-filled` を付けない（`fluent2-base.css` が既定で隠すため）。

```html demo
<div class="f2-stack" data-direction="horizontal" data-gap="xxl">
  <span class="f2-stack" data-direction="horizontal" data-gap="s">
    <svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true" focusable="false"><path d="M15.5 4A2.5 2.5 0 0 1 18 6.5v8a2.5 2.5 0 0 1-2.5 2.5h-11A2.5 2.5 0 0 1 2 14.5v-8A2.5 2.5 0 0 1 4.5 4zM17 7.96l-6.75 3.97a.5.5 0 0 1-.42.04l-.08-.04L3 7.96v6.54c0 .83.67 1.5 1.5 1.5h11c.83 0 1.5-.67 1.5-1.5zM15.5 5h-11C3.67 5 3 5.67 3 6.5v.3l7 4.12 7-4.12v-.3c0-.83-.67-1.5-1.5-1.5"/></svg>
    <svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true" focusable="false"><path d="M18 7.37v7.13a2.5 2.5 0 0 1-2.5 2.5h-11A2.5 2.5 0 0 1 2 14.5V7.37l7.75 4.56c.15.1.35.1.5 0zM15.5 4a2.5 2.5 0 0 1 2.48 2.22L10 10.92l-7.98-4.7A2.5 2.5 0 0 1 4.5 4z"/></svg>
    <span>mail</span>
  </span>
  <span class="f2-stack" data-direction="horizontal" data-gap="s">
    <svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true" focusable="false"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63zm.9.44L8.07 7.25a1 1 0 0 1-.75.55L3 8.43l3.12 3.04a1 1 0 0 1 .3.89l-.75 4.3 3.87-2.03a1 1 0 0 1 .93 0l3.86 2.03-.74-4.3a1 1 0 0 1 .29-.89L17 8.43l-4.32-.63a1 1 0 0 1-.75-.55z"/></svg>
    <svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true" focusable="false"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63z"/></svg>
    <span>star</span>
  </span>
</div>
```

## 大きさ

### 大きさの段階

- `@fluentui/svg-icons` の素材の大きさは 10、12、16、20、24、28、32、48px である。各ファイルはその大きさに合わせて描かれている。すべての名前、大きさ、スタイルの組み合わせがあるわけではない（microsoft/fluentui-system-icons の `packages/svg-icons/README.md`）。
- React の `@fluentui/react-icons` には、大きさ付き（`Mail24Regular`）と大きさなし（`MailRegular`。既定は `1em` で `font-size` に従う）がある。v9 の部品は大きさなしの版を前提に、スロットの `font-size`、`width`、`height` で大きさを決める。React を使わない HTML では、部品の大きさに合う素材を選ぶ。

サイトの指針:

- 12px のアイコンは情報の表示用で、操作の対象には小さすぎることが多い。小さいアイコンは情報の補足に使い、操作に使わない。
- 精密な操作ほど小さくできる。小さい画面では、タッチターゲットを確保するために大きめにする。

### 部品での大きさの対応（コード）

| 部品 | small | medium（既定） | large | 出典 |
|---|---|---|---|---|
| Button のアイコン | 20px | 20px | 24px | `packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:131-133`、同 `:526-539` |
| アイコンだけの Button の幅 | 24px | 32px | 40px | `packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:502-521` |
| Input、SearchBox の前後のアイコン | 16px | 20px | 24px | `packages/react-components/react-input/library/src/components/Input/useInputStyles.styles.ts:309-324`、`packages/react-components/react-search/library/src/components/SearchBox/useSearchBoxStyles.styles.ts:92-108` |
| Select、Combobox、Dropdown の開閉のアイコン | 16px | 20px | 24px | `packages/react-components/react-select/library/src/components/Select/useSelectStyles.styles.ts:14-18`、`packages/react-components/react-combobox/library/src/utils/internalTokens.ts:1-5` |
| Tab のアイコン | 20px | 20px | 24px | `packages/react-components/react-tabs/library/src/components/Tab/useTabStyles.styles.ts:540-554` |
| MenuItem のアイコン、サブメニューの印 | — | 20px | — | `packages/react-components/react-menu/library/src/components/MenuItem/useMenuItemStyles.styles.ts:110-129` |
| Breadcrumb のアイコン | 12px | 16px | 20px | `packages/react-components/react-breadcrumb/library/src/components/BreadcrumbButton/useBreadcrumbButtonStyles.styles.ts:34-45` |
| TableCellLayout の media | extra-small 16px | small と medium 20px | primary 24px | `packages/react-components/react-table/library/src/components/TableCellLayout/useTableCellLayoutStyles.styles.ts:46-56` |
| Tag のアイコン | extra-small 12px、small 16px | 20px | — | `packages/react-components/react-tags/library/src/components/Tag/useTagStyles.styles.ts:26-28`、同 `:213-230` |
| Badge のアイコン | tiny 6px、extra-small 10px、small 12px | 12px | large 16px、extra-large 20px | `packages/react-components/react-badge/library/src/components/Badge/useBadgeStyles.styles.ts:259`、同 `:279-296` |
| Field の検証メッセージのアイコン | — | 12px | — | `packages/react-components/react-field/library/src/components/Field/useFieldStyles.styles.ts:17`、同 `:94-103` |
| ToolbarButton（縦） | — | 24px | — | `packages/react-components/react-toolbar/library/src/components/ToolbarButton/useToolbarButtonStyles.styles.ts:11-14` |

まとめると、標準は 20px である。small の部品は、入力欄で 16px、ボタンとタブで 20px のまま。large の部品は 24px。12px は情報の表示（Badge、Field の検証、small の Breadcrumb）に限る。

### 実装の例

`mail` の 16px、20px、24px の素材を、それぞれの大きさで置いた。素材ごとに線の太さと細部が調整されているので、1 つの素材を拡大縮小しない。

```html demo
<div class="f2-stack" data-direction="horizontal" data-gap="xxl">
  <span class="f2-stack" data-direction="horizontal" data-gap="xs">
    <svg class="fui-Icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true" focusable="false"><path d="M2 6.04V11c0 1.1.9 2 2 2h8a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2zM4 4h8a1 1 0 0 1 1 1v.74l-5 2.7-5-2.7V5a1 1 0 0 1 1-1M3 6.88l4.76 2.56a.5.5 0 0 0 .48 0L13 6.88V11a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1z"/></svg>
    <span>16px</span>
  </span>
  <span class="f2-stack" data-direction="horizontal" data-gap="xs">
    <svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true" focusable="false"><path d="M15.5 4A2.5 2.5 0 0 1 18 6.5v8a2.5 2.5 0 0 1-2.5 2.5h-11A2.5 2.5 0 0 1 2 14.5v-8A2.5 2.5 0 0 1 4.5 4zM17 7.96l-6.75 3.97a.5.5 0 0 1-.42.04l-.08-.04L3 7.96v6.54c0 .83.67 1.5 1.5 1.5h11c.83 0 1.5-.67 1.5-1.5zM15.5 5h-11C3.67 5 3 5.67 3 6.5v.3l7 4.12 7-4.12v-.3c0-.83-.67-1.5-1.5-1.5"/></svg>
    <span>20px（標準）</span>
  </span>
  <span class="f2-stack" data-direction="horizontal" data-gap="xs">
    <svg class="fui-Icon" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false"><path d="M5.25 4h13.5a3.25 3.25 0 0 1 3.24 3.07l.01.18v9.5a3.25 3.25 0 0 1-3.07 3.24l-.18.01H5.25a3.25 3.25 0 0 1-3.24-3.07L2 16.75v-9.5a3.25 3.25 0 0 1 3.07-3.24zh13.5zM20.5 9.37l-8.15 4.3q-.3.14-.6.04l-.1-.05L3.5 9.37v7.38c0 .92.7 1.67 1.6 1.74l.15.01h13.5c.92 0 1.67-.7 1.74-1.6l.01-.15zM18.75 5.5H5.25c-.92 0-1.67.7-1.74 1.6l-.01.15v.43l8.5 4.47 8.5-4.47v-.43c0-.92-.7-1.67-1.6-1.74z"/></svg>
    <span>24px</span>
  </span>
</div>
```

## 色

- アイコンは `currentColor` で文字の色を継ぐのが基本である。ルートの `<svg>` に `fill="currentColor"` を付ける。`fluent2-base.css` も `.fui-Icon` に `fill: currentColor` を当てる。
- 部品は、アイコンのスロットに文字と別の色を指定することがある。

| 部品 | アイコンの色 | 出典 |
|---|---|---|
| Input の前後のアイコン | `colorNeutralForeground3` | `packages/react-components/react-input/library/src/components/Input/useInputStyles.styles.ts:305` |
| Tab の未選択のアイコン | `colorNeutralForeground2` | `packages/react-components/react-tabs/library/src/components/Tab/useTabStyles.styles.ts:99-101` |
| Tab の選択のアイコン | `colorCompoundBrandForeground1` | `packages/react-components/react-tabs/library/src/components/Tab/useTabStyles.styles.ts:158-160` |
| 無効の部品のアイコン | `colorNeutralForegroundDisabled` | `packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:330-368` |

サイトの指針:

- 色を加える前によく検討する。使うなら 1 色だけにし、コントラストに配慮する。システムアイコンは単色の塗りだけである。
- 意味を担うアイコンの形は、隣の色に対して 3:1 以上のコントラストが要る（WCAG 1.4.11。svg-icons の README も同じことを書く）。色だけで状態を伝えない。

## 文字との並べ方

- 部品のアイコンのスロットは `display: inline-flex; align-items: center; justify-content: center;` にし、幅と高さをアイコンの大きさに固定する（`packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:126-136`）。MenuItem は `line-height: 0` と `flex-shrink: 0` も付ける（`packages/react-components/react-menu/library/src/components/MenuItem/useMenuItemStyles.styles.ts:110-119`）。
- 文字との間隔は、アイコンの側の margin か、親の gap で取る。

| 部品 | アイコンと文字の間 | 取り方 | 出典 |
|---|---|---|---|
| Button（small） | 4px（`spacingHorizontalXS`） | アイコンの `margin-inline-end`（後ろに置くと `margin-inline-start`） | `packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:531`、同 `:545-550` |
| Button（medium） | 6px（`spacingHorizontalSNudge`） | 同上 | `packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:135` |
| Button（large） | 6px（`spacingHorizontalSNudge`） | 同上 | `packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:541` |
| MenuItem | 4px | 親の gap | `packages/react-components/react-menu/library/src/components/MenuItem/useMenuItemStyles.styles.ts:41` |
| Field の検証メッセージ | 4px | アイコンの margin | `packages/react-components/react-field/library/src/components/Field/useFieldStyles.styles.ts:94-103` |

- Field の検証のアイコンは、負の margin と `vertical-align` で文字の行に合わせる（`packages/react-components/react-field/library/src/components/Field/useFieldStyles.styles.ts:94-106`）。
- 文章の行の中にアイコンを置くときは、`fluent2-base.css` の `.fui-Icon` が `vertical-align: middle` を当てる（v9 の既定は `baseline`。差と未確認の点の節）。

## 状態での切り替え（bundleIcon）

v9 の `bundleIcon(Filled, Regular)` は、2 つの SVG を並べて出力し、`fui-Icon-filled` と `fui-Icon-regular` の class の `display` を部品の CSS で入れ替える。class 名は、v9 の Tab のスタイルが `@fluentui/react-icons` の定数と一致させると書いている（`packages/react-components/react-tabs/library/src/components/Tab/useTabStyles.styles.ts:20-25`）。

| 部品 | 状態 | 切り替え | アイコンの色 | 出典 |
|---|---|---|---|---|
| Button（subtle） | hover、pressed | Filled を見せ、Regular を隠す | `colorNeutralForeground2BrandHover`、`colorNeutralForeground2BrandPressed` | `packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:195-223` |
| Button（transparent） | hover、pressed | Filled を見せる | 文字ごと `colorNeutralForeground2BrandHover`、`colorNeutralForeground2BrandPressed` | `packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:247-269` |
| Button（disabled） | hover、pressed | Regular に戻す | `colorNeutralForegroundDisabled` | `packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:330-368` |
| ToggleButton | checked（`aria-pressed="true"`） | Filled を見せる | — | `packages/react-components/react-button/library/src/components/ToggleButton/useToggleButtonStyles.styles.ts:19-31` |
| MenuItem | hover | Filled を見せる | `colorNeutralForeground2BrandSelected` | `packages/react-components/react-menu/library/src/components/MenuItem/useMenuItemStyles.styles.ts:43-55` |
| Tab | selected（`aria-selected="true"`） | Filled を見せる（未選択は Regular） | `colorCompoundBrandForeground1`（hover で `colorCompoundBrandForeground1Hover`） | `packages/react-components/react-tabs/library/src/components/Tab/useTabStyles.styles.ts:531-536`、同 `:555-562`、同 `:158-164` |
| Nav の項目 | selected | 2 つを grid で重ね、Filled をフェードインする | `colorNeutralForeground2BrandSelected` | `packages/react-components/react-nav/library/src/components/sharedNavStyles.styles.ts:113-164` |

primary、secondary、outline の Button は、hover でアイコンを切り替えない。

React を使わない HTML では、Regular の SVG に `fui-Icon fui-Icon-regular`、Filled の SVG に `fui-Icon fui-Icon-filled` を付けて、同じスロットに並べる。`fluent2-base.css` が既定で `.fui-Icon-filled { display: none; }` にしている。入れ替えは各部品の CSS が行う。

```css
/* 部品の CSS での入れ替えの形（Button の subtle の例。値は各部品の章で定める） */
.fui-Button:where([data-appearance="subtle"]):hover .fui-Icon-filled { display: inline; }
.fui-Button:where([data-appearance="subtle"]):hover .fui-Icon-regular { display: none; }
```

### 実装の例

subtle の Button に Regular と Filled を並べた例である。ポインターを載せると Filled に替わる。入れ替えは「ボタン、リンク、ツールバー、ラベル、フィールド」の章の `components/actions.css` が担う（この章の CSS ではない）。2 つ目は、アイコンだけのボタンで、名前をボタンの `aria-label` に付ける。

```html demo
<div class="f2-stack" data-direction="horizontal" data-gap="m">
  <button class="fui-Button" data-appearance="subtle" type="button">
    <span class="fui-Button__icon">
      <svg class="fui-Icon fui-Icon-regular" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true" focusable="false"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63zm.9.44L8.07 7.25a1 1 0 0 1-.75.55L3 8.43l3.12 3.04a1 1 0 0 1 .3.89l-.75 4.3 3.87-2.03a1 1 0 0 1 .93 0l3.86 2.03-.74-4.3a1 1 0 0 1 .29-.89L17 8.43l-4.32-.63a1 1 0 0 1-.75-.55z"/></svg>
      <svg class="fui-Icon fui-Icon-filled" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true" focusable="false"><path d="M9.1 2.9a1 1 0 0 1 1.8 0l1.93 3.91 4.31.63a1 1 0 0 1 .56 1.7l-3.12 3.05.73 4.3a1 1 0 0 1-1.45 1.05L10 15.51l-3.86 2.03a1 1 0 0 1-1.45-1.05l.74-4.3L2.3 9.14a1 1 0 0 1 .56-1.7l4.31-.63z"/></svg>
    </span>
    お気に入り
  </button>
  <button class="fui-Button" data-appearance="subtle" data-icon-only type="button" aria-label="メール">
    <span class="fui-Button__icon">
      <svg class="fui-Icon fui-Icon-regular" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true" focusable="false"><path d="M15.5 4A2.5 2.5 0 0 1 18 6.5v8a2.5 2.5 0 0 1-2.5 2.5h-11A2.5 2.5 0 0 1 2 14.5v-8A2.5 2.5 0 0 1 4.5 4zM17 7.96l-6.75 3.97a.5.5 0 0 1-.42.04l-.08-.04L3 7.96v6.54c0 .83.67 1.5 1.5 1.5h11c.83 0 1.5-.67 1.5-1.5zM15.5 5h-11C3.67 5 3 5.67 3 6.5v.3l7 4.12 7-4.12v-.3c0-.83-.67-1.5-1.5-1.5"/></svg>
      <svg class="fui-Icon fui-Icon-filled" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true" focusable="false"><path d="M18 7.37v7.13a2.5 2.5 0 0 1-2.5 2.5h-11A2.5 2.5 0 0 1 2 14.5V7.37l7.75 4.56c.15.1.35.1.5 0zM15.5 4a2.5 2.5 0 0 1 2.48 2.22L10 10.92l-7.98-4.7A2.5 2.5 0 0 1 4.5 4z"/></svg>
    </span>
  </button>
</div>
```

## React を使わない HTML での使い方

### 入手先とファイル名

| 方法 | 書き方 | 注意 |
|---|---|---|
| npm | `npm install @fluentui/svg-icons`。ファイルは `node_modules/@fluentui/svg-icons/icons/` | JavaScript の API はない。SVG のファイルだけである |
| CDN | `https://unpkg.com/@fluentui/svg-icons@1.1.345/icons/mail_20_regular.svg` | 本番では `latest` ではなく版を固定する（README の勧め）。2026-11-13 の時点の版は 1.1.345 |
| 一覧 | Storybook（microsoft.github.io/fluentui-system-icons）、リポジトリの `icons_regular.md` と `icons_filled.md` | 名前を探すのに使う |

- ファイル名は `{name}_{size}_{style}.svg` である（例 `mail_24_regular.svg`）。`name` は英小文字とアンダースコア、`size` は 10〜48 の数、`style` は `regular`、`filled`、`light`（一部だけ）、`color`（非推奨の多色）。
- 地域ごとの素材は `icons/{locale}/...` にある。向きを持つ素材は、名前に `_rtl` か `_ltr` を含むか、`icons/LTR/` と `icons/RTL/` にある。
- 素材のルートの `<svg>` は `xmlns`、`width`、`height`、`viewBox` だけを持ち、`fill` がない。子の `<path>` にも `fill` がない。ビルドのときに主色の `#212121` の塗りを取り除くので、そのままでは既定の黒で描かれる（README）。

### インライン SVG の書き方

取ってきた SVG を、次のように書き換えて HTML に埋め込む。

1. ルートの `<svg>` に `class="fui-Icon"` を足す。Regular と Filled を組にするときは `fui-Icon fui-Icon-regular` と `fui-Icon fui-Icon-filled` にする。
2. `fill="currentColor"` を足す。子の要素に固定の `fill` があれば、そちらが勝つので取り除く。
3. 装飾のアイコン（隣に文字がある）には `aria-hidden="true"` と `focusable="false"` を足す。
4. `width`、`height`、`viewBox` は素材の大きさのまま残す。

```html
<!-- 素材（mail_20_regular.svg）。path の d は長いので省いた -->
<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20"><path d="…"/></svg>

<!-- 埋め込む形 -->
<svg class="fui-Icon" width="20" height="20" viewBox="0 0 20 20"
     fill="currentColor" aria-hidden="true" focusable="false"><path d="…"/></svg>
```

アクセシビリティ（README の指針）:

- アイコンだけのボタンは、ボタンに `aria-label` を付け、アイコンは `aria-hidden="true"` にする。
- 意味を持つ単独のインライン SVG（状態を表すなど）は、`role="img"` と `aria-label` を付ける。
- 装飾のアイコンには `role="img"` や `aria-label` を付けない。
- 強制カラーのモードで見え方を確かめる。`currentColor` で描けば、文字の色と同じシステムの色になる。

### img と CSS マスク

- `<img src="mail_20_regular.svg">` で読むと、ページの `color` や `fill` で色を変えられない。テーマで色が変わる UI には使わない。
- CSS マスクで描く方法もある（`background-color: currentColor; mask-image: url(...); mask-size: contain;`）。同じオリジンか CORS の許可が要り、CSP の許可も要る。強制カラーでは `forced-color-adjust: preserve-parent-color` を付ける（README）。この設計書の部品はインライン SVG を使う。

### RTL

- `dir="rtl"` を付けても、SVG の形は変わらない。向きを持つアイコン（矢印、戻る、進む）は、`_rtl` の素材があれば差し替える。
- `@fluentui/react-icons` は、向きを持つアイコンを RTL で `transform: scaleX(-1)` で反転する（microsoft/fluentui-system-icons の `packages/react-icons/src/utils/useIconStyles.styles.ts`）。React を使わない HTML で同じことをするなら、次のように書く。

```css
/* 独自: RTL で左右を反転するアイコン。v9 の react-icons の反転に当たる */
.fui-Icon[data-flip-rtl]:dir(rtl) {
  transform: scaleX(-1);
}
```

この規則は `fluent2-base.css` にある。向きを持つアイコンの `<svg>` に `data-flip-rtl` を付ける。

## ライセンス

| 対象 | 条件 | 出典 |
|---|---|---|
| Fluent System Icons（`@fluentui/svg-icons`） | MIT License。`Copyright (c) 2020 Microsoft Corporation` | microsoft/fluentui-system-icons の `LICENSE`、`@fluentui/svg-icons` の `package.json` の `license` |
| プロダクトの起動アイコン（Microsoft のアプリのロゴ） | MIT の対象外。サイトは色の変更と、Microsoft のロゴの代わりに使うことを禁じる。48px 未満は簡略化した版を使い、48px を超えるときは完全版を 4 の倍数で拡大する | fluent2.microsoft.design/iconography |
| ファイルの種類のアイコン | MIT の対象外。16px、48px、96px で最もよく見える。形式は SVG と WebP | fluent2.microsoft.design/iconography |
| Office のアイコン、Fabric のアイコン（MDL2） | Microsoft Fabric Assets License Agreement（aka.ms/fluentui-assets-license）の対象。用途が限られる | microsoft/fluentui の `LICENSE` の末尾の注記 |

- SVG を埋め込んだ HTML や CSS を配布するときは、MIT の条件に従い、著作権表示と許諾の文を同梱する（例: `THIRD-PARTY-NOTICES` に LICENSE の全文を入れる）。
- Office のアイコンと Fabric のアイコンは使わない。

## v9 との差と未確認の点

- **大きさの決め方**: v9 は大きさなしのアイコンを `font-size` で拡大縮小する。React を使わない HTML では大きさ付きの素材を選ぶので、16px と 24px のアイコンは v9 の 20px の素材の拡大縮小とは細部が違う。v9 の部品が 20px の素材を 16px や 24px に縮めて表示しているかは、確かめていない（`@fluentui/react-icons` の大きさなしの版が、どの大きさの素材から作られるかを確かめていない）。
- **`fui-Icon` の display**: `@fluentui/react-icons` の SVG の計算値は `display: inline`、`line-height: 0`、`flex-shrink: 1` である。`fluent2-base.css` の `.fui-Icon` はこれに合わせた（本物の 9.75.2 と比べて確かめた）。
- **`@fluentui/react-icons` の SVG の属性**: 出力される `<svg>` の `fill` と `aria-hidden` の既定は、取得したソースに書かれておらず、確かめていない。この設計書は `fill="currentColor"`、`aria-hidden="true"`、`focusable="false"` を付ける。
- **状態の切り替えの網羅**: 表は v9 の主な部品だけである。ほかの部品の切り替えは、各部品の章で定める。
- **アイコンのグリッドとキーライン**: サイトにアイコンの余白、グリッド、キーラインの規定はない。
- **SVG の path**: この章の例の path は、unpkg の `@fluentui/svg-icons@1.1.345` の `mail_16_regular`、`mail_20_regular`、`mail_20_filled`、`mail_24_regular`、`star_20_regular`、`star_20_filled` から写した。

## 土台に取り入れたこと

- RTL で左右を反転する `.fui-Icon[data-flip-rtl]:dir(rtl)` を `fluent2-base.css` に足した（独自）。
- `.fui-Icon` から `vertical-align: middle` を外し、v9 と同じく `baseline` にした。文章の中でアイコンの縦の位置を整えたいときは、使う側で `vertical-align` を指定する。
