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

// Mermaid の図（ADR-0030、図の描画の設計の 7）。描ける 3 つと、描けない 3 つ（構文の誤り、tiny にないマインドマップ、
// 外の画像を使う図）
const FENCE = "```";
put("concepts/流れ.md", ["---", 'type: "concept"', "---", "", "# 流れ", "",
  FENCE + "mermaid", "flowchart LR", '  予測["予測"] --> 更新["更新<br>（観測で直す）"]', "  観測 --> 更新", FENCE, "",
  FENCE + "mermaid", "sequenceDiagram", "  利用者->>サーバー: 要求する", "  サーバー-->>利用者: 返す", FENCE, "",
  FENCE + "mermaid", "flowchart TD", "  accTitle: 取り込みの流れ", "  accDescr: raw を作り、ページを書く", "  raw --> ページ", FENCE, "",
  FENCE + "mermaid", "flowchart LR", "  A -->", FENCE, "",
  FENCE + "mermaid", "mindmap", "  root((wiki))", "    取り込み", FENCE, "",
  FENCE + "mermaid", "flowchart LR", '  X@{ img: "https://example.invalid/x.png", label: "画像", pos: "t", h: 40, constraint: "on" }', FENCE, "",
  FENCE + "python", 'print("mermaid ではない")', FENCE, ""].join("\n"));
const MERMAID_OK = 3;
const MERMAID_NG = 3;
put("concepts/一つ.md", ["# 一つ", "", FENCE + "mermaid", "flowchart LR", "  a --> b", FENCE, ""].join("\n"));

// 枠の寿命の確かめに使う、偽の枠のスクリプト（mermaid-frame.js の応答を差し替える）
const FAKE_SVG = (fill) => `<svg xmlns="http://www.w3.org/2000/svg" width="40" height="20"><rect width="40" height="20" fill="${fill}"/></svg>`;
const FAKE_FRAMES = {
  // result を 2 回送る。親は 1 回目だけを使い、2 回目は処理しない
  twice: `addEventListener("message", function (e) {
    if (!e.data || e.data.type !== "render") return;
    parent.postMessage({ type: "result", ok: true, svg: ${JSON.stringify(FAKE_SVG("#000001"))}, w: 40, h: 20 }, "*");
    parent.postMessage({ type: "result", ok: true, svg: ${JSON.stringify(FAKE_SVG("#000002"))}, w: 40, h: 20 }, "*");
  }); parent.postMessage({ type: "ready" }, "*");`,
  // 応答しない
  silent: `parent.postMessage({ type: "ready" }, "*");`,
  // 画像として読めない SVG を返す。親は警告に替える
  broken: `addEventListener("message", function (e) {
    if (!e.data || e.data.type !== "render") return;
    parent.postMessage({ type: "result", ok: true, svg: "<svg>", w: 40, h: 20 }, "*");
  }); parent.postMessage({ type: "ready" }, "*");`,
  // 暗い配色のときだけ失敗する
  failDark: `addEventListener("message", function (e) {
    if (!e.data || e.data.type !== "render") return;
    if (e.data.theme && e.data.theme.darkMode) parent.postMessage({ type: "result", ok: false, error: "x" }, "*");
    else parent.postMessage({ type: "result", ok: true, svg: ${JSON.stringify(FAKE_SVG("#000003"))}, w: 40, h: 20 }, "*");
  }); parent.postMessage({ type: "ready" }, "*");`,
};

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
  // 同時に生きている枠の数の最大（図の描画の設計の 7.4 の 3）
  window.__maxFrames = 0;
  if (window === window.top) {
    new MutationObserver(() => {
      window.__maxFrames = Math.max(window.__maxFrames, document.querySelectorAll("iframe.fig-frame").length);
    }).observe(document, { childList: true, subtree: true });
  }
};

// 2 枚の PNG の違う画素の割合。端数の位置で 1 px ずれることがあるので、1 px までずらした中でいちばん小さい値をとる
function diffRatio(a, b) {
  const pa = PNG.sync.read(a), pb = PNG.sync.read(b);
  if (Math.abs(pa.width - pb.width) > 2 || Math.abs(pa.height - pb.height) > 2) return 1;
  const w = Math.min(pa.width, pb.width) - 1, h = Math.min(pa.height, pb.height) - 1;
  let best = 1;
  for (const [ax, ay, bx, by] of [[0, 0, 0, 0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1], [1, 1, 0, 0], [0, 0, 1, 1]]) {
    let bad = 0;
    for (let y = 0; y < h - 1; y++) {
      for (let x = 0; x < w - 1; x++) {
        const i = ((y + ay) * pa.width + x + ax) * 4, j = ((y + by) * pb.width + x + bx) * 4;
        if (Math.max(Math.abs(pa.data[i] - pb.data[j]), Math.abs(pa.data[i + 1] - pb.data[j + 1]),
          Math.abs(pa.data[i + 2] - pb.data[j + 2])) > 48) bad++;
      }
    }
    best = Math.min(best, bad / (w * h));
  }
  return best;
}

// 厳格な CSP のページの画像と、CSP のないページの同じ data: の画像を撮り比べる。<style> を抜いた版とも比べる
async function sameAsControl(context, img) {
  const src = await img.getAttribute("src");
  // 図の地は透明なので、対照のページの地を、入れ物（Card）の地の色にそろえる
  const [w, h, bg] = await img.evaluate((i) => [i.width, i.height, getComputedStyle(i.parentElement).backgroundColor]);
  const a = await img.screenshot();
  const shot = async (url) => {
    const p = await context.newPage();
    await p.setContent(`<!doctype html><html><body style="margin:0;background:${bg}"><img id="c" width="${w}" height="${h}"></body></html>`);
    await p.$eval("#c", (i, u) => new Promise((res) => { i.onload = res; i.onerror = res; i.src = u; }), url);
    const buf = await (await p.$("#c")).screenshot({ omitBackground: false });
    await p.close();
    return buf;
  };
  const svg = decodeURIComponent(src.slice(src.indexOf(",") + 1));
  const stripped = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg.replace(/<style[\s\S]*?<\/style>/gi, ""));
  return { same: diffRatio(a, await shot(src)), stripped: diffRatio(a, await shot(stripped)) };
}

// Mermaid の図がすべて決着した（画像か警告になり、枠が残っていない）
function settled(expected) {
  return (n) => {
    const pres = [...document.querySelectorAll("#_body pre > code.language-mermaid")].map((c) => c.parentNode);
    const done = pres.filter((p) => p.closest("details.wiki-fig-source") ||
      (p.previousElementSibling && p.previousElementSibling.classList.contains("wiki-fig-error")));
    return pres.length === n && done.length === n && document.querySelectorAll("iframe.fig-frame").length === 0;
  };
}

async function mermaidScenario(browser, base, origin, mode) {
  const context = await browser.newContext({ viewport: { width: 1200, height: 900 }, deviceScaleFactor: 1 });
  const external = [];
  const requested = [];
  await context.route("**/*", (route) => {
    const url = route.request().url();
    requested.push(url.slice(0, 200));
    if (url.startsWith("file:") || url.startsWith("data:") || url.startsWith(origin)) return route.continue();
    external.push(url);
    return route.abort();
  });
  await context.addInitScript(PROBE);
  const page = await context.newPage();
  const errors = [];
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text().slice(0, 200)); });
  page.on("pageerror", (e) => errors.push(String(e).slice(0, 200)));
  const r = {};
  await page.goto(base + "concepts/" + encodeURIComponent("流れ") + ".html");
  if (mode === "static") {
    await page.waitForTimeout(1500);
    r.static = await page.evaluate(() => ({
      frames: document.querySelectorAll("iframe").length, figures: document.querySelectorAll(".wiki-fig").length,
      codes: document.querySelectorAll("#_body pre > code.language-mermaid").length,
      styleAttrs: document.querySelectorAll("[style]").length, violations: window.__violations.slice() }));
    r.tinyRequested = requested.some((u) => u.includes("mermaid"));
    r.errors = errors;
    r.external = external;
    await context.close();
    return r;
  }
  await page.waitForFunction(settled(MERMAID_OK + MERMAID_NG), MERMAID_OK + MERMAID_NG, { timeout: 90000 });
  await page.waitForTimeout(300);
  Object.assign(r, await page.evaluate(() => {
    const ids = [...document.querySelectorAll("[id]")].map((e) => e.id);
    return {
      figures: [...document.querySelectorAll('#_body figure.wiki-fig[data-fig="mermaid"]')].map((f) => {
        const i = f.querySelector("img");
        return { cls: f.className, alt: i.alt, natural: i.naturalWidth, shown: Math.round(i.getBoundingClientRect().width) };
      }),
      sources: [...document.querySelectorAll("#_body details.fui-AccordionItem.wiki-fig-source")].map((d) => [
        d.open, !!d.querySelector("summary.fui-AccordionHeader__button .fui-AccordionHeader__expandIcon"),
        !!d.querySelector(".fui-AccordionPanel > pre > code.language-mermaid")]),
      warnings: [...document.querySelectorAll('#_body .wiki-fig-error.fui-MessageBar[data-intent="warning"]')]
        .map((b) => b.textContent),
      pythonUntouched: !!document.querySelector("#_body > pre > code.language-python"),
      styleAttrs: document.querySelectorAll("[style]").length,
      dupIds: ids.filter((x, i) => ids.indexOf(x) !== i),
      violations: window.__violations.slice(),
      maxFrames: window.__maxFrames,
    };
  }));
  // 撮る前に、コンソールのエラーを数えた（外の画像の図は、枠の中で img-src の違反を出す）
  r.errors = errors.filter((e) => !e.includes("example.invalid"));
  // 配色を変えると、すべての図を描き直す。描画の途中で 2 回変えても、生きている枠は 2 つを超えない
  const before = await page.$eval('#_body figure.wiki-fig[data-fig="mermaid"] img', (i) => i.getAttribute("src"));
  await page.evaluate(() => {
    document.documentElement.setAttribute("data-theme", "dark");
    setTimeout(() => document.documentElement.setAttribute("data-theme", "light"), 30);
    setTimeout(() => document.documentElement.setAttribute("data-theme", "dark"), 60);
  });
  await page.waitForTimeout(200);
  await page.waitForFunction(settled(MERMAID_OK + MERMAID_NG), MERMAID_OK + MERMAID_NG, { timeout: 90000 });
  await page.waitForTimeout(300);
  // 配色を変えたあとの違反とエラーも数える（撮る前）
  r.violations = await page.evaluate(() => window.__violations.slice());
  r.errors = errors.filter((e) => !e.includes("example.invalid"));
  r.afterTheme = await page.evaluate(() => ({
    maxFrames: window.__maxFrames,
    figures: document.querySelectorAll('#_body figure.wiki-fig[data-fig="mermaid"]').length,
    styleAttrs: document.querySelectorAll("[style]").length,
    styled: [...document.querySelectorAll("[style]")].map((e) => e.tagName + "." + e.className + " " + e.getAttribute("style")).slice(0, 3),
  }));
  r.themeChanged = before !== await page.$eval('#_body figure.wiki-fig[data-fig="mermaid"] img', (i) => i.getAttribute("src"));
  // 撮るのは、style と違反を数えたあとにする（Chromium は撮るときに入力欄へ空の style を付け、WebKit は CSP の違反を出す）
  const imgs = await page.$$('#_body figure.wiki-fig[data-fig="mermaid"] img');
  r.compare = imgs[0] ? await sameAsControl(context, imgs[0]) : null;
  // 枠を閉じ込めていること: 枠の中からも、枠を直接開いたページからも、トークンの付いたパスを読めない。
  // 読むのは、出力のルートの nav.js と data/search.js（ページは concepts/ にある）。親からは読めることを先に確かめる
  const frameUrl = new URL(`/_frame/${await frameVersion()}/mermaid-frame.html`, origin).href;
  const secrets = ["../nav.js", "../data/search.js"].map((p) => new URL(p, page.url()).href);
  // ページの CSP は fetch も止めるので、行き先があることはページの外（Playwright の要求）で確かめる
  r.secretsExist = await Promise.all(secrets.map((u) => context.request.get(u).then((res) => res.status(), () => 0)));
  const secret = secrets[1];
  await page.evaluate((u) => new Promise((res) => {
    const f = document.createElement("iframe");
    f.id = "probe"; f.className = "fig-frame"; f.setAttribute("sandbox", "allow-scripts"); f.onload = res; f.src = u;
    document.body.appendChild(f);
  }), frameUrl);
  const probe = page.frames().find((f) => f.url() === frameUrl);
  const tryRead = (f) => f.evaluate((u) => Promise.all([
    new Promise((res) => {
      const s = document.createElement("script");
      s.src = u; s.onload = () => res("読めた"); s.onerror = () => res("止まった");
      document.head.appendChild(s);
      setTimeout(() => res("時間切れ"), 3000);
    }),
    fetch(u).then(() => "読めた", () => "止まった"),
    Promise.resolve(document.referrer),
  ]), secret);
  r.probe = probe ? await tryRead(probe) : ["枠がない"];
  r.probeNav = probe ? await probe.evaluate((u) => new Promise((res) => {
    const s = document.createElement("script");
    s.src = u; s.onload = () => res("読めた"); s.onerror = () => res("止まった");
    document.head.appendChild(s);
    setTimeout(() => res("時間切れ"), 3000);
  }), secrets[0]) : "枠がない";
  const direct = await context.newPage();
  await direct.goto(frameUrl);
  r.direct = await tryRead(direct.mainFrame());
  await direct.close();
  r.external = external;
  await context.close();
  return r;
}

// 偽の枠で、使い切りのやり取り、時間切れ、描き直しの失敗を確かめる（図の描画の設計の 7.4 の 5〜7）
async function lifecycleScenario(browser, base, kind) {
  const context = await browser.newContext({ viewport: { width: 1200, height: 900 } });
  await context.route("**/mermaid-frame.js", (route) =>
    route.fulfill({ status: 200, contentType: "text/javascript; charset=utf-8", body: FAKE_FRAMES[kind] }));
  await context.addInitScript(PROBE);
  const page = await context.newPage();
  await page.goto(base + "concepts/" + encodeURIComponent("一つ") + ".html");
  const state = () => page.evaluate(() => {
    const img = document.querySelector('#_body figure.wiki-fig[data-fig="mermaid"] img');
    return { src: img ? decodeURIComponent(img.getAttribute("src")) : null,
             warning: document.querySelectorAll("#_body .wiki-fig-error").length,
             preInBody: !!document.querySelector("#_body > pre > code.language-mermaid"),
             details: document.querySelectorAll("#_body details.wiki-fig-source").length,
             frames: document.querySelectorAll("iframe").length };
  });
  let r;
  if (kind === "twice") {
    await page.waitForFunction(() => document.querySelector('#_body figure.wiki-fig[data-fig="mermaid"] img'), null, { timeout: 30000 });
    await page.waitForTimeout(500);
    r = await state();
    r.ok = r.src.includes("#000001") && r.frames === 0;
  } else if (kind === "broken") {
    await page.waitForFunction(() => document.querySelector("#_body .wiki-fig-error"), null, { timeout: 30000 });
    r = await state();
    r.ok = r.src === null && r.warning === 1 && r.details === 0 && r.preInBody && r.frames === 0;
  } else if (kind === "silent") {
    await page.waitForTimeout(5000);
    const early = await state();
    await page.waitForFunction(() => document.querySelector("#_body .wiki-fig-error"), null, { timeout: 30000 });
    r = await state();
    r.ok = early.warning === 0 && early.frames === 1 && r.warning === 1 && r.frames === 0 && r.preInBody;
  } else {
    await page.waitForFunction(() => document.querySelector('#_body figure.wiki-fig[data-fig="mermaid"] img'), null, { timeout: 30000 });
    await page.evaluate(() => document.documentElement.setAttribute("data-theme", "dark"));
    await page.waitForFunction(() => document.querySelector("#_body .wiki-fig-error"), null, { timeout: 30000 });
    r = await state();
    r.ok = r.src === null && r.warning === 1 && r.details === 0 && r.preInBody && r.frames === 0;
    await page.evaluate(() => document.documentElement.setAttribute("data-theme", "light"));
    await page.waitForFunction(() => document.querySelector('#_body figure.wiki-fig[data-fig="mermaid"] img'), null, { timeout: 30000 });
    const back = await state();
    r.back = back;
    r.ok = r.ok && back.warning === 0 && back.details === 1 && !back.preInBody;
  }
  r.styleAttrs = await page.evaluate(() => document.querySelectorAll("[style]").length);
  await context.close();
  return r;
}

async function frameVersion() {
  const js = (await import("node:fs")).readFileSync(
    join(REPO, "info-hive-wiki", "skills", "info-hive", "scripts", "browse_assets", "figures.js"), "utf8");
  return /var FRAME_VERSION = "([^"]+)";/.exec(js)[1];
}

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
      try {
        const m = await mermaidScenario(browser, b.base, b.origin, mode);
        run.mermaid = m;
        if (mode === "static") {
          check(m.static.frames === 0 && m.static.figures === 0 && m.static.codes === MERMAID_OK + MERMAID_NG + 0,
            `${tag}: 静的版で Mermaid に触れた: ${JSON.stringify(m.static)}`);
          check(!m.tinyRequested, `${tag}: 静的版で Mermaid を読んだ`);
          check(m.static.styleAttrs === 0 && m.static.violations.length === 0, `${tag}: 静的版の Mermaid のページに style か違反がある`);
          check(m.errors.length === 0 && m.external.length === 0, `${tag}: 静的版の Mermaid のページのエラーか外への要求: ${m.errors} ${m.external}`);
        } else {
          check(m.figures.length === MERMAID_OK, `${tag}: Mermaid の図の数が違う: ${JSON.stringify(m.figures)}`);
          check(m.figures.every((f) => f.cls === "wiki-fig fui-Card" && f.natural > 0 && f.shown > 0),
            `${tag}: Mermaid の図の画像を読めない: ${JSON.stringify(m.figures)}`);
          check(m.figures.some((f) => f.alt === "取り込みの流れ") && m.figures.filter((f) => f.alt === "図").length === 2,
            `${tag}: Mermaid の図の代替テキストが違う: ${JSON.stringify(m.figures.map((f) => f.alt))}`);
          check(m.sources.length === MERMAID_OK && m.sources.every(([open, chevron, code]) => !open && chevron && code),
            `${tag}: 図のコードの Accordion が違う: ${JSON.stringify(m.sources)}`);
          check(m.warnings.length === MERMAID_NG && m.warnings.every((t) => t.includes("図を描けなかった")),
            `${tag}: 描けない図の警告が違う: ${JSON.stringify(m.warnings)}`);
          check(m.pythonUntouched, `${tag}: Mermaid でないコードに触れた`);
          check(m.styleAttrs === 0 && m.afterTheme.styleAttrs === 0, `${tag}: Mermaid のページに style の属性がある`);
          check(m.dupIds.length === 0, `${tag}: Mermaid のページに同じ ID がある: ${m.dupIds}`);
          check(m.violations.length === 0, `${tag}: Mermaid のページに CSP の違反がある: ${m.violations}`);
          check(m.errors.length === 0, `${tag}: Mermaid のページのコンソールのエラー: ${m.errors.slice(0, 3)}`);
          check(m.external.length === 0, `${tag}: Mermaid のページが外へ要求した: ${m.external}`);
          check(m.maxFrames <= 2 && m.afterTheme.maxFrames <= 2, `${tag}: 同時に生きている枠が 2 つを超えた: ${m.afterTheme.maxFrames}`);
          // 対照との差は、端数の位置の違いで Chromium 系が 1.2% ほど。<style> を抜いた版との差は 40% を超える
          check(m.compare && m.compare.same < 0.03 && m.compare.stripped > 0.2,
            `${tag}: Mermaid の画像の中のスタイルが効いていない: ${JSON.stringify(m.compare)}`);
          check(m.themeChanged && m.afterTheme.figures === MERMAID_OK, `${tag}: 配色を変えても描き直さない`);
          check(JSON.stringify(m.secretsExist) === JSON.stringify([200, 200]),
            `${tag}: 閉じ込めの確かめの行き先が、親からも読めない: ${JSON.stringify(m.secretsExist)}`);
          check(m.probeNav === "止まった", `${tag}: 枠の中から nav.js を読めた: ${m.probeNav}`);
          check(JSON.stringify(m.probe) === JSON.stringify(["止まった", "止まった", ""]),
            `${tag}: 枠の中からトークンの付いたパスを読めた: ${JSON.stringify(m.probe)}`);
          check(m.direct[0] === "止まった" && m.direct[1] === "止まった",
            `${tag}: 枠を直接開いたページからトークンの付いたパスを読めた: ${JSON.stringify(m.direct)}`);
          run.lifecycle = {};
          for (const kind of Object.keys(FAKE_FRAMES)) {
            const l = await lifecycleScenario(browser, b.base, kind);
            run.lifecycle[kind] = l;
            check(l.ok && l.styleAttrs === 0, `${tag}: 枠の寿命（${kind}）が違う: ${JSON.stringify(l)}`);
          }
        }
      } catch (e) {
        check(false, `${tag}: Mermaid: ${String(e).slice(0, 400)}`);
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
