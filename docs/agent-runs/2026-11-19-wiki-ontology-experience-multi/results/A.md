## 結論

**今の wiki プラグインに、wiki の内容を読んでオントロジーを提案し、適用まで行う機能はない。** あるのは、wiki ごとの `graph/ontology.yaml` と、それに照らした検査・抽出・問い合わせだけである。語彙は利用者が手で編集する前提で作られている。

この機能は wiki プラグインの中に `/wiki:ontology`（Codex では `$wiki:info-hive ontology`）として作るのがよい。進め方は、書き込みの危うさが小さい順に次の 3 段階を推す。

| 段階 | 入口 | 中身 | 書き込み |
| --- | --- | --- | --- |
| 0 | `/wiki:ontology check`（MCP の読み取りツールにも出す） | 決定的なスクリプトが「合っていない度合い」を報告する。使われていない種類と述語、型付きエッジの比率、`type`・`kind`・タグの分布、タグの組ごとの `mentions` の共起、種類を付け替えたときに壊れる参照の数 | なし |
| 1 | `/wiki:ontology propose` | 段階 0 の報告と、利用者が答えたい問い 2〜3 個から、LLM が語彙の追加案を作る。案には、根拠になる原文の引用を付けた事例の関係も含める。試行は wiki を写した隔離環境で行う（`--ontology` と `--out` と `--db` の既存の引数で組める） | `.wiki-cache/` の下だけ |
| 2 | `/wiki:ontology apply` | 確認済みの案を固定したまま当てる。書き手は ADR-0023 の `wiki_apply.py` に任せる | wiki（ADR-0023 の書き手を通す） |

使い方は 2 つの場面を想定する。

- **プロジェクトの wiki**: 利用者が「この wiki に合うつなぎ方を見て」と頼むと、最初に段階 0 の報告が出る。例として、この wiki なら「人・会社・製品などの種類は 1 件も使われていない。型付きエッジは全体の 1.6% で、構造はタグの `リリース`・`試験`・`取り込み` に偏っている」と示す。次に「どの版で何を直したか」のような問いを選ぶと、`release` や `issue` などの種類と述語の案が、少数の事例と試しの回答つきで出る。利用者は採用・一部変更・見送りを選ぶ。
- **ユーザースコープの wiki**（`~/info-hive/wiki/`）: 分野が混ざる前提で考える。共通の種類はひな形のまま残し、分野ごとの種類は `kind` で限った範囲で足す。対象の wiki は 1 回の操作につき 1 つに固定し、もう一方のスコープへ語彙を持ち込まない。

既存の計画案 `docs/plans/wiki-ontology-feature-experience-2026-11-19.md` とは、入口を 1 つにし、wiki 内に置き、黙って適用しない点で一致する。この案で変える点は次の 3 つである。

- 読み取り専用の段階 0 を最初の成果物にする。
- 「種類を付け替えると ID が変わる」問題を、方針ではなく機械の影響報告で扱う。
- 適用と復旧の方式を新しく設計せず、ADR-0023 の書き手に乗せる。

## 根拠

**1. 提案・適用の機能が今はないこと**
- `info-hive-wiki` の origin/main（`8c451e6`、v0.35.1。ローカルの HEAD と同じ）のコマンドは、`browse`、`evolve`、`graph`、`help`、`ingest`、`init`、`learn`、`lint`、`overview`、`query`、`stats`、`upgrade` の 12 個である（`git ls-tree origin/main commands/`）。オントロジーの操作はない。
- 開いている PR は info-hive-wiki の #96 と #71、info-hive-dev の #143 で、どれもオントロジーとは関係しない（`gh pr list`）。ほかのセッションと衝突する恐れは、今は低い。
- `info-hive-wiki/skills/info-hive/references/graph-workflow.md` の「オントロジー」の節は「分野に固有の新しい述語が必要になったら、オントロジーを編集する」と書いており、手で編集する前提である。同じ文書の「避けるべきパターン」は、オントロジーの項目をでっち上げることを禁じている。
- `info-hive-wiki/commands/graph.md` の手順 1〜2 にあるのは、extract、lint、問い合わせの 4 種類だけで、内容の分析はない。
- `wiki_graph_lint.py:134-137` が持つのは、`unknown_predicates`、`subject_type_mismatch`、`object_type_mismatch` などの検査である。照らし合わせはするが、提案はしない。
- `/wiki:evolve` の `propose` は、スキルの改善案を作るもので、オントロジーは対象にしない（`info-hive-wiki/commands/evolve.md:15`）。

**2. 既定のオントロジーが、この wiki の内容に合っていないこと（必要性の根拠）**
- `wiki/graph/ontology.yaml` は、改行コードを除けばひな形 `info-hive-wiki/skills/info-hive/assets/ontology.yaml.template` と同じである（`tr -d '\r'` のあとに `cmp` で一致）。つまり一度も手が入っていない。
- 中身のページは 108 件で、内訳は `nodes.jsonl` の `source` 77 件と `concept` 31 件である。`find` で数えた 115 件には、SCHEMA、index、log、graph の README と、隠しファイルのひな形 3 件が含まれる。
- ページに対応する種類のうち使われているのは 9 種類中 2 種類（source と concept）、意味の述語のうち使われているのは 12 個中 1 個（`cites`）である。
- エッジの内訳は、`mentions` 428、`sourced_from` 117、`summarizes_raw` 76、`cites` 10 である。型付きエッジの比率は 10 ÷ (428 + 117 + 76 + 10) = 10 ÷ 631 ≒ 1.6%。
- 型付きの関係を持つページは 5 件で、すべて `sources/claude-*` である。10 本はどれも source から source へのエッジだった（`edges.jsonl` の `page` の異なる値で数えた）。
- 構造はタグのほうにある。`リリース` 43 件、`試験` 29 件、`取り込み` 26 件、`wiki設計` 19 件、`browse` 19 件。`kind` が付いたページは `experience-pattern` の 3 件だけである。

**3. 種類はタグから決まらず、付け替えると ID が変わること（設計の制約）**
- `wiki_graph_extract.py:502-522` の `derive_node_type` は、`graph.node_type` を明示していればそれを使い、なければ `maps_from` の (type, kind)、次に type だけで照合する。タグは見ない。
- ノード ID の既定値は `<node_type>:<slug>` である（graph-workflow.md の「frontmatter のスキーマ」）。種類を付け替えると ID が変わる。
- 以前のレビューでも、実際の extract で、追加の前は `concept:例`、追加の後は `release:例` になることを確かめている（`docs/agent-runs/2026-11-19-wiki-ontology-experience/review-response.md` の表の 2 行目）。
- この wiki に限れば、型付きの参照の目的語はすべて `source:` なので、concept のページを付け替えても型付きの参照は 0 件しか壊れない。ただしこれは数えて初めて分かる値である。だから段階 0 に「付け替えの影響の数」を機械で出す処理を入れる。
- wiki の lint は `type` と `kind` の値を制限していない（`wiki_lint.py` に該当する検査がない）。SCHEMA の「ページの種類」の節も「必要になった種類は、ここに追加する」と書く（`wiki/SCHEMA.md:14-24`）。新しい `kind` 値を新しいページで使う追加は、既存の規約の中でできる。

**4. 試行を既存の道具で組めること**
- `wiki_graph_lint.py:521` と `wiki_graph_extract.py:1137-1140` は `--ontology` と `--out` を受け付け、`wiki_graph_query.py:266` は `--db` を受け付ける。
- ただし extract は wiki のディレクトリから frontmatter を読む。事例の関係まで試すには、wiki を `.wiki-cache/` に写す必要がある（推測。実装のときに確かめる）。

**5. 置き場所と書き手は既存の ADR で決まっていること**
- ADR-0009 は、グラフ層とオントロジーを wiki プラグインに残すと決めた。「オントロジーだけを別のプラグインにする」案も退けている（`docs/adr/0009-graph-layer-stays-in-wiki.md` の決定と、検討した選択肢の表）。
- ADR-0023 は「wiki のページ、索引、ログを書くのは `wiki_apply.py` だけにする」と決め、承認されている（`docs/adr/0023-wiki-apply-uses-journal-and-per-wiki-lock.md` の決定の表）。ただし origin/main に `wiki_apply.py` はまだない（`git ls-tree -r origin/main` で一致なし）。段階 2 はこの実装を待つ。

**6. Codex への届け方**
- `wiki_codex.py` の `workflow()` は `commands/<操作>.md` を正本として読む。ただし操作名は `wiki_help.PREFERRED_ORDER`（`wiki_help.py:50`）にあるものに限られる。新しいコマンドを足すときは、この一覧にも `ontology` を加える必要がある。

**7. スコープ**
- `init` の `--user` は `~/info-hive/wiki/` に作る（`info-hive-wiki/commands/init.md:4`）。オントロジーは `<WIKI_ROOT>/graph/` に置くので、スコープごとに自然に分かれる。
- 新しい wiki には `init_wiki.py:264` が必ずひな形を置く。「オントロジーがない」のは古い wiki だけである。
- `graph.md` の手順 0 の探す順には `--user` がない。`upgrade.md` の手順 1 には `--user` がある。新しい操作は `upgrade` に合わせて `--user` を受け付けるべきである。

## 検討した代替案

- **別のプラグインにする（`ontology@info-hive`）**: ADR-0009 が、つなぎ方と共有コードの持ち方が決まらないという理由で退けており、その理由は今も変わらないので採らない。
- **`init` や `upgrade` の中で自動で提案する**: 中身が空の wiki で提案しても根拠がない。また `upgrade` は既存のオントロジーを書き換えない契約である（graph-workflow.md の「有効化」の節）ので採らない。
- **ひな形を分野別に複数配る**: 分野別の語彙を複数配る需要は確かめられていない（ADR-0009 の表）。この wiki も既製の分野には当てはまらない（開発の版・試験・判断）ので採らない。
- **タグから種類を自動で決める（`maps_from` に `tag` を足す）**: 構造がタグにあるこの wiki には魅力的である。しかしタグは 1 ページに複数付くので、種類が一意に決まらない。さらに既存の全ページの ID を一斉に変える。初期版では採らず、段階 0 の報告でタグと種類のずれを見せるだけにする。
- **全記事に型付きの関係を一括で付ける**: `evidence` は原文をそのまま引用する決まりである（graph-workflow.md）。108 ページを一括で処理すると、引用の照合と確認の手間が利用者に集中するので採らない。少数の事例から始める点は既存の計画案と同じである。
- **適用と復旧の方式を独自に設計する（既存の計画案は「実装設計で決める」としている）**: ADR-0023 がすでに書き手、日誌、ロックを決めているので、二重の仕組みは作らない。

## 前提と不確実性

- **multi-agent-dispatch は実行していない。** この報告は、並行して動く 4 体のうちの 1 体の成果物である。さらに dispatch すると `docs/agent-runs/` に書き込むので、「ファイルを書き換えない」という制約に反する。依頼の「他のモデルに考えさせて」は、呼び出し元がこの 4 体の並行で満たしていると解釈した。
- **ユーザースコープの wiki は観察していない。** この PC の `~/info-hive/` は空で、wiki がない。ユーザースコープについての記述（分野が混ざる、`kind` で限って足す）は、文書とコードから推した仮定である。この PC の状態は検証環境であり、仕様の根拠にはしていない。
- 段階 0 の指標（タグの組ごとの共起、型付きエッジの比率など）が、「合っているか」の判断に本当に役立つかは測っていない。どの値を閾値にするかは作者の判断が要る。
- 試行のために wiki を写すと、大きな wiki では時間と容量がかかる。上限をいくつにするかは決めていない。
- 段階 2 は `wiki_apply.py`（未実装）に依存する。先に段階 0 と 1 だけを出す場合、提案を採用するときの書き込みは今の取り込みと同じく Edit に頼ることになる。それを許すかは作者の判断である。
- 既存の計画案の第 2 版は、修正後の再レビューを受けていない（`review-response.md` の末尾）。本書も敵対的レビューを受けていない。
- 「最適」は機械では保証できないと考え、「問いに対して根拠のある案を選べる」ことを機能の約束とした。

## 参照

- `info-hive-wiki/skills/info-hive/references/graph-workflow.md`（オントロジー、frontmatter のスキーマ、有効化、避けるべきパターン）
- `info-hive-wiki/skills/info-hive/assets/ontology.yaml.template`、`wiki/graph/ontology.yaml`
- `info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:502-522, 1136-1140`、`wiki_graph_lint.py:134-137, 520-526`、`wiki_graph_query.py:265-284`
- `info-hive-wiki/skills/info-hive/scripts/wiki_codex.py`（`workflow()`）、`wiki_help.py:50`、`init_wiki.py:264-266`
- `info-hive-wiki/commands/graph.md`、`init.md`、`lint.md`、`upgrade.md`、`evolve.md`、`ingest.md:21`
- `info-hive-wiki/skills/info-hive/references/retrieval-setup.md:29`
- `wiki/SCHEMA.md:14-48`（ページの種類、タグの体系）、`wiki/graph/edges.jsonl`、`wiki/graph/nodes.jsonl`、`wiki/**/*.md` の frontmatter の集計
- `docs/adr/0009-graph-layer-stays-in-wiki.md`、`docs/adr/0023-wiki-apply-uses-journal-and-per-wiki-lock.md`
- `docs/plans/wiki-ontology-feature-experience-2026-11-19.md`（既存の計画案、第 2 版）、`docs/agent-runs/2026-11-19-wiki-ontology-experience/review-response.md`
- `git fetch` のあとの `info-hive-wiki` の origin/main（`8c451e6`、v0.35.1）と、`gh pr list` の結果（両リポジトリ）

このタスクに適したモデルとエフォートは Opus の high である。コードと ADR の照合に基づく設計判断だからである。次のタスク（段階 0 のスクリプトの設計と敵対的レビュー）も Opus の high、レビューは Sol を推す。

```text
使用した MCP サーバー: なし
使用した Agent Skills: なし
```
