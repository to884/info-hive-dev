Python 3.12.13、win32、部分 build:1/4

## 書き出し

| 書き出し先の種類 | 書き出し先の状態 | 作業用の状態 | 口の呼び出し | 実行 | 破れた決まり |
| --- | --- | --- | --- | --- | --- |
| --out | absent | leftovers | 338 | 1932 | 0 |
| --out | absent | lock-symlink | 288 | 1660 | 0 |
| --out | absent | work-link | 214 | 1266 | 0 |
| --out | empty | asis | 296 | 1702 | 0 |
| --out | gen | asis | 390 | 4102 | 0 |
| --out | gen | lock-dangling | 394 | 2230 | 0 |
| --out | gen | marker-owner-link | 401 | 2267 | 0 |
| --out | gen | left-links | 399 | 2256 | 0 |
| --out | gen+extra | unmarked-empty | 288 | 1655 | 0 |
| --out | gen+edited | unmarked-empty | 285 | 1639 | 0 |
| --out | userdir | unmarked-empty | 248 | 1448 | 0 |
| --out | legacy | unmarked-empty | 253 | 1473 | 0 |
| --out | gen+hardlink | unmarked-empty | 385 | 2180 | 0 |
| --out | empty+old | asis | 407 | 2301 | 0 |
| --out | insidewiki | asis | 11 | 65 | 0 |
| --out | nodata | unmarked-empty | 292 | 1681 | 0 |
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

7579 秒
exit 0
