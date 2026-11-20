"""素の Windows に Visual C++ 再頒布可能パッケージがなく、依存の DLL を読めないときの振る舞いの試験。

`usearch.index` の import が `ImportError: DLL load failed while importing compiled: 指定されたモジュールが
見つかりません` で失敗する。環境を入れ直しても直らないので、入れ直しに進まず、利用者が読む launch.log と
例外のメッセージに、原因と winget のコマンドを書いて止まることを確かめる。

    uv run --python 3.12 python -X utf8 -m unittest tests/wiki/test_vc_runtime.py -v
"""
from __future__ import annotations

import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "info-hive-wiki/skills/info-hive/scripts"
RELAY = SCRIPTS / "wiki_mcp_relay.py"
SERVER = SCRIPTS / "wiki_mcp_server.py"
sys.path.insert(0, str(SCRIPTS))
import wiki_mcp_common as common  # noqa: E402

DLL_MESSAGE = "DLL load failed while importing compiled: 指定されたモジュールが見つかりません。"
WINGET = "winget install --id Microsoft.VCRedist.2015+.x64 -e --source winget"
_real_is_dll_load_error = common.is_dll_load_error


def as_windows(exc):
    return _real_is_dll_load_error(exc, windows=True)


class DllDetectionTest(unittest.TestCase):
    def test_dll_failure_on_windows_is_detected(self):
        self.assertTrue(common.is_dll_load_error(ImportError(DLL_MESSAGE), windows=True))
        self.assertTrue(common.is_dll_load_error(ModuleNotFoundError("DLL load failed while importing x"), windows=True))

    def test_other_platforms_and_other_import_errors_are_not(self):
        self.assertFalse(common.is_dll_load_error(ImportError(DLL_MESSAGE), windows=False))
        self.assertFalse(common.is_dll_load_error(ImportError("No module named 'numpy'"), windows=True))
        self.assertFalse(common.is_dll_load_error(OSError(DLL_MESSAGE), windows=True))

    def test_message_names_the_dlls_and_the_command(self):
        message = common.vc_runtime_message()
        for dll in ("vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll"):
            self.assertIn(dll, message)
        self.assertIn(WINGET, message)
        self.assertEqual(common.VC_REDIST_COMMAND, WINGET)


class MissingRuntimeTest(unittest.TestCase):
    def test_reports_only_the_dlls_that_are_absent(self):
        directory = Path(tempfile.mkdtemp(prefix="wiki-vc-sys-"))
        self.addCleanup(shutil.rmtree, directory, ignore_errors=True)
        self.assertEqual(common.missing_vc_runtime_dlls(directory), list(common.VC_RUNTIME_DLLS))
        (directory / "vcruntime140.dll").write_bytes(b"")
        (directory / "vcruntime140_1.dll").write_bytes(b"")
        self.assertEqual(common.missing_vc_runtime_dlls(directory), ["msvcp140.dll"])
        (directory / "msvcp140.dll").write_bytes(b"")
        self.assertEqual(common.missing_vc_runtime_dlls(directory), [])

    @unittest.skipIf(os.name == "nt", "Windows 以外で空を返すことの確認")
    def test_not_windows_has_nothing_missing(self):
        self.assertEqual(common.missing_vc_runtime_dlls(), [])


class RequireEnvTest(unittest.TestCase):
    def run_require_env(self, error: Exception, missing=("msvcp140.dll",)):
        stderr = io.StringIO()
        with mock.patch.object(common, "env_problems", return_value=[]), \
                mock.patch.object(common, "is_dll_load_error", as_windows), \
                mock.patch.object(common, "missing_vc_runtime_dlls", return_value=list(missing)), \
                mock.patch("importlib.import_module", side_effect=error), \
                mock.patch.object(sys, "stderr", stderr):
            with self.assertRaises(SystemExit) as caught:
                common.require_env(("usearch.index",))
        return caught.exception.code, stderr.getvalue()

    def test_dll_failure_exits_with_runtime_lib_code(self):
        code, text = self.run_require_env(ImportError(DLL_MESSAGE))
        self.assertEqual(code, common.RUNTIME_LIB_EXIT)
        self.assertNotEqual(common.RUNTIME_LIB_EXIT, common.BROKEN_ENV_EXIT)
        self.assertIn("usearch.index", text)
        self.assertIn(WINGET, text)
        self.assertIn(DLL_MESSAGE, text)  # 原文を保つ
        self.assertIn("msvcp140.dll", text)

    def test_dll_failure_without_missing_runtime_is_still_broken_env(self):
        # 拡張ファイルの形式が不正など、ランタイムは揃っているのに DLL を読めないときは、入れ直しに任せる。
        code, text = self.run_require_env(ImportError(DLL_MESSAGE), missing=())
        self.assertEqual(code, common.BROKEN_ENV_EXIT)
        self.assertNotIn(WINGET, text)

    def test_plain_import_error_still_means_broken_env(self):
        code, text = self.run_require_env(ImportError("No module named 'usearch'"))
        self.assertEqual(code, common.BROKEN_ENV_EXIT)
        self.assertNotIn(WINGET, text)


class PrepareScriptTest(unittest.TestCase):
    def setUp(self):
        self.data = Path(tempfile.mkdtemp(prefix="wiki-vc-data-"))
        self.addCleanup(shutil.rmtree, self.data, ignore_errors=True)
        patcher = mock.patch.dict(os.environ, {common.DATA_DIR_ENV: str(self.data)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_dll_failure_stops_without_reinstall(self):
        sync = mock.Mock(return_value=(0, ""))
        result = subprocess.CompletedProcess([], common.RUNTIME_LIB_EXIT)
        with mock.patch.object(common, "_uv_sync_result", sync), \
                mock.patch.object(common, "script_python", return_value="python"), \
                mock.patch.object(common, "env_lock_path", return_value=self.data / "env.lock"), \
                mock.patch.object(common.subprocess, "run", return_value=result):
            with self.assertRaises(common.VcRuntimeError) as caught:
                common.prepare_script(SERVER, output=io.StringIO(), timeout=10, log=lambda _: None, force=True)
        self.assertIsInstance(caught.exception, common.UvSetupError)
        self.assertFalse(any(call.kwargs.get("reinstall") for call in sync.call_args_list))
        self.assertIn(WINGET, str(caught.exception))
        log = (self.data / "logs" / "launch.log").read_text(encoding="utf-8")
        self.assertEqual(log.count("VcRuntimeError"), 1)  # prepare_script が二重に記録しない
        self.assertIn(WINGET, log)
        self.assertIn("Visual C++", log)


class LauncherTest(unittest.TestCase):
    def setUp(self):
        self.data = Path(tempfile.mkdtemp(prefix="wiki-vc-launch-"))
        self.addCleanup(shutil.rmtree, self.data, ignore_errors=True)
        patcher = mock.patch.dict(os.environ, {common.DATA_DIR_ENV: str(self.data)})
        patcher.start()
        self.addCleanup(patcher.stop)
        import wiki_mcp_launch as launch
        self.launch = launch

    def run_main(self, codes):
        with mock.patch.object(self.launch, "prepare", return_value="python") as prepare, \
                mock.patch.object(self.launch, "run_relay", side_effect=codes) as run_relay:
            result = self.launch.main()
        return result, prepare, run_relay

    def log_text(self):
        path = self.data / "logs" / "launch.log"
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def test_first_run_stops_without_repair(self):
        result, prepare, run_relay = self.run_main([common.RUNTIME_LIB_EXIT])
        self.assertEqual(result, 1)
        self.assertEqual(run_relay.call_count, 1)
        self.assertEqual(prepare.call_count, 1)  # 入れ直し（force）に進まない
        self.assertEqual(self.log_text().count(WINGET), 1)

    def test_runtime_error_after_repair_is_recorded_too(self):
        # 75 で入れ直し、再起動した中継が 76 を返しても、launch.log に対処を残す。
        result, prepare, run_relay = self.run_main([common.BROKEN_ENV_EXIT, common.RUNTIME_LIB_EXIT])
        self.assertEqual(result, 1)
        self.assertEqual(run_relay.call_count, 2)
        self.assertEqual(prepare.call_args_list[1].kwargs.get("force"), True)
        self.assertEqual(self.log_text().count(WINGET), 1)

    def test_other_codes_are_returned_unchanged(self):
        result, _, _ = self.run_main([0])
        self.assertEqual(result, 0)
        self.assertEqual(self.log_text(), "")


class UpstreamTest(unittest.TestCase):
    def test_confirmed_runtime_error_is_not_retried_per_request(self):
        try:
            import anyio  # noqa: F401
            import wiki_mcp_relay as relay
        except ImportError:
            self.skipTest("anyio が要る（uv run --with anyio --with httpx --with mcp ...）")
        error = common.VcRuntimeError(common.vc_runtime_message())
        calls = []

        def ensure():
            calls.append(1)
            raise error

        async def run():
            upstream = relay.Upstream(task_group=None)
            for _ in range(3):
                with self.assertRaises(common.VcRuntimeError):
                    await upstream._connect()

        import asyncio
        with mock.patch.object(relay, "ensure_server", ensure):
            asyncio.run(run())
        self.assertEqual(len(calls), 1)  # 2 回目以降は起動しない


class RelayStartTest(unittest.TestCase):
    def test_server_exit_with_runtime_lib_code_raises_with_advice(self):
        sys.path.insert(0, str(SCRIPTS))
        import wiki_mcp_relay as relay
        data = Path(tempfile.mkdtemp(prefix="wiki-vc-relay-"))
        self.addCleanup(shutil.rmtree, data, ignore_errors=True)

        class Dead:
            def poll(self):
                return common.RUNTIME_LIB_EXIT

        files = mock.Mock()
        files.read_info.return_value = None
        files.root = data
        with mock.patch.dict(os.environ, {common.DATA_DIR_ENV: str(data)}), \
                mock.patch.object(relay, "server_python", return_value="python") as server_python, \
                mock.patch.object(relay, "spawn_server", return_value=Dead()) as spawn:
            with self.assertRaises(common.VcRuntimeError) as caught:
                relay._start_server(files, "id", io.StringIO())
        self.assertEqual(spawn.call_count, 1)  # 起動し直さない
        self.assertEqual(server_python.call_count, 1)  # 入れ直さない（force なし）
        self.assertFalse(any(call.kwargs.get("force") for call in server_python.call_args_list))
        self.assertIn(WINGET, str(caught.exception))
        self.assertIn(WINGET, (data / "logs" / "launch.log").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
