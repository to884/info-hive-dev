## 判定

**却下。確信度：高。** 16 版目で追加した絶対パス化の規則が、既存の正本定型文にある `~/info-hive/wiki/` を扱えていない。通常の登録だけで、正しいユーザースコープの wiki を引けなくなる。

## 致命的・重大な欠陥

### 1. 重大・発生度 B：`~/` の登録を、指示ファイルの下の相対パスに変えてしまう

第3.2節は、登録値を指示ファイルのディレクトリに文字のうえでつなぎ、区切りだけをそろえると規定する。ところが、既存のユーザースコープ用定型文は `~/info-hive/wiki/` を使っている。`~` を展開する順序や例外は規定されていない。

反例：

1. `C:/Users/u/.claude/CLAUDE.md` に、正本定型文どおり `~/info-hive/wiki/` を登録する。作業領域の設定による登録はない。
2. 実際のユーザー wiki は `C:/Users/u/info-hive/wiki/` にあり、プロジェクト側も別の場所に初期化済みである。
3. 第3.2節の規則どおりにつなぐと、ユーザー側は `C:/Users/u/.claude/~/info-hive/wiki/` になる。
4. 誤った場所を未初期化として除外するか、読み手が `null` を返す。登録済みの2つの wiki を引けない。

標準ライブラリで、ファイルを作らずに確認した結果：

```text
PureWindowsPath("~/info-hive/wiki").is_absolute()
→ False

指示ファイルのディレクトリにつないだ値
→ C:\Users\u\.claude\~\info-hive\wiki

その後に expanduser() を呼んだ値
→ C:\Users\u\.claude\~\info-hive\wiki
```

既存の `normalize_wiki_root()` は `expanduser()` を呼ぶが、既に親を付けた文字列の途中の `~` は展開されない。これは任意の特殊な登録ではなく、プラグイン自身が提示する定型文との食い違いである。

根拠：

- [問い合わせ設計 第3.2節・93行](/C:/Works/info-hive-dev/.claude/worktrees/query-two-wikis-0029/docs/plans/wiki-query-two-wikis-2026-11-16.md:93)：絶対パス化の規則。
- [正本定型文・51行](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/agent-memory-integration.md:51)：`~/info-hive/wiki/` による登録。
- [normalize_wiki_root()・78行](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_mcp_common.py:78)：NFC 化、`expanduser()`、実体解決の順序。

## 崩れる前提

| 暗黙の前提 | 崩れる条件 |
| --- | --- |
| 絶対パスでない登録値は、指示ファイルからの相対パスである | 正本定型文の `~/info-hive/wiki/` を使う |
| 親ディレクトリを付けても、後段の正規化がホーム表記を処理できる | `~` が文字列の先頭でなくなる |
| 索引ディレクトリの識別子が同じなら、保持済み接続の先も現在の比較集合に入る | ディレクトリを残し、内部の索引ファイルだけを移動・置換する |

## 見落としと軽微な問題

- **軽微：相対パスの試験が正本定型文を覆っていない。** [247行](/C:/Works/info-hive-dev/.claude/worktrees/query-two-wikis-0029/docs/plans/wiki-query-two-wikis-2026-11-16.md:247)は `wiki` の連結と拒否を試すが、`~/info-hive/wiki/` は含まない。重大1は、この試験一覧では検出されない。

- **軽微・推測、既出の未解決：保持済み索引の検査がディレクトリの識別子にとどまる。** [189行](/C:/Works/info-hive-dev/.claude/worktrees/query-two-wikis-0029/docs/plans/wiki-query-two-wikis-2026-11-16.md:189)と[248行の試験](/C:/Works/info-hive-dev/.claude/worktrees/query-two-wikis-0029/docs/plans/wiki-query-two-wikis-2026-11-16.md:248)は、索引ディレクトリ自体の置換だけを扱う。POSIX で保持中の `ledger.sqlite` を他方の索引へ移し、元の名前に別ファイルを置いた場合、親ディレクトリの識別子は変わらない。現在の集合は分離していても、保持済み接続は移動前の実体を参照しうる。現コードの [`Collection.pending()`](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_index.py:634)は、その保持済み接続から本文を読む。実関数を抽出したモックでは旧接続の利用を確認したが、実際のファイル移動と SQLite の動作を含む通し試験はしていない。誤回答まで立証できていないため、重大には数えない。

## 検証した事実

| 確かめた主張 | 結果 |
| --- | --- |
| 指定コードは `955c15a` | 一致。HEAD は `955c15abbe754c79baf57e29978f297bfb7e1924` |
| 正本定型文が `~/` を使う | 一致 |
| 親を付けた後の `expanduser()` が、その途中の `~` を展開する | 食い違い。標準ライブラリで確認 |
| 前回の raw の範囲制限が、内容照合より前になった | 文書上は一致。リンク実装設計161行の `(1b)` に追加済み |
| 非記事のディレクトリリンクの下も比較する | 文書上は一致。問い合わせ設計196行に追加済み |
| 新しい読み手と ADR-0029 が実際に連携する | 確かめられず。未実装 |

ファイルは変更していない。識別子集合の確認と関数のモック実行は行ったが、新読み手による実機試験は行っていない。

## 崩せなかった点

- 前回の重大3件について、元の反例を閉じる規定は追加されている。
- `State.wiki()`／`WikiIndex` の生成より前に分離を確かめる順序。
- `shared`、`key_collision`、`null` から CLI で再試行しない規則。
- 記事のリンクを拒み、警告を残して続ける扱いと ADR-0029 の整合。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
