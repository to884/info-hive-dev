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
| 宣言と CI を結ぶ | info-hive-dev の `tests/wiki/test_python_version.py` が、すべての宣言が CI の行列から作った範囲と同じかを確かめる。CI の行列に新しい版を足すと、宣言の上限も上げるまで試験が落ちる |
| 上限を上げるとき | CI の行列に新しい版を足し、試験が通ってから、宣言の上限を上げる。どちらも同じ変更で行う |
| `python` で直接動くスクリプト | ADR-0018 のまま、利用者の `python` で動き、上限を付けない。標準ライブラリだけを使うので、依存の配布物の問題は起きない |
| 依存を解決できないとき | 入口と中継は、環境が壊れたとみなさず、入れ直さずに止まり、理由を `logs/launch.log` に書く（`UvResolveError`）。上限があっても、利用者が `UV_PYTHON` などで範囲の外を選んだときには起きうる |

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

## 参照

- `info-hive-wiki/skills/info-hive/scripts/*.py` の PEP 723 の宣言
- `info-hive-wiki/skills/info-hive/scripts/wiki_mcp_common.py`（`UvResolveError`）
- `tests/wiki/test_python_version.py`、`tests/wiki/test_uv_tls.py`
