初回レビューの Minor に対応したので、変更した箇所を再レビューしてほしい。前回の文脈は引き継いでいる。
製品 SHA-256 は 021ea0774ec104f2b1b827498a6192bf64a68fc2d3dcb0d8d1d2373240aa7ab6。
初回の証跡は first-pass/ に保全した。review-counterexamples-before-fix.log で 3 つの反例を確認した。

変更点:
1. _prune_previous が一覧の書き換えより前に退役台帳へキャッシュ回収をコミットする。既存対象の世代は合併し、rows_pending=1 を0にしない。削除は_finish_retirementsのみ。
2. _extraction_in_use で未完了の内部 jobs も参照として調べる。各 wiki の policy.json の指紋から世代を求める。相手の設定は異なり得る。
3. _remove_extractionと_remove_legacy_extractionのOSErrorを回収保留にし、意図を失わず後続も処理する。
4. MCPの禁止フックを各ジョブの子ワーカーPIDで確かめ、製品全スクリプトの開始終了ハッシュを一致させる。
5. MCPに退役スキャンの設定変更・埋め込み後の失敗・同じジョブのretry_jobによる再開を追加。回帰試験の移行はtrace callback+barrierで順序を固定した。

Windows/Linux84件と実OCR/実モデルのMCP21項目は実行中または完了済み。結果ファイルが古い場合は確認できた範囲を明記する。
大量共有参照の走査の最適化とstatusへの追加は今回は行わない。理由はreview-response.mdに記録した。
新しい不整合と反例を中心に、Critical/Major/Minorと判定を日本語で返す。編集・重い試験の起動・プロセス操作・OS電源断/再起動/WSL停止はしない。
末尾を Final Result: APPROVED または REJECTED とする。
