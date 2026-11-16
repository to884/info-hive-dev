# ADR-0027 の実装（wiki 0.22.0）の敵対的レビュー

## 目的

`docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md`（承認）を、info-hive-wiki のプラグインに実装した。実装が ADR の決定を満たし、ADR が防ごうとした失敗（字幕による raw の構造の偽造、別の動画や自動翻訳の取り違え、同じ資料の二重の raw、印と定義のすり抜けによる confidence の水増し、YouTube の URL が Web ページの経路で raw になること）を本当に防いでいるかを崩してほしい。

## 対象

新しいファイル（未追跡なので差分に入っていない。全文を読む）:

- `info-hive-wiki/skills/info-hive/scripts/wiki_youtube.py`（PEP 723 で yt-dlp を固定。inspect、write、verify、define）
- `info-hive-wiki/skills/info-hive/scripts/wiki_captions.py`（raw の生成と読み取り、印と定義の読み取り、照合、confidence の計算。lint と共有）
- `info-hive-wiki/skills/info-hive/scripts/wiki_youtube_url.py`（URL の判定。wiki_fetch.py と共有）
- `tests/wiki/test_wiki_youtube.py`

既存のファイルの変更（`docs/agent-runs/2026-11-16-adr-0027-impl-review/wiki-diff-1.patch` にサブモジュールの差分がある）:

- `wiki_fetch.py`（YouTube の URL の拒み、終了コード 4）、`wiki_lint.py`（`caption_corrections`）、`wiki_mcp_server.py`、`wiki_text.py`（別名 `確かさ`）
- `commands/ingest.md`（V1〜V10）、`references/ingest-workflow.md`（「YouTube の動画」の節）、`references/query-workflow.md`（手順 5b の上限と上げる方法の行）、`references/page-conventions.md`、`references/web-raw.md`、`SKILL.md`、`CHANGELOG.md`

## 確かめてほしいこと（これに限らない）

1. 字幕、題名、チャンネルの名前、チャプターの題名から、raw の行（`L<n> [時刻]`）、区間の見出し、チャプターの題名の行、フェンスを偽れないか。`parse_raw` が偽の構造を受け入れないか。
2. トラックの判定と選び方が ADR の表のとおりか。自動翻訳や別の言語のトラックを取り違える入力がないか。
3. `inspect` が本当にディスクに何も書かないか。`write` が上書きせず、同じ資料をスラッグによらず見つけ、`different` と `slug_taken` を取り違えないか。競合の扱い。
4. `verify` と lint の照合（ADR の (1)〜(5)）をすり抜けて、定義のない訂正、根拠の付け替え、confidence の水増しができないか。印の直前の末尾の照合（バックスラッシュのエスケープ、語の途中の切れ目の文字の種類）に穴がないか。印を数えない場所（コード、引用）を使って、照合を避けられないか。
5. 関係するページの印の解決（`[[要約ページ]]`）、分割した要約ページ、親の要約ページの決め方に穴がないか。
6. `wiki_fetch.py` の拒みに漏れ（リダイレクトの先、`--page-url`、途中の取り込みの再開、画像の取得への影響）がないか。
7. 手順書（V1〜V10、ingest-workflow、手順 5b）と実装が食い違わないか。モデルが手順どおりに動いて、ADR の決定に反する結果になる箇所がないか。
8. 字幕の URL（`ip`、`signature`）が、raw、標準出力、エラーのメッセージに漏れる経路がないか。

試験は `python -X utf8 -B -m unittest tests/wiki/test_wiki_youtube.py` で動く（ネットにつながない）。
