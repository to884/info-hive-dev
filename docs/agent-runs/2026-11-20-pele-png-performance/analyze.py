"""保存した 4 方式の原標本を既存の検証処理で照合し、比較を集計する。"""
import json
import os
import statistics
from pathlib import Path
from runpy import run_path

directory = Path(__file__).resolve().parent
result_directory = Path(os.environ.get('PELE_PERF_RUN', directory))
root = directory.parents[2]
analysis = root / 'docs/agent-runs/2026-11-19-wiki-static-svg-vs-png/analysis'
helpers = run_path(str(analysis / 'analyze-figure-followup.py'))
checkpoint = run_path(str(analysis / 'analyze-retention.py'))['summarize_checkpoint']
result = json.loads((result_directory / 'memory/results.json').read_text(encoding='utf-8'))
assert result['inputsUnchanged'] and not result['requestsGC']
assert len(result['cases']) == result['repeats'] * len(result['conditions']) == 8
rows = []
for case in result['cases']:
    assert case['ok'] and case['cleanupMethod'] == 'owned-browser-kill'
    points, samples = helpers['checked_case'](case, result_directory / 'memory', checkpoint)
    rounds = helpers['summarize_static_images'](case, points, result, False)
    assert len(rounds) == 10
    empty = helpers['brief'](points['empty'])
    start = next(event['utcMs'] for event in case['events'] if event['label'] == 'round-1-light')
    end = next(point['observedUtcMs'] for point in case['checkpoints'] if point['phase'] == 'round-10-retained')
    observed = [sample for sample in samples if not sample['missing_children'] and sample['start_utc_ms'] >= start and sample['utc_ms'] <= end]
    stable = [sample for sample in observed if sample['stable']]
    peak = max(sample['private_bytes'] for sample in observed)
    intervals = [b['utc_ms'] - a['utc_ms'] for a, b in zip(observed, observed[1:])]
    web_peak = max(sum(process['private_bytes'] for process in sample['process_rows'] if process['name'] == 'WebKitWebProcess') for sample in observed)
    during_draw = [sample for sample in stable if sample['phase'].endswith(('-light', '-dark'))]
    rows.append({
        'condition': case['condition'], 'repeat': case['repeat'], 'id': case['id'],
        'empty': empty, 'observed_peak_private_bytes': peak,
        'peak_increment_bytes': peak - empty['private_bytes'],
        'stable_max_increment_bytes': max(sample['private_bytes'] for sample in stable) - empty['private_bytes'],
        'web_peak_increment_bytes': web_peak - empty['web_private_bytes'],
        'web_round10_increment_bytes': rounds[-1]['retained']['web_private_bytes'] - empty['web_private_bytes'],
        'window_start_utc_ms': start, 'window_end_utc_ms': end,
        'boundary_samples_in_window': sum(not sample['stable'] for sample in observed),
        'stable_samples_during_draw': len(during_draw),
        'round10': rounds[-1]['retained'],
        'round10_increment_bytes': rounds[-1]['retained']['private_bytes'] - empty['private_bytes'],
        'sample_interval_median_ms': statistics.median(intervals),
        'sample_interval_max_ms': max(intervals),
        'web_process_pids': [row['retained']['web_pids'] for row in rounds],
        'rounds': rounds,
    })

paint = json.loads((result_directory / 'paint/results.json').read_text(encoding='utf-8'))
assert len(paint['results']) == 8
summary = {'cases': rows, 'conditions': {}}
for condition in ['pele', 'normalized', 'png1x', 'png2x']:
    selected = [row for row in rows if row['condition'] == condition]
    assert len(selected) == 2
    summary['conditions'][condition] = {
        'peak_increment_median_bytes': statistics.median(row['peak_increment_bytes'] for row in selected),
        'stable_max_increment_median_bytes': statistics.median(row['stable_max_increment_bytes'] for row in selected),
        'web_peak_increment_median_bytes': statistics.median(row['web_peak_increment_bytes'] for row in selected),
        'web_round10_increment_median_bytes': statistics.median(row['web_round10_increment_bytes'] for row in selected),
        'round10_private_median_bytes': statistics.median(row['round10']['private_bytes'] for row in selected),
        'round10_increment_median_bytes': statistics.median(row['round10_increment_bytes'] for row in selected),
        'first_decode_light_ms': [row['rounds'][0]['light']['first_decode_ms'] for row in selected],
        'cached_first_decode_median_ms': statistics.median(row['rounds'][i][color]['first_decode_ms'] for row in selected for i in range(1, 10) for color in ['light', 'dark']),
        'paint_confirmation_ms': {color: [row[color]['screenshotCompletedMs'] for row in paint['results'] if row['format'] == condition] for color in ['light', 'dark']},
    }
manifest = result['staticImage']
summary['asset_bytes'] = {kind: sum(row[kind]['bytes'] for color in ['light', 'dark'] for row in manifest['images'][color]) for kind in summary['conditions']}
summary['source_sha256'] = manifest['sourceSha256']
(result_directory / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
print(json.dumps({'conditions': summary['conditions'], 'asset_bytes': summary['asset_bytes']}, ensure_ascii=False))
