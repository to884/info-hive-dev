# 依頼：ADR-0029 の実装の段階1の敵対的レビュー（第5回、GPT-6 Astra）

応答は日本語で書く。コード、試験、設計書を変更しない。この依頼自体がレビューであり、別のモデルやサブエージェントへの再委譲や追加レビューを起動しない。

## 対象と規範

親リポジトリ: C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl
プラグイン: 親の info-hive-wiki/（ブランチ feat/links-stage1）。親は feat/adr-0029-stage1。
プラグインの git diff HEAD はこの依頼に添付される。未追跡の wiki_links.py と親の試験は --target でも指定する。
親の試験の差分は docs/agent-runs/2026-11-17-adr-0029-stage1-review/review-5-parent.target.diff を読む。

規範:
- docs/adr/0029-wiki-and-raw-hold-no-links.md（承認済みの作者の決定と不変条件）
- docs/plans/wiki-links-2026-11-16.md（実装の設計、11版目）
- docs/agent-runs/2026-11-17-adr-0029-stage1-review/review-4.md（前回の指摘）
- 同じ場所の review-5-precheck.md（依頼元の照合記録。正しいと仮定せず、自分で検証する）

## 段階1の範囲

1. wiki_links.link_kind/is_link/find_links と check CLI。
2. wiki_pages.is_article_path とリンクを拒む walk_markdown/walk_pages/walk_index_files、Walk.links、article_path。
3. 拒んだことを黙って消さない通知。CLI の stderr、MCP の link_warnings/unverified と失敗理由、閲覧の診断。get_page/list_index のリンク拒否を「ない」に変えない。
4. lint の links/links_unchecked は wiki の側。raw の側は未実装で summary.links_raw は null。
5. SERVER_FILES の依存閉包と、その試験。名前が . で始まる項目の下は記事ではない。
6. 上記に必要な文書と CHANGELOG。

段階2〜4（resolve_raw、raw_sha256、raw の根の記録、raw 側の lint、wiki_fsguard、書き手の移行、取り込みの手順）は今回の対象外。未実装そのものは指摘しない。段階1単独で ADR の I1/I2/I4 の wiki の側を破る経路、今回の変更による既存機能の退行は対象である。作者の決定そのものは崩す対象ではない。

## 第4回の修正として入っている変更（成否は自分で判断する）

第4回は重大4件（B3、D1）、軽微2件で却下だった。
- 重大1: read_user_file の所属判定を _article_rel にまとめ、根の綴りと realpath、入力の綴りと親だけを realpath したものを比較する。根自体のリンクは許し、ファイルのリンクは解決しない意図。
- 重大2: wiki_youtube.parse_page_args に wiki を渡して read_user_file を使う。wiki_evolve.propose の単一 candidate は _article_rel と article_path の検査後に read_bytes する。
- 重大3: wiki_evolve_loop.run は元 corpus を読む前に find_links(corpus, origin=corpus, articles_only=True) で検査し、リンクまたは未確認なら止める。
- 重大4: CLI 判定は _same_dir の samefile と normcase の代替比較を使い、常駐サーバーのファイル名を小文字化して除外する。
- 軽微1: test_walk の model_index/expected_calls は indexes という名前のハードリンクの通常ファイルを道として扱わない。
- 軽微2: 読み取り箇所の分類表は裸の open だけでなく Path.open 等の属性呼び出しも検出する。

## 重点

前回の6件が閉じているか、新たな反例があるかを別々に判定する。修正前のコードの行番号を現在のコードの根拠にしない。

- _article_rel の「wiki 内」と article_path/is_article_path の「記事」の区別。外部のソース、記事でない入力、raw、根の別名、途中のリンク、..、大小文字、エラー時の扱い。検査したパスと実際に読むパスが一致するか。
- 利用者が渡す入力の全入口。単一ファイルとディレクトリ、字幕の --page、propose の --candidate、decide の入力、評価ループの corpus。直接の read_text/read_bytes/open が分類名だけで保護されたことになっていないか。
- コーパス検査が、実際に読む記事をすべて対象にするか。評価ループの実行用スクリプトのコピーと遅延 import を含め、新しい依存で既存の実行が壊れないか。
- CLI の直接実行、大小文字、根のジャンクション、MCP/閲覧で通知が欠けたり、別の呼び出しに漏れたりしないか。
- 走査、lint、MCP 索引/検索/get_page/list_index/stats/graph、閲覧の既存動作と通知の整合性。リンクで拒んだものと調べられないものを、空や不存在に変える経路。
- 読み取り分類表の検出範囲と分類の真偽、GATEWAY の関数内に呼び出しが1個あるだけの偽の保証、SERVER_FILES の依存閉包。
- 第4回の回帰試験が失敗の再現を検査するか。ソースの文字列を見ているだけの試験は、実行時の保証と区別する。

依頼元は test_wiki_links.py（40件、skip3）と test_walk.py（18件、skip2）を実行し成功した。通過自体を正しさの根拠にしない。必要な反例に絞り、既存の対象試験か一時ディレクトリでの小さな検証を使う。実ユーザーの wiki や原本、追跡対象のファイルは変更しない。理由なく全試験を繰り返さない。

## 報告

敵対的レビューの指定書式に従う。第4回の各指摘の閉鎖状況も短く示す。重大な指摘には発生の度合い A（仕様の矛盾/欠落で必ず踏む）、B（日常の使用で起こりうる）、C（まれな時機/名前）、D（作為的な配置が必要）を付ける。具体的な入力、呼び出し、結果、現在のファイルと行番号を示す。実測と推測を区別し、同じ根本原因はまとめる。欠陥の数を増やすために、対象外やすでに保証しないと決めたことを指摘しない。修正案は出さない。
