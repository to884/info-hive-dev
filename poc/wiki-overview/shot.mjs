// 概要の表示の試作を、ライトとダークで開いて撮る。配布対象ではない。
// 使い方: node shot.mjs <playwright を npm ci したディレクトリ> <ページの URL>
// 結果は out/ に書く（概要の部分の画像と、CSP の違反、style 属性、外への要求、Mermaid の結果）。
import { createRequire } from "node:module";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const [, , pwDir, url] = process.argv;
if (!pwDir || !url) {
  console.error("使い方: node shot.mjs <playwright のディレクトリ> <ページの URL>");
  process.exit(2);
}
const { chromium } = createRequire(join(resolve(pwDir), "package.json"))("playwright");
const out = join(dirname(fileURLToPath(import.meta.url)), "out");
mkdirSync(out, { recursive: true });

const browser = await chromium.launch();
const summary = [];
for (const scheme of ["light", "dark"]) {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: scheme });
  const page = await context.newPage();
  const external = [];
  page.on("request", (r) => { if (!r.url().startsWith(new URL(url).origin) && !r.url().startsWith("data:")) external.push(r.url()); });
  const consoleErrors = [];
  page.on("console", (m) => { if (m.type() === "error") consoleErrors.push(m.text().slice(0, 200)); });
  await page.addInitScript(() => {
    window.__violations = [];
    document.addEventListener("securitypolicyviolation", (e) => window.__violations.push(e.violatedDirective + " " + e.blockedURI));
  });
  await page.goto(url, { waitUntil: "load" });
  await page.evaluate(() => document.querySelectorAll("#_body img").forEach((i) => { i.loading = "eager"; }));
  await page.waitForFunction(() => window.__figs && window.__figs.state === "done", null, { timeout: 30000 }).catch(() => {});
  await page.waitForTimeout(500);
  const probe = await page.evaluate(() => ({
    figs: window.__figs ? { state: window.__figs.state, frameViolations: window.__figs.frameViolations,
      results: Object.fromEntries(Object.entries(window.__figs.results).map(([k, v]) => [k, { ok: v.ok, error: v.error }])) } : null,
    violations: window.__violations,
    styleAttrs: document.querySelectorAll("[style]").length,
    imgs: [...document.querySelectorAll("#_body img")].map((i) => ({ fig: i.parentNode.getAttribute("data-fig"), natural: i.naturalWidth, shown: i.clientWidth })),
    afterH1: document.querySelector("#_body h1")?.nextElementSibling?.className ?? null,
    ovState: document.querySelector(".ov")?.getAttribute("data-ov-state") ?? null,
  }));
  await page.locator(".ov").screenshot({ path: join(out, `overview-${scheme}.png`) });
  await page.screenshot({ path: join(out, `page-top-${scheme}.png`) });
  summary.push({ scheme, ...probe, external, consoleErrors });
  await context.close();
}
await browser.close();
writeFileSync(join(out, "summary.json"), JSON.stringify(summary, null, 2) + "\n", "utf8");
console.log(JSON.stringify(summary, null, 2));
