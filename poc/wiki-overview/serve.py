"""概要の表示の試作の site/ を 127.0.0.1 で配る。配布対象ではない。

応答の種類ごとに CSP を変える（ページ、Mermaid の枠の文書、svg）。値は、図の表示の試作（poc/browse-figures）と同じにしている。
起動したら 1 行目に {"url": ...} を出す。
使い方: python -X utf8 serve.py [ポート]
"""
from __future__ import annotations

import json
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SITE = Path(__file__).resolve().parent / "site"
CSP_PAGE = ("default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
            "frame-src 'self'; base-uri 'none'; form-action 'none'")
CSP_FRAME = ("default-src 'none'; script-src {origin}; style-src 'unsafe-inline'; img-src data:; "
             "base-uri 'none'; form-action 'none'; sandbox allow-scripts")
CSP_SVG = "default-src 'none'; style-src 'unsafe-inline'; sandbox"
TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".svg": "image/svg+xml",
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _deny(self, code: int):
        self.send_response(code)
        self.send_header("Content-Length", "0")
        self.send_header("Content-Security-Policy", CSP_PAGE)
        self.end_headers()

    def do_GET(self):
        port = self.server.server_address[1]
        if self.headers.get("Host") != f"127.0.0.1:{port}":
            return self._deny(421)
        try:
            name = urllib.parse.unquote(urllib.parse.urlsplit(self.path).path.lstrip("/"), errors="strict")
        except UnicodeDecodeError:
            return self._deny(404)
        parts = name.split("/") if name else ["index.html"]
        if any(p in ("", ".", "..") or "\\" in p or "\0" in p for p in parts):
            return self._deny(404)
        target = SITE.joinpath(*parts)
        ext = target.suffix.lower()
        if ext not in TYPES or not target.is_file():
            return self._deny(404)
        if name == "_frame/mermaid-frame.html":
            csp = CSP_FRAME.format(origin=f"http://127.0.0.1:{port}/_frame/")
        elif ext == ".svg":
            csp = CSP_SVG
        else:
            csp = CSP_PAGE
        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", TYPES[ext])
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Content-Security-Policy", csp)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(json.dumps({"url": f"http://127.0.0.1:{server.server_address[1]}/"}), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
