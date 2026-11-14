Python 3.12.13、win32、部分 build:0/4

## 書き出し

| 書き出し先の種類 | 書き出し先の状態 | 作業用の状態 | 口の呼び出し | 実行 | 破れた決まり |
| --- | --- | --- | --- | --- | --- |
| --out | absent | asis | 377 | 2188 | 0 |
| --out | absent | lock-dangling | 382 | 2218 | 0 |
| --out | absent | marker-owner-link | 389 | 2255 | 0 |
| --out | absent | left-links | 387 | 2244 | 0 |
| --out | empty | unmarked-empty | 394 | 2284 | 0 |
| --out | gen | unmarked-empty | 488 | 2788 | 0 |
| --out | gen | marker-symlink | 498 | 2842 | 0 |
| --out | gen | old-symlink | 498 | 2842 | 0 |
| --out | gen+extra | junction | 404 | 2334 | 0 |
| --out | gen+edited | junction | 401 | 2318 | 0 |
| --out | userdir | junction | 364 | 2127 | 0 |
| --out | legacy | junction | 369 | 2152 | 0 |
| --out | gen+hardlink | junction | 501 | 2859 | 0 |
| --out | absent+old | junction | 508 | 2896 | 0 |
| --out | wikiroot | asis | 18 | 106 | 0 |
| --out | nodata | junction | 405 | 2343 | 0 |
| --out | datainout | asis | 95 | 563 | 0 |
| --out | browse-junction | asis | 109 | 647 | 0 |
| 既定 | absent | junction | 286 | 1641 | 0 |
| 既定 | absent | lock-hardlink | 268 | 1543 | 0 |
| 既定 | absent | old-junction | 278 | 1597 | 0 |
| 既定 | empty | leftovers | 332 | 1892 | 0 |
| 既定 | gen | leftovers | 391 | 2214 | 0 |
| 既定 | gen | lock-symlink | 341 | 1942 | 0 |
| 既定 | gen | work-link | 199 | 1180 | 0 |
| 既定 | gen+extra | asis | 337 | 1918 | 0 |
| 既定 | gen+edited | asis | 333 | 1897 | 0 |
| 既定 | userdir | asis | 296 | 1696 | 0 |
| 既定 | legacy | asis | 300 | 1717 | 0 |
| 既定 | gen+hardlink | asis | 327 | 1864 | 0 |
| 既定 | absent+old | asis | 342 | 1947 | 0 |
| 既定 | empty+old | leftovers | 407 | 2301 | 0 |
| 既定 | nodata | junction | 286 | 1641 | 0 |
| 既定 | datainwiki | asis | 36 | 214 | 0 |
| 既定 | gen+datajunction | leftovers | 391 | 2214 | 0 |

## 気づき

- 読み取り専用のファイルは消せず、作業用に残る（属性を変えないため）: del-1
- 読み取り専用のファイルは消せず、作業用に残る（属性を変えないため）: del-9

8522 秒
exit 0
