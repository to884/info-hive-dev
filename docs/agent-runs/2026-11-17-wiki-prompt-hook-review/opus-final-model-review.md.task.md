前回の実装の再レビューからの続きです。候補を読むモデル表の最終値と根拠を敵対的に追加確認してください。読み取りだけ。他のエージェント、LLM、外部API、Webを呼ばないでください。全158件の意味の採点を最初から繰り返す必要はありません。採点と裁定の生の記録を残してあるので、選定を覆す具体的な欠陥、実装との食い違い、重要な裁定の誤りが残るかを確認してください。今回の対象はモデル表の確定と前回指摘の修正の完了です。リリース・マージの承認は求めていません。

前回の重大1（製品の値がv2のまま）:
- 最終の選定は reader-models-v3/model-selection.json。R1=sonnet/low、R2=sonnet/low、R3=sonnet/medium。R0はmain-inheritで、selected=null、読者間の比較の最安値は別欄です。
- 採用の意味の割合はR1=97.5%、R2=100%、R3=96.875%、各段の最良は100%。誤った命題・引用誤り・根拠のない追加主張・必読欠落・形式の失敗が0で、最良の95%以上の組から平均換算費用の最小を選んだ。
- wiki_prompt_context.py TIERS、agents/wiki-reader.mdの既定、prompt-context.mdの表と説明、CHANGELOGを更新した。
- tests/wiki/fixtures/prompt_context/reader_model_selection.jsonが選定のSHA・入力の指紋・表と、ルーティングの既定値を除いた読むエージェントのハッシュを持ち、ProductDecisionTestsが製品・文書との一致を確認する。grade_reader_models.py verify-productでも一致を確認済み。

前回の重大2（単独の意味の採点）:
- Opus5.5/highとGPT-6.1Sol/mediumの二人が全158件を採点した。先行するOpusの判定や対応表をSolには渡していない。
- Solは別の一時ディレクトリで、13個の質問・本文・匿名回答だけを読んだ。IDはsecretsによる乱数へ替え、答えと根拠の2節へ統一した。全入力SHAの一致を確認。CLIはツール起動が壊れていて採点0件だったため未実施として残し、アプリ内サブエージェントで完了した（semantic-grading-sol-app.json）。
- 二人の命題は598/610で一致。差のあった命題と全指摘の30件をCodexが元の本文と照合して裁定し、semantic-adjudications.jsonに採った判定と理由を保存した。reconcile_reader_grades.pyが未裁定を拒む。採用24回答の主要主張も読み合わせた（selected-manual-audit.json）。
- Opusは採点後に改行確認のためsummary/manual-spotcheckを開いたと報告し、指定範囲を超えた。この制約は明記し、完全な匿名性や二人の一致が正しさを証明するとは扱わない。Solの隔離した独立採点と本文の裁定を加えた理由でもある。
- 当初の命題の曖昧な表現は、当初からの本文優先という規則に従いrubric-clarifications.jsonで明示した。測定時の入力、命題、回答、生の採点は変更していない。
- 代表的な裁定: A010/A121は実際のwiki_pages.resolve_linkでtitleが未解決、正しいslugは解決した（link-resolution-check.json）。A102/A132は本文が明記するPDFiumとpdfminerの比較を「ない」と断定し、採用対象外。A146は主文で1024以下を正しく述べ、「1025を超えれば失敗」は十分条件として真なので、誤った事実とまでは数えない。A145は0始まりを明示した文脈から支持、曖昧な「バイト目」の表現は注記とした。

他の前回指摘:
- manifestのbundlesが空でも通る問題:13問の完全一致、命題・本文・全回答を凍結した入力と実際の回答へ照合する。欠測・改変・複数採点者の来歴・CLI版混在も拒む。semantic-provenance.jsonは全採点/裁定/写しとSHAを結ぶ。ハッシュは実際に読んだことの証明とは主張しない。
- Agent経路: 選定後の値でverify_reader_delegation.pyを起動した記録がdelegation.jsonとdelegation-validation.json。parent_tool_use_idで各呼び出しを子のassistant.message.modelと照合する。effortは渡した引数の受理と正常な戻りまでで、バックエンドの実効effortの直接の観測とはしない。MCPなしのRead経路の契約を確認しただけで、全組のAgent総費用の最安とは主張しない。
- 性能: 並列モデル測定中の150ページはp95 5.3秒・到達3/10、並列測定後の同じ条件ではp95 639ms・10/10。両方を記録し、並列作業中に外側5秒へ収まるかはリリース前の課題として残す。モデル表の確定とは別の制約。
- 現行の単体試験はフック63件と測定28件の計91件が成功。ページ集合30(1skip)、初期化41(2skip)、spawn8(1skip)も成功。ゲートrecall.889 precision.893、負例発火0。コードと文書の差分に新たな空白エラーはない（生のCLIログのCRLFはそのまま保存）。

主に新しい採点の結び付きと裁定、最終選定、製品・fixture・文書の一致を確認し、モデル表を採用できるか、重大が残るかを判定してください。必要な実験は局所的な反例に絞り、全件の再採点や全リポジトリの試験を増やす必要はありません。
