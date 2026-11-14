Python 3.12.13、win32、部分 build:3/4

## 書き出し

| 書き出し先の種類 | 書き出し先の状態 | 作業用の状態 | 口の呼び出し | 実行 | 破れた決まり |
| --- | --- | --- | --- | --- | --- |
| --out | absent | unmarked-empty | 285 | 1643 | 0 |
| --out | absent | marker-symlink | 295 | 1697 | 0 |
| --out | absent | old-symlink | 296 | 1703 | 0 |
| --out | empty | junction | 316 | 1813 | 0 |
| --out | gen | junction | 410 | 2317 | 0 |
| --out | gen | lock-hardlink | 392 | 2219 | 0 |
| --out | gen | old-junction | 401 | 2267 | 0 |
| --out | gen+extra | leftovers | 341 | 1944 | 0 |
| --out | gen+edited | leftovers | 338 | 1928 | 0 |
| --out | userdir | leftovers | 301 | 1737 | 0 |
| --out | legacy | leftovers | 306 | 1762 | 0 |
| --out | gen+hardlink | leftovers | 438 | 2469 | 0 |
| --out | absent+old | leftovers | 448 | 5825 | 0 |
| --out | empty+old | junction | 426 | 2404 | 0 |
| --out | nodata | leftovers | 345 | 1970 | 0 |
| --out | outlink-symlink | asis | 17 | 101 | 0 |
| --out | outisbrowse | asis | 98 | 582 | 0 |
| 既定 | absent | leftovers | 320 | 1826 | 0 |
| 既定 | absent | lock-symlink | 270 | 1554 | 0 |
| 既定 | absent | work-link | 193 | 1146 | 0 |
| 既定 | empty | asis | 274 | 1575 | 0 |
| 既定 | gen | asis | 333 | 1897 | 0 |
| 既定 | gen | lock-dangling | 341 | 1942 | 0 |
| 既定 | gen | marker-owner-link | 344 | 1958 | 0 |
| 既定 | gen | left-links | 346 | 1968 | 0 |
| 既定 | gen+extra | unmarked-empty | 338 | 1925 | 0 |
| 既定 | gen+edited | unmarked-empty | 334 | 1904 | 0 |
| 既定 | userdir | unmarked-empty | 297 | 1703 | 0 |
| 既定 | legacy | unmarked-empty | 301 | 1724 | 0 |
| 既定 | gen+hardlink | unmarked-empty | 328 | 1871 | 0 |
| 既定 | empty+old | asis | 354 | 2013 | 0 |
| 既定 | nodata | leftovers | 320 | 1826 | 0 |
| 既定 | outlink-symlink | asis | 42 | 250 | 0 |
| 既定 | gen+datajunction | asis | 333 | 1897 | 0 |

## 気づき

- 読み取り専用のファイルは消せず、作業用に残る（属性を変えないため）: del-1
- 読み取り専用のファイルは消せず、作業用に残る（属性を変えないため）: del-7
- 読み取り専用のファイルは消せず、作業用に残る（属性を変えないため）: del-8

7990 秒
exit 0
