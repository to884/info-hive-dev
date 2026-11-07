# Tauri の独自スキームの PoC（ADR-0010）

配布対象ではない。`gen.py` の出力（`out/static/`）を、Tauri 2 の独自スキーム `wiki` で配り、`test.mjs` と同じ手順を踏む。

- `src/main.rs`：`wiki` スキームのハンドラー。GET だけを受け、パスを UTF-8 でデコードし、`BROWSE_ROOT` の外を拒む。HTML と同じ CSP をヘッダーにも付ける。`/__report` への要求で駆動スクリプトの報告を集め、`BROWSE_RESULT` に JSON で書いて終わる
- `src/driver.js`：初期化スクリプト。`static-test/probe.js` と一緒に差し込み、`sessionStorage` の段階の番号で手順を進める。報告は同じオリジンへの画像の要求で送る（CSP の `img-src 'self'` で許される）。Tauri の IPC は使わない
- `dist/index.html`：`frontendDist` を満たすための空のページ
- 結果の比べ方：`../compare_tauri.mjs`（`test.mjs` の `summarize()` と同じ形を作り、`out/results/browsers.json` の基準と比べる）

## 再実行

Windows（Git Bash）。初回のビルドは crate の取得で約 9 分かかった。

```bash
cd poc/browse/app && cargo build
cd .. && BROWSE_ROOT="$(cygpath -w $PWD/out/static)" BROWSE_RESULT="$(cygpath -w $PWD/out/results/tauri-windows.json)" BROWSE_TIMEOUT=60 ./app/target/debug/browse-poc.exe
node compare_tauri.mjs out/results/tauri-windows.json
```

Linux（WSL の Ubuntu 24.04、WSLg）。`libwebkit2gtk-4.1-dev build-essential libxdo-dev libssl-dev libayatana-appindicator3-dev librsvg2-dev` と rustup が要る。

```bash
cd poc/browse/app && CARGO_TARGET_DIR=~/browse-poc-target cargo build
DISPLAY=:0 GDK_BACKEND=x11 WEBKIT_DISABLE_COMPOSITING_MODE=1 WEBKIT_DISABLE_DMABUF_RENDERER=1 \
  BROWSE_ROOT=<out/static の絶対パス> BROWSE_RESULT=<out/results/tauri-linux.json の絶対パス> ~/browse-poc-target/debug/browse-poc
node ../compare_tauri.mjs out/results/tauri-linux.json
```
