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
| R | current | opus | 3 | 18,20,21 | 0.743 | 1,0,1 | 0,0,0 | 0,0,0 | 0 / 65 | 0 | 23 | 21 | 0 |  |  | 1.1 | 209,646 | 31,105 | 91.667 |
| R | current | sol | 3 | 25,19,20 | 0.185 | 2,1,2 | 0,0,0 | 0,0,0 | 0 / 74 | 0 | 5 | 2 | 0 |  |  |  | 202,416 | 24,985 | 213.7 |
| R | current | all | 6 | 18,20,21,25,19,20 | 0.464 | 1,0,1,2,1,2 | 0,0,0,0,0,0 | 0,0,0,0,0,0 | 0 / 139 | 0 | 28 | 23 | 0 |  | 0.1 | 1.1 | 412,062 | 56,090 | 152.683 |
| R | hybrid | opus | 3 | 19,16,16 | 0.464 | 6,4,5 | 5,2,2 | 0,0,0 | 0 / 70 | 0 | 8 | 5 | 0 |  |  | 1.32 | 215,301 | 41,191 | 130.333 |
| R | hybrid | sol | 3 | 16,13,15 | 0.113 | 6,5,7 | 3,1,3 | 1,1,0 | 0 / 74 | 0 | 3 | 0 | 0 |  |  |  | 207,459 | 27,465 | 227.167 |
| R | hybrid | all | 6 | 19,16,16,16,13,15 | 0.288 | 6,4,5,6,5,7 | 5,2,2,3,1,3 | 0,0,0,1,1,0 | 0 / 144 | 0 | 11 | 5 | 0 |  | 0.069 | 1.32 | 422,760 | 68,656 | 178.75 |
| V | current | opus | 3 | 29,31,30 | 0.714 | 0,2,0 | 0,0,0 | 0,0,0 | 0 / 140 | 0 | 46 | 28 | 0 |  |  | 1.48 | 213,843 | 49,575 | 139.7 |
| V | current | sol | 3 | 39,46,40 | 0.514 | 3,3,3 | 0,0,0 | 1,1,1 | 0 / 190 | 0 | 5 | 1 | 0 |  |  |  | 205,980 | 48,682 | 356.1 |
| V | current | all | 6 | 29,31,30,39,46,40 | 0.614 | 0,2,0,3,3,3 | 0,0,0,0,0,0 | 0,0,0,1,1,1 | 0 / 330 | 0 | 51 | 29 | 0 |  | 0.077 | 1.48 | 419,823 | 98,257 | 247.9 |
| V | hybrid | opus | 3 | 20,21,19 | 0.703 | 4,8,3 | 3,6,2 | 0,0,0 | 0 / 130 | 0 | 10 | 5 | 0 |  |  | 1.48 | 219,498 | 49,038 | 143.067 |
| V | hybrid | sol | 3 | 41,37,39 | 0.736 | 8,8,9 | 6,4,4 | 1,0,1 | 0 / 191 | 0 | 0 | 0 | 0 |  |  |  | 210,465 | 50,434 | 382.767 |
| V | hybrid | all | 6 | 20,21,19,41,37,39 | 0.719 | 4,8,3,8,8,9 | 3,6,2,6,4,4 | 0,0,0,1,0,1 | 0 / 321 | 0 | 10 | 5 | 0 |  | 0.014 | 1.48 | 429,963 | 99,472 | 262.917 |

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
| R-current-opus-1 | True | 18 | concept_create 4, source_only 11, source_update 3 | 再生成の同等性確認 |  | 22 / 22 | 0 |
| R-current-opus-2 | True | 20 | source_only 19, source_update 1 |  |  | 22 / 22 | 0 |
| R-current-opus-3 | True | 21 | concept_create 6, source_only 14, source_update 1 | 再生成の同等性確認 |  | 21 / 21 | 0 |
| R-current-sol-1 | True | 25 | concept_create 14, source_only 10, source_update 1 | 合成データの再現性検証、実行環境の来歴記録 |  | 26 / 26 | 0 |
| R-current-sol-2 | True | 19 | concept_create 14, source_only 2, source_update 3 | semasynthの再現性検証 |  | 24 / 24 | 0 |
| R-current-sol-3 | True | 20 | concept_create 19, source_only 1 | semasynthの再現性検証、汎用csvの復元 |  | 24 / 24 | 0 |
| R-hybrid-opus-1 | True | 19 | claim_create 5, concept_create 1, section_create 2, source_only 11 | pythonのaudit-hookによる通信禁止はpythonプロセスだけが対象でos全体やネイティブコードの通信遮断を保証しない、プロセス全体のピーク常駐メモリは依存パッケージのインポートを含み処理単体の使用量ではない、再生成の同等性は同一環境では全ファイルのバイト一致異なるpythonやsqliteでは値と型の論理比較で確かめる、再生成の同等性確認、少数回の性能測定値は評価環境での基準値として保存し性能保証値にしない、汎用csvのnullと空文字はcsvだけでは区別して復元できず列のpolicyか別の期待値が要る |  | 25 / 25 | 0 |
| R-hybrid-opus-2 | True | 16 | claim_create 3, section_create 5, source_only 8 | python-audit-hook、再生成の同等性は同一環境ではバイト一致、異なるpythonとsqliteでは値と型の比較で確かめる、実行環境の記録、汎用csvのnullと空文字の区別は列のpolicyか別の期待値がなければ復元できない |  | 23 / 23 | 0 |
| R-hybrid-opus-3 | True | 16 | claim_create 2, section_create 9, source_only 5 | csvの復元、pythonのaudit-hookによる通信禁止はpythonプロセスだけを対象にしosの通信遮断を保証しない、再現性の検証、再生成の同等性は同一環境ではバイト一致で異なるpythonとsqliteでは値と型の比較で確かめる、性能測定 |  | 22 / 22 | 0 |
| R-hybrid-sol-1 | True | 16 | claim_create 3, entity_create 6, section_create 6, source_only 1 | csv復元、pythonのaudit-hookによる通信制御はos全体や任意のネイティブコードの通信遮断を保証しない、semasynth、再生成の同等性確認、少数回の性能測定値は評価環境の基準値として保存し性能保証値は設定しない、性能測定、汎用csvのnullと空文字の区別を復元するには列のpolicyか別の期待値が必要である |  | 24 / 24 | 0 |
| R-hybrid-sol-2 | True | 13 | claim_create 1, entity_create 3, section_create 8, source_only 1 | python-audit-hook、semasynth、再現性の検証、性能測定、汎用csv、汎用csvからnullと空文字を復元するには列のpolicyか別の期待値が必要になる |  | 25 / 25 | 0 |
| R-hybrid-sol-3 | True | 15 | claim_create 3, section_create 9, source_only 3 | csv復元、pythonのaudit-hookによる通信制限はos全体や任意のネイティブコードの通信遮断を保証しない、再現性検証、再生成の同等性確認と配布済みデータの改変検知は区別する、実行環境の来歴、性能測定、汎用csvだけではnullと空文字を区別して復元できず列のpolicyか別の期待値が必要である |  | 25 / 25 | 0 |
| V-current-opus-1 | True | 29 | source_only 21, source_update 8 |  |  | 49 / 49 | 0 |
| V-current-opus-2 | True | 31 | concept_create 1, section_create 6, source_only 14, source_update 10 | 基準manifestの信頼前提、敵対的レビュー |  | 51 / 51 | 0 |
| V-current-opus-3 | True | 30 | source_only 29, source_update 1 |  |  | 40 / 40 | 0 |
| V-current-sol-1 | True | 39 | concept_create 7, entity_create 6, source_only 20, source_update 6 | semasynth、合成データの再現性、生成データの独立検証、生成失敗時の診断保存 |  | 63 / 63 | 0 |
| V-current-sol-2 | True | 46 | concept_create 11, entity_create 4, source_only 22, source_update 9 | semasynth、合成データの独立検証、合成データ生成の再現性、生成失敗時の診断保存 |  | 63 / 63 | 0 |
| V-current-sol-3 | True | 40 | concept_create 8, entity_create 4, source_only 22, source_update 6 | semasynth、合成データの独立検証、合成データ生成の再現性、合成データ生成失敗時の診断保存 |  | 64 / 64 | 0 |
| V-hybrid-opus-1 | True | 20 | claim_create 3, section_create 1, source_only 16 | マスタの名称交換とcsvの改変は版管理した期待値と別保管の基準manifestで照合して検出する、会計期間の検証は期間マスタと明細の同時改変に備えて指定年度の暦と照合する、基準manifest、生成dbの再現性は同一環境ではバイト一致で別環境では行と型と値の論理一致で確かめる |  | 41 / 41 | 0 |
| V-hybrid-opus-2 | True | 21 | claim_create 6, section_create 3, source_only 12 | 会計期間は期間マスターではなく指定年度の暦と照合して検証する、再現性は同一環境ではバイト一致で別環境では行と型と値の論理一致で確認する、固定条件の専用サンプルは汎用policy対応の受け入れ根拠に含めない、基準manifest、敵対的レビュー、検証器は業務上の不変条件とシナリオの期待値を分けて小さいfixtureにも独立した期待値を渡す、検証失敗時はreportと生成条件を正常出力とは別の診断先に保存する、部門名称の交換やcsvの変更は版管理したマスター期待値と基準manifestとcsvとdbの照合で検出する |  | 50 / 50 | 0 |
| V-hybrid-opus-3 | True | 19 | claim_create 2, section_create 3, source_only 14 | sqliteに生成したデータの再現性は同一環境ではバイト一致、別環境では行・型・値の論理一致で確かめる、ハッシュ照合はデータと基準manifestの同時変更に対する真正性を保証しない、独立した期待値 |  | 39 / 39 | 0 |
| V-hybrid-sol-1 | True | 41 | claim_create 6, entity_create 3, section_create 2, source_only 30 | semasynth、シナリオ検証、ハッシュ照合は基準manifestへの信頼を前提とする、ローカル生成レポートを受け入れ時に記録する場合はコミットと再生成手順を含める、会計期間の検証では月と開始日と終了日を指定年度の暦と照合する、再現性、専用会計サンプルを汎用policy対応の受け入れの根拠には含めない、所属とcsvの変更に対応する再検証cliではマスター期待値と別保管基準とdbとcsvを照合する、検証失敗時は正常出力と別の診断先にreportと生成条件を保存する |  | 58 / 58 | 0 |
| V-hybrid-sol-2 | True | 37 | claim_create 4, section_create 4, source_only 29 | テストfixture、ハッシュ照合は基準manifestを信頼できることを前提とする、マスターとcsvの変更に備える再検証には外部期待値とdbとの照合を加えることが提案されている、再現性、受け入れ記録、固定条件の会計専用サンプルは汎用policy対応の根拠に含めないことが提案されている、指定年度の会計期間は暦と照合しマスターと明細の同時変更も試すことが提案されている、検証診断 |  | 67 / 67 | 0 |
| V-hybrid-sol-3 | True | 39 | claim_create 4, entity_create 2, section_create 6, source_only 27 | csv検証、semasynth、ハッシュ照合、マスター検証、ローカル生成レポートの受け入れ記録にはコミットと再生成手順を含めることが提案されている、再現性検証、固定条件の専用会計サンプルは汎用policy対応の根拠から除くことが提案されている、小さいfixtureの業務検証では不変条件とシナリオ期待値を分けることが提案されている、指定年度の会計期間検証では月と開始日・終了日を暦と照合することが提案されている、生成失敗時の診断記録 |  | 66 / 66 | 0 |

## 原本に見つからなかった引用

記号（引用符、ダッシュ）の違いを吸収したうえで、原本に見つからなかったもの。捏造かどうかは人が確かめる。

- なし

## スナップショットの外を指したツールの呼び出し

- なし
