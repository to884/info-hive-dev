---
type: "source"
title: "Knowledge wiki with a dynamic workflow"
authors: ["Anthropic"]
url: "https://github.com/anthropics/claude-quickstarts/tree/main/managed-agents/knowledge-wiki"
raw: "raw/claude-quickstarts-managed-agents-knowledge-wiki.md"
ingested: 2026-11-16
created: 2026-11-16
updated: 2026-11-16
tags: ["wiki設計"]
concepts: ["エージェントのメモリの階層", "editとwriteの書き込みの競合"]
---

# Knowledge wiki with a dynamic workflow

Anthropic の `claude-quickstarts` リポジトリにあるクイックスタートで、変化の遅い文書群を一度だけナレッジ wiki に読み込み、その wiki からエージェントが答える。[[components-of-agent-memory]] が紹介した 2 本のうちの 1 本である。worked example は、完了した非公開化の案件の SEC 提出書類（EDGAR から取得）と、合成と明記した社内文書 2 つである。

原本は `raw/claude-quickstarts-managed-agents-knowledge-wiki.md`（Claude Sonnet 5.5 の訳）で、GitHub のディレクトリのページの README だけである。ノートブック（`distill_documents_into_knowledge_wiki.ipynb`）とプロンプトのファイルは読んでいない。「What's inside」のファイルの一覧の表は、取得の時点で 1 つの段落につぶれ、英語のまま残っている。

## 仕組み

1. **wiki を作る。** 1 つの Managed Agents のセッションが、1 通のメッセージで記述した動的ワークフローを実行する。文書は読み取り専用、wiki は読み書きできる形でマウントする。
   - extractor: 文書のバッチごとに 1 つ。登録する内容を取り出し、不足点を挙げる。
   - resolver: extractor の挙げた上位の不足点に取り組む。
   - analyzer: 統合の段で、登録された内容を文書と照らして確かめる。
   - organizer: wiki 全体を整える。
2. **wiki に問う。** エージェントは wiki を読み取り専用でマウントし、質問ごとに新しいセッションを使う。ファイルの先頭を読んでから要るセクションだけを読み、すべての事実を引用する。

ノートブックは、実行されたことをプラットフォームの記録と照らして確かめ、wiki を使うときと使わないときの 1 問あたりの費用を測る。wiki を最新に保つには、[[managed-agents-cma-dreaming-with-a-dynamic-workflow]] を案内している。

## wiki の約束ごと

- wiki は、Managed Agents のメモリストアに置いた平文の Markdown である。
- すべての事実に出所を付ける。文書どうしの矛盾は矛盾のまま残し、置き換えられた数値は置き換えられたものとして残す。
- worked example の合成の社内文書の 1 つは、会社が報告した数値とは別の基準の EBITDA の推定値を示す。wiki が両者を分けて保つ様子を見せるためである。
- ストアのファイルは 100 KB が上限である。大きなコーパスでは、主な会社のエンティティのページと赤旗のファイル（`escalations.md`）が先に上限に達し、リンクした複数のファイルに分ける必要がある。

## 費用の主張

README は次の数値を挙げる。評価の手順の細部は README になく、この wiki では確かめていない。

| 比べたもの | 結果 |
| --- | --- |
| 小さいモデル（Haiku 5.5）＋ wiki と、生の文書を検索する大きいモデル（Sonnet 5.5） | 差は 1 ポイント以内。1 回答あたりの価格は約 15 分の 1 |
| 小さいモデル＋ wiki と、自分で文書を検索する小さいモデル | wiki のほうが約 3 ポイント良い |
| wiki を作る費用 | ベンチマークの平均で約 19 ドル（一度だけ）。約 240 問で、大きいモデルに対して元が取れる |
| 記録した実行（`core`、8 件、2.8 MB のテキスト） | 23 分、定価で約 16 ドル |

文書をまたぐ事実はどの 1 つの段落にも書かれておらず、検索は質問のたびに最初からやり直しになる、というのが wiki を作る理由である。合うのは、エージェントが繰り返し問い合わせる変化の遅いコーパス（M&A のデューデリジェンス、訴訟の証拠開示、製品文書のサポートなど）である。

## 共有ページの損失を受け入れる

エージェントは共有ページに直接書くので、ときどき互いに上書きする。いちばん混み合うエンティティのページでは、登録した行の約 5% で内容が失われる。それでも、共有ページには異なる文書の数値が集まり、エージェントがその食い違いに旗を立てられるので、この損失を受け入れている（[[editとwriteの書き込みの競合]]）。

## 信頼できない入力

`kw.normalize_any` は、PDF、Word、Excel、PowerPoint、メールをテキストに変換する。取引相手からの Office ファイルは信頼できない入力なので、コンテナーの中か、壊れたファイルにさらしてもかまわないマシンで変換するか、信頼できるツールで先にテキストにする。自分の文書から作るときは、`COOKBOOK_DOCS` を、出所を記した `.txt` のフォルダーに向ける。この wiki の Office の抽出の調査は [[抽出の方式の比較-markitdown-2026-11-15]] にある。

## 取り込んだ内容と載せたページ

| 候補 | 主張と成り立つ条件 | 根拠の位置 | 行き先 | 理由 |
| --- | --- | --- | --- | --- |
| c1 | 変化の遅いコーパスでは、小さいモデル＋ wiki が、生の文書を検索する大きいモデルとの差を 1 ポイント以内にし、価格は約 15 分の 1 で、約 240 問で wiki の費用の元が取れる | 冒頭の段落 | `update` | [[エージェントのメモリの階層]] のメモリ表現の注意に足した |
| c2 | 共有ページへの直接の書き込みで、いちばん混み合うページの約 5% の行が失われるが、食い違いに旗を立てられる利点のために受け入れている | 「Cost and tier expectations」の「共有ページ」 | `update` | [[editとwriteの書き込みの競合]] に 3 つ目の扱い方として足した |
| c3 | 作る段（extractor、resolver、analyzer、organizer）と問う段（読み取り専用、質問ごとのセッション、すべての事実を引用）を分ける | 「How it works」の節と図 | `source_only` | 組み方の例は [[managed-agents-cma-dreaming-with-a-dynamic-workflow]] で足りており、README は各段の細部を書いていない |
| c4 | すべての事実に出所を付け、矛盾は矛盾のまま、置き換えられた数値は置き換えられたものとして残す | 冒頭、「The corpus」の節 | `source_only` | この wiki の矛盾の扱いと同じ考えで、新しく載せる先がない |
| c5 | 取引相手の Office ファイルは信頼できない入力で、隔離した場所で変換する | 「The corpus」の節 | `source_only` | 1 文の注意で、この wiki の抽出の設計に関わるかは確かめていない |

## 関係するページ

- [[components-of-agent-memory]]
- [[managed-agents-cma-dreaming-with-a-dynamic-workflow]]
- [[エージェントのメモリの階層]]
- [[editとwriteの書き込みの競合]]
- [[抽出の方式の比較-markitdown-2026-11-15]]
