# 第6回の前に行った修正と検証

第5回の重大3件・軽微2件を修正した。プラグインのバージョンはマージ前に決めるため、今回は Unreleased の変更履歴に記録した。

## 読み取りの境界

- wiki_pages.absolute_user_path は、途中の .. を正規化する前に拒否する。_article_rel、候補とスキルの入力、tree/copy_tree が使う。
- user_file_path が「wiki 内か」と article_path の「記事か」を分ける。通常の記事は検査済みの同じパスを読み、記事でない入力は記事のリンクの規則では拒まない。read_user_file と新しい read_user_bytes はこの共通の処理を使う。
- tree と copy_tree は wiki_root を受け取り、ハッシュ計算だけでなく実際にコピーする読み取りも検査する。propose の単一候補、ディレクトリ候補、wiki 内にある元のスキルが、この検査を使う。apply/rollback の元のスキルのハッシュも、CLI から wiki_root を受け取る。
- コーパスの事前検査は require_readable_articles にまとめた。wiki の走査、索引、ログ、SCHEMA の記事だけを対象とし、raw 用の find_links を wiki 全体に使わない。run と evaluate の両方に適用した。元のコーパスのコピーと run の test_keys の読み取りも、同じ読む口を使う。
- 設定等のファイル入力も、wiki が分かる呼び出しでは共通の読み取りを通す。capture/evaluate を wiki の情報を持たずに呼ぶ既存のライブラリ用の呼び出しは維持した。

## 回帰試験

ReviewFiveTests を追加し、実ファイルの候補、ハードリンクの記事、ディレクトリの候補、wiki 内の元のスキル、evaluate の元コーパス、対象外の assets のハードリンク、途中の .. を検査する。通常の候補の CRLF が変わらないことも検査する。tree への wiki_root の引き渡しをわざと欠く対照では、同じ回帰の検査が失敗することを確認する。

第4回のコーパスの試験は、ソースの文字列の順序の検査から、実際に run を呼び出す試験に置き換えた。

読み取りの分類表は、静的な参照の目録であることを明記した。tree と copy_tree を GATEWAY にし、read_user_bytes、user_file_path 等を含めた。関数内の全分岐の保護を証明するとは主張しない。

expected_calls は、indexes がハードリンクの通常ファイルでも実装が scandir を呼ぶことをモデルに反映した。この木を TREES に追加し、結果の照合だけでなく、呼び出しごとの失敗を入れる探索の対象にもした。

## 実行したチェック

- python -X utf8 -B tests/wiki/test_wiki_links.py: 50件、成功、4件 skip。
- python -X utf8 -B tests/wiki/test_walk.py: 18件、成功、2件 skip。
- python -X utf8 -B tests/wiki/test_wiki_evolve_newlines.py: 12件、成功。
- python -X utf8 -B tests/wiki/test_page_set.py: 30件、成功、1件 skip。
- uv run --with pyyaml python -X utf8 -B tests/wiki/test_uninitialized_wiki.py: 41件、成功、2件 skip。
- python -X utf8 -B info-hive-wiki/eval/evolution/test_evolution.py: ライフサイクル、却下、復旧、分離、検証、パイロットの契約が PASS。
- python -X utf8 -B info-hive-wiki/eval/evolution/test_adapters.py: 9種類のアダプター等が PASS。
- 親とプラグインの git diff --check: 指摘なし。

計151件の unittest（9件 skip）と、上記2本の実行可能な統合チェック。スキップのうち1件は、POSIX の実リンクと .. を使う新しい回帰試験で、Windows では実行できない。正規化より前に拒否する回帰試験は Windows でも実行し、通過した。

実装途中には残っていたローカル import のための UnboundLocalError、wiki を受け取らない既存のライブラリ用の呼び出しとの不整合を検出して修正した。未初期化 wiki の試験は最初に PyYAML 不足で失敗したが、依存を用意した uv の環境では通過した。
