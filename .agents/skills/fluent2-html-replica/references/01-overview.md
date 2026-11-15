# Fluent 2 Web の全体像

この設計書は、Microsoft のデザインシステム Fluent 2 の Web 版を、React を使わない HTML と CSS で忠実に再現するための日本語の参照である。数値と見た目の基準は React v9（`@fluentui/react-components` 9.75.2）のコードに置く。値はトークン（CSS 変数）で書き、コンポーネントの見た目は v9 の styles を写した CSS（`assets/fluent2.css` の部品の部分）で再現する。この設計書は Microsoft の公式文書ではない。

## 設計原則

サイト（fluent2.microsoft.design の design-principles のページ）は、設計原則を「共有するビジョンを表し、判断の指針になる価値観」と位置づけ、4 つを挙げる。どの原則にも機能面と情緒面の 2 つの説明が付く。次の表はその要約である。

| 原則 | 機能面 | 情緒面 |
|---|---|---|
| Natural on every platform | 画面の大きさとプラットフォームの慣習に合わせる。ネイティブの部品とパターンを大半の場面で再利用し、残りの力を独自の体験に注ぐ | 予測でき、見慣れた体験は信頼を生む |
| Built for focus | 明快に伝え、よく動くことで、製品が邪魔をせず、人が自分のやり方で目的を果たせる | 視覚的なノイズを減らすと、人は落ち着いて自信を持てる |
| One for all, all for one | 多様な能力と視点を持つ人を初期から巻き込むと、制約の中でも強い解決策が生まれる | 受け入れられているという感覚が帰属感を生む |
| Unmistakably Microsoft | 色、音、イラスト、アイコンといった象徴の要素を製品間で共有し、認知と親しみを強める | 少しの個性が体験を魅力的にする |

React を使わない HTML と CSS に当てはめると、次のように読める（**推論**）。

- **Natural on every platform**: Web の慣習に従う。HTML のネイティブの要素とセマンティクスを使い、欧文は sentence case にする。
- **Built for focus**: 中立色を基調にし、ブランド色は主要な操作と選択状態に限る。トークンの大半が Neutral 系であることとも合う。
- **One for all, all for one**: アクセシビリティの規則（「コンテンツデザインとアクセシビリティ」の章）を必須の要件として扱う。
- **Unmistakably Microsoft**: ブランドの段階（`brandWeb`）、書体（`fontFamilyBase` の先頭の Segoe UI。`packages/tokens/src/global/fonts.ts:39-40`）、Fluent System Icons で Microsoft らしさを出す。

## Fluent 1 からの変更点

サイトの whatisnew のページは概要にとどまり、具体的な値は書いていない。Fluent 2 を、製品やプラットフォームをまたいで設計から開発へ移りやすくする次の段階と位置づけ、システムの水準の変更として 6 つの項目を見出しだけで挙げる。各項目の本文はない。

次の表の右の列は、各項目に当たりそうな資料をこの設計書が対応づけたもので、**推論**である（サイトの記述ではない）。

| 項目 | 対応しそうな資料 |
|---|---|
| Cohesive color system | 中立色の段階 `grey`、ブランドの 16 段、shared の色（status 7 色、persona 28 色。`packages/tokens/src/sharedColorNames.ts:2-42`） |
| Token system | グローバルとエイリアスの 2 層。`@fluentui/tokens` パッケージ |
| Standardized corners | `borderRadius*` の段階（`packages/tokens/src/global/borderRadius.ts:3-15`。None 0 から Circular 10000px まで） |
| Customizability | `createLightTheme(brand)` と `createDarkTheme(brand)`（`packages/tokens/src/utils/createLightTheme.ts:11-33`）。ブランドの 16 段を差し替えてテーマを作る |
| Robust usage guidance | コンポーネントごとの usage のページの、文言と操作の指針 |
| Accessibility notation | accessibility のページの、フォーカス順、スクリーンリーダー向けの注記、意味の構造を設計の仕様に書く求め |

プラットフォームの水準の変更は、各コンポーネントの概要のページに譲られている。

## Web の実装と基準の版

### 2 つの実装

サイトの components/web のページは、Web の実装として 2 つを挙げる。

| 実装 | 書き方 | スタイル | テーマの当て方 |
|---|---|---|---|
| Fluent UI React v9（`@fluentui/react-components`） | React と TypeScript | CSS-in-JS の Griffel | アプリのルートの `FluentProvider` に `theme={webLightTheme}` を渡す |
| Fluent UI Web Components v3（`@fluentui/web-components`） | FAST Element と TypeScript | CSS 変数として公開したトークン。`*.styles.css` を配る | `@fluentui/tokens` の `webLightTheme` を `setTheme` に渡す |

- Web Components v3 は v2 を土台から書き直したもので、FAST Element v3 の上に作られ、テーマは `setTheme()` で与える（`packages/web-components/src/_docs/developer/migration.mdx:7-17`）。
- 同じコンポーネントでも、2 つの実装は細部が違う。たとえば Button のフォーカスの輪は、v9 が枠の色と内側の `box-shadow` で描き（`packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:105-113`）、v3 は外側の `box-shadow` で描く（`packages/web-components/src/button/button.styles.css:55-59`）。

### この設計書の基準

| 項目 | 基準 |
|---|---|
| 数値と見た目 | React v9。`@fluentui/react-components` 9.75.2（`packages/react-components/react-components/package.json:3`） |
| トークン | `@fluentui/tokens` 1.0.0-alpha.24（`packages/tokens/package.json:3`）。版の名前は alpha だが、v9 と v3 の両方がこれに依存する |
| CSS の書き方の参考 | Web Components v3 の 3.2.1（`packages/web-components/package.json:4`）。v9 と違えば v9 を採る |
| ソースの版 | microsoft/fluentui の commit `f9720c35ba893c9630f4c0389d07dc6d6fd6068d`（2026-11-12） |
| サイトとコードが食い違うとき | コードに従い、各章の「v9 との差と未確認の点」に両方を書く |

v9 を基準にするのは、この設計書の約束（`docs/conventions.md`）で決めたことである。サイトの components/web のページが挙げる 47 個のコンポーネントは、React にしかないものと両方にあるものに分かれており、v9 を基準にすればすべての部品を同じ版の値で書ける（**推論**。Web Components にしかない部品がないことは、ページの区分から読んだ）。v3 は React を使わない CSS で書かれているので、セレクターの組み方（属性による状態、論理プロパティ）の参考にする。

### テーマを CSS 変数にする仕組み

どちらの実装も、テーマのオブジェクトのキーを、同じ名前の CSS 変数として書き出す。

- v9 の `FluentProvider` は `createCSSRuleFromTheme(selector, theme)` で `selector { --<トークン>: <値>; }` という規則を作る（`packages/react-components/react-provider/library/src/components/FluentProvider/createCSSRuleFromTheme.ts:46-60`）。
- v3 の `setTheme` は `--<トークン>:<値>;` を並べた文字列を作り（`packages/web-components/src/theme/set-theme.ts:81-94`）、全体に当てるときは `html` の規則にする。

`assets/fluent2.css` のトークンの部分（`fluent2-tokens.css`）は、同じ名前の変数を `:root` と `[data-theme]` と `.fui-FluentProvider` に宣言する。プロバイダーの既定のスタイル（文字の色、背景、書体）は、土台の部分（`fluent2-base.css`）が当てる。詳しくは「React を使わない HTML への適用」の章で扱う。

```html demo
<div style="display:flex;flex-wrap:wrap;gap:12px">
  <div data-theme="light" style="padding:16px;min-width:220px;border:1px solid var(--colorNeutralStroke2)">
    <span class="fui-Text fui-Subtitle2" data-block>data-theme="light"</span>
    <span class="fui-Text" style="color:var(--colorNeutralForeground3)">同じ変数名で、値だけが変わる</span>
  </div>
  <div data-theme="dark" style="padding:16px;min-width:220px;border:1px solid var(--colorNeutralStroke2)">
    <span class="fui-Text fui-Subtitle2" data-block>data-theme="dark"</span>
    <span class="fui-Text" style="color:var(--colorNeutralForeground3)">同じ変数名で、値だけが変わる</span>
  </div>
</div>
```

## トークンの 2 層と命名

### 2 層

サイトの design-tokens のページは、トークンを 2 層で説明する。

- **グローバルトークン**: 文脈に依存しない生の値。16 進数の色、文字の大きさ、角丸、線幅、動きの値を持つ。
- **エイリアストークン**: グローバルの値を参照して意味を与える。名前を見れば役割がわかるので、値を覚えなくても、どこにどう使うかを判断できる。影や書体のスタイルのような複合的な値も、エイリアスにまとめる。

ソースでは、どれが CSS 変数になるかが決まっている。

- CSS 変数になるのは、テーマの型 `Theme` のキーだけである（`packages/tokens/src/types.ts:800-815`）。色のエイリアス、palette と status の色、影、色以外の段階の値（文字の大きさ、行の高さ、太さ、書体、角丸、線幅、間隔、時間、曲線）が含まれる。
- **色のグローバルトークンは CSS 変数にならない**。`grey`、ブランドの段階、shared の色は、エイリアスを作る関数の入力になるだけである。`--grey14` という変数はない。この設計書は、ブランドの差し替えのためだけに、補助の変数 `--fui-brand-10`〜`--fui-brand-160` を独自に出す（「色」の章）。
- 色以外の段階の値（`fontSize*`、`borderRadius*`、`spacing*` など）は、ソースでは `global/` に置かれているが、そのまま `Theme` のキーになり、CSS 変数になる（`packages/tokens/src/utils/createLightTheme.ts:14-24`）。
- 書体のスタイル（`body1` など）は 4 つのトークンを束ねた JavaScript のオブジェクトで、CSS 変数ではない（`packages/tokens/src/global/typographyStyles.ts`）。この設計書は class（`fui-Body1` など）として出す。
- `zIndex*` はテーマに含まれない。`var(--zIndexPopup, 2000)` のように既定値を付けて参照する（`packages/tokens/src/tokens.ts:566-618`。Background 0、Content 1、Overlay 1000、Popup 2000、Messages 3000、Floating 4000、Priority 5000、Debug 6000）。

### CSS 変数の名前

CSS 変数の名前は、`--` の後にトークンのキーの camelCase をそのまま続けたものである（`packages/tokens/src/tokens.ts:5` の `'var(--colorNeutralForeground1)'`）。v9 の styles の `tokens.colorNeutralForeground1` は、React を使わない CSS では `var(--colorNeutralForeground1)` と読み替えられる。

Web Components の文書は、テーマの CSS 変数をじかに使ってはならないと書く。変数の名前は内部の実装で、変わる可能性があるという理由である（`packages/web-components/src/_docs/developer/theming.mdx:43-45`）。React を使わない HTML と CSS では変数をじかに使うしかないので、この設計書は**変数名を上の commit の版に固定する**ことで、その代わりとする。版を上げるときは、名前の変化を確かめる。

### 命名の形

サイトは命名の文法を示していない。次はソースから読んだ形である。

| 種類 | 形 | 例 |
|---|---|---|
| 色 | `color` + 系統 + 役割 + 番号 + 修飾 + 状態 | `colorNeutralForeground2BrandHover`、`colorBrandBackground` |
| 文字の大きさと行の高さ | `fontSize` または `lineHeight` + `Base`（100〜600）または `Hero`（700〜1000） | `fontSizeBase300`、`lineHeightHero800` |
| 太さと書体 | `fontWeight` + Regular、Medium、Semibold、Bold。`fontFamily` + Base、Monospace、Numeric | `fontWeightSemibold` |
| 角丸 | `borderRadius` + None、Small、Medium、Large、XLarge、2XLarge〜6XLarge、Circular | `borderRadiusMedium` |
| 線幅 | `strokeWidth` + Thin、Thick、Thicker、Thickest | `strokeWidthThin` |
| 間隔 | `spacing` + Horizontal または Vertical + None、XXS、XS、SNudge、S、MNudge、M、L、XL、XXL、XXXL | `spacingHorizontalM` |
| 時間と曲線 | `duration` + UltraFast〜UltraSlow。`curve` + Accelerate、Decelerate の Max、Mid、Min と EasyEase、Linear | `durationNormal`、`curveDecelerateMid` |
| 影 | `shadow` + 2、4、8、16、28、64（と `Brand`） | `shadow16` |

- 色の名前は語順が一定ではない（`colorNeutralStrokeOnBrand2Hover`、`colorBrandStroke2Contrast`）。**名前は規則から組み立てず、`packages/tokens/src/types.ts` から写す。**
- 大きさの表し方は、間隔が `XXL` のように文字を重ね、角丸が `2XLarge` のように数字を付ける。揃っていないので、これも写す。
- 全トークンの値は `references/tokens.md`（生成物）と「トークンの一覧」の章にある。

## この設計書の使い方

作るものに応じて、次の章を見る。

| 章 | 何が書いてあるか | 見る場面 |
|---|---|---|
| Fluent 2 Web の全体像（この章） | 基準の版、トークンの考え方、値の出どころ | 最初に 1 度 |
| 色 | パレット、エイリアスの使いどころ、状態、ブランドの差し替え、ダーク、ハイコントラスト、コントラスト | 色を選ぶとき、ブランドを替えるとき |
| タイポグラフィ | 書体の段階、Text、日本語の書体 | 文字の大きさと太さを決めるとき |
| レイアウト、間隔、形状、線 | 間隔、角丸、線幅 | 余白と形を決めるとき |
| アイコン | Fluent System Icons の置き方 | アイコンを置くとき |
| エレベーション、マテリアル、モーション | 影、重なりの順、動き | 浮かせる面と動きを作るとき |
| コンテンツデザインとアクセシビリティ | 文言、日本語の UI の表記、フォーカス、キーボード、拡大、強制カラー | 文言を書くとき、受け入れの確認のとき |
| React を使わない HTML への適用 | ファイルの読み込み、プロバイダー相当の要素、テーマの切り替え、フォーカスと強制カラーの共通の規則 | ページを組み始めるとき |
| コンポーネントの各章 | コンポーネントごとの構造、バリエーション、寸法、色と状態、例 | 部品を作るとき |
| トークンの一覧 | 全トークンの値 | 値を引くとき |

コンポーネントの節は、どれも同じ順の小見出しを持つ: 概要と使い分け、構造とマークアップ、バリエーション、寸法、色と状態、フォーカス・動き・ハイコントラスト、実装の例、v9 との差と未確認の点。

使うファイル:

| ファイル | 中身 | 手で直すか |
|---|---|---|
| `assets/fluent2.css` | すべての CSS をまとめたもの。中身はトークン、土台、部品、書体の 4 つの部分で、章ではこの部分を `fluent2-tokens.css`、`fluent2-base.css`、`fluent2-components.css`、`fluent2-typography.css` の名前で呼ぶ | 直さない（生成物） |
| `assets/fluent2.js` | 部品の振る舞い | 直さない（生成物） |
| `references/tokens.md` | トークンの全値の表 | 直さない（生成物） |

部品ごとの CSS と JS、土台の CSS の原本は、開発用のリポジトリ（非公開）の `src/` にある。直すときはそちらを直し、`fluent2.css` と `fluent2.js` を作り直す。

## 値の出どころの区別

この設計書の値は、出どころで 3 つに分ける。原稿と CSS は、どれに当たるかがわかるように書く。

| 区別 | 意味 | 書き方 | 例 |
|---|---|---|---|
| **抽出** | ソースから写した値 | 出典をリポジトリからの相対パスと行で書く | `fontSizeBase300` は 14px（`packages/tokens/src/global/fonts.ts:6`） |
| **直書き** | v9 自身がトークンを使わずに px などを書いている値 | CSS に `/* v9 の直書き */` と注記する | フォーカスの輪の太さ 2px（`createFocusOutlineStyle` の既定） |
| **推論** | 計算や推論で出した値と判断 | 原稿で「推論」と書く | コントラスト比の計算結果、スタイルの用途の読み取り |

- サイト（fluent2.microsoft.design）の文章は要約し、引用しない。
- サイトとコードが食い違うときは、コードに従う。例: サイトは Subtitle 1 の行の高さを 26px とするが、コードは 28px（`packages/tokens/src/global/fonts.ts:22`）。
- 生成された alias のファイルの行末のコメントにある hex は使わない。ブランドの値が実際と違う（「色」の章）。
- この設計書の独自の判断（日本語の書体、日本語の UI の表記、アクセシビリティの基準の版など）は、本文で「独自」と書く。

## v9 との差と未確認の点

- **React v9 の対応ブラウザー**: 一次資料の対応表は手に入らなかった。この設計書は、`:has()`、`:where()`、`:focus-visible`、`@starting-style`、ネイティブの `<dialog>` と `popover` 属性を使い、2026 年の主要なブラウザーを対象にする。
- **サイトの例とソースの食い違い**: サイトの develop のページは Web Components の登録を `ButtonDefinition.define(FluentDesignSystem.registry)` の形で示すが、手元の quick-start は `import '@fluentui/web-components/button.js'` か `Button.define(definition)` を示す。この設計書は Web Components を動かさないので影響はないが、v3 の文書を読むときは手元のソースを正とする。
- **v8 と v9 の位置づけ**: v9 が今後の系統で、v8 からの移行が勧められているという情報は検索結果の抜粋によるもので、一次資料では確かめていない。
- **Web 用のハイコントラストのテーマ**: 公開されたテーマにはない（`packages/tokens/src/index.ts:1-9`）。強制カラーで扱う（「色」の章）。
