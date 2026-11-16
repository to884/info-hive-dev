# 依頼：ADR-0029（wiki と raw の木にリンクを置かない）の 3 回目の敵対的レビュー

対象は `docs/adr/0029-wiki-and-raw-hold-no-links.md`（この worktree）の 4 版目である。応答は日本語で書く。

## 前回からの変化

2 回目のレビュー（`docs/agent-runs/2026-11-16-adr-0029-wiki-links/review-2.md`、却下）のあと、次を直した。直し方が原因を閉じているかも確かめてほしい。

- ADR-0023 の `Writer` をほかの書き手にそのまま使わせる形をやめた。`wiki_fsguard.py` を、書き込みの部品（下の層。道の検査、一意の一時ファイル、名前での置き換え、重ねて書かない置き方）と `Writer`（上の層。書く段の領域と役割）の 2 層に分け、すべての書き手が下の層を使う。
- 一時的なハードリンクの例外を、関数の名前ではなく置き方（`os.link()` のあとに一時ファイルの名前を消す）で決め、置き方を部品の 1 か所に置いた。書く段のロックと `new` のページも含める。
- raw の根を、相対パスの `raw:` の形から推し量るのをやめた。`/wiki:lint` はいつも raw の根を渡す。渡されない lint は、指す項目だけを調べ、調べられなかったものを `summary` に挙げる。
- uv のキャッシュを守る木の中に置く設定を、規則に反した配置とした。
- コマンドの表を手順の全体で書き直した。先のないファイルのシンボリックリンクの移行の扱いを足した。`SERVER_FILES` に `wiki_decide.py` がないことを書いた。

作者の決定（1〜5）そのものは崩す対象ではない。決定を具体化した本書の提案と、事実の記述を崩してほしい。1、2 回目と同じ指摘の繰り返しではなく、直したあとの形に残る欠陥を探してほしい。

## 確かめてほしいこと

- 2 層に分けた書き込みの部品が、ADR-0023 と書く段の設計（`docs/plans/wiki-apply-2026-11-14.md`）と矛盾しないか。部品の「根は書き手ごとに決める」で、根の取り違えや、根より上のリンクを通す形がないか。
- 例外の置き方の定義に、置き方を装った永続的なハードリンクや、例外を使わない書き手のハードリンクが入り込まないか。
- raw の根を渡さない lint の扱いと、`/wiki:lint` が raw の根を決める順（`/wiki:ingest` の手順 0 と同じ）に、取り違えや漏れがないか。
- 「コマンドごとの当て方」の表が、実際のコマンドとスクリプトの書き込みと合うか。
- ADR が「確かめた」と書く事実が、コードと合うか。

## 読むファイル

この worktree のサブモジュールは初期化されていない。コード、設計書、レビューの記録は、次の主のチェックアウトの絶対パスで読む（読み取りだけ）。

- ADR（対象）: `C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/adr/0029-wiki-and-raw-hold-no-links.md`
- 1、2 回目のレビュー: `C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/agent-runs/2026-11-16-adr-0029-wiki-links/review-1.md`、`review-2.md`
- 既存の ADR: `C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/adr/`（0008、0013、0017、0019、0020、0023）
- 書く段の設計: `C:/Works/info-hive-dev/.claude/worktrees/adr-wiki-links-4ebc39/docs/plans/wiki-apply-2026-11-14.md`
- 問い合わせの設計: `C:/Works/info-hive-dev/docs/plans/wiki-query-two-wikis-2026-11-16.md`
- wiki のコード（v0.19.5、`2452f59`）: `C:/Works/info-hive-dev/info-hive-wiki/`（`commands/`、`skills/info-hive/scripts/`、`skills/info-hive/references/`）
- rag のコード（`c59d05e`）: `C:/Works/info-hive-dev/info-hive-rag/scripts/`

ファイルは変えない。
