# Web の本文を取れないときに Playwright で取得する

2026-11-17。利用者は「本文を取れないとき、Playwright で自動取得する」を選んだ。Claude の利用上限のため、設計と実装の敵対的レビューは Astra が行う。

## 動作

- `wiki_fetch.py` に `--browser-fallback` を足し、Web の取り込みの W2 はこの引数を付ける。引数のない既存の呼び出しは、標準ライブラリだけで動く。
- HTTP で取得し、従来と同じ変換で本文が空または空白を除いて 500 文字未満なら、保存する前に Playwright で一度だけ取得する。HTTP 401/403 のときも一度試す。404、429、接続や TLS の失敗、PDF、YouTube は対象外とする。ログインの案内が 200 で返る場合などには `--browser-only` で最初からブラウザを読める。この明示入力では途中再開を飛ばすが、既存 raw の上書きは `--force` があるときだけにする。
- 描画後の DOM は、同じ HTML の変換、画像の保存、raw の検査に渡す。HTTP の短い本文を先に raw に書かない。DOM の UTF-8 のバイト列を `source_sha256` の対象にし、`source_sha256_of: dom`、`fetch_method: playwright` を記録する。
- 再開できる作業用の写しがあれば、ネットにつながずに再開する。既存の raw は `--force` のない限り上書きしない。`--html-file` は自動取得の対象外とする。
- Playwright に失敗したら、raw と作業用の写しを書かずに、失敗した理由と手動の HTML を渡す方法を返す。DOM でも本文が短ければ従来の `needs_browser` に戻す。自動の取り直しを繰り返さない。

## 実行

- ヘルパー `wiki_fetch_browser.py` を `uv run --script` で呼ぶ。PEP 723 で Playwright 1.65.2 と Python `>=3.12,<3.15` を固定する。最初に必要になったときだけ依存を取得し、以後はキャッシュを使う。
- 利用者の追加指定により、ブラウザの既定は `system` とする。Windows の `AssocQueryStringW` に元の URL の `http` または `https` の実行ファイルを尋ね、Chrome か Edge なら、その実パスを Playwright に渡す。転送中も同じブラウザを使う。未対応、存在しない実行ファイル、検出不能では止まり、黙って Chromium に切り替えない。非 Windows の自動検出は今回の対応範囲外である。`--browser chrome|msedge|chromium` で明示すればどの OS でも従来の取得ができる。Chromium の自動導入は明示したときだけ行う。
- `--browser-session isolated` は、ヘッドレスのブラウザと新しい一時のコンテキストを使う。普段のログイン状態は使わない。ログイン、同意ボタン、CAPTCHA は操作しない。以下の本文を待つ手順とネットワークの制限も、この独立したモードに当てる。
- DOMContentLoaded のあと、本文の変化を短い間隔で調べる。本文が 500 文字以上になり、最低 2 秒経過して、1 秒変わらなければ DOM を取得する。500 文字未満の本文は、静止していても `--timeout` まで出現を待つ。通信が絶えないサイトでも終わるように、networkidle は待たない。ブラウザの HTTP エラーの応答は原文にしない。
- HTML は子プロセスの標準出力の JSON で受け、加工前の HTML を一時ファイルに保存しない。入出力は UTF-8 とする。DOM の大きさは `--max-bytes` 以下にする。
- ページと副リソースは http/https だけにする。既存のホスト判定で公開 URL から内部アドレスへの要求を拒み、YouTube へのページ遷移も止める。DNS を検査したあとに再解決する点は、既存の HTTP の取得と同じ制約であり、ネットワークの隔離を保証する仕組みではない。
- `route.fetch(max_redirects=0)` で応答を調べ、3xx をブラウザに渡さない。ページ本体の転送先を検査したら、一時の空の 200 で現在の遷移を終えてから、新しい `goto` として次の URL を取る。最大 10 回とする。副リソースの転送は追わない。最終の本文を元 URL の応答として渡すと、相対 import の基準が崩れるためである。このようなリソースに依存するページは、手動の HTML が必要になることがある。副リソースの取得の失敗は本文の取得を失敗にせず、その要求を中断する。
- Service Worker、WebSocket、ダウンロード、ポップアップを使わず、ブラウザは成功・失敗の両方で閉じる。

## 確認

通常の本文ではブラウザを呼ばないこと、空の本文と 403 だけが自動取得されること、DOM のハッシュ、相対リンクと画像、失敗時の既存ファイルの保持、再開時の取得省略、YouTube と内部アドレスへの転送を確かめる。HTTP の本文にはない日本語を遅れて表示するローカルのページを、実際の Chromium で取り込んで確認する。

## 根拠

- [Playwright Python の Page API](https://playwright.dev/python/docs/api/class-page): `goto`、`content`、`wait_for_function`。
- [ブラウザのインストール](https://playwright.dev/python/docs/browsers): ライブラリに対応する Chromium が必要になる。
- [PyPI の Playwright](https://pypi.org/project/playwright/): 固定する版を確認した。
- [Windows の AssocQueryStringW](https://learn.microsoft.com/en-us/windows/win32/api/shlwapi/nf-shlwapi-assocquerystringw): プロトコルの既定アプリの実行ファイルを取得する。サイズを尋ねる呼び出しの `S_FALSE` は正常な応答として扱う。

ADR-0004 のブラウザによる補完を、公開ページについて自動化する。認証が要るページの手動の HTML の経路は残す。

## 普段のログイン状態を使う追加指定

既定の `--browser-session existing` は、公式 Playwright 拡張で利用者が許可した既存タブを読む。対象ページを読み込み終えてから接続確認でそのタブを 1 つ選ぶ。ページの移動、新しいタブの作成、Cookie や storageState の書き出し、プロファイルの複製はしない。URL が一致する許可済みタブがない、複数ある、読み取り中に URL が変わった場合は止まる。転送後の URL のタブなら、その URL で依頼し直す。

MCP の汎用ログ層は使わない。`playwright-core` 1.66.0-alpha-2026-11-09 の `lib/coreBundle` の `tools.createBrowserWithInfo` を通し、拡張への接続部分だけを使う。これは内部の実装への依存なので、版を厳密に固定し、存在と版を確かめ、更新時は契約の試験を通す。DOM、画像、認証値を診断ログに出さないよう、子プロセスには `DEBUG`、`DEBUG_FILE`、Playwright の診断用変数、`NODE_OPTIONS` を渡さない。接続の一時の記述には本文や認証情報を含めず、最後に unbind と切断を行う。利用者のタブとブラウザ本体は閉じない。

HTML の画像の選択には、Python の共通の本文変換器を使う。本文外の画像と重複画像で画像数の上限を消費しない。同じ origin の読み込み済み画像の表示画素を canvas から PNG にし、メモリで受け渡す。別 origin、読み取り不能、未ロードの画像は未取得を記録する。匿名 HTTP で別の画像を取り直さない。ページそのものの通常の通信や共有ストレージの変化を止める機能ではない。ネットワークを代理処理しないため、独立したモードの Service Worker とリダイレクトに関する制御を共有プロファイルへ持ち込まない。

2026-11-17 の実 Edge の試験では、利用者が対象タブを開いて接続を許可し、HttpOnly Cookie が必要な本文と画像を取得できた。接続確認は利用者自身が行う。Node.js 20 以上、npm、公式拡張が必要である。実機確認中の画面検査は Computer Use が URL を十分な確度で読めず停止したため、その後は UI 操作をせず、既に起動していた読み取り試験の結果で確認した。
