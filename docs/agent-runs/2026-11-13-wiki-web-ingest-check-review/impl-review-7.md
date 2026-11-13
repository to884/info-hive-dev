## 判定

**却下。確信度：高。** コードとリンク先の変更、画像ファイルの欠落が検査を通る反例を確認した。また、失敗した freeze の不完全な出力を「固定済み」として再開できる。

## 致命的・重大な欠陥

### 1. 【重大】リスト先頭の表では、6回目の余剰セルによる検査回避が残る

次の HTML を実物の `wiki_fetch.build()` に通した。

```html
<ul><li><table>
<tr><th>A</th><th>B</th></tr>
<tr><td>1</td><td><code>SELECT 1;</code>
<a href="https://safe.example/">safe</a></td></tr>
</table></li></ul>
```

取得結果は次になる。共通の frontmatter と題名は省略する。

```markdown
- | A | B |
  |---|---|
  | 1 | `SELECT 1;` [safe](https://safe.example/) |
```

見出しと区切り行だけから第2列を削除する。

```markdown
- | A |
  |---|
  | 1 | `SELECT 1;` [safe](https://safe.example/) |
```

**freeze は終了コード0、誤り・警告なし。** 続いて `translated_by: "Model"` を設定し、データ行を次に変えても、**check は終了コード0、誤り・警告なし**になる。

```markdown
  | 1 | `DROP TABLE users;` [safe](https://evil.example/) |
```

`table_cells()` は行頭の空白と `>` しか除かない。見出し行の `- ` を余分なセルとして数えるため、削除後の計数は **`[2, 1, 2]`** になる。実際の見出しは1列だが、freeze は「データ行が見出しより多い」と判定しない。第2セルはパーサーに捨てられ、check の木の比較から消える。変更前後でセル数も同じなので、追加の比較も通る。

`impl-root-causes-6.md` の「見えない内容が raw に残らない」という主張とは**食い違う**。

根拠：[table_cells](/C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:241)、[freeze の余剰セル判定](/C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:400)、[check の追加比較](/C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:678)。

### 2. 【重大】文字参照を含むスラッグで画像照合がずれ、正常系の拒否と欠落の見逃しが起きる

`check_slug()` が受理する **`a&amp;b`** をスラッグとし、次を取得した。

```html
<p>Body.</p><img src="i.png">
```

取得器は画像ファイルを保存し、次の Markdown を出す。

```markdown
![](assets/a&amp;b/a&amp;b-01.png "https://site.example/i.png")
```

取得記録とパーサーの値は一致しない。

| 対象 | パス |
|---|---|
| `images[].path` と `fetched_images()` のキー | `assets/a&amp;b/a&amp;b-01.png` |
| パーサーの `image.src` | `assets/a&b/a&b-01.png` |

実行結果：

- **無編集・画像ファイルあり**：freeze は「画像を消したのに、ファイルが残っている」で終了コード1。
- **画像記法を残して、保存した画像ファイルだけ削除**：freeze は終了コード0。
- 本文を日本語に訳して `translated_by: "Model"` を設定し、**補足を書かなくても check は終了コード0、誤り・警告なし**。

Markdown のリンク先を読む処理には文字参照の復号もある。`normalizeLink()` だけを取得記録へ適用しても、その処理全体とは一致しない。画像が取得済みとして認識されず、ファイル検査と補足要求の両方を逃れる。

根拠：[fetched_images](/C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:131)、[freeze の画像照合](/C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:416)、[取得済み判定](/C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:490)、[画像記法の生成](/C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py:1340)。

### 3. 【重大】失敗した freeze の部分ファイルを、固定済みの検査基準に採用する

書き込み失敗を注入して再現した。仮定した障害は、`cleaned.md` の先頭部分を書いたあとに `OSError` が発生することである。

再現手順：

1. `<p>Opening paragraph.</p><pre>SELECT 1;</pre>` を取得する。
2. 無編集で freeze する。
3. `cleaned.md` への書き込みを、コードフェンス直前まで保存したところで失敗させる。**freeze は成功していない。**
4. 同じ URL・スラッグを再取得する。

再取得は次を返した。

```json
{"unchanged": true, "work_dir": true, "work_stage": "frozen"}
```

さらに、raw を不完全な `cleaned.md` に合わせてコードブロックを落とし、`translated_by` を設定すると、**check は終了コード0、誤り・警告なし**になった。

freeze は `cleaned.md` を直接書き、再開側はその**存在だけ**で固定済みとする。check も、freeze が成功したか、固定結果が完成しているかを確かめない。したがって、未完成の基準に合わせた内容欠落を認証してしまう。

根拠：[固定結果の直接書き込み](/C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:439)、[存在による段階判定](/C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py:1244)、[check の基準読み込み](/C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:620)。

## 崩れる前提

- **元の行から数えたセル数は、パーサーの列数と一致する。** 表の見出し行にリスト記号が付くと崩れる。構造の一部を再び正規表現で推し量っている。
- **取得記録へ `normalizeLink()` をかければ、画像トークンのパスになる。** Markdown の文字参照復号が入るパスでは崩れる。
- **`cleaned.md` が存在すれば、freeze は完了している。** 部分書き込み失敗で崩れる。`fetched.md` と `fetch.json` の完成判定は、固定結果の完成を保証しない。

## 見落としと軽微な問題

- **【軽微】余剰セルの回帰試験は入れ物との組み合わせを扱わない。** `ReviewCounterexample6Test.test_hidden_cells_after_removing_a_header_column` は、リスト記号のない表だけを調べる。今回の重大1は、この試験を通る実装でも再現する。[該当試験](/C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/test_wiki_web_check.py:779)
- **【軽微】再開試験の説明と実際の操作が違う。** `test_unchanged_reports_stage_and_values` は「訳したあとに止まった取り込み」と説明するが、実際には取得・freeze・再取得だけで、raw を翻訳していない。返却値は確認するが、翻訳済み raw の継続検査までは確認していない。[該当試験](/C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/test_wiki_web_check.py:798)
- **【軽微】障害試験は固定結果の書き込み失敗を扱わない。** 現在の失敗注入は `fetch.json` の名前変更を対象としており、`cleaned.md` の部分書き込みと、その後の段階判定は対象外である。[該当試験](/C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/test_wiki_web_check.py:193)

## 検証した事実

- **一致：** `impl-7.submodule.diff` に含まれる追加 `wiki_rawcheck.py` は、実ファイルと完全一致した。
- **一致：** `wiki_pages.new_parser()` は同梱の markdown-it-py を使い、`commonmark`、HTML無効、表有効である。
- **一致：** ファイル入出力をメモリに置き換え、検査関連44試験と、取得・雑音規則・HTMLファイル・再開などの15試験が成功した。追加反例でも、変換・パーサー・freeze・check は実物を使用した。
- **一致：** 写しは `fetched.md` → 一時JSON → `fetch.json` への名前変更 → raw 出力の順に作られる。名前変更失敗を扱う既存試験も上記の実行で成功した。
- **確かめられず：** 通常のファイル入出力による全試験の成功。指定コマンドに `-B` を加えた実行では、84試験中77試験が一時ディレクトリを作れずエラーになった。環境制約として扱い、実装の試験失敗とは数えていない。
- リポジトリのファイルは変更していない。実ネットワーク取得、実ジャンクション作成、実際の再帰削除は行っていない。

## 崩せなかった点

既存反例の範囲では、次は崩せなかった。

- 貪欲な部分列判定そのもの、重複段落の対応、強調内の共有リンク削除。
- リスト内コード、エスケープした `]`、日本語・`%20` の画像パス。
- 引用・リスト内の補足、原文の補足形式の引用保持、補足内の画像拒否、コードを含む後続補足の検出。
- 深い引用での指数的再計算への対策、リンクの title 保持。
- 雑音規則の既存対照、`--html-file` の基準URLと非UTF-8拒否。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
