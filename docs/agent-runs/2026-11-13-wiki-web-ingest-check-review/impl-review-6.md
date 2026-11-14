## 判定

**却下。確信度：高。** 表の見出し列を削除すると、残ったセル内のコードとリンク先を書き換えても検査を通せる。また、翻訳後に中断した取り込みを、変更された手順どおりに再開できない。

## 致命的・重大な欠陥

### 1. 【重大】見出し列の削除で検査対象から消えたセルを、翻訳段階で自由に書き換えられる

次の HTML を実物の `wiki_fetch.build()` に通した。雑音規則は有効にしている。

```html
<table>
<tr><th>A</th><th>B</th></tr>
<tr><td>1</td><td><code>SELECT 1;</code>
<a href="https://safe.example/">safe</a></td></tr>
</table>
```

取得器の出力は次になる。共通の frontmatter と題名は省略する。

```markdown
| A | B |
|---|---|
| 1 | `SELECT 1;` [safe](https://safe.example/) |
```

見出しと区切り行だけから第2列を削除する。

```markdown
| A |
|---|
| 1 | `SELECT 1;` [safe](https://safe.example/) |
```

**`freeze` は終了コード0、誤り・警告ともに空になる。** データ行の第2セルは raw に残るが、パーサーは見出しの列数を超えるため捨てる。

続いて `translated_by: "Model"` を設定し、残っている第2セルを変更する。

```markdown
| A |
|---|
| 1 | `DROP TABLE users;` [safe](https://evil.example/) |
```

**`check` も終了コード0、誤り・警告ともに空になる。** コード変更とリンク先変更の両方が検査を逃れる。

原因は、`freeze` がセルの部分列として見出し列の削除を許し、`check` が木に残らないセルについては**個数だけ**を比較すること。変更前後で各行のセル数は同じなので、追加された対策に掛からない。

`impl-root-causes-4.md` の「木に現れない部分を別に検査する」という対策は、この組み合わせでは成立しない。描画上は見えなくても、変更された内容は原本となる raw に保存される。

根拠：[wiki_rawcheck.py:389](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:389)、[セル数の収集:241](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:241)、[check の追加比較:667](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:667)。

### 2. 【重大】翻訳後の中断を「手順4から」再開すると、正しい raw を拒否する

再現手順：

1. `<p>English body.</p>` を取得し、無編集で `freeze` する。
2. 本文を `英語の本文である。` に訳し、`translated_by: "Model"` を設定する。
3. `check` が成功することを確認し、`--finish` 前に中断する。
4. 同じ URL・スラッグを再取得する。

再取得は次を返した。

```json
{"unchanged": true, "work_dir": true}
```

差分に含まれる `commands/ingest.md` は、この場合に「手順4から続ける」と指示する。手順5で再び `freeze` を実行すると、**終了コード1、`frontmatter` と `edit` の誤り**になる。比較先が翻訳前の `fetched.md` だからである。直前に `check` を通った正常な raw でも再現する。

さらに、この `unchanged` 応答には、後続手順が参照する `needs_translation` と `images` も含まれない。

作業用の写しが完成していることと、削除工程から再開できることを同一視している。途中再開の案内と、二段階の検査の状態が食い違う。

根拠：[再開の指示:31](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/commands/ingest.md:31)、[freeze の再実行:38](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/commands/ingest.md:38)、[unchanged の早期 return:1234](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py:1234)。

## 崩れる前提

- **取得器が整形した表なら、固定後も全セルがトークンに残る。** 削除工程で見出し列だけを減らすと崩れる。本文全体の部分列判定も、この操作は正当な文字削除なので通す。
- **セル数が変わらなければ、木に残らないセルの変更も検出できる。** 同じセル内のコード・URL・文章の置換では成立しない。
- **`work_dir: true` なら削除工程から再開できる。** `cleaned.md` があり、raw が翻訳・補足工程に進んでいる状態では成立しない。
- **補足の先頭と後続段落を、同じ文字抽出方法で判定している。** 先頭はインラインコードを含め、後続段落は除外している。

## 見落としと軽微な問題

### 【軽微】後続段落の表示名をコードにすると、二つ目の補足を見逃す

取得済み画像の直後に次を追加し、`translated_by` を `Model` にすると、**`check` は誤り・警告なしで成功し、表示名を `Model` だけと報告した。**

```markdown
> Model 補足: 一つ目の説明。
>
> `Other` 補足: 二つ目の説明。
```

`caption_of()` は `code=True` で読むが、後続段落を調べる `later` は既定の `code=False` で読む。後者では `Other` が消え、補足開始を認識しない。先頭の表示名を `` `Model` `` にした補足は認識されることも確認した。

根拠：[caption_of:449](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:449)、[後続段落の抽出:502](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:502)。

### 【軽微】既存試験は、今回の組み合わせを検証していない

- `test_extra_table_cell_is_rejected` はセルを**追加する操作**だけを扱う。見出し列の削除後、既存の余剰セルを書き換える経路は扱わない。[試験:694](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/test_wiki_web_check.py:694)
- `test_unchanged_reports_missing_work_dir` は写しがない状態だけを扱う。翻訳済み raw と `cleaned.md` が残る状態の再開は扱わない。[試験:183](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/test_wiki_web_check.py:183)
- `test_code_only_caption_is_not_empty` は補足の最初の段落だけを扱い、後続段落のコード入り表示名は扱わない。[試験:760](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/test_wiki_web_check.py:760)

## 検証した事実

- **一致：** 指定ファイル、過去1〜5回のレビューと原因分類、設計を確認した。`impl-6.submodule.diff` 内の追加 `wiki_rawcheck.py` は実ファイルと一致した。
- **一致：** `wiki_pages.new_parser()` は同梱の markdown-it-py を使い、`commonmark`、HTML無効、表有効である。
- **一致：** ファイル入出力をメモリに置き換え、検査関連42試験と、雑音規則・HTMLファイル・作業用の写しなどの14試験が成功した。追加反例も実物の変換・検査処理で再現した。
- **一致：** 写しの出力順は `fetched.md` → `fetch.json.tmp` → `fetch.json` への名前変更 → raw 出力だった。一時JSONの部分書き込み失敗を注入すると、raw は出力されず、完成判定も偽になった。
- **確かめられず：** 通常のファイル入出力による全試験の成功。指定コマンドに `-B` を加えた実行では、81試験中74試験が一時ディレクトリを作れずエラーになった。環境制約による結果であり、実装の失敗とは数えていない。
- リポジトリのファイルは変更していない。実ネットワーク取得、実ジャンクション作成、実際の再帰削除は行っていない。

## 崩せなかった点

- 貪欲な部分列判定そのものと、重複段落に関する既存反例。
- 強調内のリンク削除、リスト内コード、エスケープした `]`、日本語・`%20` の画像パスに関する既存反例。
- 引用・リスト内の正しい補足、原文の補足形式の引用保持、参照定義の移動に関する既存反例。
- 5回目の「補足内の画像」「深い引用での指数的再計算」「コードだけの補足」「リンクtitle追記」の既存反例。
- 雑音規則の既存対照、`--html-file` の基準URLとUTF-8拒否、写しの書き込み失敗時の検査。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
