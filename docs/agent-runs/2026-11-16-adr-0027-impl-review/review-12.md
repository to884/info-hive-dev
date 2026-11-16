## 判定

**却下。確信度：高。** 循環しないジャンクションの別名を使うと、同時に保存できないページの組が `verify` を通る。11回目の重大指摘は、実体が同じ保存先では残っている。

## 致命的・重大な欠陥

### 【重大】別名のディレクトリ経由では、保存先同士の衝突を見落とす

Windows の次の構成を使う。`raw/a.md` は正常な `uploaded` の字幕200行で、L1は `15` とする。

```text
wiki/
  SCHEMA.md
  sources/
    real/
    alias/  → real を指す、循環しないジャンクション
raw/
  a.md
```

次の3ページを同時に渡す。

| 保存先 | 内容 |
|---|---|
| `sources/a.md` | 親の要約。`raw: "raw/a.md"`、`caption_kind: "uploaded"`、`confidence: "medium"` |
| `sources/real/x.md` | エンティティページ。`sources: ["a"]` |
| `sources/alias/x.md/child.md` | 同じrawの分割要約。confidenceは書かない |

分割要約の本文と定義：

```markdown
50〔訂正 L1-1〕

## 字幕の訂正と留保

- L1-1: 字幕 `15` を `50` に訂正（根拠 model:reason）
```

OSの応答をメモリ上で差し替え、実際の `walk_pages`、`check_wiki`、`cmd_verify` を実行した結果：

```text
通常走査の visited:
  "", "sources", "sources/alias", "sources/real"

verify:
  終了コード: 0
  findings: []
  weight: 3
  confidence: medium
```

しかし、`sources/real/x.md` と `sources/alias/x.md` は同じ場所である。一方ではファイル、他方ではディレクトリになるため、3ページを保存できる順序は存在しない。

親とエンティティだけを保存した状態を反映すると、再検査は **`confidence_mismatch`** を返した。分割要約の重み3が消え、計算値が `high` になる。

根拠：

- [wiki_captions.py:1443](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:1443)：組の衝突検査は、casefoldしたパスの綴りと接頭辞だけを比較する。`real` と `alias` の同一性は比較しない。
- [wiki_captions.py:1365](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:1365)：到達判定は、両方の既存ディレクトリが `visited` にあるため通る。
- [wiki_pages.py:276](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_pages.py:276)：識別子を比べるのは祖先との循環判定であり、兄弟の別名は走査される。これは通常走査の実装と一致する。
- [ADR-0027:112](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md:112)：保存予定ページを組として検証する要件と食い違う。

## 崩れる前提

| 暗黙の前提 | 崩れる条件 |
|---|---|
| casefold後のパスが異なれば、保存先の実体も異なる | 循環しないジャンクションが、別の保存先の祖先を指す |
| 既存の祖先へ通常走査が降りれば、その下の予定ページを同時に作れる | 別名経由の予定ページが、途中の同じ場所をファイルとして使う |
| 衝突する入力は、組の比較まで残る | ディスクの綴りへ直す段階で、辞書の同じキーに上書きされる |

## 見落としと軽微な問題

### 【軽微】既存ファイルへの大文字・小文字違いの指定は、衝突検査前に消える

既存の `sources/a.md` がある状態で、異なる内容を次の2キーで渡した。

```text
sources/a.md   → 本文に999を含む草稿
SOURCES/A.md   → 本文に999を含まない正常な草稿
```

結果は以下だった。

```text
renamed:
  sources/a.md → sources/a.md
  SOURCES/A.md → sources/a.md

検証対象ページ数: 1
999を含む草稿: 残らない
verify終了コード: 0
findings: []
unknown_words: {}
```

[wiki_captions.py:1438](C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:1438) の `overlay[disk] = text` が先の草稿を上書きする。その後の衝突検査では、入力が2つあったことを検出できない。「同じ場所になる2ページなら止まる」という説明と食い違う。

## 検証した事実

| 確認事項 | 結果 |
|---|---|
| 試験は55件 | 一致。収集件数55件 |
| 書き込みを伴わない既存4クラス | 21件成功 |
| 今回追加された3試験 | ファイルシステムをメモリ上で差し替え、試験本体が成功 |
| 11回目の字面による祖先衝突・大小文字衝突を拒む | 一致 |
| 補助面のカタカナを未知語として挙げる | 一致 |
| シンボリックリンク・循環ジャンクション配下を拒む | 一致。通常走査と拒否を確認 |
| 保存予定ページの組が実現可能である | 食い違い。上記重大指摘 |

ファイルは変更していない。全55件の一括実行、実ジャンクションの作成・実保存、固定したyt-dlpによる実取得は未実施。

## 崩せなかった点

- 既出の不可視文字・補助面カタカナによる、語の途中の境界すり抜け。
- 字幕による行番号・フェンス・区間構造の偽造。
- 種類付きIDによる、同名の投稿者字幕と自動字幕の選択。
- confidenceの計算式そのもの。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
