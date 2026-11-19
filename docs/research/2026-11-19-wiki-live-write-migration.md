# ライブ wiki の書き込み移行と受け入れ試験

通常の `ingest`、`query` の回答保存、`learn` の経験保存を、ADR-0023 の `wiki_apply.py` に接続した。Claude Code と Codex は共通の操作手順を使う。原本の保存とグラフの抽出は専用スクリプトが行い、抽出結果のログは共通の書く段から追記する。公開版を選択した wiki の更新は ADR-0036 の公開計画を使う。

## 隔離 wiki の試験

| 試験 | 確認内容 |
| --- | --- |
| ローカル資料の ingest | 実際の原本保存から、原本のパスとハッシュ、要約、関連コンセプト、索引、ログを保存した。グラフを SQLite に抽出し、実際のノード数を元の ingest のログに追記した |
| query と learn の保存 | BM25 でソースを検索し、回答を保存して再検索した。経験は既存の `capture` で保存し、原本参照を持つソースと既存のパターンに反映した。既存の lint と browse は書き込み後の wiki を読めた |
| 並行書き込み | 3 プロセスが同じ索引とログに書き、各ページ、索引項目、ログが 1 件ずつ残った。同じページの編集は後発が競合し、承認後に変えた下書きも拒んだ。最新のページに変更を当て直し、再承認すると両方の変更が残った |
| ロック待ち | 稼働中の書き手の解除を拒み、待ち時間を超えた計画を記録した。保持した承認で再実行すると、保留記録が消えた |
| プロセス強制終了 | 日誌直後、一時ファイル作成後の置換直前、1 件目の反映直後、適用済み印の直後から復旧した。明示の復旧と次の書き手による復旧を試し、再実行で索引やログが重複しないことを確認した |
| 日誌と異なる変更 | 日誌で追える反映を戻し、外部から書き換えたバイト列を保った。日誌を確認して別名に退避し、次の書き込みを適用した |
| ファイルの境界 | 外部の単独 PDF を元の位置に置いたまま要約を更新した。入れ子の wiki、Windows の短い別名、ライブ入口からの公開版更新を拒んだ。BOM、CRLF、コードフェンスを維持し、索引の表示名やアンカーを変えた二重登録も拒んだ |

下書きと承認は試験データで与え、CLI は通常の操作と同じ入口から実行した。試験対象は同じ Windows ホスト上のプロセス中断とローカルファイルシステムである。索引・ログの置換直前と直後の終了も追加で試した。新規ファイルの一時名と公開名が同じ実体を指す状態をハードリンクで再現し、復旧後に公開名だけが残ることを確認した。

実規模での処理時間、Windows の電源断、Linux の実マウントを使った検証は本番有効化前の評価に残る。ライブの読み手は複数ファイルの反映途中を読めるため、検索から引用まで同一版に固定する運用には ADR-0036 の公開版を使う。

ライブ書き込みの 11 件と公開版の 8 件はすべて成功した。リンク、lint、原本、Codex の回帰試験は 172 件中 167 件が成功し、5 件をスキップした。セッションと Web raw の回帰試験は 144 件が成功した。再レビュー後の変更に対し、ライブ、公開版、読み取り箇所とサーバーの依存ファイルの検査を合わせた 23 件を再実行し、すべて成功した。

`C:/Works/semasynth-dev/wiki` に対して行った操作は、全ファイルの SHA-256 の読み取り照合だけである。15:02 頃までは開始時の 81 ファイルと一致した。最終照合ではファイル数が同じまま、`index.md`、`log.md`、`synthesis/semasynth業務定義の持ち運び.md` に差分があった。ファイルの更新時刻は 15:03:57 と 15:05:07（日本時間）だった。変更元は確認できていない。

## レビューへの対応

Opus の初回レビューで、外部の単独 PDF の親を raw の根と見なすと、プロジェクト直下にある PDF を参照しただけで wiki が書けなくなると指摘された。合成 wiki で再現し、単独ファイルとディレクトリを区別するよう修正した。日誌の退避と再開、raw の根の記録の再利用、索引の別名と見出し指定を含む重複の検査も受け入れ試験で確かめた。

再レビューは承認だった。原本の根が見えないときにも日誌を表示できるようにし、同じ計画の複数回の退避を個別に残す。新規ファイルの公開途中に二つの名前が残る場合の復旧を自動試験に加えた。

## 再実行

```powershell
uv run --offline --with pyyaml==6.0.3 --with mcp==1.30.0 --with uvicorn==0.54.0 --with tantivy==0.27.0 --with usearch==2.26.6 --with numpy==2.5.4 python -B -X utf8 -m unittest tests/wiki/test_wiki_live_apply.py tests/wiki/test_wiki_publication_acceptance.py -v
uv run --offline --with pyyaml==6.0.3 --with mcp==1.30.0 --with uvicorn==0.54.0 --with tantivy==0.27.0 --with usearch==2.26.6 --with numpy==2.5.4 python -B -X utf8 -m unittest tests/wiki/test_wiki_links.py tests/wiki/test_wiki_lint.py tests/wiki/test_raw_links.py tests/wiki/test_codex_plugin.py
uv run --offline --with pyyaml==6.0.3 python -B -X utf8 -m unittest tests/wiki/test_wiki_session.py tests/wiki/test_web_raw_agent.py
```

[共通の書く段](../adr/0023-wiki-apply-uses-journal-and-per-wiki-lock.md) · [ライブ書き込みの操作手順](../../info-hive-wiki/skills/info-hive/references/write-workflow.md) · [受け入れ試験](../../tests/wiki/test_wiki_live_apply.py)
