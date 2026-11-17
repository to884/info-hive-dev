/* 図の描画の PoC の親の側。配布対象ではない。
 *
 * - #_body の pre > code.language-mermaid があるときだけ、見えない sandbox の枠を 1 つ作る。
 * - 枠に図のソースと Fluent のトークンから作った配色を送り、SVG の文字列を受け取る。
 * - SVG は DOM に入れず、data: の <img> にして出す。要素の style には触らない。
 * - 配色が変わったら描き直す。
 * - 試験のために、状態を window.__figs に置く。
 */
(function () {
  "use strict";
  var codes = document.querySelectorAll("#_body pre > code.language-mermaid");
  var state = { state: "none", seq: 0, t0: performance.now(), tReady: null, tFirst: null, tDone: null,
                results: {}, frameViolations: null, renders: 0, theme: null };
  window.__figs = state;
  if (!codes.length) return;

  var frameName = /[?&]frame=file(&|$)/.test(location.search) ? "mermaid-frame-file.html"
    : /[?&]frame=nometa(&|$)/.test(location.search) ? "mermaid-frame-nometa.html" : "mermaid-frame.html";
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

  var frame = document.createElement("iframe");
  frame.className = "fig-frame";
  frame.setAttribute("sandbox", "allow-scripts");
  frame.setAttribute("title", "図の描画");
  frame.setAttribute("aria-hidden", "true");
  frame.setAttribute("tabindex", "-1");
  frame.src = frameName;
  var ready = false;
  var current = null;

  function send() {
    if (!ready) return;
    var theme = readTheme();
    if (current && current.key === theme.key) return;
    current = theme;
    state.theme = theme;
    state.seq += 1;
    state.state = "rendering";
    frame.contentWindow.postMessage({
      type: "render", seq: state.seq, theme: theme.vars,
      items: items.map(function (it) { return { id: it.id, source: it.source }; })
    }, "*");
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
    it.img.setAttribute("alt", msg.title || "図");
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

  var byId = {};
  items.forEach(function (it) { byId[it.id] = it; });

  window.addEventListener("message", function (e) {
    if (e.source !== frame.contentWindow) return;
    var d = e.data;
    if (!d || typeof d.type !== "string") return;
    if (d.type === "ready") {
      ready = true;
      state.tReady = performance.now() - state.t0;
      send();
      return;
    }
    if (d.seq !== state.seq) return;
    if (d.type === "result") {
      var it = byId[d.id];
      if (!it) return;
      var ok = d.ok === true && typeof d.svg === "string" && d.svg.slice(0, 4) === "<svg" &&
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
      state.frameViolations = d.violations;
      state.renders += 1;
      state.tDone = performance.now() - state.t0;
      state.state = "done";
    }
  });

  new MutationObserver(function () { send(); })
    .observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  if (window.matchMedia) {
    var mq = window.matchMedia("(prefers-color-scheme: dark)");
    if (mq.addEventListener) mq.addEventListener("change", send);
  }
  state.state = "loading";
  document.body.appendChild(frame);
})();
