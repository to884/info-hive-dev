"""全量テーブルに実 MCP で PDF を取り込み、索引保守の途中で接続元を終了する。"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault('RAYON_NUM_THREADS', '4')
os.environ.setdefault('OMP_NUM_THREADS', '4')

from common import BASE, OCR, OUT, ROOT, WORK, configuration, initialize, measure, phase_lock, readonly, validate_checks, write_json

sys.path.insert(0, str(ROOT / 'tests/rag'))
from verify_pipeline import call, connect, wait_until
from verify_auto_indexes import fixture
from rag_index import Engine
from rag_indexes import statistics, version
from rag_jobs import Jobs


class Verification:
    def __init__(self):
        initialize()
        self.config = configuration()
        self.engine = Engine(self.config)
        self.wiki = WORK / 'wiki'
        self.folder = self.config.workspace(str(self.wiki))
        self.jobs = Jobs(self.config.data_dir)
        self.config_file = WORK / 'product-config.json'
        self.state_file = WORK / 'mcp-workflow.json'
        self.state = json.loads(self.state_file.read_text(encoding='utf-8')) if self.state_file.exists() else {}
        self.checks = self.state.setdefault('checks', [])
        self.base = json.loads((WORK / 'stage-complete.json').read_text(encoding='utf-8'))
        self.snapshots = self.state.setdefault('snapshots', [])

    def save(self):
        write_json(self.state_file, self.state)
        write_json(OUT / 'mcp-results.json', self.state)

    def record(self, name, passed, **detail):
        row = {'name': name, 'passed': bool(passed), **detail}
        self.checks.append(row)
        self.save()
        print(json.dumps(row, ensure_ascii=False), flush=True)
        if not passed:
            raise AssertionError(name)

    def table(self):
        return self.engine._table(self.folder)

    def resume_environment(self):
        return {'PYTHONPATH': str(ROOT / 'poc/rag/full_ann/fault_hook'),
                'RAG_ANN_TEST_SCRIPTS': str(ROOT / 'info-hive-rag/scripts'),
                'RAG_ANN_FORBID_DOCUMENT_EMBED': '1'}

    def vector_stamp(self, doc_id):
        import numpy as np
        rows = self.table().search().where(f"doc_id = '{doc_id}'").select(['chunk_id', 'vector']).limit(None).to_list()
        checksum = hashlib.sha256()
        for row in sorted(rows, key=lambda item: item['chunk_id']):
            checksum.update(row['chunk_id'].encode() + np.asarray(row['vector'], dtype=np.float32).tobytes())
        with self.engine._catalog(self.folder) as catalog:
            cursor = catalog.execute('SELECT completed FROM jobs WHERE generation=?', (self.config.generation(doc_id),)).fetchone()
        return {'rows': len(rows), 'sha256': checksum.hexdigest(), 'saved_embedding_cursor': cursor[0] if cursor else None}

    def check_resume(self, label, phase, doc_id):
        stop = self.state[label + '_interrupt']
        history = self.snapshots[-1]['maintenance']['history'][-1]
        committed = stop['commit_state'] == 'committed_before_checkpoint'
        expected_version = stop['pending']['version_before'] if committed else stop['table_version_after_stop']
        self.record(label + '_history_matches_stop', history['kind'] == phase
                    and history['version_before'] == expected_version and history['recovered'] == committed
                    and (not committed or self.snapshots[-1]['version'] == stop['table_version_after_stop']),
                    commit_state=stop['commit_state'], history=history)
        self.record(label + '_vectors_reused', self.vector_stamp(doc_id) == stop['vector_stamp'],
                    saved_embedding_cursor=stop['vector_stamp']['saved_embedding_cursor'])

    def covered(self, label, expected_rows):
        table = self.table()
        names = sorted({index.name for index in table.list_indices()})
        stats = {name: statistics(table, name) for name in names}
        state = json.loads((self.folder / 'index-state.json').read_text(encoding='utf-8'))
        snapshot = {'label': label, 'rows': table.count_rows(), 'version': version(table),
                    'indexes': stats, 'maintenance': state, 'at': time.time()}
        self.snapshots.append(snapshot)
        self.record(label, snapshot['rows'] == expected_rows
                    and set(names) == {'terms_idx', 'generation_idx', 'vector_idx'}
                    and state['ann_ready'] and 'pending' not in state
                    and all(s['num_indexed_rows'] == expected_rows and s['num_unindexed_rows'] == 0 for s in stats.values()),
                    rows=snapshot['rows'], expected_rows=expected_rows, indexes=stats)
        return snapshot

    def job(self, identity):
        row = self.jobs.status(str(self.wiki), identity)
        if row['status'] == 'failed':
            raise RuntimeError(row['error'])
        return row

    async def finish(self, identity):
        def completed():
            row = self.job(identity)
            return row if row['status'] == 'completed' else None
        return await wait_until(completed, 3600)

    async def interrupt(self, server, identity, phase, label):
        def operation():
            row = self.job(identity)
            if row['status'] == 'completed':
                raise RuntimeError(f'{label}: 指定の索引処理を捕捉する前にジョブが完了しました。')
            path = self.folder / 'index-state.json'
            pending = json.loads(path.read_text(encoding='utf-8')).get('pending') if path.exists() else None
            if row['phase'] == phase and pending and pending['kind'] == phase:
                return {'job': row, 'pending': pending}
            return None
        snapshot = await wait_until(operation, 3600)
        import psutil
        descendants = server.children(recursive=True)
        # OS は動かしたまま、このテストが起動した MCP サーバーだけを終了する。
        server.kill()
        _, alive = psutil.wait_procs(descendants + [server], timeout=15)
        snapshot['descendant_pids'] = [p.pid for p in descendants]
        snapshot['alive_after_parent_death'] = [p.pid for p in alive]
        snapshot['paused_job'] = self.job(identity)
        snapshot['rows_after_stop'] = self.table().count_rows()
        snapshot['table_version_after_stop'] = version(self.table())
        after = json.loads((self.folder / 'index-state.json').read_text(encoding='utf-8'))
        snapshot['pending_after_stop'] = after.get('pending')
        snapshot['indexes_after_stop'] = {name: statistics(self.table(), name) for name in {i.name for i in self.table().list_indices()}}
        doc_id = hashlib.sha256(Path(snapshot['job']['source']).read_bytes()).hexdigest()
        snapshot['vector_stamp'] = self.vector_stamp(doc_id)
        before_version = snapshot['pending']['version_before']
        after_version = snapshot['table_version_after_stop']
        complete = all(name in snapshot['indexes_after_stop']
                       and snapshot['indexes_after_stop'][name]['num_unindexed_rows'] == 0
                       and snapshot['indexes_after_stop'][name]['num_indexed_rows'] == snapshot['pending']['rows']
                       for name in snapshot['pending']['names'])
        snapshot['commit_state'] = ('not_committed' if after_version == before_version else
                                    'committed_before_checkpoint' if complete else 'partially_committed')
        self.state[label] = snapshot
        self.record(label + '_parent_death_stops_workers', not alive, descendants=len(descendants))
        self.record(label + '_job_paused', snapshot['paused_job']['status'] == 'paused',
                    job_id=identity, phase=snapshot['paused_job']['phase'])
        paused = snapshot['paused_job']
        boundary = paused['phase'] == phase and paused['completed'] == 0 and paused['total'] == 1
        boundary = boundary and snapshot['pending_after_stop'] == snapshot['pending']
        if phase == 'ANN の作成':
            boundary = boundary and after_version == before_version and 'vector_idx' not in snapshot['indexes_after_stop']
        self.record(label + '_stop_boundary_verified', boundary, commit_state=snapshot['commit_state'],
                    version_before=before_version, version_after=after_version)
        with self.engine._catalog(self.folder) as catalog:
            doc_count = catalog.execute('SELECT COUNT(*) FROM documents').fetchone()[0]
        return snapshot, doc_count

    def extracted_stamp(self, source):
        doc_id = hashlib.sha256(source.read_bytes()).hexdigest()
        cache = self.config.extraction_dir(doc_id)
        files = list(cache.glob('page-*.json'))
        if not files:
            raise RuntimeError('保存済みの抽出ページがありません。')
        return {p.name: [p.stat().st_mtime_ns, hashlib.sha256(p.read_bytes()).hexdigest()] for p in files}

    async def run(self):
        for job_key, proof_key in [('initial_job', 'ann_creation_interrupt'), ('append_job', 'ann_update_interrupt'),
                                   ('replacement_job', 'replacement_interrupt')]:
            if job_key in self.state and proof_key not in self.state:
                raise RuntimeError('中断の証跡を保存する前に検証が終了しています。合格として続行できません。')
        references = WORK / 'fixtures'
        references.mkdir(exist_ok=True)
        first = references / 'ann-initial.pdf'
        appended = references / 'ann-appended.pdf'
        if not first.exists():
            fixture(first, 40, 'FULL_INITIAL_Q83')
        if not appended.exists():
            fixture(appended, 4, 'FULL_APPEND_Q83')
        source_page = self.wiki / 'sources/ann-initial.md'
        if not source_page.exists():
            source_page.write_text('---\ntype: source\n---\n全量索引の追加資料。\n', encoding='utf-8', newline='\n')
            (self.wiki / 'dependent.md').write_text('---\nsources: [ann-initial]\n---\n資料を参照する概念。\n', encoding='utf-8', newline='\n')
        if 'initial_job' not in self.state:
            self.record('bulk_input_has_no_indexes', not self.table().list_indices(), rows=self.table().count_rows())
            async with connect(self.config_file) as (session, server):
                accepted = await call(session, 'register_pdf', wiki_root=str(self.wiki), source=str(first),
                                      source_page='sources/ann-initial.md')
                self.state['initial_job'] = accepted['job_id']
                self.save()
                stopped, count = await self.interrupt(server, accepted['job_id'], 'ANN の作成', 'ann_creation_interrupt')
                self.state['initial_extracted'] = self.extracted_stamp(first)
                self.record('initial_pdf_not_published_during_ann_creation', count == self.base['documents'])
                self.record('ann_creation_has_saved_embedding_checkpoint', stopped['rows_after_stop'] > self.base['chunks'])
        if 'initial_complete' not in self.state:
            async with connect(self.config_file, extra_env=self.resume_environment()) as (session, _):
                initial = await self.finish(self.state['initial_job'])
                self.record('ann_creation_resumes_same_job', initial['attempts'] == 2,
                            job_id=initial['job_id'], attempts=initial['attempts'])
                self.record('initial_extracted_pages_reused', self.extracted_stamp(first) == self.state['initial_extracted'])
                expected = self.base['chunks'] + initial['result']['chunks']
                self.covered('full_ann_created_after_reconnect', expected)
                self.record('ann_creation_keeps_saved_rows', self.state['ann_creation_interrupt']['rows_after_stop'] == expected)
                self.check_resume('ann_creation', 'ANN の作成', initial['result']['document_id'])
                self.state['initial_complete'] = initial
                self.save()
        initial = self.state['initial_complete']
        if 'append_job' not in self.state:
            async with connect(self.config_file) as (session, server):
                accepted = await call(session, 'register_pdf', wiki_root=str(self.wiki), source=str(appended),
                                      source_page='sources/ann-appended.md')
                self.state['append_job'] = accepted['job_id']
                self.save()
                stopped, count = await self.interrupt(server, accepted['job_id'], '索引の更新', 'ann_update_interrupt')
                self.state['append_extracted'] = self.extracted_stamp(appended)
                self.record('appended_pdf_not_published_during_update', count == self.base['documents'] + 1)
                self.record('ann_update_has_saved_embedding_checkpoint', stopped['rows_after_stop'] > self.snapshots[-1]['rows'])
        if 'append_complete' not in self.state:
            async with connect(self.config_file, extra_env=self.resume_environment()) as (session, _):
                added = await self.finish(self.state['append_job'])
                self.record('ann_update_resumes_same_job', added['attempts'] == 2,
                            job_id=added['job_id'], attempts=added['attempts'])
                self.record('appended_extracted_pages_reused', self.extracted_stamp(appended) == self.state['append_extracted'])
                expected = self.base['chunks'] + initial['result']['chunks'] + added['result']['chunks']
                self.covered('full_ann_updated_after_reconnect', expected)
                self.check_resume('ann_update', '索引の更新', added['result']['document_id'])
                self.state['append_complete'] = added
                self.save()
        added = self.state['append_complete']
        if 'replacement_interrupt' not in self.state:
            fixture(first, 44, 'FULL_REPLACED_Q83')
            gate = WORK / 'publication.gate'
            ready = gate.with_suffix('.ready.json')
            expected_gate = {'folder': str(self.folder), 'old_id': initial['result']['document_id'],
                             'new_id': hashlib.sha256(first.read_bytes()).hexdigest()}
            write_json(gate, expected_gate)
            extra_env = {'PYTHONPATH': str(ROOT / 'poc/rag/full_ann/fault_hook'),
                         'RAG_ANN_RETIREMENT_GATE': str(gate),
                         'RAG_ANN_TEST_SCRIPTS': str(ROOT / 'info-hive-rag/scripts')}
            async with connect(self.config_file, extra_env=extra_env) as (session, server):
                accepted = await call(session, 'register_pdf', wiki_root=str(self.wiki), source=str(first),
                                      source_page='sources/ann-initial.md')
                self.state['replacement_job'] = accepted['job_id']
                self.save()
                def committed():
                    row = self.job(accepted['job_id'])
                    if row['status'] == 'completed':
                        raise RuntimeError('公開後の待機を捕捉する前に差し替えが完了しました。')
                    if ready.exists():
                        observed = json.loads(ready.read_text(encoding='utf-8'))
                        if all(observed.get(key) == value for key, value in expected_gate.items()):
                            return observed
                    return None
                await wait_until(committed, 3600)
                import psutil
                descendants = server.children(recursive=True)
                server.kill()
                _, alive = psutil.wait_procs(descendants + [server], timeout=15)
                paused = self.job(accepted['job_id'])
                with self.engine._catalog(self.folder) as catalog:
                    new_active = catalog.execute('SELECT COUNT(*) FROM documents WHERE doc_id=?', (expected_gate['new_id'],)).fetchone()[0]
                    old_active = catalog.execute('SELECT COUNT(*) FROM documents WHERE doc_id=?', (expected_gate['old_id'],)).fetchone()[0]
                    queued = catalog.execute('SELECT COUNT(*) FROM retired_documents WHERE doc_id=?', (expected_gate['old_id'],)).fetchone()[0]
                old_rows = self.table().count_rows(f"doc_id = '{expected_gate['old_id']}'")
                self.state['replacement_interrupt'] = {'job': paused, 'old_rows': old_rows, 'new_active': new_active,
                    'old_active': old_active, 'retirement_queued': queued,
                    'table_version_after_stop': version(self.table()),
                    'vector_stamp': self.vector_stamp(expected_gate['new_id']),
                    'fault_injection': '製品の公開トランザクション確定後、後始末の入口で待機するテスト用フック',
                    'worker_pids': [p.pid for p in descendants]}
                self.record('replacement_interrupt_parent_death_stops_workers', not alive)
                self.record('replacement_interrupt_after_publication', paused['status'] == 'paused'
                            and paused['phase'] == '索引の公開' and paused['publication_started'] == 1
                            and new_active == 1 and old_active == 0 and queued == 1 and old_rows > 0)
            gate.unlink()
            answer = self.engine.search(str(self.wiki), 'FULL_INITIAL_Q83', limit=10)
            self.record('replacement_old_rows_hidden_before_cleanup', bool(answer['results'])
                        and all(r['doc_id'] != expected_gate['old_id'] for r in answer['results']),
                        physical_old_rows=old_rows)
        if 'replacement_complete' not in self.state:
            async with connect(self.config_file, extra_env=self.resume_environment()) as (session, _):
                replacement = await self.finish(self.state['replacement_job'])
                self.record('replacement_resumes_same_job', replacement['attempts'] == 2,
                            job_id=replacement['job_id'], attempts=replacement['attempts'])
                self.record('replacement_vectors_reused', self.vector_stamp(replacement['result']['document_id'])
                            == self.state['replacement_interrupt']['vector_stamp'])
                expected = self.base['chunks'] + added['result']['chunks'] + replacement['result']['chunks']
                self.covered('replacement_updates_full_indexes', expected)
                old_id = initial['result']['document_id']
                self.record('replaced_generation_rows_removed', self.table().count_rows(f"doc_id = '{old_id}'") == 0)
                self.record('replacement_marks_dependent_page', 'review_required: true' in (self.wiki / 'dependent.md').read_text(encoding='utf-8'))
                self.record('replacement_has_no_cleanup_error', replacement['result']['cleanup_error'] is None)
                with self.engine._catalog(self.folder) as catalog:
                    pending = catalog.execute('SELECT COUNT(*) FROM retired_documents').fetchone()[0]
                    generations = [row[0] for row in catalog.execute('SELECT generation FROM documents')]
                self.record('retirement_queue_empty', pending == 0)
                active = ','.join("'" + generation + "'" for generation in generations)
                self.record('replacement_no_inactive_generations', self.table().count_rows(f'generation NOT IN ({active})') == 0)
                answer = await call(session, 'search', wiki_root=str(self.wiki), query='FULL_REPLACED_Q83', limit=10)
                self.record('replacement_search_excludes_old_generation', any(r['doc_id'] == replacement['result']['document_id'] for r in answer['results'])
                            and all(r['doc_id'] != old_id for r in answer['results']))
                self.state['replacement_complete'] = replacement
                self.save()
        if 'reconnect_complete' not in self.state:
            before = self.covered('before_unchanged_registration', self.snapshots[-1]['rows'])
            async with connect(self.config_file) as (session, _):
                accepted = await call(session, 'register_pdf', wiki_root=str(self.wiki), source=str(first),
                                      source_page='sources/ann-initial.md')
                unchanged = await self.finish(accepted['job_id'])
                after = self.covered('after_unchanged_registration', before['rows'])
                # 0.4.0 以降は再登録を新ジョブで受け、本文を照合する。
                self.record('unchanged_registration_reuses_index', unchanged['result']['status'] == 'unchanged'
                            and before['version'] == after['version'] and before['indexes'] == after['indexes'])
                self.state['reconnect_complete'] = True
                self.save()
        await self.search_ocr()
        self.verify_vectors()
        import pyarrow.compute as pc
        table = self.table()
        ids = table.search().select(['chunk_id']).limit(None).to_arrow()['chunk_id']
        self.record('final_table_has_no_duplicate_chunk_ids', pc.count_distinct(ids).as_py() == table.count_rows())
        with self.engine._catalog(self.folder) as catalog:
            documents, chunks = catalog.execute('SELECT COUNT(*),SUM(chunks) FROM documents').fetchone()
        self.record('final_catalog_matches_table', documents == self.base['documents'] + 2 and chunks == table.count_rows(),
                    documents=documents, chunks=chunks)
        validate_checks(self.checks)
        self.state['status'] = 'completed'
        self.save()

    async def search_ocr(self):
        if 'ocr_search_complete' in self.state:
            return
        examples = []
        with readonly(WORK / 'prepared.sqlite') as db:
            candidates = db.execute('''SELECT doc_id,relative_path FROM documents
                WHERE ocr_pages>=20 ORDER BY ocr_pages DESC LIMIT 20''').fetchall()
            for candidate in candidates:
                cache = OCR / 'data/extracted' / candidate['doc_id'] / self.config.extraction_key
                for page in sorted(cache.glob('page-*.json')):
                    entry = json.loads(page.read_text(encoding='utf-8'))
                    if entry['ocr'] and len(entry['text'].strip()) > 250:
                        chunk = db.execute('SELECT page,text FROM chunks WHERE doc_id=? AND page=? ORDER BY number LIMIT 1',
                                           (candidate['doc_id'], entry['page'])).fetchone()
                        if chunk and len(chunk['text'].strip()) > 120:
                            examples.append({'doc_id': candidate['doc_id'], 'page': chunk['page'],
                                             'query': chunk['text'][:240], 'relative_path': candidate['relative_path']})
                            break
                if len(examples) == 3:
                    break
        if len(examples) != 3:
            raise RuntimeError('OCR 本文の検索試料を用意できません。')
        answers = []
        async with connect(self.config_file) as (session, _):
            for example in examples:
                with self.engine._catalog(self.folder) as catalog:
                    locations = {os.path.normcase(str(Path(row[0]))) for row in catalog.execute(
                        'SELECT path FROM locations WHERE doc_id=?', (example['doc_id'],))}
                started = time.perf_counter()
                answer = await call(session, 'search', wiki_root=str(self.wiki), query=example['query'], limit=10)
                matches = [r for r in answer['results'] if r['doc_id'] == example['doc_id'] and r['page'] == example['page']]
                correct = bool(matches) and any(r['text'].startswith(example['query']) for r in matches)
                correct = correct and all(r['raw'] and os.path.normcase(str(Path(r['raw']))) in locations
                    and r['source_pages'] == [f"sources/{example['doc_id']}.md"] and r['sha256'] == example['doc_id'] for r in matches)
                self.record('ocr_page_searchable_' + example['doc_id'][:12], correct,
                            page=example['page'], seconds=time.perf_counter() - started)
                query = example['query']
                evidence = {key: value for key, value in example.items() if key != 'query'}
                evidence['query_sha256'] = hashlib.sha256(query.encode('utf-8')).hexdigest()
                evidence['query_chars'] = len(query)
                safe_rows = []
                for row in answer['results']:
                    safe_rows.append({**{key: value for key, value in row.items() if key != 'text'},
                                      'text_sha256': hashlib.sha256(row['text'].encode('utf-8')).hexdigest(),
                                      'text_chars': len(row['text'])})
                answers.append({'example': evidence, 'results': safe_rows})
        write_json(OUT / 'ocr-search-smoke.json', {'method': '保存済み OCR 本文から作った既知ページ検索。品質評価用の人手質問ではない。', 'queries': answers})
        self.state['ocr_search_complete'] = True
        self.record('ocr_search_sources_verified', True, samples=len(answers))
        self.save()

    def verify_vectors(self):
        if self.state.get('vector_verification_complete'):
            return
        import numpy as np
        random = np.random.default_rng(20261119)
        selected = []
        with readonly(WORK / 'prepared.sqlite') as db:
            for source in ['seed', 'new']:
                ids = [row[0] for row in db.execute('SELECT id FROM chunks WHERE vector_source=?', (source,))]
                candidates = random.permutation(len(ids))
                accepted = 0
                for index in candidates:
                    row = db.execute('SELECT * FROM chunks WHERE id=?', (ids[index],)).fetchone()
                    unique = db.execute('SELECT COUNT(*) FROM chunks WHERE input_hash=?', (row['input_hash'],)).fetchone()[0]
                    if unique == 1 and len(row['text']) > 200:
                        selected.append(dict(row))
                        accepted += 1
                    if accepted == 8:
                        break
                if accepted != 8:
                    raise RuntimeError('ベクトルの照合試料が不足しています。')
        seed_path = BASE / 'embeddings-130m/vectors.f32'
        new_path = WORK / 'new-vectors.f32'
        arrays = {'seed': np.memmap(seed_path, dtype='float32', mode='r', shape=(seed_path.stat().st_size // 2048, 512)),
                  'new': np.memmap(new_path, dtype='float32', mode='r', shape=(new_path.stat().st_size // 2048, 512))}
        reference = self.engine.embedder.encode([row['embedding_text'] for row in selected])
        cosines = []
        for row, vector in zip(selected, reference):
            saved = arrays[row['vector_source']][row['position']]
            cosines.append(float(np.dot(saved, vector) / (np.linalg.norm(saved) * np.linalg.norm(vector))))
        self.record('stored_vectors_match_cpu_reference', min(cosines) >= 0.999,
                    samples=len(cosines), min_cosine=min(cosines), max_cosine=max(cosines))
        table = self.table()
        probes = []
        for row in selected[::2]:
            query = arrays[row['vector_source']][row['position']].tolist()
            ann = table.search(query).distance_type('cosine').nprobes(self.config.search_nprobes).refine_factor(self.config.search_refine_factor).select(['chunk_id']).limit(10).to_list()
            exact = table.search(query).distance_type('cosine').bypass_vector_index().select(['chunk_id']).limit(10).to_list()
            ann_ids = [item['chunk_id'] for item in ann]
            exact_ids = [item['chunk_id'] for item in exact]
            identity = f"{self.config.generation(row['doc_id'])}:{row['number']}"
            probes.append({'chunk_id': identity, 'source': row['vector_source'], 'known_vector_in_ann': identity in ann_ids,
                           'known_vector_in_exact': identity in exact_ids, 'ann_ids': ann_ids, 'exact_ids': exact_ids,
                           'top10_overlap': len(set(ann_ids) & set(exact_ids)) / len(exact_ids)})
        self.record('ann_only_returns_known_vectors', all(p['known_vector_in_ann'] and p['known_vector_in_exact'] for p in probes),
                    samples=len(probes), min_top10_overlap=min(p['top10_overlap'] for p in probes))
        write_json(OUT / 'vector-reference-and-ann.json', {'cosines': cosines, 'probes': probes,
                   'method': '既知の文書ベクトルによる ANN と全件走査の照合。利用者の質問に対する検索精度の評価ではない。',
                   'nprobes': self.config.search_nprobes, 'refine_factor': self.config.search_refine_factor})
        self.state['vector_verification_complete'] = True
        self.save()


if __name__ == '__main__':
    with phase_lock('mcp-verification'), measure('mcp'):
        asyncio.run(Verification().run())
