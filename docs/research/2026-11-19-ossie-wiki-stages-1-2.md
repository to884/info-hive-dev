# Apache Ossie 一方向 PoC の段階1・2

[SemaSynth の書き出し PoC](2026-11-19-ossie-wiki-export-poc.md) に、 [設計案](../plans/wiki-ontology-ossie-design-2026-11-19.md) の意味モデルと移行の試行を加えた。既存の書き出しを `legacy/` に保存し、別のスナップショットを `semantic/` に出す。

## SemaSynth の実データ

| 照合項目 | 結果 |
| --- | --- |
| 既存グラフ | ノード 63 件、関係 477 件のすべての列が一致した。現在の Markdown と定義を info-hive-wiki 0.37.0（`ca882fd`）で一時領域に再抽出した結果も一致した。 |
| 意味レコード | 実体 9 件、記事 54 件に区別し、元のノードと関係の ID 540 件すべてに対応を出した。本文リンクや原本参照などは既存グラフ側で保持する。 |
| 根拠 | 明示関係 `depends_on` と `cites` の 2 件を主張の候補として取り込み、元の主語・述語・目的語、引用、出典、原本参照を照合した。2 件とも原本の指定行に引用が含まれ、出典ページと原本の指紋も記録した。 |
| 再実行 | 同じ wiki ID と入力での再実行で、旧 ID の対応とスナップショット ID が一致した。 |
| 入力の変更 | 実行前後で SemaSynth wiki のファイル 81 件の内容と一覧が一致した。 |

取り込み側では、旧状態を元データとして保持し、移行後の確定判断とは区別する。引用の照合は原本に引用があることを確かめる。主張の真偽を自動で確定する処理はこの段階の対象外である。

## 合成 wiki の移行と集計

- 製品Aは顧客1社・主張1件・根拠2件。指定した終了日には0社となり、代理販売の関係だけを持つ製品Bも0社となった。製品Cでは、時期不明・係争中・未分析を結果に記録した。別 wiki の同名実体には別の ID が付き、顧客集計に入らなかった。
- 開始日の訂正と根拠の追加は同じ主張の別の版になる。根拠だけを追加した版に反証を引き継ぎ、「利用」を「試用」と「契約」に分割した後は、「未契約だった」の反証が契約だけを指した。判断できない別の参照は v2 で候補と旧参照を保持して保留し、v3 で新しい根拠により対象外と判定した。
- 保守プランの移行保留は v1 と v2 で1件、v3 で0件。v3 の確定した契約は1件で、初回の保留理由、新しい根拠、決定理由、旧定義への参照を保持した。

合成試行の意味判断は明示した入力として与え、出力した SQLite から結果を照合する。実行対象は固定したオントロジーのケースで、本文から判断を生成する処理、一般的な Ossie 実行、wiki の公開版を切り替える処理は対象外である。固定したコミットの公式検証器で SemaSynth と合成 wiki の Ontology・Core・Mapping 計21文書を検証し、すべて通過した。レビューで再現した反証の引き継ぎ漏れ、期間不明の反証、旧グラフの参照の退行を含め、関連テスト 97 件が通過した。

## 再実行

リポジトリのルートで実行する。既存 wiki の読み取りと再抽出には PyYAML が必要になる。新しい出力先を指定し、同じ wiki の比較では `--wiki-id` を固定する。

```powershell
uv run --with pyyaml==6.0.3 python -B -X utf8 poc/ossie/semantic_trial.py --wiki C:/Works/semasynth-dev/wiki --wiki-id semasynth --output poc/ossie/runs/stages12-semasynth-rerun
python -B -X utf8 poc/ossie/semantic_trial.py --demo --output poc/ossie/runs/stages12-synthetic-rerun
uv run --with pyyaml==6.0.3 python -B -X utf8 -m unittest tests/wiki/test_ossie_semantic_trial.py tests/wiki/test_ossie_export.py -v
```

公式検証を行う場合は Apache Ossie の `0f458dee0718b701930bf4597e1d84e427f0c8fc` をチェックアウトし、上の書き出しコマンドに `--ossie-checkout C:/path/to/ossie` を追加する。検証結果と件数は出力先直下の `verification.json` に入る。意味スナップショットには `release.json`、`records.jsonl`、`wiki-data.sqlite` と Ossie の 3 文書が入る。合成 wiki の記事と各版のスナップショットも出力先に残る。 [実行スクリプト](../../poc/ossie/semantic_trial.py) · [試行コード](../../poc/ossie/demo_scenario.py) · [受け入れ試験](../../tests/wiki/test_ossie_semantic_trial.py)

検証済みの今回の出力は `poc/ossie/runs/stages12-semasynth/` と `poc/ossie/runs/stages12-synthetic/` にある。
