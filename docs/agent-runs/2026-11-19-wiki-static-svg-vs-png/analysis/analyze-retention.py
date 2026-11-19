"""保持メモリをブラウザ、プロセス、段階別に検証して集計する。"""

import argparse
from hashlib import sha256
import json
from pathlib import Path
from statistics import median

CONDITIONS = ["mermaid", "bundle", "inert", "minimal"]
BLOB_CONDITIONS = ["srcdoc", "blob"]
RENDERER_CHANNELS = {"chromium": None, "chromium-full": "chromium", "chrome": "chrome", "msedge": "msedge"}
RENDERER_PHASES = ["empty", "after_dark", "after_clear_gc", "after_provider_test"]
BROWSERS = {"chromium", "firefox", "webkit", "chrome", "msedge"}
PHASES = ["empty", "after_light", "after_dark", "after_idle", "after_gc",
          "after_clear_gc", "after_navigation", "after_navigation_idle", "page_closed", "context_closed"]
WEB = "WebKitWebProcess"
CROSS_CLOCK_TOLERANCE_MS = 20


def summarize_checkpoint(checkpoint, case):
    sample = checkpoint["sample"]
    assert sample["stable"] and checkpoint["phase"] == sample["phase"] and not sample["missing_children"]
    assert sample["run_id"] == case["id"] and sample["root_pid"] == case["pid"]
    after_phase_set = sample["start_utc_ms"] - checkpoint["phaseSetUtcMs"]
    before_observation = checkpoint["observedUtcMs"] - sample["utc_ms"]
    assert sample["start_utc_ms"] <= sample["utc_ms"]
    # 段階の帰属は安定したリビジョンと標本番号で確認する。別ランタイムの時計の照合には小さな差を許す。
    assert min(after_phase_set, before_observation) >= -CROSS_CLOCK_TOLERANCE_MS
    children = {r["pid"]: r for r in sample["process_rows"]}
    assert len(children) == sample["processes"] == len(sample["process_rows"])
    assert set(children) == set(sample["process_ids"]) and case["pid"] in children
    assert sample["private_bytes"] == sum(r["private_bytes"] for r in children.values())
    assert sample["working_set_sum_bytes"] == sum(r["working_set_bytes"] for r in children.values())
    for pid in children:
        parents = set()
        while pid != case["pid"]:
            assert pid not in parents and pid in children
            parents.add(pid)
            pid = children[pid]["parent_pid"]
    process_groups = {}
    for row in children.values():
        group = process_groups.setdefault(row["name"], {"pids": [], "private_bytes": 0, "working_set_bytes": 0})
        group["pids"].append(row["pid"])
        for key in ("private_bytes", "working_set_bytes"):
            group[key] += row[key]
    return {
        "sequence": sample["sequence"],
        "start_minus_phase_set_ms": after_phase_set,
        "observed_minus_sample_end_ms": before_observation,
        "total_private_bytes": sample["private_bytes"],
        "total_working_set_bytes": sample["working_set_sum_bytes"],
        "process_groups": process_groups,
        "outer": checkpoint["outer"],
    }


def web_bytes(point):
    return point["process_groups"].get(WEB, {}).get("private_bytes", 0)


def summarize_renderers(case):
    phases = {point["phase"]: point for point in case["checkpoints"]}
    blob = case["condition"] != "srcdoc"
    expected_roles = {"page", "fig-provider"} if blob else {"page"}
    observed = case["frameProcesses"]
    frame_pids = {row["role"]: row["pid"] for row in observed}
    assert set(frame_pids) == expected_roles and len(frame_pids) == len(observed)
    for row in observed:
        assert row["events"] and all(
            event["pid"] == row["pid"] and event["cat"] == "blink.user_timing" and
            event["name"].startswith(f"diag-{case['id']}:") for event in row["events"]
        )
    output = {}
    assert set(case["processTypes"]) == set(RENDERER_PHASES)
    for phase in RENDERER_PHASES:
        point = phases[phase]
        type_rows = case["processTypes"][phase]
        types = {row["pid"]: row["type"] for row in type_rows}
        assert len(types) == len(type_rows) and types[case["pid"]] == "browser"
        rows = point["sample"]["process_rows"]
        by_pid = {row["pid"]: row["private_bytes"] for row in rows}
        frames = {role: by_pid.get(pid) for role, pid in frame_pids.items()}
        if phase == "after_clear_gc":
            assert all(pid in by_pid and types.get(pid) == "renderer" for pid in frame_pids.values())
        totals = {}
        for row in rows:
            kind = types.get(row["pid"], "unclassified")
            totals[kind] = totals.get(kind, 0) + row["private_bytes"]
        output[phase] = {
            "frame_process_private_bytes": frames,
            "total_by_process_type": totals,
            "renderer_private_bytes_without_identified_frames": sum(
                size for pid, size in by_pid.items()
                if types.get(pid) == "renderer" and pid not in frame_pids.values()
            ),
        }
    assert phases["after_provider_test"]["outer"]["providers"] == int(case["condition"] == "blob")
    return {"frames": frame_pids, "phases": output}


def analyze(data, directory, smoke):
    blob = data["design"] == "blob-comparison"
    renderer_diagnostics = data.get("rendererDiagnostics", False)
    provider_lifetime = data.get("blobProviderLifetime")
    if provider_lifetime is not None:
        assert provider_lifetime == "render" and blob and not renderer_diagnostics
    assert data["design"] in ("retention", "blob-comparison") and data["mode"] == "memory"
    browsers = data["browsers"]
    allowed_browsers = set(RENDERER_CHANNELS) if renderer_diagnostics else BROWSERS
    assert browsers and len(browsers) == len(set(browsers)) and set(browsers) <= allowed_browsers
    if not blob:
        assert browsers == ["webkit"]
    webkit_only = browsers == ["webkit"]
    conditions = BLOB_CONDITIONS if blob else CONDITIONS
    phases = PHASES
    repeats = 2
    if renderer_diagnostics:
        assert blob and data["providerWaitMs"] == 10000
        conditions = [*BLOB_CONDITIONS, "blob-remove-provider"]
        phases = [*PHASES[:6], "after_provider_test", *PHASES[6:]]
        repeats = 1
    assert data["inputsUnchanged"] and data["activeCase"] is None
    assert data["freshBrowserPerCase"] and data["samplerEnabled"]
    assert data["conditions"] == [{"name": c, "monitor": True, "prior": []} for c in conditions]
    count, = data["counts"]
    if not smoke:
        assert (count, data["repeats"], data["idleMs"]) == (50, repeats, 10000)
    cases = data["cases"]
    assert len(cases) == len({c["id"] for c in cases}) == len(browsers) * len(conditions) * data["repeats"]
    versions = {}
    for name in browsers:
        matching = [c for c in cases if c["browser"] == name]
        version, = {c["version"] for c in matching}
        versions[name] = version
        if renderer_diagnostics or name in ("chrome", "msedge"):
            assert all(c["channel"] == RENDERER_CHANNELS[name] for c in matching)
            executable, = {c["executableSha256"] for c in matching}
            assert len(executable) == 64 and all(ch in "0123456789abcdef" for ch in executable)
    rows = []
    for index, case in enumerate(cases):
        block, condition_index = divmod(index, len(conditions))
        repeat, browser_index = divmod(block, len(browsers))
        browser = browsers[(browser_index + repeat) % len(browsers)]
        order = conditions if repeat % 2 == 0 else conditions[::-1]
        assert (case["repeat"], case["condition"], case["browser"], case["count"]) == (repeat + 1, order[condition_index], browser, count)
        assert case["ok"] and case["cleanupMethod"] == "owned-browser-kill" and not case.get("cleanupIncomplete")
        assert case["monitored"] and not case["priorCounts"] and not case["warmup"] and case["gcRequested"]
        for multiplier, theme in enumerate(("light", "dark"), 1):
            draw = case[theme]
            assert draw["images"] == draw["successes"] == count
            assert draw["created"] == draw["disposed"] == count * multiplier
            assert draw["active"] == 0 and draw["peakFrames"] == 1
        checkpoints = case["checkpoints"]
        assert [p["phase"] for p in checkpoints] == phases
        raw = json.loads((directory / (case["id"] + "-memory.json")).read_bytes())
        samples = {row["sequence"]: row for row in raw}
        assert len(samples) == case["memory"]["samples"] == len(raw)
        points = {}
        prev_sequence = 0
        for phase, checkpoint in zip(phases, checkpoints, strict=True):
            point = summarize_checkpoint(checkpoint, case)
            sequence = point["sequence"]
            assert sequence > prev_sequence and samples[sequence] == checkpoint["sample"]
            prev_sequence = sequence
            if phase == "after_clear_gc":
                assert point["outer"]["images"] == 0 and point["outer"]["frames"] == 0
            if blob and point["outer"] is not None:
                expected = int(provider_lifetime is None and case["condition"] in conditions[1:] and phase != "empty")
                if phase == "after_provider_test" and case["condition"] == "blob-remove-provider":
                    expected = 0
                assert point["outer"]["providers"] == expected
                assert point["outer"]["frames"] == 0
                assert point["outer"]["tracked"] is None and point["outer"]["alive"] is None
            points[phase] = point
        row = {"id": case["id"], "condition": case["condition"], "repeat": case["repeat"], "phases": points}
        if not webkit_only:
            row["browser"] = browser
        if blob:
            row["decode_ms_with_sampler"] = {theme: case[theme]["decodeMs"] for theme in ("light", "dark")}
        if renderer_diagnostics:
            row["renderers"] = summarize_renderers(case)
        rows.append(row)

    if not webkit_only:
        summaries = {}
        for browser in browsers:
            summaries[browser] = {}
            for condition in conditions:
                group = [r["phases"] for r in rows if r["browser"] == browser and r["condition"] == condition]
                summaries[browser][condition] = {
                    phase: {
                        "total_mib": median([r[phase]["total_private_bytes"] / 2**20 for r in group]),
                        "working_set_sum_mib": median([r[phase]["total_working_set_bytes"] / 2**20 for r in group]),
                        "change_from_empty_mib": [
                            (r[phase]["total_private_bytes"] - r["empty"]["total_private_bytes"]) / 2**20 for r in group
                        ],
                    }
                    for phase in phases
                }
        return {"smoke": smoke, "versions": versions, "cases": rows, "summaries_by_browser": summaries}

    summaries = {}
    for condition in conditions:
        group = [r["phases"] for r in rows if r["condition"] == condition]
        summaries[condition] = {
            phase: {
                "total_mib": median([r[phase]["total_private_bytes"] / 2**20 for r in group]),
                "web_process_mib": median([web_bytes(r[phase]) / 2**20 for r in group]),
                "web_process_group_change_from_empty_mib": [
                    (web_bytes(r[phase]) - web_bytes(r["empty"])) / 2**20 for r in group
                ],
            }
            for phase in PHASES
        }
    return {"smoke": smoke, "cases": rows, "summaries": summaries}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    raw = args.results.read_bytes()
    summary = analyze(json.loads(raw), args.results.parent, args.smoke)
    summary["results_sha256"] = sha256(raw).hexdigest()
    summary["analyzer_sha256"] = sha256(Path(__file__).read_bytes()).hexdigest()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
