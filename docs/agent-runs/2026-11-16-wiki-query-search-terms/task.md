# レビューの目的

info-hive-wiki のコマンド `/wiki:query`（Claude Sonnet 5.5 が実行する）で、回答の「どう探したか」の説明に、wiki の外の知識が入る漏れを止める変更である。

## 漏れの形

- 0.21.1 の決まりは「自分の知識で思い付いた答えを、検索に使った語として回答に書かない」だった。
- 0.21.1 で 33 回測ると、4 回で漏れた。Q09（CQRS は何の略か。wiki に答えはない）で「コマンドとクエリの責務分離」「Command Query Responsibility Segregation」、Q10（PyMuPDF の部分は wiki にない）で `fitz`、Q11（uv の実装言語は wiki にない）で「Rust」。回答は `answers-0.21.1-q09-q11.txt` にある。
- 漏れた回は、決まりが書かれた手順 7 や `query-confidence.md` を読んだうえで破っている。どの語が答えに当たるかを、モデル自身が判断する文面が原因と見た。
- 答えのある問いの回答には、質問文にない語の引用は 0 回だった（照合は `docs/research/wiki-query-confidence-sonnet-2026-11-16/scripts/check_search_terms.py`）。

## 変更

- 語を引用してよいのは、質問文にそのままある語だけとした。自分で選んだ語は「言い換えた語でも探した」と種類だけを書く。どの検索の手段でも、ヒットした理由の説明でも同じ。
- コマンドの手順 4c と、クエリのワークフローの手順 5 に書いた。手順 7 と `query-confidence.md` は、そこを指す。差分は `wiki.diff`。

## 見てほしいこと

- この決まりで、上の漏れの形が止まるか。止まらない書き方（引用符を使わない、語を地の文に書く、取り込む候補の名前に答えを入れる、など）が残っていないか。
- 決まりが、答えのある問いの回答や、検索の縮退の報告（`warning`）、確からしさの理由を壊さないか。
- 照合のスクリプトが、測り直しの判定に使えるか。数え漏れと誤検出の形。
- 3 つのファイルの記述が食い違っていないか。

対象のファイル:
- `info-hive-wiki/commands/query.md`
- `info-hive-wiki/skills/info-hive/references/query-workflow.md`
- `info-hive-wiki/skills/info-hive/references/query-confidence.md`
- `info-hive-wiki/CHANGELOG.md` の Unreleased
- `docs/research/wiki-query-confidence-sonnet-2026-11-16/scripts/check_search_terms.py`
