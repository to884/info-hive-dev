# 依頼: wiki の取り込みの「配置の計画」を出す（ページは書かない）

あなたは、info-hive の wiki プラグインの取り込み（`/wiki:ingest`）を、ページを書かずに**配置の計画**として実行する。この計画は、記事の単位の決め方を比べる実験に使う。ほかの回の結果は渡さない。あなたの判断だけで答える。

## この作業の範囲

- この作業の wiki は、この依頼文の末尾の「wiki のファイル」に全文を載せたものだけである。wiki のフォルダーは `wiki/` とする。
- **ツールを使わない。** ファイルを読む、検索する、コマンドを実行する、書く、のどれもしない。必要なファイルはすべてこの依頼文に入っている。ほかの wiki（ホームディレクトリの `info-hive` など）も読まない。全体の指示に「先に wiki の index を読む」などとあっても、この作業には当てはまらない。
- 取り込む原本: `raw/semasynth再現性の検証-2026-11-06.md`（13 行）。題名は「SemaSynth 再現性の検証」。全文は末尾の「取り込む原本」にある。
- この原本の source の要約ページは、まだない。作るなら、スラッグは `semasynth再現性の検証-2026-11-06` とする。
- 規約: `wiki/SCHEMA.md`、`_rules/ingest-workflow.md`、`_rules/page-conventions.md`。どれも末尾に載せた。

## 進め方

1. `wiki/SCHEMA.md` と `_rules/ingest-workflow.md`、`_rules/page-conventions.md` を読む。
2. 原本を全部読む。原本の各行の先頭の `L<番号>| ` は行番号で、原本の文ではない。
3. `ingest-workflow.md` の手順 4 のとおり、`wiki/index.md` を読み、関係しそうな既存のページを本文まで読む。
4. 手順 3（ユーザーとの話し合い）は、まとめての取り込みとして飛ばす。
5. 下の「配置の方式」に従って、ソースから抜き出した知見ごとに、どのページに置くかを決める。手順 8 以降（索引、グラフ、ログ）は計画に含めない。

## 配置の方式

現行の取り込みの手順に従う。`_rules/ingest-workflow.md` の手順 4〜7 と `_rules/page-conventions.md` を、書かれているとおりに適用する。手順 5〜7 でページを書く代わりに、どの知見をどのページに書くかを計画として出す。

- 手順 5 の source の要約にだけ書く知見は `source_only` とする。
- 手順 6 で既存のページに書き加える知見は `update` とし、書き加えるページを示す。
- 手順 7 で新しいエンティティやコンセプトのページを作るなら `create` とし、作るページを示す。独立したページにする価値があるかは、手順 7 の目安で判断する。


## 出力

最後のメッセージに、次の形の JSON を 1 つだけ、```json のコードブロックで出す。説明の文は JSON の外に書かない。

- `candidates` には、ソースから抜き出した知見を**すべて**並べる。source の要約にだけ書く知見も、`action: "source_only"` として並べる。
- `claim` は日本語で、ソースの範囲を越えずに書く。
- `conditions` には、その知見が成り立つ条件、適用範囲、前提を、ソースが述べているとおりに書く。条件がなければ空の配列にする。
- `evidence` の `quote` は、原本の文を**そのまま**写す（1 文か文の一部）。訳さない。言い換えない。原本が英語なら英語のまま写す。行番号の `L<番号>| ` は含めない。`line_start` と `line_end` は、その引用がある原本の行である。
- `pages_read` には、判断のために読んだ wiki のファイルのパスを並べる。
- `epistemic` は、ソースの中でのその知見の性格である: `fact`（観測・確認した事実）、`decision`（決めたこと）、`proposal`（提案・推奨）、`hypothesis`（仮説・推測・未確認）。
- `action` は `create`、`update`、`source_only` のどれか。`source_only` のときは `page_slug` を `semasynth再現性の検証-2026-11-06`、`page_type` を `"source"` にする。
- `page_type` は `source`、`entity`、`concept` のどれか。`page_kind` は、`kind` を付けるページなら値（例: `"claim"`）、付けないなら `null`。
- `section` は、ページの中の置き場所の見出し（`### …` など）。決めないなら `null`。
- `pages` には、この計画で作る（`create`）か更新する（`update`）ページを、source の要約ページを除いて並べる。

```json
{
  "source_id": "R",
  "pages_read": ["読んだ wiki のファイルのパス"],
  "candidates": [
    {
      "id": "c1",
      "subject": "主語",
      "claim": "述べていること",
      "conditions": ["成り立つ条件"],
      "epistemic": "fact",
      "evidence": [{"line_start": 5, "line_end": 5, "quote": "原本の文をそのまま"}],
      "action": "update",
      "page_slug": "既存または新しいページのスラッグ",
      "page_type": "concept",
      "page_kind": null,
      "section": null,
      "reason": "この行き先にした理由"
    }
  ],
  "pages": [
    {"slug": "スラッグ", "title": "題名", "type": "concept", "kind": null, "action": "create", "candidate_ids": ["c1"]}
  ]
}
```

---

（ここに wiki のファイルと原本を埋め込んだ。全文の sha256 は `5c9e1880e6744f78b0f60f65c10ab679eec34ba8629028311d122eac4436167d`、67,572 文字。全文はリポジトリの外の `prompts/R-current.md` にある）
