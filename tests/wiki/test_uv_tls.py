"""TLS を検査する社内ネットワークで、uv が証明書を検証できないときの振る舞いの試験（info-hive-wiki#30）。

- 単体: wiki_mcp_common._uv_sync と prepare_script の subprocess を差し替え、OS の証明書ストアを使った
  1 回だけのやり直し、利用者の設定の尊重、入れ直しに進まないことを確かめる。
- 結合: 自己署名の証明書で HTTPS のパッケージ索引を手元に立て、uv のキャッシュを空にして入口
  （wiki_mcp_launch.py）を動かす。uv は本当に `invalid peer certificate` で失敗し、OS の証明書ストアにも
  その証明書はないので、やり直しも失敗する。入口が入れ直しに進まず、理由と対処を標準エラーと
  logs/launch.log に書いて、すぐに止まることを確かめる。証明書を作るのに cryptography か openssl が要る。

    uv run --python 3.12 --with cryptography python -X utf8 -m unittest tests/wiki/test_uv_tls.py -v
"""
from __future__ import annotations

import datetime
import http.server
import io
import ipaddress
import os
import shutil
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "info-hive-wiki/skills/info-hive/scripts"
LAUNCH = SCRIPTS / "wiki_mcp_launch.py"
RELAY = SCRIPTS / "wiki_mcp_relay.py"
sys.path.insert(0, str(SCRIPTS))
import wiki_mcp_common as common  # noqa: E402

# uv 0.12〜0.13 が証明書の検証に失敗したときの出力（info-hive-wiki#30 の報告から）。
TLS_OUTPUT = (b"error: Failed to fetch: https://pypi.org/simple/mcp/\n"
              b"  cause: invalid peer certificate: UnknownIssuer\n\n"
              b"hint: Consider enabling use of system TLS certificates with the `--system-certs` command-line flag\n")
TLS_ENVS = ("UV_SYSTEM_CERTS", "UV_NATIVE_TLS")


NEW_HELP = b"      --system-certs\n          Whether to load TLS certificates [env: UV_SYSTEM_CERTS=]\n"
OLD_HELP = b"      --native-tls\n          Whether to load TLS certificates [env: UV_NATIVE_TLS=]\n"


class FakeUv:
    """subprocess.run の代わり。`uv sync` のコマンドと環境変数を記録し、決めた順に結果を返す。
    `uv sync --help` には help の文面を返す（uv の版を見分ける）。"""

    def __init__(self, results, help_text: bytes = NEW_HELP):
        self.results = list(results)
        self.help_text = help_text
        self.calls: list[tuple[list[str], dict]] = []
        self.help_calls = 0

    def __call__(self, command, **kwargs):
        if "--help" in command:
            self.help_calls += 1
            return subprocess.CompletedProcess(command, 0, stdout=self.help_text, stderr=b"")
        self.calls.append((list(command), dict(kwargs.get("env") or {})))
        code, out = self.results.pop(0)
        return subprocess.CompletedProcess(command, code, stdout=out, stderr=b"")


class UvSyncTest(unittest.TestCase):
    def setUp(self):
        self.saved = {name: os.environ.pop(name) for name in TLS_ENVS if name in os.environ}
        self.addCleanup(self.restore_env)
        self.logs: list[str] = []
        self.data = Path(tempfile.mkdtemp(prefix="wiki-tls-data-"))
        self.addCleanup(shutil.rmtree, self.data, ignore_errors=True)
        data_patch = mock.patch.dict(os.environ, {common.DATA_DIR_ENV: str(self.data)})
        data_patch.start()
        self.addCleanup(data_patch.stop)
        patcher = mock.patch.object(common, "uv_executable", return_value="uv")
        patcher.start()
        self.addCleanup(patcher.stop)

    def clear_tls_env(self):
        for name in TLS_ENVS:
            os.environ.pop(name, None)

    def restore_env(self):
        self.clear_tls_env()
        os.environ.update(self.saved)

    def sync(self, fake, output=None):
        with mock.patch.object(common.subprocess, "run", fake):
            return common._uv_sync(RELAY, reinstall=False, output=output if output is not None else io.StringIO(),
                                   timeout=10, log=self.logs.append)

    def test_retries_with_system_certs_and_keeps_it(self):
        fake = FakeUv([(2, TLS_OUTPUT), (0, b"")])
        self.assertEqual(self.sync(fake), 0)
        self.assertEqual(len(fake.calls), 2)
        self.assertNotIn("UV_SYSTEM_CERTS", fake.calls[0][1])
        self.assertEqual(fake.calls[1][1].get("UV_SYSTEM_CERTS"), "true")
        # 以後の uv と、子のプロセス（中継）にも引き継ぐ。
        self.assertEqual(os.environ.get("UV_SYSTEM_CERTS"), "true")
        self.assertTrue(any("UV_SYSTEM_CERTS=true" in line for line in self.logs))

    def test_old_uv_retries_with_native_tls(self):
        # 古い uv は UV_SYSTEM_CERTS を黙って無視するので、UV_NATIVE_TLS でやり直す。
        fake = FakeUv([(2, TLS_OUTPUT), (0, b"")], help_text=OLD_HELP)
        self.assertEqual(self.sync(fake), 0)
        self.assertEqual(fake.calls[1][1].get("UV_NATIVE_TLS"), "true")
        self.assertNotIn("UV_SYSTEM_CERTS", fake.calls[1][1])
        self.assertEqual(os.environ.get("UV_NATIVE_TLS"), "true")
        self.assertNotIn("UV_SYSTEM_CERTS", os.environ)

    def test_raises_when_retry_also_fails_on_tls(self):
        fake = FakeUv([(2, TLS_OUTPUT), (2, TLS_OUTPUT)])
        with self.assertRaises(common.UvTlsError) as caught:
            self.sync(fake)
        self.assertIn("やり直しても失敗した", str(caught.exception))
        self.assertIn("system-certs = true", str(caught.exception))
        self.assertNotIn("UV_SYSTEM_CERTS", os.environ)
        # 中継がサーバーの環境を用意するときも、利用者が読む launch.log に残る。
        self.assertIn("UvTlsError", (self.data / "logs" / "launch.log").read_text(encoding="utf-8"))

    def test_respects_user_setting(self):
        for name, value in (("UV_SYSTEM_CERTS", "false"), ("UV_NATIVE_TLS", "true")):
            with self.subTest(name=name):
                self.clear_tls_env()
                os.environ[name] = value
                fake = FakeUv([(2, TLS_OUTPUT)])
                with self.assertRaises(common.UvTlsError) as caught:
                    self.sync(fake)
                self.assertEqual(len(fake.calls), 1)
                self.assertEqual(fake.help_calls, 0)
                self.assertIn(f"{name}={value}", str(caught.exception))
                self.assertEqual(os.environ[name], value)

    def test_other_failures_are_not_retried(self):
        fake = FakeUv([(2, b"error: Failed to read metadata from installed package\n")])
        self.assertEqual(self.sync(fake), 2)
        self.assertEqual(len(fake.calls), 1)
        self.assertNotIn("UV_SYSTEM_CERTS", os.environ)

    def test_option_names_in_paths_are_not_tls_errors(self):
        # パスにオプション名や UnknownIssuer が含まれても、証明書のエラーとはみなさない（入れ直しに任せる）。
        output = (b"error: Failed to read metadata from installed package at "
                  b"C:/cache/--system-certs/--native-tls/UnknownIssuer/pkg.dist-info/METADATA\n")
        fake = FakeUv([(2, output)])
        self.assertEqual(self.sync(fake), 2)
        self.assertEqual(len(fake.calls), 1)

    def test_timeout_keeps_output(self):
        def slow(command, **kwargs):
            raise subprocess.TimeoutExpired(command, 1, output=TLS_OUTPUT)
        text = io.StringIO()
        with mock.patch.object(common.subprocess, "run", slow), self.assertRaises(subprocess.TimeoutExpired):
            common._uv_sync(RELAY, reinstall=False, output=text, timeout=1, log=self.logs.append)
        self.assertIn("invalid peer certificate", text.getvalue())

    def test_retry_failing_for_other_reason_returns_code(self):
        # 証明書の問題は直った（以後も OS の証明書ストアを使う）が、別の理由で失敗した。入れ直しに任せる。
        fake = FakeUv([(2, TLS_OUTPUT), (2, b"error: Failed to read metadata\n")])
        self.assertEqual(self.sync(fake), 2)
        self.assertEqual(os.environ.get("UV_SYSTEM_CERTS"), "true")

    def test_output_is_forwarded_to_text_and_binary(self):
        text = io.StringIO()
        self.sync(FakeUv([(0, "進捗\n".encode("utf-8"))]), output=text)
        self.assertEqual(text.getvalue(), "進捗\n")
        binary = io.BytesIO()
        self.sync(FakeUv([(0, "進捗\n".encode("utf-8"))]), output=binary)
        self.assertEqual(binary.getvalue(), "進捗\n".encode("utf-8"))

    def test_prepare_script_does_not_reinstall_on_tls_error(self):
        fake = FakeUv([(2, TLS_OUTPUT), (2, TLS_OUTPUT)])
        with mock.patch.object(common.subprocess, "run", fake), \
                mock.patch.object(common, "env_lock_path", side_effect=AssertionError("ロックを取った")):
            with self.assertRaises(common.UvTlsError):
                common.prepare_script(RELAY, output=io.StringIO(), timeout=10, log=self.logs.append)
        self.assertFalse(any("--reinstall" in command for command, _ in fake.calls))
        self.assertFalse(any("入れ直す" in line for line in self.logs))


def make_self_signed(directory: Path) -> tuple[Path, Path] | None:
    """127.0.0.1 の自己署名の証明書と鍵を作る。作れなければ None。"""
    cert, key = directory / "cert.pem", directory / "key.pem"
    try:
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.x509.oid import NameOID
    except ImportError:
        openssl = shutil.which("openssl")
        if not openssl:
            return None
        subprocess.run([openssl, "req", "-x509", "-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:P-256", "-nodes",
                        "-keyout", str(key), "-out", str(cert), "-days", "1", "-subj", "/CN=127.0.0.1",
                        "-addext", "subjectAltName=IP:127.0.0.1"], check=True, capture_output=True)
        return cert, key
    private = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "127.0.0.1")])
    now = datetime.datetime.now(datetime.timezone.utc)
    certificate = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(private.public_key())
                   .serial_number(x509.random_serial_number()).not_valid_before(now - datetime.timedelta(minutes=5))
                   .not_valid_after(now + datetime.timedelta(days=1))
                   .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]),
                                  critical=False)
                   .sign(private, hashes.SHA256()))
    cert.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    key.write_bytes(private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                          serialization.NoEncryption()))
    return cert, key


class Quiet(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 - 証明書の検証で止まるので、ここには来ない
        self.send_error(404)

    def log_message(self, *args):
        pass


class LauncherTlsTest(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp(prefix="wiki-tls-"))
        self.addCleanup(shutil.rmtree, self.temp, ignore_errors=True)
        made = make_self_signed(self.temp)
        if made is None:
            self.skipTest("証明書を作れない（cryptography も openssl もない）")
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(*map(str, made))
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Quiet)
        self.server.socket = context.wrap_socket(self.server.socket, server_side=True)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def test_launcher_stops_with_advice_without_reinstalling(self):
        data = self.temp / "data"
        env = {key: value for key, value in os.environ.items()
               if key not in (*TLS_ENVS, "SSL_CERT_FILE", "SSL_CERT_DIR", "UV_OFFLINE") and not key.startswith("UV_INDEX")}
        env.update({"UV_DEFAULT_INDEX": f"https://127.0.0.1:{self.server.server_address[1]}/simple",
                    "UV_CACHE_DIR": str(self.temp / "uv-cache"), "INFO_HIVE_DATA_DIR": str(data),
                    "PYTHONUTF8": "1"})
        started = time.monotonic()
        out = subprocess.run([sys.executable, "-X", "utf8", str(LAUNCH), "--ensure"], stdin=subprocess.DEVNULL,
                             capture_output=True, timeout=300, env=env)
        elapsed = time.monotonic() - started
        stderr = out.stderr.decode("utf-8", "replace")
        self.assertEqual(out.returncode, 1, stderr)
        self.assertIn("invalid peer certificate", stderr.lower())
        self.assertIn("OS の証明書ストアを使ってやり直す", stderr)
        self.assertIn("UvTlsError", stderr)
        self.assertIn("system-certs = true", stderr)
        self.assertNotIn("入れ直す", stderr)
        log = (data / "logs" / "launch.log").read_text(encoding="utf-8")
        self.assertIn("UvTlsError", log)
        self.assertIn("UV_SYSTEM_CERTS=true", log)
        self.assertLess(elapsed, 120, f"止まるまでに {elapsed:.0f} 秒かかった")


if __name__ == "__main__":
    unittest.main()
