# ADR-0022：利用者向けの文書は、各プラグインの `docs/` に、Fluent 2 の見た目の HTML で直接書く

| 項目 | 内容 |
| --- | --- |
| 状態 | 承認 |
| 決定日 | 2026年11月15日 |
| 配置の追記 | 2026年11月21日。利用者向け HTML とその表示用アセットを `docs/html/` にまとめる |
| 決定者 | info-hive の開発者（このリポジトリの作者） |
| 関連 | 移植計画 `docs/porting-plan.html` の P0（docs は Markdown だけを残す）、ADR-0003（プラグインごとにリポジトリを分ける）、ADR-0021（`/wiki:browse` の Fluent 2。to884/info-hive-dev#105 で提案中）、[利用者向け文書の計画](../plans/usage-docs-2026-11-15.md) |

## 背景

`info-hive-wiki/docs/` は、移植元 llm-wiki-plugin の文書の訳がもとである。移植計画の P0 では、移植元の文書サイト（VitePress）の仕組みを削り、`docs/` の Markdown だけを残すと決めた。`info-hive-wiki/UPSTREAM.md` も、その理由を「docs サイトを持たず、`docs/` の Markdown だけを残すため」と書いている。

作者は、info-hive のプラグインの使い方を、まったく知らない人に説明する文書を作りたいと考えた。読者は Claude Code を使ったことはあるが、Python、uv、GitHub の認証には詳しくない。今の文書にはチュートリアルがなく、前提条件の記述も実態と合わない（計画の「背景」）。作者は、文書の種類を Diátaxis で分け、HTML と PDF で読めるようにしたいと考え、見た目を Fluent 2 の Web 版に寄せることを選んだ。

置き場所と形式には、次の制約がある。

- `docs/commands.md` は、`/wiki:help <コマンド>` が実行時に読み、`` ## `/wiki:<名前> ...` `` の節を詳しいヘルプとして出す（`skills/info-hive/scripts/wiki_help.py`、`tests/wiki/test_help_command.py`）。消すことも、Markdown 以外にすることもできない。
- AGENTS.md は、サブモジュールのリポジトリに開発に関わるファイルを置かないとしている。HTML と PDF を作る道具（Vivliostyle の設定など）は、開発の道具である。
- `/wiki:browse` の画面も Fluent 2 にする設計（ADR-0021）が進んでいる。同じスキルの `fluent2.css` を、書き換えずに同梱する決まりである。

## 決定

| 項目 | 決定 |
| --- | --- |
| 置き場所 | プラグインごとのリポジトリの `docs/html/`。プラグインをまたぐページ（概要、導入、用語集、トラブルシューティング）は、利用者が必ず入れる `info-hive-wiki/docs/html/` に置く。ほかのプラグインの文書は共通のページにリンクする |
| 形式 | 利用者向けのページは、HTML を直接書く。`docs/commands.md` は、`/wiki:help` のために Markdown の正本として残す |
| 見た目 | スキル `fluent2-html-replica` の `fluent2.css` を書き換えずに `docs/html/assets/` に写す。版は `/wiki:browse` の同梱（ADR-0021）とそろえ、出どころ、基準の版、SHA-256、写し直す手順を `docs/html/assets/README.md` に、ライセンスの文書を `docs/html/assets/licenses/` に置く。独自の装飾は、トークンの CSS 変数だけで書く |
| スクリプト | `fluent2.js` は使わない |
| 図 | 要る所だけ、HTML に埋め込んだ SVG で描く。色と書体は Fluent 2 のトークンに合わせる |
| 文体 | です・ます体。`docs/commands.md` と、`/wiki:help` が説明を読む `commands/*.md` の frontmatter も、です・ます体に書き直す |
| 道具 | HTML から PDF を作る道具とリンクの検査は、開発用のリポジトリ（info-hive-dev）に置く。道具（PDF の作り方）と公開先は、1 ページの試作のあとで決める |
| 既存の文書 | `index.md`、`getting-started.md`、`workflows.md`、`upgrade.md` は、新しいページに中身を移して消す。`upstream-changelog.md` は開発の記録として info-hive-dev に移す。上級の機能の文書（`search.md`、`graph.md`、`decisions.md`、`evolution.md`）と `agents.md` は、当面 Markdown のまま残す |

移植計画の P0 の決定のうち、「docs は Markdown の文書だけを残す」の部分を、この ADR で置き換える。移植元のサイトの仕組み（VitePress、`docs/.vitepress/`、`docs/public/`）を削ったことは変えない。

## 理由

- **各プラグインの `docs/` に置くと、リポジトリの中では、文書とプラグインの版がそろう。** 文書はコマンドの使い方を説明するので、コマンドを変えた PR で文書も直せる。開発用のリポジトリに置くと、プラグインの版と文書の版がずれる。ただし、利用者が読む公開先で版がそろうかは、公開先しだいである。最新の版だけを配る公開先では、古い版のプラグインの `/wiki:help` から新しい版の説明が開く。公開先を決めるときに、版の対応をどうするかを決め、この ADR に書き足す。
- **共通のページを wiki に置くのは、rag が wiki に依存し、利用者が必ず wiki を入れるためである。** マーケットプレイスのリポジトリは、定義だけを置く決まり（ADR-0003）なので使わない。2 か所に写すと、直し続ける手間が倍になる。
- **HTML を直接書くのは、Fluent 2 の部品のマークアップをそのまま使うためである。** Markdown から変換すると、部品の class と構造を、変換の規則で表すことになる。代わりに、GitHub の上ではソースのまま表示されるので、公開先を決める必要がある（試作のあとで決める）。
- **`commands.md` を Markdown のまま残すのは、`/wiki:help` が読むためである。** 仕組みを変えずに済む。
- **`fluent2.css` の扱いを browse とそろえると、出どころを 1 つの手順で確かめられる。** `fluent2.js` は要素の `style` に書き込む。文書のページには、それに頼るふるまいがない。
- **開発の道具を info-hive-dev に置くのは、サブモジュールに開発のファイルを置かない決まりのためである。** HTML と、そこから作る PDF は、利用者が読むものなので、プラグインに置いてよい。

## 検討した選択肢

| 選択肢 | 採らなかった理由 |
| --- | --- |
| 文書を info-hive-dev の `docs/guide/` に置く | 作者が、プラグインごとの `docs/` を選んだ。プラグインの版と文書の版がずれる |
| 新しいリポジトリ `info-hive-docs` を作る | リポジトリが増え、プラグインの変更と文書の変更を別の PR にすることになる |
| Markdown を正本にし、HTML と PDF を変換で作る | 作者が、HTML を直接書くことを選んだ。Fluent 2 の部品を、変換の規則で表すことになる |
| デジタル庁デザインシステム（DADS）の HTML 版 | 作者が、Fluent 2 を選んだ。browse と同じデザインシステムにそろう |
| browse の `browse_assets/fluent2.css` を文書から直接読む | 公開先（GitHub Pages の `/docs` など）では、`docs/` の外のファイルを読めない |

## 影響

- `info-hive-wiki/docs/` に、HTML のページと `assets/fluent2.css`（約 626KB）が増える。`fluent2.css` は browse の同梱と 2 か所になるので、SHA-256 が一致することを試験で確かめる。
- README、`SKILL.md`、`references/query-workflow.md`、`UPSTREAM.md` から、消した文書へのリンクを張り替える。
- `/wiki:help` の詳しいヘルプが、です・ます体になる。利用者に見える変更なので、wiki の版を上げてリリースする。
- `wiki_help.py` は、`commands.md` の相対リンクを GitHub のタグの URL に書き換える。リンク先が HTML になると、GitHub ではソースが表示される。公開先を決めたら、書き換えの規則を直すかを決める。直すなら、GitHub のタグの URL を期待する `tests/wiki/test_help_command.py` も一緒に直す。
- Microsoft の製品ではないこと、商標の帰属、Segoe UI を同梱しないことを、`docs/html/assets/README.md` に書く（ADR-0021 と同じ）。

## 参照

- [利用者向け文書の計画](../plans/usage-docs-2026-11-15.md)
- 移植計画 `docs/porting-plan.html` の P0
- ADR-0021（to884/info-hive-dev#105）
