// performance-experiment.mjs の採取処理を使い、Pele の 4 方式を比較する。
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { createHash, randomUUID } from "node:crypto";
import { mkdirSync, readFileSync, readdirSync, renameSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import os from "node:os";
import { dirname, join, resolve } from "node:path";
import { setTimeout as sleep } from "node:timers/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import { imageFormats, loadStaticImageFixture, showStaticImages } from "./pele-image-fixture.mjs";

assert.equal(process.platform, "win32", "Windows 版の測定です");
const here = dirname(fileURLToPath(import.meta.url));
const samplerPath = join(here, "sample-browser-memory.ps1");
assert.ok(process.env.STATIC_IMAGE_FIXTURE, "書き出した画像のディレクトリを指定してください");
const fixture = loadStaticImageFixture(resolve(process.env.STATIC_IMAGE_FIXTURE));
const count = Number(process.env.COUNTS ?? 50);
const rounds = Number(process.env.ROUNDS ?? 10);
const repeats = Number(process.env.REPEATS ?? 2);
const idleMs = Number(process.env.IDLE_MS ?? 5000);
const minimumHeadroom = Number(process.env.MIN_COMMIT_HEADROOM_MIB ?? 4096) * 2 ** 20;
const sampleIntervalMs = 100;
const sampleStaleMs = 15000;
const drawTimeoutMs = 180000;
assert.ok([count, rounds, repeats, minimumHeadroom].every((n) => Number.isSafeInteger(n) && n > 0));
assert.ok(count <= fixture.manifest.count);
assert.ok(Number.isFinite(idleMs) && idleMs >= 0);

const out = resolve(process.env.PERF_OUT || join(here, "out", "static-image-" + Date.now()));
mkdirSync(dirname(out), { recursive: true });
mkdirSync(out);
process.env.PLAYWRIGHT_BROWSERS_PATH = resolve(process.env.PLAYWRIGHT_BROWSERS_PATH || join(here, "out/browsers"));
const require = createRequire(join(here, "../../tests/wiki/browse/package.json"));
const { webkit } = require("playwright");
const hash = (path) => createHash("sha256").update(readFileSync(path)).digest("hex");
const inputFiles = [fileURLToPath(import.meta.url), join(here, "pele-image-fixture.mjs"), samplerPath, ...fixture.files];
const hashes = Object.fromEntries(inputFiles.map((file) => [file, hash(file)]));
const inventoryRoots = [
  dirname(require.resolve("playwright/package.json")),
  dirname(require.resolve("playwright-core/package.json")),
  dirname(webkit.executablePath()),
];

function inventory(root) {
  const entries = [];
  function walk(directory, prefix) {
    for (const item of readdirSync(directory, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name, "en"))) {
      if (item.name.startsWith(".") || ["INSTALLATION_COMPLETE", "DEPENDENCIES_VALIDATED"].includes(item.name)) continue;
      const path = join(directory, item.name);
      const name = prefix + item.name;
      if (item.isDirectory()) walk(path, name + "/");
      else if (item.isFile()) {
        const data = readFileSync(path);
        entries.push([name, data.length, createHash("sha256").update(data).digest("hex")]);
      }
    }
  }
  walk(root, "");
  return { root, files: entries.length, sha256: createHash("sha256").update(JSON.stringify(entries)).digest("hex") };
}

const inventories = inventoryRoots.map(inventory);
const conditions = imageFormats.map((name) => ({ name, monitor: true, prior: [] }));
const result = {
  format: 2, mode: "memory", design: "static-image", started: new Date().toISOString(),
  repeats, counts: [count], browsers: ["webkit"], freshBrowserPerCase: true, samplerEnabled: true,
  idleMs, conditions, nodeVersion: process.version, playwrightVersion: require("playwright/package.json").version,
  inventories, environment: { platform: process.platform, arch: process.arch, osRelease: os.release(),
    cpu: os.cpus()[0]?.model, logicalCpus: os.cpus().length, totalMemoryBytes: os.totalmem() },
  drawTimeoutMs, startupPaddingMs: 0, requestsGC: false, minimumSystemCommitHeadroomBytes: minimumHeadroom,
  rounds, staticImage: fixture.manifest, sampleIntervalMs, sampleStaleMs, hashes,
  timingDefinition: "画像の差し替え開始から先頭・全画像の img.decode() が解決するまで。SVG のラスタライズ完了は待たない。",
  memoryDefinition: "専用ブラウザと列挙できた子孫の標本。画面外の画像にも img.decode() を呼ぶ条件で採取する。",
  cases: [],
};
const save = () => writeFileSync(join(out, "results.json"), JSON.stringify(result, null, 2) + "\n", "utf8");

async function bounded(promise, ms, label, stop) {
  let timer;
  try {
    const timeout = new Promise((_, reject) => {
      timer = setTimeout(() => reject(new Error(label + "が時間切れ")), ms);
    });
    return await Promise.race(stop ? [promise, timeout, stop] : [promise, timeout]);
  } finally {
    clearTimeout(timer);
  }
}

class Sampler {
  constructor(pid, id, prefix) {
    assert.ok(readFileSync(samplerPath).subarray(0, 3).equals(Buffer.from([239, 187, 191])));
    this.pid = pid; this.id = id; this.revision = 0; this.error = null; this.stderr = "";
    this.paths = Object.fromEntries(["control", "stop", "ready", "memory"].map((n) => [n, prefix + "-" + n + ".json"]));
    this.phase("startup");
    this.child = spawn(process.env.MEMORY_SAMPLER || "powershell.exe", ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", samplerPath,
      "-BrowserProcessId", String(pid), "-RunId", id, "-ControlFile", this.paths.control, "-StopFile", this.paths.stop,
      "-OutputFile", this.paths.memory, "-ReadyFile", this.paths.ready, "-IncludeProcessRows", "-IncludeSystemCommit", "-IntervalMs", String(sampleIntervalMs)],
      { windowsHide: true, stdio: ["ignore", "ignore", "pipe"] });
    this.child.on("error", (e) => { this.error = String(e); });
    this.closed = new Promise((resolve) => this.child.once("close", resolve));
    this.child.stderr.setEncoding("utf8"); this.child.stderr.on("data", (s) => { this.stderr += s; });
  }
  phase(name) {
    this.revision++;
    const data = { run_id: this.id, revision: this.revision, case: this.id, phase: name, phase_set_utc_ms: Date.now() };
    writeFileSync(this.paths.control + ".tmp", JSON.stringify(data), "utf8");
    // Get-Content が開く短い間だけ、Windows で置換を拒まれる場合がある。
    for (let i = 0; ; i++) {
      try { renameSync(this.paths.control + ".tmp", this.paths.control); break; }
      catch (e) { if (!["EPERM", "EBUSY"].includes(e.code) || i >= 20) throw e; Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 10); }
    }
    this.phaseUtcMs = data.phase_set_utc_ms;
  }
  latest() {
    try { return JSON.parse(readFileSync(this.paths.ready, "utf8")); } catch (_) { return null; }
  }
  get failure() {
    if (this.error) return this.error;
    if (this.child.exitCode === null && this.child.signalCode === null) return null;
    return this.stderr || "終了状態: " + (this.child.signalCode ?? this.child.exitCode);
  }
  async sample(minimum = 1) {
    let first;
    for (let i = 0; i < 400; i++) {
      if (this.failure) throw new Error("計測用プロセスが停止: " + this.failure);
      const s = this.latest();
      if (s?.run_id === this.id && s.revision === this.revision && s.stable) {
        assert.equal(s.root_pid, this.pid); assert.ok(s.processes > 0 && s.private_bytes > 0);
        if (s.missing_children.length > 0) { first = undefined; await sleep(50); continue; }
        first ??= s.sequence;
        if (s.sequence >= first + minimum - 1) return s;
      }
      await sleep(50);
    }
    throw new Error("今回のフェーズの標本を取得できない");
  }
  async stop() {
    writeFileSync(this.paths.stop, "stop", "utf8");
    let timer;
    try {
      await Promise.race([this.closed, new Promise((_, reject) => { timer = setTimeout(() => { this.child.kill(); reject(new Error("計測の停止が時間切れ")); }, 10000); })]);
    } finally { clearTimeout(timer); }
    if (this.error || this.child.exitCode !== 0) throw new Error("計測が失敗: " + (this.error || this.stderr));
    const samples = JSON.parse(readFileSync(this.paths.memory, "utf8"));
    assert.ok(Array.isArray(samples) && samples.length > 0);
    assert.ok(samples.every((s) => s.run_id === this.id && s.root_pid === this.pid && s.processes > 0 && s.private_bytes > 0 && s.process_ids.includes(this.pid)));
    return samples;
  }
}

async function run(condition, repeat) {
  const record = {
    browser: "webkit", count, repeat, id: randomUUID(), mode: "memory", condition: condition.name,
    monitored: true, priorCounts: [], freshBrowserForTarget: true,
    checkpoints: [], events: [], rounds: [], availableMemoryBefore: os.freemem(),
  };
  const prefix = join(out, record.id);
  const dump = () => writeFileSync(prefix + "-case.json", JSON.stringify(record, null, 2) + "\n", "utf8");
  let rejectForHeadroom;
  const resourceLimit = new Promise((_, reject) => { rejectForHeadroom = reject; });
  const step = async (label, action, ms = 30000) => {
    record.action = label;
    record.events.push({ label, utcMs: Date.now() });
    dump();
    return bounded(action(), ms, label, resourceLimit);
  };
  let server, sampler, monitor;
  const stopBrowser = async () => {
    if (!server) return;
    try {
      await bounded(server.kill(), 15000, "専用ブラウザの終了");
      record.cleanupMethod = "owned-browser-kill";
    } catch (error) {
      record.ok = false;
      record.killError = String(error);
      record.cleanupIncomplete = true;
    }
  };

  try {
    result.activeCase = record.id;
    save();
    server = await step("ブラウザの起動", () => webkit.launchServer({ timeout: 30000 }), 35000);
    const browser = await step("ブラウザへの接続", () => webkit.connect(server.wsEndpoint(), { timeout: 10000 }), 15000);
    record.pid = server.process().pid;
    record.version = browser.version();
    sampler = new Sampler(record.pid, record.id, prefix);
    let lastSample = await step("監視の準備", () => sampler.sample());
    let lastAdvance = performance.now();
    const stopMeasurement = (reason, message) => {
      record.resourceStop = { reason, at: new Date().toISOString(), action: record.action, sample: lastSample };
      rejectForHeadroom(new Error(message));
    };
    const checkMonitor = () => {
      if (record.resourceStop) return;
      const sample = sampler.latest();
      if (sample?.run_id === record.id && sample.root_pid === record.pid && sample.sequence > lastSample.sequence) {
        lastSample = sample;
        lastAdvance = performance.now();
      }
      if (sampler.failure) stopMeasurement("sampler-exited", "計測用プロセスが停止: " + sampler.failure);
      else if (performance.now() - lastAdvance >= sampleStaleMs) {
        stopMeasurement("sampler-stale", "計測用プロセスから新しい標本を取得できない");
      } else if (!Number.isSafeInteger(lastSample.system_commit_headroom_bytes)) {
        stopMeasurement("headroom-unavailable", "OS 全体のコミット余力を取得できない");
      } else if (lastSample.system_commit_headroom_bytes < minimumHeadroom) {
        stopMeasurement("headroom", "OS 全体のコミット余力が停止条件を下回った");
      }
    };
    checkMonitor();
    if (record.resourceStop) await resourceLimit;
    monitor = setInterval(checkMonitor, 200);

    const context = await step("context を作る", () => browser.newContext({ viewport: { width: 1200, height: 900 } }));
    const page = await step("ページを作る", () => context.newPage());
    await step("ページを開く", () => page.goto(pathToFileURL(fixture.pagePath).href, { waitUntil: "domcontentloaded" }));
    await step("親のフォントの準備", () => page.evaluate(() => document.fonts.ready.then(() => undefined)), 10000);
    const checkpoint = async (phase) => {
      sampler.phase(phase);
      const sample = await Promise.race([resourceLimit, sampler.sample(2)]);
      const observedUtcMs = Date.now();
      const outer = page.isClosed() ? null : await bounded(page.evaluate(() => ({
        frames: document.querySelectorAll("iframe").length,
        images: document.querySelectorAll("img.fig-img").length,
      })), 10000, "枠の観察", resourceLimit);
      if (outer) assert.equal(outer.frames, 0);
      record.checkpoints.push({ phase, phaseSetUtcMs: sampler.phaseUtcMs, observedUtcMs, sample, outer });
      dump();
    };
    await checkpoint("empty");
    const documentId = await step("文書の識別", () => page.evaluate((id) => window.__documentId = id, randomUUID()));
    for (let number = 1; number <= rounds; number++) {
      const round = { number, documentId };
      record.rounds.push(round);
      for (const color of ["light", "dark"]) {
        const phase = "round-" + number + "-" + color;
        sampler.phase(phase);
        round[color] = await step(phase, () => showStaticImages(
          page, fixture.manifest.images[color].slice(0, count), condition.name, color), drawTimeoutMs + 45000);
        assert.equal(round[color].documentId, documentId);
        assert.equal(round[color].images, count);
        if (color === "light") await checkpoint(phase + "-decoded");
      }
      await checkpoint("round-" + number + "-displayed");
      sampler.phase("round-" + number + "-idle");
      await Promise.race([resourceLimit, sleep(idleMs)]);
      await checkpoint("round-" + number + "-retained");
    }
    await step("context を閉じる", () => context.close());
    await checkpoint("context_closed");
    record.ok = true;
  } catch (error) {
    record.ok = false;
    record.error = String(error.stack || error);
    dump();
  } finally {
    clearInterval(monitor);
    // 停止指示を先に書き、監視で異常を検出した場合はブラウザの終了もすぐに始める。
    const sampling = sampler?.stop();
    const closing = record.resourceStop ? stopBrowser() : null;
    if (sampling) {
      try {
        const samples = await sampling;
        record.memory = {
          samples: samples.length, privatePeakBytes: Math.max(...samples.map((s) => s.private_bytes)),
          boundarySamples: samples.filter((s) => !s.stable).length,
          missingChildrenSamples: samples.filter((s) => s.missing_children.length > 0).length,
          samplerCpuMs: samples.at(-1).sampler_cpu_ms - samples[0].sampler_cpu_ms,
          elapsedMs: samples.at(-1).elapsed_ms - samples[0].elapsed_ms,
        };
      } catch (error) {
        record.ok = false;
        record.samplerError = String(error.stack || error);
      }
    }
    await (closing ?? stopBrowser());
  }
  dump();
  result.cases.push(record);
  save();
  console.log(JSON.stringify({ count, repeat, condition: record.condition, ok: record.ok,
    error: record.error, samplerError: record.samplerError, killError: record.killError }));
  return record.ok && !record.cleanupIncomplete;
}

save();
cases: for (let repeat = 0; repeat < repeats; repeat++) {
  for (const condition of repeat % 2 === 0 ? conditions : conditions.toReversed()) {
    if (!(await run(condition, repeat + 1))) break cases;
  }
}
try {
  for (const [path, before] of Object.entries(hashes)) assert.equal(hash(path), before, "測定中に入力が変わった: " + path);
  assert.deepEqual(inventoryRoots.map(inventory), inventories);
  result.inputsUnchanged = true;
} catch (error) {
  result.inputsUnchanged = false;
  result.provenanceError = String(error);
}
const interrupted = result.cases.at(-1);
if (interrupted?.resourceStop && interrupted.memory && interrupted.cleanupMethod) {
  // 既存の集計スクリプトに、途中までの標本であることを伝える。
  const stop = { id: interrupted.id, pid: interrupted.pid, ...interrupted.resourceStop };
  writeFileSync(join(out, "resource-stop.json"), JSON.stringify(stop, null, 2) + "\n", "utf8");
}
result.activeCase = null;
result.finished = new Date().toISOString();
save();
process.exitCode = Number(!result.inputsUnchanged ||
  result.cases.length !== repeats * conditions.length || result.cases.some((record) => !record.ok));
