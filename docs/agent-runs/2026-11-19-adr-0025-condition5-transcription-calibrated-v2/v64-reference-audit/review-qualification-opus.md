## レビュー結果

依頼の4点を、実際の呼び出し経路と母集団のデータで確かめました。表示の経路、24枚の上限、v70 の正解変更の根拠は問題ありませんでした。Major が1件あり、正式抽出の前に直す必要があります。

**検証の方法**
- 外部の一時スクリプトで `python -B` を使い、`launch` を読み込んで調べました。依存パッケージは uv の一時環境に入れました。
- リポジトリ内のファイルは書き換えていません。
- `preflight.py` は実行していません。コーパスの中に一時ディレクトリを作るため、読み取り専用の範囲を超えるからです。

---

### [Major] 正式の入口のハッシュ固定から、本番で実行するモジュールが外れている（v47 から後退）

**対象**
- `v64-reference-audit/launch.py:27`（`primitives = core.inputs`）
- `launch.py:31-45`（`dependencies()`）、`:79-91`（`check_preflight`、`inputs`）

**根拠**
- `launch` を読み込んだ時点の `core.inputs` は、v27 の `inputs` のままです。v47 の `run.inputs` と `audit.inputs` は `main` の中でしか差し替わらないからです。
- v47 の `official.verify_preflight()` は、`preflight-final.json` に記録した全入力を毎回ハッシュし直していました。v64 はこのファイル自体のハッシュしか固定せず、記録された入力を検査し直しません。
- 読み込み時に `spec_from_file_location` と `sys.modules` を記録して数えました。読み込まれるローカルの `.py` は 116 個で、そのうち 35 個が `primitives(...) ∪ dependencies()` にありません。
- 外れているもののうち、次の5つは v47 では固定と再検査の対象でした。
  - `v44-small-point-pixel-pilot/run.py`：`strict_points` の `confirm` の本体です。v61 の `prove` も `strict.implementation.glyphs` を通してこのファイルを使います。
  - `v40-frame-edge-pilot/prepare.py`、`v43-frame-rectangle-pilot/prepare.py`：枠端の画像（`edge_stage.earlier.supplement`）と説明（`GUIDE`）を作ります。
  - `v41-paragraph-bullets-pilot/prepare.py`：`paragraph-margin` の画像と説明を作ります。
  - `v24-physical-transcription-pilot/run.py`
- 次のものも固定されていません。こちらは v47 でも固定されていませんでした。
  - `actual-geometry-pilot-v2/run.py`：`segments` を定義しており、主画像・座標画像の枚数と `capacity` の計算を決めます。
  - `v27-reference-audit/diagnose.py`（`diagnose` で使う）

**問題**
- 事前検査や母集団の固定の後に、上の v44 や v40 を書き換えたとします。それでも `check_preflight()` と `core.verify_methods()` は通ります。
- その結果、正式の出典の確定、枠端の表示、添付の枚数が、検査とレビューを受けたコードと違うまま本番で動きます。
- 依頼の「後から変えた方法を検出する」を満たしません。

**検証方法**
1. `importlib.util.spec_from_file_location` に記録用のフックを付けてから `launch` を読み込む。
2. 読み込まれたファイルの集合と、`launch.primitives(launch.trial_method(), launch.CANDIDATE/"result.json", launch.candidate())` と `launch.dependencies()` のキーの和との差を取る。
3. v44 などが差に残ることを確かめる。

**修正の方向性**
- `previous.module` や読み込みのフックで、実際に読み込んだ全ファイルを集め、`dependencies()` に入れる。`diagnose` や出典の経路のように後から読み込むものも含める。
- 事前検査で「読み込んだファイル ⊆ 固定したファイル」を必須の条件にする。
- 少なくとも v47 の `official.dependencies()` と、`preflight-final.json` に記録された入力の再ハッシュを引き継ぐ。

---

### [Minor] 出典の経路で異常と証拠不足が同じ「確定しない」になり、その記録が判定に結び付かない

**対象**
- `v64-reference-audit/source.py:63`、`:87-92`、`:115-116`
- `preflight.py:284-287`

**根拠**
- `UNPROVEN_SOURCE` は `TypeError`、`AttributeError`、`KeyError` まで捕まえて `None` を返します。v61 の中にある次のような異常も同じ扱いです。
  - 「登録済みの中黒のCIDと符号が異なる」
  - 「縦組の中黒をAdobe-Japan1の字として確認できない」
- `unsupported-point-sources.json` は、`reader.finish()` が `result.json` を書いた後に保存されます。`result.json` にはこのファイルのハッシュがありません。
- v44 の経路（`confirm` の中で例外を捕まえる）と v27 の `fallback` の中の例外は、どこにも記録されません。
- 事前検査の負の対照（防衛白書88行目）は `notes` を渡していません。例外で `None` になっても「large-bullet rejected」として合格します。

**問題**
- たとえば pypdf の API が変わって `prove` が `AttributeError` を出すと、縦組の小点はすべて参照不足になります。その結果、監査は一度きりなのに「inconclusive」で終わります。
- 誤って合格する方向には働きません。ただし、この負の対照は拒否の理由を確かめていません。

**修正の方向性**
- 想定した証拠不足（点を一つに絞れない、命令が一意でない）とそれ以外を分ける。それ以外は止めるか、別の状態として `result.json` に結び付ける。
- 負の対照では、拒否の理由が想定したものであることを確かめる。

---

### [Minor] 開発の票をきっかけに正解を変えた行が、正式抽出の対象に残る

**対象**
- `v70-reference-candidate/score.py`
- `audit_selection_v9.py` の `draw`、`summarize`

**根拠**
- v70 で変えた `kanpo1826-p3-p0001/8` は、画像補充の evaluation3・FN 層（67 行）に入りました。15 行の抽出に入る確率は 22.4% です。
- 以前の訂正行 `kanpo1828-p3-p0001/201` は tuning・FN 層（17 行）にあり、抽出される確率は 88.2% です。
- `draw` は `development_intake` を除きません。`summarize` も、この印の付いた行を不一致0の判定に含めます。

**問題**
- 正解の変更そのものは妥当です。150 DPI では枠内が 0% で、450 DPI では 36〜43% でした。これは v45 と同じ小数の枠端と「割当軸の半分以上」の規則で測った値です。
- ただし、抽出された場合は、同じ2モデルの4票に合わせて変えた正解に新しい2票が一致する形になります。独立な一致とは言えない行が「一致」に数えられます。
- 重なりを記録する既存の設計の範囲内なので、Minor としました。

**修正の方向性**
- 抽出の前に、「開発の票で正解を変えた行を除いた集計」を併記するか、そうした行を判定に数えない規則を固定する。

---

### [Minor] 字体の例を除く検査が、最終の指示文を見ていない／120行目を本番の関数で再現していない

**対象**
- `neutral.py:167`
- `launch.py:103-143`
- `preflight.py:308-311`

**根拠**
- `REMOVED` の検査は `display` の戻り値だけを見ます。そのため、後から足される `plan["guides"]` と `EDGE_NOTE` は検査されません。
  - v67 で実際に配った指示文の「」は「●」「➢」「。」だけで、いま漏れはありません。
- 120行目の確認は、v69 の `source-result.json` を読むだけです。
  - v69 は v61 の `prove` を直接呼んでいます。`mark_from_source` の来歴の検査と経路の順は、120行目では通っていません。
  - 照合も `line_index == 120` だけで、頁は見ていません。

**修正の方向性**
- 束を作った後の指示文で `REMOVED` を検査する。
- `marks()` に 120行目を正の対照として加え、`mark_from_source` で再現する。

---

### 確かめて問題がなかった点

- **表示の経路**：事前検査と本番は、同じ `launch.package()`、`neutral.active`、`render.active`、`audit.fit` を通ります。方法は同じ `trial_method()` の結果を `method.json` に保存したものです。
- **24枚の上限**：v70 の全母集団（8,853 行）で `capacity` を実行しました。
  - 必須画像の最大は 30 枚で、6組の座標を結合すれば 24 枚に収まります。
  - 事前検査で使う極端な行 `wp-summary-p0007/2`（1726×34）が、母集団の最大そのものです。
- **v67 の実際の束**：`close` の画像名はゼロ埋めで、`sorted` の両端が正しく行の両端になります。必須の分類も `capacity` の上界の内側でした。
- **開発行の除外**：v22〜v69 の選定表の行は、すべて `direct_intake` に入っていました。
- **記録との一致**：v69 と v70 が記録した入力のハッシュは、いまのファイルと一致しました。
- **本番の経路**：v47 の正式記録で、117行目は `source-location-not-proven` から `fallback` に到達していました。

### 未確認事項

- `preflight.py` は実行していないので、`packets()` と `marks()` が実際に通るかは見ていません。
- 読み込みの列挙は `launch` を読み込んだ時点の分だけです。`source` と `diagnose` で後から読み込むファイルも、さらに固定から外れている可能性があります。

`✶ Insight ─────────────────────────────────────`
- 関数を差し替えて段を重ねる作りでは、どこかの入口の固定が下流の固定をまとめて再検査しないと、古い段のコードが固定から外れていきます。今回の v44 や v40 がその例です。
- 異常を捕まえて「確定しない」にすると、誤って合格する側には倒れません。その代わり、一度きりの監査を「判定できない」で使い切る危険があります。
`─────────────────────────────────────────────────`

このレビューに適したモデルとエフォートは Opus の high です。次の作業（実際に読み込むファイルをすべて固定に入れ、例外を分ける修正）は Opus の medium〜high を勧めます。

使用した MCP サーバー: なし
使用した Agent Skills: なし

Final Result: REJECTED
