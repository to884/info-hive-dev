// 試験で落ちた 2 つの原因を分ける。
// 1. Firefox の Playwright が file:// の要求を page.route で捕まえるか。
// 2. Chrome と Edge でサーバーの方式のときに 404 になる URL は何か。
// 使い方（開発リポジトリのルートで）: node docs/agent-runs/2026-11-15-wiki-browse-cross-browser/probe.mjs <書き出したサイト>
import { createRequire } from "node:module";
import { spawn } from "node:child_process";
import { join, resolve, dirname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, "..", "..", "..");
const require = createRequire(join(REPO, "tests", "wiki", "browse", "package.json"));
const { chromium, firefox } = require("playwright");
const site = resolve(process.argv[2]);

// 1. file:// の要求を捕まえるか
for (const [name, engine] of [["chromium", chromium], ["firefox", firefox]]) {
  const b = await engine.launch();
  const p = await b.newPage();
  const routed = [];
  const requested = [];
  await p.route("**/*", (r) => { routed.push(r.request().url().split("/").pop()); return r.continue(); });
  p.on("request", (r) => requested.push(r.url().split("/").pop()));
  await p.goto(pathToFileURL(join(site, "index.html")).href);
  await p.waitForTimeout(800);
  console.log(JSON.stringify({ probe: "file-route", browser: name, routed: routed.length, requested: requested.length }));
  await b.close();
}

// 2. サーバーの方式で 404 になる URL
const py = spawn("uv", ["run", "-q", "--python", "3.12", "--with", "pyyaml==6.0.3", "python", "-X", "utf8",
  join(REPO, "info-hive-wiki", "skills", "info-hive", "scripts", "wiki_browse.py"),
  "serve", join(REPO, "wiki"), "--no-open", "--idle-timeout", "60"], { stdio: ["ignore", "pipe", "pipe"] });
let buf = "";
const url = await new Promise((ok, ng) => {
  const on = (d) => { buf += d; const m = buf.match(/http:\/\/127\.0\.0\.1:\d+\/\S*/); if (m) ok(m[0].replace(/["',}]+$/, "")); };
  py.stdout.on("data", on); py.stderr.on("data", on);
  setTimeout(() => ng(new Error("サーバーの URL が出ない: " + buf)), 60000);
});
for (const [name, opts] of [["chromium", {}], ["chrome", { channel: "chrome" }], ["msedge", { channel: "msedge" }]]) {
  const b = await chromium.launch(opts);
  const p = await b.newPage();
  const missing = [];
  const consoleErrors = [];
  p.on("response", (r) => { if (r.status() >= 400) missing.push(`${r.status()} ${r.url()}`); });
  p.on("console", (m) => { if (m.type() === "error") consoleErrors.push(`${m.text()} @ ${m.location().url}`); });
  // ページの要求に入らない要求（ファビコンなど）も、コンテキストの側で見る
  p.context().on("requestfinished", async (r) => {
    const res = await r.response();
    if (res && res.status() >= 400) missing.push(`ctx ${res.status()} ${r.url()}`);
  });
  await p.goto(url);
  await p.waitForTimeout(1500);
  await p.goto(new URL("index.html", url).href);
  await p.waitForTimeout(1500);
  console.log(JSON.stringify({ probe: "server-404", browser: name, missing, consoleErrors }));
  await b.close();
}
py.kill();
