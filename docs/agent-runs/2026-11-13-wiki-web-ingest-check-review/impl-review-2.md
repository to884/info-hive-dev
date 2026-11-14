## 判定

**却下。確信度：高。** 日本語スラッグでは無編集の取得結果を拒否し、逆に画像ファイルの欠落を見逃す。補足の検査にも、正しい追記を拒む入力と、規則違反が通る入力が残っている。

## 致命的・重大な欠陥

### 1. 【重大】日本語の画像パスが照合できず、正常系の拒否と欠落の見逃しが両方起きる

`--slug 日本語` で画像を取得すると、現在の `wiki_fetch.py` は次を生成する。

```markdown
![x](assets/日本語/日本語-01.png "https://x.example/i.png")
```

`fetch.json` の `images[].path` も日本語のパスになる。一方、パーサーの `image.src` は `assets/%E6%97%A5…` という百分率符号化されたパスになる。

実行結果：

- **無編集・ファイルあり**：`freeze` が「画像を消したのに、ファイルが残っている」で終了コード1。
- **同じ画像記法を残してファイルだけ削除**：`freeze` が終了コード0。続く `check` も、補足なしで終了コード0・警告なし。
- 正常な補足を付けた `check` は「取得できなかった画像に補足がある」で拒否する。

取得記録とトークンのパスを直接比較しているため、取得済み画像を未取得として扱う。前回の重大9に相当する欠落の見逃しが、日本語パスでは残る。

根拠：[wiki_rawcheck.py:116](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:116)、[同:304](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:304)、[同:373](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:373)。取得側は [wiki_fetch.py:1300](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py:1300)。

### 2. 【重大】リスト内の画像に後続本文があると、手順どおりの補足を拒否する

現在の取得器は、次の HTML：

```html
<ul><li>item<img src="i.png" alt="x">tail</li></ul>
```

から次を生成する。

```markdown
- item
  ![x](assets/a/a-01.png "https://x.example/i.png")
  tail
```

取り込み手順が指定する「画像の行の次」「同じ字下げ」で補足すると、次になる。

```markdown
- item
  ![x](assets/a/a-01.png "https://x.example/i.png")

  > Model 補足: 図の説明である。

  tail
```

**`check` は終了コード1**。「list_item の中のブロックの数が違う（取得1、raw2）」となる。本文を保存したまま補足を挿入しているが、元の一つの段落が補足の前後で分割されるため拒否される。

前回の重大5の回帰試験は画像が項目末尾にある場合だけで、後続本文を持つ取得結果を確かめていない。

根拠：[wiki_fetch.py:870](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py:870)、[wiki_rawcheck.py:450](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:450)、[commands/ingest.md:40](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/commands/ingest.md:40)、[test_wiki_web_check.py:468](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/tests/wiki/test_wiki_web_check.py:468)。

### 3. 【重大】補足内に入れ子の補足を置くと、複数補足と表示名不一致が通る

取得済みの画像に次を付ける。

```markdown
![x](assets/a/1.png)

> Model 補足: 説明１。
>
> > Other 補足: 説明２。
```

**`check` は終了コード0・警告なし**。認識される表示名は `Model` だけになる。引用内のリストに `Other 補足: …` を置いた場合も通った。

二つ目の補足の探索は、最初の段落の文字列と、引用直下で `inline` を持つ節点だけを見る。入れ子の引用やリストには降りず、外側の補足全体を比較対象から除去する。

設計の「1つの引用の中に2つ目の補足の始まりがあれば誤り」と食い違う。`impl-root-causes-1.md` の「本文の中の2つ目も検出する」という修正説明は、この形では成立しない。

根拠：[wiki_rawcheck.py:379](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:379)、[同:384](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:384)、設計71行。

### 4. 【重大】原文の引用を補足と誤認し、正しい追記後も原文保持を認めない

次の HTML は、現在の取得器でそのまま対応する画像と引用になる。

```html
<img src="i.png">
<blockquote><p>Alice 補足: 図の前提。</p></blockquote>
```

日本語ページとして無編集で `freeze` した後、モデルの補足を追記する。

```markdown
![x](assets/a/a-01.png "https://x.example/i.png")

> Model 補足: 図の説明である。

> Alice 補足: 図の前提。
```

**`check` は終了コード1**。補足が2個、表示名が不一致、ブロック数が不一致になる。

`strip_captions` は原文にも存在する引用かを確認せず、原文の `Alice` の引用まで補足として取り除く。保存すべき原文と、モデルが追加した補足を区別できていない。

根拠：[wiki_rawcheck.py:348](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:348)、[同:379](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:379)、[同:523](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:523)。

### 5. 【重大】強調内では、共有リンクを丸ごと消す正当な雑音削除も拒否する

取得器に次を渡す。

```html
<p><strong>Body text. <a href="/share">Share</a></strong></p>
```

出力と削除後：

```markdown
取得時: **Body text. [Share](https://x.example/share)**
削除後: **Body text.**
```

共有リンクと直前の空白だけを削除している。本文と強調を残し、リンクも丸ごと削除しているが、**`freeze` は終了コード1**になる。

外側の `strong_open` から `strong_close` まで全体を不可分の単位にするため、内部のリンクを独立して削除できない。これは設計61行とは**一致**する。ただし、リンク全体の削除を許す取り込み手順と、雑音だけを除去する目的には食い違う。

根拠：[wiki_rawcheck.py:201](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:201)、[commands/ingest.md:37](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/commands/ingest.md:37)。

### 6. 【重大】rawcheck はスラッグを検査せず、wiki 全体を再帰削除先として渡せる

`wiki_fetch.py` と違い、`wiki_rawcheck.py` は `--slug` を検査しない。

次の状態を仮定する。

- `<wiki>/.wiki-cache/ingest/` が存在する。
- `<wiki>/cleaned.md`、`<wiki>/fetch.json` が存在する。
- `<raw-root>/../...md` が存在し、上記基準との `check` を通る。

この状態で：

```text
wiki_rawcheck.py check --wiki <wiki> --raw-root <raw-root> --slug ../.. --finish
```

を実行すると、削除先は `<wiki>/.wiki-cache/ingest/../..`、つまり **wiki ルート自身**になる。`commonpath` の結果が wiki と等しいので拒否されない。

ファイルの存在をメモリ上で再現し、`rmtree` だけを差し替えて確認した。**`main` は終了コード0を返し、wiki ルートに解決されるパスを `rmtree` に渡した**。実際の削除は行っていない。

根拠：[wiki_rawcheck.py:64](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:64)、[同:86](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:86)、[同:578](C:/Works/info-hive-dev/.claude/worktrees/web-ingest-check/info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:578)。

## 崩れる前提

- **取得記録のファイルパスとトークンのURLは同じ文字列になる。** 日本語など、パーサーが百分率符号化する文字で崩れる。
- **画像の行と段落の終わりは一致する。** リスト項目で画像の後に本文が続くと崩れる。
- **補足開始は引用直下の段落だけ調べれば見つかる。** 入れ子の引用・リストで崩れる。
- **補足形式の引用はモデルが追加したものに限られる。** 原文に同形式の引用があると崩れる。
- **強調全体を不可分にしても雑音だけを削れる。** 本文と雑音が同じ強調の内側にあると崩れる。
- **wiki 内に解決されれば削除範囲は適切である。** 未検査のスラッグが親ディレクトリを指すと崩れる。

## 見落としと軽微な問題

- **【軽微】トークンの一致は、文字どおりの保存を保証しない。** 訳さないページで `**hello**` を `__hello__` に変更しても `check` は通る。未使用の参照定義 `[x]: https://evil.example/` の追加も `freeze` と比較処理を通る。`Node.signature` とインライン比較は元の記法全部を保持せず、参照定義は木にも残らない。設計の「書き足さない」「本文は1文字も変えない」と食い違う。根拠：`wiki_rawcheck.py:140`、`147`、`467`。

- **【軽微】二つのファイルの存在だけでは、写しの完成を判定できない。** `fetch.json` を開いた後、部分書き込みで失敗すると、壊れたJSONファイルが残る。`b'{'` を残して書き込み失敗を注入した結果、旧rawは保持されたが、次回取得は **`unchanged: true, work_dir: true`** を返した。`freeze` は `JSONDecodeError` で停止した。前回の軽微な指摘は「ファイルがない」場合だけ解消している。根拠：`wiki_rawcheck.py:68`、`wiki_fetch.py:1366`。

- **【軽微】雑音規則の80文字判定に、強調記号が混入する。** 79文字の本文の後に `Top highlight` がある場合、本文を `<strong>` で囲むだけで、取得後の `**` が文字数に入り、`Top highlight` が残る。本文の文字数は同じでも規則の適用範囲が変わる。根拠：`wiki_fetch.py:374`、`380`。

- **【軽微】試験が確認していない境界が残る。** `test_raw_is_not_written_when_snapshot_fails` は現在も `work_dir()` 自体の失敗であり、途中書き込み失敗を試していない。`test_snapshot_matches_raw_and_records_language` は内容一致を確認するが書き込み順序は確認しない。不完全な写しの回帰試験はJSONファイルを削除するだけで、壊れたJSONを扱わない。画像の試験もASCIIのパスに限られる。根拠：`test_wiki_web_check.py:167`、`185`、`514`。

## 検証した事実

- **一致：** 指定された実装・差分・設計・前回レビュー・原因分類・試験と、`wiki_pages.new_parser()` を確認した。同梱のパーサーを使い、`commonmark`、HTML無効、表有効という設定は説明と一致する。
- **一致：** `ReviewCounterexampleTest`、`CheckTest`、`FreezeTest`、`UntranslatedTest` の計21試験は、ファイル入出力をメモリに置き換えた実行で成功した。パーサーと検査処理は実物を使った。
- **確かめられず：** 指定コマンドによる試験全体の成功。55試験中48試験が、読み取り専用環境で一時ディレクトリを作れずエラーになった。これは実装の失敗とは数えていない。
- **前回レビューとの食い違い：** 重大7の `> First\n> Second` → `> First\nSecond` は今回も通る。ただし、実際のパーサーは両方を同じ引用として描画した。CommonMarkの継続行であり、この反例を構造破壊とは判定できない。
- 上記の追加反例はメモリ上で実行した。ネットワーク取得と実際の再帰削除は行わず、リポジトリのファイルは変更していない。

## 崩せなかった点

- 部分列判定で最も早い対応を選ぶ貪欲法そのものは崩せなかった。前回の重複する短い段落による誤拒否も再現しなかった。
- リスト内のコード変更、コード本文の接頭辞風文字の変更、エスケープした `]` を含むリンクのURL変更は拒否された。
- リストの階層変更と、表の区切り行を壊す変更は拒否された。
- 項目末尾の継続行画像への補足、エスケープした `]` を含むalt、コード内の画像記法の除外は通った。
- ASCIIの画像パスでは、取得済みファイルを `freeze` 後に削除すると `image_file` と補足欠落を検出した。
- `fetch.json` をrawより先に書く順序と、写しの書き込み失敗後にrawを書かない点は確認できた。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
