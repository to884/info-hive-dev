/* 図の描画の PoC の親の側（2 回目）。配布対象ではない。
 *
 * - http(s) のページで、#_body の pre > code.language-mermaid があるときだけ動く。
 * - 図 1 つにつき、トークンのない /_frame/ の下の枠を 1 つ作り、その図のソースと配色だけを送る。
 *   描き終えたら枠を消す。枠は、攻撃者自身が書いた図のほかに何も知らない。
 * - SVG は DOM に入れず、data: の <img> にして出す。要素の style には触らない。
 * - 配色が変わったら描き直す。
 * - 試験のために、状態を window.__figs に置く。
 */
(function () {
  "use strict";
  var state = { state: "none", seq: 0, t0: performance.now(), tReady: null, tFirst: null, tDone: null,
                results: {}, frameViolations: [], renders: 0, frames: 0, theme: null };
  window.__figs = state;
  if (location.protocol !== "http:" && location.protocol !== "https:") return;
  var codes = document.querySelectorAll("#_body pre > code.language-mermaid");
  if (!codes.length) return;

  var FRAME_URL = location.origin + "/_frame/mermaid-frame.html";
  var CONCURRENCY = 2;
  var READY_TIMEOUT = 20000;
  var items = [];
  for (var i = 0; i < codes.length; i++) {
    var pre = codes[i].parentNode;
    items.push({ id: "f" + i, pre: pre, source: codes[i].textContent, figure: null, img: null, details: null, bar: null,
                 poc: pre.getAttribute("data-poc-id") || ("f" + i) });
  }

  // Fluent のトークン（fluent2.css の CSS 変数）から、Mermaid の base テーマの変数を作る
  var TOKENS = {
    background: "--colorNeutralBackground1",
    primaryColor: "--colorBrandBackground2",
    primaryTextColor: "--colorNeutralForeground1",
    primaryBorderColor: "--colorBrandStroke1",
    secondaryColor: "--colorNeutralBackground3",
    secondaryTextColor: "--colorNeutralForeground1",
    secondaryBorderColor: "--colorNeutralStroke1",
    tertiaryColor: "--colorNeutralBackground2",
    tertiaryTextColor: "--colorNeutralForeground1",
    tertiaryBorderColor: "--colorNeutralStroke2",
    lineColor: "--colorNeutralForeground2",
    textColor: "--colorNeutralForeground1",
    mainBkg: "--colorBrandBackground2",
    nodeBorder: "--colorBrandStroke1",
    clusterBkg: "--colorNeutralBackground2",
    clusterBorder: "--colorNeutralStroke2",
    titleColor: "--colorNeutralForeground1",
    edgeLabelBackground: "--colorNeutralBackground1",
    noteBkgColor: "--colorPaletteYellowBackground1",
    noteTextColor: "--colorNeutralForeground1",
    noteBorderColor: "--colorNeutralStroke1"
  };

  function hex(value) {
    var v = (value || "").trim();
    var m = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(v);
    if (m) {
      var h = m[1];
      return "#" + (h.length === 3 ? h.replace(/./g, "$&$&") : h).toLowerCase();
    }
    m = /^rgba?\(\s*(\d+)[ ,]+(\d+)[ ,]+(\d+)/i.exec(v);
    if (m) {
      return "#" + [m[1], m[2], m[3]].map(function (n) {
        var s = Math.max(0, Math.min(255, +n)).toString(16);
        return s.length < 2 ? "0" + s : s;
      }).join("");
    }
    return null;
  }

  function luminance(h) {
    var n = parseInt(h.slice(1), 16);
    return (0.2126 * (n >> 16 & 255) + 0.7152 * (n >> 8 & 255) + 0.0722 * (n & 255)) / 255;
  }

  function readTheme() {
    var cs = getComputedStyle(document.documentElement);
    var vars = {};
    var missing = [];
    Object.keys(TOKENS).forEach(function (k) {
      var h = hex(cs.getPropertyValue(TOKENS[k]));
      if (h) vars[k] = h; else missing.push(TOKENS[k]);
    });
    vars.fontFamily = cs.getPropertyValue("--fontFamilyBase").trim() || "sans-serif";
    vars.fontSize = cs.getPropertyValue("--fontSizeBase300").trim() || "14px";
    vars.darkMode = vars.background ? luminance(vars.background) < 0.5 : false;
    return { vars: vars, missing: missing, key: JSON.stringify(vars) };
  }

  var NS = "http://www.w3.org/2000/svg";
  function chevron() {
    var span = document.createElement("span");
    span.className = "fui-AccordionHeader__expandIcon";
    span.setAttribute("aria-hidden", "true");
    var svg = document.createElementNS(NS, "svg");
    svg.setAttribute("class", "fui-Icon");
    svg.setAttribute("width", "20");
    svg.setAttribute("height", "20");
    svg.setAttribute("viewBox", "0 0 20 20");
    svg.setAttribute("fill", "currentColor");
    svg.setAttribute("aria-hidden", "true");
    var path = document.createElementNS(NS, "path");
    path.setAttribute("d", "M7.65 4.15c.2-.2.5-.2.7 0l5.49 5.46c.21.22.21.57 0 .78l-5.49 5.47a.5.5 0 0 1-.7-.71L12.8 10 7.65 4.85a.5.5 0 0 1 0-.7");
    svg.appendChild(path);
    span.appendChild(svg);
    return span;
  }

  function place(it, msg) {
    if (!it.figure) {
      it.figure = document.createElement("figure");
      it.figure.className = "fui-Card fig";
      it.figure.setAttribute("data-fig", "mermaid");
      it.figure.setAttribute("data-poc-id", it.poc);  // 試験が図を探す目印（PoC だけ）
      it.img = document.createElement("img");
      it.img.className = "fui-Image fig-img";
      it.figure.appendChild(it.img);
      it.details = document.createElement("details");
      it.details.className = "fui-AccordionItem fig-source";
      var summary = document.createElement("summary");
      summary.className = "fui-AccordionHeader__button";
      summary.appendChild(chevron());
      summary.appendChild(document.createTextNode("図のコード"));
      var panel = document.createElement("div");
      panel.className = "fui-AccordionPanel";
      it.details.appendChild(summary);
      it.details.appendChild(panel);
      it.pre.parentNode.insertBefore(it.figure, it.pre);
      it.pre.parentNode.insertBefore(it.details, it.pre);
      panel.appendChild(it.pre);
    }
    it.img.setAttribute("alt", typeof msg.title === "string" && msg.title ? msg.title.slice(0, 200) : "図");
    it.img.setAttribute("width", String(Math.round(msg.w)));
    it.img.setAttribute("height", String(Math.round(msg.h)));
    it.img.setAttribute("src", "data:image/svg+xml;charset=utf-8," + encodeURIComponent(msg.svg));
  }

  function fail(it) {
    if (it.figure || it.bar) return;
    it.bar = document.createElement("div");
    it.bar.className = "fui-MessageBar fig-error";
    it.bar.setAttribute("role", "group");
    it.bar.setAttribute("data-intent", "warning");
    it.bar.setAttribute("data-layout", "singleline");
    var body = document.createElement("div");
    body.className = "fui-MessageBarBody";
    body.textContent = "図を描けなかった。コードを表示している。";
    it.bar.appendChild(body);
    it.pre.parentNode.insertBefore(it.bar, it.pre);
  }

  // 図 1 つを、新しい枠で描く。終わったら（成功、失敗、時間切れ）枠を消して resolve する
  function renderOne(it, theme, seq) {
    return new Promise(function (resolve) {
      var frame = document.createElement("iframe");
      frame.className = "fig-frame";
      frame.setAttribute("sandbox", "allow-scripts");
      frame.setAttribute("title", "図の描画");
      frame.setAttribute("aria-hidden", "true");
      frame.setAttribute("tabindex", "-1");
      frame.setAttribute("width", "1200");
      frame.setAttribute("height", "800");
      var finished = false;
      var timer = setTimeout(function () { finish(); }, READY_TIMEOUT);
      function finish() {
        if (finished) return;
        finished = true;
        clearTimeout(timer);
        window.removeEventListener("message", onMessage);
        frame.remove();
        resolve();
      }
      function onMessage(e) {
        if (e.source !== frame.contentWindow) return;
        var d = e.data;
        if (!d || typeof d.type !== "string") return;
        if (d.type === "ready") {
          if (state.tReady === null) state.tReady = performance.now() - state.t0;
          frame.contentWindow.postMessage({ type: "render", seq: seq, theme: theme.vars,
                                            items: [{ id: it.id, source: it.source }] }, "*");
          return;
        }
        if (d.seq !== seq) return;
        if (d.type === "result" && d.id === it.id && seq === state.seq) {
          var ok = d.ok === true && typeof d.svg === "string" && d.svg.slice(0, 4) === "<svg" && d.svg.length <= 5e6 &&
            isFinite(d.w) && isFinite(d.h) && d.w > 0 && d.h > 0 && d.w <= 20000 && d.h <= 20000;
          state.results[it.poc] = { ok: ok, error: ok ? null : String(d.error || "不正な応答").slice(0, 300),
                                    foreignObject: !!d.foreignObject, title: d.title || null, length: ok ? d.svg.length : 0,
                                    svg: ok ? d.svg : null };
          if (ok) {
            place(it, d);
            if (state.tFirst === null) state.tFirst = performance.now() - state.t0;
          } else {
            fail(it);
          }
        } else if (d.type === "done") {
          if (Array.isArray(d.violations)) state.frameViolations = state.frameViolations.concat(d.violations.slice(0, 20));
          finish();
        }
      }
      window.addEventListener("message", onMessage);
      state.frames += 1;
      frame.src = FRAME_URL;
      document.body.appendChild(frame);
    });
  }

  var current = null;
  function run() {
    var theme = readTheme();
    if (current && current.key === theme.key) return;
    current = theme;
    state.theme = theme;
    state.seq += 1;
    var seq = state.seq;
    state.state = "rendering";
    var queue = items.slice();
    function worker() {
      if (seq !== state.seq) return Promise.resolve();
      var it = queue.shift();
      if (!it) return Promise.resolve();
      return renderOne(it, theme, seq).then(worker);
    }
    var workers = [];
    for (var w = 0; w < CONCURRENCY; w++) workers.push(worker());
    Promise.all(workers).then(function () {
      if (seq !== state.seq) return;
      state.renders += 1;
      state.tDone = performance.now() - state.t0;
      state.state = "done";
    });
  }

  new MutationObserver(run).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  if (window.matchMedia) {
    var mq = window.matchMedia("(prefers-color-scheme: dark)");
    if (mq.addEventListener) mq.addEventListener("change", run);
  }
  state.state = "loading";
  run();
})();
