## 判定

**却下。確信度：高。** 相対パスの登録から正しい根を選べない欠落、raw の許可範囲を確かめる前に中身を読む矛盾、非記事のディレクトリリンクを経由する共有の見逃しが残る。

## 致命的・重大な欠陥

### 1. 重大・発生度 B：登録の相対パスを解釈する基準が、読み手に渡らない

第3.2節は `dirs.wiki` を登録として使い、その綴りをそのまま読み手に渡す。しかし、作業領域の `dirs.wiki` は**相対パスだけ**を受け付ける。読み手の引数には、登録元の作業領域や基準ディレクトリがない。

反例は、指示による登録がなく、次の2つの設定だけがある通常の配置で成立する。

```text
C:/user-space/.info-hive/workspace.json     dirs.wiki = "wiki"
C:/project-space/.info-hive/workspace.json  dirs.wiki = "wiki"
```

本来の根は別々だが、仕様どおり綴りを渡すと `user="wiki", project="wiki"` になる。MCP サーバーの作業ディレクトリはデータの場所なので、両方とも `<data_dir>/wiki` に解決される。そこになければ `null`、初期化済みなら `same` となり、登録した2つの wiki を引けない。CLI でも、両方を呼び出し時の作業ディレクトリから解釈してしまう。

根拠：

- [問い合わせ設計:86](/C:/Works/info-hive-dev/.claude/worktrees/query-two-wikis-0029/docs/plans/wiki-query-two-wikis-2026-11-16.md:86)：設定から登録を読む規則。93行で綴りをそのまま渡し、177行の引数には相対パスの基準がない。
- [wiki_workspace.py:99](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_workspace.py:99)：絶対パスを拒否する。207〜220行では作業領域の根を前置している。
- [wiki_mcp_relay.py:78](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_mcp_relay.py:78)：サーバーの `cwd` は `common.data_dir()`。
- [wiki_mcp_common.py:76](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_mcp_common.py:76)：正規化は `Path.resolve()` を使う。

### 2. 重大・発生度 A：raw の範囲制限より先に、`resolve_raw()` が範囲外の中身を読む

第3.4節は、`resolve_raw()` で解いた先が許可した根の下にある場合だけ返し、それ以外は「読まず」に理由を返す。しかし、前提となる `resolve_raw()` は、結果を返す前に候補の中身を読んで、ハッシュや身元を照合する。

反例：

1. source ページに、許可した根の外の通常ファイルを指す絶対パスの `raw:` と、正しい `raw_sha256:` がある。rag の外の原本でも成立する。
2. 読み手の `raw` を呼ぶ。
3. `resolve_raw()` が候補の中身を読み、SHA-256 を計算する。
4. 戻ったパスを第3.4節で拒否しても、禁止した読み取りは既に終わっている。

今回の反例はリンクでない候補で成立する。過去に直した「リンク判定をハッシュ照合より先にする」規則では、この範囲制限は満たせない。本文が利用者に返るとは主張していないが、「根の外の任意のパスを、サーバーが読む口にしない」という目的とは食い違う。

根拠：

- [問い合わせ設計:119](/C:/Works/info-hive-dev/.claude/worktrees/query-two-wikis-0029/docs/plans/wiki-query-two-wikis-2026-11-16.md:119)：`resolve_raw()` の解決後に範囲を制限し、範囲外は読まない。
- [リンク実装設計:161](/C:/Works/info-hive-dev/.claude/worktrees/query-two-wikis-0029/docs/plans/wiki-links-2026-11-16.md:161)：解決処理の段階4で中身を読む。162行はハッシュと frontmatter による照合を要求する。

これは文書間の順序から導ける矛盾であり、未実装の読み手による実機再現はしていない。

### 3. 重大・発生度 D：非記事のディレクトリリンクに降りないため、実際に開く子ファイルの共有を見逃す

第3.9節は、記事でない場所のディレクトリリンクについて、先のディレクトリの識別子だけを取り、その下には降りない。しかし、グラフの読み取りはその下のファイルを開く。

根が独立した U、P と、その両方の外の X を用意する。

```text
U/graph                    → X/                 （ディレクトリリンク）
P/graph/graph.sqlite        → X/graph.sqlite     （ファイルリンク）
```

両側に有効なオントロジーを置き、その他の比較対象は独立させる。

- U の比較集合には X のディレクトリ識別子が入るが、`X/graph.sqlite` の識別子は入らない。
- P の比較集合には `X/graph.sqlite` の識別子が入るが、X のディレクトリ識別子は入らない。
- 集合は重ならず、`disjoint` になる。
- 両スコープの `graph` 操作は、同じ `X/graph.sqlite` を開く。

配置変更や競合は不要である。`graph/` は記事でないため、ADR-0029 の記事拒否でも止まらない。8回目の重大2で求めた子ファイルの共有検出が、ディレクトリリンクを経由する場所には反映されていない。

根拠：

- [問い合わせ設計:195](/C:/Works/info-hive-dev/.claude/worktrees/query-two-wikis-0029/docs/plans/wiki-query-two-wikis-2026-11-16.md:195)：リンク先の識別子を取り、ディレクトリリンクには降りない。
- [ADR-0029:52](/C:/Works/info-hive-dev/.claude/worktrees/query-two-wikis-0029/docs/adr/0029-wiki-and-raw-hold-no-links.md:52)：リンク拒否の対象は記事と記事までの道。
- [wiki_graph_query.py:55](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_query.py:55)：DB パスを解決して開く。244行では `wiki/graph/graph.sqlite` を渡す。

識別子集合と既存の読み取り経路からの導出であり、新読み手での実機再現はしていない。

## 崩れる前提

| 暗黙の前提 | 崩れる条件 |
| --- | --- |
| 登録の文字列だけで根を特定できる | 別々の作業領域が同じ相対値 `wiki` を登録する |
| `resolve_raw()` は、許可範囲を判定するまで中身を読まない | ハッシュや身元を照合する候補が範囲外にある |
| リンク先ディレクトリの識別子だけで、その下の読み取りも分離できる | 子ファイルだけが他方の比較集合に現れる |

## 見落としと軽微な問題

- **軽微：ハードリンクの試験期待値が、記事の拒否規則と矛盾する。** [234行](/C:/Works/info-hive-dev/.claude/worktrees/query-two-wikis-0029/docs/plans/wiki-query-two-wikis-2026-11-16.md:234)は、U の記事と P の `parse-cache.json` をハードリンクにすると `shared` を期待する。しかし、U の記事は `st_nlink >= 2` で拒まれ、194行により比較集合から除かれる。ほかに共有がなければ `disjoint` になる。237行の「記事のハードリンクで止めない」とも食い違う。

- **軽微：全操作の読み取りを比較集合に含める試験が、raw の正常系と両立しない。** [243行](/C:/Works/info-hive-dev/.claude/worktrees/query-two-wikis-0029/docs/plans/wiki-query-two-wikis-2026-11-16.md:243)は、8操作で開いたパスがすべて比較集合にあることを要求する。一方、273行は raw の根を集合に入れないと明記する。記録済みの外部 raw を正常に読むだけで、この試験条件から外れる。

- **軽微・推測、既出未解決：保持済み索引と現在の実体を結び付ける条件がない。** 見直しの [D のレビュー:163](/C:/Works/info-hive-dev/.claude/worktrees/query-two-wikis-0029/docs/agent-runs/2026-11-16-wiki-query-two-wikis-rethink/reviews/D.md:163)で残った論点である。現コードは `WikiIndex` と SQLite 接続を保持するが、15版は現在のパスを検査してから `State.wiki()` を呼ぶところまでしか定めていない。呼び出し前に索引の実体が移動した場合の再利用条件は未記載である。誤った回答への到達は確かめられていないため、重大には数えない。

## 検証した事実

| 確かめた主張 | 結果 |
| --- | --- |
| 読んだコードは指定された `955c15a` | 一致。HEAD は `955c15abbe754c79baf57e29978f297bfb7e1924` |
| 作業領域の `dirs.wiki` は相対値で、作業領域の根を前置して使う | 一致。実関数でも確認 |
| 同じ `normalize_wiki_root("wiki")` が作業ディレクトリによって別の根になる | 一致。主チェックアウトと本 worktree で実行して確認 |
| `resolve_raw()` は解決結果を返す前に候補の中身を読む | 文書で一致。実装はまだなく、実動作は確かめられず |
| 保持済み索引の接続先も毎回照合される | 確かめられず。15版に処理と試験の記載がない |

ファイルは変更していない。

## 崩せなかった点

- `State.wiki()`／`WikiIndex` の生成より前に分離を検査する順序そのもの。
- NFC 化で入力と異なる実体へ移る場合を `null` にする規則。
- `shared`、`key_collision`、`null` の結果から CLI で再試行しない規則。

使用した MCP サーバー: なし  
使用した Agent Skills: research
