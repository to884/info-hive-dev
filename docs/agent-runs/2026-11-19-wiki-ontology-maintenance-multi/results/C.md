公開版の実装と ADR-0023 を確認しました。書き込みを直列化しても、同じ実体が二重登録される場合や、問い合わせが移行途中の異なる版を読む場合が残ります。それぞれの再現条件を設計書の条文に照らしています。## 結論

**要修正です。実体を知識の単位とし、利用者の指示で既存の定義と記録を一緒に移行する方針は、作者の二つの要件を満たしています。** 一方、いまの設計では、通常の取り込みで同じ実体が二重登録される、部分移行後に誤った件数を返す、移行時に訂正の対象が変わる、という実装も仕様を満たし得ます。

実装設計に進む前に、同一性を確定する時点、移行後の問い合わせと参照の意味、公開の境界、見直しで読む資料の範囲、既存 wiki の適用条件を、反例ごとの受け入れ条件として決めてください。保存形式やロックの方式は、その条件を満たせるものを実装設計で選べます。

## 根拠

1. **重大｜書き込みを直列化しても、同じ製品が二重登録される。** 同じメーカー内で一意な品番を持つ製品を、二つの `ingest` が別々の表記で見つけます。両方が対象ページの作成前に照合し、異なる ID とパスを用意すると、先に片方が書いても、後続側の書き込み先は空いており、定義の版も同じです。見直し案の適用前には新規ページによる ID 重複を再検査しますが、通常取り込みの明示的な再検査条件は定義の版の変更です。ADR-0023 の詳細設計も、別スラッグでの意味の重複を対象外にしています。確定に使った識別情報と「該当する実体がまだない」という前提を、書く段で最新の記録に照らし直す条件が必要です。二つの取り込みが完了したとき、実体は一つで、両方の出典をたどれることを試験にしてください。 [見直し設計 112–119 行](/C:/Works/info-hive-dev/docs/plans/wiki-ontology-maintenance-2026-11-19.md:112)・[提供案 135–144 行](/C:/Works/info-hive-dev/docs/plans/wiki-ontology-feature-experience-2026-11-19.md:135)・[書く段の設計 285–305 行](https://github.com/to884/info-hive-dev/blob/main/docs/plans/wiki-apply-2026-11-14.md#L285-L305)

2. **重大｜部分移行後の集計に、数える単位と保留の適用範囲がない。** 「製品Aの契約企業は何社か」に対し、A社の同じ契約を二つの記事が裏づけ、B社については旧 `利用する` から契約か判別できないとします。旧形式を踏襲すれば、A社のエッジは出典ごとに `1 + 1 = 2` 本ですが、確定した契約企業は `|{A社}| = 1` 社です。製品Bだけの保留はこの問いに影響しません。設計には二重計上を防ぐ方針がありますが、根拠・主張・実体のどれを数え、製品・期間・状態によってどの保留が結果に影響するかが未定です。現行のグラフ CLI はエッジ行を返し、MCP も同じ処理を呼びます。CLI・MCP と通常の `/wiki:query` で、問いに応じた確定結果、影響する保留、集計対象の範囲を一貫して扱う条件が必要です。 [見直し設計 70–78 行](/C:/Works/info-hive-dev/docs/plans/wiki-ontology-maintenance-2026-11-19.md:70)・[グラフ抽出 736–775 行](https://github.com/to884/info-hive-wiki/blob/v0.35.1/skills/info-hive/scripts/wiki_graph_extract.py#L736-L775)・[グラフ問い合わせ 144–155 行](https://github.com/to884/info-hive-wiki/blob/v0.35.1/skills/info-hive/scripts/wiki_graph_query.py#L144-L155)・[MCP 460–481 行](https://github.com/to884/info-hive-wiki/blob/v0.35.1/skills/info-hive/scripts/wiki_mcp_server.py#L460-L481)

3. **重大｜分割時に、参照先の ID が解決できても訂正の意味を壊せる。** 旧 `利用する` の一項目から、試用と契約の二つの主張を取り出せるとします。旧項目を `contradicts` で指す別の資料が「その期間中は未契約だった」と述べている場合、矛盾するのは契約の主張だけです。旧 ID から新 ID 二つへの対応を保存しても、両方に参照を付け替えれば、試用まで矛盾扱いになります。現行 lint の参照検査は、値が既存のノード・出典・エッジのいずれかに当たれば通ります。分割・統合の前後で、参照ごとに根拠と適用条件から対象を確かめる必要があります。対象を決められない場合は、旧主張への参照と未確定の理由を保持できる場合に限って部分移行し、それができなければ該当変更を保留してください。 [見直し設計 53–68 行](/C:/Works/info-hive-dev/docs/plans/wiki-ontology-maintenance-2026-11-19.md:53)・[同 112–116 行](/C:/Works/info-hive-dev/docs/plans/wiki-ontology-maintenance-2026-11-19.md:112)・[グラフ lint 290–297 行](https://github.com/to884/info-hive-wiki/blob/v0.35.1/skills/info-hive/scripts/wiki_graph_lint.py#L290-L297)

4. **重大｜適用完了の報告を止めても、問い合わせが新旧を混ぜて読める。** 書く段の設計では、正本を置き換える P4 とグラフを再生成する P6 が別です。通常の `/wiki:query` はグラフで候補を選んだ後に Markdown を読みます。P4 と P6 の間に読めば、旧グラフと新しいページを一つの回答で使えます。グラフとページの間で適用が完了した場合も同じです。協調する読み手が、問いの開始から出典確認まで同じ公開版を参照するか、版が揃わない場合は回答を保留して再試行する、という条件が必要です。正本更新直後の停止と、問い合わせ中に公開版が切り替わる場合の両方を試してください。 [見直し設計 107–115 行](/C:/Works/info-hive-dev/docs/plans/wiki-ontology-maintenance-2026-11-19.md:107)・[書く段の設計 298–305 行](https://github.com/to884/info-hive-dev/blob/main/docs/plans/wiki-apply-2026-11-14.md#L298-L305)・[通常の問い合わせ手順 14–20 行](https://github.com/to884/info-hive-wiki/blob/v0.35.1/commands/query.md#L14-L20)

5. **重大｜旧定義で作った要約だけを全件読んでも、概念の乖離を見落とせる。** 現行の取り込みは raw を要約し、軽い言及には専用ページを作らないことがあります。たとえば、旧来の製品分類で取り込んだ複数の営業資料が「機器の販売から運用受託への移行」に軽く触れ、各要約からその記述が落ちていたとします。見直し設計の「新旧の記事」を wiki の Markdown と解釈すると、全記事を読み終えても、繰り返し現れる新しい概念を拾えません。提案時に要約と原本のどちらを確認したかを記録し、「新概念を探した範囲」をその実績に合わせる必要があります。差分分析の再利用条件にも、原本の版、分析時の定義、問いを含めてください。問いが変わったときは、記事の指紋が同じでも再分析が必要になり得ます。 [見直し設計 37–45 行](/C:/Works/info-hive-dev/docs/plans/wiki-ontology-maintenance-2026-11-19.md:37)・[取り込み手順 353–378 行](https://github.com/to884/info-hive-wiki/blob/v0.35.1/skills/info-hive/references/ingest-workflow.md#L353-L378)

6. **重要｜既存 wiki の導入条件が、依存先の ADR と揃っていない。** 提供案は、初期化済みで `graph/ontology.yaml` がなければ、グラフの導入と案の適用を一緒に提示します。配布スキルは `wiki/raw` を置ける構成として案内していますが、ADR-0023 は、その構成を共通の書く段で扱う前に raw を wiki の外へ移すよう求めています。このままでは、既存の有効な構成で試行まで進み、採用時に初めて適用不能と分かります。対象解決時に適用可否と理由を示し、既存構成を初期版で扱うなら ADR の変更を設計に含めてください。 [提供案 63–72 行](/C:/Works/info-hive-dev/docs/plans/wiki-ontology-feature-experience-2026-11-19.md:63)・[ADR-0023 59–64 行](https://github.com/to884/info-hive-dev/blob/main/docs/adr/0023-wiki-apply-uses-journal-and-per-wiki-lock.md#L59-L64)

## 検討した代替案

- **初期版を語彙の追加だけに絞る。** 先行提供には使えます。要望の完成形としては、同義の型の統合や、広すぎる関係の分割、既存記録の移行を利用者が実行できないため、採りません。 [見直し設計 138–143 行](/C:/Works/info-hive-dev/docs/plans/wiki-ontology-maintenance-2026-11-19.md:138)
- **曖昧な記録が一つでもあれば、見直し案全体の適用を止める。** 実装は単純になりますが、製品の分類に保留があるだけで、独立して確定できる顧客の役割整理も止まります。参照と問い合わせの意味を維持できる範囲で、依存の閉じた部分だけを適用する方が、設計の利用例に合います。 [見直し設計 93–100 行](/C:/Works/info-hive-dev/docs/plans/wiki-ontology-maintenance-2026-11-19.md:93)・[同 124–136 行](/C:/Works/info-hive-dev/docs/plans/wiki-ontology-maintenance-2026-11-19.md:124)
- **定義と参照先が揃っていることを lint で確認し、移行成功とする。** 存在確認には使えますが、参照が別の主張に付け替わった場合や、根拠の本数を企業数として数えた場合も通り得ます。成功条件には、出典を含む移行前後の問いへの期待結果が要ります。 [見直し設計 99–102 行](/C:/Works/info-hive-dev/docs/plans/wiki-ontology-maintenance-2026-11-19.md:99)・[グラフ lint 290–297 行](https://github.com/to884/info-hive-wiki/blob/v0.35.1/skills/info-hive/scripts/wiki_graph_lint.py#L290-L297)

## 前提と不確実性

- 反例は説明用の架空データです。同一性の反例では、メーカーと品番の組がその wiki で確認済みの識別条件であると仮定しました。発生頻度は測っていません。
- レビュー対象は提示された行番号付きの写しです。ローカルの読み取り環境が起動しなかったため、既存実装は GitHub の `v0.35.1`、ADR とその詳細設計は開発リポジトリの公開版で照合しました。手元のサブモジュールとの差分は未確認です。ファイル変更、ビルド、実行試験は行っていません。
- 作者の判断が要るのは、初期版で一貫性を保証する読み取り経路の範囲、旧配置の wiki への対応、原本を読めない場合に表示できる判断の範囲です。任意の外部編集や複数 PC からの同時書き込みまで保証するとは仮定していません。 [ADR-0023 62–64 行](https://github.com/to884/info-hive-dev/blob/main/docs/adr/0023-wiki-apply-uses-journal-and-per-wiki-lock.md#L62-L64)

## 参照

- 提示された設計書3本。 [見直し・整理](/C:/Works/info-hive-dev/docs/plans/wiki-ontology-maintenance-2026-11-19.md:1)・[提案・適用の提供案](/C:/Works/info-hive-dev/docs/plans/wiki-ontology-feature-experience-2026-11-19.md:1)・[実体を単位とする要件](/C:/Works/info-hive-dev/docs/plans/wiki-ontology-entity-granularity-2026-11-19.md:1)
- 書く段の範囲、承認、日誌、ロック、適用とグラフ再生成の分離。 [ADR-0023 20–30 行](https://github.com/to884/info-hive-dev/blob/main/docs/adr/0023-wiki-apply-uses-journal-and-per-wiki-lock.md#L20-L30)・[詳細設計 285–305 行](https://github.com/to884/info-hive-dev/blob/main/docs/plans/wiki-apply-2026-11-14.md#L285-L305)
- グラフ、原本、通常の操作経路の補足。 [グラフ運用 21–29 行](https://github.com/to884/info-hive-wiki/blob/v0.35.1/skills/info-hive/references/graph-workflow.md#L21-L29)・[グラフ問い合わせ 225–259 行](https://github.com/to884/info-hive-wiki/blob/v0.35.1/skills/info-hive/scripts/wiki_graph_query.py#L225-L259)・[Codex の操作 5–26 行](https://github.com/to884/info-hive-wiki/blob/v0.35.1/skills/info-hive/references/codex.md#L5-L26)・提示された `wiki:info-hive` の `SKILL.md`「保存の範囲とディレクトリ構成」
- レビューの観点を確認したプロジェクト wiki。 [索引 130 行](https://github.com/to884/info-hive-dev/blob/main/wiki/index.md#L130)・[スキーマ 1–21 行](https://github.com/to884/info-hive-dev/blob/main/wiki/SCHEMA.md#L1-L21)・[[敵対的レビューで設計を直す進め方]]（16–27、45–48 行）

使用した MCP サーバー: GitHub  
使用した Agent Skills: wiki:info-hive
