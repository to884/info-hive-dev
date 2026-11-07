// ADR-0010 の PoC。gen.py の同じ出力を file:// とサーバー（serve.py）で開き、
// Chromium、Firefox、WebKit（Playwright）で同じ手順を踏んで結果を比べる。配布対象ではない。
// 使い方: node test.mjs [出力の JSON]
import { chromium, firefox, webkit } from "playwright";
import { spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { readFileSync, readdirSync, statSync, writeFileSync, mkdirSync } from "node:fs";
import { join, resolve, dirname } from "node:path";
import { pathToFileURL, fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const WIKI = join(HERE, "out", "fixture-wiki");
const STATIC = join(HERE, "out", "static");
const STATIC_RAW = join(HERE, "out", "static-rawfull");
const PROBE = readFileSync(join(HERE, "static-test", "probe.js"), "utf8");
const OUT = process.argv[2] || join(HERE, "out", "results", "browsers.json");

function hashTree(dir) {
  const h = createHash("sha256");
  const walk = (d) => {
    for (const name of readdirSync(d).sort()) {
      const p = join(d, name);
      if (statSync(p).isDirectory()) walk(p);
      else h.update(p.slice(dir.length) + "\0").update(readFileSync(p));
    }
  };
  walk(dir);
  return h.digest("hex");
}

function startServer(root) {
  return new Promise((ok, fail) => {
    const child = spawn("python", ["-X", "utf8", join(HERE, "serve.py"), root], { stdio: ["ignore", "pipe", "pipe"] });
    child.stdout.setEncoding("utf8");
    child.stdout.once("data", (line) => ok({ child, ...JSON.parse(line.split("\n")[0]) }));
    child.once("error", fail);
  });
}

async function scenario(browser, base) {
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.addInitScript(PROBE);
  const requests = [];
  const consoleErrors = [];
  page.on("request", (r) => requests.push(r.url()));
  page.on("console", (m) => { if (m.type() === "error") consoleErrors.push(m.text()); });
  page.on("pageerror", (e) => consoleErrors.push(String(e)));
  const steps = {};
  const probe = () => page.evaluate(() => window.__probe());

  await page.goto(base + "index.html");
  steps.index = await probe();
  await page.click("#nav-list a:text-is('ナレッジグラフ')");
  await page.waitForLoadState("load");
  steps.kg = await probe();
  await page.click("article a.wl:text-is('オントロジー#定義')");
  await page.waitForLoadState("load");
  steps.anchor = await probe();
  await page.goBack();
  await page.waitForLoadState("load");
  await page.click("article a.wl:text-is('entities/山田 太郎')");
  await page.waitForLoadState("load");
  steps.entity = await probe();
  await page.fill("#search", "知識表現");
  await page.waitForFunction(() => document.querySelectorAll("#search-results a").length > 0, null, { timeout: 5000 })
    .catch(() => {});
  steps.search = await probe();
  await page.goto(base + encodeURI("concepts/ナレッジグラフ.html"));
  const before = page.url();
  await page.click("article .wl-unresolved");
  await page.waitForTimeout(300);
  steps.unresolvedClickNavigated = page.url() !== before;
  await context.close();
  const origin = base.startsWith("file:") ? "file:" : new URL(base).origin;
  return { steps, external: requests.filter((u) => !u.startsWith(origin)), requestCount: requests.length, consoleErrors };
}

async function rawLink(browser, base) {
  // ADR-0013 の raw: の絶対パスを file:/// のリンクにしたとき、そのページから開けるか。
  const context = await browser.newContext({ acceptDownloads: false });
  const page = await context.newPage();
  const requests = [];
  const consoleErrors = [];
  page.on("request", (r) => requests.push(r.url()));
  page.on("console", (m) => { if (m.type() === "error") consoleErrors.push(m.text()); });
  await page.goto(base + encodeURI("sources/報告書 2026.html"));
  const href = await page.getAttribute("a.raw", "href");
  await page.click("a.raw", { noWaitAfter: true }).catch((e) => consoleErrors.push("click: " + e.message));
  await page.waitForTimeout(1000);
  const pdfRequested = requests.some((u) => u.startsWith("file:") && u.toLowerCase().endsWith(".pdf"));
  await context.close();
  return { href, pdfRequested, consoleErrors: consoleErrors.slice(0, 3) };
}

async function longName(browser, base) {
  // 200 バイトに切り詰めて接尾辞を付けた名前のページを、リンクから実際に開く。
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.addInitScript(PROBE);
  await page.goto(base + encodeURI("concepts/ナレッジグラフ.html"));
  await page.click("article a.wl:text-matches('^長い名前のページ')");
  await page.waitForLoadState("load");
  const p = await page.evaluate(() => window.__probe());
  await context.close();
  return { page: p.page, pageId: p.pageId, navLoaded: p.navLoaded };
}

function summarize(r) {
  const s = r.steps;
  return {
    navLoaded: s.index.navLoaded && s.kg.navLoaded,
    navCount: s.index.navCount,
    kgLinks: s.kg.links.map((l) => `${l.text}|${l.cls}|${l.href}`),
    kgBacklinks: s.kg.backlinks,
    kgDiagnostics: s.kg.diagnostics,
    scriptEscaped: s.kg.scriptEscaped,
    anchorPage: s.anchor.page,
    anchorHash: s.anchor.hash,
    anchorFound: s.anchor.hashTargetFound,
    entityPage: s.entity.page,
    entityBacklinks: s.entity.backlinks,
    searchLoaded: s.search.searchLoaded,
    searchResults: s.search.searchResults,
    unresolvedClickNavigated: s.unresolvedClickNavigated,
  };
}

const wikiBefore = hashTree(WIKI);
const server = await startServer(STATIC);
const serverRaw = await startServer(STATIC_RAW);
const modes = {
  file: pathToFileURL(STATIC).href + "/",
  http: server.url,
};
const rawModes = { file: pathToFileURL(STATIC_RAW).href + "/", http: serverRaw.url };
const results = { generated: new Date().toISOString(), runs: [] };
const ENGINES = [["chromium", chromium], ["firefox", firefox], ["webkit", webkit],
  ["msedge", chromium, { channel: "msedge" }], ["chrome", chromium, { channel: "chrome" }]]
  .filter(([n]) => !process.env.BROWSERS || process.env.BROWSERS.split(",").includes(n));
for (const [name, type, opts] of ENGINES) {
  let browser;
  try { browser = await type.launch(opts || {}); } catch (e) { results.runs.push({ browser: name, error: String(e).slice(0, 200) }); continue; }
  for (const [mode, base] of Object.entries(modes)) {
    let run;
    try {
      const r = await scenario(browser, base);
      run = { browser: name, version: browser.version(), mode, summary: summarize(r), css: r.steps.kg.css,
              cspViolations: [...new Set(Object.values(r.steps).flatMap((s) => (s && s.cspViolations) || []))],
              appErrors: r.steps.index.appErrors, external: r.external, requestCount: r.requestCount,
              consoleErrors: r.consoleErrors.slice(0, 5) };
    } catch (e) {
      run = { browser: name, mode, error: String(e).slice(0, 500) };
    }
    try { run.longName = await longName(browser, base); } catch (e) { run.longName = { error: String(e).slice(0, 300) }; }
    try { run.rawLink = await rawLink(browser, rawModes[mode]); } catch (e) { run.rawLink = { error: String(e).slice(0, 300) }; }
    results.runs.push(run);
  }
  await browser.close();
}
server.child.kill();
serverRaw.child.kill();
const wikiAfter = hashTree(WIKI);
results.wikiUnchanged = wikiBefore === wikiAfter;
const ref = JSON.stringify(results.runs.find((r) => r.summary)?.summary);
results.allEqual = results.runs.every((r) => r.summary && JSON.stringify(r.summary) === ref);
mkdirSync(dirname(OUT), { recursive: true });
writeFileSync(OUT, JSON.stringify(results, null, 2), "utf8");
console.log(JSON.stringify({ allEqual: results.allEqual, wikiUnchanged: results.wikiUnchanged,
  runs: results.runs.map((r) => ({ b: r.browser, m: r.mode, err: r.error, nav: r.summary?.navLoaded,
    csp: r.cspViolations?.length, ext: r.external?.length, search: r.summary?.searchResults?.length,
    anchor: r.summary?.anchorFound, raw: r.rawLink?.pdfRequested })) }, null, 1));
