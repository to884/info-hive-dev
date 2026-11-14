# 依頼: browse の索引とサイドバーの設計（4 版目）の敵対的レビュー

対象は `docs/plans/wiki-browse-findability-2026-11-13.md` である。Claude Code のプラグイン `wiki`（サブモジュール `info-hive-wiki/`）の閲覧機能 `/wiki:browse` の索引のページとサイドバーを直し、静的の検索を足す設計である。

## 目的

この設計は、次を満たさなければならない。

- 作者の決定（設計書の「作者が決めたこと」）に従う。左のペインは件数つきで折りたためる木、索引のページは絞り込める一覧で、索引のページの木はグループの名前と件数までに畳む。検索は、題名、タグ、見出し、要約の部分一致（ADR-0010 の決定 5 の A）。
- 第 1 段階の設計（`docs/plans/wiki-browse-stage1-2026-11-09.md`）の「守ること」1〜9 と、4 の画面の契約（CSP、classic なスクリプト、相対の href、`file://` で動く、JavaScript なしで読める、インラインの style を出さない）を破らない。
- 承認済みの構造の直し（`docs/plans/wiki-browse-structure-2026-11-11.md`。実装はまだ）と食い違わない。特に、描く側が機械の情報を持たないこと（P7）、読めない入力の扱い（4.1）。
- 実装者がこの設計だけで、静的版とサーバーで同じ結果になるものを作れる。規則に、二通りに読める箇所や、規則どうしのぶつかりがない。
- 今の実装（`info-hive-wiki/skills/info-hive/scripts/wiki_browse_core.py`、`wiki_browse.py`、`browse_assets/app.js`、`browse_assets/style.css`）と試験（`tests/wiki/test_browse.py`、`tests/wiki/test_browse_server.py`、`tests/wiki/browse/browse.test.mjs`、`tests/wiki/browse/startup.test.mjs`）から見て、設計が前提にしている事実が正しい。

## 特に見てほしいところ

- 2.1 の木の規則 N1〜N7 が、索引のファイルのありうる形（h1 がない、h1 が 2 つある、`index.md` がない、`index.md` が `indexes/` を指さない、`indexes/` のファイルが互いを指す、同じページが複数の場所にある、読めない索引のファイル）で、一つに決まるか。
- 2.2 のグループの ID が、木、一覧の `data-groups`、URL の `#group=` で一致し続けるか。サーバーで、ページと `nav.js` のあいだに作り直しが入った場合。
- 4.2 の要約の取り方（frontmatter、索引の行、本文の冒頭）が、lint とグラフの抽出の読み方、構造の直しの「内容」の分け方と食い違わないか。本文の冒頭の文が、wikilink、コード、表を含むときに、HTML のエスケープや絶対パスの検査（守ること 4）を破らないか。
- 5 の検索の、後からの読み込み（5.4）が、CSP、`file://`、サーバーのトークンつきの URL、世代の照らし合わせ（第 1 段階の 4）で成り立つか。読み込みの途中で世代が変わった場合。
- 9 の試験が、設計の約束を、実装に依らずに確かめられるか。

## 参考

- 試作: `poc/browse-findability/proto.py`、`poc/browse-findability/assets/proto.js`、`poc/browse-findability/assets/proto.css`。設計の案 D の下敷きである。試作は CSP の meta を持つが、今の版の試験にはかけていない。
- ADR-0010: `docs/adr/0010-wiki-browse-separates-core-from-delivery.md`（データの契約、決定 4 と 5）。
- 止める条件: 失敗も競合も入れない正しい使い方で、設計の約束が破れる反例を、重大として挙げる。表現の好みや、範囲の外（設計書の「範囲の外」と 11）に挙げたものは、重大にしない。

## 4 版目について

1 版目は却下された（`docs/agent-runs/2026-11-13-wiki-browse-findability/design-review-1.md`）。2 版目は、設計書の「1 回目のレビューで崩れた前提」と「レビューの指摘と対応」に、直した点を書いた。特に、2.1 の木の規則（N1〜N8）を、今と同じ木を組んでから畳む 2 つの段に書き直した。直した規則が、指摘の反例だけでなく、ほかの形の索引でも 1 通りに決まるかを見てほしい。試作（`poc/browse-findability/assets/proto.js`）は、変換中のキー、すべての所属を開くこと、`<mark>` の位置、タグの数え方を直したが、木の規則（2.1）はまだ 1 版目のままで、設計の下敷きにはしていない。

2 版目と 3 版目も却下された（`design-review-2.md`、`design-review-3.md`。重大 1 件ずつ）。3 回目の重大は、当てはめの例の表を手で書き、規則を動かして確かめていなかったことから来ていた。4 版目では、2.1 の木の規則を参照の実装 `docs/agent-runs/2026-11-13-wiki-browse-findability/nav_model.py` にし、表をその `--markdown` の出力から写した。N3 は 1 度だけ畳み、N6 の対象を `index.md` から来たグループのすべてにした。参照の実装が設計の文と食い違う箇所、参照の実装の例が網羅していない索引の形で、規則が 1 通りに決まらないか、木の性質（2.1 の末尾）が破れる入力を探してほしい。参照の実装は `python -X utf8 nav_model.py` で動く。
