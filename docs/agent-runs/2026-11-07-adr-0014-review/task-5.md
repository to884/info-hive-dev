これは 5 回目の依頼で、3 回目（設計）と 4 回目（実装）の指摘を直したことの確認である。Codex のシェルではファイルを読めないので、読むべき本文をこの依頼に埋め込む。**シェルでファイルを読もうとしないこと。** 埋め込んだ本文と差分だけで判断してよい。

埋め込んだ差分は info-hive-rag の d8c4641..d82c3b1（3 回目と 4 回目の指摘への直し）である。それより前の差分（6a760b9..d8c4641）は、3 回目と 4 回目にあなたが見たものである。

確かめてほしいこと:
1. 次の指摘が、直しで本当に解消したか。新しい反例がないか。
   - 3 回目の重大 1: 抽出の版を上げても、0.4.0 の結果（extract-v1）を新しい版の結果として移す
   - 3 回目の重大 2 と 4 回目の重大 1: 抽出の版を上げても、前の版の埋め込みの途中経過を使い回す。返す本文と索引の本文が食い違う
   - 4 回目の重大 2: 同じ内容を 2 か所で登録していると、片方を取り込み直しただけで、もう片方の場所が消える
   - 3 回目の軽微: 空にしたあとで置き換えた文書の 0.4.0 の結果が残る。configure(ocr_dpi=0) を拒まない
2. 直しが新しく壊したもの（0.4.0 の索引との互換、指紋の値、generation の扱い、`_reingest()` を使う `_extraction_in_use()` と `_prune_previous()`、要再確認の印）。
3. ADR-0014 の記述と実装の食い違い。

## ADR-0014 の本文（今）

# ADR-0014：rag は抽出と OCR の結果を、埋め込みと分割の方針から切り離して保存する

| 項目 | 内容 |
| --- | --- |
| 状態 | 提案 |
| 決定日 | 未定 |
| 決定者 | info-hive の開発者（このリポジトリの作者） |
| 関連 | ADR-0007、ADR-0012、ADR-0013、[機能実装の優先順位（4 版目）](../research/feature-priority-2026-11-06.md)の 2 位と 3 位 |

## 背景

rag 0.4.0 は、PDF のページごとの抽出の結果（`page-*.json`。OCR したページは OCR の結果）と、それをつないだ本文（`document.md`）を、`<data_dir>/wikis-v2/<wiki のハッシュ>/extracted/<generation>/` に置く。`generation` は、内容の SHA-256（`doc_id`）と `Config.fingerprint` から作る。`fingerprint` には、埋め込みのモデルと版、次元、分割の大きさと重なり、OCR の設定、トークナイザーの方針が入る。

この作りには 3 つの問題がある。

1. 埋め込みのモデルや分割の設定を変えると、`generation` が変わり、OCR の結果を使えなくなる。OCR は 1 ページに数秒から数十秒かかり、作者の資料は 22,335 ページある。
2. そもそも、同じ `data_dir` では方針を変えられない。wiki ごとの索引は最初の方針を `policy.json` に記録し、`fingerprint` が違うと、取り込みも検索も「別の data_dir で構築してください」で止まる（`Engine._check_policy()`）。`data_dir` を変えると、抽出の結果も置き去りになる。このため、抽出の結果の鍵だけを変えても、モデルを変えたときに OCR をやり直すことは避けられない。
3. 同じ PDF を 2 つの wiki に取り込むと、OCR を 2 回する。抽出の結果は wiki ごとの作業領域にあるからである。

ADR-0012 の rag の移行（索引を wiki のサーバーに頼む形）も、OCR の結果と抽出した本文を使い回し、埋め込みと索引だけを作り直す前提で進め方を組んでいる。今の作りはこの前提を満たしていない。

## 決定

### 抽出の結果の鍵と置き場所

| 対象 | 決定 |
| --- | --- |
| 鍵 | 内容の SHA-256 と、抽出の設定（抽出の版 `EXTRACT_REVISION`、OCR のモデルの版 `OCR_REVISION`、`ocr_mode`、`ocr_dpi`）だけにする。埋め込みのモデル、分割、トークナイザー、題名は入れない |
| 抽出の版 | `EXTRACT_REVISION`（最初は `extract-v1`）を新しく置く。ページの判定（`inspect_page()` の文字化け、縦書き、スキャンの判定）や、テキストの取り出し方を変えたときに上げる。抽出の結果の鍵に入れる。`Config.fingerprint` にも、`extract-v1` 以外のときだけ入れる。`extract-v1` のあいだは指紋を 0.4.0 と同じ値にして、0.4.0 の索引をそのまま使うためである。版を上げると、すべての wiki の索引が方針の変わった索引になり、取り込み直すと抽出と埋め込みをやり直す。返す本文と索引の本文が食い違わず、前の版の埋め込みの途中経過（`generation` は指紋から作る）も使い回さない。指紋の値は試験で固定し、意図せずに変えないようにする |
| 置き場所 | `<data_dir>/extracted/<SHA-256>/<ocr_mode>-<ocr_dpi>-<OCR_REVISION の先頭 12 文字>-<EXTRACT_REVISION>/` に置く。同じ `data_dir` を使う wiki のあいだで共有する。同じ PDF を 2 つの wiki に取り込んでも、OCR は 1 回で済む |
| 中身 | `page-<6 桁のページ番号>.json` と `document.md`。`document.md` は題名を含まず、ページの見出し（`## p. <番号>`）と本文だけなので、wiki によらない。OCR の一時ファイル（`ocr-*`）もこのフォルダーの中に作る |
| 排他 | 文書ごとのロック `<data_dir>/extracted/<SHA-256>.lock` を、その文書を取り込むあいだ（抽出から公開まで）と、後始末で消すあいだ取る。後始末は待たずに取り、取れなければ消さずに残す。2 つの取り込みが互いの古い版を消そうとして待ち合うことを防ぐ。製品の経路では、`data_dir` ごとにワーカーが 1 つ（`worker.lock`）なので競合しないが、`Engine` を直接使う経路（試験など）のために置く |
| 読めない PDF | 開くときと読むときの `OSError` は、理由を添えた日本語のエラーにする。OneDrive のオンラインだけのファイルは、同期のアプリが動いていないと `[Errno 22] Invalid argument` で読めない（2026年11月7日、作者の PC で確かめた） |

### 方針の変更

| 対象 | 決定 |
| --- | --- |
| 方針の指紋 | `Config.fingerprint` の中身は、抽出の版を除いて変えない。OCR の設定も含めたままにする。分割は抽出した本文から作るので、OCR の設定が変われば索引も作り直す |
| 方針が変わった索引 | wiki ごとの索引の `policy.json` の指紋が今の設定と違うとき、取り込みは止めず、その wiki の索引を空にしてから取り込む。台帳の文書は、今の方針で取り込んだものとみなさない（同じ内容でも埋め込み直す）。空にするのは、LanceDB の表 `chunks`、`index-state.json`、`catalog.sqlite` の `documents`、`locations`、`citations`、`jobs` の行である。そのあと、今の方針で `policy.json` を書き直す。古い索引は、モデルの次元や分割が違うので、今の設定では検索にも使えない |
| 取り込み直しの一覧 | 索引を空にする前に、取り込み済みだった文書の SHA-256、題名、場所、ソースのページを `previous-index.json` に残す。すでに一覧があれば（取り込み直しの途中でもう一度設定を変えたとき）、今の台帳の文書と合わせる。同じ文書は、場所とソースのページの和をとる。`status` は、取り込み直すべき PDF の一覧を `reingest` で、あるかどうかを `reingest_required` で返す。方針が変わった索引では台帳の文書と一覧の文書を、空にしたあとは一覧の文書のうち、まだ取り込み直していない場所を返す。場所ごとに見るのは、同じ内容を 2 か所で登録していたとき、片方を取り込み直しても、もう片方の場所を失わないためである。台帳に載った場所（別の版を取り込んだ場所を含む）と、もうない場所は外す。場所が残らない文書は外す。取り込みのたびに一覧を書き直し、すべて外れたら `previous-index.json` を消す |
| 取り込み直したときの出典 | 一覧にある文書を取り込み直したら、空にする前にその文書を出典にしていたソースのページを `citations` に戻す。版が変わったときの要再確認の印が、取り込み直しのときに使ったページだけにならないようにする |
| 空にする順番 | 抽出が済み、最初のバッチの埋め込みが済んでから空にする。抽出、OCR、モデルの取得や読み込みに失敗したときは、前の索引を残すので、設定を戻せばそのまま使える。モデルを変える場面は、モデルの取得に失敗しやすい。一覧を書いてから台帳の行を消し、LanceDB の表を消し、最後に `policy.json` を書き直す。途中で止まっても、`policy.json` が古いままなので、次の取り込みでもう一度空にする。一覧は合わせて書くので失われない |
| 要再確認の印 | 空にしたあとは、ある場所の前の版を台帳で引けない。取り込んだ場所が一覧の別の版の場所に含まれていれば、その版を出典にしていたページに要再確認の印を付ける（ADR-0013 の版の更新と同じ） |
| 方針が変わった索引の検索 | 方針が変わった索引を空にする前の検索は、「設定が変わったので、PDF を取り込み直すまで検索できない」と伝えて止める。空にしたあとは、取り込み直した文書だけを検索する |
| 再利用 | 取り込み直すとき、抽出の設定が前と同じなら、`page-*.json` を読み直すだけで、OCR も抽出もしない。埋め込みと索引だけを作り直す |

### 後始末

| 対象 | 決定 |
| --- | --- |
| 古い版の索引 | 0.4.0 と同じく、古い版の文書を消すときは、その版の索引の行と、埋め込みの途中経過（`catalog.sqlite` の `jobs` の行）を消す。途中経過を消すのは、内容を古い版に戻して取り込んだとき、埋め込みを飛ばして索引に何も入らないことを防ぐためである（ADR-0013） |
| 古い版の抽出の結果 | `<data_dir>/extracted/<SHA-256>/`（すべての抽出の設定の分）を消すのは、同じ `data_dir` のどの wiki の `documents` にもなく、どの wiki でも取り込み直しを待っていない（`status` の `reingest` にない）ときだけにする。ほかの wiki が使っている結果や、取り込み直しを待っている結果は残す。消す機会は 2 つある。古い版を台帳から消したときと、取り込み直しの一覧から文書が外れたとき（空にしたあとで別の版に置き換えられたとき）である |
| 抽出の設定を変えたとき | 前の設定の抽出の結果は、その文書を消すまで残す。設定を戻したときに使い回せる |
| 0.4.0 の抽出の結果 | 新しい置き場所に結果がなく、0.4.0 の置き場所（`<wiki の作業領域>/extracted/<generation>/`）に結果があれば、新しい置き場所に移す。`generation` は、今の指紋で作ったものと、前の方針のうち埋め込みのモデルだけが違うものの指紋で作ったものを探す。前の方針は、`policy.json`（空にする前）と、`previous-index.json` に残した空にした索引の方針（空にしたあと）である。今の設定のモデルを前の方針のモデルに替えた指紋が、前の方針の指紋と一致するときだけ使う。移す途中で止まったときは、次の取り込みで、まだ移していないファイルを移す。どちらも、抽出の設定が今と同じであることが指紋から分かる。0.4.0 の索引と台帳は、置き場所も形も変えないので、そのまま使う。古い版を消すときは、0.4.0 の置き場所に残った結果も消す |

### `/rag:setup`

| 対象 | 決定 |
| --- | --- |
| `configure` の引数 | `ocr_mode`（`auto`、`always`、`off`）と `ocr_dpi`（72〜300）を足す。値の確かめは今の `Config` のとおりである |
| `configure` の結果 | 指紋が変わったかを `reingest_required`、抽出の設定が変わったかを `extraction_changed` として返す。`data_dir` を変えたときは、前の保存先の索引も抽出の結果も引き継がないので、どちらも `true` にする |
| 説明 | 埋め込みのモデルを変えると、取り込み済みの PDF の入れ直しが要るが、OCR はやり直さない。`ocr_mode` か `ocr_dpi` を変えると、入れ直しのときに OCR もやり直す。`/rag:setup` は変える前にこれを説明する |

## 理由

- OCR は rag でいちばん重い処理で、結果は埋め込みの方式によらない。ADR-0012 の移行で索引の持ち主が変わっても、抽出の結果はそのまま使える。
- 抽出の結果を wiki ごとでなく `data_dir` で共有するのは、同じ PDF を複数の wiki に取り込む使い方があり、`data_dir` ごとにワーカーが 1 つなので、共有しても書き込みが競合しないからである。`data_dir` は PC ごとの派生データの置き場所で、wiki の外にある。
- 方針が変わった索引を、次の取り込みで空にするのは、古い索引が今の設定ではもう使えないからである。別のフォルダーに方針ごとの索引を残す案より、0.4.0 の索引の置き場所と形を変えずに済み、使えない索引が残り続けることもない。
- `previous-index.json` を残すのは、索引を空にしたあと、どの PDF を取り込み直せばよいかを利用者が見失わないためである。
- 空にするのを最初のバッチの埋め込みのあとまで待つのは、埋め込みが動くと分かる前に空にすると、モデルの取得の失敗だけで、設定を戻しても使えない索引が残るからである（Claude による暫定の敵対的レビューで、試験で確かめた）。

## 検討した選択肢

| 選択肢 | 判断 |
| --- | --- |
| 抽出の結果を `data_dir` で共有し、方針が変わった索引は次の取り込みで空にする | 採る |
| 抽出の結果を wiki ごとの作業領域に置いたまま、鍵だけを変える | 採らない。同じ PDF を 2 つの wiki に取り込むと OCR を 2 回する。後始末は簡単になる |
| 方針ごとに索引のフォルダーを分ける（`wikis-v2/<wiki>/<指紋>/`） | 採らない。設定を戻したときに古い索引をすぐ使えるが、使えない索引が残り続け、0.4.0 の索引を移す手順が要る |
| `configure` で方針が変わったときに、すべての wiki の索引を空にする | 採らない。取り込み直す前に設定を戻すこともありうる。取り込みの時まで待てば、wiki ごとに空にできる |
| 方針が変わった索引では、今までどおり取り込みを止める | 採らない。モデルを変えるには `data_dir` も変えるしかなく、抽出の結果を使い回せない |
| `ocr_mode` が違っても、OCR しなかったページの結果は使い回す | 採らない。ページごとに判定が要り、鍵が複雑になる。`ocr_mode` を変えることはまれである |

## 影響

- rag: `scripts/rag_config.py`（`EXTRACT_REVISION`、抽出の設定の鍵）、`scripts/rag_index.py`（抽出の結果の置き場所、0.4.0 の結果の移し替え、方針が変わった索引を空にすること、`previous-index.json`、後始末）、`scripts/rag_server.py`（`configure` の引数と結果、`status`）、`commands/setup.md`、`commands/status.md`、`README.md`、`CHANGELOG.md`、`plugin.json`。
- 開発リポジトリの試験: `tests/rag/verify_pipeline.py` は、抽出の結果の置き場所を新しいものに合わせる。`tests/rag/test_jobs.py` に、次の試験を足す。
  - 埋め込みのモデルを変えて取り込み直すと、`page-*.json` を書き直さず、抽出も呼ばない
  - `ocr_dpi` を変えると、別の置き場所に抽出し直し、前の結果は残る
  - 同じ PDF を 2 つの wiki に取り込むと、抽出は 1 回だけ呼ばれる
  - 古い版の文書を wiki A から消しても、wiki B が同じ版を使っていれば、抽出の結果は残る。どちらからも消えたら、抽出の結果も消える
  - 方針が変わった索引では、取り込む前の検索が止まり、`status` が取り込み直す PDF を返す。取り込み直すと、その一覧から外れる
  - 0.4.0 の置き場所の抽出の結果を、新しい置き場所に移して使う
  - `configure` が `ocr_mode` と `ocr_dpi` を受け付け、範囲の外の値を拒む
  - モデルを変えたあとの最初の埋め込みが失敗しても、設定を戻せば前の索引を検索できる
  - 取り込み直した版を置き換えたときと、空にしたあとで前の版を置き換えたときに、前の版の抽出の結果を消す
  - 2 回続けて設定を変えても、取り込み直しの一覧のソースのページが減らない
  - モデルを変えたあとでも、0.4.0 の置き場所の抽出の結果を使う
  - 指紋の値が 0.4.0 と変わらない
  - モデルを変えて索引を空にしたあとの 2 件目以降でも、0.4.0 の抽出の結果を使う
  - 0.4.0 の抽出の結果を移す途中で止まっても、次の取り込みで残りを移す
  - 抽出の版を上げると、方針が変わった索引になり、取り込み直すと新しい抽出で索引を作り直す。前の版の埋め込みの途中経過を使い回さず、0.4.0 の抽出の結果を新しい版の結果として移さない
  - 同じ内容を 2 か所で登録していたとき、片方を取り込み直しても、もう片方が取り込み直しの一覧に残る
- 全量の OCR の途中経過（`docs/research/rag-full-pipeline-2026-11-04/`）は、0.3.0 の方針の指紋で作られているので、この決定でも製品の経路からは使えない。全量の OCR は、この決定を実装した版で始め直す。
- `data_dir` を変えると、抽出の結果も新しい `data_dir` には引き継がない。これは今までと同じである。

## 残した制約

- 0.4.0 の抽出の結果を探すのは、方針の違いが埋め込みのモデルだけのときである。分割の設定（`chunk_chars`、`chunk_overlap`）も変えたときは、前の指紋を再現できないので見つけられず、OCR をやり直す（Sol のレビューの軽微な指摘）。
- 後始末は、文書のロックを待たずに取る。取れなかったとき（ほかの取り込みがその文書を使っているとき）は消さずに残し、あとで消し直す仕組みはない。製品の経路ではワーカーが 1 つなので、この競合は起きない。
- 0.4.0 の置き場所の結果を後始末するときも、指紋を再現できる方針のものだけを消す。

## 見直す条件

- ADR-0012 の移行で、索引と台帳の持ち主が変わり、`documents` を数える場所が変わったとき（抽出の結果の後始末の条件を合わせる）。
- 複数のワーカーが同じ `data_dir` を同時に使うようになったとき。
- 抽出の設定ごとの結果が、ディスクを無視できないほど使うようになったとき。

## 参照

- `info-hive-rag/scripts/rag_index.py`（`Engine._check_policy()`、`Engine.ingest_pdf()`）
- `info-hive-rag/scripts/rag_pdf.py`（`extract_pages()`、`inspect_page()`）
- `info-hive-rag/scripts/rag_config.py`（`Config.fingerprint`）

## tests/rag/test_extraction.py の本文（今）

```python
"""抽出と OCR の結果を、埋め込みと分割の方針から切り離して保存する（ADR-0014）回帰試験。"""
import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "info-hive-rag/scripts"))
import rag_pdf
from rag_config import MODELS, Config, write_json
from rag_index import Engine


class FakeEmbedder:
    def __init__(self, dimension):
        self.dimension = dimension

    def encode(self, texts, **_):
        import numpy as np
        return np.tile(np.asarray([1.] + [0.] * (self.dimension - 1), dtype=np.float32), (len(texts), 1))


class ExtractionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get("RAG_TEST_RUN_ROOT", str(ROOT / ".rag-poc-data")),
                                                ignore_cleanup_errors=True)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / "refs" / "資料.pdf"
        self.source.parent.mkdir()
        self.make_pdf(self.source, "Extraction cache checkpoint")
        self.wiki = self.make_wiki("wiki")
        self.values = {"data_dir": str(self.root / "data"), "embedding_model": "cl-nagoya/ruri-v3-30m",
                       "ocr_mode": "off", "batch_size": 4}
        # 抽出（ページの判定）が呼ばれた回数を数える。キャッシュを使えば呼ばれない。
        self.inspected = 0
        original = rag_pdf.inspect_page

        def counting(page):
            self.inspected += 1
            return original(page)
        patcher = patch.object(rag_pdf, "inspect_page", counting)
        patcher.start()
        self.addCleanup(patcher.stop)

    def make_wiki(self, name):
        wiki = self.root / name
        (wiki / "sources").mkdir(parents=True)
        (wiki / "SCHEMA.md").write_text("# 検証\n", encoding="utf-8")
        return wiki

    @staticmethod
    def make_pdf(path, text, pages=3):
        from reportlab.pdfgen import canvas
        pdf = canvas.Canvas(str(path))
        for number in range(pages):
            pdf.drawString(40, 700, text + " " + str(number))
            pdf.showPage()
        pdf.save()

    def engine(self, **changes):
        config = Config({**self.values, **changes})
        return Engine(config, embedder=FakeEmbedder(MODELS[config.model]))

    def ingest(self, engine, wiki=None, source=None):
        return engine.ingest_pdf(str(wiki or self.wiki), str(source or self.source), "sources/資料.md")

    def pages(self, engine, doc_id):
        return sorted(engine.config.extraction_dir(doc_id).glob("page-*.json"))

    def test_fingerprint_is_unchanged_from_0_4_0(self):
        # 指紋の中身を変えると、すべての利用者の索引が方針の変わった索引になる（ADR-0014）。変えるときはこの値も直す。
        self.assertEqual(Config({"data_dir": str(self.root / "data")}).fingerprint,
                         "1c61f7d933f39d12ba198703de5b65c8a88110116a91f9b619395ce5cbdfc909")

    def test_cache_lives_in_data_dir_and_is_keyed_by_extraction_settings(self):
        engine = self.engine()
        result = self.ingest(engine)
        cache = engine.config.extraction_dir(result["sha256"])
        self.assertEqual(cache.parent.parent, engine.config.data_dir / "extracted")
        self.assertEqual(cache.parent.name, result["sha256"])
        self.assertEqual(len(self.pages(engine, result["sha256"])), 3)
        self.assertEqual(Path(result["extracted_markdown"]), cache / "document.md")
        # 埋め込みのモデルと分割は鍵に入らない。抽出の設定は入る。
        self.assertEqual(Config({**self.values, "embedding_model": "cl-nagoya/ruri-v3-70m", "chunk_chars": 500}).extraction_key,
                         engine.config.extraction_key)
        self.assertNotEqual(Config({**self.values, "ocr_dpi": 200}).extraction_key, engine.config.extraction_key)
        self.assertNotEqual(Config({**self.values, "ocr_mode": "auto"}).extraction_key, engine.config.extraction_key)

    def test_model_change_reuses_extraction_and_resets_the_index(self):
        first = self.engine()
        result = self.ingest(first)
        stamps = {page.name: page.stat().st_mtime_ns for page in self.pages(first, result["sha256"])}
        self.assertEqual(self.inspected, 3)
        second = self.engine(embedding_model="cl-nagoya/ruri-v3-70m")
        # 取り込み直す前は、方針が変わった索引で検索しない。status は取り込み直す PDF を返す。
        with self.assertRaisesRegex(ValueError, "取り込み直"):
            second.search(str(self.wiki), "Extraction cache", limit=3)
        state = second.status(str(self.wiki))
        self.assertTrue(state["reingest_required"])
        self.assertEqual([item["sha256"] for item in state["reingest"]], [result["sha256"]])
        self.assertEqual(state["reingest"][0]["paths"], [self.source.as_posix()])
        again = self.ingest(second)
        self.assertEqual(again["status"], "indexed")
        self.assertTrue(again["index_reset"])
        self.assertEqual(self.inspected, 3)  # 抽出し直していない
        self.assertEqual({page.name: page.stat().st_mtime_ns for page in self.pages(second, result["sha256"])}, stamps)
        found = second.search(str(self.wiki), "Extraction cache checkpoint", limit=3)["results"]
        self.assertTrue(found and all(row["sha256"] == result["sha256"] for row in found))
        state = second.status(str(self.wiki))
        self.assertFalse(state["reingest_required"])
        self.assertEqual(state["reingest"], [])
        self.assertEqual(state["documents"], 1)

    def test_reset_keeps_the_list_of_documents_to_reingest(self):
        other = self.root / "refs" / "別の資料.pdf"
        self.make_pdf(other, "Another document entirely")
        first = self.engine()
        kept = self.ingest(first)
        waiting = first.ingest_pdf(str(self.wiki), str(other), "sources/別の資料.md")
        second = self.engine(embedding_model="cl-nagoya/ruri-v3-70m")
        self.ingest(second)  # 索引を空にしてから、1 件目だけ取り込み直す
        state = second.status(str(self.wiki))
        self.assertTrue(state["reingest_required"])
        self.assertEqual([item["sha256"] for item in state["reingest"]], [waiting["sha256"]])
        self.assertEqual(state["reingest"][0]["source_pages"], ["sources/別の資料.md"])
        # 取り込み直しを待つ文書の抽出の結果は、残っている。
        self.assertTrue(self.pages(second, waiting["sha256"]))
        results = second.search(str(self.wiki), "Another document entirely", limit=5)["results"]
        self.assertTrue(all(row["sha256"] == kept["sha256"] for row in results))
        second.ingest_pdf(str(self.wiki), str(other), "sources/別の資料.md")
        self.assertEqual(second.status(str(self.wiki))["reingest"], [])
        self.assertFalse((second.config.workspace(str(self.wiki)) / "previous-index.json").exists())

    def test_ocr_setting_change_extracts_again_and_keeps_the_previous_result(self):
        first = self.engine()
        result = self.ingest(first)
        previous = first.config.extraction_dir(result["sha256"])
        second = self.engine(ocr_dpi=200)
        self.ingest(second)
        self.assertEqual(self.inspected, 6)
        current = second.config.extraction_dir(result["sha256"])
        self.assertNotEqual(previous, current)
        self.assertEqual(len(list(previous.glob("page-*.json"))), 3)
        self.assertEqual(len(list(current.glob("page-*.json"))), 3)

    def test_same_pdf_in_two_wikis_is_extracted_once(self):
        engine = self.engine()
        other = self.make_wiki("other")
        first = self.ingest(engine)
        second = self.ingest(engine, wiki=other)
        self.assertEqual(first["sha256"], second["sha256"])
        self.assertEqual(second["status"], "indexed")
        self.assertEqual(self.inspected, 3)
        self.assertEqual(first["extracted_markdown"], second["extracted_markdown"])

    def test_old_version_cache_is_removed_only_when_no_wiki_uses_it(self):
        engine = self.engine()
        other = self.make_wiki("other")
        copy = self.root / "refs" / "写し.pdf"
        copy.write_bytes(self.source.read_bytes())
        old = self.ingest(engine)
        engine.ingest_pdf(str(other), str(copy), "sources/資料.md")
        self.make_pdf(self.source, "Second edition")
        self.ingest(engine)  # wiki から古い版が消える。other はまだ使っている
        self.assertTrue(self.pages(engine, old["sha256"]))
        self.make_pdf(copy, "Third edition")
        engine.ingest_pdf(str(other), str(copy), "sources/資料.md")
        self.assertFalse(engine.config.extraction_dir(old["sha256"]).exists())
        self.assertFalse((engine.config.data_dir / "extracted" / old["sha256"]).exists())

    def test_cleanup_removes_caches_of_every_extraction_setting(self):
        first = self.engine()
        old = self.ingest(first)
        self.ingest(self.engine(ocr_dpi=200), wiki=self.make_wiki("other"))
        self.make_pdf(self.source, "Second edition")
        self.ingest(first)
        # other は ocr_dpi=200 の指紋で同じ版を使っているので、まだ残る。
        self.assertTrue((first.config.data_dir / "extracted" / old["sha256"]).exists())

    def test_extraction_from_0_4_0_is_moved_and_reused(self):
        engine = self.engine()
        data = self.source.read_bytes()
        doc_id = hashlib.sha256(data).hexdigest()
        generation = hashlib.sha256((doc_id + engine.config.fingerprint).encode("ascii")).hexdigest()
        legacy = engine.config.workspace(str(self.wiki)) / "extracted" / generation
        rag_pdf.extract_pages(data, engine.config, legacy)
        self.assertEqual(self.inspected, 3)
        result = self.ingest(engine)
        self.assertEqual(self.inspected, 3)
        self.assertEqual(len(self.pages(engine, doc_id)), 3)
        self.assertFalse(legacy.exists())
        self.assertEqual(result["pages"], 3)

    def test_failed_embedding_after_model_change_keeps_the_old_index(self):
        first = self.engine()
        result = self.ingest(first)
        second = self.engine(embedding_model="cl-nagoya/ruri-v3-70m")

        class Broken:
            def encode(self, texts, **_):
                raise RuntimeError("モデルを取得できない")
        second._embedder = Broken()
        with self.assertRaisesRegex(RuntimeError, "モデルを取得できない"):
            self.ingest(second)
        # 設定を戻せば、前の索引をそのまま使える。
        again = self.engine()
        self.assertEqual(again.status(str(self.wiki))["documents"], 1)
        self.assertFalse(again.status(str(self.wiki))["reingest_required"])
        found = again.search(str(self.wiki), "Extraction cache checkpoint", limit=3)["results"]
        self.assertTrue(found and all(row["sha256"] == result["sha256"] for row in found))

    def test_reingested_then_replaced_version_cache_is_removed(self):
        other = self.root / "refs" / "別の資料.pdf"
        self.make_pdf(other, "Another document entirely")
        first = self.engine()
        old = self.ingest(first)
        first.ingest_pdf(str(self.wiki), str(other), "sources/別の資料.md")
        second = self.engine(embedding_model="cl-nagoya/ruri-v3-70m")
        self.ingest(second)  # 空にして、1 件目を取り込み直す。別の資料は取り込み直しを待つ
        self.make_pdf(self.source, "Second edition")
        self.ingest(second)  # 取り込み直した版を置き換える
        self.assertFalse((second.config.extraction_root / old["sha256"]).exists())

    def test_version_replaced_after_reset_is_dropped_and_its_cache_removed(self):
        first = self.engine()
        old = self.ingest(first)
        self.make_pdf(self.source, "Edited while the model changed")
        second = self.engine(embedding_model="cl-nagoya/ruri-v3-70m")
        new = self.ingest(second)
        self.assertNotEqual(old["sha256"], new["sha256"])
        state = second.status(str(self.wiki))
        self.assertEqual(state["reingest"], [])
        self.assertFalse((second.config.workspace(str(self.wiki)) / "previous-index.json").exists())
        self.assertFalse((second.config.extraction_root / old["sha256"]).exists())

    def test_two_changes_in_a_row_keep_every_source_page(self):
        first = self.engine()
        first.ingest_pdf(str(self.wiki), str(self.source), "sources/資料.md")
        first.ingest_pdf(str(self.wiki), str(self.source), "sources/別のページ.md")
        other = self.root / "refs" / "別の資料.pdf"
        self.make_pdf(other, "Another document entirely")
        first.ingest_pdf(str(self.wiki), str(other), "sources/別の資料.md")
        second = self.engine(embedding_model="cl-nagoya/ruri-v3-70m")
        second.ingest_pdf(str(self.wiki), str(self.source), "sources/資料.md")  # 空にして 1 件だけ取り込み直す
        third = self.engine(embedding_model="cl-nagoya/ruri-v3-130m")
        state = third.status(str(self.wiki))
        pages = {item["sha256"]: item["source_pages"] for item in state["reingest"]}
        self.assertEqual(len(pages), 2)
        third.ingest_pdf(str(self.wiki), str(other), "sources/別の資料.md")  # もう一度空にする
        item = [item for item in third.status(str(self.wiki))["reingest"]][0]
        self.assertEqual(item["source_pages"], ["sources/別のページ.md", "sources/資料.md"])

    def test_extraction_from_0_4_0_is_reused_after_a_model_change(self):
        first = self.engine()
        data = self.source.read_bytes()
        doc_id = hashlib.sha256(data).hexdigest()
        result = self.ingest(first)
        # 0.4.0 の置き場所に戻す（0.4.0 で取り込んだ状態を作る）。
        generation = hashlib.sha256((doc_id + first.config.fingerprint).encode("ascii")).hexdigest()
        legacy = first.config.workspace(str(self.wiki)) / "extracted" / generation
        legacy.parent.mkdir(parents=True)
        os.replace(first.config.extraction_dir(doc_id), legacy)
        second = self.engine(embedding_model="cl-nagoya/ruri-v3-70m")
        self.ingest(second)
        self.assertEqual(self.inspected, 3)
        self.assertEqual(len(self.pages(second, result["sha256"])), 3)
        self.assertFalse(legacy.exists())

    def legacy_layout(self, engine, *sources):
        """取り込んだ文書の抽出の結果を、0.4.0 の置き場所に戻す（0.4.0 で取り込んだ状態を作る）。"""
        for source in sources:
            doc_id = hashlib.sha256(source.read_bytes()).hexdigest()
            generation = hashlib.sha256((doc_id + engine.config.fingerprint).encode("ascii")).hexdigest()
            legacy = engine.config.workspace(str(self.wiki)) / "extracted" / generation
            legacy.parent.mkdir(parents=True, exist_ok=True)
            os.replace(engine.config.extraction_dir(doc_id), legacy)

    def test_every_0_4_0_extraction_is_reused_after_a_model_change(self):
        other = self.root / "refs" / "別の資料.pdf"
        self.make_pdf(other, "Another document entirely")
        first = self.engine()
        self.ingest(first)
        first.ingest_pdf(str(self.wiki), str(other), "sources/別の資料.md")
        self.legacy_layout(first, self.source, other)
        second = self.engine(embedding_model="cl-nagoya/ruri-v3-70m")
        self.ingest(second)  # 1 件目で索引を空にする。2 件目は空にしたあとの取り込み
        second.ingest_pdf(str(self.wiki), str(other), "sources/別の資料.md")
        self.assertEqual(self.inspected, 6)  # 最初の 2 件の取り込みだけ。取り込み直しでは抽出しない
        self.assertFalse((second.config.workspace(str(self.wiki)) / "extracted").exists())

    def test_interrupted_move_of_0_4_0_extraction_is_finished(self):
        engine = self.engine()
        result = self.ingest(engine)
        self.legacy_layout(engine, self.source)
        legacy = next((engine.config.workspace(str(self.wiki)) / "extracted").iterdir())
        cache = engine.config.extraction_dir(result["sha256"])
        cache.mkdir(parents=True)
        os.replace(legacy / "page-000001.json", cache / "page-000001.json")  # 1 ページだけ移して止まった
        (engine.config.workspace(str(self.wiki)) / "catalog.sqlite").unlink()  # 取り込み直させる
        for name in ("lance", "index-state.json"):
            path = engine.config.workspace(str(self.wiki)) / name
            shutil.rmtree(path) if path.is_dir() else path.unlink()
        self.ingest(engine)
        self.assertEqual(self.inspected, 3)
        self.assertEqual(len(self.pages(engine, result["sha256"])), 3)
        self.assertFalse(legacy.exists())

    def test_raising_the_extraction_revision_reindexes_with_the_new_extraction(self):
        engine = self.engine()
        self.ingest(engine)
        with patch("rag_config.EXTRACT_REVISION", "extract-v2"):
            # 抽出の版を上げると、方針が変わった索引になる。取り込み直すまで前の抽出で検索しない。
            self.assertTrue(engine.status(str(self.wiki))["reingest_required"])
            with self.assertRaisesRegex(ValueError, "取り込み直"):
                engine.search(str(self.wiki), "Extraction cache checkpoint", limit=3)
            again = self.ingest(engine)
            self.assertEqual(again["status"], "indexed")
            self.assertTrue(again["index_reset"])
            self.assertIn("extract-v2", again["extracted_markdown"])
            self.assertTrue(Path(again["extracted_markdown"]).is_file())
            self.assertEqual(self.inspected, 6)
            found = engine.search(str(self.wiki), "Extraction cache checkpoint", limit=3)["results"]
            self.assertTrue(found)

    def test_same_content_at_two_paths_stays_in_the_list_until_both_are_reingested(self):
        copy = self.root / "refs" / "写し.pdf"
        copy.write_bytes(self.source.read_bytes())
        first = self.engine()
        self.ingest(first)
        first.ingest_pdf(str(self.wiki), str(copy), "sources/写し.md")
        second = self.engine(embedding_model="cl-nagoya/ruri-v3-70m")
        self.ingest(second)
        state = second.status(str(self.wiki))
        self.assertTrue(state["reingest_required"])
        self.assertEqual([item["paths"] for item in state["reingest"]], [[copy.as_posix()]])
        second.ingest_pdf(str(self.wiki), str(copy), "sources/写し.md")
        self.assertEqual(second.status(str(self.wiki))["reingest"], [])

    def test_0_4_0_extraction_is_not_adopted_after_raising_the_extraction_revision(self):
        engine = self.engine()
        self.ingest(engine)
        self.legacy_layout(engine, self.source)
        workspace = engine.config.workspace(str(self.wiki))
        (workspace / "catalog.sqlite").unlink()  # 0.4.0 の結果だけが残った状態で取り込み直させる
        for name in ("lance", "index-state.json"):
            path = workspace / name
            shutil.rmtree(path) if path.is_dir() else path.unlink()
        with patch("rag_config.EXTRACT_REVISION", "extract-v2"):
            result = self.ingest(engine)
            self.assertEqual(self.inspected, 6)  # 0.4.0 の結果を新しい版として使わず、抽出し直した
            self.assertEqual(len(self.pages(engine, result["sha256"])), 3)
            self.assertIn("extract-v2", result["extracted_markdown"])

    def test_embedding_checkpoint_is_not_reused_after_raising_the_extraction_revision(self):
        import numpy as np

        class Counting(FakeEmbedder):
            def __init__(self):
                super().__init__(256)
                self.texts = 0

            def encode(self, texts, **_):
                self.texts += len(texts)
                return super().encode(texts)
        engine = Engine(Config({**self.values, "batch_size": 1}), embedder=Counting())

        def stop(phase, completed, total):
            if phase == "埋め込み" and completed == 1:
                raise RuntimeError("最初のバッチのあとで止まった")
        with self.assertRaisesRegex(RuntimeError, "止まった"):
            engine.ingest_pdf(str(self.wiki), str(self.source), "sources/資料.md", progress=stop)
        engine._embedder.texts = 0
        with patch("rag_config.EXTRACT_REVISION", "extract-v2"):
            result = self.ingest(engine)
            self.assertEqual(engine._embedder.texts, result["chunks"])  # 前の版の途中経過を飛ばさない
            generation = engine.config.generation(result["sha256"])
        rows = engine._table(engine.config.workspace(str(self.wiki))).search().where(
            f"generation = '{generation}'").limit(100).to_list()
        self.assertEqual(len(rows), result["chunks"])

    def test_0_4_0_extraction_of_a_version_replaced_after_reset_is_removed(self):
        first = self.engine()
        self.ingest(first)
        self.legacy_layout(first, self.source)
        legacy = first.config.workspace(str(self.wiki)) / "extracted"
        self.make_pdf(self.source, "Edited while the model changed")
        self.ingest(self.engine(embedding_model="cl-nagoya/ruri-v3-70m"))
        self.assertFalse(legacy.exists())

    def test_restoring_old_content_after_cleanup_extracts_again(self):
        engine = self.engine()
        original = self.source.read_bytes()
        first = self.ingest(engine)
        self.make_pdf(self.source, "Second edition")
        self.ingest(engine)
        self.source.write_bytes(original)
        again = self.ingest(engine)
        self.assertEqual(again["sha256"], first["sha256"])
        self.assertEqual(again["status"], "indexed")
        table = engine._table(engine.config.workspace(str(self.wiki)))
        rows = table.search().where(f"doc_id = '{first['sha256']}'").limit(100).to_list()
        self.assertEqual(len(rows), again["chunks"])


class ConfigureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get("RAG_TEST_RUN_ROOT", str(ROOT / ".rag-poc-data")),
                                                ignore_cleanup_errors=True)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.config_file = self.root / "config.json"
        write_json(self.config_file, {"data_dir": str(self.root / "data"), "embedding_model": "cl-nagoya/ruri-v3-30m"})
        patcher = patch.dict(os.environ, {"INFO_HIVE_RAG_CONFIG": str(self.config_file)})
        patcher.start()
        self.addCleanup(patcher.stop)
        import rag_server
        self.server = rag_server
        # 試験ではワーカーを起動しない。
        host = patch.object(rag_server, "WorkerHost")
        host.start()
        self.addCleanup(host.stop)
        for name in ("_engine", "_config", "_jobs", "_host"):
            setattr(rag_server, name, None)

    def saved(self):
        return json.loads(self.config_file.read_text(encoding="utf-8"))

    def test_ocr_settings_can_be_changed(self):
        result = self.server.configure(ocr_mode="always", ocr_dpi=200)
        self.assertEqual(self.saved()["ocr_mode"], "always")
        self.assertEqual(self.saved()["ocr_dpi"], 200)
        self.assertEqual((result["ocr_mode"], result["ocr_dpi"]), ("always", 200))
        self.assertTrue(result["reingest_required"])
        self.assertTrue(result["extraction_changed"])

    def test_model_change_needs_reingest_but_not_extraction(self):
        result = self.server.configure(embedding_model="cl-nagoya/ruri-v3-70m")
        self.assertTrue(result["reingest_required"])
        self.assertFalse(result["extraction_changed"])

    def test_data_dir_change_needs_reingest(self):
        result = self.server.configure(data_dir=str(self.root / "elsewhere"))
        self.assertTrue(result["reingest_required"])
        self.assertTrue(result["extraction_changed"])

    def test_retrieval_change_needs_nothing(self):
        result = self.server.configure(retrieval={"search_nprobes": 30})
        self.assertFalse(result["reingest_required"])
        self.assertFalse(result["extraction_changed"])
        self.assertNotIn("ocr_mode", self.saved())

    def test_invalid_ocr_settings_are_rejected_and_not_saved(self):
        for values in ({"ocr_mode": "sometimes"}, {"ocr_mode": ""}, {"ocr_dpi": 0}, {"ocr_dpi": 71}, {"ocr_dpi": 301}):
            with self.assertRaises(ValueError):
                self.server.configure(**values)
        self.assertNotIn("ocr_mode", self.saved())
        self.assertNotIn("ocr_dpi", self.saved())


if __name__ == "__main__":
    unittest.main()
```
