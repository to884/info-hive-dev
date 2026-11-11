# グラフの抽出が読む frontmatter の値を lint にそろえる（wiki 0.9.5）

2026-11-11。対象は `info-hive-wiki` の `skills/info-hive/scripts/wiki_graph_extract.py` と `wiki_graph_lint.py` である。Sol の設計レビュー（`docs/agent-runs/2026-11-11-wiki-graph-frontmatter-values/design-review-1.md`、条件付きで採用可）を受けて 2.2 から 2.6、3、4 を改め、実装のレビュー（同じディレクトリの `review-1.md`、却下。`review-2.md`、条件付きで採用可）を受けて 2.2、2.3、2.4、2.6、3、4 を改めた。

## 1. 不具合

wiki の lint、検索、統計、MCP は、frontmatter を `wiki_text.parse_frontmatter_text()`（文字列のパーサー。以下「lint の形」）で読む。値はすべて、書かれた文字のままの文字列か、その配列になる。グラフの抽出とグラフの lint だけは、frontmatter の全体を PyYAML で読む。PyYAML は、引用符のない `true`、`yes`、`no`、数、日付、`null` を、真偽値、数値、日付、`None` にする。同じ欄が 2 つの道具で違う値になる。

`a.md` が `type: "concept"` と `sources: [true]`、`true.md` が `type: "source"` のとき（0.9.3 で実測）:

| | `sources` の値 | 結果 |
| --- | --- | --- |
| wiki の lint | `["true"]` | `true.md` に解決する。`unresolved_sources` は空 |
| グラフの抽出 | `[True]` | `sourced_from` を作らない。診断 `unresolved_source`（`source: "True"`） |

`sources: [null]` は、lint では `"null"` という未解決の出典になり、グラフでは値が捨てられて診断も出ない。`type: yes` や `kind: 2024` は、lint では文字、グラフでは真偽値と数値になる。

PyYAML は、値を組み立てられないとき `yaml.YAMLError` ではなく `ValueError` を出すことがある（`created: 2026-13-01`、`!!int abc`）。0.9.3 はこれを捕まえないので、そのページが 1 つあると抽出とグラフの lint が止まる。lint の形は、同じ値を文字として読む（`non_iso_dates` が挙げる）。

閲覧（browse）の第 1 段階の設計（`feature/wiki-browse-stage1` の `docs/plans/wiki-browse-stage1-2026-11-09.md` の 2）は、「`graph` の欄だけを PyYAML から取り、ほかの最上位の欄は lint の形の値を使う」と決めた。`/wiki:graph` の出力とグラフの lint を、それと同じ形にする。

## 2. 決めたこと

### 2.1 最上位の欄は lint の形で読む

`wiki_graph_extract.read_frontmatter(text) -> (meta, body, 診断の一覧)` を足し、`parse_frontmatter(text) -> (meta, body)` はそれを包む（形は変えない）。

最上位の欄は `canonical_meta(parse_frontmatter_text(fm_text))` で作る。wiki の lint の `parse_frontmatter_raw()` と `canonical_meta()` が返す辞書と同じ関数、同じ値である。frontmatter を切り出す正規表現は、今も lint と同じ文字列である。

`graph` の欄だけを PyYAML から取る（2.3）。lint の形の `graph`（入れ子を読まないので `[]` になり、字下げ 2 つの `  - x` の行が紛れ込むこともある）は、必ず捨てる。PyYAML の `graph` がマッピングならそれを入れ、そうでなければ `graph` のキーを置かない。

そのあと、今までどおり `normalize_refs()` で参照の値（`sources`、`raw`、`graph` の参照の欄）を NFC にそろえる。lint の辞書と等しいのは、この正規化の前である。NFD で書いた `sources` の値は、lint では NFD のまま、グラフでは NFC になる（どちらも、リンクを解決するときに NFC にするので、当たるページは同じ）。

対象を `sources`、`raw`、`type`、`kind` に限らず、最上位の欄すべてにする理由は 2 つある。browse の設計と同じ辞書になること。欄ごとに出どころを変えると、次に足した欄でまた食い違うこと。ノードの `title`、`kind`、`tags`、`created`、`updated` も lint の形の値になる（`title: 2024` と `kind: 2024` は文字の `"2024"`、`created: 2024-1-1` は書かれたままの `"2024-1-1"`）。

lint の形の値を、lint と同じ読み方で使う。

- `raw:` は、lint の `missing_raw` と同じく `ref_values()` で読み、値 1 つにつき `summarizes_raw` を 1 本作る。今は配列を `raw:['a', 'b']` という 1 つの目的語にしている。値が 1 つのときのエッジは変わらない（`raw: " raw/a.md "` のように引用符の中の前後に空白があるときだけ、lint と同じく空白を除く）。
- `tags:` に文字列を 1 つ書いたとき（`tags: ml`）は、1 つのタグにする。今は 1 文字ずつに分けている（0.9.2 で `sources:` について直したものと同じ誤り）。配列で書いたタグは、今と同じ値のまま出す（前後の空白も空の要素も残し、NFKC にもしない）。

### 2.2 `graph:` の中の、ページやノードを指す欄は、書かれた文字で読む

`graph:` の中は lint が読まないので、そろえる相手の値はない。ただ、同じ種類の取り違えが起きる（0.9.3 で実測）。

| 書いた値 | PyYAML の値 | 今の結果 |
| --- | --- | --- |
| `source: 007`（ソースページ `007.md`） | `7` | `broken_source_refs`（`source: 7`） |
| `source: 1.10` | `1.1` | `broken_source_refs` |
| `source: true` | `True` | `broken_source_refs`。エッジの `source` は真偽値 |
| `object: no`、`node_id: no` | `False` | 関係を黙って捨てる。node_id は既定の ID になる |
| `aliases: [1.10, yes]` | `[1.1, True]` | 別名が `1.1` と `True` になる |

2.1 のあとは、最上位の `sources: [007]` が `007.md` に解決するのに、同じページを指す `graph.relationships[].source: 007` は解決しない。これも直す。

`normalize_refs()` が NFC にそろえている欄、つまりページやノードを指す欄を対象にする: `graph.node_id`、`graph.aliases`、`graph.relationships[]` の `object`、`source`、`contradicts`、`supersedes`。これらの欄で PyYAML が文字列でも `None` でもないスカラー（真偽値、数、日付、日時）に読んだ値を、書かれた文字に置き換える。

- 書かれた文字は、`graph` のノード（PyYAML が構文として読んだ木）から直接取る。スカラーのノードは、書かれた文字を値として持っている。もう一度構文を読むことも、木の全体を別の方法で組み立てることもしない。参照の欄のノードだけを見て、その中には入らないので、自分を含むアンカー（`graph: &g {node_id: 007, unused: *g}`）があっても読める。
- マッピングは文字列のキーで（同じキーが複数あれば、PyYAML が辞書を作るときと同じく後のもの）、配列は同じ長さのときだけ同じ番号で引く（`relationships` の同じ番号の項目の同じキー、`aliases` の同じ番号）。引けない値は、PyYAML の値のまま残す。マージキー（`<<`）で来た値とアンカーの値も、PyYAML が値に組み立てるときにノードのマージキーを展開しているので、同じキーで引けて、書かれた文字になる。
- 置き換えは、新しい辞書と配列を作って行う。アンカーで同じ配列を共有する別の欄（`aliases: &a [007]` と `notes: *a`）は変えない。
- 置き換える値があるページだけで行う。引用符で囲む規約どおりのページでは起きない。
- `None`（`null`、`~`、値なし）は「値なし」のまま残す。`supersedes: null` のように、ないことを書く使い方を壊さないためである。`"null"` と引用符で囲めば、文字として読む。最上位の `sources: [null]` は、lint が文字の `"null"` と読んで未解決と挙げるので、2.1 でグラフもそれに従う。`graph:` の中には従う相手がないので、YAML の意味を残す。
- 文字列の値は置き換えない。

対象にしない欄: `predicate`、`node_type`（オントロジーのキーと照らす。オントロジーのキーも PyYAML が読むので、両側が同じ型になる）、`canonical`（真偽値）、`confidence`、`status`、`evidence`、`valid_from`、`valid_to`、`notes`、`raw_ref`。

### 2.3 PyYAML が組み立てるのは `graph` のノードだけにし、読めなかったら診断に挙げる

PyYAML には frontmatter を構文として読ませ（`SafeLoader.get_single_node()`）、最上位のマッピングから `graph` のキーのノードを探し、そのノードだけを値に組み立てる（`construct_document()`）。最上位のマージキーは、PyYAML が読むときと同じに展開してから探す。同じキーが 2 つあれば、PyYAML と同じく後のものを使う。

- `graph` の外の値に左右されない。`created: 2026-13-01` があっても `graph` は読め、抽出は止まらない。展開できない最上位のマージキー（`<<: 3`）は、ないものとして扱い、`graph` は読む。
- 例外は、種類を問わず捕まえ、外に出さない。ローダーを作るところ（YAML に書けない NUL などの文字で `ReaderError`）、構文を読むところ、`graph` のノードを組み立てるところ（`valid_from: 2026-13-01`、`!!float nope`）のどれでも、止まらずに「読めなかった」とする。

今は、PyYAML が frontmatter を読めないと（`title: a: b`、タブ）、辞書が空になり、`type` も `graph` も黙って失う。2.1 のあとは、`type` や `sources` は lint の形で読めるのに、`graph` の関係だけを黙って失う。これを黙らせない。診断 `unreadable_graph` に挙げる。

- `reason: "not_mapping"`: `graph` の値が、値なし（`null`、`~`、空）でもマッピングでもない（`graph: x`、`graph: ""`、配列）。
- `reason: "yaml_error"`:
  - `graph` のノードを値に組み立てられない。
  - frontmatter を構文として読めない（YAML に書けない文字を含む）、または最上位がマッピングでなく、`graph` の欄がありそうなとき。構文を読めないので、文字で見る。lint の形に `graph` のキーがあるか、行頭が `graph:`、`"graph":`、`'graph':`（コロンの前の空白とタブを許す）の行があれば、ありそうとする。読める YAML なら `graph` として読むその他の書き方（`? graph`、1 行のフロー `{graph: ...}`）は、構文を読めないときには見つけられない。

`graph:` に値がないページと、`graph` のないページは、診断しない。

### 2.4 lint のパーサーが読めない書き方の欄を、診断に挙げる

lint のパーサーは、YAML のすべての書き方を読むわけではない。字下げのない `- x` の配列、字下げ 4 つの配列、複数行の `[a,` … `]`、引用符つきのキー（`"type": x`）、`type : x` は読まない。2.1 のあと、グラフもこれらを読まなくなる（3 の表）。今グラフだけが読めていた `sources:` から、`sourced_from` が黙って消える。

読まないことは受け入れる（3）。ただし黙らせない。グラフがエッジとノードの種類に使う最上位の欄（`type`、`kind`、`sources`、`raw`。日本語の別名を含む）について、YAML には値があるのに lint のパーサーが読めなかったものを、診断 `unread_field` に挙げる。PyYAML が構文として読んだ最上位のノードと、lint の形の辞書を比べる。

- その欄を書いた回数（最上位に自分で書いたキー）が、lint のパーサーがキーの行として読んだ回数（`wiki_text.top_level_keys()`）より多い。`"type": x` と `type : x` のほか、読めるキーと読めないキーで 2 度書いたもの（`type: "concept"` と `"type": "source"`。YAML では後の値が勝つ）も挙がる。値のある宣言が 1 つもなければ（`"sources":` だけ）、失うものがないので挙げない。
- 同じキーに書いた YAML の配列の要素の数より少ない数しか、lint のパーサーが読んでいない。数え方は lint のパーサーに合わせる。書かれたままのキーごとに数え（`sources` と `出典` は別。別名の衝突で片方を捨てるのは `canonical_meta()` で、読めなかったのではない）、同じキーの配列はつなぎ、あとに書いた文字列は配列を置き換える。
- 最上位のマージキーで来た値があるのに、lint の形にその欄がない。マージで来た既定値を、自分で書いた値が上書きしているときは、YAML の値も lint の値も書いた値なので、挙げない。

値の中身は比べない（真偽値や数の読み方の違いは、2.1 で lint にそろえたものである）。ブロックのスカラー（`raw: >`）のように、数は合うが値が違う書き方は挙がらない。frontmatter を構文として読めないページでは、比べられないので挙げない。

### 2.5 診断の形

`read_frontmatter()` が返す診断は、ページを付ける前の `{"kind": "unreadable_graph", "reason": ...}` と `{"kind": "unread_field", "field": ...}` である。`collect_pages()` がページの `fm_problems` に持たせ、`build_nodes()` が `{"kind", "page": <rel_path>, ...}` にして `diagnostics` に足す。グラフの lint は `unreadable_graph` と `unread_fields` に挙げ、`summary` に件数を入れる。抽出は、ほかの診断と同じく件数を標準エラーに書く。

### 2.6 オントロジーの `maps_from` も、書かれた文字で読む

ページの `type` と `kind` は文字になるので、それと照らす `node_types[*].maps_from` の `type` と `kind` も、書かれた文字にする。ページの規約は数値を引用符で囲まないので、`maps_from: {kind: 2024}` とページの `kind: 2024` は、今（数値どうし）も 0.9.5（文字どうし）も当たる必要がある。当たらなくなると、そのページのノード ID が変わり、それを指す別のページの参照が切れる。

`read_ontology()` は、`yaml.safe_load()` と同じ読み方（構文を読み、値に組み立てる）をしたうえで、2.2 と同じく、`node_types` の同じ名前の `maps_from` の `type` と `kind` のノードから書かれた文字を取り、PyYAML が文字列でも `None` でもないスカラーに読んだ値を置き換える。マージキーで来た `maps_from` の値（`maps_from: {<<: *base}`）とアンカーの値も、書かれた文字になる。オントロジーのほかの値（述語、`subject_types` など）は PyYAML の値のままにする。`read_ontology()` は、PyYAML の `ValueError` なども「オントロジーを読めない」として扱う（今は止まる）。

`maps_from` とページで書き方が違うとき（`2024` と `2024.0`、`yes` と `true`）は、当たらない。今は PyYAML が同じ値に読むので当たる。

### 2.7 版

利用者に見える修正なので、パッチの 0.9.5 にする。0.9.4 は開いている PR（to884/info-hive-wiki#38、`fix/graph-lint-edge-id-refs`）が使う。0.9.2 と同じく、修正のためのグラフの lint の検出結果の追加（`unreadable_graph`、`unread_fields`）を含む。3 の書き方をしている wiki では、グラフのノードとエッジが変わる。

## 3. 変わること（利用者から見て）

ページの規約（`references/page-conventions.md`）どおりに書き、下の 2 つも満たすページでは、書き出すノードとエッジ（`nodes.jsonl`、`edges.jsonl`、`graph.sqlite`、`graph.graphml`）は、ID を含めて変わらないはずである。確かめたのは、試験の中の規約どおりの 5 ページ（0.9.3 のスクリプトが作った出力と比べる。4 の 3）と、このリポジトリの `wiki/`（4 ページ）、作者のユーザースコープの wiki（39 ページ、エッジ 219 本）で、どれも 0.9.3 と同じノード、エッジ、グラフの lint の結果になり、新しい診断は 0 件だった。すべての書き方について証明したものではないので、下の表にない違いが見つかったら、表に足す。

- 規約どおりに、文字列の値を配列の要素も含めて二重引用符で囲み（エスケープは `\"` と `\\` だけ。日時も囲む）、配列を 1 行の `[...]` か字下げ 2 つの `  - ` の行で書いている。
- 2.1 で読み方を直した 2 つの書き方をしていない。ソースページの `raw:` は文字列 1 つで、前後に空白がない（配列は値ごとのエッジになり、前後の空白は除かれる）。`tags:` は配列で書いている（文字列 1 つのタグは、1 文字ずつでなく 1 つのタグになる）。
- 引用符のない数、真偽値、日付、`null` を、グラフが読む欄に書いていない。グラフが読む欄は、最上位の `type`、`kind`、`title`、`tags`、`sources`、`raw` と、`graph:` の参照の欄（2.2）である。`created` と `updated` の `YYYY-MM-DD` の日付は、今も書き出すときに同じ文字になるので、変わらない。

変わるのは、次の書き方のページである。

| 書き方 | 今（0.9.3） | 0.9.5 |
| --- | --- | --- |
| 最上位の `true`・`yes`・`no`・数・日付・`null`（引用符なし） | 真偽値、数値、日付、`None` | 書かれた文字。lint と同じ |
| `graph:` の参照の欄の真偽値・数・日付（引用符なし） | `str()` した値（`True`、`7`、`1.1`）か、捨てる | 書かれた文字 |
| 字下げのない `- x`、字下げ 4 つの `    - x` の配列 | 配列として読む | 読まない（空の配列）。lint と同じ。`unread_field` |
| 複数行にまたがる `[a,` … `]` | 配列として読む | 1 行目だけの文字列。lint と同じ。`unread_field` |
| 引用符つきのキー（`"type": x`）、`type : x` | 読む | 読まない。lint と同じ。`unread_field` |
| 同じキーを 2 度書いた配列 | 後のものだけ | 2 つをつなぐ。lint と同じ |
| `key:value`（コロンのあとに空白なし）、タブ、`title: a: b` | frontmatter 全体を失う | 最上位の欄は読む。`graph` は失い、`unreadable_graph` に挙げる |
| `>`、`|` のブロックのスカラー、`&`・`*`、`!!str` | YAML の意味で読む | 書かれた文字。lint と同じ |
| 二重引用符の中の、`\"` と `\\` のほかのエスケープ（`\t`、`\n`、`\u00e9`） | YAML の意味で読む（タブ、改行、`é`） | 書かれた文字のまま。lint と同じ |
| 引用符のない日時（`created: 2026-11-01 10:00:00`） | 日時にして `2026-11-01T10:00:00` と書き出す | 書かれた文字。lint と同じ |
| PyYAML が組み立てられない値（`created: 2026-13-01`） | 抽出とグラフの lint が止まる | 最上位は書かれた文字。`graph` の中なら `unreadable_graph` |

3 行目から 5 行目は、今グラフだけが読めている書き方を、読まなくなる後退である。受け入れる理由:

- その書き方のページは、今も lint、検索、統計、MCP、browse のメタ欄では値が空である。グラフだけが別の値を見ている状態が、この不具合そのものである。
- 規約にない書き方である。このリポジトリの `wiki/`、作者のユーザースコープの wiki、プラグインの試験データには 1 つもなかった（`^(sources|tags|raw|aliases):\s*$` で探した）。ほかの利用者の wiki にないとは言えないので、2.4 の診断で知らせる。
- 読めるようにするなら、`wiki_text` のパーサーを広げて、すべての道具で一度に読めるようにするのが筋である。検索、統計、lint が共有するパーサーなので、この修正では広げず、別の課題にする（5）。

エッジの行き先と ID が変わるのは、上の表の書き方のページだけである。たとえば `sources: [1.10]` は、今は `1.1.md`、0.9.5 では `1.10.md` を指す。`graph:` の参照の欄に `007`、`1.10`、`true` を書いていた関係と、`contradicts`・`supersedes` に引用符のない数を書いていた関係は、ID が変わる。

## 4. 試験

`tests/wiki/test_graph_frontmatter_values.py`（PyYAML 6.0.3）を足し、CI（`.github/workflows/wiki-mcp.yml`）に足す。

1. 再現: `sources: [true]` と `true.md` で、`sourced_from` ができ、診断がない。`sources: [null]` は、wiki の lint の `unresolved_sources` とグラフの診断 `unresolved_source` の両方が `null` を挙げる。CLI の抽出が `edges.jsonl` にそのエッジを書く。
2. 表の試験: 真偽値、`null`、数（`007`、`1.10`、`0x1F`、`1_000`、`12:30`）、日付、日時を `sources`・`raw`・`type`・`kind` に書き、日本語の別名でも、`extract.collect_pages()` の meta が、`wiki_lint.collect_pages()` の meta に `normalize_refs()` をかけたものと等しい（どちらも `graph` を除く）。3 の表の書き方、NFD の値、PyYAML が組み立てられない値、最上位のマージキーでも等しく、抽出とグラフの lint が止まらない。
3. 3 つの条件を満たすページ（この試験の中の 5 ページ。型付きの関係、別名、`sources`、`raw`、日本語の別名のキーを含む）で、ノード、エッジ、別名、診断、グラフの lint の結果と、CLI が書く `nodes.jsonl`・`edges.jsonl` が、0.9.3（c50854a）のスクリプトそのものが作った出力（`tests/wiki/graph_frontmatter_values_golden.json`）と等しい。プラグインの試験データ `eval/decisions/fixtures/graph_wiki` では、0.9.3 の読み方（`yaml.safe_load` → `canonical_meta` → `normalize_refs`）の meta から作ったものと等しい。
4. `graph:` の参照の欄: `source` に `007`、`1.10`、`true`、`no`、`0x1F`、`1_000`、日付、日時を書くと、書かれた文字になり、その名前のソースページに解決する。`object: no`、`node_id: no`、`aliases`、`contradicts`、`supersedes` も書かれた文字になる。`null` は値なしのまま。`canonical`、`valid_from`、`notes`、`raw_ref`、`evidence` は PyYAML の値のまま。マージキーとアンカーで来た値も書かれた文字になり、アンカーを共有する対象外の欄は変わらない。自分を含むアンカーがあっても、参照の欄は書かれた文字になる。変わった形（参照の欄が辞書や配列、同じキーの重複）で止まらない。NFD の参照は NFC になる。
5. `graph` の外の値に左右されない: `created: 2026-13-01` と `!!int abc` があっても、`graph` を読み、診断がない。`"graph":`、最上位のマージキーで来た `graph`、2 度書いた `graph` を読む。展開できない最上位のマージキー（`<<: 3`）があっても読む。
6. `unreadable_graph`: `title: a: b`、タブ、`type:concept` だけの形、YAML に書けない文字（NUL、DEL、U+0080）で `yaml_error`（止まらない。`graph` のないページは挙がらない）。`"graph":`・`'graph':`・`graph :` と読めない YAML でも挙がる。`graph` の中の `!!float nope`、`valid_from: 2026-13-01`、配列のキーで `yaml_error`（止まらない）。`graph: x`、配列、`""` で `not_mapping`。`graph:` が空のページ、`graph` のないページ、frontmatter のないページは挙がらない。CLI の lint の `--json` とテキスト、抽出の標準エラーに出る。
7. `unread_field`: 字下げのない配列、字下げ 4 つ、複数行、引用符つきのキー、`sources :`、日本語の別名、同じキーの 2 つ目だけ読めない、アンカーで挙がる。`type`・`kind`・`raw` でも挙がる。読めるキーと読めないキーで 2 度書いた欄（読めるほうが値なしでも）、マージキーだけで来た欄も挙がり、マージで来た既定値を書いた値が上書きしている欄は挙がらない。配列のあとに同じキーで文字列を書いた欄、英語のキーと日本語の別名の両方で書いた欄、値のある宣言がない欄は挙がらない。読める書き方（1 行の配列、字下げ 2 つ、文字列 1 つ、値なし、同じキー 2 度、入れ子の `[[...]]`、コメント、見ていない欄）は挙がらない。CLI に出る。
8. `raw:` の配列は値ごとに `summarizes_raw` を作る。`tags: ml` は 1 つのタグになり、配列で書いたタグは空白と空の要素を含めてそのまま残る。`title` と日付は文字になる。
9. オントロジーの `maps_from: {type: entity, kind: 2024}` と `{type: yes, kind: 007}` が、同じ書き方のページに当たり、そのノード ID を指す別のページの参照が切れない。マージキー（`{<<: *base}`）とアンカー（`maps_from: *m`、型の定義ごとの `*w`）で来た値でも当たる。`maps_from` のほかの値は PyYAML の値のまま。PyYAML が組み立てられない値のあるオントロジーは、読めないものとして終了コード 2 で止まる。

既存の試験も通す: `tests/wiki/`（グラフ、lint、ページの集合、索引、MCP）、`tests/graph/`、プラグインの `eval/scripts/`、`eval/decisions/`（`graph_lint_golden.json` は検出結果のキーが増えるので取り直す）、`skills/info-hive/scripts/test_link_resolution.py`。

## 5. 範囲外

- `wiki_text` のパーサーが読まない YAML の書き方（字下げのない `- ` の配列、複数行の `[...]`、ブロックのスカラー、引用符つきのキー）を読めるようにすること。lint、検索、統計、グラフ、browse が同じパーサーを使うので、広げればすべてが同じに変わる。
- `object` のない関係の項目（`predicate` だけ）を、抽出もグラフの lint も黙って飛ばすこと。
- `graph.relationships` が配列でない（`relationships: 7`）と抽出が、`predicate` が辞書だとグラフの lint が、`TypeError` で止まること（0.9.3 からある）。
- ノードの `tags` を NFKC にそろえること（lint と検索は NFKC にして比べる）。
- オントロジーの `maps_from` の `type`・`kind` に、日本語の別名（`ソース`、`人物`）を書けるようにすること。
