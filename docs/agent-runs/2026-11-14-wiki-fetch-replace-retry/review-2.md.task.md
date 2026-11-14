# 依頼: 1 回目のレビューの「重大」への直しの敵対的レビュー

1 回目のレビュー（`review-1.md`）の重大な指摘は、「退避した古い画像を戻しきれないまま止まると、`finally` が退避の場所の中身を消す」だった。main の版でも、実ファイルで同じことが起きるのを確かめた（本文の置き換えが EIO、戻しが PermissionError のとき、古い画像が 2 つとも消える）。

## 直し方

- 戻しの手順（順序、`replace_with_retry` を使うこと、最初の失敗で止まること、戻しの例外が元の例外に替わること）は変えていない。
- 後始末の規則を 1 つにした。退避の場所の中身を消すのは、本文の置き換えが成功したあと（`replaced = True`）だけにする。失敗したときは、空のときだけ `rmdir` する。一時の本文（`.tmp`）と新しい画像の置き場（`.new`）は今までどおり消す。
- 戻しが例外で抜けたとき、まだ退避の場所にある古い画像があれば、その例外に `add_note` で退避の場所と戻し方を書く。`main` は `OSError` のときに `__notes__` も標準エラーに出す。対応する Python は 3.12 以上である。

## 対象

- 直しの差分: `docs/agent-runs/2026-11-14-wiki-fetch-replace-retry/fix-1-submodule.diff`（info-hive-wiki）と `fix-1-parent.diff`（試験）
- 変更後のファイル: `info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py`（`write_outputs` と `main`）、`tests/wiki/test_wiki_fetch.py`（`check_old_images_survive_unfinished_restore` と `MainReportsKeptBackupTest`）、`info-hive-wiki/CHANGELOG.md`

## 作者が確かめたこと

- 試験は 28 件が通る（Python 3.14 と `uv run --python 3.12`）。新しい 3 件は、直す前の版で落ちた。
- 壊した写し 10 通り（1 回目の 7 通りに、「後始末で退避をいつも消す」「注記をなくす」「main で注記を出さない」を足した）では、それぞれ対応する試験が落ちる。
- Windows の実機でファイルを開いたままにする確かめ（0.3 秒なら書ける、1.5 秒なら約 1 秒で PermissionError、前の raw と画像が残り、一時のファイルも残らない）は、直したあとも同じ結果だった。

## 見てほしいこと

- 直しが、成功のときと、戻しを終えた失敗のときに、今までどおり何も残さないか。
- 直しが新しい欠陥を持ち込んでいないか（`replaced` の印の位置、注記の条件、`main` の出力、`KeyboardInterrupt`）。
- 限界として扱うつもりのもの（下）に、限界と呼べない重大なものがないか。

## 限界として扱うつもりのもの（直さない）

- 戻しは最初の失敗で止まる。止まったあとの古い画像は退避の場所に残るが、自動では戻さない。
- 退避の場所の名前はプロセス ID を含む。残った退避の場所と同じ ID のプロセスが、同じスラッグをあとで保存して成功すると、その退避の場所の中身を消す。
- 置き換えが成功した直後、`replaced = True` の前に `KeyboardInterrupt` が届くと、新しい本文のまま画像だけが古いものに戻る（直す前からある）。
