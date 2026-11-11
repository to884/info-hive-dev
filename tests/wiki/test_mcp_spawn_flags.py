"""wiki の MCP の経路で子プロセスを起動するときの旗の試験（info-hive-wiki#36）。

Windows では、コンソールを持たないプロセスがコンソール用のプログラムを起動すると、新しいコンソールが作られ、
画面が出る。一方、子が親と別のコンソールに入ると、親から受け取ったコンソールの標準ハンドルに書けない。
そのため、入口、中継、サーバーの子プロセスの起動は、すべて次のどちらかを creationflags に渡す。

- `wiki_mcp_common.child_creationflags()`: 親にコンソールがあれば引き継ぎ（0）、なければ CREATE_NO_WINDOW。
- `wiki_mcp_common.server_creationflags()`: サーバー。中継と別の、窓のないコンソールと新しいプロセスグループ。

依存は要らない。

    python -X utf8 -m unittest tests/wiki/test_mcp_spawn_flags.py -v
"""
from __future__ import annotations

import ast
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "info-hive-wiki/skills/info-hive/scripts"
MCP_FILES = ("wiki_mcp_common.py", "wiki_mcp_launch.py", "wiki_mcp_relay.py", "wiki_mcp_server.py")
SPAWNERS = {"run", "Popen", "call", "check_call", "check_output", "getoutput", "getstatusoutput"}
FLAG_FUNCTIONS = {"child_creationflags", "server_creationflags"}
sys.path.insert(0, str(SCRIPTS))
import wiki_mcp_common as common  # noqa: E402
import wiki_mcp_relay as relay  # noqa: E402


def subprocess_calls(tree: ast.AST):
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in SPAWNERS
                and isinstance(node.func.value, ast.Name) and node.func.value.id == "subprocess"):
            yield node


def flag_function(call: ast.Call) -> str | None:
    """creationflags に渡しているのが FLAG_FUNCTIONS の呼び出しなら、その名前。"""
    value = next((k.value for k in call.keywords if k.arg == "creationflags"), None)
    if not isinstance(value, ast.Call):
        return None
    func = value.func
    name = func.attr if isinstance(func, ast.Attribute) else func.id if isinstance(func, ast.Name) else None
    return name if name in FLAG_FUNCTIONS else None


class SpawnFlagsTests(unittest.TestCase):
    def test_every_child_process_uses_flag_function(self):
        """MCP の経路の子プロセスの起動は、すべて child_creationflags か server_creationflags を渡す。"""
        wrong = []
        for name in MCP_FILES:
            tree = ast.parse((SCRIPTS / name).read_text(encoding="utf-8"), filename=name)
            wrong += [f"{name}:{call.lineno}" for call in subprocess_calls(tree) if flag_function(call) is None]
        self.assertEqual(wrong, [], "旗の関数を通さない子プロセスの起動")

    def test_only_spawn_server_uses_server_flags(self):
        found = []
        for name in MCP_FILES:
            tree = ast.parse((SCRIPTS / name).read_text(encoding="utf-8"), filename=name)
            found += [name for call in subprocess_calls(tree) if flag_function(call) == "server_creationflags"]
        self.assertEqual(found, ["wiki_mcp_relay.py"])

    def test_detached_process_is_not_used(self):
        used = []
        for name in MCP_FILES:
            tree = ast.parse((SCRIPTS / name).read_text(encoding="utf-8"), filename=name)
            used += [f"{name}:{n.lineno}" for n in ast.walk(tree)
                     if isinstance(n, ast.Attribute) and n.attr == "DETACHED_PROCESS"]
        self.assertEqual(used, [])

    @unittest.skipUnless(os.name == "nt", "Windows だけの試験")
    def test_child_flags_follow_console(self):
        with mock.patch.object(common, "has_console", return_value=True):
            self.assertEqual(common.child_creationflags(), 0)
        with mock.patch.object(common, "has_console", return_value=False):
            self.assertEqual(common.child_creationflags(), subprocess.CREATE_NO_WINDOW)
        self.assertEqual(common.server_creationflags(),
                         subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP)

    @unittest.skipIf(os.name == "nt", "POSIX だけの試験")
    def test_flags_are_zero_on_posix(self):
        self.assertEqual(common.child_creationflags(), 0)
        self.assertEqual(common.server_creationflags(), 0)

    @unittest.skipUnless(os.name == "nt", "Windows だけの試験")
    def test_has_console_without_console(self):
        """コンソールを持たないプロセス（DETACHED_PROCESS）では偽、窓のないコンソールでは真になる。"""
        code = f"import sys; sys.path.insert(0, {str(SCRIPTS)!r}); import wiki_mcp_common as c; print(c.has_console())"
        python = getattr(sys, "_base_executable", sys.executable)
        for flags, expected in ((subprocess.DETACHED_PROCESS, "False"), (subprocess.CREATE_NO_WINDOW, "True")):
            out = subprocess.run([python, "-c", code], capture_output=True, text=True, encoding="utf-8",
                                 creationflags=flags, timeout=60)
            self.assertEqual(out.stdout.strip(), expected, out.stderr)

    @unittest.skipUnless(os.name == "nt", "Windows だけの試験")
    def test_child_can_write_to_inherited_console(self):
        """親のコンソールの標準出力を渡した子が、そこに書ける（子を別のコンソールに入れると書けない）。

        親（ここで起動する python）は、窓のないコンソールを持ち、その CONOUT$ を標準出力にして子を起動する。
        """
        code = textwrap.dedent(f"""
            import subprocess, sys
            sys.path.insert(0, {str(SCRIPTS)!r})
            import wiki_mcp_common as c
            out = open("CONOUT$", "w")
            child = subprocess.run([sys.executable, "-c", "print('ok')"], stdout=out,
                                   creationflags=c.child_creationflags())
            sys.exit(child.returncode)
        """)
        python = getattr(sys, "_base_executable", sys.executable)
        out = subprocess.run([python, "-c", code], capture_output=True, text=True, encoding="utf-8",
                             creationflags=subprocess.CREATE_NO_WINDOW, timeout=60)
        self.assertEqual(out.returncode, 0, out.stderr)

    def test_spawn_server_flags(self):
        captured = {}

        class FakeProcess:
            def wait(self):
                return 0

        def fake_popen(args, **kwargs):
            captured.update(kwargs)
            return FakeProcess()

        with tempfile.TemporaryDirectory() as data, \
                mock.patch.dict(os.environ, {common.DATA_DIR_ENV: data}), \
                mock.patch.object(relay.subprocess, "Popen", fake_popen):
            relay.spawn_server(sys.executable, subprocess.DEVNULL)
        self.assertEqual(captured["creationflags"], common.server_creationflags())
        self.assertEqual(captured["start_new_session"], os.name != "nt")


if __name__ == "__main__":
    unittest.main()
