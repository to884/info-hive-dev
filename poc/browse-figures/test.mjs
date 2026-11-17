// 図の描画の PoC を、サーバーと file:// の 2 方式 × 5 つのブラウザで確かめる。配布対象ではない。
//
// 使い方（poc/browse-figures で）:
//   python -X utf8 setup.py <mermaid.tiny.js>
//   node test.mjs
// 環境変数:
//   BROWSERS  既定 "chromium,firefox,webkit,msedge,chrome"
//   MODES     既定 "server,file"
//   FRAME     既定 "self"。"file" で、file:// の枠の CSP に file: を足した版を使う（門 1 の下がり方）
// 結果は out/<ブラウザ>-<方式>.json に書き、最後に表を出す。
import { createRequire } from "node:module";
import { spawn } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const require = createRequire(join(HERE, "..", "..", "tests", "wiki", "browse", "package.json"));
const { chromium, firefox, webkit } = require("playwright");
const { PNG } = require("playwright-core/lib/utilsBundle");
const TYPES = { chromium: [chromium], firefox: [firefox], webkit: [webkit],
  msedge: [chromium, { channel: "msedge" }], chrome: [chromium, { channel: "chrome" }] };
const BROWSERS = (process.env.BROWSERS || "chromium,firefox,webkit,msedge,chrome").split(",");
const MODES = (process.env.MODES || "server,file").split(",");
const FRAME = process.env.FRAME || "self";
const SITE = join(HERE, "site");
const OUT = join(HERE, "out");
mkdirSync(OUT, { recursive: true });

const PROBE = () => {
  window.__v = [];
  document.addEventListener("securitypolicyviolation", (e) => window.__v.push(e.violatedDirective + " " + e.blockedURI));
};

function startServer() {
  return new Promise((resolve, reject) => {
    const p = spawn("python", ["-X", "utf8", join(HERE, "serve.py")], { cwd: HERE, stdio: ["ignore", "pipe", "inherit"] });
    p.stdout.once("data", (b) => {
      try { resolve({ proc: p, url: JSON.parse(String(b).split("\n")[0]).url }); } catch (e) { reject(e); }
    });
    p.once("error", reject);
  });
}

async function waitDone(page, renders, timeout = 60000) {
  await page.waitForFunction((n) => window.__figs && window.__figs.renders >= n && window.__figs.state === "done",
    renders, { timeout });
}

async function frameViolations(page) {
  const out = [];
  for (const f of page.frames()) {
    if (f === page.mainFrame()) continue;
    try { out.push(...await f.evaluate(() => window.__v || [])); } catch (e) { out.push("評価できない: " + e.message.split("\n")[0]); }
  }
  return out;
}

// 2 枚の PNG の画素の違い。要素の位置の端数で大きさが 1 px 違うことがあるので、重なる範囲で比べる。
// 2 px 以上違えば 1
// 端数の位置で 1 px ずれることがあるので、上下左右に 1 px までずらした中でいちばん小さい値をとる。
function diffRatio(a, b) {
  const pa = PNG.sync.read(a), pb = PNG.sync.read(b);
  if (Math.abs(pa.width - pb.width) > 1 || Math.abs(pa.height - pb.height) > 1) return 1;
  const w = Math.min(pa.width, pb.width) - 1, h = Math.min(pa.height, pb.height) - 1;
  let best = 1;
  for (const dy of [0, 1]) for (const dx of [0, 1]) for (const [sa, sb] of [[0, 0], [1, 0], [0, 1]]) {
    const ay = sa ? dy : 0, ax = sa ? dx : 0, by = sb ? dy : 0, bx = sb ? dx : 0;
    let bad = 0;
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const i = ((y + ay) * pa.width + x + ax) * 4, j = ((y + by) * pb.width + x + bx) * 4;
        const d = Math.max(Math.abs(pa.data[i] - pb.data[j]), Math.abs(pa.data[i + 1] - pb.data[j + 1]), Math.abs(pa.data[i + 2] - pb.data[j + 2]));
        if (d > 48) bad++;
      }
    }
    best = Math.min(best, bad / (w * h));
  }
  return best;
}

async function shotSame(context, page, sel, dataUrl, w, h, bg) {
  // 厳格な CSP のページの <img> と、CSP のない対照のページの同じ data: の <img> を撮り比べる。
  // 地の色をそろえるために、撮る間だけ入れ物に style を付ける（撮ったら外す）
  const el = await page.$(sel);
  await el.evaluate((img, color) => { img.parentElement.style.background = color; }, bg);
  const a = await el.screenshot();
  await el.evaluate((img) => img.parentElement.removeAttribute("style"));
  const ctl = await context.newPage();
  await ctl.setContent(`<!doctype html><html><body style="margin:0;background:${bg}"><img id="c" width="${w}" height="${h}"></body></html>`);
  await ctl.$eval("#c", (img, src) => new Promise((res) => { img.onload = res; img.onerror = res; img.src = src; }), dataUrl);
  const b = await (await ctl.$("#c")).screenshot();
  await ctl.close();
  const ratio = diffRatio(a, b);
  return { same: ratio < 0.01, ratio, a, b };
}

async function runOne(browserName, mode, server) {
  const [type, opts] = TYPES[browserName];
  const browser = await type.launch(opts || {});
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, deviceScaleFactor: 1 });
  const external = [];
  const requested = [];
  await context.route("**/*", (route) => {
    const u = route.request().url();
    requested.push(u.replace(/^data:([^,;]*).*/, "data:$1"));
    if (u.startsWith("file:") || u.startsWith("data:") || u.startsWith("blob:") || (server && u.startsWith(server.url))) return route.continue();
    external.push(u);
    return route.abort();
  });
  await context.addInitScript(PROBE);
  const page = await context.newPage();
  const consoleErrors = [];
  page.on("console", (m) => { if (m.type() === "error") consoleErrors.push(m.text().slice(0, 200)); });
  page.on("pageerror", (e) => consoleErrors.push("pageerror " + String(e).slice(0, 200)));

  const base = mode === "server" ? server.url : pathToFileURL(SITE).href + "/";
  const query = FRAME === "self" ? "" : "?frame=" + FRAME;
  const r = { browser: browserName, mode, frame: FRAME, version: browser.version(), checks: {} };
  const t0 = Date.now();
  await page.goto(base + "page.html" + query);
  try { await waitDone(page, 1); } catch (e) { r.timeout = true; }
  r.wallMs = Date.now() - t0;
  const figs = await page.evaluate(() => {
    const f = window.__figs || {};
    const res = {};
    for (const [k, v] of Object.entries(f.results || {})) res[k] = { ok: v.ok, error: v.error, foreignObject: v.foreignObject, title: v.title, length: v.length };
    return { state: f.state, tReady: f.tReady, tFirst: f.tFirst, tDone: f.tDone, frameViolations: f.frameViolations, missing: f.theme && f.theme.missing, results: res };
  });
  r.figs = figs;
  const dom = await page.evaluate(() => {
    const ids = [...document.querySelectorAll("[id]")].map((e) => e.id);
    const imgs = [...document.querySelectorAll("img.fig-img")].map((i) => ({ fig: i.closest("figure").getAttribute("data-fig"), w: i.naturalWidth, h: i.naturalHeight, alt: i.alt }));
    return {
      styleAttrs: [...document.querySelectorAll("[style]")].map((e) => e.tagName + "." + e.className).slice(0, 5),
      dupIds: ids.filter((x, i) => ids.indexOf(x) !== i),
      imgs, errors: document.querySelectorAll(".fig-error").length,
      details: document.querySelectorAll("details.fig-source").length,
      frames: document.querySelectorAll("iframe").length,
      pwned: document.documentElement.getAttribute("data-pwned"),
      parentViolations: window.__v.slice()
    };
  });
  r.dom = dom;
  r.frameViolationsProbe = await frameViolations(page);
  const svgs = await page.evaluate(() => {
    const out = {};
    for (const [k, v] of Object.entries(window.__figs.results || {})) if (v.svg) out[k] = v.svg;
    return out;
  });
  // 図の側の上書きが通っていないか（htmlLabels、forest、themeCSS の赤）
  if (svgs.override) r.override = { foreignObject: /<foreignObject/i.test(svgs.override), red: /#ff0000|rgb\(255, ?0, ?0\)|fill:red/i.test(svgs.override) };

  // 門 4: スタイルが画像の中で効いているか（対照と撮り比べ、<style> を抜いた版とは違うこと）
  const shots = {};
  const bg = "#ffffff";
  for (const [k, svg] of Object.entries(svgs)) {
    const sel = `figure[data-fig="mermaid"][data-poc-id="${k}"] img`;
    const has = await page.$(sel);
    if (!has) { shots[k] = "img がない"; continue; }
    const size = await has.evaluate((i) => [i.width, i.height]);
    const url = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
    const s = await shotSame(context, page, sel, url, size[0], size[1], bg);
    const stripped = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg.replace(/<style[\s\S]*?<\/style>/gi, ""));
    const s2 = await shotSame(context, page, sel, stripped, size[0], size[1], bg);
    shots[k] = { sameAsControl: s.same, ratio: +s.ratio.toFixed(4), differsWhenStyleRemoved: !s2.same, ratioStripped: +s2.ratio.toFixed(4) };
    if (!s.same) { writeFileSync(join(OUT, `${browserName}-${mode}-${k}-page.png`), s.a); writeFileSync(join(OUT, `${browserName}-${mode}-${k}-ctl.png`), s.b); }
  }
  {
    const sel = 'figure[data-fig="svg"] img';
    const el = await page.$(sel);
    const svgUrl = base + "fig.svg";
    // 手書きの svg は、同じファイルを data: にして対照と比べる
    const text = readFileSync(join(SITE, "fig.svg"), "utf8");
    if (el && text !== null) {
      const s = await shotSame(context, page, sel, "data:image/svg+xml;charset=utf-8," + encodeURIComponent(text), 240, 120, bg);
      shots.handSvg = { sameAsControl: s.same, ratio: +s.ratio.toFixed(4), natural: await el.evaluate((i) => i.naturalWidth) };
      if (!s.same) { writeFileSync(join(OUT, `${browserName}-${mode}-svg-page.png`), s.a); writeFileSync(join(OUT, `${browserName}-${mode}-svg-ctl.png`), s.b); }
    } else {
      shots.handSvg = { error: el ? "fig.svg を読めない" : "img がない", url: svgUrl };
    }
  }
  r.shots = shots;
  // 撮ったあとの違反（WebKit は撮るたびに出るので、撮る前の値と分けて記録する）
  r.violationsAfterShots = await page.evaluate(() => window.__v.length);

  // 門 8: 配色を変えると描き直す
  const before = await page.$eval("figure[data-fig='mermaid'] img", (i) => i.getAttribute("src")).catch(() => null);
  await page.evaluate(() => document.documentElement.setAttribute("data-theme", "dark"));
  try {
    await waitDone(page, 2, 30000);
    const after = await page.$eval("figure[data-fig='mermaid'] img", (i) => i.getAttribute("src"));
    const dark = await page.evaluate(() => ({ bg: window.__figs.theme.vars.background, dark: window.__figs.theme.vars.darkMode,
      svgCard: getComputedStyle(document.querySelector("figure[data-fig='svg']")).backgroundColor }));
    r.themeSwitch = { changed: before !== null && before !== after, ...dark };
    // 目で確かめるために、暗い配色の図を撮る
    for (const [k, sel] of [["seq", 'figure[data-poc-id="seq"]'], ["svg", 'figure[data-fig="svg"]']]) {
      const el = await page.$(sel);
      if (el) writeFileSync(join(OUT, `${browserName}-${mode}-dark-${k}.png`), await el.screenshot());
    }
  } catch (e) {
    r.themeSwitch = { error: "描き直さなかった" };
  }
  r.dom.styleAttrsAfterTheme = await page.evaluate(() => document.querySelectorAll("[style]").length);
  r.dom.styleAttrsAfterThemeList = await page.evaluate(() => [...document.querySelectorAll("[style]")].slice(0, 4).map((e) => e.tagName + "." + e.className + " " + e.getAttribute("style")));

  // 図のないページ: 枠を作らず、mermaid.tiny.js を読まない
  const n0 = requested.length;
  await page.goto(base + "page-empty.html");
  await page.waitForLoadState("load");
  r.empty = { frames: await page.evaluate(() => document.querySelectorAll("iframe").length),
              tinyRequested: requested.slice(n0).some((u) => u.includes("mermaid.tiny.js")) };

  r.consoleErrors = consoleErrors.slice();
  r.externalBeforeDirect = external.slice();
  // svg を直接開いても、中のスクリプトが動かない（サーバーは CSP の sandbox、file:// はブラウザ任せ）
  try {
    await page.goto(base + "fig.svg");
    await page.waitForTimeout(500);
    r.directSvg = { pwned: await page.evaluate(() => document.documentElement.getAttribute("data-pwned")) };
  } catch (e) {
    r.directSvg = { error: e.message.split("\n")[0] };
  }

  r.external = external;
  await browser.close();
  return r;
}

function verdict(r) {
  const res = r.figs.results || {};
  const okIds = Object.entries(res).filter(([, v]) => v.ok).map(([k]) => k);
  const ngIds = Object.entries(res).filter(([, v]) => !v.ok).map(([k]) => k);
  const shotsBad = Object.entries(r.shots).filter(([, v]) => typeof v !== "object" || v.sameAsControl === false || v.error).map(([k]) => k);
  const unstyled = Object.entries(r.shots).filter(([k, v]) => k !== "handSvg" && v && v.differsWhenStyleRemoved === false).map(([k]) => k);
  return {
    browser: r.browser, mode: r.mode, version: r.version,
    gate1_frameLoaded: r.figs.tReady != null,
    rendered: okIds.join(","), failed: ngIds.join(","),
    frameViolations: (r.figs.frameViolations || []).length + "/" + r.frameViolationsProbe.length,
    parentViolations: r.dom.parentViolations.length,
    styleAttrs: r.dom.styleAttrs.length + "/" + r.dom.styleAttrsAfterTheme,
    dupIds: r.dom.dupIds.length,
    foreignObject: Object.entries(res).filter(([, v]) => v.foreignObject).map(([k]) => k).join(","),
    override: r.override ? JSON.stringify(r.override) : "-",
    shotsBad: shotsBad.join(","), unstyled: unstyled.join(","),
    theme: r.themeSwitch.changed === true ? "ok" : JSON.stringify(r.themeSwitch),
    empty: r.empty.frames === 0 && !r.empty.tinyRequested ? "ok" : JSON.stringify(r.empty),
    directSvg: JSON.stringify(r.directSvg), pwnedInPage: r.dom.pwned,
    external: r.externalBeforeDirect.length + "/" + r.external.length, console: r.consoleErrors.length,
    tReady: Math.round(r.figs.tReady || -1), tFirst: Math.round(r.figs.tFirst || -1), tDone: Math.round(r.figs.tDone || -1)
  };
}

const server = MODES.includes("server") ? await startServer() : null;
const rows = [];
try {
  for (const b of BROWSERS) {
    for (const m of MODES) {
      let r;
      try { r = await runOne(b, m, m === "server" ? server : null); } catch (e) { r = { browser: b, mode: m, fatal: String(e).slice(0, 400) }; }
      writeFileSync(join(OUT, `${b}-${m}${FRAME === "self" ? "" : "-frame" + FRAME}.json`), JSON.stringify(r, null, 2));
      const v = r.fatal ? { browser: b, mode: m, fatal: r.fatal } : verdict(r);
      rows.push(v);
      console.log(JSON.stringify(v));
    }
  }
} finally {
  if (server) server.proc.kill();
}
writeFileSync(join(OUT, `summary${FRAME === "self" ? "" : "-frame" + FRAME}.json`), JSON.stringify(rows, null, 2));
