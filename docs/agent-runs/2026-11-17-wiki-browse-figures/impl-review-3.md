## 判定

**条件付きで採用可。確信度：中。** 致命的・重大な欠陥は崩せなかった。ただし、隔離テストの参照先の誤り、配色変更後の違反の見落とし、不正な画像応答を成功扱いする問題が残る。ブラウザでの再検証はできていない。

## 致命的・重大な欠陥

なし。

## 崩れる前提

- **「隔離テストの `secret` は、存在する保護対象を指す」**  
  `concepts/流れ.html` を基準に `new URL("nav.js", page.url())` を作ると、`concepts/nav.js` になる。実際の配信先は wiki の出力ルートの `nav.js` である。

- **「受理した SVG 文字列は画像として読める」**  
  `<svg>` や `<svgnot-an-image/>` でも `imageUrl` は成功する。画像の読み込み成否は確認していない。

- **「CSP 違反とエラーの判定は、配色変更後まで含む」**  
  判定する配列は配色変更前のコピーであり、変更後の違反やエラーは反映されない。

- **「HTTP で開いた出力には、専用の枠の配信経路がある」**  
  静的出力を一般の HTTP サーバーで開くと崩れる。`figures.js` は動き、同梱されていない `/_frame/…` を要求し、最終的に警告になる。設計が明示する `file://` の範囲では発生しない。

## 見落としと軽微な問題

1. **軽微：隔離テストの `<script>` 側は、存在しないファイルの読み込み失敗を合格にできる。**

   再現例：

   ```js
   new URL("nav.js",
     "http://127.0.0.1:41234/TOKEN/w/KEY/concepts/page.html").pathname
   // /TOKEN/w/KEY/concepts/nav.js
   ```

   正しい保護対象は `/TOKEN/w/KEY/nav.js`。したがって、スクリプトの CSP 制限が弱まっても、誤った参照先の 404 によって `s.onerror` が発火し、「止まった」と判定できる。これは隔離の破綻を実証した指摘ではなく、試験の検出能力の欠陥である。

   根拠：[figures.test.mjs:259](C:/Works/info-hive-dev/.claude/worktrees/browse-figures/tests/wiki/browse/figures.test.mjs:259)、[wiki_browse.py:513](C:/Works/info-hive-dev/.claude/worktrees/browse-figures/info-hive-wiki/skills/info-hive/scripts/wiki_browse.py:513)。設計 §10.2 が挙げる、実在するページ・`nav.js`・`data/search.js` の検証とも食い違う。

2. **軽微：配色変更によって初めて発生する CSP 違反とコンソールエラーを見落とす。**

   `r.violations` と `r.errors` は変更前に確定する。変更後の収集は図の数と `style` 属性などに限定され、最終判定は古い配列を使う。

   例えば、暗い配色への変更時だけ親にインラインの `<style>` を追加する退行では、図の描画が成功し続ければ、CSP 違反が発生しても当該判定はゼロのままになる。`<style>` 要素には `style` 属性がないため、その属性数の判定でも捕捉できない。

   根拠：[figures.test.mjs:231](C:/Works/info-hive-dev/.claude/worktrees/browse-figures/tests/wiki/browse/figures.test.mjs:231)、同ファイルの235行以降、468行の判定。

3. **軽微：不正な SVG 応答でも、コードを閉じて画像の成功状態にする。**

   枠が次を返すと、`imageUrl` は URL を返し、`showImage` が呼ばれる。

   ```js
   { type: "result", ok: true, svg: "<svg>", w: 40, h: 20 }
   ```

   XML として成立しない文字列だが、画像の `error` を処理する箇所がない。読み込みに失敗しても警告へ移らず、コードは閉じた Accordion に入る。受理することは実コードを Node VM で実行して確認した。ブラウザでの表示結果は未実測。

   根拠：[figures.js:189](C:/Works/info-hive-dev/.claude/worktrees/browse-figures/info-hive-wiki/skills/info-hive/scripts/browse_assets/figures.js:189)、[figures.js:128](C:/Works/info-hive-dev/.claude/worktrees/browse-figures/info-hive-wiki/skills/info-hive/scripts/browse_assets/figures.js:128)。

## 検証した事実

- **一致：** 同梱物のハッシュ・サイズ、枠の版、HTML の外部スクリプト構成、ライセンスファイルの存在、CSP の計5試験を、ファイルを作る `setUp` を呼ばずに実行し、通過した。
- **一致：** 実際のルーティング関数をメモリー上の応答先につなぎ、3ファイルの本文・CSP・キャッシュ、HEAD の本文なし、不正パス6件の404、POST の405、不一致Hostの421を確認した。
- **一致：** サーバーの待ち受けは `127.0.0.1` 固定で、枠の経路より先にHostを検査する。
- **食い違い：** 不正な SVG 文字列を画像として受理する。隔離テストのURLも実際の配信先と異なる。
- **確かめられず：** Playwright は一時ディレクトリ作成時に `EPERM` となり起動できなかった。実ブラウザの隔離、描画、画像比較の閾値は再検証していない。ファイルは変更していない。

## 崩せなかった点

- 実コードを使った状態遷移の模擬実行では、別の送信元と `ready` 前の `result` は無視された。
- 二重の `ready` でも送信は1回、二重の `result` でも画像への反映は1回だった。
- `stop()` 後は枠・タイマー・受信リスナーがすべて消え、警告は追加されなかった。停止と再開始を含む模擬実行の最大枠数は2だった。
- 親へ送る内容は当該図のソースと配色に限られ、返された SVG を親の DOM に挿入する処理は見つからなかった。
- `/_frame/` から、固定の3ファイル以外やトークン付き経路へ抜ける反例は見つからなかった。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
