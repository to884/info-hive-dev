前回の session 12d68d69-4d89-4098-aa5f-1bde83add5da の重大7件を修正したので、実装と測定手順を敵対的に再レビューしてください。読み取りだけ。他エージェント/LLM/API/Webを呼ばず、コードを書き換えないでください。

今回の目的は「候補を読むモデルとエフォートの確定、およびOpusレビュー」です。リリースやマージの承認は求めていません。第3版の158回の採取は完了し、別の1件の採点作業でモデルと費用を伏せた意味の採点を進めています。モデル表の最終値はまだ確定していないため、この回では値そのものを承認せず、下の実装と最終判定の仕組みを検証してください。意味の採点が終わった後、同じセッションで結果と最終値だけを追加確認します。

変更の要点:
1. 単語やファイル名の一致は診断値だけ。回答採取前に命題を固定し、全158回答をブラインドでsupported/omitted/wrongと引用の役割、根拠のない主張に分けて判定する。未読の出典を正直に紹介したものを、未読を根拠にした引用とは数えない。grade_reader_models.py が欠測・写しや元回答の改変を拒み、95%とゼロ誤り、費用の基準で選定する。
2. reader_measurement_runtime.py に採取を分離した。採点器の変更は指紋を変えない。第2版の測定時コードとデータを保存し、recorded_experimentで現在の製品やCLIの版と混ぜず再採点できる。CLI版は各試行の記録。
3. protocol3では自動メモリを設定と環境変数で無効にし、実際の全158件のinit.memory_paths={}を確認。モデルの強制上書きを拒む。CLIの自動更新も止めた。各問の命題はv3のmanifestのdata_sha256に含む。
4. valid_observation（通信・モデル・計量）とformat_ok（品質）を分けた。形式の失敗は有効な失敗として保持し、自動再試行で成功するまで選別しない。
5. 子は選別結果のメタデータだけを返し、親が実際のhook出力をstdoutへ書いてflushしてから既出を保存する。親子で単調時計の絶対時刻を共有。キーはscope・wikiの実体・relpathの組。出力の失敗や保存の遅れ、別wiki同名ページの回帰テストを追加。
6. HEADERの読む主体をmainまたはreaderと明示。query-confidenceは報告だけではmainの既読に数えず「未読Low」、mainが本文を開く必要がある。0Fも同じwiki/同じpageの意味検索が必要。
7. R0の最安という主張を撤回。Read単独の測定の順位を全Agent経路の総費用の最安とは主張しない。代表3件を実際のAgentで呼び、指定model/effort、戻り、actual modelUsage、main Readなしを記録した（reader-models-v3/delegation-validation.json）。最終表が変われば選定後にその値でも確認する。

既知の未解決事項: publication-timing.json の150ページ・別作業の高CPU負荷があるPCではGit Bash/uvを含む検索p95が5.3秒、候補到達3/10だった。内部2.5秒はuvやPython起動を含む外側期限の保証ではない。調査レポートとADRにリリース前の性能課題として記録し、旧版の0.5秒を現行保証としていない。ほかの作業のプロセスは停止していない。この既知のリリース阻害と、今回のモデル表/測定の確定を阻む欠陥を分けて報告してください。

検証済み: hook63、measurement22、page_set30(1skip)、uninitialized41(2skip、uv+PyYAML環境)、spawn8(1skip)。合計164成功/skipを含むテスト。ゲートrecall.889 precision.893、負例発火0。テストを自分で動かすならuninitializedは冒頭のuv/PyYAMLの指定が必要。

主に対象コードとテスト、query-confidence、prompt-context、docs/research/wiki-prompt-hook-stage0-2026-11-17.md を読んでください。158件の原記録すべてをこの回で再読する必要はありません。重大な欠陥は実証例と該当箇所を示してください。