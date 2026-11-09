# 機械で出した指標

`scripts/tabulate.py` が `runs/` から作った。意味の対応づけは含まない。一致率は、既存のページのスラッグ、または新規のページのスラッグが**文字列として**一致したものだけを数えた参考値である。

## 資料 × 方式 × モデル

| 資料 | 方式 | モデル | 件数 | 候補の数 | source_only の割合 | concept の新規 | うち claim | entity の新規 | 引用が原本にない / 引用の数 | 引用の行がずれた | 条件が空 | 条件の脱落の疑い | 外のパス | 既存の更新先の Jaccard | 新規スラッグの Jaccard | 費用 USD | 入力トークン | 出力トークン | 平均の秒 |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| O | current | opus | 3 | 34,33,31 | 0.284 | 0,0,0 | 0,0,0 | 0,0,0 | 0 / 208 | 0 | 48 | 6 | 0 |  |  | 1.85 | 254,244 | 62,349 | 169.433 |
| O | current | sol | 3 | 52,58,54 | 0.188 | 0,0,0 | 0,0,0 | 1,1,1 | 0 / 296 | 0 | 34 | 5 | 0 |  |  |  | 233,751 | 60,518 | 530.333 |
| O | current | all | 6 | 34,33,31,52,58,54 | 0.236 | 0,0,0,0,0,0 | 0,0,0,0,0,0 | 0,0,0,1,1,1 | 0 / 504 | 0 | 82 | 11 | 0 | 0.831 | 0.25 | 1.85 | 487,995 | 122,867 | 349.883 |
| O | hybrid | opus | 3 | 27,21,23 | 0.272 | 1,1,1 | 1,1,1 | 0,0,0 | 0 / 175 | 0 | 24 | 4 | 0 |  |  | 1.83 | 259,899 | 60,786 | 177.733 |
| O | hybrid | sol | 3 | 41,34,37 | 0.221 | 0,1,0 | 0,1,0 | 1,2,2 | 0 / 266 | 0 | 0 | 0 | 0 |  |  |  | 238,557 | 51,921 | 485.567 |
| O | hybrid | all | 6 | 27,21,23,41,34,37 | 0.246 | 1,1,1,0,1,0 | 1,1,1,0,1,0 | 0,0,0,1,2,2 | 0 / 441 | 0 | 24 | 4 | 0 | 1.0 | 0.1 | 1.83 | 498,456 | 112,707 | 331.65 |
| R | current | opus | 3 | 21,21,21 | 0.54 | 1,1,1 | 0,0,0 | 0,0,0 | 0 / 67 | 0 | 28 | 25 | 0 |  |  | 1.19 | 215,964 | 34,628 | 104.7 |
| R | current | sol | 3 | 25,24,22 | 0.129 | 1,1,1 | 0,0,0 | 0,0,0 | 0 / 74 | 0 | 3 | 0 | 0 |  |  |  | 207,333 | 26,281 | 349.133 |
| R | current | all | 6 | 21,21,21,25,24,22 | 0.334 | 1,1,1,1,1,1 | 0,0,0,0,0,0 | 0,0,0,0,0,0 | 0 / 141 | 0 | 31 | 25 | 0 |  | 0.4 | 1.19 | 423,297 | 60,909 | 226.917 |
| R | hybrid | opus | 3 | 16,16,16 | 0.584 | 5,4,4 | 2,3,3 | 0,0,0 | 0 / 70 | 0 | 3 | 1 | 0 |  |  | 1.34 | 221,619 | 41,130 | 189.867 |
| R | hybrid | sol | 3 | 12,14,13 | 0.18 | 7,8,7 | 2,3,4 | 0,0,1 | 0 / 71 | 0 | 3 | 0 | 0 |  |  |  | 212,139 | 26,655 | 384.467 |
| R | hybrid | all | 6 | 16,16,16,12,14,13 | 0.382 | 5,4,4,7,8,7 | 2,3,3,2,3,4 | 0,0,0,0,0,1 | 0 / 141 | 0 | 6 | 1 | 0 |  | 0.071 | 1.34 | 433,758 | 67,785 | 287.167 |
| V | current | opus | 3 | 35,31,29 | 0.791 | 0,0,0 | 0,0,0 | 0,0,0 | 0 / 162 | 0 | 42 | 22 | 0 |  |  | 1.52 | 216,423 | 51,510 | 144.667 |
| V | current | sol | 3 | 43,37,51 | 0.409 | 3,5,2 | 0,0,0 | 1,0,1 | 0 / 186 | 0 | 13 | 7 | 0 |  |  |  | 207,681 | 51,614 | 438.833 |
| V | current | all | 6 | 35,31,29,43,37,51 | 0.6 | 0,0,0,3,5,2 | 0,0,0,0,0,0 | 0,0,0,1,0,1 | 0 / 348 | 0 | 55 | 29 | 0 |  | 0.033 | 1.52 | 424,104 | 103,124 | 291.75 |
| V | hybrid | opus | 3 | 21,21,21 | 0.603 | 6,4,6 | 3,3,4 | 0,0,0 | 0 / 149 | 0 | 6 | 2 | 0 |  |  | 1.65 | 222,078 | 56,768 | 164.967 |
| V | hybrid | sol | 3 | 34,40,41 | 0.678 | 8,8,10 | 3,5,4 | 1,1,1 | 0 / 201 | 0 | 0 | 0 | 0 |  |  |  | 212,487 | 53,878 | 458.933 |
| V | hybrid | all | 6 | 21,21,21,34,40,41 | 0.641 | 6,4,6,8,8,10 | 3,3,4,3,5,4 | 0,0,0,1,1,1 | 0 / 350 | 0 | 6 | 2 | 0 |  | 0.053 | 1.65 | 434,565 | 110,646 | 311.95 |

数の列（候補の数、concept の新規など）は、回ごとの値をカンマで並べた。

## 実行ごと

| run_id | ok | 候補 | 行き先の内訳 | 新規ページ | 更新する既存ページ | 引用（原本にある / 数） | 外のパス |
| --- | --- | ---: | --- | --- | --- | --- | ---: |
| O-current-opus-1 | True | 34 | concept_update 24, source_only 10 |  | rdf-rdfs-owl、オントロジー、オープンワールド仮定、ナレッジグラフ | 73 / 73 | 0 |
| O-current-opus-2 | True | 33 | concept_update 22, source_only 11 |  | rdf-rdfs-owl、オントロジー、オープンワールド仮定、ナレッジグラフ | 63 / 63 | 0 |
| O-current-opus-3 | True | 31 | concept_update 24, source_only 7 |  | rdf-rdfs-owl、オントロジー、オープンワールド仮定、ナレッジグラフ | 72 / 72 | 0 |
| O-current-sol-1 | True | 52 | concept_update 24, entity_create 10, section_update 7, source_only 11 | scima-owl | rdf-rdfs-owl、sparql、tbox-abox、オントロジー、オープンワールド仮定、ナレッジグラフ | 96 / 96 | 0 |
| O-current-sol-2 | True | 58 | concept_update 34, entity_create 10, source_only 14 | scima-owl | rdf-rdfs-owl、sparql、オントロジー、オープンワールド仮定、ナレッジグラフ | 99 / 99 | 0 |
| O-current-sol-3 | True | 54 | concept_update 26, entity_create 10, section_update 12, source_only 6 | scima-owl | rdf-rdfs-owl、sparql、オントロジー、オープンワールド仮定、ナレッジグラフ | 101 / 101 | 0 |
| O-hybrid-opus-1 | True | 27 | claim_create 4, concept_update 10, section_update 7, source_only 6 | オントロジーと関係データベースは意味と推論か書き込みの速度かで使い分ける | rdf-rdfs-owl、オントロジー、オープンワールド仮定、ナレッジグラフ | 54 / 54 | 0 |
| O-hybrid-opus-2 | True | 21 | claim_create 2, concept_update 6, section_update 6, source_only 7 | 大量のトランザクション書き込みには関係dbかドキュメントストアを使い意味と推論と統合が書き込み速度より重要ならオントロジーを使う | rdf-rdfs-owl、オントロジー、オープンワールド仮定、ナレッジグラフ | 61 / 61 | 0 |
| O-hybrid-opus-3 | True | 23 | claim_create 2, concept_update 7, section_update 8, source_only 6 | 意味の共有と推論と統合が書き込み速度より重要な場面では関係スキーマよりオントロジーを選ぶ | rdf-rdfs-owl、オントロジー、オープンワールド仮定、ナレッジグラフ | 60 / 60 | 0 |
| O-hybrid-sol-1 | True | 41 | entity_create 3, section_update 27, source_only 11 | scima | rdf-rdfs-owl、オントロジー、オープンワールド仮定、ナレッジグラフ | 90 / 90 | 0 |
| O-hybrid-sol-2 | True | 34 | claim_create 1, entity_create 3, section_update 23, source_only 7 | scima、scima-owl、明示的な公理から導く結論は導出をたどって説明できる | rdf-rdfs-owl、オントロジー、オープンワールド仮定、ナレッジグラフ | 93 / 93 | 0 |
| O-hybrid-sol-3 | True | 37 | entity_create 5, section_update 25, source_only 7 | scima、scima-owl | rdf-rdfs-owl、オントロジー、オープンワールド仮定、ナレッジグラフ | 83 / 83 | 0 |
| R-current-opus-1 | True | 21 | section_create 5, source_only 13, source_update 3 | 再生成の同等性確認 |  | 22 / 22 | 0 |
| R-current-opus-2 | True | 21 | concept_create 11, source_only 9, source_update 1 | 再生成の同等性確認 |  | 23 / 23 | 0 |
| R-current-opus-3 | True | 21 | concept_create 8, source_only 12, source_update 1 | 再生成の同等性確認 |  | 22 / 22 | 0 |
| R-current-sol-1 | True | 25 | concept_create 19, source_only 2, source_update 4 | semasynthの再現性検証 |  | 26 / 26 | 0 |
| R-current-sol-2 | True | 24 | concept_create 17, source_only 3, source_update 4 | semasynthの再現性検証 |  | 25 / 25 | 0 |
| R-current-sol-3 | True | 22 | concept_create 17, source_only 4, source_update 1 | semasynthの再現性検証 |  | 23 / 23 | 0 |
| R-hybrid-opus-1 | True | 16 | claim_create 2, section_create 7, source_only 7 | csv、pythonのaudit-hookによる通信禁止はpythonプロセスだけに働きos全体の遮断を保証しない、再現性確認、再生成の比較は同一環境でバイト一致異環境で値と型の一致を確かめる、性能測定 |  | 25 / 25 | 0 |
| R-hybrid-opus-2 | True | 16 | claim_create 4, section_create 2, source_only 10 | pythonのaudit-hookによる通信禁止はpythonプロセスだけを対象としos全体の遮断とは扱わない、再生成の同等性は同一環境ではバイト一致でpythonとsqliteが異なる環境では値と型の論理一致で確かめる、再生成の同等性確認、汎用csvのnullと空文字はcsvだけでは区別を復元できず列のpolicyか別の期待値が要る |  | 23 / 23 | 0 |
| R-hybrid-opus-3 | True | 16 | claim_create 3, section_create 2, source_only 11 | pythonのaudit-hookによる通信禁止はpythonプロセスだけが対象でos全体の通信遮断を保証しない、再生成の同等性は同一環境ではバイト一致異なる環境では値と型の一致で確かめる、再生成の同等性確認、汎用csvのnullと空文字はcsvだけでは区別して復元できず列のpolicyか別の期待値を要する |  | 22 / 22 | 0 |
| R-hybrid-sol-1 | True | 12 | claim_create 2, section_create 8, source_only 2 | csv復元、python-audit-hook、semasynthの会計データの再生成は環境に応じてバイト一致か値・型・csv一致で確認する、semasynthの再現確認の少数回の性能測定値は評価環境の基準値として保存し性能保証値は設定しない、再現性検証、実行環境の識別、性能測定 |  | 23 / 23 | 0 |
| R-hybrid-sol-2 | True | 14 | claim_create 3, section_create 9, source_only 2 | csv、python-audit-hook、再現性検証、再生成比較は同一環境ではバイト一致としpython・sqliteが異なる環境では値と型を照合する、実行環境の記録、少数回の性能測定値は評価環境の基準値として保存し性能保証値を設定しない、性能測定、数式対策の先頭アポストロフィを復元したcsv値は元のcheckを持つsqliteへ再投入して検証する |  | 23 / 23 | 0 |
| R-hybrid-sol-3 | True | 13 | claim_create 4, entity_create 1, section_create 5, source_only 3 | csv、pythonのaudit-hook、semasynth、会計データの同一環境での再生成はmanifestを含む全ファイルのバイト一致で確認する、再現確認の少数回の性能測定値は評価環境の基準値として扱い性能保証値は設定しない、再生成の同等性確認と配布済みデータの改変検知は区別する、性能測定、異なるpython・sqliteでの会計データ再生成は値・読戻し型・csv全行で比較する |  | 25 / 25 | 0 |
| V-current-opus-1 | True | 35 | source_only 27, source_update 8 |  |  | 57 / 57 | 0 |
| V-current-opus-2 | True | 31 | source_only 24, source_update 7 |  |  | 55 / 55 | 0 |
| V-current-opus-3 | True | 29 | source_only 24, source_update 5 |  |  | 50 / 50 | 0 |
| V-current-sol-1 | True | 43 | concept_create 10, entity_create 6, source_only 19, source_update 8 | semasynth、合成データの再現性検証、合成データの独立検証、合成データ生成の失敗診断 |  | 56 / 56 | 0 |
| V-current-sol-2 | True | 37 | concept_create 9, source_only 16, source_update 12 | データ再生成の再現性検証、会計データの独立検証、基準manifestによる改変検出、専用サンプルと汎用機能の受け入れ分離、生成失敗時の診断保存 |  | 63 / 63 | 0 |
| V-current-sol-3 | True | 51 | concept_create 12, entity_create 12, source_only 18, source_update 9 | semasynth、会計データの独立再検証、合成データの再現性検証 |  | 67 / 67 | 0 |
| V-hybrid-opus-1 | True | 21 | claim_create 3, section_create 5, source_only 13 | sqliteに生成したデータの再現性は同一環境ではバイト一致で別環境では論理一致で確かめる、会計期間は検証対象の期間マスタではなく指定年度の暦と照合する、基準manifest、敵対的レビュー、検証に失敗したときはreportと生成条件を正常出力と別の診断先に保存する、独立した期待値 |  | 47 / 47 | 0 |
| V-hybrid-opus-2 | True | 21 | claim_create 4, section_create 4, source_only 13 | 合成データの検証、合成データの検証は検証対象dbの外に置いた期待値と照合しないと整合を保った改変を見逃す、基準manifestによるハッシュ照合はmanifestを信頼できることを前提にする、生成したsqliteデータの再現性は同一環境ではバイト一致別環境では行型値の論理一致で確かめる |  | 52 / 52 | 0 |
| V-hybrid-opus-3 | True | 21 | claim_create 4, section_create 5, source_only 12 | 再生成の一致は同一環境ではバイト異なる環境では論理一致で確かめる、受け入れ境界、合成データの検証、敵対的レビューの指摘は再現して確かめた範囲で採用する、期間マスタと明細の同時変更は指定年度の暦との照合で検出する、集計を変えない名称の入れ替えは別保管した基準manifestとの照合で検出する |  | 50 / 50 | 0 |
| V-hybrid-sol-1 | True | 34 | claim_create 3, entity_create 3, section_create 5, source_only 23 | semasynth、データ再現性、受け入れ証跡、合成データの再検証、固定条件の会計専用サンプルを汎用policy対応の根拠に含めない案、基準manifest、小さいfixtureの検証では不変条件と独立したシナリオ期待値を分ける案、期間マスターと明細の同時変更に備え指定年度の暦と照合する案、検証診断 |  | 64 / 64 | 0 |
| V-hybrid-sol-2 | True | 40 | claim_create 5, entity_create 3, section_create 4, source_only 28 | csv検証、semasynth、会計データの再生成は同一環境でバイト一致を別環境で論理一致を確認する案、会計期間は指定年度の暦と照合し期間と明細の同時変更を試す案、固定条件で生成しossieを後付けする会計専用サンプルは汎用policy対応の根拠に含めない案、基準manifest、基準manifestによるハッシュ照合は基準への信頼を前提とする、検証期待値、生成時の検証失敗は正常出力と別の診断先にレポートと生成条件を保存する案 |  | 70 / 70 | 0 |
| V-hybrid-sol-3 | True | 41 | claim_create 4, entity_create 2, section_create 8, source_only 27 | csv検証、semasynth、再生成の比較には同一環境でバイト一致を別環境で行・型・値の一致を提案する、受け入れ条件、受け入れ証跡、回帰テスト、固定条件の会計専用サンプルを汎用policy対応の根拠に含めないことを提案する、基準manifest、指定年度の会計期間の検証には暦照合とマスター・明細の同時変更の反例を提案する、検証の期待値、検証失敗で一時reportが残らない場合は診断と生成条件を別に保存することを提案する |  | 67 / 67 | 0 |

## 原本に見つからなかった引用

記号（引用符、ダッシュ）の違いを吸収したうえで、原本に見つからなかったもの。捏造かどうかは人が確かめる。

- なし

## スナップショットの外を指したツールの呼び出し

- なし
