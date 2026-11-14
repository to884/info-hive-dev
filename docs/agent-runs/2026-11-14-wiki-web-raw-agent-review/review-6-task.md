# 依頼: 5 回目のレビューと PR の指摘を直した版の敵対的レビュー

## 背景

wiki プラグイン 0.15.0 は、`/wiki:ingest` に URL を渡したときの raw の段（W1〜W8）を、`model: sonnet` のエージェント `wiki:web-raw`（`info-hive-wiki/agents/web-raw.md`）に任せる。手順は `info-hive-wiki/skills/info-hive/references/web-raw.md` にある。エージェントはユーザーに聞けず、前の呼び出しを覚えていない。判断が要るときは `needs_user` で返し、呼び出す側がユーザーに聞き、依頼の JSON を変えて呼び直す。

5 回目のレビュー（`docs/agent-runs/2026-11-14-wiki-web-raw-agent-review/review-5.md`、却下）の指摘を、`root-causes-5.md` の考えで直した。

- 呼び出す側の手順 4 に規則を足した。呼び直すたびに `fetch.force`、`fetch.html_file`、`fetch.page_url` を戻し、表や手順がその呼び直しで指示したときだけ設定する。`fetch.force` を `true` にするときは、`conditions` の「本文が短いまま続ける」を消す。
- `old_work_dir` は、終了コード 0 と 3 でだけ先に見る。終了コード 1 と 2 では、誤りを先に `failed` で返す。

また、PR（to884/info-hive-dev#103）の Codex のレビューの指摘で、実地の確かめのスクリプト `tests/wiki/check_web_raw_agent.py` を直した。直したのは、相対パスのプロジェクト、単一引用符のスクリプトのパス、書けなかった要約ページの 3 点である。

## 対象

- `docs/agent-runs/2026-11-14-wiki-web-raw-agent-review/review-6.submodule.diff`: `references/web-raw.md` の修正
- `docs/agent-runs/2026-11-14-wiki-web-raw-agent-review/review-6.tests.diff`: 確かめのスクリプトと試験の修正
- 前回の記録: `review-5.md`、`root-causes-5.md`（同じフォルダー）
- 現在の全文: `info-hive-wiki/skills/info-hive/references/web-raw.md`、`info-hive-wiki/agents/web-raw.md`、`tests/wiki/check_web_raw_agent.py`、`tests/wiki/test_web_raw_agent.py`
- 挙動の根拠: `info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py`、`info-hive-wiki/skills/info-hive/scripts/wiki_rawcheck.py`、`tests/wiki/test_wiki_web_check.py`（`test_dom_take_resumes_without_fetch` など）

## 探してほしいこと

1. 戻す規則が、5 回目の反例を本当に塞いだか。戻したことで、新しく壊れた往復がないか。たとえば、取り直すべき場面で取り直さない場面や、`needs_browser` で HTML を渡した呼び出しのあと、同じ呼び出しの中で続けたいときに困る場面である。`needs_user` の 4 つの種類と `warnings`、表示名の確かめ（手順 6）について、ユーザーのありうる答えごとに、呼び直したときに `wiki_fetch.py` が実際にどう動くかをたどる。
2. 「本文が短いまま続ける」を `conditions` に置く作りで、承認した本文と別の本文に承認が効いてしまう経路が、`--force` を戻す規則のもとでも残っていないか。`root-causes-5.md` は、ハッシュで結ぶ案を採らなかった理由を書いている。その理由が崩れるかを確かめる。
3. `old_work_dir` を終了コードで分けたことで、新しい行き止まりや取り違えがないか。
4. 確かめのスクリプトの修正の穴。`resolve()` とシンボリックリンクや大文字小文字の関係、引用符の扱いの残り（PowerShell の書き方、`&` での呼び出し、パスを変数に入れた形など）、要約ページがあるかの判定の誤り（前の取り込みの要約ページが残っている、など）を見る。
5. 試験が見ていないために、上の欠陥が通ってしまうところ。

推測は推測と書く。スクリプトの挙動についての主張は、コードの行を根拠にする。
