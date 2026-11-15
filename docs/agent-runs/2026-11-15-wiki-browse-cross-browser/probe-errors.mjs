// 見つからないページ（404 の HTML）と、組み立てられないとき（503 のテキスト）に、
// 製品の Chrome と Edge が /favicon.ico を要求するか、文書そのものの状態でコンソールにエラーが出るかを見る。
// 使い方（開発リポジトリのルートで）: node docs/agent-runs/2026-11-15-wiki-browse-cross-browser/probe-errors.mjs
import { createRequire } from "node:module";
import { spawn } from "node:child_process";
import { cpSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, "..", "..", "..");
const require = createRequire(join(REPO, "tests", "wiki", "browse", "package.json"));
const { chromium } = require("playwright");

// 使い捨ての Wiki とデータの場所（作者のサーバーを使い回さない）
const tmp = mkdtempSync(join(tmpdir(), "favicon-probe-"));
const wiki = join(tmp, "wiki");
cpSync(join(REPO, "wiki"), wiki, { recursive: true });
const py = spawn("uv", ["run", "-q", "--python", "3.12", "--with", "pyyaml==6.0.3", "python", "-X", "utf8",
  join(REPO, "info-hive-wiki", "skills", "info-hive", "scripts", "wiki_browse.py"),
  "serve", wiki, "--no-open", "--idle-timeout", "120"],
  { stdio: ["ignore", "pipe", "pipe"], env: { ...process.env, INFO_HIVE_DATA_DIR: join(tmp, "data") } });
let buf = "";
const url = await new Promise((ok, ng) => {
  const on = (d) => { buf += d; const m = buf.match(/http:\/\/127\.0\.0\.1:\d+\/\S*/); if (m) ok(m[0].replace(/["',}]+$/, "")); };
  py.stdout.on("data", on); py.stderr.on("data", on);
  setTimeout(() => ng(new Error("サーバーの URL が出ない: " + buf)), 60000);
});

async function visit(opts, target) {
  const b = await chromium.launch(opts);
  const ctx = await b.newContext();
  const p = await ctx.newPage();
  const consoleErrors = [];
  p.on("console", (m) => { if (m.type() === "error") consoleErrors.push(`${m.text().slice(0, 80)} @ ${m.location().url.replace(/\/[^/]+\/w\/[^/]+\//, "/<token>/w/<key>/")}`); });
  const res = await p.goto(target);
  await p.waitForTimeout(1500);
  await b.close();
  return { status: res.status(), consoleErrors };
}

const out = [];
const nope = new URL("concepts/nope.html", url).href;
for (const [name, opts] of [["chrome", { channel: "chrome" }], ["msedge", { channel: "msedge" }]]) {
  out.push({ browser: name, screen: "200 index", ...(await visit(opts, url)) });
  out.push({ browser: name, screen: "404 html", ...(await visit(opts, nope)) });
}
// SCHEMA.md を消すと、サーバーは 503 のテキストを返す
rmSync(join(wiki, "SCHEMA.md"));
await new Promise((r) => setTimeout(r, 3000));
for (const [name, opts] of [["chrome", { channel: "chrome" }], ["msedge", { channel: "msedge" }]]) {
  out.push({ browser: name, screen: "503 text", ...(await visit(opts, url)) });
}
py.kill();
console.log(JSON.stringify(out, null, 1));
