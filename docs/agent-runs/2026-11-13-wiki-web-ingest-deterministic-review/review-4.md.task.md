対象は、`/wiki:ingest` で URL を取り込むとき、規則で決まる工程をモデルからスクリプトに移す設計案の 4 版である。

1〜3 版は却下された（docs/agent-runs/2026-11-13-wiki-web-ingest-deterministic-review/review-1.md、review-2.md、review-3.md）。指摘は原因の構造で分け、前提を変えた（root-causes.md、root-causes-2.md、root-causes-3.md）。4 版の主な変更は次のとおり。
- 段階 1 の合格の条件から「今の出力との一致」を外し、HTML の内容との一致だけにした。
- raw に書く口を apply だけにし、--stage なしで raw に直接書く使い方をやめた。
- 守る語は綴りごとの既定にし、出現ごとに release_terms で外せるようにした。守る句は 1 つの text の中だけで当て、インラインの境目をまたいで当てない。
- 錠を OS のファイルの錠（msvcrt.locking、fcntl.flock）にし、錠を回収する操作をなくした。
- 確定前の生成物を定め、clean が錠を取って消す。Markdown は書き終えた一時ファイルを os.link で正式な名前に結んで公開する。
- 判断が必要な範囲を、decisions.json の content_root で決まる最終の本文で数える。

目的: 2026-11-13 の比較（docs/research/wiki-ingest-model-comparison-2026-11-13.md）で見つかった raw の誤りを、モデルの能力に頼らず構造で防ぐこと。raw は取り込み後に書き換えない原本である（docs/adr/0004-raw-holds-translated-web-pages.md）。

見てほしい点:
- review-1〜3 の指摘が、4 版の構造で本当に起きなくなったか。root-causes-3.md の対応表の主張を崩せるか。
- 4 版で新しく入った仕組み（OS のファイルの錠、os.link による公開、release_terms、最終の本文での判断の範囲）が持ち込んだ欠陥。
- 正しい訳や正しい判断を誤りとして止めてしまう経路が、まだ残っていないか。

読むもの: 設計案 docs/plans/wiki-web-ingest-deterministic-2026-11-13.md、root-causes*.md、review-*.md、ADR-0004、info-hive-wiki/commands/ingest.md、info-hive-wiki/skills/info-hive/references/ingest-workflow.md、info-hive-wiki/skills/info-hive/scripts/wiki_fetch.py。
