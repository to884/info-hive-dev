# 8 版目の試作の探索（全量）

領分の根に入る決まり、書き込みの口の確かめが Wiki のルートの鎖と結論だけを覚える形、役目を先に決める判定を入れたあとの、全部の状態の探索である。破れた決まりは 0 件、飛ばした状態は 0 件だった。標準エラーに出たのは、15 分ごとの `faulthandler` のスタックの書き出し（止まっていないことの確かめ）だけである。

Python 3.14.6、win32

## サーバーの記録

実行 3923 回、破れた決まり 0 件

## 領分の名前がリンク（データの場所と状態のディレクトリ。起動、stop、動いているかの確かめ）

実行 93 回、破れた決まり 0 件

## 同じ場所を使う別の Wiki

実行 499 回、破れた決まり 0 件

## 強制停止のあとで、利用者が書き出し先を消す

実行 1450 回、破れた決まり 0 件

## 番号の巻き戻りと復旧（3 回の実行に 1 つずつの失敗）

破れた決まり 0 件

## 対照

| 対照 | 見つけた件数 | 最初の 1 件 |
| --- | --- | --- |
| skip_gate | 3053 | browse のものでない書き出し先か、Wiki のルートが変わった（gen+extra/asis/out、None@None、None、rc=0） |
| follow_links | 971 | 書き出し先と領分の外が変わった（gen/junction/out、None@None、None、rc=stop） |
| commit_then_fail | 126 | 確定のあとの失敗で、0 でなく終わった（gen/asis/out、denied@135、lstat、rc=unknown） |
| chmod_on_delete | 1327 | 書き出し先と領分の外が変わった（gen+hardlink/asis/out、None@None、None、rc=0） |
| no_root_guard | 3043 | 書き出し先と領分の外が変わった（wikiroot/asis/out、None@None、None、rc=0） |
| climb_on_absent | 2 | 書き出し先と領分の外が変わった（insidewiki/asis/out、absent@8、lstat、rc=stop） |
| default_verifies | 828 | 既定の書き出し先の前の世代を読んだ（gen/asis/default、None@None、None、rc=0） |
| swallow_close | 24 | 確定の前の「分からない」の失敗を吸収して 0 で終わった（absent/asis/out、denied@27、close-write、rc=0） |
| silent_post_commit | 149 | 「分からない」の失敗を、警告なしに吸収して 0 で終わった（gen/asis/out、denied@135、lstat、rc=0） |
| coarse_warning | 2 | 「分からない」の失敗を、警告なしに吸収して 0 で終わった（gen+hardlink/asis/out、denied@157、unlink、rc=0） |
| report_fails_unit | 2 | 確定のあとの失敗で、0 でなく終わった（absent/asis/out、denied@86、stdout_write、rc=unknown） |
| swallow_marker_failure | 1 | 確定の前の「分からない」の失敗を吸収して 0 で終わった（absent/asis/out、denied@27、close-write、rc=0） |
| fallback_rmdir | 18 | 「分からない」の失敗を、警告なしに吸収して 0 で終わった（absent/junction/out、denied@41、lstat、rc=0） |
| follow_on_open | 8 | 書き出し先と領分の外が変わった（absent/lock-dangling/out、absent@23、lstat、rc=0） |
| discard_old_first | 774 | 確定の前の「分からない」の失敗を吸収して 0 で終わった（empty+old/asis/out、denied@37、lstat、rc=0） |
| warn_on_marker_close | 17 | 確定の前の「分からない」の失敗を吸収して 0 で終わった（absent/asis/out、denied@22、lstat、rc=0） |
| enter_root_unchecked | 2336 | 書き出し先と領分の外が変わった（browse-junction/asis/default、None@None、None、rc=0） |
| raise_post_listdir | 10 | 確定のあとの失敗で、0 でなく終わった（gen/asis/out、denied@130、scandir_open、rc=unknown） |
| cache_ids_by_name | 80 | 作業用に残りがある: ['del-1']（gen+datajunction/asis/default、denied@125、lstat、rc=0） |
| warn_on_record_failure | 98 | 起動の「分からない」の失敗を吸収して、起動した（状態 absent、start、denied@39、lstat、rc=ok） |
| recover_by_published_seq | 2 | 最後に公開した世代（G1）が残っていない（既定、rc=0,crash,unknown、書き出し先の中身 ['index.html']） |
| delete_in_place | 156 | 書き出し先を消したあとの書き出しが、新しい世代に着かなかった（rc=stop）（gen/asis/out、crash@153、lstat） |
| refuse_unknown_entries | 317 | 次の起動が失敗した: 決まった名前のほかの項目がある: server.json.new（状態 absent、start、denied@41、write、rc=unknown） |
| skip_owner | 180 | 失敗のない実行で、別の Wiki のサーバーだと知らせて止まらなかった（B の serve、None@None、None、結果 reuse） |
| enter_root_unchecked（サーバー） | 490 | 失敗のない実行で、領分の名前のリンクで止まらなかった（browse-junction、serve、None@None、None、結果 started） |

## 書き出し

| 書き出し先の種類 | 書き出し先の状態 | 作業用の状態 | 口の呼び出し | 実行 | 破れた決まり |
| --- | --- | --- | --- | --- | --- |
| --out | absent | asis | 88 | 477 | 0 |
| --out | absent | leftovers | 139 | 755 | 0 |
| --out | absent | junction | 105 | 570 | 0 |
| --out | absent | unmarked-empty | 87 | 472 | 0 |
| --out | absent | lock-dangling | 89 | 483 | 0 |
| --out | absent | lock-symlink | 89 | 483 | 0 |
| --out | absent | lock-hardlink | 87 | 472 | 0 |
| --out | absent | marker-symlink | 86 | 467 | 0 |
| --out | absent | marker-owner-link | 86 | 467 | 0 |
| --out | absent | work-link | 18 | 107 | 0 |
| --out | empty | asis | 96 | 520 | 0 |
| --out | empty | leftovers | 147 | 798 | 0 |
| --out | empty | junction | 113 | 613 | 0 |
| --out | empty | unmarked-empty | 95 | 515 | 0 |
| --out | gen | asis | 190 | 2440 | 0 |
| --out | gen | leftovers | 241 | 4076 | 0 |
| --out | gen | junction | 207 | 1117 | 0 |
| --out | gen | unmarked-empty | 189 | 1019 | 0 |
| --out | gen | lock-dangling | 191 | 1030 | 0 |
| --out | gen | lock-symlink | 191 | 1030 | 0 |
| --out | gen | lock-hardlink | 189 | 1019 | 0 |
| --out | gen | marker-symlink | 188 | 1014 | 0 |
| --out | gen | marker-owner-link | 188 | 1014 | 0 |
| --out | gen | work-link | 20 | 118 | 0 |
| --out | gen+extra | asis | 87 | 466 | 0 |
| --out | gen+extra | leftovers | 138 | 744 | 0 |
| --out | gen+extra | junction | 104 | 559 | 0 |
| --out | gen+extra | unmarked-empty | 86 | 461 | 0 |
| --out | gen+edited | asis | 84 | 450 | 0 |
| --out | gen+edited | leftovers | 135 | 728 | 0 |
| --out | gen+edited | junction | 101 | 543 | 0 |
| --out | gen+edited | unmarked-empty | 83 | 445 | 0 |
| --out | userdir | asis | 47 | 259 | 0 |
| --out | userdir | leftovers | 98 | 537 | 0 |
| --out | userdir | junction | 64 | 352 | 0 |
| --out | userdir | unmarked-empty | 46 | 254 | 0 |
| --out | legacy | asis | 52 | 284 | 0 |
| --out | legacy | leftovers | 103 | 562 | 0 |
| --out | legacy | junction | 69 | 377 | 0 |
| --out | legacy | unmarked-empty | 51 | 279 | 0 |
| --out | gen+hardlink | asis | 184 | 991 | 0 |
| --out | gen+hardlink | leftovers | 235 | 1269 | 0 |
| --out | gen+hardlink | junction | 201 | 1084 | 0 |
| --out | gen+hardlink | unmarked-empty | 183 | 986 | 0 |
| --out | absent+old | asis | 195 | 2484 | 0 |
| --out | absent+old | leftovers | 248 | 4130 | 0 |
| --out | absent+old | junction | 214 | 1155 | 0 |
| --out | empty+old | asis | 203 | 1095 | 0 |
| --out | empty+old | leftovers | 256 | 1383 | 0 |
| --out | empty+old | junction | 222 | 1198 | 0 |
| --out | wikiroot | asis | 18 | 106 | 0 |
| --out | insidewiki | asis | 11 | 65 | 0 |
| --out | nodata | asis | 88 | 477 | 0 |
| --out | nodata | leftovers | 139 | 755 | 0 |
| --out | nodata | junction | 105 | 570 | 0 |
| --out | nodata | unmarked-empty | 87 | 472 | 0 |
| 既定 | absent | asis | 97 | 526 | 0 |
| 既定 | absent | leftovers | 147 | 799 | 0 |
| 既定 | absent | junction | 113 | 614 | 0 |
| 既定 | absent | unmarked-empty | 96 | 521 | 0 |
| 既定 | absent | lock-dangling | 97 | 527 | 0 |
| 既定 | absent | lock-symlink | 97 | 527 | 0 |
| 既定 | absent | lock-hardlink | 95 | 516 | 0 |
| 既定 | absent | marker-symlink | 100 | 543 | 0 |
| 既定 | absent | marker-owner-link | 100 | 543 | 0 |
| 既定 | absent | work-link | 20 | 119 | 0 |
| 既定 | empty | asis | 105 | 569 | 0 |
| 既定 | empty | leftovers | 155 | 842 | 0 |
| 既定 | empty | junction | 121 | 657 | 0 |
| 既定 | empty | unmarked-empty | 104 | 564 | 0 |
| 既定 | gen | asis | 164 | 891 | 0 |
| 既定 | gen | leftovers | 214 | 1164 | 0 |
| 既定 | gen | junction | 180 | 979 | 0 |
| 既定 | gen | unmarked-empty | 163 | 886 | 0 |
| 既定 | gen | lock-dangling | 164 | 892 | 0 |
| 既定 | gen | lock-symlink | 164 | 892 | 0 |
| 既定 | gen | lock-hardlink | 162 | 881 | 0 |
| 既定 | gen | marker-symlink | 167 | 908 | 0 |
| 既定 | gen | marker-owner-link | 167 | 908 | 0 |
| 既定 | gen | work-link | 22 | 130 | 0 |
| 既定 | gen+extra | asis | 168 | 912 | 0 |
| 既定 | gen+extra | leftovers | 218 | 1185 | 0 |
| 既定 | gen+extra | junction | 184 | 1000 | 0 |
| 既定 | gen+extra | unmarked-empty | 167 | 907 | 0 |
| 既定 | gen+edited | asis | 164 | 891 | 0 |
| 既定 | gen+edited | leftovers | 214 | 1164 | 0 |
| 既定 | gen+edited | junction | 180 | 979 | 0 |
| 既定 | gen+edited | unmarked-empty | 163 | 886 | 0 |
| 既定 | userdir | asis | 127 | 690 | 0 |
| 既定 | userdir | leftovers | 177 | 963 | 0 |
| 既定 | userdir | junction | 143 | 778 | 0 |
| 既定 | userdir | unmarked-empty | 126 | 685 | 0 |
| 既定 | legacy | asis | 131 | 711 | 0 |
| 既定 | legacy | leftovers | 181 | 984 | 0 |
| 既定 | legacy | junction | 147 | 799 | 0 |
| 既定 | legacy | unmarked-empty | 130 | 706 | 0 |
| 既定 | gen+hardlink | asis | 158 | 858 | 0 |
| 既定 | gen+hardlink | leftovers | 208 | 1131 | 0 |
| 既定 | gen+hardlink | junction | 174 | 946 | 0 |
| 既定 | gen+hardlink | unmarked-empty | 157 | 853 | 0 |
| 既定 | absent+old | asis | 168 | 914 | 0 |
| 既定 | absent+old | leftovers | 221 | 1202 | 0 |
| 既定 | absent+old | junction | 187 | 1017 | 0 |
| 既定 | empty+old | asis | 176 | 957 | 0 |
| 既定 | empty+old | leftovers | 229 | 1245 | 0 |
| 既定 | empty+old | junction | 195 | 1060 | 0 |
| 既定 | nodata | asis | 107 | 582 | 0 |
| 既定 | nodata | leftovers | 147 | 799 | 0 |
| 既定 | nodata | junction | 113 | 614 | 0 |
| 既定 | nodata | unmarked-empty | 96 | 521 | 0 |
| 既定 | datainwiki | asis | 13 | 77 | 0 |
| 既定 | browse-junction | asis | 1 | 7 | 0 |
| 既定 | browse-symlink | asis | 1 | 7 | 0 |
| 既定 | gen+datajunction | asis | 164 | 891 | 0 |
| 既定 | gen+datajunction | leftovers | 214 | 1164 | 0 |

## 気づき

- 読み取り専用のファイルは消せず、作業用に残る（属性を変えないため）: del-1
- 読み取り専用のファイルは消せず、作業用に残る（属性を変えないため）: del-7
- 読み取り専用のファイルは消せず、作業用に残る（属性を変えないため）: del-8
- 読み取り専用のファイルは消せず、作業用に残る（属性を変えないため）: del-9

7748 秒
