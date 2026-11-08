推奨は、用語ページを残し、独立して再利用・更新する知見だけを主張ページにする併用案です。指定の重みでは併用案が首位ですが、コストを重くすると現行案が首位になります。採点だけで全面移行は決めず、同じソースを別モデルで処理したときの分割一致と、再取り込みでの重複ゼロを PoC の条件にします。## 結論

Atomic Notes と Evergreen Notes は、**用語・実体のページを残し、再利用する知見を選んで独立させる併用案**として採る。  
独立ページの単位は「1 文」ではなく、**条件・根拠・留保を含む、独立して更新できる 1 つの判断・説明**とする。  
`type` は増やさず、`concept` に `note_role: "claim"` を加え、用語ページは入口と構造ノートを兼ねる。  
再現性のため、取り込みに「知見の抽出 → 既存ページとの照合 → 昇格判定 → 判定結果の保存」を追加する。  
56 ページの一括分割はせず、実在する 3 ソースで PoC を行い、分割の一致・重複・検索の改善を確かめて段階的に適用する。

## 根拠

### 1. 定義と出典

**Atomic Notes と Evergreen Notes は、同一の手法でも、厳密なページ分割アルゴリズムでもない。**

Luhmann の一次文献で確認できたのは、固定した識別番号、相互参照、キーワード索引、書誌情報と知識ノートの接続である。「Atomic Notes」「1 ノート 1 アイデア」を、そのまま Luhmann の用語や直接の指示として扱う根拠は確認できなかった。[Luhmann, *Communicating with Slip Boxes*, II](https://luhmann.surge.sh/communicating-with-slip-boxes)

現代の atomicity の説明では、Christian Tietze が「一緒に扱うべきものをまとめ、関心事を分ける」という原則を提示している。これは、根拠や適用条件までばらばらにする指示ではない。[Tietze, *Create Zettel from Reading Notes*](https://zettelkasten.de/posts/create-zettel-from-reading-notes/)

Matuschak も、細分化しすぎるとリンク網が分断されること、適切な単位に明確な正解はないことを述べている。また、題名は主張の文を推奨するが、用語の定義、問い、アウトラインを例外として認めている。したがって、**全面的な「1 主張 1 ページ」は Evergreen Notes の必須条件ではない。** [atomic](https://notes.andymatuschak.org/Evergreen_notes_should_be_atomic)、[題名の方針](https://notes.andymatuschak.org/Prefer_note_titles_with_complete_phrases_to_sharpen_claims)

| 原則 | 確認した内容 | LLM が保守する wiki での判定 | info-hive への適用 |
|---|---|---|---|
| 1 ノート 1 アイデア | 独立して再利用できる関心事を分ける。短さそのものが目的ではない | 変えれば保てる | 「独立した判断・説明」を単位にする。根拠・条件・反例は同じページに残す |
| atomic | 広すぎても細かすぎても接続しにくくなる | 保てる | 大きさと意味上のまとまりを別々に検査する |
| concept-oriented | 著者・本・出来事・プロジェクトごとでなく、概念を軸に知識を蓄積する | 保てる | `source` を入口とし、複数ソースが同じ知見を更新する |
| densely linked | 関係を考えて結ぶ。階層だけに閉じない | 変えれば保てる | 出典・用語・関連する判断に意味のあるリンクを付ける。リンク数のノルマは設けない |
| 題名を主張の文にする | 本文で支えるべき主張を明確にする。定義用の名詞題名などは例外 | 変えれば保てる | 主張ページに適用し、用語・実体・source には強制しない |
| 時間をかけて育つ | プロジェクトを越えて追記・修正し、知見を蓄積する | 変えれば保てる | 新規取り込み・query・lint を見直しの契機とし、毎回の全面再生成を避ける |
| 自分のために書く | 公開用文章の完成度を最初から要求しない | 変えれば保てる | 「自分」は LLM でなく wiki の利用者。関心と用途を `SCHEMA.md` に明示する |
| 書くことで本人が理解を深める | 人の読解・思考・記憶の実践を含む | 保てない | LLM の出力から作者の理解・習得を推定しない。評価対象は wiki の品質と再利用に限る |
| literature note と permanent note を分ける | 資料に従属する記録と、資料を越えて使う知見を区別する | 変えれば保てる | `source` と、継続更新する `concept` を機能上区別する |

表の Evergreen Notes の根拠は、Matuschak の [概要](https://notes.andymatuschak.org/Evergreen_notes)、[concept-oriented](https://notes.andymatuschak.org/Evergreen_notes_should_be_concept-oriented)、[densely linked](https://notes.andymatuschak.org/Evergreen_notes_should_be_densely_linked)、[自分のために書く](https://notes.andymatuschak.org/zXDPrYcxUSZbF5M8vM5Y1U9)、[ノートの分類](https://notes.andymatuschak.org/Taxonomy_of_note_types)である。

Ahrens の *How to Take Smart Notes* は関連する原典として扱う。ただし、著者公開のプレビューで確認できた範囲は限られ、**「各アイデアに 1 ノート」の該当箇所と、literature note を permanent note に含める用語上の範囲は一次資料で未確認**である。本稿の対応表は、Ahrens の分類の厳密な翻訳ではなく、info-hive での機能上の対応である。[著者公式ページとプレビュー](https://www.soenkeahrens.de/en/takesmartnotes/)

なお、2025 年の Zettelkasten.de の再検討も、atomicity を保存前の必須条件にすると未発達な主張だけを量産しやすいと論じ、継続的に近づける目標として扱っている。これは手法の提唱側による見解であり、効果の実証研究ではない。[Sascha, *The Principle of Atomicity*](https://zettelkasten.de/posts/principle-of-atomicity-difference-between-principle-and-implementation/)

### 2. 既存の種類との対応

| 現行の種類・場所 | 対応する役割 | 推奨する扱い |
|---|---|---|
| raw | 原資料。literature note そのものではない | 変更不可を維持する |
| `source` | literature note、書誌・出来事への入口 | ソース単位の要約を維持し、抽出した知見と行き先を記録する |
| `entity` | 人物・製品などの参照ノート | 同一性と属性を蓄積する。属性ごとに主張ページを作らない |
| 用語を説明する `concept` | 定義ノート、概念の入口 | 定義を残し、関係する主張を束ねる構造ノートも兼ねる |
| 主張の形になった `concept` | permanent / evergreen note に近い | `note_role: "claim"` で役割を明示する |
| `concept` の `kind: experience-pattern` | 適用条件と証拠を持つ経験則 | 既存の `status` と、観測事実・原因仮説の区別を維持する |
| `synthesis` | 問いに答える統合・比較ノート | 複数の判断を結ぶ役割を維持する。全文を 1 主張に縮めない |
| `index.md`、`indexes/` | 目録、MOC の入口 | 網羅的な所在案内を担う |
| 用語ページの関係節 | structure note に相当する機能 | 主張の関係や読み順を説明する。索引の単なる複製にはしない |

欠けているのは、第五のページ型よりも、次の二つである。

- **資料から知見へ昇格させる明示的な判定手順。**
- **何を既存ページへ統合し、何を source に残したかを追える記録。**

`source` にしかない記述をすべて欠落とみなしてはいけない。実行日時、テスト件数、特定コミットの受け入れ状況は、source に残ること自体が適切である。

### 3. 現状から分かる問題

作者の wiki を読み取り、次を確認した。

| 指標 | 確認結果 |
|---|---:|
| `source` | 37 |
| `entity` | 1 |
| `concept` | 17 |
| `synthesis` | 1 |
| 合計 | 56 |
| `semasynth*.md` の source | 28 |
| `sources:` に `semasynth` を含む concept | 0 |
| `index.md` | 104 行 |
| `indexes/` 内の Markdown | 0 |

集計は対象四ディレクトリの Markdown と `type:`、concept の `sources:` を読み取った結果である。したがって「SemaSynth への言及が本文にも一切ない」とまでは結論しない。

既存の `concepts/編集要求の復元世代を最終適用まで保持する.md` は、理由、三つの境界、適用範囲を一つにまとめている。これは推奨単位に近く、三つの境界を機械的に三ページへ分ける必要はない。同ページの 12–34 行が根拠になる。

また、**実 wiki のサイズ規約はプラグインの既定値と異なる。**

- 既定：ソフト 10,000 文字・100 行、ハード 25,000 文字・200 行。
- 作者の `SCHEMA.md` 38–45 行：ソフト **4,000 文字・400 行**、ハード **8,000 文字・800 行**。

本件では後者が優先する。上限の変更を Atomic Notes 導入に便乗させる必要はない。

### 4. 単位の候補の比較

点数は測定結果ではなく、現行コードと提案する運用に基づく判断値である。③には後述の判定記録を、④には Markdown の見出しとして主張を明示する軽い実装を想定した。④にグラフ内主張の完全な管理まで要求して、不当に重く採点してはいない。

| 案 | 再利用・成長 25 | 再現性 20 | 規模・コスト 20 | 既存整合 20 | 移行・実装 15 | 加重合計 |
|---|---:|---:|---:|---:|---:|---:|
| **③ 用語・実体と、選別した主張ページの併用** | 9 | 8 | 7 | 9 | 8 | **8.25** |
| ④ 主張をページ内の単位にする | 7 | 7 | 9 | 9 | 8 | **7.95** |
| ① 現行のまま | 5 | 6 | 9 | 10 | 10 | **7.75** |
| ② 1 主張 1 ページを全面適用 | 9 | 4 | 3 | 6 | 3 | **5.30** |

各点数の理由は次のとおりである。

| 案 | 点数の理由 |
|---|---|
| ① | 用語の同一性と既存構成を保ちやすい。主張の抽出と行き先が引き続き暗黙なので、source 偏重は残りやすい |
| ② | 知見を直接指せるが、言い換え・条件差・主張と根拠の切り分けが大量のページ境界になる。索引、探索、改名、移行の負担が大きい |
| ③ | 知見を複数ソースで育てつつ、定義や属性は集約できる。判定記録と既存ページ優先で揺れを抑える。ただし新規ページと照合の費用は増える |
| ④ | 現行のセクション検索に適し、ファイル増加が少ない。一方、同じ主張が複数ページに現れた場合の正本、更新先、被リンクをページとは別に決める必要がある |

計算式は `Σ（点数 × 重み）÷ 100`。③は  
`(9×25 + 8×20 + 7×20 + 9×20 + 8×15) / 100 = 8.25` である。

**重みを変えると首位は入れ替わる。**

| 重みの設定〔再利用、再現性、コスト、整合、軽さ〕 | ① | ② | ③ | ④ | 順位 |
|---|---:|---:|---:|---:|---|
| 指定〔25,20,20,20,15〕 | 7.75 | 5.30 | **8.25** | 7.95 | ③ → ④ → ① → ② |
| 成長重視〔40,25,10,15,10〕 | 6.90 | 6.10 | **8.45** | 7.60 | ③ → ④ → ① → ② |
| コスト重視〔10,15,35,20,20〕 | **8.55** | 4.35 | 7.95 | 8.30 | ① → ④ → ③ → ② |

③と④の基準重みでの差は 0.30 にすぎない。③の「再利用」と「再現性」を各 1 点下げれば 7.80 になり、④が上回る。**推奨は PoC で確認する仮説であり、採点だけを根拠に全面移行する判断ではない。**

### 5. 推す案の詳細

#### 5.1 ページにするかの判定手順

**独立ページの定義**

> 一つの問いに対し、条件付きの答え・説明・判断を示し、その根拠、適用範囲、反例を同じ場所で更新できる単位。

「同一環境ではバイト一致、異なる環境では論理一致」は二つの文に分けられるが、比較して判定方法を選ぶ一つの判断である。逆に「再現性の判定」と「CSV の NULL 復元」は、短くても別の判断になる。

`/wiki:ingest` では次の順で判定する。

| 順 | モデルが問うこと | 判定・処置 |
|---|---|---|
| 0 | どの `SCHEMA.md`、関心・用途、判定規約を適用するか | 規約の版と、取り込む raw の内容ハッシュを確定する |
| 1 | ソースのどこに、どんな知見が明示されているか | 候補ごとに主語、条件、述べていること、根拠位置、事実・提案・仮説の別を記録する |
| 2 | 単なる進捗・一回の数値・固有対象の属性・用語の定義ではないか | 進捗は source、属性は entity、定義は既存の用語ページへ送る |
| 3 | 同じ条件と意味を扱う既存ページがあるか | 索引、別名、関連ページ、必要なら検索で調べ、本文まで読む。あれば更新を優先する |
| 4 | 条件を保ったまま、別の資料や将来の問いから再利用できる答えになるか | `SCHEMA.md` の用途、既存の問い、複数ソースでの再登場、資料が明示する設計原則のいずれかを根拠にする。「いつか役立ちそう」だけでは昇格しない |
| 5 | 根拠・理由・適用範囲を、ソースの範囲内で説明できるか | 題名の言い換えしか書けない、条件が不明、推測で一般化が必要なら source の候補として残す |
| 6 | この知見だけが独立して支持・反証・更新されうるか | 独立するなら主張ページ。既存の判断の説明・例・条件なら同ページの節にする |
| 7 | 隣の候補と分けることで、別々に再利用できるか | 同じ判断の理由と結論ならまとめる。対象・条件・更新理由が独立するなら分ける |
| 8 | 行き先と見送り理由が記録されているか | `create`、`update`、`source_only` と対象ページ・理由を source に残す |

候補の照合では、題名の類似よりも、**対象・条件・肯定／否定・断定の強さ・述べている関係**を優先する。例えば「有効である」と「有効かもしれない」、「Windows 全般」と「今回の版・環境」は同じ主張と決めつけない。

候補の抽出順は raw の出現順とし、一度割り当てた候補 ID は保存する。同じ候補を取り込むたびに題名から ID を作り直さない。

**境界の裁き方**

| 揺れやすい例 | 裁き方 |
|---|---|
| 「オープンワールド仮定」と「未記載の事実を不明と扱う」 | 定義として同義なので既存の用語ページへ統合する。題名を文章にできることだけでは新設しない |
| 「同一環境のバイト一致」と「異環境の論理一致」 | 判定基準を選ぶ比較として一ページにする。後に各方式が独立した論点へ育ったら切り出す |
| 「検証対象から独立した期待値」と「信頼する基準 manifest」 | 前者は意味上の正しさ、後者は改変検出の信頼条件を扱うので分け、相互参照する |
| 「386 テストが通った」と「独立した期待値で検証する」 | 前者は時点・版に属する source の観測。後者は再利用できる判断の候補 |
| OUTPUT 編集の三つの境界 | 一つの世代整合の設計を成立させる協調手順なので、既存の一ページを維持する |
| Windows の Tantivy の失敗例 | 測定条件・版・原因未特定を残す。「Windows では常に失敗する」と一般化しない。既存ページを更新する |

#### 5.2 題名とスラッグ

- 用語・entity は名詞題名を維持する。
- 主張ページは「何が、どんな条件で、どうなる／どう扱う」を表す文にする。
- 一資料の提案を確定事実に変えない。提案・仮説であることをリードに明記し、題名でも必要な限定を落とさない。
- 題名は人向け、スラッグは安定した参照先とする。文章の推敲だけでスラッグを変えない。
- 新しいスラッグは現行の小文字・空白なし・禁止文字なし・NFC の規則に従う。
- 長さは題名 60 文字程度を見直しの目安にする。これは新しいハード上限ではない。長い場合は意味を保ってスラッグを短縮し、実際の保存先まで含むパス長を確認する。
- `aliases:` は同義表現の照合に使う。**別名をそのままリンク先として解決できるとは仮定しない。** 本文は実在するスラッグを指す。
- 日本語の文中では、例えば `[[同一環境と異なる環境では再現性の判定を分ける|環境別の再現性判定]]` のように表示名を使える。

次は、実際に読んだ raw から作れる題名の例である。すべてを直ちに新設する指示ではない。

| 題名の例 | 新設する場合のスラッグ例 | 根拠 |
|---|---|---|
| 同一環境と異なる環境では再現性の判定を分ける | `同一環境と異なる環境では再現性の判定を分ける.md` | SemaSynth 再現性 raw 7 行 |
| 再生成の同等性と配布物の改変検出を区別する | `再生成の同等性と配布物の改変検出を区別する.md` | 同 7 行 |
| 汎用CSVからNULLと空文字を復元するには列情報が要る | `汎用csvのnullと空文字の復元には列情報が要る.md` | 同 13 行 |
| 検証対象と独立した期待値で会計データを検証する | `検証対象と独立した期待値で会計データを検証する.md` | 敵対的レビュー raw 15–17 行 |
| ハッシュによる改変検出は基準manifestの信頼を前提とする | `ハッシュによる改変検出は基準manifestの信頼を前提とする.md` | 同 22 行 |
| 実行環境の識別には日時と絶対パスを含めない | `実行環境の識別には日時と絶対パスを含めない.md` | 再現性 raw 5 行。まず再現性ページの条件として扱う |
| 少数回の性能測定から性能保証値を定めない | `少数回の性能測定から性能保証値を定めない.md` | 同 11 行。性能評価を対象にする取り込みで昇格を判断する |

既存の空白入りスラッグを、この規約導入だけで一括改名しない。

#### 5.3 frontmatter と `type` / `kind`

**`type` は四種類を維持する。`kind` に役割を詰め込まず、追加するなら `note_role` を使う。** これにより `kind: "experience-pattern"` と併用できる。

```yaml
---
type: "concept"
note_role: "claim"
title: "同一環境と異なる環境では再現性の判定を分ける"
claim: "同一環境ではバイト一致を、異なる環境では値と型の一致を確認する。"
scope: "SemaSynthの再生成検証。PythonとSQLiteの版が異なる場合を含む。"
tags: ["知識表現"]
sources: ["semasynth再現性の検証-2026-11-06", "semasynth-mvp設計の敵対的レビュー-2026-11-06"]
created: 2026-11-08
updated: 2026-11-08
---
```

これは作成例であり、ファイルは書いていない。

- `note_role: "claim"`：主張ページ。`claim` と `scope` を必須にする。
- `note_role: "hub"`：主張を束ねる役割を明示したい用語ページ。既存ページには一括付与しない。
- フィールドのない既存ページも引き続き有効にする。
- `experience-pattern` の `status: hypothesis|supported|superseded` は維持する。通常の知見を作るだけで、検証済み経験へ格上げしない。
- キー・値は英語で書き、日本語の別名を追加する場合は `wiki_text.py` の読み取り側も合わせる。
- 原子性だけを理由に `type: "claim"`、`claims/`、`type: "moc"` は新設しない。

追加フィールドを平坦にしたのは、通常の frontmatter パーサーが文字列と文字列配列を扱い、入れ子を一般には読まないためでもある。根拠は `wiki_text.py` 281–298 行である。

#### 5.4 ingest・query・graph・インデックスへの影響

| 対象 | 改訂の要点 |
|---|---|
| `ingest-workflow.md` | 手順 2 の後に候補抽出を追加。手順 4 を意味と条件による既存ページ照合へ拡張。手順 5 に候補と行き先の表を追加。手順 7 の「今後掘り下げそう」を、前述の判定表で置き換える |
| `page-conventions.md` | 定義ページ・主張ページ・構造ノートの役割を区別する。「見出しが多いから分割」を警告へ下げ、独立した更新単位かを主基準にする |
| `SKILL.md`、`architecture.md` | 「すべて一コンセプト」の説明を、ページの役割ごとの単位へ更新する |
| `SCHEMA.md.template` | 採用する単位、利用目的、`note_role`、判定規約の版、既存ページ優先を追加する。既存 wiki の規約を自動上書きしない |
| `page.md.template` | 現行の共通テンプレートを残し、主張ページの構成例を追加する |
| query | 主張ページを直接読めるようにする。用語ページから全リンクを無条件に展開せず、必要な主張だけを選ぶ。重要な判断は条件と元ソースまでたどる |
| 検索 | `type: "concept"` を維持するので既存の絞り込みを壊しにくい。セクション検索も維持する。細分化による類似結果の増加は PoC で測る |
| インデックス | 全ページ一行を維持する。主張ページを用語ページに隠して目録から除外しない。150 ページ／300 行の分割条件を維持する |
| `learn.md`、`evolution-workflow.md` | 経験のパターンを同じ単位判定に接続する。観測・仮説・適用範囲・反例の既存要件を維持する |
| `lint.md`、`lint-workflow.md` | 構造エラーと、意味上の分割・統合候補を分けて報告する |

source に追加する判定表は、例えば「候補 ID、知見、根拠位置、処置、行き先、理由」とする。LLM の非公開の推論ではなく、編集判断を監査するための短い結果を残す。

同じ raw を再取り込みした場合、保存した判定表をまず読む。内容ハッシュと規約が同じで、関係する wiki の状態にも変化がなければ再分割しない。wiki が成長した場合は既存表との差分を調べ、過去の候補 ID とページ参照を保つ。**raw のハッシュが同じというだけで、その後の統合機会まで永久に無視する設計にはしない。**

グラフについては、文書と実装の区別が必要である。

- `ontology.yaml.template` は `claim` を `explicit_only` にしている。
- `graph-workflow.md` 59 行は claim がページを持たないと説明する。
- 一方、`wiki_graph_extract.py` 238–258、266–300 行と `wiki_graph_lint.py` 148–171 行は、実在ページの明示的な `graph.node_type` を受け入れる。

コード上は、主張ページに次を付ければ、ページに対応する claim ノードを表現できると読める。**実行検証はしていない。**

```yaml
graph:
  node_type: "claim"
```

したがって、まず直すのは「claim は必ずページを持たない」という説明である。新しいページ型やブロック用ノードを実装する必要はない。

ただし、全主張ページを無条件に claim ノードへ変換する必要もない。通常の探索は `mentions` と `sourced_from` で成立する。型付きの `contradicts` / `supersedes` が必要なページに明示するところから始める。

- `concept` のままでは、既定の `contradicts` / `supersedes` の型制約に合わない。
- claim ノードにすると、今度は既定の `depends_on` が claim を受け付けない。
- 必要な型制約の変更だけを別途検討し、全述語を `*` に緩めない。
- 主張への新しい裏づけは同ページに追加する。
- 条件が異なる主張は、直ちに `contradicts` にしない。
- 明示された置き換えだけを `supersedes` にする。単に新しい資料が出たことを置き換えとみなさない。
- ソースが明示しない wiki 編集上の判断は、本文で理由を説明する。型付きエッジを捏造しない。

既存の証拠確認は source ページの本文を対象にしており、raw 全体の忠実性を保証しない。新しい主張の根拠記録は raw の位置までたどれるようにし、グラフの引用照合と混同しない。該当コードは `wiki_graph_lint.py` の `decide_evidence` である。

#### 5.5 lint で機械的に検査する指標

現行の `wiki_lint.py` は大きさ、リンク、frontmatter 等を検査するが、**見出し数や意味上の主張数による原子性検査は実装していない。** `collect_pages`、`lint`、`DEFAULT_REQUIRED_FM` が根拠である。

| 機械的に検査できるもの | 扱い |
|---|---|
| `note_role` の許容値、claim ページの `claim`・`scope` の欠落 | エラー |
| claim ページの `sources:` が空、参照先が存在しない／`source` でない | エラー |
| 異なるページからの被リンクがない | エラー。自己リンクは被リンクとして数えない |
| 候補 ID の重複、処置や行き先の欠落 | エラー |
| `create` / `update` の行き先が存在しない | エラー |
| 保存した根拠位置と短い引用が raw に一致するか | 不一致をエラー。ただし一致しても主張の含意までは保証しない |
| スラッグの禁止文字・正規化衝突・重複 | エラー |
| ページのサイズ | `SCHEMA.md` の値で従来どおり検査 |
| 主張ページの題名が名詞だけ、長すぎる、複数の独立節を連ねる | 警告。日本語の活用や意味は正規表現だけで判定しない |
| 主張本文が題名の反復だけ、根拠・範囲がない | 構造的な欠落は警告。十分性は内容レビュー |
| 見出し数が多い、同じ `claim` が複数ページにある | 分割・重複の候補として警告 |
| index の区分と実際の `type` が食い違う | 警告 |

「主張が一つか」「二つの言い換えが同じ意味か」「引用が結論を支えるか」は、機械的な件数だけでは保証できない。見出し数やリンク数を、意味上の原子性の代用品にしない。

### 6. 実在ソースによる取り込み直しの試案

以下は**実際にファイルを書かない机上の試案**である。今回の対象を「部分観測の判断、再現性、独立検証」に固定する。source は既存のものを更新し、原本や実行記録は残す。

略号：

- **O**：`part-1-what-is-an-ontology-classes-properties-and-axioms`
- **R**：`semasynth再現性の検証-2026-11-06`
- **V**：`semasynth-mvp設計の敵対的レビュー-2026-11-06`

| ページの題名 | 種類・処置 | 主なリンク先 |
|---|---|---|
| Part 1: What Is an Ontology? Classes, Properties, and Axioms | `source`、O を更新 | 既存の用語ページ、下の部分観測の主張 |
| オントロジー | `concept`、既存更新 | O、オープンワールド仮定、`rdf-rdfs-owl` |
| オープンワールド仮定 | `concept`、既存更新 | O、部分観測の主張 |
| RDF・RDFS・OWL を扱う既存ページ | `concept`、既存更新 | O、オントロジー |
| 部分観測のエージェントでは欠測を偽と決めつけない | `concept`、`note_role: "claim"`、新規 | O、オープンワールド仮定、グラウンディング |
| SemaSynth 再現性の検証 | `source`、R を更新 | 下の再現性・改変検出・CSV の主張 |
| 同一環境と異なる環境では再現性の判定を分ける | `concept`、claim、新規 | R、V、再生成と改変検出の主張 |
| 再生成の同等性と配布物の改変検出を区別する | `concept`、claim、新規 | R、基準 manifest の主張 |
| 汎用CSVからNULLと空文字を復元するには列情報が要る | `concept`、claim、新規 | R、V |
| SemaSynth MVP 設計の敵対的レビュー | `source`、V を更新 | 独立した期待値、再現性、基準 manifest の主張 |
| 検証対象と独立した期待値で会計データを検証する | `concept`、claim、新規 | V、`semasynth会計データの再検証-2026-11-06` |
| ハッシュによる改変検出は基準manifestの信頼を前提とする | `concept`、claim、新規 | V、R、再生成と改変検出の主張 |

この試案では、新しい主張ページは 6 本である。既存 56 ページに追加するだけなら **62 ページ**になる。これは運用全体の増加予測ではない。

判定上の注意は次のとおりである。

- O の定義・四構成要素・標準の説明は既存ページへ戻す。四構成要素を四枚の主張ページにしない。
- 「部分観測では欠測を偽と決めつけない」は、O の第 4 節にある著者の推奨として書く。一般的な優越性が実証されたとは書かない。
- R と V にある環境別の再現性判定は一ページへ統合する。二資料があることと、独立した二実験で裏づけられたことは区別する。
- R の日時・絶対パスの扱いは、まず再現性ページの条件に含める。
- 性能測定と通信制御の範囲は source に残し、今回の対象外と記録する。取り込み規約に対象を明記せず、モデルの気分で候補を落とさない。
- V の「未実施」と、source に追記された後続実装の記録は時点を分ける。古い記録を消したり、同時点の矛盾と扱ったりしない。

**再現性を測る PoC**

1. 同じ raw、同じ `SCHEMA.md`、同じ wiki のスナップショット、同じ検索条件を固定する。
2. 2 モデルで各 3 回、3 ソースを独立に処理する。合計は `2×3×3 = 18` 回。成果は編集前の候補・行き先一覧として比較する。
3. 自由な候補抽出と、共通の候補一覧を渡した行き先判定を分けて実施する。抽出の揺れとページ分割の揺れを区別する。
4. 別に、取り込み済みの状態へ同じソースを再度渡し、重複を作らないか確認する。
5. 比較者にはモデル名を隠し、raw に照らして意味と条件の一致を判定する。題名の完全一致だけで評価しない。

| 指標 | 測り方 |
|---|---|
| 候補抽出の一致 | 意味と範囲が一致した候補について `F1 = 2TP / (候補数A + 候補数B)` |
| ページ分割の一致 | 共通候補の組について、同じページにまとめた／分けた判断の pairwise F1 |
| 行き先の一致 | `create`、`update`、`source_only` と対象ページが一致した候補の割合 |
| 再取り込みの冪等性 | 二回目の新規ページ数、重複候補行数。ともに 0 を目標にする |
| 根拠と条件の保持 | raw にない一般化、条件・留保の脱落、引用不一致の件数 |
| 再利用の改善 | 固定した質問で必要な判断と出典を取得できた割合、読む文字数・ページ数 |
| 費用 | 入出力トークン、探索・更新対象数、新規ページ数、索引の増分 |

初期の採用条件案は、候補・分割・行き先の一致がそれぞれ 0.90 以上、重複 0、重大な条件脱落 0 とする。数値は実績でなく提案値であり、小さい試験なので件数も併記する。0.90 を満たしても「モデルが変わっても同一になる」とまでは主張しない。

一致が不足する場合は、条件や同一性の基準を直す。それでも不安定なら、④のページ内主張を既定にして、再利用が確認されたものだけ昇格する。

### 7. 移行

一括変換は勧めない。

1. **既存 56 ページを維持する。** 主張題名の既存ページも、用語題名の既存ページも有効とする。
2. PoC を通して、`SCHEMA.md` と references の差分を確定する。
3. 新規取り込みから候補抽出と行き先の記録を始める。source だけで終えた場合も理由を残す。
4. 次の取り込み・query・lint で実際に使う既存ページから、必要な知見を切り出す。
5. 切り出した元ページには短い説明とリンクを残し、本文の同じ主張を二か所で独立に育てない。
6. SemaSynth の 28 source は、今回の再現性・検証のまとまりから順に扱う。28 本を一度に再編集しない。
7. 移行後は索引・検索の同期と、グラフ有効時の extract を行う。

索引には既に、実体は `sources/` の SemaSynth 記録が「シンセシス」の節に並ぶ箇所がある。これは新しい型を考える前に直すべき目録の不整合であり、ページ数だけでなく実際の `type` に基づいて整理する。

規模の感度として、28 source から平均 2 ページずつ追加すれば `56+28×2=112`、平均 5 ページなら `56+28×5=196` になる。後者は 150 ページの分割目安を超える。これは重複統合を考慮しない仮定計算だが、全面的な主張分割の費用が小さくないことを示す。

## 検討した代替案

- **① 現行のまま**  
  費用を最優先するなら妥当であり、感度分析でも首位になる。ただし、作者の実 wiki で確認された source 偏重に対し、知見を昇格させる判断が引き続き暗黙になる。

- **② 1 主張 1 ページの全面適用**  
  採らない。定義・根拠・比較・協調する手順まで分断しやすく、日本語の長い題名、同義主張の重複、改名、索引増加が取り込みごとの負担になる。Evergreen Notes の原典も、この全面適用を要求していない。

- **④ 主張をページ内に持つ**  
  有力な次点であり、昇格前の候補の保存には採る。既存のセクション検索と相性がよい。一方、複数ソースを越えて同じ知見を継続更新する際には、どのページ内主張を正本にするかという別の規約が要る。

- **グラフの `claim` だけを知識の正本にする**  
  採らない。ADR-0009 はグラフを Markdown の派生索引と位置付けている。ブロックや命題をグラフだけに置くと、本文との二重管理になる。独立させる価値がある知見は Markdown に置き、必要な場合だけ claim ノードを明示する。

## 前提と不確実性

- **完全な意味上の再現性は保証できない。** 判定表・固定入力・既存ページ優先・保存した行き先で揺れを抑えられるが、初回の抽出と意味の同一性にはモデルの判断が残る。
- **source 偏重の原因は、単位だけとは限らない。** 今回確認できたのは source と concept の参照の偏りである。再利用する問いの不足、取り込み時の指示、索引の不整合も原因になりうる。
- **Ahrens の該当章は一次資料で未確認。** 用語の厳密な包含関係を、今回の分類案の根拠にはしていない。
- **graph の claim ページ対応はコードからの判断。** `graph.node_type` の明示が受け入れられる実装は確認したが、本件では抽出・lint の実行試験をしていない。
- **検索性能と費用は未測定。** 小さいページになれば必ず検索が良くなるとは限らない。見出しとページの文脈が減り、似た結果が増える可能性もある。
- **評価基準には不足がある。** 「出典への忠実性」「条件・留保の保持」は加重点で相殺できる性質ではない。別の必須条件にするべきである。また、再利用・成長と既存整合には、索引やリンクの効果を重複評価する余地がある。
- **作者の判断が要るのは、知識を育てる対象範囲である。** ソフトウェア検証の一般則、製品固有の判断、業務上の判断のどこまでを wiki の再利用対象にするかを `SCHEMA.md` に書く必要がある。本稿では、条件を保って再利用できる設計・検証の判断を対象と仮定した。
- リポジトリと作者の wiki は変更していない。ビルド、取り込み直し、PoC は実行していない。指定された今回の他エージェント成果ディレクトリは読んでいない。

## 参照

ローカル参照でのプラグインのルートは `C:/Works/info-hive-dev/info-hive-wiki/`、作者の wiki は `D:/Users/toshiki/info-hive/W0_Wiki/` である。以下の絶対パスは読んだ場所の提示であり、提案する仕様の固定パスではない。

**現行規約と実装**

- [AGENTS.md](/C:/Works/info-hive-dev/.claude/worktrees/determined-colden-314f71/AGENTS.md)：応答言語、配置、方針 B、変更とリリースの規約。
- [docs/porting-plan.html](/C:/Works/info-hive-dev/.claude/worktrees/determined-colden-314f71/docs/porting-plan.html)：方針 B・D・I。
- [SKILL.md](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/SKILL.md)：三層、アトミックなページ、索引、部分更新、検索。
- [ingest-workflow.md](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/ingest-workflow.md:135)：手順 4–8b、末尾の raw 再確認。
- [page-conventions.md](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/page-conventions.md:68)：大きさ、命名、本文構成、引用、留保。
- [architecture.md](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/architecture.md)：各層とページの役割、Markdown が正本である理由。
- [scaling-playbook.md](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/scaling-playbook.md:18)：150・300・500 ページの段階。
- [graph-workflow.md](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/graph-workflow.md:27)：明示的ノード、証拠、型付き関係、extract。
- [lint-workflow.md](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/lint-workflow.md)、[query-workflow.md](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/query-workflow.md)、[evolution-workflow.md](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/references/evolution-workflow.md)：構造と内容の検査、検索、経験の記録と検証。
- [SCHEMA.md.template](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/assets/SCHEMA.md.template)、[ontology.yaml.template](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/assets/ontology.yaml.template)、[page.md.template](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/assets/page.md.template)：既定の型、必須項目、ノード・述語、本文例。
- [commands/ingest.md](/C:/Works/info-hive-dev/info-hive-wiki/commands/ingest.md)、[learn.md](/C:/Works/info-hive-dev/info-hive-wiki/commands/learn.md)、[lint.md](/C:/Works/info-hive-dev/info-hive-wiki/commands/lint.md)。
- [wiki_lint.py](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_lint.py:215)：`collect_pages`、`DEFAULT_REQUIRED_FM`、`lint`。
- [wiki_text.py](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_text.py:281)：通常の frontmatter の解析。
- [wiki_graph_extract.py](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_extract.py:238)、[wiki_graph_lint.py](/C:/Works/info-hive-dev/info-hive-wiki/skills/info-hive/scripts/wiki_graph_lint.py:148)：ノードの導出、明示的型、証拠の検査。
- [ADR-0009](/C:/Works/info-hive-dev/.claude/worktrees/determined-colden-314f71/docs/adr/0009-graph-layer-stays-in-wiki.md:24)：グラフを wiki 内の任意の派生索引とする決定。
- [前回の活用方法の総括](/C:/Works/info-hive-dev/.claude/worktrees/determined-colden-314f71/docs/agent-runs/2026-11-06-wiki-knowledge-utilization/summary.md)：利用習慣、観測と仮説、採点の限界。

**作者の wiki と原資料**

- [index.md](/D:/Users/toshiki/info-hive/W0_Wiki/index.md)、[SCHEMA.md](/D:/Users/toshiki/info-hive/W0_Wiki/SCHEMA.md:38)、`graph/ontology.yaml`、四種類のページ一覧と frontmatter。
- [オントロジー](/D:/Users/toshiki/info-hive/W0_Wiki/concepts/オントロジー.md)、[オープンワールド仮定](/D:/Users/toshiki/info-hive/W0_Wiki/concepts/オープンワールド仮定.md)。
- [編集要求の復元世代を最終適用まで保持する](/D:/Users/toshiki/info-hive/W0_Wiki/concepts/編集要求の復元世代を最終適用まで保持する.md:12)。
- [Windows での Tantivy の commit の失敗](</D:/Users/toshiki/info-hive/W0_Wiki/concepts/Windows での Tantivy の commit の失敗.md>)、[BM25 の IDF の式の違い](</D:/Users/toshiki/info-hive/W0_Wiki/concepts/BM25 の IDF の式の違い.md>)。
- [オントロジー連載第 1 回の source](/D:/Users/toshiki/info-hive/W0_Wiki/sources/part-1-what-is-an-ontology-classes-properties-and-axioms.md)、[保存された raw](/D:/Users/toshiki/info-hive/W1_Raw/part-1-what-is-an-ontology-classes-properties-and-axioms.md:57)：第 4–6 節。
- [SemaSynth 再現性の source](/D:/Users/toshiki/info-hive/W0_Wiki/sources/semasynth再現性の検証-2026-11-06.md)、[raw](/D:/Users/toshiki/info-hive/W1_Raw/semasynth再現性の検証-2026-11-06.md:5)：環境、再生成、通信制御、測定、CSV。
- [SemaSynth 敵対的レビューの source](/D:/Users/toshiki/info-hive/W0_Wiki/sources/semasynth-mvp設計の敵対的レビュー-2026-11-06.md)、[raw](/D:/Users/toshiki/info-hive/W1_Raw/semasynth-mvp設計の敵対的レビュー-2026-11-06.md:10)：独立した期待値、再現性、基準 manifest、実施時点。

外部原典の URL と該当する論点は「定義と出典」に記載した。GitHub 接続でも文書を参照した後、ローカルの指定ファイルを読み直し、本稿の現行仕様の判断にはローカル側を用いた。

```text
使用した MCP サーバー: codex_apps（GitHub）
使用した Agent Skills: なし
```
