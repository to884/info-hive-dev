## 判定

**却下。確信度：高。** 不正な印を正常な訂正として数える反例と、同じ raw に属する定義や関連ページのエラーを verify が除外する反例を再現した。「照らせないものは誤りにする」方針は、まだ貫けていない。

## 致命的・重大な欠陥

### 1. 【重大】見える印と隠れた印の個数を相殺でき、定義のない留保が通る

raw は `uploaded`・200行、L1 は `15`、L2 は `50` とする。親の要約ページを `confidence: "high"` とし、本文と定義を次のようにする。

```markdown
15〔[[留保]] L1-2〕 [[50〔訂正 L1-1〕|本文]]

## 字幕の訂正と留保

- L1-1: 字幕 `15` を `50` に訂正（根拠 caption:L2）
```

閲覧側の `inline_text` が返す表示文字列は、次のとおりである。

```text
15〔留保 L1-2〕 本文
```

表示にあるのは、定義のない `L1-2` の留保だけである。一方、原文の正規表現は、wikilink の**行き先に隠れた** `L1-1` の訂正印を拾う。

表示上の開始形も原文の印も1個なので、個数の検査を通る。その後は隠れた印の直前の `50` を照合し、表示された留保を調べない。

実際の `load_pages`、照合、`cmd_verify`、lint を通した結果は次のとおりだった。

- verify：**終了コード0、`findings: []`**
- 定義：`L1-1` だけを使用済みとして受理
- 重み：**1**、confidence：**`high`**
- `unknown_words: {}`
- lint の `caption_corrections: []`

両方の wikilink の参照先ページも用意したため、リンク切れに依存しない。

根拠：[wiki_captions.py:708](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:708) は表示と原文の印を個数だけで比較し、位置・種類・識別子を対応づけない。[同ファイル:725](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:725) は、拾った原文側の印から照合対象を作る。ADR 101行目・112行目の規則と食い違う。

### 2. 【重大】Windows では、raw の大小文字の違いだけで訂正の集計を分離できる

大小文字を区別しない Windows のファイルシステムで、次の状態を作る。

1. `raw/a.md` は `uploaded`・200行、L1 は `15`。
2. 親 `sources/a.md` は `raw: "raw/a.md"`、confidence は `high`、定義なし。
3. 分割ページ `sources/part.md` は `raw: "raw/A.md"` とし、次の本文と定義を置く。confidence は書かない。

```markdown
50〔訂正 L1-1〕

## 字幕の訂正と留保

- L1-1: 字幕 `15` を `50` に訂正（根拠 model:x）
```

`raw/a.md` と `raw/A.md` は同じファイルだが、集計のキーは異なる文字列になる。親側は重み0・`high`、分割ページ側は別の raw として重み3・`medium` になる。

全体検査は分割ページに `no_parent_summary` を出す。しかし `a` に絞った verify は、そのページと指摘を除外し、**終了コード0、指摘なし、重み0・`high`** を返す。分割ページの `raw` の綴りを親と同じに戻すだけで、**終了コード1、重み3・`medium`、`confidence_mismatch`** になった。

検証では、実環境の既存ファイル `AGENTS.md`／`agents.md` に対して `os.path.samefile(...) == True` を確認し、読み取る内容だけを字幕 raw に差し替えた。ファイルの同一性とパス解決は実際の Windows の処理を使っている。

根拠：[wiki_captions.py:960](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:960) の読み取りキャッシュは `normcase` で統一する一方、[同ファイル:907](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:907) の `raw_label` は大小文字を保持する。そのラベルを集計と [対象の絞り込み](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:1173) に使っている。

### 3. 【重大】関連ページの印が壊れると、形式エラーを verify の絞り込みが捨てる

正常な親 `sources/a.md` に、`15` → `50` の定義 `L1-1` と対応する印を置く。既存の `concepts/c.md` に次を書く。

```markdown
999〔**訂正** [[a]] L1-1〕
```

`concepts/c.md` は今回の `--page` に含めず、親ページだけを用意して verify する。

全体検査は `concepts/c.md` に `bad_mark` を出す。しかし `only_raw="raw/a.md"` では、**終了コード0、`findings: []`** になる。

同じ関連ページを次の形にすると、verify は `mark_tail` を報告して終了コード1になる。

```markdown
999〔訂正 [[a]] L1-1〕
```

つまり、印に書式を入れると形式違反を検出するが、その結果として印を `scan.marks` に登録しなくなる。関連ページの選定も `scan.marks` に依存するため、検出した形式違反まで消える。`[[a]]` が明示されている既存ページで再現した。

根拠：[wiki_captions.py:712](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:712) は `bad_mark` を記録して、その inline の印の登録を飛ばす。[同ファイル:1178](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:1178) は登録済みの印だけから関連ページを選び、それ以外のページの指摘を除外する。今回追加した `refs_of` は、この関連ページを救わない。

## 崩れる前提

- **表示側と原文側の印の個数が同じなら、同じ印を読めている。** 表示された不正な印と、wikilink の行き先に隠れた正常形の印を組み合わせると崩れる。
- **絶対パスにした文字列が違えば、別の raw である。** Windows の大小文字の別表記で崩れる。読み取りキャッシュだけは同一視するため、同じ `RawDoc` を別々に集計できてしまう。
- **正常に読めた印から、関係するページを漏れなく選べる。** 関連ページの印そのものに形式違反があると崩れる。

## 見落としと軽微な問題

**【軽微】表示文字列は、閲覧側と完全には一致しない。**

次の本文で確認した。

```markdown
1![](missing.png)5〔訂正 L1-1〕
```

`wiki_browse_core.inline_text` は `15〔訂正 L1-1〕` を返す。一方、`wiki_captions.inline_texts` は空の代替テキストを `U+FFFC` に置き換え、`1<U+FFFC>5〔訂正 L1-1〕` を返す。数字の直前の文字も変わる。

根拠：[wiki_captions.py:622](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:622) と [wiki_browse_core.py:432](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:432)。ここで確かめたのは両関数の出力の不一致であり、ブラウザでの画像の見え方までは検証していない。

## 検証した事実

| 確かめた主張 | 結果 |
| --- | --- |
| 試験は46件 | 一致。収集件数は46件 |
| ファイルを書かない既存4クラス | 20件成功 |
| 複数 raw の分割ページの指摘を、対象 raw に絞っても残す | 前回の反例では一致。`several_video_raws` などを検出 |
| `unlistable`・`unknown` を誤りにする | 一致。どちらも `unreadable_page` を検出 |
| 区間のない raw を拒む | 一致。`CaptionError` |
| 印の個数の照合で、読めない印を除外しない | 食い違い。重大1を再現 |
| 同じ raw の訂正をまとめて confidence に数える | Windows の別表記では食い違い |
| 関連ページの不正な印を verify が報告する | 重大3の条件では食い違い |

一時ファイルを作る試験を含む全46件は実行していない。追加検証は、読み取り対象や取得する一覧をメモリ上の素材に差し替えて実施した。リポジトリのファイルは変更していない。

固定した yt-dlp による実取得、実ファイルへの公開・読み取り専用化・競合は、今回のレビューでは確かめていない。

## 崩せなかった点

- 前回の `[[1]]5`、印内の wikilink、複数 raw の分類除外、ディレクトリ列挙失敗という単独の反例。
- 既存試験が扱う、字幕の改行・偽の行番号・バッククォート列による raw の構造の偽造。
- 通常形のトラック情報での自動翻訳の除外、自動字幕の統合、曖昧な候補での停止。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
