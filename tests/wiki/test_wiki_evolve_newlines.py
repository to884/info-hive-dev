"""経験の記録（`wiki_evolve.py capture`）と実験の記録が、どの OS でも LF のバイト列で書かれること（wiki 0.19.2）。

0.19.1 までは、文字のモードで改行の指定なしに書いていたので、Windows では raw の JSON が CRLF になり、
`capture` が返す `sha256`（LF の文字列の値）とファイルのバイト列の SHA-256 が食い違った。

- Windows の文字のモード（書くときに `\\n` を `\\r\\n` に変える）を、どの OS でも真似て確かめる。
  `io.open` と `open` を包み、改行の指定がない文字のモードの書き込みに `newline='\\r\\n'` を渡す。
  直す前のコードは、この真似のもとで、Windows でなくても落ちる。
- 新しく記録したファイルが LF で、返した `sha256` がファイルのバイト列の SHA-256 と一致すること。
- 同じ内容の再試行、0.19.1 までの Windows が書いた CRLF の記録（書き直さず、実際のバイト列の値を返す）、
  違う内容の拒否。
- 実験の記録（`event()`）と、ファイル単位の提案（`propose`）の候補のファイルが、渡したバイト列のままであること。
- 本物の OS の上で CLI を動かし、標準出力の `sha256` がファイルの値と一致すること。

標準ライブラリだけで動く。

    python -X utf8 -B -m unittest tests/wiki/test_wiki_evolve_newlines.py -v
"""
from __future__ import annotations

import ast
import builtins
import contextlib
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "info-hive-wiki" / "skills" / "info-hive" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import wiki_evolve as e  # noqa: E402
import wiki_evolve_loop as loop  # noqa: E402
from wiki_text import format_frontmatter  # noqa: E402
from wiki_raw_roots import read_raw_roots  # noqa: E402

ENV = {**os.environ, "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"}
RECORD = {"id": "crlf-check", "task": "経験の記録", "outcome": "success", "verification": "ファイルのハッシュを比べた",
          "actions": ["capture を実行した", "複数行の\n値"], "model": "test", "tools": "test", "scope": "試験"}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@contextlib.contextmanager
def windows_text_mode():
    """Windows の文字のモードの書き込みを真似る。読むほうは変えない（Windows も読むときは改行をそろえる）。"""
    real = io.open

    def fake(file, mode="r", buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None):
        if "b" not in mode and newline is None and any(c in mode for c in "wxa+"):
            newline = "\r\n"
        return real(file, mode, buffering, encoding, errors, newline, closefd, opener)

    with mock.patch.object(io, "open", fake), mock.patch.object(builtins, "open", fake):
        yield


class EmulationTests(unittest.TestCase):
    """真似が効いていること。効いていなければ、ほかの試験は直す前のコードでも通ってしまう。"""

    def test_emulation_turns_lf_into_crlf(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.txt"
            with windows_text_mode():
                path.write_text("a\nb\n", encoding="utf-8")
                with open(Path(tmp) / "b.txt", "x", encoding="utf-8") as f:
                    f.write("a\n")
                with (Path(tmp) / "c.txt").open("x", encoding="utf-8") as f:
                    f.write("a\n")
                (Path(tmp) / "d.bin").write_bytes(b"a\n")
            self.assertEqual(path.read_bytes(), b"a\r\nb\r\n")
            self.assertEqual((Path(tmp) / "b.txt").read_bytes(), b"a\r\n")
            self.assertEqual((Path(tmp) / "c.txt").read_bytes(), b"a\r\n")
            self.assertEqual((Path(tmp) / "d.bin").read_bytes(), b"a\n")


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        self.raw = self.root / "raw"
        self.raw.mkdir()
        self.wiki = self.root / "wiki"
        self.wiki.mkdir()
        (self.wiki / "SCHEMA.md").write_text("", encoding="utf-8")
        self.record = self.root / "experience.json"
        self.record.write_bytes(e.encode(RECORD).encode("utf-8"))
        self.stored = self.raw / "experiences" / "crlf-check.json"
        self.lf = e.encode(RECORD).encode("utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def capture(self):
        with windows_text_mode():
            return e.capture(SimpleNamespace(wiki=self.wiki, raw=self.raw, record=self.record))

    def test_new_record_is_lf_and_hash_matches_file(self):
        result = self.capture()
        data = self.stored.read_bytes()
        self.assertNotIn(b"\r", data)
        self.assertEqual(data, self.lf)
        self.assertEqual(result["sha256"], sha256(data))
        self.assertEqual(result["raw"], str(self.stored))
        self.assertEqual(result["raw_ref"], self.stored.as_posix())
        self.assertEqual(result["raw_sha256"], sha256(data))
        self.assertEqual(read_raw_roots(self.wiki), ([self.raw], []))

    def test_capture_does_not_write_before_root_record(self):
        with mock.patch.object(e, "record_raw_root", side_effect=OSError("記録できない")):
            with self.assertRaisesRegex(OSError, "記録できない"):
                self.capture()
        self.assertFalse(self.stored.parent.exists())

    def test_capture_refuses_hardlinked_record(self):
        self.capture()
        alias = self.root / "old.json"
        os.link(self.stored, alias)
        with self.assertRaisesRegex(OSError, "hardlink"):
            self.capture()
        self.assertEqual(alias.read_bytes(), self.lf)

    def test_loop_adds_hash_to_previous_days_source_and_preserves_crlf(self):
        args = SimpleNamespace(wiki=self.wiki, raw=self.raw, id="test")
        row = {"task": "exercise", "question": "観察する", "passed": True, "output": {"events": []},
               "judge": {"reason": "結果を確認した"}, "checks": [], "model": "test", "runner": {}}
        name = "evolution-" + sha256(b"test:1:exercise")[:20]
        target = self.wiki / "sources" / f"{name}.md"
        target.parent.mkdir()
        old_raw = self.raw / "experiences" / f"{name}.json"
        legacy = (format_frontmatter({
            "title": f"学習時の観察 {name}", "type": "source", "tags": ["skill-evolution"],
            "created": "2025-01-01", "updated": "2025-01-02", "authors": ["評価ループ"],
            "raw": str(old_raw), "ingested": "2025-01-01",
        }) + "\n課題: 観察する\n\n結果: success\n\n結果を確認した\n").encode("utf-8").replace(b"\n", b"\r\n")
        target.write_bytes(legacy)
        loop.publish_learning(args, [row], {}, 1)
        sha_line = f'raw_sha256: "{sha256(old_raw.read_bytes())}"\r\n'.encode("utf-8")
        self.assertEqual(target.read_bytes(), legacy.replace(b"\r\n---\r\n", b"\r\n" + sha_line + b"---\r\n", 1))
        updated = target.read_bytes()
        loop.publish_learning(args, [row], {}, 1)
        self.assertEqual(target.read_bytes(), updated)

    def test_identical_retry_returns_same_hash_and_keeps_file(self):
        first = self.capture()
        before = self.stored.read_bytes()
        second = self.capture()
        self.assertEqual(self.stored.read_bytes(), before)
        self.assertEqual(second["sha256"], first["sha256"])
        self.assertEqual(second["sha256"], sha256(before))

    def test_legacy_crlf_record_is_accepted_unchanged_with_its_own_hash(self):
        """0.19.1 までの Windows が書いた記録。中身は同じなので受け入れ、書き直さず、実際のバイト列の値を返す。"""
        self.stored.parent.mkdir()
        legacy = self.lf.replace(b"\n", b"\r\n")
        self.stored.write_bytes(legacy)
        result = self.capture()
        self.assertEqual(self.stored.read_bytes(), legacy)
        self.assertEqual(result["sha256"], sha256(legacy))
        self.assertNotEqual(result["sha256"], sha256(self.lf))

    def test_different_content_is_rejected(self):
        self.capture()
        before = self.stored.read_bytes()
        changed = {**RECORD, "task": "別の作業"}
        self.record.write_bytes(e.encode(changed).encode("utf-8"))
        with self.assertRaisesRegex(ValueError, "変更できない"):
            self.capture()
        self.assertEqual(self.stored.read_bytes(), before)

    def test_different_content_in_crlf_is_rejected(self):
        self.stored.parent.mkdir()
        other = e.encode({**RECORD, "task": "別の作業"}).encode("utf-8").replace(b"\n", b"\r\n")
        self.stored.write_bytes(other)
        with self.assertRaisesRegex(ValueError, "変更できない"):
            self.capture()
        self.assertEqual(self.stored.read_bytes(), other)

    def test_other_line_ending_variants_are_rejected(self):
        """CRLF の記録として受け入れるのは、すべての改行を CRLF にしたものだけである。"""
        self.stored.parent.mkdir()
        variants = {
            "一部だけ CRLF": self.lf.replace(b"\n", b"\r\n", 1),
            "CR だけ": self.lf.replace(b"\n", b"\r"),
            "BOM つき": b"\xef\xbb\xbf" + self.lf,
            "末尾の改行なし": self.lf.rstrip(b"\n"),
        }
        for label, data in variants.items():
            with self.subTest(label):
                self.stored.write_bytes(data)
                with self.assertRaisesRegex(ValueError, "変更できない"):
                    self.capture()
                self.assertEqual(self.stored.read_bytes(), data)


class ExperimentRecordTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self):
        self._tmp.cleanup()

    def test_event_writes_lf(self):
        exp = self.root / "exp"
        exp.mkdir()
        with windows_text_mode():
            record = e.event(exp, "inputs", {"note": "複数行の\n値"})
        (path,) = exp.glob("inputs-*.json")
        data = path.read_bytes()
        self.assertNotIn(b"\r", data)
        self.assertEqual(data, e.encode(record).encode("utf-8"))

    def propose(self, root: Path, candidate_bytes: bytes):
        wiki, skill = root / "wiki", root / "skill"
        (wiki / "concepts").mkdir(parents=True)
        (wiki / "SCHEMA.md").write_bytes("# スキーマ\n".encode("utf-8"))
        (wiki / "concepts" / "教訓.md").write_bytes("---\ntype: concept\n---\n根拠\n".encode("utf-8"))
        (skill / "references").mkdir(parents=True)
        (skill / "SKILL.md").write_bytes(b"skill\n")
        (skill / "references" / "query.md").write_bytes(b"baseline\n")
        candidate = root / "candidate.md"
        candidate.write_bytes(candidate_bytes)
        args = SimpleNamespace(id="newline-check", skill=skill, target="references/query.md", candidate=candidate,
                               evidence=["concepts/教訓.md"], reason="改行を確かめる", wiki=wiki)
        with windows_text_mode(), e.locked(wiki) as state:
            e.propose(args, state)
        return wiki / ".evolution" / "newline-check"

    def test_file_candidate_keeps_given_bytes(self):
        for label, data in {"LF": "候補\n2 行目\n".encode("utf-8"), "CRLF": "候補\r\n2 行目\r\n".encode("utf-8")}.items():
            with self.subTest(label):
                exp = self.propose(self.root / label, data)
                stored = (exp / "candidate" / "references" / "query.md").read_bytes()
                self.assertEqual(stored, data)
                proposal = json.loads((exp / "proposal.json").read_text(encoding="utf-8"))
                self.assertEqual(proposal["candidate"]["references/query.md"]["sha256"], sha256(data))

    def test_line_ending_only_change_appears_in_diff(self):
        """ハッシュが変わる候補は、改行だけの違いでも、レビュー用の差分（change.diff）に出る。"""
        exp = self.propose(self.root, b"baseline\r\n")
        proposal = json.loads((exp / "proposal.json").read_text(encoding="utf-8"))
        self.assertNotEqual(proposal["candidate"]["references/query.md"], proposal["baseline"]["references/query.md"])
        diff = (exp / "change.diff").read_bytes()
        self.assertIn(b"-baseline\n", diff)
        self.assertIn(b"+baseline\r\n", diff)


class NoTextModeWritesTests(unittest.TestCase):
    """wiki_evolve.py は、ファイルをバイト列だけで書く（write_text も、文字のモードの open もない）。

    wiki_evolve_loop.py などの、ハッシュの契約のない書き込みは対象にしない。
    """

    def test_wiki_evolve_has_no_text_mode_writes(self):
        tree = ast.parse((SCRIPTS / "wiki_evolve.py").read_text(encoding="utf-8"))
        found = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", None)
            if name == "write_text":
                found.append((node.lineno, "write_text"))
            elif name in ("open", "fdopen"):
                args = node.args[1:] if name == "fdopen" or isinstance(node.func, ast.Name) else node.args
                # mode を省いた open は読むだけ（"r"）である。
                mode = next((k.value for k in node.keywords if k.arg == "mode"), args[0] if args else ast.Constant("r"))
                text = mode.value if isinstance(mode, ast.Constant) and isinstance(mode.value, str) else None
                if text is None:
                    found.append((node.lineno, "mode が定数でない"))
                elif "b" not in text and any(c in text for c in "wxa+"):
                    found.append((node.lineno, text))
        self.assertEqual(found, [])


class CliTests(unittest.TestCase):
    """本物の OS の文字のモードで CLI を動かす。Windows では、直す前のコードがここでも落ちる。"""

    def test_cli_capture_hash_matches_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            wiki, raw = root / "wiki", root / "raw"
            wiki.mkdir()
            raw.mkdir()
            (wiki / "SCHEMA.md").write_bytes("# スキーマ\n".encode("utf-8"))
            record = root / "experience.json"
            record.write_bytes(e.encode(RECORD).encode("utf-8"))
            done = subprocess.run([sys.executable, "-X", "utf8", str(SCRIPTS / "wiki_evolve.py"), "--wiki", str(wiki),
                                   "capture", "--raw", str(raw), "--record", str(record)],
                                  capture_output=True, encoding="utf-8", env=ENV, cwd=root)
            self.assertEqual(done.returncode, 0, done.stderr)
            result = json.loads(done.stdout)
            data = Path(result["raw"]).read_bytes()
            self.assertNotIn(b"\r", data)
            self.assertEqual(result["sha256"], sha256(data))


if __name__ == "__main__":
    unittest.main()
