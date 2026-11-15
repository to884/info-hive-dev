同梱の Markdown パーサーで、字幕中の `**x**`、`&copy;`、画像記法が文字どおりには表示されないことを再現しました。また、yt-dlp には元の動画から予告編へ処理を移す経路があり、取得結果の動画 ID を照合しない設計では、依頼と違う動画を取り込む余地があります。重大な欠陥と、明示的に受け入れられている制約を分けて判定をまとめます。
## 判定

**却下。確信度：高。** 元の自動字幕を自動翻訳と誤分類する仕様と、字幕の文字列を Markdown の構文として解釈させる仕様がある。重複判定も F-I08 と整合しておらず、現状のまま実装の根拠にはできない。

## 致命的・重大な欠陥

### 1. 【重大】`-orig` がない元の自動字幕を、明示指定でも取り込めない

**主張：** 「`automatic_captions` の `-orig` でないものは自動翻訳」という分類は、固定対象の yt-dlp の実装と食い違う。

**反例：** 自動字幕の言語が `translationLanguages` に含まれず、字幕トラックの `isTranslatable` が偽または欠落している入力。yt-dlp は元の字幕を裸の言語コードで登録するが、`-orig` は登録しない。ADR に従うと、この字幕は使用禁止になり、`--track` でも救済できない。

**根拠：** [ADR-0027 L42–43](/C:/Works/info-hive-dev/.claude/worktrees/adr-youtube/docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md:42)。yt-dlp 2026.08.19 の `YoutubeIE._real_extract` は、該当経路で `-orig` の追加だけを `isTranslatable` の条件下に置き、裸のコードでの追加は無条件に行う。**ソースで確認済み。実動画での発生頻度は未検証。** [固定版の実装](https://raw.githubusercontent.com/yt-dlp/yt-dlp/2026.08.19/yt_dlp/extractor/youtube/_video.py)

### 2. 【重大】字幕をそのまま Markdown に埋め込むと、原文にない構造になる

**主張：** NFC 以外の文字を変えずに `[時刻] 本文` として書く規則は、字幕を文字どおりに保存・表示する規則になっていない。

**再現：** 字幕本文を次にする。

```text
**x** &copy; ![slide](https://example.org/p.png)
```

ADR の出力を同梱の `wiki_pages.new_parser()` で描画すると、`x` は強調、`&copy;` は `©`、画像記法は外部画像になることを再現した。また、隣接する字幕行は、別々の段落ではなく一つの段落として解析された。

**根拠：** [ADR-0027 L47](/C:/Works/info-hive-dev/.claude/worktrees/adr-youtube/docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md:47)、[同梱パーサーの設定](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:391)。逐語の本文を動的な長さのフェンスで囲む [ADR-0020 L22](/C:/Works/info-hive-dev/.claude/worktrees/adr-youtube/docs/adr/0020-session-raw-is-rendered-once-from-decisions.md:22) とも、この点で異なる。**再現済み。スクリプト実行や XSS が起きるとの主張ではない。**

### 3. 【重大】依存の更新だけで、変更のない字幕が別資料版になる

**主張：** 「同じ字幕なら同じ raw」は成立しない。raw に取得器の版を含め、その全バイト列を重複判定に使うためである。

**再現：**

1. ある動画を取り込む。
2. 別の動画の取得障害を直すため、yt-dlp の固定版を上げる。
3. 元の動画を、同じ字幕・題名・チャプターで取り直す。

`fetched_by` が変わるので raw は必ず不一致になる。字幕もメタデータも変わっていないのに、別版の作成を問い合わせる。

**根拠：** [ADR-0027 L35、L50–51](/C:/Works/info-hive-dev/.claude/worktrees/adr-youtube/docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md:50)。F-I08 は同じ内容の重複作成を避ける要件であり、[ADR-0004 L33](/C:/Works/info-hive-dev/.claude/worktrees/adr-youtube/docs/adr/0004-raw-holds-translated-web-pages.md:33) も変換結果の違いを原資料の変化と取り違えない理由を明記している。ADR-0027 の要件変更予定は F-I03 を扱うが、この F-I08 の変更は明示していない。**バイト列の不一致は再現済み。要件との食い違い。**

### 4. 【重大】yt-dlp が別動画へ解決した場合、依頼した動画の字幕だと保証できない

**主張：** 入力 URL の動画 ID と取得結果の ID を照合する条件がなく、公開状態の検査だけでは別動画への置き換わりを検出できない。

**反例：** YouTube の応答に `trailerVideoId` がある動画。固定版の抽出器は、その ID への `url_result` を返し、`YoutubeDL` の通常処理は移動先を抽出する。移動先が字幕付きの公開予告編なら、ADR の公開状態と字幕の条件を満たしうる。依頼した本編の代わりに予告編を取り込んでも、止まる条件がない。

**根拠：** [ADR-0027 L38、L41、L46、L50](/C:/Works/info-hive-dev/.claude/worktrees/adr-youtube/docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md:41)、固定版の [`YoutubeIE._real_extract`](https://raw.githubusercontent.com/yt-dlp/yt-dlp/2026.08.19/yt_dlp/extractor/youtube/_video.py) と [`YoutubeDL.process_ie_result`](https://raw.githubusercontent.com/yt-dlp/yt-dlp/2026.08.19/yt_dlp/YoutubeDL.py)。**移動する経路はソースで確認済み。字幕付き予告編という条件は仮定で、実動画では未再現。**

## 崩れる前提

| 暗黙の前提 | 崩れる条件 |
| --- | --- |
| `-orig` の有無で元字幕と自動翻訳を区別できる | yt-dlp が元字幕を裸の言語コードだけで登録する |
| 字幕を変えずに書けば、Markdown でも逐語になる | 字幕に強調、画像、リンク、文字参照などの構文が含まれる |
| 取得時刻を外せば、同じ字幕から同じ raw ができる | `fetched_by`、題名、チャンネル名、チャプターなどが変わる |
| yt-dlp の取得結果は入力動画そのものである | 抽出器が予告編など別 ID への結果を返す |
| チャプター開始時刻に対応する字幕行がある | チャプターが無音区間や字幕イベントの途中から始まる |
| `language` は動画固有の言語である | 未処理の抽出結果を使う場合や、選択された音声形式に依存する場合。固定版では形式選択結果が最上位へ反映される。[実装](https://raw.githubusercontent.com/yt-dlp/yt-dlp/2026.08.19/yt_dlp/YoutubeDL.py) |

## 見落としと軽微な問題

- **【軽微】チャプターの挿入位置が未定義。** 字幕が `00:59` と `01:03`、チャプター開始が `01:00` の場合、「その開始の時刻の行」は存在しない。10 分ごとの見出しも同様である。境界をまたぐ字幕、同じ秒の複数イベント、1 時間以上の見出し表記も決まっていない。[ADR-0027 L47–48](/C:/Works/info-hive-dev/.claude/worktrees/adr-youtube/docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md:48)

- **【軽微】地域コードの照合は片方向。** `L=en-US`、投稿者字幕が `en` の場合は一致せず停止する。一方、`L=en` で `en` と `en-US` がある場合は、完全一致があっても複数候補として停止する。`--track` で回避できるので、取り込み不能とは判定しない。[ADR-0027 L43](/C:/Works/info-hive-dev/.claude/worktrees/adr-youtube/docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md:43)

- **【軽微】raw 保存後の中断からの再開が曖昧。** raw を保存し、要約ページを書く前に中断した場合、「一致すれば何もしない」が raw の書き込みだけを指すのか、取り込み全体を指すのか決まっていない。後者なら未完了の取り込みが放置される。前例は、raw の一致と取り込み完了を明確に分けている。[ADR-0027 L51](/C:/Works/info-hive-dev/.claude/worktrees/adr-youtube/docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md:51)、[ADR-0020 L27](/C:/Works/info-hive-dev/.claude/worktrees/adr-youtube/docs/adr/0020-session-raw-is-rendered-once-from-decisions.md:27)

- **【軽微】URL の守りがリダイレクト先まで及ぶか未規定。** 現行 `wiki_fetch.py` はリダイレクトを追う。入口だけを判定する実装では、別ホストの短縮 URL から YouTube に転送される場合に、下部リンクだけの raw を再び作れる。**将来実装についての条件付きの指摘であり、発生済みとはしていない。** [ADR-0027 L40](/C:/Works/info-hive-dev/.claude/worktrees/adr-youtube/docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md:40)、[現行の転送処理](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py:100)

- **【軽微】ASR の留保を関連ページへ引き継ぐ範囲が不明。** 留保と `caption_kind` の転記は要約ページに指定されているが、関連するエンティティ・コンセプトの更新は通常手順に任せている。型付きエッジを作らなくても、留保のない本文として誤りが広がる余地は残る。[ADR-0027 L53–55](/C:/Works/info-hive-dev/.claude/worktrees/adr-youtube/docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md:53)

## 検証した事実

- **一致：** 現行の取り込み手順は HTTP/HTTPS を Web ページへ送る。動画分岐を先に置く必要性は、リポジトリの記述と一致する。
- **食い違い：** `-orig` 以外をすべて自動翻訳とする説明は、固定版のソースと一致しない。
- **一致：** Shorts のパスと限定公開は ADR の許可範囲に入る。yt-dlp 側にも Shorts の認識と `unlisted` の扱いがある。実動画の取得は試していない。
- **一致：** `language` 欠落時の停止は明記されている。欠落を別言語で推測して埋める仕様ではない。
- **一致：** 原語の引用は既存の引用規約と整合する。グラフの証拠照合先は raw ではなくソースページ本文である。[引用規約](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/page-conventions.md:177)、[照合処理](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_lint.py:356)
- **確かめられず：** json3 の日をまたいだバイト列の安定性、クラウド IP、各種制限下での取得成功率。ADR 自身も保証していない。

## 崩せなかった点

- yt-dlp の固定依存は、標準ライブラリを「優先する」という CONTRIBUTING の規則に、例外の理由を明示している。禁止規則への違反とはいえない。
- Python の範囲を既存の uv スクリプトに合わせる決定は、ADR-0018 と別ブランチの ADR-0026 の関係を踏まえている。独立した範囲の矛盾は見つからなかった。
- 取得日時を要約ページに記録すること自体は、記録場所を限定していない F-I03 に反しない。raw に日時がないことだけを欠陥とはできない。
- 原語 raw、短い原語引用、ASR から型付きの意味エッジを作らない方針は、既存の証拠規則と両立する。
- json3 原本を残さずハッシュを記録する割り切りは、原文 HTML を残さない ADR-0004 に前例がある。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
