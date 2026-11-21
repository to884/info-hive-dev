## レビュー結果

結論として、前回の Major「出典不足の許可リストに `prove` の下流が出す証拠不足が入っていない」は解消しています。残っているのは Minor の 3 件です。

確かめた内容は次のとおりです。

- **分類の向きが逆になった**: 許可リスト `UNPROVEN_SOURCE` をやめ、止める例外を `INTEGRITY_FAILURE`（`source.py:18-24`）の 5 つの文に限りました。それ以外の `ValueError` と `PdfReadError` は、出典不足として `None` と notes に回ります（`:50-56`）。
- **5 つの文は実在する**: 次の箇所が投げる固定の文と、1 字ずつ一致しました。
  - `v61-vertical-point-command-pilot/run.py:82`、`:110`、`:130`
  - `v19-object-source-pilot/trace.py:136`、`:144`
  - どれも f-string ではないので、文の照合が文の組み立てでずれることはありません。
- **前回の実例は出典不足に落ちる**: 前回の実例 `wp-summary-p0010/34` が出す「同じ画素の位置に文字以外の描画がある」（`trace.py:148`）は、`INTEGRITY_FAILURE` に入っていません。そのため出典不足になります。
  - `replay_archived_marks`（`preflight.py:97-124`）は、前回のレビューと同じ抽出条件を使っています。横の行で、座標が 1 つ、丸印が 1 つ、`round` の行です。
  - そのうえで、件数が 16、該当行が `insufficient`、notes の message がこの文であることを必須にしています。実例は拾えています。
- **誤って採用する経路は見つからない**:
  - 来歴の照合（`source.py:38-40`）は、450 DPI の経路と `prove` の経路のどちらよりも前で例外を投げます。
  - `marks()` の `bad-sha` の対照で、この拒否を確かめています。
  - 採用されるのは、`confirm` か `prove` が証明を返したときだけです。例外を捕まえたときは、必ず `None` になります。
  - `confirm` が整合の異常を黙って捨てる場合も考えました（`v44-small-point-pixel-pilot/run.py:96`）。この場合も後の `prove` が同じ `reproduce` を通るので、そこで止まります。
- **診断が結果に残る**:
  - `None` を返す道は 3 つあり、どれも notes を書きます。そのため `after_old` の `unsupported[key]`（`source.py:103`）で `KeyError` にはなりません。
  - notes は `unsupported-point-sources.json` に保存し、そのハッシュを `result.json` に入れています（`:106-116`）。

### [Minor] `prove` の下流が投げる `ValueError` 以外の例外は、引き続き正式の段を止める

対象
`source.py:50`

根拠
- `prove` の経路が捕まえるのは `(PdfReadError, ValueError)` だけです。
- 一方、同じ母集団に使う `confirm` は、`(ValueError, KeyError, TypeError, AttributeError, IndexError)` を捕まえて `None` にしています（`v44-small-point-pixel-pilot/run.py:96`）。
- `prove` の下流には、`ValueError` 以外を投げうる箇所があります。
  - pypdfium2 の `PdfiumError`
  - `render()` の `ops[index]` と `words[0].original_bytes`（`v61/run.py:78-80`）
  - pypdf の書き出し

問題
これらの例外は、どちらにも分類されずに `reader.finish` まで伝わります。前回の Major と同じく、やり直せない停止になります。ただし `render` まで進むのは、U+30FB の字が 1 つに定まった行だけです。起きる確率は低いと見ています。

検証方法
静的に読めば確かめられます。`prove` の 119〜147 行目にある呼び出しのうち、`ValueError` 以外を投げうるものを並べます。

修正の方向性
- 止める対象は、`INTEGRITY_FAILURE` に挙げた 5 つの検査に限ったままにします。
- それ以外の例外の型をどう扱うかを決めて、明記します。例えば `PdfiumError` を出典不足に含めるかどうかです。

### [Minor] 異常に近い文の一部と、ページ全体の再描画の不一致が、出典不足に分類される

対象
- `v19-object-source-pilot/trace.py:129`「元の描画命令の表示状態が不明」
- `trace.py:37`、`:40`（PDFium の API の失敗）
- `v61/run.py:136`（ページ全体の再描画が、固定した画素と一致しない場合）

根拠
- 前の 2 つは、API が失敗したときの文です。資料の性質ではありません。
- 136 行目は、`reproduce` の「元の描画と固定した画素が異なる」（整合の異常として止める）と同じ種類の照合です。それなのに、ここでは `None` を返し、notes の type は `no-proof` になります。

問題
採用の誤りにはつながりません。ただ、環境の異常を出典不足として数えるので、診断の区別があいまいになります。

検証方法
`INTEGRITY_FAILURE` と、各 `raise` の発生源を見比べます。

修正の方向性
- 136 行目の不一致に、別の type を付けます（例: `render-mismatch`）。
- API の失敗を、整合の異常に入れるかどうかを決めて、記録します。

### [Minor] `prior_routes_without_proof` が、試していない経路も試したと記録しうる

対象
`source.py:43`、`:103`

根拠
- 450 DPI の経路を試すのは、次の 2 つを満たすときだけです。
  - ページの `evidence` の記録が、ハッシュと一致する
  - その記録に `unsupported` がない
- 一方、`after_old` は条件に関係なく、`["isolated-fallback", "fixed-450-dpi-location"]` を書きます。
- v47 では、20 ページのどれにも `unsupported` がなく、`wp-summary-p0010` の記録はありました。そのため実例では正しい記録になります。しかし新しい標本で、記録のないページの行が来ると、事実と食い違います。

問題
監査の記録が、試した経路を多めに主張します。

検証方法
`data["evidence"]` にページの記録がない行で、`after_old` の結果を追います。

修正の方向性
`mark_from_source` が、実際に試した経路を notes に記録するようにします。

### 未確認のこと

- 回帰検査を実際に動かすこと（Codex の側で実行中です）は、今回行っていません。そのため、16 行のうちほかの 15 行が `INTEGRITY_FAILURE` で止まらないかは、前回のレビューの観測に頼っています。
- `replay_archived_marks` が必須にしているのは 1 行の状態だけです。ほかの 15 行は、件数と preflight.json への記録で見るだけです。

`✶ Insight ─────────────────────────────────────`
- 前回の欠陥は、許可リストで深い下流の例外を分類しようとした点にありました。今回は、止める対象を少数の整合の検査に限り、残りを安全な側（採用しない）に倒しました。この形だと、未知の例外の文が来ても誤って採用することはなく、診断の精度が下がるだけで済みます。
- 例外の文を固定の文字列で照合する設計は、f-string を使うと壊れます。そこで、5 つの文が発生源で固定の文になっていることを確かめました。
`─────────────────────────────────────────────────`

Final Result: APPROVED

---
- このタスクに最適なモデルとエフォート: Opus、high
- 次のタスク（Codex の回帰検査の結果を突き合わせる）: Sonnet、medium

使用した MCP サーバー: なし
使用した Agent Skills: なし
