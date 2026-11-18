"""ADR-0029 の MCP 起動ファイルの検査。MCP の外部依存を使わずに確かめる。"""

import io
import os
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stderr
from pathlib import Path
from threading import Event
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[2] / "info-hive-wiki/skills/info-hive/scripts"
sys.path.insert(0, str(SCRIPTS))
from wiki_fsguard import Refused  # noqa: E402
from wiki_browse_fs import X  # noqa: E402
from wiki_mcp_common import DATA_DIR_ENV, ServerFiles, data_dir, record_failure  # noqa: E402


class ServerFilesTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.data = self.root / "data"
        self.enterContext(mock.patch.dict(os.environ, {DATA_DIR_ENV: str(self.data)}))
        self.files = ServerFiles()
        self.info = {"pid": os.getpid(), "port": 1234, "token": "test-token"}

    def test_refuses_linked_temporary_file(self):
        outside = self.root / "original"
        outside.write_bytes(b"unchanged")
        temporary = self.data / ".server-json-collision.tmp"
        os.link(outside, temporary)
        with mock.patch("wiki_fsguard.secrets.token_hex", return_value="collision"), \
                self.assertRaises(Refused) as caught:
            self.files.write_info(self.info)
        self.assertEqual(caught.exception.path, temporary)
        self.assertEqual(caught.exception.kind, "hardlink")
        self.assertEqual(outside.read_bytes(), b"unchanged")
        self.assertTrue(temporary.samefile(outside))
        self.assertFalse(self.files.record.exists())

    def test_cleans_own_private_temporary_file_when_replace_is_refused(self):
        outside = self.root / "original"
        outside.write_bytes(b"unchanged")
        replace = self.files.guard.replace_file

        def refuse_replace(temporary, record, **kwargs):
            if os.name != "nt":
                self.assertEqual(temporary.stat().st_mode & 0o077, 0)
            os.link(outside, record)
            replace(temporary, record, **kwargs)

        with mock.patch.object(self.files.guard, "replace_file", side_effect=refuse_replace), \
                self.assertRaises(Refused) as caught:
            self.files.write_info(self.info)
        self.assertEqual(caught.exception.path, self.files.record)
        self.assertEqual(caught.exception.kind, "hardlink")
        self.assertFalse(list(self.data.glob(".server-json-*.tmp")))
        self.assertEqual(outside.read_bytes(), b"unchanged")
        self.assertTrue(self.files.record.samefile(outside))

    def test_old_pid_temporary_name_is_left_alone(self):
        outside = self.root / "original"
        outside.write_bytes(b"unchanged")
        legacy = self.data / f"server.json.{os.getpid()}.tmp"
        os.link(outside, legacy)
        self.files.write_info(self.info)
        self.assertEqual(self.files.read_info(), self.info)
        self.assertEqual(outside.read_bytes(), b"unchanged")
        self.assertTrue(legacy.samefile(outside))
        if os.name != "nt":
            self.assertEqual(self.files.record.stat().st_mode & 0o077, 0)

    def test_only_owner_removes_record(self):
        self.files.write_info(self.info)
        self.files.remove_own_info(self.info["pid"] + 1, self.info["token"])
        self.files.remove_own_info(self.info["pid"], "old-token")
        self.assertEqual(self.files.read_info(), self.info)
        self.files.remove_own_info(self.info["pid"], self.info["token"])
        self.assertFalse(self.files.record.exists())

    def test_exit_and_publication_are_serialized(self):
        self.files.write_info(self.info)
        newer = {**self.info, "token": "new-token"}
        writer = ServerFiles()
        removing, release, publishing = Event(), Event(), Event()
        remove = self.files.guard.remove_file
        record_lock = writer._record_lock

        def pause_removal(path):
            removing.set()
            self.assertTrue(release.wait(5))
            remove(path)

        def announce_publication():
            publishing.set()
            return record_lock()

        with ThreadPoolExecutor(max_workers=2) as pool, \
                mock.patch.object(self.files.guard, "remove_file", side_effect=pause_removal), \
                mock.patch.object(writer, "_record_lock", side_effect=announce_publication):
            exiting = pool.submit(self.files.remove_own_info, self.info["pid"], self.info["token"])
            try:
                self.assertTrue(removing.wait(5))
                writing = pool.submit(writer.write_info, newer)
                self.assertTrue(publishing.wait(5))
                self.assertFalse(writing.done())
            finally:
                release.set()
            exiting.result(timeout=5)
            writing.result(timeout=5)
        self.assertEqual(self.files.read_info(), newer)

    def test_relay_preserves_record_published_while_stopping(self):
        self.files.write_info(self.info)
        newer = {**self.info, "token": "new-token"}
        with self.files.startup_lock(timeout=0):
            start_id = self.files.reserve_start(self.info)
            self.files.write_info(newer, start_id=start_id)
            self.files.release_start(start_id)
            with self.assertRaisesRegex(RuntimeError, "記録が変わった"):
                self.files.reserve_start(self.info)
        self.assertEqual(self.files.read_info(), {**newer, "start_id": start_id})

    def test_direct_start_cannot_overwrite_running_server_record(self):
        with self.files.startup_lock(timeout=0):
            start_id = self.files.reserve_start(None)
            self.files.write_info(self.info, start_id=start_id)
            self.files.release_start(start_id)
        with self.assertRaisesRegex(OSError, "記録がすでにある"):
            self.files.write_info({**self.info, "pid": self.info["pid"] + 1, "token": "other-token"})
        self.assertEqual(self.files.read_info(), {**self.info, "start_id": start_id})

    def test_read_refuses_a_different_file_opened_after_check(self):
        self.files.write_info(self.info)
        original = self.files.record.with_suffix(".previous")
        open_plain_read = X.open_plain_read

        def swap_record(path):
            path.rename(original)
            path.write_bytes(b"unrelated bytes")
            return open_plain_read(path)

        with mock.patch.object(X, "open_plain_read", side_effect=swap_record), \
                self.assertRaises(Refused) as caught:
            self.files.read_info()
        self.assertEqual(caught.exception.path, self.files.record)
        self.assertEqual(caught.exception.kind, "changed")
        self.assertEqual(self.files.record.read_bytes(), b"unrelated bytes")

    def test_linked_launch_log_refusal_is_reported_to_stderr(self):
        outside = self.root / "original"
        outside.write_bytes(b"unchanged")
        logs = self.data / "logs"
        logs.mkdir()
        log = logs / "launch.log"
        os.link(outside, log)
        with redirect_stderr(io.StringIO()) as stderr:
            record_failure("元の起動エラー")
        self.assertIn(str(log), stderr.getvalue())
        self.assertIn("hardlink", stderr.getvalue())
        self.assertEqual(outside.read_bytes(), b"unchanged")
        self.assertTrue(log.samefile(outside))

    def test_legacy_process_default_data_dir_uses_its_own_home(self):
        home = self.root / "other-home"
        if os.name == "nt":
            self.assertEqual(data_dir({"USERPROFILE": str(home)}), home / "AppData/Local/info-hive")
        else:
            self.assertEqual(data_dir({"HOME": str(home)}), home / ".local/share/info-hive")
        with self.assertRaisesRegex(ValueError, "ホームディレクトリ"):
            data_dir({})

    def test_startup_lock_is_released_explicitly_when_body_fails(self):
        with mock.patch.object(X, "unlock", wraps=X.unlock) as unlock:
            with self.assertRaisesRegex(RuntimeError, "処理に失敗"), self.files.startup_lock(timeout=0) as fd:
                raise RuntimeError("処理に失敗")
            unlock.assert_called_once_with(fd)
        with self.files.startup_lock(timeout=0):
            self.assertTrue((self.data / "server.lock").is_file())
