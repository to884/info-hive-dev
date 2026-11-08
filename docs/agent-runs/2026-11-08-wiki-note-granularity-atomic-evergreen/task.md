# タスク：wiki の記事の単位を決める手法として、Atomic Notes と Evergreen Notes を検討する

## 作者の指示

> 記事の単位を決定する手法として、Atomic Notes + Evergreen Notes を検討してください

この指示の直前に、作者は「現在の `/wiki:ingest` で raw を取得し wiki の記事を作る場合に、系統だった手法を使っているか」と尋ねた。それへの回答の要点は次のとおりで、今回の検討はその続きである。

- raw の取得と保存（`wiki_fetch.py`、SHA-256 による重複判定、文字コードの判定、raw を書き換えない決まり）は系統立っている。
- 記事を作る部分は、手順の順序とチェック項目（関係するページの洗い出し、`str_replace` による部分更新、矛盾の記録、被リンク必須、大きさの上限）だけが決まっている。何を抜き出し、何を独立したページにするかはモデルの判断に任されている。
  - 要約ページの本文は「主な主張、必要なら方法論、結論、未解決の問い」とあるだけで、主張を 1 件ずつ取り出す形式がない。
  - entity や concept を独立したページにするかは「目安」（ソースが主要なトピックとして扱っているか、今後のソースが掘り下げそうか）で決める。
  - 要約が原文に忠実かを機械で照合するのは、グラフの `evidence` の引用だけである。

## 決めたいこと

1. Atomic Notes と Evergreen Notes の考え方を、info-hive の wiki の「記事の単位」を決める手法として採るか。採るなら、そのまま採るか、どこを変えて採るか。
2. 採る場合に、`/wiki:ingest` の中でモデルが「何を 1 ページにするか」を**再現性をもって**判定できる手順（判定の基準、チェックリスト、ページの題名の付け方）。
3. 既存の規約（ページの種類 `source`、`entity`、`concept`、`synthesis`、大きさの上限、インデックス、検索、グラフ、lint）への影響と、変える箇所。

## 現状として分かっていること

### wiki プラグイン（`info-hive-wiki`、プラグイン名 `wiki`、スキル名 `info-hive`）

- LLM が保守する Markdown の wiki。移植元は praneybehl/llm-wiki-plugin v4.0.1 で、それは Karpathy の「LLM Wiki」の gist をもとにしている。人が書く Zettelkasten ではなく、**LLM が取り込みのたびにページを作り、更新する**のが前提である。
- 3 層: raw（変更不可の原本）、wiki（LLM が書くページ）、`SCHEMA.md`（wiki ごとの規約。スキルの記述より優先）。任意で `graph/`（型付きエッジの派生データ）。
- ページの `type` は `source`（`sources/`）、`entity`（`entities/`、`kind` は person、company、product、paper、place、organization）、`concept`（`concepts/`）、`synthesis`（`synthesis/`、クエリの回答を保存したもの）。`learn` は `concept` に `kind: experience-pattern`、`status: hypothesis|supported|superseded` のページを作る。
- 現行の「アトミックなページ」の定義（`SKILL.md` と `references/page-conventions.md`）: 「1 つのページは 1 つのことを扱う。『消費税』のページが『インボイス制度』のページを兼ねてはならない」「中身のある小見出しが 5 つもあれば独立したページにすべき」。大きさはソフト上限 10,000 文字または 100 行、ハード上限 25,000 文字または 200 行（空白を除く文字数）。つまり単位は「1 コンセプト（または 1 エンティティ）」と大きさで決まっていて、「1 つの考え・主張」ではない。
- 取り込みでは、ソースごとに `sources/<スラッグ>.md` を 1 つ書き、関係する entity と concept のページを `str_replace` で部分更新し、新しいものはページを作って被リンクを付ける。
- インデックスは 1 ページ 1 行。`index.md` が約 300 行か wiki が約 150 ページを超えたら `indexes/` に分割する。スケーリングの閾値は 150、300、500 ページ。
- 検索はセクション単位のハイブリッド検索（語彙 + 埋め込み）。ローカルで完結し、wiki の内容をマシンの外に出さない。
- グラフ: 本文の `[[wikilink]]` から `mentions`、`sources:` から `sourced_from` のエッジが自動でできる。型付きの述語（`contradicts`、`supersedes`、`depends_on` など）は `ontology.yaml` で宣言し、`evidence`（原文の引用）、`confidence`、`status` が必須。ノード型 `claim` と `decision` は `explicit_only`（明示したときだけ使う）。
- ファイル名（スラッグ）は日本語可。空白、`\ / : * ? " < > |`、`# | [ ] ^`、全角の `｜` `＃`、全角英数字、半角カタカナは使えない。Windows のパス長にも注意がいる。

### 作者の wiki の実態（2026-11-08 時点）

作者のユーザースコープの wiki は `D:\Users\toshiki\info-hive\W0_Wiki\` にある（このリポジトリの外。読んでよいが書き換えない。PC 固有のパスを仕様に書かない）。

- source 37、entity 1、concept 17、synthesis 1。source のうち約 28 本は作者の別プロジェクト（SemaSynth）の作業記録で、それに対応する concept はほとんどない。source に知識が溜まり、concept に育っていない偏りがある。
- concept の多くは Yuan An の連載（オントロジー、ナレッジグラフ、コンテキストグラフ）の用語ページ（`オントロジー`、`ナレッジグラフ`、`グラウンディング` など）で、1,600〜4,300 文字。
- 一方で、`concepts/編集要求の復元世代を最終適用まで保持する.md`、`concepts/Windows での Tantivy の commit の失敗.md`、`concepts/BM25 の IDF の式の違い.md` のように、題名が主張や知見の形になったページも自然に生まれている。

## 検討の観点（少なくとも次を扱う）

- **定義の確認**: Atomic Notes（Zettelkasten の Luhmann と Ahrens、「1 ノート 1 アイデア」）、Evergreen Notes（Andy Matuschak: atomic、concept-oriented、densely linked、題名は主張の文、時間をかけて育つ、自分のために書く）、literature note と permanent note の区別。出典を示し、確かめられなかった点は「未確認」と書く。
- **対応づけ**: 既存の `source`、`entity`、`concept`、`synthesis`、`experience-pattern` を、literature note、permanent（evergreen）note、structure note（MOC）などにどう対応づけられるか。どれが欠けているか。
- **単位の候補の比較**: 少なくとも次の 4 つを比べる。ほかの候補を足してよい。
  1. 現行のまま（1 コンセプト 1 ページ + 大きさの上限）
  2. 1 主張 1 ページ（題名を主張の文にする evergreen を全面的に採る）
  3. 併用（用語・エンティティのページは現行どおり、その下に主張のページを置き、用語のページが主張のページを束ねる構造ノートを兼ねる）
  4. 主張をページではなくページ内の単位（見出しやブロック、または frontmatter・グラフの `claim` ノード）として持つ
- **LLM が保守する前提での問題**: 人が時間をかけて育てる手法を、取り込みのたびに LLM が書く wiki に移すと何が壊れるか。ページ数の増加（インデックスの閾値、取り込みのトークン、`str_replace` の対象の探索）、重複ページ（言い換えの違う同じ主張）、主張の題名の揺れ、「自分のために書く」の扱い、主張の更新と `contradicts` / `supersedes` との関係。
- **日本語での問題**: 主張の文を題名とスラッグにするときの長さ、記号の制約、表記揺れ、wikilink を文中に埋め込む書き方の自然さ。
- **判定の再現性**: 同じソースを 2 回取り込んだときに、同じページ割りになるか。モデルが変わっても揺れない判定基準と、lint で機械的に検査できる指標（例: 見出しの数、主張の数、被リンクの数、題名の形）。
- **作者の wiki の偏り**（source に溜まり concept に育たない）を、この手法が解くか。
- **移行**: 既存の 56 ページをどう扱うか（そのまま、段階的、一括）。

## 評価の基準

候補を次の基準で 1〜10 点で採点し、合計（各点数 × 重みの和 ÷ 100）で並べる。点数の根拠を短く添え、重みを 2 通り変えて上位が入れ替わるかも確かめる。基準の妥当性への異議は成果に書いてよい。

| 基準 | 重み | 高く評価する条件 |
| --- | --- | --- |
| 知識の再利用と成長 | 25 | クエリで必要な知見を直接引ける。複数のソースにまたがって 1 つのページが育つ。source に溜まったままにならない |
| 判定の再現性 | 20 | 同じソースから同じページ割りになる。モデルが変わっても揺れない。lint で検査できる |
| 規模とコスト | 20 | 150〜500 ページでもインデックス、検索、取り込みのトークンが破綻しない |
| 既存設計との整合 | 20 | Markdown が正本、ローカル完結、グラフ（ADR-0009）、検索、日本語のスラッグの規則と矛盾しない |
| 移行と実装の軽さ | 15 | SCHEMA.md と references の改訂で回るか、スクリプトの変更が小さい。既存のページを壊さない |

## 読むべき文書とコード

プラグインの本体はサブモジュール `info-hive-wiki/` だが、作業ディレクトリによっては空なので、`C:\Works\info-hive-dev\info-hive-wiki\` を読む。

- `AGENTS.md`（リポジトリの役割、日本語と機械が読む文字列の方針）
- `info-hive-wiki/skills/info-hive/SKILL.md`
- `info-hive-wiki/skills/info-hive/references/ingest-workflow.md`、`page-conventions.md`、`architecture.md`、`scaling-playbook.md`、`graph-workflow.md`、`lint-workflow.md`、`query-workflow.md`、`evolution-workflow.md`
- `info-hive-wiki/skills/info-hive/assets/SCHEMA.md.template`、`ontology.yaml.template`、`page.md.template`
- `info-hive-wiki/commands/ingest.md`、`learn.md`、`lint.md`
- `info-hive-wiki/skills/info-hive/scripts/wiki_lint.py`（大きさとアトミックさの検査）
- `docs/adr/0009-graph-layer-stays-in-wiki.md`
- `docs/agent-runs/2026-11-06-wiki-knowledge-utilization/summary.md`（前回の活用方法の検討）
- 作者の wiki: `D:\Users\toshiki\info-hive\W0_Wiki\` の `SCHEMA.md`、`index.md`、`concepts/` と `sources/` のいくつか

## 成果に含めるもの

成果は 1 本の Markdown で、次の順に書く。

1. **結論の要約**: 採るか、採らないか、どこを変えて採るか。推す単位の案と、その理由を 5 行以内で。
2. **定義と出典**: Atomic Notes と Evergreen Notes の原則を表にし、各原則が LLM が保守する wiki で保てるか（保てる / 変えれば保てる / 保てない）を判定する。
3. **既存の種類との対応表**と、欠けている種類。
4. **単位の候補の比較**: 上の基準での採点表と、重みを変えたときの結果。
5. **推す案の詳細**:
   - ページにするかの判定手順（取り込みの中でモデルが順に問う質問、または判定表）。同じ判定にならない境界の例を 3 つ以上挙げ、どう裁くかを書く。
   - 題名とスラッグの規則（日本語の例を 5 つ以上。作者の wiki の実在のソースから作る）。
   - frontmatter と `type` / `kind` の変更案（キーと値は英語。方針 B）。
   - ingest、query、lint、graph、インデックスへの影響と、`ingest-workflow.md` と `page-conventions.md` の改訂の要点。
   - lint で機械的に検査できる指標の案。
6. **試し方**: 作者の wiki の実在のソース 2〜3 本（オントロジー連載の 1 回分と SemaSynth の作業記録 1 本を含む）を、推す案で取り込み直したらどうなるかを、ページの一覧（題名、種類、リンク先）として示す。実際にファイルは書かない。再現性を確かめる PoC の手順（同じソースを別のモデルや別の回で取り込み、ページ割りの一致を測る方法と指標）も書く。
7. **移行**の案。
8. **確認できなかったこと**と、基準や重みへの異議。

リポジトリのファイルと作者の wiki は書き換えないこと。成果は日本語で書き、コマンド名、frontmatter のキー、`type` の値、述語名、ファイル名は英語の原文のまま書く。
