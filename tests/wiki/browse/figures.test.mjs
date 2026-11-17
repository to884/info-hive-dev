// wiki の閲覧（browse）の図のブラウザでの試験（ADR-0030、図の描画の設計の 10.2）。
// 図の svg を、静的の書き出し（file://）とサーバー（http://127.0.0.1）で開き、画像として出ること、画像の中の
// スタイルが効くこと、中のスクリプトが動かないこと、ページの約束（CSP の違反、[style]、外への要求が 0 件）を確かめる。
// 1 つでも外れれば、終了コードを 1 にする。
//
// 使い方（開発リポジトリのルートで）:
//   cd tests/wiki/browse && npm ci && node figures.test.mjs
// 環境変数:
//   BROWSE_PYTHON   python を呼ぶコマンド（空白で区切る。既定は "uv run --python 3.12 --with pyyaml==6.0.3 python"）
//   MODES           "static,server"（既定）
//   BROWSERS        "chromium"（既定）。"chromium,firefox,webkit,msedge,chrome" で手で流す試験にする
//   OUT             結果の JSON の書き出し先（既定は書き出さない）
import { chromium, firefox, webkit } from "playwright";
import { createRequire } from "node:module";
import { spawn, spawnSync } from "node:child_process";
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, "..", "..", "..");
const SCRIPT = join(REPO, "info-hive-wiki", "skills", "info-hive", "scripts", "wiki_browse.py");
const PYTHON = (process.env.BROWSE_PYTHON || "uv run --python 3.12 --with pyyaml==6.0.3 python").split(/\s+/);
const MODES = (process.env.MODES || "static,server").split(",");
const ENGINES = { chromium: [chromium], firefox: [firefox], webkit: [webkit],
  msedge: [chromium, { channel: "msedge" }], chrome: [chromium, { channel: "chrome" }] };
const BROWSERS = (process.env.BROWSERS || "chromium").split(",");
// 画像の画素を読む。Playwright に同梱の PNG の読み手を使う（package-lock.json で版を固定している）
const { PNG } = createRequire(import.meta.url)("playwright-core/lib/utilsBundle");

const failures = [];
function check(cond, message) { if (!cond) failures.push(message); return cond; }

// --- 試験用の Wiki ---

const work = mkdtempSync(join(tmpdir(), "browse-figures-"));
const wiki = join(work, "wiki");
const data = join(work, "data");
function put(rel, text) {
  const p = join(wiki, rel);
  mkdirSync(dirname(p), { recursive: true });
  writeFileSync(p, text, "utf8");
}
put("SCHEMA.md", "# スキーマ\n");
put("index.md", "# 索引\n\n- [[図]]\n");
// 色は <style> だけで決める。スタイルが効かなければ、四角は既定の黒になる
const FILL = [15, 108, 189];
put("assets/図-01.svg", [
  '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="100" viewBox="0 0 200 100"',
  "  onload=\"document.documentElement.setAttribute('data-pwned','onload')\">",
  "<style>.box{fill:#0f6cbd}</style>",
  '<rect class="box" x="0" y="0" width="200" height="100"/>',
  '<image href="https://example.invalid/x.png" x="0" y="0" width="10" height="10"/>',
  "<script>document.documentElement.setAttribute('data-pwned','script');",
  "fetch('https://example.invalid/pwn').catch(function(){});</script>",
  "</svg>", ""].join("\n"));
// 根に大きさのない svg。中核は width と height の属性を付けられないので、CSS だけで見える大きさになること
put("assets/無寸.svg", '<svg xmlns="http://www.w3.org/2000/svg"><rect width="300" height="150" fill="#0f6cbd"/></svg>\n');
put("concepts/図.md", ["---", 'type: "concept"', "---", "", "# 図", "",
  "手書きの図。", "", "![四角の図](../assets/図-01.svg)", "",
  "大きさのない図。", "", "![大きさのない図](../assets/無寸.svg)", "",
  "ない図。", "", "![ない図の説明](../assets/ない.svg)", ""].join("\n"));

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

const PROBE = () => {
  window.__violations = [];
  document.addEventListener("securitypolicyviolation", (e) => window.__violations.push(e.violatedDirective + " " + e.blockedURI));
};

// 画像の中心の画素の色
async function centerColor(el) {
  const png = PNG.sync.read(await el.screenshot());
  const i = (Math.floor(png.height / 2) * png.width + Math.floor(png.width / 2)) * 4;
  return [png.data[i], png.data[i + 1], png.data[i + 2]];
}

async function scenario(browser, base, origin) {
  const context = await browser.newContext({ viewport: { width: 1200, height: 900 }, deviceScaleFactor: 1 });
  const external = [];
  await context.route("**/*", (route) => {
    const url = route.request().url();
    if (url.startsWith("file:") || url.startsWith("data:") || url.startsWith(origin)) return route.continue();
    external.push(url);
    return route.abort();
  });
  await context.addInitScript(PROBE);
  const page = await context.newPage();
  const errors = [];
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text().slice(0, 200)); });
  page.on("pageerror", (e) => errors.push(String(e).slice(0, 200)));
  await page.goto(base + "concepts/" + encodeURIComponent("図") + ".html");
  await page.waitForFunction(() => [...document.querySelectorAll("img.fui-Image")].every((i) => i.complete));
  await page.waitForTimeout(300);
  const r = await page.evaluate(() => {
    const imgs = [...document.querySelectorAll("#_body .wiki-fig > img")];
    return {
      imgs: imgs.map((i) => ({ alt: i.alt, natural: i.naturalWidth, src: i.getAttribute("src"),
                               shown: Math.round(i.getBoundingClientRect().width) })),
      wrappers: [...document.querySelectorAll("#_body .wiki-fig")].map((w) => [w.tagName, w.className, w.getAttribute("data-theme")]),
      missingAltShown: document.querySelector("#_body").textContent.includes("ない図の説明"),
      styleAttrs: document.querySelectorAll("[style]").length,
      pwned: document.documentElement.getAttribute("data-pwned"),
      violations: window.__violations.slice(),
      linkedSvg: [...document.querySelectorAll("a[href]")].filter((a) => /\.svg($|[?#])/i.test(a.getAttribute("href"))).length,
    };
  });
  // 撮る前に違反とコンソールのエラーを数えた（WebKit は撮るたびに、Playwright のスタイルシートを CSP が拒む）
  r.errors = errors.slice();
  const img = await page.$("#_body .wiki-fig > img");
  r.color = img ? await centerColor(img) : null;
  // 暗い配色でも、手書きの svg の入れ物は明るい配色のトークンを使う（明るい配色のときと同じ地の色のまま）
  await page.evaluate(() => document.documentElement.setAttribute("data-theme", "light"));
  r.lightWrapperBg = await page.$eval("#_body .wiki-fig", (w) => getComputedStyle(w).backgroundColor).catch(() => null);
  r.lightPageBg = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
  await page.evaluate(() => document.documentElement.setAttribute("data-theme", "dark"));
  r.darkWrapperBg = await page.$eval("#_body .wiki-fig", (w) => getComputedStyle(w).backgroundColor).catch(() => null);
  r.darkPageBg = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
  // svg を直接開いても、中のスクリプトが動かない（サーバーの方式。CSP の sandbox）
  if (!base.startsWith("file:") && r.imgs[0]) {
    const svgUrl = new URL(r.imgs[0].src, page.url()).href;
    const direct = await context.newPage();
    await direct.goto(svgUrl);
    await direct.waitForTimeout(300);
    r.directPwned = await direct.evaluate(() => document.documentElement.getAttribute("data-pwned"));
    await direct.close();
  }
  r.external = external;
  await context.close();
  return r;
}

const results = { runs: [] };
let server = null;
try {
  const bases = {};
  if (MODES.includes("static")) {
    const site = join(work, "site");
    const built = python(["build", wiki, "--out", site, "--raw", "text"]);
    if (!check(built.status === 0, "静的の書き出しが失敗した: " + built.stderr)) throw new Error(built.stderr);
    bases.static = { base: pathToFileURL(site).href + "/", origin: "file:" };
  }
  if (MODES.includes("server")) {
    server = await startServer();
    const base = server.url.replace(/[^/]*$/, "");
    bases.server = { base, origin: new URL(base).origin };
  }
  for (const name of BROWSERS) {
    const [type, opts] = ENGINES[name];
    let browser;
    try { browser = await type.launch(opts || {}); } catch (e) { check(false, `${name} を起動できない: ${e}`); continue; }
    for (const [mode, b] of Object.entries(bases)) {
      const tag = `${name}/${mode}`;
      const run = { browser: name, mode };
      try {
        const r = await scenario(browser, b.base, b.origin);
        Object.assign(run, r);
        check(r.imgs.length === 2, `${tag}: 図の画像が 2 つでない: ${JSON.stringify(r.imgs)}`);
        check(r.imgs.every((i) => i.natural > 0), `${tag}: 図の画像を読めない`);
        check(r.imgs.every((i) => i.shown > 0), `${tag}: 図の画像の幅が 0: ${JSON.stringify(r.imgs)}`);
        check(r.imgs[0] && r.imgs[0].alt === "四角の図" && r.imgs[0].shown === 200, `${tag}: 代替テキストか幅が違う`);
        const wrapper = ["SPAN", "wiki-fig fui-Card", "light"];
        check(JSON.stringify(r.wrappers) === JSON.stringify([wrapper, wrapper]),
          `${tag}: 入れ物が違う: ${JSON.stringify(r.wrappers)}`);
        check(r.missingAltShown, `${tag}: ない図の代替テキストが出ていない`);
        check(r.color && r.color.every((v, k) => Math.abs(v - FILL[k]) <= 8),
          `${tag}: 画像の中のスタイルが効いていない: ${JSON.stringify(r.color)}`);
        check(r.styleAttrs === 0, `${tag}: style の属性がある`);
        check(r.violations.length === 0, `${tag}: CSP の違反がある: ${r.violations}`);
        check(r.pwned === null, `${tag}: 画像の中のスクリプトが動いた`);
        check(r.linkedSvg === 0, `${tag}: svg へのリンクがある`);
        check(r.external.length === 0, `${tag}: 外へ要求した: ${r.external}`);
        check(r.errors.length === 0, `${tag}: コンソールのエラー: ${r.errors.slice(0, 3)}`);
        check(r.lightWrapperBg && r.darkWrapperBg === r.lightWrapperBg && r.darkPageBg !== r.lightPageBg,
          `${tag}: 暗い配色で、手書きの svg の入れ物が明るい配色の地を保たない: ${JSON.stringify([r.lightWrapperBg, r.darkWrapperBg, r.lightPageBg, r.darkPageBg])}`);
        if (mode === "server") check(r.directPwned === null, `${tag}: svg を直接開くと中のスクリプトが動いた`);
      } catch (e) {
        check(false, `${tag}: ${String(e).slice(0, 400)}`);
      }
      results.runs.push(run);
    }
    await browser.close();
  }
} finally {
  if (server) {
    const stopped = python(["stop", wiki]);
    check(stopped.status === 0, "stop が失敗した: " + stopped.stderr);
  }
  if (process.env.OUT) writeFileSync(process.env.OUT, JSON.stringify({ ...results, failures }, null, 2));
  rmSync(work, { recursive: true, force: true });
}
for (const f of failures) console.error("NG: " + f);
console.log(JSON.stringify({ runs: results.runs.length, failures: failures.length }));
process.exit(failures.length ? 1 : 0);
