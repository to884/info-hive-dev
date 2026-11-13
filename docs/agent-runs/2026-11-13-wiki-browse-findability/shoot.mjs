// 書き出した閲覧ページを Chromium で開き、画面を撮る。配布対象ではない。
// 使い方: node shoot.mjs <playwright の index.mjs の絶対パス> <撮る一覧の JSON> <保存先>
// 一覧の JSON は [{"name": "large-index", "file": "<html の絶対パス>", "width": 1280, "dark": false, "full": true}] の形。
import { readFileSync, mkdirSync } from "node:fs";
import { pathToFileURL } from "node:url";
import { join } from "node:path";

const [pwPath, listPath, outDir] = process.argv.slice(2);
const { chromium } = await import(pathToFileURL(pwPath).href);
const shots = JSON.parse(readFileSync(listPath, "utf8"));
mkdirSync(outDir, { recursive: true });
const browser = await chromium.launch();
for (const s of shots) {
  const page = await browser.newPage({ viewport: { width: s.width, height: s.height || 900 },
                                       colorScheme: s.dark ? "dark" : "light" });
  const errors = [];
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  await page.goto(pathToFileURL(s.file).href);
  if (s.type) {
    await page.locator(s.typeInto || "#_q").fill(s.type);
    await page.waitForTimeout(150);
  }
  await page.screenshot({ path: join(outDir, `${s.name}.png`), fullPage: !!s.full });
  console.log(`${s.name}: エラー ${errors.length} 件${errors.length ? " " + errors.join(" | ") : ""}`);
  await page.close();
}
await browser.close();
