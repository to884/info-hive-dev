## 判定

**却下。確信度：高。** 重大1件、軽微1件を再現した。新規ページについて、検証時のページ集合が保存後の通常走査と一致せず、指摘なしで承認に進める。

## 致命的・重大な欠陥

### 【重大】新規ページが別名側にも現れることを、保存予定の状態に反映しない

Windowsで次の構成を使う。`real/` は空で、`alias/` はそのディレクトリを指す、循環しないジャンクションとする。

```text
wiki/
  sources/
    real/
    alias/ → real/
  entities/
raw/
  a.md
```

`raw/a.md` は正常な `uploaded` の字幕200行で、L1は `15`。次の2ページを用意する。

| 保存先 | 内容 |
|---|---|
| `sources/real/a.md` | `type: "source"`、`raw: "raw/a.md"`、`caption_kind: "uploaded"`、`confidence: "medium"` |
| `entities/e.md` | `type: "entity"`、本文は `50〔訂正 [[a]] L1-1〕` |

要約ページの本文と定義：

```markdown
50〔訂正 L1-1〕

## 字幕の訂正と留保

- L1-1: 字幕 `15` を `50` に訂正（根拠 model:x）
```

OSの応答とファイル内容をメモリ上で差し替え、実際の `walk_pages`、`cmd_verify`、lintを実行した。

| 段階 | 結果 |
|---|---|
| 保存前の通常走査 | `sources/real` と `sources/alias` の両方に降りる。ページはない |
| 2ページを `--page` で検証 | **終了コード0、`findings: []`** |
| 同じ内容の保存を反映した通常走査 | 要約を `sources/real/a.md` と `sources/alias/a.md` の両方で読む |
| 保存後の `verify` | **終了コード1**。`bad_mark_summary`、`confidence_on_child` |
| 保存後のlint | 同じ2件を `caption_corrections` に報告 |

保存後はスラッグ `a` の候補が2つになるため、関係ページの `[[a]]` が曖昧になる。また、親として先に選ばれなかった実体側のページが、`confidence` を持つ分割ページとして拒まれる。ほかの変更や競合は必要ない。

原因は、新規ページを保存先の相対パス1つだけで `new_pages` に追加すること。同じ実体のディレクトリへ降りる別経路には、新規ページを追加しない。既存ファイルに対する `by_identity` の置き換えでは、この欠落を補えない。

根拠：

- [wiki_captions.py:1448](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:1448)：新規ページの判定と登録。
- [wiki_captions.py:1478](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:1478)：登録した相対パスだけを追加する。
- [wiki_pages.py:276](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:276)：祖先との循環だけを除き、兄弟の別名は走査する。
- [ADR-0027:112](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md:112)：保存後の状態を照らす要件と食い違う。

## 崩れる前提

| 暗黙の前提 | 崩れる条件 |
|---|---|
| 保存先が一覧の降りる場所にあり、ほかの保存先と衝突しなければ、保存後のページ集合も再現できる | 同じディレクトリがジャンクションの別名でも走査され、新規ファイルが複数の相対パスに現れる |
| 実体の重複検査には、渡された草稿がすべて届く | `parse_page_args` が同じ相対パスの入力を辞書への代入で消す |

## 見落としと軽微な問題

### 【軽微】同じ相対パスの `--page` は、衝突検査前に上書きされる

上記の要約について、`bad.md` は `confidence: "high"`、`good.md` は正しい `confidence: "medium"` とする。

```text
--page sources/real/a.md=bad.md
--page sources/real/a.md=good.md
```

実際の結果：

- `bad.md` 単独：終了コード1、`confidence_mismatch`。
- 2つをこの順で指定：overlayは1件になり、**終了コード0、`findings: []`**。
- `bad.md` が渡された事実は、実体の重複検査に残らない。

[wiki_youtube.py:581](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_youtube.py:581) の `overlay[nfc(rel)] = ...` が先の草稿を捨てる。[wiki_captions.py:1455](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:1455) の重複検査では検出できない。「同じ実体を指す2ページなら止まり、片方を捨てない」という説明は、CLI入力全体には成立しない。

## 検証した事実

| 確認事項 | 結果 |
|---|---|
| 試験は55件 | 一致。収集件数55件 |
| 書き込みを伴わない既存4クラス | 21件すべて成功 |
| 12回目の別名経由のファイル・ディレクトリ衝突 | 拒否を確認 |
| 別名経由で同じ新規ファイルを2回指定 | 拒否を確認 |
| 別名経由で同じ既存ファイルを2回指定 | 拒否を確認 |
| 既存ファイルのoverlayを、走査された別名にも反映 | 一致。両方が用意した内容になる |
| 新規ページの検証が保存後と一致 | **食い違い。重大指摘のとおり** |

追加検証はOSの応答とファイル内容の差し替えによるもの。ファイルは変更していない。全55件の一括実行、実ジャンクションの作成・実保存、固定したyt-dlpによる実取得は未実施。

## 崩せなかった点

- 12回目の衝突例そのもの。
- 既存試験が扱う、字幕による行番号・区間・フェンスの偽造。
- 不可視文字と補助面カタカナによる、既出の語境界のすり抜け。
- 種類付きIDによる、同名の投稿者字幕と自動字幕の選択。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
