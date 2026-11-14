## 判定

**条件付きで採用可。確信度：高。** 2版目の採用根拠である「扱えない Markdown は警告と試験で排除する」が、具体的な反例で崩れた。現行文書への変更をメモリ上で再現し、出力が壊れても関連する検査を通過することを確認した。

## 致命的・重大な欠陥

1. **重大：範囲外の Markdown を検出できず、コード例の改変やリンクの消失を検査が見逃す。**

   **反例A：引用内で字下げしたチルダのフェンス**

   `docs/commands.md` の query 節に次を加える。

   ```markdown
   > text
   >   ~~~md
   >   [search](./search.md)
   >   ~~~
   ```

   同梱の Markdown パーサーでは、引用内のコードブロックになる。しかし `unsupported_markdown()` は空配列を返し、`rewrite_links()` はコード例の宛先を `file:///…/docs/search.md` に改変する。警告もない。

   原因は、`CONTAINER_FENCE_RE` が `>` の直後の空白を最大1文字しか扱わず、追加の字下げを取りこぼすこと。[wiki_help.py:65](/C:/Works/info-hive-dev/.claude/worktrees/wiki-help-command/info-hive-wiki/skills/info-hive/scripts/wiki_help.py:65)

   **反例B：参照リンクの定義を最初のコマンド見出しより前に置く**

   文書の先頭に次を加える。

   ```markdown
   [s]: ./search.md
   ```

   query 節には次を加える。

   ```markdown
   [search][s]
   ```

   元の文書ではリンクになる。詳細ヘルプでは定義が切り落とされ、`[search][s]` という文字列になる。参照リンクの使用箇所を検査せず、定義も取り出した節の中だけで検査するため、警告が出ない。[wiki_help.py:305](/C:/Works/info-hive-dev/.claude/worktrees/wiki-help-command/info-hive-wiki/skills/info-hive/scripts/wiki_help.py:305)、[wiki_help.py:382](/C:/Works/info-hive-dev/.claude/worktrees/wiki-help-command/info-hive-wiki/skills/info-hive/scripts/wiki_help.py:382)

   **検証結果：** どちらもメモリ上で文書を差し替え、既存の `test_every_section_is_in_supported_range()` がそのまま通ることを確認した。出力リンクの検査条件も通過した。試験の `link_targets()` が本体と同じフェンス判定・コード判定・リンク正規表現を使うため、本体が見落としたリンクを試験も見落とす。[test_help_command.py:53](/C:/Works/info-hive-dev/.claude/worktrees/wiki-help-command/tests/wiki/test_help_command.py:53)、同:355、369

   したがって、設計:97の「範囲外を足したらCIが落ちる」と、`docs/commands.md:177` の「警告を出し、試験が落ちる」は実装と食い違う。現行文書にこの反例が含まれているという指摘ではない。

## 崩れる前提

- **検査と書き換えが同じ読み方なら、出力の正しさを検証できる。** 両者が同じリンクを認識し損ねると、相対リンクが残っても検査対象にならない。
- **範囲外の構文は取り出した節だけを調べれば分かる。** 参照リンクの定義を節の外に置くと崩れる。
- **バッククォートの並びはコード区間の区切りである。** バックスラッシュでエスケープされたバッククォートで崩れる。
- **`file:` URI のパス部分だけで元のファイルを復元できる。** UNC URI ではサーバー名が `netloc` に入り、パス部分だけでは復元できない。

## 見落としと軽微な問題

1. **軽微：範囲内の通常リンクも、エスケープされたバッククォートによって書き換えから漏れる。**

   ```markdown
   \`prefix [search](./search.md) suffix\`
   ```

   Markdown としては、バッククォートの文字に挟まれた通常のリンクになる。本体はこれをコード区間と誤認し、相対リンクのまま返す。警告はなく、関連する出力検査も通過した。

   `mask_code_spans()` がバッククォート直前のエスケープを調べていない。[wiki_help.py:275](/C:/Works/info-hive-dev/.claude/worktrees/wiki-help-command/info-hive-wiki/skills/info-hive/scripts/wiki_help.py:275)

2. **軽微：許容範囲として記載されたリンクでも誤検出する。**

   ```markdown
   [search [note] text](./search.md)
   ```

   同梱パーサーでは有効なインラインリンクになる。宛先に空白・丸括弧はないが、本体は「書き換えられないリンク」と警告し、変換しない。`LINK_RE` がラベル内の `]` を扱えないためで、ラベルのこの制限は設計の範囲表に書かれていない。[wiki_help.py:71](/C:/Works/info-hive-dev/.claude/worktrees/wiki-help-command/info-hive-wiki/skills/info-hive/scripts/wiki_help.py:71)

3. **軽微：文字参照で書かれたフラグメントから、別のファイルを指す URI を生成する。**

   ```markdown
   [x](./search.md&#35;intro)
   ```

   元のリンク先は `./search.md#intro`。本体は文字参照を復号する前に `#` で分割するため、`search.md&` をファイル名として扱い、末尾が `search.md%26` の URI と不存在警告を生成する。範囲検査はこの記法を通す。[wiki_help.py:339](/C:/Works/info-hive-dev/.claude/worktrees/wiki-help-command/info-hive-wiki/skills/info-hive/scripts/wiki_help.py:339)

4. **軽微：試験側の URI 復元が UNC パスを誤判定する。**

   ```text
   file://server/share/plugin/docs/search.md
   ```

   `path_from_file_uri()` に渡すと、Windows 上で `\share\plugin\docs\search.md` になる。`server` が失われるため、UNC 上に正しく導入された場合でも、実在確認が別の場所を検査する。[test_help_command.py:412](/C:/Works/info-hive-dev/.claude/worktrees/wiki-help-command/tests/wiki/test_help_command.py:412)

## 検証した事実

- **一致：** Windows・Python 3.14.6で、書き込み不要な新規試験23件と既存の `RealCommandsTests` 2件、計25件が通った。一時ファイルを作る試験とCI全体は実行していない。
- **一致：** 現行11コマンドは詳細を出し、標準エラーは空だった。
- **一致：** 一覧の描画を変更前の実装と同じメタデータで比較し、完全一致した。現行一覧は33行、JSONは従来の5キーを持つ配列。help のメタデータ変更は計画どおりだった。
- **一致：** `.github/workflows/wiki-mcp.yml:106` に新規試験の実行が追加されている。ただし、その試験の検出漏れは上記のとおり。
- **一致：** 日本語・空白を含むパスの百分率符号化と、通常の相対リンクのフラグメント除去は確認した。
- **一致：** `plugin.json` は0.14.0、CHANGELOGへの追記も同版。ローカルHEADは `bdae5f5`、ローカルに `v0.14.0` タグはなかった。
- **確かめられず：** Claude Code経由の引数処理、対話セッションでの展開、デスクトップアプリでのリンク開封、実際のUNC・ジャンクション・8.3名を使った導入。CLIの直接試験や文面検査を、これらの実動作確認として扱うことはできない。

## 崩せなかった点

- `commands/help.md` の手順をそのとおり実行する条件では、許可された英数字・ハイフンの値から、1版目の引用符脱出を再現できなかった。Git Bashの引数変換対象になる `/`・`:` も値に残らない。
- 名前を収集済みコマンドとだけ照合する処理から、`../` を使って任意の文書を読む経路は見つからなかった。
- 現行文書での節の取り違え、通常フェンス内の見出しによる誤終了、閉じる `#` を付けた見出しの取りこぼしは再現しなかった。
- `/wiki:help /wiki:query` を保証対象から外したことは、案内文と一致している。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
