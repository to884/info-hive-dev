# browse の Fluent 2 化の設計のレビュー（1 回目）

## 対象

- 設計書: `docs/plans/wiki-browse-fluent2-2026-11-14.md`
- 改訂した設計: `docs/plans/wiki-browse-findability-2026-11-13.md`（改訂の差分は `git diff HEAD~1 -- docs/plans/wiki-browse-findability-2026-11-13.md`）
- ADR: `docs/adr/0021-wiki-browse-uses-fluent2-replica.md`
- 試作: `poc/browse-fluent2/`（`proto_fluent.py`、`assets/style.css`、`assets/theme.js`、`assets/app.js`、`shoot.mjs`）と、確かめの結果 `docs/agent-runs/2026-11-14-wiki-browse-fluent2/shots/report.json`
- 同梱した資産: `info-hive-wiki/skills/info-hive/scripts/browse_assets/`（`fluent2.css`、`README.md`、`licenses/`。サブモジュールのブランチ `feature/browse-fluent2`）

## 目的

`/wiki:browse` の画面（索引、サイドバー、検索、記事のページ）を、React を使わずに Fluent 2 を再現した CSS（`fluent2.css`）で描く。設計が約束すること:

1. CSP（`default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:`）、`[style]` が 0 件、外への通信が 0 件、classic な `<script src>` だけ、`file://` とサーバーの 2 方式で同じ画面、スクリプトなしでも読める、という今の約束を保つ。
2. 配色を、ライト、ダーク、OS に合わせる、から選べ、選んだ値がページを移っても、サーバーを起動し直しても（ポートが変わる）残る。保存できないときは OS に合わせ、エラーを出さない。
3. 段 F1（探しやすさの実装と一緒）を単独で出しても、記事のページの配色が混ざらない。
4. 日本語の組版（禁則、折り返し）、幅 320〜1000 ではみ出さない、主な要素のコントラスト比 4.5:1、強制カラーで今のページが見分けられる。
5. 実装は同梱した `fluent2.css` だけを読み、スキルの場所に依存しない。ライセンスの表示が閲覧の出力に付いて回る。

前提となる既存の設計: `docs/plans/wiki-browse-stage1-2026-11-09.md`、`docs/plans/wiki-browse-structure-2026-11-11.md`（承認済み、未実装）、ADR-0010、0016、0017。今の実装は `info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py`、`wiki_browse.py`、`browse_assets/`、試験は `tests/wiki/test_browse*.py`、`tests/wiki/browse/`。

## 止める条件（作者が決めたこと）

指摘には分類を付ける。

- A: 失敗も競合も入れない正しい使い方で、設計の約束（上の 1〜5）を破る反例。
- B: 試作や参照の実装だけの欠陥で、設計の文は正しいもの。
- C: 表現、試験の網羅、限界の書き漏らし。

A が 0 件なら、残りは限界に書いて作者の承認に回す。A には、具体的な入力か操作と、約束のどれを破るかを書く。
