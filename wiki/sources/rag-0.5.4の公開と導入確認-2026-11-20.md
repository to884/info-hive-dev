---
type: "source"
title: "rag 0.5.4 の公開と導入確認"
authors: ["Codex"]
url: "https://github.com/to884/info-hive-rag/releases/tag/v0.5.4"
raw: "raw/rag-0.5.4の公開と導入確認-2026-11-20.json"
raw_sha256: "c9368c9ea7e883d3b2af7a4aac92f619a441e23e203e57d9b625064180192900"
created: 2026-11-20
updated: 2026-11-20
ingested: 2026-11-20
tags: ["rag", "リリース", "試験"]
entities: ["info-hive-rag"]
---

# rag 0.5.4 の公開と導入確認

[[info-hive-rag]] の PR #13 を main にマージし、コミット `9af30c3d46fd1699638ea87c908c8d1bb313bae8` に v0.5.4 のタグと GitHub リリースを作成した。
旧世代の回収と OCR 結果の再利用の修正を含む。
検証の根拠は [[rag全量ocr後のann保守と中断再開-2026-11-19]] と [[ragのocrキャッシュの再利用と回収-2026-11-20]] にある。

## 公開版の導入

Claude Code 2.1.325 の設定を隔離し、公開マーケットプレイスから rag@info-hive を新規導入した。
rag 0.5.4 と依存先 wiki 0.39.0 が有効になった。
v0.5.3 から変更された 6 ファイルのバイト列が v0.5.4 のタグと一致し、manifest の検査も成功した。
利用中の設定は変更せず、隔離した導入先は検証後に削除した。
証跡は `docs/agent-runs/2026-11-20-rag-0.5.4/claude-marketplace.json` にある。

## 検証と保持方針

製品の rag_index.py は検証時と同じ SHA-256 `021ea0774ec104f2b1b827498a6192bf64a68fc2d3dcb0d8d1d2373240aa7ab6` である。
Windows 回帰 84 件、Linux 82 件成功・2 件スキップ、実 MCP 21 項目の証跡を使った。
バージョンと変更履歴だけを公開用に更新し、製品スクリプトは変更していない。
再試行可能な内部ジョブの OCR は、失敗・キャンセル後も保持する。
マージ後の作業用リモート・ローカルブランチは削除した。
