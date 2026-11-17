## 判定

**条件付きで採用可。確信度：高。** 既存のジャンクション経由でサイドカーが通常ページに混ざる反例と、経路検査より先に要求ファイルを書いてしまう欠陥が残る。3 回目の重大な指摘への対処は、設計上は確認できた。

新機能は未実装である。以下では、既存コードを実行して確認した結果と、設計の手順から導いた反例を区別する。

## 致命的・重大な欠陥

### 1. 重大・D：除外ディレクトリを指すジャンクション経由で、概要が通常ページになる

「`assets/` と `.wiki-cache/` を名前で除けば、概要や下書きがページ集合に入らない」という前提は成立しない。既存の走査は、**別名のジャンクションをたどる**。

反例となる配置：

```text
wiki/
  concepts/foo.md
  assets/
  mirror/                 ← assets/ を指すジャンクション
```

1. この状態で通常ページは `concepts/foo.md` だけである。
2. 概要を作り、`assets/overview/ad3d747063f9b50e.overview.md` を置く。
3. 次の走査では、同じファイルが `mirror/overview/ad3d747063f9b50e.overview.md` として現れる。
4. `mirror` は除外名ではないため、通常ページとして採用される。

書き込み先の `assets/` と `assets/overview/` 自体は普通のディレクトリなので、7.4 節の経路検査を通る。検査後の差し替えも、同時書き込みも不要である。`.wiki-cache/` を指す別名のジャンクションでも、ページの写しや下書きが同様に漏れる。

**検証結果：食い違い。** 既存の `walk_pages()` に、上記配置に相当する一覧・識別子を模擬して渡したところ、作成後だけ `mirror/overview/…overview.md` が `files` に加わった。`unlistable` と `unknown` はどちらも空だった。実際のジャンクションを作る実験は行っていない。

検索とグラフの収集処理も同じ走査を使うため、「既存の読み手の結果を変えない」という保証を破る。

**根拠：**

- [設計書:91](C:/Works/info-hive-dev/.claude/worktrees/wiki-overview/docs/plans/wiki-overview-2026-11-17.md:91)：ページとして数える者はいないという保証。
- [設計書:243](C:/Works/info-hive-dev/.claude/worktrees/wiki-overview/docs/plans/wiki-overview-2026-11-17.md:243)：検査するのは書き込み経路。
- [wiki_pages.py:229](C:/Works/info-hive-dev/.claude/worktrees/wiki-overview/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:229)：ジャンクションには降り、除外は起点直下の名前で行う。
- [wiki_search.py:270](C:/Works/info-hive-dev/.claude/worktrees/wiki-overview/info-hive-wiki/skills/info-hive/scripts/wiki_search.py:270)、[wiki_graph_extract.py:379](C:/Works/info-hive-dev/.claude/worktrees/wiki-overview/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:379)：共通走査を使用。

### 2. 重大・D：要求ファイルへの最初の書き込みが、経路検査より先に行われる

7.1 節は `.wiki-cache/overview/` を使う前の経路検査を要求する。しかし、9.1 節のコマンドの流れは、**モデルの Write → `prepare`** である。最初の Write を守る検査の呼び出しがない。

反例：

```text
wiki/.wiki-cache/          ← C:/shared/ を指す既存のジャンクション
C:/shared/overview/request.json
```

1. `/wiki:overview foo` を実行する。
2. モデルは指定された手順に従い、`wiki/.wiki-cache/overview/request.json` を Write する。
3. そのパスは `C:/shared/overview/request.json` に到達し、wiki 外のファイルを作成・上書きする。
4. 続く `prepare` が `unsafe_path` を返しても、書き込みはすでに終わっている。

これは検査後の差し替えではなく、**開始時から存在するリンク**である。12 節の競合に関する保証除外には当たらない。

**検証結果：手順の食い違い。** モデルの Write 自体は実行していない。親ディレクトリのジャンクションを経由する通常のファイル書き込みを前提とした、設計手順の静的な反例である。

**根拠：**

- [設計書:200](C:/Works/info-hive-dev/.claude/worktrees/wiki-overview/docs/plans/wiki-overview-2026-11-17.md:200)：使う前に経路を検査する契約。
- [設計書:315](C:/Works/info-hive-dev/.claude/worktrees/wiki-overview/docs/plans/wiki-overview-2026-11-17.md:315)：モデルが要求ファイルを書く手順。
- [設計書:330](C:/Works/info-hive-dev/.claude/worktrees/wiki-overview/docs/plans/wiki-overview-2026-11-17.md:330)：Write の後に `prepare` を呼ぶ順序。
- [ADR-0031:27](C:/Works/info-hive-dev/.claude/worktrees/wiki-overview/docs/adr/0031-wiki-page-overview-lives-in-a-sidecar.md:27)：同じ要求ファイル方式を採用。

## 崩れる前提

- **除外名の下に置けば、どの経路からもページにならない。** 別名のジャンクションから到達すると崩れる。走査の除外は実体ではなく名前に対して働く。
- **スクリプトが経路を検査すれば、作業領域への書き込みを守れる。** スクリプト起動前にモデルが要求ファイルを書く手順で崩れる。
- **wiki を Git で運べば、概要の管理状態も運べる。** サイドカーと図は運べるが、所有記録は `.gitignore` により運べない。
- **削除後に所有記録から引けば、所有情報を失わない。** 削除の永続化より記録更新の永続化が先になる手順では、電源断後に崩れる。

## 見落としと軽微な問題

### Git clone でも、使用中の図の所有情報を失う

12 節は利用者による `owned/` の削除を保証外としているが、通常の Git clone でも同じ状態になる。

別 PC で clone して `remove` を実行すると、サイドカーは消えるが、図は所有記録にないため残る。`refresh` でも旧世代の図が残り、lint は知らせない。「片付けが残った図」だけでなく、**移動時点で使用中だった全図**が対象になる。

保証除外そのものへの異議ではなく、通常の移動でも発生することが説明から抜けているという指摘である。

**根拠：** 設計書 250・281・411 行、ADR-0031 の 23・50・60 行。既存の `wiki-cache_gitignore.template` は `*` と `!.gitignore` である。

### POSIX の片付け順に、同期の記述の矛盾がある

7.4 節の表では、旧図を削除して所有記録から引き、`assets/` は片付けの最後に同期する。一方、直後の説明は、名前を変更した直後にディレクトリを同期してから次へ進むとしている。

表に従う場合：

1. 旧図 A を削除する。
2. 所有記録から A を引き、記録を同期する。
3. `assets/` の同期前に電源が切れる。
4. A の削除だけが失われると、A が所有記録なしで残る。

参照切れにはならないが、12 節に記載された「公開後、記録前の停止」とは別の、回収不能な図を生む停止位置である。電源断の実験はしていない。

**根拠：** 設計書 254・256・268・273 行。

### 出力契約に小さな欠落がある

- `status` が `<P>` を返すとする一方、示された項目は `page`、`sidecar`、`state`、`detail` だけで、`orphan_id` の置き場所がない。lint には明記されている。
- 6.5 節は lint の code `page_unknown` を要求するが、10 節の code 一覧にはない。
- `classify(..., sidecar: bytes | None, ...)` に対し、読めない場合は「理由を表す値」を渡すとする。その値の型・形が定義されていない。

**根拠：** 設計書 163〜180・277〜279・359〜370 行。

## 検証した事実

| 主張 | 結果 |
| --- | --- |
| 基準版は wiki 0.25.2、新機能は未実装 | **一致。** `plugin.json` とスクリプトの有無を確認 |
| 正規の配置ではサイドカーと下書きがページ集合から外れる | **一致。** `is_page_path()` を実行して確認 |
| 別名のジャンクション経由でも外れる | **食い違い。** 既存走査への模擬入力で通常ページになることを確認 |
| `Assets/` の綴りは安全でない | **一致。** その下の `.md` は通常ページになる |
| frontmatter の `format: 1` と `figures: []` を既存関数で往復できる | **一致。** `format` は文字列 `"1"`、`figures` は空配列になる |
| NFC で同じ識別子は同じ P、大文字小文字が異なれば別の P | **一致。** 設計の式を実行して確認 |
| コードスパン・コードブロック内の画像記法と、本文の画像を区別できる | **一致。** 同梱パーサーで確認 |
| BOM・CRLF・単独 CR を既存 browse の読み方で正規化できる | **一致。** `read_text_like_lint()` を実行して確認 |
| MCP の lint は共通の `wiki_lint.lint()` を呼ぶ | **一致。** `wiki_mcp_server.py:387` を確認 |
| ADR-0030 の実物との接続 | **確かめられず。** 指定された別 worktree の設計書が存在しなかった |

ファイルは変更していない。新しい書き込み処理、モデルの Write、実機の電源断は未検証である。

## 崩せなかった点

- 作成成功後だけ所有記録へ加える規則では、3 回目の「作成に失敗した既存図を次回削除する」反例は成立しない。
- 所有記録を足し引きで維持する規則では、サイドカー置き換えによって旧世代の名前が失われる反例は成立しない。
- 記録済みで同じバイト列の図を再利用する規則では、前回指摘した自分の図との衝突は成立しない。
- `remove` のサイドカー削除後の同期により、前回の POSIX の参照切れ反例は成立しない。
- `page_unknown` と `walk_incomplete` により、不完全な走査だけを根拠に `orphan` として削除する反例は成立しない。
- 単独の書き手によるプロセス停止では、図の公開 → サイドカーの公開 → 旧図の削除という参照順は崩せなかった。
- ページ名を要求ファイルで渡す規則では、ページ名によるシェル注入は崩せなかった。
- 開発 PC 固有のスキル名や絶対パスを必須にする規則は見つからなかった。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
