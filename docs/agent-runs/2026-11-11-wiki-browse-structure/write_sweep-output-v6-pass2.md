# 6 版目の試作の探索（2 回目。ジャンクションと警告の基準を直したあと、6.1 の確かめを直す前）

Wiki のルートと重なる `--out` の 2 つの状態で、世界の差分の基準が 2 件ずつ破れた。

Python 3.14.6、win32

## サーバーの記録

実行 1762 回、破れた決まり 0 件

## 同じ場所を使う別の Wiki

実行 443 回、破れた決まり 0 件

## 強制停止のあとで、利用者が書き出し先を消す

実行 1330 回、破れた決まり 0 件

## 番号の巻き戻りと復旧（3 回の実行に 1 つずつの失敗）

破れた決まり 0 件

## 対照

| 対照 | 見つけた件数 | 最初の 1 件 |
| --- | --- | --- |
| skip_gate | 2793 | browse のものでない書き出し先か、Wiki のルートが変わった（gen+extra/asis/out、None@None、None、rc=0） |
| follow_links | 872 | 書き出し先と領分の外が変わった（gen/junction/out、None@None、None、rc=stop） |
| commit_then_fail | 102 | 0 でないのに、書き出し先が前のままでも、戻せる形でもない（gen/asis/out、denied@127、lstat、rc=unknown） |
| chmod_on_delete | 1216 | 書き出し先と領分の外が変わった（gen+hardlink/asis/out、None@None、None、rc=0） |
| no_root_guard | 3137 | 書き出し先と領分の外が変わった（wikiroot/asis/out、None@None、None、rc=0） |
| default_verifies | 752 | 既定の書き出し先の前の世代を読んだ（gen/asis/default、None@None、None、rc=0） |
| swallow_close | 24 | 「分からない」の失敗を、警告なしに吸収して 0 で終わった（absent/asis/out、denied@25、close-write、rc=0） |
| silent_post_commit | 123 | 「分からない」の失敗を、警告なしに吸収して 0 で終わった（gen/asis/out、denied@127、lstat、rc=0） |
| coarse_warning | 2 | 「分からない」の失敗を、警告なしに吸収して 0 で終わった（gen+hardlink/asis/out、denied@148、unlink、rc=0） |
| report_fails_unit | 2 | 0 でないのに、書き出し先が前のままでも、戻せる形でもない（absent/asis/out、denied@79、stdout_write、rc=unknown） |
| swallow_marker_failure | 1 | 「分からない」の失敗を、警告なしに吸収して 0 で終わった（absent/asis/out、denied@25、close-write、rc=0） |
| fallback_rmdir | 14 | 「分からない」の失敗を、警告なしに吸収して 0 で終わった（absent/junction/out、denied@38、lstat、rc=0） |
| recover_by_published_seq | 2 | 最後に公開した世代（G1）が残っていない（既定、rc=0,crash,unknown、書き出し先の中身 ['index.html']） |
| delete_in_place | 126 | 書き出し先を消したあとの書き出しが、新しい世代に着かなかった（rc=stop）（gen/asis/out、crash@144、lstat） |
| refuse_unknown_entries | 179 | 次の起動が失敗した: 決まった名前のほかの項目がある: server.json.new（状態 absent、start、denied@36、write、rc=unknown） |
| skip_owner | 168 | 失敗のない実行で、別の Wiki のサーバーだと知らせて止まらなかった（B の serve、None@None、None、結果 reuse） |

## 書き出し

| 書き出し先の種類 | 書き出し先の状態 | 作業用の状態 | 口の呼び出し | 実行 | 破れた決まり |
| --- | --- | --- | --- | --- | --- |
| --out | absent | asis | 81 | 435 | 0 |
| --out | absent | leftovers | 125 | 671 | 0 |
| --out | absent | junction | 96 | 516 | 0 |
| --out | absent | unmarked-empty | 80 | 430 | 0 |
| --out | empty | asis | 88 | 472 | 0 |
| --out | empty | leftovers | 132 | 708 | 0 |
| --out | empty | junction | 103 | 553 | 0 |
| --out | empty | unmarked-empty | 87 | 467 | 0 |
| --out | gen | asis | 175 | 2187 | 0 |
| --out | gen | leftovers | 219 | 3571 | 0 |
| --out | gen | junction | 190 | 1015 | 0 |
| --out | gen | unmarked-empty | 174 | 929 | 0 |
| --out | gen+extra | asis | 84 | 448 | 0 |
| --out | gen+extra | leftovers | 128 | 684 | 0 |
| --out | gen+extra | junction | 99 | 529 | 0 |
| --out | gen+extra | unmarked-empty | 83 | 443 | 0 |
| --out | gen+edited | asis | 81 | 432 | 0 |
| --out | gen+edited | leftovers | 125 | 668 | 0 |
| --out | gen+edited | junction | 96 | 513 | 0 |
| --out | gen+edited | unmarked-empty | 80 | 427 | 0 |
| --out | userdir | asis | 44 | 241 | 0 |
| --out | userdir | leftovers | 88 | 477 | 0 |
| --out | userdir | junction | 59 | 322 | 0 |
| --out | userdir | unmarked-empty | 43 | 236 | 0 |
| --out | legacy | asis | 49 | 266 | 0 |
| --out | legacy | leftovers | 93 | 502 | 0 |
| --out | legacy | junction | 64 | 347 | 0 |
| --out | legacy | unmarked-empty | 48 | 261 | 0 |
| --out | gen+hardlink | asis | 170 | 907 | 0 |
| --out | gen+hardlink | leftovers | 214 | 1143 | 0 |
| --out | gen+hardlink | junction | 185 | 988 | 0 |
| --out | gen+hardlink | unmarked-empty | 169 | 902 | 0 |
| --out | absent+old | asis | 181 | 2267 | 0 |
| --out | absent+old | leftovers | 227 | 3661 | 0 |
| --out | absent+old | junction | 198 | 1059 | 0 |
| --out | empty+old | asis | 187 | 999 | 0 |
| --out | empty+old | leftovers | 233 | 1245 | 0 |
| --out | empty+old | junction | 204 | 1090 | 0 |
| --out | wikiroot | asis | 16 | 94 | 2 |
| --out | insidewiki | asis | 14 | 83 | 2 |
| --out | nodata | asis | 81 | 435 | 0 |
| --out | nodata | leftovers | 125 | 671 | 0 |
| --out | nodata | junction | 96 | 516 | 0 |
| --out | nodata | unmarked-empty | 80 | 430 | 0 |
| 既定 | absent | asis | 89 | 478 | 0 |
| 既定 | absent | leftovers | 132 | 709 | 0 |
| 既定 | absent | junction | 103 | 554 | 0 |
| 既定 | absent | unmarked-empty | 88 | 473 | 0 |
| 既定 | empty | asis | 96 | 515 | 0 |
| 既定 | empty | leftovers | 139 | 746 | 0 |
| 既定 | empty | junction | 110 | 591 | 0 |
| 既定 | empty | unmarked-empty | 95 | 510 | 0 |
| 既定 | gen | asis | 148 | 795 | 0 |
| 既定 | gen | leftovers | 191 | 1026 | 0 |
| 既定 | gen | junction | 162 | 871 | 0 |
| 既定 | gen | unmarked-empty | 147 | 790 | 0 |
| 既定 | gen+extra | asis | 152 | 816 | 0 |
| 既定 | gen+extra | leftovers | 195 | 1047 | 0 |
| 既定 | gen+extra | junction | 166 | 892 | 0 |
| 既定 | gen+extra | unmarked-empty | 151 | 811 | 0 |
| 既定 | gen+edited | asis | 148 | 795 | 0 |
| 既定 | gen+edited | leftovers | 191 | 1026 | 0 |
| 既定 | gen+edited | junction | 162 | 871 | 0 |
| 既定 | gen+edited | unmarked-empty | 147 | 790 | 0 |
| 既定 | userdir | asis | 116 | 624 | 0 |
| 既定 | userdir | leftovers | 159 | 855 | 0 |
| 既定 | userdir | junction | 130 | 700 | 0 |
| 既定 | userdir | unmarked-empty | 115 | 619 | 0 |
| 既定 | legacy | asis | 120 | 645 | 0 |
| 既定 | legacy | leftovers | 163 | 876 | 0 |
| 既定 | legacy | junction | 134 | 721 | 0 |
| 既定 | legacy | unmarked-empty | 119 | 640 | 0 |
| 既定 | gen+hardlink | asis | 143 | 768 | 0 |
| 既定 | gen+hardlink | leftovers | 186 | 999 | 0 |
| 既定 | gen+hardlink | junction | 157 | 844 | 0 |
| 既定 | gen+hardlink | unmarked-empty | 142 | 763 | 0 |
| 既定 | absent+old | asis | 153 | 824 | 0 |
| 既定 | absent+old | leftovers | 199 | 1070 | 0 |
| 既定 | absent+old | junction | 170 | 915 | 0 |
| 既定 | empty+old | asis | 159 | 855 | 0 |
| 既定 | empty+old | leftovers | 205 | 1101 | 0 |
| 既定 | empty+old | junction | 176 | 946 | 0 |
| 既定 | nodata | asis | 97 | 522 | 0 |
| 既定 | nodata | leftovers | 132 | 709 | 0 |
| 既定 | nodata | junction | 103 | 554 | 0 |
| 既定 | nodata | unmarked-empty | 88 | 473 | 0 |
| 既定 | datainwiki | asis | 16 | 95 | 0 |

## 気づき

- 読み取り専用のファイルは消せず、作業用に残る（属性を変えないため）: del-1
- 読み取り専用のファイルは消せず、作業用に残る（属性を変えないため）: del-7
- 読み取り専用のファイルは消せず、作業用に残る（属性を変えないため）: del-8
- 読み取り専用のファイルは消せず、作業用に残る（属性を変えないため）: del-9

## 破れた決まり（4 件。先頭 40 件）

- 書き出し先と領分の外が変わった（wikiroot/asis/out、absent@15、lstat、rc=stop）
- 次の実行で、書き出し先と領分の外が変わった（wikiroot/asis/out、absent@15、lstat、rc=stop）
- 書き出し先と領分の外が変わった（insidewiki/asis/out、absent@13、lstat、rc=stop）
- 次の実行で、書き出し先と領分の外が変わった（insidewiki/asis/out、absent@13、lstat、rc=stop）

5244 秒
