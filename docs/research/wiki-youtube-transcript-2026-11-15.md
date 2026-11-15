# YouTube の動画の字幕を wiki に取り込む方法の選択肢（2026-11-15）

YouTube の動画の字幕（トランスクリプト）を取り、要約を wiki に取り込む方法を調べ、選択肢を並べた。字幕の本文の取り方（選択肢 A）と、プラグインへの組み込み方（選択肢 B）を分けて整理する。設計は決めていない。決めるときは ADR にする。

## 結論

- **今の `/wiki:ingest` に YouTube の URL を渡しても、字幕は取れない。** ページは `text/html` なので Web ページの経路（`wiki_fetch.py`）に進み、raw にはページの下のリンク（概要、プレスルーム、著作権…）しか残らなかった（「手元で確かめたこと」の 1）。
- **今すぐ使える方法は、字幕の本文を `.md` か `.txt` にして `raw/` に置くことだけである。** 文字起こしとして取り込める（`ingest-workflow.md` の手順 1）。
- **作るなら、yt-dlp で字幕を取るスクリプト（A2）を作り、取り込みに動画の分岐を足す（B2）のが候補になる。** 投稿者の字幕、自動字幕、自動翻訳を区別して取れ、時刻とチャプターも取れる。字幕のない動画は、利用者が求めたときだけ、音声を手元で文字に起こす方法（A7）で補う。
- **公式の YouTube Data API（A8）は、他人の動画には使えない。** `captions.download` は動画を編集する権限を求める。

## 手元で確かめたこと

この節の結果は、この PC（Windows 11、自宅の回線）で、1 本の公開動画を 1 回ずつ試したものである。検証の環境での観測であり、利用者の環境での動きを保証しない。

1. **今の `wiki_fetch.py` の動き。** `wiki_fetch.py --no-images --json <YouTube の URL>` は成功した。警告は「article と main がないので、段落の多い要素を本文と推定した」で、`raw/yt.md`（1,324 バイト）の本文は、題名とページの下のリンクだけだった。字幕は入らない。
2. **yt-dlp 2026.08.19 で字幕を取る。** `--skip-download --list-subs` で、投稿者の字幕（`ja`、`en`）と自動字幕（`en`、`ja` など）が出た。`--write-subs --write-auto-subs --sub-format json3` で、投稿者の字幕（`ja`、`en`）を取れた。`--write-auto-subs` だけで、自動字幕（`en-orig`）と自動翻訳（`ja`）を取れた。PO Token は求められなかった。
3. **yt-dlp の警告。** 実行のたびに「No supported JavaScript runtime could be found. Only deno is enabled by default」と出た。JS の実行環境がないと、YouTube からの取得は非推奨になり、一部の形式が欠けることがある。
4. **自動字幕の質。** 英語の自動字幕（`en-orig`）には、句読点の位置のずれと聞き違いがあった（例: 「I feel commitments from what I'm thinking of」）。

自動字幕しかない日本語の動画、クラウドの IP、続けて何十本も取る場合は、試していない。

## 選択肢 A: 字幕の本文の取り方

| # | 方法 | 利用者が用意するもの | 強み | 弱み・危うさ |
| --- | --- | --- | --- | --- |
| A1 | 動画の「文字起こし」の欄から手で写す | なし | コードがいらない。今すぐ使える | 手間がかかる。時刻と字幕の種類が残らない |
| A2 | yt-dlp の `--skip-download --write-subs --write-auto-subs --sub-format json3` | yt-dlp、推奨の JS 実行環境（deno） | 投稿者の字幕、自動字幕、自動翻訳を区別して取れる。時刻とチャプターも取れる。保守が活発 | 公式でない取り方なので、YouTube の変更で壊れることがある。一部の利用元は字幕に PO Token を求め、取れない言語は飛ばされる |
| A3 | Python の youtube-transcript-api（1.2.5） | Python の依存 1 つ | 軽い。uv の inline の依存に載せやすい | 公式の API ではない。クラウドの IP は弾かれやすい。自宅の回線でも、速く何十件も取ると制限される |
| A4 | ブラウザ（Claude in Chrome など）で文字起こしの欄を読む | ブラウザの拡張 | ログインした状態で読める | 遅い。画面の作りに依存する。自動化に向かない |
| A5 | 第三者の MCP サーバーやホスト型の API（TubeTranscript など） | npm、または API キーと月額の費用 | 導入が 1 行で済む。字幕のない動画を文字に起こすサービスもある | 外部に頼る。保守の状態がまちまち。動画の URL を外部に送る |
| A6 | Gemini API に YouTube の URL を渡す | Gemini の API キー | 映像と音声から、要約まで一度に作れる | 公開動画だけ。無料枠は 1 日 8 時間分。字幕そのものを返す API ではなく、raw の「原本」にならない |
| A7 | 音声を落とし、手元で文字に起こす（faster-whisper、Kotoba-Whisper、ReazonSpeech など） | yt-dlp、ffmpeg、できれば GPU | 字幕のない動画にも使える。日本語の精度で道具を選べる | 重く、時間がかかる。音声を落とすことは YouTube の規約に関わる（判断は利用者に委ねる） |
| A8 | 公式の YouTube Data API の `captions.download` | OAuth | 公式の取り方 | 他人の動画では使えない。動画を編集する権限が必要で、ないと 403 になる。自分のチャンネルの動画でしか使えない |

### 取り方ごとの補足

- **A2 の PO Token。** yt-dlp の wiki は、字幕の要求を PO Token が要る場面の 1 つに挙げ、Token は動画ごとに作り直す必要があるとしている。手で取り出す方法は勧めておらず、PO Token Provider のプラグイン（BgUtils など）を勧めている。字幕の PO Token への対応は #13234 で入った。
- **A3 の弾かれ方。** PyPI のページは、IP を弾かれた（`RequestBlocked`、`IpBlocked`）ときの回避策として、住宅用のプロキシを挙げている。弾かれる条件と回避策を書いた記事の多くは、プロキシやホスト型 API の販売元によるもので、裏付けは取っていない。
- **A6 の新しい機能。** 長い動画の必要な場面だけを、映像、音声、字幕から選んで調べる「エージェント型の動画理解」が出たという報道がある。根拠は二次情報 1 件だけで、Google の文書では確かめていない。
- **A7 の道具の選び方。** 2026 年の解説記事は、無料で済ませるなら faster-whisper か WhisperX、日本語の精度を上げるなら Kotoba-Whisper か ReazonSpeech、と整理している。Kotoba-Whisper の model card にある速度の数値は、古い計測で、ハードウェアも違う（Apple M2 Pro）。L40S で日本語の音声認識を比べた記事では、NVIDIA の Parakeet の結果が良かった。速さと精度は、実際の音声で測る必要がある。

## 選択肢 B: プラグインへの組み込み方

| # | 形 | 内容 |
| --- | --- | --- |
| B1 | 文書だけ | 手順書に「A1 か A2 で本文を作り、`raw/` に置く」と書く。コードは足さない |
| B2 | 取り込みに動画の分岐とスクリプトを足す | URL が YouTube なら、Web ページの経路ではなく、新しいスクリプト（仮に `wiki_youtube.py`）に送る。スクリプトが A2 か A3 で字幕を取り、時刻付きの Markdown を raw に書く |
| B3 | B2 とエージェント | `wiki:web-raw` と同じ形で、句読点を補う、整える、訳す、といった段をエージェントに任せる |
| B4 | 別のプラグイン | 文字起こし（A7）のような重い処理だけを、`rag` と同じく別のプラグインにし、永続ジョブで動かす |

## 決めておくこと

- **raw の範囲。** 自動字幕に句読点を補ったものや訳文を raw とみなすか。ADR-0004 は、Web ページの訳文と画像の補足を raw に置く例外を決めており、これが前例になる。元の字幕（json3 など）を残すかも決める。
- **frontmatter に書く項目。** URL、`video_id`、字幕の種類（投稿者の字幕、自動字幕、自動翻訳）、言語、元の字幕の SHA-256、取得に使った道具と版。キーは英語にする（計画の方針 B）。
- **引用と分割。** 時刻を残せば、`?t=` 付きのリンクで出典を示せる。yt-dlp のメタデータにあるチャプターは、長い動画を分けて読むときの区切りに使える。
- **利用者に求める依存。** yt-dlp、deno、ffmpeg、GPU、API キーのどこまでを求めるか。この PC に yt-dlp、ffmpeg、CUDA があるのは検証の環境の事情で、仕様の前提にしない。
- **壊れやすさと規約。** A2、A3、A5 は公式でない取り方で、取れなくなる、IP を弾かれる、ということが起こりうる。失敗したときは、推測で埋めず、理由をそのまま伝える。音声を落とす A7 は、YouTube の規約に関わることを利用者に示す。

## 出典

- [youtube-transcript-api（PyPI）](https://pypi.org/project/youtube-transcript-api/)
- [yt-dlp の PO Token のガイド](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide)
- [yt-dlp の字幕の PO Token 対応のコミット（#13234）](https://github.com/yt-dlp/yt-dlp/commit/32ed5f107c6c641958d1cd2752e130de4db55a13)
- [YouTube Data API の captions.download](https://developers.google.com/youtube/v3/docs/captions/download)
- [YouTube Data API のエラー](https://developers.google.cn/youtube/v3/docs/errors?hl=en)
- [Gemini API の動画理解](https://ai.google.dev/gemini-api/docs/video-understanding?hl=ja)
- [tbreak の Gemini の動画理解の記事（二次情報）](https://tbreak.com/gemini-video-understanding-ai-studio/)
- [Kotoba-Whisper v2.0 の faster-whisper 版](https://huggingface.co/kotoba-tech/kotoba-whisper-v2.0-faster)
- [L40S での日本語の音声認識の比較（Classmethod）](https://dev.classmethod.jp/articles/japanese-asr-l40s-fleurs-benchmark/)
- [Whisper の代わりになる日本語の音声認識（2026）](https://aipicks.jp/mag/whisper-alternatives-japanese-stt-2026)
- [hancengiz/youtube-transcript-mcp](https://github.com/hancengiz/youtube-transcript-mcp)
- [youtube-transcript-api が弾かれる問題の記事（DEV、販売元による記事）](https://dev.to/lmslay/youtube-transcript-api-requestblocked-on-your-server-what-actually-works-in-2026-1pak)
