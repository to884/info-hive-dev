# Ossie 公開前の受け入れ試験

[ADR-0036](../adr/0036-wiki-published-release-journal-and-reader-pinning.md) に、[ADR-0023](../adr/0023-wiki-apply-uses-journal-and-per-wiki-lock.md) の公開版を使う場合の承認・書き込み・復旧・読み取りを追加した。共通の適用口は `wiki_apply.apply_plan()` と `wiki_apply.py apply`。合成 wiki の ingest と定義を変更する試行が同じ適用口を使う。

## 合成 wiki の結果

| 項目 | 実際に確かめたこと |
| --- | --- |
| 並行 ingest | 2プロセスを同じ基準版から準備し、第三の無関係な取り込みをその間に公開した。2プロセスとも再試行し、対象を実体1件・主張1件・出典2件にまとめた。無関係な取り込み、索引、ログも保持した。 |
| 中断と再試行 | 書き手プロセスをポインター切替前と切替後に強制終了した。読み手が見たのはそれぞれ完全な旧版と新版だった。日誌を復旧し、同じ承認済み入力を再試行しても引用・ログを二重に追加しなかった。 |
| 検証失敗 | 承認後に変わったファイル、定義の指紋の偽装、旧定義の承認、別の書き手の変更を消す試行を拒否した。日誌の作成前に改変されたステージを拒否した。中断後に壊れた未公開候補は旧版を保って打ち切り、後続の正当な公開が通った。 |
| 検索と引用、browse の添付 | MCP の検索呼び出しとページ取得の間で公開版を切り替えた。同じ `release_id` を指定した取得は元の引用を返し、現在の版では新しい引用を返した。browse の旧 URL は旧 HTML・SVG を返し、`serve --release-id` でも旧版を起動できた。取り下げ後は MCP の引用取得を拒否し、旧 browse の添付は HTTP 410 を返した。 |
| 互換性 | 固定入力で `neighbors`・`edges`・`facts`・`path` と、CLI の lint・graph lint・browse の表示、MCP の lint を比較した。版を固定した場合は従来の結果と一致した。公開後も移行対象外の関係・引用を保持し、同じスラッグを持つ別ページを勝手に選ばなかった。 |

段階3のローカルアダプターで、公開し直した合成 wiki の Ossie バンドルも読み込み、型付きリンクを SQLite と照合した。SemaSynth は実行前後にファイル名と SHA-256 を比較し、書き込み対象は一時ディレクトリの合成 wiki に限定した。

## 再実行

依存がローカルにある状態で、リポジトリのルートから実行する。受け入れ判定では MCP のテストを含め、スキップがないことを確認する。

```powershell
uv run --offline --with pyyaml==6.0.3 --with mcp==1.30.0 --with uvicorn==0.54.0 --with tantivy==0.27.0 --with usearch==2.26.6 --with numpy==2.5.4 python -B -X utf8 -m unittest tests/wiki/test_wiki_publication_acceptance.py -v
```

今回の検査結果は `poc/ossie/runs/publication-acceptance/verification.json`。動作確認の範囲は合成 wiki に対する公開プロトコルと、公開版を読む既存コマンドである。既存のライブ書き込みを全面移行する工程、物理パージ、実規模での性能、Windows の電源断からの復旧は本番有効化前に評価する。 [受け入れ試験](../../tests/wiki/test_wiki_publication_acceptance.py) · [合成 wiki の ingest](../../poc/ossie/publication_trial.py)
