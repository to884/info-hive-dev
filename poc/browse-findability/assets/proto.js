/* browse の索引とサイドバーの試作。classic なスクリプトだけを使い、style を触らない（クラスと属性だけ）。 */
(function () {
  "use strict";
  var doc = document.documentElement;
  var root = doc.getAttribute("data-root") || "";
  var variant = doc.getAttribute("data-variant") || "a";
  var NAV = window.PROTO_NAV || { groups: [] };
  var S = window.WIKI_SEARCH;
  var TYPE = { source: "ソース", entity: "エンティティ", concept: "コンセプト", synthesis: "シンセシス" };
  var art = document.getElementById("_article");
  var current = art ? art.getAttribute("data-page-id") : null;
  var isIndex = !art;
  var navbody = document.getElementById("_navbody");

  function href(path) { return root + path.split("/").map(encodeURIComponent).join("/"); }
  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) { e.className = cls; }
    if (text != null) { e.textContent = text; }
    return e;
  }
  function norm(s) { return String(s || "").normalize("NFC").toLowerCase(); }
  function badge(t) { return el("span", "badge t-" + (t || "none"), TYPE[t] || t || "種類なし"); }

  // --- 検索 ---
  var rows = [];
  if (S) {
    rows = S.rows.map(function (r) {
      return { p: r[0], i: r[1], t: r[2], s: r[3], y: r[4], g: r[5], h: r[6], u: r[7], gp: r[8],
               nt: norm(r[2]), ns: norm(r[3]), ng: r[5].map(norm), nh: r[6].map(norm) };
    });
  }
  // 語を空白で分け、どの語もどこかの欄に当たる行を返す。題名 > タグ > 見出し > 要約 の順に重みを付ける。
  function search(q) {
    var terms = norm(q).split(/\s+/).filter(Boolean);
    if (!terms.length) { return []; }
    var out = [];
    rows.forEach(function (r) {
      var score = 0, hits = [], ok = true;
      terms.forEach(function (term) {
        var best = 0;
        if (r.nt.indexOf(term) >= 0) { best = r.nt.indexOf(term) === 0 ? 12 : 8; hits.push(["題名", r.t, term]); }
        r.ng.forEach(function (g, k) { if (g.indexOf(term) >= 0) { best = Math.max(best, g === term ? 6 : 4); hits.push(["タグ", r.g[k], term]); } });
        r.nh.forEach(function (h, k) { if (h.indexOf(term) >= 0) { best = Math.max(best, 3); hits.push(["見出し", r.h[k], term]); } });
        if (r.ns.indexOf(term) >= 0) { best = Math.max(best, 2); hits.push(["要約", r.s, term]); }
        if (!best) { ok = false; }
        score += best;
      });
      if (ok) { out.push({ r: r, score: score, hits: hits }); }
    });
    out.sort(function (a, b) { return b.score - a.score || (a.r.t < b.r.t ? -1 : 1); });
    return out;
  }
  // 当たった文字に <mark> を付けて、要素に入れる（innerHTML は使わない）
  function highlight(node, text, terms) {
    var low = norm(text), pos = 0, marks = [];
    terms.forEach(function (t) { var k = low.indexOf(t); if (k >= 0) { marks.push([k, k + t.length]); } });
    marks.sort(function (a, b) { return a[0] - b[0]; });
    marks.forEach(function (m) {
      if (m[0] < pos) { return; }
      node.appendChild(document.createTextNode(text.slice(pos, m[0])));
      node.appendChild(el("mark", null, text.slice(m[0], m[1])));
      pos = m[1];
    });
    node.appendChild(document.createTextNode(text.slice(pos)));
  }
  function resultList(found, q, limit, rich) {
    var terms = norm(q).split(/\s+/).filter(Boolean);
    var ul = el("ul", "sr-results");
    found.slice(0, limit).forEach(function (f, n) {
      var li = el("li"), a = el("a");
      a.href = href(f.r.p);
      if (n === 0) { a.className = "is-active"; }
      var title = el("span", "sr-title"); highlight(title, f.r.t, terms); a.appendChild(title);
      var meta = el("span", "sr-meta");
      meta.appendChild(badge(f.r.y));
      if (f.r.gp.length) { meta.appendChild(document.createTextNode(" " + f.r.gp.join(" › "))); }
      a.appendChild(meta);
      var other = f.hits.filter(function (h) { return h[0] !== "題名"; })[0];
      if (rich && other) {
        var hit = el("span", "sr-hit", other[0] + ": "); highlight(hit, other[1], terms); a.appendChild(hit);
      } else if (rich && f.r.s) {
        a.appendChild(el("span", "sr-hit", f.r.s));
      }
      li.appendChild(a); ul.appendChild(li);
    });
    return ul;
  }
  function makeSearch(container, opts) {
    var wrap = el("div", "search");
    var input = el("input");
    input.type = "search"; input.id = "_q"; input.autocomplete = "off";
    input.placeholder = opts.placeholder || "題名、タグ、見出し、要約で探す";
    input.setAttribute("aria-label", "ページを探す");
    wrap.appendChild(input);
    var hint = el("p", "search-hint");
    hint.appendChild(el("kbd", null, "/")); hint.appendChild(document.createTextNode(" で移動 · "));
    hint.appendChild(el("kbd", null, "Enter")); hint.appendChild(document.createTextNode(" で最初の結果を開く"));
    wrap.appendChild(hint);
    container.appendChild(wrap);
    if (!S) { input.disabled = true; hint.textContent = "検索の索引を読めない"; return input; }
    input.addEventListener("input", function () { opts.onQuery(input.value, search(input.value)); });
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        var first = (opts.resultsBox() || document).querySelector(".sr-results a");
        if (first) { location.href = first.href; }
      } else if (e.key === "Escape") { input.value = ""; opts.onQuery("", []); }
    });
    return input;
  }
  document.addEventListener("keydown", function (e) {
    var q = document.getElementById("_q");
    if (e.key === "/" && q && document.activeElement !== q && !/^(INPUT|SELECT|TEXTAREA)$/.test(document.activeElement.tagName)) {
      e.preventDefault(); q.focus(); q.select();
    }
  });

  // --- 狭い幅では、木と一覧を「メニュー」に畳む ---
  function drawer(content) {
    var d = el("details", "drawer");
    var s = el("summary", null, "メニュー");
    d.appendChild(s); d.appendChild(content);
    var mq = window.matchMedia("(max-width: 48rem)");
    function sync() { d.open = !mq.matches; }
    sync();
    if (mq.addEventListener) { mq.addEventListener("change", sync); }
    return d;
  }

  // 現在のページを含むグループの道
  function pathTo(groups, id) {
    for (var k = 0; k < groups.length; k++) {
      var g = groups[k];
      for (var j = 0; j < g.items.length; j++) { if (g.items[j].i === id) { return [g]; } }
      var sub = pathTo(g.children, id);
      if (sub) { return [g].concat(sub); }
    }
    return null;
  }
  var trail = current ? (pathTo(NAV.groups, current) || []) : [];
  var openIds = {};
  trail.forEach(function (g) { openIds[g.id] = true; });

  function itemLink(it) {
    var li = el("li");
    if (it.state === "resolved") {
      var a = el("a", it.i === current ? "is-current" : null, it.t);
      a.href = href(it.p);
      if (it.i === current) { a.setAttribute("aria-current", "page"); }
      li.appendChild(a);
    } else if (it.state === "group") {
      var g = el("a", null, it.t + " →"); g.href = href("index.html") + "#" + it.g; li.appendChild(g);
    } else {
      li.appendChild(el("span", "unresolved", it.t));
    }
    return li;
  }

  // --- A. 分類の木 ---
  function treeA() {
    var box = el("div", "tree");
    function group(g, depth) {
      var d = el("details");
      d.open = !!openIds[g.id] || (isIndex && depth === 0 && NAV.groups.length <= 2);
      var s = el("summary", null, g.title || "索引");
      s.appendChild(el("span", "count", String(g.count)));
      s.setAttribute("data-gid", g.id);
      if (variant === "d") {
        // D: グループの名前の横の「一覧」で、索引のページの一覧をこのグループに絞る
        var f = el("a", "tree-filter", "一覧");
        f.href = href("index.html") + "#group=" + g.id;
        f.setAttribute("aria-label", g.title + " のページを一覧で見る");
        s.appendChild(f);
      }
      d.appendChild(s);
      if (g.items.length) {
        var ul = el("ul");
        g.items.forEach(function (it) { ul.appendChild(itemLink(it)); });
        d.appendChild(ul);
      }
      g.children.forEach(function (c) { d.appendChild(group(c, depth + 1)); });
      return d;
    }
    NAV.groups.forEach(function (g) { box.appendChild(group(g, 0)); });
    return box;
  }

  // --- B. グループの名前だけ ---
  function groupsB() {
    var ul = el("ul", "groups");
    var currentTop = trail.length ? trail[0].id : null;
    NAV.groups.forEach(function (g) {
      var li = el("li"), a = el("a");
      a.href = href("index.html") + "#group=" + g.id;
      if (g.id === currentTop) { a.className = "is-current"; }
      a.appendChild(el("span", null, g.title)); a.appendChild(el("span", "count", String(g.count)));
      li.appendChild(a); ul.appendChild(li);
      g.children.forEach(function (c) {
        var sl = el("li", "sub"), sa = el("a");
        sa.href = href("index.html") + "#group=" + c.id;
        sa.appendChild(el("span", null, c.title)); sa.appendChild(el("span", "count", String(c.count)));
        sl.appendChild(sa); ul.appendChild(sl);
      });
    });
    return ul;
  }

  // --- C. このページの場所と、同じグループのページ ---
  function placeC() {
    var box = el("div");
    if (!trail.length) { return box; }
    box.appendChild(el("p", "place", "場所: " + trail.map(function (g) { return g.title; }).filter(Boolean).join(" › ")));
    var ul = el("ul", "siblings");
    trail[trail.length - 1].items.forEach(function (it) { ul.appendChild(itemLink(it)); });
    box.appendChild(ul);
    return box;
  }

  // サイドバーの検索の結果（A と C の記事のページ、B の記事のページ）
  var sideResults = el("div");
  function sideQuery(q, found) {
    sideResults.textContent = "";
    if (!q.trim()) { navMain.hidden = false; return; }
    navMain.hidden = true;
    if (!found.length) { sideResults.appendChild(el("p", "sr-empty", "当たるページはない")); return; }
    sideResults.appendChild(el("p", "sr-empty", found.length + " 件"));
    sideResults.appendChild(resultList(found, q, 30, false));
  }
  var navMain;
  if (variant === "a" || variant === "d") { navMain = treeA(); }
  else if (variant === "b") { navMain = groupsB(); }
  else { navMain = placeC(); }

  if (variant === "c" && isIndex) {
    // C の索引のページでは、検索欄は本文の上の大きな 1 つだけにする
    navbody.appendChild(drawer(groupsB()));
  } else if ((variant === "b" || variant === "d") && isIndex) {
    // 索引のページでは、検索欄は一覧の上の 1 つだけにする
    navbody.appendChild(drawer(navMain));
  } else {
    makeSearch(navbody, { onQuery: sideQuery, resultsBox: function () { return sideResults; } });
    navbody.appendChild(sideResults);
    navbody.appendChild(drawer(navMain));
  }
  var cur = navbody.querySelector(".is-current");
  if (cur && cur.scrollIntoView) { cur.scrollIntoView({ block: "center" }); window.scrollTo(0, 0); }

  // --- B の索引: 絞り込みと並べ替え ---
  if ((variant === "b" || variant === "d") && isIndex) {
    var allGroups = [];
    (function flat(gs) { gs.forEach(function (g) { allGroups.push(g); flat(g.children); }); })(NAV.groups);
    var bar = document.getElementById("_filters"), list = document.getElementById("_list");
    var count = document.getElementById("_count");
    var items = Array.prototype.slice.call(list.children);
    var state = { q: "", type: "", tag: "", group: "", sort: "order" };
    makeSearch(bar, { placeholder: "この一覧を絞る（題名、タグ、見出し、要約）",
                      onQuery: function (q) { state.q = q; apply(); }, resultsBox: function () { return list; } });
    var chips = el("div", "chips");
    var types = {};
    items.forEach(function (li) { types[li.getAttribute("data-type")] = true; });
    [""].concat(Object.keys(types).sort()).forEach(function (t) {
      var b = el("button", null, t ? (TYPE[t] || t) : "すべて");
      b.type = "button"; b.setAttribute("aria-pressed", t === "" ? "true" : "false");
      b.addEventListener("click", function () {
        state.type = t;
        Array.prototype.forEach.call(chips.children, function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
        apply();
      });
      chips.appendChild(b);
    });
    bar.appendChild(chips);
    var tagSel = el("select"), tags = {};
    items.forEach(function (li) { (li.getAttribute("data-tags") || "").split("\u001f").forEach(function (t) { if (t) { tags[t] = (tags[t] || 0) + 1; } }); });
    tagSel.appendChild(new Option("タグ: すべて", ""));
    Object.keys(tags).sort().forEach(function (t) { tagSel.appendChild(new Option(t + "（" + tags[t] + "）", t)); });
    tagSel.setAttribute("aria-label", "タグで絞る");
    tagSel.addEventListener("change", function () { state.tag = tagSel.value; apply(); });
    bar.appendChild(tagSel);
    var sortSel = el("select");
    [["order", "索引の順"], ["updated", "更新の新しい順"], ["title", "題名の順"]].forEach(function (o) { sortSel.appendChild(new Option(o[1], o[0])); });
    sortSel.setAttribute("aria-label", "並べ方");
    sortSel.addEventListener("change", function () { state.sort = sortSel.value; apply(); });
    bar.appendChild(sortSel);
    var groupNote = el("button", null, "");
    groupNote.type = "button"; groupNote.hidden = true;
    groupNote.addEventListener("click", function () { state.group = ""; location.hash = ""; apply(); });
    bar.appendChild(groupNote);
    var byPath = {};
    rows.forEach(function (r) { byPath[r.p] = r; });
    function apply() {
      var found = state.q.trim() ? search(state.q) : null, ok = {};
      if (found) { found.forEach(function (f) { ok[f.r.p] = true; }); }
      var shown = 0;
      items.forEach(function (li) {
        var p = li.querySelector(".ix-title").getAttribute("href");
        var vis = (!found || ok[decodeURIComponent(p)]) && (!state.type || li.getAttribute("data-type") === state.type)
          && (!state.tag || (li.getAttribute("data-tags") || "").split("\u001f").indexOf(state.tag) >= 0)
          && (!state.group || (li.getAttribute("data-groups") || "").split(" ").indexOf(state.group) >= 0);
        li.hidden = !vis;
        if (vis) { shown++; }
      });
      var key = state.sort;
      items.slice().sort(function (a, b) {
        if (key === "updated") { return (b.getAttribute("data-updated") || "").localeCompare(a.getAttribute("data-updated") || "") || 0; }
        if (key === "title") { return a.getAttribute("data-title").localeCompare(b.getAttribute("data-title"), "ja"); }
        return a.getAttribute("data-order") - b.getAttribute("data-order");
      }).forEach(function (li) { list.appendChild(li); });
      count.textContent = items.length + " 件中 " + shown + " 件";
      var g = allGroups.filter(function (x) { return x.id === state.group; })[0];
      groupNote.hidden = !g;
      groupNote.textContent = g ? "グループ: " + g.title + " ×" : "";
      // D: 絞っているグループを木の中で強調し、開く
      Array.prototype.forEach.call(navbody.querySelectorAll(".tree summary"), function (s) {
        var on = s.getAttribute("data-gid") === state.group;
        s.classList.toggle("is-current", on);
        if (on) { for (var p = s.parentNode; p && p !== navbody; p = p.parentNode) { if (p.tagName === "DETAILS") { p.open = true; } } }
      });
    }
    function fromHash() {
      var m = /group=(_g\d+)/.exec(location.hash);
      state.group = m ? m[1] : "";
      apply();
    }
    window.addEventListener("hashchange", fromHash);
    fromHash();
  }

  // --- C の索引: 大きな検索欄 ---
  if (variant === "c" && isIndex) {
    var resultsBox = document.getElementById("_results"), browse = document.getElementById("_browse");
    makeSearch(document.getElementById("_herosearch"), {
      placeholder: "題名、タグ、見出し、要約で探す",
      resultsBox: function () { return resultsBox; },
      onQuery: function (q, found) {
        resultsBox.textContent = "";
        if (!q.trim()) { resultsBox.hidden = true; browse.hidden = false; return; }
        resultsBox.hidden = false; browse.hidden = true;
        resultsBox.appendChild(el("p", "sr-empty", found.length ? found.length + " 件" : "当たるページはない"));
        resultsBox.appendChild(resultList(found, q, 50, true));
      }
    });
    var q0 = document.getElementById("_q");
    if (q0) { q0.focus(); }
  }
})();
