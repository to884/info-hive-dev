# ADR-0029 段階1・第6回レビューの結果（2026年11月17日）

GPT-6 Astra（high）の最終判定は **採用可、確信度は高**。重大・軽微の指摘はともにない。第5回の重大3件・軽微2件を修正し、第6回で見つかった同じ読み取りの境界の問題と、その修正で生じた退行も、同じセッションの継続で修正・確認した。

**最終報告は [review-6-native.md](review-6-native.md)**。review-6.md、review-6-continued.md、review-6-final.md は、それぞれ修正前の時点の報告として保存している。

## 第5回の5件の修正

| 指摘 | 修正と確認 |
| --- | --- |
| 重大1：ディレクトリ候補・元コーパスを検査せず読む | 文字列とバイト列の読み取り、木のハッシュとコピー、ディレクトリへの降下を共通の検査に通した。候補、元のスキル、run/evaluate の元コーパス、apply/rollback の元スキルに検査の根を渡す。コーパスが wiki の一部なら元の根を引き継ぐ。実際の入口を動かし、拒む記事を読まずに停止することと、根を欠かす・誤った根を渡す対照を検出することを確認した |
| 重大2：記事でない通常の候補・assets のファイルまで拒否 | 所属の判定と記事の名前の判定を分け、記事でないものをリンクの記事の規則では拒まない。wiki 外、通常の記事、assets、非 Markdown、隠し項目下の候補について、同じバイト列を提案に使えることを確認した。除外領域内のコーパスでも新たな記事を作らない |
| 重大3：途中の .. を畳み、検査先と入力が変わる | 絶対化前に .. を拒む。根の別名は祖先を上から解決し、既知の根に届いたらその下を解決せず検査する。OS 上の名前とコマンド表記を分け、POSIX のコロンやバックスラッシュも別の読み取りへ流れないようにした |
| 軽微1：indexes のハードリンクの呼び出しモデルが不一致 | expected_calls に実装の scandir を反映した。該当する木を TREES に加え、結果だけでなく呼び出しごとの失敗を入れる探索でも検査した |
| 軽微2：読む口の名前が関数にあれば保護済みとする試験 | 分類表は静的な目録であると明記し、実行の回帰試験と対照に保証を移した。tree/copy_tree の分類を実態に合わせ、コーパスの専用試験もソースの文字列の順序から実際の入口の実行に置き換えた |

## 共通化した境界

- absolute_user_path は、意味を変える途中の .. を正規化前に拒む。
- _article_rel は根の所属を調べる。文字列を小文字化した長さではなく、パスの要素で比較・切り出しを行う。
- user_file_path、user_directory_path、read_user_file、read_user_bytes は記事と記事までの道を検査し、検査した同じ名前を使う。
- source_wiki_root は、部分木が属する元の wiki の根を保持する。コーパス自身を一律に新たな wiki の根にはしない。
- article_path と記事の名前の判定は native を受け取り、OS 上の名前とコマンドの区切り表記を区別する。走査、統計、lint、根拠ページ、MCP の物理的なファイルの読み取りで、出所に合わせたモードを使う。
- tree は os.walk の一覧取得の失敗を捨てず、元の例外を伝える。根・途中のディレクトリが一覧不可でも、空の木や完全な写しとして進まない。

第6回では、根の別名と配下の外向きリンク、部分コーパスの根の取り違え、POSIX のコロン名、一覧取得失敗、バックスラッシュ名の変換、走査と読む口の分類不一致も確認した。これらは修正後の各続報で閉鎖を確認し、最終報告には残る指摘がない。

## 最終状態の検証

作業ディレクトリは C:/Works/info-hive-dev/.claude/worktrees/adr-0029-impl。

| チェック | 結果 |
| --- | --- |
| python -X utf8 -B tests/wiki/test_wiki_links.py | 63件、成功、6件 skip |
| python -X utf8 -B tests/wiki/test_walk.py | 18件、成功、2件 skip |
| python -X utf8 -B tests/wiki/test_wiki_evolve_newlines.py | 12件、成功 |
| python -X utf8 -B tests/wiki/test_page_set.py | 30件、成功、1件 skip |
| uv run --with pyyaml python -X utf8 -B tests/wiki/test_uninitialized_wiki.py | 41件、成功、2件 skip |
| python -X utf8 -B info-hive-wiki/eval/evolution/test_evolution.py | ライフサイクル、却下、復旧、分離、検証、パイロットの契約が PASS |
| python -X utf8 -B info-hive-wiki/eval/evolution/test_adapters.py | 9種類のアダプター等が PASS |
| 親とプラグインの git diff --check | 指摘なし |

計164件の unittest は失敗なし（11件 skip）、統合チェック2本も通過した。Windows の実ジャンクションとハードリンクを使った回帰を含む。POSIX の実リンクと ..、実ファイル名のコロン、バックスラッシュの3試験は、この Windows 環境では skip した。POSIX のパス・属性を差し替えた検査は Windows でも実行し、実機の確認とは区別している。

Astra は差分、規範、実装を照合し、反例に絞ったモックや既存のテストメソッドを実行した。依頼元の164件と統合チェック2本を毎回全実行したという判定ではなく、これまでの閉鎖判定と最新の差分の確認を合わせた結果である。段階2〜4や、全機能の統合検証が完了したとはしていない。

## 対象の固定と記録

- セッション: 01a1e9b3-9ddf-7443-b3ec-f69e677fe115。
- 最初の依頼: task-6.md。続きは task-6-continuation.md、task-6-final.md、task-6-native.md。
- 最新の実ファイルの差分: review-6-native.delta.diff。
- プラグイン全体と親の試験のスナップショット: review-6-native-plugin.target.diff、review-6-native-parent.target.diff。
- 最新の28ファイルのハッシュ: review-6-native-input-sha256.json。
- レビュー後の照合: review-6-native-input-check.json。28ファイルに変更はなく、両方の差分もスナップショットと一致した。

変更は未コミット。CHANGELOG の Unreleased に記録し、バージョンはまだ上げていない。PR、マージ、公開は行っていない。変更を引き続き確認・取り込めるよう、元の worktree とブランチを保持する。
