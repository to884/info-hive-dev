"""索引の後始末だけの修正であることを照合し、準備済み入力の固定記録を更新する。"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import subprocess
import time

from common import OCR, OUT, ROOT, WORK, digest, write_json


def method(source, class_name, name):
    tree = ast.parse(source)
    parent = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name)
    return next(node for node in parent.body if isinstance(node, ast.FunctionDef) and node.name == name)


def input_prefix(source):
    function = copy.deepcopy(method(source, 'Engine', 'ingest_pdf'))
    block = next(node for node in ast.walk(function) if isinstance(node, ast.With)
                 and any(isinstance(item.context_expr, ast.Call)
                         and isinstance(item.context_expr.func, ast.Attribute)
                         and item.context_expr.func.attr == '_catalog' for item in node.items))
    before = []
    retirement = ast.parse("""if not stale and connection.execute('SELECT 1 FROM retired_documents WHERE doc_id=?', (doc_id,)).fetchone():
    self._finish_retirements(folder, connection, only_doc_id=doc_id)
""").body[0]
    for statement in block.body:
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call) and isinstance(statement.value.func, ast.Attribute) and statement.value.func.attr == '_maintain_indexes':
            break
        if ast.dump(statement, include_attributes=False) == ast.dump(retirement, include_attributes=False):
            continue
        before.append(statement)
    block.body = before
    return ast.dump(function, include_attributes=False)


def unchanged_module(source):
    tree = ast.parse(source)
    permitted = {'_catalog', '_reset_index', '_finish_retirements', 'maintain_indexes', 'ingest_pdf'}
    engine = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'Engine')
    engine.body = [node for node in engine.body if not isinstance(node, ast.FunctionDef) or node.name not in permitted]
    return ast.dump(tree, include_attributes=False)


def main():
    path = WORK / 'source-policy.json'
    policy = json.loads(path.read_text(encoding='utf-8'))
    saved = policy['product_scripts']
    current = {p.name: digest(p) for p in sorted((ROOT / 'info-hive-rag/scripts').glob('*.py'))}
    changed = {name for name in saved if saved[name] != current[name]}
    if not changed:
        print('この製品コードは固定記録に取り込み済みです。')
        return
    if changed != {'rag_index.py'}:
        raise RuntimeError('索引の中核以外にもコードの変更があります。')
    old = subprocess.check_output(['git', '-C', str(ROOT / 'info-hive-rag'), 'show',
                                   '4fabe3294d86a367e635bc18635af6e7132a8d93:scripts/rag_index.py'], encoding='utf-8')
    new = (ROOT / 'info-hive-rag/scripts/rag_index.py').read_text(encoding='utf-8')
    if unchanged_module(old) != unchanged_module(new):
        raise RuntimeError('明示した台帳・公開・後始末の範囲以外にコードの変更があります。')
    if input_prefix(old) != input_prefix(new):
        raise RuntimeError('PDF の読み込みから埋め込み保存までのコードが変わっています。')
    for class_name, name in [('Embedder', '__init__'), ('Embedder', 'encode'), ('Engine', 'tokenize'), ('Engine', '_table')]:
        if ast.dump(method(old, class_name, name), include_attributes=False) != ast.dump(method(new, class_name, name), include_attributes=False):
            raise RuntimeError(f'入力・ベクトル・スキーマのコードが変わっています。{class_name}.{name}')
    # 保存済み OCR の抽出・分割関数と、現在使う関数も照合する。
    run = json.loads((OCR / 'run-policy.json').read_text(encoding='utf-8'))
    old_pdf = (OCR / 'rag' / run['rag_commit_prefix'] / 'scripts/rag_pdf.py').read_text(encoding='utf-8')
    new_pdf = (ROOT / 'info-hive-rag/scripts/rag_pdf.py').read_text(encoding='utf-8')
    same = {}
    for name in ['extract_pages', 'chunks_for']:
        a = next(n for n in ast.parse(old_pdf).body if isinstance(n, ast.FunctionDef) and n.name == name)
        b = next(n for n in ast.parse(new_pdf).body if isinstance(n, ast.FunctionDef) and n.name == name)
        same[name] = ast.dump(a, include_attributes=False) == ast.dump(b, include_attributes=False)
    if not all(same.values()):
        raise RuntimeError('保存済み OCR の抽出または分割の関数が異なります。')
    record = {'at': time.time(), 'before_product_scripts': saved, 'after_product_scripts': current,
              'ingest_input_prefix_unchanged': True, 'embedding_and_tokenization_unchanged': True,
              'ocr_v050_functions_match': same, 'permitted_methods': ['_catalog', '_reset_index', '_finish_retirements', 'maintain_indexes', 'ingest_pdf'],
              'reason': '公開と同じ台帳に旧文書の後始末を保存し、削除と再開位置を整合させる修正'}
    patch = subprocess.check_output(['git', '-C', str(ROOT / 'info-hive-rag'), 'diff',
                                     '4fabe3294d86a367e635bc18635af6e7132a8d93', '--', 'scripts/rag_index.py'])
    patch_path = OUT / ('product-fix-' + current['rag_index.py'][:12] + '.patch')
    patch_path.write_bytes(patch)
    record['patch'] = patch_path.name
    record['patch_sha256'] = hashlib.sha256(patch).hexdigest()
    log_path = OUT / 'index-fix-adoption-log.json'
    previous = json.loads(log_path.read_text(encoding='utf-8')) if log_path.exists() else [json.loads((OUT / 'index-fix-adoption.json').read_text(encoding='utf-8'))]
    write_json(log_path, previous + [record])
    write_json(OUT / 'index-fix-adoption.json', record)
    policy['product_scripts'] = current
    write_json(path, policy)
    write_json(OUT / 'source-policy.json', policy)
    print(json.dumps(record, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
