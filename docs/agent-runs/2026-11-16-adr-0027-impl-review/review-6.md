## 判定

**却下。確信度：高。** 同じ表示の語でも Unicode の表現を変えると、本文を直していない訂正が verify と lint を通る。また、走査対象外のファイルを要約ページとして受理する問題と、明示した投稿者字幕を選べない問題を再現した。

## 致命的・重大な欠陥

### 1. 【重大】結合文字で語の途中の切れ目を隠せる

raw を `uploaded`・200行とし、L1 に `ドヨタ`、L2 に `ヨタ` を置く。親の要約ページに `confidence: "high"` と次の定義を書く。

```markdown
- L1-1: 字幕 `ドヨタ` を `ヨタ` に訂正（根拠 caption:L2）
```

本文の「ド」を、`ト` と結合濁点 U+3099 に分ける。次の Python 文字列が再現用の本文である。

```python
body = "ト\u3099ヨタ〔訂正 L1-1〕"
```

この語を NFC にすると、raw の元の語 `ドヨタ` と一致する。本文は訂正した語 `ヨタ` になっていないが、結果は以下だった。

- verify：**終了コード0、`findings: []`**
- lint：**`caption_corrections: []`**
- 重み1、confidence `high`

同じ本文を合成済みの `ドヨタ〔訂正 L1-1〕` にすると、`mark_tail` になる。英字でも `ÁBC` → `BC` の定義に対し、本文を `A\u0301BC` にすると同じすり抜けが起きた。

原因は、語の直前の**1コードポイントだけ**を分類すること。分解表現では結合濁点やアクセントを取り出し、カタカナ・英字の続きと認識しない。

根拠：[wiki_captions.py:499](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:499)、[文字種の判定:471](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:471)。語の途中の切れ目を拒む [ADR-0027:101](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md:101) と食い違う。

### 2. 【重大】走査対象外のファイルを、存在する要約ページとして検証できる

正常な `raw/a.md` を置き、要約ページは存在しない状態にする。正常な要約の全文を用意し、次のように渡す。

```text
verify --wiki <W> --raw-root <R> --slug a \
  --page ".wiki-cache/a.md=<用意した要約ファイル>" --json
```

要約は `type: "source"`、`raw: "raw/a.md"`、raw と一致する `caption_kind` と `confidence` を持つものとする。訂正の定義は不要である。

実際の `cmd_verify` は、**終了コード0、`findings: []`、親の要約ページ `.wiki-cache/a.md`** を返した。`raw/a.md`、`assets/a.md`、`indexes/a.md` を渡しても同じだった。

これらは通常の wiki 走査ではページにならない。承認した全文をその場所に書いても、以後の読み取りでは要約ページとして存在しない。overlay を外した verify は、**終了コード1、`no_summary`** になった。

原因は、新しい overlay の項目を、ページとして認められるパスか確認せず追加すること。

根拠：[wiki_captions.py:1291](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:1291)、[引数の検査:wiki_youtube.py:565](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_youtube.py:565)。通常のページの範囲は [wiki_pages.py:49](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:49) にあり、両者が一致しない。

### 3. 【重大】自動字幕の別名との衝突により、投稿者字幕を明示選択できない

次のトラック情報で再現した。自動字幕の URL は、それぞれ対応する `kind=asr&lang=...` を持ち、`tlang` はない。

```text
subtitles:
  ja
automatic_captions:
  ja
  ja-orig
  en
  en-orig
```

分類後の候補は、投稿者字幕 `ja`、自動字幕 `ja-orig`、自動字幕 `en-orig` になる。

1. 指定なしの inspect は、複数言語の自動字幕があるため終了コード3で停止する。
2. 表示された投稿者字幕を選び、`--track ja` で再実行する。
3. **終了コード3、`track_undecided`** のまま、「指定したトラック 'ja' は……ない」と返す。

`ja` は投稿者字幕の名前であると同時に、自動字幕 `ja-orig` の別名でもあるため、候補が2件になる。投稿者字幕には別の指定名がなく、V2 の案内どおりに選択を完了できない。`--track ja-orig` では自動字幕を選べた。

根拠：[wiki_youtube.py:111](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_youtube.py:111)、[自動字幕の別名:125](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_youtube.py:125)、[明示選択:143](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_youtube.py:143)。利用者によるトラック指定を認める ADR 57行目と食い違う。

## 崩れる前提

- **直前の1コードポイントで、英字・カタカナの続きか判断できる。** 結合文字による分解表現で崩れる。
- **wiki 内の相対 `.md` パスなら、保存後もページとして読まれる。** `.wiki-cache/` などの除外対象で崩れる。
- **公開したトラック名と別名をまとめて検索しても、選択が一意になる。** 投稿者字幕の名前と自動字幕の別名が重なると崩れる。

## 見落としと軽微な問題

### 【軽微】拡張子 `.MD` の既存 raw を検索から落とす

`existing_raws` は `entry.name.endswith(".md")` だけを認める。同じ動画・同じハッシュの既存ファイルについて、列挙結果の名前を `a.md` から `a.MD` に変えるだけで、`existing` と `_same` が空になった。別スラッグは `free` のままである。

したがって、拡張子の大小文字を変更した既存 raw があると、別スラッグで同じ資料を書ける経路が残る。検証は列挙結果と読み取り内容をメモリ上で差し替えて行い、実ファイルの作成は行っていない。

根拠：[wiki_youtube.py:339](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_youtube.py:339)、[既存資料の判定:358](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_youtube.py:358)。

## 検証した事実

| 主張 | 結果 |
|---|---|
| 試験は49件 | 一致。収集件数49件 |
| ファイルを書かない既存4クラス | 20件成功 |
| 前回の部分的なコード化を検出する | 一致。3つの反例すべてで `bad_mark` |
| 画像の代替テキストを抽出する | 一致。`![999](...)` の `999` を検出 |
| 表示上同じ語なら境目の判定も同じになる | 食い違い。重大1 |
| overlay と保存後でページの範囲が一致する | 食い違い。重大2 |
| 一覧にある投稿者字幕を名前で指定できる | 食い違い。重大3 |

追加の反例は、ファイル一覧・読み取り内容・取得結果をメモリ上で差し替えて検証した。リポジトリのファイルは変更していない。全49件の試験、固定した yt-dlp による実取得、実ファイルへの公開・競合は確かめていない。

## 崩せなかった点

- レビュー5の、印の始まりだけをコード化する反例と、画像の代替テキストの脱落。
- レビュー4の、隠れた印との相殺、Windows の大小文字による集計分離、関連ページの形式エラーの脱落。今回も指摘が残った。
- 既存試験が扱う字幕・メタデータによる raw の構造の偽造。
- 表のセルにある印の検出。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
