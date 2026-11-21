Ready to write up; checking with advisor before finalizing.**結論：Major 1件、Minor 4件です。判定は REJECTED です。** Major は、Codex（Sol）の利用上限による拒否を技術失敗と区別できず、送信も止まらない点です。一度だけの監査標本が、運用上の理由で取り返せない形で「保留（inconclusive）」に落ちる経路があります。

依頼にある確認の観点のうち、次は問題を見つけられませんでした。

- **事前固定と一回の抽出**：`prepare` は二重実行を拒否し、`draw-started.json` は `save_once` で書かれます。`packets.prepare` は母集団の固定（LOCK）と、抽出前に固定した入力のハッシュを照合しています。一行一束の構成は `image_cases` が確かめています。
- **同じ画像と新規セッション**：二系統は同じ `cards/<pack>` を読みます。`v19 receive` が argv、画像の SHA、要求の SHA を照合します。`collect` は全試行のセッションの重複と、旧セッションとの重複を拒否します。束や系統をまたいで原票を複製しても、要求の SHA が合わずに拒否されます。
- **出典補助の範囲**：`MARK` は `round|trail` だけです。補える符号は 2022・30FB・2026 に限られます。本文はどの経路でも画像の票から採り、置き換えるのは印の部分だけです。`compatible_bounds` と `anchors` の検査で、同じ点の再使用と順序の逆転は拒否されます。v28 の地色の検査は、対象窓が完全に一色の場合だけを通します。
- **分母**：`summarize` は層ごとに `min(15, population)` を強制し、参照を全行そろえることも求めます。開発や既監査の印は重なりの記録に使うだけで、分母は減りません。
- **正解の漏れ**：配布の画像と指示に、正解の本文（`targets`）は入っていません。

---

### [Major] Codex の利用上限の拒否と、型から外れた Claude の 429 が技術失敗として確定し、残りの束を投入し続ける

対象
- `v27-reference-audit/delivery.py:102-119`（`send_queue`。保留に入れるのは 115 行の `quota-rejection` だけ）
- `v22-list-mark-pilot/recover.py:48-49`（`role != "claude"` ならそのまま返す）、`16-20`（5 つのイベントの並びを厳密に要求する）
- `v19-reference-audit/run.py:190-191`（`returncode != 0` なら `failed-technical`）
- `v27-reference-audit/delivery.py:46-49`（直前の試行が `unstarted` か `quota-rejection` でなければ再送を拒否する）

根拠
- `inspect_attempt` が `quota-rejection` を返すのは、`claude` で、v22 で観測したイベントの並びに完全に一致した場合だけです。Codex の利用上限による終了は、0 以外の終了コードで `failed-technical` になります。
- `send_queue` は `quota-rejection` 以外の結果では投入を止めません。Codex は同時に 6 本ずつ、残りの束をすべて送ります。
- 一度 `failed-technical` になった束は、`attempts()` の 47 行の条件で再送できません。
- その行は `image_cases` の 171-172 行で `technical-incomplete` になり、`summarize` では `unresolved_reference` として数えられます（`audit_selection_v9.py:132-133`）。その結果、`status` は `inconclusive` になります（同 146 行）。
- 前例があります。`v19-reference-audit/development-result.md:5` に「Opusの残り66束117行には5時間枠の利用上限の応答が記録され」とあります。今回は一行一束なので、各系統で行数と同じ数のセッションを起動します。束数は v19 の 212 束より増えます。

問題
- Codex が利用上限に達すると、それ以降の束はすべて、画像を読む前に拒否されます。それでも「技術失敗」として確定します。これは依頼にある「利用枠の拒否」と「技術失敗」の混同そのものです。
- Claude でも、制限の種類や前後のイベントの違いで型から外れれば、同じように残りすべてを使い切ります。
- その結果、既知の層に参照不足が残り、合格に必要な「参照不足0」を満たせなくなります。標本は一度しか抽出できないので、この版の監査は取り返せません。
- 再送の条件を緩めないのは正しい判断です。欠けているのは、送信を止める仕組みです。

検認方法
1. 一時ディレクトリに `delivery` のひな形を作ります。
2. `Delivery.inspect_attempt` を、`gpt` のとき常に `{"availability": "failed-technical", "response_sha256": ...}` を返す関数に差し替えます。
3. `run_role(shipment, "gpt")` を実行します。
4. 全束に `attempt-0001` ができ、`holds` は空のまま、2 回目の実行では `todo` が空になることを確かめます。
5. `close` が成功し、`technical-incomplete` が束の数だけ残ることも確かめます。

修正の方向性
- 系統ごとに、`received` 以外の結果が出た時点で、新しい束の投入を止めます。実行役が原票を確かめてから、明示的に再開する形にします。
- Codex にも、画像を読む前に拒否されたことを示す厳密な判定を追加します。条件は、イベントの並び、使用量 0、回答なしです。判定できない場合は再送しないまま、送信を止めます。
- 同時実行数を落とし、最初の数束で上限を検知できるようにすることも検討してください。

### [Minor] 試行の記録を後から改ざんしても検出できない（最後の試行を消すと読み直せる）

対象
`delivery.py:40-58`（`attempts`）、`delivery.py:149-156`（`close`）

根拠
試行の連なりの正しさは、`attempt-NNNN` の連番と、`claim.json` の内部の整合だけで確かめています。作った試行の数やハッシュを、配布物の外に追記していく記録がありません。`old_sessions()` は、消された原票のセッションを知りようがありません。

問題
`close` の前に最後の `attempt-000N` を消すと、`send()` は消した試行を「前の試行」とみなして新しい試行を始めます。都合の悪い有効票を引き直しても、`collect` と `close` は通ります。v12 の `launches` にも同じ性質があり、今回の変更で生じたものではありません。それでも、依頼の「原票の来歴の迂回」に当たります。

検認方法
一時のひな形で `attempt-0001` に `received` を作り、フォルダーごと消します。そのあと `send` を実行し、`attempt-0001` が新しく作られて `close` が成功することを確かめます。

修正の方向性
`claim.json` を作るたびに、その SHA を追記専用の台帳に記録します。置き場所は `OUT` の外で、git で追跡している `HERE` にします。`close` と `image_cases` では、台帳と試行の数とハッシュが一致することを確かめます。

### [Minor] 作りかけの試行が残ると、その系統の操作がすべて止まる

対象
- `delivery.py:75-79`（`mkdir` のあとに `save_once`）、`delivery.py:45`
- `delivery.py:51-52`
- `v16-structured-readers-pilot/run.py:32-47`（`schema.json` を `start.json` より先に書く）

根拠
- `mkdir` と `claim.json` の保存の間でプロセスが止まると、空のフォルダーが残ります。`self.audit.load(label)` が `FileNotFoundError` を出し、これはどこでも捕まえていません。
- `raw/schema.json` だけがあって `start.json` がない状態でも、例外になります。この状態は CLI の起動前なので、画像への露出は確実に 0 です。

問題
`run_role`、`status`、`close`、`source` は、どれも `attempts()` を通ります。そのため、上の状態が一つ残るだけで、その系統の全操作が止まります。直すには手でフォルダーを消すしかなく、それは上の改ざんの指摘と同じ操作になります。

検認方法
一時のひな形で、空の `attempts/pack-000/gpt/attempt-0001/` を作ります。`status` を実行し、`FileNotFoundError` で止まることを確かめます。

修正の方向性
- `claim.json` は一時ディレクトリに書いてから、`rename` で確定させます。
- `start.json` がない `raw` は例外にせず、「未起動（露出0）」として記録します。そのうえで、再送するかどうかを明示的に決めます。

### [Minor] ライブラリの版を確かめるのが出典の段階だけで、失敗が最後まで分からない

対象
`run.py:123-127` と `214`。`draw`（`v14 selection.draw`）、`package`（`packets.prepare`）、配布では、`versions` を確かめていません。

根拠
`LOCK["versions"]`（numpy、Pillow、pypdfium2 など）を確かめるのは `verify_methods()` だけで、呼ばれるのは `source` のときだけです。

問題
途中でライブラリの版が変わると、二系統の読み取りをすべて使い終えたあとで初めて止まります。また、配布画像を作ったときの Pillow の版が固定時と違っても、それを検出できません。

修正の方向性
`draw`、`package`、`initialize`、`close` でも、`versions` と `inputs` を確かめます。

### [Minor] 正解に v26 を選ぶ場合、対照の不一致を確かめていない

対象
`run.py:43-54` と `63-68`、`v26-kanpo-name-candidate/score.py:104-106`

根拠
v26 の採点結果には、二読で正解と食い違った対照の行が `development_control_issues` として記録されます。v27 の `methods` と `prepare` は、これが空であることを求めていません。

問題
対照で二読の結果が食い違っていても、全配置での採点に通れば、その訂正を正解として母集団に固定します。

修正の方向性
`development_control_issues == []` を条件にします。不一致を例外として認める場合は、その行を `method.json` に固定します。

---

### 未確認事項（判定に関わるが、資料がまだないもの）
- `v27-reference-audit/method.json` と `population-lock.json` がまだありません。そのため、`guides` の文言、`direct_intake` が v20〜v30 の開発行を漏れなく含むか、`gold` を v19 と v26 のどちらにするかは確認できていません。
- `v26-kanpo-name-candidate/candidate-score.json` はまだなく、`v31-kanpo-glyph-pilot` も空です。v26 の経路は動かして確かめていません。
- Codex が利用上限で拒否したときに実際に出るイベントの形は、手元の資料に記録がありません。

`✶ Insight ─────────────────────────────────────`
- この監査の安全装置は、確信できないものは再送しないという一方向に寄せて作られています。分類の誤りは保守側に倒れます。その代わり、取り返せない欠損は送信の制御の側で生じます。
- 出典の補助は、画素の再現で描画の所有者を切り分け、PDF の命令やフォントの対応、点の位置と照合します。三重の照合なので、本文を PDF から採る経路は構造的に塞がれています。
`─────────────────────────────────────────────────`

Final Result: REJECTED

Major の修正（送信の停止と Codex の判定の追加）は、Opus・effort high が適しています。今回のレビューも Opus・high が適当でした。

使用した MCP サーバー: なし
使用した Agent Skills: なし
