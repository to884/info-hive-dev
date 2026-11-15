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
# uv 0.13.8 が依存を解決できなかったときの出力（Python のない Windows 11 で、wiki 0.19.4 の段階 2 の確認から）。
RESOLVE_OUTPUT = (b"error: No solution found when resolving dependencies\n"
                  b"  cause: Because onnxruntime==1.31.1 has no wheels with a matching Python ABI tag (e.g., `cp315`)"
                  b" and you require onnxruntime==1.31.1, we can conclude that your requirements are unsatisfiable.\n\n"
                  b"hint: You require CPython 3.15 (`cp315`), but we only found wheels for `onnxruntime` (v1.31.1)"
                  b" with the following Python ABI tags: `cp311`, `cp312`, `cp313`, `cp313t`, `cp314`, `cp314t`\n")


NEW_HELP = b"      --system-certs\n          Whether to load TLS certificates [env: UV_SYSTEM_CERTS=]\n"
OLD_HELP = b"      --native-tls\n          Whether to load TLS certificates [env: UV_NATIVE_TLS=]\n"


class FakeUv:
    """subprocess.run の代わり。`uv sync` のコマンドと環境変数を記録し、決めた順に結果を返す。
    `uv sync --help` には help の文面を返す（uv の版を見分ける）。"""

    def __init__(self, results, help_text: bytes = NEW_HELP, help_code: int = 0, help_error: Exception | None = None):
        self.results = list(results)
        self.help_text = help_text
        self.help_code = help_code
        self.help_error = help_error
        self.calls: list[tuple[list[str], dict]] = []
        self.help_calls = 0

    def __call__(self, command, **kwargs):
        if "--help" in command:
            self.help_calls += 1
            if self.help_error is not None:
                raise self.help_error
            return subprocess.CompletedProcess(command, self.help_code, stdout=self.help_text, stderr=b"")
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

    def test_old_uv_ignoring_system_certs_retries_with_native_tls(self):
        # 古い uv は UV_SYSTEM_CERTS を黙って無視する。設定があっても利用者の意図は uv に届いていないので、
        # 決定とみなさず、UV_NATIVE_TLS でやり直す。真の値の書き方は uv と同じに読む（大文字と小文字は区別しない）。
        for value in ("true", "1", "YES", "On"):
            with self.subTest(value=value):
                self.clear_tls_env()
                self.logs.clear()
                os.environ["UV_SYSTEM_CERTS"] = value
                fake = FakeUv([(2, TLS_OUTPUT), (0, b"")], help_text=OLD_HELP)
                self.assertEqual(self.sync(fake), 0)
                self.assertEqual(len(fake.calls), 2)
                self.assertEqual(fake.help_calls, 1)
                self.assertNotIn("UV_NATIVE_TLS", fake.calls[0][1])
                self.assertEqual(fake.calls[1][1].get("UV_NATIVE_TLS"), "true")
                self.assertEqual(os.environ.get("UV_NATIVE_TLS"), "true")
                self.assertEqual(os.environ["UV_SYSTEM_CERTS"], value)
                self.assertTrue(any("UV_NATIVE_TLS=true" in line and "読まない" in line for line in self.logs))

    def test_old_uv_ignoring_system_certs_explains_when_retry_fails(self):
        os.environ["UV_SYSTEM_CERTS"] = "true"
        fake = FakeUv([(2, TLS_OUTPUT), (2, TLS_OUTPUT)], help_text=OLD_HELP)
        with self.assertRaises(common.UvTlsError) as caught:
            self.sync(fake)
        message = str(caught.exception)
        self.assertIn("UV_SYSTEM_CERTS=true が設定されているが", message)
        self.assertIn("uv self update", message)
        self.assertNotIn("そのまま止まる", message)
        self.assertNotIn("UV_NATIVE_TLS", os.environ)

    def test_new_uv_reading_system_certs_respects_it(self):
        # 新しい uv が UV_SYSTEM_CERTS=true を読んでも失敗したなら、同じ設定でやり直しても直らない。
        os.environ["UV_SYSTEM_CERTS"] = "true"
        fake = FakeUv([(2, TLS_OUTPUT)], help_text=NEW_HELP)
        with self.assertRaises(common.UvTlsError) as caught:
            self.sync(fake)
        self.assertEqual(len(fake.calls), 1)
        self.assertIn("UV_SYSTEM_CERTS=true が設定されているので", str(caught.exception))

    def test_false_system_certs_is_respected_without_asking_uv(self):
        # 偽の値は uv の既定と同じなので、uv が読むかに関わらず利用者の決定である。uv の版も確かめない。
        os.environ["UV_SYSTEM_CERTS"] = "false"
        fake = FakeUv([(2, TLS_OUTPUT)], help_text=OLD_HELP)
        with self.assertRaises(common.UvTlsError):
            self.sync(fake)
        self.assertEqual(len(fake.calls), 1)
        self.assertEqual(fake.help_calls, 0)
        self.assertNotIn("UV_NATIVE_TLS", os.environ)

    def test_both_settings_are_a_decision_on_any_uv(self):
        # 両方あれば、新しい uv は UV_SYSTEM_CERTS を、古い uv は UV_NATIVE_TLS を使う。どちらにしても利用者の
        # 決定なので、uv の版を確かめずに止まり、案内には両方とどちらを使うかを書く。
        for help_text in (NEW_HELP, OLD_HELP):
            with self.subTest(help_text=help_text):
                self.clear_tls_env()
                os.environ["UV_SYSTEM_CERTS"] = "true"
                os.environ["UV_NATIVE_TLS"] = "false"
                fake = FakeUv([(2, TLS_OUTPUT)], help_text=help_text)
                with self.assertRaises(common.UvTlsError) as caught:
                    self.sync(fake)
                self.assertEqual(len(fake.calls), 1)
                self.assertEqual(fake.help_calls, 0)
                message = str(caught.exception)
                self.assertIn("UV_SYSTEM_CERTS=true と UV_NATIVE_TLS=false", message)
                self.assertIn("古い uv は UV_NATIVE_TLS だけを使い", message)

    def test_padded_true_is_not_read_as_true(self):
        # uv は前後の空白を除かないので、" true " は真ではない。偽と同じく、利用者の決定として止まる。
        os.environ["UV_SYSTEM_CERTS"] = " true "
        fake = FakeUv([(2, TLS_OUTPUT)], help_text=OLD_HELP)
        with self.assertRaises(common.UvTlsError):
            self.sync(fake)
        self.assertEqual(len(fake.calls), 1)
        self.assertEqual(fake.help_calls, 0)

    def help_failures(self):
        return (("終了コードが 0 でない", {"help_code": 2}),
                ("どちらの名前も挙げない", {"help_text": b"Usage: uv sync [OPTIONS]\n"}),
                ("OSError", {"help_error": OSError("uv がない")}),
                ("待ちきれない", {"help_error": subprocess.TimeoutExpired(["uv"], 60)}))

    def test_unknown_uv_with_system_certs_retries_with_both_names(self):
        # `uv sync --help` が動かなければ uv の版は分からない。新しい uv とみなすと、古い uv で届いていない
        # UV_SYSTEM_CERTS=true を決定と取り違え、やり直しを止めてしまう。両方の名前を真にしてやり直す。
        for label, kwargs in self.help_failures():
            with self.subTest(label):
                self.clear_tls_env()
                self.logs.clear()
                os.environ["UV_SYSTEM_CERTS"] = "true"
                fake = FakeUv([(2, TLS_OUTPUT), (0, b"")], **{"help_text": OLD_HELP, **kwargs})
                self.assertEqual(self.sync(fake), 0)
                self.assertEqual(len(fake.calls), 2)
                self.assertEqual(fake.calls[1][1].get("UV_SYSTEM_CERTS"), "true")
                self.assertEqual(fake.calls[1][1].get("UV_NATIVE_TLS"), "true")
                self.assertEqual(os.environ.get("UV_NATIVE_TLS"), "true")
                self.assertTrue(any("確かめられなかった" in line for line in self.logs))

    def test_unknown_uv_without_setting_retries_with_both_names(self):
        for label, kwargs in self.help_failures():
            with self.subTest(label):
                self.clear_tls_env()
                fake = FakeUv([(2, TLS_OUTPUT), (0, b"")], **kwargs)
                self.assertEqual(self.sync(fake), 0)
                self.assertEqual(fake.calls[1][1].get("UV_SYSTEM_CERTS"), "true")
                self.assertEqual(fake.calls[1][1].get("UV_NATIVE_TLS"), "true")
                self.assertEqual(os.environ.get("UV_SYSTEM_CERTS"), "true")
                self.assertEqual(os.environ.get("UV_NATIVE_TLS"), "true")

    def test_unknown_uv_explains_when_retry_fails(self):
        os.environ["UV_SYSTEM_CERTS"] = "true"
        fake = FakeUv([(2, TLS_OUTPUT), (2, TLS_OUTPUT)], help_code=2)
        with self.assertRaises(common.UvTlsError) as caught:
            self.sync(fake)
        message = str(caught.exception)
        self.assertIn("UV_SYSTEM_CERTS=true が設定されているが、この uv が UV_SYSTEM_CERTS を読むかを確かめられなかった",
                      message)
        self.assertNotIn("そのまま止まる", message)

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

    def test_unresolvable_dependencies_stop_without_reinstall(self):
        # 新しい Windows で uv が CPython 3.15 を取り、onnxruntime に 3.15 の wheel がなかったときの出力（0.19.4）。
        # 環境は作られていないので、壊れた環境とみなして入れ直しても直らない。入れ直さずに止まり、理由を残す。
        fake = FakeUv([(1, RESOLVE_OUTPUT)])
        with mock.patch.object(common.subprocess, "run", fake), \
                mock.patch.object(common, "env_lock_path", side_effect=AssertionError("ロックを取った")):
            with self.assertRaises(common.UvResolveError) as caught:
                common.prepare_script(RELAY, output=io.StringIO(), timeout=10, log=self.logs.append)
        self.assertIsInstance(caught.exception, common.UvSetupError)
        self.assertEqual(len(fake.calls), 1)
        self.assertFalse(any("入れ直す" in line for line in self.logs))
        message = str(caught.exception)
        self.assertIn("依存を解決できなかった", message)
        self.assertIn("hint: You require CPython 3.15", message)
        log = (self.data / "logs" / "launch.log").read_text(encoding="utf-8")
        self.assertEqual(log.count("UvResolveError"), 1)

    def test_resolve_phrase_inside_a_path_is_not_a_resolve_error(self):
        # 同じ句がパスに含まれていても、行の頭の誤りでなければ、依存を解決できない失敗とはみなさない。
        # 壊れた環境の失敗なので、入れ直しに任せる（UvResolveError で止めない）。
        output = (b"error: Failed to read metadata from installed package at "
                  b"C:/cache/no solution found when resolving/pkg.dist-info/METADATA\n")
        self.assertFalse(common.is_resolve_error(output.decode()))
        fake = FakeUv([(2, output)])
        self.assertEqual(self.sync(fake), 2)

    def test_colored_resolve_error_is_recognized(self):
        # uv は FORCE_COLOR などで、パイプにも色を付けることがある。色の指定を除いてから見分ける。
        output = b"\x1b[1;31merror\x1b[0m: No solution found when resolving dependencies\n" + RESOLVE_OUTPUT[53:]
        fake = FakeUv([(1, output)])
        with self.assertRaises(common.UvResolveError) as caught:
            self.sync(fake)
        self.assertEqual(len(fake.calls), 1)
        self.assertNotIn("\x1b", str(caught.exception))

    def test_timeout_records_uv_output_in_launch_log(self):
        # 待ちきれずに止まったときも、それまでの uv の出力の理由の行を launch.log に残す。
        def slow(command, **kwargs):
            if "--help" in command:
                return subprocess.CompletedProcess(command, 0, stdout=NEW_HELP, stderr=b"")
            raise subprocess.TimeoutExpired(command, 1, output=b"error: Failed to download Python\n"
                                                              b"  cause: proxy connection refused\n")
        with mock.patch.object(common.subprocess, "run", slow), self.assertRaises(subprocess.TimeoutExpired):
            common.prepare_script(RELAY, output=io.StringIO(), timeout=1, log=self.logs.append)
        log = (self.data / "logs" / "launch.log").read_text(encoding="utf-8")
        self.assertIn("TimeoutExpired", log)
        self.assertIn("uv の出力: error: Failed to download Python / cause: proxy connection refused", log)

    def test_unresolvable_after_tls_retry_is_reported_as_resolve_error(self):
        # 証明書の問題は OS の証明書ストアで直ったが、依存を解決できなかった。
        fake = FakeUv([(2, TLS_OUTPUT), (1, RESOLVE_OUTPUT)])
        with self.assertRaises(common.UvResolveError):
            self.sync(fake)
        self.assertEqual(os.environ.get("UV_SYSTEM_CERTS"), "true")

    def test_other_prepare_failures_are_recorded_once(self):
        # 入れ直しても直らなかったなど、UvSetupError でない失敗も launch.log に残す。中継がサーバーの環境を
        # 用意するときは、ここで残さないと、利用者が読む場所に理由が残らない。終了コードだけでなく、uv の
        # 出力の理由の行も残す（Python を取れない、プロキシに断られた、など）。
        output = b"error: Failed to download Python\n  cause: connection refused by proxy 127.0.0.1:9\n"
        fake = FakeUv([(2, output)] * 3)
        lock = Path(tempfile.mkdtemp(prefix="wiki-tls-lock-"))
        self.addCleanup(shutil.rmtree, lock, ignore_errors=True)
        with mock.patch.object(common.subprocess, "run", fake), \
                mock.patch.object(common, "env_lock_path", return_value=lock / "env.lock"):
            with self.assertRaises(RuntimeError) as caught:
                common.prepare_script(RELAY, output=io.StringIO(), timeout=10, log=self.logs.append)
        self.assertNotIsInstance(caught.exception, common.UvSetupError)
        log = (self.data / "logs" / "launch.log").read_text(encoding="utf-8")
        self.assertEqual(log.count("の環境を用意できなかった"), 1)
        self.assertIn("--reinstall", log)
        self.assertIn("error: Failed to download Python / cause: connection refused by proxy", log)


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
