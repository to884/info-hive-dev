# 6 版目の試作の探索（サーバーの起動に、ない祖先を作る段を足したあと。サーバーに関わる探索だけ）

書き出しの道は変えていないので、書き出しの探索は [write_sweep-output-v6.md](write_sweep-output-v6.md) のままである。

Python 3.14.6、win32

## サーバーの記録（状態のディレクトリ 7 種。nodata を含む）

実行 2163 回、破れた決まり 0 件

## 同じ場所を使う別の Wiki

実行 450 回、破れた決まり 0 件

## 対照

| 対照 | 見つけた件数 | 最初の 1 件 |
| --- | --- | --- |
| refuse_unknown_entries | 209 | 次の起動が失敗した: 決まった名前のほかの項目がある: server.json.new（状態 absent、start、denied@37、write、rc=unknown） |
| skip_owner | 168 | 失敗のない実行で、別の Wiki のサーバーだと知らせて止まらなかった（B の serve、None@None、None、結果 reuse） |

129 秒
