"""実 LanceDB に対する ANN の作成、差分、再構築、コミット直後の復帰。"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'info-hive-rag/scripts'))
from rag_config import Config
from rag_index import Engine
from rag_indexes import statistics,version

class IndexTests(unittest.TestCase):
    def setUp(self):
        import numpy as np
        self.temp=tempfile.TemporaryDirectory(dir=os.environ.get('RAG_TEST_RUN_ROOT',str(ROOT/'.rag-poc-data')),ignore_cleanup_errors=True)
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name); self.wiki=self.root/'wiki'; self.wiki.mkdir()
        (self.wiki/'SCHEMA.md').write_text('# 索引試験\n',encoding='utf-8')
        self.cfg=Config({'data_dir':str(self.root/'data'),'embedding_model':'cl-nagoya/ruri-v3-30m',
            'ann_min_rows':16,'index_cleanup_age_days':3650})
        self.engine=Engine(self.cfg); self.folder=self.cfg.workspace(str(self.wiki))
        self.engine._check_policy(self.folder)
        self.table=self.engine._table(self.folder,create=True)
        self.rng=np.random.default_rng(20261104)

    def add(self,count,start=0):
        import numpy as np
        vectors=self.rng.normal(size=(count,256)).astype(np.float32)
        vectors/=np.linalg.norm(vectors,axis=1,keepdims=True)
        self.table.add([{'chunk_id':f'g:{start+i}','doc_id':'doc','generation':'g','page':start+i+1,
            'section':'検証','title':'索引の試験','text':'追加の検証' if start else '最初の検証',
            'terms':'追加 検証' if start else '最初 検証','vector':vector.tolist()} for i,vector in enumerate(vectors)])

    def maintain(self): return self.engine._maintain_indexes(self.folder,self.table)

    def assert_covered(self,rows):
        for name in ['terms_idx','generation_idx','vector_idx']:
            stats=statistics(self.table,name)
            self.assertEqual((stats['num_indexed_rows'],stats['num_unindexed_rows']),(rows,0))

    def test_create_append_and_unchanged_noop(self):
        self.add(32); state=self.maintain()
        self.assertTrue(state['ann_ready']); self.assertEqual(state['trained_rows'],32)
        self.assert_covered(32)
        self.add(8,32); state=self.maintain(); self.assert_covered(40)
        self.assertTrue(self.table.search('追加',query_type='fts',fts_columns='terms').to_list())
        previous=version(self.table); parts=statistics(self.table,'vector_idx')['num_indices']
        self.maintain(); self.maintain()
        self.assertEqual(version(self.table),previous)
        self.assertEqual(statistics(self.table,'vector_idx')['num_indices'],parts)

    def test_growth_and_delete_trigger_rebuild(self):
        self.add(32); self.maintain(); self.add(96,32)
        state=self.maintain(); self.assertEqual(state['trained_rows'],128)
        self.assertEqual(statistics(self.table,'vector_idx')['num_indices'],1)
        self.table.delete('page <= 64')
        state=self.maintain(); self.assertEqual(state['trained_rows'],64)
        self.assertEqual(state['deleted_since_training'],0)
        self.assert_covered(64)
        self.assertEqual(self.table.count_rows('page <= 64'),0)

    def test_resume_after_ann_commit_does_not_rebuild(self):
        self.add(32); actual=self.table.create_index
        def committed_then_interrupted(*args,**kwargs):
            actual(*args,**kwargs)
            raise RuntimeError('ANN コミット直後の中断')
        with patch.object(self.table,'create_index',side_effect=committed_then_interrupted):
            with self.assertRaisesRegex(RuntimeError,'コミット'): self.maintain()
        before=version(self.table)
        with patch.object(self.table,'create_index',side_effect=AssertionError('完了済み ANN を再作成しました')):
            state=self.maintain()
        self.assertEqual(version(self.table),before)
        self.assertEqual(state['trained_rows'],32)
        self.assertTrue(any(row['recovered'] for row in state['history']))
        self.assert_covered(32)

    def test_resume_after_optimize_commit_does_not_add_delta(self):
        self.add(32); self.maintain(); self.add(8,32); actual=self.table.optimize
        def committed_then_interrupted(*args,**kwargs):
            actual(*args,**kwargs)
            raise RuntimeError('更新コミット直後の中断')
        with patch.object(self.table,'optimize',side_effect=committed_then_interrupted):
            with self.assertRaisesRegex(RuntimeError,'コミット'): self.maintain()
        before=version(self.table); parts=statistics(self.table,'vector_idx')['num_indices']
        with patch.object(self.table,'optimize',side_effect=AssertionError('完了済み更新を再実行しました')):
            self.maintain()
        self.assertEqual(version(self.table),before)
        self.assertEqual(statistics(self.table,'vector_idx')['num_indices'],parts)
        self.assert_covered(40)

if __name__=='__main__': unittest.main(verbosity=2)
