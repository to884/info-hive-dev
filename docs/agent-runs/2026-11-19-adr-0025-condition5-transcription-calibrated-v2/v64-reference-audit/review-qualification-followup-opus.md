## レビュー結果

前回の Major だった固定の欠落は解消しています。ただし、新しく入れた「出典不足」の許可リストが狭すぎて、本番の出典の段が通常の証拠不足で止まります。この問題は v47 の正式の行で再現しました。Major が1件、Minor が1件です。

**検証の方法**
- 作業ツリーの外の一時ディレクトリ（`%TEMP%\v64rev`）に計測用のスクリプトを置き、`uv run --no-project --with …` と `python -B` で読み取りだけを行いました。
- リポジトリのファイルは書き換えていません。`preflight.main()` と `packets()` はコーパスに一時ディレクトリを作るので、実行していません。
- `marks()` と、v47 の正式出力に対する `mark_from_source` は、書き込みがないことをコードで確かめてから実行しました。`transport.check` は `status` で呼んでおり、`commitment` は読み取りだけです。

---

### [Major] 出典不足の許可リストに、`prove` の下流が出す証拠不足が入っていない。正式の `source` の段が止まり、やり直せない

**対象**
- `v64-reference-audit/source.py:18-25`（`UNPROVEN_SOURCE`）、`:49-56`（`except` の中で投げ直す箇所）
- 呼び出し先は次のとおりです。
  - `v61-vertical-point-command-pilot/run.py:120-124`（`trace.reproduce`、`proof.old.visible_glyphs`）
  - `v19-object-source-pilot/trace.py:27-41`（`font_name`）、`:124-175`（`reproduce`）
  - `v20-trail-source-pilot/run.py:71`

**根拠**
- `UNPROVEN_SOURCE` にある6つの文は、`strict_points.physical` と v61 の `matching_fonts`・`candidates` が出すものだけです。
- `prove` は `physical` の後で `trace.reproduce` と `visible_glyphs`（内部で `font_name`）を呼びます。これらは許可リストにない `ValueError` を出します。
  - 証拠不足の性質のもの：「同じ画素の位置に文字以外の描画がある」「他の描画でも同じ位置にインクが残る」「文字の描画だけで固定画素を再現できない」「点を描画するオブジェクトを確認できない」「丸印の埋め込んだフォントを確認できない」
  - 実装か環境の異常に近いもの：「描画命令の切り分けに失敗」「元の描画と固定した画素が異なる」など
- **実測の反例**：v47 の正式の標本で、丸印が1つの横の行は16行ありました。その全行に v64 の `mark_from_source` を当てました。
  - `wp-summary-p0010/34` は、正式の証跡の理由が `source-location-not-proven` です。本番では `fallback` が `None` を返し、`after_old` から `mark_from_source` に回ります。
  - この行で `ValueError 同じ画素の位置に文字以外の描画がある` が投げ直されました。
  - 同じ行は v18 の `result.json` でも「点と同じ場所に文字以外の描画がある」で insufficient でした。このコーパスで再び起きる種類の不足です。
- 偏りもあります。v27 の `fallback` は丸印の経路で `trace.trace` を呼び、同じ `reproduce` の例外を捕まえて `None` を返します（`v27-reference-audit/source.py:72-75`）。そのため `prove` に回る行は、先の経路が `reproduce` の失敗で落ちた行に集まります。
- 事前確認はこの問題を検出できません。`marks()` の負の対照（`defense-p0089/88`）は `reproduce` を通った後、符号が U+30FB でないことで `prove` の128行目から `None` を返します（行番号で追跡しました）。

**問題**
- 新しい標本に同じ種類の行が1つでもあると、`reader.finish` の途中で例外になります。`reference-evidence.json`、`unsupported-point-sources.json`、`result.json` は保存されません。
- 再実行しても、同じ行で同じように止まります。
- `source.py` を直すと、事前確認に記録したハッシュと合わなくなります。`check_preflight()` がすべての action を拒否するので、抽出とモデルの読取を終えた一度きりの監査を閉じられません。
- v47 の標本では、丸印の横の行16行のうち1行が当たりました。同じ規模の新しい標本で起きる確率は低くありません。
- 依頼の「出典不足として想定した理由と、実装異常・取り違えを区別する」に対して、区別の線が `prove` の外側の6つの文で引かれており、下流の証拠不足を「異常」に分類しています。

**検証方法**
1. `launch` を読み込む。`configure()` は呼ばない。`core.OUT` は v47 のままである。
2. `core.transport.check(core.OUT/"delivery", sha(packages.json))` と `core.image_cases(...)` で行を得る。
3. 丸印が1つで座標が1つの横の行に、`launch.source.mark_from_source(item, source-commands, catalog, {}, delivery/"source-assets", source_assets, notes)` を呼ぶ。
4. `wp-summary-p0010/34` が上の例外を投げることを確かめる。

**修正の方向性**
- 例外の文を並べた許可リストで、深い下流を分類するのをやめる。
- 異常として止めるものを、来歴と整合の検査に限って明示する。対象は次のとおりです。
  - 来歴の不一致
  - 「登録済みの中黒のCIDと符号が異なる」
  - 「非表示にする一つの描画命令が異なる」
  - 「元の描画と固定した画素が異なる」
  - `ValueError` 以外の型
- それ以外の `ValueError` と `PdfReadError` は、理由と型を付けて出典不足として `notes` に記録する。下流に専用の例外の型を設けて段で分けてもよいです。
- 事前確認に回帰の試験を足す。v47 の正式の丸印の16行を `mark_from_source` に通し、投げ直しが0件であること、`wp-summary-p0010/34` が出典不足として記録されることを必須にする。

---

### [Minor] 異常と不足を区別しているのは v61 の経路だけで、記録も一部に限られる

**対象**
- `source.py:40-47`（先に通る `strict_450.confirm`）
- `v44-small-point-pixel-pilot/run.py:61, 96-97`
- `v27-reference-audit/source.py:72-75, 81-90`

**根拠**
- 最初の経路の v44 `confirm` と、その前の v27 `fallback` は、`ValueError`・`KeyError`・`TypeError`・`AttributeError`・`IndexError` をすべて `None` にしており、記録しません。
- `notes` には、`prove` が許可リストの例外を出したときだけ書きます。`prove` が `None` を返した行（例：88）は記録されません。
  - 実測では、`defense-p0453/52` などは記録されました。88 は記録されませんでした。

**問題**
- 同じ `reproduce` の異常が、前の2つの経路では黙って `None` になり、v61 の経路では止まります。
- 前の経路に実装の異常があっても見えません。
- ハッシュで結び付けた「出典不足の記録」は、不足の行の一部しか含みません。
- 誤って合格する方向には働かないので Minor としました。

**修正の方向性**
- 3つの経路の結果を、行ごとに「確定／不足（理由）／異常」として一つの記録にまとめ、`result.json` に結び付ける。

---

### 確かめて問題がなかった点

- **固定の網羅（前回の Major）**
  - `launch` の読み込みと `dependencies()` の間に開いた作業ツリー内の `.py` は132個でした。監査用のフックで数えています。すべて `dependencies()` のキーに入っていました。
  - 関数の中の動的ロードを全件調べました。v35 ruler、v23、v27 source、v19 source、v25、v28、v27 diagnose から v27 run・v10 diagnose へ、v44 です。どれも `DEFERRED`、v47 の事前確認の入力、または読み込み時の `sys.modules` に入っていました。
  - `check_preflight()` は、事前確認のすべての入力を再ハッシュします。そのうえで「`dependencies()` ⊆ 事前確認」を確かめ、`enforce` の後は未固定の `spec_from_file_location` を拒否します。
- **小点の対照（`marks()` を実際に実行）**
  - 117行目と120行目は、v44 の経路で確定しない（`confirm` が `False`）ことを確かめたうえで、`single-vertical-source-command` で確定しました。v69 の証拠と一致しています。
  - `bad-sha` は来歴の違いで拒否されました。
  - 88 は出典の段で、符号の違いにより拒否されました。
  - 照合は頁と行で行っています。
- **字体例**
  - `verify_packages` は、保存した最終の `request["prompt"]` を、両方の軸で `REMOVED` に照らします。`continue` より前で行うので、縦の行も含みます。
  - 送信は、この本文をそのまま使います。受領記録が `prompt_sha256` で照合しています。
  - 素材の「」の例は次のとおりで、すべて `REMOVED` で拾えます。
    - `orientation.VERTICAL`：「ニ」「二」「ロ」「口」
    - `instructions.VERTICAL`：「っ」「つ」
  - `guides` の「●」「➢」「。」は、記号の形の説明です。
- **参考集計**
  - v70 の `changed` にある5行をすべて除いています。
  - v47 の正式出力で確かめたところ、`targets` の `known`・`text` と、`reference-evidence.json` の `answer` の `status`・`text` の形が、`development_overlap()` の参照と合っていました。
  - 既存の `summary` と判定は変えていません。

### 未確認事項

- `packets()` は実行していません。開発用の配布で、枠の上下、座標の結合、24枚の上限が通るかは見ていません。
- `enforce` の後の通常の `import` はフックの対象外です。調べた範囲では本番の経路にありません（`v47 official.preflight` の `import preflight` には到達しません）。ただし `source`、`diagnose`、`close` の後で `snapshot()` は呼ばれません。
- `pypdf` と `pypdfium2` の版は固定されていません。版が変わって描画が変わった場合は「元の描画と固定した画素が異なる」で止まる側に働くと見ていますが、試していません。

`✶ Insight ─────────────────────────────────────`
- 「想定した不足だけを許し、ほかは止める」という形は安全に見えます。しかし許可リストを例外の文で作ると、呼び出し先の深い層にある正当な不足まで「異常」に分類され、一度きりの段の可用性が壊れます。区別は、来歴と整合の検査という少数の明示した条件の側で引くほうが漏れにくいです。
- 事前確認の負の対照が通るのは、対象の行が下流の `reproduce` を通るほど素直な場合です。実際に `prove` へ回るのは先の経路で落ちた行なので、対照の選び方が本番の分布と逆向きに偏っていました。
`─────────────────────────────────────────────────`

このレビューに適したモデルとエフォートは Opus の high です。次の作業は、`source.py` で異常として止める条件を明示し、v47 の丸印16行を事前確認の回帰の試験に加える修正です。これにも Opus の high を勧めます。

使用した MCP サーバー: なし
使用した Agent Skills: なし

Final Result: REJECTED
