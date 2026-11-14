# 依頼: main の取り込みで移した手順の敵対的レビュー

## 背景

wiki プラグイン 0.15.0 は、`/wiki:ingest` に URL を渡したときの raw の段（W1〜W8）を、`model: sonnet` のプラグインのエージェント `wiki:web-raw`（`info-hive-wiki/agents/web-raw.md`）に任せる。手順の本文は `info-hive-wiki/skills/info-hive/references/web-raw.md` にある。エージェントはユーザーに聞けないので、判断が要るときは報告の `status: needs_user` と `question.kind` で返し、呼び出す側（ユーザーのモデル）がユーザーに聞いて、表のとおりに依頼の JSON を変えて呼び直す。エージェントは前の呼び出しを覚えていない。

この機能のブランチを作っているあいだに、main に #57（`wiki_fetch.py` が、途中の作業用の写しがあれば取得の前に再開する。0.14.1 までの版が書いた写しは続けず `old_work_dir` を報告する。出力に `source_sha256_of` を足す）が入った。#57 は `commands/ingest.md` の W2 と W3 に文を足したが、こちらのブランチでは W1〜W8 を `references/web-raw.md` に移してあるので、その文を `references/web-raw.md` に移し、エージェントの問いの種類に `old_work_dir` を足し、`needs_browser` に「本文が短いまま続ける」という答えの依頼の変え方を足した。

## 対象

- `docs/agent-runs/2026-11-14-wiki-web-raw-agent-review/merge-port.main-ingest.diff`: #57 が `commands/ingest.md` に加えた変更（移す元）
- `docs/agent-runs/2026-11-14-wiki-web-raw-agent-review/merge-port.submodule.diff`: こちらが `references/web-raw.md` と `CHANGELOG.md` に加えた変更（移した先）
- 現在の全文: `info-hive-wiki/skills/info-hive/references/web-raw.md`、`info-hive-wiki/agents/web-raw.md`
- 挙動の根拠: `info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py`（`has_old_work_dir`、`build`、`report_failure` の周り）、`info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py`（`resumable_fetch`、`old_version_work_dir`）
- 試験: `tests/wiki/test_web_raw_agent.py`

## 探してほしいこと

1. 移した文が、#57 の意味から変わったところ、落ちたところ（特に、`fetch_skipped`、`work_stage` が `fetched` と `frozen` のときの続け方、`old_work_dir`、`source_sha256_of` が `dom` のとき、`--force`）。
2. エージェントと呼び出す側の往復で、抜け出せない繰り返しや、行き先のない答え。`needs_user` のどの `question.kind` についても、ユーザーのありうる答え（取り直す、別版にする、上書きする、今のまま続ける、やめる）ごとに、表の依頼の変え方で呼び直したとき、`wiki_fetch.py` の実際の挙動（`--force`、`--html-file`、途中の写しの有無）で次に何が返るかをたどる。
3. `old_work_dir` を「終了コードごとの扱いより先に見る」としたことで、本当の誤り（取得の失敗、`--html-file` の誤り）が隠れる経路。
4. 「本文が短いまま続ける」を `conditions` の決まった文で渡す作りの穴（エージェントが見落とす、ほかの条件と取り違える、W8 の `check` や後の段と食い違う、など）。
5. 試験が見ていないために、上の欠陥が通ってしまうところ。

推測は推測と書く。スクリプトの挙動の主張は、コードの行を根拠に書く。
