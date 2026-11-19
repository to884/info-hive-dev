// 実際の browse サーバーで、描画枠の寿命と、接続されたページでのコード表示を確かめる。
// BROWSERS、BROWSE_PYTHON、OUT は figures.test.mjs と同じ。
import assert from "node:assert/strict";
import { spawn, spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, realpathSync, rmSync, writeFileSync } from "node:fs";
import { createServer } from "node:http";
import { tmpdir } from "node:os";
import { basename, dirname, join } from "node:path";
import { createInterface } from "node:readline";
import { fileURLToPath } from "node:url";
import { chromium, firefox, webkit } from "playwright";

const script = fileURLToPath(new URL("../../../info-hive-wiki/skills/info-hive/scripts/wiki_browse.py", import.meta.url));
const [python, ...pythonArgs] = (process.env.BROWSE_PYTHON || "uv run --python 3.12 --with pyyaml==6.0.3 python").split(/\s+/);
const temp = realpathSync(tmpdir());
const work = mkdtempSync(join(temp, "wiki-peer-isolation-"));
const wiki = join(work, "wiki");
const env = { ...process.env, PYTHONUTF8: "1", INFO_HIVE_DATA_DIR: join(work, "data") };
const frameSelector = "iframe.fig-frame";
const codeSelector = "#_body pre > code.language-mermaid";
const imageSelector = '#_body figure[data-fig="mermaid"] img';
const frameLock = "info-hive-browse-figure";
const engines = {
  chromium: [chromium], firefox: [firefox], webkit: [webkit],
  msedge: [chromium, { channel: "msedge" }], chrome: [chromium, { channel: "chrome" }],
};
const requestedEngines = (process.env.BROWSERS || "chromium").split(",");
const results = { runs: [], failures: [] };

function fixture() {
  mkdirSync(wiki);
  writeFileSync(join(wiki, "SCHEMA.md"), "# スキーマ\n", "utf8");
  writeFileSync(join(wiki, "index.md"), "# 索引\n\n- [[article]]\n", "utf8");
  writeFileSync(join(wiki, "article.md"), [
    "---", 'type: "concept"', 'title: "図のある記事"', "created: 2026-11-17", "updated: 2026-11-17", "---",
    "", "# 図のある記事", "", "```mermaid", "flowchart LR", '  A["入力"] --> B["確認"]', "```", "",
    "```mermaid", "flowchart LR", '  C["集計"] --> D["表示"]', "```", "",
  ].join("\n"), "utf8");
}

async function ready(child) {
  let error = "";
  child.stderr.setEncoding("utf8").on("data", (chunk) => { error += chunk; });
  const stdout = createInterface({ input: child.stdout });
  let timer;
  try {
    const report = await new Promise((resolve, reject) => {
      child.once("error", reject);
      child.once("exit", (code) => reject(new Error(`serve が終わった（${code}）: ${error}`)));
      stdout.once("line", (line) => {
        try { resolve(JSON.parse(line)); } catch (cause) { reject(cause); }
      });
      timer = setTimeout(() => reject(new Error("serve が URL を出さない: " + error)), 60000);
    });
    assert.equal(report.reused, false);
    return new URL("article.html", report.url).href;
  } finally {
    clearTimeout(timer);
    stdout.close();
    child.stdout.resume();
  }
}

async function checkStandalone(page, url, throughIndex = false) {
  await page.addInitScript((selector) => {
    const frames = new Set();
    window.figureFrames = { peak: 0, created: 0, removed: 0 };
    new MutationObserver((records) => {
      for (const entry of records) {
        for (const node of entry.removedNodes) {
          if (frames.delete(node)) window.figureFrames.removed++;
        }
        for (const node of entry.addedNodes) {
          if (node.nodeType === Node.ELEMENT_NODE && node.matches(selector)) {
            frames.add(node);
            window.figureFrames.created++;
            window.figureFrames.peak = Math.max(window.figureFrames.peak, frames.size);
          }
        }
      }
    }).observe(document, { childList: true, subtree: true });
  }, frameSelector);
  if (throughIndex) {
    await page.goto(new URL("index.html", url).href);
    await page.locator("#_main").getByRole("link", { name: "図のある記事" }).first().click();
    await page.waitForURL(url);
  } else {
    const response = await page.goto(url);
    assert.equal(response.headers()["cross-origin-opener-policy"], "same-origin");
  }
  const images = page.locator(imageSelector);
  await images.nth(1).waitFor({ state: "visible" });
  const dimensions = await images.evaluateAll((nodes) => Promise.all(nodes.map(async (node) => {
    await node.decode();
    return [node.naturalWidth, node.naturalHeight];
  })));
  assert.equal(dimensions.length, 2);
  assert.ok(dimensions.every(([width, height]) => width > 0 && height > 0));
  assert.deepEqual(await page.evaluate(() => window.figureFrames), { peak: 1, created: 2, removed: 2 });
  assert.equal(await page.locator(frameSelector).count(), 0);
}

async function checkConnected(context, page, url, kind, foreignUrl) {
  // 開き元は通常の記事として表示でき、開いた側だけがコード表示になる。
  if (kind === "opener") await checkStandalone(page, url);
  if (kind === "foreign-opener") await page.goto(foreignUrl);
  const frameRequests = [];
  context.on("request", (request) => {
    if (new URL(request.url()).pathname.startsWith("/_frame/")) frameRequests.push(request.url());
  });
  let articles;
  if (kind === "embedded") {
    await page.evaluate((src) => {
      for (let i = 0; i < 2; i++) {
        const frame = document.createElement("iframe");
        frame.src = src;
        document.body.append(frame);
      }
    }, url);
    const elements = await page.locator("iframe").elementHandles();
    assert.equal(elements.length, 2);
    articles = await Promise.all(elements.map((element) => element.contentFrame()));
  } else {
    const opened = context.waitForEvent("page");
    await page.evaluate((href) => { window.open(href); }, url);
    articles = [await opened];
  }
  for (const article of articles) {
    assert.ok(article, "記事を開けない");
    // 同期スクリプトの実行を含め、記事の読み込みが終わってから観測する。
    await article.waitForURL(url, { waitUntil: "load" });
    assert.equal(await article.evaluate(() => window.parent !== window), kind === "embedded");
    assert.equal(await article.evaluate(() => Boolean(window.opener)), kind === "opener");
    assert.equal(await article.locator(codeSelector).count(), 2);
    assert.equal(await article.locator(imageSelector).count(), 0);
    assert.equal(await article.locator(frameSelector).count(), 0);
  }
  assert.deepEqual(frameRequests, []);
}

async function checkLock(context, page, url) {
  // 同じオリジンの別タブが先にロックを保持している間は、図の枠を作れない。
  await page.goto(new URL("index.html", url).href);
  await page.evaluate((name) => new Promise((acquired, reject) => {
    navigator.locks.request(name, () => new Promise((release) => {
      window.releaseFigureLock = release;
      acquired();
    })).catch(reject);
  }), frameLock);
  const other = await context.newPage();
  await other.goto(url);
  await other.waitForFunction(async (name) => (await navigator.locks.query()).pending.some((lock) => lock.name === name), frameLock);
  assert.equal(await other.locator(frameSelector).count(), 0);
  assert.equal(await other.locator(codeSelector).count(), 2);
  await page.evaluate(() => window.releaseFigureLock());
  await other.locator(imageSelector).nth(1).waitFor({ state: "visible" });
  assert.equal(await other.locator(frameSelector).count(), 0);
}

async function checkWithoutLocks(page, url) {
  await page.addInitScript(() => {
    Object.defineProperty(navigator, "locks", { value: undefined });
  });
  const frameRequests = [];
  const scriptLoaded = page.waitForResponse((response) => new URL(response.url()).pathname.endsWith("/assets/figures.js"));
  page.on("request", (request) => {
    if (new URL(request.url()).pathname.startsWith("/_frame/")) frameRequests.push(request.url());
  });
  await page.goto(url);
  assert.equal((await scriptLoaded).status(), 200);
  assert.equal(await page.locator(codeSelector).count(), 2);
  assert.equal(await page.locator(frameSelector).count(), 0);
  assert.deepEqual(frameRequests, []);
}

async function checkRelease(context, page, url, kind) {
  // 描画枠の読み込みだけを失敗させ、停止操作の前まで枠とロックが残る状態にする。
  await page.route("**/_frame/**/mermaid-frame.html", (route) => route.abort(), { times: 1 });
  await page.goto(url);
  const originalFrame = await page.locator(frameSelector).elementHandle();
  const other = await context.newPage();
  await other.goto(url);
  await other.waitForFunction(async (name) => (await navigator.locks.query()).pending.some((lock) => lock.name === name), frameLock);
  assert.equal(await other.locator(frameSelector).count(), 0);
  if (kind === "theme-release") {
    await page.evaluate(() => { document.documentElement.dataset.theme = "dark"; });
  } else {
    // 元の文書が残る場合にも、pagehide の処理が枠とロックを片付けることを確かめる。
    await page.evaluate(() => window.dispatchEvent(new PageTransitionEvent("pagehide", { persisted: true })));
  }
  await other.locator(imageSelector).nth(1).waitFor({ state: "visible", timeout: 10000 });
  assert.equal(await originalFrame.evaluate((frame) => frame.isConnected), false);
}

async function waitForClose(closed, delay) {
  let timer;
  try {
    return await Promise.race([closed.then(() => true), new Promise((resolve) => {
      timer = setTimeout(() => resolve(false), delay);
    })]);
  } finally {
    clearTimeout(timer);
  }
}

let server;
let serverClosed;
const foreignServer = createServer((_request, response) => {
  response.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
  response.end("<!doctype html><title>開き元の試験ページ</title>");
});
const cases = ["standalone", "index-link", "embedded", "opener", "foreign-opener", "lock", "without-locks",
  "theme-release", "pagehide-release"];
try {
  fixture();
  server = spawn(python, [...pythonArgs, "-B", "-X", "utf8", script, "serve", wiki, "--no-open"], {
    env, stdio: ["ignore", "pipe", "pipe"],
  });
  serverClosed = new Promise((resolve) => server.once("close", resolve));
  const url = await ready(server);
  await new Promise((resolve, reject) => {
    foreignServer.once("error", reject);
    foreignServer.listen(0, "127.0.0.1", resolve);
  });
  const foreignUrl = `http://127.0.0.1:${foreignServer.address().port}/`;
  for (const engine of requestedEngines) {
    const [type, options] = engines[engine];
    const browser = await type.launch(options);
    try {
      for (const kind of cases) {
        const context = await browser.newContext();
        try {
          const page = await context.newPage();
          if (kind === "standalone" || kind === "index-link") await checkStandalone(page, url, kind === "index-link");
          else if (kind === "lock") await checkLock(context, page, url);
          else if (kind === "without-locks") await checkWithoutLocks(page, url);
          else if (kind.endsWith("-release")) await checkRelease(context, page, url, kind);
          else await checkConnected(context, page, url, kind, foreignUrl);
          results.runs.push({ browser: engine, version: browser.version(), case: kind, ok: true });
        } catch (error) {
          results.failures.push(`${engine}/${kind}: ${error.stack || error}`);
        } finally {
          await context.close();
        }
      }
    } finally {
      await browser.close();
    }
  }
} catch (error) {
  results.failures.push(String(error.stack || error));
} finally {
  if (foreignServer.listening) await new Promise((resolve) => foreignServer.close(resolve));
  if (server) {
    const stop = spawnSync(python, [...pythonArgs, "-B", "-X", "utf8", script, "stop", wiki], {
      env, encoding: "utf8", timeout: 20000,
    });
    if (stop.status !== 0) {
      results.failures.push("サーバーを停止できない: " + (stop.stderr || stop.error));
    }
    if (!(await waitForClose(serverClosed, 2000))) {
      results.failures.push("サーバーの終了を確認できなかった");
      if (process.platform === "win32" && server.pid) {
        // uv から起動した Python も含め、この試験が起動したプロセスだけを終了する。
        spawnSync("taskkill.exe", ["/PID", String(server.pid), "/T", "/F"], { windowsHide: true, timeout: 10000 });
      } else {
        server.kill();
      }
      await waitForClose(serverClosed, 2000);
    }
  }
  try {
    const absolute = realpathSync(work);
    assert.equal(dirname(absolute), temp);
    assert.ok(basename(absolute).startsWith("wiki-peer-isolation-"));
    rmSync(absolute, { recursive: true, force: true, maxRetries: 3 });
  } catch (error) {
    results.failures.push("試験用ディレクトリを削除できない: " + error.message);
  }
}
if (process.env.OUT) writeFileSync(process.env.OUT, JSON.stringify(results, null, 2) + "\n", "utf8");
console.log(JSON.stringify({ runs: results.runs.length, failures: results.failures.length }));
for (const error of results.failures) console.error(error);
process.exitCode = results.failures.length === 0 && results.runs.length === requestedEngines.length * cases.length ? 0 : 1;
