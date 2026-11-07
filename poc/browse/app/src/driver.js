/* PoC 用の駆動スクリプト。sessionStorage の段階の番号で test.mjs の scenario() を再現する。 */
(function () {
  if (window.top !== window) return;
  var handled = -1; var inFlight = false; // 1 文書で 1 段階だけ進める（bfcache 復帰の pageshow だけ再開）
  function stage() { try { return parseInt(sessionStorage.getItem("__stage") || "0", 10); } catch (e) { return -1; } }
  function setStage(n) { sessionStorage.setItem("__stage", String(n)); }
  function report(step, extra, cb) {
    var data = { step: step, href: location.href, origin: location.origin, ua: navigator.userAgent,
      external: performance.getEntriesByType("resource").map(function (r) { return r.name; })
        .filter(function (u) { return u.indexOf(location.origin + "/") !== 0 && u.indexOf("data:") !== 0; }) };
    for (var k in extra) data[k] = extra[k];
    var done = false;
    function fin() { if (!done) { done = true; if (cb) cb(); } }
    var img = new Image();
    img.onload = img.onerror = fin;
    setTimeout(fin, 3000);
    img.src = "/__report?step=" + encodeURIComponent(step) + "&data=" + encodeURIComponent(JSON.stringify(data));
  }
  function waitFor(cond, ms, cb) {
    var t0 = Date.now();
    (function poll() {
      var ok = false; try { ok = cond(); } catch (e) {}
      if (ok || Date.now() - t0 > ms) return cb(ok);
      setTimeout(poll, 50);
    })();
  }
  function findByText(sel, text) {
    var l = document.querySelectorAll(sel);
    for (var i = 0; i < l.length; i++) if (l[i].textContent === text) return l[i];
    return null;
  }
  function tick() {
    var s = stage();
    if (s < 0 || s === handled || inFlight) return;
    handled = s;
    inFlight = true;
    var navReady = function () { return window.__probe && window.__browse && window.__browse.navLoaded; };
    function probeStep(name, next, action) {
      waitFor(navReady, 4000, function () {
        var p = window.__probe();
        setStage(next);
        report(name, { probe: p }, action);
      });
    }
    if (s === 0) probeStep("index", 1, function () { findByText("#nav-list a", "ナレッジグラフ").click(); });
    else if (s === 1) probeStep("kg", 2, function () { findByText("article a.wl", "オントロジー#定義").click(); });
    else if (s === 2) probeStep("anchor", 3, function () { history.back(); });
    else if (s === 3) {
      waitFor(function () { return findByText("article a.wl", "entities/山田 太郎"); }, 4000, function () {
        setStage(4);
        findByText("article a.wl", "entities/山田 太郎").click();
      });
    } else if (s === 4) {
      waitFor(navReady, 4000, function () {
        var p0 = window.__probe();
        setStage(5);
        report("entity", { probe: p0 }, function () {
          var inp = document.getElementById("search");
          inp.value = "知識表現";
          inp.dispatchEvent(new Event("input", { bubbles: true }));
          waitFor(function () { return document.querySelectorAll("#search-results a").length > 0; }, 5000, function () {
            report("search", { probe: window.__probe() }, function () {
              setStage(6);
              location.href = "/concepts/" + encodeURIComponent("ナレッジグラフ") + ".html";
            });
          });
        });
      });
    } else if (s === 6) {
      waitFor(function () { return document.querySelector("article .wl-unresolved"); }, 4000, function () {
        var before = location.href;
        document.querySelector("article .wl-unresolved").click();
        setTimeout(function () {
          setStage(7);
          report("unresolved", { navigated: location.href !== before, before: before, after: location.href }, function () {
            report("done", {});
          });
        }, 300);
      });
    }
  }
  window.addEventListener("load", tick);
  window.addEventListener("pageshow", function (e) { if (e.persisted) { inFlight = false; setTimeout(tick, 0); } });
  if (document.readyState === "complete") tick();
})();
