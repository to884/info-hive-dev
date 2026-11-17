# プロンプトのフック：並列作業中の性能の修正

2026-11-18。対象はADR-0032のUserPromptSubmitフック。モデル表の再測定後に残った、起動の遅さと候補の欠落を扱う。モデル表と `agents/wiki-reader.md` は今回変更しない。

## 原因と修正

1. **依存が空でもスクリプト専用の仮想環境を経由していた。** 旧起動行の `uv run --script` は、PEP 723の `dependencies = []` でもuvのスクリプト用仮想環境を使っていた。計測した親子の `sys.executable` は `environments-v2/.../Scripts/python.exe` だった。Windowsでは仮想環境のPythonから基底のPythonへの起動が加わる。`uv run --no-project --no-config ... --python ">=3.12,<3.15" python -I -S <hook>` に変え、スクリプト専用の仮想環境を作らず既存のPythonを選ぶ。利用者の `VIRTUAL_ENV` やcwdの `.venv` があると入口はそのPythonを使うため、入口のvenvランチャーのコストは残る。解析の子は、CPythonの `_base_executable`（なければ `sys.executable`）を `-I -S` で起動する。
2. **ファイルの走査が本文の解析器まで初期化していた。** `wiki_pages` のimport時に、同梱したMarkdown解析器のソース全体のハッシュ、`markdown_it`・`mdurl` のimport、共有パーサーの生成を行っていた。フックが使うのは `walk_pages` と `walk_index_files` であり、本文のMarkdown解析器は不要である。解析器とハッシュを、本文の解析または `PARSER_ID` の参照時に初期化するよう分けた。解析器の初期化はロックで保護し、同梱版の検証、解析の設定、既存の公開属性は維持する。
3. **CPUが埋まると、短いフックも起動を待たされていた。** 合成負荷を停止した後のPCでも、別のPython処理などがCPUを使い、全体の使用率が99%だった。起動と解析器の修正だけでは、8本の合成負荷で19/20、16本で14/20となる回が残った。Windowsの実行入口だけを `ABOVE_NORMAL_PRIORITY_CLASS` にし、子の起動にも同じ優先度を指定する。[Windowsの定義](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-setpriorityclass)で通常より一段高いクラスであり、HighやRealtimeは使わない。変更できなければ通常の優先度で続ける。ライブラリとしてimportする側、他の作業のプロセス、Windows以外には適用しない。

起動だけの修正では、16本の合成負荷を繰り返したときに候補到達が20/20から10/20まで変動した（`stress-after-16.json`、`release-parallel-16.json`）。不要なMarkdown解析器の読み込みと、前景の短時間の処理の優先度まで修正した。途中の版を完成版とは扱わない。優先度の変更により、同じCPUを使う通常優先度の処理がフックの実行中に使えるCPU時間は減る。フックは内部期限で終了し、優先度を永続的な設定には残さない。

親子の絶対期限、内部2.5秒、登録のtimeout 5秒、ゲート、出力の2,000文字上限、出力をflushしてから既出を保存する順序には手を加えていない。wikiとその索引には書き込まない。常駐プロセスや検索キャッシュは導入していない。

## 測定条件

- Windows 11（10.0.26300）、Ryzen 7 3800XT（8コア16論理プロセッサ）、RAM 32 GiB。uv 0.12.2、Git Bash 2.45.2。venvなしの入口はuvが選んだCPython 3.13.7。測定器と、既存venvのケースに用意したPythonはCPython 3.14.6。
- `bench_prompt_parallel.py` が150ページの合成wikiを作り、2ページを明示する日本語の同じ問い合わせを、異なるセッションIDで20回実行する。フックは4本同時に起動する。
- 負荷の1本は、新しいPythonを繰り返し起動し、標準ライブラリを読み、同じ合成wikiの全Markdownファイルを読む。負荷は4・8・16本。APIやネットワークは使わず、他の作業のプロセスは停止・変更しない。生データに各負荷の反復数・読込バイト数・実行時間を保存する。
- 時間は、シェルの起動前から標準出力の回収まで。ウォームアップ1回を除く。原因調査の `--profile` では親子の時刻を取る計測用コピーを使い、製品のモジュールを読む。最終の並列・逐次測定は計測コードを挿入せず、登録済みのコマンドと実際の入口を使う。
- 候補到達は、終了コード0、標準エラーなし、フックのJSONの型、候補2件のスラッグと相対パス、2,000文字以内を検査する。単なる標準出力の有無では数えない。
- 実行ホストから引き継いだ `RUST_LOG=warn` だけを測定から外した。この明示的なログ設定はuvのquiet指定より優先する。製品で利用者のログ設定を上書きする変更は行っていない。

## 初回レビュー時の測定

| 版・追加の負荷 | p95 | 最大 | 候補到達 | 生データ |
| --- | ---: | ---: | ---: | --- |
| 旧起動行・16本、計測コピー | 3,628.9 ms | 4,362.9 ms | 19/20 | `paired-before-16.json` |
| 起動と解析器の修正・8本、計測コピー | 3,757.8 ms | 3,803.0 ms | 19/20 | `lazy-parallel-8.json` |
| 起動と解析器の修正・16本、実際の入口 | 4,252.9 ms | 4,601.4 ms | 14/20 | `actual-parallel-16.json` |
| 初回レビュー時の版・8本、実際の入口 | 2,048.0 ms | 2,396.2 ms | 20/20 | `foreground-parallel-8.json` |
| 初回レビュー時の版・16本、実際の入口 | 2,661.0 ms | 2,777.5 ms | 20/20 | `foreground-parallel-16.json` |

初回レビュー時の8本と16本の計40回は、候補2件がすべて届き、終了コード0、標準エラーなし、外側の5秒以内だった。追加の合成負荷を入れない逐次測定は、短文p95 747.2 ms、検索p95 1,167.9 ms、到達10/10（`foreground-serial.json`）。このときも他の作業は止めていない。検索1秒の目安には届いておらず、アイドル状態での性能を表す値とはしない。

この時点の負荷は8本で各8〜9回、16本で各6〜8回のPython起動と全ファイル読込を完了した。優先度の変更前後で負荷側のスループットも変わるため、同じ負荷本数でも同じCPU・I/Oの配分ではない。また他作業のCPU使用率も変動する。表から一定の速度向上率や、旧5.3秒の全原因を取り除いたという結論は出さない。

## レビュー指摘の修正後の測定

URL取り込みの回帰、優先度の二重適用、ベンチマークのcwdとハッシュの記録を直したコードで測り直した。シェルも合成wikiを置いたプロジェクトのcwdで動かす。`cwd`・`active` のvenvは測定前に作った既存の環境であり、フックが作るものではない。

| 条件（全てフック4本同時） | p95 | 最大 | 候補到達 | 生データ |
| --- | ---: | ---: | ---: | --- |
| 8本の負荷、明示参照 | 1,153.1 ms | 1,322.2 ms | 20/20 | `review2-parallel-8.json` |
| 16本の負荷、明示参照・1バッチ目 | 1,356.3 ms | 1,402.7 ms | 20/20 | `review2-parallel-16-a.json` |
| 16本の負荷、明示参照・2バッチ目 | 1,625.6 ms | 1,741.1 ms | 20/20 | `review2-parallel-16-b.json` |
| 8本の負荷、cwdの既存 `.venv` | 1,494.8 ms | 1,559.0 ms | 20/20 | `review2-venv-cwd-8.json` |
| 8本の負荷、有効な `VIRTUAL_ENV` | 1,160.1 ms | 1,178.7 ms | 20/20 | `review2-venv-active-8.json` |
| 8本の負荷、明示参照なしの題の一致 | 3,178.7 ms | 3,258.8 ms | 20/20 | `review2-names-corrected-8.json` |

計120回で候補2件がすべて届き、終了コード0、標準エラーなし、最大3.26秒だった。逐次の短文はp95 348.5ms、検索は780.2ms、検索到達10/10（`review2-serial.json`）。このバッチでは検索1秒の目安に届いたが、前の逐次測定の1.17秒も残しており、負荷の変動による幅がある。

明示参照のない試行では、最初の2ページの題だけを「固有の候補資料アルファ」「固有の候補資料ベータ」に変えて、その題を問い合わせる（S2）。索引の要約だけで選ぶS4や、別のwiki、同時フック数を増やした場合は測っていない。合成の負荷は通常優先度であり、競合相手もAboveNormalの場合に同じ改善が出るとは保証しない。bash・uv・Python自体の初期化は優先度変更より前であり、I/Oの優先度も変えない。

`review2-names-8.json` は、計測用のページ1の題を置換するときに元の題を取り違え、問い合わせに対応するページが1件しかなかった。候補2件を検査する条件では0/20となった無効なfixtureの記録であり、性能の失敗または成功には数えない。題をファイルから取得して確実に置換するよう測定器を直し、別名の `review2-names-corrected-8.json` に再測定した。製品のゲートは変更していない。

## 互換性と限界

- 既存のPython 3.12〜3.14を使い、Pythonや依存のダウンロードと、呼び出し元プロジェクトの同期は行わない。起動行の範囲とPEP 723の宣言の一致も試験する。
- BashとPowerShellで、日本語と空白を含むパス、日本語の標準入力の完全一致、不正な `pyproject.toml`・`uv.toml`・`.python-version`、`PYTHONPATH` の影響、Python・uv・スクリプトの欠落、venvからの直接起動を確認する。
- 閲覧は従来、`wiki_pages` のimportの副作用でMarkdownのToken型が読めることに依存していた。遅延初期化に合わせ、`wiki_browse_core` が同梱版の型を明示して取得するよう変更した。検査で見つけたimport失敗を修正し、PyYAML付きPython 3.12でページ集合・閲覧の161件を通した（156成功、環境による5件をskip）。
- `-I -S` が対象にするのはフックと子のPythonである。uvのPython検出時には、有効な `VIRTUAL_ENV` の起動時の処理が実行されることがある。旧起動行でも起きており、uvまで独立モードで動くと主張しない。
- 旧記録の検索p95 5.3秒・到達3/10では、当時のCPU・I/O・メモリの連続記録がない。同じモデル測定や他作業の負荷を正確に再現した比較ではない。合成負荷の本数を実際のClaude CLIの本数に換算しない。
- 実測値は、当該PCと150ページの合成wikiでの有限回の結果である。短い試験のp95を一般的な速度向上率にはしない。内部2.5秒はPythonの入口からの期限であり、シェル・uv・Python自体の起動やOSのスケジューリング、任意のファイルシステムの待ち時間を含む上限ではない。

## 生データの扱いと再現

生データは `wiki-prompt-hook-performance-2026-11-18/` に置く。`baseline-hook.py`、`baseline-hooks.json`、`baseline-wiki-pages.py` は変更前のスナップショットである。変更前のhookのSHA-256は `84f639b153564c660e28cd9e634b5772895ee4ec355f99f8719aeeeb8e533f43`。各測定にはコマンドと入口のハッシュを記録し、最終測定には `wiki_prompt_context.py` と `wiki_pages.py` のハッシュも付ける。

`baseline-profiler-error.json` は計測用コピーの構文誤りで無効。`final-parallel-4.json` と `final-parallel-8.json` は、uvを2回起動する不採用案である。`optimized-*`、`paired-after-*`、`release-*`、`stress-after-16.json` は途中の調査または起動だけの修正版。`lazy-*`、`actual-parallel-16.json` は解析器の遅延初期化までの版。`foreground-*` は初回レビュー時の版。修正後の最終データは上表の6ファイルと `review2-serial.json`。旧検証のハッシュは `validation-before-review.json` に残し、現行版との対応は `validation.json` に記録する。

```powershell
python tests/wiki/bench_prompt_parallel.py --load-workers 8 --out <result.json>
python tests/wiki/bench_prompt_publication.py --pages 150 --runs 10 --out <serial.json>
python -X utf8 -m unittest tests/wiki/test_prompt_hook.py tests/wiki/test_prompt_launcher.py tests/wiki/test_reader_measurement.py tests/wiki/test_page_set.py
```

変更前を再測定する場合は、入口と登録だけでなく `wiki_pages.py` も変更前に戻した隔離コピーを使う。現在のモジュールと旧入口を混ぜたものを変更前の測定とはしない。

uvのオプションの仕様は、[Running commands](https://docs.astral.sh/uv/concepts/projects/run/)、[CLI reference](https://docs.astral.sh/uv/reference/cli/)、[Running scripts](https://docs.astral.sh/uv/guides/scripts/)を参照した。今回の環境での動作は上記の起動試験でも確かめる。

## 回帰試験

- 解析器の変更後、走査・lint・ページ集合・フック・測定の155件：成功（環境による3件をskip）。
- 最終の優先度変更後、フック・実際の起動行・モデル測定の96件：全件成功。ライブラリのimportでは優先度を変えず、実際の入口と子だけがAboveNormalになることも確認した。
- 閲覧の明示的な解析器の取得への変更後、PyYAML付きPython 3.12でページ集合・閲覧の161件：成功（環境による5件をskip）。

モデルの決定記録と製品の定数・エージェントの一致は上記96件に含む。158回の有料のモデル測定は再実行していない。

## Opusの初回レビューと修正

Opus 5.5/highの初回判定は却下だった（`docs/agent-runs/2026-11-18-wiki-prompt-hook-performance/opus-review-1.md`）。`wiki_rawcheck` が `importlib.import_module` でMarkdownの規則と型を直接読む箇所を見落としており、URL取り込みが起動できなかった。外部のMarkdown解析器がある場合には、同梱版のパーサーと外部版の規則・型が混ざることも確認された。

`wiki_pages.markdown_module()` に同梱版の検証とサブモジュールの取得をまとめ、rawcheckとbrowseが必ずこの口を使うよう修正した。初期化後に外部のサブモジュールが混ざった場合も、その所在を検査して拒否する。freshなPythonで、外部版のない環境と、外部版を先に読み込んだ環境の両方を試験する。遅延化したimportの副作用に依存する呼び出しを残さない。

また、子自身による優先度の再設定を止め、親が変更に成功したときだけ `creationflags` で子に適用するよう統一した。親のAPIを拒否する試験では親子とも通常優先度で動くこと、子がAPIを再呼び出ししないことを確かめる。既存venvの利用を説明に明記し、cwdの `.venv` と `VIRTUAL_ENV` の両方の実起動を試験する。最終のベンチマークではシェルのcwdも合成プロジェクトにそろえ、逐次測定にもcontextとpagesのハッシュを付ける。

修正後は、フック・ページ集合・URL取得・取り込み検査・web-raw・YouTubeの393件（1skip）、PyYAML付きPython 3.12で未初期化wiki・閲覧の171件（6skip）が成功した。同梱版の6件の追加試験も成功。実際の外部markdown-it-py 4.3.0を先に読み込んだ環境でも、取り込みが同梱3.0.0の型と規則を使うことを確認した。これらの試験はネットワークからページや動画を取得せず、有料のモデルも呼ばない。

## 最終レビュー

[Opus 5.5/highの再レビュー](../agent-runs/2026-11-18-wiki-prompt-hook-performance/opus-review-2.md)は「採用可」、確信度は中、致命的・重大な欠陥は0件だった。レビュアーも関係する167件の試験、新しいPythonでのimport、実際の外部4.3.0との混在、優先度の失敗経路、ソース13ファイルと測定7ファイルのハッシュ・数値を独立に確認した。

軽微な点として、`validation.json` の1秒達成の真偽値を `one_second_goal_met_in_this_batch` に変え、単一バッチの結果であることを明示した。製品のコードは採用可のレビュー後に変更していない。

残る制約は次のとおり。上記の測定範囲を広げた保証にはしない。

- 有効なvenvの実測はcwdの `.venv` と同じ場所を指定した場合であり、cwdの外のvenvは測っていない。S2は8本の負荷だけで、16本の負荷やS4は未測定。
- 利用者が先祖のプロセスを意図的に低い優先度にしていても、フックの親子はAboveNormalへ上げる。入口より前のuvやPython初期化、I/Oの優先度は変えない。
- 初期化後に `sys.modules` から同梱パッケージを手で削除して再importすると、同じ所在でも異なるTokenのクラスを取得できる。製品はこの操作をせず、任意のモジュール再読込の同一性までは保証しない。
- 不正な個数の `--worker` 引数で手動実行した場合、通常の入口として動く一方、優先度は適用されない。登録済みのコマンドと解析の子はこの引数の形を使わない。

レビューと現在のコード・測定記録の対応は `wiki-prompt-hook-performance-2026-11-18/final-review.json` に残す。
