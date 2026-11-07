# browse の実装前の PoC（ADR-0010）

このディレクトリは配布対象ではない。ADR-0010 の「見直す条件」が挙げる、実装前の PoC の 5 項目を確かめるための試作である。
結果と判断の材料は [docs/research/wiki-browse-adr-0010-poc-2026-11-07.md](../../docs/research/wiki-browse-adr-0010-poc-2026-11-07.md) にまとめた。

wiki のコードは、サブモジュールの固定版（wiki 0.6.0、`36a4089`）を `out/wiki-src/` に取り出して使う。`out/` は Git の対象から外してある。

## ファイル

| ファイル | 中身 |
| --- | --- |
| `make_fixture.py` | 試験用の Wiki を `out/fixture-wiki/` に作る。日本語と空白を含む名前、重複したスラッグ、未解決のリンク、見出しのアンカー、ext4 の上限を超える長い名前、`raw:` の絶対パスを含む |
| `page_sets.py` | lint と search の `collect_pages()` が返すページの集合を比べる（未決 1） |
| `gen.py` | 中核と静的 HTML の生成器の試作。lint の `collect_pages()`、`clean_link_target()`、`resolve_link()` をそのまま使う。生成の記録は出力の外（`<出力先>.build-report.json`）に書き、出力に Wiki のルートの絶対パスが残っていないかを調べる |
| `static/` | 生成器が書き出す `app.js`（ナビゲーションと検索）と `style.css`（日本語の CSS） |
| `names_check.py` | `gen.py` の `export_name()` を、Codex のレビューが挙げた反例（接尾辞の形の名前、`.html` で終わるディレクトリ、予約名）で確かめる（未決 3） |
| `serve.py` | サーバーのアダプタの試作。127.0.0.1、パスの先頭のトークン、Host の確認、GET だけ |
| `static-test/probe.js` | 3 方式で同じ検査をするために、ページに差し込んで状態を取り出すスクリプト |
| `test.mjs` | 同じ出力を `file://` とサーバーで開き、Chromium、Firefox、WebKit、Edge、Chrome で同じ手順を踏む |
| `mcp_origin_probe.py` | wiki の MCP サーバー（ADR-0012）に、アダプタとブラウザのページからつなげるかを確かめる（未決 4） |
| `webkitgtk_probe.py` | WSL の Ubuntu の WebKitGTK 4.1 で、`file://` の読み込みと日本語の CSS を確かめ、スクリーンショットを撮る |
| `static-test/kinsoku.html` | 幅を 8em から 30em まで変えながら、行頭と行末の禁則の違反を数えるページ。対照に `line-break: anywhere` を置く |
| `kinsoku.mjs`、`webkitgtk_kinsoku.py` | `kinsoku.html` を Playwright の各エンジンと WebKitGTK で開いて数える |
| `app/` | Tauri 2 の最小のアプリ。独自スキーム `wiki` で同じ出力を配り、同じ手順を踏む |

## 再実行

リポジトリのルートで実行する。127.0.0.1 への接続を使うので、サンドボックスでは拒まれることがある。

```bash
cd poc/browse
mkdir -p out/wiki-src && git -C ../../info-hive-wiki archive 36a4089 skills/info-hive/scripts | tar -x -C out/wiki-src
python -X utf8 make_fixture.py
python -X utf8 page_sets.py out/fixture-wiki ~/info-hive/W0_Wiki
uv run --script gen.py out/fixture-wiki out/static
uv run --script gen.py out/fixture-wiki out/static-rawfull --raw full
uv run --script gen.py ~/info-hive/W0_Wiki out/static-w0
uv run --script names_check.py
npm install && npx playwright install chromium firefox webkit
node test.mjs
BROWSERS=msedge node test.mjs out/results/msedge.json
BROWSERS=chrome node test.mjs out/results/chrome.json
node kinsoku.mjs
python -X utf8 mcp_origin_probe.py
```

サブモジュールが空の worktree では、`git -C` に本体のチェックアウトの `info-hive-wiki` を渡す。

WebKitGTK は WSL の Ubuntu 24.04 で動かす。

```bash
sudo apt-get install -y gir1.2-webkit2-4.1 python3-gi python3-gi-cairo fonts-noto-cjk xvfb
xvfb-run -a -s "-screen 0 1280x1024x24" python3 webkitgtk_probe.py out/static out/results/webkitgtk.json out/results/webkitgtk.png
xvfb-run -a python3 webkitgtk_kinsoku.py out/results/kinsoku-webkitgtk.json
```

Tauri のアプリの手順は `app/README.md` にある。
