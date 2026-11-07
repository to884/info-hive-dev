// ADR-0010 の PoC。Tauri のアプリが書いた結果（steps）から test.mjs の summarize() と同じ summary を作り、
// out/results/browsers.json の基準と比べて、同じファイルに summary と比較の結果を書き足す。
// 使い方: node compare_tauri.mjs out/results/tauri-windows.json
import { readFileSync, writeFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const file = process.argv[2] || join(HERE, "out", "results", "tauri-windows.json");
const res = JSON.parse(readFileSync(file, "utf8"));
const base = JSON.parse(readFileSync(join(HERE, "out", "results", "browsers.json"), "utf8")).runs[0].summary;

const byName = {};
for (const s of res.steps) byName[s.name] = s.data;
const s = {
  index: byName.index?.probe, kg: byName.kg?.probe, anchor: byName.anchor?.probe,
  entity: byName.entity?.probe, search: byName.search?.probe,
};
const missing = Object.entries(s).filter(([, v]) => !v).map(([k]) => k);
let summary = null, diff = [];
if (!missing.length && byName.unresolved) {
  summary = {
    navLoaded: s.index.navLoaded && s.kg.navLoaded,
    navCount: s.index.navCount,
    kgLinks: s.kg.links.map((l) => `${l.text}|${l.cls}|${l.href}`),
    kgBacklinks: s.kg.backlinks,
    kgDiagnostics: s.kg.diagnostics,
    scriptEscaped: s.kg.scriptEscaped,
    anchorPage: s.anchor.page,
    anchorHash: s.anchor.hash,
    anchorFound: s.anchor.hashTargetFound,
    entityPage: s.entity.page,
    entityBacklinks: s.entity.backlinks,
    searchLoaded: s.search.searchLoaded,
    searchResults: s.search.searchResults,
    unresolvedClickNavigated: byName.unresolved.navigated,
  };
  for (const k of Object.keys(base)) {
    if (JSON.stringify(summary[k]) !== JSON.stringify(base[k])) diff.push({ key: k, tauri: summary[k], baseline: base[k] });
  }
}
res.summary = summary;
res.missingSteps = missing;
res.matchesBaseline = summary !== null && diff.length === 0;
res.diffFromBaseline = diff;
res.hrefs = Object.fromEntries(res.steps.map((x) => [x.name, x.data.href]));
res.cspViolations = [...new Set(Object.values(s).flatMap((p) => (p && p.cspViolations) || []))];
res.externalRequests = [...new Set(res.steps.flatMap((x) => x.data.external || []))];
res.appErrors = s.index?.appErrors || [];
res.css = s.kg?.css || null;
res.userAgent = byName.index?.ua || null;
writeFileSync(file, JSON.stringify(res, null, 2), "utf8");
console.log(JSON.stringify({ reason: res.reason, tauri: res.tauri, webview: res.webview, hrefs: res.hrefs,
  matchesBaseline: res.matchesBaseline, missing, diff, csp: res.cspViolations, external: res.externalRequests,
  appErrors: res.appErrors, css: res.css }, null, 1));
