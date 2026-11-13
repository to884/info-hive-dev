# 7 版目の試作の探索（全量）

ファイルを作る口をリンクをたどらない形にし、ロックの名前のリンクを外してから作り、確定の前の失敗と最後に公開した世代の基準を足したあとの、全部の状態の探索である。破れた決まりは 0 件、飛ばした状態は 0 件だった。

Python 3.14.6、win32

## サーバーの記録

実行 3417 回、破れた決まり 0 件

## 同じ場所を使う別の Wiki

実行 464 回、破れた決まり 0 件

## 強制停止のあとで、利用者が書き出し先を消す

実行 1336 回、破れた決まり 0 件

## 番号の巻き戻りと復旧（3 回の実行に 1 つずつの失敗）

破れた決まり 0 件

## 対照

| 対照 | 見つけた件数 | 最初の 1 件 |
| --- | --- | --- |
| skip_gate | 2793 | browse のものでない書き出し先か、Wiki のルートが変わった（gen+extra/asis/out、None@None、None、rc=0） |
| follow_links | 887 | 書き出し先と領分の外が変わった（gen/junction/out、None@None、None、rc=stop） |
| commit_then_fail | 94 | 0 でないのに、最後に公開した世代が、書き出し先にも作業用の退避にも残っていない（gen/asis/out、denied@133、lstat、rc=unknown） |
| chmod_on_delete | 1216 | 書き出し先と領分の外が変わった（gen+hardlink/asis/out、None@None、None、rc=0） |
| no_root_guard | 3021 | 書き出し先と領分の外が変わった（wikiroot/asis/out、None@None、None、rc=0） |
| climb_on_absent | 2 | 書き出し先と領分の外が変わった（insidewiki/asis/out、absent@13、lstat、rc=stop） |
| default_verifies | 752 | 既定の書き出し先の前の世代を読んだ（gen/asis/default、None@None、None、rc=0） |
| swallow_close | 24 | 確定の前の「分からない」の失敗を吸収して 0 で終わった（absent/asis/out、denied@25、close-write、rc=0） |
| silent_post_commit | 123 | 「分からない」の失敗を、警告なしに吸収して 0 で終わった（gen/asis/out、denied@128、lstat、rc=0） |
| coarse_warning | 2 | 「分からない」の失敗を、警告なしに吸収して 0 で終わった（gen+hardlink/asis/out、denied@149、unlink、rc=0） |
| report_fails_unit | 2 | 0 でないのに、最後に公開した世代が、書き出し先にも作業用の退避にも残っていない（absent/asis/out、denied@80、stdout_write、rc=unknown） |
| swallow_marker_failure | 1 | 確定の前の「分からない」の失敗を吸収して 0 で終わった（absent/asis/out、denied@25、close-write、rc=0） |
| fallback_rmdir | 14 | 「分からない」の失敗を、警告なしに吸収して 0 で終わった（absent/junction/out、denied@39、lstat、rc=0） |
| follow_on_open | 8 | 書き出し先と領分の外が変わった（absent/lock-dangling/out、absent@22、lstat、rc=0） |
| discard_old_first | 673 | 確定の前の「分からない」の失敗を吸収して 0 で終わった（empty+old/asis/out、denied@35、lstat、rc=0） |
| warn_on_marker_close | 13 | 確定の前の「分からない」の失敗を吸収して 0 で終わった（absent/asis/out、denied@21、lstat、rc=0） |
| warn_on_record_failure | 90 | 起動の「分からない」の失敗を吸収して、起動した（状態 absent、start、denied@36、lstat、rc=ok） |
| recover_by_published_seq | 2 | 最後に公開した世代（G1）が残っていない（既定、rc=0,crash,unknown、書き出し先の中身 ['index.html']） |
| delete_in_place | 126 | 書き出し先を消したあとの書き出しが、新しい世代に着かなかった（rc=stop）（gen/asis/out、crash@145、lstat） |
| refuse_unknown_entries | 285 | 次の起動が失敗した: 決まった名前のほかの項目がある: server.json.new（状態 absent、start、denied@38、write、rc=unknown） |
| skip_owner | 174 | 失敗のない実行で、別の Wiki のサーバーだと知らせて止まらなかった（B の serve、None@None、None、結果 reuse） |

## 書き出し

| 書き出し先の種類 | 書き出し先の状態 | 作業用の状態 | 口の呼び出し | 実行 | 破れた決まり |
| --- | --- | --- | --- | --- | --- |
| --out | absent | asis | 82 | 441 | 0 |
| --out | absent | leftovers | 126 | 677 | 0 |
| --out | absent | junction | 97 | 522 | 0 |
| --out | absent | unmarked-empty | 81 | 436 | 0 |
| --out | absent | lock-dangling | 83 | 447 | 0 |
| --out | absent | lock-symlink | 83 | 447 | 0 |
| --out | absent | lock-hardlink | 81 | 436 | 0 |
| --out | absent | marker-symlink | 80 | 431 | 0 |
| --out | empty | asis | 89 | 478 | 0 |
| --out | empty | leftovers | 133 | 714 | 0 |
| --out | empty | junction | 104 | 559 | 0 |
| --out | empty | unmarked-empty | 88 | 473 | 0 |
| --out | gen | asis | 176 | 2193 | 0 |
| --out | gen | leftovers | 220 | 3577 | 0 |
| --out | gen | junction | 191 | 1021 | 0 |
| --out | gen | unmarked-empty | 175 | 935 | 0 |
| --out | gen | lock-dangling | 177 | 946 | 0 |
| --out | gen | lock-symlink | 177 | 946 | 0 |
| --out | gen | lock-hardlink | 175 | 935 | 0 |
| --out | gen | marker-symlink | 174 | 930 | 0 |
| --out | gen+extra | asis | 85 | 454 | 0 |
| --out | gen+extra | leftovers | 129 | 690 | 0 |
| --out | gen+extra | junction | 100 | 535 | 0 |
| --out | gen+extra | unmarked-empty | 84 | 449 | 0 |
| --out | gen+edited | asis | 82 | 438 | 0 |
| --out | gen+edited | leftovers | 126 | 674 | 0 |
| --out | gen+edited | junction | 97 | 519 | 0 |
| --out | gen+edited | unmarked-empty | 81 | 433 | 0 |
| --out | userdir | asis | 45 | 247 | 0 |
| --out | userdir | leftovers | 89 | 483 | 0 |
| --out | userdir | junction | 60 | 328 | 0 |
| --out | userdir | unmarked-empty | 44 | 242 | 0 |
| --out | legacy | asis | 50 | 272 | 0 |
| --out | legacy | leftovers | 94 | 508 | 0 |
| --out | legacy | junction | 65 | 353 | 0 |
| --out | legacy | unmarked-empty | 49 | 267 | 0 |
| --out | gen+hardlink | asis | 171 | 913 | 0 |
| --out | gen+hardlink | leftovers | 215 | 1149 | 0 |
| --out | gen+hardlink | junction | 186 | 994 | 0 |
| --out | gen+hardlink | unmarked-empty | 170 | 908 | 0 |
| --out | absent+old | asis | 182 | 2273 | 0 |
| --out | absent+old | leftovers | 228 | 3667 | 0 |
| --out | absent+old | junction | 199 | 1065 | 0 |
| --out | empty+old | asis | 188 | 1005 | 0 |
| --out | empty+old | leftovers | 234 | 1251 | 0 |
| --out | empty+old | junction | 205 | 1096 | 0 |
| --out | wikiroot | asis | 16 | 94 | 0 |
| --out | insidewiki | asis | 14 | 83 | 0 |
| --out | nodata | asis | 82 | 441 | 0 |
| --out | nodata | leftovers | 126 | 677 | 0 |
| --out | nodata | junction | 97 | 522 | 0 |
| --out | nodata | unmarked-empty | 81 | 436 | 0 |
| 既定 | absent | asis | 90 | 484 | 0 |
| 既定 | absent | leftovers | 133 | 715 | 0 |
| 既定 | absent | junction | 104 | 560 | 0 |
| 既定 | absent | unmarked-empty | 89 | 479 | 0 |
| 既定 | absent | lock-dangling | 90 | 485 | 0 |
| 既定 | absent | lock-symlink | 90 | 485 | 0 |
| 既定 | absent | lock-hardlink | 88 | 474 | 0 |
| 既定 | absent | marker-symlink | 94 | 507 | 0 |
| 既定 | empty | asis | 97 | 521 | 0 |
| 既定 | empty | leftovers | 140 | 752 | 0 |
| 既定 | empty | junction | 111 | 597 | 0 |
| 既定 | empty | unmarked-empty | 96 | 516 | 0 |
| 既定 | gen | asis | 149 | 801 | 0 |
| 既定 | gen | leftovers | 192 | 1032 | 0 |
| 既定 | gen | junction | 163 | 877 | 0 |
| 既定 | gen | unmarked-empty | 148 | 796 | 0 |
| 既定 | gen | lock-dangling | 149 | 802 | 0 |
| 既定 | gen | lock-symlink | 149 | 802 | 0 |
| 既定 | gen | lock-hardlink | 147 | 791 | 0 |
| 既定 | gen | marker-symlink | 153 | 824 | 0 |
| 既定 | gen+extra | asis | 153 | 822 | 0 |
| 既定 | gen+extra | leftovers | 196 | 1053 | 0 |
| 既定 | gen+extra | junction | 167 | 898 | 0 |
| 既定 | gen+extra | unmarked-empty | 152 | 817 | 0 |
| 既定 | gen+edited | asis | 149 | 801 | 0 |
| 既定 | gen+edited | leftovers | 192 | 1032 | 0 |
| 既定 | gen+edited | junction | 163 | 877 | 0 |
| 既定 | gen+edited | unmarked-empty | 148 | 796 | 0 |
| 既定 | userdir | asis | 117 | 630 | 0 |
| 既定 | userdir | leftovers | 160 | 861 | 0 |
| 既定 | userdir | junction | 131 | 706 | 0 |
| 既定 | userdir | unmarked-empty | 116 | 625 | 0 |
| 既定 | legacy | asis | 121 | 651 | 0 |
| 既定 | legacy | leftovers | 164 | 882 | 0 |
| 既定 | legacy | junction | 135 | 727 | 0 |
| 既定 | legacy | unmarked-empty | 120 | 646 | 0 |
| 既定 | gen+hardlink | asis | 144 | 774 | 0 |
| 既定 | gen+hardlink | leftovers | 187 | 1005 | 0 |
| 既定 | gen+hardlink | junction | 158 | 850 | 0 |
| 既定 | gen+hardlink | unmarked-empty | 143 | 769 | 0 |
| 既定 | absent+old | asis | 154 | 830 | 0 |
| 既定 | absent+old | leftovers | 200 | 1076 | 0 |
| 既定 | absent+old | junction | 171 | 921 | 0 |
| 既定 | empty+old | asis | 160 | 861 | 0 |
| 既定 | empty+old | leftovers | 206 | 1107 | 0 |
| 既定 | empty+old | junction | 177 | 952 | 0 |
| 既定 | nodata | asis | 98 | 528 | 0 |
| 既定 | nodata | leftovers | 133 | 715 | 0 |
| 既定 | nodata | junction | 104 | 560 | 0 |
| 既定 | nodata | unmarked-empty | 89 | 479 | 0 |
| 既定 | datainwiki | asis | 16 | 95 | 0 |

## 気づき

- 読み取り専用のファイルは消せず、作業用に残る（属性を変えないため）: del-1
- 読み取り専用のファイルは消せず、作業用に残る（属性を変えないため）: del-7
- 読み取り専用のファイルは消せず、作業用に残る（属性を変えないため）: del-8
- 読み取り専用のファイルは消せず、作業用に残る（属性を変えないため）: del-9

6308 秒
