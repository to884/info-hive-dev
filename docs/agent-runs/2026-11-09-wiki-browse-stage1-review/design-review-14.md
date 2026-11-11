## 判定

**条件付きで採用可。確信度：高。** `sources:` の解釈がメタ欄と関係表で食い違う反例を、現行関数で再現した。また、停止と起動の競合、子プロセスの再試行、サーバーの安全条件を確かめる試験に抜けがある。

## 致命的・重大な欠陥

### 1. 【重大】同じ `sources:` が、メタ欄では解決済み、関係表では未解決になる

次の入力を置く。オントロジーは存在し、`node_types: {}`、`predicates: {}` とする。

```yaml
# a.md の frontmatter
type: "concept"
sources: [true]
```

```yaml
# true.md の frontmatter
type: "source"
```

設計 §2 は、メタ欄には lint のパーサー、関係表には PyYAML のパーサーを使う。PyYAML 6.0.3 と現行関数をメモリ上で実行した結果は、次のとおりだった。

| 確認箇所 | 実行結果 |
| --- | --- |
| lint の `sources` | `["true"]` |
| lint の `classify_source_ref()` | `ok`。`true.md` に解決 |
| lint の `unresolved_sources` | `[]` |
| lint の `unquoted_strings` | `[]` |
| グラフ用の `sources` | `[True]` |
| `build_edges()` | エッジなし |
| グラフの診断 | `unresolved_source`、`source: "True"` |

設計どおりに表示すると、**メタ欄では `true.md` へのリンクを出し、同じページの診断では出典が未解決だと表示する。** 関係表からも、その出典との関係が消える。

これはグラフ抽出の受け入れ済みの性質を否定する指摘ではない。異なるパーサーから作った辞書を browse が使い、その診断を掲載することで生じる不一致である。`sources: [null]` では、グラフ側で値が捨てられ、診断も出なくなる。

根拠：

- [計画 §2：二つの辞書](/C:/Works/info-hive-dev/docs/plans/wiki-browse-stage1-2026-11-09.md:81)、[§3.6：グラフ用辞書の使用と診断の掲載](/C:/Works/info-hive-dev/docs/plans/wiki-browse-stage1-2026-11-09.md:146)、[§3.8：メタ欄の出典解決](/C:/Works/info-hive-dev/docs/plans/wiki-browse-stage1-2026-11-09.md:176)。
- [lint の文字列パーサー](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_text.py:281)、[グラフの PyYAML パーサー](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:141)、[参照値の文字列化](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:259)、[グラフの出典解決](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:524)。

§11 の出典試験は `paper` 系の文字列を扱い、この型変換による食い違いを検査しない。

## 崩れる前提

| 暗黙の前提 | 崩れる条件 |
| --- | --- |
| 同じ文字列から同じ参照解決関数を呼べば、出典の判定が一致する | 参照解決の前に、lint と PyYAML が値を違う型・字句に変換する |
| `server.lock` を取得できなければ、使い回せるサーバーが存在する | `stop` が、停止済みサーバーの記録を片付けるためにロックを保持している |
| 入力の印が変わらなければ、子プロセスの写しを再利用できる | 一時的な読み取り失敗が解消しても、サイズと更新時刻が変わらない |
| Host・トークン・パスの拒否試験で、手元限定の待ち受けも確かめられる | `0.0.0.0` で待ち受ける実装でも、それらの試験には合格できる |

## 見落としと軽微な問題

### 1. 【軽微】`stop` の後処理中に来た `serve` が、起動できずに終わる

記載された手順から、次の順序が成立する。

1. サーバー S1 が終了する。
2. `stop` が `server.lock` を取得し、`server.json` を削除する。
3. `stop` がロックを解放する前に、新しい `serve` がロック取得を試みて失敗する。
4. `serve` は、記録と `control/status` の一致を待つ。
5. 記録もサーバーも存在せず、10 秒後に「使い回せない」と終了する。

§8.5 の取得失敗側には、待っている間にロックを取得し直す遷移がない。停止と起動が短時間重なるだけで起きる、設計上の反例である。§11 は同時 `serve` と同時 `stop` を扱うが、この組み合わせを扱わない。

根拠：[§8.5 の取得失敗側](/C:/Works/info-hive-dev/docs/plans/wiki-browse-stage1-2026-11-09.md:329)、[§8.6 の記録削除](/C:/Works/info-hive-dev/docs/plans/wiki-browse-stage1-2026-11-09.md:340)、[起動・停止の試験](/C:/Works/info-hive-dev/docs/plans/wiki-browse-stage1-2026-11-09.md:421)。

### 2. 【軽微】`core` の写し再利用には、読み取り失敗からの復帰条件がない

最初の `manifest` 要求でページの読み取りだけを一時的に失敗させ、その後、ファイルのサイズ・更新時刻を変えずに読める状態へ戻す。

§9 は「入力の印が変わらないかぎり写しを使い回す」とするため、同じプロセスへの後続要求でも、ページが欠けた写しを再利用する。サーバーには §8.3 の再試行規則があるが、`core` には適用する記載がない。

第1段階では試験だけが使う入口なので、重大度は軽微とした。製品実装による再現ではなく、記載されたキャッシュ規則からの反例である。

根拠：[§9 の写し再利用](/C:/Works/info-hive-dev/docs/plans/wiki-browse-stage1-2026-11-09.md:353)、[サーバーだけに記載された再試行条件](/C:/Works/info-hive-dev/docs/plans/wiki-browse-stage1-2026-11-09.md:310)。

### 3. 【軽微・試験不足】守ること7の二条件を、指定の試験では確かめられない

- **127.0.0.1 だけでの待ち受け：** `0.0.0.0` に bind し、Host・トークン・パスの検査を正しく実装しても、§11 の列挙された拒否試験は通る。待ち受け先そのもの、または別インターフェースからの接続を検査する項目がない。
- **起動ごとのトークン：** 再起動しても固定トークンを使う実装を落とす明示的な試験がない。インスタンス ID の違いを確かめる試験だけでは、トークンの更新を証明できない。

機構の記述には両条件がある。ここでの指摘は、条件を破った実装を受け入れ試験が検出できないことである。

根拠：[守ること7](/C:/Works/info-hive-dev/docs/plans/wiki-browse-stage1-2026-11-09.md:48)、[§11 の安全試験](/C:/Works/info-hive-dev/docs/plans/wiki-browse-stage1-2026-11-09.md:420)、[選択肢レポート §6.8](/C:/Works/info-hive-dev/docs/research/llm-wiki-browse-options.md:508)。

## 検証した事実

| 確かめた主張 | 結果 |
| --- | --- |
| サブモジュールの HEAD | **一致。** `be117ad` |
| `link_candidates()` の候補0件と lint の未解決判定 | **確認した18入力で一致。** パス、重複スラッグ、大小文字、拡張子、見出し、空の行き先を含む |
| `sources:` の二つのパーサーによる解釈 | **食い違いを実行確認。** 上記重大指摘 |
| `build_nodes()` の三要素の返り値、対応表のキー、診断の `pages` | **設計と一致** |
| 第11〜13回の指摘への対応 | **本文と試験への反映を確認。** 衝突ページ、CR改行、バイトコード、管理用要求、各データの世代確認など |
| ADR-0016 の受け入れ条件 | **記載は一致。** 二方式の実ブラウザ比較、ファイル増減とハッシュ、外部通信、クリック時の `Referer` を含む |
| 製品の競合・復旧・ブラウザ動作 | **確かめられず。** `wiki_browse*` は未実装 |

実行確認は `python -B` とメモリ上の入力で行った。ファイルは変更していない。

## 崩せなかった点

- 同じ本文・同じパーサー設定・同じ正規表現から、描画対象と `extract_wikilinks()` の抽出対象をそろえる方針。
- 最初の書き込み前に外部入力を保護対象へ入れ、実体で重なりを判定し、既存ファイルを直接上書きしない規則。
- 同じ `data_dir` の共通ロックと、正規の退避世代を許す復旧手順に対する、過去の破壊・二重実行の反例。
- 明記された限界を超える、絶対パス検査の利用者内容の例外からの漏洩経路。
- ADR-0016 自体の試験条件と、二方式で合格とする決定。

使用した MCP サーバー: なし  
使用した Agent Skills: research
