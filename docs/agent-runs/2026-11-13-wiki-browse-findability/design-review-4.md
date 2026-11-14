## 判定

**却下。確信度：高。** 参照実装が、正常なMarkdownの解析とリンクの解決で、設計が維持するとした現行規則と食い違います。第9節の10例にはこの反例がなく、参照実装との一致を正しさの基準にできません。致命的な欠陥は確認していません。

## 致命的・重大な欠陥

1. **重大：参照実装がコード内の文字をリンクとして拾い、別のページを索引に載せる。**

   `a.md` と `b.md` が存在し、`index.md` が次の場合です。

   ```markdown
   # Index
   - `[[a]]` [[b]]
   ```

   現行の `_nav_item()` はコードスパンを除外し、**`b` を項目にします**。参照実装は行全体を正規表現で検索するため、**`a` を項目にします**。実際に両方をメモリ上で実行して確認しました。

   N3〜N6は項目の行き先を訂正しないため、最終的にも「索引」に載るページと「索引にないページ」が逆になります。読み取り失敗や競合は不要です。

   同じ原因で、参照実装はコードブロック内の `# Fake` や `- [[a]]` も木に取り込みます。また、Setext形式の見出しを認識しません。

   根拠：設計はN1の段階を「今と同じ」としていますが、[参照実装の行単位の解析](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/docs/agent-runs/2026-11-13-wiki-browse-findability/nav_model.py:61)は、[現行のトークンによる項目抽出](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:834)と異なります。[第1段階の3.7](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/docs/plans/wiki-browse-stage1-2026-11-09.md:161)も同じパーサーを使う契約です。

2. **重大：参照実装のリンク解決が、通常の `.md` つきリンクや短い名前を未解決にする。**

   `a.md` が存在し、`index.md` が次の場合です。

   ```markdown
   # Index
   - [[a.md]]
   ```

   次の入力を参照実装の `build()` に渡しました。

   ```python
   index_files = {"index.md": "# Index\n- [[a.md]]\n"}
   pages = {"a": "concept"}
   ```

   結果は「索引（0）: ?a.md」と「索引にないページ」の `a` です。一方、現行 `Core` は同じリンクを `a` に解決します。

   `concepts/a.md` だけが存在する場合の `[[a]]` でも、現行は解決し、参照実装は未解決になります。`[[indexes/x.md]]` も参照実装ではグループへのリンクになりません。

   参照実装は文字列の完全一致だけで判定し、現行の正規化・スラッグ解決を持っていません。これは通常のリンク表記で分類と件数が変わる反例です。

   根拠：[参照実装の判定](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/docs/agent-runs/2026-11-13-wiki-browse-findability/nav_model.py:77)、[現行の索引リンク解決](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:844)、[`.md`・区切り・NFCの正規化とスラッグ解決](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:483)。

## 崩れる前提

- **行への正規表現適用で、現行パーサーと同じ木を作れる。** コードスパン、コードブロック、Setext見出し、番号付きリストで崩れます。番号付きリストの項目も、参照実装では丸ごと失われました。
- **リンクの対象文字列とページのキーを直接比較すれば解決できる。** `.md` つきリンク、ディレクトリを省略したリンクで崩れます。
- **独自のfrontmatter解析でもN2の名前が一致する。** `題名: Custom` と本文の `# Heading` を持つ索引では、現行の名前は `Custom`、参照実装は `Heading` でした。
- **10例で参照実装と一致すれば、維持する既存規則も確認できる。** 上記の入力形式が含まれていないため、今回の欠陥を検出できません。[第9節の試験基準](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/docs/plans/wiki-browse-findability-2026-11-13.md:379)はこの不足を残しています。

## 見落としと軽微な問題

1. **軽微：参照実装のグループ要約が、N5の「表示の文字」にならない。**

   ```markdown
   - [[indexes/x]]: **bold** [[a|Alias]]
   ```

   参照実装の要約は `**bold** [[a|Alias]]` です。既存の `inline_text()` による表示文字は `bold Alias` でした。N5は4.2と同じ取り方を指定しているため、参照実装と文章が食い違います。

   根拠：[区切りだけを除く `after_link()`](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/docs/agent-runs/2026-11-13-wiki-browse-findability/nav_model.py:45)、[設計N5](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/docs/plans/wiki-browse-findability-2026-11-13.md:88)。

2. **軽微・試作：種類 `__proto__` の収集を直しても、表示名は壊れたまま。**

   実ファイルの `badge()` をNode上で実行すると、種類 `__proto__` の表示は `[object Object]`、`toString` は `function toString() { [native code] }` になります。`TYPE[t]` が継承プロパティを拾うためです。種類ボタンにも同じ参照式が残っています。

   根拠：[種類の表示辞書と `badge()`](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/poc/browse-findability/assets/proto.js:9)、[種類ボタンの表示名](C:/Works/info-hive-dev/.claude/worktrees/wiki-browse-findability/poc/browse-findability/assets/proto.js:304)。設計4.3の「ふつうの種類として扱う」を試作は満たしていません。

## 検証した事実

| 主張 | 結果 |
| --- | --- |
| 設計書の10例の表は `nav_model.py --markdown` の出力と一致する | **一致**。12行を比較 |
| 参照実装の解析が現行と同じ | **食い違い**。コード、Setext、番号付きリストで確認 |
| 参照実装のリンク解決が現行と同じ | **食い違い**。短い名前、`.md` つきリンクで確認 |
| N2のfrontmatterの読み方が現行と同じ | **食い違い**。日本語の `題名` キーで確認 |
| 参照実装が見出しアンカーを保持する | **保持しない**。`[[a#Details]]` は現行では `anchor: "details"`、参照実装では `("page", "a")` のみ |
| 遅延読み込みが各ブラウザのCSP・`file://`で動く | **確かめられず**。実ブラウザ試験は未実行 |
| 1,000行の索引ページが5秒以内に表示される | **確かめられず**。測定は未実行 |

検証はファイルの読み取りとメモリ上の実行に限り、ファイルは変更していません。

## 崩せなかった点

- 第3回レビューのN3反復による食い違いは、1回だけ畳む現行の参照実装では再発しませんでした。
- 見出しのない `index.md` が分割索引だけを指す例では、0件の「索引」の包みは残りませんでした。
- 中継・相互参照・自己参照の例で、木から外されたグループを指すリンクは作れませんでした。
- 要約を入力の文字から作る方針そのものに、P7に反する機械情報の追加は見つかりませんでした。
- 世代変更によるグループIDの意味の変化は、2.2・11に明記された限界として扱い、重大には数えていません。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
