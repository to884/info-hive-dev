# raw の段を任せるエージェントを、実際の取り込みで確かめた記録（2026-11-14）

設計の 3 版（[wiki-web-raw-agent-2026-11-14.md](../plans/wiki-web-raw-agent-2026-11-14.md)）の試作（`info-hive-wiki` の `feature/web-raw-agent`）で、`/wiki:ingest` を実際に動かした。どちらも、`init_wiki.py` で作った一時の wiki で、次のように動かした（Claude Code 2.1.316、Windows 11）。

```text
claude -p "/wiki:ingest <URL> 人と話し合わないまとめての取り込みとして行う。グラフ層の手順は飛ばす。" \
    --plugin-dir <info-hive-wiki> --model opus --allowedTools "Bash Read Edit Write Glob Grep Agent" --output-format json
```

セッションの記録（メインと、`subagents/` の下のエージェントの記録）を、`tests/wiki/check_web_raw_agent.py` で調べた。結果の JSON は `docs/agent-runs/2026-11-14-wiki-web-raw-agent-review/trial-cqrs.json` と `trial-bloom.json` にある。

## 結果

| ページ | 確かめた項目 | メイン | エージェント | raw の名前 | 時間 | 費用（`advisor` を除く） |
| --- | --- | --- | --- | --- | --- | --- |
| CQRS（英語） | 14 / 14 | `claude-opus-5-5` | `claude-sonnet-5-5` | 訳: Claude Sonnet 5.5、補足: Claude Sonnet 5.5 | 248 秒 | 1.92 USD（Opus 1.73、Sonnet 0.19） |
| ブルームフィルタ（日本語の Wikipedia） | 14 / 14 | `claude-opus-5-5` | `claude-sonnet-5-5` | 訳: なし、補足: Claude Sonnet 5.5 | 197 秒 | 1.61 USD（Opus 1.46、Sonnet 0.15） |

時間は `claude -p` の `duration_ms` である。

確かめた項目（どちらのページも通った）:

- メインが Agent ツールで `wiki:web-raw` を呼び、`model` の引数を渡していない。
- メインの応答のモデルは Opus、エージェントの応答のモデルは Sonnet。
- `wiki_fetch.py` と `freeze` は、エージェントだけが実行した。メインは raw と画像に書いていない。
- エージェントは、wiki のページ、`index.md`、`log.md` に書いていない。メインが要約ページ、`index.md`、`log.md` を書いた。
- エージェントの出力に、要約ページの文の並び（40 文字。raw にもある並びは除く）がない。エージェントを呼ぶまでのメインの出力に、raw の文の並びがない。
- raw があり、log に分担のサブ行（「raw: `wiki:web-raw` に任せた（報告したモデル: Claude Sonnet 5.5）。訳: …、補足: …」）があり、作業用の写しが消えた。

## 分かったこと

- メインは、`SCHEMA.md` から raw に関わる条件（画像の置き場所）を読み、依頼の `conditions` に入れていた。エージェントは、`SCHEMA.md`、参照文書の順に読み、W1〜W8 のとおりに進め、決まった形の報告を返した（CQRS では、著者の顔写真を飾りとして消し、残った 2 枚に補足を書いた。`check --finish` は誤りも警告もなかった）。
- エージェントは、この環境では裏で動き（`run_in_background`）、報告は通知でメインに届いた。
- 両方の取り込みで、メインは `advisor`（この環境にある、Fable 5.1 を使う相談の道具）を呼んだ。その費用（CQRS 2.82 USD、ブルームフィルタ 1.42 USD）は、ユーザーの環境のものなので、上の表から除いた。
- 前の試行（[sonnet-trial-2](../agent-runs/2026-11-13-wiki-web-ingest-check-review/sonnet-trial-2.md)。取り込み全体を Sonnet で行った）は、CQRS 166 秒、ブルームフィルタ 145 秒だった。分けたほうが時間はかかった。後段を Opus で行うためで、比べたのは時間だけである（前の試行は費用を記録していない）。
- 試作の確かめで、試験のスクリプトの誤りが 3 つ見つかり、直した（Bash の読み取りのコマンドを raw への書き込みと見ていた、原文の言葉を文の受け渡しと見ていた、Bash で `log.md` に書いたのを数えていなかった）。
- 3 回目のレビュー（`docs/agent-runs/2026-11-14-wiki-web-raw-agent-review/review-3.md`）で、試験のスクリプトが違反を見落とす穴（Bash の中の Python の書き込み、メインの文の出力と 2 回目以降の依頼）が見つかり、塞いだ。塞いだスクリプトで 2 回の記録を調べ直しても、14 項目とも通った（`trial-cqrs.json`、`trial-bloom.json` は調べ直した結果）。

## 確かめていないこと

- 文を考えたモデル。試験が見つけるのは、長い文の並びの受け渡しだけである。
- 本文が取れないページ（`needs_browser`）、同じスラッグの別版（`existing_differs`）、警告が残る場合（`warnings`）の流れ。
- 組織の許可リストやフォールバックの連鎖で、エージェントが Sonnet 以外で動く場合。
