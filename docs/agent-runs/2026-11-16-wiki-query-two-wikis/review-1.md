## 判定

**却下。確信度：高。** 問い合わせ中の書き込みと、二つの根の間でページが混ざらないという前提が、既存の手順・実装と食い違う。また、登録済みの二つの wiki を発見できない配置と、既存の定型文が問い合わせごとの opt-in に反する配置が残っている。

## 致命的・重大な欠陥

1. **重大：シンセシスを保存しなくても、問い合わせの途中でグラフを書き換える。**

   **反例：** 両方の wiki にオントロジーと `graph.sqlite` があり、片方の DB が最新の取り込みより古い状態で、`/wiki:query --both X と関係するものは？` を実行する。

   既存の `query-workflow.md` はグラフの鮮度確認を `graph-workflow.md` に委ね、その手順は「古ければ先に extract で作り直す」と要求する。したがって、回答の保存を断っても、問い合わせの途中で `graph.sqlite`、`nodes.jsonl`、`edges.jsonl`、`graph.graphml` を書く。JSONL は既定の `.gitignore` でも無視されない。

   **根拠・結果：食い違い。** 設計第3.7節の「wiki のページ、索引、ログは書かない」は、グラフ索引に対して成立しない。第4節の変更対象にも `graph-workflow.md` はない。
   
   根拠：[設計書 第3.7節](/C:/Works/info-hive-dev/docs/plans/wiki-query-two-wikis-2026-11-16.md:103)、[問い合わせからの委譲](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/query-workflow.md:41)、[問い合わせ時の再抽出](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/graph-workflow.md:158)、[成果物の書き込み](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:881)、[Git での扱い](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/graph-workflow.md:170)。

2. **重大：二つの根が親子関係にあると、検索段階ですでにページ集合が混ざる。**

   **反例：** ユーザー wiki を `C:/kb`、プロジェクト wiki を `C:/kb/projects/p/wiki` として登録し、両方に `SCHEMA.md` を置く。内側に `concepts/secret.md` があると、外側の検索もこのページを収集する。

   第3.2節は根の「同一」だけを除き、包含関係を扱わない。既存の走査は、途中に別の `SCHEMA.md` があっても止まらない。除外名も最上位にしか効かないため、内側の `SCHEMA.md` や `raw/private.md` まで外側の通常ページになる。結果として、同じ内容が二つの検索に現れ、プロジェクトのページを「ユーザースコープ」の出典として扱える。

   外側だけの出典を付ければ、第3.6節でも単一 wiki の回答として保存可能になる。これは、出典にしなかったページの混入ではなく、**出典自体の所属が誤る経路**である。

   **根拠・結果：実装で確認。** 入出力を伴わない確認で、`is_page_path()` は `projects/p/wiki/concepts/secret.md`、`projects/p/wiki/SCHEMA.md`、`projects/p/wiki/raw/private.md` のすべてに `True` を返した。

   根拠：[根の比較](/C:/Works/info-hive-dev/docs/plans/wiki-query-two-wikis-2026-11-16.md:66)、[ページの判定](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:49)、[最上位だけの除外と再帰走査](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:251)、[検索のページ収集](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_search.py:264)。

3. **重大：反対のスコープを設定で登録していても、発見する手順がない。**

   **反例：** グローバルな指示にユーザー wiki を登録し、プロジェクト wiki はそのプロジェクトの `.info-hive/workspace.json` にだけ登録する。プロジェクトの指示には wiki の指定を書かない。この状態で `/wiki:query --both` を実行する。

   今の手順0では、作業領域の設定より先にグローバルな指示が採用され、主はユーザー wiki になる。一方、引用している browse の規則は、指示で根が決まった場合に設定を追加で読むことを禁じる。第3.2節も読むファイルを今の手順0と同じに制限する。したがって、登録済みのプロジェクト wiki を発見できない。

   第7節の「二つの設定が見つかる配置」も、既存の `find_workspace()` は最初に見つけた設定で戻るため、その関数を一度呼ぶだけでは成立しない。メモリ上で親を `user`、子を `project` とした確認でも、読まれたのは子の設定一つだけだった。

   **根拠・結果：手順間の食い違い。** 設定を読めば browse と同じ読み取り範囲ではなく、読まなければ登録済みの対を扱えない。「登録の読み違い」という免責では説明できない。

   根拠：[設計の根の決定](/C:/Works/info-hive-dev/docs/plans/wiki-query-two-wikis-2026-11-16.md:60)、[読み取り範囲の制限](/C:/Works/info-hive-dev/docs/plans/wiki-query-two-wikis-2026-11-16.md:70)、[browse の制限](/C:/Works/info-hive-dev/docs/plans/wiki-browse-scope-2026-11-12.md:25)、[最初の設定で戻る実装](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_workspace.py:176)。

4. **重大：既存の正本定型文は、問い合わせごとの opt-in と両立しない。**

   **反例：** `agent-memory-integration.md` が提示するユーザースコープ用定型文と、プロジェクト用定型文を両方導入する。その状態で、`--both` を付けずにプロジェクトの知識について問い合わせる。

   ユーザー用定型文は、蓄積した知識から答える前にユーザー wiki の索引を読むよう無条件に指示する。プロジェクト用定型文も、そのプロジェクトの索引を読むよう要求する。両方を正しく実行すれば、問い合わせごとの要求がなくても二つの wiki の中身が会話に入る。

   第4節で変えるのは同文書の「黙って混ぜない」という説明であり、この二つの定型文ではない。すでに利用者の指示ファイルへ書かれた定型文についても扱いがない。

   **根拠・結果：既存の指示との食い違い。** エージェントの誤読を仮定せず、第3.1節が崩れる。コマンド手順だけで、利用者の既存の指示に対する優先関係は確定できない。

   根拠：[問い合わせごとの要求](/C:/Works/info-hive-dev/docs/plans/wiki-query-two-wikis-2026-11-16.md:49)、[変更対象](/C:/Works/info-hive-dev/docs/plans/wiki-query-two-wikis-2026-11-16.md:132)、[プロジェクト用定型文](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/agent-memory-integration.md:31)、[ユーザー用定型文](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/agent-memory-integration.md:51)。

## 崩れる前提

| 暗黙の前提 | 崩れる条件 |
| --- | --- |
| 根を別々に渡せば、ページ集合も分かれる | 一方の根が他方を包含する |
| 今の手順0が読む情報で、反対のスコープも探せる | 指示で主が決まり、反対側が作業領域の設定にだけある |
| 問い合わせ中の書き込みは、保存か検索キャッシュに限られる | グラフの鮮度確認が extract を要求する |
| 通常の問い合わせでは、既存の指示も一つの wiki だけを読ませる | ユーザー用・プロジェクト用の定型文が両方存在する |

## 見落としと軽微な問題

- **軽微：スキーマと保存禁止の優先関係が未定義。** 既存の手順は「スキーマは既定の動作より優先」としている。たとえば正規のカスタマイズとして「回答は必ず保存する」と書かれた wiki で、今回の禁止とどちらが優先するかは決まっていない。実在する該当設定は確認しておらず、これは仮定による反例である。根拠：[query-workflow.md](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/query-workflow.md:9)。

- **軽微：`--decide` による外部送信が第5・6節にない。** 第3.3節は判定レイヤーも両方へ適用するが、既存実装は環境変数から共通のバックエンドを選び、外部バックエンドなら検索対象の文を送る。二つ目の wiki も同じ送信対象になる。これは「そのあと会話の中身をファイルに書く」という免責とは別の経路である。根拠：[バックエンドと送信内容](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/decision-models.md:44)、[設定の選択](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_decide.py:170)、[HTTP 送信](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_decide.py:136)。

- **軽微：初回検索が必ず非同期になるという前提は誤り。** モデルを利用でき、未埋め込み件数が64以下なら、その場で埋め込みを終える。初回でも `warning` なし・`ready` になりうる。根拠：[State.query_wiki()](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_mcp_server.py:255)。

## 検証した事実

| 主張 | 結果 |
| --- | --- |
| 通常の MCP の wiki 操作は、呼び出しごとに `SCHEMA.md` を確認する | 一致。`wiki_root()` と各入口で確認 |
| 一つのサーバーが根ごとの `WikiIndex` を持つ | 一致。`State.wiki()` の辞書で分離 |
| MCP の検索順位は索引内の順位から作る | 一致。`wiki_index.fuse()` を確認 |
| CLI の意味検索は `.wiki-cache/` に書く | 一致。`open_vector_index()` を確認 |
| `--no-embed` かつ `--cache` なしなら、検索キャッシュを書かない | 一致。ページ収集と検索の分岐を確認 |
| 初期化が `.wiki-cache/.gitignore` を配置する | 一致。`init_wiki.py` のテンプレート一覧で確認 |
| help の引数表示がコマンドの frontmatter を読む | 一致。ただし詳細本文は別の `docs/commands.md` から読む |
| 作業領域の探索が複数の登録を返す | 食い違い。最初の一つで戻る |

実際の二つの wiki に対する問い合わせや、書き込みを伴う試験は実行していない。実装の読解と、ファイルを書かない関数・モックによる確認を行った。

## 崩せなかった点

- ページ集合が分離している場合、既存の MCP ツールへ根を明示して二回問い合わせること自体には、コード上の障害を見つけられなかった。
- 二つの検索結果のスコアを統合せず、別々に扱う規則は、既存のツールで実行できる。
- MCP の `graph` 呼び出し自体は DB を読み取り専用で開く。上記の書き込みは、その前に適用される既存の再抽出手順による。
- 出典にしなかった内容の混入と、後続作業への持ち出しは第5節が明示しているため、それ自体は未記載の欠陥として数えていない。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
