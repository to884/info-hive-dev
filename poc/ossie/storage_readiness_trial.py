"""隔離 wiki の承認済み保存、停止、別ディスクからの復元を計測する。"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Event, Thread
from time import perf_counter, sleep

import rollout_trial as trial
from publication_trial import frontmatter
import wiki_apply as publish
from wiki_fsguard import WriteGuard
import wiki_live_apply as live
import wiki_live_return as cutback
import wiki_public_save as save
import wiki_republish as republish


HERE = Path(__file__).resolve()
WIKI_SIZE = 195
LIVE_SIZE = 192
RAW_SIZE = 160
OPS = ("ingest", "query", "learn")


def elapsed(start):
    return round(perf_counter() - start, 4)


def put(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))


def snapshot(root):
    return {p.relative_to(root).as_posix(): sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}


def children(mode, args, env):
    return subprocess.Popen([sys.executable, "-B", str(HERE), mode, *map(str, args)],
                            encoding="utf-8", env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def output(child, timeout=300):
    stdout, stderr = child.communicate(timeout=timeout)
    if child.returncode:
        raise RuntimeError(f"子プロセス終了コード {child.returncode}: {stderr or stdout}")
    return json.loads(stdout)


def ready(paths, workers):
    deadline = perf_counter() + 180
    while not all(path.is_file() for path in paths):
        for worker in workers:
            if worker.poll() is not None:
                output(worker)
                raise RuntimeError("検証位置を示す前に子プロセスが終わりました")
        if perf_counter() >= deadline:
            raise TimeoutError("検証位置を待ちきれません")
        sleep(.02)


def cleanup(workers):
    for child in workers:
        if child.poll() is None:
            child.kill()
        child.communicate(timeout=20)


def cli(script, *args, env, expected=0):
    command = [sys.executable, "-B", str(trial.SCRIPT / script), *map(str, args)]
    p = subprocess.run(command, capture_output=True, encoding="utf-8", env=env, timeout=180)
    if p.returncode != expected:
        raise RuntimeError(f"{script} の終了コード {p.returncode}: {p.stderr or p.stdout}")
    return json.loads(p.stdout) if expected == 0 else p.stderr.strip()


def seed(parent, candidate):
    staged, raw = trial.prepare_live(parent, 2, RAW_SIZE)
    # 同じ wiki で 192 ライブ記事と 195 公開記事を用意する。
    wiki = parent / "wiki"
    staged.rename(parent / "raw-fixture-input")
    shutil.copytree(candidate, wiki)
    for path in sorted((wiki / "sources").glob("release-seed-*.md"))[:WIKI_SIZE-LIVE_SIZE]:
        path.unlink()
    raw_hashes = snapshot(raw)
    assert len(raw_hashes) == RAW_SIZE
    assert sum(live.is_page_path(name) for name in publish.live_files(WriteGuard(wiki))) == LIVE_SIZE
    plan, result = trial.publish_existing(wiki, candidate)
    assert sum(live.is_page_path(name) for name in plan["files"]) == WIKI_SIZE
    return wiki, raw, result["release_id"], raw_hashes


def draft(wiki, raw, slug, operation="query", edit=None):
    start = perf_counter()
    prepared = live.begin(wiki, raw, slug, allow_publication=True)
    work = live.work_directory(prepared["apply_dir"])
    plan = live.read_plan(work)
    guard = live.plan_wiki(plan)
    kind = "synthesis" if operation == "query" else "source"
    group = "synthesis" if kind == "synthesis" else "sources"
    relative = f"{group}/{slug}.md"
    details = {"type": kind, "title": slug, "sources": ["sources/seed"]}
    if kind == "source":
        original = raw / "group-0" / "original-000.txt"
        details.update(raw=f"raw/{original.relative_to(raw).as_posix()}", raw_sha256=sha256(original.read_bytes()).hexdigest())
    put(Path(live.register(work, plan, guard, "new", relative)["path"]),
        frontmatter(details, f"{slug} の記録。[[sources/seed]]"))
    if edit:
        target = Path(live.register(work, plan, guard, "edit", edit)["path"])
        put(target, target.read_bytes() + f"\n{slug} の追記。\n".encode("utf-8"))
    heading = f"## [{trial.DATE}] {operation} | {slug}"
    plan["operations"] = [
        {"kind": "index-add", "file": "index.md", "section": "## シンセシス" if kind == "synthesis" else "## ソース",
         "nth": None, "line": f"- [[{group}/{slug}]]: 隔離試験"},
        {"kind": "log-entry", "heading": heading, "nth": None, "lines": []},
    ]
    live.write(work, work.root / "plan.json", publish.encoded(plan), replace=True)
    preview = save.public_preview(work, plan, guard) if "publication" in plan else live.preview(work, plan, guard)
    return {"wiki": str(wiki), "directory": str(work.root), "id": plan["plan_id"],
            "sha": preview["plan_sha256"], "page": relative, "heading": heading, "slug": slug,
            "prepare_s": elapsed(start), "operation": operation, "edit": edit}


def verify_once(root, plan):
    assert (root / plan["page"]).is_file(), plan["slug"]
    assert (root / "index.md").read_text(encoding="utf-8").count(f"[[{plan['page'][:-3]}]]") == 1, plan["slug"]
    assert (root / "log.md").read_text(encoding="utf-8").splitlines().count(plan["heading"]) == 1, plan["slug"]


def describe_samples(values):
    if not values:
        return {}
    ordered = sorted(values)
    return {key: ordered[math.ceil(len(ordered) * p) - 1] for key, p in (("p50", .5), ("p95", .95), ("max", 1))}


def read_probe(wiki, pinned, stop, readings):
    while not stop.is_set():
        start = perf_counter()
        try:
            view = publish.resolve_publication(wiki, pinned)
            found = publish.search_publication(view, "KabutoMarker", 5, None, [], None, 1)
            page = publish.publication_page(view, "sources/seed.md")
            assert found["release_id"] == view.release_id == page["release_id"]
            assert pinned is None or view.release_id == pinned
            assert "KabutoMarker" in page["body"]
        except (OSError, ValueError, AssertionError) as error:
            readings.append({"s": elapsed(start), "error": str(error)})
        else:
            readings.append({"s": elapsed(start)})
        stop.wait(2)


def workload_worker(plan_file, gate, waiting):
    plan = json.loads(Path(plan_file).read_bytes())
    original = WriteGuard.hold_lock
    queue, hold = [], []
    attempts = 0

    @contextmanager
    def timed(self, path, **kwargs):
        if path.name != "apply.lock":
            with original(self, path, **kwargs) as result:
                yield result
            return
        start = perf_counter()
        with original(self, path, **kwargs) as result:
            queue.append(perf_counter() - start)
            acquired = perf_counter()
            try:
                yield result
            finally:
                hold.append(perf_counter() - acquired)

    def checkpoint(point):
        nonlocal attempts
        if point == "save_prepared":
            attempts += 1

    WriteGuard.hold_lock = timed
    trial.sync_start(Path(gate), Path(waiting))
    start = perf_counter()
    result = save.queue_save(plan["directory"], plan["sha"], checkpoint=checkpoint)
    return {"state": result["state"], "seconds": elapsed(start), "prepare_s": plan["prepare_s"],
            "lock_wait_s": round(sum(queue), 4), "lock_held_s": round(sum(hold), 4), "attempts": attempts}


def workload(parent, candidate, env, repeats, mixed=False):
    waves = []
    profiles = (8,) if mixed else (1, 4, 8)
    for n in profiles:
        for iteration in range(repeats):
            zone = parent / f"writers-{n}-{iteration}"
            wiki, raw, pinned, originals = seed(zone, candidate)
            plans = [draft(wiki, raw, f"storage-{n}-{iteration}-{i}", OPS[i % len(OPS)],
                           "concepts/platform.md" if mixed and i in (0, 2) else None) for i in range(n)]
            workers, signals, reads, default_reads = [], [], [], []
            gate = zone / "go"
            stop = Event()
            readers = [Thread(target=read_probe, args=(wiki, pinned, stop, reads), daemon=True)]
            if mixed:
                readers.append(Thread(target=read_probe, args=(wiki, None, stop, default_reads), daemon=True))
            try:
                for i, plan in enumerate(plans):
                    item, signal = zone / f"plan-{i}.json", zone / f"ready-{i}"
                    put(item, publish.encoded(plan))
                    workers.append(children("workload-worker", (item, gate, signal), env))
                    signals.append(signal)
                ready(signals, workers)
                for reader in readers:
                    reader.start()
                start = perf_counter()
                put(gate, "go\n")
                samples = [output(child) for child in workers]
                first_pass = elapsed(start)
                for plan, row in zip(plans, samples):
                    if row["state"] == "pending":
                        begin = perf_counter()
                        retry = save.resume(wiki, plan["id"], plan["sha"])
                        row["retry_state"] = retry["state"]
                        row["retry_s"] = elapsed(begin)
                        if retry["state"] == "pending":
                            row["retry_reason"] = retry["reason"]
                recovered = elapsed(start)
                stop.set()
                tip = publish.resolve_publication(wiki)
                conflicts = []
                for plan, row in zip(plans, samples):
                    if row.get("retry_state") == "pending":
                        assert mixed and plan["edit"] and "ページの基準版" in row["retry_reason"]
                        assert not (tip.root / plan["page"]).exists()
                        assert plan["heading"] not in (tip.root / "log.md").read_text(encoding="utf-8")
                        assert plan["slug"] not in (tip.root / "index.md").read_text(encoding="utf-8")
                        conflicts.append(plan["id"])
                    else:
                        verify_once(tip.root, plan)
                        if plan["edit"]:
                            assert (tip.root / plan["edit"]).read_text(encoding="utf-8").count(plan["slug"]) == 1
                assert len(conflicts) == int(mixed)
                assert {row["plan_id"] for row in save.pending_public(wiki)} == set(conflicts)
                assert snapshot(raw) == originals
                assert publish.resolve_publication(wiki, pinned) is not None
            finally:
                stop.set()
                for reader in readers:
                    if reader.ident:
                        reader.join(30)
                        assert not reader.is_alive(), "読み取りの計測スレッドが終了しません"
                cleanup(workers)
            waves.append({"writers": n, "first_pass_s": first_pass, "after_retries_s": recovered,
                          "awaiting_new_approval": conflicts, "samples": samples,
                          "pinned_reader": reads, "default_reader": default_reads})
            print(f"{n} 並行 {iteration+1} 回目の検証が完了", file=sys.stderr, flush=True)
    summary = {}
    for n in profiles:
        group = [wave for wave in waves if wave["writers"] == n]
        rows = [row for wave in group for row in wave["samples"]]
        probes = [read for wave in group for read in wave["pinned_reader"]]
        summary[n] = {"n": len(rows), "pending": sum(row["state"] == "pending" for row in rows),
                      "read_n": len(probes), "read_errors": sum("error" in row for row in probes),
                      "read_s": describe_samples([row["s"] for row in probes if "error" not in row]),
                      "after_retries_s": describe_samples([wave["after_retries_s"] for wave in group]),
                      **{key: describe_samples([row[key] for row in rows])
                         for key in ("seconds", "lock_wait_s", "lock_held_s")}}
    return {"waves": waves, "summary": summary}


def crash_worker(plan_file, checkpoint_name, marker):
    plan = json.loads(Path(plan_file).read_bytes())

    def check(point):
        if point == checkpoint_name:
            put(Path(marker), point)
            while True:
                sleep(1)

    save.queue_save(plan["directory"], plan["sha"], checkpoint=check)


def stop_at(root, plan, checkpoint, env):
    item, marker = root / f"{plan['slug']}.json", root / f"{plan['slug']}.ready"
    put(item, publish.encoded(plan))
    worker = children("crash-worker", (item, checkpoint, marker), env)
    try:
        ready([marker], [worker])
        start = perf_counter()
        worker.kill()
        worker.communicate(timeout=20)
        assert worker.returncode not in (None, 0)
        return start
    finally:
        cleanup([worker])


def replay(wiki, plan, env):
    return cli("wiki_apply.py", "retry", "--wiki", wiki, "--plan-id", plan["id"],
               "--expect-sha256", plan["sha"], env=env)


def verify_pin(wiki, release_id, env):
    result = cli("wiki_search.py", "KabutoMarker", "--wiki", wiki, "--release-id", release_id,
                 "--no-embed", "--json", env=env)
    assert result["release_id"] == release_id
    assert "sources/seed.md" in json.dumps(result)
    archived = publish.resolve_publication(wiki, release_id)
    assert "KabutoMarker" in publish.publication_page(archived, "sources/seed.md")["body"]


def restore_contents(backup, destination, quarantine):
    quarantine.mkdir()
    for path in sorted(destination.iterdir()):
        path.rename(quarantine / path.name)
    shutil.copytree(backup, destination, dirs_exist_ok=True)


def receipts(wiki):
    guard = WriteGuard(wiki)
    area = guard.root / publish.AREA
    active = publish.read_active(guard, area)
    return {entry["plan_id"]: publish.verify_release(guard, area, release, entry, payload=False)
            for release, entry in publish.history(guard, area, active)}


def recovery(parent, candidate, backup, env):
    wiki, raw, initial, originals = seed(parent, candidate)
    fault_rows = []
    for point in ("save_queued", "after_journal", "pointer_written"):
        plan = draft(wiki, raw, "stop-" + point.replace("_", "-"))
        stop = stop_at(parent, plan, point, env)
        ledger = cli("wiki_apply.py", "recover", "--wiki", wiki, env=env)
        inspected = elapsed(stop)
        pending = {row["plan_id"]: row["plan_sha256"] for row in save.pending_public(wiki)}
        assert pending[plan["id"]] == plan["sha"]
        ack = replay(wiki, plan, env)
        assert ack["state"] in {"applied", "already_applied"}
        assert replay(wiki, plan, env)["release_id"] == ack["release_id"]
        tip = publish.resolve_publication(wiki)
        assert tip.release_id == ack["release_id"]
        verify_once(tip.root, plan)
        verify_pin(wiki, initial, env)
        fault_rows.append({"boundary": point, "journal_recovery_s": inspected,
                           "verified_read_and_retry_s": elapsed(stop),
                           "journal_advanced": ledger is not None, "pending_after_recover": plan["id"] in pending,
                           "verified_plan": ack["plan_id"]})
    # 再公開の履歴には wiki の実体を指す切り戻しの記録が残る。
    down = cutback.build_plan(wiki, raw)
    cutback.apply(wiki, down, cutback.approval(down))
    accepted = draft(wiki, raw, "before-backup-live", "learn")
    live.apply(accepted["directory"], accepted["sha"])
    next_source = parent / "next-source"
    next_plan = republish.build_plan(wiki, raw, next_source)
    saved_release = publish.apply_plan(wiki, next_source, next_plan, trial.sha(next_plan))["release_id"]
    held = draft(wiki, raw, "approved-at-backup")
    stop_at(parent, held, "save_queued", env)
    identity = list(WriteGuard(wiki).root_id)
    backup_start = perf_counter()
    shutil.copytree(wiki, backup / "wiki")
    shutil.copytree(raw, backup / "raw")
    copy_s = elapsed(backup_start)
    inventory = {"wiki": snapshot(wiki), "raw": snapshot(raw), "receipts": receipts(wiki)}
    assert all(inventory[name] == snapshot(backup / name) for name in ("wiki", "raw"))
    put(backup / "manifest.json", publish.encoded(inventory))
    captured = perf_counter()
    later = draft(wiki, raw, "after-backup")
    later_ack = save.queue_save(later["directory"], later["sha"])
    assert later_ack["state"] == "applied"
    completed = receipts(wiki)
    acknowledged_id = save.load_record(WriteGuard(wiki), later["id"])["attempt"]
    assert completed[acknowledged_id]["release_id"] == later_ack["release_id"]
    witness = backup / "acknowledged-before-fault.json"
    put(witness, publish.encoded(completed))
    old = wiki / publish.AREA / "current"
    old.rename(parent / "fault-current")
    failure = cli("wiki_apply.py", "view", "--wiki", wiki, env=env, expected=1)
    assert "ポインターがありません" in failure, failure
    failure_at = perf_counter()

    # 同じパスを再作成する復元では、ファイルの指紋が一致していても実体が変わる。
    offline = parent / "original-wiki-root"
    wiki.rename(offline)
    fresh_start = perf_counter()
    shutil.copytree(backup / "wiki", wiki)
    assert snapshot(wiki) == inventory["wiki"]
    new_directory_bytes_s = elapsed(fresh_start)
    fresh = cli("wiki_apply.py", "view", "--wiki", wiki, env=env, expected=1)
    fresh_pin = cli("wiki_apply.py", "view", "--wiki", wiki, "--release-id", initial, env=env, expected=1)
    assert "切り戻し" in fresh and "切り戻し" in fresh_pin
    changed_identity = list(WriteGuard(wiki).root_id) != identity
    assert changed_identity
    wiki.rename(parent / "recreated-root")
    offline.rename(wiki)

    restore_start = perf_counter()
    restore_contents(backup / "wiki", wiki, parent / "old-wiki-contents")
    restore_contents(backup / "raw", raw, parent / "old-raw-contents")
    restore_copy_s = elapsed(restore_start)
    inventory = json.loads((backup / "manifest.json").read_bytes())
    assert snapshot(wiki) == inventory["wiki"] and snapshot(raw) == originals == inventory["raw"]
    assert list(WriteGuard(wiki).root_id) == identity
    assert cli("wiki_apply.py", "view", "--wiki", wiki, env=env)["release_id"] == saved_release
    verify_pin(wiki, saved_release, env)
    verify_pin(wiki, initial, env)
    before_write_s = elapsed(restore_start)
    restored = receipts(wiki)
    assert restored == inventory["receipts"]
    witnessed = json.loads(witness.read_bytes())
    assert all(witnessed.get(key) == row for key, row in restored.items())
    lost = witnessed.keys() - restored.keys()
    assert lost == {acknowledged_id}
    held_record = next(row for row in save.pending_public(wiki) if row["plan_id"] == held["id"])
    assert held_record["plan_sha256"] == held["sha"]
    assert "承認済みの保存の記録がありません" in cli(
        "wiki_apply.py", "retry", "--wiki", wiki, "--plan-id", later["id"], "--expect-sha256", later["sha"],
        env=env, expected=1)
    pending_ack = replay(wiki, held, env)
    assert replay(wiki, held, env)["release_id"] == pending_ack["release_id"]
    c = publish.resolve_publication(wiki)
    verify_once(c.root, held)
    verify_once(c.root, accepted)
    assert not (c.root / later["page"]).exists()
    assert snapshot(raw) == originals
    writes_s = elapsed(restore_start)

    # 廃止された固定版は別の版に切り替えない。
    retired = saved_release
    publish.retire(wiki, retired)
    stopped_pin = cli("wiki_apply.py", "view", "--wiki", wiki, "--release-id", retired, env=env, expected=1)
    assert "取り下げ" in stopped_pin
    assert cli("wiki_apply.py", "view", "--wiki", wiki, env=env)["release_id"] == c.release_id
    return {"stops": fault_rows, "backup": {"copy_s": copy_s,
                "files": {kind: len(paths) for kind, paths in inventory.items()},
                "backup_to_fault_s": round(failure_at - captured, 4), "witnessed_receipts": witnessed,
                "restored_receipt_ids": sorted(restored), "acknowledged_receipts_missing": sorted(lost),
                "approved_pending_at_backup_replayed": pending_ack["plan_id"], "missing_current_rejected": failure,
                "new_root_contents_copied_and_verified_s": new_directory_bytes_s,
                "new_root_same_path_identity_changed": changed_identity,
                "new_root_default_rejected": fresh, "new_root_pinned_rejected": fresh_pin,
                "same_root_copy_s": restore_copy_s, "same_root_verified_read_s": before_write_s,
                "same_root_verified_write_s": writes_s, "sha256_verified": True, "raw_preserved": True},
            "retirement": {"pin_rejected": stopped_pin, "default_preserved": True}}


def retirement_trial(parent, candidate, backup, env):
    wiki, raw, archived, _ = seed(parent, candidate)
    next_save = draft(wiki, raw, "new-tip-before-retirement")
    response = save.queue_save(next_save["directory"], next_save["sha"])
    assert response["state"] == "applied"
    current = response["release_id"]
    shutil.copytree(wiki, backup / "wiki")
    publish.retire(wiki, archived)
    retired = cli("wiki_apply.py", "view", "--wiki", wiki, "--release-id", archived, env=env, expected=1)
    assert "取り下げ" in retired
    witness = backup / "retired-after-backup.json"
    put(witness, publish.encoded({"release_id": archived}))
    restore_contents(backup / "wiki", wiki, parent / "offline")
    verify_pin(wiki, archived, env)
    from_witness = json.loads(witness.read_bytes())["release_id"]
    assert from_witness == archived
    publish.retire(wiki, from_witness)
    final = cli("wiki_apply.py", "view", "--wiki", wiki, "--release-id", archived, env=env, expected=1)
    assert final == retired
    assert cli("wiki_apply.py", "view", "--wiki", wiki, env=env)["release_id"] == current
    return {"archived_release": archived, "current_release": current, "pre_restore_rejection": retired,
            "old_backup_restored_pin": archived, "reapplied_record_rejection": final}


def windows_volumes(work_parent, backup_parent):
    if os.name != "nt":
        return None
    letters = [Path(path).resolve().drive.removesuffix(":") for path in (work_parent, backup_parent)]
    if not all(len(letter) == 1 and letter.isascii() and letter.isalpha() for letter in letters):
        raise ValueError("試験とバックアップにはドライブ文字を持つローカルボリュームを指定してください")
    query = ("$ErrorActionPreference='Stop'; @(foreach ($letter in @('" + "','".join(letters) +
             "')) { $p=Get-Partition -DriveLetter $letter; $v=Get-Volume -DriveLetter $letter; "
             "$d=Get-Disk -Number $p.DiskNumber; "
             "[ordered]@{letter=$letter; disk=$d.Number; bus=[string]$d.BusType; fs=$v.FileSystem} "
             "}) | ConvertTo-Json -Compress")
    result = subprocess.run(["powershell.exe", "-NoProfile", "-Command", query], encoding="utf-8",
                            capture_output=True, check=True, timeout=30)
    volumes = json.loads(result.stdout)
    if volumes[0]["disk"] == volumes[1]["disk"]:
        raise ValueError("試験とバックアップには別の物理ディスクを指定してください")
    return volumes


def run(work_parent, backup_parent, result, section, repeats):
    volumes = windows_volumes(work_parent, backup_parent)
    with TemporaryDirectory(dir=work_parent, prefix="ih-storage-") as root_name:
        root = Path(root_name).resolve()
        env = trial.env_for(root)
        os.environ.update({key: env[key] for key in ("INFO_HIVE_DATA_DIR", "PYTHONUTF8")})
        candidate = root / "candidate"
        trial.create_public_candidate(candidate, 96)
        with (candidate / "index.md").open("a", encoding="utf-8") as stream:
            stream.write("\n## シンセシス\n")
        record = {"platform": platform.platform(), "test_volume": root.anchor,
                  "backup_volume": str(backup_parent.anchor), "storage": volumes, "repetitions": repeats,
                  "public_articles": WIKI_SIZE, "live_articles": LIVE_SIZE, "raw_files": RAW_SIZE,
                  "public_files": len(publish.source_files(candidate))}
        if section in {"all", "recovery"}:
            with TemporaryDirectory(dir=backup_parent, prefix="ih-storage-backup-") as backup:
                record["recovery"] = recovery(root / "recovery", candidate, Path(backup), env)
            put(result, publish.encoded(record))
            print("別ディスクからの復元試験が完了", file=sys.stderr, flush=True)
        if section in {"all", "load"}:
            record["load"] = workload(root / "load", candidate, env, repeats)
        if section == "mixed":
            record["mixed_load"] = workload(root / "mixed", candidate, env, repeats, mixed=True)
        if section == "retirement":
            with TemporaryDirectory(dir=backup_parent, prefix="ih-storage-backup-") as backup:
                record["retirement"] = retirement_trial(root / "retirement", candidate, Path(backup), env)
        put(result, publish.encoded(record))


def main():
    args = sys.argv[1:]
    if args[0:1] == ["workload-worker"]:
        print(json.dumps(workload_worker(*args[1:]), ensure_ascii=False))
    elif args[0:1] == ["crash-worker"]:
        crash_worker(*args[1:])
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("--work-parent", required=True, type=Path)
        parser.add_argument("--backup-parent", required=True, type=Path)
        parser.add_argument("--result", required=True, type=Path)
        parser.add_argument("--section", choices=("all", "load", "mixed", "recovery", "retirement"), default="all")
        parser.add_argument("--repeats", type=int, default=2)
        options = parser.parse_args(args)
        if options.repeats < 1:
            parser.error("試行回数は 1 以上を指定してください")
        run(options.work_parent, options.backup_parent, options.result, options.section, options.repeats)


if __name__ == "__main__":
    main()
