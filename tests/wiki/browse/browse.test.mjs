// wiki の閲覧（browse）のブラウザでの試験（ADR-0016 の合格の条件）。
// 同じ試験用の Wiki を、静的の書き出し（file://）とサーバー（http://127.0.0.1）で開き、同じ手順を踏んで結果を比べる。
// 1 つでも外れれば、終了コードを 1 にする。
//
// 使い方（開発リポジトリのルートで）:
//   cd tests/wiki/browse && npm ci && node browse.test.mjs
// 環境変数:
//   BROWSE_PYTHON   python を呼ぶコマンド（空白で区切る。既定は "uv run --python 3.12 --with pyyaml==6.0.3 python"）
//   MODES           "static,server"（既定）。片方だけを流すときに使う
//   BROWSERS        "chromium"（既定）。"chromium,firefox,webkit,msedge,chrome" で手で流す試験にする
//   OUT             結果の JSON の書き出し先（既定は書き出さない）
import { chromium, firefox, webkit } from "playwright";
import { spawn, spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdtempSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync, rmSync, cpSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, "..", "..", "..");
const SCRIPT = join(REPO, "info-hive-wiki", "skills", "info-hive", "scripts", "wiki_browse.py");
const CORPUS = join(REPO, "info-hive-wiki", "eval", "retrieval", "ja", "corpus", "wiki");
const PYTHON = (process.env.BROWSE_PYTHON || "uv run --python 3.12 --with pyyaml==6.0.3 python").split(/\s+/);
const MODES = (process.env.MODES || "static,server").split(",");
const ENGINES = { chromium: [chromium], firefox: [firefox], webkit: [webkit],
  msedge: [chromium, { channel: "msedge" }], chrome: [chromium, { channel: "chrome" }] };
const BROWSERS = (process.env.BROWSERS || "chromium").split(",");

const failures = [];
function check(cond, message) { if (!cond) failures.push(message); return cond; }

// --- 試験用の Wiki ---

const work = mkdtempSync(join(tmpdir(), "browse-test-"));
const wiki = join(work, "wiki-ROOTMARK");
const data = join(work, "data-DATAMARK");
function put(rel, text) {
  const p = join(wiki, rel);
  mkdirSync(dirname(p), { recursive: true });
  writeFileSync(p, text, "utf8");
}
cpSync(CORPUS, wiki, { recursive: true });
put("試験/リンク.md", [
  "---", 'type: "concept"', 'title: "リンクの試験 <script>x</script>"', 'tags: ["試験"]', "---", "",
  "# リンクの試験", "", "## 定義", "",
  "[[試験/行き先]] と [[試験/行き先#定義|定義へ]] と [[ない|未解決]] と [[同名]] と `[[コード]]`。", "",
  "[外部](https://example.invalid/page) と [相対](rel/x.md) と [ [[ない2]] ](https://example.invalid/x)。", "",
  "| 左 | 右 |", "| :--- | ---: |", "| 1 | 2 |", "",
].join("\n"));
put("試験/行き先.md", ["---", 'type: "concept"', "---", "", "# 行き先", "", "## 定義", "", "本文。", ""].join("\n"));
put("a/同名.md", "# 同名 A\n");
put("b/同名.md", "# 同名 B\n");
put("index.md", ["# 索引", "", "## 試験", "", "- [[試験/リンク]]", "- [[試験/行き先]]", "- [[ない]]", ""].join("\n"));
put("graph/ontology.yaml", "node_types:\n  concept: {}\npredicates:\n  uses: {}\n");

function hashTree(dir) {
  const h = createHash("sha256");
  const walk = (d) => {
    for (const name of readdirSync(d).sort()) {
      const p = join(d, name);
      const st = statSync(p);
      h.update(p.slice(dir.length) + (st.isDirectory() ? "/" : "") + "\0");
      if (st.isDirectory()) walk(p); else h.update(readFileSync(p));
    }
  };
  walk(dir);
  return h.digest("hex");
}

function python(args, opts = {}) {
  return spawnSync(PYTHON[0], [...PYTHON.slice(1), "-X", "utf8", SCRIPT, ...args],
    { encoding: "utf8", env: { ...process.env, INFO_HIVE_DATA_DIR: data }, ...opts });
}

function startServer() {
  return new Promise((ok, fail) => {
    const child = spawn(PYTHON[0], [...PYTHON.slice(1), "-X", "utf8", SCRIPT, "serve", wiki, "--no-open"],
      { env: { ...process.env, INFO_HIVE_DATA_DIR: data }, stdio: ["ignore", "pipe", "pipe"] });
    let buf = "";
    let err = "";
    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stderr.on("data", (s) => { err += s; });
    child.stdout.on("data", (s) => {
      buf += s;
      const nl = buf.indexOf("\n");
      if (nl >= 0) { try { ok({ child, ...JSON.parse(buf.slice(0, nl)) }); } catch (e) { fail(e); } }
    });
    child.once("exit", (code) => fail(new Error(`serve が終わった（${code}）: ${err}`)));
    setTimeout(() => fail(new Error("serve が URL を出さない: " + err)), 60000);
  });
}

// --- ページの状態を取り出す ---

const PROBE = `(() => {
  const violations = [];
  document.addEventListener("securitypolicyviolation", (e) => violations.push(e.violatedDirective + " " + e.blockedURI));
  window.__probe = () => {
    const base = document.documentElement.getAttribute("data-root") || "";
    const rootUrl = new URL(base || "./", location.href).href;
    const rel = (url) => url && url.indexOf(rootUrl) === 0 ? decodeURIComponent(url.slice(rootUrl.length)) : "EXTERNAL:" + url;
    const texts = (sel) => Array.from(document.querySelectorAll(sel), (n) => n.textContent.trim());
    const hash = decodeURIComponent(location.hash.slice(1));
    const ids = Array.from(document.querySelectorAll("[id]"), (n) => n.id);
    return {
      page: rel(location.href.split("#")[0]), hash,
      hashTargetFound: hash ? !!document.getElementById(hash) : null,
      pageId: (document.querySelector("#_article") || {}).getAttribute ? document.querySelector("#_article").getAttribute("data-page-id") : null,
      navLoaded: !!(window.__browse && window.__browse.navLoaded),
      navLinks: document.querySelectorAll("#_nav a").length,
      appErrors: (window.__browse && window.__browse.errors) || [],
      mismatch: (window.__browse && window.__browse.mismatch) || [],
      links: Array.from(document.querySelectorAll("#_body .wl"), (n) => ({ text: n.textContent, cls: n.className, href: n.tagName === "A" ? rel(n.href) : null })),
      external: Array.from(document.querySelectorAll("#_body a.ext"), (n) => ({ href: n.href, rel: n.rel })),
      backlinks: texts("#_backlinks a"), relations: texts("#_relations tr"), diagnostics: texts("#_diagnostics li"),
      duplicateIds: ids.filter((x, i) => ids.indexOf(x) !== i),
      styleAttrs: document.querySelectorAll("[style]").length,
      scriptEscaped: document.title.indexOf("<script>") >= 0,
      cspViolations: violations.slice(),
    };
  };
})();`;

async function scenario(browser, base, origin) {
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.addInitScript(PROBE);
  const external = [];
  const errors = [];
  await context.route("**/*", (route) => {
    const url = route.request().url();
    if (url.startsWith("file:") || url.startsWith(origin)) return route.continue();
    external.push({ url, referer: route.request().headers()["referer"] || null, nav: route.request().isNavigationRequest() });
    return route.abort();
  });
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  const probe = () => page.evaluate(() => window.__probe());
  const steps = {};
  await page.goto(base + "index.html");
  steps.index = await probe();
  await page.click("#_index a:text-is('リンクの試験 <script>x</script>')");
  await page.waitForLoadState("load");
  steps.links = await probe();
  const beforeUrl = page.url();
  await page.click("#_body .wl-unresolved >> nth=0");
  await page.waitForTimeout(300);
  steps.unresolvedNavigated = page.url() !== beforeUrl;
  const beforeExternal = external.length;
  await page.click("#_body a.ext >> nth=0", { noWaitAfter: true }).catch(() => {});
  await page.waitForTimeout(500);
  steps.externalOnClick = external.slice(beforeExternal);
  steps.externalBeforeClick = external.slice(0, beforeExternal);
  await page.goto(beforeUrl);
  await page.click("#_body a.wl:text-is('定義へ')");
  await page.waitForLoadState("load");
  steps.anchor = await probe();
  await context.close();
  return { steps, errors };
}

async function noScript(browser, base) {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto(base + encodeURI("試験/リンク.html"));
  const result = await page.evaluate(() => ({
    body: !!document.querySelector("#_body h1"), meta: !!document.querySelector("#_meta tr"),
    backlinks: !!document.querySelector("#_backlinks"), diagnostics: !!document.querySelector("#_diagnostics li"),
    relations: !!document.querySelector("#_relations"),
  }));
  // <noscript> のリンクを、実際にたどる（失敗を握りつぶさない）。
  await page.click("#_nav noscript a");
  await page.waitForLoadState("load");
  result.noscriptReachedIndex = decodeURIComponent(page.url()).endsWith("/index.html");
  result.indexLinks = await page.locator("#_index a").count();
  await context.close();
  return result;
}

async function typesetting(browser, base, pages) {
  const NO_START = "、。，．」』）】〕〉》ーっゃゅょァィゥェォッャュョぁぃぅぇぉ・：；！？";
  const context = await browser.newContext();
  const page = await context.newPage();
  const out = { pages: 0, startViolations: 0, overflow: [], examples: [] };
  for (const rel of pages) {
    for (const width of [360, 600, 1000]) {
      await page.setViewportSize({ width, height: 800 });
      await page.goto(base + rel.split("/").map(encodeURIComponent).join("/"));
      const r = await page.evaluate((noStart) => {
        const main = document.querySelector("#_main");
        const overflow = main.scrollWidth > main.clientWidth + 1;
        let violations = 0; const examples = [];
        for (const el of document.querySelectorAll("#_body p, #_body li")) {
          const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
          let prevTop = null; let node;
          while ((node = walker.nextNode())) {
            const range = document.createRange();
            for (let i = 0; i < node.length; i++) {
              range.setStart(node, i); range.setEnd(node, i + 1);
              const rects = Array.from(range.getClientRects()).filter((x) => x.width > 0);
              if (!rects.length) continue;
              const top = rects[0].top;
              if (prevTop !== null && top - prevTop > 4 && noStart.indexOf(node.data[i]) >= 0) {
                violations++; if (examples.length < 3) examples.push(node.data.slice(Math.max(0, i - 3), i + 3));
              }
              prevTop = top;
            }
          }
        }
        return { overflow, violations, examples };
      }, NO_START);
      out.pages++;
      out.startViolations += r.violations;
      out.examples.push(...r.examples.slice(0, 1));
      if (r.overflow) out.overflow.push(`${rel}@${width}`);
    }
  }
  await context.close();
  return out;
}

function summarize(r) {
  const s = r.steps;
  return {
    navLoaded: s.index.navLoaded && s.links.navLoaded,
    navLinks: s.links.navLinks,
    links: s.links.links.map((l) => `${l.text}|${l.cls}|${l.href}`),
    backlinks: s.links.backlinks,
    relations: s.links.relations,
    diagnostics: s.links.diagnostics,
    anchorPage: s.anchor.page, anchorHash: s.anchor.hash, anchorFound: s.anchor.hashTargetFound,
    unresolvedNavigated: s.unresolvedNavigated,
  };
}

// --- 流す ---

const before = hashTree(wiki);
const results = { runs: [], wikiUnchanged: null };
let server = null;
const bases = {};
try {
  if (MODES.includes("static")) {
    const site = join(work, "site");
    const built = python(["build", wiki, "--out", site, "--raw", "text"]);
    if (!check(built.status === 0, "静的の書き出しが失敗した: " + built.stderr)) throw new Error(built.stderr);
    bases.static = { base: pathToFileURL(site).href + "/", origin: "file:", root: site };
  }
  if (MODES.includes("server")) {
    server = await startServer();
    const base = server.url.replace(/[^/]*$/, "");
    bases.server = { base, origin: new URL(base).origin };
  }
  // ページの集合と同じ規則で、最上位の SCHEMA.md などと indexes/ などを除く（wiki_pages.is_page_path）。
  const SKIP_FILES = ["SCHEMA.md", "index.md", "log.md", "README.md"];
  const SKIP_DIRS = ["indexes", "graph", "raw", "assets", ".evolution", ".wiki-cache"];
  const allPages = readdirSync(CORPUS, { recursive: true }).map((p) => p.replace(/\\/g, "/"))
    .filter((p) => p.toLowerCase().endsWith(".md") && !p.split("/").pop().startsWith("."))
    .filter((p) => (p.includes("/") ? !SKIP_DIRS.includes(p.split("/")[0]) : !SKIP_FILES.includes(p)))
    .map((p) => p.replace(/\.md$/i, ".html"));
  for (const name of BROWSERS) {
    const [type, opts] = ENGINES[name];
    let browser;
    try { browser = await type.launch(opts || {}); } catch (e) { check(false, `${name} を起動できない: ${e}`); continue; }
    for (const [mode, b] of Object.entries(bases)) {
      const run = { browser: name, mode };
      try {
        const r = await scenario(browser, b.base, b.origin);
        run.summary = summarize(r);
        run.errors = r.errors;
        const s = r.steps;
        const all = [s.index, s.links, s.anchor];
        check(run.summary.navLoaded, `${name}/${mode}: ナビゲーションを読めない`);
        check(all.every((x) => x.cspViolations.length === 0), `${name}/${mode}: CSP の違反がある`);
        check(all.every((x) => x.styleAttrs === 0), `${name}/${mode}: style の属性がある`);
        check(all.every((x) => x.duplicateIds.length === 0), `${name}/${mode}: 同じ ID の要素がある`);
        check(all.every((x) => x.appErrors.length === 0 && x.mismatch.length === 0), `${name}/${mode}: 画面のエラー`);
        check(s.externalBeforeClick.length === 0, `${name}/${mode}: 表示の時点で外へ要求した`);
        check(s.externalOnClick.length === 1 && s.externalOnClick[0].referer === null,
          `${name}/${mode}: 外部リンクのクリックの移動か Referer が期待と違う: ${JSON.stringify(s.externalOnClick)}`);
        check(!run.summary.unresolvedNavigated, `${name}/${mode}: 未解決リンクで移動した`);
        check(run.summary.anchorFound, `${name}/${mode}: 見出しへの移動先がない`);
        check(r.errors.length === 0, `${name}/${mode}: コンソールのエラー: ${r.errors.slice(0, 3)}`);
        check(s.links.scriptEscaped, `${name}/${mode}: 題名の <script> が文字として出ていない`);
        run.noScript = await noScript(browser, b.base);
        check(run.noScript.body && run.noScript.meta && run.noScript.backlinks && run.noScript.diagnostics &&
          run.noScript.relations && run.noScript.noscriptReachedIndex && run.noScript.indexLinks > 0,
          `${name}/${mode}: JavaScript を切ると読めない: ${JSON.stringify(run.noScript)}`);
        if (mode === "static") {
          run.typesetting = await typesetting(browser, b.base, allPages);
          check(run.typesetting.startViolations === 0, `${name}: 行頭の禁則の違反 ${run.typesetting.startViolations}: ${run.typesetting.examples}`);
          check(run.typesetting.overflow.length === 0, `${name}: 本文の幅からはみ出す: ${run.typesetting.overflow.slice(0, 5)}`);
        }
      } catch (e) {
        check(false, `${name}/${mode}: ${String(e).slice(0, 400)}`);
      }
      results.runs.push(run);
    }
    await browser.close();
  }
  const sums = results.runs.filter((r) => r.summary).map((r) => JSON.stringify(r.summary));
  check(sums.length === results.runs.length && new Set(sums).size <= 1, "方式やブラウザで結果が違う");
  if (server) {
    const stopped = python(["stop", wiki]);
    check(stopped.status === 0, "stop が失敗した: " + stopped.stderr);
  }
  // 出力に絶対パスがない（静的版）
  if (bases.static) {
    const walk = (d) => readdirSync(d, { recursive: true }).map((p) => join(d, p)).filter((p) => statSync(p).isFile());
    for (const f of walk(bases.static.root)) {
      const text = readFileSync(f, "utf8");
      for (const mark of ["ROOTMARK", "DATAMARK"]) check(!text.includes(mark), `出力に ${mark} がある: ${f}`);
    }
  }
} catch (e) {
  check(false, String(e));
} finally {
  if (server) { try { server.child.kill(); } catch { /* 終わっている */ } }
  results.wikiUnchanged = before === hashTree(wiki);
  check(results.wikiUnchanged, "閲覧の前後で Wiki のファイルが変わった");
}
results.failures = failures;
if (process.env.OUT) writeFileSync(process.env.OUT, JSON.stringify(results, null, 2), "utf8");
console.log(JSON.stringify({ failures, runs: results.runs.map((r) => ({ b: r.browser, m: r.mode, nav: r.summary?.navLoaded, links: r.summary?.links?.length, typesetting: r.typesetting && { v: r.typesetting.startViolations, o: r.typesetting.overflow.length } })) }, null, 1));
try { rmSync(work, { recursive: true, force: true }); } catch { /* Windows で掴まれていれば残す */ }
process.exit(failures.length ? 1 : 0);
