# コンテンツデザインとアクセシビリティ

UI の文言は、短く、行動がわかる言葉で書く。欧文は sentence case にし、ボタン、ラベル、見出しに句読点を付けない。アクセシビリティは必須の要件とし、この設計書は WCAG 2.2 AA を目標にする（**独自**の決定。理由は後述）。日本語の UI への当てはめは Fluent 2 の範囲外なので、この設計書が**独自**に決める。

## コンテンツデザインの考え方

サイトの content-design のページの要約である。

- 言葉は、アイコンやイラストと並ぶ設計の素材である。コンテンツデザインは、読み手が必要とする情報を、必要なときに届ける方法を考えることである。
- 書く前に 3 つの問いに答える。
    1. 読み手は誰か（「開発者」よりも狭く定義する）
    2. 読み手は何を成し遂げたいか
    3. 読み手はどう感じていそうか（不安か、迷っているか、満足しているか）
- 口調は、読み手の意図と心の状態に合わせる。ダッシュボードでは親しみやすく、メニューや見出しでは事実だけを伝える。
- 文体の 3 つの心得:
    - **簡潔に**: 平易な言葉、短い文、断片で書き、流し読みしやすくする。
    - **要点を先に**: 選択肢と次の一歩を明らかにし、余分な語を削る。
    - **人と話すように**: 一対一で話すような、くだけた会話の調子で書く。
- 現在形で書き、能動態を基本にする。受動態は、行為者を主語にしたくないときや、行為者より行為が大事なときに限る。
- 二人称で書く。一人称は、読み手の視点で書くとき以外は避ける。
- 見出しは文書の骨組みである。見出しを飛ばして読まれると、その下の本文も読まれにくい。

## 大文字小文字と句読点

- **大文字小文字**: Windows、Android、Web では sentence case（最初の語と固有名詞だけを大文字にする）。iOS と macOS では title case。sentence case を選ぶ理由は、読みやすさと翻訳のしやすさである。
- **ピリオド**: 完全な文の後にだけ付ける。見出し、ボタン、ラベル、箇条書き、プレースホルダー、ヘルパーテキストには付けない。迷ったら付けない。
- **疑問符**: 問いには必ず付ける。
- **感嘆符**: 避ける。祝う場面に限る。
- **方向の語**: above、below、left、right で画面の位置を指さない。画面が見えることを前提にしており、翻訳もしにくい。
- **リンク**: 行き先を短く具体的に書く。「Click here」のような汎用の語や URL を使わない。

## ボタンの文言

サイトの Button の usage のページの要約である。

- 次の操作を表す能動の語にする。ふつうは動詞 1 語で、わかりやすくなる場合だけ名詞を足す。sentence case にし、末尾に句読点を付けない。
- 新しく作る操作は「New + 対象」、既存のものを加える操作は「Add + 対象」にする。メニューボタンでは、ボタンを「New」とし、メニューの項目からは「New」を省く。スプリットボタンでは、主ボタンと各項目の両方に完全な句を書く。
- ダイアログとドロワーのボタンは、タイトルの問いへの具体的な答えにする（ファイルの削除を確かめるなら「Delete」と「Cancel」）。
- 複数の段階を進む流れでは、「Continue」ではなく「Next」、「Back」ではなく「Previous」を使う。
- 自動保存できないときは「Save」を使い、成功か失敗のフィードバックを組み合わせる。

作業を終えるボタンの使い分け:

| 語 | 使う場面 |
|---|---|
| Done | 確認するだけの最後の画面 |
| Finish | 押した時点で選択を確定する流れ |
| Close | 行動を求めない情報の表示。**エラーのメッセージでは「OK」ではなく「Close」** |
| Got it | 閉じる前に内容を読んでほしいとき（機能の紹介など） |
| Dismiss | 閉じて、再び表示させないとき |
| Cancel | 進行中の作業を止め、未保存の変更を捨てる。Close は作業の状態に影響せずに閉じる |

## フォームの文言

サイトの Field の usage のページの要約である。

- **ラベル**: 短い句にし、完全な文や指示文にしない。問いの形は必要なときだけ使う。
- **プレースホルダー**: 入力すると消えるので、必要な情報を置かない。必要な情報はラベルかヘルパーテキストに書く。補足のヒントだけに使い、ピリオドを付けない。
- **ヘルパーテキスト**: フィールドの下に置き、受け付ける値や書式を説明する。複数の文になるなら箇条書きにする。
- **検証のメッセージ**: 短く書く。無効なときはどうすればよいかを伝え、有効なときは確認を伝える。

## エラーとメッセージの文言

サイトの MessageBar と Dialog の usage のページの要約である。

- **MessageBar のタイトル**: 何が起きているかを短く具体的に書く。「Warning」のような汎用の語で済ませない。
- **MessageBar の本文**: 行動に必要な情報を 1〜2 文で書き、タイトルを繰り返さない。長さは約 2 行（1 行あたり約 100 文字）までにし、長い説明は文書へのリンクにする。
- **成功のメッセージ**: 日常の操作で祝わない。「success」「successfully」を避け、何が準備できたか、何が変わったかを書く。
- **エラーと警告**: 解決のためのリンクかボタンを必ず付ける。エラーは進行を妨げるので解決の道筋が要る。警告は進行を妨げないが、問題を防ぐ手段を付ける。リンクは「Learn」「Explore」などの動詞で始め、話題を示す。
- **MessageBar のボタン**: タイトルに応える明確な動詞にし、曖昧なら名詞を足す（例: Renew license）。
- **Dialog のタイトル**: 必須。「Error」のような汎用の語ではなく、何が起きたかを書く。問いでない限り末尾に句読点を付けない。
- **Dialog の本文**: タイトルを繰り返さない。最も重要な情報を先に書き、操作の結果がどうなるかを冒頭で伝える。
- **Dialog のボタン**: タイトルに応える 1〜2 語。

## 日本語の UI に当てはめる

この節は Fluent 2 にない、この設計書の**独自**の規則である。サイトの規則は英語の UI を前提にしており、日本語の表記（敬体か常体か、全角か半角か）は扱っていない。英語の規則の意図（短く、行動がわかり、読み手に寄り添う）を保つように読み替えた。

| 英語の規則 | 日本語の UI での読み替え（独自） |
|---|---|
| sentence case | 日本語には当てはまらない。文中の欧文の一般の語は小文字で始め、固有名詞（製品名、機能名）は正式な表記に従う |
| ボタン、ラベル、見出しにピリオドを付けない | 句点「。」を付けない。説明の文やメッセージの本文には付ける |
| 問いには疑問符 | 問いには全角の「？」を付ける（例: このファイルを削除しますか？） |
| 感嘆符を避ける | 「！」を使わない |
| ボタンは動詞 1 語 | 「保存」「削除」「共有」のような名詞か、「閉じる」「戻る」のような動詞の終止形にする。「〜してください」「〜する」を付けない。1 つの画面の中で形を揃える |
| New + 対象、Add + 対象 | 「新しい〇〇」「〇〇を追加」 |
| Next、Previous | 「次へ」「前へ」 |
| Done、Finish、Close、Got it、Dismiss、Cancel | 「完了」「完了」「閉じる」「了解しました」「今後表示しない」「キャンセル」。エラーのダイアログを閉じるボタンは「OK」ではなく「閉じる」にする |
| 二人称で書く | 主語を省く。「あなた」を使わない |
| 現在形、能動態 | 「〜されました」より「〜しました」。システムを主語にした受け身を避ける |
| 文体 | 説明の文とメッセージの本文は敬体（です・ます）。ボタン、ラベル、見出し、メニューの項目は体言止めか動詞の終止形 |
| success を使わない | 「正常に」「成功しました」を避け、何が変わったかを書く（「3 件のファイルを共有しました」） |
| 汎用のタイトルにしない | 「エラー」「警告」だけのタイトルにしない（「ファイルを保存できませんでした」） |
| Click here を使わない | 「こちら」「ここをクリック」を使わない。行き先を書く（「共有の設定を開く」） |
| 方向の語を使わない | 「上の」「右の」「下記の」で画面の位置を指さない |
| MessageBar の本文は約 2 行（1 行約 100 文字） | 日本語では 1 行約 50 字を目安にする（**推論**。和文の 1 字は欧文の約 2 字の幅とみなした） |

表記の既定（独自）:

- 英数字は半角、括弧と句読点は全角（「（）」「、。」）。
- 全角と半角の間の空白は、プロジェクトで統一する。この設計書の例は空白を入れている。
- 数と単位の間（「32 px」か「32px」か）も統一する。この設計書は単位を詰めて書く。
- 斜体で強調しない（日本語の書体に斜体の字形がない。「タイポグラフィ」の章）。強調は Semibold にする。

```html demo
<div style="display:grid;gap:12px;max-width:520px">
  <div style="border:1px solid var(--colorNeutralStroke1);border-radius:var(--borderRadiusMedium);padding:12px">
    <span class="fui-Text fui-Caption1Strong" data-block style="color:var(--colorPaletteGreenForeground1)">Do</span>
    <span class="fui-Text fui-Subtitle2" data-block>このファイルを削除しますか？</span>
    <span class="fui-Text fui-Body1" data-block>削除すると、共有している相手もファイルを開けなくなります。</span>
    <span class="fui-Text fui-Body1Strong">ボタン: 削除、キャンセル</span>
  </div>
  <div style="border:1px solid var(--colorNeutralStroke1);border-radius:var(--borderRadiusMedium);padding:12px">
    <span class="fui-Text fui-Caption1Strong" data-block style="color:var(--colorPaletteRedForeground1)">Don't</span>
    <span class="fui-Text fui-Subtitle2" data-block>確認</span>
    <span class="fui-Text fui-Body1" data-block>本当に削除してもよろしいですか！</span>
    <span class="fui-Text fui-Body1Strong">ボタン: OK、キャンセルする。</span>
  </div>
</div>
```

## アクセシビリティの基準

- サイトの accessibility のページは、Fluent のコンポーネントが WCAG 2.1 AA を満たすか上回るとする。Web Components の文書は「WCAG 2.2 compliant」と書く（`packages/web-components/src/_docs/concepts/introduction.mdx:53`）。
- **この設計書は WCAG 2.2 AA を目標にする（独自）**。2.2 は 2.1 の達成基準をほぼすべて含むので、2.2 を満たせば 2.1 AA も満たす。2.2 で加わった基準のうち、フォーカスが隠れないこと（2.4.11）と、操作の対象の最小の大きさ（2.5.8、24 × 24 CSS px か、十分な間隔）は、React を使わない HTML で組むときに崩しやすいので、受け入れの確認に入れる。
- コードの水準では、意味の正しい HTML を書き、WAI-ARIA Authoring Practices（APG）に従う。最初のワイヤーフレームから最後のマークアップまで、アクセシビリティを考える。
- 設計の仕様には、余白や色と同じ詳しさで、デバイスごとの操作、フォーカス順、スクリーンリーダー向けの注記、意味の構造を書く（サイトの指針）。

## コントラスト

- 通常の文字は 4.5:1 以上、大きな文字（太字で約 18.5px 超、または標準の太さで 24px 以上）は 3:1 以上。
- アイコンや操作部品など文字でない要素は、隣り合う色に対して 3:1 以上。
- 境界が操作に必要な線は `colorNeutralStrokeAccessible` で描く。`colorNeutralStroke1`、`2` は 3:1 を満たさない（light で約 1.5:1、1.3:1。**推論**、計算）。
- 無効の部品は WCAG のコントラストの要件から外れる。`colorNeutralForegroundDisabled` は 3:1 も満たさないので、無効であることを色以外でも伝える（`disabled` 属性か `aria-disabled="true"`）。
- 色だけで意味を伝えない。文字、アイコン、形を添える。強制カラーでは palette と status の色の区別がなくなる。
- トークンの組み合わせとコントラスト比の計算結果は「色」の章にある。面と文字の組を既定から変えたら、計算し直す。

```html demo
<div style="display:grid;gap:8px;max-width:520px">
  <div>
    <span class="fui-Text fui-Caption1Strong" data-block>Do: 色に文字を添える</span>
    <span class="fui-Text fui-Caption1" style="color:var(--colorPaletteRedForeground1)">エラー: 郵便番号は 7 桁の数字で入力してください</span>
  </div>
  <div>
    <span class="fui-Text fui-Caption1Strong" data-block>Don't: 枠の色だけで伝える</span>
    <span class="fui-Text" style="display:inline-block;min-width:200px;padding:4px 8px;border:1px solid var(--colorPaletteRedBorder2);border-radius:var(--borderRadiusMedium)">123-45</span>
  </div>
</div>
```

## フォーカス

- フォーカスは、次に何を操作するかを見せるものである。focus では部品の色を変えず、輪を描いてキーボードとマウスの操作を見分けられるようにする（サイトの color のページ）。
- 輪の色は `colorStrokeFocus2`、内側に線を重ねるときは `colorStrokeFocus1` を使う（light は Focus2 が黒、dark は白。`packages/tokens/src/alias/lightColor.ts:182-183`）。
- 既定の輪は `createFocusOutlineStyle()` の形で、React を使わない CSS では次のように書く（`packages/react-components/react-tabster/src/focus/createFocusOutlineStyle.ts:55-112`）。
    - 要素は `position: relative`。`:focus` と `:focus-visible` で `outline-style: none`。
    - フォーカス中は要素自身の `border-color: transparent`。
    - `::after` に `content: ""`、`position: absolute`、`pointer-events: none`、`z-index: 1`、`border: 2px solid var(--colorStrokeFocus2)`（2px は v9 の直書き）、`border-radius: var(--borderRadiusMedium)`、`inset: -2px`。
    - `@media (forced-colors: active)` で `::after` の `border-color: Highlight`。
- コンポーネントによって輪の形が違う。Button は枠の色と内側の 1px の `box-shadow` で描き、透明な `outline` を併せる（`packages/react-components/react-button/library/src/components/Button/useButtonStyles.styles.ts:105-113`）。Link は二重の下線にする（`packages/react-components/react-link/library/src/components/Link/useLinkStyles.styles.ts:14-19`）。各コンポーネントの節の値を写す。
- v9 は `[data-fui-focus-visible]` を JavaScript（keyborg の判定）で付ける。この設計書は `:focus-visible` で近似する。子孫のフォーカスで輪を描く `[data-fui-focus-within]:focus-within` は `:has(:focus-visible)` で近似する。ブラウザーの `:focus-visible` は、テキストの入力欄ではマウスでも一致するなど、細部が v9 と違う。
- `<input>` などの置換要素は `::after` を持てないので、輪は外側の要素（根）に描く。
- 固定のヘッダーやダイアログで、フォーカスした要素が隠れないようにする（WCAG 2.2 の 2.4.11）。`scroll-padding-block-start` で固定のヘッダーの高さを空けるとよい（**推論**）。

既定の輪の見本（この例のための CSS で、共通の規則の正式な定義は「React を使わない HTML への適用」の章にある）。Tab キーでフォーカスを移すと輪が出る。

```html demo
<style>
  .demo-focus-outline { position: relative; }
  .demo-focus-outline:focus, .demo-focus-outline:focus-visible { outline-style: none; }
  .demo-focus-outline:focus-visible { border-color: transparent; }
  .demo-focus-outline:focus-visible::after {
    content: ""; position: absolute; pointer-events: none; z-index: 1;
    border: 2px solid var(--colorStrokeFocus2); /* v9 の直書き */
    border-radius: var(--borderRadiusMedium); inset: -2px;
  }
  @media (forced-colors: active) {
    .demo-focus-outline:focus-visible::after { border-color: Highlight; }
  }
</style>
<div style="display:flex;gap:12px;flex-wrap:wrap">
  <div class="demo-focus-outline fui-Text" tabindex="0" style="padding:8px 12px;border:1px solid var(--colorNeutralStroke1);border-radius:var(--borderRadiusMedium)">フォーカスできる区画 1</div>
  <div class="demo-focus-outline fui-Text" tabindex="0" style="padding:8px 12px;border:1px solid var(--colorNeutralStroke1);border-radius:var(--borderRadiusMedium)">フォーカスできる区画 2</div>
</div>
```

## キーボード

- フォーカスは Z 字の順（左から右へ、上から下へ）に移す。DOM の順を見た目の順と揃え、正の `tabindex` を使わない。
- 操作は、まずネイティブの要素（`button`、`a[href]`、`input`、`select`、`details`、`dialog`）で作る。ネイティブの要素は、Enter と Space、矢印キー（ラジオボタンの組）を自前で処理する。
- 矢印キーで中を移る部品（MenuList と MenuItem、RadioGroup と Radio、TabList と Tab、Tree と TreeItem）は、Web Components v3 では HTML の focusgroup とそのポリフィルで作っている（`packages/web-components/src/_docs/developer/polyfilling.mdx:98-110`）。React を使わない HTML と CSS だけでは、この移動（ロービング）は作れない。ネイティブのラジオボタンで足りない部品は、`components/<group>.js` の小さな JS で APG のキーボード操作を補う。CSS だけで済む見た目は CSS で作る。
- ダイアログの規則（サイトの Dialog の usage のページ）:
    - 開いたら、中の最初の操作できる要素にフォーカスを移す。
    - モーダルと警告のダイアログでは、フォーカスを中に閉じ込める。
    - 閉じたら、開いた要素にフォーカスを戻す。
    - Esc キーや外側のクリックに頼らずに閉じられるよう、少なくとも 1 つの操作できる要素を置く。
    - ネイティブの `<dialog>` の `showModal()` は、背後を操作できなくし、閉じたときに開く前の要素へフォーカスを戻す（HTML の仕様。ブラウザーごとの挙動は未確認）。
- 一時的な UI（Popover、Menu）を閉じたときに、フォーカスを失わせない。

## 拡大とリフロー

- 400% に拡大しても、横スクロールなしで内容を折り返す。幅 320 CSS px まで設計する（サイトの指針）。
- 文字を 200% に拡大しても、内容が切れないようにする。
- トークンは px で定義されている。ブラウザーのページの拡大は px も拡大するので、拡大の要件はページの拡大で満たせる。一方、ブラウザーの既定の文字サイズの設定は px の文字を変えない（**推論**。v9 も px のトークンを使うので、v9 と同じ振る舞いになる）。
- 高さを固定しない。部品の高さは `min-height` と行の高さで決め、文字が増えたら伸びるようにする。`data-truncate` で切るときは、全文を読める手段（title 属性や Tooltip だけに頼らず、詳細の画面など）を用意する。
- 縦横の向きの違いにも対応する。

## ハイコントラスト

サイトの accessibility のページは、ハイコントラストに触れていない。実装の規則はソースから読む。

- Web の標準の経路は、OS の強制カラー（`@media (forced-colors: active)`）である。固定の色のハイコントラストのテーマは旧式とされる（`packages/web-components/src/_docs/developer/theming.mdx:56-61`）。
- 部品の CSS は、強制カラーの中でシステムカラーのキーワード（`Canvas`、`CanvasText`、`Highlight`、`HighlightText`、`GrayText`、`ButtonText`、`ButtonFace`、`ButtonBorder`、`LinkText`）を直接書く。値は v9 の各コンポーネントの規則を写す。
- 状態の区別が消える所（hover、選択、primary）だけを書き直し、反転させる部品には `forced-color-adjust: none` を付ける。
- light と dark で透明な線（`colorTransparentStroke*`）と透明な `outline` を残しておく。強制カラーでは、それが枠とフォーカスの輪として現れる。
- `data-theme="high-contrast"` は Teams のハイコントラストの値を模した近似で、確認用である。これで対応を済ませない（「色」の章）。
- 確かめるときは、Windows のコントラスト テーマを有効にするか、ブラウザーの開発者ツールで `forced-colors: active` を模す。

## 動きを減らす

- v9 は、動きのある部品で `@media screen and (prefers-reduced-motion: reduce)` のときに `transition-duration: 0.01ms` にする（例 `useButtonStyles.styles.ts:77-79`）。この設計書の CSS も、v9 が書いている部品にだけ同じ規則を書く。
- サイトの accessibility のページは、動きを減らす設定に触れていない。動きの章（「エレベーション、マテリアル、モーション」）も参照する。

## スクリーンリーダー

- `<html lang="ja">` を書く。日本語以外の部分には、その要素に `lang` を書く。読み上げの言語と、日本語の書体の指定（「タイポグラフィ」の章）の両方がこれに頼る。
- 見出しの要素を論理的な順に使い、レベルを飛ばしたり混ぜたりしない。見た目は class（`fui-Title3` など）で決め、レベルとは切り離す。
- 情報を予測できる形に整理し、見出し、表、箇条書きで構造化する。
- アイコンと画像に代替テキストを付ける。飾りのアイコンは `aria-hidden="true"` にする（Fluent System Icons の SVG の既定）。アイコンだけのボタンには `aria-label` を付ける。
- 太字と斜体は、読み上げソフトによっては伝わらない。意味は要素（`strong`、`em`）か文字で伝える。
- ARIA はネイティブの要素で足りないときだけ、APG に従って補う。状態は `aria-pressed`、`aria-checked`、`aria-selected`、`aria-expanded`、`aria-current`、`aria-invalid` で表し、CSS もその属性で見た目を変える（約束の「状態」の規則）。
- 動画の字幕は、利用者がコントラストを変えられるようにする。難しければ十分なコントラストを確保する。

## 受け入れの確認

ページやコンポーネントを作ったら、次を確かめる。

| 項目 | 確かめ方 |
|---|---|
| 文字のコントラスト 4.5:1、大きな文字と非テキスト 3:1 | 使った前景と背景のトークンの組で計算する |
| 色だけで意味を伝えていない | 強制カラーと白黒の表示で、意味が残るか見る |
| キーボードだけで操作できる | Tab、Shift+Tab、Enter、Space、Esc、矢印キーで全操作を試す |
| フォーカスが見え、隠れない | Tab で移り、輪が見えるか、固定の要素に隠れないか見る |
| 400% と幅 320px で横スクロールが出ない | ブラウザーの拡大と、幅を狭めた表示で見る |
| 強制カラーで状態がわかる | Windows のコントラスト テーマか、開発者ツールの模擬で見る |
| 見出しのレベルと言語 | 見出しの順、`lang` 属性を確かめる |
| 操作の対象が 24 × 24 CSS px 以上か、十分に離れている | 小さい size の部品を並べた所で測る |
| 文言 | ボタン、ラベル、エラーが、この章の規則に合うか読む |

## v9 との差と未確認の点

- **基準の版**: サイトは WCAG 2.1 AA、Web Components の文書は 2.2 と書く。この設計書は 2.2 AA を目標にする（独自）。v9 の各コンポーネントが 2.2 の 2.5.8（操作の対象の大きさ）をすべて満たすかは確かめていない。小さい size の部品は、間隔で満たす必要がある可能性がある。
- **フォーカスの近似**: `:focus-visible` と `:has(:focus-visible)` は、v9 の keyborg の判定の近似である。
- **フォーカスのコントラスト**: フォーカスの表示に求めるコントラストの数値は、サイトのどのページにもない。
- **ハイコントラスト、タッチの対象の大きさ、動きを減らす設定**: サイトの accessibility のページは触れていない。この章の規則はソースからの読み取りと、この設計書の判断である。
- **日本語の UI の規則**: すべて独自である。Microsoft の日本語のスタイルガイドとの突き合わせはしていない。
- **サイトの do と don't の例**: content-design のページの例はすべて画像で、文字として取り出せなかった。
