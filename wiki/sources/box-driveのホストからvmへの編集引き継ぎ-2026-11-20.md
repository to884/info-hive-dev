---
type: "source"
title: "Box Drive 上の wiki の編集担当をホストから VM に引き継いだ試験"
authors: ["Codex"]
tags: ["windows", "試験", "wiki設計"]
created: 2026-11-20
updated: 2026-11-20
ingested: 2026-11-20
raw: "raw/box-driveのホストからvmへの編集引き継ぎ-2026-11-20.json"
raw_sha256: "90a95decb960321754ee6ff7bef25bc7d6ed0f643b9b9e8316c8b9c3742c577b"
---

# Box Drive 上の wiki の編集担当をホストから VM に引き継いだ試験

Windows 11 ホストと Hyper-V 上の Windows 11 VM を使った。両端末の Box Drive は 2.56.271 の Cloud Files 方式で、同じアカウントに接続した。以前 Box Web のごみ箱から元の記事を復元した検証用 wiki の `concepts/guide.md`、`index.md`、`log.md` を使い、試験前に両端末のハッシュを照合した。[[box-webのごみ箱復元と版の確認-2026-11-20]]

1. ホストで記事に潮位表を確認する手順を足した。索引の要約を 1 件更新し、操作ログを 1 件追記した。3 ファイルを閉じてホストでの編集を止めた。
2. 3 ファイルについて、ホストと VM の SHA-1・SHA-256 を期待値と照合した。Box Drive が受け取った Box API 応答の SHA-1 と、両端末の Windows Cloud Files API の `InSyncState` も調べた。すべて一致した状態が続いたことを確認してから VM に編集を指示した。 [Cloud Files API の状態取得](https://learn.microsoft.com/en-us/windows/win32/api/cfapi/nf-cfapi-cfgetplaceholderinfo)
3. VM でホスト版を再確認してから、同じ記事に足元が滑りやすい場合の対応を足した。同じ要約に反映し、操作ログを 1 件追記した。ホストは読み取りだけを行い、VM が保存した 3 ファイルが届いたことを確認した。

| 保存元 | 両端末の同期済み状態と Box 側の SHA-1 を初めて確認 | 両端末の内容も一致した最初の照合 | 一致を再確認 |
| --- | --- | --- | --- |
| ホスト | 約 8 秒後 | 約 34 秒後 | 約 39 秒後 |
| VM | 約 8 秒後 | 約 25 秒後 | 約 31 秒後 |

同期済み状態は Windows Cloud Files API で観測した。時刻は書き込み開始から各照合までの概数。ホストの保存から約 8 秒後の照合では、両端末とも 3 ファイルが同期済みの状態を返し、Box 側にも更新が届いていたが、VM 上の内容はまだホスト版にそろっていなかった。エクスプローラーの同期アイコンと緑のチェックの意味は Box の資料を参照した。 [Box Drive の状態アイコン](https://support.box.com/hc/en-us/articles/43854492838419-New-Box-Drive-for-Windows-Built-on-a-New-Architecture)

各段階でドットから始まるパスを除いた Markdown の一覧を試験前と比べ、新しいパスと競合コピーは両端末とも 0 件だった。最終版の記事と索引には両方の変更が残り、操作ログは各 1 件だった。試験用 wiki のリンク切れは 0 件だった。試験はこの環境で 1 回行った。

## 取り込んだ内容と載せたページ

| 番号 | 取り込んだ内容 | 出典の該当箇所 | 掲載方法 | 掲載ページと理由 |
| --- | --- | --- | --- | --- |
| c1 | ホスト版を VM で確認してから編集し、同じ 3 ファイルが両端末と Box で一致した | writer_switch、stages、content_checks | update | [[box-drive上のwikiの運用]] に引き継ぎ順と競合コピーの有無を記録 |
| c2 | 同期済み状態を両端末で観測した時点では、受け手の内容が新版にそろっていなかった | stages | update | [[box-drive上のwikiの運用]] に受け手で新版を照合する条件を追記 |

## 関係するページ

- [[box-drive上のwikiの運用]]
- [[box-webのごみ箱復元と版の確認-2026-11-20]]
