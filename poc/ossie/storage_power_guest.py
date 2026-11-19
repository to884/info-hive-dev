"""Windows PE の試験専用仮想マシンで、公開保存の途中に停止を要求する。"""

import ctypes
import json
import os
from pathlib import Path
import sqlite3
import subprocess
from time import perf_counter, sleep
import traceback

from storage_readiness_trial import (
    cli, draft, replay, seed, snapshot, trial, verify_once, verify_pin,
)
import wiki_apply as publish
import wiki_live_apply as live
import wiki_live_return as cutback
import wiki_public_save as save
import wiki_republish as republish
from wiki_fsguard import WriteGuard


POINTS = ("save_queued", "after_journal", "pointer_written")
QUEUED_OPERATIONS = ("query", "ingest", "learn")
LABEL = "IHPOWTEST"


def signal(tag, value):
    # WinPE の表示からホストが読み取る。ネットワークや共有ドライブを使用しない。
    from ctypes import wintypes

    class Coord(ctypes.Structure):
        _fields_ = [("x", ctypes.c_short), ("y", ctypes.c_short)]

    class Rect(ctypes.Structure):
        _fields_ = [(name, ctypes.c_short) for name in ("left", "top", "right", "bottom")]

    class Cell(ctypes.Structure):
        _fields_ = [("char", wintypes.WCHAR), ("style", wintypes.WORD)]

    height, width = 20, 70
    raw = (tag + " " + json.dumps(value, ensure_ascii=True, separators=(",", ":"))).encode("ascii")
    data = (raw[:((height - 1) * (width - 2)) // 2 - 1] + b"\0").hex()
    palette = [13] * 4 + [number for number in range(16) for _ in range(4)] + [13, 13]
    rows = [palette]
    for row in range(height - 1):
        digits = data[row * (width - 2):(row + 1) * (width - 2)]
        rows.append([11] + [int(digit, 16) for digit in digits.ljust(width - 2, "0")] + [11])
    cells = (Cell * (width * height))(*(Cell(" ", index << 4) for row in rows for index in row))
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetStdHandle.argtypes = (wintypes.DWORD,)
    kernel.GetStdHandle.restype = wintypes.HANDLE
    kernel.WriteConsoleOutputW.argtypes = (wintypes.HANDLE, ctypes.POINTER(Cell), Coord, Coord, ctypes.POINTER(Rect))
    kernel.WriteConsoleOutputW.restype = wintypes.BOOL
    region = Rect(0, 0, width - 1, height - 1)
    handle = kernel.GetStdHandle(-11)
    if not kernel.WriteConsoleOutputW(handle, cells, Coord(width, height), Coord(0, 0), ctypes.byref(region)):
        raise ctypes.WinError(ctypes.get_last_error())


def diskpart(commands):
    script = Path("X:/ih-storage-diskpart.txt")
    script.write_text("\n".join(commands) + "\n", encoding="ascii")
    result = subprocess.run(["diskpart", "/s", str(script)], capture_output=True, text=True,
                            encoding="ascii", errors="replace", timeout=120)
    if result.returncode:
        raise RuntimeError(result.stdout or result.stderr)
    return result.stdout


def label_for(letter):
    name = ctypes.create_unicode_buffer(128)
    fs = ctypes.create_unicode_buffer(64)
    if ctypes.windll.kernel32.GetVolumeInformationW(f"{letter}:\\", name, len(name), None, None, None, fs, len(fs)):
        return name.value, fs.value
    return "", ""


def data_volume():
    # 専用 PE の RAM ディスクから起動し、空の 8 GiB 仮想ディスク 1 台だけを初期化する。
    if os.environ.get("SystemDrive", "").upper() != "X:" or not Path("X:/IH/repo").is_dir():
        raise RuntimeError("試験専用の Windows PE から起動してください")
    matches = [letter for letter in "CDEFGHIJKLMNOPQRSTUVWYZ" if label_for(letter)[0] == LABEL]
    if len(matches) == 1 and matches[0] != "W":
        diskpart([f"select volume {matches[0]}", "assign letter=W"])
    elif not matches:
        listed = diskpart(["list disk"])
        rows = [line.strip() for line in listed.splitlines() if line.lstrip().startswith("Disk ") and line.strip()[5:6].isdigit()]
        if (len(rows) != 1 or not rows[0].startswith("Disk 0 ")
                or sum(token in rows[0] for token in ("8192 MB", " 8 GB")) == 0):
            raise RuntimeError("試験用の仮想ディスク 1 台を確認できません")
        diskpart(["select disk 0", "create partition primary", f"format fs=ntfs quick label={LABEL}", "assign letter=W"])
    if label_for("W") != (LABEL, "NTFS"):
        raise RuntimeError("試験用 NTFS ボリュームを確認できません")
    return Path("W:/ih-storage-guest")


def write_state(root, state):
    guard = WriteGuard(root)
    guard.write_bytes(root / "state.json", publish.encoded(state), replace=True, write_through=True)


def verify_image(root, wiki, raw, state, env):
    if "image_target" not in state:
        down = cutback.build_plan(wiki, raw)
        cutback.apply(wiki, down, cutback.approval(down))
        plan = draft(wiki, raw, "vm-image-live")
        live.apply(plan["directory"], plan["sha"])
        candidate = root / "image-candidate"
        next_plan = republish.build_plan(wiki, raw, candidate)
        result = publish.apply_plan(wiki, candidate, next_plan, trial.sha(next_plan))
        state["image_target"] = {"release": result["release_id"], "identity": list(WriteGuard(wiki).root_id), "plan": plan}
        write_state(root, state)
    target = state["image_target"]
    assert list(WriteGuard(wiki).root_id) == target["identity"]
    view = publish.resolve_publication(wiki)
    assert view.release_id == target["release"]
    verify_once(view.root, target["plan"])
    verify_pin(wiki, state["pinned"], env)
    verify_pin(wiki, view.release_id, env)
    assert snapshot(raw) == state["originals"]
    return {"identity_verified": True, "default_verified": True, "fixed_reader_verified": True,
            "raw_preserved": True, "republished_plan_verified": True}


def verify_queued_retry(root, wiki, plan, visible, env):
    draft_dir = Path(plan["directory"])
    if draft_dir.exists():
        draft_dir.rename(root / f"original-draft-{plan['slug']}")
    assert not draft_dir.exists()
    assert not (visible.root / plan["page"]).exists()
    entries = cli("wiki_apply.py", "pending", "--wiki", wiki, env=env)["pending"]
    assert [(row["plan_id"], row["plan_sha256"]) for row in entries] == [(plan["id"], plan["sha"])]
    first = replay(wiki, plan, env)
    again = replay(wiki, plan, env)
    assert (first["state"], again["state"]) == ("applied", "already_applied")
    active = publish.resolve_publication(wiki)
    assert active.release_id == first["release_id"] == again["release_id"]
    verify_once(active.root, plan)
    assert (f"{plan['slug']} の記録。" in (active.root / plan["page"]).read_text(encoding="utf-8"))
    guard = WriteGuard(wiki)
    area = wiki / publish.AREA
    chain = publish.history(guard, area, publish.read_active(guard, area))
    assert [release for release, entry in chain if entry["plan_id"] == plan["id"]] == [active.release_id]
    database = active.root / "ontology/ossie/wiki-data.sqlite"
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as connection:
        assert connection.execute("SELECT count(*) FROM sem_articles WHERE page = ?", (plan["page"],)).fetchone() == (1,)
    assert cli("wiki_apply.py", "pending", "--wiki", wiki, env=env)["pending"] == []
    return {"approved_replayed": True, "plan_id": plan["id"], "release_id": active.release_id,
            "first_retry": first["state"], "second_retry": again["state"], "operation": plan["operation"]}


def exercise():
    signal("START", {"os": os.environ.get("OS"), "drive": os.environ.get("SystemDrive")})
    root = data_volume()
    root.mkdir(exist_ok=True)
    temporary = root / "temp"
    temporary.mkdir(exist_ok=True)
    env = trial.env_for(root)
    env.update(TEMP=str(temporary), TMP=str(temporary))
    os.environ.update({k: env[k] for k in ("TEMP", "TMP", "INFO_HIVE_DATA_DIR", "PYTHONUTF8")})
    queued_only = os.environ.get("IH_POWER_QUEUED_TRIAL") == "1"
    points = ("save_queued",) * len(QUEUED_OPERATIONS) if queued_only else POINTS
    state_file = root / "state.json"
    if state_file.exists():
        state = json.loads(state_file.read_bytes())
    else:
        candidate = root / "candidate"
        trial.create_public_candidate(candidate, 96)
        with (candidate / "index.md").open("a", encoding="utf-8") as stream:
            stream.write("\n## シンセシス\n")
        wiki, raw, pinned, originals = seed(root / "work", candidate)
        state = {"wiki": str(wiki), "raw": str(raw), "pinned": pinned,
                 "originals": originals, "runs": [], "planned": None}
        write_state(root, state)
        # 試験用原本はアプリの取り込みを経ていない。初回だけ正常終了し、安定した基準から停止試験を始める。
        signal("BASE", {"raw_files": len(originals)})
        sleep(5)
        subprocess.run(["wpeutil", "shutdown"], check=True, capture_output=True, timeout=30)
        return
    wiki, raw = Path(state["wiki"]), Path(state["raw"])
    if state["planned"]:
        point, plan = state["planned"]
        now = perf_counter()
        restored = publish.recover(wiki)
        visible = publish.resolve_publication(wiki)
        verify_pin(wiki, state["pinned"], env)
        observed_hashes = snapshot(raw)
        assert observed_hashes == state["originals"], {"expected": len(state["originals"]),
            "observed": len(observed_hashes), "changed": sum(observed_hashes.get(name) != digest
                                                             for name, digest in state["originals"].items())}
        if queued_only:
            result = verify_queued_retry(root, wiki, plan, visible, env)
        else:
            ack = replay(wiki, plan, env)
            assert replay(wiki, plan, env)["release_id"] == ack["release_id"]
            visible = publish.resolve_publication(wiki)
            assert visible.release_id == ack["release_id"]
            verify_once(visible.root, plan)
            result = {"approved_replayed": True}
        observed = {"point": point, "journal_recovered": restored is not None,
                    "guest_recovery_and_verification_s": round(perf_counter()-now, 4),
                    "fixed_reader_verified": True, **result}
        state["runs"].append(observed)
        state["planned"] = None
        write_state(root, state)
        signal("VERIFIED", observed)
        sleep(3)
    index = len(state["runs"])
    if index == len(points):
        if queued_only:
            signal("DONE", {"verified": index})
        else:
            signal("IMAGE", verify_image(root, wiki, raw, state, env))
        sleep(5)
        subprocess.run(["wpeutil", "shutdown"], check=True, capture_output=True, timeout=30)
        return
    point = points[index]
    operation = QUEUED_OPERATIONS[index] if queued_only else "query"
    plan = draft(wiki, raw, "vm-" + operation + "-" + point.replace("_", "-"), operation)
    state["planned"] = (point, plan)
    write_state(root, state)
    signal("ARMED", {"point": point})

    def checkpoint(current):
        if point == current:
            signal("CUT", {"point": point})
            while True:
                sleep(1)

    save.queue_save(plan["directory"], plan["sha"], checkpoint=checkpoint)
    raise AssertionError("停止位置を通らずに処理が終わりました")


if __name__ == "__main__":
    try:
        exercise()
    except BaseException as error:
        frame = traceback.extract_tb(error.__traceback__)[-1]
        signal("ERROR", {"error": f"{type(error).__name__}: {error}", "where": f"{Path(frame.filename).name}:{frame.lineno}"})
        sleep(60)
        raise
