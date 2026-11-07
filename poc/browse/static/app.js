/* ADR-0010 の PoC の画面。classic なスクリプトだけを使い、fetch も ES モジュールも使わない。 */
(function () {
  var root = document.documentElement.getAttribute("data-root") || "";
  var state = window.__browse = { navLoaded: false, searchLoaded: false, errors: [] };
  function href(path) {
    return root + path.split("/").map(encodeURIComponent).join("/");
  }
  var nav = document.getElementById("nav");
  if (!window.WIKI_NAV) { state.errors.push("nav.js が読めない"); return; }
  if (window.WIKI_NAV.protocol_version !== 1) { state.errors.push("未対応の契約の版"); return; }
  state.navLoaded = true;
  var box = document.createElement("input");
  box.type = "search"; box.id = "search"; box.placeholder = "題名、要約、タグ、見出しで探す";
  var results = document.createElement("ul"); results.id = "search-results";
  var list = document.createElement("ul"); list.id = "nav-list";
  window.WIKI_NAV.pages.forEach(function (p) {
    var li = document.createElement("li"); var a = document.createElement("a");
    a.href = href(p[0]); a.textContent = p[1]; li.appendChild(a); list.appendChild(li);
  });
  nav.appendChild(box); nav.appendChild(results); nav.appendChild(list);
  function loadSearch(done) {
    if (window.WIKI_SEARCH) { done(); return; }
    var s = document.createElement("script");
    s.src = root + "data/search.js";
    s.onload = function () { state.searchLoaded = true; done(); };
    s.onerror = function () { state.errors.push("search.js が読めない"); };
    document.body.appendChild(s);
  }
  function run() {
    var q = box.value.normalize("NFC").toLowerCase().trim();
    results.textContent = "";
    if (!q) return;
    window.WIKI_SEARCH.rows.forEach(function (r) {
      var hay = [r[1], r[2]].concat(r[3], r[4]).join("\n").normalize("NFC").toLowerCase();
      if (hay.indexOf(q) >= 0) {
        var li = document.createElement("li"); var a = document.createElement("a");
        a.href = href(r[0]); a.textContent = r[1]; li.appendChild(a); results.appendChild(li);
      }
    });
  }
  box.addEventListener("input", function () { loadSearch(run); });
})();
