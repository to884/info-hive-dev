対象は、`/wiki:ingest` で URL を取り込むときの、raw の書き換えの検査（`wiki_rawcheck.py`）の 9 回目の実装と、`wiki_fetch.py` の雑音の規則・`--html-file`・作業用の写しである。設計は docs/plans/wiki-web-ingest-check-2026-11-13.md。

1〜8 回目の実装は却下された（docs/agent-runs/2026-11-13-wiki-web-ingest-check-review/impl-review-1.md〜impl-review-8.md）。指摘は原因の構造で分けて直し（impl-root-causes-1.md〜impl-root-causes-8.md）、反例を tests/wiki/test_wiki_web_check.py の ReviewCounterexampleTest〜ReviewCounterexample8Test、FetchCounterexample8Test などに回帰試験として入れた。本文は同梱の markdown-it-py（wiki_pages.new_parser()。lint と閲覧と同じ設定）のトークンの木で照らす。freeze は木の上で「消すことだけで作れるか」を再帰的に照らし、check は補足の引用を木から取り除いてから節点ごとに照らす。

8 回目の指摘への直し（impl-root-causes-8.md）の要点:
- 表: 6 回目と 7 回目の「列の数とパイプの数による言い換え」の保証を取り下げた。wiki_rawcheck.py は自分のパーサーの表の規則だけを差し替え（_table_with_real_cells）、検査の木の表のデータの行を、本文の行に実際にあるセルだけで作る（パーサーが補う空のセルを除き、捨てるセルを足す）。freeze の derivable は表の行のセルを位置で対応させ、check の compare は行の子の数を比べる。table_pipes と table_columns は消した。最初は「見出しより多いセルを raw に置かない」一律の禁止にしたが、取得した段落が `<br>` の行で表に読める場合と、セルの少ない行で値がずれる場合で崩れたので、この形に改めた。
- リスト: derivable の子の並びの対応で、リストを項目に開き、リストの種類を添えた項目を単位にした（block_units）。同じ記号のリストの間の雑音を消して前後のリストがつながる削除を通す。
- check --finish は、警告が残るあいだは作業用の写しを消さない（--accept-warnings で受け入れる）。freeze は残った画像を images に出す。unchanged の再取得では、写しと raw の frontmatter が同じときだけ work_dir を真にする。誤りと警告の行番号を raw のファイルの行番号にした。
- そのあと Sonnet 5.5 で 2 回目の実地の試行をし（sonnet-trial-2.md）、改善点を直した: 日本語の文でふつうに使う略語（JAPANESE_ABBREVIATIONS）を「原文にない英字か記号」の警告で数えない。「訳文にない名前」の警告と手順に、原語を括弧で添える直し方を書いた。参照の文書に「長いページの訳し方」を足した。補足の長さの目安をゆるめ、補足の中の段落を許した。

見てほしい点:
- impl-review-8.md の指摘が本当に起きなくなったか。impl-root-causes-8.md の主張（とくに、検査の木の表の行が本文のセルを表すこと、セルの数の違いがどちらの段でも木の対応の中で見つかること、リストの項目を単位にしても入れ子の変更や並べ替えを通さないこと）を崩せるか。
- 表の規則の差し替えが新しく持ち込んだ欠陥（トークンの並び、レベル、インラインの解析、参照の定義、入れ物の中の表、表に読める段落）。
- 正しい雑音の削除と正しい訳を止めてしまう入力、規則に反した raw が通る入力。今の wiki_fetch.py が実際に出す Markdown の形で確かめてほしい。
- 手順（commands/ingest.md の W1〜W9、references/ingest-workflow.md）と検査の動きが食い違うところ。とくに --finish と --accept-warnings、freeze の images、「長いページの訳し方」。
- 試験が確かめていると言いながら、実は確かめていないこと。

読むもの: info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py、info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py（origin/main からの差分は docs/agent-runs/2026-11-13-wiki-web-ingest-check-review/impl-9.submodule.diff）、tests/wiki/test_wiki_web_check.py、info-hive-wiki/skills/info-hive/scripts/wiki_pages.py の new_parser、同梱の info-hive-wiki/skills/info-hive/scripts/_vendor/markdown_it/rules_block/table.py、設計案、impl-review-8.md、impl-root-causes-8.md、sonnet-trial-2.md。

試験は `python -X utf8 -m unittest tests/wiki/test_wiki_web_check.py tests/wiki/test_wiki_fetch.py` で流せる（標準ライブラリと同梱のパーサーだけ）。
