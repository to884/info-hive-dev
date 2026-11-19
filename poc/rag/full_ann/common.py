"""全量 OCR 後の検証で共用する配置と、入力の固定。"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "poc"))
from poc_data import POC_DATA

sys.path.insert(0, str(ROOT / "info-hive-rag/scripts"))
from rag_config import Config, write_json
from filelock import FileLock

BASE = POC_DATA / "full-20261104"
OCR = POC_DATA / "full-ocr-v050-20261109"
WORK = Path(os.environ.get("RAG_FULL_ANN_WORK", str(POC_DATA / "full-ann-20261119"))).resolve()
OUT = ROOT / "docs/research/rag-full-ann-2026-11-19"
MODEL = "cl-nagoya/ruri-v3-130m"
REVISION = "e3114c6ee10dbab8b4b235fbc6dcf9dd4d5ac1a6"
REQUIRED_CHECKS = {
    'bulk_input_has_no_indexes',
    'ann_creation_interrupt_parent_death_stops_workers', 'ann_creation_interrupt_job_paused',
    'ann_creation_interrupt_stop_boundary_verified', 'initial_pdf_not_published_during_ann_creation',
    'ann_creation_has_saved_embedding_checkpoint', 'ann_creation_resumes_same_job',
    'initial_extracted_pages_reused', 'full_ann_created_after_reconnect', 'ann_creation_keeps_saved_rows',
    'ann_creation_history_matches_stop', 'ann_creation_vectors_reused',
    'ann_update_interrupt_parent_death_stops_workers', 'ann_update_interrupt_job_paused',
    'ann_update_interrupt_stop_boundary_verified', 'appended_pdf_not_published_during_update',
    'ann_update_has_saved_embedding_checkpoint', 'ann_update_resumes_same_job',
    'appended_extracted_pages_reused', 'full_ann_updated_after_reconnect',
    'ann_update_history_matches_stop', 'ann_update_vectors_reused',
    'replacement_interrupt_after_publication', 'replacement_interrupt_parent_death_stops_workers',
    'replacement_resumes_same_job', 'replacement_updates_full_indexes',
    'replacement_vectors_reused', 'replacement_old_rows_hidden_before_cleanup',
    'replacement_no_inactive_generations',
    'replaced_generation_rows_removed', 'replacement_marks_dependent_page',
    'replacement_has_no_cleanup_error', 'replacement_search_excludes_old_generation',
    'retirement_queue_empty', 'before_unchanged_registration', 'after_unchanged_registration',
    'unchanged_registration_reuses_index', 'ocr_search_sources_verified',
    'stored_vectors_match_cpu_reference', 'ann_only_returns_known_vectors',
    'final_table_has_no_duplicate_chunk_ids', 'final_catalog_matches_table',
}


def validate_checks(checks):
    passed = {row['name'] for row in checks if row['passed']}
    missing = REQUIRED_CHECKS - passed
    failed = [row['name'] for row in checks if not row['passed']]
    if missing or failed:
        raise RuntimeError(f'必須の検査が揃っていません。missing={sorted(missing)}, failed={failed}')


def phase_lock(name: str):
    WORK.mkdir(parents=True, exist_ok=True)
    return FileLock(str(WORK / (name + '.lock')), timeout=0)


@contextmanager
def measure(name: str):
    import psutil
    process = psutil.Process()
    stopped = threading.Event()
    peak = [0]
    started = time.perf_counter()

    def sample():
        while not stopped.wait(0.1):
            total = 0
            for item in [process, *process.children(recursive=True)]:
                try:
                    total += item.memory_info().rss
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            peak[0] = max(peak[0], total)

    thread = threading.Thread(target=sample, daemon=True)
    thread.start()
    try:
        yield
    finally:
        stopped.set()
        thread.join(timeout=1)
        write_json(OUT / (name + '-resources.json'), {'seconds': time.perf_counter() - started,
                   'peak_sum_process_tree_rss_bytes': peak[0], 'sample_interval_ms': 100,
                   'rss_definition': 'この試験プロセスと子孫の RSS の和。共有ページを重複して数える。'})


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(8 * 1024 * 1024):
            value.update(block)
    return value.hexdigest()


def frozen_uri(path: Path) -> str:
    wal = path.with_name(path.name + '-wal')
    if wal.exists() and wal.stat().st_size:
        raise RuntimeError(f'固定入力の WAL が空ではありません。{path}')
    return path.resolve().as_uri() + '?mode=ro&immutable=1'


def readonly(path: Path, *, frozen=False):
    uri = frozen_uri(path) if frozen else path.resolve().as_uri() + '?mode=ro'
    connection = sqlite3.connect(uri, uri=True, timeout=60)
    connection.row_factory = sqlite3.Row
    return connection


def configuration() -> Config:
    return Config({"data_dir": str(WORK / "product-data"), "embedding_model": MODEL,
                   "embedding_revision": REVISION, "model_cache_dir": str(POC_DATA / "model-cache"),
                   "uv_cache_dir": str(WORK / "uv-cache"), "cpu_threads": 4, "batch_size": 32,
                   "ocr_mode": "auto", "ocr_dpi": 150, "index_cleanup_age_days": 3650,
                   "search_nprobes": 128, "search_refine_factor": 4, "reranker": "off"})


def initialize() -> dict:
    WORK.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    config = configuration()
    policy = {"model": MODEL, "revision": REVISION, "dimension": config.dimension,
              "fingerprint": config.fingerprint, "extraction_key": config.extraction_key,
              "ocr_policy_sha256": digest(OCR / "run-policy.json"),
              "ocr_ledger_sha256": digest(OCR / "ledger.sqlite"),
              "manifest_sha256": digest(BASE / "manifest.json"),
              "product_scripts": {p.name: digest(p) for p in sorted((ROOT / "info-hive-rag/scripts").glob("*.py"))}}
    path = WORK / "source-policy.json"
    if path.exists() and json.loads(path.read_text(encoding="utf-8")) != policy:
        raise RuntimeError("固定した入力または製品コードが変わっています。別の作業領域を使ってください。")
    write_json(path, policy)
    write_json(OUT / "source-policy.json", policy)
    write_json(WORK / "product-config.json", config.snapshot())
    return policy
