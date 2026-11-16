## 判定

**却下。確信度：高。** 大小文字を区別するWindowsのディレクトリを仮定すると、別ファイルへの草稿で訂正定義が検証上だけ消え、過大な `confidence` を承認できる。14回目の2件の修正は崩せなかったが、保存前後の検証結果が一致しない反例が残る。

## 致命的・重大な欠陥

### 【重大】大小文字を区別するWindowsの別ファイルを、同じ実体として上書きする

Windowsで、wikiのディレクトリに大小文字の区別が有効な状態を仮定する。`Detail.md` と `detail.md` は別ファイルである。

`raw/a.md` は正常な `uploaded` の字幕200行とし、L1は `15`。既存ページを次のように置く。

| ページ | 内容 |
|---|---|
| `sources/a.md` | `raw: "raw/a.md"`、`caption_kind: "uploaded"`、`confidence: "medium"` |
| `sources/Detail.md` | 同じrawを参照。下記の訂正と定義を持つ。confidenceなし |
| `sources/detail.md` | 同じrawを参照。本文は `caption`。定義・confidenceなし |

`Detail.md` の本文：

```markdown
50〔訂正 L1-1〕

## 字幕の訂正と留保

- L1-1: 字幕 `15` を `50` に訂正（根拠 model:x）
```

保存予定として、次の2ページを渡す。

- `sources/a.md`：confidenceを `high` に変更。
- `sources/detail.md`：定義のない本文を渡す。`Detail.md` は変更しない。

OSの応答とファイル内容をメモリ上で差し替え、実際の走査・照合・CLI処理を実行した。

| 状態 | 結果 |
|---|---|
| 変更前 | 指摘なし。重み3、confidenceは `medium` |
| 保存予定の検証 | **終了コード0、`findings: []`。重み0、`high`** |
| 同じ変更を保存した状態 | **終了コード1、`confidence_mismatch`。重み3、計算値は `medium`** |
| 保存後のlint | `caption_corrections` に `confidence_mismatch` |

原因は、[_identity](/C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:1403) が実際のパスへ無条件に `os.path.normcase()` を適用すること。Windowsでは両ファイルの鍵が同じになる。

そのため、[草稿の登録](/C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:1465) と[既存ページへの適用](/C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:1475) によって、`detail.md` の草稿が `Detail.md` にも適用される。実際には残る訂正定義が、検証時には消える。

[NFC衝突の検査](/C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/info-hive-wiki/skills/info-hive/scripts/wiki_captions.py:1493) は、大小文字の異なる相対パスを衝突としないため止められない。両ファイルの実体の鍵を別々に保つ対照実験では、保存前にも `confidence_mismatch` が出た。

これは、[ADR-0027の機械の照合](/C:/Works/info-hive-dev/.claude/worktrees/adr-0027-impl/docs/adr/0027-youtube-captions-via-pinned-yt-dlp.md:112) が求める、保存予定の状態に対する承認前の検証と食い違う。

## 崩れる前提

| 暗黙の前提 | 崩れる条件 |
|---|---|
| Windowsで `normcase(realpath(path))` が同じなら、同じファイルである | 対象ディレクトリが大小文字を区別し、`Detail.md` と `detail.md` が共存する |
| 同じ鍵を持つ全ページへ草稿を反映すれば、保存後を再現できる | 鍵が別ファイルを混同し、変更対象でないページの定義まで置き換わる |
| NFC衝突の検出によって、ページの混同を止められる | 混同がNFCの相対パスではなく、実体の鍵の大小文字変換で起きる |

## 見落としと軽微な問題

独立した軽微な指摘はなし。

## 検証した事実

| 確認事項 | 結果 |
|---|---|
| 試験は59件 | 一致。収集件数59件 |
| 書き込みを伴わない既存4クラス | 21件すべて成功 |
| NFCで重なる別ファイルを指摘する | 一致。メモリ上の再現で `ambiguous_page_path` を確認 |
| 同じrawへの `Video`／`video` の指定を `different` とする | 一致。大小文字を区別しない応答の再現で両方とも `different` |
| 保存予定の検証が保存後と一致する | 食い違い。上記の反例を再現 |

ファイルは変更していない。追加検証ではOSの応答と読み込む内容を差し替え、実際の `walk_pages`、`check_wiki`、`cmd_verify`、lintを実行した。大小文字を区別する実ディレクトリの作成、全59件の一括実行、固定したyt-dlpによる実取得は未実施。

## 崩せなかった点

- 14回目のNFC衝突によって、指摘なしで定義が消える反例。
- 大小文字を区別しない環境で、同じ動画の別版を `slug_taken` と取り違える反例。
- 実行した既存試験の範囲での、字幕による行・区間・フェンスの偽造。
- 種類付きIDによるトラックの選択と、自動翻訳の除外。
- 定義が漏れずに渡された場合のconfidenceの計算。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
