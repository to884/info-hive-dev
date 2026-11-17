前回の敵対的レビューの続きです。同じ実装と指摘を引き継ぎ、今回変えた差分だけをレビューしてください。変更禁止です。大規模テスト、バックグラウンドのテスト、CI 待機、レビューの再委譲は不要です。必要なら数秒で終わる狭いテストだけにしてください。
前回の最終本文は review-integration-transcript-final.md に保存しました。前回 CLI は最終メッセージ (end_turn 2026-11-17T15:08:36.738Z) を返した後、バックグラウンドの browse_fs 試験等が終わらず wrapper が timeout しました。session ID はこの --resume で引き継いでいます。
新しい差分は integration-opus-fixes.diff、実装は info-hive-wiki 以下です。
対応: (1) _diagnostics_html に path/link_kind、build JSON に link_warnings を追加。(2)(3) wiki_pages.refused_link を lint と browse が共用。拒んだファイルはスラッグとパス、拒んだ道は要素境界の下のパスだけで認識。browse は state refused と日本語の理由を表示し、unresolved に数えない。(4) SVG の再解析点とハードリンクの扱いを CHANGELOG に追記。(5) 正しいクラス名は Core。len(failures)==2 の依存も、入口ごとに少なくとも1回の注入を確かめる形に変更。
macOS の大小文字を区別しない根の懸念: _article_rel は祖先を上から比べ、文字列で根に一致しない場合は samefile で根そのものの実体を比べます。根に届いた時点で止め、根より下は解決せず article_path が検査します。case_variant_root の実ファイルシステムの試験を追加し、Mac CI でも確認します。これが根より下のリンクを追ってしまわないかを重点的に崩してください。
既存 CI の JSON 固定出力は、JSON15ケースの末尾に空の link_warnings 欄だけを追加しました。全ケースの検索結果・標準エラー・終了コードは保存前後で一致し、decisions43件も合格です。
未確認のCI状態は保留条件として記してよく、CIを自分で待つ必要はありません。残るコードの欠陥があるかを結論にしてください。
