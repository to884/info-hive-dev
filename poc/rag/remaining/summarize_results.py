"""確定済みの検証結果を照合し、条件と未確認範囲をまとめる。"""
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'info-hive-rag/scripts'))
from rag_config import write_json
from provenance import approved_queries
OUT=ROOT/'docs/research/rag-validation-remaining-2026-11-04'


def read(name): return json.loads((OUT/name).read_text(encoding='utf-8'))


def checked(name,expected):
    checks=read(name)['checks']
    if len(checks)!=expected or not all(check['passed'] for check in checks):
        raise RuntimeError(f'{name} に未完了または失敗した機能試験があります。')
    return {'passed':len(checks),'evidence':name}


def main():
    assert len(approved_queries())==60
    extraction=read('full-extraction-summary.json')
    embedding=read('full-embedding-summary.json')
    index=read('full-product-index.json')
    generation=read('full-generation-index.json')
    baseline=read('full-mcp-results.json')
    final=read('full-generation-bitmap-mcp-results.json')
    ann=read('full-ann-quality.json')
    assert extraction['status']==embedding['status']=='completed'
    assert extraction['failed_files']==0
    assert extraction['unique_chunks']==embedding['active_chunks']==index['chunks']==generation['before']['rows']==generation['after']['rows']==ann['rows']
    assert len(baseline['profiles'])==len(final['profiles'])==3
    assert all(profile['queries']==72 for profile in final['profiles'])
    for profile in final['profiles']:
        original=next(row for row in baseline['profiles'] if row['profile']==profile['profile'])
        assert original['recall_at_30']==profile['recall_at_30']
        assert original['ndcg_at_10']==profile['ndcg_at_10']
    for path in [ROOT/'.rag-poc-data/unit-windows-context.log',OUT/'linux/unit.log']:
        log=path.read_text(encoding='utf-8')
        assert 'Ran 11 tests' in log and '\nOK\n' in log
    assert all(case['build_confirmed'] for case in read('ann-linux-api-smoke.json')['cases'])
    results={
        'date':'2026-11-04','verification_run_status':'completed','all_candidates_accepted':False,
        'os_scope':['windows','linux'],'excluded_by_user':['os_power_cut','macos'],
        'os_shutdown_or_restart_commands_executed':False,
        'functional_checks':{
            'windows_unit_tests':11,'linux_unit_tests':11,
            'multiple_mcp_sessions':checked('concurrency-results.json',13),
            'windows_uv_controls':checked('controls-results.json',5),
            'retrieval_configuration':checked('retrieval-config-results.json',4),
            'linux_pdf_pipeline':checked('linux/pipeline-results.json',18),
            'linux_uv_controls':checked('linux/controls-results.json',5)
        },
        'source':{'local_pdf_files':extraction['files_completed'],'source_bytes':extraction['source_bytes'],'unique_documents':extraction['unique_pdf_contents'],'unique_pages':extraction['unique_pages'],'chunks':index['chunks'],'source_size_or_mtime_changes':extraction['source_metadata_changed_files']},
        'full_index':{'native_text_only':True,'document_embedding_device':'cuda','query_device':'cpu','model':index['model'],'vector_index':'IVF_SQ','generation_index':'BITMAP','bytes':generation['after']['disk_bytes'],'construction_sampled_peak_rss_bytes':index['sampled_peak_process_rss_bytes']},
        'full_mcp_profiles':[{'profile':row['profile'],'p95_ms':row['warm_p95_ms'],'p95_below_1000ms':row['warm_p95_ms']<1000,'page_recall_at_30':row['recall_at_30'],'ndcg_at_10':row['ndcg_at_10'],'aggregate_peak_rss_bytes':row['aggregate_peak_rss_bytes']} for row in final['profiles']],
        'ann':{'nprobes':ann['nprobes'],'refine_factor':ann['refine_factor'],'exact_top30_id_recall':ann['mean_id_recall_at_30'],'native_ann_p95_ms':ann['p95_ms']},
        'limitations':[
            '全量のOCR候補22335ページは処理していない。規模検証では抽出済みテキストと文書ベクトルを投入した。',
            '全量ANNと世代索引は補助コードで作成。製品の自動作成・継続更新を含む全資料の取り込みE2Eは未検証。',
            'CPUによる全量の文書埋め込み時間は測っていない。',
            '承認済み60問の正解ラベルは4文書由来で、全資料に対する網羅的な関連判定ではない。',
            'xsmallは今回の全量MCP検索でもp95が1秒を超えた。',
            'OCRの段組み・表の読み順、数式の誤認、縦書きの偽陽性、一般的な正解なし質問の棄却が残る。',
            'WindowsでのQdrant binary量子化は設定受理まで。Linuxの1k API試験では実payload生成を確認したが、大規模品質は未検証。',
            'Linuxの旧環境破損とキャンセル遅延の初回失敗を保持。独立環境と負荷の異なる再試験で機能試験を完了した。',
            '検証用ストレージの削除は自動承認レビューがblocked by policyとして拒否したため保持した。'
        ]
    }
    write_json(OUT/'verification-summary.json',results)
    print('確定済みの検証結果、件数、承認済み質問の整合を確認しました。',flush=True)


if __name__=='__main__': main()
