"""OCR 後の新規入力を GPU で埋め込み、追記ファイルを台帳より先に確定する。"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time

from common import MODEL, OUT, POC_DATA, REVISION, WORK, digest, initialize, phase_lock, write_json


def main():
    initialize()
    while not (WORK / 'prepared.sqlite').is_file():
        time.sleep(2)
    db = sqlite3.connect(WORK / 'prepared.sqlite', timeout=120)
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA cache_size=-131072')
    db.execute('CREATE TABLE IF NOT EXISTS new_vectors(input_hash TEXT PRIMARY KEY,position INTEGER UNIQUE NOT NULL)')
    db.commit()
    import numpy as np
    import torch
    from sentence_transformers import SentenceTransformer

    if not torch.cuda.is_available():
        raise RuntimeError('検証用の GPU 埋め込みを利用できません。')
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.cuda.set_per_process_memory_fraction(0.7)
    model = SentenceTransformer(MODEL, revision=REVISION, device='cuda',
                                cache_folder=str(POC_DATA / 'model-cache'),
                                model_kwargs={'attn_implementation': 'sdpa'})
    model.max_seq_length = min(int(model[0].auto_model.config.max_position_embeddings), 8192)
    position = db.execute('SELECT COUNT(*) FROM new_vectors').fetchone()[0]
    maximum = db.execute('SELECT COALESCE(MAX(position),-1) FROM new_vectors').fetchone()[0]
    if maximum + 1 != position:
        raise RuntimeError('新規ベクトルの台帳に欠番があります。')
    path = WORK / 'new-vectors.f32'
    if not path.exists():
        path.touch()
    if path.stat().st_size < position * 2048:
        raise RuntimeError('ベクトルファイルが確定済みの台帳より短くなっています。')
    started = time.perf_counter()
    encoded = 0
    maximum_tokens = 0
    try:
        with path.open('r+b') as stream:
            # 強制終了前に追記したが台帳に確定していない末尾だけを回収する。
            stream.truncate(position * 2048)
            stream.seek(0, 2)
            while True:
                with db:
                    db.execute("""UPDATE chunks SET vector_source='new',position=(
                        SELECT position FROM new_vectors n WHERE n.input_hash=chunks.input_hash)
                        WHERE vector_source IS NULL AND input_hash IN (SELECT input_hash FROM new_vectors)""")
                rows = db.execute('''SELECT input_hash,MIN(embedding_text) FROM chunks
                    WHERE vector_source IS NULL GROUP BY input_hash ORDER BY input_hash LIMIT 128''').fetchall()
                if not rows:
                    if (WORK / 'prepared-complete.json').exists():
                        break
                    time.sleep(5)
                    continue
                for key, text in rows:
                    if hashlib.sha256(text.encode('utf-8')).hexdigest() != key:
                        raise RuntimeError('埋め込み入力のハッシュが一致しません。')
                inputs = ['検索文書: ' + text for _, text in rows]
                lengths = [len(ids) for ids in model.tokenizer(inputs, truncation=False, padding=False)['input_ids']]
                longest = max(lengths)
                maximum_tokens = max(maximum_tokens, longest)
                if longest > model.max_seq_length:
                    raise RuntimeError(f'モデル上限を超える入力です。{longest} トークン。本文の切り詰めは行っていません。')
                batch = max(1, min(32, (32 * 1536**2) // longest**2))
                try:
                    vectors = model.encode(inputs, batch_size=batch, normalize_embeddings=True,
                                           show_progress_bar=False, convert_to_numpy=True).astype(np.float32)
                except torch.cuda.OutOfMemoryError:
                    torch.cuda.empty_cache()
                    vectors = model.encode(inputs, batch_size=1, normalize_embeddings=True,
                                           show_progress_bar=False, convert_to_numpy=True).astype(np.float32)
                if vectors.shape != (len(rows), 512) or not np.isfinite(vectors).all():
                    raise RuntimeError('新規ベクトルの形または数値が不正です。')
                stream.write(vectors.tobytes())
                stream.flush()
                os.fsync(stream.fileno())
                with db:
                    db.executemany('INSERT INTO new_vectors VALUES (?,?)',
                                   [(key, position + i) for i, (key, _) in enumerate(rows)])
                    db.executemany("UPDATE chunks SET vector_source='new',position=? WHERE input_hash=? AND vector_source IS NULL",
                                   [(position + i, key) for i, (key, _) in enumerate(rows)])
                position += len(rows)
                encoded += len(rows)
                progress = {'stored_new_unique_vectors': position, 'new_this_run': encoded,
                            'max_input_tokens_this_run': maximum_tokens, 'seconds_this_run': time.perf_counter() - started,
                            'gpu_peak_allocated_bytes': torch.cuda.max_memory_allocated()}
                write_json(WORK / 'embedding-progress.json', progress)
                if encoded % 2048 == 0:
                    print(json.dumps(progress), flush=True)
        count, missing = db.execute('SELECT COUNT(*),SUM(vector_source IS NULL) FROM chunks').fetchone()
        prepared = json.loads((WORK / 'prepared-complete.json').read_text(encoding='utf-8'))
        if count != prepared['chunks'] or missing:
            raise RuntimeError('全量の埋め込みが揃っていません。')
        result = {'status': 'completed', 'chunks': count, 'new_unique_vectors': position,
                  'new_this_run': encoded, 'new_vector_sha256': digest(path), 'model': MODEL,
                  'revision': REVISION, 'dimension': 512, 'document_device': 'cuda',
                  'max_input_tokens_this_run': maximum_tokens, 'seconds_this_run': time.perf_counter() - started,
                  'gpu_peak_allocated_bytes': torch.cuda.max_memory_allocated()}
        write_json(WORK / 'embedding-complete.json', result)
        write_json(OUT / 'embedding-complete.json', result)
        print(json.dumps(result), flush=True)
    finally:
        db.close()


if __name__ == '__main__':
    with phase_lock('embed'):
        main()
