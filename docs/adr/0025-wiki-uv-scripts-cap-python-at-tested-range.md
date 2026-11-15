# ADR-0025：wiki の uv で動くスクリプトは、CI で試す Python の範囲に上限を付ける

| 項目 | 内容 |
| --- | --- |
| 状態 | 承認 |
| 決定日 | 2026年11月15日 |
| 決定者 | info-hive の開発者（このリポジトリの作者） |
| 関連 | ADR-0018（Python 3.12 以上。上限は付けない）、ADR-0012（MCP サーバー）、to884/info-hive-wiki の 0.19.5、[利用者向け文書の段階 2 の確認表](../research/usage-docs-stage2-checklist-2026-11-15.md) |

## 背景

ADR-0018 は、wiki の同梱のスクリプトの対象を Python 3.12 以上とし、上限は付けないと決めた。理由は「3.14 まで試験が通っている」ことで、上限は依存の都合があるときに付けるとした。

利用者向け文書の段階 2 で、Python の入っていない新しい Windows 11 に wiki 0.19.4 を入れると、MCP サーバーが起動しなかった。uv で動くスクリプトは `requires-python = ">=3.12"` で、uv は、使える Python がないと、宣言に合う中でいちばん新しい版を取る。そのとき取ったのは CPython 3.15 で、MCP サーバーの依存の `onnxruntime==1.31.1` には 3.15 の配布物（wheel）がなかった。uv は依存を解決できずに止まった（`No solution found when resolving dependencies`）。開発用の PC には 3.12 が入っていたので、表に出なかった。

上限を付けない決定は、「試験が通った範囲」と「uv が実際に選ぶ範囲」が同じだと見ていた。実際には、uv が選ぶのは、試験より後に出た、まだ誰も試していない版である。依存の配布物は、新しい Python が出てから遅れてそろうので、新しい版ほど失敗しやすい。

## 決定

| 項目 | 決定 |
| --- | --- |
| uv で動くスクリプト | PEP 723 の `requires-python` を、どれも同じ範囲にする。範囲は、プラグインの CI（`info-hive-wiki/.github/workflows/wiki-tests.yml`）の行列で試す版の最小から最大までで、上限は最大の次の minor の未満とする。今は `">=3.12,<3.15"` である |
| 宣言と CI を結ぶ | info-hive-dev の `tests/wiki/test_python_version.py` が、すべての宣言が CI の行列から作った範囲と同じかを確かめる。行列は YAML として読み（各ジョブの `strategy.matrix` の `python` と `include` の項目）、版として読めない値が 1 つでもあれば落ちる。CI の行列に新しい版を足すと、宣言の上限も上げるまで試験が落ちる |
| 範囲のすべての版で依存が入る | プラグインの CI の行列は、範囲の両端の版しか試さず、MCP サーバーの依存を入れない。そこで、info-hive-dev の CI（`wiki-mcp.yml`）が、`tests/wiki/check_script_python_range.py` で、宣言の範囲のすべての minor の版で、uv で動くすべてのスクリプトに `uv sync --script` をかける。1 つでも失敗すれば落ちる |
| 上限を上げるとき | CI の行列に新しい版を足し、上の 2 つの確かめが通ってから、宣言の上限を上げる。どちらも同じ変更で行う |
| `python` で直接動くスクリプト | ADR-0018 のまま、利用者の `python` で動き、上限を付けない。標準ライブラリだけを使うので、依存の配布物の問題は起きない |
| 依存を解決できないとき | 入口と中継は、環境が壊れたとみなさず、入れ直さずに止まり、理由を `logs/launch.log` に書く（`UvResolveError`）。上限があっても、利用者が `UV_PYTHON` などで範囲の外を選んだときには起きうる |
| 環境を用意できないときの記録 | 入れ直しても直らなかった失敗も含めて、理由と uv の出力の要約（`error:`、`cause:`、`hint:` の行）を `logs/launch.log` に書く（`prepare_script`）。終了コードだけでは、Python を取れない、プロキシに断られた、などの理由が分からない |

## 理由

- uv で動くスクリプトの依存の多くは、配布物が Python の版ごとに分かれる（onnxruntime、usearch、tantivy、pydantic-core など）。新しい Python の配布物は、出てからしばらくそろわない。
- 試していない版を選ばせないことで、Python のない PC でも、どの版を取るかが決まる（今は 3.14）。
- すべての宣言を同じ範囲にすると、入口、中継、サーバーで取る Python が 1 つで済む。

## 検討した選択肢

| 選択肢 | 採らなかった理由 |
| --- | --- |
| 上限を付けず、依存の版を上げて新しい Python に追いつく | 新しい Python が出るたびに、配布物がそろうまで、Python のない利用者は起動できない |
| MCP サーバーだけに上限を付ける | `/wiki:init` の `setup_wiki.py`（FastEmbed、onnxruntime）と検索も同じ依存を持つ。スクリプトごとに範囲を変えると、取る Python が増える |
| 上限を、依存の配布物を調べて決める | 依存は多く、配布物は版ごとに変わる。CI で試した範囲なら、試験が通ったことが根拠になる |

## 影響

- ADR-0018 の「上限は付けない」は、uv で動くスクリプトについては、この ADR で置き換わる。`python` で直接動くスクリプトの決定は変わらないので、ADR-0018 は、状態の欄だけを直した。
- 0.19.4 から 0.19.5 への更新のあとの最初の接続で、宣言が変わるので、MCP サーバーの環境を作り直す。3.15 しかない PC では、uv が 3.14 を取る。
- 新しい Python に対応するには、CI の行列と宣言の上限を一緒に上げる変更が要る。
- 範囲の Python が PC になく、uv が Python を取れないとき（`UV_PYTHON_DOWNLOADS=never`、オフライン、取得先への通信の制限）は起動しない。0.19.4 までは、同じ状況でも PC にある新しい版で動くことがあった（依存の配布物がその版にあれば）。Claude Code は入口そのものを `uv run --script` で起動するので、入口の Python を選べない失敗は、プラグインのコードに届く前に起きる。README のトラブルシューティングに、範囲の Python を入れる手順を書く。

## 参照

- `info-hive-wiki/skills/info-hive/scripts/*.py` の PEP 723 の宣言
- `info-hive-wiki/skills/info-hive/scripts/wiki_mcp_common.py`（`UvResolveError`）
- `tests/wiki/test_python_version.py`、`tests/wiki/test_uv_tls.py`
