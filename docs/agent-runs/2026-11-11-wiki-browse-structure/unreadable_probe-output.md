Python 3.14.6、win32

## drawn
- N: ['concepts/a', 'concepts/b', 'concepts/c']
- U: ['concepts/b', 'concepts/c']
- E: ['concepts/a', 'concepts/b', 'concepts/c']

## unresolved
- N: [('concepts/a.md', 'missing')]
- U: [('concepts/b.md', 'a')]
- E: []

## backlinks
- N: {'concepts/a': ['concepts/b'], 'concepts/b': ['concepts/a'], 'concepts/c': ['concepts/a']}
- U: {}
- E: {'concepts/a': ['concepts/b']}

## diagnostics
- N: [('unresolved', 'concepts/a')]
- U: [('read_error', 'concepts/a'), ('unresolved', 'concepts/b')]
- E: []

## files
- N: ['concepts/a.html', 'concepts/b.html', 'concepts/c.html', 'data/diagnostics.js', 'data/manifest.js', 'index.html', 'nav.js']
- U: ['concepts/b.html', 'concepts/c.html', 'data/diagnostics.js', 'data/manifest.js', 'index.html', 'nav.js']
- E: ['concepts/a.html', 'concepts/b.html', 'concepts/c.html', 'data/diagnostics.js', 'data/manifest.js', 'index.html', 'nav.js']

## N と比べて、中身が変わった出力のファイル
- U: ['concepts/a.html', 'concepts/b.html', 'concepts/c.html', 'data/diagnostics.js', 'data/manifest.js', 'index.html', 'nav.js']
- E: ['concepts/a.html', 'concepts/b.html', 'concepts/c.html', 'data/diagnostics.js', 'index.html', 'nav.js']

## lint の broken_links（a.md の読み取りを失敗させる）
- N: [('concepts/a.md', 'missing')]
- U: [('concepts/b.md', 'a')]
