---
type: "source"
title: "Box Drive 上での info-hive wiki の動作"
authors: ["Codex"]
tags: ["windows", "試験", "wiki設計"]
created: 2026-11-19
updated: 2026-11-19
ingested: 2026-11-19
raw: "raw/box-driveでのwiki互換性-2026-11-19.json"
raw_sha256: "f7793b7841bff4883e16a6d58c42bd6ea82f0f8b9ddc6246a4e600c9ff48c547"
---

# Box Drive 上での info-hive wiki の動作

Windows 11、Box Drive 2.56.271 の Cloud Files 方式、wiki v0.38.1 を組み合わせた 1 台の PC で、架空の wiki の初期化、原本保存、記事の再編集、検索、lint、グラフ生成と照会、browse が通った。オンライン専用に戻した記事と原本も再取得できた。 [調査レポート](../../docs/deep-dive/2026-11-19-box-drive-wiki.md)

- 管理用ツールに見える Cloud Files の再解析点は通常の Python の `os.lstat()` からは見えず、書き込みガードを通った。 [Microsoft の互換性仕様](https://learn.microsoft.com/en-us/windows/win32/cfapi/build-a-cloud-file-sync-engine#compatibility-with-applications-that-use-reparse-points)
- グラフ DB の読み取り接続を開いたまま再生成すると、Box とローカルの両方で Windows の置き換えが拒否された。接続を閉じると両方で再生成できた。
- Box の競合検出はファイル単位。`index.md` と `log.md` を共有する複数端末の同時編集は避け、共有には確定版のアーカイブや静的 HTML を使う。Box Web の表示、2 台目への同期、通信切断中の操作は未検証。 [Box のファイル競合](https://support.box.com/hc/en-us/articles/360044193873-File-Version-Conflicts)

## 取り込んだ内容と載せたページ

| 番号 | 取り込んだ内容 | 出典の該当箇所 | 掲載方法 | 掲載ページと理由 |
| --- | --- | --- | --- | --- |
| c1 | 単一端末の操作とオンライン専用からの再取得 | 実測記録の results | update | [[info-hive-wiki]] に互換性試験への入口を追加 |
| c2 | 複数端末の編集を避ける判断 | 調査レポートの「複数端末で共有するときの制約」 | update | [[info-hive-wiki]] に共有方法を追記 |

## 関係するページ

- [[box-drive上のwikiの運用]]
- [[box-drive-wiki-compatibility-2026-11-19]]
- [[info-hive-wiki]]
- [[info-hive-wikiのアーキテクチャ-v0.38.1]]
- [[windowsのファイルの共有と削除待ち]]
