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
| CQRS（英語、0.16.1 の版。2026年11月15日） | 15 / 15 | `claude-opus-5-5` | `claude-sonnet-5-5` | 訳: Claude Sonnet 5.5、補足: Claude Sonnet 5.5 | 350 秒 | 1.85 USD（Opus 1.65、Sonnet 0.20） |
| CQRS（英語、0.18.1 の版。2026年11月15日） | 19 / 19 | `claude-opus-5-5` | `claude-sonnet-5-5` | 訳: Claude Sonnet 5.5、補足: Claude Sonnet 5.5 | 203 秒 | 1.48 USD（Opus 1.29、Sonnet 0.20） |

3 行目は、main の 0.14.1 と #57（`wiki_fetch.py` の取得の前の再開）を取り込み、取り直したら W3 に戻る決まりを足した版（`info-hive-wiki` の `fix/web-raw-w3-after-fetch`）で動かした。結果は `trial-0161-cqrs.json` にある。この修正の版の番号は、main が先に進んだので、0.17.1、0.18.1 と付け直した。そのあと、8 回目から 13 回目のレビューで確かめのスクリプトを直し、3 件とも確かめ直した（2026年11月15日。結果の JSON は確かめ直した結果に差し替え、費用と時間は取り込んだときの値を残した）。

13 回目のレビューのあと、確かめのスクリプトは、W8 の終わりを `check --finish --json` の出力だけで決めるようにした。文字の出力には、ページの本文（誤りの詳細）がそのまま出て、検査の結果の行と見分けられないからである。合わせて、プラグインの手順の W8 に `--json` を足し、文字の出力の値の中の改行のあとを字下げした（0.18.1）。14 回目のレビューのあと、記録の JSONL を LF だけで分け、読めない行があれば不合格にした。さらに、Sol の修正案との総括（`fix-proposal-14/synthesis.md`）で、読めない証拠（メタデータ、結果のない `check --finish` の呼び出し、途中で切れた check の JSON）があれば、違反がないとは言えないとして不合格にした。15 回目のレビューのあと、check の JSON の印をどれも説明する形にし、メインの Agent の呼び出しを記録のファイルと agentId で結んだ（`root-causes-15.md`）。確かめ直すと、1 行目と 2 行目は 22 / 22 で通った（W8 を `--json` で動かしていた）。3 行目は 20 / 21 で、W8 の項目だけが通らない（その版の手順には `--json` がなく、エージェントは W8 を文字の出力で終えた。raw の frontmatter の `translated_by` は Claude Sonnet 5.5 だった）。

4 行目は、W8 に `--json` を足した 0.18.1 の手順で、取り込み直したものである。結果は `trial-0181-cqrs.json` にある。取り込んだときは 19 項目、15 回目のあとの確かめ直しでは 22 項目がすべて通り、エージェントが W8 を `--json` で終え、訳と補足の表示名を `check` の結果から確かめられた。

時間は `claude -p` の `duration_ms` である。

確かめた項目（どちらのページも通った）:

- メインが Agent ツールで `wiki:web-raw` を呼び、`model` の引数を渡していない。
- メインの応答のモデルは Opus、エージェントの応答のモデルは Sonnet。
- エージェントが `wiki_fetch.py` と `freeze` の出力を受け取り、W8 の `check --finish` を自分で動かして通った。メインは raw と画像に Edit と Write で書いていない。メインのコマンドの一覧と、結果の形から見えるメインの実行（なかった）も読んだ。ほかの担当が動かさなかったことは、記録からは示せない（2026年11月15日に確かめのスクリプトの主張を狭め、合否を決めない一覧に移した。直したスクリプトで確かめ直しても、2 件とも通った）。
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

## 調べ直し（4 回目のレビューのあと）

4 回目のレビュー（`docs/agent-runs/2026-11-14-wiki-web-raw-agent-review/review-4.md`）のあと、実地の確かめのスクリプトを、Bash のコマンドの中の書き込みで合否を決めない形に改めた（`root-causes-4.md`）。改めたスクリプトで 2 回の記録を調べ直すと、どちらも 14 項目とも通った（`trial-cqrs.json`、`trial-bloom.json`）。一覧（`bash_to_review`）に出たメインのコマンド（CQRS 3 件、ブルームフィルタ 4 件）を読むと、どれも読み取り（`ls`、`cat`、`sed -n`）と `log.md` への追記で、raw に書いたものはなかった。エージェントのコマンドは、一覧に出なかった。
