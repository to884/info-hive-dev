"""普段のブラウザのログイン状態を、ローカルの試験ページで確かめる。

最初に表示される login の URL をブラウザで開き、そのタブを Playwright 拡張で許可する。
本物のサービスのログイン情報は読まず、Cookie の値も出力しない。
"""
from __future__ import annotations

import argparse
import json
import secrets
import struct
import sys
import tempfile
import threading
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "info-hive-wiki/skills/info-hive/scripts"))
import wiki_fetch

BODY = "普段のブラウザのログイン状態で読める本文を、HTML の保存なしで取り込む。" * 30
COOKIE = "info_hive_browser_test_" + secrets.token_hex(6)
VALUE = secrets.token_hex(16)


def png():
    def chunk(name, data):
        return struct.pack('>I', len(data)) + name + data + struct.pack('>I', zlib.crc32(name + data) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 120, 80, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress((b'\0' + b'\x32\x70\xb0' * 120) * 80)) + chunk(b'IEND', b''))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_GET(self):
        if self.path == '/login':
            self.send_response(302)
            self.send_header('Set-Cookie', f'{COOKIE}={VALUE}; HttpOnly; SameSite=Lax; Max-Age=600; Path=/')
            self.send_header('Location', '/authenticated')
            self.send_header('Content-Length', '0')
            self.end_headers()
            return
        authorized = f'{COOKIE}={VALUE}' in self.headers.get('Cookie', '')
        if authorized and self.path == '/image.png':
            content, kind = png(), 'image/png'
        elif authorized:
            content = ('<!doctype html><html lang="ja"><meta charset="utf-8"><title>info-hive ログインの試験</title>'
                       '<article><h1>ログイン済みの試験ページ</h1><p>' + BODY
                       + '</p><img width="120" height="80" alt="試験の図" src="/image.png"></article>'
                       '<script>console.error("info-hive-console-must-not-be-written")</script></html>').encode('utf-8')
            kind = 'text/html; charset=utf-8'
        else:
            content, kind = b'authentication required', 'text/plain'
        self.send_response(200 if authorized else 401)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=0)
    parser.add_argument('--prepare-seconds', type=float, default=0)
    options = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', options.port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    origin = f'http://127.0.0.1:{server.server_port}'
    print('ブラウザで開く URL: ' + origin + '/login', flush=True)
    print('そのタブがログイン済みの本文を表示したら、Playwright 拡張の接続でそのタブを許可する', flush=True)
    if options.prepare_seconds:
        import time
        time.sleep(options.prepare_seconds)
    try:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            wiki, raw = root / 'wiki', root / 'raw'
            wiki.mkdir(); raw.mkdir()
            (wiki / 'SCHEMA.md').write_text('# 規約\n', encoding='utf-8')
            args = argparse.Namespace(url=origin + '/authenticated', wiki=wiki, raw_root=raw, slug='session-test',
                                      no_images=False, timeout=60, max_bytes=200000, max_images=10, force=False,
                                      browser_fallback=True, browser='system', browser_session='existing')
            code, result = wiki_fetch.build(args)
            text = (raw / 'session-test.md').read_text(encoding='utf-8')
            assert code == 0 and BODY in text
            assert result['browser_session'] == 'existing'
            assert result['images'][0]['path'] and (raw / result['images'][0]['path']).is_file()
            assert 'info-hive-console-must-not-be-written' not in text
            print(json.dumps({'status': 'passed', 'authenticated_body': True, 'authenticated_image': True,
                              'browser_session': result['browser_session'], 'cookie_exported': False}, ensure_ascii=False), flush=True)
    finally:
        server.shutdown(); server.server_close()


if __name__ == '__main__':
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'): stream.reconfigure(encoding='utf-8')
    main()
