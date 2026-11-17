# ページの概要の生成と表示（wiki 0.32.0）の作業記録

2026年11月18日。設計、実装、公開と導入の確認を記録する。

## 設計と実装

- 作者は保存設計第6版を承認し、段階1を実装した。表示設計は第3版で、Astra の最終判定は採用可だった。
- `/wiki:overview` は求めた1ページだけから概要を作る。元記事を編集せず、format 2 のサイドカーに Markdown と SVG をまとめる。CLI だけが書き、閲覧は読み取りだけである。
- サーバーと静的版の browse は、最初のトップレベル h1 の直後、h1 がなければ本文先頭に概要を差し込む。新しい概要は開き、古い概要は警告付きで閉じる。
- 概要は検索、見出し ID、被リンク、ページ数、グラフに含めない。元記事と概要を同じ Snapshot から判定する。
- SVG は内容の SHA-256 で名付け、img で出す。Mermaid は既存の sandbox で描き、静的版はコードを示す。CSP と配色の規則は既存の図と共用する。
- main の Codex ADR が0031を使っていたため、概要の決定は ADR-0033 に移した。過去のレビュー記録は旧番号を残す。

## レビューで修正したこと

- 保存済み本文の先頭と末尾の空白を保ち、64 KiB の境界を共有の検査で扱う。ページ先頭の BOM は1個だけ取り除き、status と browse のハッシュを一致させた。
- Opus の初回実装レビューで、リンクの裏に隠れた記事を孤立と誤判定し、概要を消せる反例が見つかった。拒否した記事の道と概要の識別子を照合して page_unreadable とし、remove --orphan では消さない。
- 規定名のハードリンクの概要は broken/unreadable として一覧に残し、恒久的な拒否を transient にしない。属性の拒否印を署名に含め、リンク数だけが戻った場合も回復を検出する。
- 第2回と第3回の判定は採用可。最終は確信度が中〜高で、致命的・重大は0件。
- 概要が壊れて識別子を読めず、不在を確かめられない場合は削除を拒む。人が対応と不要であることを確認した場合の、サイドカーだけを削除する復旧手順を残した。

## 検証

- 関連 Python 410件、入出力と障害注入33件、プラグイン内116件で失敗なし。最終の概要・help・ひな形・Codexの140件も失敗なし（1件skip）。UTF-8入出力の静的検査は63ファイルで指摘なし。
- 5ブラウザ（Chromium、Firefox、WebKit、Edge、Chrome）×2方式×2配色の20ケースで失敗なし。Tab、Enter、Space、320px、閉じた図を開く操作、Mermaidの配色の再描画、手書きSVGの明るい地を確認。CSP違反・外部への自動通信・style属性は0、wikiは不変。
- 1,000ページの起動は本文中央値2.873秒、索引3.467秒で、従来の5秒基準を通過した。同じホストの main でも時間の変動があり、遅かった先行実行を新機能の回帰とは断定しない。
- 実MCPサーバーで lint と CLI の一致を確認。Codex の隔離したローカル導入で2スキル・7ツールを認識し、統計と日本語検索が成功した。

## 公開

プラグイン PR #90 と親 PR #177 の全 CI 成功後、プラグインを先にマージした。main の d761c62f680e923751dd02e00e982c67a3e3be0e に注釈付きタグ v0.32.0 を付け、GitHub リリースを公開した。公開時刻は2026年11月18日08:08:11（Asia/Tokyo）。

使い捨ての CLAUDE_CONFIG_DIR と CODEX_HOME で、公開カタログ to884/info-hive-marketplace から wiki@info-hive を導入した。両ホストの版は0.32.0で、0.31.1から変わった全25ファイルがタグとバイト単位・SHA-256で一致した。各導入先で概要の保存、新しい概要のh1直後への表示、SVGの配信データ、元記事を変えないこと、記事更新後のstaleと折りたたみを確認した。使い捨ての設定とfixtureは削除済み。

導入済みのスクリプトを直接呼ぶ試験であり、モデルに生成を推論させる試験ではない。プラグインのリモートブランチとローカルブランチは削除済み。親PRには公開の記録とタグのマージコミットを指すサブモジュール参照を追加する。

## 根拠の位置

- `docs/plans/wiki-overview-2026-11-17.md`、`docs/plans/wiki-browse-overview-2026-11-17.md`、`docs/adr/0033-wiki-page-overview-lives-in-a-sidecar.md`。
- `docs/agent-runs/2026-11-18-wiki-overview/implementation.md`、`impl-review-1-opus.md`〜`impl-review-3-opus.md`、`overview-browser-final.json`、`startup-comparison.json`、`codex-local-smoke.json`。

公開の根拠は `release.json`、`ci-before-plugin-merge.json`、`claude-marketplace.json`、`codex-marketplace.json`（同じ agent-runs のディレクトリ）。

公開カタログからの別のCodex隔離導入でも、2スキルと7 MCPツールを認識し、統計と日本語検索が成功した。読む前後でfixtureのwikiはバイト単位で一致した（`codex-marketplace-mcp.json`）。
