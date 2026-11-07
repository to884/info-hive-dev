"""ADR-0010 の PoC。static-test/kinsoku.html を WebKitGTK 4.1 で開き、幅を変えながら禁則の違反を数える。
WSL の Ubuntu で動かす（配布対象ではない）。
使い方: xvfb-run -a python3 webkitgtk_kinsoku.py <結果の JSON>
"""
import json
import sys
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("WebKit2", "4.1")
from gi.repository import GLib, Gtk, WebKit2  # noqa: E402

PAGE = Path(__file__).resolve().parent / "static-test" / "kinsoku.html"
OUT = Path(sys.argv[1])
result = {"version": "%d.%d.%d" % (WebKit2.get_major_version(), WebKit2.get_minor_version(),
                                   WebKit2.get_micro_version())}
window = Gtk.OffscreenWindow()
window.set_default_size(1000, 900)
view = WebKit2.WebView()
window.add(view)
window.show_all()


def done(webview, task):
    try:
        result.update(json.loads(webview.evaluate_javascript_finish(task).to_json(0)))
    except GLib.Error as exc:
        result["error"] = str(exc)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    Gtk.main_quit()


def on_load(webview, event):
    if event == WebKit2.LoadEvent.FINISHED:
        view.evaluate_javascript("window.kinsoku()", -1, None, None, None, done)


view.connect("load-changed", on_load)
GLib.timeout_add_seconds(60, Gtk.main_quit)
view.load_uri(PAGE.as_uri())
Gtk.main()
