# Opus レビューの指摘に対する反証と対応

対象は 2026-11-20 の図解 HTML と参照記録。初回レビューは Major 1件、Minor 3件で REJECTED だった。指摘の数ではなく、固定ソースと現行の説明を照合した。修正後の Opus の再レビューは行っていない。

## Major: 公開版の前提と Ossie の必須性

反証として、Ossie を使わない公開版を許す分岐がないか、固定した wiki_apply.py と wiki_public_projection.py を確認した。しかし REQUIRED が Ossie の6成果物と graph/ontology.yaml、ontology/definition.json、graph.sqlite を要求し、article_documents が WikiArticle / sem_articles を検査するため、指摘を覆せなかった。

採用した。公開版を検証向けの拡張と明記し、定義・Ossie・wiki 外の raw の根、PoC での初回候補・計画の準備を目立つ位置に追加した。「Ossie があれば」という条件付き説明をやめ、公開版では必須とした。プラグインの適用・読取機能と、初回セットアップが完結することを区別した。

実行による確認: verify_sources.py で Ossie のない候補が verify_files に拒否されること、Ossie の必須パスが6つあることを確認した。初回生成の経路は git grep と PoC の関数を照合した。

## Minor: 状態ではなく都度選ぶ検索モードに見える

反証として release_id 未指定の resolve_publication と MCP の query の呼び出しを確認した。有効な公開版がある wiki は既定でその版を読むため、指摘を覆せなかった。

採用した。ボタンは wiki の状態ごとの「説明」の切替とし、実際の wiki を操作しないことを記した。保存の分岐も「公開版なし／あり」に変更した。公開版を使う wiki は通常保存と版未指定の読み取りが公開版を使い、ライブへ戻すには return-live が必要とした。

## Minor: 目次と検索索引の混在

反証としてモバイル版と SVG の desc を確認した。index.md を指す2箇所が索引と表記されていたため採用した。index.md は目次、検索用の索引は検索索引として区別し、モバイル版とテキスト代替も揃えた。

## Minor: 参照ファイルの記録の不足

各主張は固定ソースのリンクで確認できるため、本文の誤りではない。しかし SHA-256 の記録としては不足があると確認した。

採用した。wiki_lint.py、wiki_search.py、wiki_browse_pele.py、wiki_decide.py と、初回準備の PoC 2ファイルを固定して追加した。myKG の manifest をパスと SHA-256 で関連付け、版の根拠には固定コミットの pyproject.toml を加えた。

## 修正後の検証

- source-verification.json: 固定ソース44ファイルの SHA-256、myKG manifest の SHA-256、公開版の必須ファイルと説明を確認した。
- verification.json: 幅360・375・1024・1440px、明暗の計5条件で、層・wiki状態の説明・導入案・配色・詳細の開閉・表のキー操作を確認した。本文の横はみ出し、JavaScript 例外、外部依存の読み込みはなかった。
- 画面の検査は、抽出の精度、性能、費用、本番の保存先の適性を検証するものではない。
