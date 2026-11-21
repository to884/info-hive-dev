// 探しやすさ（docs/plans/wiki-browse-findability-2026-11-13.md の 9 節）と Fluent 2（wiki-browse-fluent2-2026-11-14.md の
// 6 節）のブラウザでの試験。試験用の小さな Wiki を、静的の書き出し（file://）とサーバー（http://127.0.0.1）で開く。
// 1 つでも外れれば、終了コードを 1 にする。
//
// 使い方（開発リポジトリのルートで）:
//   cd tests/wiki/browse && npm ci && node findability.test.mjs
// 環境変数は browse.test.mjs と同じ（BROWSE_PYTHON、MODES、BROWSERS、OUT）。
import { chromium, firefox, webkit } from "playwright";
import { spawn, spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
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
// 深い段（左のペインの木の設計の 2.3）: h1〜h6 の見出し。最初の見出しの前にも項目を置き、N3 で畳まれないようにする。
// abc の木は、ファイル（1）› D1〜D6（2〜7）› タグなし（8）› abc（9）の 9 段になる
put("indexes/deep.md", ["- [[abc]]", "# D1", "## D2", "### D3", "#### D4", "##### D5", "###### D6", "- [[abc]]", ""].join("\n"));
put("concepts/bm25.md", pg({ type: "concept", title: "BM25", tags: ["検索", "ランキング"], updated: "2026-04-18" },
  "# BM25\n\n語の頻度で点数を付ける。[[未作成のページ]] はまだない。\n\n## 語の頻度\n\n本文。"));
put("concepts/two.md", pg({ type: "concept", title: "ΟΣ", updated: "2026-05-01" }, "# ΟΣ\n\n二つのグループに載る。[[bm25]] を見る。"));
put("concepts/strasse.md", pg({ type: "__proto__", title: "Straße", updated: "2025-01-01" }, "# Straße\n\n通り。"));
put("concepts/istanbul.md", pg({ type: "entity", title: "İstanbul", tags: ["__proto__", "toString"] }, "# İstanbul\n\n街。"));
put("concepts/abc.md", pg({ type: "concept", title: "abcdef" }, "# abcdef\n\n文字。"));
put("concepts/nfd.md", pg({ type: "concept", title: NFD, tags: [NFD] }, `# ${NFD}\n\n## 固有の語ズズズ\n\n本文。`));
put("sources/src.md", pg({ type: "source", title: "ソースの例" }, "# ソースの例\n\nソース。"));
put("synthesis/syn.md", pg({ type: "synthesis", title: "シンセシスの例" }, "# シンセシスの例\n\nまとめ。"));
put("concepts/note.md", pg({ type: "note", title: "ノートの種類" }, "# ノートの種類\n\n知らない種類。"));
// 長い値: 種類、タグ、題名、要約、出典の題名。本文から関係のページへ（被リンクの題名）と、長い未解決のリンク（診断）
const LONG_TITLE = "長い値" + "L".repeat(150);
put("concepts/long.md", pg({ type: "W".repeat(120), title: LONG_TITLE, tags: ["W".repeat(200)],
  summary: "要約の長い文。" + "S".repeat(200), sources: ["sources/longsrc"] },
  `# ${LONG_TITLE}\n\n本文。[[rel]] を見る。[[${"D".repeat(150)}]] はない。`));
put("sources/longsrc.md", pg({ type: "source", title: "出典" + "T".repeat(150) }, "# 長い出典\n\n出典。"));
// 記事のページの部品（Fluent 2 の設計の 5）: メタ欄の出典のリンク、関係表（長い値を含む 9 列）、本文の見出し、表、引用、
// コード、区切り、見出しのない行き先と曖昧なリンク。関係表は graph/ontology.yaml があるときだけ描かれる
put("graph/ontology.yaml", "node_types:\n  concept: {}\n  source: {}\npredicates:\n  uses: {}\n");
put("concepts/rel.md", ["---", 'type: "concept"', 'title: "関係の例"', 'sources: ["sources/src"]', "graph:", "  relationships:",
  "    - predicate: uses", "      object: concept:bm25", "      source: sources/src", "      confidence: 0.9",
  `      evidence: "${"Y".repeat(150)}"`,
  "    - predicate: uses", "      object: concept:まだない", "      status: active",
  `      evidence: "${"関係の証拠の長い日本語の文。".repeat(12)}"`,
  "---", "", "# 関係の例", "", "[[bm25]] と [[two#ない見出し]] と [[dup]] と [[まだないページ]] と [外](https://example.invalid/) を見る。", "",
  "## 表と引用", "", "| 左 | 中 | 右 |", "| :--- | :---: | ---: |", "| 一 | 二 | 三 |", "",
  "> 引用の段落。", "", "`インラインのコード` を書く。", "", "```", "整形済みのコード", "```", "", "---", "",
  "### 三段目", "", "本文。", "", "#### 四段目", "", "本文。", ""].join("\n"));
put("a/dup.md", "# 同名 A\n");
put("b/dup.md", "# 同名 B\n");
const PAGES = 14;

function python(args) {
  return spawnSync(PYTHON[0], [...PYTHON.slice(1), "-X", "utf8", SCRIPT, ...args],
    { encoding: "utf8", env: { ...process.env, INFO_HIVE_DATA_DIR: data } });
}
function startServer() {
  return new Promise((ok, fail) => {
    const child = spawn(PYTHON[0], [...PYTHON.slice(1), "-X", "utf8", SCRIPT, "serve", wiki, "--no-open", "--scope", "project"],
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
  window.__settled = async () => {
    await new Promise((ok) => requestAnimationFrame(() => ok()));
    await Promise.all(document.getAnimations().map((a) => a.finished.catch(() => {})));
  };
  window.__health = () => {
    const ids = Array.from(document.querySelectorAll("[id]"), (n) => n.id);
    return { style: document.querySelectorAll("[style]").length, dupIds: ids.filter((x, i) => ids.indexOf(x) !== i),
             csp: window.__csp.slice(), errors: (window.__browse && window.__browse.errors) || [] };
  };
})();`;

// 左の木は Tree の部品（左のペインの木の設計の 2、6）。葉の名前、今の項目、枝の名前、件数のバッジ、索引のページのグループの葉
const CONTRAST = ["#_body p", "#_body h2", "#_scope .fui-Badge",
  ".tree .fui-TreeItem.is-current .fui-TreeItemLayout__main", ".tree-group .tree-name", ".tree .tree-count",
  ".tree-index .tree-name", ".nav-home", "#_meta th", ".t-concept", ".t-entity", ".t-source",
  ".t-synthesis", ".t-other", ".fui-Tag__primaryText", ".ix-summary", ".ix-title", ".fx-path", "#_backlinks a", ".sr-title", ".sr-meta",
  ".chips .fui-ToggleButton", ".theme-label", "#_body .wl-unresolved",
  // 記事のページの部品（F2）
  "#_body h1", "#_body h3", "#_body h4", "#_body a", "#_body .wl-ambiguous", "#_body .wl-missing-heading",
  "#_body code", "#_body pre code", "#_body blockquote p", "#_body th", "#_body td",
  "#_meta td", "#_meta a", "#_backlinks h2", "#_relations h2", "#_relations th", "#_relations td", "#_relations a",
  "#_diagnostics h2", "#_diagnostics li"];

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

// 地が状態で変わりうる入れ物のすべてにポインターを置き、押したままでも測る（Fluent 2 の設計の 4.2、6）。
// 読むだけの入れ物（#_main の表の行と一覧の行）は、ポインターと押下の前後で地が変わらないことも、すべてで比べる
// （比が 4.5 を保っても、地を変えれば 4.2 の 1 つ目の規則に外れる。実装の 1 回目のレビューの C）
async function stateContrast(page) {
  // 木の行（.fui-TreeItemLayout）にポインターを置き、行の中の文字（名前と件数のバッジ）を測る
  const sel = "#_main tr, #_main li, a, summary, button, .fui-NavItem, .fui-TreeItemLayout, .fui-Select";
  const n = await page.locator(sel).count();
  let min = 99, where = "";
  const changed = [];
  const name = (e) => e.tagName + "." + (typeof e.className === "string" ? e.className : "");
  for (let i = 0; i < n; i++) {
    const loc = page.locator(sel).nth(i);
    if (!(await loc.isVisible())) continue;
    const readOnly = await loc.evaluate((e) => e.matches("#_main tr, #_main li"));
    const bg = (e) => getComputedStyle(e).backgroundColor;
    const bg0 = readOnly ? await loc.evaluate(bg) : null;
    await loc.hover();
    const [r1, bg1] = await loc.evaluate(async (e) => { await window.__settled(); return [window.__textRatio(e), getComputedStyle(e).backgroundColor]; });
    await page.mouse.down();
    const [r2, bg2] = await loc.evaluate(async (e) => { await window.__settled(); return [window.__textRatio(e), getComputedStyle(e).backgroundColor]; });
    // 押したままポインターを外した状態（:active が残り、:hover が外れる）も測る（実装の 1 回目のレビューの 3）
    await page.mouse.move(0, 0);
    const [r3, bg3] = await loc.evaluate(async (e) => { await window.__settled(); return [window.__textRatio(e), getComputedStyle(e).backgroundColor]; });
    await page.mouse.up();
    if (readOnly && (bg1 !== bg0 || bg2 !== bg0 || bg3 !== bg0)) changed.push(`${await loc.evaluate(name)} ${bg0}→${bg1}/${bg2}/${bg3}`);
    const r = Math.min(r1, r2, r3);
    if (r < min) { min = r; where = await loc.evaluate(name); }
  }
  return { min, where, changed };
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

// 変換中の Enter と Esc は扱わない（isComposing が真か、keyCode が 229）。記事のページと索引のページの両方
async function imeChecks(page, tag) {
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
  await page.fill("#_q", "");
}

async function articleChecks(browser, base, tag) {
  const { context, page, errors } = await newPage(browser);
  const requests = [];
  page.on("request", (r) => requests.push(r.url()));
  await page.goto(url(base, "concepts/two.html"));
  // 記事のページの木も、グループの名前と件数だけを描き、記事の題名は描かない（左のペインの木の設計の 9 節）
  // 2 つのグループに載ったページ: 今のページを持つ 2 つのグループ（どちらも「タグなし」）に印が付き、その祖先が開く
  const tree = await page.evaluate(() => ({
    pages: document.querySelectorAll(".tree a.tree-page").length,
    current: Array.from(document.querySelectorAll('.tree .fui-TreeItem.is-current[aria-current="true"]'), (i) => ({
      name: i.querySelector(":scope > .fui-TreeItemLayout .tree-name").textContent,
      parent: i.parentElement.closest(".fui-TreeItem")?.querySelector(":scope > .fui-TreeItemLayout .tree-name").textContent,
      open: i.parentElement.closest(".fui-TreeItem")?.getAttribute("aria-expanded") })),
  }));
  check(tree.pages === 0, `${tag}: 記事のページの木に記事の題名が ${tree.pages} 個ある`);
  check(tree.current.length === 2 && tree.current.every((c) => c.name === "タグなし" && c.open === "true")
    && tree.current.map((c) => c.parent).sort().join() === "第一,第二", `${tag}: 今のページのグループの印が違う: ${JSON.stringify(tree.current)}`);
  {
    const p2 = await context.newPage();
    await p2.goto(url(base, "concepts/bm25.html"));
    const t2 = await p2.evaluate(() => {
      const c = document.querySelector(".tree .fui-TreeItem.is-current");
      return { name: c?.querySelector(":scope > .fui-TreeItemLayout .tree-name").textContent,
               parent: c?.parentElement.closest(".fui-TreeItem")?.querySelector(":scope > .fui-TreeItemLayout .tree-name").textContent };
    });
    // bm25 の最初のタグは「検索」。「Index」の下の「検索」のグループに印が付く
    check(t2.name === "検索" && t2.parent === "Index", `${tag}: bm25 の今のページのグループが違う: ${JSON.stringify(t2)}`);
    await p2.close();
  }
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
  await imeChecks(page, tag + " 記事");
  const health = await page.evaluate(() => window.__health());
  check(health.style === 0 && health.dupIds.length === 0 && health.csp.length === 0 && health.errors.length === 0,
    `${tag}: 記事のページの [style]、ID の重複、CSP、画面のエラー: ${JSON.stringify(health)}`);
  check(errors.length === 0, `${tag}: コンソールのエラー: ${errors.slice(0, 3)}`);
  await context.close();
}

// 左の木（Fluent 2 の Tree。左のペインの木の設計の 2、4、6）
async function treeChecks(browser, base, tag) {
  const shape = () => {
    const root = document.querySelector('.tree .fui-Tree[role="tree"]');
    const items = Array.from(document.querySelectorAll(".tree .fui-TreeItem"));
    const level = (i) => Number(i.getAttribute("aria-level"));
    return {
      root: !!root && !!root.getAttribute("aria-label"),
      roles: items.filter((i) => i.getAttribute("role") !== "treeitem").length,
      badLevel: items.filter((i) => { const p = i.parentElement.closest(".fui-TreeItem"); return level(i) !== (p ? level(p) + 1 : 1); }).length,
      badExpanded: items.filter((i) => i.hasAttribute("aria-expanded") !== !!i.querySelector(":scope > .fui-Tree")).length,
      noLayout: items.filter((i) => !i.querySelector(":scope > .fui-TreeItemLayout > .fui-TreeItemLayout__main")).length,
      tab0: items.filter((i) => i.getAttribute("tabindex") === "0").length,
      underline: items.filter((i) => i.tagName === "A" && getComputedStyle(i).textDecorationLine !== "none").length,
      deep: items.filter((i) => level(i) >= 5 && !i.classList.contains("tree-deep")).length,
    };
  };
  const tab0 = (page) => page.evaluate(() => document.querySelectorAll('.tree .fui-TreeItem[tabindex="0"]').length);
  const active = (page) => page.evaluate(() => {
    const a = document.activeElement;
    return { cls: a ? a.className : "", text: a ? (a.querySelector(":scope > .fui-TreeItemLayout > .fui-TreeItemLayout__main") || a).textContent : "",
             current: !!(a && a.classList && a.classList.contains("is-current")), expanded: a ? a.getAttribute("aria-expanded") : null };
  });

  // 記事のページ
  {
    const { context, page, errors } = await newPage(browser);
    await page.goto(url(base, "concepts/bm25.html"));
    const s = await page.evaluate(shape);
    check(s.root && s.roles === 0 && s.badLevel === 0 && s.badExpanded === 0 && s.noLayout === 0 && s.tab0 === 1 && s.underline === 0 && s.deep === 0,
      `${tag}: 記事のページの木の作りが違う: ${JSON.stringify(s)}`);
    // 見た目: ペインの地はページと同じ。枝は semibold。件数は CounterBadge で、title に件数の文がある
    const look = await page.evaluate(() => {
      const nav = document.getElementById("_nav");
      const badge = document.querySelector(".tree-group .tree-count");
      return { navBg: getComputedStyle(nav).backgroundColor, homeBg: getComputedStyle(document.querySelector(".nav-home")).backgroundColor,
               weight: getComputedStyle(document.querySelector(".tree-group > .fui-TreeItemLayout > .fui-TreeItemLayout__main")).fontWeight,
               badge: !!badge && badge.classList.contains("fui-CounterBadge") && /^\d+ ページ$/.test(badge.title) && badge.getAttribute("aria-hidden") === "true",
               label: /（\d+ ページ）$/.test(document.querySelector(".tree-group").getAttribute("aria-label") || "") };
    });
    check(look.navBg === "rgba(0, 0, 0, 0)" && look.homeBg === "rgba(0, 0, 0, 0)" && Number(look.weight) >= 600 && look.badge && look.label,
      `${tag}: 木の見た目が違う: ${JSON.stringify(look)}`);
    // バッジは名前のすぐ隣（作者の決定）。字下げは Fluent 2 のサイトの形: 1 段目と 2 段目の名前がそろい、3 段目は 1 段深い（6.1）
    const place = await page.evaluate(() => {
      // 3 段目を見えるようにするため、すべての枝を開く（測ったあとで読み直す）
      document.querySelectorAll(".tree-group[aria-expanded]").forEach((b) => b.setAttribute("aria-expanded", "true"));
      const main = (i) => i.querySelector(":scope > .fui-TreeItemLayout > .fui-TreeItemLayout__main").getBoundingClientRect();
      const lay = document.querySelector(".tree-group > .fui-TreeItemLayout");
      const gap = lay.querySelector(".tree-count").getBoundingClientRect().left - lay.querySelector(".fui-TreeItemLayout__main").getBoundingClientRect().right;
      const at = (n) => Array.from(document.querySelectorAll(`.tree .fui-TreeItem[aria-level="${n}"]`)).find((i) => i.offsetParent !== null);
      const [l1, l2, l3] = [at(1), at(2), at(3)].map((i) => i && Math.round(main(i).left));
      return { gap: Math.round(gap), l1, l2, l3 };
    });
    check(place.gap >= 0 && place.gap <= 12 && place.l1 === place.l2 && place.l3 - place.l2 >= 16 && place.l3 - place.l2 <= 20,
      `${tag}: バッジの位置か字下げが違う: ${JSON.stringify(place)}`);
    await page.reload();
    await page.waitForFunction(() => window.__browse && window.__browse.navLoaded);
    // Tab で木に入ると、今のページの項目にフォーカスがある
    await page.focus("#_q");
    for (let k = 0; k < 4 && !(await page.evaluate(() => !!document.activeElement.closest(".tree"))); k++) { await page.keyboard.press("Tab"); }
    let a = await active(page);
    check(a.current, `${tag}: Tab で木に入ると今のページの項目にない: ${JSON.stringify(a)}`);
    // ← で親の枝に移り、もう一度 ← で閉じ、→ で開き、→ で最初の子に移る
    await page.keyboard.press("ArrowLeft");
    a = await active(page);
    check(a.cls.includes("tree-group") && a.expanded === "true", `${tag}: ← で親の枝に移らない: ${JSON.stringify(a)}`);
    await page.evaluate(() => { document.activeElement.dataset.testBranch = "1"; });
    await page.keyboard.press("ArrowLeft");
    check((await active(page)).expanded === "false", `${tag}: ← で枝が閉じない`);
    await page.keyboard.press("ArrowRight");
    check((await active(page)).expanded === "true", `${tag}: → で枝が開かない`);
    await page.keyboard.press("ArrowRight");
    check(await page.evaluate(() => {
      const b = document.querySelector('[data-test-branch="1"]');
      return document.activeElement === b.querySelector(":scope > .fui-Tree > .fui-TreeItem");
    }), `${tag}: → で最初の子に移らない`);
    check(await tab0(page) === 1, `${tag}: 矢印キーのあと、tabindex="0" の項目が 1 つでない`);
    // バッジにポインターを置いても、バッジは隠れず title を持つ（6.3）
    await page.locator(".tree-group > .fui-TreeItemLayout .tree-count").first().hover();
    const onBadge = await page.evaluate(() => {
      const b = document.querySelector(".tree-group > .fui-TreeItemLayout .tree-count");
      return { shown: b.offsetParent !== null, hovered: b.matches(":hover"), title: b.title };
    });
    check(onBadge.shown && onBadge.hovered && /^\d+ ページ$/.test(onBadge.title), `${tag}: バッジにポインターを置き続けられない: ${JSON.stringify(onBadge)}`);
    // 記事のページの枝のシェブロンを押すと開閉だけをする
    const before = await page.evaluate(() => document.querySelector(".tree-group").getAttribute("aria-expanded"));
    await page.locator(".tree-group > .fui-TreeItemLayout .fui-TreeItemLayout__expandIcon").first().click();
    const after = await page.evaluate(() => [document.querySelector(".tree-group").getAttribute("aria-expanded"), location.pathname]);
    check(before !== after[0] && after[1].endsWith("/bm25.html"), `${tag}: 記事のページの枝のシェブロンで開閉しないか、ページが移る`);
    await page.locator(".tree-group > .fui-TreeItemLayout .fui-TreeItemLayout__expandIcon").first().click();
    // 枝の名前を押すと、Index のページがそのグループに絞られて開く（9 節）
    const bid = await page.evaluate(() => document.querySelector(".tree-group").getAttribute("data-group"));
    await Promise.all([page.waitForURL((u) => u.pathname.endsWith("/index.html")),
                       page.locator(".tree-group > .fui-TreeItemLayout .tree-name").first().click()]);
    await page.waitForFunction(() => window.__browse && window.__browse.navLoaded);
    check(await page.evaluate((id) => location.hash === "#group=" + id && document.querySelector(".tree .fui-TreeItem.is-current")?.getAttribute("data-group") === id, bid),
      `${tag}: 記事のページの枝の名前で、Index のページがそのグループに絞られない`);
    // キーボード: 枝で Enter を押しても、葉（子のないグループ）で Enter を押しても、Index のページがそのグループに絞られて開く
    for (const which of ["branch", "leaf"]) {
      await page.goto(url(base, "concepts/bm25.html"));
      await page.waitForFunction(() => window.__browse && window.__browse.navLoaded);
      const gid = await page.evaluate((w) => {
        const el = w === "branch" ? document.querySelector(".tree-group") : document.querySelector(".tree a.tree-index.is-current");
        el.focus();
        return el.getAttribute("data-group");
      }, which);
      await Promise.all([page.waitForURL((u) => u.pathname.endsWith("/index.html")), page.keyboard.press("Enter")]);
      await page.waitForFunction(() => window.__browse && window.__browse.navLoaded);
      check(await page.evaluate((id) => location.hash === "#group=" + id, gid), `${tag}: ${which} の Enter で Index のページがそのグループに絞られない`);
    }
    // 深い段: abc のページでは 8 段まで開く。4 段目より深い項目の名前の左端は、4 段目の項目と同じ位置にある（2.3）
    await page.goto(url(base, "concepts/abc.html"));
    const deep = await page.evaluate(() => {
      const items = Array.from(document.querySelectorAll(".tree .fui-TreeItem")).filter((i) => Number(i.getAttribute("aria-level")) >= 4 && i.offsetParent !== null);
      const left = (i) => Math.round(i.querySelector(":scope > .fui-TreeItemLayout > .fui-TreeItemLayout__main").getBoundingClientRect().left);
      const levels = items.map((i) => Number(i.getAttribute("aria-level")));
      return { max: Math.max(0, ...levels), lefts: [...new Set(items.map(left))],
               untagged: items.filter((i) => Number(i.getAttribute("aria-level")) >= 5 && !i.classList.contains("tree-deep")).length };
    });
    check(deep.max >= 8 && deep.lefts.length === 1 && deep.untagged === 0,
      `${tag}: 4 段目より深い項目の字下げが 4 段目と同じでない: ${JSON.stringify(deep)}`);
    check(errors.length === 0, `${tag}: 木の操作でコンソールのエラー: ${errors.slice(0, 3)}`);
    const health = await page.evaluate(() => window.__health());
    check(health.style === 0 && health.dupIds.length === 0 && health.csp.length === 0, `${tag}: 木の操作のあとの [style]、ID、CSP: ${JSON.stringify(health)}`);
    await context.close();
  }

  // 索引のページ
  {
    const { context, page, errors } = await newPage(browser);
    await page.goto(url(base, "index.html"));
    const s = await page.evaluate(shape);
    check(s.root && s.roles === 0 && s.badLevel === 0 && s.badExpanded === 0 && s.noLayout === 0 && s.tab0 === 1 && s.underline === 0,
      `${tag}: 索引のページの木の作りが違う: ${JSON.stringify(s)}`);
    // 深さ 1 の枝は開いている
    check(await page.evaluate(() => Array.from(document.querySelectorAll('.tree-group[aria-level="1"]')).every((b) => b.getAttribute("aria-expanded") === "true")),
      `${tag}: 索引のページで深さ 1 の枝が開いていない`);
    // 枝の名前を押すと絞られ、シェブロンを押すと開閉だけをする
    const b = page.locator('.tree-group[aria-level="1"]').first();
    const bid = await b.getAttribute("data-group");
    await b.locator(":scope > .fui-TreeItemLayout .tree-name").click();
    await page.waitForTimeout(100);
    check(await page.evaluate((id) => location.hash === "#group=" + id, bid), `${tag}: 索引のページの枝の名前を押しても絞られない`);
    await b.locator(":scope > .fui-TreeItemLayout .fui-TreeItemLayout__expandIcon").click();
    await page.waitForTimeout(100);
    check((await b.getAttribute("aria-expanded")) === "false" && await page.evaluate((id) => location.hash === "#group=" + id, bid),
      `${tag}: シェブロンを押したときに閉じないか、絞り込みが変わる`);
    await b.locator(":scope > .fui-TreeItemLayout .fui-TreeItemLayout__expandIcon").click();
    // Enter で枝を選ぶと絞られる
    await page.evaluate(() => { location.hash = ""; });
    await page.waitForTimeout(100);
    await b.focus();
    await page.keyboard.press("Enter");
    await page.waitForTimeout(100);
    check(await page.evaluate((id) => location.hash === "#group=" + id, bid), `${tag}: 索引のページの枝で Enter を押しても絞られない`);
    // ローヴィング: 葉を押したあと、Tab の入口はその葉になる。木の後ろの入力欄から Shift+Tab で戻ると、押した葉に入り、
    // そこから Tab で木の外に出る。マウスで押した直後のリンクからの Tab の動きはブラウザで違う（WebKit は動かない）ので、
    // 入口はキーボードで木に入る操作で確かめる
    const leaf = page.locator("a.tree-index").first();
    const leafId = await leaf.getAttribute("data-group");
    await leaf.click();
    await page.waitForTimeout(100);
    check(await tab0(page) === 1 && await page.evaluate((id) => document.querySelector('.tree [tabindex="0"]').getAttribute("data-group") === id, leafId),
      `${tag}: 葉を押したあと、Tab の入口が押した葉でない`);
    await page.focus("#_filters input");
    await page.keyboard.press("Shift+Tab");
    check(await page.evaluate((id) => document.activeElement.getAttribute("data-group") === id, leafId),
      `${tag}: Shift+Tab で押した葉に戻らない`);
    await page.keyboard.press("Tab");
    check(await page.evaluate(() => !document.activeElement.closest(".tree")), `${tag}: Tab で木の外に出ない`);
    check(errors.length === 0, `${tag}: 索引のページの木の操作でコンソールのエラー: ${errors.slice(0, 3)}`);
    await context.close();
  }
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
  // タグのグループ（N9）でも絞れる。「索引」の下の「検索」には bm25 だけが載る。左の木の行に印が付く
  const tagGroup = await page.evaluate(() => {
    const walk = (gs, parent) => {
      for (const g of gs) {
        if (g.title === "検索" && parent === "Index") return { id: g.id, children: g.children.length };
        const r = walk(g.children, g.title); if (r) return r;
      }
      return null;
    };
    return walk(window.WIKI_NAV.groups, null);
  });
  check(tagGroup && /^_gt[0-9]+$/.test(tagGroup.id) && tagGroup.children === 0, `${tag}: タグのグループの形が違う: ${JSON.stringify(tagGroup)}`);
  if (tagGroup) {
    // 左の木のタグのグループの行を押す（断片を直に書かず、行のリンクが正しいグループを指すことも確かめる）
    const row = page.locator(`#_navbody a[href="#group=${tagGroup.id}"]`);
    check(await row.count() === 1 && (await row.textContent()).includes("検索"), `${tag}: 左の木にタグのグループの行がない`);
    await row.click();
    await page.waitForTimeout(100);
    check(await page.evaluate(() => location.hash) === "#group=" + tagGroup.id, `${tag}: 行を押しても断片が変わらない`);
    const shown = await page.evaluate(() => Array.from(document.querySelectorAll("#_index .fx-row:not([hidden]) .ix-title"), (a) => a.textContent));
    const mark = await page.evaluate(() => document.querySelector('#_navbody [aria-current="true"]')?.textContent || "");
    check(shown.join() === "BM25", `${tag}: タグのグループで絞った行が違う: ${shown}`);
    check(mark.includes("検索"), `${tag}: 左の木のタグのグループの行に印がない: ${mark}`);
    const path = await page.evaluate(() => document.querySelector('#_index .fx-row[data-id="concepts/bm25"] .fx-path')?.textContent);
    check(path === "Index › 検索", `${tag}: bm25 の階層が「Index › 検索」でない: ${path}`);
    await page.evaluate(() => { location.hash = ""; });
    await page.waitForTimeout(100);
  }
  // 種類とグループは、あとから選んだほうだけが効く（種類とグループの設計の 2 節、3 節）
  {
    const pressed = () => page.evaluate(() => document.querySelector('.chips .fui-ToggleButton[aria-pressed="true"]')?.textContent);
    const state = () => page.evaluate(() => ({ hash: location.hash, chip: !document.querySelector(".group-chip").hidden,
      current: document.querySelector(".tree .fui-TreeItem.is-current")?.getAttribute("data-group") ?? null }));
    // グループを選んでから種類を押すと、グループが外れ、種類だけで絞る
    await page.evaluate((id) => { location.hash = "#group=" + id; }, firstId);
    await page.waitForTimeout(100);
    await page.click(".chips .fui-ToggleButton:text-is('エンティティ')");
    let s = await state();
    check(s.hash === "" && !s.chip && s.current === "" && (await page.textContent("#_count")) === `${total} 件中 1 件`,
      `${tag}: グループを選んだまま種類を押しても、グループが外れない: ${JSON.stringify(s)}`);
    // 種類を押してから左の木でグループの行を押すと、種類が「すべて」に戻り、グループだけで絞る
    const groupRow = (id) => page.locator(`.tree .fui-TreeItem[data-group="${id}"] > .fui-TreeItemLayout .tree-name`);
    await groupRow(firstId).click();
    await page.waitForTimeout(100);
    check((await pressed()) === "すべて" && (await page.textContent("#_count")) === `${total} 件中 1 件`,
      `${tag}: 種類を押してからグループを選んでも、種類が「すべて」に戻らない: ${await pressed()}`);
    // 検索語とタグは、グループを選んでも、種類を押してグループを外しても、絞り込みに効いたまま残る（実装のレビューの 1、2）。
    // 「エンティティ」だけなら 1 件（İstanbul）なので、検索語かタグが効いていれば 0 件になる
    await page.click(".chips .fui-ToggleButton:text-is('すべて')");
    await page.evaluate(() => { location.hash = ""; });
    await page.waitForTimeout(100);
    for (const [what, set, reset] of [
      ["検索語", () => page.fill("#_filters input", "zzzz"), () => page.fill("#_filters input", "")],
      ["タグ", () => page.selectOption(".tag-select select", { label: "検索（1）" }), () => page.selectOption(".tag-select select", { index: 0 })],
    ]) {
      await set();
      await groupRow(firstId).click();
      await page.waitForTimeout(100);
      await page.click(".chips .fui-ToggleButton:text-is('エンティティ')");
      const r = await page.evaluate(() => ({ hash: location.hash, shown: document.querySelectorAll("#_index .fx-row:not([hidden])").length,
        q: document.querySelector("#_filters input").value, tag: document.querySelector(".tag-select select").selectedIndex }));
      check(r.hash === "" && r.shown === 0 && (what === "検索語" ? r.q === "zzzz" : r.tag > 0),
        `${tag}: グループを選んで種類を押すと、${what}の絞り込みが効かなくなる: ${JSON.stringify(r)}`);
      await reset();
      await page.click(".chips .fui-ToggleButton:text-is('すべて')");
    }
    // 履歴: グループの行を 2 つ続けて押し、種類を押してから戻ると、1 つ目のグループに戻り、種類は「すべて」（5 節の限界）
    const secondId = await page.evaluate(() => {
      const walk = (gs) => { for (const g of gs) { if (g.title === "第二") return g.id; const r = walk(g.children); if (r) return r; } return null; };
      return walk(window.WIKI_NAV.groups);
    });
    await page.click(".chips .fui-ToggleButton:text-is('すべて')");
    await groupRow(firstId).click();
    await page.waitForTimeout(100);
    await groupRow(secondId).click();
    await page.waitForTimeout(100);
    await page.click(".chips .fui-ToggleButton:text-is('エンティティ')");
    await page.goBack();
    await page.waitForTimeout(200);
    check(await page.evaluate((id) => location.hash === "#group=" + id, firstId) && (await pressed()) === "すべて"
      && (await page.textContent("#_count")) === `${total} 件中 1 件`,
      `${tag}: 履歴を戻ったときの絞り込みが違う: ${await page.evaluate(() => location.hash)} ${await pressed()}`);
    // 種類を選んでから「すべてのページ」を押しても、種類は残る
    await page.click(".chips .fui-ToggleButton:text-is('エンティティ')");
    await page.click(".tree a.tree-all");
    await page.waitForTimeout(100);
    check((await pressed()) === "エンティティ" && (await page.textContent("#_count")) === `${total} 件中 1 件`,
      `${tag}: 「すべてのページ」を押すと、選んだ種類が消える: ${await pressed()}`);
    await page.click(".chips .fui-ToggleButton:text-is('すべて')");
    const h = await page.evaluate(() => window.__health());
    check(h.style === 0 && h.dupIds.length === 0 && h.csp.length === 0 && h.errors.length === 0,
      `${tag}: 種類とグループの操作のあとの [style]、ID、CSP、画面のエラー: ${JSON.stringify(h)}`);
  }
  // 壊れた断片（%）でも、例外にならず、前の絞り込みを外す（2 回目の実装のレビューの A）
  await page.evaluate((id) => { location.hash = "#group=" + id; }, firstId);
  await page.waitForTimeout(100);
  await page.evaluate(() => { location.hash = "#group=%"; });
  await page.waitForTimeout(100);
  check((await page.textContent("#_count")) === `${total} 件` && (await page.locator(".group-chip:visible").count()) === 0,
    `${tag}: 壊れた断片で前の絞り込みが残る`);
  {
    const p2 = await page.context().newPage();
    const errs = [];
    p2.on("pageerror", (e) => errs.push(String(e)));
    await p2.goto(url(base, "index.html") + "#group=%");
    check(await p2.evaluate(() => window.__browse.navLoaded) && errs.length === 0, `${tag}: #group=% で開くと止まる: ${errs}`);
    await p2.close();
  }
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
  await imeChecks(page, tag + " 索引");
  // 空白だけの欄は、絞っていない（3 回目の実装のレビューの A）
  for (const blank of [" ", "　"]) {
    await page.fill("#_q", blank);
    await page.waitForTimeout(50);
    check((await page.textContent("#_count")) === `${total} 件`, `${tag}: 空白だけの欄で件数が「件中」になる`);
  }
  await page.fill("#_q", "");
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
  for (const [width, open] of [[360, false], [320, false], [600, false], [1000, true]]) {
    for (const rel of ["concepts/bm25.html", "index.html", "concepts/long.html", "concepts/rel.html"]) {
      const { context, page } = await newPage(browser, { width });
      await page.goto(url(base, rel));
      const r = await page.evaluate(() => {
        const main = document.getElementById("_main");
        // 本文、メタ欄、節の中の要素が #_main の右端を越えない（表だけを送る入れ物の中は除く）
        const right = main.getBoundingClientRect().right - parseFloat(getComputedStyle(main).paddingRight) + 1;
        // 祖先が切り取っている要素（畳んだ検索欄の消去ボタンなど）は見えないので数えない
        const clipped = (e) => {
          for (let a = e.parentElement; a && a !== main; a = a.parentElement) {
            if (getComputedStyle(a).overflowX !== "visible" && a.getBoundingClientRect().right <= right) return true;
          }
          return false;
        };
        const over = Array.from(main.querySelectorAll("*"))
          .filter((e) => !e.closest(".table-scroll, #_body table, pre") && e.getBoundingClientRect().right > right && !clipped(e))
          .map((e) => e.tagName + "." + e.className).slice(0, 5);
        const scroll = document.querySelector("#_relations .table-scroll");
        return { drawer: document.querySelector("details.drawer").open,
                 main: main.scrollWidth > main.clientWidth + 1,
                 page: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1, over,
                 scroll: scroll && { over: scroll.scrollWidth > scroll.clientWidth + 1,
                                     inside: scroll.getBoundingClientRect().right <= right } };
      });
      check(r.drawer === open, `${tag}: 幅 ${width} の ${rel} で「メニュー」の開閉が違う`);
      check(!r.main && !r.page, `${tag}: 幅 ${width} の ${rel} で横にはみ出す`);
      check(r.over.length === 0, `${tag}: 幅 ${width} の ${rel} で #_main の右端を越える要素: ${r.over}`);
      if (rel === "concepts/long.html") {
        // N9: long は 200 文字のタグを持つ。今のページのタグのグループの名前が、開いた木の中で #_nav からはみ出さない
        const nav = await page.evaluate(() => {
          document.querySelector("details.drawer").open = true;
          const box = document.getElementById("_nav");
          const right = box.getBoundingClientRect().right + 1;
          const name = document.querySelector(".tree .fui-TreeItem.is-current > .fui-TreeItemLayout .tree-name");
          return { found: !!name, long: name ? name.textContent.length : 0,
                   over: name ? name.getBoundingClientRect().right > right : true,
                   scroll: box.scrollWidth > box.clientWidth + 1 };
        });
        check(nav.found && nav.long === 200 && !nav.over && !nav.scroll,
          `${tag}: 幅 ${width} で長いタグのグループの名前が #_nav からはみ出す: ${JSON.stringify(nav)}`);
      }
      if (rel === "concepts/rel.html") {
        check(r.scroll && r.scroll.inside, `${tag}: 幅 ${width} で関係表の入れ物が #_main からはみ出す`);
        if (width <= 600) {
          check(r.scroll && r.scroll.over, `${tag}: 幅 ${width} で関係表が横に送れない（最小幅 48em が効いていない）`);
          // キーボードで送れる: 入れ物にフォーカスし、右の矢印で送る
          await page.focus("#_relations .table-scroll");
          await page.keyboard.press("ArrowRight");
          await page.keyboard.press("End");
          await page.waitForTimeout(300);
          const left = await page.evaluate(() => document.querySelector("#_relations .table-scroll").scrollLeft);
          check(left > 0, `${tag}: 幅 ${width} で関係表をキーボードで横に送れない`);
        }
      }
      await context.close();
    }
  }
  // スクリプトなし: 配色は auto、索引の一覧はすべて読める
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto(url(base, "index.html"));
  const r = await page.evaluate(() => ({ theme: document.documentElement.getAttribute("data-theme"),
    rows: document.querySelectorAll("#_index .fx-row").length, titles: document.querySelectorAll("#_index .ix-title").length }));
  check(r.theme === "auto" && r.rows === PAGES && r.titles === PAGES, `${tag}: スクリプトなしの索引のページが違う: ${JSON.stringify(r)}`);
  await context.close();
}

// 記事のページの部品の書体、配置、線、class の約束（Fluent 2 の設計の 5）を、計算された値で確かめる
async function articlePartsChecks(browser, base, tag) {
  const { context, page, errors } = await newPage(browser);
  await page.goto(url(base, "concepts/rel.html"));
  const r = await page.evaluate(() => {
    const cs = (sel) => { const e = document.querySelector(sel); return e ? getComputedStyle(e) : null; };
    const token = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    const px = (v) => parseFloat(v);
    // 色は書き方（hex と rgb）が違うので、canvas で同じ書き方にそろえて比べる
    const ctx = document.createElement("canvas").getContext("2d");
    const color = (v) => { ctx.fillStyle = "#000"; ctx.fillStyle = v; return ctx.fillStyle; };
    const main = cs("#_main");
    const fs = px(main.fontSize);
    const heads = {};
    for (const [h, t] of [["h1", "Hero700"], ["h2", "Base600"], ["h3", "Base500"], ["h4", "Base400"]]) {
      const s = cs(`#_body ${h}`);
      heads[h] = { size: s && s.fontSize === token(`--fontSize${t}`), line: s && s.lineHeight === token(`--lineHeight${t}`),
                   weight: s && s.fontWeight === token("--fontWeightSemibold") };
    }
    const sub = Array.from(document.querySelectorAll("#_backlinks > h2, #_relations > h2, #_diagnostics > h2"));
    const link = cs("#_body a:not(.wl-missing-heading)");
    const meta = document.getElementById("_meta");
    const rel = document.querySelector("#_relations table");
    return {
      body: { size: main.fontSize === token("--fontSizeBase400"), line: Math.abs(px(main.lineHeight) - fs * 1.8) < 0.5,
              width: Math.abs(px(main.maxWidth) - fs * 48) < 0.5 },
      heads,
      sub: sub.length === 3 && sub.every((h) => h.classList.contains("fui-Subtitle2")
        && getComputedStyle(h).fontSize === token("--fontSizeBase400") && getComputedStyle(h).fontWeight === token("--fontWeightSemibold")),
      link: link && link.textDecorationLine.includes("underline") && link.color === getComputedStyle(document.querySelector("#_meta a")).color,
      missing: cs("#_body a.wl-missing-heading").textDecorationStyle,
      ambiguous: cs("#_body .wl-ambiguous").textDecorationStyle,
      unresolved: cs("#_body .wl-unresolved").textDecorationStyle,
      ext: getComputedStyle(document.querySelector("#_body a.ext"), "::after").content,
      align: ["th.ta-left", "th.ta-center", "th.ta-right", "td.ta-center", "td.ta-right"].map((s) => cs(`#_body ${s}`).textAlign),
      code: color(cs("#_body p code").backgroundColor) === color(token("--colorNeutralBackground3")) || cs("#_body p code").backgroundColor,
      pre: cs("#_body pre").borderRadius === token("--borderRadiusMedium"),
      quote: cs("#_body blockquote").borderInlineStartStyle === "solid",
      hr: cs("#_body hr").borderTopStyle === "solid",
      bodyTable: cs("#_body table").display,
      meta: { display: getComputedStyle(meta).display, narrow: meta.offsetWidth < document.getElementById("_main").clientWidth,
              th: cs("#_meta th").whiteSpace },
      rel: { display: getComputedStyle(rel).display, min: Math.abs(px(getComputedStyle(rel).minWidth) - px(getComputedStyle(rel).fontSize) * 48) < 0.5,
             wrap: cs("#_relations td").overflowWrap + " " + cs("#_relations td").wordBreak, inScroll: !!rel.closest(".table-scroll") },
      backlinks: getComputedStyle(document.querySelector("#_backlinks ul")).listStyleType,
      marker: color(getComputedStyle(document.querySelector("#_diagnostics li"), "::marker").color)
        === color(token("--colorStatusWarningForeground3")),
    };
  });
  check(r.body.size && r.body.line && r.body.width, `${tag}: 本文の大きさ、行間、幅が違う: ${JSON.stringify(r.body)}`);
  for (const [h, v] of Object.entries(r.heads)) {
    check(v.size && v.line && v.weight, `${tag}: 本文の ${h} の書体がトークンと違う: ${JSON.stringify(v)}`);
  }
  check(r.sub, `${tag}: 被リンク、関係、診断の見出しが Subtitle2 でない`);
  check(r.link, `${tag}: 本文のリンクに下線がないか、メタ欄のリンクと色が違う`);
  check(r.missing === "dotted" && r.ambiguous === "wavy" && r.unresolved === "dotted",
    `${tag}: wikilink の状態の下線の形が違う: ${r.missing} ${r.ambiguous} ${r.unresolved}`);
  check(r.ext.includes("↗"), `${tag}: 外部のリンクの印がない: ${r.ext}`);
  check(JSON.stringify(r.align) === JSON.stringify(["left", "center", "right", "center", "right"]),
    `${tag}: 本文の表の配置の class が効かない: ${r.align}`);
  check(r.code === true && r.pre && r.quote && r.hr, `${tag}: 本文のコード、整形済み、引用、区切りの線が違う: ${JSON.stringify([r.code, r.pre, r.quote, r.hr])}`);
  check(r.bodyTable === "block", `${tag}: 本文の表が横に送れる形（block）でない: ${r.bodyTable}`);
  check(r.meta.display === "table" && r.meta.narrow && r.meta.th === "nowrap", `${tag}: メタ欄の表の形が違う: ${JSON.stringify(r.meta)}`);
  check(r.rel.display === "table" && r.rel.min && r.rel.wrap === "normal keep-all" && r.rel.inScroll, `${tag}: 関係表の形が違う: ${JSON.stringify(r.rel)}`);
  check(r.backlinks === "none", `${tag}: 被リンクが Fluent の List でない: ${r.backlinks}`);
  check(r.marker, `${tag}: 診断の一覧の印が警告の色でない`);
  // 読むだけの行の地がポインターと押下で変わらないことは、colorChecks の stateContrast がすべての行で比べる
  const health = await page.evaluate(() => window.__health());
  check(health.style === 0 && health.dupIds.length === 0 && health.csp.length === 0 && health.errors.length === 0,
    `${tag}: 関係のページの [style]、ID の重複、CSP、画面のエラー: ${JSON.stringify(health)}`);
  check(errors.length === 0, `${tag}: 関係のページのコンソールのエラー: ${errors.slice(0, 3)}`);
  await context.close();
}

async function colorChecks(browser, base, tag) {
  for (const dark of [false, true]) {
    // 測れた部品は配色ごとに数える。片方の配色だけで消えた部品を、もう片方で測れたことにしない（実装の 1 回目のレビューの B）
    const measured = new Set();
    // 記事のページは、木を出した状態と、検索の結果を出した状態（木は隠れる）の両方で測る
    for (const [rel, query] of [["concepts/bm25.html", null], ["concepts/bm25.html", "検索"], ["concepts/rel.html", null],
                                ["index.html", null], ["index.html", "#group"]]) {
      const { context, page } = await newPage(browser, { dark });
      await page.goto(url(base, rel));
      if (query === "#group") {
        // 索引のページでグループを絞った状態（左の木の is-current）も測る
        await page.evaluate(() => { location.hash = "#group=" + window.WIKI_NAV.groups[0].id; });
        await page.waitForTimeout(100);
      } else if (query) {
        await page.focus("#_q");
        await page.fill("#_q", query);
        await page.waitForFunction(() => window.__browse.searchLoaded);
      } else if (rel !== "index.html") {
        // 木のすべてのグループを開き、ポインターと押下の状態を測れるようにする
        await page.evaluate(() => document.querySelectorAll(".tree-group[aria-expanded]").forEach((d) => { d.setAttribute("aria-expanded", "true"); }));
      }
      const c = await contrastOf(page);
      const low = Object.entries(c).filter(([, v]) => v < 4.5);
      check(low.length === 0, `${tag}: ${dark ? "暗い" : "明るい"}配色の ${rel} でコントラスト比が 4.5 を割る: ${JSON.stringify(low)}`);
      const s = await stateContrast(page);
      check(s.min >= 4.5, `${tag}: ${dark ? "暗い" : "明るい"}配色の ${rel} で、ポインターか押下の状態のコントラスト比が ${s.min.toFixed(2)}（${s.where}）`);
      check(s.changed.length === 0, `${tag}: ${dark ? "暗い" : "明るい"}配色の ${rel} で、読むだけの行の地がポインターか押下で変わる: ${s.changed.slice(0, 3)}`);
      Object.keys(c).forEach((k) => measured.add(k));
      notes.push(`${tag} ${dark ? "dark" : "light"} ${rel}: 最小 ${Math.min(...Object.values(c)).toFixed(2)}、状態 ${s.min.toFixed(2)}`);
      await context.close();
    }
    const missing = CONTRAST.filter((s) => !measured.has(s));
    check(missing.length === 0, `${tag}: ${dark ? "暗い" : "明るい"}配色でコントラストを測れなかった部品がある: ${missing}`);
  }
  // 強制カラー: 今のページの項目に輪郭がある
  const { context, page } = await newPage(browser, { forced: true });
  await page.goto(url(base, "concepts/bm25.html"));
  const outline = await page.evaluate(() => getComputedStyle(document.querySelector(".tree .fui-TreeItem.is-current > .fui-TreeItemLayout")).outlineStyle);
  // 強制カラーで、トグルの枠とつまみが見える（枠の線があり、つまみが塗られている。最終のレビューの 3）
  const tg = await page.evaluate(() => {
    const track = getComputedStyle(document.querySelector(".theme-track"));
    const knob = getComputedStyle(document.querySelector(".theme-knob"));
    return { border: track.borderTopStyle, bw: parseFloat(track.borderTopWidth), knob: knob.backgroundColor };
  });
  check(tg.border === "solid" && tg.bw > 0 && tg.knob !== "rgba(0, 0, 0, 0)" && tg.knob !== "transparent",
    `${tag}: 強制カラーでトグルの枠かつまみが見えない: ${JSON.stringify(tg)}`);
  check(outline !== "none", `${tag}: 強制カラーで今のページの印がない`);
  await page.goto(url(base, "index.html"));
  await page.evaluate(() => { location.hash = "#group=" + window.WIKI_NAV.groups[0].id; });
  await page.waitForTimeout(100);
  const groupOutline = await page.evaluate(() => getComputedStyle(document.querySelector(".tree .fui-TreeItem.is-current > .fui-TreeItemLayout")).outlineStyle);
  check(groupOutline !== "none", `${tag}: 強制カラーで絞っているグループの印がない`);
  await context.close();
}

async function filterPreferenceChecks(browser, base, tag, restart) {
  const context = await browser.newContext();
  try {
    const page = await context.newPage();
    const second = await context.newPage();
    const index = () => url(base, "index.html");
    const tagSelect = ".tag-select select";
    const typeButton = (type) => `.chips .fui-ToggleButton:text-is('${type}')`;
    async function read(p) {
      return p.evaluate(() => ({
        type: document.querySelector('.chips [aria-pressed="true"]').textContent,
        tag: document.querySelector(".tag-select select").selectedOptions[0].textContent,
        visible: Array.from(document.querySelectorAll(".fx-row:not([hidden])"), (row) => row.dataset.id),
      }));
    }
    const expectedTag = "検索（1）";
    const onlyBM25 = (state) => state.visible.join() === "concepts/bm25";
    await page.goto(index());
    await second.goto(index());
    await page.click(typeButton("コンセプト"));
    await second.selectOption(tagSelect, { label: expectedTag });
    await second.close();
    await page.reload();
    let state = await read(page);
    check(state.type === "コンセプト" && state.tag === expectedTag && onlyBM25(state),
      `${tag}: 別々のタブで選んだ種類とタグを復元できない: ${JSON.stringify(state)}`);
    if (restart) {
      const cookies = (await context.cookies(index())).filter(({ name }) => name.startsWith("info-hive-browse-filter-"));
      const unkeyedTag = createHash("sha256").update("browse-filter\0tag\0検索").digest("hex").slice(0, 32);
      check(cookies.length === 2 && cookies.every(({ name, value }) =>
        /^info-hive-browse-filter-[0-9a-f]{32}-(tag|type)$/.test(name) && /^[0-9a-f]{32}$/.test(value) && value !== unkeyedTag),
      `${tag}: 絞り込みの cookie に鍵付きの識別子がない`);
      base = await restart();
      await page.goto(index());
      state = await read(page);
      check(state.type === "コンセプト" && state.tag === expectedTag && onlyBM25(state),
        `${tag}: 再起動後に種類とタグを復元できない: ${JSON.stringify(state)}`);
    }
    const group = await page.evaluate(() => {
      const queue = [...window.WIKI_NAV.groups];
      for (const candidate of queue) {
        if (candidate.title === "第一") return candidate.id;
        queue.push(...candidate.children);
      }
      return null;
    });
    if (!check(group, `${tag}: グループ「第一」の ID がない`)) return;
    await page.goto(index() + "#group=" + group);
    await page.reload();
    state = await read(page);
    check(state.type === "すべて" && state.tag === expectedTag && state.visible.length === 0,
      `${tag}: グループを開いたときの絞り込みが違う: ${JSON.stringify(state)}`);
    // 左の木で種類が一時的に解除されても、タグ変更で以前の種類まで消さない。
    await page.selectOption(tagSelect, { index: 0 });
    await page.selectOption(tagSelect, { label: expectedTag });
    await page.goto(index());
    await page.reload();
    state = await read(page);
    check(state.type === "コンセプト" && state.tag === expectedTag && onlyBM25(state),
      `${tag}: グループを開いたあとに選んでいた種類を復元できない: ${JSON.stringify(state)}`);
    await page.click(typeButton("すべて"));
    await page.reload();
    state = await read(page);
    check(state.type === "すべて" && state.tag === expectedTag && onlyBM25(state),
      `${tag}: 種類の「すべて」を保存できない: ${JSON.stringify(state)}`);
    await page.selectOption(tagSelect, { index: 0 });
    await page.reload();
    state = await read(page);
    check(state.type === "すべて" && state.tag === "タグ: すべて" && state.visible.length === PAGES,
      `${tag}: タグの「すべて」を保存できない: ${JSON.stringify(state)}`);
    await context.addInitScript(() => {
      Object.defineProperty(window, "localStorage", { get() { throw new Error("blocked"); } });
      Object.defineProperty(Document.prototype, "cookie", { get() { throw new Error("blocked"); }, set() { throw new Error("blocked"); } });
    });
    await page.reload();
    await page.selectOption(tagSelect, { label: expectedTag });
    await page.click(typeButton("コンセプト"));
    state = await read(page);
    check(state.type === "コンセプト" && state.tag === expectedTag && onlyBM25(state),
      `${tag}: 保存を拒否したブラウザーで索引を絞れない: ${JSON.stringify(state)}`);
  } finally {
    await context.close();
  }
}

async function themeChecks(browser, base, tag, restart) {
  const context = await browser.newContext({ colorScheme: "light" });
  await context.addInitScript(INIT);
  const page = await context.newPage();
  await page.goto(url(base, "concepts/bm25.html"));
  // 配色のトグル（左のペインの木の設計の 7 節）。既定は auto で、明るい OS ではオフ
  check((await page.getAttribute("html", "data-theme")) === "auto" && !(await page.isChecked("#_theme")),
    `${tag}: 既定の配色が auto でないか、明るい OS でトグルがオフでない`);
  check((await page.getAttribute("#_theme", "role")) === "switch" && (await page.getAttribute("#_theme", "aria-label")).includes("テーマ")
    && (await page.textContent(".theme-label")) === "テーマ", `${tag}: トグルの role か名前が違う`);
  await page.click("#_theme");
  check((await page.getAttribute("html", "data-theme")) === "dark", `${tag}: トグルをオンにしても dark にならない`);
  await page.goto(url(base, "index.html"));
  check((await page.getAttribute("html", "data-theme")) === "dark" && await page.isChecked("#_theme"), `${tag}: 選んだ配色がページを移ると消える`);
  if (restart) {
    base = await restart();
    await page.goto(url(base, "index.html"));
    check((await page.getAttribute("html", "data-theme")) === "dark", `${tag}: サーバーを起動し直すと選んだ配色が消える`);
  }
  // もう一度オフにすると、OS と同じ見た目なので auto（OS に合わせる）に戻り、ページを移っても auto のまま
  await page.click("#_theme");
  await page.goto(url(base, "concepts/bm25.html"));
  check((await page.getAttribute("html", "data-theme")) === "auto" && !(await page.isChecked("#_theme")),
    `${tag}: OS と同じ見た目に戻しても auto にならない`);
  // auto の間に OS の配色が暗くなると、トグルがオンになる
  await page.emulateMedia({ colorScheme: "dark" });
  await page.waitForTimeout(100);
  check(await page.isChecked("#_theme"), `${tag}: auto の間に OS の配色が変わっても、トグルが合わない`);
  await context.close();
  // 暗い OS では、既定でオン。Space キーでオフにすると light が保存され、ページを移っても light のまま。
  // もう一度 Space でオンに戻すと、OS と同じ見た目なので auto に戻る（最終のレビューの 2、3）
  {
    const c3 = await browser.newContext({ colorScheme: "dark" });
    const p3 = await c3.newPage();
    await p3.goto(url(base, "concepts/bm25.html"));
    check((await p3.getAttribute("html", "data-theme")) === "auto" && await p3.isChecked("#_theme"), `${tag}: 暗い OS で既定のトグルがオンでない`);
    await p3.focus("#_theme");
    await p3.keyboard.press("Space");
    check((await p3.getAttribute("html", "data-theme")) === "light" && !(await p3.isChecked("#_theme")), `${tag}: 暗い OS で Space でオフにしても light にならない`);
    await p3.goto(url(base, "index.html"));
    check((await p3.getAttribute("html", "data-theme")) === "light", `${tag}: 暗い OS で選んだ light がページを移ると消える`);
    await p3.focus("#_theme");
    await p3.keyboard.press("Space");
    await p3.goto(url(base, "concepts/bm25.html"));
    check((await p3.getAttribute("html", "data-theme")) === "auto" && await p3.isChecked("#_theme"), `${tag}: 暗い OS でオンに戻しても auto にならない`);
    await c3.close();
  }
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
  await p2.click("#_theme");
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
    const built = python(["build", wiki, "--out", site, "--raw", "text", "--scope", "project"]);
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
        await treeChecks(browser, base, tag);
        await loadingChecks(browser, base, tag);
        await layoutChecks(browser, base, tag);
        await articlePartsChecks(browser, base, tag);
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
        await filterPreferenceChecks(browser, base, tag, restart);
        await themeChecks(browser, restart ? server.url.replace(/[^/]*$/, "") : base, tag, restart);
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
