既存の `FigureTargetTest` 4 件は通過しましたが、追加のメモリー上の検証では、UTF-16 SVG が診断なしで出力されることを確認しました。また、コメント中の `<svg>` や `data-width` をサイズ判定が拾い、実際の幅 800 の図に幅 1 を指定する反例も確認しました。
## 判定

**却下。確信度：高。** BOM なしの UTF-16 SVG が UTF-8 制限を通過し、絶対パスとトークンを公開前の検査で検出できないまま出力される。ほかに、サイズ判定の誤りと lint との解決結果の不一致を確認した。

## 致命的・重大な欠陥

**1. 重大：BOM なしの UTF-16 が文字コード検査をすり抜ける**

ASCII 文字だけで構成した XML を `utf-16-le` または `utf-16-be` で符号化すると、バイト列は NUL を含むものの、UTF-8 のデコードにも成功する。デコード後の文字列では `<` と `?xml` の間などに NUL が入るため、XML 宣言の正規表現が一致せず、`is_utf8_svg` は `True` を返す。

反例：

```python
text = (
    '<?xml version="1.0" encoding="UTF-16"?>'
    '<svg xmlns="http://www.w3.org/2000/svg">'
    '<desc>C:/Users/secret TOKEN_0123456789</desc></svg>'
)
data = text.encode("utf-16-le")

assert core.is_utf8_svg(data) is True
assert core.scan_machine_info(
    {"x.svg": data},
    ["C:/Users/secret"],
    ["TOKEN_0123456789"],
) == []
```

実行結果は上記のとおりだった。`utf-16-be` でも再現した。標準ライブラリの XML パーサーでは、元のパスとトークンを含む `desc` を読み取れた。

さらに、入出力をメモリーに差し替えて `take_snapshot → Core → render_all` を実行した結果、次を確認した。

- `snapshot.unreadable == []`
- 図の診断も空
- 本文に `<img>` が生成される
- SVG の元のバイト列が出力辞書に入る
- 出力全体の `scan_machine_info` も検出ゼロ

したがって、設計の「UTF-8 に制限することで公開前の検査が働く」という防御が成立していない。ブラウザでの表示成否にかかわらず、検査対象の情報を含むバイト列が書き出し対象になる。

根拠：[wiki_browse_core.py:164](C:/Works/info-hive-dev/.claude/worktrees/browse-figures/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:164) の宣言検査、同ファイルの `_read_asset`、`render_all`、`scan_machine_info`。設計書 6.2 と食い違う。既存の `test_utf8_only` は BOM 付きの `encode("utf-16")` だけを試しており、この反例を検出しない。

## 崩れる前提

- **「UTF-8 としてデコードできれば、XML も UTF-8 として読む」**  
  BOM なし UTF-16 の ASCII XML で崩れる。Python の文字列化と XML の文字コード判定が一致しない。

- **「最初に現れる `<svg ...>` と `width`・`height` は根の属性である」**  
  コメント中の記述や `data-width`・`data-height` で崩れる。

- **「文字参照を解く前後で `#`・`?` の切り落とし結果は同じ」**  
  数値文字参照の `#`、および `&quest;` で崩れる。lint と browse の処理順が一致していない。

## 見落としと軽微な問題

**2. 軽微：有効な SVG に誤った表示サイズを指定する**

次のいずれも、`svg_size` の実行結果は `(1, 1)` だった。

```xml
<!-- <svg width="1" height="1"> -->
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600"/>
```

```xml
<svg xmlns="http://www.w3.org/2000/svg"
     width="800" height="600" data-width="1" data-height="1"/>
```

前者はコメント内の偽の開始タグを拾う。後者は属性名の手前を `\b` で判定しているため、`data-width` も `width` として拾い、辞書化すると本物の値を上書きする。その値が `<img width="1" height="1">` に使われ、通常の大きさの図が極端に縮む。

根拠：[wiki_browse_core.py:180](C:/Works/info-hive-dev/.claude/worktrees/browse-figures/info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py:180) の正規表現と `svg_size`、同ファイルの `_figure_html`。

**3. 軽微：存在する図を lint が欠落として報告する**

`assets/a&b.svg` がある状態で、次の参照を使う。

```markdown
![図](../assets/a&#38;b.svg)
```

browse は `assets/a&b.svg` に解決する。一方、lint は文字参照を解く前に `#` で切り、`../assets/a&` を探す。実際の `missing_assets` を、ファイルの存在判定だけメモリーに差し替えて実行し、誤検出を確認した。

同様に、次の参照も不一致になる。

```markdown
![図](../assets/a.svg&quest;v=1)
```

browse は `assets/a.svg` を指すが、lint は `?v=1` を含むファイル名を探す。

根拠：[wiki_lint.py:282](C:/Works/info-hive-dev/.claude/worktrees/browse-figures/info-hive-wiki/skills/info-hive/scripts/wiki_lint.py:282)、`figure_target`。設計書 6.4 の「同じ順で解く」という主張と食い違う。

**4. 軽微：一部の試験は、説明している保証より弱い**

- `figures.test.mjs:194` は、暗い配色で入れ物と本文の背景色が**異なることだけ**を判定する。入れ物が本文より暗くなっても通るため、「明るい配色を保つ」の検証にはなっていない。
- `test_links_are_not_read` は、最初のファイル symlink 作成に失敗すると、後続のディレクトリ symlink の検証も丸ごと飛ばす。ジャンクションを作る試験もこのケースにはない。権限のない Windows では、リンク除外を実環境で検証した根拠にならない。

根拠：[figures.test.mjs:194](C:/Works/info-hive-dev/.claude/worktrees/browse-figures/tests/wiki/browse/figures.test.mjs:194)、[test_browse.py:2056](C:/Works/info-hive-dev/.claude/worktrees/browse-figures/tests/wiki/test_browse.py:2056)。

## 検証した事実

- **一致：** 既存の `FigureTargetTest` 4 件はすべて通過した。その状態でも上記の追加反例は成立した。
- **一致：** PNG の中心画素を読み、期待する青色と比較する処理は存在する。画像の寸法だけで色を判定しているわけではない。
- **一致：** `assets/` の一覧不能は `asset_dir`、種類不明の SVG は大きさのない `asset` になり、`unreadable` と `transient` に入る。メモリー上の検証で確認した。
- **一致：** ルート一覧不能は、引き続き入力全体の不採用になる。
- **確かめられず：** Playwright と実サーバーの試験は実行していない。ファイルを作る試験は避け、読み取りとメモリー上の検証に限定した。
- **確かめられず：** この環境のサブモジュールには Git メタデータがなく、`git diff HEAD` は取得できなかった。保存されたプラグイン差分、提示された親差分、実ファイルを読んだ。

## 崩せなかった点

- 読み取り上限は、走査時のサイズだけに依存していない。100 バイトの入力に上限 99 を与えると `TooLarge`、上限 100 なら成功し、いずれもハンドルを閉じた。
- NFC・NFD で同じ名前になる別々の SVG は、両方とも出力から除外され、`asset_collision` になった。
- 大文字・小文字だけが違う SVG は別の出力名になった。確認した `assets.md`、`Assets/wiki.md`、固定ファイルとの衝突はなかった。
- symlink・ジャンクションと判定された `assets` は子を一覧せず、ファイル symlink は `stat` せずに除外した。これは OS 応答を差し替えた検証であり、Windows の実ジャンクションでの実証ではない。

使用した MCP サーバー: なし  
使用した Agent Skills: なし
