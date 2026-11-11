"""wiki の MCP の経路で子プロセスを起動するときの旗の試験（info-hive-wiki#36）。

Windows では、コンソールを持たないプロセスがコンソール用のプログラムを起動すると、新しいコンソールが作られ、
画面が出る。入口、中継、サーバーのどれがコンソールなしで起動されても画面が出ないよう、子プロセスの起動には
すべて `wiki_mcp_common.NO_WINDOW`（CREATE_NO_WINDOW）を付ける。`DETACHED_PROCESS` は使わない。
依存は要らない。

    python -X utf8 -m unittest tests/wiki/test_mcp_spawn_flags.py -v
"""
from __future__ import annotations

import ast
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "info-hive-wiki/skills/info-hive/scripts"
MCP_FILES = ("wiki_mcp_common.py", "wiki_mcp_launch.py", "wiki_mcp_relay.py", "wiki_mcp_server.py")
SPAWNERS = {"run", "Popen", "call", "check_call", "check_output", "getoutput", "getstatusoutput"}
sys.path.insert(0, str(SCRIPTS))
import wiki_mcp_common as common  # noqa: E402
import wiki_mcp_relay as relay  # noqa: E402


def subprocess_calls(tree: ast.AST):
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in SPAWNERS
                and isinstance(node.func.value, ast.Name) and node.func.value.id == "subprocess"):
            yield node


class SpawnFlagsTests(unittest.TestCase):
    def test_every_child_process_sets_creationflags(self):
        """MCP の経路の子プロセスの起動は、すべて creationflags を明示する。"""
        missing = []
        for name in MCP_FILES:
            tree = ast.parse((SCRIPTS / name).read_text(encoding="utf-8"), filename=name)
            for call in subprocess_calls(tree):
                if not any(k.arg == "creationflags" for k in call.keywords):
                    missing.append(f"{name}:{call.lineno}")
        self.assertEqual(missing, [], "creationflags のない子プロセスの起動")

    def test_detached_process_is_not_used(self):
        used = []
        for name in MCP_FILES:
            tree = ast.parse((SCRIPTS / name).read_text(encoding="utf-8"), filename=name)
            used += [f"{name}:{n.lineno}" for n in ast.walk(tree)
                     if isinstance(n, ast.Attribute) and n.attr == "DETACHED_PROCESS"]
        self.assertEqual(used, [])

    def test_no_window_flag(self):
        expected = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        self.assertEqual(common.NO_WINDOW, expected)

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
        if os.name == "nt":
            # 中継とは別の、窓のないコンソール。中継のコンソールの Ctrl+C や閉じる操作は、サーバーに届かない。
            self.assertEqual(captured["creationflags"],
                             subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP)
            self.assertFalse(captured["start_new_session"])
        else:
            self.assertEqual(captured["creationflags"], 0)
            self.assertTrue(captured["start_new_session"])


if __name__ == "__main__":
    unittest.main()
