# wiki の記事の単位の PoC（2026-11-09）の実行の記録

結果の報告は [docs/research/wiki-note-granularity-poc-2026-11-09.md](../../research/wiki-note-granularity-poc-2026-11-09.md) にある。本書は、何をどう走らせたかの記録である。

## 見積もったコスト（走らせる前に記録）

見積もり: Claude Opus 5.5（effort high）の 18 件は 1 件 1〜2.5 USD で計 20〜45 USD、GPT-6.1 Sol（effort high、ChatGPT のプランの Codex CLI）の 18 件は 1 件 50 万〜300 万入力トークン（大半がキャッシュ）で従量の課金なし、所要はベンダーごとに 3 並列で 1〜2 時間。根拠は、前日の 4 体の検討の 1 件（Opus 3.1 USD、Sol 650 万入力トークン）より読む量が少ないことと、`claude -p` の空の呼び出しが 0.20 USD かかったこと。

実績（本番の 36 件。R と V は走らせ直したもの）: Opus 9.06 USD、1 件平均 142 秒。Sol 入力 130 万トークン、出力 26 万トークン、1 件平均 366 秒。最初の本番は 2026-11-09 08:40〜09:35、R と V の走らせ直しは 09:51〜10:14。このほか、パイロットに Opus 1.73 USD と Sol の失敗 2 回の約 40 分、原本が混ざった R と V の最初の 24 件に Opus 約 5.70 USD を使った。

## 規模

固定の 3 資料 × 2 モデル × 3 回 × 2 方式（現行、併用案）＝ 36 件。規模は作者が 2026年11月9日に決めた（[wiki-article-methodology-adoption-2026-11-08.md](../../research/wiki-article-methodology-adoption-2026-11-08.md) の第 8 節）。

| 記号 | 資料 | 置き場所 | 行数 |
| --- | --- | --- | --- |
| O | Yuan An「Part 1: What Is an Ontology? Classes, Properties, and Axioms」（オントロジー連載の第 1 回） | `~/info-hive/W1_Raw/`、wiki は `~/info-hive/W0_Wiki/` | 197 |
| R | SemaSynth 再現性の検証（ADR 0005） | `C:\works\semasynth-dev\raw\`、wiki は同じ `wiki\` | 13 |
| V | SemaSynth MVP 設計の敵対的レビュー | 同上 | 42 |

### 資料を選んだ理由

- **前日の机上の試案と同じ 3 本にした。** 4 体の検討で C（GPT-6.1 Sol）と D（GPT-6 Astra）が、この 3 本で配置の試案を作っている（[C.md](../2026-11-08-wiki-note-granularity-atomic-evergreen/results/C.md) の第 6 節、[D.md](../2026-11-08-wiki-note-granularity-atomic-evergreen/results/D.md)）。PoC の結果を、机上の試案と突き合わせられる。
- **O は「既存の用語ページを更新するか、新しく作るか」を試す。** W0 には、O から作ったコンセプト（`オントロジー`、`オープンワールド仮定`、`rdf-rdfs-owl`）が既にある。英語の原本なので、引用の照合が英語でも働くかも確かめられる。
- **R と V は「何もないところから concept を作るか」を試す。** SemaSynth の wiki は source 28 本、concept 0 本、entity 0 本である。併用案の狙い（source に溜まる知見を concept に出す）が働くかと、全件を `source_only` にして一致率を稼いでいないかを、ここで見る。R と V は、再現性の判定と改変検出という同じ話題に、条件の違う記述で触れている。条件を落とした統合（レポートの第 7 節の反例 1、2）が起きるかを見られる。
- R は 13 行と短く、V は表と箇条書きを含む 42 行である。長さと形式の違う SemaSynth の記録を 2 本にした。

## スナップショット

`scripts/build_snapshots.py` で、実際の wiki を読み、複製を作った。実際の wiki には書いていない。ハッシュは [snapshots/manifest.json](snapshots/manifest.json) にある。複製そのものは、作者の wiki の内容を含むのでリポジトリに入れていない。

| スナップショット | 元 | 抜いたもの | 使う資料 |
| --- | --- | --- | --- |
| `w0` | `~/info-hive/W0_Wiki/` | O の source ページと索引の行。この PoC の題材を論じたシンセシス 2 本（記事の単位、方法論の提案）と索引の行 | O |
| `semasynth` | `C:\works\semasynth-dev\wiki\` | R と V の source ページと索引の行 | R、V |

- どちらも、`log.md` を前文だけに切り詰め、`graph/`、`.wiki-cache/`、`.evolution/` を除いた。原本は取り込む資料だけを置いた。
- 規約は `_rules/` に、サブモジュール `info-hive-wiki`（`6031e80`）の `ingest-workflow.md` と `page-conventions.md` を写した。
- O の source ページを抜いても、O から作ったコンセプトの `sources:` と、連載のほかの回の source からのリンクは残る。O は「取り込み直し」に近い条件になる。R と V の source ページも、`semasynth会計データの再検証-2026-11-06` などからリンクされている。

## 方式

- **現行**: `ingest-workflow.md` の手順 4〜7 を書かれているとおりに適用し、書く代わりに計画を出す。
- **併用案**: [procedure-hybrid.md](procedure-hybrid.md) に従う。レポートの第 4 節と第 6 節から書き起こした。レポートが決めていない行き先の分け方（用語ページの `###` の節か、`kind: "claim"` のページか）は補い、補った箇所に印を付けた。レポートの例のうち PoC の資料から作られたものは、答えを先に示すことになるので、関係のない分野（消費税）の例に差し替えた。

依頼文は [prompt-template.md](prompt-template.md) から作り、方式の節だけが違う。資料と方式の組ごとの依頼文は [prompts/](prompts/) にある。同じ組の 6 件（2 モデル × 3 回）は、同じ依頼文を使う。

両方式とも、出力は同じ JSON の形（知見、条件、根拠の行と引用、行き先、理由）にした。そのため現行の対照は「現行の規則 + 構造化した出力」であり、ふだんの `/wiki:ingest` そのものではない。

## 設計の変更（パイロットのあと、本番の前）

最初は、モデルがスナップショットのファイルをツールで読む形にしていた。パイロットで次のことが起き、**wiki のファイルと原本をすべて依頼文に埋め込み、両モデルともツールなしで答えさせる形**に変えた。

- Claude Opus 5.5 は、ツールで読む形で正常に動いた（R、併用案、候補 18 件、1.73 USD、319 秒）。
- GPT-6.1 Sol は、Codex の Windows のサンドボックスがコマンドを起動できず（`runner handshake task failed`）、ファイルを 1 つも読めなかった。Claude Code の Bash のサンドボックスの中から起動したとき（907 秒）も、ユーザーのターミナルから起動したとき（1,468 秒）も同じだった。どちらも候補 0 件で、モデル自身が「読めなかった」と報告した。読めないまま推測で埋めた計画はなかった。
- サンドボックスを外して Codex を起動することは、権限の判定で拒まれた。

埋め込みにした影響は次のとおりである。

- 36 件の入力が、資料と方式の組ごとにバイト単位で同じになる。ツールの信頼性の差が結果に混ざらない。
- 一方で、`ingest-workflow.md` の手順 4 の「どのページを読むかを選ぶ」部分が試されない。モデルは wiki の全文を最初から見ている。実際の取り込みより一致しやすい条件なので、**一致率は実際の取り込みでの上限の目安**として読む。読んだページ数は、モデルの自己申告（`pages_read`）だけになる。
- 埋め込んだのは、スナップショットの wiki と規約の Markdown（O は 35 本、R と V は 34 本）と、取り込む原本 1 本である。原本の各行には `L<番号>| ` を付けた。依頼文は 1 本 7 万〜9 万文字である。
- パイロットの 2 件（ツールで読む形の Opus と、失敗した Sol）は本番に数えない。記録はリポジトリの外の `pilot-tools/` と `pilot-failed/` に残した。
- 埋め込みの形に変えたあと、`R-hybrid-opus-1` と `R-hybrid-sol-1` を先に走らせて動作を確かめた。本番と同じ依頼文なので、この 2 件は 36 件に含めた。のちに R と V を走らせ直したので、この 2 件も退避した（次の節）。

## R と V の走らせ直し（PR のレビューのあと）

PR #52 への Codex のレビューで、R と V の依頼文に、もう一方の原本が混ざっていたと分かった。R と V は同じ `semasynth` のスナップショットを使い、その `raw/` には両方の原本がある。最初の `embed_files` は、取り込む原本だけを「wiki のファイル」から除いていたので、R の依頼文に V の原本の全文が、V の依頼文に R の原本の全文が入った。O のスナップショットには O の原本しかないので、O の依頼文は影響を受けていない（全文の sha256 が修正の前後で同じ）。

- `embed_files` を、原本のフォルダー（`raw/`、`W1_Raw/`）の中身を wiki のファイルとして埋め込まないように直した。
- R と V の 24 件を走らせ直した。最初の 24 件は、リポジトリの外の `superseded/20261109-095135/` に退避した。本番の数には入れない。
- 依頼文が変わった組に既存の結果があれば、黙って上書きせずに止まるようにした（`--supersede` で退避してから走らせ直す）。

## 実行

- `scripts/run_poc.py` で走らせた。CLI の呼び出しは `multi-agent-dispatch` スキルの `dispatch.py` から写した。
- Claude Opus 5.5 は `claude -p`（Claude Code 2.1.316）、`--permission-mode dontAsk`、`--strict-mcp-config`（MCP なし）、ファイルの読み書きとコマンドのツールはすべて禁止にした。
- GPT-6.1 Sol は `codex exec`（codex-cli 0.166.0）、`-s read-only`、`--skip-git-repo-check`。
- effort はすべて high。毎回新しいセッションで、ほかの回の結果は渡していない。
- 作者の全体の指示（`~/.claude/CLAUDE.md`、`~/.codex/AGENTS.md`）は、実際の W0 の wiki を先に読むよう求めている。依頼文で「この作業の wiki は依頼文に載せたものだけ」と断り、ツールの呼び出しがあればその中のパスを `outside_snapshot` に記録した。
- 実際の wiki と原本のフォルダー 4 つのハッシュを、埋め込みの形の 36 件の前と後、R と V の走らせ直しの前と後に取り、どれも同じだった（[snapshots/real-wiki-hashes.json](snapshots/real-wiki-hashes.json)、`scripts/hash_real_wikis.py`）。ツールで読む形のパイロット（Opus 1 件と、コマンドを 1 つも起動できなかった Sol 1 件）は、最初のハッシュより前に走った。Opus は読むツールだけ、Sol は読み取り専用のサンドボックスだった。

### 事前に決めた、人が確かめる点

パイロットの Opus の計画で、主張のページのスラッグが長い文になり、英字が小文字に崩れていた（`python-audit-hookによる通信禁止は作動を先に確かめて試行ゼロを記録しpythonプロセス内の制御として扱う`）。命名の規則どおりではあるが、題名とスラッグが長すぎて同じページかの対応づけが難しくなる。結果を見る前に、確かめる点として記録しておく。

## ファイル

| パス | 内容 |
| --- | --- |
| `procedure-hybrid.md` | 併用案の手順書（全 18 件で同じ版） |
| `prompt-template.md`、`prompts/` | 依頼文。`prompts/` は埋め込む前の部分と、全文の sha256 |
| `snapshots/manifest.json` | スナップショットと原本と規約のハッシュ |
| `snapshots/real-wiki-hashes.json` | 実際の wiki と原本のフォルダーの、実行の前後のハッシュ（前後で同じ） |
| `runs/<run_id>.json` | 1 件ごとの結果。使用量、監査、計画の行き先と根拠の行。候補の本文と引用は落とし、ハッシュだけを残した |
| `metrics/mechanical.md`、`metrics/mechanical.json` | 機械で出した指標 |
| `mapping/` | 人が対応づけるための表の写しと、埋め方（[mapping/README.md](mapping/README.md)） |
| `scripts/build_snapshots.py` | スナップショットの作成 |
| `scripts/run_poc.py`、`scripts/run_batch.ps1` | 実行 |
| `scripts/tabulate.py` | 機械の指標と対応づけの表の作成 |
| `scripts/metrics_from_mapping.py` | 人の対応づけからの一致率と合否 |
| `scripts/hash_real_wikis.py` | 実際の wiki のハッシュ |

リポジトリの外（`%USERPROFILE%\info-hive-dev-private\2026-11-09-wiki-note-granularity-poc\`）に、依頼文の全文、引用を伏せない結果、CLI の生の出力、人が埋める表、原文の行番号つきの写し、パイロットの記録を置いた。O の原文（Medium の会員限定記事）、R と V の原文（リモートのない SemaSynth のプロジェクトの記録）、作者の wiki の全文を、公開リポジトリに載せないためである。`run_batch.ps1` のスナップショットの既定の場所は、このセッションの一時フォルダーである。作り直すときは `build_snapshots.py --out` で作り、`--snapshot-root` で渡す。
