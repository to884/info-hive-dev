# 依頼：ADR-0029 の実装の段階 1 の敵対的レビュー（4 回目）

応答は日本語で書く。ファイルは変えない。

## 対象

info-hive-wiki（サブモジュール、ブランチ `feat/links-stage1`、基点は v0.25.2 の `e8886d6`）の作業ツリーの差分（埋め込んだ diff）と、新しいファイル `skills/info-hive/scripts/wiki_links.py`。あわせて、親のリポジトリの試験 `tests/wiki/test_wiki_links.py`（新規）、`tests/wiki/test_walk.py`、`tests/wiki/test_page_set.py`、`tests/wiki/test_uninitialized_wiki.py` の変更。

## 位置づけ

ADR-0029（`C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/docs/adr/0029-wiki-and-raw-hold-no-links.md`、承認済み）は、wiki と raw の記事にリンクを置かない規則を決め、実装の設計は `C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/docs/plans/wiki-links-2026-11-16.md` にある。マーケットプレイスは info-hive-wiki の main を配るので、段階ごとに、その段階が触る不変条件をそれだけで満たす必要がある。段階 1 は、次をまとめて入れる。

- リンクの判定（`wiki_links.link_kind()`、`is_link()`、`find_links()`、CLI の `check`）
- 記事の名前の規則（`wiki_pages.is_article_path()`）と、リンクを拒む走査（`walk_markdown()`、`walk_pages()`、`walk_index_files()`。`Walk.links`）、記事を読む口（`article_path()`）
- 読む側の `link_warnings`（MCP の `query`、`get_page`、`list_index`、`lint`、`stats`、`graph`、CLI の検索と統計、閲覧の診断）と、`get_page`・`list_index` の「ない」でなく「リンクなので読まない」（`LinkRefused`）
- lint の指摘 `links`、`links_unchecked`（wiki の側だけ。raw の側は段階 2 で、`summary.links_raw` は `null`）
- `SERVER_FILES` の不足の補い（`wiki_links`、`wiki_decide`、`wiki_captions`、`wiki_browse_core`、`wiki_browse_fs`）と、読み込みをたどって足りていることを確かめる試験
- 名前が `.` で始まる項目の下を、どの深さでも記事にしない（作者の決定の 6。0.25 まではページだった）
- 文書と CHANGELOG

段階 2 以降に回したもの：`resolve_raw()`、`raw_sha256:`、raw の根の記録、lint の raw の側、書き込みの部品（`wiki_fsguard.py`）、取り込みの手順。これらが無いこと自体は指摘しない。ただし、段階 1 が入った main で、段階 1 が触った不変条件（ADR-0029 の I1、I2、I4 の wiki の側）が破れる経路があれば挙げる。

## 前回のレビュー

3 回目（`review-3.md`、却下）の重大 5 件と軽微 3 件を直した。3 回目は、知らせの受け皿の形そのものは崩せなかったと報告した。残ったのは、記事を読む口を通らない直接の読み取り（評価ループのパターンのページ、判定のレイヤーの入力）と、受け皿の周りの食い違い（アップグレードの「追いついている」、Windows の S_IFBLK の読み替え、検索の JSON の二重の走査、プロセスの知らせの増え方）だった。

直接の読み取りは、1 つずつ探す形をやめ、スクリプトの中のすべてのファイルの読み取り（read_text、read_bytes、open）を関数ごとに分類する表の試験（`tests/wiki/test_wiki_links.py` の `ReadSiteInventoryTests`）で閉じた。新しく読み取りを足した関数は、分類しないと試験が落ちる。読む口を通すと分類した関数は、読む口を本当に呼ぶことも確かめる。この表の分類に誤りがないか（記事を読んでいるのに「記事でない」「raw」「作業用の写し」に入れたもの）を、とくに確かめる。

そのほか、評価ループは書く先の記事をすべて先に確かめる。アップグレードは調べなかったとき None を返し、「調べていない」と出す。判定の部品（`wiki_links.is_link()`、`find_links()`）は走査と同じ `_stat_entry()` を使う。検索の JSON は、ページを集めた走査の知らせから作る。プロセスの知らせは、CLI のときだけ重ねずに貯める。前回と同じ指摘の繰り返しは、直せていなければ直せていないこととして挙げる。

## 見ること

- 走査がリンクを拒む判定に、漏れか誤りがないか（Windows と POSIX、ジャンクション、ディレクトリとファイルのシンボリックリンク、ハードリンク、名前の代理のリパースポイント、先のないリンク、一覧と lstat の間の置き換え）。`DirEntry.stat(follow_symlinks=False)` と `os.lstat()` の使い分けが正しいか。
- 拒んだことが「ない」に変わる経路が残っていないか（I4）。走査の結果を使う側のうち、`link_warnings` が届かないもの、記事を走査や読む口を通さずに直接読むもの（`read_text`、`read_bytes`、`open` を探す）。lint の broken_links と orphans の扱い。
- `article_path()` が根の外へ出る名前を拒むか。`list_index` の `name` の扱いが、前のコード（`resolve()` と `is_relative_to()`）より弱くなっていないか。
- 試験が、狙った振る舞いを確かめているか。`test_walk.py` の木の答え（`model`、`expected_calls`）と、対照（わざと決まりを破った実装）が、変えた走査の決まりを正しく写しているか。
- `SERVER_FILES` の試験が、足りないものを見逃す形になっていないか。
- 既存の振る舞いを壊していないか（閲覧の写しと世代、MCP の索引の印、統計、YouTube の字幕の照合が使う `visited`）。

重大の指摘には、発生の度合いを添える。A（仕様の矛盾か欠落で、必ず踏む）、B（日常の使い方で起きうる）、C（まれな時機や名前）、D（作為的な配置が要る）。ADR-0029 と実装の設計の作者の決定は崩す対象ではない。

## 読むもの

- 差分（埋め込み）、`skills/info-hive/scripts/wiki_links.py`
- 試験: `C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/tests/wiki/`
- ADR と設計: 上のパス
- コード全体: この作業ツリー（`C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl/info-hive-wiki/`）
