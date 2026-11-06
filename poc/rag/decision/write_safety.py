"""E5: usearch と Tantivy の書き込みを、Windows で安全に行えるかを測る。

統一の測定（wiki-scale.json）では、2 プロセスが同じ usearch のファイルに追記すると Permission denied で失敗した。
対策として「書き手を 1 つにし、一時ファイルに保存してから置き換える」を挙げたが、実測していなかった。

(a) 別プロセスの読み手が view（メモリ写像）で開いている間に、書き手が一時ファイルに保存して os.replace で置き換える。
    Windows では写像中のファイルを置き換えられないと見込む（記録のため。失敗しても推奨は変わらない）。
(b) 1 プロセスがメモリに読み込み（view にしない）、書き込みのスレッドが追記して一時ファイルに保存し os.replace する間、
    4 つのスレッドが検索を続ける。wiki 規模で 200 回、全量で 5 回。追記と検索は読み書きロックで分ける。
(c) 版ごとのファイルと manifest.json の付け替え。外の読み手（2 プロセス）は manifest を見て新しい版を開き直し、
    書き手は古い版を消す（写像中なら後で再試行）。保存中に書き手を強制終了する試験を 20 回行い、
    manifest が常に開けるファイルを指しているかを確かめる。
(d) Tantivy: 書き手が commit を繰り返す間、別プロセスの読み手が reload と検索を続ける。
"""
from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import numpy as np

from decision_common import DWORK, load, save, write_json
from common import WORK, limit_threads
from full_common import USEARCH_KEPT

HERE = Path(__file__).resolve().parent
ROOT_W = DWORK / "write-safety"
NATURAL_VECTORS = WORK / "vectors/natural/R-130.npy"


def new_index(vectors, start=0):
    from usearch.index import Index
    index = Index(ndim=vectors.shape[1], metric="cos", dtype="f16", connectivity=16, expansion_add=128)
    index.add(np.arange(start, start + len(vectors), dtype=np.uint64), vectors, threads=4)
    return index


class RWLock:
    """読み手は並べ、書き手は 1 つだけにする簡単な読み書きロック。

    書き手が待っている間は新しい読み手を入れない（書き手を優先する）。
    読み手を優先すると、検索が途切れずに続くときに書き手がいつまでもロックを取れない。
    """

    def __init__(self):
        self._cond = threading.Condition()
        self._readers = 0
        self._writing = False
        self._writers_waiting = 0

    def shared(self):
        lock = self

        class _Shared:
            def __enter__(self):
                with lock._cond:
                    while lock._writing or lock._writers_waiting:
                        lock._cond.wait()
                    lock._readers += 1

            def __exit__(self, *_):
                with lock._cond:
                    lock._readers -= 1
                    lock._cond.notify_all()
        return _Shared()

    def exclusive(self):
        lock = self

        class _Exclusive:
            def __enter__(self):
                with lock._cond:
                    lock._writers_waiting += 1
                    try:
                        while lock._writing or lock._readers:
                            lock._cond.wait()
                    finally:
                        lock._writers_waiting -= 1
                    lock._writing = True

            def __exit__(self, *_):
                with lock._cond:
                    lock._writing = False
                    lock._cond.notify_all()
        return _Exclusive()


# ---- 子プロセス ----

def reader_view(path, seconds, out):
    """(a) の読み手: view で開いたまま検索を続ける。"""
    from usearch.index import Index
    index = Index.restore(path, view=True)
    query = np.random.default_rng(0).standard_normal(index.ndim).astype(np.float32)
    ends, count, errors = time.time() + seconds, 0, 0
    while time.time() < ends:
        try:
            index.search(query, 10)
            count += 1
        except Exception:
            errors += 1
    Path(out).write_text(json.dumps({"searches": count, "errors": errors}), encoding="utf-8")


def reader_manifest(folder, seconds, out):
    """(c) の読み手: manifest が変わったら新しい版を view で開き直す。古い版の写像は少し持ってから手放す。"""
    from usearch.index import Index
    folder = Path(folder)
    query = np.random.default_rng(1).standard_normal(512).astype(np.float32)
    current, index, held = None, None, []
    stats = {"reopens": 0, "searches": 0, "errors": [], "manifest_read_errors": 0}
    ends = time.time() + seconds
    while time.time() < ends:
        try:
            manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        except Exception:
            stats["manifest_read_errors"] += 1
            continue
        if manifest["file"] != current:
            try:
                fresh = Index.restore(str(folder / manifest["file"]), view=True)
            except Exception as error:
                stats["errors"].append(f"open {manifest['file']}: {type(error).__name__}: {error}"[:200])
                continue
            if index is not None:
                held.append(index)
                held = held[-1:]  # 1 つ前の版を少しだけ持ち続け、削除と重なるようにする
            index, current = fresh, manifest["file"]
            stats["reopens"] += 1
        try:
            index.search(query, 10)
            stats["searches"] += 1
        except Exception as error:
            stats["errors"].append(f"search: {type(error).__name__}: {error}"[:200])
    Path(out).write_text(json.dumps(stats), encoding="utf-8")


def writer_versions(folder, rounds, rows_per_round, crash_after_bytes=0):
    """(c) の書き手: 追記して新しい版のファイルに保存し、manifest を付け替え、古い版を消す。"""
    from usearch.index import Index
    folder = Path(folder)
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    index = Index.restore(str(folder / manifest["file"]), view=False)
    rng = np.random.default_rng(int(time.time()))
    pending_delete, deferred = [], 0
    version = manifest["version"]
    for _ in range(rounds):
        start = int(index.size) + 10_000_000 + version * rows_per_round
        index.add(np.arange(start, start + rows_per_round, dtype=np.uint64),
                  rng.standard_normal((rows_per_round, index.ndim)).astype(np.float32), threads=1)
        version += 1
        name = f"vectors-{version:06d}.usearch"
        index.save(str(folder / (name + ".tmp")))
        os.replace(folder / (name + ".tmp"), folder / name)
        tmp = folder / "manifest.json.tmp"
        tmp.write_text(json.dumps({"version": version, "file": name}), encoding="utf-8")
        os.replace(tmp, folder / "manifest.json")
        pending_delete.append(manifest["file"])
        manifest = {"version": version, "file": name}
        still = []
        for old in pending_delete:
            try:
                (folder / old).unlink(missing_ok=True)
            except PermissionError:
                deferred += 1
                still.append(old)
        pending_delete = still
    print(json.dumps({"rounds": rounds, "deferred_deletes": deferred, "left": pending_delete}), flush=True)


def tantivy_reader(folder, seconds, out):
    import tantivy
    sys.path.insert(0, str(HERE.parent / "unification"))
    stats = {"reloads": 0, "searches": 0, "errors": []}
    builder = tantivy.SchemaBuilder()
    builder.add_integer_field("id", stored=True, fast=True)
    builder.add_text_field("terms", stored=False, tokenizer_name="ws", index_option="freq")
    schema = builder.build()
    index = tantivy.Index(schema, path=str(folder))
    index.register_tokenizer("ws", tantivy.TextAnalyzerBuilder(tantivy.Tokenizer.whitespace()).build())
    ends = time.time() + seconds
    while time.time() < ends:
        try:
            index.reload()
            searcher = index.searcher()
            stats["reloads"] += 1
            searcher.search(index.parse_query("税", ["terms"]), 10)
            stats["searches"] += 1
        except Exception as error:
            stats["errors"].append(f"{type(error).__name__}: {error}"[:200])
    Path(out).write_text(json.dumps(stats), encoding="utf-8")


def child(args):
    return subprocess.Popen([sys.executable, "-X", "utf8", __file__, *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, encoding="utf-8")


# ---- 本体 ----

def test_a(vectors):
    folder = ROOT_W / "a"
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True)
    path = folder / "vectors.usearch"
    index = new_index(vectors)
    index.save(str(path))
    out = folder / "reader.json"
    reader = child(["--reader-view", str(path), "20", str(out)])
    time.sleep(5)
    results = []
    for attempt in range(20):
        index.add(np.array([10_000_000 + attempt], dtype=np.uint64), vectors[:1])
        tmp = folder / "vectors.usearch.tmp"
        index.save(str(tmp))
        try:
            os.replace(tmp, path)
            results.append("ok")
        except OSError as error:
            results.append(f"{type(error).__name__}: {error.winerror if hasattr(error, 'winerror') else ''}")
            tmp.unlink(missing_ok=True)
    reader.wait()
    return {"attempts": len(results), "succeeded": results.count("ok"), "errors": sorted(set(r for r in results if r != "ok")),
            "reader": json.loads(out.read_text(encoding="utf-8"))}


def test_b(vectors, path_label, rounds, rows_per_round, base_path=None):
    """1 プロセスで読み込み、追記・保存・置き換えと検索を並べる。"""
    from usearch.index import Index
    folder = ROOT_W / f"b-{path_label}"
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True)
    path = folder / "vectors.usearch"
    if base_path:
        shutil.copyfile(base_path, path)
        index = Index.restore(str(path), view=False)
    else:
        index = new_index(vectors)
        index.save(str(path))
    lock = RWLock()  # 検索は共有、追記は排他。保存（save）は読み取りなので共有で行う
    stop = threading.Event()
    stats = {"searches": 0, "search_errors": [], "saves": 0, "save_errors": [], "replace_errors": [], "save_seconds": []}
    query = np.random.default_rng(2).standard_normal(index.ndim).astype(np.float32)

    def searcher():
        while not stop.is_set():
            try:
                with lock.shared():
                    index.search(query, 10, threads=1)
                stats["searches"] += 1
            except Exception as error:
                stats["search_errors"].append(f"{type(error).__name__}: {error}"[:200])

    threads = [threading.Thread(target=searcher) for _ in range(4)]
    for t in threads:
        t.start()
    rng = np.random.default_rng(3)
    for r in range(rounds):
        start = 50_000_000 + r * rows_per_round
        batch = rng.standard_normal((rows_per_round, index.ndim)).astype(np.float32)
        with lock.exclusive():
            index.add(np.arange(start, start + rows_per_round, dtype=np.uint64), batch, threads=1)
        started = time.perf_counter()
        tmp = folder / "vectors.usearch.tmp"
        try:
            with lock.shared():
                index.save(str(tmp))
            stats["saves"] += 1
        except Exception as error:
            stats["save_errors"].append(f"{type(error).__name__}: {error}"[:200])
            continue
        try:
            os.replace(tmp, path)
        except OSError as error:
            stats["replace_errors"].append(f"{type(error).__name__}: {error}"[:200])
        stats["save_seconds"].append(time.perf_counter() - started)
    stop.set()
    for t in threads:
        t.join()
    restored = Index.restore(str(path), view=True)
    stats.update(rounds=rounds, rows_per_round=rows_per_round, final_size=int(restored.size), expected_size=int(index.size),
                 save_seconds_max=max(stats["save_seconds"]) if stats["save_seconds"] else None)
    del stats["save_seconds"]
    return stats


def test_c(vectors):
    from usearch.index import Index
    folder = ROOT_W / "c"
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True)
    index = new_index(vectors)
    index.save(str(folder / "vectors-000000.usearch"))
    (folder / "manifest.json").write_text(json.dumps({"version": 0, "file": "vectors-000000.usearch"}), encoding="utf-8")
    outs = [folder / f"reader-{i}.json" for i in range(2)]
    readers = [child(["--reader-manifest", str(folder), "90", str(o)]) for o in outs]
    time.sleep(5)
    writer = subprocess.run([sys.executable, "-X", "utf8", __file__, "--writer-versions", str(folder), "60", "50"],
                            capture_output=True, text=True, encoding="utf-8")
    normal = json.loads(writer.stdout.strip().splitlines()[-1]) if writer.returncode == 0 else {"error": writer.stderr[-1000:]}
    # 強制終了の試験: 書き手を起動し、乱数の時間で kill する。毎回 manifest の指すファイルが開けるかを確かめる。
    kills, broken = 0, []
    rng = random.Random(20261106)
    for attempt in range(20):
        proc = subprocess.Popen([sys.executable, "-X", "utf8", __file__, "--writer-versions", str(folder), "1000", "50"],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(rng.uniform(1.0, 4.0))
        proc.kill()
        proc.wait()
        kills += 1
        manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        try:
            Index.restore(str(folder / manifest["file"]), view=True)
        except Exception as error:
            broken.append({"attempt": attempt, "file": manifest["file"], "error": f"{type(error).__name__}: {error}"[:200]})
    for r in readers:
        r.wait()
    leftovers = sorted(p.name for p in folder.glob("*.tmp"))
    versions = sorted(p.name for p in folder.glob("vectors-*.usearch"))
    return {"writer": normal, "kills": kills, "broken_after_kill": broken, "tmp_left_after_kills": len(leftovers),
            "version_files_left": len(versions), "readers": [json.loads(o.read_text(encoding="utf-8")) for o in outs]}


def test_d():
    import tantivy
    folder = ROOT_W / "tantivy"
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True)
    builder = tantivy.SchemaBuilder()
    builder.add_integer_field("id", stored=True, fast=True)
    builder.add_text_field("terms", stored=False, tokenizer_name="ws", index_option="freq")
    schema = builder.build()
    index = tantivy.Index(schema, path=str(folder))
    index.register_tokenizer("ws", tantivy.TextAnalyzerBuilder(tantivy.Tokenizer.whitespace()).build())
    writer = index.writer(heap_size=100_000_000, num_threads=1)
    for i in range(1000):
        writer.add_document(tantivy.Document(id=i, terms="税 消費 軽減"))
    writer.commit()
    out = folder.parent / "tantivy-reader.json"
    reader = child(["--tantivy-reader", str(folder), "40", str(out)])
    time.sleep(3)
    commits, errors = 0, []
    ends = time.time() + 30
    n = 1000
    while time.time() < ends:
        try:
            for _ in range(50):
                writer.add_document(tantivy.Document(id=n, terms="税 所得 控除"))
                n += 1
            writer.commit()
            commits += 1
        except Exception as error:
            errors.append(f"{type(error).__name__}: {error}"[:200])
    writer.wait_merging_threads()
    reader.wait()
    return {"commits": commits, "writer_errors": errors, "reader": json.loads(out.read_text(encoding="utf-8"))}


def test_d_same_process():
    """(d2) 案 B の形: 書き手と読み手が同じプロセス（サーバー）にいる。読み手はスレッドで reload と検索を続ける。"""
    import tantivy
    folder = ROOT_W / "tantivy-same"
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True)
    builder = tantivy.SchemaBuilder()
    builder.add_integer_field("id", stored=True, fast=True)
    builder.add_text_field("terms", stored=False, tokenizer_name="ws", index_option="freq")
    schema = builder.build()
    index = tantivy.Index(schema, path=str(folder))
    index.register_tokenizer("ws", tantivy.TextAnalyzerBuilder(tantivy.Tokenizer.whitespace()).build())
    writer = index.writer(heap_size=100_000_000, num_threads=1)
    for i in range(1000):
        writer.add_document(tantivy.Document(id=i, terms="税 消費 軽減"))
    writer.commit()
    stop = threading.Event()
    reader = {"reloads": 0, "searches": 0, "errors": []}

    def read_loop():
        query = index.parse_query("税", ["terms"])
        while not stop.is_set():
            try:
                index.reload()
                index.searcher().search(query, 10)
                reader["reloads"] += 1
                reader["searches"] += 1
            except Exception as error:
                reader["errors"].append(f"{type(error).__name__}: {error}"[:200])

    thread = threading.Thread(target=read_loop)
    thread.start()
    commits, errors, n = 0, [], 1000
    ends = time.time() + 30
    while time.time() < ends:
        try:
            for _ in range(50):
                writer.add_document(tantivy.Document(id=n, terms="税 所得 控除"))
                n += 1
            writer.commit()
            commits += 1
        except Exception as error:
            errors.append(f"{type(error).__name__}: {error}"[:200])
    writer.wait_merging_threads()
    stop.set()
    thread.join()
    index.reload()
    return {"commits": commits, "writer_errors": errors, "reader": reader,
            "num_docs_after": index.searcher().num_docs, "expected_docs": n}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--add-d2", action="store_true", help="保存済みの write-safety.json に (d2) だけを足す")
    parser.add_argument("--reader-view", nargs=3)
    parser.add_argument("--reader-manifest", nargs=3)
    parser.add_argument("--writer-versions", nargs=2)
    parser.add_argument("--tantivy-reader", nargs=3)
    args, rest = parser.parse_known_args()
    if args.reader_view:
        return reader_view(args.reader_view[0], float(args.reader_view[1]), args.reader_view[2])
    if args.reader_manifest:
        return reader_manifest(*args.reader_manifest[:1], float(args.reader_manifest[1]), args.reader_manifest[2])
    if args.writer_versions:
        return writer_versions(args.writer_versions[0], int(args.writer_versions[1]), int(rest[0]) if rest else 50)
    if args.tantivy_reader:
        return tantivy_reader(args.tantivy_reader[0], float(args.tantivy_reader[1]), args.tantivy_reader[2])
    limit_threads()
    if args.add_d2:
        report = load("write-safety.json")
        report.pop("env", None)
        report["d2_tantivy_same_process"] = test_d_same_process()
        d2 = report["d2_tantivy_same_process"]
        print("d2", {k: (len(v) if isinstance(v, list) else v) for k, v in d2.items()}, flush=True)
        report["d2_passed"] = not d2["writer_errors"] and not d2["reader"]["errors"] and d2["num_docs_after"] == d2["expected_docs"]
        report["note_d"] = ("(d) は読み手が別のプロセスで、Windows では meta.json の置き換えが拒まれる。"
                            "案 B は索引をサーバーのプロセスだけが開くので、判定には (d2) を使う")
        save("write-safety.json", report)
        return
    vectors = np.load(NATURAL_VECTORS).astype(np.float32)
    report = {"wiki_rows": len(vectors)}
    report["a_replace_while_mapped"] = test_a(vectors)
    print("a", report["a_replace_while_mapped"], flush=True)
    report["b_single_writer_wiki"] = test_b(vectors, "wiki", 200, 50)
    print("b wiki", {k: v for k, v in report["b_single_writer_wiki"].items() if not isinstance(v, list)}, flush=True)
    report["b_single_writer_full"] = test_b(vectors, "full", 5, 500, base_path=USEARCH_KEPT)
    print("b full", {k: v for k, v in report["b_single_writer_full"].items() if not isinstance(v, list)}, flush=True)
    report["c_versioned_manifest"] = test_c(vectors)
    print("c", {k: v for k, v in report["c_versioned_manifest"].items() if k != "readers"}, flush=True)
    report["d_tantivy"] = test_d()
    print("d", report["d_tantivy"], flush=True)
    b_ok = all(not report[k]["search_errors"] and not report[k]["save_errors"] and not report[k]["replace_errors"]
               and report[k]["final_size"] == report[k]["expected_size"] for k in ("b_single_writer_wiki", "b_single_writer_full"))
    c = report["c_versioned_manifest"]
    c_ok = not c["broken_after_kill"] and all(not r["errors"] for r in c["readers"]) and "error" not in c["writer"]
    save("write-safety.json", {"purpose": "Windows での usearch と Tantivy の書き込みの安全性", **report,
                               "b_passed": b_ok, "c_passed": c_ok, "passed": b_ok or c_ok,
                               "criterion": "(b) か (c) のどちらかで、失敗 0 回、検索のエラー 0 回、manifest が常に開けるファイルを指す"})


if __name__ == "__main__":
    main()
