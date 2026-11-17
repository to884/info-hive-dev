## 判定

**条件付きで採用可**（確信度：中〜高）。`keep` による抜け道を塞いだ点と、`completed` を追加した点は機能しています。ただし二つの欠陥があり、直してからのマージを条件にします。

- **正しい訳を止める**：見出しと表のセルに製品名を英語で残すと、`untranslated` エラーになります。このエラーを受理する手段はありません。
- **未翻訳のまま完了する**：段落の後半を英語で残しても、中国語をほぼ訳さなくても `completed: true` になります。

## 致命的・重大な欠陥

### 1. 重大（実装と設計）：見出しと表のセルで、固有名詞を英語に残した正しい訳がエラーになり、完了できない

- **反例**：隔離した一時ディレクトリで `main(["check", …, "--json", "--finish", "--accept-warnings"])` を実行しました。いずれも `code=1`、`errors=['untranslated']`、`completed=False` です。
  - `# Introduction to Apache Kafka` → `# Apache Kafka 入門`
  - `# Getting Started with Apache Kafka Streams` → `# Apache Kafka Streams 入門`
  - `## Apache Kafka versus RabbitMQ Streams` → `## Apache Kafka と RabbitMQ Streams`
  - `## What is Amazon Elastic Kubernetes Service` → `## Amazon Elastic Kubernetes Service とは`
  - 表のセル `Supported on Linux, macOS and Windows` → `Linux、macOS、Windows で対応`
  - 表のセル `Microsoft Azure Cosmos Database` を、製品名なのでそのまま残した場合
  - 論文名の見出し `## Attention Is All You Need` を英語のまま残した場合も、同じ経路でエラーになります（実行して確かめたのではなく、計算上の推定です）。
- **原因**
  - 見出し、`th`、`td` では `title_case_ok=False` が渡されます（`info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py:1007`）。
  - `names_of` はこの場合、大文字で始まる普通の語を名前として返しません（`:911-913`）。
  - そのため `translation_block` の `protected` に `Apache`、`Kafka`、`Linux`、`Windows` などが入らず（`:937`）、名前が「訳すべき外国語の文章」として数えられます。
  - 日本語の比率が 0.2 未満になり、エラーになります（`:963`）。
- **完了できない理由**：エラーなので `--accept-warnings` では通りません（`:1203`）。W6 は固有名詞のカタカナ化を禁じています（`references/web-raw.md` の W6）。結果として、正しく訳したエージェントは `failed` で止まるしかありません。
- **退行であること**：変更前は、これらの見出しは警告にとどまり、完了できていました。英語の技術記事では「Introduction to X」「What is X」型の見出しが普通に現れるので、多くの取り込みが止まります。
- **試験の穴**：`test_headings_lists_quotes_and_table_cells_are_checked` は未翻訳の例しか試していません。名前を含む見出しを正しく訳した例の試験がありません。

### 2. 重大（実装）：段落の中の部分翻訳が完了する

- **反例**（`--finish --accept-warnings`）
  - 6 文の英語の段落のうち前半 3 文だけを訳し、後半の英文 3 文（約 150 文字）をそのまま残す → `code=0`、`completed=True`、`state=checked`
  - 3 文の段落のうち 2 文を訳し、最後の 1 文（約 100 文字）を英語のまま残す → `completed=True`
  - 文ごとに訳と原文を交互に置く対訳 → `completed=True`
- **原因**
  - 英文の丸残しの検査は、原文の一続き（`foreign_runs`）全体が訳文の部分文字列のときだけ働きます（`:943-946`）。英語だけの段落では一続きが段落全体になるので、1 文でも訳すと外れます。
  - 残りは文字数の比率 0.2 だけで判定しています（`:963`）。日本語は同じ内容を英語の 3 分の 1 程度の文字数で書くので、おおよそ 4 割を訳せば通ります。
  - 長い出力を途中で打ち切る、後半を訳し忘れる、といった現実的な失敗が `completed: true` になります。
- **計画との関係**：計画の (c)「一段落だけ翻訳」は、段落が 2 つある場合（`test_one_translated_paragraph_does_not_cover_another`）しか試していません。

### 3. 重大（実装。中国語の資料に限る）：中国語は 1 文字変えるだけで「翻訳済み」になる

- **反例**
  - 中国語の段落の「的」を 1 か所だけ「の」に変える → `completed=True`
  - 2 文のうち 1 文だけを日本語に訳し、残りを中国語のまま残す → `completed=True`
- **原因**：`counts` は漢字を「日本語の文字」として数えています（`:950`）。そのため中国語の文は、手を入れなくても比率が 1 に近くなります。止められるのは、まったく変えていない場合（`same(src) in same(out)`）だけです。
- **この経路に実際に入ること**：`wiki_fetch.japanese_text_ratio` はかなが 1 文字もなければ 0 を返します（`wiki_fetch.py:1102-1107`）。したがって中国語のページは `needs_translation: true` になり、この検査を通ります。
- **試験の穴**：試験（`test_unchanged_long_chinese_prose_is_not_translation`）は、まったく変えない場合と末尾に日本語を足す場合しか試していません。

## 崩れる前提

- **「短いブロックだけを除けば、名前はほぼ守られる」**
  - 見出しと表のセルでは名前の保護がほぼ働かないので、崩れます（欠陥 1）。
  - 逆に普通の段落でも、`We Use Apache Kafka And Redis For Fast Event Delivery Across All Regions Today.` のように大文字で始まる語が多い文は、すべて名前として除かれます。英語のまま残しても `checked_blocks: 0` で通ります。
- **「漢字は日本語の文字の証拠になる」**：中国語の原文では成り立ちません（欠陥 3）。日本語の文であることは、かなの有無で見ないと判別できません。
- **「誤検出は例外的で、手順で吸収できる」**
  - 計画の 4 は受理のフラグを作らず、エラーは警告として受理できません。そのため、誤検出が一つあるたびに、取り込みの失敗かコードへの例外の追加しか選べなくなります。
  - しきい値は固定です（20 文字、4 語、0.2、全大文字は 6 文字未満なら略語扱い、`JAPANESE_ABBREVIATIONS` の流用）。欠陥 1 を直すには、さらに例外を足す圧力がかかります。場当たり的な修正を招きやすい構造です。
- **「`translation.state: checked` は何かを検査した結果である」**：`checked_blocks: 0` でも `checked` になります（`:1112`）。呼び出す側の手順（`web-raw.md` の 5）も `verified_completion` も、0 件を受け入れます（`tests/wiki/check_web_raw_agent.py:509-521`）。
- **「読み取り API が言語の検査を十分にする」**：`html_block` の中身は、翻訳するページでは比べていません。`Node.content` を持つのは `fence` と `code_block` だけで（`:440`）、`compare` も `html_block` を見ません。`wiki_fetch` が `html_block` を出力しうるかは確かめられていません（推測）。

## 見落としと軽微な問題

- **軽微（設計）：短いブロックだけのページは、翻訳者名を入れるだけで完了する**
  - 再現：「- Fixed crash on startup / - Faster cold boot / - New config loader」と、短い英語のセルの表を、英語のまま残して `translated_by` だけを入れる → `completed=True`、`state=checked`、`checked_blocks=0`
  - 3 語以下の長い句（`Comprehensive observability infrastructure`）も対象外です（`:958`）。
  - 計画の (b)「翻訳者名だけ」の拒否が成り立つのは、検査対象のブロックがあるときだけです。ページ全体の集計がありません。
- **軽微（実装）：英語の引用を残した正しい訳が止まる**：`As the README says, "Move fast and break nothing in production".` → `README にあるとおり、"Move fast and break nothing in production" である。` は `untranslated` になります。引用を訳せば回避できるので軽微とします。
- **軽微（手順）：警告を受理する経路では、完了の根拠が写しの消失だけになる**：`web-raw.md` の 5 の `warnings` では、`--finish --accept-warnings` のあとに「作業用の写しが消えたこと」だけを確かめます。同じ節の「フォルダーの消失や `ok` だけを根拠にしてはならない」と食い違います。
- **軽微（手順）：止まるときの状態が計画と文書で食い違う**：計画は「`needs_user` または `failed`」としていますが、`web-raw.md` と `agents/web-raw.md` は `failed`（`kind: other`）だけです。
- **軽微（実装）：`state` が翻訳以外の誤りでも `incomplete` になる**：`translation.state` は、リンクや frontmatter の誤りでも `incomplete` になり（`:1112`）、翻訳が未完了だと誤読されえます。
- **軽微（実装）：文字の出力には完了の情報が出ない**：`--json` を付けない出力（`render`）には `completed` も `translation` も出ません。手順は `--json` を必須にしているので、実害は小さいです。

## 検証した事実

- 一致：必要な翻訳を `keep` で外すと `translation_required` になり、`--finish --accept-warnings` でも写しが残ります（`:1057-1060`、`:1203`）。
- 一致：`needs_translation` が真偽値でないか、ないときは `ValueError` になります。JSON は出さず、終了コードは 1 で、写しも残ります（`:1046-1048`）。
- 一致：`completed` が真になるのは `--finish` で写しを消せたときだけです（`:1209`）。
- 一致：`wiki_fetch` は中国語を `needs_translation: true` と判定します（`japanese_text_ratio` はかながなければ 0 を返す）。
- 一致：既存の回帰試験 `tests.wiki.test_wiki_web_check` と `tests.wiki.test_web_raw_agent` は 183 件すべて成功しました（`PYTHONDONTWRITEBYTECODE=1` で実行し、作業ツリーの状態は開始時と同じであることを確かめた）。
- 一致：PR to884/info-hive-wiki#87 は OPEN で、head は `3ad7018` です。origin/main の版は 0.29.0、タグは `v0.29.0` までで、0.29.1 はまだ使われていません。
- 上の反例はすべて、`C:\UserData\toshiki\Temp\tmp.Excb0A1C8Q\probe.py` と `probe2.py` で一時ディレクトリを使って再現しました。

## 崩せなかった点

- `keep` で翻訳必須の判定を解除する経路、および `--accept-warnings` でエラーを通す経路は、ともに塞がれていました。
- 次の場合は正しく止まりました。
  - 英文を言い換えた場合、句読点だけを変えた場合
  - 図の補足だけを足した場合
  - 日本語を短く足した場合
  - 全大文字の文章
  - 日本語の段落の中に英文を丸ごと残した場合
- 次の正しい訳と原文は誤検出しませんでした。
  - 普通の段落で、文頭の製品名を英語で残した訳
  - コードスパンにしていないエラーメッセージを英語で残した訳
  - UI の表示名を英語で残したリストの項目
  - 日本語の原文
- `verified_completion` は、旧形式、`keep`、`translation` のない結果、`translated_by` が空の結果を完了と認めませんでした。

`✶ Insight ─────────────────────────────────────`
- 「英字に対する日本語の文字数の割合」で判定すると、日本語は情報の密度が高いぶん、4 割を訳すだけで通ります。そのうえ漢字は中国語と区別できません。言語の判定には、かなの有無と、原文の文ごとの丸残しを別々に見る必要があります。
- 見出しは語ごとに大文字で始まるので、固有名詞と区別できません。名前の保護を外すと、名前だけの見出しが「未翻訳」と同じに見えます。受理の手段がないエラーに、この曖昧さを持ち込んだことが、欠陥 1 の構造上の原因です。
`─────────────────────────────────────────────────`

次の作業（欠陥 1〜3 の構造的な修正）に適したモデルとエフォートは、Opus（high）です。

使用した MCP サーバー: なし
使用した Agent Skills: なし
