Python 3.12.13、win32

## サーバーの記録

実行 6174 回、破れた決まり 0 件

## サーバーの記録（<data_dir> そのものがジャンクション）

実行 5689 回、破れた決まり 0 件

## 領分の名前がリンク、目印のない空の状態のディレクトリ（起動、stop と動いているかの確かめ）

実行 77 回、破れた決まり 0 件

## 同じ場所を使う別の Wiki

実行 366 回、破れた決まり 0 件

## 強制停止のあとで、利用者が書き出し先を消す

実行 1646 回、破れた決まり 0 件

## 番号の巻き戻りと復旧（3 回の実行に 1 つずつの失敗）

破れた決まり 0 件

## 対照

| 対照 | 見つけた件数 | 最初の 1 件 |
| --- | --- | --- |
| skip_gate | 3927 | browse のものでない書き出し先か、Wiki のルートが変わった（gen+extra/asis/out、None@None、None、rc=0） |
| follow_links | 1743 | 書き出し先と領分の外が変わった（gen/junction/out、None@None、None、rc=stop） |
| commit_then_fail | 126 | 確定のあとの失敗で、0 でなく終わった（gen/asis/out、denied@182、lstat、rc=unknown） |
| chmod_on_delete | 1690 | 書き出し先と領分の外が変わった（gen+hardlink/asis/out、None@None、None、rc=0） |
| no_root_guard | 4265 | 書き出し先と領分の外が変わった（wikiroot/asis/out、None@None、None、rc=0） |
| climb_on_absent | 2 | 書き出し先と領分の外が変わった（insidewiki/asis/out、absent@9、lstat、rc=stop） |
| default_verifies | 830 | 既定の書き出し先の前の世代を読んだ（gen/asis/default、None@None、None、rc=0） |
| swallow_close | 24 | 確定の前の「分からない」の失敗を吸収して 0 で終わった（absent/asis/out、denied@64、close-write、rc=0） |
