// 概要の実ブラウザ試験。保存は公開 API、閲覧は使い捨てのサーバーと静的版を使う（ADR-0033）。
import { chromium, firefox, webkit } from "playwright";
import { spawn, spawnSync } from "node:child_process";
import { mkdtempSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync, rmSync } from "node:fs";
import { createHash } from "node:crypto";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const REPO = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");
const SCRIPTS = join(REPO, "info-hive-wiki/skills/info-hive/scripts");
const SCRIPT = join(SCRIPTS, "wiki_browse.py");
const PYTHON = (process.env.BROWSE_PYTHON || "uv run --python 3.12 --with pyyaml==6.0.3 python").split(/\s+/);
const work = mkdtempSync(join(tmpdir(), "browse-overview-"));
const wiki = join(work, "wiki"), data = join(work, "data"), site = join(work, "site");
const env = { ...process.env, INFO_HIVE_DATA_DIR: data, PYTHONUTF8: "1", PYTHONDONTWRITEBYTECODE: "1" };
const failures = [], runs = [];
const check = (value, message) => { if (!value) failures.push(message); };
const engines = { chromium: [chromium], firefox: [firefox], webkit: [webkit],
  msedge: [chromium, { channel: "msedge" }], chrome: [chromium, { channel: "chrome" }] };
function python(args) {
  const result = spawnSync(PYTHON[0], [...PYTHON.slice(1), "-X", "utf8", "-B", ...args], { cwd: REPO, env, encoding: "utf8", timeout: 60000 });
  if (result.status !== 0) throw new Error(result.stderr || String(result.error));
  return result.stdout;
}
const FIXTURE = String.raw`
import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import wiki_overview as ov
wiki=Path(sys.argv[2]); action=sys.argv[3]
wiki.mkdir(exist_ok=True); (wiki/'concepts').mkdir(exist_ok=True)
if action=='init':
    (wiki/'SCHEMA.md').write_bytes(b'# schema\n')
    for name in ('Fresh','Stale','Broken'):
        (wiki/f'concepts/{name}.md').write_bytes(('# 資料の整理\n\n元の本文。\n').encode('utf-8'))
svg='''<svg xmlns="http://www.w3.org/2000/svg" width="720" height="140" viewBox="0 0 720 140">
<rect width="720" height="140" fill="#e5f1fb"/><text x="30" y="75" font-size="24">資料 → メモ → 一覧</text>
<image href="https://example.invalid/unwanted.png" width="1" height="1"/>
<script>document.documentElement.setAttribute('data-pwned','true');fetch('https://example.invalid/unwanted');</script></svg>'''
body='### 全体像\n\n![資料の流れ](#fig-flow)\n\n'+chr(96)*3+'mermaid\nflowchart TD\n A[資料] --> B[メモ]\n'+chr(96)*3+'\n\n'+chr(96)*3+'mermaid\nflowchart TD\n A -->\n'+chr(96)*3+'\n'
if action=='refresh': body=body.replace('全体像','更新された概要')
for name in (('Fresh','Stale','Broken') if action=='init' else ('Fresh',)):
    req=ov.begin(wiki)
    Path(req['request_path']).write_bytes(json.dumps({'format':2,'action':'create','page':name,'refresh':True,'generator':'browser-test'}).encode('utf-8'))
    ready=ov.prepare(wiki); draft=Path(ready['draft_dir'])
    (draft/'overview.md').write_bytes(body.encode('utf-8')); (draft/'flow.svg').write_bytes(svg.encode('utf-8'))
    assert ov.check(wiki,ready['work_id'])['status']=='ok'
    saved=ov.write(wiki,ready['work_id'])
    if name=='Broken': (wiki/saved['sidecar']).write_bytes(b'broken')
if action=='init':
    with (wiki/'concepts/Stale.md').open('ab') as f: f.write(b'changed')
`;
function treeHash(root) {
  const hash = createHash("sha256");
  function walk(dir) {
    for (const name of readdirSync(dir).sort()) {
      const path = join(dir, name), st = statSync(path, { bigint: true });
      hash.update(path.slice(root.length) + "\0" + st.mode + "\0" + st.mtimeNs + "\0");
      if (st.isDirectory()) walk(path); else hash.update(readFileSync(path));
    }
  }
  walk(root); return hash.digest("hex");
}
function start() {
  return new Promise((ok, fail) => {
    const child = spawn(PYTHON[0], [...PYTHON.slice(1), "-X", "utf8", "-B", SCRIPT, "serve", wiki, "--no-open"], { cwd: REPO, env });
    let out = "", err = "";
    const timer = setTimeout(() => { child.kill(); fail(new Error("serve の応答待ち: " + err)); }, 60000);
    child.stderr.on("data", s => { err += s; });
    child.stdout.on("data", s => {
      out += s; const end = out.indexOf("\n");
      if (end >= 0) { clearTimeout(timer); try { ok({ child, ...JSON.parse(out.slice(0, end)) }); } catch (e) { fail(e); } }
    });
    child.once("exit", code => { clearTimeout(timer); fail(new Error(`serve 終了 ${code}: ${err}`)); });
  });
}
const settled = () => document.querySelectorAll(".wiki-overview [data-fig=mermaid]").length === 1 &&
  document.querySelectorAll(".wiki-overview .wiki-fig-error").length === 1 && document.querySelectorAll("iframe.fig-frame").length === 0;
let server;
try {
  python(["-c", FIXTURE, SCRIPTS, wiki, "init"]);
  const before = treeHash(wiki);
  python([SCRIPT, "build", wiki, "--out", site]);
  server = await start(); check(server.reused === false, "作者のサーバーを流用した");
  const bases = { static: pathToFileURL(site + "/").href, server: server.url.replace(/index\.html$/, "") };
  for (const engine of (process.env.BROWSERS || "chromium").split(",")) {
    const [launcher, options = {}] = engines[engine];
    const browser = await launcher.launch({ headless: true, ...options });
    try {
      for (const mode of (process.env.MODES || "static,server").split(",")) {
        for (const theme of ["light", "dark"]) {
          const context = await browser.newContext({ viewport: { width: 1100, height: 900 }, colorScheme: theme });
          const external = [], errors = [];
          const origin = mode === "server" ? new URL(bases.server).origin : "file:";
          await context.route("**/*", route => {
            const url = route.request().url();
            if (url.startsWith(origin) || url.startsWith("data:")) return route.continue();
            external.push(url); return route.abort();
          });
          await context.addInitScript(() => {
            window.violations = [];
            document.addEventListener("securitypolicyviolation", e => window.violations.push(e.violatedDirective));
          });
          const page = await context.newPage();
          page.on("pageerror", e => errors.push(String(e)));
          const tag = `${engine}/${mode}/${theme}`;
          try {
            await page.goto(bases[mode] + "concepts/Fresh.html");
            const summary = page.locator(".wiki-overview > summary");
            check(await page.locator(".wiki-overview").getAttribute("open") !== null, tag + ": fresh が閉じている");
            check(await page.locator("#_body > h1 + details.wiki-overview").count() === 1, tag + ": h1直後にない");
            if (mode === "server") await page.waitForFunction(settled);
            else check(await page.locator("iframe, [data-fig=mermaid]").count() === 0, tag + ": 静的版で実行した");
            const sourceSvg = page.locator(".wiki-overview [data-fig=svg] img");
            await sourceSvg.evaluate(img => img.decode());
            check((await sourceSvg.boundingBox()).width > 100, tag + ": SVGの幅がない");
            if (mode === "server") {
              const response = await context.request.get(await sourceSvg.evaluate(img => img.src));
              check(response.status() === 200 && response.headers()["content-security-policy"].includes("sandbox"), tag + ": SVG CSP");
            }
            await page.locator("#_nav input").first().focus();
            for (let n = 0; n < 30 && !(await summary.evaluate(el => document.activeElement === el)); n++) await page.keyboard.press("Tab");
            const focus = await summary.evaluate(el => ({ active: document.activeElement === el, visible: el.matches(":focus-visible"),
              ring: getComputedStyle(el, "::after").borderTopStyle === "solid" && parseFloat(getComputedStyle(el, "::after").borderTopWidth) >= 2 }));
            if (!focus.active) throw new Error(tag + ": Tabで概要へ移れない");
            check(focus.visible && focus.ring, tag + ": Tabのフォーカス表示 " + JSON.stringify(focus));
            await page.keyboard.press("Enter");
            check(await page.locator(".wiki-overview").getAttribute("open") === null, tag + ": Enterで閉じない");
            await page.keyboard.press("Space");
            check(await page.locator(".wiki-overview").getAttribute("open") !== null, tag + ": Spaceで開かない");
            await page.setViewportSize({ width: 320, height: 800 });
            check(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), tag + ": 320pxではみ出す");
            const security = await page.evaluate(() => ({ violations: window.violations, styles: document.querySelectorAll("[style]").length, pwned: document.documentElement.hasAttribute("data-pwned") }));
            check(security.violations.length === 0 && security.styles === 0 && !security.pwned, tag + ": CSP/属性 " + JSON.stringify(security));
            if (process.env.SHOT_DIR && engine === "chromium" && mode === "server") {
              await page.setViewportSize({ width: 1100, height: 900 });
              await summary.evaluate(el => el.blur());
              mkdirSync(process.env.SHOT_DIR, { recursive: true });
              await page.screenshot({ path: join(process.env.SHOT_DIR, `overview-${theme}.png`), fullPage: true });
            }
            await page.goto(bases[mode] + "concepts/Stale.html");
            check(await page.locator(".wiki-overview").getAttribute("open") === null, tag + ": staleが開いている");
            check(await page.locator(".wiki-overview-status").isVisible(), tag + ": staleの警告が見えない");
            if (mode === "server") await page.waitForFunction(settled);
            const previousMermaid = mode === "server" ? await page.locator(".wiki-overview [data-fig=mermaid] img").getAttribute("src") : null;
            const previousSvgBackground = await page.locator(".wiki-overview [data-fig=svg]").evaluate(el => getComputedStyle(el).backgroundColor);
            await page.evaluate(value => document.documentElement.setAttribute("data-theme", value), theme === "light" ? "dark" : "light");
            if (mode === "server") {
              await page.waitForFunction(previous => {
                const img = document.querySelector(".wiki-overview [data-fig=mermaid] img");
                return img && img.getAttribute("src") !== previous && document.querySelectorAll("iframe.fig-frame").length === 0;
              }, previousMermaid);
              await page.waitForFunction(settled);
            }
            const svgBackground = await page.locator(".wiki-overview [data-fig=svg]").evaluate(el => ({
              theme: el.getAttribute("data-theme"), background: getComputedStyle(el).backgroundColor,
            }));
            check(svgBackground.theme === "light" && svgBackground.background === previousSvgBackground &&
              svgBackground.background === "rgb(255, 255, 255)", tag + ": 手書きSVGの明るい地を失った " + JSON.stringify(svgBackground));
            await page.locator(".wiki-overview > summary").click();
            await page.locator(".wiki-overview [data-fig=svg] img").evaluate(img => img.decode());
            // details の開閉は、イベントの完了と描画の更新が同じ時点ではない。最初の描画を待って測る。
            await page.waitForFunction(() => document.querySelector(".wiki-overview [data-fig=svg] img").getBoundingClientRect().width > 0,
              null, { timeout: 5000 });
            const dimensions = await page.locator(".wiki-overview [data-fig=svg] img").evaluate(img => {
              const parents = []; let node = img;
              while (node && parents.length < 5) {
                const st = getComputedStyle(node), box = node.getBoundingClientRect();
                parents.push({ tag: node.tagName, cls: node.className, width: box.width, display: st.display, cssWidth: st.width, maxWidth: st.maxWidth });
                node = node.parentElement;
              }
              return { naturalWidth: img.naturalWidth, open: img.closest("details.wiki-overview").open, parents };
            });
            check(dimensions.parents[0].width > 0, tag + ": 開いた図の読み込み後も幅0 " + JSON.stringify(dimensions));
            if (mode === "server") check((await page.locator(".wiki-overview [data-fig=mermaid] img").boundingBox()).width > 0, tag + ": 閉じたMermaidが幅0");
            check(await page.evaluate(() => window.violations.length === 0 && document.querySelectorAll("[style]").length === 0), tag + ": 配色変更後のCSP");
            await page.goto(bases[mode] + "concepts/Broken.html");
            check(await page.locator(".wiki-overview").count() === 0 && (await page.locator("#_body").innerText()).includes("概要を読めない"), tag + ": brokenを描いた");
            check(external.length === 0 && errors.length === 0, tag + ": 外部通信/例外 " + JSON.stringify({ external, errors }));
            runs.push({ engine, mode, theme, passed: !failures.some(f => f.startsWith(tag)) });
          } finally { await context.close(); }
        }
      }
    } finally { await browser.close(); }
  }
  check(treeHash(wiki) === before, "閲覧と書き出しで wiki の内容・属性が変わった");
} catch (error) { failures.push(String(error.stack || error)); }
finally {
  if (server) { try { python([SCRIPT, "stop", wiki]); } catch (e) { failures.push("stop: " + String(e)); } }
  if (process.env.OUT) writeFileSync(process.env.OUT, JSON.stringify({ runs, failures }, null, 2));
  rmSync(work, { recursive: true, force: true });
}
for (const failure of failures) console.error(failure);
console.log(JSON.stringify({ runs: runs.length, failures: failures.length }));
process.exit(failures.length ? 1 : 0);
