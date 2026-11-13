# 探索の状態になかったリンクの位置（8 版目の試作）

[link_positions_probe.py](link_positions_probe.py) の出力である。探索（`write_sweep.py`）の状態になかったリンクの位置で、手を入れない実行を 2 回続けて流し、リンクの先の木と砂場の全体の木を、前と後で比べた。経緯は [results.md](results.md) の 8.3 にある。直したあとは、`--out` の親がリンクの位置と、既定の書き出し先の中のジャンクションも足して流した（末尾の 4 つ）。

直す前は、`--out` の書き出し先がなく、作業用の `old-5` の名前そのものがリンクのとき、復旧がそのリンクを書き出し先の名前に付け替え、門で止まった（書き出し先の名前の種類が `link` になる）。既定の書き出し先の名前がリンクのときは、止まらずに置き換えた。どちらも、リンクの先は変わらなかった。

## 直す前（8 版目の初めの試作）

Python 3.14.6、win32

#### 既定の書き出し先の名前が junction

- 終わり方: 0、次の実行: 0
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: dir、新しい世代か: True
- 砂場で変わった名前: ['data/browse', 'data/browse/KEY', 'data/browse/KEY.browse-work', 'data/browse/KEY.browse-work/.browse-work', 'data/browse/KEY.browse-work/build.lock', 'data/browse/KEY/.browse-generation', 'data/browse/KEY/assets', 'data/browse/KEY/assets/app.js', 'data/browse/KEY/concepts', 'data/browse/KEY/concepts/a.html', 'data/browse/KEY/concepts/b.html', 'data/browse/KEY/index.html']

#### 既定の書き出し先の名前が symlink

- 終わり方: 0、次の実行: 0
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: dir、新しい世代か: True
- 砂場で変わった名前: ['data/browse', 'data/browse/KEY', 'data/browse/KEY.browse-work', 'data/browse/KEY.browse-work/.browse-work', 'data/browse/KEY.browse-work/build.lock', 'data/browse/KEY/.browse-generation', 'data/browse/KEY/assets', 'data/browse/KEY/assets/app.js', 'data/browse/KEY/concepts', 'data/browse/KEY/concepts/a.html', 'data/browse/KEY/concepts/b.html', 'data/browse/KEY/index.html']

#### --out の名前が junction（先に userfiles）

- 終わり方: stop、次の実行: stop
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: link、新しい世代か: False
- 砂場で変わった名前: ['exports', 'exports/site.browse-work', 'exports/site.browse-work/.browse-work', 'exports/site.browse-work/build.lock']

#### --out の名前が junction（先に generation）

- 終わり方: stop、次の実行: stop
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: link、新しい世代か: False
- 砂場で変わった名前: ['exports', 'exports/site.browse-work', 'exports/site.browse-work/.browse-work', 'exports/site.browse-work/build.lock']

#### --out の名前が symlink（先に userfiles）

- 終わり方: stop、次の実行: stop
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: link、新しい世代か: False
- 砂場で変わった名前: ['exports', 'exports/site.browse-work', 'exports/site.browse-work/.browse-work', 'exports/site.browse-work/build.lock']

#### --out の名前が symlink（先に generation）

- 終わり方: stop、次の実行: stop
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: link、新しい世代か: False
- 砂場で変わった名前: ['exports', 'exports/site.browse-work', 'exports/site.browse-work/.browse-work', 'exports/site.browse-work/build.lock']

#### --out、書き出し先がなく、old-5 が junction（先に userfiles）

- 終わり方: stop、次の実行: stop
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: link、新しい世代か: False
- 砂場で変わった名前: ['exports', 'exports/site', 'exports/site.browse-work', 'exports/site.browse-work/build.lock', 'exports/site.browse-work/old-5']

#### --out、書き出し先がなく、old-5 が junction（先に generation）

- 終わり方: stop、次の実行: stop
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: link、新しい世代か: False
- 砂場で変わった名前: ['exports', 'exports/site', 'exports/site.browse-work', 'exports/site.browse-work/build.lock', 'exports/site.browse-work/old-5']

#### --out、書き出し先がなく、old-5 が symlink（先に userfiles）

- 終わり方: stop、次の実行: stop
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: link、新しい世代か: False
- 砂場で変わった名前: ['exports', 'exports/site', 'exports/site.browse-work', 'exports/site.browse-work/build.lock', 'exports/site.browse-work/old-5']

#### --out、書き出し先がなく、old-5 が symlink（先に generation）

- 終わり方: stop、次の実行: stop
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: link、新しい世代か: False
- 砂場で変わった名前: ['exports', 'exports/site', 'exports/site.browse-work', 'exports/site.browse-work/build.lock', 'exports/site.browse-work/old-5']

#### 既定、書き出し先がなく、old-5 が junction（先に userfiles）

- 終わり方: 0、次の実行: 0
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: dir、新しい世代か: True
- 砂場で変わった名前: ['data/browse', 'data/browse/KEY', 'data/browse/KEY.browse-work', 'data/browse/KEY.browse-work/build.lock', 'data/browse/KEY.browse-work/old-5', 'data/browse/KEY/.browse-generation', 'data/browse/KEY/assets', 'data/browse/KEY/assets/app.js', 'data/browse/KEY/concepts', 'data/browse/KEY/concepts/a.html', 'data/browse/KEY/concepts/b.html', 'data/browse/KEY/index.html']

#### 既定、書き出し先がなく、old-5 が junction（先に generation）

- 終わり方: 0、次の実行: 0
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: dir、新しい世代か: True
- 砂場で変わった名前: ['data/browse', 'data/browse/KEY', 'data/browse/KEY.browse-work', 'data/browse/KEY.browse-work/build.lock', 'data/browse/KEY.browse-work/old-5', 'data/browse/KEY/.browse-generation', 'data/browse/KEY/assets', 'data/browse/KEY/assets/app.js', 'data/browse/KEY/concepts', 'data/browse/KEY/concepts/a.html', 'data/browse/KEY/concepts/b.html', 'data/browse/KEY/index.html']

#### 既定、書き出し先がなく、old-5 が symlink（先に userfiles）

- 終わり方: 0、次の実行: 0
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: dir、新しい世代か: True
- 砂場で変わった名前: ['data/browse', 'data/browse/KEY', 'data/browse/KEY.browse-work', 'data/browse/KEY.browse-work/build.lock', 'data/browse/KEY.browse-work/old-5', 'data/browse/KEY/.browse-generation', 'data/browse/KEY/assets', 'data/browse/KEY/assets/app.js', 'data/browse/KEY/concepts', 'data/browse/KEY/concepts/a.html', 'data/browse/KEY/concepts/b.html', 'data/browse/KEY/index.html']

#### 既定、書き出し先がなく、old-5 が symlink（先に generation）

- 終わり方: 0、次の実行: 0
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: dir、新しい世代か: True
- 砂場で変わった名前: ['data/browse', 'data/browse/KEY', 'data/browse/KEY.browse-work', 'data/browse/KEY.browse-work/build.lock', 'data/browse/KEY.browse-work/old-5', 'data/browse/KEY/.browse-generation', 'data/browse/KEY/assets', 'data/browse/KEY/assets/app.js', 'data/browse/KEY/concepts', 'data/browse/KEY/concepts/a.html', 'data/browse/KEY/concepts/b.html', 'data/browse/KEY/index.html']

#### --out、前の世代があり、tmp-7 が junction

- 終わり方: 0、次の実行: 0
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: dir、新しい世代か: True
- 砂場で変わった名前: ['exports', 'exports/site', 'exports/site.browse-work', 'exports/site.browse-work/build.lock', 'exports/site.browse-work/tmp-7', 'exports/site/.browse-generation', 'exports/site/assets', 'exports/site/assets/app.js', 'exports/site/concepts', 'exports/site/concepts/a.html', 'exports/site/concepts/b.html', 'exports/site/index.html']

#### --out、前の世代があり、tmp-7 が symlink

- 終わり方: 0、次の実行: 0
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: dir、新しい世代か: True
- 砂場で変わった名前: ['exports', 'exports/site', 'exports/site.browse-work', 'exports/site.browse-work/build.lock', 'exports/site.browse-work/tmp-7', 'exports/site/.browse-generation', 'exports/site/assets', 'exports/site/assets/app.js', 'exports/site/concepts', 'exports/site/concepts/a.html', 'exports/site/concepts/b.html', 'exports/site/index.html']

#### --out、前の世代があり、del-6 が junction

- 終わり方: 0、次の実行: 0
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: dir、新しい世代か: True
- 砂場で変わった名前: ['exports', 'exports/site', 'exports/site.browse-work', 'exports/site.browse-work/build.lock', 'exports/site.browse-work/del-6', 'exports/site/.browse-generation', 'exports/site/assets', 'exports/site/assets/app.js', 'exports/site/concepts', 'exports/site/concepts/a.html', 'exports/site/concepts/b.html', 'exports/site/index.html']

#### --out、前の世代があり、del-6 が symlink

- 終わり方: 0、次の実行: 0
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: dir、新しい世代か: True
- 砂場で変わった名前: ['exports', 'exports/site', 'exports/site.browse-work', 'exports/site.browse-work/build.lock', 'exports/site.browse-work/del-6', 'exports/site/.browse-generation', 'exports/site/assets', 'exports/site/assets/app.js', 'exports/site/concepts', 'exports/site/concepts/a.html', 'exports/site/concepts/b.html', 'exports/site/index.html']

#### 既定、前の世代があり、tmp-7 が junction

- 終わり方: 0、次の実行: 0
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: dir、新しい世代か: True
- 砂場で変わった名前: ['data/browse', 'data/browse/KEY', 'data/browse/KEY.browse-work', 'data/browse/KEY.browse-work/build.lock', 'data/browse/KEY.browse-work/tmp-7', 'data/browse/KEY/.browse-generation', 'data/browse/KEY/assets', 'data/browse/KEY/assets/app.js', 'data/browse/KEY/concepts', 'data/browse/KEY/concepts/a.html', 'data/browse/KEY/concepts/b.html', 'data/browse/KEY/index.html']

#### 既定、前の世代があり、tmp-7 が symlink

- 終わり方: 0、次の実行: 0
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: dir、新しい世代か: True
- 砂場で変わった名前: ['data/browse', 'data/browse/KEY', 'data/browse/KEY.browse-work', 'data/browse/KEY.browse-work/build.lock', 'data/browse/KEY.browse-work/tmp-7', 'data/browse/KEY/.browse-generation', 'data/browse/KEY/assets', 'data/browse/KEY/assets/app.js', 'data/browse/KEY/concepts', 'data/browse/KEY/concepts/a.html', 'data/browse/KEY/concepts/b.html', 'data/browse/KEY/index.html']

#### 既定、前の世代があり、del-6 が junction

- 終わり方: 0、次の実行: 0
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: dir、新しい世代か: True
- 砂場で変わった名前: ['data/browse', 'data/browse/KEY', 'data/browse/KEY.browse-work', 'data/browse/KEY.browse-work/build.lock', 'data/browse/KEY.browse-work/del-6', 'data/browse/KEY/.browse-generation', 'data/browse/KEY/assets', 'data/browse/KEY/assets/app.js', 'data/browse/KEY/concepts', 'data/browse/KEY/concepts/a.html', 'data/browse/KEY/concepts/b.html', 'data/browse/KEY/index.html']

#### 既定、前の世代があり、del-6 が symlink

- 終わり方: 0、次の実行: 0
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: dir、新しい世代か: True
- 砂場で変わった名前: ['data/browse', 'data/browse/KEY', 'data/browse/KEY.browse-work', 'data/browse/KEY.browse-work/build.lock', 'data/browse/KEY.browse-work/del-6', 'data/browse/KEY/.browse-generation', 'data/browse/KEY/assets', 'data/browse/KEY/assets/app.js', 'data/browse/KEY/concepts', 'data/browse/KEY/concepts/a.html', 'data/browse/KEY/concepts/b.html', 'data/browse/KEY/index.html']

#### 状態のディレクトリの server.json が、利用者のファイルへのシンボリックリンク

- 結果: ['serve=started', '動いているあいだの stop=stop-sent', 'stop=not-running', 'is_running=False']
- 警告: []
- リンクの先が変わったか: 変わらない
- 砂場で変わった名前: ['data/browse/KEY.server', 'data/browse/KEY.server/server.json']
- 状態のディレクトリの中: ['.browse-server', 'server.lock']、server.json の種類: absent

#### 状態のディレクトリの server.json.new が、利用者のファイルへのシンボリックリンク

- 結果: ['serve=started', '動いているあいだの stop=stop-sent', 'stop=not-running', 'is_running=False']
- 警告: []
- リンクの先が変わったか: 変わらない
- 砂場で変わった名前: ['data/browse/KEY.server', 'data/browse/KEY.server/server.json.new']
- 状態のディレクトリの中: ['.browse-server', 'server.lock']、server.json の種類: absent

#### <data_dir> がジャンクションのときの、サーバー（手を入れない起動と終了、状態 11 種。直す前の探索の状態の数）

- 実行 22 回、破れた決まり 0 件

- 起動、動いているあいだの stop、終了、stop、動いているかの確かめ: ['serve=started', '動いているあいだの stop=stop-sent', 'stop=not-running', 'is_running=False']
- 砂場で変わった名前: ['udata/browse', 'udata/browse/KEY.server', 'udata/browse/KEY.server/.browse-server', 'udata/browse/KEY.server/server.lock']

#### 対照 cache_ids_by_name を、手を入れずに流す

- gen+datajunction/asis/default: 破れた決まり 0 件 []
- gen+datajunction/leftovers/default: 破れた決まり 0 件 []

3 秒

## 直したあと

Python 3.14.6、win32

#### 既定の書き出し先の名前が junction

- 終わり方: stop、次の実行: stop
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: link、新しい世代か: False
- 砂場で変わった名前: []

#### 既定の書き出し先の名前が symlink

- 終わり方: stop、次の実行: stop
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: link、新しい世代か: False
- 砂場で変わった名前: []

#### --out の名前が junction（先に userfiles）

- 終わり方: stop、次の実行: stop
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: link、新しい世代か: False
- 砂場で変わった名前: []

#### --out の名前が junction（先に generation）

- 終わり方: stop、次の実行: stop
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: link、新しい世代か: False
- 砂場で変わった名前: []

#### --out の名前が symlink（先に userfiles）

- 終わり方: stop、次の実行: stop
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: link、新しい世代か: False
- 砂場で変わった名前: []

#### --out の名前が symlink（先に generation）

- 終わり方: stop、次の実行: stop
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: link、新しい世代か: False
- 砂場で変わった名前: []

#### --out、書き出し先がなく、old-5 が junction（先に userfiles）

- 終わり方: 0、次の実行: 0
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: dir、新しい世代か: True
- 砂場で変わった名前: ['exports', 'exports/site', 'exports/site.browse-work', 'exports/site.browse-work/build.lock', 'exports/site.browse-work/old-5', 'exports/site/.browse-generation', 'exports/site/assets', 'exports/site/assets/app.js', 'exports/site/concepts', 'exports/site/concepts/a.html', 'exports/site/concepts/b.html', 'exports/site/index.html']

#### --out、書き出し先がなく、old-5 が junction（先に generation）

- 終わり方: 0、次の実行: 0
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: dir、新しい世代か: True
- 砂場で変わった名前: ['exports', 'exports/site', 'exports/site.browse-work', 'exports/site.browse-work/build.lock', 'exports/site.browse-work/old-5', 'exports/site/.browse-generation', 'exports/site/assets', 'exports/site/assets/app.js', 'exports/site/concepts', 'exports/site/concepts/a.html', 'exports/site/concepts/b.html', 'exports/site/index.html']

#### --out、書き出し先がなく、old-5 が symlink（先に userfiles）

- 終わり方: 0、次の実行: 0
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: dir、新しい世代か: True
- 砂場で変わった名前: ['exports', 'exports/site', 'exports/site.browse-work', 'exports/site.browse-work/build.lock', 'exports/site.browse-work/old-5', 'exports/site/.browse-generation', 'exports/site/assets', 'exports/site/assets/app.js', 'exports/site/concepts', 'exports/site/concepts/a.html', 'exports/site/concepts/b.html', 'exports/site/index.html']

#### --out、書き出し先がなく、old-5 が symlink（先に generation）

- 終わり方: 0、次の実行: 0
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: dir、新しい世代か: True
- 砂場で変わった名前: ['exports', 'exports/site', 'exports/site.browse-work', 'exports/site.browse-work/build.lock', 'exports/site.browse-work/old-5', 'exports/site/.browse-generation', 'exports/site/assets', 'exports/site/assets/app.js', 'exports/site/concepts', 'exports/site/concepts/a.html', 'exports/site/concepts/b.html', 'exports/site/index.html']

#### 既定、書き出し先がなく、old-5 が junction（先に userfiles）

- 終わり方: 0、次の実行: 0
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: dir、新しい世代か: True
- 砂場で変わった名前: ['data/browse', 'data/browse/KEY', 'data/browse/KEY.browse-work', 'data/browse/KEY.browse-work/build.lock', 'data/browse/KEY.browse-work/old-5', 'data/browse/KEY/.browse-generation', 'data/browse/KEY/assets', 'data/browse/KEY/assets/app.js', 'data/browse/KEY/concepts', 'data/browse/KEY/concepts/a.html', 'data/browse/KEY/concepts/b.html', 'data/browse/KEY/index.html']

#### 既定、書き出し先がなく、old-5 が junction（先に generation）

- 終わり方: 0、次の実行: 0
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: dir、新しい世代か: True
- 砂場で変わった名前: ['data/browse', 'data/browse/KEY', 'data/browse/KEY.browse-work', 'data/browse/KEY.browse-work/build.lock', 'data/browse/KEY.browse-work/old-5', 'data/browse/KEY/.browse-generation', 'data/browse/KEY/assets', 'data/browse/KEY/assets/app.js', 'data/browse/KEY/concepts', 'data/browse/KEY/concepts/a.html', 'data/browse/KEY/concepts/b.html', 'data/browse/KEY/index.html']

#### 既定、書き出し先がなく、old-5 が symlink（先に userfiles）

- 終わり方: 0、次の実行: 0
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: dir、新しい世代か: True
- 砂場で変わった名前: ['data/browse', 'data/browse/KEY', 'data/browse/KEY.browse-work', 'data/browse/KEY.browse-work/build.lock', 'data/browse/KEY.browse-work/old-5', 'data/browse/KEY/.browse-generation', 'data/browse/KEY/assets', 'data/browse/KEY/assets/app.js', 'data/browse/KEY/concepts', 'data/browse/KEY/concepts/a.html', 'data/browse/KEY/concepts/b.html', 'data/browse/KEY/index.html']

#### 既定、書き出し先がなく、old-5 が symlink（先に generation）

- 終わり方: 0、次の実行: 0
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: dir、新しい世代か: True
- 砂場で変わった名前: ['data/browse', 'data/browse/KEY', 'data/browse/KEY.browse-work', 'data/browse/KEY.browse-work/build.lock', 'data/browse/KEY.browse-work/old-5', 'data/browse/KEY/.browse-generation', 'data/browse/KEY/assets', 'data/browse/KEY/assets/app.js', 'data/browse/KEY/concepts', 'data/browse/KEY/concepts/a.html', 'data/browse/KEY/concepts/b.html', 'data/browse/KEY/index.html']

#### --out、前の世代があり、tmp-7 が junction

- 終わり方: 0、次の実行: 0
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: dir、新しい世代か: True
- 砂場で変わった名前: ['exports', 'exports/site', 'exports/site.browse-work', 'exports/site.browse-work/build.lock', 'exports/site.browse-work/tmp-7', 'exports/site/.browse-generation', 'exports/site/assets', 'exports/site/assets/app.js', 'exports/site/concepts', 'exports/site/concepts/a.html', 'exports/site/concepts/b.html', 'exports/site/index.html']

#### --out、前の世代があり、tmp-7 が symlink

- 終わり方: 0、次の実行: 0
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: dir、新しい世代か: True
- 砂場で変わった名前: ['exports', 'exports/site', 'exports/site.browse-work', 'exports/site.browse-work/build.lock', 'exports/site.browse-work/tmp-7', 'exports/site/.browse-generation', 'exports/site/assets', 'exports/site/assets/app.js', 'exports/site/concepts', 'exports/site/concepts/a.html', 'exports/site/concepts/b.html', 'exports/site/index.html']

#### --out、前の世代があり、del-6 が junction

- 終わり方: 0、次の実行: 0
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: dir、新しい世代か: True
- 砂場で変わった名前: ['exports', 'exports/site', 'exports/site.browse-work', 'exports/site.browse-work/build.lock', 'exports/site.browse-work/del-6', 'exports/site/.browse-generation', 'exports/site/assets', 'exports/site/assets/app.js', 'exports/site/concepts', 'exports/site/concepts/a.html', 'exports/site/concepts/b.html', 'exports/site/index.html']

#### --out、前の世代があり、del-6 が symlink

- 終わり方: 0、次の実行: 0
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: dir、新しい世代か: True
- 砂場で変わった名前: ['exports', 'exports/site', 'exports/site.browse-work', 'exports/site.browse-work/build.lock', 'exports/site.browse-work/del-6', 'exports/site/.browse-generation', 'exports/site/assets', 'exports/site/assets/app.js', 'exports/site/concepts', 'exports/site/concepts/a.html', 'exports/site/concepts/b.html', 'exports/site/index.html']

#### 既定、前の世代があり、tmp-7 が junction

- 終わり方: 0、次の実行: 0
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: dir、新しい世代か: True
- 砂場で変わった名前: ['data/browse', 'data/browse/KEY', 'data/browse/KEY.browse-work', 'data/browse/KEY.browse-work/build.lock', 'data/browse/KEY.browse-work/tmp-7', 'data/browse/KEY/.browse-generation', 'data/browse/KEY/assets', 'data/browse/KEY/assets/app.js', 'data/browse/KEY/concepts', 'data/browse/KEY/concepts/a.html', 'data/browse/KEY/concepts/b.html', 'data/browse/KEY/index.html']

#### 既定、前の世代があり、tmp-7 が symlink

- 終わり方: 0、次の実行: 0
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: dir、新しい世代か: True
- 砂場で変わった名前: ['data/browse', 'data/browse/KEY', 'data/browse/KEY.browse-work', 'data/browse/KEY.browse-work/build.lock', 'data/browse/KEY.browse-work/tmp-7', 'data/browse/KEY/.browse-generation', 'data/browse/KEY/assets', 'data/browse/KEY/assets/app.js', 'data/browse/KEY/concepts', 'data/browse/KEY/concepts/a.html', 'data/browse/KEY/concepts/b.html', 'data/browse/KEY/index.html']

#### 既定、前の世代があり、del-6 が junction

- 終わり方: 0、次の実行: 0
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: dir、新しい世代か: True
- 砂場で変わった名前: ['data/browse', 'data/browse/KEY', 'data/browse/KEY.browse-work', 'data/browse/KEY.browse-work/build.lock', 'data/browse/KEY.browse-work/del-6', 'data/browse/KEY/.browse-generation', 'data/browse/KEY/assets', 'data/browse/KEY/assets/app.js', 'data/browse/KEY/concepts', 'data/browse/KEY/concepts/a.html', 'data/browse/KEY/concepts/b.html', 'data/browse/KEY/index.html']

#### 既定、前の世代があり、del-6 が symlink

- 終わり方: 0、次の実行: 0
- 警告: [] / []
- リンクの先が変わったか: 変わらない
- 書き出し先の名前の種類: dir、新しい世代か: True
- 砂場で変わった名前: ['data/browse', 'data/browse/KEY', 'data/browse/KEY.browse-work', 'data/browse/KEY.browse-work/build.lock', 'data/browse/KEY.browse-work/del-6', 'data/browse/KEY/.browse-generation', 'data/browse/KEY/assets', 'data/browse/KEY/assets/app.js', 'data/browse/KEY/concepts', 'data/browse/KEY/concepts/a.html', 'data/browse/KEY/concepts/b.html', 'data/browse/KEY/index.html']

#### 状態のディレクトリの server.json が、利用者のファイルへのシンボリックリンク

- 結果: ['serve=started', '動いているあいだの stop=stop-sent', 'stop=not-running', 'is_running=False']
- 警告: []
- リンクの先が変わったか: 変わらない
- 砂場で変わった名前: ['data/browse/KEY.server', 'data/browse/KEY.server/server.json']
- 状態のディレクトリの中: ['.browse-server', 'server.lock']、server.json の種類: absent

#### 状態のディレクトリの server.json.new が、利用者のファイルへのシンボリックリンク

- 結果: ['serve=started', '動いているあいだの stop=stop-sent', 'stop=not-running', 'is_running=False']
- 警告: []
- リンクの先が変わったか: 変わらない
- 砂場で変わった名前: ['data/browse/KEY.server', 'data/browse/KEY.server/server.json.new']
- 状態のディレクトリの中: ['.browse-server', 'server.lock']、server.json の種類: absent

#### <data_dir> がジャンクションのときの、サーバー（手を入れない起動と終了、状態 13 種）

- 実行 26 回、破れた決まり 0 件

- 起動、動いているあいだの stop、終了、stop、動いているかの確かめ: ['serve=started', '動いているあいだの stop=stop-sent', 'stop=not-running', 'is_running=False']
- 砂場で変わった名前: ['udata/browse', 'udata/browse/KEY.server', 'udata/browse/KEY.server/.browse-server', 'udata/browse/KEY.server/server.lock']

#### 対照 cache_ids_by_name を、手を入れずに流す

- gen+datajunction/asis/default: 破れた決まり 0 件 []
- gen+datajunction/leftovers/default: 破れた決まり 0 件 []
#### --out の親が、利用者のディレクトリへのジャンクション（書き出し先がない）

- 終わり方: 0、次の実行: 0（期待: 0）
- 警告: [] / []
- 書き出し先が新しい世代か: True、作業用の中: ['.browse-work', 'build.lock']
- 見張った木（userparent\keep.txt）で変わった名前: []
- 砂場で変わった名前: ['userparent', 'userparent/site', 'userparent/site.browse-work', 'userparent/site.browse-work/.browse-work', 'userparent/site.browse-work/build.lock', 'userparent/site/.browse-generation', 'userparent/site/assets', 'userparent/site/assets/app.js', 'userparent/site/concepts', 'userparent/site/concepts/a.html', 'userparent/site/concepts/b.html', 'userparent/site/index.html']

#### --out の親が、利用者のディレクトリへのジャンクション（その先に前の世代がある）

- 終わり方: 0、次の実行: 0（期待: 0）
- 警告: [] / []
- 書き出し先が新しい世代か: True、作業用の中: ['.browse-work', 'build.lock']
- 見張った木（userparent\keep.txt）で変わった名前: []
- 砂場で変わった名前: ['userparent', 'userparent/site', 'userparent/site.browse-work', 'userparent/site.browse-work/.browse-work', 'userparent/site.browse-work/build.lock', 'userparent/site/.browse-generation', 'userparent/site/assets', 'userparent/site/assets/app.js', 'userparent/site/concepts', 'userparent/site/concepts/a.html', 'userparent/site/concepts/b.html', 'userparent/site/index.html']

#### --out の親が、Wiki のルートへのジャンクション

- 終わり方: stop、次の実行: stop（期待: 止まる）
- 警告: [] / []
- 書き出し先が新しい世代か: False、作業用の中: None
- 見張った木（wiki）で変わった名前: []
- 砂場で変わった名前: []

#### 既定の書き出し先の前の世代の中に、Wiki のルートへのジャンクションがある

- 終わり方: 0、次の実行: 0（期待: 0）
- 警告: [] / []
- 書き出し先が新しい世代か: True、作業用の中: ['.browse-work', 'build.lock']
- Wiki で変わった名前: []


3 秒
