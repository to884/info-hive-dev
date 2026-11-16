## 判定

**却下。確信度：高。** 保存した推論を次回の問い合わせで「高」にできる規則の衝突と、検索失敗の原因を解消しない「上げる方法」が残っている。以下は文書・コードの静的照合と規則への反例であり、実際の LLM の判定頻度は測定していない。

## 致命的・重大な欠陥

1. **重大：シンセシスへの保存だけで、推論を「中」から「高」に変えられる。**

   反例として、ソース A に「製品 A の重量は 100 g」、ソース B に「製品 B の重量は 200 g」があり、どちらにも比較の記述はない状態を考える。「B は A の何倍重いか」に「2 倍」と答える初回の判定は、複数ページを組み合わせたので「中」になる。

   その回答を、両ソースを `sources` に入れたシンセシスとして保存する。次回は、そのページに「B は A の 2 倍」と直接書かれており、ソースの要約ページにも到達できるため、出発点の第1行では「高」に該当する。元資料が比較を直接述べるようになったわけではない。

   「独立した根拠に数えない」「保存しても上がらない」という禁止と、「直接書かれていてソースまでたどれる」という判定条件が衝突している。ソースを読んでも、保存された主張がそこで直接裏づけられることを必須にする規則はない。同じ保存済み wiki から、シンセシスの直接記述を採るエージェントと、元の導出過程を採るエージェントで判定が割れる。

   根拠：[query-workflow.md](/C:/Works/info-hive-dev/.claude/worktrees/query-confidence/info-hive-wiki/skills/info-hive/references/query-workflow.md:86) の出発点、92 行のシンセシスの扱い、127 行の保存による昇格禁止、154・162 行の保存形式。

2. **重大：出発点の表が、単一ページから導く回答を定義していない。**

   1 ページに「成功 8 件、失敗 2 件」と書かれ、ソースにも到達できる状態で、「成功率は？」と質問する。答えの「80%」はページに直接書かれておらず、複数ページを組み合わせた結果でも、検索の抜粋でもない。新しい外部事実を補ったわけでもない。

   表にはこの回答の出発点がない。元の数値を判定対象にすれば「高」、計算を「組み合わせ」と拡張解釈すれば「中」、算術を一般的知識に含めれば「低」になる。「結論を支える主な主張」を採点するため、入力の数値だけを採点し、導いた結論自体を採点しない解釈も残る。通常の計算・集計で規則が未定義になる。

   根拠：[query-workflow.md](/C:/Works/info-hive-dev/.claude/worktrees/query-confidence/info-hive-wiki/skills/info-hive/references/query-workflow.md:75) の判定単位と、86〜90 行の出発点の列挙。ADR-0028 の 57 行も主張の切り分けによる判定差を認めているが、この表の未定義部分は解消していない。

3. **重大：`failed_open` に対する「上げる方法」が、その失敗を解消しない。**

   `--decide` を有効にし、判定バックエンドが未設定の状態で検索する。コードは `DecisionError("unavailable", ...)` を発生させ、結果を残して `decision.failed_open: true` を返す。規則上、回答は最大「中」になる。

   ところが提案表は、この原因を「検索が縮退していた」にまとめ、「初回の埋め込みが終わり、`warning` が消えてから同じ質問をし直す」と案内する。判定バックエンドの未設定は埋め込み完了では直らない。CLI の JSON には、そもそもこの `warning` フィールドがない。MCP が使えていても、任意の判定レイヤーを使うため CLI を選ぶ手順なので、MCP の復旧案内にも該当しない。

   同様に、MCP の `warning` はモデルを使えない恒久的なエラーでも発生し、待機で消えるとは限らない。

   根拠：[query-workflow.md](/C:/Works/info-hive-dev/.claude/worktrees/query-confidence/info-hive-wiki/skills/info-hive/references/query-workflow.md:103)、同 134 行。[wiki_decide.py](/C:/Works/info-hive-dev/.claude/worktrees/query-confidence/info-hive-wiki/skills/info-hive/scripts/wiki_decide.py:303) の未設定時の fail-open、[wiki_search.py](/C:/Works/info-hive-dev/.claude/worktrees/query-confidence/info-hive-wiki/skills/info-hive/scripts/wiki_search.py:847) の JSON 形式、[wiki_mcp_server.py](/C:/Works/info-hive-dev/.claude/worktrees/query-confidence/info-hive-wiki/skills/info-hive/scripts/wiki_mcp_server.py:264) のモデル利用不能時の warning。

## 崩れる前提

- **ページからソースへ到達できれば、その主張もソースに裏づけられる。** ページ単位の `sources` は、個々の主張との対応を保証しない。保存した分析や、複数の話題を含むページで崩れる。
- **結論を支える主張の集合が一定になる。** 根拠の数値を主張とするか、計算結果や推奨まで主張に含めるかで変わる。最小値を取る処理だけでは、入力集合の違いは吸収できない。
- **検索の縮退は埋め込み待ちか MCP の不通である。** 判定バックエンドの設定不足、CLI の埋め込み失敗、MCP のモデル利用不能では成立しない。
- **矛盾・旧版の状態が、選んだページから分かる。** 候補ページと見込みのあるリンクだけを読む手順なので、別ページにある反証を読むエージェントだけ上限が下がる。全文走査を避ける設計上、同じ wiki・同じ質問でもこの差は残る。

## 見落としと軽微な問題

- **軽微：自動的な CLI の縮退が明示されていない。** 上限表は CLI の `--no-embed` を挙げるが、通常実行でも埋め込み失敗を捕捉して語彙検索に戻る。JSON は `mode: "lexical"`、警告は stderr である。「縮退」を広く解釈すれば対象だが、列挙された条件だけを確認すると見落とす。根拠：query-workflow.md 103 行、wiki_search.py 1027〜1032 行。

- **軽微：概要と正本で保存・confidence の例外が一致していない。** `SKILL.md` 171 行は保存提案を無条件に記述し、「低なら提案しない」を省いている。利用者向け `docs/commands.md` 75 行と CHANGELOG 13 行も、関連内容がない場合は confidence を付けない例外を説明していない。正本を読めば解決するが、概要だけでは異なる動作になる。

- **軽微：承認前の書き込み経路が既存手順に残る。** query-workflow.md 41 行が参照する graph-workflow.md 161 行は、古いグラフを先に extract で作り直すよう命じる。extract は `graph/` の成果物を書き換える。一方、`commands/graph.md` 22 行は実行の「提案」にしている。新規に導入された経路ではないが、「承認しない限り実行されない」という利用者向け説明を問い合わせ全体に読むと成立しない。ページ本文の無断修正とは区別すべき既存不整合である。

- **軽微・組み合わせ時の未定義：2 wiki の衝突を上限表が明示的に扱わない。** 親 main の計画では、片方が「担当は甲」、他方が「担当は乙」なら両方を示す。しかし現規則の低上限は「wiki の中に矛盾する記述」となっている。各 wiki 内には矛盾がないため、各主張を「高」のまま扱う解釈が残る。計画の第3.6節との組み合わせで生じる問題であり、現行の単一 wiki 動作の不具合とはしていない。

## 検証した事実

- **一致：** グラフの値は `confidence: high|medium|low`、`status: current|historical|proposed|disputed|superseded`。新規規則が参照する値は実在する。根拠：graph-workflow.md 23 行。
- **一致：** 経験パターンの `hypothesis|supported|superseded` は SCHEMA テンプレート 211 行に存在する。`/wiki:learn` は検証済み経験を記録・統合するコマンドであり、提案された用途は存在する。
- **一致：** `/wiki:graph lint` は存在し、`source`・`evidence` の欠落を検査する。ただし通常の検査だけで主張の意味的な裏づけまで保証するものではない。根拠：commands/graph.md 15 行、wiki_graph_lint.py 270〜280 行。
- **一致：** `/wiki:lint` のワークフローには矛盾・古い主張の内容確認がある。ただしスクリプトの自動検出ではなく LLM による確認で、最近の約10ページなどに対象を絞る。根拠：lint-workflow.md 71〜83 行。
- **一致：** MCP の `warning` と `index.state: embedding` は実装に存在する。初回でも少量なら同期的に埋め込むため、常に warning が出るわけではない。根拠：wiki_mcp_server.py 266〜276 行。
- **一致：** HEAD `daabf28` はコードを変更せず、文書・指示と plugin の版を変更している。`plugin.json` と CHANGELOG はともに `0.20.0`。回答への情報追加に minor を使う判断は、この差分からは崩せなかった。
- 対象ファイルは変更していない。

## 崩せなかった点

- RRF の `score` や関連度判定を、回答の正しさの確率として流用しない方針。
- 判定対象の主張・出発点・上限が確定した後に、最小値を取る処理の順序独立性。
- 「低」の保存を提案しない規則と、保存済み confidence をそのまま再利用しない規則自体。
- confidence を上げるための取り込み・ページ修正・エッジ修正を、承認前は提案にとどめる明示的な制約。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
