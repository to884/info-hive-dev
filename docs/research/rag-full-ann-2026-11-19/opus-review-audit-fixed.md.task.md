監査コードの前回 Critical は正しかった。式を読み違えていた。
`finish.py` を次のように修正したので、この変更を再レビューしてほしい。

- ページ読み取り前に documents 表の全行を prepare.py と同じ JSON の式でハッシュ化し、prepared-complete.json と照合する。
- ページの読取結果は文書ごとの extraction_digest、pages、ocr_pages、ocr_empty と照合する。ページ番号と document.md の存在も確認する。
- 全ページの集約ハッシュは extraction_aggregate_sha256 として記録し、台帳 JSON のハッシュとは比較しない。
- 全体の pages、ocr_pages、ocr_empty を prepared-complete.json と照合する。
- 4 スレッドの読み取りと入力順の集約は維持した。

`audit-formula-preflight.json` は実 DB を読み、修正後の台帳ハッシュが準備時と同じ 9af238db... であることと、ファイル用の集約ハッシュ f1dd72a7... を別々に確かめた証跡。
変更前に起動した自分の読み取り監査だけを終了し、修正版を1つ再実行中。
製品のコードと完了済み MCP 検証は変更していない。
前回の欠陥が解消したか、読み取り監査に新しい反例がないかだけを確認する。
ファイル編集・追加の監査実行・プロセス操作・OS 電源断や WSL 停止はしない。
日本語で結果を返し、末尾を Final Result: APPROVED または REJECTED とする。
