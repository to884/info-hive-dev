// wiki の閲覧（browse）の起動の速さの試験（選択肢のレポートの合格の目安）。
// 1,000 ページの合成 Wiki で、`uv run --script wiki_browse.py serve` の実行から、Chromium で最初のページの描画が
// 終わるまでを測り、5 秒以内であることを確かめる。uv の環境ができていない初回は、別に記録する（合否に入れない）。
// ブラウザは先に起動しておく（利用者のブラウザは、ふつう開いている）。
//
// 使い方: cd tests/wiki/browse && node startup.test.mjs
import { chromium } from "playwright";
import { spawn, spawnSync } from "node:child_process";
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, "..", "..", "..");
const SCRIPT = join(REPO, "info-hive-wiki", "skills", "info-hive", "scripts", "wiki_browse.py");
const LIMIT_MS = Number(process.env.LIMIT_MS || 5000);
const PAGES = Number(process.env.PAGES || 1000);

const work = mkdtempSync(join(tmpdir(), "browse-startup-"));
const wiki = join(work, "wiki");
const env = { ...process.env, INFO_HIVE_DATA_DIR: join(work, "data") };
const kinds = ["concepts", "entities", "sources", "synthesis"];
for (let i = 0; i < PAGES; i++) {
  const kind = kinds[i % kinds.length];
  const dir = join(wiki, kind);
  mkdirSync(dir, { recursive: true });
  const links = [1, 7, 31].map((d) => `[[ページ${(i + d) % PAGES}]]`).join("、");
  writeFileSync(join(dir, `ページ${i}.md`), [
    "---", `type: "${kind.replace(/s$/, "").replace("synthesi", "synthesis")}"`, `title: "ページ ${i}"`,
    'tags: ["合成"]', "---", "", `# ページ ${i}`, "", "## 概要", "",
    `これは合成のページである。関連は ${links} を見る。`.repeat(4), "", "## 詳細", "",
    "| 項目 | 値 |", "| --- | --- |", `| 番号 | ${i} |`, "",
  ].join("\n"), "utf8");
}
// 入口は SCHEMA.md のないディレクトリを断る（ADR-0019）。
writeFileSync(join(wiki, "SCHEMA.md"), "# スキーマ\n", "utf8");
writeFileSync(join(wiki, "index.md"), ["# 索引", "", ...Array.from({ length: PAGES }, (_, i) => `- [[ページ${i}]]`), ""].join("\n"), "utf8");

function serveOnce(browser) {
  return new Promise((ok, fail) => {
    const started = Date.now();
    const child = spawn("uv", ["run", "--script", SCRIPT, "serve", wiki, "--no-open", "--page", "ページ0"],
      { env, stdio: ["ignore", "pipe", "pipe"] });
    let buf = "";
    let err = "";
    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stderr.on("data", (s) => { err += s; });
    child.stdout.on("data", async (s) => {
      buf += s;
      const nl = buf.indexOf("\n");
      if (nl < 0 || buf === null) return;
      const line = buf.slice(0, nl);
      buf = null;
      try {
        const { url } = JSON.parse(line);
        const page = await browser.newPage();
        await page.goto(url, { waitUntil: "load" });
        await page.waitForFunction(() => window.__browse && window.__browse.navLoaded, null, { timeout: 30000 });
        const ms = Date.now() - started;
        await page.close();
        ok({ ms, child });
      } catch (e) { child.kill(); fail(e); }
    });
    child.once("exit", (code) => fail(new Error(`serve が終わった（${code}）: ${err}`)));
  });
}

function stop() {
  spawnSync("uv", ["run", "--script", SCRIPT, "stop", wiki], { env, encoding: "utf8" });
}

const browser = await chromium.launch();
const result = {};
let failed = false;
try {
  const first = await serveOnce(browser);   // uv の環境を作る初回。合否に入れない
  result.firstRunMs = first.ms;
  stop();
  await new Promise((r) => first.child.once("exit", r));
  const times = [];
  for (let i = 0; i < 3; i++) {
    const run = await serveOnce(browser);
    times.push(run.ms);
    stop();
    await new Promise((r) => run.child.once("exit", r));
  }
  result.runsMs = times;
  result.medianMs = times.sort((a, b) => a - b)[1];
  failed = result.medianMs > LIMIT_MS;
} catch (e) {
  result.error = String(e).slice(0, 500);
  failed = true;
} finally {
  await browser.close();
  try { rmSync(work, { recursive: true, force: true }); } catch { /* Windows で掴まれていれば残す */ }
}
console.log(JSON.stringify({ pages: PAGES, limitMs: LIMIT_MS, ...result, ok: !failed }));
process.exit(failed ? 1 : 0);
