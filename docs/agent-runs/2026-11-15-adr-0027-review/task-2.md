# レビューの目的（2 回目）

`docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md` は、info-hive の wiki プラグイン（`info-hive-wiki`）で、YouTube の動画の字幕を取り込む設計の ADR（提案）である。1 回目のレビュー（`docs/agent-runs/2026-11-15-adr-0027-review/review-1.md`）の指摘を受けて、次の構造を変えた。この版を実装の根拠にしてよいかを判定する。

- トラックの種類を、名前の `-orig` ではなく、yt-dlp が返す字幕の URL の引数（`kind=asr`、`tlang` の有無、`lang`）で決める。同じ `lang` の `asr` のトラックは 1 つにまとめる。話された言語 L を `asr` のトラックの `lang` から取る。
- YouTube から来た文字（字幕、題名、チャンネル、チャプターの題名）は、frontmatter の引用符の中かフェンスの中にだけ置く（ADR-0020 と同じ）。区間の見出しはスクリプトの語だけにした。
- 同じ資料を、raw のバイト列ではなく `video_id`、`caption_track`、`source_sha256`（json3）で決める（ADR-0004、F-I15 と同じく原本のハッシュ）。
- yt-dlp が返した動画の ID を、URL の ID と照らす。
- `wiki_fetch.py` は、リダイレクトのあとの URL も YouTube なら止まる。
- 区間の分け方、同じ秒の並び、1 時間以上の時刻、取り込みの状態（`same` は raw の段だけ）、留保を関係するページに広げることを決めた。

1 回目で崩れた点が直ったかと、直しが新しい欠陥を生んでいないかを探す。1 回目と同じ指摘は、直っていなければそう書く。

## 読むべきもの

- 対象: `docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md`
- 1 回目のレビュー: `docs/agent-runs/2026-11-15-adr-0027-review/review-1.md`
- 前例と制約: `docs/adr/0004-raw-holds-translated-web-pages.md`、`docs/adr/0020-session-raw-is-rendered-once-from-decisions.md`、`docs/adr/0023-wiki-apply-uses-journal-and-per-wiki-lock.md`
- 要件: `llm-wiki-product-concept-and-requirements-ja.md` の F-I02、F-I03、F-I08、F-I15、S-01、O-14
- 今の取り込みの手順とスクリプト: `info-hive-wiki/commands/ingest.md`、`info-hive-wiki/skills/info-hive/references/ingest-workflow.md`、`info-hive-wiki/skills/info-hive/references/page-conventions.md`、`info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py`、`info-hive-wiki/skills/info-hive/scripts/wiki_pages.py`（サブモジュールが空なら、親のリポジトリ `C:/Works/info-hive-dev/info-hive-wiki/` の同じパスを読む）
- yt-dlp 2026.08.19 のソース（必要なら）: https://raw.githubusercontent.com/yt-dlp/yt-dlp/2026.08.19/yt_dlp/extractor/youtube/_video.py

yt-dlp の振る舞いについての主張は、ソースで確かめられるなら確かめ、確かめられなければ「推測」と書く。重大の指摘には、実装すれば必ず踏むものか、日常の使い方で起きうるものか、まれな時機や作為的な配置が要るものかを書き添える。
