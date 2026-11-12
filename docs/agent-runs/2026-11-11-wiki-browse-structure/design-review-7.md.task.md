対象は、info-hive の wiki プラグイン（サブモジュール `info-hive-wiki`、wiki 0.10.0、`f0a758f`）の閲覧（browse）の、構造の直しの設計である。実装はまだない。

経緯:
- browse の実装は、Sol の敵対的レビューで 7 回却下された（`docs/agent-runs/2026-11-09-wiki-browse-stage1-review/impl-review-1.md`〜`impl-review-7.md`）。指摘を原因の構造で分けた文書が `docs/agent-runs/2026-11-09-wiki-browse-stage1-review/impl-root-causes.md` である。
- 構造の直しの設計は、1〜6 版目が却下された（`docs/agent-runs/2026-11-11-wiki-browse-structure/design-review-1.md`〜`design-review-6.md`）。この版は 7 版目である。5 回目と 6 回目のレビューでは、下の A に当たる指摘が 1 件ずつだった。

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
- 設計: `docs/plans/wiki-browse-structure-2026-11-11.md`（とくに「6 回目のレビューで崩れた前提」と「レビューの指摘と対応」の 6 回目）
- 作者の決定: `docs/adr/0017-wiki-browse-changes-only-what-it-created.md`
- 前の版のレビュー: `docs/agent-runs/2026-11-11-wiki-browse-structure/design-review-1.md`〜`design-review-6.md`
- 書く側の規則の試作と探索と結果: 同じディレクトリの `write_model.py`、`write_sweep.py`、`write_sweep-output-v7.md`（7 版目の試作の全量の探索の出力）、`results.md`（経緯は 7 と 6 にまとめた）。6 版目の出力（`write_sweep-output-v6*.md`）は、前の版の記録である。読めないページの確かめ: `unreadable_probe.py` と `unreadable_probe-output.md`。名前がリンクのときの作る口の確かめ: `lock_link_probe.py`、`createfile_probe.py`、`create_probe-output.md`
- 原因の分析: `docs/agent-runs/2026-11-09-wiki-browse-stage1-review/impl-root-causes.md`
- 走査の計画（作者が承認した。実装済み、未マージ）: `.claude/worktrees/wiki-walk-excluded-dirs/docs/plans/wiki-walk-excluded-dirs-2026-11-11.md`。この作業ツリーの `docs/plans/` にある同じ名前の未追跡のファイルは古い写しなので、読まない
- info-hive-wiki の main は 0.11.0（Python の下限を 3.12 に上げた）まで進んでいる。レビューの対象のサブモジュールの作業ツリーは、0.10.0（`f0a758f`）のままである
- 今の実装: `info-hive-wiki/skills/info-hive/scripts/wiki_browse.py`、`wiki_browse_core.py`、`wiki_browse_fs.py`、`wiki_pages.py`、`wiki_lint.py`
- 今の試験: `tests/wiki/test_browse.py`、`test_browse_fs.py`、`test_browse_server.py`

7 版目は、6 回目のレビューの指摘を次のように直した。試作は規則の写しであり、製品のコードではない。
- A（ロックのファイルが Wiki の中を指すリンクのとき、`O_CREAT` で開くと Wiki の中に作る）: 書き込みの口が名前そのものに働き、最後の名前を解かないことを原則にした（3.2、6.1）。ファイルを作る口を、Windows では `CreateFileW` と `FILE_FLAG_OPEN_REPARSE_POINT` で呼ぶ（3.1）。Windows の `os.open` は `O_EXCL` を付けても先のないリンクをたどることを確かめた。ロックの名前のリンクは、たどらずに外してから作る（6.2）。探索に、ロックと目印の名前のリンクの状態を足した。
- C（唯一の退避の世代を失う実行を合格にする）: 基準を、最後に公開した世代が書き出し先か作業用の `old-N` に残ることで量る形にした（9.2）。
- C（確定の前の失敗を、警告付きで吸収すれば合格する）: 失敗の役目を、試験の側が、手を入れない実行の記録と呼び出しの対象から決める形にした（9.2）。サーバーにも 7.1 の判定を足した。
- 軽微な指摘は、文で直した（3.1 の識別子、4.1 と 11 の読めない入力の範囲、12 の走査の計画の版）。

6 版目の全量の探索で自分で見つけて直したもの（ジャンクションを外す試し直し、警告の文と基準、6.1 の確かめの祖先へのさかのぼり、書き出しとサーバーの始めの順）は、`results.md` の 6 と設計の 9.6 にある。

とくに崩してほしい点（反例を 1 つ挙げるだけでなく、その反例がどの前提、どの原則を崩しているかを書いてほしい）:
1. 失敗も競合もない正しい使い方で、守ること 1〜9 のどれかが破れる配置や手順（A）。とくに、6.1（書き込みの口の重なりの確かめ）を抜ける配置、3.2 の「口は名前そのものに働く」が成り立たない口や配置、7.1（持ち主の確かめ）で別の Wiki のものに触れる手順、2.1 の 4 つの性質が領分の外で変わる手順。
2. 試作（write_model.py）が、設計の 3.1、6、7 を正しく写しているか。探索（write_sweep.py）の基準が、試作の出力に依って甘くなっている箇所。
3. 4（入力の集合）と 9.2（読めない入力の基準）の穴。
4. 9.7 の表の 17 件のうち、挙げた道具では見つからないもの（1 件ずつ照らしてほしい）。
5. 振る舞いが変わる点（10）の漏れ、順序（12）の問題、原則どうしの矛盾。
