## 結論

**wiki 0.35.1 には、プロジェクトスコープとユーザースコープのそれぞれで、グラフのオントロジーを定義し、検査・反映する機能があります。各 wiki の記事からオントロジーを提案し、利用者が選んだ差分を適用する専用機能は、現行のコマンドと実装には見当たりません。** 現在も、対象 wiki と答えたい問いをエージェントに伝え、出典付きの差分案を作らせ、確認後に `graph lint` と `graph extract` を使う運用はできます。

機能としては、既存の `graph` に **`propose` と `apply` を追加**する案を推します。利用者は YAML の書き方を覚える必要はなく、「この wiki でどんな関係をたどりたいか」を伝え、実例を見て採用する項目を選びます。初版は語彙の追加を中心とし、過去の記事に型付きの関係を追記する場合は、その記事と根拠も確認できるようにします。

## 根拠

### 現行機能

- `/wiki:init` と `/wiki:init --user` は異なる保存先を選び、どちらも同じひな形を各 wiki の `graph/ontology.yaml` に置きます。既存のファイルは保持されます。`SCHEMA.md` はページの種類、タグ、運用の規約を持ち、`ontology.yaml` はグラフのノード型、述語、主語・目的語の型、根拠の要否を定めます。現行の `graph` 操作は抽出、検査、照会です。`evolve` が改善する対象はスキルです。 [初期化手順 11–18行](https://github.com/to884/info-hive-wiki/blob/main/commands/init.md#L11-L18) · [ひな形のコピー 255–277行](https://github.com/to884/info-hive-wiki/blob/main/skills/info-hive/scripts/init_wiki.py#L255-L277) · [グラフの操作 3–22行](https://github.com/to884/info-hive-wiki/blob/main/commands/graph.md#L3-L22) · [コマンド一覧 158–174行](https://github.com/to884/info-hive-wiki/blob/main/docs/commands.md#L158-L174)
- 開発プロジェクトの `wiki/graph/ontology.yaml` と配布ひな形は、改行を LF にそろえて比較すると **差分 0 行／123 行**でした。コミット済みの `edges.jsonl` は **421 `mentions` ＋ 115 `sourced_from` ＋ 75 `summarizes_raw` ＋ 10 `cites` ＝ 621 本**で、明示的な型付き関係は `cites` の10本です。これは保存済みの生成物の集計です。開発 wiki にどんな語彙が役立つかは、実際にたどりたい問いと記事から判断する余地があります。 [開発 wiki の定義 1–123行](https://github.com/to884/info-hive-dev/blob/main/wiki/graph/ontology.yaml#L1-L123) · [配布ひな形 1–123行](https://github.com/to884/info-hive-wiki/blob/main/skills/info-hive/assets/ontology.yaml.template#L1-L123) · [関係の生成物 1–621行](https://github.com/to884/info-hive-dev/blob/main/wiki/graph/edges.jsonl#L1-L621)
- 述語を登録すると、その述語を使った関係を検査できます。型付きの関係を検索できるようにするには、記事の `graph.relationships[]` に出典と根拠を記録し、グラフを再生成します。通常の wikilink から生成されるのは `mentions` です。新しい語彙を今後の取り込みで使うか、過去の記事にも根拠付きで追記するかは、利用者が選べます。 [グラフの関係と語彙 19–25・78–101行](https://github.com/to884/info-hive-wiki/blob/main/skills/info-hive/references/graph-workflow.md#L19-L25) · [取り込み時の更新 434–440行](https://github.com/to884/info-hive-wiki/blob/main/skills/info-hive/references/ingest-workflow.md#L434-L440)

### 提供方法と使い方

1. **対象と問いを指定する。** 提案する入口は Claude Code の `/wiki:graph propose` と Codex の `$wiki:info-hive graph propose` です。自然言語なら「このプロジェクトの wiki で、どの変更が以前の検証規則を広げたか、たどれるようにしたい」で始められます。ユーザースコープでも同じ操作を使い、処理前に対象のスコープと絶対パスを表示します。提案・適用は一つの wiki を単位にします。 [Codex の共通操作 5–26行](https://github.com/to884/info-hive-wiki/blob/main/skills/info-hive/references/codex.md#L5-L26)
2. **実例を見て選ぶ。** 対象の `SCHEMA.md`、索引、現行の語彙、関連ページを読み、既存の述語で表せるかを先に確かめます。追加候補には日本語での意味、英語の識別子、主語と目的語の型、出典付きの例、影響するページを示します。開発 wiki では、[[rawのリンクの検証とリリース-wiki-0.34.0]] が、0.31.0 の記事リンクの検証規則を原本にも広げたと記録しています。この種の問いが繰り返し出るなら、`extends_rule_from` を試す材料になります。ユーザースコープで論文と手法をたどりたい場合は、たとえば `evaluates` を候補にできます。こちらは利用例の仮定です。既存語で足りる場合や根拠が少ない場合は、追加候補がゼロでも構いません。 [開発 wiki の索引](https://github.com/to884/info-hive-dev/blob/main/wiki/index.md) · [0.34.0 の記事 14–22行](https://github.com/to884/info-hive-dev/blob/main/wiki/sources/rawのリンクの検証とリリース-wiki-0.34.0.md#L14-L22)
3. **差分を適用し、同じ問いで確かめる。** `graph apply <提案ID>` は、対象 wiki とプレビュー時点のファイルが一致することを確認し、承認された差分だけを反映します。候補 YAML は `lint --ontology … --json` と `extract --ontology … --out …` で事前に試せます。検査は終了コードだけで判定せず、新たな指摘とノード ID・参照の差分を確認します。`maps_from` の追加でも既定 ID が変わる場合があり、抽出は型の誤りがある関係も格納するためです。再生成後に、代表的な問いから出典ページまでたどれた時点で完了とします。複数ファイルの変更が途中で止まった場合に備え、変更前の状態に戻せるようにします。 [lint の引数と結果 518–556行](https://github.com/to884/info-hive-wiki/blob/main/skills/info-hive/scripts/wiki_graph_lint.py#L518-L556) · [ノード型・IDの決定 502–555行](https://github.com/to884/info-hive-wiki/blob/main/skills/info-hive/scripts/wiki_graph_extract.py#L502-L555) · [抽出先の指定 1134–1173行](https://github.com/to884/info-hive-wiki/blob/main/skills/info-hive/scripts/wiki_graph_extract.py#L1134-L1173) · [抽出と中断時の挙動 121–143行](https://github.com/to884/info-hive-wiki/blob/main/skills/info-hive/references/graph-workflow.md#L121-L143)

## 検討した代替案

| 案 | 採らなかった理由 |
| --- | --- |
| 初期化や取り込みのたびに語彙を自動追加する | 初期化時は実例が乏しく、取り込みごとの追加では似た述語が増えやすい。繰り返し答えたい問いが生じた時点で、複数の実例を見て選ぶほうが判断しやすい。 |
| プロジェクト用とユーザー用の専用ひな形を配る | スコープが示すのは保存先と利用範囲です。同じスコープにも開発記録、研究資料、業務メモなどがあり、必要な関係は用途によって変わります。 |
| `/wiki:evolve` に統合する | `evolve` の適用対象はインストールされたスキルです。今回の変更対象は、指定した wiki の語彙と記事です。既存の検査・抽出と同じ `graph` から呼べば、利用者が対象を把握しやすくなります。 |

## 前提と不確実性

- 「最適」は、**利用者が繰り返し尋ねる関係を、少数の語彙で出典までたどれること**と仮定しました。候補の有用性は、同じ問いを適用前後に試して判断する設計案です。改善効果は未測定です。
- 調査対象は GitHub 上の既定ブランチです。ローカルの未コミット変更、ユーザースコープの実データ、実機での適用と復旧は未確認です。
- `multi-agent-dispatch` のスキルが定める独立検討の手順を使いました。ローカルのプロセス起動が拒否されて `dispatch.py check` を実行できず、通常の `init` と `run` はリポジトリへの記録書き込みを伴います。このため、同じ問いを **GPT-6.2 Sol と GPT-6.2 Astra** に、このセッションのサブエージェント機能で互いの回答を見せずに依頼しました。両者とも専用機能は見当たらないと判断し、既存の `graph` を入口にした提案・適用を支持しました。Sol の検査結果の読み方と、Astra のノード ID の差分確認および記事の実例を採用しました。Claude を含む4モデルでの比較は未実施です。 [multi-agent-dispatch の手順 6–64行](https://github.com/to884/dev-agent-skills/blob/main/.agents/skills/multi-agent-dispatch/SKILL.md#L6-L64)

## 参照

- **開発リポジトリ**。wiki の索引、規約、保存済みのグラフ定義と関係、リリース間の関係を記した記事を参照しました。 [wiki/index.md](https://github.com/to884/info-hive-dev/blob/main/wiki/index.md) · [wiki/SCHEMA.md 130–186行](https://github.com/to884/info-hive-dev/blob/main/wiki/SCHEMA.md#L130-L186) · [wiki/graph/ontology.yaml](https://github.com/to884/info-hive-dev/blob/main/wiki/graph/ontology.yaml) · [wiki/graph/edges.jsonl](https://github.com/to884/info-hive-dev/blob/main/wiki/graph/edges.jsonl) · [0.31.0 の記事 19–25行](https://github.com/to884/info-hive-dev/blob/main/wiki/sources/wikiの記事リンクの拒否とリリース-wiki-0.31.0.md#L19-L25)
- **プラグイン**。版、コマンド一覧、グラフと MCP の仕様、本文に示した初期化・検査・抽出の実装を照合しました。 [CHANGELOG.md 7–13行](https://github.com/to884/info-hive-wiki/blob/main/CHANGELOG.md#L7-L13) · [docs/commands.md 5–22行](https://github.com/to884/info-hive-wiki/blob/main/docs/commands.md#L5-L22) · [graph-workflow.md 166–176行](https://github.com/to884/info-hive-wiki/blob/main/skills/info-hive/references/graph-workflow.md#L166-L176) · [mcp-server.md 31–45行](https://github.com/to884/info-hive-wiki/blob/main/skills/info-hive/references/mcp-server.md#L31-L45)

使用した MCP サーバー: GitHub  
使用した Agent Skills: multi-agent-dispatch
