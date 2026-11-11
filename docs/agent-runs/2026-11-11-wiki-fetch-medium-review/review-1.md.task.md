# 目的

info-hive-wiki#42 の修正をレビューする。`wiki_fetch.py`（Web ページを取得して本文を Markdown にし、図を保存する標準ライブラリだけのスクリプト）が、Medium の記事で次の 2 つを取りこぼしていた。

1. 図: Medium の図は `<picture><source srcset="...webp..." type="image/webp"><source srcset="...png..."><img alt="" width height></picture>` の形で、`<img>` に URL がない。`image_mark()` が `<img>` の属性しか見ないので `no_src` で捨てていた。
2. コードブロック: Medium は `<pre>` の中の行を `<br>` で区切る。`pre` の処理が `text_of()` で文字だけをつなぐので 1 行につながっていた。

修正の方針:
- `<img>` から URL を取れない（または `data:` の代わりの画像）ときだけ、同じ `<picture>` の `<source>` から取る。WebP でない `<source>` を先に見て、`srcset` のうち幅か密度のいちばん大きい候補を取る。
- `text_of()` に `br` 引数を足し、`pre` のときだけ `<br>` を `\n` にする。ほかの呼び出しの結果は変えない。

# 読むもの

- 差分: `docs/agent-runs/2026-11-11-wiki-fetch-medium-review/submodule.diff`（サブモジュール info-hive-wiki の差分）と `parent.diff`（親リポジトリ）
- 本体: `info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py`（とくに `text_of`、`_largest_candidate`、`picture_source_url`、`Converter.image_mark`、`Converter.block` の `pre`、`build` の画像の保存）
- テスト: `tests/wiki/test_wiki_fetch.py`
- 変更履歴: `info-hive-wiki/CHANGELOG.md` の `[Unreleased]`

# 見てほしい点

- 既存のページ（`<picture>` を使わないサイト、`<pre>` の外の `<br>`、`text_of` のほかの呼び出し元: 題名、`_visible_len`、`code` のインライン、数式など）で出力が変わる場合がないか。
- `srcset` の解析の誤り（URL にカンマを含む、記述子なし、`1.5x`、不正な記述子、`data-srcset`、`media` 付きの `<source>`、`<source>` が `<picture>` の外や入れ子の中にある場合）。
- 安全性: 取得する URL が増えることで、内部のアドレスや意図しない URL を取りに行くことにならないか（`build` の `block_private` の扱いと照らす）。
- テストが修正の主張を本当に確かめているか。テストの不備。
- CHANGELOG の記述が実装と食い違っていないか。

テストは `python -X utf8 -m unittest tests/wiki/test_wiki_fetch.py -v` で動く（ネットにはつながない）。
