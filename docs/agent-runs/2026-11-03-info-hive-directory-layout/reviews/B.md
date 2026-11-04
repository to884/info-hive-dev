## エージェント A のレビュー

### 長所
- **現行コードの読み込みが 4 案の中で最も深い。** `wiki_evolve_loop.py` L419 が raw の既定を `args.wiki.parent / 'raw'` と決め打ちしている点、`wiki_graph_extract.py` L402〜407 が `raw:` の値を文字列のまま `raw:<パス>` のノード ID にする点、`91_Raw/experiences/` が必要な点は、他の 3 案（私を含む）が見落とした。`91_Raw` を兄弟に置くと `/wiki:learn` が `~/info-hive/raw/` を勝手に作りうる、という具体的な破綻を示せている。
- **設定ファイルを JSON にした根拠が正しい。** wiki は Python 3.10 以上を前提にし（`retrieval-setup.md` L16）、lint・stats・グラフのクエリは標準ライブラリだけで書く方針（`CONTRIBUTING.md` L34）。`tomllib` は 3.11 から、YAML は PyYAML が要る。私の YAML 案より筋が通る。
- **5 つの規則（表示名と識別子の分離、`90`/`91` は改名しない、4 つのルートを一致させる、ファイル名に完全な日付、境界を wiki の外に引く）が簡潔で、作者が判断しやすい。**
- svg を `90_Wiki/assets/` に残し、作者の決定 2 を「取り込んだ画像」と読んだうえで U-2 として明示している。ADR-0004 の raw 不変性と ADR-0005 の browse の設計に整合する。
- `daily` のキーの有無で「既定はグローバル」を表す案は、プラグインごとの分岐がなく、私の案と同じ結論に独立に至っている。

### 短所
- **プロジェクトでは Foam のルートがプロジェクトルートになり、コードのサブモジュールが Foam の索引に入る。** `.info-hive/`、`.foam/`、`.vscode/` を `<project-root>` に置き、番号付きディレクトリを `<project-id>/` の下に置いているため、Foam は `repos/` 以下の `README.md` なども索引化する。除外設定で防ぐとしているが、サブモジュールを足すたびに設定の保守が要る。C と D と私は `<project-id>/` を Foam のルートにしており、そちらのほうが構造で防げる。
- **テンプレートの `filepath` の例が自分の対応表と食い違う。** 対応表ではプロジェクトの `daily` を `myapp/20_Daily` と書くとしながら、`filepath` の例は `20_Daily/$FOAM_DATE_YEAR/...` のまま。プロジェクトでは `myapp/20_Daily/...` にしないと Foam がプロジェクトルート直下に `20_Daily/` を作る。
- **「日付ノートへのリンクはファイル名だけで解決するので、フォルダーを変えても切れない」は Foam のリンクには当てはまるが、`$FOAM_PREVIOUS_DAILY_NOTE` には当てはまらない。** daily-notes.md は「Notes written before a path change are not found」としている。D はこの点を正しく指摘している。
- `00_Inbox` の資料を `/wiki:ingest` が `91_Raw` に「移す」としているが、`ingest-workflow.md` L11 は「raw にない場合はそこに置く」としか言っておらず、移動の挙動は現行にない。U-10 で未決にはしているが、表の本文では既定の挙動のように読める。
- `repos/` という階層は作者の決定 3 にない追加で、根拠は名前の衝突回避だけ。作者のツリーに `80_Code` のような番号もないので、要確認事項として扱うべきだった。
- 行番号の小さなずれ：`wiki_stats.py` の除外は L56（A は L55）、`SCHEMA.md.template` の `raw_ref` は L134（A は L132）。結論には影響しない。

### 検証した事実
| 主張 | 結果 |
| --- | --- |
| `wiki_evolve_loop.py` L419 `args.wiki.parent / 'raw'`、L699 のヘルプ「wiki と同じ階層の raw」 | 一致 |
| `wiki_graph_extract.py` L91 の除外に `raw`、L402〜407 で `obj=f"raw:{raw_path}"` | 一致 |
| `init_wiki.py` L263〜264 の `--wiki-dir`／`--raw-dir`、raw/assets の作成 | 一致（assets は L200） |
| `copy_template` に SCHEMA の置換を渡していない | 一致（`template_map` の呼び出しに `substitutions` なし） |
| 要件定義書 D-06 の `project-id` が `[a-z0-9]+(?:-[a-z0-9]+)*` | 一致（L138） |
| Python 3.10 以上、lint・stats は標準ライブラリだけ | 一致（`retrieval-setup.md` L16、`CONTRIBUTING.md` L34。`wiki_lint.py` に yaml の import はない） |
| `91_Raw/experiences/` | 一致（`SCHEMA.md.template` L191「設定した raw ルートの `experiences/`」） |
| 2026 年は ISO 週が 53 週 | 一致（私の計算と同じ） |

## エージェント C のレビュー

### 長所
- **Foam の除外設定を正確に押さえている。** `foam.files.ignore` は非推奨で `foam.files.exclude` が現行、という指摘は package.json（0.47.0）で確認できた。A、D、私はいずれも非推奨のキーを書いていた。
- **`.github/instructions` を外側のリポジトリに置く判断が正しい。** GitHub や Copilot はリポジトリの根の `.github/` を読むので、`<project-id>/.github/` に置いても効かない。私は「効かない可能性」を未確認事項に残しただけで、C は構成で解決している。
- **外側のプロジェクトルートに案内だけの `project.json` を置き、内側の `workspace.json` を正本にする 2 段構えは、サブモジュール内から起動したときの探索を単純にする。** 私の「1 段下を走査する」案より、複数候補の曖昧さがない。
- **ADR-0005 の `![説明](assets/<slug>-NN.svg)` が、`90_Wiki/concepts/` のページからは `concepts/assets/` に解決されてしまう**という指摘は、ADR-0005 自体の不備で、構成とは独立に直す必要がある。D も同じ指摘をしている。
- タイムゾーン、同時編集、`workspace_id`（改名しても変えない ID）、未知の設定項目の保持、といった運用上のリスクを挙げている。私は同時編集とタイムゾーンを落としていた。
- `[[concepts/名前]]` で同名を区別できるという Foam の挙動は、wikilinks.md で確認できた。

### 短所
- **生成 svg を `91_Raw/assets/figures/` に置く判断は、承認済みの 2 つの ADR に反し、根拠が弱い。** ADR-0004 は raw を「取り込み後に変えない」とし、ADR-0005 は svg を `wiki/assets/` に置くと決めている。どちらも作者が 2026年11月3日に承認している。「最新指示を優先」としているが、作者の決定 2 と ADR-0005 は同じ日のもので、どちらが後かは示されていない。さらに C 自身が「raw 全体を一律に不変と扱わない」と raw の意味を変えており、版番号 `-v001` という新しい命名まで足している。作者の一言の解釈のために、承認済みの 2 つの決定と raw の定義を変えるのは費用が大きい。A と私のように「取り込んだ画像」と読み、未決として確認を求めるほうが安全である。
- **`50_Knowledge/notes/` の 2 段構成は作者のツリーにない。** 作者は `50_Knowledge` を直下に置いている。`notes/` を残す意図は ADR-0006 との連続性だろうが、`50_Knowledge` の直下に他に何を置くのかが示されていない。
- `00_Inbox` と `50_Knowledge` の命名を `YYYYMMDD-HHMMSS-件名.md` にしているが、秒まで含む名前は人が書くには重く、ADR-0006 が最も重く見る「入力の軽さ」と合わない。wiki のスラッグ規則（`page-conventions.md` L83〜89）とも別の体系になる。
- `--project` を付けないと常にグローバルに書く設計は、作者の「既定はグローバル」を忠実に守る一方で、プロジェクトの作業領域にいても毎回フラグが要る。設定で切り替えられる A・D・私の案と比べて、入力の負担が増える。
- 「Foam の索引除外は `foam.files.exclude`」の根拠に package.json の行番号 L742 を挙げているが、行番号は版で変わるので、設定名だけを根拠にしたほうがよい。
- 週次を ISO 週にしているが、ISO 週年のディレクトリにする点は A と同じで、暦年と混ぜない注意書きがあるのはよい。

### 検証した事実
| 主張 | 結果 |
| --- | --- |
| `foam.files.ignore` は非推奨、`foam.files.exclude` が現行 | 一致（package.json 0.47.0 に `deprecationMessage` あり。`exclude` の既定は 22 個の glob） |
| Foam は `[[folder/filename]]` の識別子リンクで同名を区別できる | 一致（wikilinks.md「Identifier links」「Foam picks the shortest unambiguous form」） |
| `wiki_lint.py` L243〜256 に NFC の重複検出 | 一致（`normalization_collision` のフラグ） |
| ADR-0005 の参照 `assets/<slug>-NN.svg` がページ相対では解決しない | 一致（ADR-0005 L27 の書き方。ページは `wiki/concepts/` などに置かれる） |
| `SCHEMA.md.template` L64 に source ページの `raw` | 一致 |
| 作者の決定 2 が ADR-0005 より後 | 確かめられず（両方とも 2026年11月3日） |

## エージェント D のレビュー

### 長所
- **`index.md` からのリンクは被リンクに数えられない、という指摘が正確。** `wiki_lint.py` は `index.md` を `SKIP_TOP_LEVEL_FILES`（L107）で走査から外し、被リンクは走査したページの本文からだけ集める（L247〜）。日付ノートをインデックスに並べても孤立は消えない、という帰結も正しい。
- **`$FOAM_PREVIOUS_DAILY_NOTE` がテンプレートのパスの型に依存するため、古い年を `A0_Archive` に動かすと繰り越し元が見つからなくなる**、という破綻を具体的に挙げている。A と私は「古い年の daily は動かしてよい」寄りで、D のほうが慎重で正しい。
- **「一意性の単位を作業領域 ID と日付にする」**という整理で、グローバルとプロジェクトに同じ `2026-11-03.md` があることを明示的に許している。私は Foam のフォルダー名の違いで済ませていたが、`log` の集計を考えるとこの定義が要る。
- 外側 `P/.info-hive.json` に `log_scope` を持たせる案は、「ローカルの wiki があるだけで log の既定を変えない」という作者の決定を守りつつ、プロジェクトごとに切り替えられる。C の毎回 `--project` より軽い。
- `graph/` 全体を Git から除外して `ontology.yaml` まで失わないよう注意している点は、既存の `graph_gitignore.template`（`graph.sqlite` と `graph.graphml` だけ無視）と合っている。
- 日付の切り替え時刻、深夜をまたぐ作業、休業日を挟む繰り越しなど、`log` の実装で必ず決める事項を未決として列挙している。

### 短所
- **生成 svg を `91_Raw/assets/generated/` に置く判断は C と同じ問題を持つ。** ADR-0004 と ADR-0005 に反し、D 自身が「Raw 全体を一律に不変と扱わない」と raw の定義を変えている。さらに `imported/<資料ID>/<内容ハッシュ>.<拡張子>` という命名は、ADR-0004 が決めた「出現順の連番、元の URL は title 属性」と異なる。承認済みの ADR を、今回の課題（ディレクトリ構成）に必要のない範囲まで変えている。
- **`80_Code/` を外側 `P` に番号付きで置くのは、番号の体系を 2 つの階層に分散させる。** D 自身が「適用範囲を W 直下の利用者向け分類に限定する」と書いており、`80_Code` はその規則に反する。作者の決定 3 は「サブモジュールとして配置する」とだけ言っており、専用の番号ディレクトリは作者の指示にない。
- **週次を「週の月曜日の日付」で名付ける案は、Foam の `FOAM_DATE_WEEK`／`FOAM_DATE_WEEK_YEAR` を使えなくする。** ISO 週の混乱を避ける意図は分かるが、ディレクトリを `YYYY/` の暦年にしているので、2026-12-28 の週は `2026/` に入り、2027-01-04 の週は `2027/` に入る。これは ISO 週年と同じ分け方であり、ISO 週年を避けた利点がない。
- 「日付ノートの場所を変える旧設定は非推奨と案内されている」の根拠に daily-notes.md を挙げているが、daily-notes.md に「deprecated」の語はない。主張自体は package.json の `deprecationMessage` で正しいので、引用元の誤りである。
- 「Foam の指定された master のテンプレート文書は取得できなかった」としているが、私の取得では 200 で読めた。環境の問題と思われるが、結果として `main` の文書を代わりに読んでおり、指定された文書を読んだとは言えない。
- `50_Knowledge/notes/` の 2 段構成、`YYYY-MM-DD-<識別子>-<題名>.md` という命名は C と同じく作者のツリーより重い。
- 文量が多く、`log` の実装仕様（排他、再実行の冪等性、タイムゾーン）にまで踏み込んでいる。作者が今決めるべきディレクトリ構成と、後で設計書で決める事項の区別が薄い。

### 検証した事実
| 主張 | 結果 |
| --- | --- |
| `index.md` は走査対象外で、被リンクに数えられない | 一致（`SKIP_TOP_LEVEL_FILES` L107、`collect_pages` L159） |
| `$FOAM_PREVIOUS_DAILY_NOTE` はパスの型に依存し、パス変更前のノートは見つからない | 一致（daily-notes.md） |
| `foam.openDailyNote.directory` などは非推奨 | 一致（package.json。ただし daily-notes.md には書かれていない） |
| `init_wiki.py` はテンプレートのコピーでパスの置換を渡さない | 一致 |
| `SCHEMA.md.template` L7〜11 が `wiki/`、`raw/`、`raw/assets/` | 一致 |
| `docs/porting-plan.html` L461「変えてはいけないもの」 | 一致 |
| master の templates.md を取得できない | 食い違い（私の環境では取得できた） |

## 自分の結論の見直し

結論の骨格（根を 1 つに固定、`90_Wiki`/`91_Raw` を兄弟に、プラグインは役割→ディレクトリの対応表を読む、svg は `90_Wiki/assets/` のまま、`.foam` は内側の作業領域に置く）は変えない。A、C、D の 3 案も同じ骨格に独立に至っており、ADR と現行コードに整合する。次の 7 点を改める。

1. **設定ファイルは YAML ではなく JSON にする。** A の根拠のとおり、wiki の lint・stats は標準ライブラリだけで動き、Python 3.10 が下限なので `tomllib` も使えない。名前は `info-hive.json` か A の `.info-hive/workspace.json` のどちらでもよく、作者が決める。
2. **プロジェクトの探索は「1 段下の走査」をやめ、外側のプロジェクトルートに案内ファイルを置く**（C と D の方式）。複数候補の曖昧さがなく、サブモジュール内からも親の案内で見つかる。D の `log_scope` を案内ファイルに持たせる。
3. **`91_Raw/experiences/` を加え、`/wiki:learn`・`/wiki:evolve` が `--raw` を省くと `~/info-hive/raw/` を作る**ことを食い違いの表に加える（A の発見）。`commands/learn.md` と `evolve.md` は「raw ルートを特定する」としか書いておらず、`--raw` を渡す手順が明文化されていない。
4. **Foam の除外設定は `foam.files.exclude`** と書く（C の指摘。私は非推奨の `foam.files.ignore` を記憶で書いていた）。
5. **ADR-0005 の `![説明](assets/<slug>-NN.svg)` はページ相対では解決しない**ので、`../assets/<slug>-NN.svg` のようにページからの相対パスに改める必要がある、という点を食い違いの表に加える（C と D の指摘）。
6. **古い年の `20_Daily` を `A0_Archive` に動かす運用は勧めない**に改める。`$FOAM_PREVIOUS_DAILY_NOTE` の連鎖が切れる（D の指摘）。
7. 未決事項に、**タイムゾーンと日付の切り替え時刻**、**Foam と `log` の同時編集**を加える（C と D）。構成だけでは解決しないが、作業領域の設定に持たせる値として今決めておくほうがよい。

改めない点とその理由：

- **svg は `90_Wiki/assets/` のまま。** C と D は作者の決定 2 を広く読んで raw に入れたが、ADR-0004 の raw 不変性と ADR-0005 の決定（どちらも同日に承認）に反し、raw の定義まで変える必要が出る。作者の一言の解釈としては「取り込んだ画像」のほうが費用が小さい。作者の確認は要る。
- **`.foam/templates` は内側の作業領域に置く。** A はプロジェクトルートに置くが、Foam のルートにコードのサブモジュールが入る。
- **`50_Knowledge` は直下に置く**（作者のツリーのまま）。C と D の `notes/` の 1 段は作者のツリーにない。
- **週次は ISO 週（`YYYY-Www.md`）のまま。** Foam の変数と同じ値を作れる。

## 順位と確信度

| 順位 | 案 | 理由 |
| --- | --- | --- |
| 1 | エージェント A | 現行コードの読み込みが最も深く、`wiki_evolve_loop.py` の raw の決め打ち、`experiences/`、JSON を選ぶ根拠など、実装に直接効く発見がある。承認済みの ADR を変えない。弱点は Foam のルートをプロジェクトルートにしたことと、`filepath` の例の不整合で、どちらも局所的に直せる |
| 2 | 自分（この文書） | 骨格は A と同じで、Foam のマルチルートと単一ルートでの `filepath` の解釈の違い、ISO 週年の計算、ディレクトリ名を ASCII に限る理由など、構成の破綻の場面は具体的に書けた。YAML の選択、1 段下の走査、`foam.files.ignore`、`experiences/` の見落としが A に劣る |
| 3 | エージェント C | Foam と VS Code の設定、`.github` の置き場、外側の案内ファイル、同時編集とタイムゾーンの指摘は 4 案で最も丁寧。ただし生成 svg を raw に入れる判断で承認済みの 2 つの ADR と raw の定義を変えており、作者の一言に対して費用が大きい。命名も重い |
| 4 | エージェント D | C と同じ長所と同じ弱点（svg を raw に、`notes/` の 2 段、重い命名）に加え、`80_Code` で番号の体系を外側に広げ、ADR-0004 の画像の命名まで変えている。`index.md` と `$FOAM_PREVIOUS_DAILY_NOTE` の指摘は正確で価値がある |

確信度は**中**。A と自分の差は小さく、Foam のルートをどこにするかの一点で A を 2 位に置く判断もありうる。C と D の順位は、svg の置き場の解釈を作者がどう確認するかで入れ替わりうるが、どちらも承認済みの ADR の変更を伴う点で A と自分より下に置く判断は変わらない。

使用した MCP サーバー: なし
使用した Agent Skills: なし
