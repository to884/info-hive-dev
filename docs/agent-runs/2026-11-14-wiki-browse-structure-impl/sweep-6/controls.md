Python 3.12.13、win32、部分 controls

## 対照

| 対照 | 見つけた件数 | 最初の 1 件 |
| --- | --- | --- |
| skip_gate | 6789 | browse のものでない書き出し先か、Wiki のルートが変わった（gen+extra/asis/out、None@None、None、rc=0） |
| follow_links | 6314 | 書き出し先と領分の外が変わった（gen/junction/out、None@None、None、rc=0） |
| commit_then_fail | 126 | 確定のあとの失敗で、0 でなく終わった（gen/asis/out、denied@333、lstat、rc=unknown） |
| chmod_on_delete | 2854 | 書き出し先と領分の外が変わった（gen+hardlink/asis/out、None@None、None、rc=0） |
| no_root_guard | 12116 | 書き出し先と領分の外が変わった（wikiroot/asis/out、None@None、None、rc=0） |
| climb_on_absent | 2 | 書き出し先と領分の外が変わった（insidewiki/asis/out、absent@8、lstat、rc=stop） |
| default_verifies | 1161 | 既定の書き出し先の前の世代を読んだ（gen/asis/default、None@None、None、rc=0） |
| swallow_close | 24 | 確定の前の「分からない」の失敗を吸収して 0 で終わった（absent/asis/out、denied@221、close-write、rc=0） |
| silent_post_commit | 149 | 「分からない」の失敗を、警告なしに吸収して 0 で終わった（gen/asis/out、denied@333、lstat、rc=0） |
| coarse_warning | 2 | 「分からない」の失敗を、警告なしに吸収して 0 で終わった（gen+hardlink/asis/out、denied@355、unlink、rc=0） |
| report_fails_unit | 2 | 確定のあとの失敗で、0 でなく終わった（absent/asis/out、denied@280、stdout_write、rc=unknown） |
| swallow_marker_failure | 1 | 確定の前の「分からない」の失敗を吸収して 0 で終わった（absent/asis/out、denied@221、close-write、rc=0） |
| fallback_rmdir | 18 | 「分からない」の失敗を、警告なしに吸収して 0 で終わった（absent/junction/out、denied@238、lstat、rc=0） |
| follow_on_open | 8 | 書き出し先と領分の外が変わった（absent/lock-dangling/out、absent@220、lstat、rc=0） |
| discard_old_first | 774 | 確定の前の「分からない」の失敗を吸収して 0 で終わった（empty+old/asis/out、denied@238、lstat、rc=0） |
| warn_on_marker_close | 17 | 確定の前の「分からない」の失敗を吸収して 0 で終わった（absent/asis/out、denied@216、lstat、rc=0） |
| enter_root_unchecked | 10300 | 書き出し先と領分の外が変わった（browse-junction/asis/default、None@None、None、rc=0） |
| raise_post_listdir | 10 | 確定のあとの失敗で、0 でなく終わった（gen/asis/out、denied@328、scandir_open、rc=unknown） |
| cache_ids_by_name | 80 | 作業用に残りがある: ['del-1']（gen+datajunction/asis/default、denied@291、lstat、rc=0） |
| recover_unchecked | 1433 | 失敗のない実行が 0 で終わらなかった（absent/old-junction/out、None@None、None、rc=stop） |
| accept_out_link | 2052 | 書き出し先と領分の外が変わった（outlink-junction/asis/default、None@None、None、rc=0） |
| enter_root_first | 6 | 書き出し先と領分の外が変わった（datainout/asis/out、None@None、None、rc=stop） |
| warn_on_record_failure（サーバーなど） | 115 | 起動の「分からない」の失敗を吸収して、起動した（状態 absent、start、denied@80、lstat、rc=ok） |
| recover_by_published_seq（サーバーなど） | 2 | 最後に公開した世代（G1）が残っていない（既定、rc=0,crash,unknown、書き出し先の中身 ['index.html']） |
| delete_in_place（サーバーなど） | 48 | 書き出し先を消したあとの、復旧の直後の失敗で、途中の世代が書き出し先に残った（rc=unknown）（gen/asis/default、crash@294、lstat） |
| refuse_unknown_entries（サーバーなど） | 1392 | 次の起動が失敗した: 決まった名前のほかの項目がある: server.json.new（状態 absent、start、denied@82、write、rc=unknown） |
| skip_owner（サーバーなど） | 324 | 失敗のない実行で、別の Wiki のサーバーだと知らせて止まらなかった（B の serve、None@None、None、結果 reuse） |
| enter_root_unchecked（サーバーなど） | 620 | 失敗のない実行で、領分の名前のリンクで止まらなかった（browse-junction、serve、None@None、None、結果 started） |

## 気づき

- 読み取り専用のファイルは消せず、作業用に残る（属性を変えないため）: del-1
- 読み取り専用のファイルは消せず、作業用に残る（属性を変えないため）: del-9

8510 秒
exit 0
