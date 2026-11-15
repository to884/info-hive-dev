// 静的に書き出した閲覧の画面を、5 つのブラウザで撮る（目で見比べるため）。
// 使い方（開発リポジトリのルートで）: node docs/agent-runs/2026-11-15-wiki-browse-cross-browser/shoot.mjs <書き出したサイト> <撮った画像の置き場所>
// 撮るもの: 索引と記事のページ 2 つを、ライトとダーク、幅 1280 と 360 で。あわせて [style] の数と、横にはみ出した幅を記録する。
import { createRequire } from "node:module";
import { mkdirSync, writeFileSync } from "node:fs";
import { join, resolve, dirname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const require = createRequire(join(HERE, "..", "..", "..", "tests", "wiki", "browse", "package.json"));
const { chromium, firefox, webkit } = require("playwright");

const site = resolve(process.argv[2]);
const out = resolve(process.argv[3]);
mkdirSync(out, { recursive: true });

const ENGINES = {
  chromium: [chromium, {}], firefox: [firefox, {}], webkit: [webkit, {}],
  msedge: [chromium, { channel: "msedge" }], chrome: [chromium, { channel: "chrome" }],
};
const PAGES = {
  index: "index.html",
  design: "concepts/browseのデザインシステム.html",
  release: "sources/browseの記事のページのFluent2のリリース-wiki-0.19.0.html",
};
const WIDTHS = [1280, 360];
const SCHEMES = ["light", "dark"];

const report = [];
for (const [name, [engine, opts]] of Object.entries(ENGINES)) {
  const browser = await engine.launch(opts);
  for (const scheme of SCHEMES) {
    for (const width of WIDTHS) {
      const ctx = await browser.newContext({ viewport: { width, height: 900 }, colorScheme: scheme });
      const page = await ctx.newPage();
      const errors = [];
      page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
      page.on("pageerror", (e) => errors.push(String(e)));
      for (const [key, rel] of Object.entries(PAGES)) {
        await page.goto(pathToFileURL(join(site, rel)).href);
        await page.waitForLoadState("load");
        await page.waitForTimeout(300);
        const m = await page.evaluate(() => ({
          theme: document.documentElement.getAttribute("data-theme"),
          styled: document.querySelectorAll("[style]").length,
          overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
          bg: getComputedStyle(document.body).backgroundColor,
        }));
        const file = `${name}-${key}-${scheme}-${width}.png`;
        await page.screenshot({ path: join(out, file) });
        report.push({ browser: name, page: key, scheme, width, file, ...m });
      }
      report.push({ browser: name, scheme, width, errors });
      await ctx.close();
    }
  }
  await browser.close();
}
writeFileSync(join(out, "report.json"), JSON.stringify(report, null, 1), "utf8");
const bad = report.filter((r) => (r.styled ?? 0) > 0 || (r.overflow ?? 0) > 0 || (r.errors?.length ?? 0) > 0);
console.log(JSON.stringify({ shots: report.filter((r) => r.file).length, bad }, null, 1));
