対象は、info-hive の wiki プラグイン（サブモジュール `info-hive-wiki`、wiki 0.10.0、`f0a758f`）の閲覧（browse）の、構造の直しの設計である。実装はまだない。

経緯:
- browse の実装は、Sol の敵対的レビューで 7 回却下された（`docs/agent-runs/2026-11-09-wiki-browse-stage1-review/impl-review-1.md`〜`impl-review-7.md`）。指摘を原因の構造で分けた文書が `docs/agent-runs/2026-11-09-wiki-browse-stage1-review/impl-root-causes.md` である。
- 構造の直しの設計は、1〜4 版目が却下された（`docs/agent-runs/2026-11-11-wiki-browse-structure/design-review-1.md`〜`design-review-4.md`）。この版は 5 版目である。

作者の決定（設計の「作者が決めたこと」と `docs/adr/0017-wiki-browse-changes-only-what-it-created.md`）は、崩す対象にしない。決定から出る結果のうち、設計が書いていないものがあれば、挙げてほしい。

レビューを止める条件（作者が 2026年11月12日に決めた）:
- 確かめた OS と版で、**失敗のないときの約束**を破る反例が出なければ、残りの指摘は限界に書いて、作者の承認に回す。
- 失敗のないときの約束は、失敗（入出力の失敗、強制停止）も競合も入れない実行が守るべきこと（設計の 9.1 の基準を、手を入れない実行に当てたもの）である。
- そこで、指摘のそれぞれに、次のどれに当たるかを付けてほしい。
  - **A: 失敗のないときの約束を破る**（失敗も競合もない、正しい使い方で、約束が破れる）
  - **B: 失敗を入れたときの約束を破る**（失敗か強制停止を入れたときに、9.2 の許す結果から外れる）
  - **C: 試験や試作が、約束を確かめていない**
  - **D: 範囲の外**（設計の 2.2 に挙げたもの）
- 判定の節に、A に当たる指摘の件数を書いてほしい。

目的（対象が果たすべきこと）:
- 元の設計（`docs/plans/wiki-browse-stage1-2026-11-09.md`）の「守ること」の 1（言い換えたあとの文）と 2〜9 を、「その場合が起きても守りが外れない作り」で守る。
- 過去のレビューの重大な指摘と同じ種類の反例が、直したあとの作りでは作れなくなる。

読むもの:
- 設計: `docs/plans/wiki-browse-structure-2026-11-11.md`（とくに「4 回目のレビューで崩れた前提」と「レビューの指摘と対応」の 4 回目）
- 作者の決定: `docs/adr/0017-wiki-browse-changes-only-what-it-created.md`
- 前の版のレビュー: `docs/agent-runs/2026-11-11-wiki-browse-structure/design-review-1.md`〜`design-review-4.md`
- 書く側の規則の試作と探索と結果: 同じディレクトリの `write_model.py`、`write_sweep.py`、`write_sweep-output.md`、`results.md`。読めないページの確かめ: `unreadable_probe.py` と `unreadable_probe-output.md`
- 原因の分析: `docs/agent-runs/2026-11-09-wiki-browse-stage1-review/impl-root-causes.md`
- 走査の計画（7 版目、作者が承認した）: `docs/plans/wiki-walk-excluded-dirs-2026-11-11.md`
- 今の実装: `info-hive-wiki/skills/info-hive/scripts/wiki_browse.py`、`wiki_browse_core.py`、`wiki_browse_fs.py`、`wiki_pages.py`、`wiki_lint.py`
- 今の試験: `tests/wiki/test_browse.py`、`test_browse_fs.py`、`test_browse_server.py`

5 版目は、4 回目の指摘のうち、失敗のないときの約束を破った 4 件（1、2、4、7）を、守る対象の数え上げをやめる形で直した（書き込みの口が Wiki のルートとの重なりを確かめる、入力の一覧を 1 つにする、持ち主の識別子を記録を読むどの口でも照らす）。試作と探索も直し、探索に手を入れない実行の約束を足した。試作は規則の写しであり、製品のコードではない。

とくに崩してほしい点（反例を 1 つ挙げるだけでなく、その反例がどの前提、どの原則を崩しているかを書いてほしい）:
1. 失敗も競合もない正しい使い方で、守ること 1〜9 のどれかが破れる配置や手順（A）。とくに、6.1（書き込みの口の重なりの確かめ）を抜ける配置、7.1（持ち主の確かめ）で別の Wiki のものに触れる手順、2.1 の 4 つの性質が領分の外で変わる手順。
2. 試作（write_model.py）が、設計の 6 と 7 を正しく写しているか。探索（write_sweep.py）の基準が、試作の出力に依って甘くなっている箇所。
3. 4（入力の集合）と 9.2（読めない入力の基準）の穴。
4. 9.7 の表の 17 件のうち、挙げた道具では見つからないもの（1 件ずつ照らしてほしい）。
5. 振る舞いが変わる点（10）の漏れ、順序（12）の問題、原則どうしの矛盾。
