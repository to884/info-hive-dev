# 依頼: セッションの取り込みの実装の敵対的レビュー（1 回目）

承認済みの設計 `docs/plans/wiki-session-ingest-2026-11-14.md`（5 版目）と ADR `docs/adr/0020-session-raw-is-rendered-once-from-decisions.md` を実装した。設計が書いていない細部は `docs/plans/wiki-session-ingest-impl-2026-11-14.md` で決めた。前段の確かめと実物での確かめは `docs/research/wiki-session-id-probe-2026-11-14.md` にある。

## 対象

- `info-hive-wiki/skills/info-hive/scripts/wiki_session.py`（新規。中心）
- `info-hive-wiki/commands/ingest.md`（手順 2 の分岐と S1〜S10）
- `info-hive-wiki/skills/info-hive/references/ingest-workflow.md` の「Claude Code のセッション」、`page-conventions.md` の「セッションの raw の frontmatter」
- `tests/wiki/test_wiki_session.py`、`tests/wiki/fixtures/session/`（生成器と手で作った記録）、`tests/wiki/check_session_readonly.py`

## 目的（実装が守るべきこと）

1. 設計の 1〜13 節と「試験」の節のとおりに動く。設計から外れた箇所、設計の決定を弱めている箇所を探す。
2. 確認の前の会話の文、モデルの思考、ツールの結果、通知・伝言・差し込みの中身、`mark` に渡した文字列が、raw、wiki、決定のファイル、ディスクのどこにも出ない（標準出力と、いま動いているセッションの記録は設計が認めた限界）。
3. raw は、承認した `render_sha256` に一致したときだけ、重ねて書かない形で置かれ、上書きされない。同じ入力から、どの PC でも同じバイト列になる。
4. 記録の形が変わっても、漏れる側に倒れない（許可リスト）。
5. `scan` が、伏せた文字列と規則に当たる文字列を、文字列を出さずに見つける。`--allow` が穴にならない。
6. 試験が、設計の求める性質を本当に確かめている（対照が本当に落ちる理由で落ちる、空回りする試験がない）。

## 範囲の外（指摘しなくてよい）

- wiki の書き込みの排他（ロックとパッチ）。別の設計 `docs/plans/wiki-apply-2026-11-14.md` で扱う。
- 設計の「保証しないこと」の 1〜13 に書いた限界そのもの。ただし、実装がその限界を広げているなら指摘する。
- 作者の判断（設計書の見出しの表の (1)〜(7)）そのもの。

## 出力

テンプレートの見出しのとおりに。指摘には、ファイルと行、再現の入力（記録の行の形、引数）を添える。
