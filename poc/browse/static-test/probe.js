/* ADR-0010 の PoC。3 方式で同じ検査をするために、ページに差し込んで状態を取り出す。
   Playwright では addInitScript で、Tauri では initialization_script で読み込む。 */
(function () {
  var violations = [];
  document.addEventListener("securitypolicyviolation", function (e) {
    violations.push(e.violatedDirective + " " + e.blockedURI);
  });
  window.__probe = function () {
    var base = document.documentElement.getAttribute("data-root") || "";
    var rootUrl = new URL(base || "./", location.href).href;
    function rel(url) {
      if (!url) return null;
      return url.indexOf(rootUrl) === 0 ? decodeURIComponent(url.slice(rootUrl.length)) : "EXTERNAL:" + url;
    }
    function texts(sel) {
      return Array.prototype.map.call(document.querySelectorAll(sel), function (n) { return n.textContent; });
    }
    var article = document.querySelector("article");
    var hash = decodeURIComponent(location.hash.slice(1));
    var b = window.__browse || {};
    var style = article ? getComputedStyle(document.querySelector("main")) : null;
    return {
      page: rel(location.href.split("#")[0]),
      hash: hash,
      hashTargetFound: hash ? !!document.getElementById(hash) : null,
      pageId: article ? article.getAttribute("data-page-id") : null,
      navLoaded: !!b.navLoaded,
      navCount: document.querySelectorAll("#nav-list li").length,
      searchLoaded: !!b.searchLoaded,
      searchResults: texts("#search-results a"),
      capabilities: window.WIKI_CAPABILITIES ? window.WIKI_CAPABILITIES.search : null,
      appErrors: b.errors || [],
      links: Array.prototype.map.call(document.querySelectorAll("article .wl"), function (n) {
        return { text: n.textContent, cls: n.className, href: n.tagName === "A" ? rel(n.href) : null };
      }),
      backlinks: texts("#backlinks a"),
      diagnostics: texts("#diagnostics li"),
      scriptEscaped: article ? article.innerHTML.indexOf("&lt;script&gt;") >= 0 : null,
      cspViolations: violations.slice(),
      css: style ? {
        lineBreak: style.lineBreak || style.getPropertyValue("line-break"),
        wordBreak: style.wordBreak,
        overflowWrap: style.overflowWrap || style.getPropertyValue("overflow-wrap"),
        textAutospace: style.getPropertyValue("text-autospace") || null,
        fontFamily: style.fontFamily
      } : null
    };
  };
})();
