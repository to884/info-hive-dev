"""索引の別プロセス更新と再起動を、実際のエンジンで確認する。"""
import contextlib
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from datetime import timedelta
from pathlib import Path

import lancedb
import pyarrow as pa
import yaml
from qdrant_client import QdrantClient, models as qm

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "poc"))
from poc_data import POC_DATA  # noqa: E402
WORK = (Path(os.environ["LOCALAPPDATA"]) / "info-hive/rag-poc/2026-11-04").resolve()
FOLDER = POC_DATA /  f"contracts-{time.time_ns()}"
FOLDER.mkdir(parents=True)
results = []


def check(name, success, **details):
    results.append({"name": name, "passed": bool(success), **details})
    print(json.dumps(results[-1]), flush=True)


db = lancedb.connect(str(FOLDER / "lance"), read_consistency_interval=timedelta(0))
schema = pa.schema([("id", pa.int64()), ("terms", pa.string()), ("vector", pa.list_(pa.float32(), 4))])
table = db.create_table("chunks", data=pa.Table.from_pylist([{"id": 1, "terms": "original", "vector": [1., 0., 0., 0.]}], schema=schema))
table.create_fts_index("terms", base_tokenizer="whitespace", stem=False, remove_stop_words=False)
reader = db.open_table("chunks")
code = "import lancedb,sys; t=lancedb.connect(sys.argv[1]).open_table('chunks'); t.add([{'id':2,'terms':'tsuika','vector':[0.,1.,0.,0.]}])"
started = time.perf_counter()
subprocess.run([sys.executable, "-c", code, str(FOLDER / "lance")], check=True)
dense = reader.search([0., 1., 0., 0.]).limit(1).to_list()
lexical = reader.search("tsuika", query_type="fts", fts_columns="terms").limit(10).to_list()
check("lancedb_cross_process_append_dense", dense[0]["id"] == 2, writer_and_query_seconds=time.perf_counter() - started)
check("lancedb_cross_process_append_fts_before_optimize", any(row["id"] == 2 for row in lexical))
started = time.perf_counter()
table.optimize()
check("lancedb_optimize_preserves_new_rows", reader.count_rows() == 2, seconds=time.perf_counter() - started)
table.merge_insert("id").when_matched_update_all().when_not_matched_insert_all().execute([{"id": 2, "terms": "updated", "vector": [0., 1., 0., 0.]}])
check("lancedb_idempotent_merge", table.count_rows() == 2)


@contextlib.contextmanager
def server():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    config = {"storage": {"storage_path": str(FOLDER / "qstorage")}, "service": {"host": "127.0.0.1", "http_port": port, "grpc_port": None}, "telemetry_disabled": True}
    config_path = FOLDER / "qdrant.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    with (FOLDER / "qdrant.log").open("a", encoding="utf-8") as log:
        proc = subprocess.Popen([str(WORK / "qdrant-bin/qdrant.exe"), "--config-path", str(config_path)], cwd=FOLDER,
                                stdout=log, stderr=log, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        url = f"http://127.0.0.1:{port}"
        try:
            for _ in range(100):
                try:
                    with urllib.request.urlopen(url + "/readyz", timeout=.2):
                        break
                except Exception:
                    time.sleep(.1)
            else:
                raise TimeoutError("Qdrant の起動待ち")
            with contextlib.closing(QdrantClient(url=url)) as client:
                yield client
        finally:
            proc.terminate()
            proc.wait(timeout=10)


with server() as client:
    client.create_collection("test", vectors_config=qm.VectorParams(size=4, distance=qm.Distance.COSINE))
    client.upsert("test", [qm.PointStruct(id=1, vector=[1., 0., 0., 0.])], wait=True)
    client.upsert("test", [qm.PointStruct(id=1, vector=[0., 1., 0., 0.])], wait=True)
    check("qdrant_idempotent_upsert", client.count("test", exact=True).count == 1)
with server() as client:
    items = client.query_points("test", query=[0., 1., 0., 0.], limit=1).points
    check("qdrant_reopen_preserves_data", items[0].id == 1)
(ROOT / "docs/research/rag-poc-2026-11-04/backend-contracts.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
