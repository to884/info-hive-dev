"""ADR-0010 の PoC。Linux の WebKitGTK（libwebkit2gtk-4.1、Tauri が Linux で使う版）で、
gen.py の出力を file:// で開き、日本語の CSS と classic な <script src> の読み込みを確かめる。

WSL の Ubuntu で、システムの python3 と gi を使って動かす（配布対象ではない）。
使い方: xvfb-run -s "-screen 0 1280x1024x24" python3 webkitgtk_probe.py <static のディレクトリ> <結果の JSON> <PNG>
"""
import json
import sys
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("WebKit2", "4.1")
from gi.repository import GLib, Gtk, WebKit2  # noqa: E402

STATIC = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2])
PNG = Path(sys.argv[3])
PROBE = (Path(__file__).resolve().parent / "static-test" / "probe.js").read_text(encoding="utf-8")
PAGE = STATIC / "concepts" / "ナレッジグラフ.html"

# 行頭禁則などを目で確かめるため、要素ごとの実際の位置を取り出す。
MEASURE = r"""
(function () {
  var p = Array.prototype.find.call(document.querySelectorAll("article p"), function (n) {
    return n.textContent.indexOf("禁則の確認用") >= 0; });
  var text = p.firstChild; var range = document.createRange(); var lines = []; var lastTop = null; var cur = "";
  for (var i = 0; i < text.length; i++) {
    range.setStart(text, i); range.setEnd(text, i + 1);
    // 折り返しの境目の文字は、前の行の末尾にも幅 0 の矩形を返すので、幅のある最後の矩形を使う。
    var rs = Array.prototype.filter.call(range.getClientRects(), function (x) { return x.width > 0; });
    if (!rs.length) { cur += text.data[i]; continue; }
    var top = rs[rs.length - 1].top;
    if (lastTop !== null && Math.abs(top - lastTop) > 4) { lines.push(cur); cur = ""; }
    lastTop = top; cur += text.data[i];
  }
  lines.push(cur);
  var main = document.querySelector("main");
  return { lines: lines, overflow: main.scrollWidth > main.clientWidth,
           fonts: document.fonts ? document.fonts.status : null };
})()
"""

result = {"page": PAGE.as_uri(), "webkit_version": "%d.%d.%d" % (
    WebKit2.get_major_version(), WebKit2.get_minor_version(), WebKit2.get_micro_version())}

window = Gtk.OffscreenWindow()
window.set_default_size(1000, 900)
view = WebKit2.WebView()
view.get_settings().set_enable_developer_extras(True)
manager = view.get_user_content_manager()
manager.add_script(WebKit2.UserScript.new(PROBE, WebKit2.UserContentInjectedFrames.TOP_FRAME,
                                          WebKit2.UserScriptInjectionTime.START, None, None))
window.add(view)
window.show_all()


def finish():
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    Gtk.main_quit()


def evaluate(script, key, then):
    def done(webview, task):
        try:
            value = webview.evaluate_javascript_finish(task)
            result[key] = json.loads(value.to_json(0))
        except GLib.Error as exc:
            result[key] = {"error": str(exc)}
        then()
    view.evaluate_javascript(script, -1, None, None, None, done)


def snapshot():
    def done(webview, task):
        try:
            surface = webview.get_snapshot_finish(task)
            surface.write_to_png(str(PNG))
            result["png"] = PNG.name
        except GLib.Error as exc:
            result["png_error"] = str(exc)
        finish()
    view.get_snapshot(WebKit2.SnapshotRegion.FULL_DOCUMENT, WebKit2.SnapshotOptions.NONE, None, done)


def after_search():
    GLib.timeout_add(500, lambda: evaluate("window.__probe()", "after_search", snapshot) and False)


def on_load(webview, event):
    if event != WebKit2.LoadEvent.FINISHED:
        return
    evaluate("window.__probe()", "probe", lambda: evaluate(MEASURE, "measure", lambda: evaluate(
        "var s=document.getElementById('search'); s.value='知識表現'; s.dispatchEvent(new Event('input')); true",
        "typed", after_search)))


view.connect("load-changed", on_load)
GLib.timeout_add_seconds(30, lambda: (result.setdefault("timeout", True), finish()))
view.load_uri(PAGE.as_uri())
Gtk.main()
