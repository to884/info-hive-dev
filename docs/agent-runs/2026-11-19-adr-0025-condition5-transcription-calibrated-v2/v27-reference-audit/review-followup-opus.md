**結論：重大な再現反例はありません。Minor が 5 件で、判定は APPROVED です。** 初回の Major だった「利用枠の拒否と技術失敗の混同」で配布が続く問題は、構造的に直っています。`send_queue` は受領以外の結果が 1 件でも返ると新しい束を投入しません（`delivery.py:171-172`）。`run_role` も、確認していない技術障害が残っている間は配布を保留します（`delivery.py:147-150`）。

依頼にあった確認の観点のうち、次は問題がありませんでした。

- **起動境界の台帳**
  - 予約（claim）だけの試行と、`schema.json`・`start.json` だけの試行は `unlaunched-technical` になり、再送できます。
  - 起動記録（launch）がある試行は、`process.json` がなければ v19 の `receive` で `technical-unresolved` になり、再送されません。
  - 起動記録があるのに `start.json` を消すと拒否されます（`delivery.py:73`）。完了記録（completed）のあとに原票を変えても拒否されます（同 70 行）。
  - 起動記録は `subprocess.run` の直前に書かれます。書き込みに失敗すれば CLI は起動しないので、「起動記録なし」は「露出 0」を意味します。
- **Codex の未証明の利用枠**：`limits.suspected` は分類の名前を変えるだけで、再送を許可する経路はありません。`quota-rejection` は v22 の厳密なイベント列に一致した Claude の応答だけで、そのまま残っています。
- **各段階での照合**：`draw`・`package`・`initialize`・`gpt`/`claude`・`status`・`close`・`source` のすべてで `verify_methods()` を呼んでいます（`run.py` の `main`）。`source` では、確定の直前にも呼んでいます。
- **正解の来歴（v38）**
  - v38 の `changed` 4 行はすべて `direct_intake` に入っています（照合済み）。
  - `development_results` の 19 件はすべて存在します。
  - 対照の留保（`kanpo1828-p3-p0001` の 147 行目、`unresolved`）は、v38 の `result.json` と一致しています。
  - v38 の `score.py` は、訂正に二系統の全文一致（`gpt == claude == after`）と v36 の対照がすべて `same` であることを要求しています。
- **`source.py` の近接候補**
  - `boxes` は半開区間で、幅と高さは 2 以上です。そのため `compatible_bounds` の厳密な重なりの判定と `anchors` の順序の判定で、同じ点の再使用は必ず拒否されます。1 画素幅の箱で抜けることもありません。
  - 候補の条件は次の 3 つです。
    - 二票の始点と終点の 4 値すべてから 3 画素以内にある
    - 二つの閾値で一致する
    - 候補がただ一つである
  - 符号は 2 段で絞っています。まず `trace` が、重なる文字が `APPROVED`（2022・30FB・2026）以外なら例外にし、描いた文字がただ一つであることを要求します。そのうえで `close_round` の経路が 2022・30FB だけを受け付けます。許可対象外の符号が通る例は見つかりませんでした。
- `transport-preflight.json` の `methods` は、`delivery.py`・`limits.py`・`runner.py`・`preflight.py` の現在のハッシュと一致しています。レビュー中に `run.py` が更新され、v38 の正解のディレクトリを `previous.LABELS.with_name(...)` で求める形に変わりましたが、輸送側のファイルは変わっていません。

---

### [Minor] Codex の利用枠に一度当たるだけで、この標本の監査は取り返せない

対象
- `delivery.py:160`（gpt は同時に 6 本）
- `delivery.py:147-155`（`--continue-after-technical`）
- `transport-preflight.json`（`stopped_before_remaining: 6`）

根拠
- 未証明の利用枠は再送しない設計です。一方で、事前試験そのものが、最初の 6 束が同時に着手されて消費されることを示しています。
- 失われた行は `image_cases` で `technical-incomplete` になり、集計では参照不足になります。合格の条件は参照不足が 0 です。
- `--continue-after-technical` には、Codex の利用枠の解除を待つ仕組みがありません。続けて実行すると、さらに最大 6 束を失います。

問題
- 利用枠に一度当たるだけで、1〜6 行が恒久的に欠け、監査は `inconclusive` に確定します。
- 再送しない判断そのものは正しいと考えます。問題は、この帰結が手順書（`protocol.md`）に明記されていないことと、損失を減らす手当てがないことです。

検証方法
`preflight.py` の `controls` と同じ置き換えで、`send` が常に `quota-unproven` を返すようにします。`send_queue` を 2 回実行し、そのたびに 6 束ずつ消費されることを確かめます。

修正の方向性
- gpt の最初の数束は同時に 1 本で送ります。
- `--continue-after-technical` に、利用枠の解除時刻を手で入れる引数を必須にします。
- 「利用枠を一度でも疑ったら監査は保留で確定する」ことを `protocol.md` に書きます。

### [Minor] 起動前に `raw` に一時ファイルが残ると、その系統の全操作が止まる

対象
- `runner.py:9-19`（`publish`）
- `delivery.py:79`

根拠
- `publish` は、書き込み先と同じディレクトリに `.write-*` という一時ファイルを作ります。
- 台帳の側では `.write-*` を無視しています（`delivery.py:49`）。しかし `raw` の側では、`files` に一時ファイルが含まれます。
- 起動記録がない試行で `files.keys() - {"schema.json", "start.json"}` が空でないと、「起動していない試行に原票がある」で例外になります。

問題
- `schema.json` か `start.json` の書き込み中にプロセスが強制終了されると、一時ファイルが残ります。
- 一時ファイルが残ると、`attempts()` を通る `run_role`・`status`・`close`・`source` がすべて止まります。
- 回答は「起動前の途中状態に対応した」としていますが、この経路が残っています。
- ファイルは `prepare` で固定されるので、固定したあとはコードを直して戻すことができません。

検証方法
`preflight.py` の `controls` と同じひな形を作ります。予約を書いたあと、`raw/.write-x` を置いて `attempts` を呼び、`ValueError` になることを確かめます。

修正の方向性
起動記録がない試行では、`.write-` で始まる名前を除いてから判定します。除いたファイルは、来歴として記録に残します。

### [Minor] `limits.suspected` が想定外の JSON の行で例外になる

対象
`limits.py:17-26`

根拠
- `json.loads` の結果が dict であることを確かめていません。そのため、配列や文字列の行が来ると `event.get` で `AttributeError` になります。
- `"rate_limit_info": null` の行でも、`.get("status")` で `AttributeError` になります。
- この関数は、障害の試行（`failed-technical` と `invalid-technical`）でだけ呼ばれます。CLI の出力が崩れやすいのは、まさにこの場面です。

問題
例外は捕まえられないので、上の指摘と同じく、その系統の全操作が恒久的に止まります。

検証方法
`response.jsonl` に `[]` の行か、`{"type":"rate_limit_event","rate_limit_info":null}` の行を書きます。そのうえで `suspected(folder, "claude", {"availability": "failed-technical"})` を呼び、例外になることを確かめます。

修正の方向性
dict でない行は読み飛ばします。`rate_limit_info` は `or {}` で dict に直してから使います。

### [Minor] 台帳は追記専用ではなく、3 つのファイルを消すと読取済みの束を再送できる

対象
`delivery.py:44-81`

根拠
- 起動済みの試行で次の 3 つを行うと、その試行は `unlaunched-technical` と判定され、`send` が再送します。
  - `-launch.json` を消す
  - `-completed.json` を消す
  - `raw` を `schema.json` と `start.json` だけに減らす
- 最後の試行は、予約・起動・完了の 3 つの記録とフォルダーをまとめて消せば、連番の連なりも短くなるだけです。
- `close` より前の状態を、台帳の外の何かと突き合わせる仕組みはありません。

問題
- 回答の「起動後に原票を消すと読み直しが拒否される」は、`raw` だけを消した場合にしか成り立ちません。
- 初回の Minor（来歴の迂回）と同じ脅威が、操作の手順を 2 つ増やしただけで残っています。
- ただし、台帳を `git clean` などでまるごと消した場合は、51 行の検査で検出されます。

検証方法
1. `controls` のひな形で `received` の試行を作ります。
2. 起動記録と完了記録を消し、`raw` を `schema.json` と `start.json` だけにします。
3. `send` が `attempt-0001` の次の試行を始めることを確かめます。

修正の方向性
- 各段階のあとに台帳を git にコミットし、`close` で HEAD との差がないことを確かめます。
- あるいは、次の予約に前の試行の起動記録と完了記録のハッシュを入れ、記録を鎖のようにつなぎます。

### [Minor] 固定する資料にレビューの文書が入っていて、事前試験とのつながりも検査していない

対象
- `method.json` の `development_results`（`review-response.md`・`review-opus.md`・`transport-preflight.json`）
- `run.py` の `prepare`

根拠
- 上の 3 つのファイルは、`prepare` のときにハッシュで固定されます。
- `prepare` は、`transport-preflight.json` の `methods` と現在の `delivery.py` などのハッシュを比べていません。
- `preflight.py` は、事前試験をやり直すことを拒否します（98 行）。

問題
- このレビューを受けて輸送側のコードを直すと、事前試験の証拠は黙って古くなります。
- `prepare` のあとに回答の文書を書き直すと、以後のすべての段階が `verify_methods` で止まり、取り返せません。

修正の方向性
- `prepare` で、`transport-preflight.json` の `methods` が現在のファイルと一致することを要求します。
- レビューの文書を固定するのは、最終の回答を書いたあとだけにします。

---

### 未確認事項
- Codex CLI が利用上限に当たったときに実際に出すイベントと終了コードは、手元の資料にありません。ただし、どの分類になっても配布は止まるので、判定には影響しません。
- 「対照の二票が同じ誤りで一致した場合はこの候補を固定できない」という回答の記述は、コードでは検出できません。両方の票が誤った正解と一致すれば `pair_result` は `same` になるので、回答の方針の宣言として扱いました。
- `status` で `check(..., None)` を通したときに、`shipment.runtime[role]` が埋まっているかは、v12 の `commitment` を読んでいないため確かめていません。

`✶ Insight ─────────────────────────────────────`
- 今回の修正で「止める」と「再送する」が別の判定になりました。止めるのは受領以外のすべての結果、再送するのは証明できた拒否だけです。そのため、分類を誤っても配布が止まるだけで、監査の正しさは損なわれません。
- 残っている指摘は、コードを固定したあとに例外で止まり、二度と動かせなくなる経路です。一度しか抽出できない監査では、正しさの検査と同じくらい、取り返せない停止を作らないことが重要です。
`─────────────────────────────────────────────────`

Final Result: APPROVED

Minor の修正（一時ファイルの除外、`limits` の型の検査、事前試験とのつながりの検査）は、Sonnet・effort medium で足ります。台帳を git に固定する設計の変更は、Opus・effort high が適しています。今回のレビューには Opus・effort high が適当でした。

使用した MCP サーバー: なし
使用した Agent Skills: なし
