"""ADR-0010 のサーバーのアダプタの試作。gen.py の出力を、そのまま 127.0.0.1 で配る。配布対象ではない。

- 127.0.0.1 だけで待ち受け、ポートは OS に選ばせる
- 起動ごとのトークンを URL のパスの先頭に置く（/<token>/w/<wiki-id>/...）
- Host ヘッダーが 127.0.0.1:<ポート> でなければ 421 を返す
- GET と HEAD だけを受け付ける（閲覧専用）

使い方: python -X utf8 serve.py <出力先> [--wiki-id fixture]
起動したら、1 行目に {"url": ...} を出す。
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import secrets
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
       "base-uri 'none'; form-action 'none'")


def make_handler(root: Path, token: str, wiki_id: str):
    prefix = f"/{token}/w/{wiki_id}/"

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            sys.stderr.write("serve: " + (fmt % args) + "\n")

        def _deny(self, code: int):
            self.send_response(code)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_GET(self, head_only: bool = False):
            port = self.server.server_address[1]
            if self.headers.get("Host") != f"127.0.0.1:{port}":
                return self._deny(421)
            path = urllib.parse.urlsplit(self.path).path
            if not path.startswith(prefix):
                return self._deny(404)
            rel = urllib.parse.unquote(path[len(prefix):], encoding="utf-8", errors="strict") or "index.html"
            target = (root / rel).resolve()
            if not target.is_relative_to(root) or not target.is_file():
                return self._deny(404)
            body = target.read_bytes()
            ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            if ctype.startswith("text/") or ctype in ("application/javascript", "text/javascript"):
                ctype += "; charset=utf-8"
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Content-Security-Policy", CSP)
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            if not head_only:
                self.wfile.write(body)

        def do_HEAD(self):
            self.do_GET(head_only=True)

        def _readonly(self):
            self._deny(405)

        do_POST = do_PUT = do_DELETE = do_PATCH = _readonly

    return Handler


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root")
    parser.add_argument("--wiki-id", default="fixture")
    args = parser.parse_args(argv)
    mimetypes.add_type("text/javascript", ".js")
    root = Path(args.root).resolve()
    token = secrets.token_urlsafe(24)
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(root, token, args.wiki_id))
    port = server.server_address[1]
    print(json.dumps({"url": f"http://127.0.0.1:{port}/{token}/w/{args.wiki_id}/", "port": port}), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
