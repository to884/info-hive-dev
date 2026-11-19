"""位置・文字画素・OCR の結果を集計する。"""
import json
import os
import re
import unicodedata
from pathlib import Path

directory = Path(os.environ.get('PELE_LABEL_RUN', Path(__file__).resolve().parent))
audit = json.loads((directory / 'results/results.json').read_text(encoding='utf-8'))
ocr = {row['id']: row for row in json.loads((directory / 'ocr/results.json').read_text(encoding='utf-8-sig'))}

def normalize(value):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', value))

def order_words(words, chars):
    # 句読点の小さい OCR 枠でも同じ行を保つよう、SVG の行位置を基準にする。
    centers = []
    for char in sorted(chars, key=lambda c: c['y']):
        center = char['y'] + char['height'] / 2
        if not any(abs(center - previous) < 2 for previous in centers):
            centers.append(center)
    lines = [[] for center in centers]
    for word in words:
        center = (word['y'] + word['height'] / 2) / 2
        index = min(range(len(centers)), key=lambda i: abs(centers[i] - center))
        lines[index].append(word)
    return ''.join(word['text'] for line in lines for word in sorted(line, key=lambda w: w['x']))

comparisons = []
for observation in audit['observations']:
    if observation['browser'] != 'chromium':
        continue
    for label in observation['labels']:
        box = label['bounds']
        selected = []
        for word in ocr[observation['id']]['words']:
            center_x = (word['x'] + word['width'] / 2) / 2
            center_y = (word['y'] + word['height'] / 2) / 2
            if box['x'] - 3 <= center_x <= box['x'] + box['width'] + 3 and box['y'] - 3 <= center_y <= box['y'] + box['height'] + 3:
                selected.append(word)
        recognized = order_words(selected, label['chars'])
        comparisons.append({'id': observation['id'], 'index': label['index'], 'expected': label['text'], 'ocr': recognized, 'matches': normalize(label['text']) == normalize(recognized)})

summary = {}
for browser in ('chromium', 'webkit'):
    observations = [row for row in audit['observations'] if row['browser'] == browser]
    labels = [label for row in observations for label in row['labels']]
    summary[browser] = {
        'figures': len(observations), 'labels': len(labels),
        'with_shape': sum(bool(label['shape']) for label in labels),
        'envelope_warnings': sum(bool(label['envelopeOutsideShape']) for label in labels),
        'char_mapping_mismatches': sum(not label['charCountMatches'] for label in labels),
        'overlapping_label_pairs': sum(len(row['overlaps']) for row in observations),
    }
for scale in (1, 2):
    rows = [row for row in audit['rendering'] if row['scale'] == scale]
    missing = [{'id': row['id'], 'label': label['index'], 'char': char} for row in rows for label in row['labelContributions'] for char in label['chars'] if char['pixels'] == 0]
    summary[f'png{scale}x'] = {'labels': sum(len(row['labelContributions']) for row in rows), 'nonspace_chars': sum(len(label['chars']) for row in rows for label in row['labelContributions']), 'zero_contribution_chars': missing}
refined = json.loads((directory / 'results/refinement.json').read_text(encoding='utf-8'))
summary['shape_ink_outside'] = [{'id': row['id'], **warning} for row in refined for warning in row['warnings'] if warning['outsidePixels']]
summary['foreign_nodes'] = [{'id': row['id'], **warning} for row in refined for warning in row['foreignNodes']]
summary['ocr'] = {'matched_labels': sum(row['matches'] for row in comparisons), 'mismatched_labels': sum(not row['matches'] for row in comparisons)}
(directory / 'ocr/comparisons.json').write_text(json.dumps(comparisons, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
(directory / 'ocr/mismatches.json').write_text(json.dumps([row for row in comparisons if not row['matches']], ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
(directory / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
print(json.dumps(summary, ensure_ascii=False))
