## 判定

**却下。確信度：高。** 重大な欠陥を2件再現した。前回の反例自体は解消しているが、不可視文字による語の境目のすり抜けと、Windows の別表記による除外ディレクトリへの保存を防げていない。

## 致命的・重大な欠陥

### 1. 【重大】WORD JOINER を挟むと、本文を訂正前のままにして照合を通せる

raw を `uploaded`・200行とし、L1 に `ト\u2060ヨタ`、L2 に `ヨタ` を置く。U+2060 は WORD JOINER である。親の要約ページを `confidence: "high"` とし、次の本文と定義を使う。

```python
original = "ト\u2060ヨタ"
body = original + "〔訂正 L1-1〕"
definition = f"- L1-1: 字幕 `{original}` を `ヨタ` に訂正（根拠 caption:L2）"
```

本文は raw の元の語から変わっていない。それでも結果は以下だった。

| 項目 | 結果 |
|---|---|
| verify 終了コード | **0** |
| `findings` | **`[]`** |
| 重み・confidence | **1・`high`** |
| `unknown_words` | **`{}`** |
| lint の `caption_corrections` | **`[]`** |

U+200D（ZERO WIDTH JOINER）でも同じ結果になった。比較として、不可視文字のない `トヨタ〔訂正 L1-1〕` は `mark_tail` になる。browse の本文HTMLも、U+2060を含む元の語を通常の本文として保持することを確認した。

NFKC はこれらの文字を取り除かない。正規化後も、語の直前の1文字はカテゴリー `Cf` であり、結合文字の検査にも、カタカナの文字種の検査にも当たらない。その位置を語の境目として受理している。

根拠：[wiki_captions.py:503](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:503)、[文字種の判定:471](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:471)。語の途中の切れ目を拒む [ADR-0027:101](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md:101) と食い違う。漢字の語に関する受け入れ済みの限界ではなく、カタカナで成立する。

### 2. 【重大】Windows の末尾の点・空白で、除外ディレクトリへの保存先を受理する

Windows で、wiki に `graph/` が存在する状態を使う。正常な raw と、それを参照する正常な親の要約を用意し、次を渡す。

```text
verify --wiki <W> --raw-root <R> --slug a \
  --page "graph./a.md=<要約ファイル>" --json
```

再現結果は以下だった。

| 保存先の指定 | verify の結果 |
|---|---|
| `graph./a.md` | **終了コード0、指摘なし、親 `graph./a.md`** |
| `graph /a.md` | **終了コード0、指摘なし、親 `graph /a.md`** |
| `graph/a.md` | 終了コード1、保存先を拒否 |
| overlay なし | 終了コード1、`no_summary` |

実環境でも、次の両方が真になることを確認した。

```python
os.path.samefile(wiki / "graph", wiki / "graph.")
os.path.samefile(wiki / "graph", wiki / "graph ")
```

保存先は既存の `graph/` の中である。保存後の通常走査は、ディスク上の名前 `graph` でこのディレクトリを除外する。

`disk_spelling` が直すのは `normcase` で一致する名前だけなので、末尾の点・空白は残る。再検査もその字面に対して行われ、除外名との比較を通過する。

根拠：[wiki_captions.py:1286](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:1286)、[disk_spelling:1293](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:1293)、[通常走査の除外:wiki_pages.py:254](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:254)。保存後もページとして読まれる場所だけを認める [ADR-0027:112](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md:112) と食い違う。

## 崩れる前提

| 暗黙の前提 | 崩れる条件 |
|---|---|
| NFKC 後の直前1文字で、語が続いているか判断できる | WORD JOINER や ZERO WIDTH JOINER が語の途中にある |
| 大小文字をそろえてディスクの名前と比較すれば、保存先の実体を特定できる | Windows がディレクトリ名末尾の点・空白を無視する |
| ページの相対パスを直しても、検査対象の集合との対応は保たれる | `unknown_for` に修正前の綴りが残る |

## 見落としと軽微な問題

**【軽微】保存先の綴りを直すと、「raw にない語」が脱落する。**

既存の `sources/` がある Windows で、正常な要約の本文を、raw にない `999` とする。保存先の指定だけを変えた。

| `--page` の保存先 | 結果の親 | `unknown_words` |
|---|---|---|
| `sources/a.md` | `sources/a.md` | `{"sources/a.md": ["999"]}` |
| `SOURCES/a.md` | `sources/a.md` | **`{}`** |

`load_pages` はパスをディスクの綴りに直すが、`cmd_verify` が渡す `unknown_for=set(overlay)` は元の綴りのままである。そのため、ページを抽出対象から外してしまう。

根拠：[wiki_youtube.py:599](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_youtube.py:599)、[wiki_captions.py:1324](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:1324)、[対象の照合:1224](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:1224)。補助的な目印の脱落なので、重大には数えていない。

## 検証した事実

| 確かめた主張 | 結果 |
|---|---|
| 試験は51件 | 一致。収集件数51件 |
| ファイルを書かない既存4クラス | **21件成功** |
| 前回の分解濁点・半角濁点を拒む | 一致。`mark_tail` |
| `GRAPH/a.md` を拒む | 一致 |
| 投稿者字幕と同名の自動字幕をIDで選べる | 一致。`uploaded:ja` と `asr:ja` でそれぞれ選択できた |
| 動画ID末尾の `%0A` を拒む | 一致。`youtube_other` |
| 正規化後の保存先が通常走査と一致する | 食い違い。重大2 |
| 保存先の綴りによらず未知語を抽出する | 食い違い。軽微な問題 |

反例は、合成した raw・ページとファイル一覧をメモリ上で差し替え、実際の `cmd_verify`、`check_wiki`、lint を通して検証した。ディレクトリの別表記の `samefile` は実環境で確認した。ファイルは変更していない。

全51件の一括実行、固定した yt-dlp による実取得、実ファイルへの公開・競合は確かめていない。

## 崩せなかった点

- 前回のトラック名の衝突を、種類付きIDで選択する処理。
- 印の始まりだけをコードにする既出の反例。今回も `bad_mark` になった。
- 既存試験が扱う、字幕による偽の行番号・フェンス・区間構造の挿入。
- confidence の計算式そのもの。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
