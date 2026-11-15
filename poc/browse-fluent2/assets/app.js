/* 閲覧の画面の試作（Fluent 2）。classic なスクリプトで、fetch、ES モジュール、Web Worker を使わない。
   要素を作るほかに変えるのは、class、hidden、open、aria-* と、<html> の data-theme だけである。
   要素の style には触らない。 */
(function () {
  "use strict";
  var doc = document.documentElement;
  var root = doc.getAttribute("data-root") || "";
  var NAV = window.WIKI_NAV;
  var TYPE_LABELS = { source: "ソース", entity: "エンティティ", concept: "コンセプト", synthesis: "シンセシス" };
  var SVG_NS = "http://www.w3.org/2000/svg";
  var CHEVRON = "M15.85 7.65c.2.2.2.5 0 .7l-5.46 5.49a.55.55 0 0 1-.78 0L4.15 8.35a.5.5 0 1 1 .7-.7L10 12.8l5.15-5.16c.2-.2.5-.2.7 0";
  var SEARCH = "M13.73 14.44a6.5 6.5 0 1 1 .7-.7l3.42 3.4a.5.5 0 0 1-.63.77l-.07-.06zm-.71-.71A5.5 5.5 0 0 0 15 9.5a5.5 5.5 0 1 0-1.98 4.23";
  var DISMISS = "m4.09 4.22.06-.07a.5.5 0 0 1 .63-.06l.07.06L10 9.29l5.15-5.14a.5.5 0 0 1 .63-.06l.07.06c.18.17.2.44.06.63l-.06.07L10.71 10l5.14 5.15c.18.17.2.44.06.63l-.06.07a.5.5 0 0 1-.63.06l-.07-.06L10 10.71l-5.15 5.14a.5.5 0 0 1-.63.06l-.07-.06a.5.5 0 0 1-.06-.63l.06-.07L9.29 10 4.15 4.85a.5.5 0 0 1-.06-.63l.06-.07z";
  var state = window.__browse = { navLoaded: false, errors: [] };
  var isIndex = document.body.classList.contains("page-index");
  var article = document.getElementById("_article");
  var currentPath = article ? "pages/" + article.getAttribute("data-page-id") + ".html" : "";

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) { e.className = cls; }
    if (text !== undefined) { e.textContent = text; }
    return e;
  }

  function icon(d, size) {
    var svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("class", "fui-Icon");
    svg.setAttribute("width", size || "20");
    svg.setAttribute("height", size || "20");
    svg.setAttribute("viewBox", "0 0 20 20");
    svg.setAttribute("fill", "currentColor");
    svg.setAttribute("aria-hidden", "true");
    var p = document.createElementNS(SVG_NS, "path");
    p.setAttribute("d", d);
    svg.appendChild(p);
    return svg;
  }

  function href(path) { return root + path; }

  /* --- 配色の切り替え（fui-Select） --- */
  function themeSelect() {
    var api = window.__browseTheme;
    if (!api) { return null; }
    var wrap = el("div", "theme-field");
    var label = el("label", "fui-Label theme-label", "配色");
    label.htmlFor = "_theme";
    var sel = el("span", "fui-Select");
    sel.setAttribute("data-size", "small");
    var s = el("select", "fui-Select__select");
    s.id = "_theme";
    var names = { auto: "OS に合わせる", light: "ライト", dark: "ダーク" };
    for (var i = 0; i < api.values.length; i++) {
      var o = el("option", "", names[api.values[i]]);
      o.value = api.values[i];
      s.appendChild(o);
    }
    s.value = api.read();
    s.addEventListener("change", function () { api.save(s.value); });
    var ic = el("span", "fui-Select__icon");
    ic.appendChild(icon(CHEVRON, "1em"));
    sel.appendChild(s);
    sel.appendChild(ic);
    wrap.appendChild(label);
    wrap.appendChild(sel);
    return wrap;
  }

  /* --- 検索欄（fui-SearchBox） --- */
  function searchBox(id, placeholder, onInput) {
    var box = el("span", "fui-SearchBox fui-Input");
    box.setAttribute("data-size", "small");
    var before = el("span", "fui-SearchBox__contentBefore fui-Input__contentBefore");
    before.appendChild(icon(SEARCH, "1em"));
    var input = el("input", "fui-SearchBox__input fui-Input__input");
    input.type = "search";
    input.id = id;
    input.placeholder = placeholder;
    input.setAttribute("aria-label", placeholder);
    var after = el("span", "fui-SearchBox__contentAfter fui-Input__contentAfter");
    var dismiss = el("span", "fui-SearchBox__dismiss");
    dismiss.setAttribute("role", "button");
    dismiss.setAttribute("aria-label", "消去");
    dismiss.tabIndex = -1;
    dismiss.appendChild(icon(DISMISS, "1em"));
    dismiss.addEventListener("mousedown", function (ev) { ev.preventDefault(); });
    dismiss.addEventListener("click", function () { input.value = ""; onInput(""); input.focus(); });
    after.appendChild(dismiss);
    box.appendChild(before);
    box.appendChild(input);
    box.appendChild(after);
    input.addEventListener("input", function () { onInput(input.value); });
    input.addEventListener("keydown", function (ev) {
      if (ev.isComposing || ev.keyCode === 229) { return; }
      if (ev.key === "Escape") { input.value = ""; onInput(""); }
    });
    return box;
  }

  /* --- 検索の索引（後から読む） --- */
  var searchWaiters = [];
  var searchLoading = false;
  function withSearch(fn) {
    if (window.WIKI_SEARCH) { fn(window.WIKI_SEARCH); return; }
    searchWaiters.push(fn);
    if (searchLoading) { return; }
    searchLoading = true;
    var s = document.createElement("script");
    s.src = root + "data/search.js";
    s.onload = function () { var w = searchWaiters; searchWaiters = []; for (var i = 0; i < w.length; i++) { w[i](window.WIKI_SEARCH); } };
    s.onerror = function () { state.errors.push("search.js を読めない"); };
    document.body.appendChild(s);
  }

  function fold(s) { return String(s).normalize("NFC").toLowerCase(); }
  function matches(row, words) {
    var hay = fold([row.title, row.summary, (row.tags || []).join(" ")].join(" "));
    for (var i = 0; i < words.length; i++) { if (hay.indexOf(words[i]) < 0) { return false; } }
    return true;
  }
  function words(q) { return fold(q).split(/[\s　]+/).filter(function (w) { return w; }); }

  /* --- 左の木 --- */
  function containsCurrent(g) {
    for (var i = 0; i < g.items.length; i++) { if (g.items[i].path === currentPath) { return true; } }
    for (var c = 0; c < g.children.length; c++) { if (containsCurrent(g.children[c])) { return true; } }
    return false;
  }

  function treeItem(it) {
    if (it.state === "resolved") {
      var a = el("a", "fui-NavSubItem", it.label);
      a.href = href(it.path);
      a.setAttribute("aria-current", it.path === currentPath ? "page" : "false");
      if (it.path === currentPath) { a.classList.add("is-current"); }
      return a;
    }
    var span = el("span", "fui-NavSubItem wl wl-" + it.state, it.label);
    span.title = it.state === "unresolved" ? "ページがない" : "行き先を 1 つに決められない";
    return span;
  }

  function treeGroup(g, depth) {
    var d = el("details", "fui-NavCategory tree-group nav-depth-" + Math.min(depth, 6));
    d.open = containsCurrent(g);
    var sum = el("summary", "fui-NavCategoryItem");
    var name = el("span", "tree-name", g.title);
    var cnt = el("span", "fui-Caption1 tree-count", String(g.count));
    var list = el("a", "fui-Link tree-filter", "一覧");
    list.href = href("index.html") + "#group=" + encodeURIComponent(g.id);
    list.setAttribute("data-size", "small");
    var exp = el("span", "fui-NavCategoryItem__expandIcon");
    exp.setAttribute("aria-hidden", "true");
    exp.appendChild(icon(CHEVRON));
    sum.appendChild(name);
    sum.appendChild(cnt);
    sum.appendChild(list);
    sum.appendChild(exp);
    d.appendChild(sum);
    var sub = el("div", "fui-NavSubItemGroup");
    for (var i = 0; i < g.items.length; i++) { sub.appendChild(treeItem(g.items[i])); }
    for (var c = 0; c < g.children.length; c++) { sub.appendChild(treeGroup(g.children[c], depth + 1)); }
    d.appendChild(sub);
    return d;
  }

  function indexTree(groups, depth, current) {
    var ul = el("ul", "tree-groups nav-depth-" + Math.min(depth, 6) + (depth ? "" : " tree-groups-root"));
    for (var i = 0; i < groups.length; i++) {
      var g = groups[i];
      var li = el("li");
      var a = el("a", "fui-NavItem nav-depth-" + Math.min(depth, 6));
      a.href = "#group=" + encodeURIComponent(g.id);
      a.setAttribute("data-group", g.id);
      a.appendChild(el("span", "tree-name", g.title));
      a.appendChild(el("span", "fui-Caption1 tree-count", String(g.count)));
      li.appendChild(a);
      if (g.children.length) { li.appendChild(indexTree(g.children, depth + 1)); }
      ul.appendChild(li);
    }
    return ul;
  }

  var navBody = document.getElementById("_navbody");
  var head = document.querySelector(".nav-head");
  if (!navBody || !NAV) { state.errors.push("nav.js を読めない"); return; }
  var themeField = themeSelect();
  if (themeField && head) { head.appendChild(themeField); }

  var drawer = el("details", "drawer");
  var drawerSum = el("summary", "fui-Button drawer-toggle", "メニュー");
  drawerSum.setAttribute("data-appearance", "subtle");
  drawer.appendChild(drawerSum);
  var tree = el("div", "tree");

  if (isIndex) {
    var all = el("a", "fui-NavItem tree-all");
    all.href = "#";
    all.setAttribute("data-group", "");
    all.appendChild(el("span", "tree-name", "すべてのページ"));
    tree.appendChild(all);
    tree.appendChild(indexTree(NAV.groups, 0));
  } else {
    /* 記事のページ: 検索欄と、その結果の場所 */
    var results = el("div", "sr-area");
    results.hidden = true;
    var box = searchBox("_q", "ページを探す", function (q) {
      var w = words(q);
      if (!w.length) { results.hidden = true; tree.hidden = false; return; }
      withSearch(function (data) {
        var hits = data.rows.filter(function (r) { return matches(r, w); });
        while (results.firstChild) { results.removeChild(results.firstChild); }
        results.appendChild(el("p", "fui-Caption1 sr-count", hits.length + " 件"));
        if (!hits.length) { results.appendChild(el("p", "fui-Caption1 sr-empty", "当たるページはない")); }
        var ul = el("ul", "fui-List sr-results");
        ul.setAttribute("role", "list");
        hits.slice(0, 30).forEach(function (r) {
          var li = el("li", "fui-ListItem");
          var a = el("a", "sr-link");
          a.href = href(r.path);
          a.appendChild(el("span", "sr-title", r.title));
          a.appendChild(el("span", "fui-Caption1 sr-meta", (TYPE_LABELS[r.type] || r.type) + " · " + r.group));
          li.appendChild(a);
          ul.appendChild(li);
        });
        results.appendChild(ul);
        results.hidden = false;
        tree.hidden = true;
      });
    });
    var field = el("div", "search");
    field.appendChild(box);
    field.appendChild(el("p", "fui-Caption1 search-hint", "/ で検索欄に移る"));
    navBody.appendChild(field);
    navBody.appendChild(results);
    for (var n = 0; n < NAV.groups.length; n++) { tree.appendChild(treeGroup(NAV.groups[n], 0)); }
    document.addEventListener("keydown", function (ev) {
      var t = ev.target;
      if (ev.key === "/" && !(t && (t.tagName === "INPUT" || t.tagName === "SELECT" || t.tagName === "TEXTAREA"))) {
        ev.preventDefault();
        document.getElementById("_q").focus();
      }
    });
  }
  drawer.appendChild(tree);
  navBody.appendChild(drawer);

  var wide = window.matchMedia("(min-width: 48.0625rem)");
  function syncDrawer() { if (wide.matches) { drawer.open = true; } }
  syncDrawer();
  if (wide.addEventListener) { wide.addEventListener("change", syncDrawer); }

  var cur = navBody.querySelector(".is-current");
  if (cur && cur.scrollIntoView) { cur.scrollIntoView({ block: "nearest" }); }

  /* --- 索引のページの絞り込み --- */
  if (isIndex) {
    var rows = Array.prototype.slice.call(document.querySelectorAll("#_index .fx-row"));
    var bar = document.getElementById("_filters");
    var countEl = document.getElementById("_count");
    var filt = { type: "", group: "", q: "" };
    var chips = el("div", "chips");
    chips.setAttribute("role", "group");
    chips.setAttribute("aria-label", "種類");
    var types = [""];
    rows.forEach(function (r) { var t = r.getAttribute("data-type"); if (types.indexOf(t) < 0) { types.push(t); } });
    types.forEach(function (t) {
      var b = el("button", "fui-ToggleButton fui-Button", t ? (Object.prototype.hasOwnProperty.call(TYPE_LABELS, t) ? TYPE_LABELS[t] : t) : "すべて");
      b.type = "button";
      b.setAttribute("data-size", "small");
      b.setAttribute("data-shape", "circular");
      b.setAttribute("aria-pressed", t === "" ? "true" : "false");
      b.addEventListener("click", function () {
        filt.type = t;
        Array.prototype.forEach.call(chips.children, function (c) { c.setAttribute("aria-pressed", c === b ? "true" : "false"); });
        apply();
      });
      chips.appendChild(b);
    });
    var sortWrap = el("span", "fui-Select sort");
    sortWrap.setAttribute("data-size", "small");
    var sort = el("select", "fui-Select__select");
    sort.setAttribute("aria-label", "並べ方");
    [["order", "索引の順"], ["updated", "更新の新しい順"], ["title", "題名の順"]].forEach(function (o) {
      var op = el("option", "", o[1]);
      op.value = o[0];
      sort.appendChild(op);
    });
    var sic = el("span", "fui-Select__icon");
    sic.appendChild(icon(CHEVRON, "1em"));
    sortWrap.appendChild(sort);
    sortWrap.appendChild(sic);
    sort.addEventListener("change", apply);
    var fbox = searchBox("_ixq", "題名、要約、タグで絞る", function (q) { filt.q = q; apply(); });
    var noscript = bar.querySelector("noscript");
    if (noscript) { bar.removeChild(noscript); }
    bar.appendChild(fbox);
    bar.appendChild(chips);
    bar.appendChild(sortWrap);

    var list = document.getElementById("_index");
    function apply() {
      var w = words(filt.q);
      var shown = 0;
      rows.forEach(function (r) {
        var ok = (!filt.type || r.getAttribute("data-type") === filt.type)
          && (!filt.group || (" " + r.getAttribute("data-groups") + " ").indexOf(" " + filt.group + " ") >= 0);
        if (ok && w.length) {
          var tags = Array.prototype.map.call(r.querySelectorAll("span.tag"), function (s) { return s.textContent; });
          var summ = r.querySelector(".ix-summary");
          ok = matches({ title: r.getAttribute("data-title"), summary: summ ? summ.textContent : "", tags: tags }, w);
        }
        r.hidden = !ok;
        if (ok) { shown++; }
      });
      var key = sort.value;
      var sorted = rows.slice().sort(function (a, b) {
        if (key === "updated") { return (b.getAttribute("data-updated") || "").localeCompare(a.getAttribute("data-updated") || ""); }
        if (key === "title") { return a.getAttribute("data-title").localeCompare(b.getAttribute("data-title"), "ja"); }
        return Number(a.getAttribute("data-order")) - Number(b.getAttribute("data-order"));
      });
      sorted.forEach(function (r) { list.appendChild(r); });
      countEl.textContent = shown + " 件";
      Array.prototype.forEach.call(tree.querySelectorAll("[data-group]"), function (a) {
        var on = a.getAttribute("data-group") === filt.group;
        a.setAttribute("aria-current", on ? "true" : "false");
        a.classList.toggle("is-current", on);
      });
    }
    function fromHash() {
      var m = /^#group=(.+)$/.exec(location.hash);
      filt.group = m ? decodeURIComponent(m[1]) : "";
      apply();
    }
    window.addEventListener("hashchange", fromHash);
    tree.addEventListener("click", function (ev) {
      var a = ev.target.closest ? ev.target.closest("[data-group]") : null;
      if (a && a.getAttribute("data-group") === "") { ev.preventDefault(); history.replaceState(null, "", "#"); filt.group = ""; apply(); }
    });
    fromHash();
  }
  state.navLoaded = true;
})();
