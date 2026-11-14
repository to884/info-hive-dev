"""セッションの取り込み（wiki_session.py）の試験。設計は docs/plans/wiki-session-ingest-2026-11-14.md の「試験」の節。

- 抜き出しの性質: 思考の目印がどこにも出ない、返答の宛先が参照の実装と一致する、見出しとターン・フェンスと本文の
  あるターンが 1 対 1、環境（HOME、TZ、記録の置き場所）で raw が変わらない。対照として、3 版目の規則
  （attachment を境界にしない）と、除くものを並べる方式に差し替えると落ちる。
- ディスクの走査: inspect、show、decide、scan の前後で、会話の文と mark に渡した文字列がディスクに出ない。対照として、
  写しを書く実装に差し替えると落ちる。
- 縛り、raw の排他（対照は os.replace）、公開の前後の例外、リンクとルートの包含、読み取り専用と verify、自己検査、
  show の分け方、scan、locate と inspect。

記録は、手で作った JSONL（fixtures/session/basic.jsonl）と生成器（fixtures/session/gen_session.py）で作る。

実行（標準ライブラリと、プラグインに同梱の markdown-it-py だけで動く）:
    python -X utf8 -B -m unittest tests/wiki/test_wiki_session.py -v
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "info-hive-wiki/skills/info-hive/scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "session"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(FIXTURES))

import wiki_pages  # noqa: E402
import wiki_session as ws  # noqa: E402
from gen_session import NOSHOW, SECRET_EMAIL, SECRET_KEY, Builder, generate  # noqa: E402

NT = os.name == "nt"
BASIC = FIXTURES / "basic.jsonl"
TITLE = "索引の作り方"
HEADING_RE = re.compile(r"^## T(\d+) (ユーザー|Claude|印)（(.*)）$", re.MULTILINE)
INTERRUPTS = {"[Request interrupted by user]", "[Request interrupted by user for tool use]"}
GEN_CONTEXT_ATTACHMENTS = {"hook_success", "edited_text_file", "date_change"}


def force_rmtree(path) -> None:
    def onexc(func, p, _exc):
        os.chmod(p, stat.S_IWRITE | stat.S_IREAD)
        func(p)
    if os.path.lexists(path):
        shutil.rmtree(path, onexc=onexc)


def driver(patch: str = "") -> str:
    return (f"import sys; sys.path.insert(0, {str(SCRIPTS)!r}); import wiki_session as m\n{patch}\n"
            "sys.exit(m.main(sys.argv[1:]))")


def run(args, cwd=None, env=None, stdin: bytes | None = None, patch: str = "") -> subprocess.CompletedProcess:
    """wiki_session.py を別のプロセスで動かす。出力はバイト列で受ける。patch は main の前に実行する差し替え。"""
    base_env = {**os.environ, "PYTHONUTF8": "1"}
    base_env.pop("CLAUDE_CONFIG_DIR", None)
    return subprocess.run([sys.executable, "-X", "utf8", "-B", "-c", driver(patch), *map(str, args)],
                          cwd=cwd, env={**base_env, **(env or {})}, input=stdin, capture_output=True, timeout=120)


def make_wiki(base: Path) -> tuple[Path, Path]:
    wiki = base / "wiki"
    (wiki / "sources").mkdir(parents=True)
    (wiki / "SCHEMA.md").write_bytes("# スキーマ\n".encode("utf-8"))
    raw = base / "raw"
    raw.mkdir()
    return wiki, raw


def make_junction(link: Path, target: Path) -> bool:
    if NT:
        done = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], capture_output=True)
        return done.returncode == 0
    try:
        os.symlink(target, link, target_is_directory=True)
        return True
    except OSError:
        return False


def extract_file(path: Path, **opts) -> ws.Extract:
    o = ws.Options(**opts)
    return ws.extract(ws.read_range(path, o.before, ws.DEFAULT_MAX_BYTES), o)


def snapshot(*roots: Path) -> dict:
    out = {}
    for root in roots:
        for dirpath, _dirs, files in os.walk(root):
            for name in files:
                p = Path(dirpath) / name
                out[str(p)] = p.read_bytes()
    return out


# ---------------------------------------------------------------- 参照の実装（設計の 4 節の表を素朴に書いたもの）


def ref_kind(rec: dict) -> str:
    t = rec.get("type")
    if t == "user":
        origin = rec.get("origin") or {}
        content = rec["message"]["content"]
        if origin.get("kind") == "human" and not (rec.get("isMeta") or rec.get("isCompactSummary")
                                                  or rec.get("isSidechain")):
            return "H"
        if "origin" not in rec:
            text = content if isinstance(content, str) else (
                content[0].get("text") if isinstance(content, list) and len(content) == 1 else None)
            if text in INTERRUPTS:
                return "I"
        if isinstance(content, list) and content and all(b.get("type") == "tool_result" for b in content):
            return "T"
        return "X"
    if t == "assistant":
        return "X" if rec.get("isSidechain") or rec.get("isApiErrorMessage") else "A"
    if t == "attachment":
        att = rec["attachment"]
        if att["type"] == "queued_command":
            human = (att.get("origin") or {}).get("kind") == "human"
            return "H" if human and isinstance(att.get("prompt"), str) else "X"
        return "T" if att["type"] in GEN_CONTEXT_ATTACHMENTS and "origin" not in att else "X"
    if t == "system":
        return "T" if rec.get("subtype") in {"stop_hook_summary", "informational", "api_error"} else "X"
    return "X"


def ref_target(records: dict, uid: str):
    seen = set()
    parent = records[uid].get("parentUuid")
    while True:
        if parent is None or parent not in records:
            return None
        kind = ref_kind(records[parent])
        if kind in ("A", "T"):
            if parent in seen:
                return None
            seen.add(parent)
            parent = records[parent].get("parentUuid")
            continue
        return parent


def parse_turns(text: str) -> list:
    """raw を (番号, 話者, 見出しの括弧の中, 本文) の並びにする。"""
    matches = list(HEADING_RE.finditer(text))
    out = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out.append((int(m.group(1)), m.group(2), m.group(3), text[m.end():end]))
    return out


def reply_problems(builder: Builder, text: str) -> list:
    """各 A の札の入ったターンの「T<m> への返答」が、参照の実装の宛先と一致しないものを返す。"""
    records = {r["uuid"]: r for r in builder.records if "uuid" in r}
    turns = {n: (who, head, body) for n, who, head, body in parse_turns(text)}
    problems = []
    pairs = {}
    for uid, rec in records.items():
        if rec.get("type") != "assistant":
            continue
        blocks = rec["message"]["content"]
        tags = [m for b in blocks if b.get("type") == "text" for m in re.findall(r"返答 (A\d+) です", b["text"])]
        if not tags:
            continue
        tag = tags[0]
        where = [n for n, (who, _h, body) in turns.items() if who == "Claude" and f"返答 {tag} です" in body]
        if len(where) != 1:
            problems.append(f"{tag} が {len(where)} 個のターンにある")
            continue
        head = turns[where[0]][1]
        m = re.search(r"、(T(\d+)|不明)への返答$", head.replace(" への返答", "への返答"))
        reply = int(m.group(2)) if m and m.group(2) else None
        target = ref_target(records, uid)
        if target is None:
            if reply is None or turns.get(reply, ("", "", ""))[2].strip() != ws.MARK_UNKNOWN:
                problems.append(f"{tag}: 宛先は不明のはずが T{reply}")
            continue
        kind = ref_kind(records[target])
        if reply is None or reply not in turns:
            problems.append(f"{tag}: 宛先 {kind} が不明になった")
            continue
        who, _head, body = turns[reply]
        if kind == "H":
            src = records[target]
            raw_text = src["attachment"]["prompt"] if src["type"] == "attachment" else json.dumps(
                src["message"]["content"], ensure_ascii=False)
            htag = re.search(r"H\d+", raw_text).group(0)
            if who != "ユーザー" or not re.search(rf"\b{htag}\b", body):
                problems.append(f"{tag}: 宛先は {htag} のはずが T{reply}")
        else:
            if who != "印" or body.strip() == ws.MARK_UNKNOWN:
                problems.append(f"{tag}: 宛先 {kind} の印のはずが T{reply}")
        if kind != "H":
            pairs.setdefault(target, set()).add(reply)
    for target, replies in pairs.items():
        if len(replies) != 1:
            problems.append(f"同じ宛先 {target} が複数の印に分かれた")
    owners = {}
    for target, replies in pairs.items():
        for r in replies:
            owners.setdefault(r, set()).add(target)
    problems += [f"T{r} の印が複数の宛先を持つ" for r, ts in owners.items() if len(ts) != 1]
    return problems


def structure_problems(text: str, ex: ws.Extract) -> list:
    m = ws.FRONTMATTER_RE.match(text)
    body = text[m.end():]
    tokens = wiki_pages.new_parser().parse(body)
    h2 = [t for t in tokens if t.type == "heading_open" and t.tag == "h2"]
    others = [t for t in tokens if t.type == "heading_open" and t.tag != "h2"]
    fences = [t for t in tokens if t.type == "fence"]
    fenced = [t for t in ex.turns if t.fenced]
    out = []
    if len(h2) != len(ex.turns) or others:
        out.append(f"2 段目の見出し {len(h2)} とターン {len(ex.turns)} が合わない")
    if len(fences) != len(fenced):
        out.append(f"フェンス {len(fences)} と本文のあるターン {len(fenced)} が合わない")
    return out


class ExtractionPropertyTests(unittest.TestCase):
    SEEDS = range(30)

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(force_rmtree, self.tmp)

    def rendered(self, seed: int) -> tuple[Builder, ws.Extract, str]:
        b = generate(seed)
        path = self.tmp / f"{seed}.jsonl"
        path.write_bytes(b.to_bytes())
        ex = extract_file(path)
        return b, ex, ws.render(ex, "合成のセッション", [], []).decode("utf-8")

    def test_noshow_never_appears(self):
        for seed in self.SEEDS:
            with self.subTest(seed=seed):
                _b, _ex, text = self.rendered(seed)
                self.assertNotIn(NOSHOW, text)
                self.assertNotIn("NOSHOW", text)

    def test_reply_targets_match_reference(self):
        for seed in self.SEEDS:
            with self.subTest(seed=seed):
                b, _ex, text = self.rendered(seed)
                self.assertEqual(reply_problems(b, text), [])

    def test_headings_and_fences_are_one_to_one(self):
        for seed in self.SEEDS:
            with self.subTest(seed=seed):
                _b, ex, text = self.rendered(seed)
                self.assertEqual(structure_problems(text, ex), [])

    def test_generator_covers_the_listed_records(self):
        """生成器が、試験の節の挙げる記録を実際に混ぜていること（混ざっていなければ性質の試験が空回りする）。"""
        kinds = set()
        for seed in self.SEEDS:
            b = generate(seed)
            for line in b.lines:
                if line == b'{"broken": ':
                    kinds.add("broken")
                    continue
                r = json.loads(line)
                if "uuid" not in r:
                    kinds.add("uuidless:" + r["type"])
                elif r["type"] == "attachment":
                    a = r["attachment"]
                    kinds.add(f"att:{a['type']}:{(a.get('origin') or {}).get('kind')}:{type(a.get('prompt')).__name__}")
                elif r["type"] not in ("user", "assistant", "system"):
                    kinds.add("unknown_type")
                elif r.get("isMeta"):
                    kinds.add("meta:" + str((r.get("origin") or {}).get("kind")))
        for need in ("broken", "uuidless:never-seen-before", "att:future_thing:None:NoneType","att:queued_command:human:str",
                     "att:queued_command:task-notification:str", "att:queued_command:human:list", "unknown_type",
                     "meta:peer"):
            self.assertIn(need, kinds)

    def test_warnings_for_cycles_and_unknown_types(self):
        _b, ex, _text = self.rendered(3)
        codes = {w["code"] for w in ws.summarize_warnings(ex.warnings)}
        self.assertIn("reply_unresolved", codes)
        self.assertIn("unknown_uuidless_type", {w["code"] for s in self.SEEDS
                                                for w in ws.summarize_warnings(self.rendered(s)[1].warnings)})

    def test_same_bytes_across_environments(self):
        b = generate(7)
        first = self.tmp / "a" / "x.jsonl"
        second = self.tmp / "b" / "deep" / "x.jsonl"
        for p in (first, second):
            p.parent.mkdir(parents=True)
            p.write_bytes(b.to_bytes())
        args = ["show", "--title", "合成", "--session-id", b.session_id, "--max-chars", "10000000", "--transcript"]
        one = run(args + [first], env={"HOME": str(self.tmp / "h1"), "USERPROFILE": str(self.tmp / "h1"),
                                       "TZ": "Asia/Tokyo"})
        two = run(args + [second], env={"HOME": str(self.tmp / "h2"), "USERPROFILE": str(self.tmp / "h2"),
                                        "TZ": "America/New_York"}, cwd=self.tmp)
        self.assertEqual(one.returncode, 0, one.stderr.decode())
        self.assertEqual(one.stdout, two.stdout)
        self.assertEqual(one.stdout, ws.render(extract_file(first, session_id_arg=b.session_id), "合成", [], []))

    # ---- 対照

    def test_control_v3_rule_breaks_reply_targets(self):
        """3 版目の規則（attachment を境界にしない）に差し替えると、宛先が参照の実装と食い違う。"""
        real = ws.classify_record

        def v3(rec):
            return ws.T if rec.get("type") == "attachment" else real(rec)
        failed = 0
        with mock.patch.object(ws, "classify_record", v3):
            for seed in self.SEEDS:
                b, _ex, text = self.rendered(seed)
                failed += bool(reply_problems(b, text))
        self.assertGreater(failed, 0)

    def test_control_deny_list_leaks_noshow(self):
        """除くもの（thinking）だけを並べる方式に差し替えると、知らないブロックの中身が raw に出る。"""
        def deny(block):
            if not isinstance(block, dict) or block.get("type") == "thinking":
                return None
            if block.get("type") in ("tool_use", "server_tool_use"):
                return "tool"
            block.setdefault("text", json.dumps(block, ensure_ascii=False))
            return "text"
        leaked = 0
        with mock.patch.object(ws, "keep_assistant_block", deny):
            for seed in self.SEEDS:
                leaked += NOSHOW in self.rendered(seed)[2]
        self.assertGreater(leaked, 0)


class BasicFixtureTests(unittest.TestCase):
    def test_basic_render(self):
        ex = extract_file(BASIC, utc_offset="+09:00")
        text = ws.render(ex, TITLE, [], []).decode("utf-8")
        self.assertNotIn("NOSHOW", text)
        self.assertNotIn("taro@example.com", text)
        self.assertNotIn("taro", text.split("---", 2)[1])
        heads = [(n, who) for n, who, _h, _b in parse_turns(text)]
        self.assertEqual(heads, [(1, "ユーザー"), (2, "Claude"), (3, "印"), (4, "Claude"), (5, "ユーザー"), (6, "Claude")])
        self.assertIn("T3 への返答", text)
        self.assertIn(ws.MARK_TASK, text)
        self.assertIn("[ツール] Read ~\\work\\顧客A\\wiki\\index.md", text)
        self.assertIn("````text", text)  # 本文の ``` より長いフェンス
        self.assertTrue(text.endswith("```\n") and not text.endswith("\n\n"))
        self.assertNotIn("\r", text)
        self.assertIn("stripped_reminder", {w["code"] for w in ws.summarize_warnings(ex.warnings)})

    def test_keep_reminders_and_tools_none(self):
        ex = extract_file(BASIC, keep_reminders=True, tools="none")
        text = ws.render(ex, TITLE, [], []).decode("utf-8")
        self.assertIn("NOSHOW 差し込み", text)  # 引数で戻せる
        self.assertNotIn("[ツール]", text)

    def test_before_cuts_the_range(self):
        cut = "10000000-0000-4000-8000-00000000000a"
        ex = extract_file(BASIC, before=cut)
        data = BASIC.read_bytes()
        self.assertEqual(ex.source_bytes, data.index(cut.encode()) - data[:data.index(cut.encode())][::-1].index(b"\n"))
        self.assertEqual(len(ex.turns), 4)
        with self.assertRaises(ws.Fail):
            extract_file(BASIC, before="99999999-0000-4000-8000-000000000000")

    def test_unterminated_last_line_is_not_read(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(force_rmtree, tmp)
        p = tmp / "x.jsonl"
        p.write_bytes(BASIC.read_bytes() + b'{"type":"user","uuid":"u"')
        self.assertEqual(extract_file(p).source_sha256, hashlib.sha256(BASIC.read_bytes()).hexdigest())


class CliCase(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp())
        self.addCleanup(force_rmtree, self.base)
        self.outside = Path(tempfile.mkdtemp())
        self.addCleanup(force_rmtree, self.outside)
        self.wiki, self.raw = make_wiki(self.base)
        self.transcript = self.outside / "5f1c2d3e-aaaa-4bbb-8ccc-0123456789ab.jsonl"
        shutil.copyfile(BASIC, self.transcript)

    def ok(self, args, code=0, **kw):
        done = run(args, **kw)
        self.assertEqual(done.returncode, code, done.stderr.decode("utf-8", "replace"))
        return done

    def common(self, transcript=None):
        return ["--transcript", transcript or self.transcript, "--utc-offset", "+09:00"]

    def init(self, slug="会話", transcript=None) -> Path:
        done = self.ok(["decide", "init", *self.common(transcript), "--wiki", self.wiki, "--slug", slug, "--json"])
        return Path(json.loads(done.stdout)["decisions"])

    def meta(self, dec, title=TITLE, slug="会話", transcript=None) -> dict:
        done = self.ok(["show", *self.common(transcript), "--title", title, "--decisions", dec, "--slug", slug,
                        "--meta", "--json"])
        return json.loads(done.stdout)

    def write(self, dec, sha, title=TITLE, slug="会話", code=0, transcript=None, patch="", raw=None, wiki=None):
        return self.ok(["write", *self.common(transcript), "--title", title, "--decisions", dec,
                        "--wiki", wiki or self.wiki, "--raw-root", raw or self.raw, "--slug", slug,
                        "--expect-sha256", sha, "--json"], code=code, patch=patch)


class DiskScanTests(CliCase):
    """inspect、show、decide、scan は、会話の文と mark に渡した文字列をディスクに書かない。"""

    BODY = "索引の作り方を教えて".encode("utf-8")
    MARKED = "顧客A"

    def flow(self, patch=""):
        work = self.base / "work"
        work.mkdir(exist_ok=True)
        before = snapshot(self.base)
        self.ok(["inspect", *self.common(), "--wiki", self.wiki, "--raw-root", self.raw, "--slug", "会話", "--json"],
                cwd=work, patch=patch)
        self.ok(["show", *self.common(), "--title", TITLE], cwd=work, patch=patch)
        dec = self.init()
        self.ok(["decide", "mark", *self.common(), "--decisions", dec, "--text", self.MARKED, "--all-turns"],
                cwd=work, patch=patch)
        self.ok(["decide", "drop", *self.common(), "--decisions", dec, "--turn", "T4"], cwd=work, patch=patch)
        self.ok(["show", *self.common(), "--title", TITLE, "--decisions", dec, "--meta"], cwd=work, patch=patch)
        self.ok(["scan", *self.common(), "--decisions", dec], cwd=work, patch=patch,
                stdin="要約の文。索引を作った。\n".encode("utf-8"))
        after = snapshot(self.base)
        return before, after, dec

    def leaks(self, files: dict) -> list:
        """中身とパスの両方を調べる（ファイルの名前に出ても、ディスクに出たことになる）。"""
        return [p for p, data in files.items()
                if self.BODY in data or self.MARKED.encode("utf-8") in data or self.MARKED in p]

    def test_nothing_reaches_the_disk(self):
        _before, after, dec = self.flow()
        self.assertEqual(self.leaks(after), [])
        data = dec.read_bytes()
        self.assertNotIn(self.MARKED.encode("utf-8"), data)
        self.assertEqual(set(json.loads(data)), {"format", "extracted_by", "session_id", "source_sha256", "source_bytes",
                                                 "cut_before", "options", "base_sha256", "spans", "drop"})

    def test_control_copy_writing_implementation_is_caught(self):
        """写しを書く実装に差し替えると、走査が見つける。"""
        patch = ("_r = m.render_parts\n"
                 "def _copy(*a, **k):\n"
                 "    parts = _r(*a, **k)\n"
                 "    open('copy.md', 'w', encoding='utf-8').write(''.join(p for _n, p in parts))\n"
                 "    return parts\n"
                 "m.render_parts = _copy")
        _before, after, _dec = self.flow(patch)
        self.assertTrue(self.leaks(after))


class BindingTests(CliCase):
    def test_write_refuses_after_the_range_changes(self):
        dec = self.init()
        sha = self.meta(dec)["render_sha256"]
        data = self.transcript.read_bytes().replace("ありがとう".encode(), "ありがたい".encode())
        self.transcript.write_bytes(data)
        done = self.write(dec, sha, code=1)
        self.assertIn("source_sha256", done.stderr.decode())
        self.assertFalse(list(self.raw.iterdir()))

    def test_write_refuses_after_the_decisions_change(self):
        dec = self.init()
        sha = self.meta(dec)["render_sha256"]
        d = json.loads(dec.read_bytes())
        d["drop"] = [2]
        dec.write_bytes(json.dumps(d).encode())
        self.write(dec, sha, code=1)
        d["drop"] = []
        d["base_sha256"] = "0" * 64
        dec.write_bytes(json.dumps(d).encode())
        self.assertIn("base_sha256", self.write(dec, sha, code=1).stderr.decode())
        self.assertFalse(list(self.raw.iterdir()))

    def test_mark_refuses_ambiguous_and_missing_text(self):
        dec = self.init()
        self.assertIn("か所に一致", self.ok(["decide", "mark", *self.common(), "--decisions", dec, "--target", "T6",
                                          "--text", "し"], code=1).stderr.decode())
        self.ok(["decide", "mark", *self.common(), "--decisions", dec, "--target", "T6", "--text", "存在しない"], code=1)
        self.ok(["decide", "mark", *self.common(), "--decisions", dec, "--target", "T99", "--text", "x"], code=1)
        self.ok(["decide", "mark", *self.common(), "--decisions", dec, "--target", "T6", "--text", "し", "--nth", "2"])
        self.assertEqual(len(json.loads(dec.read_bytes())["spans"]), 1)

    def test_overlapping_matches_are_ambiguous(self):
        """重なる一致も数える（前提: 一致の長さだけ進めても、すべての一致を数えられる）。"""
        b = Builder(session_id="3a1c2d3e-aaaa-4bbb-8ccc-0123456789ab")
        b.human("abababa の件")
        b.text("了解")
        p = self.outside / f"{b.session_id}.jsonl"
        p.write_bytes(b.to_bytes())
        dec = self.init(transcript=p)
        args = ["decide", "mark", *self.common(p), "--decisions", dec, "--target", "T1", "--text", "ababa"]
        self.ok(args, code=1)
        self.ok(args + ["--nth", "2"])
        self.assertEqual(json.loads(dec.read_bytes())["spans"], [{"target": "T1", "start": 2, "end": 7}])

    def test_title_with_hidden_text_is_refused(self):
        dec = self.init()
        self.ok(["decide", "mark", *self.common(), "--decisions", dec, "--text", "顧客A", "--all-turns"])
        sha = self.meta(dec)["render_sha256"]
        for title in ("顧客Aとの相談", "顧客Ａとの相談", "連絡は taro@example.com"):
            with self.subTest(title=title):
                self.ok(["show", *self.common(), "--title", title, "--decisions", dec, "--meta"], code=1)
                self.write(dec, sha, title=title, code=1)
        self.ok(["show", *self.common(), "--title", TITLE, "--decisions", dec, "--slug", "顧客A-相談", "--meta"], code=1)
        self.assertFalse(list(self.raw.iterdir()))

    def test_slug_with_a_secret_is_refused_before_writing(self):
        """スラッグは、ディスクに書く前に検査する（前提: 最後の確認で検査すれば、保存先にも出ない）。"""
        before = snapshot(self.base)
        self.ok(["decide", "init", *self.common(), "--wiki", self.wiki, "--slug", "sk-abcdefghijklmnopqrst"], code=1)
        self.ok(["decide", "init", *self.common(), "--wiki", self.wiki, "--slug", "taro@example.com"], code=1)
        self.assertEqual(snapshot(self.base), before)

    def test_options_come_from_the_decisions(self):
        dec = self.init()
        done = self.ok(["show", "--transcript", self.transcript, "--title", TITLE, "--decisions", dec, "--meta",
                        "--json"])
        self.assertEqual(json.loads(done.stdout)["render_sha256"], self.meta(dec)["render_sha256"])
        self.ok(["show", "--transcript", self.transcript, "--title", TITLE, "--decisions", dec, "--meta",
                 "--utc-offset", "+00:00"], code=1)

    def test_marked_text_is_hidden_in_cwd_and_turns(self):
        dec = self.init()
        self.ok(["decide", "mark", *self.common(), "--decisions", dec, "--text", "顧客A", "--all-turns"])
        out = self.ok(["show", *self.common(), "--title", TITLE, "--decisions", dec, "--max-chars", "100000"]).stdout
        self.assertNotIn("顧客A".encode(), out)
        self.assertIn('cwd: "~\\\\work\\\\［伏せ字］"'.encode(), out)
        meta = self.meta(dec)
        self.assertGreaterEqual(meta["manual_redactions"], 4)


class RawExclusiveTests(CliCase):
    def race(self, publish, reps=200) -> tuple[int, int]:
        """2 つのスレッドが違うバイト列を同じ行き先に同時に置く。返り値は（1 つだけが置けた回数, 上書きが起きた回数）。"""
        single = overwritten = 0
        for i in range(reps):
            d = self.base / "race" / str(i)
            d.mkdir(parents=True)
            target = d / "x.md"
            tmps = [d / "a.tmp", d / "b.tmp"]
            for j, t in enumerate(tmps):
                t.write_bytes(f"版 {j}\n".encode())
            barrier = threading.Barrier(2)
            won = [False, False]

            def go(j):
                barrier.wait()
                try:
                    publish(tmps[j], target)
                    won[j] = True
                except (FileExistsError, PermissionError):
                    pass
            threads = [threading.Thread(target=go, args=(j,)) for j in range(2)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            if sum(won) == 1 and target.read_bytes() == f"版 {won.index(True)}\n".encode():
                single += 1
            if sum(won) == 2:
                overwritten += 1
        return single, overwritten

    def test_only_one_writer_wins(self):
        single, overwritten = self.race(ws.publish_exclusive)
        self.assertEqual((single, overwritten), (200, 0))

    def test_control_os_replace_overwrites(self):
        _single, overwritten = self.race(os.replace)
        self.assertGreater(overwritten, 0)

    def process_race(self, mode: str, reps: int = 200) -> tuple[list, list]:
        """2 つのプロセスが、回ごとに足並みをそろえて、違うバイト列を同じスラッグに write_raw() で書く。"""
        worker = FIXTURES / "race_worker.py"
        procs = [subprocess.Popen([sys.executable, "-X", "utf8", "-B", str(worker), str(SCRIPTS), str(self.base),
                                   str(self.wiki), str(self.raw), str(who), str(reps), mode],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE) for who in (0, 1)]
        outs = [p.communicate(timeout=600) for p in procs]
        for p, (out, err) in zip(procs, outs):
            self.assertEqual(p.returncode, 0, err.decode("utf-8", "replace"))
        return [json.loads(out) for out, _err in outs]

    def test_two_processes_200_times(self):
        """設計の試験: 2 つのプロセスが違うバイト列を同じスラッグに同時に書くことを 200 回繰り返し、毎回 1 つだけが
        created になり、raw がその側のバイト列と一致する。"""
        a, b = self.process_race("exclusive")
        for i, pair in enumerate(zip(a, b)):
            self.assertEqual(sorted(pair), ["conflict", "created"], f"{i} 回目: {pair}")
            who = pair.index("created")
            self.assertEqual((self.raw / f"r{i}.md").read_bytes(), f"版 {who} の {i}\n".encode("utf-8"))
        self.assertEqual(sorted(p.name for p in self.raw.iterdir() if p.name.endswith(".tmp")), [])

    def test_control_process_race_with_os_replace_overwrites(self):
        a, b = self.process_race("replace", reps=60)
        self.assertGreater(sum(1 for pair in zip(a, b) if list(pair) == ["created", "created"]), 0)

    def test_access_denied_during_a_concurrent_rename_becomes_conflict(self):
        """Windows で、相手の名前の変更の最中に返るアクセスの拒否は、行き先を確かめ直して conflict にする。"""
        target = self.raw / "競争.md"

        def busy(tmp, dst):
            dst.write_bytes("相手の版\n".encode("utf-8"))
            raise PermissionError(13, "アクセスが拒否されました")
        with mock.patch.object(ws, "publish_exclusive", busy), mock.patch.object(ws.os, "name", "nt"):
            state, path = ws.write_raw(self.wiki, self.raw, "競争", "自分の版\n".encode("utf-8"))
        self.assertEqual((state, path), ("conflict", target))
        self.assertEqual(sorted(p.name for p in self.raw.iterdir()), ["競争.md"])

        def denied(tmp, dst):
            raise PermissionError(13, "アクセスが拒否されました")
        with mock.patch.object(ws, "publish_exclusive", denied), mock.patch.object(ws.time, "sleep"):
            with self.assertRaises(ws.Fail):
                ws.write_raw(self.wiki, self.raw, "書けない", b"x\n")
        self.assertEqual(sorted(p.name for p in self.raw.iterdir()), ["競争.md"])

    def test_two_processes_one_created(self):
        for i in range(3):
            slug = f"同時-{i}"
            decs = [self.init(slug), self.init(slug)]
            titles = ["題名その一", "題名その二"]
            shas = [self.meta(d, t, slug)["render_sha256"] for d, t in zip(decs, titles)]
            procs = [subprocess.Popen([sys.executable, "-X", "utf8", "-B", "-c", driver(), "write", *map(str, self.common()),
                                       "--title", t, "--decisions", str(d), "--wiki", str(self.wiki), "--raw-root",
                                       str(self.raw), "--slug", slug, "--expect-sha256", s, "--json"],
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                     for d, t, s in zip(decs, titles, shas)]
            results = [(p.wait(timeout=120), json.loads(p.stdout.read() or b"{}")) for p in procs]
            for p in procs:
                p.stdout.close()
                p.stderr.close()
            states = sorted(r[1].get("raw_state") for r in results)
            self.assertEqual(states, ["conflict", "created"], results)
            winner = next(r[1] for r in results if r[1]["raw_state"] == "created")
            self.assertEqual(hashlib.sha256((self.raw / f"{slug}.md").read_bytes()).hexdigest(),
                             winner["render_sha256"])

    def test_exception_before_publish_leaves_nothing(self):
        dec = self.init()
        sha = self.meta(dec)["render_sha256"]
        self.write(dec, sha, code=1, patch="def _boom():\n    raise RuntimeError('止める')\nm.before_publish = _boom")
        self.assertEqual(list(self.raw.iterdir()), [])

    def test_exception_after_publish_then_identical(self):
        dec = self.init()
        sha = self.meta(dec)["render_sha256"]
        self.write(dec, sha, code=1, patch="def _boom():\n    raise RuntimeError('止める')\nm.after_publish = _boom")
        self.assertEqual([p.name for p in self.raw.iterdir()], ["会話.md"])
        done = self.write(dec, sha)
        self.assertEqual(json.loads(done.stdout)["raw_state"], "identical")
        self.assertTrue(ws.is_read_only(self.raw / "会話.md"))

    def test_conflict_and_slug_taken(self):
        dec = self.init()
        sha = self.meta(dec)["render_sha256"]
        self.assertEqual(json.loads(self.write(dec, sha).stdout)["raw_state"], "created")
        dec2 = self.init()
        sha2 = self.meta(dec2, "別の題名")["render_sha256"]
        self.assertEqual(json.loads(self.write(dec2, sha2, "別の題名", code=3).stdout)["raw_state"], "conflict")
        (self.wiki / "sources" / "使用済み.md").write_bytes(b"x\n")
        dec3 = self.init("使用済み")
        sha3 = self.meta(dec3, slug="使用済み")["render_sha256"]
        self.assertEqual(json.loads(self.write(dec3, sha3, slug="使用済み", code=3).stdout)["raw_state"], "slug_taken")

    def test_hash_mismatch_writes_nothing(self):
        dec = self.init()
        self.write(dec, "0" * 64, code=1)
        self.assertEqual(list(self.raw.iterdir()), [])

    def test_link_raw_root_is_refused(self):
        real = self.base / "real"
        real.mkdir()
        link = self.base / "link"
        if not make_junction(link, real):
            self.skipTest("リンクを作れない")
        dec = self.init()
        sha = self.meta(dec)["render_sha256"]
        self.write(dec, sha, code=1, raw=link)
        (real / "raw").mkdir()
        self.write(dec, sha, code=1, raw=link / "raw")
        self.assertEqual(list(real.rglob("*.md")), [])

    def test_link_target_is_refused_even_if_identical(self):
        dec = self.init()
        sha = self.meta(dec)["render_sha256"]
        self.write(dec, sha)
        data = (self.raw / "会話.md").read_bytes()
        other = self.base / "other"
        other.mkdir()
        (other / "copy.md").write_bytes(data)
        target = self.raw / "会話.md"
        os.chmod(target, stat.S_IWRITE | stat.S_IREAD)
        target.unlink()
        try:
            os.symlink(other / "copy.md", target)
        except OSError:
            self.skipTest("シンボリックリンクを作れない")
        self.write(dec, sha, code=1)

    def test_overlapping_roots_are_refused(self):
        dec = self.init()
        sha = self.meta(dec)["render_sha256"]
        self.write(dec, sha, code=1, raw=self.wiki / "sources")
        self.assertEqual(list((self.wiki / "sources").iterdir()), [])
        inner = self.raw / "wiki"
        (inner / "sources").mkdir(parents=True)
        (inner / "SCHEMA.md").write_bytes(b"# s\n")
        dec2 = self.init()
        sha2 = self.meta(dec2)["render_sha256"]
        self.write(dec2, sha2, code=1, wiki=inner)
        self.assertEqual(sorted(p.name for p in self.raw.iterdir()), ["wiki"])

    def test_roots_on_different_drives_are_not_overlapping(self):
        """ドライブの違うパスは commonpath が ValueError を上げる（前提: 絶対パスどうしなら比べられる）。"""
        self.assertFalse(ws.path_within("D:\\raw", "C:\\project\\wiki") if NT else ws.path_within("/a", "/b"))
        with mock.patch("os.path.commonpath", side_effect=ValueError("Paths don't have the same drive")):
            self.assertFalse(ws.path_within("D:\\raw", "C:\\project\\wiki"))
            ws.check_destination(self.wiki, self.raw, self.raw / "x.md")

    def test_missing_raw_root_is_not_created(self):
        dec = self.init()
        sha = self.meta(dec)["render_sha256"]
        self.write(dec, sha, code=1, raw=self.base / "ない")
        self.assertFalse((self.base / "ない").exists())


class ReadOnlyVerifyTests(CliCase):
    def written(self):
        dec = self.init()
        sha = self.meta(dec)["render_sha256"]
        out = json.loads(self.write(dec, sha).stdout)
        return sha, Path(out["raw_path"]), out

    def verify(self, sha, code=0):
        return json.loads(self.ok(["verify", "--raw-root", self.raw, "--slug", "会話", "--expect-sha256", sha,
                                   "--json"], code=code).stdout)

    def test_write_makes_raw_read_only_and_verify_passes(self):
        sha, path, out = self.written()
        self.assertTrue(ws.is_read_only(path))
        self.assertEqual(out["raw_ref"], "raw/会話.md")
        self.assertEqual(self.verify(sha), {"raw_path": str(path), "sha256_matches": True, "read_only": True})
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), sha)

    def test_clearing_read_only_fails_verify(self):
        sha, path, _out = self.written()
        os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
        self.assertEqual(self.verify(sha, code=1)["read_only"], False)

    def test_replacement_through_an_alias(self):
        """wiki の中の別名（Windows はジャンクション、POSIX はシンボリックリンク）を経由して、Claude Code の
        Write と同じく一時ファイルからの名前の変更で raw を置き換える。Windows では読み取り専用で失敗し、
        POSIX では置き換わるが verify が見つける。"""
        sha, path, _out = self.written()
        alias = self.wiki / "indexes"
        if not make_junction(alias, self.raw):
            self.skipTest("別名を作れない")
        tmp = alias / "会話.md.tmp.1"
        tmp.write_bytes(b"# \xe6\x9b\xb8\xe3\x81\x8d\xe6\x8f\x9b\xe3\x81\x88\n")
        try:
            os.replace(tmp, alias / "会話.md")
            replaced = True
        except PermissionError:
            replaced = False
            tmp.unlink()
        if NT:
            self.assertFalse(replaced)
            self.assertEqual(self.verify(sha)["sha256_matches"], True)
        else:
            self.assertTrue(replaced)
            self.assertEqual(self.verify(sha, code=1)["sha256_matches"], False)

    def test_verify_refuses_missing_raw(self):
        sha, _path, _out = self.written()
        self.ok(["verify", "--raw-root", self.raw, "--slug", "ない", "--expect-sha256", sha], code=1)

    def test_verify_refuses_link(self):
        """raw の名前がリンクなら、指す先が同じバイト列で読み取り専用でも、照らさずに拒む。"""
        sha, path, _out = self.written()
        other = self.base / "other"
        other.mkdir()
        shutil.copyfile(path, other / "copy.md")
        ws.make_read_only(other / "copy.md")
        link = self.raw / "別名.md"
        try:
            os.symlink(other / "copy.md", link)
        except OSError:
            self.skipTest("シンボリックリンクを作れない")
        self.ok(["verify", "--raw-root", self.raw, "--slug", "別名", "--expect-sha256", sha], code=1)


class SelfCheckTests(CliCase):
    def build(self, fill) -> Path:
        b = Builder(session_id="7a1c2d3e-aaaa-4bbb-8ccc-0123456789ab")
        fill(b)
        p = self.outside / f"{b.session_id}.jsonl"
        p.write_bytes(b.to_bytes())
        return p

    def test_dropping_the_only_human_turn(self):
        p = self.build(lambda b: (b.human("ひとつだけの発言"), b.text("返答")))
        dec = self.init(transcript=p)
        self.ok(["decide", "drop", *self.common(p), "--decisions", dec, "--turn", "T1"])
        self.ok(["decide", "drop", *self.common(p), "--decisions", dec, "--turn", "T2"])
        out = self.ok(["show", *self.common(p), "--title", TITLE, "--decisions", dec]).stdout.decode()
        self.assertEqual(out.count(ws.MARK_DROPPED), 2)
        self.assertNotIn("ひとつだけ", out)

    def test_only_marker_turns(self):
        def fill(b):
            b.human("<system-reminder>差し込みだけ</system-reminder>")
            b.queued("通知", "task-notification")
            b.text("通知への返答")
            b.interrupt()
        p = self.build(fill)
        ex = extract_file(p)
        self.assertEqual([t.kind for t in ex.turns], ["marker", "marker", "claude", "marker"])
        text = ws.render(ex, TITLE, [], []).decode()
        self.assertIn(ws.MARK_EMPTY_HUMAN, text)
        self.assertIn(ws.MARK_INTERRUPT, text)

    def test_self_check_rejects_broken_structure(self):
        ex = extract_file(BASIC)
        fields = ws.frontmatter_fields(ex, TITLE, [], [])
        turns = ws.rendered_turns(ex, [], [])
        good = ws.render(ex, TITLE, [], []).decode()
        ws.self_check(good, fields, turns)
        for bad in (good.replace("````text", "```text", 1), good.replace("## T2", "# T2", 1),
                    good + "\n## T7 ユーザー（x）\n", good.replace("（バックグラウンド", "- （バックグラウンド", 1)):
            with self.assertRaises(ws.RenderError):
                ws.self_check(bad, fields, turns)

    def test_backticks_and_odd_text_stay_inside_the_fence(self):
        nasty = "```\n## T9 ユーザー（偽）\n````\n---\ntitle: x\n<script>\n" + chr(0) + "\r\n末尾"
        p = self.build(lambda b: (b.human(nasty), b.text("`````\n## 偽\n")))
        ex = extract_file(p)
        text = ws.render(ex, TITLE, [], []).decode()
        # 偽の見出しはフェンスの中にあり、パーサーが見出しとして読むのは 2 つだけ
        self.assertEqual(structure_problems(text, ex), [])
        fences = [t.content for t in wiki_pages.new_parser().parse(ws.FRONTMATTER_RE.sub("", text, 1))
                  if t.type == "fence"]
        self.assertIn("## T9 ユーザー（偽）", fences[0])
        self.assertIn(chr(0xFFFD), fences[0])
        self.assertNotIn("\r", text)


class ShowSplitTests(CliCase):
    def test_from_chain_reassembles_the_raw(self):
        long_text = ("長い本文の行。`code` と ```` を含む。\n" * 3000)
        p = self.outside / "8a1c2d3e-aaaa-4bbb-8ccc-0123456789ab.jsonl"
        b = Builder(session_id="8a1c2d3e-aaaa-4bbb-8ccc-0123456789ab")
        b.human("短い発言")
        b.text(long_text)
        b.human("次の発言")
        p.write_bytes(b.to_bytes())
        expected = ws.render(extract_file(p, utc_offset="+09:00"), TITLE, [], [])
        self.assertGreater(len(long_text), 7000 * 5)
        chunks, frm, calls = [], None, 0
        while True:
            args = ["show", *self.common(p), "--title", TITLE, "--max-chars", "7000"] + (["--from", frm] if frm else [])
            done = self.ok(args)
            self.assertNotIn("続き".encode(), done.stdout)
            chunks.append(done.stdout)
            m = re.search(r"--from (T\d+:\d+)", done.stderr.decode())
            calls += 1
            if not m:
                break
            frm = m.group(1)
        self.assertEqual(b"".join(chunks), expected)
        self.assertGreater(calls, 5)
        j = json.loads(self.ok(["show", *self.common(p), "--title", TITLE, "--max-chars", "7000", "--json"]).stdout)
        parts = ws.render_parts(extract_file(p, utc_offset="+09:00"), TITLE, [], [])
        self.assertEqual(j["next"], f"T2:{7000 - len(parts[0][1]) - len(parts[1][1])}")
        self.assertEqual(j["text"].encode("utf-8"), chunks[0])

    def test_turn_range(self):
        out = self.ok(["show", *self.common(), "--title", TITLE, "--turns", "T3-T4"]).stdout.decode()
        self.assertTrue(out.startswith("## T3 印"))
        self.assertIn("## T4 Claude", out)
        self.assertNotIn("## T5", out)
        self.ok(["show", *self.common(), "--title", TITLE, "--turns", "T3-T99"], code=1)


class ScanTests(CliCase):
    def scan(self, dec, text: str, *allow, transcript=None, code=None):
        args = ["scan", *self.common(transcript), "--decisions", dec, "--json"]
        for a in allow:
            args += ["--allow", a]
        done = run(args, stdin=text.encode("utf-8"))
        if code is not None:
            self.assertEqual(done.returncode, code, done.stderr.decode())
        return done, json.loads(done.stdout) if done.stdout else None

    def secret_transcript(self, text) -> Path:
        b = Builder(session_id="9a1c2d3e-aaaa-4bbb-8ccc-0123456789ab", cwd="C:\\Users\\alice\\proj")
        b.human(text)
        b.text("了解です")
        p = self.outside / f"{b.session_id}.jsonl"
        p.write_bytes(b.to_bytes())
        return p

    def test_manual_strings_are_found_without_printing_them(self):
        dec = self.init()
        self.ok(["decide", "mark", *self.common(), "--decisions", dec, "--text", "顧客A", "--all-turns"])
        self.ok(["decide", "mark", *self.common(), "--decisions", dec, "--target", "T2", "--text", "index.md", "--nth", "1"])
        page = "# 要約\n\n顧客A の件。\n全角の顧客Ａ。\n大文字の INDEX.MD。\n問題のない行。\n"
        done, result = self.scan(dec, page, code=1)
        rules = [(f["line"], f["rule"]) for f in result["findings"]]
        self.assertEqual(rules, [(3, "manual"), (4, "manual"), (5, "manual")])
        self.assertEqual(result["findings"][0]["column"], 1)
        for s in ("顧客A", "顧客Ａ", "INDEX.MD", "index.md"):
            self.assertNotIn(s.encode(), done.stdout)
        self.scan(dec, "# 要約\n\n問題のない行。\n", code=0)

    def test_auto_redacted_strings_are_found(self):
        p = self.secret_transcript(f"連絡先は {SECRET_EMAIL}、鍵は {SECRET_KEY}")
        dec = self.init(transcript=p)
        for text, rule in ((f"メールは {SECRET_EMAIL} です", "auto_email"), ("名前は alice.smith です", "auto_email"),
                           (f"鍵は {SECRET_KEY}", "auto_secret"), ("ALICE.SMITH の件", "auto_email")):
            with self.subTest(text=text):
                done, result = self.scan(dec, text, transcript=p, code=1)
                self.assertIn(rule, {f["rule"] for f in result["findings"]})
                self.assertNotIn(b"alice", done.stdout.lower())
                self.assertNotIn(SECRET_KEY.encode(), done.stdout)

    def test_short_local_part_is_skipped_and_frontmatter_passes(self):
        p = self.secret_transcript("連絡は a@example.com へ")
        dec = self.init(transcript=p)
        page = ('---\ntype: source\ntitle: "会話"\nraw: "raw/会話.md"\ntags: [session, wiki]\n'
                'session_id: "9a1c2d3e-aaaa-4bbb-8ccc-0123456789ab"\n---\n\n# 会話\n\nあいさつをした。\n')
        _done, result = self.scan(dec, page, transcript=p, code=0)
        self.assertEqual(result, {"findings": [], "skipped_short": 1})
        self.scan(dec, "連絡は a@example.com へ", transcript=p, code=1)

    def test_allow_excludes_the_raw_ref(self):
        p = self.secret_transcript("相談です")
        dec = self.init(transcript=p)
        ref = "C:/Users/alice/proj/raw/会話.md"
        page = f'raw: "{ref}"\n'
        _done, result = self.scan(dec, page, transcript=p, code=1)
        self.assertEqual({f["rule"] for f in result["findings"]}, {"auto_home", "pattern_home"})
        self.scan(dec, page, ref, transcript=p, code=0)
        self.scan(dec, page + "alice の家\n", ref, transcript=p, code=1)

    def test_short_manual_string_is_found(self):
        p = self.secret_transcript("太郎さんに聞いた")
        dec = self.init(transcript=p)
        self.ok(["decide", "mark", *self.common(p), "--decisions", dec, "--target", "T1", "--text", "太郎"])
        self.scan(dec, "太郎の話", transcript=p, code=1)

    # ---- 1 回目のレビューで崩れた前提（docs/agent-runs/2026-11-14-wiki-session-ingest/impl-review-1.md）

    def mark(self, p, dec, text, *extra):
        self.ok(["decide", "mark", *self.common(p), "--decisions", dec, "--target", "T1", "--text", text, *extra])

    def test_each_marked_string_is_kept_after_merging(self):
        """隣り合う 2 つの指定を区間でまとめても、指定ごとの文字列を探す（前提: まとめても失われない）。"""
        p = self.secret_transcript("顧客A顧客Bの相談")
        dec = self.init(transcript=p)
        self.mark(p, dec, "顧客A")
        self.mark(p, dec, "顧客B")
        self.assertEqual(self.meta(dec, transcript=p)["manual_redactions"], 1)
        for page in ("顧客A の件", "顧客B の件"):
            with self.subTest(page=page):
                self.scan(dec, page, transcript=p, code=1)
        self.ok(["show", *self.common(p), "--title", "顧客A review", "--decisions", dec, "--meta"], code=1)

    def test_nfkc_is_applied_to_whole_strings(self):
        """半角カナと濁点は、文字列の全体に NFKC をかけたときに合成される（前提: 1 文字ずつかけてよい）。"""
        p = self.secret_transcript("ガンダム社の相談")
        dec = self.init(transcript=p)
        self.mark(p, dec, "ガンダム社")
        _done, result = self.scan(dec, "まえがき\nこれは ｶﾞﾝﾀﾞﾑ社 の件", transcript=p, code=1)
        self.assertEqual(result["findings"], [{"line": 2, "column": 5, "rule": "manual"}])
        self.ok(["show", *self.common(p), "--title", "ｶﾞﾝﾀﾞﾑ社 review", "--decisions", dec, "--meta"], code=1)

    def test_marked_text_with_newline_is_found(self):
        """改行を含む伏せた文字列を、文の全体の上で探す（前提: 伏せる文字列は 1 行に収まる）。"""
        p = self.secret_transcript("顧客A\n顧客B\nほかの話")
        dec = self.init(transcript=p)
        self.mark(p, dec, "顧客A\n顧客B")
        _done, result = self.scan(dec, "前置き\n顧客A\n顧客B\n", transcript=p, code=1)
        self.assertEqual(result["findings"], [{"line": 2, "column": 1, "rule": "manual"}])
        self.scan(dec, "前置き\n顧客A\r\n顧客B\n", transcript=p, code=1)

    def test_allow_must_contain_the_whole_finding(self):
        """許可は、1 つの許可の出現が見つけた範囲の全体を含むときだけ（前提: 許可の和集合で覆えば許可済み）。"""
        p = self.secret_transcript(f"ABCDEF と {SECRET_KEY}")
        dec = self.init(transcript=p)
        self.mark(p, dec, "ABCDEF")
        for allow in (("ABC", "DEF"), ("ABCD", "CDEF")):
            with self.subTest(allow=allow):
                self.scan(dec, "ABCDEF", *allow, transcript=p, code=1)
        _done, result = self.scan(dec, SECRET_KEY, "sk-", SECRET_KEY[3:], transcript=p, code=1)
        self.assertIn("pattern_secret", {f["rule"] for f in result["findings"]})
        self.scan(dec, "ABCDEF の件", "ABCDEF の件", transcript=p, code=0)

    # ---- 2 回目のレビューで崩れた前提（impl-review-2.md、impl-root-causes.md）

    def test_redaction_is_applied_to_the_joined_body(self):
        """秘密の鍵の塊がブロックをまたいでも、つないだ本文の全体で伏せる（前提: ブロックごとの伏せ字は全体と同じ）。"""
        body = "QUFBQUFBQUFBQUFB\nQkJCQkJCQkJCQkJC"
        b = Builder(session_id="4a1c2d3e-aaaa-4bbb-8ccc-0123456789ab")
        b.human("鍵を見せて")
        b.assistant([{"type": "text", "text": "-----BEGIN PRIVATE KEY-----"},
                     {"type": "text", "text": f"{body}\n-----END PRIVATE KEY-----"}])
        b.text("-----BEGIN RSA PRIVATE KEY-----")
        b.text(f"{body}\n-----END RSA PRIVATE KEY-----")
        p = self.outside / f"{b.session_id}.jsonl"
        p.write_bytes(b.to_bytes())
        ex = extract_file(p)
        text = ws.render(ex, TITLE, [], []).decode()
        self.assertNotIn("QUFBQUFB", text)
        self.assertNotIn("QkJCQkJC", text)
        dec = self.init(transcript=p)
        self.scan(dec, f"鍵は\n{body}\n", transcript=p, code=1)

    # ---- 3 回目のレビューで崩れた前提（impl-review-3.md）: 形を変える前の元の文の全体で見つける

    KEY_BODY = "QUFBQUFBQUFBQUFB\nQkJCQkJCQkJCQkJC"

    def key_session(self, fill, **builder) -> tuple[Path, str]:
        b = Builder(session_id="2a1c2d3e-aaaa-4bbb-8ccc-0123456789ab", **builder)
        b.human("鍵の件")
        fill(b)
        p = self.outside / f"{b.session_id}.jsonl"
        p.write_bytes(b.to_bytes())
        return p, ws.render(extract_file(p), TITLE, [], []).decode()

    def assert_key_hidden(self, p, text, *opts):
        self.assertNotIn("QUFBQUFB", text)
        self.assertNotIn("QkJCQkJC", text)
        dec = self.init(transcript=p)
        for line in self.KEY_BODY.split("\n"):
            with self.subTest(line=line):
                self.scan(dec, f"本文\n{line}\n", transcript=p, code=1)

    def test_header_in_a_tool_value_and_body_in_text(self):
        p, text = self.key_session(lambda b: (
            b.tool_use("Grep", {"pattern": "-----BEGIN PRIVATE KEY-----"}),
            b.text(f"{self.KEY_BODY}\n-----END PRIVATE KEY-----")))
        self.assert_key_hidden(p, text)
        self.assertIn("[ツール] Grep ［伏せ字］", text)

    def test_header_in_a_hidden_tool_value_with_tools_none(self):
        b = Builder(session_id="2b1c2d3e-aaaa-4bbb-8ccc-0123456789ab")
        b.human("鍵の件")
        b.tool_use("Grep", {"pattern": "-----BEGIN PRIVATE KEY-----"})
        b.text(f"{self.KEY_BODY}\n-----END PRIVATE KEY-----")
        p = self.outside / f"{b.session_id}.jsonl"
        p.write_bytes(b.to_bytes())
        text = ws.render(extract_file(p, tools="none"), TITLE, [], []).decode()
        self.assertNotIn("QUFBQUFB", text)
        self.assertNotIn("[ツール]", text)

    def test_whole_key_in_a_tool_value_registers_body_lines(self):
        key = f"-----BEGIN PRIVATE KEY-----\n{self.KEY_BODY}\n-----END PRIVATE KEY-----"
        p, text = self.key_session(lambda b: (b.tool_use("Grep", {"pattern": key}), b.text("探した")))
        self.assert_key_hidden(p, text)

    def test_whole_key_in_cwd_registers_body_lines(self):
        key = f"-----BEGIN PRIVATE KEY-----\n{self.KEY_BODY}\n-----END PRIVATE KEY-----"
        p, text = self.key_session(lambda b: b.text("了解"), cwd=key)
        self.assert_key_hidden(p, text)

    def test_key_in_command_args_is_hidden_before_flattening(self):
        key = f"-----BEGIN PRIVATE KEY-----\n{self.KEY_BODY}\n-----END PRIVATE KEY-----"
        p, text = self.key_session(lambda b: (
            b.human(f"<command-name>/x</command-name>\n<command-args>{key}</command-args>"), b.text("了解")))
        self.assert_key_hidden(p, text)

    # ---- 4 回目のレビューで崩れた前提（impl-review-4.md）: 見つける、決める、変えるを分ける

    def test_overlapping_rules_are_unioned(self):
        """重なる規則の範囲は捨てずに和集合にする（前提: 先に当たった範囲と重なる規則は捨ててよい）。"""
        p = self.secret_transcript("password=sk-abcdefghijklmnop/SECONDSECRET と token=alice.smith@example.org")
        text = ws.render(extract_file(p), TITLE, [], []).decode()
        self.assertNotIn("SECONDSECRET", text)
        self.assertNotIn("alice", text.split("---", 2)[2])
        dec = self.init(transcript=p)
        for page, rule in (("値は sk-abcdefghijklmnop/SECONDSECRET だった", "auto_secret"),
                           ("名前は alice.smith", "auto_email")):
            with self.subTest(page=page):
                _done, result = self.scan(dec, page, transcript=p, code=1)
                self.assertIn(rule, {f["rule"] for f in result["findings"]})

    def test_structure_is_judged_on_the_original_text(self):
        """差し込みとコマンドの要素の判定は、伏せ字の前の元の文で行う（前提: 伏せ字を先にかけても構造は判定できる）。"""
        p = self.secret_transcript("<system-reminder>NOSHOW-差し込み\nThe file contains -----BEGIN PRIVATE KEY-----"
                                   "</system-reminder>\n質問です")
        ex = extract_file(p)
        text = ws.render(ex, TITLE, [], []).decode()
        self.assertNotIn("NOSHOW", text)
        self.assertNotIn("system-reminder", text)
        self.assertIn("質問です", text)
        self.assertEqual({w["code"] for w in ws.summarize_warnings(ex.warnings)}, {"stripped_reminder"})

    def test_many_hits_are_not_quadratic(self):
        import time
        started = time.perf_counter()
        ranges, hits = ws.find_secrets(" ".join(f"u{i}@example.org" for i in range(6000)))
        self.assertEqual((len(ranges), len(hits)), (6000, 6000))
        self.assertLess(time.perf_counter() - started, 2)

    def test_column_survives_reordering_and_long_lines_are_fast(self):
        """位置の対応は、正規化で切れない塊ごとに取る（前提: 接頭辞の長さから元の位置が分かる）。"""
        p = self.secret_transcript("太郎さんに聞いた")
        dec = self.init(transcript=p)
        self.mark(p, dec, "太郎")
        ex = extract_file(p, utc_offset="+09:00")
        spans = ws.load_decisions(dec).spans
        rows, _ = ws.scan_text("あ" + chr(0x0315) + chr(0x0300) + "x太郎", ex, spans, [])
        self.assertEqual(rows, [{"line": 1, "column": 5, "rule": "manual"}])
        import time
        started = time.perf_counter()
        rows, _ = ws.scan_text("太郎。" * 3000, ex, spans, [])
        self.assertEqual(len(rows), 3000)
        self.assertEqual(rows[1]["column"], 4)
        self.assertLess(time.perf_counter() - started, 5)

    def test_path_scans_the_written_files(self):
        """書いたあとのファイルの全体を照らす（前提: 新しい断片に秘密がなければ、書いたあとのページにもない）。
        関連ページの「顧客Bについて。」の B を A に直すと、断片の「A」は通るが、書いたあとのページは当たる。"""
        p = self.secret_transcript("顧客Aの相談")
        dec = self.init(transcript=p)
        self.mark(p, dec, "顧客A")
        page = self.wiki / "concepts" / "相談.md"
        page.parent.mkdir()
        page.write_bytes("# 相談\n\n顧客Bについて。\n".encode("utf-8"))
        self.scan(dec, "A", transcript=p, code=0)  # 断片だけでは見つからない
        page.write_bytes(page.read_bytes().replace("B".encode(), "A".encode()))
        clean = self.wiki / "sources" / "会話.md"
        clean.write_bytes("# 会話\n\n問題のない要約。\n".encode("utf-8"))
        done = self.ok(["scan", *self.common(p), "--decisions", dec, "--path", clean, "--path", page, "--json"], code=1)
        result = json.loads(done.stdout)
        self.assertEqual(result["findings"], [{"path": str(page), "line": 3, "column": 1, "rule": "manual"}])
        self.assertNotIn("顧客A".encode(), done.stdout)
        self.ok(["scan", *self.common(p), "--decisions", dec, "--path", clean])
        self.ok(["scan", *self.common(p), "--decisions", dec, "--path", self.wiki / "ない.md"], code=1)

    def test_invalid_utf8_input_is_refused(self):
        dec = self.init()
        done = run(["scan", *self.common(), "--decisions", dec], stdin="顧客A".encode("cp932"))
        self.assertEqual(done.returncode, 1)


class LocateInspectTests(CliCase):
    SID = "5f1c2d3e-aaaa-4bbb-8ccc-0123456789ab"

    def config(self) -> Path:
        cfg = self.base / "cfg"
        (cfg / "projects" / "p1").mkdir(parents=True)
        return cfg

    def test_locate_finds_one(self):
        cfg = self.config()
        shutil.copyfile(BASIC, cfg / "projects" / "p1" / f"{self.SID}.jsonl")
        done = self.ok(["locate", "--session-id", self.SID, "--json"], env={"CLAUDE_CONFIG_DIR": str(cfg)})
        self.assertEqual(Path(json.loads(done.stdout)["transcript"]).name, f"{self.SID}.jsonl")
        self.ok(["locate", "--session-id", self.SID.upper()], code=1, env={"CLAUDE_CONFIG_DIR": str(cfg)})
        (cfg / "projects" / "p2").mkdir()
        shutil.copyfile(BASIC, cfg / "projects" / "p2" / f"{self.SID}.jsonl")
        self.ok(["locate", "--session-id", self.SID], code=1, env={"CLAUDE_CONFIG_DIR": str(cfg)})

    def test_locate_does_not_follow_links(self):
        cfg = self.config()
        elsewhere = self.base / "elsewhere"
        elsewhere.mkdir()
        shutil.copyfile(BASIC, elsewhere / f"{self.SID}.jsonl")
        if not make_junction(cfg / "projects" / "linked", elsewhere):
            self.skipTest("リンクを作れない")
        self.ok(["locate", "--session-id", self.SID], code=1, env={"CLAUDE_CONFIG_DIR": str(cfg)})

    def test_print_session_without_human_is_refused(self):
        b = Builder(session_id="6a1c2d3e-aaaa-4bbb-8ccc-0123456789ab")
        b.user("claude -p の依頼")
        b.text("返答")
        p = self.outside / f"{b.session_id}.jsonl"
        p.write_bytes(b.to_bytes())
        done = self.ok(["inspect", "--transcript", p, "--json"], code=2)
        self.assertEqual(json.loads(done.stdout)["verdict"], "not_session")
        self.ok(["show", "--transcript", p, "--title", TITLE], code=2)

    def test_non_object_line_is_not_a_session(self):
        p = self.outside / "x.jsonl"
        p.write_bytes(BASIC.read_bytes() + b"[1, 2]\n")
        self.ok(["inspect", "--transcript", p, "--session-id", self.SID], code=2)

    def test_inspect_reports_raw_and_temp_files(self):
        dec = self.init()
        sha = self.meta(dec)["render_sha256"]
        self.write(dec, sha)
        (self.raw / ".wiki-session-deadbeef.tmp").write_bytes(b"x")
        done = self.ok(["inspect", *self.common(), "--wiki", self.wiki, "--raw-root", self.raw, "--slug", "会話",
                        "--json"])
        result = json.loads(done.stdout)
        self.assertEqual(result["raw"]["session_id"], self.SID)
        self.assertEqual(result["temp_files"], [".wiki-session-deadbeef.tmp"])
        self.assertFalse(result["source_page_exists"])
        self.assertEqual(len(result["human_tail"]), 2)
        self.assertNotIn("taro@example.com", done.stdout.decode())

    def test_uninitialized_wiki_is_refused_before_reading(self):
        (self.wiki / "SCHEMA.md").unlink()
        before = snapshot(self.base)
        for args in (["decide", "init", "--transcript", self.outside / "ない.jsonl", "--wiki", self.wiki, "--slug", "x"],
                     ["inspect", "--transcript", self.outside / "ない.jsonl", "--wiki", self.wiki, "--raw-root",
                      self.raw, "--slug", "x"]):
            done = self.ok(args, code=1)
            self.assertIn("/wiki:init", done.stderr.decode())
        self.assertEqual(snapshot(self.base), before)


if __name__ == "__main__":
    unittest.main()
