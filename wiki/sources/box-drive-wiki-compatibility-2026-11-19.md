---
type: "source"
title: "Box Drive 上の wiki の互換性試験の経験"
authors: ["Codex"]
tags: ["windows", "試験", "wiki設計"]
created: 2026-11-19
updated: 2026-11-19
ingested: 2026-11-19
raw: "raw/experiences/box-drive-wiki-compatibility-2026-11-19.json"
raw_sha256: "1ea26bba298c6eb910c70e6e4c3e971a43d347d94d797bdd920c73238c7c2768"
---

# Box Drive 上の wiki の互換性試験の経験

[[box-driveでのwiki互換性-2026-11-19]] の実測を、同じ条件で確認し直せる形にまとめた。対象は Windows 11 Enterprise（ビルド 26300）、Box Drive 2.56.271.0（Cloud Files 方式）、Python 3.14.6、wiki v0.38.1（コミット `b8596d1`）。同じ架空の記事 1 ページと原本を、Box と非同期のローカルフォルダーにそれぞれ置いた。実験を担当した Codex のモデル ID は実測記録から特定できない。

- Box 上で初期化、原本保存、記事とログの置き換え、CLI と MCP の検索、lint、グラフ生成と照会、browse が成功した。
- 試験記事と原本をオンライン専用にした後、MCP 検索が再編集後の本文を返し、原本の SHA-256 が保存前と一致した。
- グラフ DB の読み取り接続を開いたまま再生成すると、Box とローカルの両方で `WinError 5` が発生した。接続を閉じると両方で連続 2 回成功した。
- 別端末との同期と競合、通信切断時の操作、旧方式では試験していない。複数端末での競合は Box のファイル単位の同期仕様から判断した。

## 取り込んだ内容と載せたページ

| 番号 | 取り込んだ内容 | 出典の該当箇所 | 掲載方法 | 掲載ページと理由 |
| --- | --- | --- | --- | --- |
| c1 | 単一端末で確認した操作とオンライン専用からの再取得 | actions、verification、scope | create | [[box-drive上のwikiの運用]] の動作表に記録 |
| c2 | DB を開いている間の置き換え失敗と、接続を閉じた後の成功 | verification、counterexamples | create | [[box-drive上のwikiの運用]] に復旧できる条件を記録 |
| c3 | 端末をまたぐ運用への適用限界 | hypothesis、counterexamples | create | [[box-drive上のwikiの運用]] に同期仕様から分かる制約を記録 |

## 関係するページ

- [[box-drive上のwikiの運用]]
- [[box-driveでのwiki互換性-2026-11-19]]
- [[windowsのファイルの共有と削除待ち]]
