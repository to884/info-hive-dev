## 判定

**条件付きで採用可。** 確信度は中。

- 致命的な欠陥は見つからなかった。
- 重大は1件ある。リンクの裏にある記事の概要を「元ページなし（orphan）」と分類する問題で、多くは HEAD から引き継いだ挙動である。
- 提示差分では、ページの先頭に BOM が2つあると browse と status の判定が分かれた。今の作業ツリーでは直っている。
- レビュー中に作業ツリーが提示差分から変わったため、確信度を中にした。

## 致命的・重大な欠陥

### 1.【重大】リンク（ジャンクション、シンボリックリンク）の裏にある記事の概要を orphan にし、削除もできる

- **反例（実測、Windows のジャンクション）**
  1. `concepts/p.md` の概要を保存する。
  2. `concepts` を wiki の外へ移し、`mklink /J concepts <移した先>` を置く。
  3. browse は次のとおりになる。
     - `take_snapshot` の entries は `('link','concepts',None,'junction')`、`drawn=[]`。
     - 診断は `overview_orphan`。
  4. `status` は `orphan`（`orphan_id` 付き）、`complete: True` になる。
  5. `remove(w, key)` を `--orphan` で呼ぶと `{'status': 'removed'}` になり、概要が消える。
- **根拠**
  - `wiki_browse_core.py` の `_build_overviews` は、`by_key` を `snapshot.by_kind("page")` だけから作る。`take_snapshot` は `kind == "link"` を `continue` で飛ばすため、その記事は `PageState("absent")` になる。
  - `wiki_overview._index` は `walk_pages().files` だけを使い、リンクを含まない。差分で `_page_state` を `article_path` に替えたが、その処理は index にあるページにしか届かない。
  - `wiki_pages.article_path` の docstring は「拒んだことを『ない』に変えない」としている。重点6の「記事のリンクを読まない main の規則との統合」が、この経路では満たされていない。
  - ADR-0033 と保存設計（`wiki-overview-2026-11-17.md`）は、リンクの裏の記事の分類に触れていない。ADR-0029 の実装より前に書かれたためである。
- **何が新しいか**
  - `status` の orphan と `remove --orphan` での削除は、HEAD `022013c` の時点からある。差分は `_index` と `remove` を変えていない。
  - 差分で新しく加わったのは、browse の `overview_orphan` 診断である。その記事は `page_unreadable` にも `page_unknown` にもならない。

## 崩れる前提

- **レビューした差分と作業ツリーが同じである。** 崩れた。レビュー中に次のファイルが変わり、どれも提示差分には含まれていない。
  - `wiki_browse_core.py`（07:22 に更新）が `normalized_text_sha256(f.text)` を使うようになった。
  - `wiki_pages.py` に `page_text` と `normalized_text_sha256` が加わった。
  - `wiki_mcp_common.py` の `SERVER_FILES` に3ファイルが加わった。
  - `tests/wiki/test_browse_overview.py` も更新された（07:22）。
- **`page` 入力が記事の名前の全集合である。** リンクの裏の記事は別の種別（`link`）なので、この前提が崩れる（重大1）。
- **transient は「ファイルを変えずに読めるようになりうる」失敗だけである。** 崩れた。
  - ハードリンク数が1でないサイドカーは、`read_sidecar` → `_file` の `OverviewError` → `os_error` → `f.error="os"` → transient と扱われる。何度試しても直らない状態である。
  - 実測（`BrowseState`）：待ち時間の間は同じ中核を返し、`attempts.clear()` のあとは作り直した。`transient` は残り続けた。そのため、5秒ごとに中核を作り直し続ける。
  - `core_loop` は `not cached.snapshot.transient` で判定するので、待ち時間なしに要求ごとに作り直すはずである（推論、`wiki_browse.py:226`）。
  - 設計8節の「既知の不正な項目は、入力が変わったときに再試行する」と食い違う。ただし、ハードリンク数が変わっても大きさと更新時刻は変わらない。transient から外すと回復を検出できなくなるので、この扱いはトレードオフでもある。
  - さらに、表示の案内「/wiki:overview で作り直せる」は誤っている。実測では、`write` は `unsafe_path` で書き込みを拒んだ。
- **`assets` は通常の、正しい綴りのディレクトリである。** 崩れた。
  - 最上位に `Assets/` がある wiki と、`assets` がジャンクションの wiki を実測した。どちらも概要を一度も作っていないのに、全記事に「概要の一覧を確認できない」が出た（`overview_scan_unknown=True`）。
  - 同じ条件では既存の図もすでに描かれていない（`<img` なし）。新しく増えた影響は、この警告だけである。
- **SVG の出力名の衝突は起こりうる。** 名前は内容の SHA-256 なので、違うバイト列が同じ名前になるのは SHA-256 が衝突したときだけである。衝突を全関係ページで拒む経路は、実際には動かず、mock でしか試せない（推論）。

## 見落としと軽微な問題

1. **【軽微】提示差分の時点では、先頭に BOM が2つあるページで判定が分かれた（実測）。**
   - 原因：`read_text_like_lint` と `page_text_sha256(f.text.encode())` が BOM を2回除いていた。
   - 結果：status は `fresh`、browse は `stale`。
   - 今の作業ツリーでは両方 `fresh` になることを実測した。`refresh` のあとも `fresh` だった。
   - 回帰試験は grep では見つからなかった（確かめられず）。既存の `test_saved_boundary_preserves_all_payload_whitespace` は、ページの SHA に `page_files[...].sha`（生のバイト列の SHA）を渡している。BOM や CRLF を含むページでは、browse 側のハッシュの経路を試していない。
2. **【軽微】`check` の所見が変わった（実測）。** 65,537 バイトの下書きで `['too_large', 'too_large']` と重複する。`_draft` の生のバイト数の検査と `_body_problems` の両方が同じ所見を出すためである。設計4節・10節の「既存の所見を維持する」と食い違う。
3. **【軽微】存在しないサイドカーへの診断が出る（実測）。** NFC で重なる2ファイルがあり、概要がないときでも `overview_page_unknown`（path は存在しない `assets/overview/<P>.overview.md`、reason は collision）が出る。サイドカーがある場合は、衝突の診断と状態の診断の2件が重複して出る（コードから）。
4. **【軽微】`page_unknown` でも「概要を読めない。/wiki:overview で作り直せる」と案内する。** P が衝突しているときは、書き手が `id_collision` で拒むので作り直せない。ハードリンクのときも同じく作り直せない。
5. **【軽微】描かれない記事の図も静的版に出力される（推論）。** frontmatter を解釈できず描かれなかった記事の概要が `fresh` なら、その図は `overview_assets` に入る。参照されない SVG が書き出される。
6. **【軽微】`browse_read_sweep.py` の網羅に穴がある（コードから）。**
   - 計測しているのは `os.scandir`、`os.stat`、`win_file_id` だけである。`walk_sidecars` と `_dirs` が使う `os.lstat` と、`read_sidecar` の `open` には障害を入れていない。
   - `overview_walk` の役割では、失敗が続いたまま `rc == 0` で `overview_dir` の印付きの世代を採る場合を、許してしまう。
7. **【軽微】ブラウザ試験の配色の確認が弱い（推論）。** 配色を変えたあとの `waitForFunction(settled)` は、前の回の図がまだ残っていれば、描き直す前に成立しうる。描き直したことは保証されない。また、暗い配色で手書き SVG の地が明るく保たれるかは確かめていない。GUI は実行していないので、確かめられず。
8. **【軽微】文書の残り。** `wiki_overview.py:9` に「将来の browse で共有する」が残っている。

## 検証した事実

- **git の状態**（fetch した）
  - origin/main は `ce2b610`、最新タグは `v0.31.1`。
  - origin/main は HEAD の祖先である。「main の 0.31.1 を取り込んだ」は一致した。
  - プラグイン側の開いている PR は #71（`feat/page-report`）だけで、概要とは別の領域である。
  - 他セッションとの競合リスク：同じ worktree が今も更新されている。結果を読むときは、このリスクが最も大きい。
- **`page_id` の区切り**：`page_id` から `replace("\\","/")` を除いても、browse と書き手の識別子は一致した。どちらも `walk_pages` の `f.rel` から作る。`_work` はバックスラッシュを含むページを拒むので、保存済みのデータへの影響もない。
- **キーの欠落**：`drawn` の各記事は必ず `by_key` に入る。`views[key]` が KeyError になる経路はない（コードから）。
- **ページの診断の表示**：`page_diagnostics` は汎用の描画なので、`overview_*` の診断で記事の描画が失敗することはない（コードから）。
- **frontmatter の解釈**：`_metadata` を正規表現と `parse_frontmatter_text` に替えても緩くなっていない。元の `parse_frontmatter_raw` も、`FRONTMATTER_RE` が合わないものを malformed として拒むだけで、値の解釈は同じ関数である。
- **SVG の配信**：HTTP は `CSP_SVG`（sandbox あり）で返す。`render(name)` は `_render_lock` の下で動く。
- **実測した値**
  - 提示差分の二重 BOM：status `fresh`、browse `stale`。作業ツリーでは両方 `fresh`。
  - ハードリンク：transient に残り、作り直しが続く。`write` は `unsafe_path` で拒む。
  - ジャンクション：orphan と判定し、`remove --orphan` で消える。
  - `Assets/` とジャンクションの `assets`：全記事に一覧不明の警告が出る。
  - 65,537 バイトの下書き：`too_large` が2件出る。
  - NFC の衝突：存在しないサイドカーへの `overview_page_unknown` が出る。

## 崩せなかった点

- **h1 の直後への配置**：トップレベルの `heading_close` の h1（`level == 0`）で決めている。引用やリストの中の h1 は差し込み位置にならない。差し込みは見出し ID を付けたあとに行う。概要の字句は ID の付与、wikilink、リンクのカウンター、`_prepass` を通らない。
- **保存済み本文の境界**：ヘッダー後の1 LF と、本文後の2 LF だけを外す処理を確かめた。図あり・図なし、末尾の空行の数、空白だけの行、閉じていないフェンスを机上で追ったが、崩せなかった。閉じていないフェンスは `assembly` で拒まれる。
- **概要だけの変更の検出**：概要だけの追加・更新・削除は、署名と世代に反映される。読んでいる間に一覧が変わったときは `InputsChanged` になる。
- **描画の失敗の扱い**：失敗は概要の中で止まり、キャッシュせず、次の描画で直れば診断を取り除く。
- **安全な表示**：概要の SVG は `<img>` で表示し、DOM に入れない。外部リンク以外は文字にする。style 属性は表の位置合わせのクラスに替えている。

## このタスクの推奨モデルとエフォート

- このレビュー：Opus、high。
- 次の修正（リンクの裏の記事の分類、ハードリンクの transient の扱い、重複した診断）と回帰試験の追加：Opus、high。

`✶ Insight ─────────────────────────────────────`
- 同じ写しから判定するときは、どの入力の種類を集合に数えるかが状態の正しさを決める。`link` を数えないと、「読まない」が「ない」に変わる。
- transient を「OS エラーかどうか」で決めると、ハードリンクのような恒久的な拒否も再試行の対象になる。そうすると、再構築の頻度を利用者の環境が決めてしまう。
`─────────────────────────────────────────────────`
