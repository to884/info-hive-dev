"""図の描画の PoC の site/ を 127.0.0.1 で配る。配布対象ではない。

応答の種類ごとに CSP を変える（ページ、枠の文書、svg）。起動したら 1 行目に {"url": ...} を出す。
使い方: python -X utf8 serve.py
"""
from __future__ import annotations

import json
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from setup import CSP_FRAME_HEADER, CSP_PAGE, CSP_SVG, SITE

TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".svg": "image/svg+xml",
}


def policy(name: str, origin: str) -> str:
    if name == "_frame/mermaid-frame.html":
        # 2 回目の PoC: スクリプトは /_frame/ の下だけから読む（配信元のほかのファイルを読ませない）
        return CSP_FRAME_HEADER.replace("script-src 'self'", f"script-src {origin}/_frame/")
    if name.startswith("mermaid-frame") and name.endswith(".html"):
        # WebKit は、sandbox で不透明になった文書の 'self' を配信元に一致させない。配信元を書き足す
        return CSP_FRAME_HEADER.replace("script-src 'self'", f"script-src 'self' {origin}")
    if name.endswith(".svg"):
        return CSP_SVG
    return CSP_PAGE


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _deny(self, code: int):
        self.send_response(code)
        self.send_header("Content-Length", "0")
        self.send_header("Content-Security-Policy", CSP_PAGE)
        self.end_headers()

    def do_GET(self, head_only: bool = False):
        port = self.server.server_address[1]
        if self.headers.get("Host") != f"127.0.0.1:{port}":
            return self._deny(421)
        name = urllib.parse.unquote(urllib.parse.urlsplit(self.path).path.lstrip("/"), errors="strict")
        parts = name.split("/")
        if not (len(parts) == 1 or (len(parts) == 2 and parts[0] == "_frame")) \
                or any(p in ("", ".", "..") or "\\" in p for p in parts):
            return self._deny(404)
        target = SITE.joinpath(*parts)
        ext = target.suffix.lower()
        if ext not in TYPES or not target.is_file():
            return self._deny(404)
        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", TYPES[ext])
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Content-Security-Policy", policy(name, f"http://127.0.0.1:{port}"))
        self.send_header("X-Content-Type-Options", "nosniff")
        # /_frame/ の下はトークンを含まない固定の同梱物なので、キャッシュを許す（2 回目の PoC）
        self.send_header("Cache-Control", "private, max-age=3600" if name.startswith("_frame/") else "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        if not head_only:
            self.wfile.write(body)

    def do_HEAD(self):
        self.do_GET(head_only=True)


def main() -> int:
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    print(json.dumps({"url": f"http://127.0.0.1:{server.server_address[1]}/"}), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
