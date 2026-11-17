# 依頼：ADR-0029 の段階1の敵対的レビュー（第6回、GPT-6 Astra）

日本語で報告する。対象のコード、文書、試験を変更しない。再委譲や別のモデルの追加レビューを起動しない。この依頼自体が、作者が指定した第6回の敵対的レビューである。

## 対象と規範

親リポジトリ: C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl
プラグイン: 親の info-hive-wiki/（ブランチ feat/links-stage1）。親は feat/adr-0029-stage1。
プラグインの git diff HEAD はこの依頼に添付される。未追跡の wiki_links.py と親の試験は --target でも指定する。
親の試験の差分は docs/agent-runs/2026-11-17-adr-0029-stage1-review/review-6-parent.target.diff を読む。

規範:
- docs/adr/0029-wiki-and-raw-hold-no-links.md（承認済みの作者の決定と不変条件）
- docs/plans/wiki-links-2026-11-16.md（実装の設計、11版目）
- docs/agent-runs/2026-11-17-adr-0029-stage1-review/review-5-continued.md（前回の指摘）
- 同じ場所の review-6-precheck.md（依頼元の照合記録。正しいと仮定せず、自分で検証する）

## 段階1の範囲

1. wiki_links.link_kind/is_link/find_links と check CLI。
2. wiki_pages.is_article_path とリンクを拒む walk_markdown/walk_pages/walk_index_files、Walk.links、article_path。
3. 拒んだことを黙って消さない通知。CLI の stderr、MCP の link_warnings/unverified と失敗理由、閲覧の診断。get_page/list_index のリンク拒否を「ない」に変えない。
4. lint の links/links_unchecked は wiki の側。raw の側は未実装で summary.links_raw は null。
5. SERVER_FILES の依存閉包と、その試験。名前が . で始まる項目の下は記事ではない。
6. 上記に必要な文書と CHANGELOG。

段階2〜4（resolve_raw、raw_sha256、raw の根の記録、raw 側の lint、wiki_fsguard、書き手の移行、取り込みの手順）は今回の対象外。未実装そのものは指摘しない。段階1単独で ADR の I1/I2/I4 の wiki の側を破る経路、今回の変更による既存機能の退行は対象である。作者の決定そのものは崩す対象ではない。


## 今回の確認対象

前回は review-5-continued.md（重大3件、軽微2件、却下）。最初の review-5.md は環境問題による部分レビューなので、第5回の最終報告は continued の方を使う。

前回の5件が閉じたかと、今回の共通化で別の欠陥が生まれたかを独立して確認する。修正内容と実行した試験は review-6-precheck.md、プラグインの第5回からの差分の変化は review-6-incremental.diff、親の現在の試験の差分は review-6-parent.target.diff にある。これらは依頼元の説明であり、正しいと仮定せず、現物のコードと ADR、設計に照合する。

第5回の重大1: propose のディレクトリ候補と evaluate の元のコーパスが、未保護の tree を通って記事のハードリンクを読む。
重大2: wiki 内かと記事かを混同し、通常の assets/candidate.md と、コーパス内の assets/image.png のハードリンクで誤って止まる。
重大3: _article_rel が abspath で途中の .. を畳み、検査するパスと実際の入力の意味が変わる。
軽微1: expected_calls が indexes のハードリンクのファイルについて、実装の scandir をモデル化していない。
軽微2: tree を NOT_ARTICLE、propose 全体を GATEWAY と分類し、関数に読む口の名前が1つあれば保護されるとする試験が、実際の分岐の漏れを見逃す。

重点:
- absolute_user_path と _article_rel と user_file_path の所属・記事の判定。根の別名、根より下のリンク、外部のファイル、記事でない入力、..、Windows と POSIX。検査済みのパスと実際に読むパスが一致するか。
- tree/copy_tree の wiki_root が、実際の利用者の入力に届くか。単一候補とディレクトリ候補、元のスキル、apply/rollback、run/evaluate の元コーパスと test_keys。引数を足しただけで渡し忘れた入口がないか。記事でない対象まで拒まないか。
- require_readable_articles が wiki の記事と記事までの道に正しい範囲で当たるか。トップの index/log/SCHEMA、indexes、未知・一覧不可、許した根のリンク。元のコーパスの読み取りは事前検査後も読む口を通すか。
- 元からの機能（評価のライフサイクル、候補のバイト列、CLI/MCP の通知、wiki の初期化の判定、外のソースの扱い）を壊していないか。
- 読み取りの分類表と実行の回帰試験の役割。わざと wiki_root の引き渡しを欠く対照を検出できるか。新しく追加した indexes の木が、エラーを入れる探索に含まれるか。

依頼元では計151件の unittest（9件 skip）、評価のライフサイクルとアダプターの2本の統合チェックが通った。POSIX 実機のリンクの回帰試験は Windows では skip。テストの通過を正しさの根拠とせず、必要な反例を絞って検証する。理由なく全試験を繰り返さない。実ユーザーの wiki と原本、追跡対象のファイルに書かない。

第5回の各指摘の閉鎖状況を明記する。重大には発生の度合い A（必ず踏む）、B（日常の使用で起こりうる）、C（まれな時機や名前）、D（作為的な配置が必要）を添える。実測、モック、コードからの推論を分け、現在のファイルと行番号を示す。重複した原因はまとめる。作者の決定や、段階2〜4の未実装それ自体は指摘しない。欠陥がなければ崩せなかったと書く。修正案は書かない。
