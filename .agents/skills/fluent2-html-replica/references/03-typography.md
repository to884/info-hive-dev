# タイポグラフィ

Fluent 2 の Web の文字は、17 個の書体のスタイル（type ramp）と、それを当てる Text コンポーネントで組む。本文の既定は Body1（14px / 20px / 400）である。値はすべてトークン（`--fontSizeBase300` など）で参照し、px を直接書かない。日本語の書体は Fluent 2 の Web にないので、`fluent2-base.css` が独自に補う。

## 書体の段階

### 17 個のスタイル

段階の型は 17 個のキーを持つ（`packages/tokens/src/types.ts:603-621`）。値は `packages/tokens/src/global/typographyStyles.ts` にあり、どれも `fontFamilyBase` と、サイズ、行の高さ、太さのトークンを 1 組にしたものである。下の表は生成物で、見本はこのページの書体の並び（日本語の拡張を含む）で描く。

<!-- spec:tokens-typography -->

- サイズは Base（100〜600）と Hero（700〜1000）の 2 系統に分かれる（`packages/tokens/src/types.ts:535-561`）。Hero は見出しや表示用の大きな文字である。
- 太さは Regular 400、Medium 500、Semibold 600、Bold 700 の 4 つ（`packages/tokens/src/global/fonts.ts:31-36`）。名前の Strong は Semibold、Stronger は Bold を表す。Medium はどのスタイルも使わず、Text の `data-weight="medium"` でだけ当たる。
- 本文の既定は Body1 である。FluentProvider の root も `typographyStyles.body1` を当てる（`packages/react-components/react-provider/library/src/components/FluentProvider/useFluentProviderStyles.styles.ts:14-19`）。この設計書では `fluent2-base.css` の `.fui-FluentProvider` と `[data-theme]` が同じ宣言を持つ。

### スタイルの使いどころ

サイトの表にも一次資料にも、スタイルごとの用途の列はない。次の表は、v9 のコンポーネントの styles での使用例から読んだもので、**推論**である（数は `typographyStyles.<キー>` の出現数。react-text 自身、テスト、ストーリーを除く）。

| スタイル | 使用例（v9 のコンポーネント） | 出現数 |
|---|---|---|
| `body1` | Input の medium など、地の文と既定の大きさの部品 | 33 |
| `caption1` | Field の補助文、Input の small、TableCellLayout の description | 22 |
| `body2` | Input、Combobox、Tab の large | 8 |
| `subtitle2` | Tab の large の選択、Nav の AppItem、Persona | 8 |
| `body1Strong` | MessageBarTitle、Tab の選択 | 6 |
| `caption1Strong` | Badge の既定、NavSectionHeader | 4 |
| `subtitle1` | DialogTitle、Spinner の huge | 3 |
| `caption2`、`caption2Strong` | MenuItem の subText、Tag、Badge の最小 | 2 |
| `title3` | AvatarGroupPopover | 1 |
| `title2`、`title1`、`largeTitle`、`display`、`*Stronger` の 3 つ | 部品では使わない。ページの見出しなど利用者の内容のための段階と読める | 0 |

出典の例: DialogTitle は `packages/react-components/react-dialog/library/src/components/DialogTitle/useDialogTitleStyles.styles.ts:17-18`、Field の補助文は `packages/react-components/react-field/library/src/components/Field/useFieldStyles.styles.ts:81-84`、Badge の既定は `packages/react-components/react-badge/library/src/components/Badge/useBadgeStyles.styles.ts:24`。

```html demo
<div style="display:grid;gap:8px">
  <span class="fui-Text fui-Display">Display 68</span>
  <span class="fui-Text fui-LargeTitle">LargeTitle 40 大見出し</span>
  <span class="fui-Text fui-Title1">Title1 32 ページの見出し</span>
  <span class="fui-Text fui-Title2">Title2 28 節の見出し</span>
  <span class="fui-Text fui-Title3">Title3 24 小見出し</span>
  <span class="fui-Text fui-Subtitle1">Subtitle1 20 ダイアログのタイトル</span>
  <span class="fui-Text fui-Subtitle2">Subtitle2 16 グループの見出し</span>
  <span class="fui-Text fui-Body2">Body2 16 大きな本文</span>
  <span class="fui-Text fui-Body1Strong">Body1Strong 14 強調した本文</span>
  <span class="fui-Text fui-Body1">Body1 14 既定の本文。文字の階層はサイズ、太さ、色で付ける。</span>
  <span class="fui-Text fui-Caption1">Caption1 12 補助の説明</span>
  <span class="fui-Text fui-Caption2">Caption2 10 Caption2</span>
</div>
```

## フォントの並び

3 つの書体のトークンは次のとおり（`packages/tokens/src/global/fonts.ts:38-44`）。`webLightTheme` と `webDarkTheme` はこれをそのまま持つ（`packages/tokens/src/utils/createLightTheme.ts:4,18`）。

| トークン | 値 | 用途 |
|---|---|---|
| `fontFamilyBase` | `'Segoe UI', 'Segoe UI Web (West European)', -apple-system, BlinkMacSystemFont, Roboto, 'Helvetica Neue', sans-serif` | すべての文字の既定 |
| `fontFamilyMonospace` | `Consolas, 'Courier New', Courier, monospace` | コード |
| `fontFamilyNumeric` | `Bahnschrift, 'Segoe UI', 'Segoe UI Web (West European)', -apple-system, BlinkMacSystemFont, Roboto, 'Helvetica Neue', sans-serif` | 数字を目立たせる表示 |

- `'Segoe UI Web (West European)'` は、v8 では CDN の `@font-face` として登録されていた名前である。手元の tokens、react-components、web-components には `@font-face` の登録がない。React を使わない HTML でも、`@font-face` を自分で書かない限り解決しない。この設計書は Segoe UI を Web フォントとして配らない（配布の許諾を確かめていないため）。
- Windows 11 の書体は Segoe UI Variable だが、トークンが指すのは `'Segoe UI'` である。忠実さのため、トークンどおりにする。
- Segoe UI がない環境（macOS、Linux、Android）では、`-apple-system` 以降が使われる。
- Teams のテーマだけは `fontFamilyBase` を差し替える（`packages/tokens/src/alias/teamsFontFamilies.ts:5-6`）。Web の基準には使わない。

書体、サイズ、太さのトークンの値（生成物）:

<!-- spec:tokens-font -->

行の高さのトークン（生成物）:

<!-- spec:tokens-line-height -->

## 使い方の指針

サイト（fluent2.microsoft.design の typography と Text の usage のページ）の指針を要約する。

- **階層**: 段階は意味の役割を与え、拾い読みしやすい階層を作るためにある。階層はサイズ、太さ、色で付ける。ブランド色の文字は標準より目立ち、薄い中立色（`colorNeutralForeground2`、`3`）は控えめになる。
- **太さ**: 強調は Strong（Semibold）を基本にし、Stronger（Bold）は控えめに使う。
- **揃え**: 左から右へ書く文章は start に揃える。中央揃えは短い文に限る。Web では両端揃え（justify）を避ける。語の間隔が不揃いになり、拾い読みしにくくなるためである。
- **大文字小文字**: 欧文は sentence case にする。注意を引くための全部大文字は読みにくいので避ける。
- **縦の揃え**: ベースラインで揃え、縦の空きを一定のリズムで配る。
- **書体の使い分け**: ほとんどは base を使う。コードを表すときだけ monospace を使う。
- **意味**: 見た目の書体だけで意味を伝えない。太字と斜体は、読み上げソフトによっては伝わらないので、必要なときだけ使う。
- **コントラスト**: 標準の文字は 4.5:1 以上、大きな文字は 3:1 以上にする（詳しくは「コンテンツデザインとアクセシビリティ」の章）。

| Do | Don't |
|---|---|
| 本文は Body1、補助は Caption1、見出しは Subtitle と Title の段階から選ぶ | px で独自のサイズを作る |
| 強調は Semibold（Strong）で付ける | 強調に全部大文字や斜体を使う |
| 階層の下位の文字を `colorNeutralForeground2`、`3` で下げる | 階層を色だけで表し、サイズや位置の手がかりをなくす |
| 揃えは start を既定にする | 長い文を中央揃えや両端揃えにする |
| 見出しは `h1`〜`h6` の要素で表し、見た目は class で決める | 見た目のために見出しのレベルを飛ばす |

行の長さ、切り詰め、最小サイズの指針は、Fluent 2 の Web のページにない。Windows アプリの指針（Learn）には、1 行 50〜60 文字、最小 12px（Regular）と 14px（Semibold）という値があるが、これは Windows の規則であり、Fluent 2 の Web の規則として扱わない。

## Text

### 概要と使い分け（Do / Don't）

Text は、Fluent のタイポグラフィの決定を地の文に当てるための部品である。React を使わない HTML では、任意の要素に `class="fui-Text"` を付け、props に当たる data 属性で変える。CSS は `assets/fluent2.css` の `text` の部分にある（開発用のリポジトリ（非公開）の原本は `src/components/text.css`）。

| Do | Don't |
|---|---|
| 地の文、ラベルの文字、数値の表示に使う | リンクに使う（Link を使う） |
| 段階どおりの見た目ならプリセット（`fui-Body1` など）を組み合わせる | プリセットと `data-size`、`data-weight`、`data-font` を一緒に使う |
| 意味は要素で表す（`h2`、`p`、`code`） | `span` に見出しの見た目だけを付けて見出しの代わりにする |
| 1 行で切るときは `data-wrap="false"`、`data-truncate`、`data-block` を併せる | `data-truncate` だけで省略記号が出ると考える |

### 構造とマークアップ

- スロットは root だけである。class は `fui-Text`（`packages/react-components/react-text/library/src/components/Text/useTextStyles.styles.ts:8-10`）。
- 既定の要素は `span`。v9 の `as` で選べるのは `h1`〜`h6`、`p`、`pre`、`strong`、`b`、`em`、`i` である（`packages/react-components/react-text/library/src/components/Text/Text.types.ts:7`）。React を使わない HTML ではどの要素にも付けられる（`code`、`label`、`div` など）。
- role と ARIA は持たない。フォーカスを受けず、キーボード操作もない。意味は要素が担う。
- Text は margin を消さない。`h1` や `p` に付けると、ブラウザーの既定の margin が残る（v9 と同じ）。余白は、置く側で間隔のトークン（`--spacingVerticalM` など）を使って決める。
- プリセットは `class="fui-Text fui-Body1"` のように 2 つの class を並べる。v9 の出力も `fui-Body1 fui-Text` である（`packages/react-components/react-text/library/src/components/presets/Body1/Body1.test.tsx:17`）。

### バリエーション

v9 の props と data 属性の対応（props の型は `Text.types.ts:13-84`、既定値は `packages/react-components/react-text/library/src/components/Text/useText.ts:17-27`）。既定値は属性なしで当たる。

| v9 の prop | 値（既定） | data 属性 | 当たる CSS（`useTextStyles.styles.ts` の行） |
|---|---|---|---|
| `size` | `100`〜`1000`（`300`） | `data-size="100"` など | `font-size` と `line-height` を対応するトークンに（49-84） |
| `weight` | `regular`、`medium`、`semibold`、`bold`（`regular`） | `data-weight="semibold"` など | `font-weight: var(--fontWeightSemibold)` など（91-99） |
| `font` | `base`、`monospace`、`numeric`（`base`） | `data-font="monospace"` など | `font-family: var(--fontFamilyMonospace)` など（85-90） |
| `italic` | 真偽（false） | `data-italic` | `font-style: italic`（37-39） |
| `underline` | 真偽（false） | `data-underline` | `text-decoration-line: underline`（40-42） |
| `strikethrough` | 真偽（false） | `data-strikethrough` | `text-decoration-line: line-through`（43-45）。underline と併せると `line-through underline`（46-48） |
| `wrap` | 真偽（**true**） | `data-wrap="false"` | `white-space: nowrap; overflow: hidden`（27-30） |
| `truncate` | 真偽（false） | `data-truncate` | `text-overflow: ellipsis` だけ（31-33） |
| `block` | 真偽（false） | `data-block` | `display: block`（34-36） |
| `align` | `start`、`center`、`end`、`justify`（`start`） | `data-align="center"` など | `text-align`（100-108） |

`wrap` だけは既定が true なので、属性は `data-wrap="false"` の形にする。`data-wrap` を付けただけでは何も変わらない。

### 寸法

`data-size` とトークンの対応（値は `packages/tokens/src/global/fonts.ts:4-28`）。

| `data-size` | font-size | line-height | 同じ大きさのスタイル |
|---|---|---|---|
| `100` | `fontSizeBase100` 10px | `lineHeightBase100` 14px | Caption2 |
| `200` | `fontSizeBase200` 12px | `lineHeightBase200` 16px | Caption1 |
| `300`（既定） | `fontSizeBase300` 14px | `lineHeightBase300` 20px | Body1 |
| `400` | `fontSizeBase400` 16px | `lineHeightBase400` 22px | Body2、Subtitle2 |
| `500` | `fontSizeBase500` 20px | `lineHeightBase500` 28px | Subtitle1 |
| `600` | `fontSizeBase600` 24px | `lineHeightBase600` 32px | Title3 |
| `700` | `fontSizeHero700` 28px | `lineHeightHero700` 36px | Title2 |
| `800` | `fontSizeHero800` 32px | `lineHeightHero800` 40px | Title1 |
| `900` | `fontSizeHero900` 40px | `lineHeightHero900` 52px | LargeTitle |
| `1000` | `fontSizeHero1000` 68px | `lineHeightHero1000` 92px | Display |

### 色と状態

Text は色を指定しない。文字の色は親から継承し、ふつうはプロバイダー相当の要素の `colorNeutralForeground1` になる。階層を下げるときは、置く側で色のトークンを当てる。

| 用途 | トークン |
|---|---|
| 主要な文字 | `colorNeutralForeground1` |
| 二次の文字 | `colorNeutralForeground2` |
| 補助の説明 | `colorNeutralForeground3` |
| ブランド色の文字 | `colorBrandForeground1` |
| 無効の文字 | `colorNeutralForegroundDisabled` |

状態（hover、pressed など）は持たない。

### フォーカス・動き・ハイコントラスト

- フォーカスを受けないので、フォーカスの表示はない。
- transition と animation はない。
- `@media (forced-colors: active)` の規則はない。色を指定しないので、強制カラーではブラウザーが `CanvasText` などに置き換える。

### 実装の例

修飾の組み合わせ。

```html demo
<p class="fui-Text" data-block>既定の Text（Body1 と同じ 14px / 20px）</p>
<p class="fui-Text" data-block data-size="500" data-weight="semibold">size 500、semibold</p>
<p class="fui-Text" data-block data-font="monospace">font monospace: npm run build</p>
<p class="fui-Text" data-block data-font="numeric" data-size="600">1,234,567.89</p>
<p class="fui-Text" data-block><span class="fui-Text" data-underline>下線</span>、<span class="fui-Text" data-strikethrough>取り消し線</span>、<span class="fui-Text" data-underline data-strikethrough>両方</span></p>
<p class="fui-Text" data-block data-align="center">中央揃え（短い文に限る）</p>
```

1 行で切り詰める。`data-truncate` は、`data-wrap="false"` と `data-block` を併せたときだけ省略記号を出す。

```html demo
<div style="max-width:240px">
  <span class="fui-Text" data-block data-wrap="false" data-truncate>長いファイル名の例: 2026 年度 第 3 四半期 売上報告書 最終版.xlsx</span>
  <span class="fui-Text" data-block data-wrap="false">truncate なし: 2026 年度 第 3 四半期 売上報告書 最終版.xlsx</span>
</div>
```

プリセットと見出しの要素。見出しのレベルは文書の構造で決め、見た目は class で決める。

```html demo
<h2 class="fui-Text fui-Title3" style="margin:0 0 var(--spacingVerticalS)">見出しのレベルと見た目は別に決める</h2>
<p class="fui-Text fui-Body1" style="margin:0;color:var(--colorNeutralForeground2)">h2 に Title3 の見た目を当てた。Text は margin を消さないので、余白は置く側で間隔のトークンを使って決める。</p>
```

### v9 との差と未確認の点

- **プリセットと Text の重なり**: v9 はプリセットの root を Text のスタイルより後に merge するので、プリセットの書体、サイズ、行の高さ、太さが勝つ（`packages/react-components/react-text/library/src/components/presets/createPreset.ts:21`）。同じ詳細度の規則は後に書いたものが勝つので、配布の束（`fluent2.css`）では `fluent2-typography.css` を `fluent2-components.css` の後に置いた。これで `class="fui-Text fui-Body1"` のとき、v9 と同じくプリセットが勝つ。個別に読むときも、書体のプリセットを最後に読む。
- **プリセットと修飾の併用**: v9 の型はプリセットから `font`、`size`、`weight` を外している（`packages/react-components/react-text/library/src/components/Text/Text.types.ts:89`）。React を使わない HTML では併用を止められないが、併用するとプリセットが勝つ（v9 と同じ結果）。
- **`fui-Body1` だけを付けた場合**: Text の root（`display: inline`、`text-align: start`、`white-space: normal` など）は当たらず、書体の 4 つの宣言だけが当たる。v9 にはこの形がないので、React を使わない HTML での拡張である。
- **Web Components v3 との差**: `<fluent-text>` は子要素に `font: inherit; margin: 0` を当て、中に `h1` などを置ける（`packages/web-components/src/text/text.styles.css:101-108`）。この設計書は v9 に合わせ、margin を消さない。
- **要素の候補**: `code`、`label`、`div` などに付けるのは、v9 の `as` の候補にない React を使わない HTML での拡張である。

## 日本語への適用

この節の内容は Fluent 2 の Web にない、この設計書の**独自**の拡張である。

### 事実: Fluent 2 の Web には日本語の書体がない

- v9 の 3 つの書体の並びには、日本語の書体が 1 つもない（`packages/tokens/src/global/fonts.ts:38-44`）。tokens、react-components、web-components を `Meiryo`、`Yu Gothic` で検索しても 0 件である。日本語の文字は `'Segoe UI'` にないので、どの書体で描かれるかは OS とブラウザーの代替の選び方に任される。
- Fluent UI v8 には日本語の並びがあった。`LocalizedFontFamilies.Japanese` は `'Yu Gothic UI', 'Meiryo UI', Meiryo, 'MS Pgothic', Osaka` で（`packages/theme/src/fonts/FluentFonts.ts:28`）、`ja` に割り当てられ（`packages/theme/src/fonts/createFontStyles.ts:23`）、その後ろに欧文の代替が続く（`packages/theme/src/fonts/__snapshots__/createFontStyles.test.ts.snap:200`）。v8 は言語でサイズと太さを変えず（`createFontStyles.ts:75-89`）、行の高さの指定も持たない。
- Windows アプリの指針（Learn）は、Yu Gothic UI を日本語の UI 用の書体としている。Yu Gothic UI は Semibold の字形を持つが、Meiryo と Meiryo UI は Regular と Bold だけである。

### `fluent2-base.css` の拡張

土台（`fluent2-base.css`。開発用のリポジトリ（非公開）では `src/fluent2-base.css:22-32`）は、ページの言語が日本語のとき、`--fontFamilyBase` と `--fontFamilyNumeric` を次の並びに上書きする。

```text
--fontFamilyBase:    'Segoe UI', 'Segoe UI Web (West European)', 'Yu Gothic UI', 'Meiryo UI', Meiryo,
                     -apple-system, BlinkMacSystemFont, 'Hiragino Sans', 'Hiragino Kaku Gothic ProN',
                     Roboto, 'Noto Sans JP', 'Helvetica Neue', sans-serif
--fontFamilyNumeric: Bahnschrift, （以下 --fontFamilyBase と同じ）
```

- **当たる条件**: 次の 3 つのセレクターで当てる。どれも `:lang(ja)` なので、`lang="ja"` にも `lang="ja-JP"` にも一致する。
    1. `:root:lang(ja)`（ページ全体）
    2. `[data-theme]:lang(ja)`（テーマを切り替える要素。tokens.css がその要素で `--fontFamilyBase` を宣言し直すため、上書きも当て直す）
    3. `.fui-FluentProvider:lang(ja)`（プロバイダー相当の要素。理由は 2 と同じ）
- **止め方**: `<html>` に `data-fui-cjk-fonts="off"` を付けると、3 つとも当たらなくなる。
- **前提**: `<html lang="ja">` を必ず書く。`lang` がないと、日本語の書体の指定は当たらない。
- **Monospace は上書きしない**: `--fontFamilyMonospace` はトークンのままで、コードの中の日本語はブラウザーの既定の代替になる。

### 案 A と案 B

| | 案 A（v8 を踏襲） | 案 B（採用） |
|---|---|---|
| 並び | `'Yu Gothic UI', 'Meiryo UI', Meiryo, 'MS Pgothic', Osaka, 'Segoe UI', …` | `'Segoe UI', 'Segoe UI Web (West European)', 'Yu Gothic UI', 'Meiryo UI', Meiryo, …` |
| 欧文と数字 | Yu Gothic UI の字形になる | トークンどおり Segoe UI |
| 和欧の字面 | 1 つの書体なので揃う | 2 つの書体が混ざる |
| 根拠 | Microsoft の実装そのもの | Fluent 2 の Web の見た目を保つことを優先した独自の判断 |

案 B を採った理由: この設計書の目的は Fluent 2 の Web の忠実な再現である。欧文と数字はトークンどおり Segoe UI にし、日本語だけを Microsoft が日本語の UI 用とする Yu Gothic UI に決め打ちする。ブラウザーの代替に任せるより、結果が予測しやすい。

案 B での独自の追加と除外:

- `'MS Pgothic'` と `Osaka` は外した。古い環境のための書体で、今の主要な環境には要らないと判断した。
- `'Hiragino Sans'`、`'Hiragino Kaku Gothic ProN'`（macOS と iOS）、`'Noto Sans JP'`（Android と Linux）は Microsoft の資料にない独自の追加である。日本語の代替を明示するために入れた。

案 B の代償（未検証）: Segoe UI にも字形がある約物（三点リーダー、ダッシュ、引用符など）は、和文の中でも欧文の字形と幅で描かれる可能性がある。

```html demo
<div style="display:grid;gap:12px">
  <div>
    <span class="fui-Text fui-Caption1" style="color:var(--colorNeutralForeground3)">lang="ja"（案 B の並び）</span>
    <p class="fui-Text fui-Body1" data-block style="margin:0">Fluent 2 のボタンは 32px の高さで、角丸は 4px です。</p>
  </div>
  <div data-theme="light" lang="en">
    <span class="fui-Text fui-Caption1" style="color:var(--colorNeutralForeground3)">lang="en"（トークンのまま。日本語はブラウザーの代替）</span>
    <p class="fui-Text fui-Body1" data-block style="margin:0" lang="ja">Fluent 2 のボタンは 32px の高さで、角丸は 4px です。</p>
  </div>
</div>
```

2 つ目の例では、`data-theme` と `lang="en"` を付けた要素で、tokens.css が `--fontFamilyBase` をトークンの値に宣言し直し、日本語の上書きは当たらない。中の段落は `lang="ja"` だが、変数を宣言し直すのは `:root`、`[data-theme]`、`.fui-FluentProvider` の要素だけなので、段落は外側の値を継承する。つまり、日本語の書体の指定は「変数を宣言し直す要素の言語」で決まる。この例は `data-theme="light"` を付けたので、ページのテーマにかかわらずライトで表示する。

### 太さ、斜体、サイズ

- **太さ**: Yu Gothic UI には Semibold があるので、600 はそのまま当たる。Meiryo と Meiryo UI では、CSS の照合の規則により 600 は Bold で、500 は Regular で描かれる見込みである（**推論**、描画は未確認）。Yu Gothic UI にも Medium の字形はない。日本語の強調は Semibold（Strong）にし、Medium（`data-weight="medium"`）に頼らない。
- **斜体**: Yu Gothic UI には斜体の字形がない。日本語に `data-italic` を使わない。
- **サイズ**: 日本語の文字に 10px の段階（Caption2、Caption2Strong、`data-size="100"`）を使わない。根拠は Windows アプリの指針の最小 12px で、Fluent 2 の Web の規則ではない（Fluent 2 の Web は 10px の段階を持つ）。
- **約物の詰め**: Yu Gothic UI に `font-feature-settings: "palt"` や `text-spacing-trim` を当てない。古い版（1.95 より前）では括弧の幅が 0 になって重なる不具合が報告されている（W3C CSSWG の issue #11074）。

### 行の高さの考え方

- Fluent 2 の段階は言語で変わらない。v8 も言語で数値を変えない。行の高さを日本語のために変える Microsoft の根拠はない。
- Fluent の行間（行の高さから文字の大きさを引いた量）は、Body1 で 6px / 14px（約 0.43 字）、Caption1 で約 0.33 字、Title1 で 0.25 字である（**推論**、計算）。W3C の「日本語組版処理の要件（jlreq）」が横組みの行間として挙げる半角から全角（line-height で 1.5〜2.0）より狭い。
- **結論**: UI の部品（1 行のラベル、ボタン、表のセル、メニュー）は、忠実さのためトークンどおりにする。部品の高さと余白はトークンの行の高さを前提に決まっているので、変えると崩れる。
- 日本語の長い本文（文書の段落）だけは、行の高さを広げてよい。これは Fluent 2 からの逸脱で、根拠は jlreq であり Microsoft ではない。広げるときは `.fui-Body1` を書き換えず、文書用の別の class `f2-prose` を使う（末尾を参照）。

## プリセットの class

`fluent2-typography.css` に、17 個のスタイルの class がある（生成物）。v9 のプリセットのコンポーネントと同じ名前である（各 `packages/react-components/react-text/library/src/components/presets/*/use*Styles.styles.ts:9`）。サイトの Text の usage のページは 10 個としか書いていないが、ソースには 17 個ある。

| class | v9 のコンポーネント | 値の出典（`typographyStyles.ts` の行） |
|---|---|---|
| `fui-Caption2`、`fui-Caption2Strong` | `Caption2`、`Caption2Strong` | 50-55、56-61 |
| `fui-Caption1`、`fui-Caption1Strong`、`fui-Caption1Stronger` | `Caption1`、`Caption1Strong`、`Caption1Stronger` | 32-37、38-43、44-49 |
| `fui-Body1`、`fui-Body1Strong`、`fui-Body1Stronger` | `Body1`、`Body1Strong`、`Body1Stronger` | 8-13、14-19、20-25 |
| `fui-Body2` | `Body2` | 26-31 |
| `fui-Subtitle2`、`fui-Subtitle2Stronger` | `Subtitle2`、`Subtitle2Stronger` | 68-73、74-79 |
| `fui-Subtitle1` | `Subtitle1` | 62-67 |
| `fui-Title3`、`fui-Title2`、`fui-Title1` | `Title3`、`Title2`、`Title1` | 92-97、86-91、80-85 |
| `fui-LargeTitle`、`fui-Display` | `LargeTitle`、`Display` | 98-103、104-109 |

使い方:

- **v9 のプリセットと同じにする**: `class="fui-Text fui-Title1"` と 2 つ並べる。Text の root が当たり、`data-italic`、`data-underline`、`data-align`、`data-wrap="false"`、`data-truncate`、`data-block` も効く。
- **書体だけを当てる**: ほかのコンポーネントの中の文字や、独自の部品の文字には、`fui-Body1` などを単独で付けてよい。書体、サイズ、行の高さ、太さの 4 つだけが当たる。
- **CSS で使う**: class を付けられないときは、4 つのトークンを書く（`font-family: var(--fontFamilyBase); font-size: var(--fontSizeBase300); line-height: var(--lineHeightBase300); font-weight: var(--fontWeightRegular);`）。v9 のコンポーネントの styles も `...typographyStyles.body1` の形で同じ 4 つを展開している。

```html demo
<div style="display:grid;gap:4px">
  <span class="fui-Text fui-Subtitle2">プリセットに修飾を足す</span>
  <span class="fui-Text fui-Body1" data-italic lang="en">Body1 with italic (for Latin text only)</span>
  <span class="fui-Text fui-Caption1" style="color:var(--colorNeutralForeground3)">fui-Caption1 と colorNeutralForeground3 で補助の説明にする</span>
</div>
```

## v9 との差と未確認の点

- **Subtitle1 の行の高さ**: サイトの Web の表は Subtitle 1 を 20px / 26px としている。ソースは `lineHeightBase500` = 28px（`packages/tokens/src/global/fonts.ts:22`）で、Web Components の段階も同じトークンを使う。この設計書はソースの 28px を採る。
- **サイトの表の行数**: サイトの Web の表には Body 2 がない。ソースには `body2` がある。
- **用途**: スタイルごとの用途を書いた一次資料はない。「スタイルの使いどころ」の表は使用例からの推論である。
- **未確認**: Meiryo と Yu Gothic UI で 500 と 600 がどの字形で描かれるか。macOS の `-apple-system` が日本語をどの書体で描くか。Office の Web の日本語の書体の並び。jlreq の数値は要約から得たもので、節番号を確かめていない。

## 土台に取り入れたこと

- 日本語の長い段落のために、独自の class `f2-prose` を `fluent2-base.css` に置いた。`lang="ja"` の中で `line-height: 1.7` と `max-inline-size: 40em` を当てる。根拠は jlreq で、Fluent 2 ではない。部品の行の高さは変えない。接頭辞は、Fluent の部品と区別するため `f2-` にした。
- 等幅の日本語の書体（`'MS Gothic'` を足す案）は、描画を確かめていないので取り入れていない。

```html demo
<div lang="ja" class="f2-prose">Fluent 2 の部品は 14px / 20px の行で組む。設計書や説明の長い段落のように、日本語を続けて読ませる所だけは、行の間を広げて読みやすくする。これは Fluent 2 にない独自の拡張である。</div>
```
