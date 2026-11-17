/* 図の描画の PoC の枠の側。配布対象ではない。
 *
 * sandbox の枠（不透明なオリジン）の中で動く。親から図のソースと配色を受け取り、
 * Mermaid で描いて、SVG の文字列を返す。親の DOM には触れない。
 */
(function () {
  "use strict";
  var violations = [];
  document.addEventListener("securitypolicyviolation", function (e) {
    violations.push(e.violatedDirective + " " + (e.blockedURI || ""));
  });
  var parentWin = window.parent;
  function post(m) { parentWin.postMessage(m, "*"); }

  // 図の側（%%{init}%% など）から変えられない設定。既定の secure に足す
  var SECURE = ["secure", "securityLevel", "startOnLoad", "maxTextSize", "suppressErrorRendering", "maxEdges",
                "theme", "themeVariables", "themeCSS", "fontFamily", "htmlLabels", "darkMode", "look"];

  function config(vars) {
    return {
      startOnLoad: false,
      securityLevel: "strict",
      suppressErrorRendering: true,
      htmlLabels: false,
      flowchart: { htmlLabels: false },
      theme: "base",
      themeVariables: vars,
      fontFamily: vars.fontFamily,
      maxTextSize: 50000,
      secure: SECURE
    };
  }

  var host = document.createElement("div");
  document.body.appendChild(host);

  function normalize(svgText) {
    host.innerHTML = svgText;
    var svg = host.querySelector("svg");
    if (!svg) throw new Error("svg がない");
    var vb = (svg.getAttribute("viewBox") || "").trim().split(/[\s,]+/).map(Number);
    var w = vb.length === 4 ? vb[2] : svg.getBBox().width;
    var h = vb.length === 4 ? vb[3] : svg.getBBox().height;
    svg.setAttribute("width", String(w));
    svg.setAttribute("height", String(h));
    svg.removeAttribute("style");
    var title = svg.querySelector("title");
    var out = {
      svg: new XMLSerializer().serializeToString(svg),
      w: w, h: h,
      title: title ? title.textContent : null,
      foreignObject: !!svg.querySelector("foreignObject")
    };
    host.textContent = "";
    return out;
  }

  var queue = Promise.resolve();
  window.addEventListener("message", function (e) {
    if (e.source !== parentWin) return;
    var d = e.data;
    if (!d || d.type !== "render" || !Array.isArray(d.items)) return;
    queue = queue.then(function () { return renderAll(d); });
  });

  function renderAll(d) {
    mermaid.initialize(config(d.theme || {}));
    var chain = Promise.resolve();
    d.items.forEach(function (item, i) {
      chain = chain.then(function () {
        return mermaid.render("fig-" + d.seq + "-" + i, String(item.source)).then(function (r) {
          var n = normalize(r.svg);
          post({ type: "result", seq: d.seq, id: item.id, ok: true, svg: n.svg, w: n.w, h: n.h,
                 title: n.title, foreignObject: n.foreignObject });
        }, function (err) {
          post({ type: "result", seq: d.seq, id: item.id, ok: false,
                 error: String(err && err.message || err).slice(0, 300) });
        });
      });
    });
    return chain.then(function () {
      // 違反のイベントは非同期に届くので、少し待ってから数える
      return new Promise(function (res) { setTimeout(res, 100); });
    }).then(function () {
      post({ type: "done", seq: d.seq, violations: violations.slice() });
    });
  }

  if (typeof mermaid === "undefined") {
    post({ type: "load-error" });
    return;
  }
  post({ type: "ready" });
})();
