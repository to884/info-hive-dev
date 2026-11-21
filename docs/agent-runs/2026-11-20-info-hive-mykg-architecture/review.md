## レビュー結果

publication の前提条件が誤って伝わる箇所が Major で1件あり、判定は REJECTED です。ほかに Minor が3件あります。

**前提と範囲**
- 対象の目的は、依頼元の説明どおりと仮定しました。
- 対象の HTML と JSON は、レビュー中の 2026-11-20 09:16:36 に別の作業で更新されました。判定と行番号は更新後の版に基づきます。
- 更新で、SVG のラベル位置、「索引」から「目次」への言い換え、28行の文言が変わっています。
- JSON の 38 件の SHA-256 は、更新の前後とも固定ソースと一致しました。固定ソースは、wiki が 84d149f（タグ v0.39.0）、rag が 9af30c3（タグ v0.5.4）の `git show` と同じ内容です。

### [Major] 公開版の前提条件が欠け、Ossie を「あれば使う」任意の連携に見せている

対象
- 20行: 「公開版は任意。初回公開の計画・承認が必要で…」
- 24行の SVG: 「ontology.yaml（任意）」
- 48行の比較表: 「Ossie 連携は準備済み成果物の記事履歴を更新する」
- 51行の対応表: 「準備済みの Ossie 成果物があれば記事の版を追記する」
- 56行: 「機能は v0.39.0 にある」

根拠
- 公開版は、どの版でもマニフェストが `REQUIRED` のファイルをすべて含む必要があり、欠けると `PublicationError` になります（`wiki_apply.py:39-44` と `84-87`）。
  - `graph/ontology.yaml`、`graph/graph.sqlite`、`ontology/definition.json`
  - `ontology/ossie/` の 6 ファイル（`wiki.ontology.json`、`wiki.semantic_model.json`、`wiki.mapping.json`、`wiki-data.sqlite`、`records.jsonl`、`release.json`）
- 公開保存で記事が変わると、必ず `article_rows` が呼ばれます（`wiki_public_projection.py:119-145`）。そこから呼ばれる `article_documents` は、`sem_articles` と `WikiArticle` の定義がなければ `Conflict("公開版に記事履歴を保存できる Ossie の定義がありません")` を返します（同 `25-42`）。条件付きの「あれば」ではありません。
- 初回の計画を作る `build_plan` と `capture_live_base` の呼び出し元は2系統だけです。
  - プラグイン内: 2回目以降の保存を担う `wiki_public_save.py:301`
  - 親リポジトリの PoC: `poc/ossie/publication_trial.py:170-172` と `poc/ossie/rollout_trial.py:338-339`
- v0.39.0 の `commands/`、`references/`、`SKILL.md` には、初回公開の手順も、Ossie の成果物を作る手順もありません（`git grep` で確認）。CLI の `apply` は、利用者が用意した `--source` と `--plan` を受け取るだけです。
- CHANGELOG 0.39.0 は、この機能を「公開版を隔離環境で検証するための適用…」と書いています。
- 公開版では、原本の根を wiki の外に独立して用意する必要があります（`write-workflow.md:5`）。

問題
- 初心者は「プラグインを入れ、初回の計画を承認すれば公開版を使える」と読みます。実際には、プラグインが配らないものを外で用意しないと公開版は作れません。
  - Ossie の意味モデル、マッピング、SQLite
  - `ontology/definition.json` と `graph/ontology.yaml`
  - wiki の外の raw の根
- 公開版を使っている wiki で Ossie の定義が欠けると、記事を変える保存はすべて衝突で止まります。
- 「ontology.yaml（任意）」はライブにしか当てはまりません。公開版では必須なので、図だけを見ると逆の結論になります。
- 観点 1 の「任意・初回承認が必要」と観点 3 の「限定した連携」は、表現としては合っています。しかし、どちらも成立条件が抜けていて、構成上の分担を誤解させます。

検証方法
1. 固定ソースで `wiki_apply.py:39-44, 84-87, 344-352` と `wiki_public_projection.py:25-42, 119-145` を読む。
2. `git -C info-hive-wiki grep -n "build_plan\|capture_live_base" 84d149ff` を実行する。呼び出し元は `wiki_apply.py` と `wiki_public_save.py` だけである。
3. `git grep -n "build_plan" HEAD -- poc` を実行する。PoC からの呼び出しが見つかる。

修正の方向性
- 20行か 56行に、公開版の前提を1文で書く。
  - 「`ontology.yaml`、`definition.json`、Ossie の成果物、wiki の外の raw の根が必須」
  - 「初回の候補と計画は、v0.39.0 では開発リポジトリの PoC の手順で作る」
- 51行と 48行の「あれば」をやめる。「公開版では必須。記事が変わるたびに `sem_articles` に行を足す」と書き直す。
- 24行の「（任意）」を「（ライブでは任意、公開版では必須）」にする。

### [Minor] 読み取りモードが、読み手が都度選ぶものに見える（実際は wiki 全体の状態）

対象
- 33行の切替ボタン: 「ライブ（既定）」
- 69行の `modes.publication`: 「公開版を選ぶ」
- 66行: 「ライブと公開版を選ぶ。」
- 27行の SVG: 「通常の保存」→ライブ、「有効化した場合」→公開版

根拠
- `resolve_publication(wiki, None)` は、公開版がある wiki では有効な版を返します（`wiki_apply.py:203-227`）。印が `live` になった切り戻し後だけ `None` を返します。
- そのため、公開版を使う wiki では、MCP の次のツールが既定で公開版を読みます（`wiki_mcp_server.py:368-374, 387-389, 475-481`）。
  - `query`: 語彙検索だけで、埋め込みを使いません
  - `get_page`、`list_index`、`lint`、`stats`
- `wiki_public_save.py:1` は「公開版を使う wiki に、承認済みの記事・索引・ログを保存する」です。57行の出典リンクも「通常保存から公開候補を作る処理」と書いています。これは 27行の「通常の保存→ライブ」と食い違います。

問題
- 公開版を有効にした後も、問い合わせごとにハイブリッド検索を選べると誤解させます。
- 有効化すると、その wiki の通常保存（ingest、query、learn）がすべて公開版に向かうことも伝わりません。

検証方法
- 上記の行を読み、`release_id=None` のときの分岐を追う。

修正の方向性
- 切替ボタンを「公開版なし（既定）」と「公開版を使う wiki」にする。
- 「有効化すると、その wiki の保存と MCP の読み取りはすべて公開版になり、検索は語彙検索だけ。ライブに戻すには `return-live` を使う」と1文を足す。
- 27行の分岐ラベルを「公開版なし」と「公開版あり」にする。

### [Minor] 途中の更新で「目次」と「索引」の表記が混在している

対象
- 新しい表記: 26行と 27行の SVG と 30行・63行の説明文は「ページ・目次・ログ」「記事・目次・ログ」
- 古い表記のまま: 29行のモバイル版は「現在の Markdown・索引・ログを更新する」、23行の `desc` は「ページ、索引、ログ」

根拠
- 30行の caption は、「目次は index.md などで、検索用キャッシュとは別」と定義しています。一方、32行の「索引で候補を探し」は検索用の索引の意味で使っています。

問題
- 同じ `index.md` が、デスクトップでは「目次」、モバイル版とスクリーンリーダーでは「索引」になります。
- 初心者は、検索索引と `index.md` を区別できなくなります。

検証方法
- 対象の HTML で `索引` を grep する。

修正の方向性
- `index.md` を指す箇所は「目次」に統一する。23行と 29行も直す。

### [Minor] 出典の JSON が、一部の主張を支えるファイルを記録していない

対象
- `info-hive-mykg-architecture-sources-2026-11-20.json` の `files`（38 件）

根拠
次の主張について、裏づけとなるファイルが記録にありません。

| 主張 | 行 | 記録にないファイル |
|---|---|---|
| 被リンクのないページを点検する通常の lint | 35・55 | `wiki_lint.py:443, 591, 819` |
| 公開版の語彙検索の本体と CLI の代替検索 | 33 | `wiki_search.py` |
| Pele の SVG 出力 | 34 | `wiki_browse_pele.py` |
| D2 は失敗しても続く | 56 | `wiki_decide.py` |
| myKG の各主張 | 43-48 | myKG 側のファイル（`raw/mykg-source-afb0a9c9/manifest.json` があるのに参照していない） |

問題
- 主張は照合すると正しいものの、記録からは再確認できません。
- 57行の「参照コミット・ファイル・SHA-256 の記録」の再現性が不完全です。

修正の方向性
- 上記のファイルの SHA-256 を足すか、myKG の manifest へのパスを記録する。

### 照合して正しかった項目

次の主張は、固定ソースまたはブラウザーでの確認と一致しました。
- MCP のライブ検索は BM25 と埋め込みを RRF で組み合わせ、Tantivy と usearch を使う。stdio の中継が 127.0.0.1 のサーバーにつなぐ。
- 公開版の `query` は `mode: "lexical"` を返す。`release_id` は `get_page`、`graph`、`browse` で版をそろえる。
- `update_projections` は、公開候補の中でグラフを検査してから再生成する。
- `orphan_typed_nodes` と通常の lint の `orphans`（被リンクなし）は別の検査である。D2 は `--decide` を付けたときだけ動く。
- RAG は `SentenceTransformer` と `lancedb` を使い、`index_chunks` を呼んでいない。CHANGELOG 0.5.4 の OCR キャッシュの記述とも一致する。
- myKG の 12 工程、7 アダプター、Pass 1 の標本抽出、`DiGraph`、BM25、BFS/DFS は設計文書と一致する。
- 前の版（wiki 0.30.0 / rag 0.5.3）の記述は、11-18 の HTML と一致する。
- 相対リンク 7 件はすべて実在する。
- 操作は、1280px、1120px、800px、390px で試した。
  - 層の切替、モバイルの `is-muted`、読み取りモードと `aria-pressed`、導入案の3枚の切替、配色の切替と `aria-label` が動く。
  - 横方向のはみ出しはない。
  - コンソールのエラーは favicon の 404 だけ。
- 図の文字と配線の重なりを `getBBox` で数値判定したところ、重なりはなかった。「同じ計画」は縦線から 0.15px 離れている。

### 未確認事項
- myKG の ls-remote（57行）は再実行していません。
- 「myKG v0.4.10」は、raw のスナップショット内では確かめられませんでした。

### 作業の後始末
- 一時的に起動した HTTP サーバーは停止し、作成した `.playwright-mcp/` は削除しました。
- リポジトリのファイルは変更していません。

`✶ Insight ─────────────────────────────────────`
- この実装では、公開版は読み方の選択肢ではなく、wiki 全体の状態です。`resolve_publication(wiki, None)` が、印のファイルと `current` から既定の版を決めます。図解では「経路」より「状態の遷移」として描くほうが実装に近くなります。
- `REQUIRED` の集合は、マニフェストごとに毎回検査されます。そのため Ossie の成果物は、任意の連携ではなく公開版の前提です。「連携が限定的」（意味主張を自動で作らない）と「連携が任意」（なくても動く）は別の性質です。
`─────────────────────────────────────────────────`

Final Result: REJECTED

使用した MCP サーバー: playwright（plugin_playwright）
使用した Agent Skills: なし

このレビューに合うモデルとエフォートは Opus の medium です。次の作業として、HTML の文言と図のラベルを直すなら Sonnet の medium が適しています。直した後の再レビューは Opus の medium で行ってください。
