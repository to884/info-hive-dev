## 判定

**却下。確信度：高。** 正常な索引で、N6 により非表示になるグループへのリンクが残り、指定したグループで一覧を絞る約束が破れます。致命的な欠陥は確認していません。

## 致命的・重大な欠陥

1. **重大・設計：N6 が参照先のグループを除外する一方、そのグループへのリンクの扱いが決まっていない。**

   通常のページ `a.md`、`b.md` が存在し、索引が次の場合です。読み取り失敗も再生成も必要ありません。

   ```markdown
   <!-- index.md -->
   # 入口
   - [[a]]
   - [[indexes/relay]]
   ```

   ```markdown
   <!-- indexes/relay.md -->
   # 中継
   - [[indexes/leaf]]
   ```

   ```markdown
   <!-- indexes/leaf.md -->
   # 記事
   - [[b]]
   ```

   N3・N4 の変換後、N6 により「中継」は木に出なくなります。しかし、「索引」グループは `a` を持つため残り、そこにある `indexes/relay` への項目も残ります。

   3.1 は、この項目を `index.html#group=<中継のID>` へのリンクにする規則です。除外後の木を `nav.js` に書けば、その ID は存在しません。4.3 の「知らない ID なら絞り込まない」に従うと、リンクから**全ページの一覧が開きます**。

   現行の `Core._nav()` にこの入力を渡し、その結果へ N3・N4・N6 をメモリ上で適用して、残ったリンクの参照先 ID が木に存在しないことを確認しました。非表示グループを別途保持する解釈も考えられますが、その登録先や絞り込み時の扱いは設計にありません。

   第9節の検査変更も、この反例を通します。`a` と `b` の `data-groups` は、残ったグループだけを参照するため、「`data-groups` の ID がすべて `nav.js` にある」は成立します。

   根拠：[設計 N3〜N6（70〜73行）](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/docs/plans/wiki-browse-findability-2026-11-13.md:70)、同3.1・4.3・9（133・220・341行）。現行のグループ参照生成は [wiki_browse_core.py](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:834)。

## 崩れる前提

- **木からグループを除いても、その ID を使う項目には影響しない。** 別の残存グループから参照されている場合に崩れます。上記の反例です。
- **文字列全体の小文字化と、符号位置ごとの小文字化は同じになる。** ギリシャ文字の語末の `Σ` で崩れ、照合と強調表示が一致しません。
- **世代違いの通知があれば、グループ ID の意味も一致する。** 旧 HTML の `data-groups` と、新 `nav.js` の通し番号が別のグループを表す場合、通知しても対応は戻りません。これは初回レビューと設計2.2・11に記載された限界なので、重大には数えていません。

## 見落としと軽微な問題

1. **軽微・設計と試作：検索に当たる題名でも、強調表示が付かない。**

   題名 `ΟΣ`、問い合わせ `ος` で再現します。

   ```text
   文字列全体の toLowerCase():       ος
   符号位置ごとの toLowerCase() の連結: οσ
   ```

   5.2 の照合には成功しますが、5.3 の強調用文字列には問い合わせがありません。試作の実際の `highlight()` を Node 上で実行し、検索相当の照合は `true`、生成される `<mark>` は0個になることを確認しました。

   根拠：[設計5.2・5.3（251・283行）](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/docs/plans/wiki-browse-findability-2026-11-13.md:251)、[proto.js の強調処理](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/poc/browse-findability/assets/proto.js:55)。

2. **軽微・試験：遅延読み込みの成功時の約束を、第9節の列挙では検証できない。**

   フォーカス前に検索データを取得しないこと、読み込み中の入力を完了時に反映すること、検索データだけが別世代だった場合の通知は、検査として列挙されていません。最初から検索データを読む誤実装でも、検索結果と404時の検査には合格し得ます。

   試作も検索データを通常の `<script src>` で先に読むため、この部分の実証にはなりません。

   根拠：[設計5.4・9（288・356行）](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/docs/plans/wiki-browse-findability-2026-11-13.md:288)、[proto.py の読み込み](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/poc/browse-findability/proto.py:254)。

3. **軽微・試験：現在の起動時間の試験では、1,000行の索引ページを開かない。**

   `startup.test.mjs` は `--page ページ0` で記事を開き、`navLoaded` までを測っています。設計11で一覧の事前描画の量を起動時間と結び付けていますが、現在の測定対象には、その索引ページの HTML の解析・描画が入りません。

   根拠：[startup.test.mjs](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/tests/wiki/browse/startup.test.mjs:43)、設計9・11（366・387行）。

## 検証した事実

| 主張 | 結果 |
| --- | --- |
| N2 の「最初の見出し」は現行実装と同じ | **一致**。現行は深さによらず最初の見出しを取る |
| 現行の見出し処理は h1 も扱う | **一致**。実際に `assign_heading_ids()` を呼び、ID を確認 |
| 試作の変換中の Enter・Esc の修正 | **一致**。実ハンドラーに `isComposing` と `keyCode: 229` を別々に渡し、移動・消去がないことを確認 |
| 試作が複数所属の経路を集める | **一致**。実際の `pathsTo()` が2本の経路を返した |
| 相対 URL でサーバーのトークンを引き継げる | **一致**。`data-root` と相対 URL の解決を、記事・索引・`file://` の例で確認 |
| 遅延読み込みが CSP と各ブラウザの `file://` で動く | **確かめられず**。試作には遅延読み込みがなく、実ブラウザ試験は未実行 |

検証は読み取りとメモリ上の実行に限り、ファイルは変更していません。

## 崩せなかった点

- 初回レビューの「h1 直後の項目の所属が決まらない」反例は、第2版の N1→N3→N4 では所属が決まります。
- 要約を入力の文字と既存パーサーから作る方針について、P7 に反する機械情報の追加は見つかりませんでした。
- `inline_text()` の結果を HTML エスケープする経路では、wikilink の表示名に含む `<script>`、インラインコード、`&` から HTML が実行される反例は得られませんでした。
- `js_data()` の `</`・U+2028・U+2029 のエスケープと、結果を `textContent` で描く方針は崩せませんでした。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
