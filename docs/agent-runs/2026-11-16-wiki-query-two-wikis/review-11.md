## 判定

**却下。確信度：高。** Windows のパス分類に矛盾があり、登録した根の解釈が、再び読み手の作業ディレクトリに依存する。第9回の重大1は、許可するパス表記の一部で閉じていない。

## 致命的・重大な欠陥

### 1. 重大・発生度 C：Windows で根を一意に決めない値を「絶対パス」に含めている

[問い合わせ設計:93](/C:/Works/info-hive-dev/.claude/worktrees/query-two-wikis-0029/docs/plans/wiki-query-two-wikis-2026-11-16.md:93)は、「ドライブ付きのパス」「`/` か `\` で始まるパス」を絶対パスに分類し、登録の基準につながず、そのまま読み手に渡す。

Windows では、`C:wiki` はドライブ相対パス、`\wiki` と `/wiki` は現在のドライブに依存するパスである。どれも完全な絶対パスではない。

反例：

1. Windows で、プロジェクト側のプロセスは C ドライブ、MCP サーバーのデータの場所は D ドライブに置く。
2. 指示に `\kb\user-wiki` を登録する。C、D 両方の該当場所に、別々の初期化済み wiki がある。
3. 93行の分類に従えば、その値を基準につながず渡す。
4. MCP は `D:\kb\user-wiki`、CLI は `C:\kb\user-wiki` を選びうる。それぞれのプロセス内では入力の実体と正規化後の実体が一致するため、その照合では取り違えを検出できない。

現行の **実関数 `normalize_wiki_root()`** を抽出し、ディスクを書かずに、既存の2ディレクトリから同じ値を解いた結果も次のとおりだった。

```text
given = C:wiki

cwd = C:/Works/info-hive-dev
→ C:/Works/info-hive-dev/wiki

cwd = C:/Works/info-hive-dev/.claude/worktrees/query-two-wikis-0029
→ C:/Works/info-hive-dev/.claude/worktrees/query-two-wikis-0029/wiki
```

両方に `SCHEMA.md` が存在した。

一方、[185行](/C:/Works/info-hive-dev/.claude/worktrees/query-two-wikis-0029/docs/plans/wiki-query-two-wikis-2026-11-16.md:185)の「絶対パスでなければ `null`」を `Path.is_absolute()` どおりに実装すれば、この入力は拒否され、93行の許可条件と食い違う。許可しても拒否しても、現在の2つの規定は両立しない。

コードの根拠：

- [wiki_mcp_common.py:78](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_mcp_common.py:78)：`Path(...).expanduser().resolve(strict=True)` で解決する。
- [wiki_mcp_relay.py:82](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_mcp_relay.py:82)：MCP サーバーの作業ディレクトリは `data_dir()`。
- [問い合わせ設計:93](/C:/Works/info-hive-dev/.claude/worktrees/query-two-wikis-0029/docs/plans/wiki-query-two-wikis-2026-11-16.md:93)：相対パスを拒む理由として、このプロセス間の基準の違いを挙げている。

発生度 C は、まれなパス表記に限られるためである。リンクや作為的な共有配置は要らない。

## 崩れる前提

| 暗黙の前提 | 崩れる条件 |
| --- | --- |
| ドライブが付くか、区切り文字で始まれば、Windows でも解決基準が確定する | `C:wiki`、`\wiki`、`/wiki` を使う |
| 入力と正規化後の識別子が一致すれば、登録した根を読んでいる | 両方の解決が同じプロセスの作業ディレクトリに依存する |
| 開いたときの索引の識別子は、外から置換されるまで変わらない | 索引自身が通常の保存でファイルを置換する。次項はこの規定の空白についての指摘 |

## 見落としと軽微な問題

- **軽微・推測：保持済み索引の検査に、正規の保存による識別子変更の扱いがない。** [189行](/C:/Works/info-hive-dev/.claude/worktrees/query-two-wikis-0029/docs/plans/wiki-query-two-wikis-2026-11-16.md:189)は、ベクトル索引を含む「開いたとき」の識別子と現在の識別子を照合する。しかし現行の [`_save_vectors()`](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_index.py:545)は、一時ファイルを保存し、`os.replace()` で `vectors.usearch` を置換する。通常の埋め込み更新でも識別子は変わる。また、[453行](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_index.py:453)はファイルをメモリに読み込み、写像したままにはしない。規定を文字どおり適用すると、正常な保存後の次の呼び出しを `null` にしうる。新読み手は未実装なので誤停止までは確認できていない。実関数をメモリ上の模擬ファイルシステムで動かし、置換による識別子変更は確認した。[249行の試験](/C:/Works/info-hive-dev/.claude/worktrees/query-two-wikis-0029/docs/plans/wiki-query-two-wikis-2026-11-16.md:249)は外部からの置換だけを扱い、この通常更新を覆わない。

- **軽微：パスの試験が重大1を検出しない。** [247行](/C:/Works/info-hive-dev/.claude/worktrees/query-two-wikis-0029/docs/plans/wiki-query-two-wikis-2026-11-16.md:247)は `wiki`、248行は `~/...` を扱うが、Windows のドライブ相対・ルート相対の入力を含まない。

## 検証した事実

| 主張 | 結果 |
| --- | --- |
| 指定コードの版は `955c15a` | 一致。HEAD は `955c15abbe754c79baf57e29978f297bfb7e1924` |
| ホームからの登録を基準につながない | 文書上は一致。第10回の反例を閉じる規定がある |
| raw の範囲検査が内容照合より前にある | 一致。[リンク実装設計:161](/C:/Works/info-hive-dev/.claude/worktrees/query-two-wikis-0029/docs/plans/wiki-links-2026-11-16.md:161)の `(1b)` |
| 非記事のディレクトリリンクにも降りて比較する | 文書上は一致。問い合わせ設計196行 |
| ベクトル索引の通常保存がファイルを置換する | 一致。実コードとメモリ上の模擬実行で確認 |
| 新読み手と ADR-0029 の実装が連携する | 確かめられず。未実装 |

ファイルは変更していない。新読み手による通し試験は行っていない。

## 崩せなかった点

- `State.wiki()`／`WikiIndex` の生成前に分離を確かめる順序。
- 記事・派生データを両側で対称に比較する範囲。
- `shared`、`key_collision`、`null` から CLI へ再試行しない規則。
- raw の内容照合前の範囲制限。
- 記事のリンクを拒み、警告を残して続ける規則と ADR-0029 の整合。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
