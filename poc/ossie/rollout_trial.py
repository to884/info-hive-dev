"""実データを使わず、ライブ書き込みと公開版の有効化を判定する試験。"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import math
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import perf_counter, sleep
from uuid import uuid4

import publication_trial as fixture
import wiki_apply as publish
import wiki_live_apply as live


HERE = Path(__file__).resolve()
DATE = "2026-11-19"
SCRIPT = fixture.PLUGIN / "scripts"
RAW_COUNT = 160


def save(path, contents):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(contents if isinstance(contents, bytes) else contents.encode("utf-8"))


def text(path):
    return path.read_text(encoding="utf-8")


def sha(plan):
    return publish.digest(publish.encoded(plan))


def file_manifest(root):
    return {p.relative_to(root).as_posix(): publish.digest(p.read_bytes())
            for p in root.rglob("*") if p.is_file() and p != root / publish.MARKER
            and ".wiki-cache" not in p.relative_to(root).parts}


def prepare_live(parent, pages, raw_count=RAW_COUNT):
    wiki, raw = parent / "wiki", parent / "raw"
    wiki.mkdir(parents=True)
    raw.mkdir()
    save(wiki / "SCHEMA.md", "# 隔離した運用試験\n")
    save(wiki / "index.md", "# 索引\n\n- [[indexes/sources]]\n- [[indexes/concepts]]\n")
    save(wiki / "log.md", "# 履歴\n\n" + "".join(
        f"## [{DATE}] ingest | 既存の資料 {i}\n\n" for i in range(pages)))
    for i in range(raw_count):
        save(raw / f"group-{i // 20}" / f"original-{i:03}.txt", (f"原本の識別子 {i}\n" * 5800))
    for kind, count in (("sources", pages // 2), ("concepts", pages - pages // 2)):
        links = []
        for i in range(count):
            slug = f"{kind}-{i:03}"
            details = {"type": "source" if kind == "sources" else "concept", "title": slug,
                       "tags": ["fixture"], "created": DATE, "updated": DATE}
            if kind == "sources":
                number = i % raw_count
                original = raw / f"group-{number // 20}" / f"original-{number:03}.txt"
                details.update(raw=original.relative_to(parent).as_posix(), raw_sha256=publish.digest(original.read_bytes()))
            else:
                details["sources"] = [f"sources-{i % (pages // 2):03}"]
            body = "\n\n".join(
                f"所見 {section}。この資料は合成の運用検証と確認に使う。[[sources-{i % (pages // 2):03}]]。" * 12
                for section in range(6))
            save(wiki / kind / f"{slug}.md", fixture.frontmatter(details, body))
            links.append(f"- [[{slug}]]: 合成の既存資料")
        save(wiki / "indexes" / f"{kind}.md", "# 索引\n\n## 項目\n\n" + "\n".join(links) + "\n")
    return wiki, raw


def new_plan(wiki, raw, name, index):
    at = perf_counter()
    directory = Path(live.begin(wiki, raw, name)["apply_dir"])
    work = live.work_directory(directory)
    plan = live.read_plan(work)
    guard = live.plan_wiki(plan)
    source = f"sources/{name}.md"
    register = live.register(work, plan, guard, "new", source)
    save(Path(register["path"]), fixture.frontmatter(
        {"type": "source", "title": name, "tags": ["fixture"], "created": DATE, "updated": DATE},
        f"rolloutmarker{name} 追加の証拠。[[concepts-{index:03}]]"))
    concept = f"concepts/concepts-{index:03}.md"
    update = Path(live.register(work, plan, guard, "edit", concept)["path"])
    save(update, update.read_bytes() + f"\n\n[[{name}]] に別の証拠を追記。\n".encode("utf-8"))
    heading = f"## [{DATE}] ingest | {name}"
    plan["operations"] = [
        {"kind": "index-add", "file": "indexes/sources.md", "section": "## 項目", "nth": None,
         "line": f"- [[{name}]]: 検証済みの追加資料"},
        {"kind": "log-entry", "heading": heading, "nth": None, "lines": ["原本の指紋を照合した"]},
    ]
    live.write(work, directory / "plan.json", publish.encoded(plan), replace=True)
    preview = live.preview(work, plan, guard)
    return {"directory": str(directory), "sha": preview["plan_sha256"], "name": name,
            "source": source, "concept": concept, "heading": heading, "prepare_s": perf_counter() - at}


def env_for(root):
    return {**os.environ, "INFO_HIVE_DATA_DIR": str(root / "workspace-data"), "PYTHONUTF8": "1",
            "PYTHONDONTWRITEBYTECODE": "1"}


def child(job, env, *args):
    return [sys.executable, "-B", str(HERE), job, *map(str, args)], env


def sync_start(gate, ready):
    save(ready, "ready\n")
    deadline = perf_counter() + 180
    while not gate.is_file():
        if perf_counter() >= deadline:
            raise TimeoutError("開始合図を待ちきれません")
        sleep(.01)


def write_worker(plan_file, gate, ready):
    plan = json.loads(plan_file.read_bytes())
    spans = []
    original = live.with_gate

    @contextmanager
    def timed(*args):
        queued = perf_counter()
        with original(*args) as acquired:
            entered = perf_counter()
            try:
                yield acquired
            finally:
                spans.append((entered - queued, perf_counter() - entered))

    live.with_gate = timed
    sync_start(gate, ready)
    started = perf_counter()
    try:
        result = live.apply(plan["directory"], plan["sha"])
    except publish.Conflict as exc:
        if not plan.get("allow_conflict"):
            raise
        return {"status": "conflict", "reason": str(exc)}
    return {"elapsed_s": perf_counter() - started, "wait_s": sum(w for w, _ in spans),
            "held_s": sum(h for _, h in spans), "acquisitions": len(spans), "files": result["files"]}


def run_wave(root, plans, env, job="write-worker"):
    workers, readiness = [], []
    gate = root / "start"
    try:
        for i, plan in enumerate(plans):
            item, ready = root / f"plan-{i}.json", root / f"ready-{i}"
            save(item, publish.encoded(plan))
            command, child_env = child(job, env, item, gate, ready)
            workers.append(subprocess.Popen(command, env=child_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                            encoding="utf-8"))
            readiness.append(ready)
        deadline = perf_counter() + 120
        while not all(path.is_file() for path in readiness):
            if perf_counter() >= deadline or any(worker.poll() is not None for worker in workers):
                raise RuntimeError("並行処理を開始できません")
            sleep(.02)
        start = perf_counter()
        save(gate, "go\n")
        rows = []
        for worker, plan in zip(workers, plans):
            output, error = worker.communicate(timeout=220)
            if worker.returncode:
                raise RuntimeError(error)
            rows.append({**{k: plan[k] for k in ("name", "prepare_s") if k in plan}, **json.loads(output)})
        return {"wave_s": perf_counter() - start, "samples": rows}
    finally:
        for worker in workers:
            if worker.poll() is None:
                worker.kill()
            worker.communicate()


def live_visibility(wiki, plan):
    return (
        (wiki / plan["source"]).exists(),
        text(wiki / plan["concept"]).count(f"[[{plan['name']}]]") == 1,
        text(wiki / "indexes/sources.md").count(f"[[{plan['name']}]]") == 1,
        text(wiki / "log.md").count(plan["heading"] + "\n") == 1,
    )


def verify_live(wiki, plan, expected):
    actual = live_visibility(wiki, plan)
    if actual != expected:
        raise AssertionError(f"{plan['name']}: {actual} != {expected}")


def benchmark(parent, pages, repetitions, env):
    wiki, raw = prepare_live(parent, pages)
    originals = file_manifest(raw)
    initial = {"page_count": pages, "wiki_bytes": sum(p.stat().st_size for p in wiki.rglob("*") if p.is_file()),
               "raw_files": len(originals), "raw_bytes": sum(p.stat().st_size for p in raw.rglob("*") if p.is_file())}
    result = {}
    seq = 0
    for count in (1, 4, 8):
        waves = []
        for rep in range(repetitions):
            plans = [new_plan(wiki, raw, f"parallel-{count}-{rep}-{i}", (seq + i) % (pages - pages // 2))
                     for i in range(count)]
            seq += count
            waves.append(run_wave(parent / f"wave-{count}-{rep}", plans, env))
            for plan in plans:
                verify_live(wiki, plan, (True,) * 4)
        result[str(count)] = waves
        print(f"{count} 並行の測定完了", file=sys.stderr, flush=True)
    assert file_manifest(raw) == originals
    return {"fixture": initial, "waves": result}


def checkpoint_at(wanted):
    def checkpoint(actual):
        if actual == wanted:
            os._exit(71)
    return checkpoint


def interrupt(job, env, *args):
    command, child_env = child(job, env, *args)
    result = subprocess.run(command, env=child_env, capture_output=True, encoding="utf-8", timeout=220)
    if result.returncode != 71:
        raise RuntimeError(f"予定した地点で停止しませんでした {result.returncode}\n{result.stderr}")


def recover_in_process(wiki, env, *, is_live):
    started = perf_counter()
    common = [sys.executable, "-B", str(SCRIPT / "wiki_apply.py")]
    if is_live:
        unlocked = subprocess.run([*common, "unlock", "--wiki", str(wiki)], env=env, capture_output=True,
                                  encoding="utf-8", timeout=180)
        if unlocked.returncode:
            return {"elapsed_s": perf_counter() - started, "status": unlocked.returncode,
                    "value": unlocked.stderr.strip()}
    result = subprocess.run([*common, "recover", "--wiki", str(wiki), *(["--live"] if is_live else [])],
                            env=env, capture_output=True, encoding="utf-8", timeout=180)
    return {"elapsed_s": perf_counter() - started, "status": result.returncode,
            "value": json.loads(result.stdout) if result.returncode == 0 else result.stderr.strip()}


def must_stop(operation, expected):
    try:
        operation()
    except (OSError, publish.PublicationError) as error:
        if expected in str(error):
            return str(error)
        raise
    raise AssertionError(f"整合性違反を見つけて停止しませんでした: {expected}")


def live_faults(parent, pages, env):
    wiki, raw = prepare_live(parent, pages)
    normal = new_plan(wiki, raw, "recoverable", 0)
    interrupt("live-crash", env, normal["directory"], normal["sha"], "after_write:0")
    survived = recover_in_process(wiki, env, is_live=True)
    assert survived["status"] == 0 and survived["value"]["state"] == "applied"
    verify_live(wiki, normal, (True,) * 4)
    assert live.apply(normal["directory"], normal["sha"])["state"] == "already_applied"
    collision = [new_plan(wiki, raw, f"edit-collision-{i}", 3) for i in range(2)]
    for plan in collision:
        plan["allow_conflict"] = True
    wave = run_wave(parent / "edit-collision", collision, env)
    results = [row.get("status", "applied") for row in wave["samples"]]
    assert sorted(results) == ["applied", "conflict"]
    for plan, status in zip(collision, results):
        verify_live(wiki, plan, (status == "applied",) * 4)
    broken = new_plan(wiki, raw, "journal-loss", 1)
    before = file_manifest(wiki)
    interrupt("live-crash", env, broken["directory"], broken["sha"], "after_write:0")
    journal = wiki / publish.AREA / publish.LIVE_JOURNAL
    loss = journal.with_name("simulated-lost-live-journal.bin")
    journal.rename(loss)
    visible = recover_in_process(wiki, env, is_live=True)
    assert visible["status"] == 5 and "日誌がありません" in visible["value"]
    partial = live_visibility(wiki, broken)
    assert sum(partial) == 1
    # 試験用に保管した日誌を復元し、その後は製品の復旧経路だけを使う。
    loss.rename(journal)
    repaired = recover_in_process(wiki, env, is_live=True)
    assert repaired["status"] == 0 and repaired["value"]["state"] == "applied"
    verify_live(wiki, broken, (True,) * 4)
    after = file_manifest(wiki)
    touched = {broken["source"], broken["concept"], "indexes/sources.md", "log.md"}
    assert {k: v for k, v in before.items() if k not in touched} == {
        k: v for k, v in after.items() if k not in touched}

    receipt_case = new_plan(wiki, raw, "receipt-survived", 2)
    index_before = (wiki / "indexes/sources.md").read_bytes()
    interrupt("live-crash", env, receipt_case["directory"], receipt_case["sha"], "after_receipt")
    verify_live(wiki, receipt_case, (True,) * 4)
    index_after = (wiki / "indexes/sources.md").read_bytes()
    save(wiki / "indexes/sources.md", index_before)
    completed = recover_in_process(wiki, env, is_live=True)
    assert completed["status"] == 5 and "成果物が一致しません" in completed["value"]
    assert journal.exists()
    must_stop(lambda: live.apply(receipt_case["directory"], receipt_case["sha"]), "成果物が一致しません")
    verify_live(wiki, receipt_case, (True, True, False, True))
    save(wiki / "indexes/sources.md", index_after)
    assert recover_in_process(wiki, env, is_live=True)["value"]["state"] == "applied"
    assert live.apply(receipt_case["directory"], receipt_case["sha"])["state"] == "already_applied"
    save(wiki / "indexes/sources.md", index_before)
    must_stop(lambda: live.apply(receipt_case["directory"], receipt_case["sha"]), "成果物が一致しません")
    assert recover_in_process(wiki, env, is_live=True)["status"] == 5
    save(wiki / "indexes/sources.md", index_after)
    rollback_plan = new_plan(wiki, raw, "rollback-cleanup", 4)
    interrupt("live-rollback-crash", env, rollback_plan["directory"], rollback_plan["sha"])
    assert journal.exists() and not (wiki / publish.AREA / publish.LIVE_TRANSACTION).exists()
    aborted = recover_in_process(wiki, env, is_live=True)
    assert aborted["status"] == 0 and aborted["value"]["state"] == "aborted"
    verify_live(wiki, rollback_plan, (False,) * 4)
    return {"process_exit": survived, "same_page_concurrent_edit": results,
            "journal_name_lost": visible, "after_restore_journal": repaired,
            "published_files_without_journal": dict(zip(("source", "concept", "index", "log"), partial)),
            "receipt_survives_index_update_loss": {"recover": completed, "retry_stopped_after_journal_removed": True},
            "rollback_cleanup_interruption": aborted}


def create_public_candidate(folder, count):
    state = {"definition": {"label": "初回切替"}, "citations": {}}
    fixture.insert(state, fixture.SEED)
    for i in range(count - 1):
        fixture.insert(state, {"source": f"release-seed-{i:03}", "maker": "fixture-maker", "part": f"PART{i:03}",
                               "quote": "合成の確認済み資料。既存の公開内容を再現する。" * 22})
    fixture.materialize(folder, None, state)
    return fixture.read_json(folder / "ontology/registry.json")


def publish_existing(wiki, folder, base=None, *, stop=None, env=None):
    live_base = publish.capture_live_base(wiki) if base is None else None
    plan = publish.build_plan(wiki, folder, base=base, live_base=live_base)
    approved = sha(plan)
    if stop is None:
        return plan, publish.apply_plan(wiki, folder, plan, approved)
    path = folder.parent / f"{plan['plan_id']}.plan.json"
    save(path, publish.encoded(plan))
    interrupt("publication-crash", env, wiki, folder, path, approved, stop)
    return plan, None


def read_query(wiki, keyword, env):
    result = subprocess.run([sys.executable, "-B", str(SCRIPT / "wiki_search.py"), keyword, "--wiki", str(wiki),
                             "--no-embed", "--json"], env=env, capture_output=True, encoding="utf-8", timeout=120)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return json.loads(result.stdout)


def quote(wiki, release_id=None):
    version = publish.resolve_publication(wiki, release_id)
    return text((version.root if version else wiki) / "sources/seed.md")


def stage_live_source(wiki, raw, slug):
    directory = Path(live.begin(wiki, raw, slug)["apply_dir"])
    work = live.work_directory(directory)
    plan = live.read_plan(work)
    guard = live.plan_wiki(plan)
    path = live.register(work, plan, guard, "new", f"sources/{slug}.md")["path"]
    save(Path(path), f"# {slug}\n")
    live.write(work, directory / "plan.json", publish.encoded(plan), replace=True)
    return directory, live.preview(work, plan, guard)["plan_sha256"]


def switch_trial(parent, pages, env):
    parent.mkdir()
    candidate = parent / "first"
    state = create_public_candidate(candidate, pages // 2)
    original_manifest = file_manifest(candidate)
    wiki = parent / "wiki"
    shutil.copytree(candidate, wiki)
    raw = parent / "raw"
    raw.mkdir()
    legacy = read_query(wiki, "KabutoMarker", env)
    assert legacy.get("release_id") is None and legacy["results"][0]["rel_path"] == "sources/seed.md"
    _, first = publish_existing(wiki, candidate)
    active = publish.resolve_publication(wiki)
    area = wiki / publish.AREA
    anchor_a = (area / publish.HEAD).read_bytes()
    assert first["release_id"] == active.release_id
    assert file_manifest(active.root) == original_manifest
    try:
        live.begin(wiki, raw, "公開中の通常の保存")
    except publish.Conflict as exc:
        live_writer_blocked = str(exc)
    else:
        raise AssertionError("公開版の wiki でライブへの保存を許しました")
    result_a = read_query(wiki, "KabutoMarker", env)
    assert result_a["release_id"] == active.release_id and result_a["results"][0]["rel_path"] == "sources/seed.md"
    fixture.insert(state, {"source": "published-only", "maker": "trial", "part": "NEW",
                           "quote": "ReleaseOnlyMarker 公開側にだけ追加した証拠。"})
    second = parent / "second"
    fixture.materialize(second, active, state)
    _, forward = publish_existing(wiki, second, base=active)
    published = publish.resolve_publication(wiki)
    assert read_query(wiki, "ReleaseOnlyMarker", env)["results"][0]["rel_path"] == "sources/published-only.md"
    anchor_b = (area / publish.HEAD).read_bytes()
    save(area / "current", active.release_id + "\n")
    stale_pointer = must_stop(lambda: publish.resolve_publication(wiki), "先頭の完了記録")
    save(area / publish.HEAD, anchor_a)
    stale_pair = must_stop(lambda: publish.resolve_publication(wiki), "完了記録の一覧")
    save(area / "current", published.release_id + "\n")
    save(area / publish.HEAD, anchor_b)
    _, reverted = publish_existing(wiki, active.root, base=published)
    previous_content = publish.resolve_publication(wiki)
    assert file_manifest(previous_content.root) == original_manifest
    assert quote(wiki, result_a["release_id"]) == text(candidate / "sources/seed.md")
    pinned_b = publish.resolve_publication(wiki, forward["release_id"])
    assert "ReleaseOnlyMarker" in text(pinned_b.root / "sources/published-only.md")
    assert not (previous_content.root / "sources/published-only.md").exists()

    # ポインターを退避し、通常の読み書きがライブに戻らないことを確かめる。
    guard, area = publish.writing_area(wiki)
    with guard.hold_lock(area / "apply.lock"):
        assert publish.finish_journal(guard, area) is None
        pointer = area / "current"
        parked = area / "isolated-disabled-current"
        guard.replace_file(pointer, parked)
    must_stop(lambda: publish.resolve_publication(wiki), "公開ポインターがありません")
    assert file_manifest(wiki) == original_manifest
    disabled_pin = must_stop(lambda: publish.resolve_publication(wiki, forward["release_id"]), "公開ポインターがありません")
    must_stop(lambda: live.begin(wiki, raw, "ポインターのない wiki を保存する"), "公開版")
    assert not (wiki / "sources/published-only.md").exists()
    with guard.hold_lock(area / "apply.lock"):
        guard.replace_file(parked, pointer)
    assert publish.resolve_publication(wiki).release_id == reverted["release_id"]

    # 最初のゲートを出た後に別の書き手が確定させたライブ変更を、二度目のゲートで検出する。
    drift = parent / "drift"
    shutil.copytree(candidate, drift)
    plan = publish.build_plan(drift, candidate, live_base=publish.capture_live_base(drift))
    directory, approval = stage_live_source(drift, raw, "last-live")
    def concurrent_writer(checkpoint):
        if checkpoint == "after_initial_check":
            live.apply(directory, approval)
    drift_stop = must_stop(lambda: publish.apply_plan(drift, candidate, plan, sha(plan), checkpoint=concurrent_writer),
                           "初回公開の基準からライブ wiki が変わりました")
    assert "last-live" in text(drift / "sources/last-live.md")
    assert publish.resolve_publication(drift) is None and not (drift / publish.MARKER).exists()
    assert not (drift / publish.AREA / publish.JOURNAL).exists()
    queued, queued_sha = stage_live_source(drift, raw, "queued-live")
    pending_plan = publish.build_plan(drift, candidate, live_base=publish.capture_live_base(drift))

    def writer_waits(point):
        if point == "before_journal":
            args = [sys.executable, "-B", str(SCRIPT / "wiki_apply.py"), "apply", "--apply-dir", str(queued),
                    "--expect-sha256", queued_sha, "--wait", "0"]
            held = subprocess.run(args, env=env, capture_output=True, encoding="utf-8", timeout=120)
            assert held.returncode == 4 and "保留しました" in held.stderr, held.stderr
    pending_stop = must_stop(
        lambda: publish.apply_plan(drift, candidate, pending_plan, sha(pending_plan), checkpoint=writer_waits),
        "保留されたライブの承認済み差分")
    assert len(live.pending(drift)["pending"]) == 1 and publish.resolve_publication(drift) is None
    live.apply(queued, queued_sha)
    assert not live.pending(drift)["pending"]
    refreshed = parent / "refreshed"
    basis = publish.capture_live_base(drift)
    shutil.copytree(drift, refreshed, ignore=shutil.ignore_patterns(".wiki-cache"))
    ready = publish.build_plan(drift, refreshed, live_base=basis)
    publish.apply_plan(drift, refreshed, ready, sha(ready))
    new_root = publish.resolve_publication(drift).root
    assert all((new_root / "sources" / f"{slug}.md").is_file() for slug in ("last-live", "queued-live"))
    return {"wiki_articles": len(list(candidate.glob("**/*.md"))) - 3, "snapshot_bytes": sum(
        p.stat().st_size for p in candidate.rglob("*") if p.is_file()),
        "snapshot_files": len(original_manifest), "first": first["release_id"], "second": forward["release_id"],
        "republished_previous": reverted["release_id"], "explicit_b_after_live_fallback": disabled_pin,
        "published_only_excluded_after_rollback": True, "stale_cutover_blocked": drift_stop,
        "ordinary_live_write_blocked_after_switch": live_writer_blocked,
        "stale_pointer_blocked": stale_pointer, "stale_pointer_and_head_blocked": stale_pair,
        "pending_live_blocked": pending_stop, "recapture_preserved_both_live_pages": True}, candidate


def publication_faults(parent, candidate, env):
    parent.mkdir()
    rows = {}
    for name, point, loss in (
        ("before_pointer", "before_pointer", None),
        ("pointer_written", "pointer_written", None),
        ("receipt_lost_during_commit", "pointer_written", "receipt"),
        ("after_pointer", "after_pointer", None),
        ("payload_name_lost", "after_pointer", "release"),
    ):
        wiki = parent / name
        shutil.copytree(candidate, wiki)
        plan, _ = publish_existing(wiki, candidate, stop=point, env=env)
        area = wiki / publish.AREA
        active = area / "current"
        observed = active.exists()
        if point == "pointer_written":
            must_stop(lambda: publish.resolve_publication(wiki), "先頭の完了記録")
        parked = None
        if loss == "release":
            release = area / "releases" / text(active).strip()
            parked = release.with_name("simulated-lost-release")
            release.rename(parked)
            try:
                publish.resolve_publication(wiki)
            except (OSError, ValueError) as exc:
                read_error = str(exc)
            else:
                raise AssertionError("欠けた公開版を読みました")
        elif loss == "receipt":
            release = area / "receipts" / f"{plan['plan_id']}.json"
            parked = area / "simulated-lost-receipt"
            release.rename(parked)
            read_error = must_stop(lambda: publish.resolve_publication(wiki), "完了記録")
        result = recover_in_process(wiki, env, is_live=False)
        if parked:
            assert result["status"] != 0
            parked.rename(release)
            repaired = recover_in_process(wiki, env, is_live=False)
            assert repaired["status"] == 0
            result.update(read_error=read_error, after_restore_release=repaired)
        else:
            assert result["status"] == 0
        assert file_manifest(publish.resolve_publication(wiki).root) == file_manifest(candidate)
        assert publish.apply_plan(wiki, candidate, plan, sha(plan))["release_id"] == text(active).strip()
        rows[name] = {"pointer_present_at_stop": observed, **result}
    wiki = parent / "pointer-name-lost-after-ack"
    shutil.copytree(candidate, wiki)
    plan, applied = publish_existing(wiki, candidate)
    pointer = wiki / publish.AREA / "current"
    hidden = pointer.with_name("simulated-lost-current")
    pointer.rename(hidden)
    assert not (wiki / publish.AREA / "publication.journal.json").exists()
    must_stop(lambda: publish.resolve_publication(wiki), "公開ポインターがありません")
    try:
        read_query(wiki, "KabutoMarker", env)
    except RuntimeError as exc:
        assert "公開ポインターがありません" in str(exc)
    else:
        raise AssertionError("CLI の検索が公開ポインターの欠損を見逃しました")
    must_stop(lambda: publish.apply_plan(wiki, candidate, plan, sha(plan)), "公開ポインターがありません")
    raw = parent / "raw-fallback"
    raw.mkdir()
    must_stop(lambda: live.begin(wiki, raw, "公開ポインター喪失後のライブ書き込み"), "公開版")
    hidden.rename(pointer)
    assert publish.resolve_publication(wiki).release_id == applied["release_id"]
    rows["pointer_name_lost_after_ack"] = {"retry_stopped": True, "live_begin_stopped": True}

    for key, item, expected in (
        ("marker_missing", wiki / publish.MARKER, "公開状態の印が一致しません"),
        ("head_missing", wiki / publish.AREA / publish.HEAD, "先頭の完了記録"),
        ("receipt_missing", wiki / publish.AREA / "receipts" / f"{plan['plan_id']}.json", "完了記録がないか"),
        ("whole_cache_missing", wiki / ".wiki-cache", "公開ポインターがありません"),
        ("payload_missing", publish.resolve_publication(wiki).root / "sources/seed.md", "公開ファイルの一覧"),
    ):
        hidden = parent / f"simulated-{key}"
        item.rename(hidden)
        # 状態の違反ごとに読み手、同じ承認の再実行、復旧がいずれも停止することを確かめる。
        operations = (
            lambda: publish.resolve_publication(wiki),
            lambda: publish.apply_plan(wiki, candidate, plan, sha(plan)),
            lambda: publish.recover(wiki),
        )
        reasons = (expected, "公開の管理領域がありません", "公開の管理領域がありません") if key == "whole_cache_missing" else (expected,) * 3
        messages = [must_stop(operation, reason) for operation, reason in zip(operations, reasons)]
        assert not item.exists()
        hidden.rename(item)
        assert publish.resolve_publication(wiki).release_id == applied["release_id"]
        rows[key] = messages

    record = wiki / publish.AREA / "receipts" / f"{plan['plan_id']}.json"
    actual_record = record.read_bytes()
    save(record, publish.encoded({**applied, "plan_sha256": "1" * 64}))
    rows["receipt_mismatch"] = must_stop(lambda: publish.read_receipt(wiki, plan["plan_id"]), "完了記録")
    save(record, actual_record)

    orphan = parent / "staging-orphan"
    shutil.copytree(candidate, orphan)
    plan, _ = publish_existing(orphan, candidate, stop="before_journal", env=env)
    staging = orphan / publish.AREA / "staging"
    assert len(list(staging.iterdir())) == 1 and publish.resolve_publication(orphan) is None
    restored = recover_in_process(orphan, env, is_live=False)
    assert restored["status"] == 0 and restored["value"] is None
    publish.apply_plan(orphan, candidate, plan, sha(plan))
    assert publish.resolve_publication(orphan) is not None
    rows["before_journal"] = {"retry_published": True, "orphan_after_retry": len(list(staging.iterdir()))}

    for key in ("damaged_initial_candidate", "live_changed_after_initial_journal"):
        initial = parent / key
        shutil.copytree(candidate, initial)
        plan, _ = publish_existing(initial, candidate, stop="before_pointer", env=env)
        management = initial / publish.AREA
        tx = fixture.read_json(management / publish.JOURNAL)
        release = management / "releases" / tx["release_id"]
        if key == "damaged_initial_candidate":
            save(release / "wiki/index.md", "# 壊れた候補\n")
        else:
            save(initial / "sources/live-newer.md", "# 日誌の後に変更されたライブ\n")
        result = recover_in_process(initial, env, is_live=False)
        assert result["status"] == 0 and result["value"]["state"] == "aborted"
        assert not (management / publish.JOURNAL).exists()
        assert (management / "quarantine" / tx["release_id"]).is_dir()
        assert publish.resolve_publication(initial) is None
        live.begin(initial, raw, "切り替えを打ち切った後のライブ")
        rows[key] = {"journal_closed": True, "quarantined": True, "live_remains_available": True}
    return rows


def release_worker(plan_file, gate, ready):
    plan = json.loads(plan_file.read_bytes())
    sync_start(gate, ready)
    started = perf_counter()
    bases = []

    def same_base(attempt, release_id):
        bases.append(release_id)
        if attempt != 1:
            return
        save(ready.with_name(ready.name + ".prepared"), release_id)
        deadline = perf_counter() + 180
        while len(list(gate.parent.glob("ready-*.prepared"))) < plan["writers"]:
            if perf_counter() >= deadline:
                raise TimeoutError("同じ基準版からの公開候補を待ちきれません")
            sleep(.02)

    try:
        result = fixture.ingest(Path(plan["wiki"]), plan["approval"], plan["id"], after_prepare=same_base)
    except publish.Conflict as exc:
        return {"status": "held", "attempts": len(bases), "first_base": bases[0] if bases else None,
                "elapsed_s": perf_counter() - started, "reason": str(exc)}
    return {"status": "published", "attempts": result["attempts"], "first_base": bases[0],
            "elapsed_s": perf_counter() - started, "release_id": result["release_id"]}


def release_load(parent, candidate, env):
    rows = {}
    for writers in (1, 4, 8):
        wiki = parent / f"wiki-{writers}"
        shutil.copytree(candidate, wiki)
        _, initial = publish_existing(wiki, candidate)
        base = publish.resolve_publication(wiki, initial["release_id"])
        plans = []
        for i in range(writers):
            name = f"release-load-{writers}-{i}"
            plans.append({"name": name, "wiki": str(wiki), "id": uuid4().hex, "writers": writers,
                          "approval": {"definition_id": base.definition_id,
                                       "intent": {"source": name, "maker": "same-maker", "part": "SAME-PART",
                                                  "quote": f"証拠 {i} は同じ製品について記述する。"}}})
        wave = run_wave(parent / f"wave-{writers}", plans, env, "release-worker")
        final = publish.resolve_publication(wiki)
        citations = fixture.state_of(final)["citations"]
        successes = [row for row in wave["samples"] if row["status"] == "published"]
        assert all(row["first_base"] == base.release_id for row in wave["samples"])
        assert {name for name in citations if name.startswith("release-load-")} == {row["name"] for row in successes}
        wave["published"] = len(successes)
        wave["held"] = writers - len(successes)
        rows[str(writers)] = wave
        print(f"公開版の {writers} 並行の測定完了", file=sys.stderr, flush=True)
    return rows


def stats(waves):
    def describe(values):
        ordered = sorted(values)
        return {f"p{q}": ordered[math.ceil(len(ordered) * q / 100) - 1] for q in (50, 95, 100)}

    return {count: {"n": sum(len(wave["samples"]) for wave in runs),
                    "wave_s": describe([wave["wave_s"] for wave in runs]),
                    **{key: describe([sample[key] for wave in runs for sample in wave["samples"]])
                       for key in ("elapsed_s", "prepare_s", "wait_s", "held_s")}}
            for count, runs in waves.items()}


def scale_check(parent, pages, env):
    checks = []
    for multiplier in (1, 2):
        count = multiplier * pages
        raw_count = multiplier * RAW_COUNT
        wiki, raw = prepare_live(parent / f"size-{count}", count, raw_count)
        plans = [new_plan(wiki, raw, f"size-{count}-{i}", i) for i in range(4)]
        wave = run_wave(parent / f"wave-{count}", plans, env)
        for plan in plans:
            verify_live(wiki, plan, (True,) * 4)
        checks.append({"pages": count, "raw_files": raw_count, **wave})
    return checks


def run(output, pages, repetitions, section):
    with TemporaryDirectory(prefix="info-hive-rollout-") as temp:
        root = Path(temp)
        env = env_for(root)
        os.environ.update({k: env[k] for k in ("INFO_HIVE_DATA_DIR", "PYTHONUTF8")})
        outcome = {"platform": platform.platform(), "pages": pages, "repetitions": repetitions}
        if section in ("all", "performance"):
            result = benchmark(root / "load", pages, repetitions, env)
            outcome["performance"] = {**result, "summary": stats(result["waves"])}
            save(output, publish.encoded(outcome))
        if section in ("all", "recovery"):
            outcome["live_recovery"] = live_faults(root / "live-faults", pages, env)
            outcome["cutover"], candidate = switch_trial(root / "switch", pages, env)
            outcome["publication_recovery"] = publication_faults(root / "publication-faults", candidate, env)
            outcome["cutover_and_integrity_checks_passed"] = True
            save(output, publish.encoded(outcome))
        if section == "release-load":
            candidate = root / "candidate"
            create_public_candidate(candidate, pages // 2)
        if section in ("all", "release-load"):
            outcome["publication_load"] = release_load(root / "release-load", candidate, env)
            save(output, publish.encoded(outcome))
        if section in ("all", "scale"):
            outcome["scale_check"] = scale_check(root / "scale", pages, env)
        save(output, publish.encoded(outcome))


def main():
    args = sys.argv[1:]
    if args[0:1] == ["write-worker"]:
        print(json.dumps(write_worker(*map(Path, args[1:]))))
    elif args[0:1] == ["release-worker"]:
        print(json.dumps(release_worker(*map(Path, args[1:]))))
    elif args[0:1] == ["live-crash"]:
        live.apply(Path(args[1]), args[2], checkpoint=checkpoint_at(args[3]))
    elif args[0:1] == ["live-rollback-crash"]:
        remove = live.remove

        def stop_after_marker(guard, target):
            remove(guard, target)
            if target.name == publish.LIVE_TRANSACTION:
                os._exit(71)

        def rollback_after_write(point):
            if point == "after_write:0":
                raise OSError("戻す経路を試すための試験エラー")

        live.remove = stop_after_marker
        live.apply(Path(args[1]), args[2], checkpoint=rollback_after_write)
    elif args[0:1] == ["publication-crash"]:
        _, wiki, source, plan, approved, point = args
        publish.apply_plan(Path(wiki), Path(source), json.loads(Path(plan).read_bytes()), approved,
                           checkpoint=checkpoint_at(point))
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("--output", required=True, type=Path)
        parser.add_argument("--pages", type=int, default=192)
        parser.add_argument("--repetitions", type=int, default=3)
        parser.add_argument("--section", choices=("all", "performance", "recovery", "release-load", "scale"), default="all")
        options = parser.parse_args(args)
        if options.pages < 16 or options.repetitions < 1:
            parser.error("ページは 16 以上、試行回数は 1 以上にしてください")
        run(options.output, options.pages, options.repetitions, options.section)


if __name__ == "__main__":
    main()
