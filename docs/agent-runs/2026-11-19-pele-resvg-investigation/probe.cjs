const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const { Resvg } = require(path.join(process.env.TEMP, "pele-png-tools/node_modules/@resvg/resvg-js"));
const { chromium, webkit } = require(path.join(process.cwd(), "tests/wiki/browse/node_modules/playwright"));
const sourceDir = path.join(process.cwd(), "docs/agent-runs/2026-11-19-pele-png-comparison");
const out = process.env.PELE_PROBE_OUT;
if (!out) throw Error("PELE_PROBE_OUT を指定してください");
fs.mkdirSync(out, { recursive: true });
if (fs.readdirSync(out).length) throw Error("空のディレクトリを指定してください");
function resolveVars(svg) {
  const style = svg.match(/ style="([^"]*)"/)[1].replaceAll("&quot;", "'");
  const vars = {};
  for (const d of style.split(";")) {
    const m = d.match(/^\s*(--[\w-]+):(.+)$/);
    if (m) vars[m[1]] = m[2];
  }
  for (let i = 0; i < 8; i++) svg = svg.replace(/var\((--[\w-]+)(?:,([^()]*))?\)/g, (_, key, fallback) => vars[key] ?? fallback ?? "");
  return svg;
}
const fontDir = "C:/Windows/Fonts/";
const fontSets = {
  noto: ["NotoSansJP-Regular.otf"],
  regular: ["YuGothR.ttc"],
  medium: ["YuGothM.ttc"],
  bold: ["YuGothB.ttc"],
  all: ["YuGothR.ttc", "YuGothM.ttc", "YuGothB.ttc", "YuGothL.ttc"],
};
const records = [];
for (const id of [0, 3]) for (const theme of ["light", "dark"]) {
  const raw = fs.readFileSync(path.join(sourceDir, id + "-" + theme + ".svg"), "utf8");
  const resolved = resolveVars(raw);
  const geometry = resolved.replace(/style="rx:([\d.]+)px"/g, 'rx="$1"');
  for (const [variant, svg, fontSet] of [
    ["raw", raw, "regular"],
    ["resolved", resolved, "regular"],
    ["rounded", geometry, "regular"],
    ["noto", geometry, "noto"],
    ["medium", geometry, "medium"],
    ["bold", geometry, "bold"],
    ["all", geometry, "all"],
  ]) {
    const renderer = new Resvg(svg, { font: { fontFiles: fontSets[fontSet].map(f => fontDir + f), loadSystemFonts: false, defaultFontFamily: "Yu Gothic" } });
    const png = renderer.render().asPng();
    const name = id + "-" + theme + "-" + variant;
    fs.writeFileSync(path.join(out, name + ".png"), png);
    fs.writeFileSync(path.join(out, name + "-usvg.svg"), renderer.toString());
    records.push({ id, theme, variant, bytes: png.length, sha256: crypto.createHash("sha256").update(png).digest("hex"), fontSet: fontSets[fontSet] });
  }
  const background = theme === "light" ? "#ffffff" : "#1f1f1f";
  const backgroundRenderer = new Resvg(geometry, {
    background,
    font: { fontFiles: [fontDir + "NotoSansJP-Regular.otf"], loadSystemFonts: false, defaultFontFamily: "Noto Sans JP" },
  });
  fs.writeFileSync(path.join(out, id + "-" + theme + "-noto-background.png"), backgroundRenderer.render().asPng());
  fs.writeFileSync(path.join(out, id + "-" + theme + "-original.svg"), raw);
  fs.writeFileSync(path.join(out, id + "-" + theme + "-resolved.svg"), resolved);
  fs.writeFileSync(path.join(out, id + "-" + theme + "-rounded.svg"), geometry);
}
(async () => {
  const browsers = [];
  for (const [name, type] of [["chromium", chromium], ["webkit", webkit]]) {
    const browser = await type.launch({ headless: true });
    for (const id of [0, 3]) for (const theme of ["light", "dark"]) {
      const page = await browser.newPage({ viewport: { width: 1000, height: 800 }, deviceScaleFactor: 1 });
      const svg = fs.readFileSync(path.join(sourceDir, id + "-" + theme + ".svg"), "utf8");
      await page.setContent("<!doctype html><meta charset='utf-8'><body>" + svg + "</body>");
      await page.evaluate(() => document.fonts.ready);
      const text = await page.locator("svg text").first().evaluate(el => {
        const css = getComputedStyle(el);
        return {text: el.textContent, fontFamily: css.fontFamily, fontSize: css.fontSize, fontWeight: css.fontWeight, bbox: {width: el.getBBox().width, height: el.getBBox().height}};
      });
      let platformFonts = null;
      if (name === "chromium") {
        const cdp = await page.context().newCDPSession(page);
        await cdp.send("DOM.enable"); await cdp.send("CSS.enable");
        const root = await cdp.send("DOM.getDocument");
        const target = await cdp.send("DOM.querySelector", {nodeId: root.root.nodeId, selector: "svg text"});
        platformFonts = (await cdp.send("CSS.getPlatformFontsForNode", {nodeId: target.nodeId})).fonts;
      }
      await page.screenshot({ path: path.join(out, name + "-" + id + "-" + theme + ".png") });
      browsers.push({browser: name, version: browser.version(), id, theme, text, platformFonts});
      await page.close();
    }
    await browser.close();
  }
  fs.writeFileSync(path.join(out, "results.json"), JSON.stringify({ records, browsers }, null, 2));
  console.log(JSON.stringify({ variants: records.length, browsers: browsers.length, first: browsers[0] }));
})().catch(e => { console.error(e); process.exit(1); });
