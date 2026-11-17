"""登録済みの起動行が、呼び出し元の環境に左右されず入力を渡すことを確かめる。"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import venv

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bench_prompt_hook as bench
from test_prompt_hook import WikiFixture, hook_input, write

HOOK = bench.SCRIPTS / "wiki_prompt_hook.py"


class LauncherTests(unittest.TestCase):
    def setUp(self):
        if not shutil.which("uv"):
            self.skipTest("uv がない")
        self.temp = tempfile.TemporaryDirectory(prefix="wiki-hook-launch-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.fixture = WikiFixture(self.base, name="日本語を含む project")
        self.env = dict(os.environ, INFO_HIVE_PROMPT_CONTEXT="1",
                        CLAUDE_PLUGIN_DATA=str(self.base / "data"))
        for key in ("VIRTUAL_ENV", "RUST_LOG", "UV_PYTHON", "UV_PYTHON_INSTALL_DIR",
                    "UV_MANAGED_PYTHON", "UV_PYTHON_PREFERENCE"):
            self.env.pop(key, None)
        self.payload = json.dumps(hook_input(self.fixture.project,
            "[[リリースの確かめ方]] の完了の条件を確認して", session_id="launcher"),
            ensure_ascii=False).encode("utf-8")
        self.shells = {}
        if bench.bash_path():
            self.shells["bash"] = [bench.bash_path(), "-c"]
        if bench.pwsh_path():
            self.shells["powershell"] = [bench.pwsh_path(), "-NoProfile", "-NonInteractive", "-Command"]
        if not self.shells:
            self.skipTest("対応するシェルがない")

    def invoke(self, shell, command=None, env=None):
        return subprocess.run([*self.shells[shell], command or bench.shell_line(HOOK)],
            cwd=self.fixture.project, input=self.payload, capture_output=True,
            env=env or self.env, timeout=20)

    def assert_context(self, result):
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        self.assertEqual(result.stderr, b"")
        output = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "UserPromptSubmit")
        self.assertIn("リリースの確かめ方", output["additionalContext"])
        self.assertLessEqual(len(output["additionalContext"]), 2000)

    def test_project_config_and_pythonpath_do_not_change_hook(self):
        # プロジェクトと uv の設定が壊れていても、環境の同期や設定の解析をしない。
        for name, text in (("pyproject.toml", "[壊れた設定"), ("uv.toml", "[壊れた設定"),
                           (".python-version", "3.99\n")):
            write(self.fixture.project / name, text)
        poison = self.base / "pythonpath"
        marker = self.base / "site-ran"
        write(poison / "sitecustomize.py",
              f"from pathlib import Path\nPath({str(marker)!r}).touch()\nraise RuntimeError('site')\n")
        env = dict(self.env, PYTHONPATH=str(poison))
        before = {name: (self.fixture.project / name).read_bytes()
                  for name in ("pyproject.toml", "uv.toml", ".python-version")}
        for shell in self.shells:
            with self.subTest(shell=shell):
                self.assert_context(self.invoke(shell, env=dict(env,
                    CLAUDE_PLUGIN_DATA=str(self.base / (shell + "-data")))))
        self.assertFalse(marker.exists())
        self.assertFalse((self.fixture.project / ".venv").exists())
        self.assertFalse((self.fixture.project / "uv.lock").exists())
        for name, content in before.items():
            self.assertEqual((self.fixture.project / name).read_bytes(), content)

    def test_utf8_stdin_arrives_unchanged_in_both_shells(self):
        echo = self.base / "日本語 echo.py"
        write(echo, "import os, sys\nfrom pathlib import Path\n"
                    "Path(os.environ['ECHO_OUT']).write_bytes(sys.stdin.buffer.read())\n")
        for shell in self.shells:
            with self.subTest(shell=shell):
                sink = self.base / (shell + ".bin")
                result = self.invoke(shell, bench.shell_line(echo), dict(self.env, ECHO_OUT=str(sink)))
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stderr, b"")
                self.assertEqual(sink.read_bytes(), self.payload)

    def test_missing_python_script_and_uv_do_not_block_prompt(self):
        env = dict(self.env, UV_MANAGED_PYTHON="1",
                   UV_PYTHON_INSTALL_DIR=str(self.base / "no-python"))
        scenarios = ((bench.shell_line(HOOK), env),
                     (bench.shell_line(self.base / "missing.py"), self.env),
                     (bench.shell_line(HOOK, uv="info_hive_missing_uv_0123456789"), self.env))
        for shell in self.shells:
            for command, current_env in scenarios:
                with self.subTest(shell=shell, command=command):
                    result = self.invoke(shell, command, current_env)
                    self.assertEqual(result.returncode, 0)
                    self.assertEqual(result.stdout, b"")
                    # 実際に起動が失敗しており、末尾の exit 0 がそれを吸収したことを確かめる。
                    failed = self.invoke(shell, command.removesuffix("; exit 0"), current_env)
                    self.assertNotEqual(failed.returncode, 0)
                    self.assertEqual(failed.stdout, b"")

    def test_direct_virtualenv_entry_can_start_worker_without_site(self):
        # フックを直接 venv の Python から呼ぶ経路も維持する。uv の環境検出とは別の試験。
        root = self.base / "venv"
        venv.EnvBuilder(with_pip=False).create(root)
        python = root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        result = subprocess.run([str(python), "-I", "-S", str(HOOK)], input=self.payload,
            capture_output=True, env=self.env, timeout=20)
        self.assert_context(result)

    def test_existing_project_and_active_virtualenvs_are_supported(self):
        root = self.fixture.project / ".venv"
        venv.EnvBuilder(with_pip=False).create(root)
        echo = self.base / "interpreter.py"
        write(echo, "import json, os, sys\nfrom pathlib import Path\n"
                    "Path(os.environ['ECHO_OUT']).write_text(json.dumps(sys.executable), encoding='utf-8')\n")
        for active in (False, True):
            for shell in self.shells:
                with self.subTest(active=active, shell=shell):
                    env = dict(self.env, CLAUDE_PLUGIN_DATA=str(self.base / f"data-{active}-{shell}"))
                    if active:
                        env["VIRTUAL_ENV"] = str(root)
                    sink = self.base / "interpreter.json"
                    probe = self.invoke(shell, bench.shell_line(echo), dict(env, ECHO_OUT=str(sink)))
                    self.assertEqual(probe.returncode, 0)
                    self.assertEqual(probe.stderr, b"")
                    self.assertTrue(Path(json.loads(sink.read_text(encoding="utf-8"))).is_relative_to(root))
                    self.assert_context(self.invoke(shell, env=env))

    @unittest.skipUnless(os.name == "nt", "Windowsの優先度を使う試験")
    def test_foreground_priority_is_limited_to_the_hook_parent_and_worker(self):
        # importしただけでは呼び出し元を変えず、実際の入口と解析の子だけがAboveNormalになる。
        query = """import ctypes
k = ctypes.WinDLL('kernel32', use_last_error=True)
get = k.GetPriorityClass
get.argtypes = (ctypes.c_void_p,)
get.restype = ctypes.c_uint32
"""
        code = ("import sys\n" + query + f"\nsys.path.insert(0, {str(bench.SCRIPTS)!r})\n"
                "before = get(ctypes.c_void_p(-1))\nimport wiki_prompt_hook\n"
                "assert before == get(ctypes.c_void_p(-1))\n")
        imported = subprocess.run([sys.executable, "-I", "-S", "-c", code], capture_output=True, timeout=20)
        self.assertEqual(imported.returncode, 0, imported.stderr.decode("utf-8", "replace"))
        source = HOOK.read_text(encoding="utf-8").replace(
            "sys.path.insert(0, str(Path(__file__).resolve().parent))",
            f"sys.path.insert(0, {str(bench.SCRIPTS)!r})")
        source = source.replace('    if os.name != "nt":',
            '    if "--worker" in sys.argv:\n        raise AssertionError("子が優先度を再設定した")\n    if os.name != "nt":')
        probe = (query + "\nwith open(os.environ['PRIORITY_OUT'], 'ab') as stream:\n"
                 "    stream.write((json.dumps({'priority': get(ctypes.c_void_p(-1)), "
                 "'worker': '--worker' in sys.argv}) + '\\n').encode('ascii'))\n")
        source = source.replace('if __name__ == "__main__":\n',
            'if __name__ == "__main__":\n' + "\n".join("    " + line for line in probe.splitlines()) + "\n")
        copy = self.base / "priority_hook.py"
        write(copy, source)
        sink = self.base / "priority.jsonl"
        result = subprocess.run([sys.executable, "-I", "-S", str(copy)], input=self.payload,
            capture_output=True, env=dict(self.env, PRIORITY_OUT=str(sink)), timeout=20)
        self.assert_context(result)
        rows = [json.loads(line) for line in sink.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(rows, [{"priority": 0x8000, "worker": False}, {"priority": 0x8000, "worker": True}])
        # 親のAPIが拒否されたら、子も起動時の通常優先度を維持する。
        refused = self.base / "priority_refused.py"
        write(refused, source.replace('change = kernel32.SetPriorityClass', 'raise OSError("優先度の変更を拒否")'))
        sink = self.base / "refused.jsonl"
        result = subprocess.run([sys.executable, "-I", "-S", str(refused)], input=self.payload,
            capture_output=True, env=dict(self.env, PRIORITY_OUT=str(sink), CLAUDE_PLUGIN_DATA=str(self.base / "refused-data")), timeout=20)
        self.assert_context(result)
        rows = [json.loads(line) for line in sink.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(rows, [{"priority": 0x20, "worker": False}, {"priority": 0x20, "worker": True}])


if __name__ == "__main__":
    unittest.main()
