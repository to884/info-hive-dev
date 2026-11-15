Python 3.12.13、win32、部分 build:1/4

## 書き出し

| 書き出し先の種類 | 書き出し先の状態 | 作業用の状態 | 口の呼び出し | 実行 | 破れた決まり |
| --- | --- | --- | --- | --- | --- |
| --out | absent | leftovers | 432 | 2490 | 0 |
| --out | absent | lock-symlink | 382 | 2218 | 0 |
| --out | absent | work-link | 307 | 1818 | 0 |
| --out | empty | asis | 392 | 2271 | 0 |
| --out | gen | asis | 486 | 4671 | 0 |
| --out | gen | lock-dangling | 491 | 2805 | 0 |
| --out | gen | marker-owner-link | 498 | 2842 | 0 |
| --out | gen | left-links | 496 | 2831 | 0 |
| --out | gen+extra | unmarked-empty | 385 | 2230 | 0 |
| --out | gen+edited | unmarked-empty | 382 | 2214 | 0 |
| --out | userdir | unmarked-empty | 345 | 2023 | 0 |
| --out | legacy | unmarked-empty | 350 | 2048 | 0 |
| --out | gen+hardlink | unmarked-empty | 482 | 2755 | 0 |
| --out | empty+old | asis | 504 | 2876 | 0 |
| --out | insidewiki | asis | 11 | 65 | 0 |
| --out | nodata | unmarked-empty | 386 | 2239 | 0 |
| --out | insidewiki-nodata | asis | 11 | 65 | 0 |
| --out | browse-symlink | asis | 109 | 647 | 0 |
| 既定 | absent | unmarked-empty | 263 | 1516 | 0 |
| 既定 | absent | marker-symlink | 273 | 1570 | 0 |
| 既定 | absent | old-symlink | 278 | 1597 | 0 |
| 既定 | empty | junction | 298 | 1707 | 0 |
| 既定 | gen | junction | 357 | 2029 | 0 |
| 既定 | gen | lock-hardlink | 339 | 1931 | 0 |
| 既定 | gen | old-junction | 348 | 1979 | 0 |
| 既定 | gen+extra | leftovers | 395 | 2235 | 0 |
| 既定 | gen+edited | leftovers | 391 | 2214 | 0 |
| 既定 | userdir | leftovers | 354 | 2013 | 0 |
| 既定 | legacy | leftovers | 358 | 2034 | 0 |
| 既定 | gen+hardlink | leftovers | 385 | 2181 | 0 |
| 既定 | absent+old | leftovers | 395 | 2235 | 0 |
| 既定 | empty+old | junction | 373 | 2116 | 0 |
| 既定 | nodata | unmarked-empty | 263 | 1516 | 0 |
| 既定 | browse-junction | asis | 24 | 144 | 0 |

## 気づき

- 読み取り専用のファイルは消せず、作業用に残る（属性を変えないため）: del-1
- 読み取り専用のファイルは消せず、作業用に残る（属性を変えないため）: del-7
- 読み取り専用のファイルは消せず、作業用に残る（属性を変えないため）: del-8

8777 秒
exit 0
