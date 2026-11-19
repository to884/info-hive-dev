# 承認済みの公開保存を突然停止後に回収する

前回の隔離試験では、承認済み保存の保留記録を書いた直後に Hyper-V を強制停止すると、再起動後にその記録が見つからず `retry` が失敗した。成功応答を返す前の停止で、固定版の読み取りは続けられた。[前回のストレージ・復旧試験](2026-11-19-wiki-production-storage-validation.md)

## 変更

保留記録の本文を一時名で書いて同期してから、同じディレクトリ内の最終名に移す。Windows では新規の受付と既存記録の更新に `MoveFileExW` の `MOVEFILE_WRITE_THROUGH` を使う。新規受付では上書きを許さず、移動が失敗した場合は保存を開始しない。POSIX では最終名のあるディレクトリに加え、ロック取得時に作成されることがある `saves/` の親も初回受付で同期する。保留ファイルの形式、承認 ID・ハッシュ、公開版の完了記録による再試行の契約は既存のものを使う。[ADR-0036](../adr/0036-wiki-published-release-journal-and-reader-pinning.md) · [Microsoft の `MoveFileExW`](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-movefileexw)

POSIX で最終名のリンクを付けた直後に終了すると、同じファイルに一時名と最終名が残る。計画 ID から一時名を決め、保留受付と共用するロックの内側で照合し、一時名だけを回収する。`pending`、`retry`、切り戻し時の保留照合で同じ処理を使う。

## 隔離試験

ローカル NVMe SSD 上の専用 NTFS VHDX を使い、ライブ192記事、公開195記事・212ファイル、原本160件の合成 wiki を Windows PE に作る。初回は正常終了して、生成した試験データを同期した状態から始める。`query`・`ingest`・`learn` の保存をそれぞれ開始し、保留記録を発行した `save_queued` で処理を止める。ゲストからの画面表示を受けて、ホストが試験 VM だけに `Stop-VM -TurnOff` を実行する。[Microsoft の `Stop-VM`](https://learn.microsoft.com/ja-jp/powershell/module/hyper-v/stop-vm?view=windowsserver2025-ps)

再起動後は元の下書きディレクトリを使えない状態にして、`pending` が元の計画 ID と承認ハッシュを返すことを確認する。同じ承認で2回 `retry` し、1回目が `applied`、2回目が `already_applied` で、両方が同じ公開版 ID を返すことを確かめる。記事・索引・ログ、Ossie の SQLite の記事行、計画 ID に対応する公開履歴を1件ずつ照合し、旧固定版の検索と根拠の取得、原本の指紋も確認する。

| 保存 | 停止操作から再起動・照合まで（初回試験 / 再試験） | 初回 / 2回目の `retry` |
| --- | ---: | --- |
| `query` | 36.91秒 / 40.54秒 | `applied` / `already_applied` |
| `ingest` | 41.68秒 / 47.61秒 | `applied` / `already_applied` |
| `learn` | 38.09秒 / 43.12秒 | `applied` / `already_applied` |

同期付きの移動を加えた初回試験と、POSIX の一時名回収を加えた後の再試験で、それぞれ3件とも同じ承認で一度だけ反映された。個々の再試行には元の下書きが不要だった。初回試験では、ホストが停止要求を観測してから停止コマンドが戻るまで0.53〜0.58秒だった。表の所要時間には WinPE の起動、再試行2回、結果の照合を含む。確認範囲は隔離 Hyper-V のゲスト OS の強制停止で、ホストと物理 SSD は稼働したままだった。

Windows ホスト上では、同期付きの移動が失敗するケースも別に検査した。`save_queued` に達せず、既定版も保留一覧も変わらなかった。同じ承認で保存を再実行すると、一度だけ反映された。

WSL の ext4 上では、POSIX の `link` 直前と直後に保存プロセスを終了させた。直前の終了は同じ承認で `apply` し直せた。直後の終了は `pending` から見つけた場合も、直接 `retry` した場合も、一時名を回収して同じ変更を一度だけ反映できた。既存の切り戻し試験でも、並行保存で未適用の承認がある間は切り戻しを停止し、処理後にライブへ書き戻せることを確かめた。

補足の browse 静的検査には `wiki_browse.py` の `OSError` の受け口に既存の指摘が2件あった。修正前のファイル操作層と比較し、同じ2件であることを確認した。

[Hyper-V の初回試験結果](../../raw/wiki承認済み公開保存の突然停止復旧-2026-11-19.json) · [Hyper-V の再試験結果](../../raw/wiki承認済み公開保存の突然停止復旧-再試験-2026-11-19.json)

## 再実行

[前回の手順](2026-11-19-wiki-production-storage-validation.md#再実行) と同じ Windows PE の起動 ISO に最新のスクリプトを入れ、`startnet.cmd` で `storage_power_guest.py` を起動する前に `set IH_POWER_QUEUED_TRIAL=1` を加える。ホストで `poc/ossie/storage_power_hyperv.ps1 -Base <ISOのある隔離ディレクトリ> -QueuedOnly` を実行すると、`vm-evidence.json` に観測値が出る。
