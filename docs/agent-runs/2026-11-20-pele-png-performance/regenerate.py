"""保存した 50 原稿と、製品処理による Pele SVG の一致を確認する。"""
import hashlib
import json
import sys
from pathlib import Path

directory = Path(__file__).resolve().parent
root = directory.parents[2]
content = (directory / 'sources.json').read_bytes()
assert hashlib.sha256(content).hexdigest() == 'f882a73df7f2836ca48331909d35c7d2941b874c0709015fb59a202fbfcf1741'
sources = json.loads(content)
sys.path.insert(0, str(root / 'info-hive-wiki/skills/info-hive/scripts'))
from wiki_browse_pele import render_sources

images, warnings = render_sources(sources)
assert not warnings and len(images) == len(sources) == 50
for index, source in enumerate(sources):
    for theme, data in zip(('light', 'dark'), images[source][:2]):
        assert (directory / 'fixture' / theme / f'{index}-pele.svg').read_bytes() == data
print('原稿の SHA-256 と Pele SVG 100 枚が一致した')
