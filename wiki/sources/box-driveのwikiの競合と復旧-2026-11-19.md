---
type: "source"
title: "Box Drive と Box Web による wiki の競合・復旧試験"
authors: ["Codex"]
tags: ["windows", "試験", "wiki設計"]
created: 2026-11-19
updated: 2026-11-19
ingested: 2026-11-19
raw: "raw/box-driveのwikiの競合と復旧-2026-11-19.json"
raw_sha256: "91c196d1fb0fbf5a982c745026b350304646d9d810abc0a467169e05eb823747"
---

# Box Drive と Box Web による wiki の競合・復旧試験

Windows 11 の 1 台で、Box Drive 2.56.271.0（Cloud Files 方式）と Edge の Box Web を独立した書き手として使った。同じ Box アカウントの架空の wiki を対象に、info-hive wiki v0.39.0 で確認した。

## 競合の再現

記事、`index.md`、`log.md` の共通版を同期してから、Box Drive の Box への通信を遮断した。Box Drive 側で 3 ファイルを更新し、通信遮断中に Box Web 側から別内容の 3 ファイルを同名でアップロードした。

| ファイル | Box Drive を再接続した後 |
| --- | --- |
| `concepts/guide.md` | 正規名に Web 版が残り、Box Drive 版が別名コピーになった。記事の別々の節に入れた変更も、Box では自動統合されなかった。 |
| `index.md` | 正規名に Web 版が残り、Box Drive 版が別名コピーになった。各版はそれぞれ片方の変更だけを反映した。 |
| `log.md` | 正規名に Web 版が残り、Box Drive 版が別名コピーになった。それぞれの追記は別のファイルに残った。 |

> Codex 補足: 3 ファイルが個別に競合し、正規名が指す内容と別名コピーを SHA-1 で区別できた。両方の内容が Box に保存されたことを API 応答でも照合した。

## 復旧の実測

共通版と回収した 2 つの版を同期外に置いた。記事の離れた節の変更は三方向マージで統合できた。同じ行に別の変更を加えた対照試験では競合が出た。索引は確定した記事の内容から 1 項目にまとめ、ログには両方の操作を 1 回ずつ反映した。

双方の変更を正規の記事から BM25 で検索でき、リンク切れと重複スラッグは 0 件だった。グラフを再生成できた。復旧版の 3 ファイルを Box の正規名へ同期し、SHA-1 を照合した。競合コピーも 3 ファイルとも wiki 外へ退避し、退避先で Box の SHA-1 が一致した。

別々の記事が残り、索引の項目とログの操作だけが片方ずつ欠けた状態をローカルで再現した。リンク切れと孤立ページはどちらも 0 件だった。索引と操作記録は復旧前に保全した 2 つの版と照合する必要がある。

2 台の Box Drive、別アカウント、同時の再接続、別々の記事を編集する場合のクラウド側の競合は未検証。 [Box のファイル競合](https://support.box.com/hc/en-us/articles/360044193873-File-Version-Conflicts) [Box の版履歴](https://support.box.com/hc/en-us/articles/360043697054-Accessing-Version-History)

## 取り込んだ内容と載せたページ

| 番号 | 取り込んだ内容 | 出典の該当箇所 | 掲載方法 | 掲載ページと理由 |
| --- | --- | --- | --- | --- |
| c1 | 3 ファイルが個別に競合し、両方の版が保存された | conflicts.local、conflicts.cloud_api | update | [[box-drive上のwikiの運用]] に実機で確認した競合を追記 |
| c2 | 3 ファイルの統合、同期、競合コピーの退避に成功した | recovery | update | [[box-drive上のwikiの運用]] に復旧手順を追記 |
| c3 | 別々の記事が残っても索引とログの欠落は通常の lint で検出できなかった | recovery.distinct_article_mixed_local_only | update | [[box-drive上のwikiの運用]] に手元の版との照合を追加 |

## 関係するページ

- [[box-drive上のwikiの運用]]
- [[box-driveのオフライン編集と再同期-2026-11-19]]
