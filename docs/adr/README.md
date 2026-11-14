# ADR（設計判断の記録）

info-hive の設計で決めたことと、その理由を残す。1 つの判断を 1 つのファイルに書き、ファイル名は `<4 桁の番号>-<判断を表す英語の短い名前>.md` にする。

| 番号 | 判断 | 状態 | 決定日 |
| --- | --- | --- | --- |
| [0001](0001-local-only-server-is-not-hosted-wiki.md) | 127.0.0.1 だけで待ち受けるサーバーは、方針 G の「ホスト型 wiki」に当たらない | 承認 | 2026年11月3日 |
| [0002](0002-wiki-browse-uses-on-demand-local-server.md) | `/wiki:browse` は、必要なときだけ起動するローカルサーバーで作る | 承認（作る順序と書き出しは 0010 で置き換え済み） | 2026年11月3日 |
| [0003](0003-split-marketplace-repo.md) | マーケットプレイスをプラグインと別のリポジトリに置く | 承認 | 2026年11月3日 |
| [0004](0004-raw-holds-translated-web-pages.md) | Web ページは訳文と図の説明を raw に置き、原文は出所とハッシュで記録する | 承認 | 2026年11月3日 |
| [0005](0005-wiki-figures-use-mermaid-and-svg.md) | 知識ページの図は mermaid を本文に書き、svg は wiki/assets/ に置く | 承認 | 2026年11月3日 |
| [0006](0006-daily-journal-is-separate-plugin.md) | 日々の記録は wiki と別のプラグイン `log` にする | 承認（保存先とノートの置き場所は 0008 で置き換え済み） | 2026年11月3日 |
| [0007](0007-rag-uses-mcp-core-and-persistent-jobs.md) | RAG は MCP、共通コア、永続ジョブで構成する | 承認（モデルの保持と共有、埋め込みと索引更新の実行場所は 0012 で置き換え済み） | 2026年11月3日 |
| [0008](0008-numbered-workspace-layout.md) | info-hive の作業領域は番号付きのディレクトリで構成する | 承認 | 2026年11月4日 |
| [0009](0009-graph-layer-stays-in-wiki.md) | グラフ層は wiki プラグインに残し、別のプラグインにしない | 承認 | 2026年11月4日 |
| [0010](0010-wiki-browse-separates-core-from-delivery.md) | `/wiki:browse` は Wiki を解釈する中核と表示の方式を分け、どの方式でも同じ契約で動かす | 承認（合格の条件の一部は 0016 で置き換え済み） | 2026年11月7日 |
| [0011](0011-shared-embedding-and-index-stack.md) | wiki と rag の埋め込み、ベクトル索引、語彙検索をそろえる | 承認 | 2026年11月6日 |
| [0012](0012-wiki-owns-local-mcp-index-server.md) | wiki が 127.0.0.1 の MCP サーバーを持ち、モデルと索引の唯一の持ち主になる | 承認 | 2026年11月6日 |
| [0013](0013-rag-records-pdfs-by-absolute-path-and-hash.md) | rag は参照ルートを持たず、PDF を絶対パスと内容の SHA-256 で記録する | 承認 | 2026年11月7日 |
| [0014](0014-rag-keeps-extraction-independent-of-embedding.md) | rag は抽出と OCR の結果を、埋め込みと分割の方針から切り離して保存する | 承認 | 2026年11月8日 |
| [0015](0015-wiki-article-methodology-adopted-in-stages.md) | wiki の記事作成の方法論は、提案を一括で入れず、検査と記録から段階を分けて入れる | 承認 | 2026年11月9日 |
| [0016](0016-wiki-browse-stage1-accepts-two-delivery-methods.md) | `/wiki:browse` の第 1 段階は、サーバーと静的 HTML の 2 方式で合格とし、アプリでの確認はアプリを作るときに行う | 承認 | 2026年11月9日 |
| [0017](0017-wiki-browse-changes-only-what-it-created.md) | `/wiki:browse` は、自分が作ったものだけを置き換え、消す。入力の実体は、置き場所によらず Wiki の内容として読む | 承認 | 2026年11月11日 |
| [0018](0018-wiki-requires-python-312.md) | info-hive の wiki の同梱のスクリプトは、Python 3.12 以上を対象にする | 承認 | 2026年11月12日 |
| [0019](0019-wiki-root-is-marked-by-schema.md) | wiki とみなすのは、ルートに SCHEMA.md がある（初期化された）ディレクトリだけにする | 提案 | （承認の日を入れる） |
| [0020](0020-session-raw-is-rendered-once-from-decisions.md) | Claude Code のセッションの raw は、会話だけを抜き出し、人の決定を当てて、スクリプトが 1 回で、重ねて書かない形で作る | 承認 | 2026年11月14日 |

各 ADR には、状態、決定日、決定者、関連を表で書き、続けて背景、決定、理由、検討した選択肢、影響、参照を書く。判断を変えるときは元の ADR を書き換えず、新しい ADR を書いて、元の ADR の状態を「置き換え済み」にする。
