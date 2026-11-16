# 依頼：ADR-0029 の残る欠陥と、その修正案

対象は `C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/adr/0029-wiki-and-raw-hold-no-links.md`（10 版目）である。応答は日本語で書く。ファイルは変えない（読み取りだけ）。

## 背景

この ADR は、info-hive の wiki プラグインで、wiki と raw の「記事」にリンク（シンボリックリンク、ジャンクション、ハードリンク）を置かない規則を決める。GPT-6.1 Sol の敵対的レビューを 5 回受け、5 回とも却下だった（`docs/agent-runs/2026-11-16-adr-0029-wiki-links/review-1.md`〜`review-5.md`）。指摘は回を追うごとに、全体の設計から、細かい契約の食い違い（書き込みの部品の根、警告の届け先、読む口）に移っている。ADR は約 3.5 万字に膨らんだ。

作者の決定（ADR の「作者の決定」の 1〜8）は動かさない。とくに次の 3 つは前提とする。

- 対象は記事だけ（ページ、索引、`log.md`、`SCHEMA.md`、`raw:` が指す raw）。`.git/` などは対象外。
- 走査はリンクを拒む。
- リンクに当たっても、プラグインは置き換えず、警告を利用者に通知する。

## してほしいこと

今回は、欠陥を挙げるだけでなく、直し方も考えてほしい。

1. **残る欠陥。** 10 版目に残る、致命的と重大な欠陥を挙げる。それぞれに、具体的な反例（配置と手順）と根拠（ADR とコードの行）を付ける。1〜5 回目と同じ指摘の繰り返しは除く。確かめられないものは「推測」と書く。
2. **修正案。** 欠陥ごとに、原因の構造を直す修正案を出す。反例を 1 つずつ塞ぐ直し方ではなく、どの前提を変えればその種類の欠陥がまとめて消えるかを書く。案が複数あれば、採る案と理由を書く。
3. **全体の見立て。** 5 回の却下が続いた理由を、ADR の構造から説明する。ADR を小さく保ったまま閉じる形（たとえば、決定を少数の不変条件と 1 つの部品に寄せ、実装の詳細は設計書に移す）があれば、具体的に提案する。どこまでを ADR に書き、どこからを実装の設計書と試験に任せるかの線引きも書く。
4. **作者に聞くべきこと。** 修正案のうち、作者の決定に触れるか、作者が決めるべき選択があれば、それを挙げる。

## 出力の形

`## 残る欠陥`、`## 修正案`、`## 全体の見立て`、`## ADR を小さく閉じる案`、`## 作者に聞くべきこと`、`## 検証した事実` の順に書く。

## 読むファイル

この worktree のサブモジュールは初期化されていない。コードは主のチェックアウトで読む。wiki の指定の版は `git show 2452f59:<パス>`（`C:/Works/info-hive-dev/info-hive-wiki`）で照らす。

- ADR: 上のパス
- レビューの記録: `C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/agent-runs/2026-11-16-adr-0029-wiki-links/review-1.md`〜`review-5.md`
- 既存の ADR: `C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/adr/`（0008、0010、0013、0017、0019、0020、0023）
- 書く段の設計: `C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-apply-2026-11-14.md`
- 問い合わせの設計: `C:/Works/info-hive-dev/docs/plans/wiki-query-two-wikis-2026-11-16.md`
- wiki のコード: `C:/Works/info-hive-dev/info-hive-wiki/`
- rag のコード（`c59d05e`）: `C:/Works/info-hive-dev/info-hive-rag/scripts/`
