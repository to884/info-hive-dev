// 探しやすさ（docs/plans/wiki-browse-findability-2026-11-13.md の 9 節）と Fluent 2（wiki-browse-fluent2-2026-11-14.md の
// 6 節）のブラウザでの試験。試験用の小さな Wiki を、静的の書き出し（file://）とサーバー（http://127.0.0.1）で開く。
// 1 つでも外れれば、終了コードを 1 にする。
//
// 使い方（開発リポジトリのルートで）:
//   cd tests/wiki/browse && npm ci && node findability.test.mjs
// 環境変数は browse.test.mjs と同じ（BROWSE_PYTHON、MODES、BROWSERS、OUT）。
import { chromium, firefox, webkit } from "playwright";
import { spawn, spawnSync } from "node:child_process";
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync } from "node:fs";
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

const failures = [];
const notes = [];
function check(cond, message) { if (!cond) failures.push(message); return cond; }

// --- 試験用の Wiki ---

const work = mkdtempSync(join(tmpdir(), "browse-find-"));
const wiki = join(work, "wiki");
const data = join(work, "data");
function put(rel, text) {
  const p = join(wiki, rel);
  mkdirSync(dirname(p), { recursive: true });
  writeFileSync(p, text, "utf8");
}
function pg(meta, body) {
  return ["---", ...Object.entries(meta).map(([k, v]) => `${k}: ${JSON.stringify(v)}`), "---", "", body, ""].join("\n");
}
const NFD = "カイド";   // 「カイド」を NFD で書いたもの
put("SCHEMA.md", "# スキーマ\n");
put("index.md", ["# 索引", "- [[bm25]]: 索引の行の要約", "## 第一", "- [[two]]", "## 第二", "- [[two]]", "- [[strasse]]",
  "- [[indexes/x]]: 分割の索引", "- [[ない]]", ""].join("\n"));
put("indexes/x.md", "# X の索引\n- [[istanbul]]\n- [[abc]]\n");
put("concepts/bm25.md", pg({ type: "concept", title: "BM25", tags: ["検索", "ランキング"], updated: "2026-04-18" },
  "# BM25\n\n語の頻度で点数を付ける。\n\n## 語の頻度\n\n本文。"));
put("concepts/two.md", pg({ type: "concept", title: "ΟΣ", updated: "2026-05-01" }, "# ΟΣ\n\n二つのグループに載る。"));
put("concepts/strasse.md", pg({ type: "__proto__", title: "Straße", updated: "2025-01-01" }, "# Straße\n\n通り。"));
put("concepts/istanbul.md", pg({ type: "entity", title: "İstanbul", tags: ["__proto__", "toString"] }, "# İstanbul\n\n街。"));
put("concepts/abc.md", pg({ type: "concept", title: "abcdef" }, "# abcdef\n\n文字。"));
put("concepts/nfd.md", pg({ type: "concept", title: NFD, tags: [NFD] }, `# ${NFD}\n\n## 固有の語ズズズ\n\n本文。`));
put("concepts/note.md", pg({ type: "note", title: "ノートの種類" }, "# ノートの種類\n\n知らない種類。"));
put("concepts/long.md", pg({ type: "W".repeat(120), title: "長い値", tags: ["W".repeat(200)] }, "# 長い値\n\n本文。"));

function python(args) {
  return spawnSync(PYTHON[0], [...PYTHON.slice(1), "-X", "utf8", SCRIPT, ...args],
    { encoding: "utf8", env: { ...process.env, INFO_HIVE_DATA_DIR: data } });
}
function startServer() {
  return new Promise((ok, fail) => {
    const child = spawn(PYTHON[0], [...PYTHON.slice(1), "-X", "utf8", SCRIPT, "serve", wiki, "--no-open"],
      { env: { ...process.env, INFO_HIVE_DATA_DIR: data }, stdio: ["ignore", "pipe", "pipe"] });
    let buf = "", err = "";
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
async function stopServer(s) {
  const stopped = python(["stop", wiki]);
  check(stopped.status === 0, "stop が失敗した: " + stopped.stderr);
  try { s.child.kill(); } catch { /* 終わっている */ }
}

// --- 状態とコントラストを取り出す ---

const INIT = `(() => {
  window.__csp = [];
  document.addEventListener("securitypolicyviolation", (e) => window.__csp.push(e.violatedDirective + " " + e.blockedURI));
  window.__ratio = (el) => {
    const rgb = (s) => { const m = s.match(/[\\d.]+/g); return m ? m.slice(0, 4).map(Number) : [0, 0, 0, 1]; };
    const f = (c) => { c /= 255; return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };
    const lum = ([r, g, b]) => 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
    let bg = [255, 255, 255];
    for (let e = el; e; e = e.parentElement) {
      const c = rgb(getComputedStyle(e).backgroundColor);
      if (c.length < 4 || c[3] > 0) { bg = c; break; }
    }
    const a = lum(rgb(getComputedStyle(el).color)), b = lum(bg);
    return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
  };
  window.__textRatio = (root) => Math.min(...[root, ...root.querySelectorAll("*")]
    .filter((x) => x.offsetParent !== null && [...x.childNodes].some((c) => c.nodeType === 3 && c.textContent.trim()))
    .map(window.__ratio), 99);
  window.__health = () => {
    const ids = Array.from(document.querySelectorAll("[id]"), (n) => n.id);
    return { style: document.querySelectorAll("[style]").length, dupIds: ids.filter((x, i) => ids.indexOf(x) !== i),
             csp: window.__csp.slice(), errors: (window.__browse && window.__browse.errors) || [] };
  };
})();`;

const CONTRAST = ["#_body p", "#_body h2", "#_scope .fui-Badge", ".fui-NavSubItem", ".fui-NavSubItem.is-current",
  ".fui-NavCategoryItem .tree-name", ".tree-count", "#_meta th", ".fui-MessageBarBody", ".t-concept", ".t-entity",
  ".t-other", ".fui-Tag__primaryText", ".ix-summary", ".ix-title", ".fx-path", "#_backlinks a", ".sr-title", ".sr-meta",
  ".chips .fui-ToggleButton", "#_theme", "#_body .wl-unresolved"];

async function contrastOf(page) {
  return page.evaluate((sels) => {
    const out = {};
    for (const s of sels) {
      const all = Array.from(document.querySelectorAll(s)).filter((e) => e.offsetParent !== null && e.textContent.trim());
      if (all.length) { out[s] = Math.min(...all.map(window.__ratio)); }
    }
    return out;
  }, CONTRAST);
}

// 地が状態で変わりうる入れ物のすべてにポインターを置き、押したままでも測る（Fluent 2 の設計の 4.2、6）
async function stateContrast(page) {
  const sel = "#_main tr, #_main li, #_nav li, a, summary, button, .fui-NavItem, .fui-NavSubItem, .fui-Select";
  const n = await page.locator(sel).count();
  let min = 99, where = "";
  for (let i = 0; i < n; i++) {
    const loc = page.locator(sel).nth(i);
    if (!(await loc.isVisible())) continue;
    await loc.hover();
    const r1 = await loc.evaluate((e) => window.__textRatio(e));
    await page.mouse.down();
    const r2 = await loc.evaluate((e) => window.__textRatio(e));
    await page.mouse.move(0, 0);
    await page.mouse.up();
    const r = Math.min(r1, r2);
    if (r < min) { min = r; where = await loc.evaluate((e) => e.tagName + "." + (typeof e.className === "string" ? e.className : "")); }
  }
  return { min, where };
}

function url(base, rel) { return base + rel.split("/").map(encodeURIComponent).join("/"); }

async function newPage(browser, opts = {}) {
  const context = await browser.newContext({ viewport: { width: opts.width || 1280, height: 900 },
    colorScheme: opts.dark ? "dark" : "light", forcedColors: opts.forced ? "active" : "none" });
  await context.addInitScript(INIT);
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  return { context, page, errors };
}

async function articleChecks(browser, base, tag) {
  const { context, page, errors } = await newPage(browser);
  const requests = [];
  page.on("request", (r) => requests.push(r.url()));
  await page.goto(url(base, "concepts/two.html"));
  // 2 つのグループに載ったページ: 2 つのグループがどちらも開き、どちらの項目にも aria-current がある
  const tree = await page.evaluate(() => ({
    current: document.querySelectorAll('.fui-NavSubItem[aria-current="page"]').length,
    open: Array.from(document.querySelectorAll("details.tree-group[open] > summary .tree-name"), (n) => n.textContent),
  }));
  check(tree.current === 2, `${tag}: 2 つのグループの今のページの印が ${tree.current} 個`);
  check(tree.open.includes("第一") && tree.open.includes("第二"), `${tag}: 今のページのグループが開いていない: ${tree.open}`);
  // 後からの読み込み: フォーカスの前に search.js を読まない
  check(!requests.some((u) => u.includes("search.js")), `${tag}: フォーカスの前に search.js を読んだ`);
  await page.focus("#_q");
  await page.waitForFunction(() => window.__browse.searchLoaded);
  check(requests.some((u) => u.includes("search.js")), `${tag}: フォーカスしても search.js を読まない`);
  const S = (q) => page.evaluate((x) => window.__browse.search(x), q);
  const titles = async (q) => (await S(q)).map((r) => r.title);
  check((await titles("カイド"))[0] === "カイド", `${tag}: NFD の題名に NFC の語で当たらない`);
  check((await titles(NFD))[0] === "カイド", `${tag}: NFD の語で当たらない`);
  check((await titles("STRASSE")).includes("Straße"), `${tag}: STRASSE で Straße に当たらない`);
  check((await titles("ος")).includes("ΟΣ"), `${tag}: ος で ΟΣ に当たらない`);
  check((await titles("i̇st")).includes("İstanbul"), `${tag}: i̇st で İstanbul に当たらない`);
  check((await titles("bm25 頻度")).join() === "BM25", `${tag}: 2 語の AND が違う`);
  check((await titles("bm25　頻度")).join() === "BM25", `${tag}: 全角の空白で区切れない`);
  check((await S("zzzz")).length === 0, `${tag}: 0 件にならない`);
  const zu = await S("ズズズ");
  check(zu.length === 1 && zu[0].hit && zu[0].hit.field === "heading" && zu[0].href.includes("#"),
    `${tag}: 見出しだけにある語の hit と href が違う: ${JSON.stringify(zu)}`);
  check(JSON.stringify(Object.keys(zu[0] || {}).slice(0, 10)) ===
    JSON.stringify(["rel_path", "title", "type", "tags", "updated", "score", "snippet", "heading_path", "href", "hit"]),
    `${tag}: search() の欄が契約と違う`);
  // 強調: 範囲をつないで 1 つの mark にする
  await page.fill("#_q", "abc cdef");
  const marks = await page.evaluate(() => Array.from(document.querySelectorAll(".sr-title mark"), (m) => m.textContent));
  check(marks.length === 1 && marks[0] === "abcdef", `${tag}: 重なる範囲の mark が 1 つにならない: ${marks}`);
  await page.fill("#_q", "ος");
  const greek = await page.evaluate(() => Array.from(document.querySelectorAll(".sr-title mark"), (m) => m.textContent));
  check(greek.includes("ΟΣ"), `${tag}: ΟΣ に mark が付かない: ${greek}`);
  await page.fill("#_q", "zzzz");
  check(await page.locator(".sr-empty").count() === 1, `${tag}: 0 件の表示がない`);
  // 変換中の Enter と Esc は扱わない
  await page.fill("#_q", "検索");
  const before = page.url();
  for (const [key, composing, code] of [["Enter", true, 13], ["Escape", false, 229], ["Enter", false, 229]]) {
    await page.evaluate(([k, c, kc]) => {
      const ev = new KeyboardEvent("keydown", { key: k, isComposing: c, bubbles: true, cancelable: true });
      Object.defineProperty(ev, "keyCode", { get: () => kc });
      document.getElementById("_q").dispatchEvent(ev);
    }, [key, composing, code]);
  }
  await page.waitForTimeout(200);
  check(page.url() === before && (await page.inputValue("#_q")) === "検索", `${tag}: 変換中のキーで移動したか、欄が空になった`);
  const health = await page.evaluate(() => window.__health());
  check(health.style === 0 && health.dupIds.length === 0 && health.csp.length === 0 && health.errors.length === 0,
    `${tag}: 記事のページの [style]、ID の重複、CSP、画面のエラー: ${JSON.stringify(health)}`);
  check(errors.length === 0, `${tag}: コンソールのエラー: ${errors.slice(0, 3)}`);
  await context.close();
}

async function indexChecks(browser, base, tag) {
  const { context, page, errors } = await newPage(browser);
  await page.goto(url(base, "index.html"));
  const total = await page.locator("#_index .fx-row").count();
  const chips = await page.locator(".chips .fui-ToggleButton").allTextContents();
  check(chips.includes("__proto__"), `${tag}: 種類 __proto__ のボタンがない: ${chips}`);
  const tagOpts = await page.locator(".tag-select option").allTextContents();
  check(tagOpts.includes("__proto__（1）") && tagOpts.includes("toString（1）"), `${tag}: タグの選択が違う: ${tagOpts}`);
  await page.click(".chips .fui-ToggleButton:text-is('エンティティ')");
  check((await page.textContent("#_count")) === `${total} 件中 1 件`, `${tag}: 種類で絞った件数が違う`);
  await page.click(".chips .fui-ToggleButton:text-is('すべて')");
  await page.selectOption(".tag-select select", { label: "toString（1）" });
  check((await page.textContent("#_count")) === `${total} 件中 1 件`, `${tag}: タグで絞った件数が違う`);
  await page.selectOption(".tag-select select", { index: 0 });
  // グループ（#group=）。第一には two だけが載る
  const firstId = await page.evaluate(() => {
    const walk = (gs) => { for (const g of gs) { if (g.title === "第一") return g.id; const r = walk(g.children); if (r) return r; } return null; };
    return walk(window.WIKI_NAV.groups);
  });
  await page.evaluate((id) => { location.hash = "#group=" + id; }, firstId);
  await page.waitForTimeout(100);
  check((await page.textContent("#_count")) === `${total} 件中 1 件`, `${tag}: グループで絞った件数が違う`);
  check(await page.locator(".group-chip:visible").count() === 1, `${tag}: グループの印が出ない`);
  await page.evaluate((id) => { location.hash = "#group=" + id + "garbage"; }, firstId);
  await page.waitForTimeout(100);
  check((await page.textContent("#_count")) === `${total} 件`, `${tag}: 知らない ID で絞った`);
  // 並べ方
  await page.selectOption(".sort-select select", "updated");
  const upd = await page.evaluate(() => Array.from(document.querySelectorAll("#_index .fx-row"), (r) => r.getAttribute("data-updated")));
  const nonEmpty = upd.filter(Boolean);
  check(JSON.stringify(nonEmpty) === JSON.stringify(nonEmpty.slice().sort().reverse()) && upd.slice(nonEmpty.length).every((x) => !x),
    `${tag}: 更新の新しい順が違う: ${upd}`);
  // 並べ替えたあとの Enter は、いま見えている先頭の行を開く（1 回目の実装のレビューの A）
  await page.selectOption(".sort-select select", "title");
  const firstHref = await page.evaluate(() => document.querySelector("#_index .fx-row:not([hidden]) .ix-title").href);
  await page.focus("#_q");
  await Promise.all([page.waitForURL((u) => u.href !== page.url(), { timeout: 5000 }).catch(() => {}),
                     page.keyboard.press("Enter")]);
  check(page.url() === firstHref, `${tag}: 並べ替えたあとの Enter が見えている先頭の行を開かない: ${page.url()} != ${firstHref}`);
  await page.goto(url(base, "index.html"));
  await page.waitForFunction(() => window.__browse.navLoaded);
  // 知らない種類の札は、中立の色（Fluent の既定の brand の色にしない）
  const badge = await page.evaluate(() => ({
    note: getComputedStyle(document.querySelector(".badge.t-note")).backgroundColor,
    other: getComputedStyle(document.querySelector(".badge.t-other")).backgroundColor,
    concept: getComputedStyle(document.querySelector(".badge.t-concept")).backgroundColor,
  }));
  check(badge.note === badge.other && badge.note !== badge.concept, `${tag}: 知らない種類の札の色が違う: ${JSON.stringify(badge)}`);
  // 検索での絞り込み
  await page.focus("#_q");
  await page.fill("#_q", "カイド");
  await page.waitForFunction(() => window.__browse.searchLoaded);
  await page.waitForTimeout(100);
  check((await page.textContent("#_count")).startsWith(`${total} 件中 1 件`), `${tag}: 検索で絞った件数が違う`);
  const health = await page.evaluate(() => window.__health());
  check(health.style === 0 && health.dupIds.length === 0 && health.csp.length === 0 && health.errors.length === 0,
    `${tag}: 索引のページの [style]、ID の重複、CSP、画面のエラー: ${JSON.stringify(health)}`);
  check(errors.length === 0, `${tag}: コンソールのエラー: ${errors.slice(0, 3)}`);
  await context.close();
}

async function loadingChecks(browser, base, tag) {
  // search.js を読めない（file:// は abort、サーバーは 404）とき、欄を使えなくし、コンソールにエラーを出さない
  {
    const { context, page } = await newPage(browser);
    const errors = [];
    page.on("pageerror", (e) => errors.push(String(e)));
    await page.route("**/data/search.js", (r) => (base.startsWith("file:") ? r.abort() : r.fulfill({ status: 404, body: "" })));
    await page.goto(url(base, "concepts/bm25.html"));
    await page.focus("#_q");
    await page.waitForTimeout(500);
    const r = await page.evaluate(() => ({ disabled: document.getElementById("_q").disabled,
      hint: (document.querySelector(".search-hint") || {}).textContent }));
    check(r.disabled && r.hint === "検索の索引を読めない", `${tag}: 読めない検索の索引の表示が違う: ${JSON.stringify(r)}`);
    check(errors.length === 0, `${tag}: 読めない検索の索引でページのエラー: ${errors}`);
    await context.close();
  }
  // 遅れて届く search.js: 読み終わるまでに打った語を、読み終わったときに照らす。世代が違えば知らせる
  {
    const { context, page } = await newPage(browser);
    await page.route("**/data/search.js", async (r) => {
      const u = r.request().url();
      const text = u.startsWith("file:") ? readFileSync(fileURLToPath(u), "utf8") : await (await r.fetch()).text();
      await new Promise((ok) => setTimeout(ok, 600));
      await r.fulfill({ status: 200, contentType: "text/javascript; charset=utf-8",
        body: text.replace(/"generation":"[^"]*"/, '"generation":"other"') });
    });
    await page.goto(url(base, "concepts/bm25.html"));
    await page.focus("#_q");
    await page.keyboard.type("カイド");
    await page.waitForFunction(() => window.__browse.searchLoaded, null, { timeout: 5000 });
    await page.waitForTimeout(100);
    const r = await page.evaluate(() => ({ results: document.querySelectorAll(".sr-results li").length,
      mismatch: window.__browse.mismatch, notice: !!document.querySelector(".notice-updated") }));
    check(r.results === 1 && r.mismatch.includes("WIKI_SEARCH") && r.notice, `${tag}: 遅れて届く検索の索引の扱いが違う: ${JSON.stringify(r)}`);
    await context.close();
  }
}

async function layoutChecks(browser, base, tag) {
  for (const [width, open] of [[360, false], [320, false], [1000, true]]) {
    for (const rel of ["concepts/bm25.html", "index.html", "concepts/long.html"]) {
      const { context, page } = await newPage(browser, { width });
      await page.goto(url(base, rel));
      const r = await page.evaluate(() => {
        const main = document.getElementById("_main");
        return { drawer: document.querySelector("details.drawer").open,
                 main: main.scrollWidth > main.clientWidth + 1,
                 page: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1 };
      });
      check(r.drawer === open, `${tag}: 幅 ${width} の ${rel} で「メニュー」の開閉が違う`);
      check(!r.main && !r.page, `${tag}: 幅 ${width} の ${rel} で横にはみ出す`);
      await context.close();
    }
  }
  // スクリプトなし: 配色は auto、索引の一覧はすべて読める
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto(url(base, "index.html"));
  const r = await page.evaluate(() => ({ theme: document.documentElement.getAttribute("data-theme"),
    rows: document.querySelectorAll("#_index .fx-row").length, titles: document.querySelectorAll("#_index .ix-title").length }));
  check(r.theme === "auto" && r.rows === 8 && r.titles === 8, `${tag}: スクリプトなしの索引のページが違う: ${JSON.stringify(r)}`);
  await context.close();
}

async function colorChecks(browser, base, tag) {
  for (const dark of [false, true]) {
    for (const rel of ["concepts/bm25.html", "index.html"]) {
      const { context, page } = await newPage(browser, { dark });
      await page.goto(url(base, rel));
      if (rel !== "index.html") {
        await page.focus("#_q");
        await page.fill("#_q", "検索");
        await page.waitForFunction(() => window.__browse.searchLoaded);
      }
      const c = await contrastOf(page);
      const low = Object.entries(c).filter(([, v]) => v < 4.5);
      check(low.length === 0, `${tag}: ${dark ? "暗い" : "明るい"}配色の ${rel} でコントラスト比が 4.5 を割る: ${JSON.stringify(low)}`);
      const s = await stateContrast(page);
      check(s.min >= 4.5, `${tag}: ${dark ? "暗い" : "明るい"}配色の ${rel} で、ポインターか押下の状態のコントラスト比が ${s.min.toFixed(2)}（${s.where}）`);
      notes.push(`${tag} ${dark ? "dark" : "light"} ${rel}: 最小 ${Math.min(...Object.values(c)).toFixed(2)}、状態 ${s.min.toFixed(2)}`);
      await context.close();
    }
  }
  // 強制カラー: 今のページの項目に輪郭がある
  const { context, page } = await newPage(browser, { forced: true });
  await page.goto(url(base, "concepts/bm25.html"));
  const outline = await page.evaluate(() => getComputedStyle(document.querySelector(".fui-NavSubItem.is-current")).outlineStyle);
  check(outline !== "none", `${tag}: 強制カラーで今のページの印がない`);
  await context.close();
}

async function themeChecks(browser, base, tag, restart) {
  const context = await browser.newContext({ colorScheme: "light" });
  await context.addInitScript(INIT);
  const page = await context.newPage();
  await page.goto(url(base, "concepts/bm25.html"));
  check((await page.getAttribute("html", "data-theme")) === "auto", `${tag}: 既定の配色が auto でない`);
  await page.selectOption("#_theme", "dark");
  await page.goto(url(base, "index.html"));
  check((await page.getAttribute("html", "data-theme")) === "dark", `${tag}: 選んだ配色がページを移ると消える`);
  if (restart) {
    base = await restart();
    await page.goto(url(base, "index.html"));
    check((await page.getAttribute("html", "data-theme")) === "dark", `${tag}: サーバーを起動し直すと選んだ配色が消える`);
  }
  await context.close();
  // 保存先が例外を出す
  const c2 = await browser.newContext({ colorScheme: "light" });
  await c2.addInitScript(() => {
    Object.defineProperty(window, "localStorage", { get() { throw new Error("blocked"); } });
    Object.defineProperty(Document.prototype, "cookie", { get() { throw new Error("blocked"); }, set() { throw new Error("blocked"); } });
  });
  const p2 = await c2.newPage();
  const errors = [];
  p2.on("pageerror", (e) => errors.push(String(e)));
  await p2.goto(url(base, "concepts/bm25.html"));
  await p2.selectOption("#_theme", "dark");
  const chosen = await p2.getAttribute("html", "data-theme");
  await p2.reload();
  const after = await p2.getAttribute("html", "data-theme");
  check(chosen === "dark" && after === "auto" && errors.length === 0,
    `${tag}: 保存先が例外を出すときの扱いが違う: ${chosen} ${after} ${errors}`);
  await c2.close();
}

// --- 流す ---

let server = null;
try {
  const bases = {};
  if (MODES.includes("static")) {
    const site = join(work, "site");
    const built = python(["build", wiki, "--out", site, "--raw", "text"]);
    if (!check(built.status === 0, "静的の書き出しが失敗した: " + built.stderr)) throw new Error(built.stderr);
    bases.static = pathToFileURL(site).href + "/";
  }
  if (MODES.includes("server")) {
    server = await startServer();
    bases.server = server.url.replace(/[^/]*$/, "");
  }
  for (const name of BROWSERS) {
    const [type, opts] = ENGINES[name];
    let browser;
    try { browser = await type.launch(opts || {}); } catch (e) { check(false, `${name} を起動できない: ${e}`); continue; }
    for (const [mode, base] of Object.entries(bases)) {
      const tag = `${name}/${mode}`;
      try {
        await articleChecks(browser, base, tag);
        await indexChecks(browser, base, tag);
        await loadingChecks(browser, base, tag);
        await layoutChecks(browser, base, tag);
        await colorChecks(browser, base, tag);
        const restart = mode === "server" ? async () => {
          await stopServer(server);
          // 止めたサーバーが終わりきる前に起動すると、終わりかけのサーバーを使い回す。新しいサーバーになるまで待つ
          for (let k = 0; k < 20; k++) {
            server = await startServer();
            if (!server.reused) break;
            try { server.child.kill(); } catch { /* 終わっている */ }
            await new Promise((ok) => setTimeout(ok, 500));
          }
          check(!server.reused, "起動し直しても、前のサーバーを使い回した");
          check(server.port !== undefined, "起動し直したサーバーのポートがない");
          return server.url.replace(/[^/]*$/, "");
        } : null;
        await themeChecks(browser, base, tag, restart);
        if (restart) { bases.server = server.url.replace(/[^/]*$/, ""); }
      } catch (e) {
        check(false, `${tag}: ${String(e).slice(0, 400)}`);
      }
    }
    await browser.close();
  }
} catch (e) {
  check(false, String(e));
} finally {
  if (server) { await stopServer(server); }
}
const results = { failures, notes };
if (process.env.OUT) writeFileSync(process.env.OUT, JSON.stringify(results, null, 2), "utf8");
console.log(JSON.stringify(results, null, 1));
try { rmSync(work, { recursive: true, force: true }); } catch { /* Windows で掴まれていれば残す */ }
process.exit(failures.length ? 1 : 0);
