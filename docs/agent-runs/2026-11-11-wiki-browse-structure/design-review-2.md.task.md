対象は、info-hive の wiki プラグイン（サブモジュール `info-hive-wiki`、wiki 0.10.0、`f0a758f`）の閲覧（browse）の、構造の直しの設計である。実装はまだない。

経緯:
- browse の実装は、Sol の敵対的レビューで 7 回却下された（`docs/agent-runs/2026-11-09-wiki-browse-stage1-review/impl-review-1.md`〜`impl-review-7.md`）。そのたびに、指摘された反例を 1 つずつ塞いだ（`impl-responses.md`）。
- 作者が、場当たりの対応をやめて根本から直すよう指示した。指摘を原因の構造で分けた文書が `docs/agent-runs/2026-11-09-wiki-browse-stage1-review/impl-root-causes.md` である。
- この設計は、その構造（A: 守る場所を写しで持つ、C: 失敗の境界が決まっていない、D: 絶対パスの検査が推定、T: 試験が確かめていない）を直す。B（入力の走査が複数ある）は、別の計画（`docs/plans/wiki-walk-excluded-dirs-2026-11-11.md`）に乗る。

目的（対象が果たすべきこと）:
- 元の設計（`docs/plans/wiki-browse-stage1-2026-11-09.md`）の「守ること」1〜9 を変えずに、守り方を「起きると分かった場合を防ぐ」形から「その場合が起きても守りが外れない作り」に変える。
- 過去 7 回のレビューの重大な指摘と同じ種類の反例が、直したあとの作りでは作れなくなる。
- 作者の決定（設計の冒頭の表）: 0.10.0 は先に出した。絶対パスの実行時の検査は警告だけにする。この 2 つは崩す対象にしない。

読むもの:
- 設計: `docs/plans/wiki-browse-structure-2026-11-11.md`
- 原因の分析: `docs/agent-runs/2026-11-09-wiki-browse-stage1-review/impl-root-causes.md`
- 過去のレビューと対応: 同じディレクトリの `impl-review-1.md`〜`impl-review-7.md`、`impl-responses.md`
- 今の実装: `info-hive-wiki/skills/info-hive/scripts/wiki_browse.py`、`wiki_browse_core.py`、`wiki_browse_fs.py`
- 今の試験: `tests/wiki/test_browse.py`、`test_browse_fs.py`、`test_browse_server.py`、`tests/wiki/browse/browse.test.mjs`

この版は 2 版目である。1 版目は却下された（`docs/agent-runs/2026-11-11-wiki-browse-structure/design-review-1.md`）。2 版目は、1 版目の指摘が崩した前提を書き出し（設計の「1 版目のレビューで崩れた前提」）、同じ前提に頼る箇所をコードから探したうえで、8 つの原則（P1〜P8）から書き直した。1 版目の指摘が、反例を塞ぐ形ではなく、前提をなくす形で直っているかも確かめてほしい。

とくに崩してほしい点（反例を 1 つ挙げるだけでなく、その反例がどの前提、どの原則を崩しているかを書いてほしい）:
1. 原則 P1〜P8 のそれぞれについて、その原則を守った実装でも成り立つ、過去の指摘と同じ種類の反例。原則どうしの矛盾。
2. 「1 版目のレビューで崩れた前提」の表に、まだ挙がっていない前提。コードに残る、同じ前提に頼る箇所。
3. P3（設計の 3）: 走査を browse で 1 つにし、たどり方を lint の `rglob` に合わせる判断。lint と違う集合になる配置。wiki の走査の計画（`docs/plans/wiki-walk-excluded-dirs-2026-11-11.md`）との関係の穴。
4. P4（設計の 4）: 持ち場の実体を読まない規則で、読んでしまう経路、読むべきものを読まなくなる経路。`shutdown_requested` をなくして困る場面が、まだあるか。
5. P5（設計の 5）: 持ち場の単位の確かめを含めた守りで、守りから外れる経路。正しい使い方が止まってしまう経路。
6. P6（設計の 6）: 確定の点の表で、「すべて済むか、前のまま」が成り立たない順序。部分の失敗の扱いで、守ることのどれかが崩れるか。
7. P7（設計の 7）: 描く側に絶対パスが入る経路。
8. P8（設計の 8）: N と P の比較、3 つの探索、初期の状態と敵対的な入力の一覧、対照で、見つけられない欠陥の種類。8.5 の表の 17 件のうち、挙げた道具では見つからないもの（1 件ずつ照らしてほしい）。
9. 振る舞いが変わる点（設計の 9）の漏れと、順序（設計の 10）の問題。
