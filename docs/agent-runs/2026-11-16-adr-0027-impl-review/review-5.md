## 判定

**却下。確信度：高。** 印の冒頭だけをコードにすると、定義のない訂正・留保を verify と lint が見落とす反例を再現した。「印全体がコード内の場合だけ除外する」という説明と実装が食い違う。

## 致命的・重大な欠陥

### 1. 【重大】印の一部だけをコードにすれば、照合対象から印全体を消せる

次の条件で再現した。

- raw は `uploaded`・200行。L1 に `15`、L2 に `50` がある。
- 同じスラッグの親の要約ページに `caption_kind: "uploaded"`、`confidence: "high"` を書く。
- 定義は置かず、本文を次にする。

```markdown
50`〔訂正` L1-1〕
```

閲覧側の表示文字列は `50〔訂正 L1-1〕` である。コードなのは冒頭の `〔訂正` だけで、印全体はコード内に収まっていない。

実測結果は次のとおりだった。

| 項目 | 結果 |
| --- | --- |
| verify 終了コード | **0** |
| `findings` | **`[]`** |
| 重み・confidence | **0・`high`** |
| `unknown_words` | `{}` |
| lint の `caption_corrections` | **`[]`** |

次の別形でも通った。後者は、存在しない行の識別子まで見落とす。

```markdown
15`〔留保` L1-1〕
50`〔訂正 L999-9`〕
```

比較として、コードを外した `50〔訂正 L1-1〕` は `undefined_mark` で終了コード1になる。

原因は、[wiki_captions.py:740](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:740) の除外判定である。`MARK_START_RE` が拾った**開始部分だけ**の文字種を調べ、すべて `code` なら `_read_mark` を呼ぶ前に飛ばしている。印全体の範囲や、単一のコードスパンに収まるかは調べない。

これは [ADR-0027:101](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md:101) の「印の中にコードを入れたものは形の誤り」とする規則に反する。定義のない印が本文に存在するため、受け入れ済みの「印の付け忘れ」という限界にも当たらない。

## 崩れる前提

- **印の開始部分がコードなら、印全体もコード内の例である。** `〔訂正` や `〔留保` の直後でコードスパンを閉じると崩れる。
- **閲覧と同じ表示文字列を作れば、本文の語も漏れなく検査対象になる。** 表示文字列を作った後、文字種 `other` の画像の代替テキストを除くため、次の見落としが残る。

## 見落としと軽微な問題

### 【軽微】本文として表示する画像の代替テキストを、「raw にない語」から除外する

raw に `999` がない条件で、用意したページの本文を比較した。

| 本文 | 閲覧の本文HTML | `unknown_words` |
| --- | --- | --- |
| `999` | `<p>999</p>` | `["999"]` |
| `![999](https://example.com/image.png)` | `<p>999</p>` | `{}` |

閲覧側は画像を代替テキストの通常文字に置き換える。[wiki_browse_core.py:1129](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:1129)

一方、照合側は代替テキストを `other` に分類し、[wiki_captions.py:694](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:694) の `_prose` で空白にする。表示される本文の数値が、引用・コード・印のいずれでもないのに一覧から落ちる。[ADR-0027:113](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md:113) の抽出範囲と食い違う。

「raw にない語」は補助的な目印なので、重大には数えていない。

## 検証した事実

| 確かめた主張 | 結果 |
| --- | --- |
| 試験は49件 | 一致。収集件数49件 |
| ファイルを書かない既存4クラス | **20件成功** |
| レビュー4の隠れた印との相殺 | `bad_mark`・`unused_definition`、verify 終了コード1 |
| レビュー4の Windows の大小文字による集計分離 | 同じ raw に統合され、重み3・`medium`・`confidence_mismatch` |
| レビュー4の関連ページの形式エラーの脱落 | `bad_mark` が残り、verify 終了コード1 |
| 部分的にコード化した印の検出 | 食い違い。上記重大1を再現 |
| 固定した yt-dlp による実取得、実ファイルへの公開・競合 | 確かめていない |

反例は読み取り対象とファイル一覧をメモリ上の素材に差し替え、実際の `check_wiki`、`cmd_verify`、lint を通した。一時ファイルを作る全49件の試験は実行していない。ファイルは変更していない。

## 崩せなかった点

- レビュー4の3反例による、指摘の除外と confidence の水増し。
- 既存試験が扱う、字幕の改行・偽の行番号・バッククォート列による raw の構造の偽造。
- 通常形のトラック情報に対する自動翻訳の除外、自動字幕の統合、候補が曖昧な場合の停止。
- confidence の計算式そのもの。重大1は、計算前に印が検査対象から落ちる問題である。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
