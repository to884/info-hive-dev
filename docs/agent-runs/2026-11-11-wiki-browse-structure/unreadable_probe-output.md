Python 3.14.6、win32

## `concepts/a.md` を読めなくする

| | N（すべて読める） | U（読めない） | R（取り除いた木） | E（空にした。対照） |
| --- | --- | --- | --- | --- |
| 描くページ | ['concepts/a', 'concepts/b', 'concepts/c'] | ['concepts/b', 'concepts/c'] | ['concepts/b', 'concepts/c'] | ['concepts/a', 'concepts/b', 'concepts/c'] |
| 未解決リンク | [('concepts/a.md', 'missing')] | [('concepts/b.md', 'a')] | [('concepts/b.md', 'a')] | [] |
| リンクの解決 | {'concepts/a': [('b', 'resolved', 'concepts/b', ()), ('missing', 'unresolved', None, ()), ('c#見出し', 'resolved', 'concepts/c', ())], 'concepts/b': [('a', 'resolved', 'concepts/a', ())], 'concepts/c': []} | {'concepts/b': [('a', 'unresolved', None, ())], 'concepts/c': []} | {'concepts/b': [('a', 'unresolved', None, ())], 'concepts/c': []} | {'concepts/a': [], 'concepts/b': [('a', 'resolved', 'concepts/a', ())], 'concepts/c': []} |
| 被リンク | {'concepts/a': ['concepts/b'], 'concepts/b': ['concepts/a'], 'concepts/c': ['concepts/a']} | {} | {} | {'concepts/a': ['concepts/b']} |

- lint の broken_links（読めなくしたとき）: [('concepts/b.md', 'a')]
- U と R: リンクの解決が同じ True、被リンクが同じ True、未解決リンクが同じ True。世代の識別子をそろえて、中身が違う出力のファイル ['data/diagnostics.js', 'index.html']（そろえないと 6 個）
- E と R: リンクの解決が同じ False、被リンクが同じ False、未解決リンクが同じ False。世代の識別子をそろえて、中身が違う出力のファイル ['concepts/a.html', 'concepts/b.html', 'data/diagnostics.js', 'data/manifest.js', 'index.html', 'nav.js']（そろえないと 7 個）

## `two/x.md` を読めなくする

| | N（すべて読める） | U（読めない） | R（取り除いた木） | E（空にした。対照） |
| --- | --- | --- | --- | --- |
| 描くページ | ['b', 'one/x', 'two/x'] | ['b', 'one/x'] | ['b', 'one/x'] | ['b', 'one/x', 'two/x'] |
| 未解決リンク | [] | [] | [] | [] |
| リンクの解決 | {'b': [('x', 'ambiguous', None, ('one/x', 'two/x'))], 'one/x': [], 'two/x': []} | {'b': [('x', 'resolved', 'one/x', ())], 'one/x': []} | {'b': [('x', 'resolved', 'one/x', ())], 'one/x': []} | {'b': [('x', 'ambiguous', None, ('one/x', 'two/x'))], 'one/x': [], 'two/x': []} |
| 被リンク | {} | {'one/x': ['b']} | {'one/x': ['b']} | {} |

- lint の broken_links（読めなくしたとき）: []
- U と R: リンクの解決が同じ True、被リンクが同じ True、未解決リンクが同じ True。世代の識別子をそろえて、中身が違う出力のファイル ['data/diagnostics.js', 'index.html']（そろえないと 6 個）
- E と R: リンクの解決が同じ False、被リンクが同じ False、未解決リンクが同じ True。世代の識別子をそろえて、中身が違う出力のファイル ['b.html', 'data/diagnostics.js', 'data/manifest.js', 'index.html', 'nav.js', 'one/x.html', 'two/x.html']（そろえないと 7 個）
