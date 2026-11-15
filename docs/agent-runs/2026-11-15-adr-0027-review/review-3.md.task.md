# レビューの目的（3 回目）

`docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md` は、info-hive の wiki プラグイン（`info-hive-wiki`）で、YouTube の動画の字幕を取り込む設計の ADR（提案）である。この版を実装の根拠にしてよいかを判定する。

2 回目のレビュー（`docs/agent-runs/2026-11-15-adr-0027-review/review-2.md`）の指摘を受けて、次を変えた。

- 同じ資料を、`video_id` と `source_sha256`（json3 のバイト列）の 2 つだけで決める。トラックの名前は同一性に使わない。
- `inspect` は、スラッグによらず、`<RAW_ROOT>` の直下の `.md` のうち `video_id` が同じものをすべて挙げ、`same` か `different` かを返す。指定したスラッグが別の動画の raw なら `slug_taken` を返す。
- 題名とチャプターを別版にしない理由を、「根拠が変わらない」から「主張の根拠になる字幕が同じなら同じ資料とする」に改めた。
- 同じ時刻の行が 2 つ以上あるときは、根拠の位置に行の短い引用を添える。
- `wiki_fetch.py` の取得の処理を、リダイレクトの先を本文を読む前に確かめる形に変えると「影響」に書いた。

1 回目と 2 回目で崩れた点が直ったかと、直しが新しい欠陥を生んでいないかを探す。前の回と同じ指摘は、直っていなければそう書く。

## 読むべきもの

- 対象: `docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md`
- 前の回のレビュー: `docs/agent-runs/2026-11-15-adr-0027-review/review-1.md`、`review-2.md`
- 前例と制約: `docs/adr/0004-raw-holds-translated-web-pages.md`、`docs/adr/0020-session-raw-is-rendered-once-from-decisions.md`、`docs/adr/0023-wiki-apply-uses-journal-and-per-wiki-lock.md`
- 要件: `llm-wiki-product-concept-and-requirements-ja.md` の F-I02、F-I03、F-I08、F-I15、S-01、O-14
- 今の取り込みの手順とスクリプト: `info-hive-wiki/commands/ingest.md`、`info-hive-wiki/skills/info-hive/references/ingest-workflow.md`、`info-hive-wiki/skills/info-hive/references/page-conventions.md`、`info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py`（サブモジュールが空なら、親のリポジトリ `C:/Works/info-hive-dev/info-hive-wiki/` の同じパスを読む）
- yt-dlp 2026.08.19 のソース（必要なら）: https://raw.githubusercontent.com/yt-dlp/yt-dlp/2026.08.19/yt_dlp/extractor/youtube/_video.py

yt-dlp の振る舞いについての主張は、ソースで確かめられるなら確かめ、確かめられなければ「推測」と書く。重大の指摘には、仕様の矛盾か欠落で実装すれば必ず踏むもの（A）か、日常の使い方で起きうるもの（B）か、まれな時機や名前によるもの（C）か、作為的な配置が要るもの（D）かを書き添える。
