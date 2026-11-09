"""全量抽出と並行して文書を埋め込む。検索計測とは分け、GPU 利用を明記する。"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "poc"))
from poc_data import POC_DATA  # noqa: E402
sys.path.insert(0,str(ROOT/'info-hive-rag/scripts'))
from rag_config import write_json
WORK = POC_DATA / "full-20261104"
OUT = ROOT / "docs/research/rag-validation-remaining-2026-11-04"
MODEL = "cl-nagoya/ruri-v3-130m"
REVISION = "e3114c6ee10dbab8b4b235fbc6dcf9dd4d5ac1a6"
DIMENSION = 512


def save(path, value):
    write_json(path,value)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device",choices=["cpu","cuda"],default="cuda")
    parser.add_argument("--batch-size",type=int,default=8)
    args = parser.parse_args()
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    import numpy as np
    import torch
    from sentence_transformers import SentenceTransformer
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    if args.device == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA が利用できません。CPU への無言の切り替えは行いません。")
        torch.cuda.set_per_process_memory_fraction(.45)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
    folder = WORK / "embeddings-130m"
    folder.mkdir(parents=True,exist_ok=True)
    model = SentenceTransformer(MODEL,revision=REVISION,device=args.device,
        cache_folder=str(POC_DATA / "model-cache"),model_kwargs={"attn_implementation":"sdpa"})
    model.max_seq_length=min(int(model[0].auto_model.config.max_position_embeddings),8192)
    source = sqlite3.connect(WORK / "corpus.sqlite",timeout=30)
    ledger = sqlite3.connect(folder / "ledger.sqlite")
    ledger.execute("PRAGMA journal_mode=WAL")
    ledger.execute("CREATE TABLE IF NOT EXISTS vectors(id INTEGER PRIMARY KEY, position INTEGER UNIQUE, input_hash TEXT)")
    ledger.commit()
    position = ledger.execute("SELECT COUNT(*) FROM vectors").fetchone()[0]
    last_id = ledger.execute("SELECT COALESCE(MAX(id),-1) FROM vectors").fetchone()[0]
    source.execute('ATTACH DATABASE ? AS embeddings',(str(folder/'ledger.sqlite'),))
    for text,expected_hash in source.execute('SELECT c.embedding_text,e.input_hash FROM chunks c JOIN embeddings.vectors e ON e.id=c.id'):
        if hashlib.sha256(text.encode('utf-8')).hexdigest()!=expected_hash:
            raise RuntimeError('保存済みの埋め込み入力が変更されています。別の保存先で再構築してください。')
    vector_path = folder / "vectors.f32"
    vectors_file = vector_path.open("r+b" if vector_path.exists() else "w+b")
    if vectors_file.seek(0,2) < position * DIMENSION * 4:
        raise RuntimeError("ベクトルファイルが台帳より短く、再開できません。")
    vectors_file.truncate(position * DIMENSION * 4)
    vectors_file.seek(0,2)
    started, initial_position, last_report = time.perf_counter(), position, 0.0
    manifest = json.loads((WORK / "manifest.json").read_text(encoding="utf-8"))
    inventory=json.loads((OUT/'full-inventory.json').read_text(encoding='utf-8'))
    target_documents = sum(inventory['include_cloud'] or not row["cloud_only"] for row in manifest["files"])
    max_tokens = 0
    effective_batch_size=args.batch_size
    try:
        while True:
            rows = source.execute("SELECT id,embedding_text FROM chunks WHERE id>? ORDER BY id LIMIT 128",(last_id,)).fetchall()
            if not rows:
                completed = source.execute("SELECT COUNT(*) FROM documents WHERE status IN ('completed','failed')").fetchone()[0]
                if completed >= target_documents:
                    break
                time.sleep(2)
                continue
            texts = ["検索文書: " + row[1] for row in rows]
            lengths = [len(tokens) for tokens in model.tokenizer(texts,truncation=False,padding=False)["input_ids"]]
            max_tokens = max(max_tokens,max(lengths))
            if max(lengths) > model.max_seq_length:
                bad = [(rows[i][0],length) for i,length in enumerate(lengths) if length>model.max_seq_length]
                save(OUT / "long-inputs.json",{"chunks":bad,"limit":model.max_seq_length})
                raise RuntimeError("入力が上限を超えました。自動分割の見直しが必要です。")
            order = sorted(range(len(rows)),key=lambda i:lengths[i])
            effective_batch_size=min(args.batch_size,max(1,(32*1536**2)//max(lengths)**2))
            while True:
                try:
                    encoded = model.encode([texts[i] for i in order],normalize_embeddings=True,
                        batch_size=effective_batch_size,show_progress_bar=False,convert_to_numpy=True).astype(np.float32)
                    break
                except torch.cuda.OutOfMemoryError:
                    if args.device!='cuda' or effective_batch_size==1:
                        raise
                    effective_batch_size=max(1,effective_batch_size//2)
                    print(json.dumps({'phase':'reduce_batch_after_cuda_oom','batch_size':effective_batch_size}),flush=True)
                torch.cuda.empty_cache()
            restored = np.empty_like(encoded)
            restored[order] = encoded
            if restored.shape != (len(rows),DIMENSION) or not np.isfinite(restored).all():
                raise RuntimeError("埋め込みの形状または数値が不正です。")
            vectors_file.write(restored.tobytes())
            vectors_file.flush()
            os.fsync(vectors_file.fileno())
            ledger.executemany("INSERT INTO vectors VALUES (?,?,?)",[(row[0],position+i,hashlib.sha256(row[1].encode('utf-8')).hexdigest()) for i,row in enumerate(rows)])
            ledger.commit()
            position += len(rows)
            last_id = rows[-1][0]
            elapsed = time.perf_counter()-started
            if elapsed-last_report > 20:
                last_report = elapsed
                result = {"device":args.device,"model":MODEL,"revision":REVISION,"dimension":DIMENSION,
                    "batch_size":args.batch_size,
                    "effective_batch_size":effective_batch_size,"input_limit":model.max_seq_length,
                    "completed_vectors_including_retired_ids":position,"new_vectors_this_run":position-initial_position,
                    "seconds":elapsed,"vectors_per_second":(position-initial_position)/elapsed,"max_input_tokens":max_tokens,
                    "gpu_peak_allocated_bytes":torch.cuda.max_memory_allocated() if args.device=='cuda' else None,
                    "gpu_build_does_not_validate_cpu_build_time":args.device=='cuda'}
                save(OUT / "full-embedding-progress.json",result)
                print(json.dumps(result),flush=True)
    finally:
        vectors_file.close()
        source.close()
        ledger.close()
    failures=sqlite3.connect(WORK/'corpus.sqlite').execute("SELECT COUNT(*) FROM documents WHERE status='failed'").fetchone()[0]
    save(folder / "complete.json",{"status":"completed" if not failures else "partial","failed_documents":failures,"vectors_including_retired_ids":position,"model":MODEL,"revision":REVISION,
         "dimension":DIMENSION,"device":args.device,"input_limit":model.max_seq_length,"batch_size":args.batch_size,"effective_batch_size":effective_batch_size,"max_input_tokens_this_run":max_tokens,"seconds_this_run":time.perf_counter()-started})


if __name__ == "__main__":
    main()
