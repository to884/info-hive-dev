"""合成した Codex の履歴を、実際の読み取り API と wiki_session.py で取り込む試験。

    python -X utf8 -B tests/wiki/check_codex_session.py [--out <結果.json>]

OS の一時ディレクトリに CODEX_HOME、legacy の履歴、wiki、raw を作る。
legacy を取り込んだあと、この合成ホームだけを Codex CLI で明示的に paginated に移行し、
同じ手順を確かめる。通常のホームと利用者の履歴は読まない。モデルのターンと resume は呼ばない。
出力するのは版、件数、ハッシュ、検証の成否だけで、会話の本文は出さない。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SESSION_SCRIPT = ROOT / "info-hive-wiki/skills/info-hive/scripts/wiki_session.py"


def build_fixture(home: Path, sid: str | None = None, turn_count: int = 2) -> tuple[str, list[str], Path]:
    """人工的な 2 ターンの履歴。実際のユーザーの履歴をコピーしない。"""
    sid = sid or str(uuid.uuid4())
    folder = home / "sessions/2026/11/17"
    folder.mkdir(parents=True, exist_ok=True)
    stamp = "2026-11-17T00:00:00.000Z"
    rows = [{"type": "session_meta", "payload": {
        "session_id": sid, "id": sid, "timestamp": stamp, "cwd": str(home.parent),
        "originator": "codex_cli_rs", "cli_version": "0.166.0", "source": "cli",
        "model_provider": "openai", "history_mode": "legacy", "base_instructions": None,
    }}]
    turn_ids = []
    for i in range(turn_count):
        turn_id = str(uuid.uuid4())
        turn_ids.append(turn_id)
        start = 1794873600 + i * 10
        rows.extend([
            {"type": "event_msg", "payload": {"type": "task_started", "turn_id": turn_id, "started_at": start}},
            {"type": "event_msg", "payload": {"type": "user_message", "message": f"合成した履歴の質問{i + 1}です。",
                                                "images": [], "local_images": []}},
            {"type": "event_msg", "payload": {"type": "agent_message", "message": f"合成した履歴の回答{i + 1}です。",
                                                "phase": "final_answer"}},
            {"type": "event_msg", "payload": {"type": "task_complete", "turn_id": turn_id,
                                                "last_agent_message": f"合成した履歴の回答{i + 1}です。",
                                                "started_at": start, "completed_at": start + 1}},
        ])
    path = folder / f"rollout-2026-11-17T00-00-00-{sid}.jsonl"
    path.write_text("".join(json.dumps({"timestamp": stamp, **row}, ensure_ascii=False) + "\n" for row in rows),
                    encoding="utf-8", newline="\n")
    return sid, turn_ids, path


def file_digest(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def remove_tree(path: Path) -> None:
    resolved = path.resolve()
    temp_root = Path(tempfile.gettempdir()).resolve()
    if resolved.parent != temp_root or not resolved.name.startswith("info-hive-codex-session-"):
        raise RuntimeError("試験で作った一時ディレクトリ以外は削除しない")
    def onexc(func, name, _exc):
        os.chmod(name, stat.S_IWRITE | stat.S_IREAD)
        func(name)
    shutil.rmtree(path, onexc=onexc)


def check(cli: str, base: Path) -> dict:
    home = base / "合成した Codex のホーム"
    home.mkdir()
    sid, _turn_ids, rollout = build_fixture(home)
    initial_digest = file_digest(rollout)
    project = base / "合成した利用者のプロジェクト"
    wiki = project / "wiki"
    (wiki / "sources").mkdir(parents=True)
    (wiki / "SCHEMA.md").write_text("# 合成した試験用のスキーマ\n", encoding="utf-8")
    raw = project / "raw"
    raw.mkdir()
    env = {**os.environ, "CODEX_HOME": str(home), "CODEX_THREAD_ID": sid, "PYTHONUTF8": "1"}
    env.pop("CODEX_SESSION_ID", None)
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0

    def execute(command: list[str], label: str, parse_json: bool = True):
        result = subprocess.run(command, cwd=project, env=env, capture_output=True,
                                encoding="utf-8", timeout=180, creationflags=flags)
        if result.returncode:
            # API のエラーにも会話が含まれうるので、子の出力は例外に混ぜない。
            raise RuntimeError(f"{label} が失敗した（終了コード {result.returncode}）")
        if not parse_json:
            return result.stdout.strip()
        try:
            return json.loads(result.stdout)
        except ValueError:
            raise RuntimeError(f"{label} が JSON を返さなかった") from None

    def session(*args: str) -> dict:
        return execute([sys.executable, "-X", "utf8", "-B", str(SESSION_SCRIPT), *map(str, args)], str(args[0]))

    def ingest(mode: str) -> dict:
        source_before = file_digest(rollout)
        located = session("locate", "--host", "codex", "--current", "--json")
        assert located["session_id"] == sid
        assert located["source_kind"] == "codex-session"
        assert located["history_mode"] == mode
        assert located["current"] is True and located["cutoff_kind"] == "turn"
        assert isinstance(located["before"], str) and located["before"]
        common = ["--transcript", located["transcript"], "--before", located["before"], "--utc-offset", "+09:00"]
        inspected = session("inspect", *common, "--json")
        assert inspected["verdict"] == "session"
        assert len(inspected["human_tail"]) == 1, "最新のターンが範囲に混ざった"
        assert inspected["range"]["before"] == located["before"]
        slug = f"合成した会話-{mode}"
        initialized = session("decide", "init", *common, "--wiki", str(wiki), "--slug", slug, "--json")
        decisions = initialized["decisions"]
        meta = session("show", *common, "--title", "合成した会話の記録", "--decisions", decisions,
                       "--slug", slug, "--meta", "--json")
        written = session("write", *common, "--title", "合成した会話の記録", "--decisions", decisions,
                          "--wiki", str(wiki), "--raw-root", str(raw), "--slug", slug,
                          "--expect-sha256", meta["render_sha256"], "--json")
        assert written["raw_state"] == "created"
        raw_path = Path(written["raw_path"])
        assert file_digest(raw_path) == meta["render_sha256"]
        raw_bytes = raw_path.read_bytes()
        assert b'source_kind: "codex-session"' in raw_bytes
        assert b'source_sha256_of: "codex-thread-range-v1"' in raw_bytes
        verified = session("verify", "--raw-root", str(raw), "--slug", slug,
                           "--expect-sha256", meta["render_sha256"], "--json")
        assert verified["sha256_matches"] is True and verified["read_only"] is True
        assert file_digest(rollout) == source_before, "取り込みが元の履歴を変更した"
        return {"history_mode": mode, "human_count": len(inspected["human_tail"]),
                "turns": inspected["turns"], "cutoff_kind": located["cutoff_kind"],
                "source_kind": inspected["source_kind"], "source_sha256": inspected["range"]["source_sha256"],
                "source_bytes": inspected["range"]["source_bytes"], "render_sha256": meta["render_sha256"],
                "raw_state": written["raw_state"], "hash_matches": verified["sha256_matches"],
                "read_only": verified["read_only"], "source_unchanged_by_ingest": True}

    version = execute([cli, "--version"], "Codex の版の取得", parse_json=False)
    legacy = ingest("legacy")
    assert file_digest(rollout) == initial_digest
    # 移行は製品の処理に含めず、合成したホームで試験の準備として明示的に行う。
    migration = execute([cli, "--no-daemon", "migrate-rollouts", "--apply", "--thread", sid, "--json"], "合成した履歴の移行")
    assert isinstance(migration, dict), "移行の結果がオブジェクトでない"
    paginated = ingest("paginated")
    return {"client": version, "synthetic_only": True, "normal_codex_home_unchanged": True,
            "models_called": False, "fixture_turns": len(_turn_ids),
            "migration_explicit_in_smoke_only": True, "modes": [legacy, paginated]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="本文を含まない検証結果の JSON")
    args = parser.parse_args()
    cli = shutil.which("codex")
    if not cli:
        parser.error("Codex CLI が PATH にない")
    base = Path(tempfile.mkdtemp(prefix="info-hive-codex-session-"))
    try:
        report = check(cli, base)
    finally:
        remove_tree(base)
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8", newline="\n")
    print(output, end="")


if __name__ == "__main__":
    main()
