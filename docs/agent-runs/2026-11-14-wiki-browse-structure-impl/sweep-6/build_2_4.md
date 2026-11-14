Python 3.12.13、win32、部分 build:2/4

## 書き出し

| 書き出し先の種類 | 書き出し先の状態 | 作業用の状態 | 口の呼び出し | 実行 | 破れた決まり |
| --- | --- | --- | --- | --- | --- |
| --out | absent | junction | 304 | 1747 | 0 |
| --out | absent | lock-hardlink | 286 | 1649 | 0 |
| --out | absent | old-junction | 296 | 1703 | 0 |
| --out | empty | leftovers | 350 | 1998 | 0 |
| --out | gen | leftovers | 444 | 5772 | 0 |
| --out | gen | lock-symlink | 394 | 2230 | 0 |
| --out | gen | work-link | 220 | 1300 | 0 |
| --out | gen+extra | asis | 287 | 1648 | 0 |
| --out | gen+edited | asis | 284 | 1632 | 0 |
| --out | userdir | asis | 247 | 1441 | 0 |
| --out | legacy | asis | 252 | 1466 | 0 |
| --out | gen+hardlink | asis | 384 | 2173 | 0 |
| --out | absent+old | asis | 395 | 4163 | 0 |
| --out | empty+old | leftovers | 460 | 2589 | 0 |
| --out | nodata | asis | 291 | 1674 | 0 |
| --out | outlink-junction | asis | 17 | 101 | 0 |
| --out | outisdata | asis | 88 | 522 | 0 |
| 既定 | absent | asis | 262 | 1509 | 0 |
| 既定 | absent | lock-dangling | 270 | 1554 | 0 |
| 既定 | absent | marker-owner-link | 273 | 1570 | 0 |
| 既定 | absent | left-links | 275 | 1580 | 0 |
| 既定 | empty | unmarked-empty | 275 | 1582 | 0 |
| 既定 | gen | unmarked-empty | 334 | 1904 | 0 |
| 既定 | gen | marker-symlink | 344 | 1958 | 0 |
| 既定 | gen | old-symlink | 348 | 1979 | 0 |
| 既定 | gen+extra | junction | 361 | 2050 | 0 |
| 既定 | gen+edited | junction | 357 | 2029 | 0 |
| 既定 | userdir | junction | 320 | 1828 | 0 |
| 既定 | legacy | junction | 324 | 1849 | 0 |
| 既定 | gen+hardlink | junction | 351 | 1996 | 0 |
| 既定 | absent+old | junction | 361 | 2050 | 0 |
| 既定 | nodata | asis | 268 | 1541 | 0 |
| 既定 | outlink-junction | asis | 42 | 250 | 0 |
| 既定 | browse-symlink | asis | 24 | 144 | 0 |

## 気づき

- 読み取り専用のファイルは消せず、作業用に残る（属性を変えないため）: del-1
- 読み取り専用のファイルは消せず、作業用に残る（属性を変えないため）: del-9

7678 秒
exit 0
