対象は、info-hive の wiki プラグイン（サブモジュール `info-hive-wiki`、wiki 0.10.0、`f0a758f`）の閲覧（browse）の、構造の直しの設計である。実装はまだない。

経緯:
- browse の実装は、Sol の敵対的レビューで 7 回却下された（`docs/agent-runs/2026-11-09-wiki-browse-stage1-review/impl-review-1.md`〜`impl-review-7.md`）。指摘を原因の構造で分けた文書が `docs/agent-runs/2026-11-09-wiki-browse-stage1-review/impl-root-causes.md` である。
- 構造の直しの設計は、1〜3 版目が却下された（`docs/agent-runs/2026-11-11-wiki-browse-structure/design-review-1.md`〜`design-review-3.md`）。この版は 4 版目である。

作者の決定（設計の「作者が決めたこと」と `docs/adr/0017-wiki-browse-changes-only-what-it-created.md`）は、崩す対象にしない。ただし、決定から出る結果のうち、設計が書いていないものがあれば、挙げてほしい。とくに、3 回目のレビューのあとで次の 2 つが決まった。
1. 守る範囲を、項目の名前、種類、通常の中身、属性（読み取り専用か、と更新時刻）に限る。代替データストリーム、拡張属性、アクセス制御の一覧、マウント、調べてから操作するまでの競合、利用者が書き換えた一覧は、守る対象にしない（設計の 2）。範囲の外のものを使った反例は、「範囲の外」と分けて書いてほしい。範囲の中の 4 つの性質が変わる反例を、とくに求める。
2. browse の領分（`<data_dir>/browse/` の下に browse が作るディレクトリと、`--out` の隣の作業用のディレクトリ）の中に利用者が手で置いたものは、守らない。

目的（対象が果たすべきこと）:
- 元の設計（`docs/plans/wiki-browse-stage1-2026-11-09.md`）の「守ること」の 1（言い換えたあとの文）と 2〜9 を、「その場合が起きても守りが外れない作り」で守る。
- 過去のレビューの重大な指摘と同じ種類の反例が、直したあとの作りでは作れなくなる。

読むもの:
- 設計: `docs/plans/wiki-browse-structure-2026-11-11.md`
- 作者の決定: `docs/adr/0017-wiki-browse-changes-only-what-it-created.md`
- 前の版のレビュー: `docs/agent-runs/2026-11-11-wiki-browse-structure/design-review-1.md`〜`design-review-3.md`
- 書く側の規則の試作と探索と結果: 同じディレクトリの `write_model.py`、`write_sweep.py`、`results.md`。読めないページの確かめ: `unreadable_probe.py`
- 原因の分析: `docs/agent-runs/2026-11-09-wiki-browse-stage1-review/impl-root-causes.md`
- 走査の計画（3 版目、作者の承認待ち）: `docs/plans/wiki-walk-excluded-dirs-2026-11-11.md`
- 今の実装: `info-hive-wiki/skills/info-hive/scripts/wiki_browse.py`、`wiki_browse_core.py`、`wiki_browse_fs.py`、`wiki_pages.py`、`wiki_lint.py`
- 今の試験: `tests/wiki/test_browse.py`、`test_browse_fs.py`、`test_browse_server.py`

4 版目は、3 回目の指摘のうち 2 件を範囲の決定で、残りを規則の直しで受けた。規則どうしのぶつかり（3 回目の重大 3 と 5）を文章で見落とさないよう、書く側の規則を試作にし、失敗、2 つ目の失敗、短い書き込み、強制停止の探索をかけた（設計の 9.6）。試作は規則の写しであり、製品のコードではない。

とくに崩してほしい点（反例を 1 つ挙げるだけでなく、その反例がどの前提、どの原則を崩しているかを書いてほしい）:
1. 6（書く側）と 7.1（サーバーの記録）: 領分の外で、2.1 の 4 つの性質が変わる経路。正しい使い方が止まってしまう経路（止まり続ける場合を含む）。6.1 の「作る場所が Wiki のルートの下にないか」の確かめ（`realpath(strict=True)` と識別子）で、抜ける配置。
2. 試作（write_model.py）が、設計の 6 と 7.1 を正しく写しているか。写していない規則、写し違い。探索（write_sweep.py）の基準が、試作の出力に依って甘くなっている箇所。探索が届かない種類の失敗。
3. 4（入力の集合）: 2 回の走査（4.2）で受けられない変化。走査の計画の約束と、4.1 の表の穴。
4. 9.2 の「入力の中身の読み取り」の基準（同じ失敗を入れた lint との一致）で、通ってしまう誤り。
5. 3（入出力の層）: 口の一覧と、失敗の読み替えの 1 か所で、握りつぶしが残る場所。
6. 5 と 8（読む側、描く側）: 生成器が機械の情報を足す経路。
7. 9.7 の表の 17 件のうち、挙げた道具では見つからないもの（1 件ずつ照らしてほしい）。
8. 振る舞いが変わる点（10）の漏れ、順序（12）の問題、原則どうしの矛盾。
