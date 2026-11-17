// Chrome で gantt が不正な応答になる原因を見る。配布対象ではない。
import { createRequire } from "node:module";
import { spawn } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const require = createRequire(join(HERE, "..", "..", "tests", "wiki", "browse", "package.json"));
const { chromium } = require("playwright");
const channel = process.argv[2] || "chrome";
const p = spawn("python", ["-X", "utf8", join(HERE, "serve.py")], { cwd: HERE, stdio: ["ignore", "pipe", "inherit"] });
const url = await new Promise((res) => p.stdout.once("data", (b) => res(JSON.parse(String(b).split("\n")[0]).url)));
const browser = await chromium.launch(channel === "chromium" ? {} : { channel });
const page = await browser.newPage();
page.on("console", (m) => { if (m.type() === "error") console.log("console:", m.text().slice(0, 120)); });
await page.goto(url + "page.html");
await page.waitForFunction(() => window.__figs && window.__figs.state === "done", null, { timeout: 60000 });
const frame = page.frames().find((f) => f !== page.mainFrame());
const out = await frame.evaluate(async () => {
  const src = "gantt\n  dateFormat YYYY-MM-DD\n  section 準備\n  PoC :a1, 2026-11-17, 2d\n  設計 :after a1, 2d";
  const r = await mermaid.render("dbg", src);
  const m = /viewBox="([^"]*)"/.exec(r.svg);
  return { viewBox: m && m[1], head: r.svg.slice(0, 300), bodyW: document.body.clientWidth, date: String(new Date("2026-11-17")) };
});
console.log(JSON.stringify(out, null, 1));
await browser.close();
p.kill();
