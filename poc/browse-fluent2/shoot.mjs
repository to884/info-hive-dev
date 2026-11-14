// browse の Fluent 2 の試作を Chromium で開き、画面を撮って確かめる。配布対象ではない。
// 使い方: node shoot.mjs <playwright の index.mjs の絶対パス> <試作の出力先（out）> <保存先>
// 確かめること: [style] の数、CSP の違反、外への要求、横のはみ出し、主な要素のコントラスト比、
// 配色の切り替えがページを移っても残ること（file:// と、ポートの違う 2 つの http のサーバー）。
import { mkdirSync, writeFileSync, readFileSync, existsSync, statSync } from "node:fs";
import { createServer } from "node:http";
import { pathToFileURL } from "node:url";
import { join, extname, resolve } from "node:path";

const [pwPath, outRoot, shotDir] = process.argv.slice(2);
const { chromium } = await import(pathToFileURL(pwPath).href);
mkdirSync(shotDir, { recursive: true });

const TYPES = { ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8" };
function serve() {
  return new Promise((ok) => {
    const srv = createServer((req, res) => {
      const p = resolve(outRoot, "." + decodeURIComponent(new URL(req.url, "http://x").pathname));
      if (!p.startsWith(resolve(outRoot)) || !existsSync(p) || statSync(p).isDirectory()) { res.writeHead(404); res.end(); return; }
      res.writeHead(200, { "Content-Type": TYPES[extname(p)] || "application/octet-stream", "Cache-Control": "no-store" });
      res.end(readFileSync(p));
    });
    srv.listen(0, "127.0.0.1", () => ok(srv));
  });
}

const PROBE = () => {
  function rgb(s) { const m = s.match(/[\d.]+/g); return m ? m.slice(0, 4).map(Number) : [0, 0, 0, 1]; }
  function lum([r, g, b]) {
    const f = (c) => { c /= 255; return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
  }
  function bg(el) {
    for (let e = el; e; e = e.parentElement) {
      const c = rgb(getComputedStyle(e).backgroundColor);
      if (c.length < 4 || c[3] > 0) { return c; }
    }
    return [255, 255, 255, 1];
  }
  function ratio(el) {
    const a = lum(rgb(getComputedStyle(el).color)), b = lum(bg(el));
    return Math.round(((Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05)) * 100) / 100;
  }
  const pick = {
    "本文": "#_body p", "見出し": "#_body h2", "本文のリンク": "#_body a.wl", "未解決のリンク": "#_body .wl-unresolved",
    "曖昧のリンク": "#_body .wl-ambiguous", "スコープ": "#_scope .fui-Badge", "ナビの項目": ".fui-NavSubItem:not(.is-current)",
    "今のページ": ".fui-NavSubItem.is-current", "グループ": ".fui-NavCategoryItem .tree-name", "件数": ".tree-count",
    "メタ欄の見出し": "#_meta th", "注意の帯": ".fui-MessageBarBody", "種類 ソース": ".t-source", "種類 エンティティ": ".t-entity",
    "種類 コンセプト": ".t-concept", "種類 シンセシス": ".t-synthesis", "タグ": ".fui-Tag__primaryText", "要約": ".ix-summary",
    "索引の題名": ".ix-title", "グループの階層": ".fx-path", "被リンク": "#_backlinks a", "診断": ".diag-list li",
  };
  const contrast = {};
  for (const [k, sel] of Object.entries(pick)) { const e = document.querySelector(sel); if (e) { contrast[k] = ratio(e); } }
  const main = document.getElementById("_main");
  return {
    theme: document.documentElement.getAttribute("data-theme"),
    styleAttrs: document.querySelectorAll("[style]").length,
    overflowPage: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
    overflowMain: main ? main.scrollWidth > main.clientWidth + 1 : false,
    navLoaded: !!(window.__browse && window.__browse.navLoaded),
    errors: (window.__browse && window.__browse.errors) || [],
    csp: window.__csp || [],
    contrast,
  };
};

const browser = await chromium.launch();
const report = { shots: [], theme: {} };

async function open(url, opts = {}) {
  const ctx = opts.ctx || await browser.newContext({ viewport: { width: opts.width || 1280, height: opts.height || 900 },
    colorScheme: opts.dark ? "dark" : "light", forcedColors: opts.forced ? "active" : "none" });
  const page = await ctx.newPage();
  const consoleErrors = [];
  const external = [];
  page.on("console", (m) => { if (m.type() === "error") consoleErrors.push(m.text()); });
  page.on("request", (r) => { const u = r.url(); if (!u.startsWith("file:") && !u.startsWith("http://127.0.0.1")) external.push(u); });
  await page.addInitScript(() => {
    window.__csp = [];
    document.addEventListener("securitypolicyviolation", (e) => window.__csp.push(e.violatedDirective + " " + e.blockedURI));
  });
  await page.goto(url);
  await page.waitForTimeout(100);
  return { ctx, page, consoleErrors, external };
}

const base = (variant) => pathToFileURL(join(outRoot, variant)).href + "/";
const SHOTS = [];
for (const width of [1280, 768, 360, 320]) {
  for (const dark of [false, true]) {
    for (const [name, path] of [["index", "index.html"], ["article", "pages/bm25.html"], ["deep", "pages/deep-leaf.html"]]) {
      if (name === "deep" && width !== 1280) { continue; }
      SHOTS.push({ name: `${name}-${width}-${dark ? "dark" : "light"}`, variant: "project-green", path, width, dark });
    }
  }
}
SHOTS.push({ name: "article-1280-forced", variant: "project-green", path: "pages/bm25.html", width: 1280, forced: true });
SHOTS.push({ name: "index-1280-forced", variant: "project-green", path: "index.html", width: 1280, forced: true });
SHOTS.push({ name: "scope-neutral-1280-light", variant: "project-neutral", path: "pages/bm25.html", width: 1280 });
SHOTS.push({ name: "scope-neutral-1280-dark", variant: "project-neutral", path: "pages/bm25.html", width: 1280, dark: true });
SHOTS.push({ name: "scope-user-1280-light", variant: "user", path: "pages/bm25.html", width: 1280 });
SHOTS.push({ name: "scope-user-1280-dark", variant: "user", path: "pages/bm25.html", width: 1280, dark: true });
SHOTS.push({ name: "index-1280-light-filtered", variant: "project-green", path: "index.html#group=_g2", width: 1280 });
SHOTS.push({ name: "article-1280-light-search", variant: "project-green", path: "pages/bm25.html", width: 1280, type: "検索" });
SHOTS.push({ name: "article-360-light-menu-open", variant: "project-green", path: "pages/bm25.html", width: 360, openMenu: true });

for (const s of SHOTS) {
  const { ctx, page, consoleErrors, external } = await open(base(s.variant) + s.path, s);
  if (s.type) { await page.locator("#_q").fill(s.type); await page.waitForTimeout(300); }
  if (s.openMenu) { await page.locator(".drawer > summary").click(); await page.waitForTimeout(100); }
  const probe = await page.evaluate(PROBE);
  await page.screenshot({ path: join(shotDir, `${s.name}.png`), fullPage: true });
  report.shots.push({ name: s.name, consoleErrors, external, ...probe });
  await ctx.close();
}

// 配色の切り替え: file:// では localStorage、http ではポートを区別しない cookie に残る
{
  const ctx = await browser.newContext({ colorScheme: "light" });
  const { page } = await open(base("project-green") + "pages/bm25.html", { ctx });
  const before = await page.evaluate(() => document.documentElement.getAttribute("data-theme"));
  await page.selectOption("#_theme", "dark");
  await page.goto(base("project-green") + "index.html");
  const after = await page.evaluate(() => document.documentElement.getAttribute("data-theme"));
  report.theme.file = { before, afterNavigation: after };
  await ctx.close();
}
{
  const a = await serve(), b = await serve();
  const ctx = await browser.newContext({ colorScheme: "light" });
  const pa = await ctx.newPage();
  await pa.goto(`http://127.0.0.1:${a.address().port}/project-green/pages/bm25.html`);
  await pa.selectOption("#_theme", "dark");
  const pb = await ctx.newPage();
  await pb.goto(`http://127.0.0.1:${b.address().port}/project-green/index.html`);
  const other = await pb.evaluate(() => document.documentElement.getAttribute("data-theme"));
  report.theme.httpOtherPort = { portA: a.address().port, portB: b.address().port, themeOnB: other };
  await pb.screenshot({ path: join(shotDir, "theme-dark-on-light-os.png"), fullPage: true });
  await ctx.close();
  a.close(); b.close();
}
// 保存先が例外を出すとき（file:// で localStorage を壊す）
{
  const ctx = await browser.newContext({ colorScheme: "light" });
  await ctx.addInitScript(() => {
    Object.defineProperty(window, "localStorage", { get() { throw new Error("blocked"); } });
  });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  await page.goto(base("project-green") + "pages/bm25.html");
  await page.selectOption("#_theme", "dark");
  const theme = await page.evaluate(() => document.documentElement.getAttribute("data-theme"));
  await page.reload();
  const afterReload = await page.evaluate(() => document.documentElement.getAttribute("data-theme"));
  report.theme.storageThrows = { themeAfterSelect: theme, afterReload, pageErrors: errors };
  await ctx.close();
}
// スクリプトなし
{
  const ctx = await browser.newContext({ javaScriptEnabled: false, colorScheme: "dark" });
  const page = await ctx.newPage();
  await page.goto(base("project-green") + "index.html");
  report.theme.noScript = { theme: await page.evaluate === undefined ? null : await page.getAttribute("html", "data-theme"),
    rows: await page.locator("#_index .fx-row").count() };
  await page.screenshot({ path: join(shotDir, "index-1280-dark-noscript.png"), fullPage: true });
  await ctx.close();
}
await browser.close();
writeFileSync(join(shotDir, "report.json"), JSON.stringify(report, null, 2));
const bad = report.shots.filter((s) => s.styleAttrs || s.csp.length || s.external.length || s.overflowPage || s.overflowMain || s.consoleErrors.length || !s.navLoaded);
console.log(JSON.stringify({ shots: report.shots.length, problems: bad.map((s) => s.name), theme: report.theme }, null, 2));
