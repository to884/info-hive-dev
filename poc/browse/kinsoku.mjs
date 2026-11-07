// ADR-0010 の PoC。static-test/kinsoku.html を Playwright の各エンジンで開き、幅を変えながら禁則の違反を数える。
// WebKitGTK の分は webkitgtk_kinsoku.py で測る。使い方: node kinsoku.mjs [出力の JSON]
import { chromium, firefox, webkit } from "playwright";
import { writeFileSync, mkdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { pathToFileURL, fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = process.argv[2] || join(HERE, "out", "results", "kinsoku.json");
const url = pathToFileURL(join(HERE, "static-test", "kinsoku.html")).href;
const results = {};
for (const [name, type, opts] of [["chromium", chromium], ["firefox", firefox], ["webkit", webkit],
  ["msedge", chromium, { channel: "msedge" }]]) {
  const b = await type.launch(opts || {});
  const p = await b.newPage();
  await p.goto(url);
  results[name] = { version: b.version(), ...(await p.evaluate(() => window.kinsoku())) };
  await b.close();
  const r = results[name];
  console.log(name, r.version, "strict", r.strict.startViolations, r.strict.endViolations, "/", r.strict.lines,
    "control", r.control.startViolations, r.control.endViolations, "/", r.control.lines);
}
mkdirSync(dirname(OUT), { recursive: true });
writeFileSync(OUT, JSON.stringify(results, null, 2), "utf8");
