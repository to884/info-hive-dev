# info-hive-rag のアーキテクチャの根拠

- info-hive-rag の対象は親リポジトリが参照する 4fabe3294d86a367e635bc18635af6e7132a8d93（プラグイン定義の版は 0.5.3）。
- 連携先の手順は info-hive-wiki v0.38.1（b8596d1888035769528cb74e35bda51c9d9c40a0）。
- 設計時の決定は info-hive-dev の 23abeb19e1fa42cd4d974c99bb9c0d44f5bec000 を参照する。

抜粋はそれぞれ指定した Git コミットのオブジェクトから取得した。リンク先の行番号も同じ版を指す。

## 対象の版と Claude Code の入口

- [info-hive-rag/.claude-plugin/plugin.json 1 行目から](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/.claude-plugin/plugin.json#L1-L10)

````
{
  "name": "rag",
  "version": "0.5.3",
  "description": "wiki@info-hive に依存し、PDF の抽出・OCR・埋め込みを永続ジョブで進め、中断後の再開とローカル検索を提供する Claude Code プラグイン。",
  "dependencies": [
    "wiki@info-hive"
  ],
  "author": {
    "name": "to884"
  },
````

- [info-hive-rag/.mcp.json 1 行目から](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/.mcp.json#L1-L13)

````
{
  "mcpServers": {
    "rag": {
      "command": "uv",
      "args": ["run", "--no-project", "--script", "${CLAUDE_PLUGIN_ROOT}/scripts/rag_server.py"],
      "env": {
        "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONDONTWRITEBYTECODE": "1"
      }
    }
  }
}
````

- [info-hive-rag/CHANGELOG.md 7 行目から](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/CHANGELOG.md#L7-L16)

````
## [Unreleased]

### 内部

- ページの判定（`inspect_page`）を、新しい `scripts/rag_pdf_layer.py` に移しました。wiki の `wiki_pdf_layer.py` と同じ中身のファイルで、pdfminer.six による文字の層の取り出し（距離の同じテキストボックスの組の順を、決まった番号で決める）と、本文の崩れの数え方も含みます（ADR-0025）。取り込みの動きは変えていません。本文は今までどおり PDFium の文字の層で、pdfminer の本文に変えるのは、OCR の結果を分けて保存するのと一緒に行います。

## [0.5.3] - 2026-11-13

### 修正

````

## 受付と永続ジョブ

- [info-hive-rag/scripts/rag_server.py 50 行目から](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/scripts/rag_server.py#L50-L70)

````

def jobs() -> Jobs:
    global _jobs
    if _jobs is None:
        _jobs = Jobs(configuration().data_dir)
    return _jobs


@asynccontextmanager
async def lifespan(_server):
    global _host
    _host = WorkerHost(jobs())
    _host.start()
    try:
        yield {}
    finally:
        if _host:
            _host.close()


server = FastMCP("info-hive-rag", lifespan=lifespan)
````

- [info-hive-rag/scripts/rag_server.py 123 行目から](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/scripts/rag_server.py#L123-L159)

````

@server.tool()
def register_pdf(wiki_root: str, source: str, source_page: str, title: str = "") -> dict:
    """wiki の PDF 取り込みを受け付け、永続ジョブを返す。source は利用者が指定した PDF の絶対パス。queued は索引化完了ではない。原本はコピーしない。"""
    with _lock:
        return jobs().register(configuration(), wiki_root, source, source_page, title)


@server.tool()
def ingest_pdf(wiki_root: str, source: str, source_page: str, title: str = "") -> dict:
    """register_pdf の互換名。ジョブを受け付けて返し、完了は job_status で確認する。"""
    return register_pdf(wiki_root, source, source_page, title)


@server.tool()
async def job_status(wiki_root: str, job_id: str, wait_seconds: int = 0) -> dict:
    """進捗と完了時の抽出 Markdown を返す。wait_seconds=1〜30 で完了を短時間待てる。"""
    if not 0 <= wait_seconds <= 30:
        raise ValueError("wait_seconds は 0〜30 にしてください。")
    deadline = time.monotonic() + wait_seconds
    while True:
        result = jobs().status(wiki_root, job_id)
        if result["status"] in {"completed", "failed", "cancelled"} or time.monotonic() >= deadline:
            return result
        await asyncio.sleep(.1)


@server.tool()
def cancel_job(wiki_root: str, job_id: str) -> dict:
    """明示キャンセルし、次回接続時の自動再開から外す。公開開始後はキャンセルを受理しない。"""
    return jobs().cancel(wiki_root, job_id)


@server.tool()
def retry_job(wiki_root: str, job_id: str) -> dict:
    """失敗またはキャンセルしたジョブを明示的に再試行し、チェックポイントを再利用する。"""
    return jobs().retry(wiki_root, job_id)
````

- [info-hive-rag/scripts/rag_jobs.py 20 行目から](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/scripts/rag_jobs.py#L20-L40)

````
class Jobs:
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir).resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        # 0.3.0 の jobs.sqlite は開かない（ADR-0013）。
        self.path = self.data_dir / "jobs-v2.sqlite"
        with self.connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS ingest_jobs (
                    id TEXT PRIMARY KEY, wiki TEXT NOT NULL, source TEXT NOT NULL,
                    source_page TEXT NOT NULL, title TEXT NOT NULL, size INTEGER, mtime_ns INTEGER,
                    config TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'queued',
                    phase TEXT NOT NULL DEFAULT '受付', completed INTEGER NOT NULL DEFAULT 0,
                    total INTEGER NOT NULL DEFAULT 0, attempts INTEGER NOT NULL DEFAULT 0,
                    owner TEXT, error TEXT, result TEXT, created_at REAL, updated_at REAL,
                    publication_started INTEGER NOT NULL DEFAULT 0, request_key TEXT NOT NULL,
                    dev TEXT, ino TEXT);
                CREATE INDEX IF NOT EXISTS ingest_jobs_request ON ingest_jobs(request_key, status);
                CREATE TABLE IF NOT EXISTS search_requests (
                    id TEXT PRIMARY KEY, config TEXT NOT NULL, wiki TEXT NOT NULL,
````

- [info-hive-rag/scripts/rag_jobs.py 54 行目から](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/scripts/rag_jobs.py#L54-L79)

````

    def register(self, config: Config, wiki_root: str, source: str, source_page: str, title: str = "") -> dict:
        wiki = Path(wiki_root).expanduser().resolve()
        config.workspace(str(wiki))
        path = config.pdf_path(source)
        page = config.source_page(wiki, source_page)
        stat = os.stat(path)
        key = [os.path.normcase(str(wiki)), str(path), stat.st_size, stat.st_mtime_ns,
               config.fingerprint, page, title.strip()]
        request_key = hashlib.sha256(json.dumps(key, ensure_ascii=False).encode("utf-8")).hexdigest()
        now = time.time()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            # 同じ登録が受け付け済みか処理中なら、そのジョブを返す。完了、失敗、キャンセルしかなければ
            # 新しいジョブにする。大きさと更新時刻を変えずに中身を差し替えた PDF も読み直すため（ADR-0013）。
            row = db.execute("""SELECT id FROM ingest_jobs WHERE request_key=?
                AND status IN ('queued','running','paused') ORDER BY created_at DESC LIMIT 1""", (request_key,)).fetchone()
            if row:
                identity = row[0]
            else:
                identity = uuid.uuid4().hex
                db.execute("""INSERT INTO ingest_jobs
                    (id,wiki,source,source_page,title,size,mtime_ns,config,created_at,updated_at,request_key,dev,ino)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (identity, str(wiki), config.pdf_source(source), page, title.strip(), stat.st_size, stat.st_mtime_ns,
                     json.dumps(config.snapshot(), ensure_ascii=False), now, now, request_key, str(stat.st_dev), str(stat.st_ino)))
````

- [info-hive-rag/scripts/rag_jobs.py 117 行目から](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/scripts/rag_jobs.py#L117-L125)

````
        # ワーカーの排他ロックを取得した実行者だけが呼ぶ。
        with self.connect() as db:
            db.execute("UPDATE ingest_jobs SET status='paused',phase='再開待ち',owner=NULL,updated_at=? WHERE status='running'", (time.time(),))
            db.execute("UPDATE search_requests SET status='queued' WHERE status='running'")

    def request_search(self, config: Config, wiki_root: str, query: str, limit: int) -> str:
        config.workspace(wiki_root)
        if not query.strip() or not 1 <= limit <= 50:
            raise ValueError("空でない質問と、1〜50 の limit を指定してください。")
````

- [info-hive-rag/scripts/rag_jobs.py 159 行目から](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/scripts/rag_jobs.py#L159-L206)

````

    def claim(self, owner: str) -> dict | None:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM ingest_jobs WHERE status IN ('queued','paused') ORDER BY created_at LIMIT 1").fetchone()
            if row is None:
                return None
            db.execute("UPDATE ingest_jobs SET status='running',phase='開始',owner=?,attempts=attempts+1,error=NULL,updated_at=? WHERE id=?",
                       (owner, time.time(), row["id"]))
            return dict(row)

    def progress(self, identity: str, owner: str, phase: str, completed: int, total: int):
        with self.connect() as db:
            changed = db.execute("""UPDATE ingest_jobs SET phase=?,completed=?,total=?,updated_at=?
                WHERE id=? AND owner=? AND status='running'""",
                (phase, completed, total, time.time(), identity, owner)).rowcount
        if not changed:
            raise JobCancelled()

    def begin_publication(self, identity: str, owner: str):
        # 公開開始後はキャンセルを受理しない。台帳の切り替えとキャンセルの競合を防ぐ。
        with self.connect() as db:
            changed = db.execute("UPDATE ingest_jobs SET phase='索引の公開',publication_started=1,updated_at=? WHERE id=? AND owner=? AND status='running'",
                                 (time.time(), identity, owner)).rowcount
        if not changed:
            raise JobCancelled()

    def finish(self, identity: str, owner: str, *, result=None, error=None):
        with self.connect() as db:
            db.execute("""UPDATE ingest_jobs SET status=?,phase=?,result=?,error=?,owner=NULL,updated_at=?
                WHERE id=? AND owner=? AND status='running'""",
                ("failed" if error else "completed", "失敗" if error else "完了",
                 json.dumps(result, ensure_ascii=False) if result is not None else None,
                 error, time.time(), identity, owner))

    def pause(self, owner: str):
        with self.connect() as db:
            db.execute("UPDATE ingest_jobs SET status='paused',owner=NULL,updated_at=? WHERE owner=? AND status='running'", (time.time(), owner))

    def cancel(self, wiki_root: str, job_id: str) -> dict:
        current = self.status(wiki_root, job_id)
        with self.connect() as db:
            changed = db.execute("""UPDATE ingest_jobs SET status='cancelled',phase='キャンセル',updated_at=?
                WHERE id=? AND status IN ('queued','paused','running','failed') AND publication_started=0""",
                (time.time(), job_id)).rowcount
        return {**self.status(current["wiki"], job_id), "cancellation_accepted": bool(changed)}

    def retry(self, wiki_root: str, job_id: str) -> dict:
````

- [info-hive-rag/scripts/rag_worker.py 87 行目から](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/scripts/rag_worker.py#L87-L96)

````
def run(data_dir: str):
    jobs = Jobs(Path(data_dir))
    owner = uuid.uuid4().hex
    # 同じ保存先では、複数の MCP 接続があってもモデルを持つワーカーを一つにする。
    try:
        lock = FileLock(str(jobs.data_dir / "worker.lock"), timeout=0)
        lock.acquire()
    except Timeout:
        return

````

- [info-hive-rag/scripts/rag_worker.py 106 行目から](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/scripts/rag_worker.py#L106-L156)

````

    def parent_closed():
        # 親が強制終了してもパイプの EOF を受け取れる。OCR の uv とその子孫も停止する。
        if os.name == "nt":
            # ブロックする CRT の stdin 読み取りと、NumPy 等の DLL 初期化を競合させない。
            while peek(input_handle, None, 0, None, None, None):
                time.sleep(.1)
        else:
            sys.stdin.buffer.read()
        try:
            jobs.pause(owner)
        finally:
            for child in reversed(psutil.Process().children(recursive=True)):
                try:
                    child.kill()
                except psutil.NoSuchProcess:
                    pass
            os._exit(0)

    threading.Thread(target=parent_closed, name="rag-parent-watch", daemon=True).start()
    try:
        jobs.recover()
        engine, engine_key = None, None
        def get_engine(values):
            nonlocal engine, engine_key
            from rag_index import Engine
            config = Config(json.loads(values))
            key = json.dumps(config.snapshot(), sort_keys=True)
            if key != engine_key:
                engine, engine_key = Engine(config), key
            return engine
        while True:
            request = jobs.claim_search()
            if request:
                try:
                    result = get_engine(request["config"]).search(request["wiki"], request["query"], request["result_limit"])
                    jobs.finish_search(request["id"], result=result)
                except Exception as error:
                    jobs.finish_search(request["id"], error=str(error))
                continue
            job = jobs.claim(owner)
            if job is None:
                time.sleep(.02)
                continue
            try:
                source = Path(job["source"])
                stat = source.stat()
                if (stat.st_size, stat.st_mtime_ns) != (job["size"], job["mtime_ns"]):
                    raise ValueError("登録後に PDF が変わりました。新しいジョブで取り込んでください。")
                result = get_engine(job["config"]).ingest_pdf(job["wiki"], job["source"], job["source_page"], job["title"],
                    progress=lambda phase, completed, total: jobs.progress(job["id"], owner, phase, completed, total),
````

## PDF の読み込みとページ抽出

- [info-hive-rag/scripts/rag_index.py 37 行目から](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/scripts/rag_index.py#L37-L80)

````
PDF_HEADER_OFFSET_LIMIT = 1024


def has_pdf_header(data: bytes) -> bool:
    """%PDF- の前にあるバイトが PDF_HEADER_OFFSET_LIMIT バイト以下なら True。

    言い換えると、%PDF- の開始位置（0 始まり）が 0〜PDF_HEADER_OFFSET_LIMIT のどこかであれば True。
    """
    return data.find(b"%PDF-", 0, PDF_HEADER_OFFSET_LIMIT + len(b"%PDF-")) != -1


def read_pdf(path: Path, expected: tuple | None = None) -> tuple[bytes, os.stat_result]:
    """確かめたファイルを 1 回だけ開いて読み、読んだバイト列が PDF であることを確かめる（ADR-0013）。

    expected は登録したときのファイルの (st_dev, st_ino, st_size, st_mtime_ns)。開いたファイルがこれと
    違えば読まない。登録のあとで親のフォルダーが差し替えられても、別のファイルを読まないため。
    """
    before = os.lstat(path)
    try:
        handle = open(path, "rb")
    except OSError as error:
        raise ValueError(f"PDF を開けません（{error.strerror or error}）。") from error
    with handle:
        opened = os.fstat(handle.fileno())
        if not _same_file(before, opened):
            raise ValueError("確かめた PDF と開いたファイルが違います。もう一度取り込んでください。")
        if expected is not None:
            dev, ino, size, mtime_ns = expected
            if (opened.st_size, opened.st_mtime_ns) != (size, mtime_ns) or (
                    ino not in (None, "", "0", 0) and file_id(opened) != (str(dev), str(ino))):
                raise ValueError("登録した PDF と開いたファイルが違います。新しいジョブで取り込んでください。")
        try:
            data = handle.read()
        except OSError as error:
            # OneDrive などのオンラインだけのファイルは、同期のアプリが動いていないと読めない（Errno 22 になる）。
            raise ValueError(f"PDF を読めません（{error.strerror or error}）。OneDrive などのオンラインだけの"
                             "ファイルなら、同期のアプリを起動してから、もう一度取り込んでください。") from error
        after = os.fstat(handle.fileno())
    if not _same_file(opened, after) or len(data) != after.st_size:
        raise ValueError("読み込み中に PDF が変更されました。もう一度取り込んでください。")
    if not has_pdf_header(data):
        raise ValueError(f"PDF の形式ではありません（%PDF- がないか、最初の %PDF- の前に "
                         f"{PDF_HEADER_OFFSET_LIMIT} バイトを超えるバイトがある）。")
    return data, after
````

- [info-hive-rag/scripts/rag_pdf_layer.py 63 行目から](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/scripts/rag_pdf_layer.py#L63-L72)

````
def inspect_page(page) -> tuple[str, dict]:
    """PDFium のページを判定する。返す本文は PDFium の文字の層で、判定の材料と rag の今の本文に使う。"""
    import pypdfium2 as pdfium

    with closing(page.get_textpage()) as textpage:
        text = normalize_newlines(textpage.get_text_range())
        visible = [c for c in text if not c.isspace()]
        bad = sum(c == "\ufffd" or 0xE000 <= ord(c) <= 0xF8FF for c in visible)
        cjk = sum("\u3040" <= c <= "\u30ff" or "\u3400" <= c <= "\u9fff" for c in visible)
        vertical = 0
````

- [info-hive-rag/scripts/rag_pdf.py 17 行目から](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/scripts/rag_pdf.py#L17-L28)

````
def ocr_page(page, config: Config, work: Path, client=None) -> str:
    # 原本ではなく、メモリ上の PDF から描画した一時画像を渡す。
    with tempfile.TemporaryDirectory(prefix="ocr-", dir=work, ignore_cleanup_errors=True) as directory:
        folder = Path(directory)
        image = folder / "page.png"
        bitmap = page.render(scale=config.ocr_dpi / 72)
        try:
            bitmap.to_pil().save(image)
        finally:
            bitmap.close()
        if client is not None:
            return client.recognize(image)['text']
````

- [info-hive-rag/scripts/rag_pdf.py 45 行目から](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/scripts/rag_pdf.py#L45-L103)

````
def extract_pages(data: bytes, config: Config, cache: Path, progress=None) -> list[dict]:
    import pypdfium2 as pdfium

    cache.mkdir(parents=True, exist_ok=True)
    pages = []
    from rag_ocr_client import OcrClient
    with pdfium.PdfDocument(data) as document, OcrClient(config) as ocr:
        for number in range(len(document)):
            saved = cache / f"page-{number + 1:06d}.json"
            if progress:
                progress("PDF の抽出", number, len(document))
            if saved.exists():
                pages.append(json.loads(saved.read_text(encoding="utf-8")))
                continue
            with closing(document[number]) as page:
                text, quality = inspect_page(page)
                needs_ocr = quality["kind"] in {"garbled", "scan", "vertical"} or config.ocr_mode == "always"
                if needs_ocr:
                    if config.ocr_mode == "off":
                        raise ValueError(f"{number + 1} ページ目に OCR が必要です。ocr_mode を auto にしてください。")
                    text = ocr_page(page, config, cache,client=ocr)
                entry = {"page": number + 1, "text": text, "quality": quality, "ocr": needs_ocr,
                         "ocr_empty":needs_ocr and not text.strip()}
                write_json(saved, entry)
                pages.append(entry)
                if progress:
                    progress("PDF の抽出", number + 1, len(document))
    return pages


def chunks_for(pages: list[dict], title: str, config: Config) -> list[dict]:
    import re

    chunks = []
    section = ""
    for page in pages:
        # ページ境界を越えず、見出し・段落・句点の順で分割する。
        blocks = re.split(r"\n\s*\n|(?=^#{1,6}\s)", page["text"], flags=re.M)
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            if re.match(r"^#{1,6}\s", block):
                section = block.splitlines()[0].lstrip("# ")
            start = 0
            while start < len(block):
                end = min(len(block), start + config.chunk_chars)
                if end < len(block):
                    boundary = max(block.rfind(c, start + config.chunk_chars // 2, end) for c in "。！？\n")
                    if boundary >= 0:
                        end = boundary + 1
                text = block[start:end].strip()
                if text:
                    chunks.append({"page": page["page"], "section": section, "text": text,
                                   "embedding_text": f"{title}\n{section}\n{text}"})
                if end == len(block):
                    break
                start = max(start + 1, end - config.overlap)
    return chunks
````

- [info-hive-rag/scripts/rag_ocr.py 1 行目から](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/scripts/rag_ocr.py#L1-L16)

````
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["ndlocr-lite @ git+https://github.com/ndl-lab/ndlocr-lite@e57f7c6bd9cfb3de5f12f008e71ad2122bd44bfd"]
# ///
"""NDLOCR-Lite を初回の OCR 時に取得して CPU で実行する。"""

import os
import sys

os.environ["PYTHONUTF8"] = "1"
for stream in (sys.stdin, sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8")

def serve(threads: int,device: str='cpu'):
    """固定版の OCR モデルを一度だけ初期化し、画像ごとの要求を処理する。"""
````

- [info-hive-rag/scripts/rag_config.py 146 行目から](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/scripts/rag_config.py#L146-L179)

````
    @property
    def extraction_key(self) -> str:
        """抽出の結果の鍵。埋め込みのモデル、分割、題名は入れない（ADR-0014）。"""
        return f"{self.ocr_mode}-{self.ocr_dpi}-{OCR_REVISION[:12]}-{EXTRACT_REVISION}"

    @property
    def extraction_root(self) -> Path:
        """同じ data_dir を使う wiki のあいだで共有する、抽出の結果の置き場所。"""
        return self.data_dir / "extracted"

    def extraction_dir(self, doc_id: str) -> Path:
        return self.extraction_root / doc_id / self.extraction_key

    @property
    def adopts_legacy_extraction(self) -> bool:
        """0.4.0 が wiki ごとに置いた抽出の結果（extract-v1）を、今の抽出の版の結果として使えるなら True。"""
        return EXTRACT_REVISION == LEGACY_EXTRACT_REVISION

    def generation(self, doc_id: str) -> str:
        """索引の行と埋め込みの途中経過の鍵。指紋（抽出の版を含む）が変われば変わるので、前の方針の途中経過を使い回さない。"""
        return hashlib.sha256((doc_id + self.fingerprint).encode("ascii")).hexdigest()

    @staticmethod
    def pdf_source(source: str) -> str:
        """ジョブに記録する、利用者が渡したままの絶対パス。ネットワークドライブの PDF は解決すると UNC に
        なるので、解決したパスではなくこちらを記録し、ワーカーで同じように確かめ直す。"""
        return str(Path(str(source).strip()).expanduser())

    def workspace(self, wiki_root: str) -> Path:
        wiki = Path(wiki_root).expanduser().resolve()
        if not (wiki / "SCHEMA.md").is_file():
            raise ValueError("wiki_root に SCHEMA.md がありません。先に wiki を初期化してください。")
        identity = hashlib.sha256(os.path.normcase(str(wiki)).encode("utf-8")).hexdigest()[:24]
        return self.data_dir / "wikis-v2" / identity
````

## 埋め込み、索引、公開

- [info-hive-rag/scripts/rag_config.py 16 行目から](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/scripts/rag_config.py#L16-L24)

````
MODELS = {
    "cl-nagoya/ruri-v3-30m": 256,
    "cl-nagoya/ruri-v3-70m": 384,
    "cl-nagoya/ruri-v3-130m": 512,
    "cl-nagoya/ruri-v3-310m": 768,
}
DEFAULT_MODEL = "cl-nagoya/ruri-v3-130m"
DEFAULT_REVISION = "e3114c6ee10dbab8b4b235fbc6dcf9dd4d5ac1a6"
OCR_REVISION = "e57f7c6bd9cfb3de5f12f008e71ad2122bd44bfd"
````

- [info-hive-rag/scripts/rag_index.py 83 行目から](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/scripts/rag_index.py#L83-L113)

````
class Embedder:
    def __init__(self, config: Config):
        import torch
        from sentence_transformers import SentenceTransformer

        torch.set_num_threads(config.threads)
        if torch.get_num_interop_threads() != 1:
            torch.set_num_interop_threads(1)
        os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
        self.model = SentenceTransformer(config.model, revision=config.revision, device="cpu",
                                         cache_folder=str(config.model_cache_dir),
                                         model_kwargs={"attn_implementation": "sdpa"})
        # モデル本来の文脈長を使い、トークン数は encode 前に検査する。
        native_limit=int(self.model[0].auto_model.config.max_position_embeddings)
        self.model.max_seq_length=min(native_limit,8192)
        self.dimension = config.dimension

    def encode(self, texts: list[str], *, query: bool = False):
        prefix = "検索クエリ: " if query else "検索文書: "
        inputs=[prefix+text for text in texts]
        if not inputs:
            return self.model.encode(inputs,normalize_embeddings=True,show_progress_bar=False,convert_to_numpy=True)
        lengths=[len(ids) for ids in self.model.tokenizer(inputs,truncation=False,padding=False)['input_ids']]
        longest=max(lengths)
        if longest>self.model.max_seq_length:
            raise ValueError(f"埋め込み入力がモデルの上限 {self.model.max_seq_length} トークンを超えています。本文を失わないよう分割を小さくしてください。")
        # 長い入力で注意行列のメモリが膨らまないよう、二乗長に応じて件数を下げる。
        batch=max(1,min(32,len(inputs),(8*2048**2)//max(1,longest**2)))
        return self.model.encode(inputs, normalize_embeddings=True,batch_size=batch,
                                 show_progress_bar=False, convert_to_numpy=True)

````

- [info-hive-rag/scripts/rag_index.py 137 行目から](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/scripts/rag_index.py#L137-L184)

````
        import unicodedata
        from sudachipy import dictionary, tokenizer

        if self._tokenizer is None:
            self._tokenizer = dictionary.Dictionary().create()
        normalized = unicodedata.normalize("NFKC", text).lower()
        return " ".join(word.normalized_form().lower() for word in
                        self._tokenizer.tokenize(normalized, tokenizer.Tokenizer.SplitMode.C)
                        if word.surface().strip() and word.part_of_speech()[0] != "補助記号")

    @contextmanager
    def _catalog(self, folder: Path):
        folder.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(folder / "catalog.sqlite")
        connection.row_factory = sqlite3.Row
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY, generation TEXT NOT NULL, title TEXT NOT NULL,
                pages INTEGER, chunks INTEGER, fingerprint TEXT NOT NULL, ingested_at REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS locations (
                path TEXT PRIMARY KEY, doc_id TEXT NOT NULL, size INTEGER, mtime_ns INTEGER,
                confirmed_at REAL NOT NULL, dev TEXT, ino TEXT);
            CREATE INDEX IF NOT EXISTS locations_file ON locations(dev, ino);
            CREATE TABLE IF NOT EXISTS citations (
                doc_id TEXT, source_page TEXT, PRIMARY KEY(doc_id, source_page));
            CREATE TABLE IF NOT EXISTS jobs (
                generation TEXT PRIMARY KEY, completed INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'pending', error TEXT);
        """)
        with closing(connection), connection:
            yield connection

    def _table(self, folder: Path, create: bool = False):
        import lancedb
        import pyarrow as pa

        database = lancedb.connect(str(folder / "lance"), read_consistency_interval=timedelta(0))
        try:
            return database.open_table("chunks")
        except (FileNotFoundError, ValueError):
            if not create:
                return None
        schema = pa.schema([
            ("chunk_id", pa.string()), ("doc_id", pa.string()), ("generation", pa.string()),
            ("page", pa.int32()), ("section", pa.string()), ("title", pa.string()),
            ("text", pa.string()), ("terms", pa.string()),
            ("vector", pa.list_(pa.float32(), self.config.dimension)),
        ])
````

- [info-hive-rag/scripts/rag_index.py 296 行目から](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/scripts/rag_index.py#L296-L305)

````
        return FileLock(str(self.config.extraction_root / f"{doc_id}.lock"), timeout=timeout)

    @staticmethod
    def _write_markdown(markdown: Path, pages: list[dict]) -> None:
        """document.md は題名を含まないので、wiki によらない。途中で止まっても半端なファイルを残さない。"""
        temporary = markdown.with_name(markdown.name + ".tmp")
        temporary.write_text("\n\n".join(f"## p. {page['page']}\n\n{page['text']}" for page in pages), encoding="utf-8")
        os.replace(temporary, markdown)

    @staticmethod
````

- [info-hive-rag/scripts/rag_index.py 494 行目から](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/scripts/rag_index.py#L494-L573)

````
            index_reset = False
            with self._catalog(folder) as connection:
                if progress:
                    progress("PDF の読み込み", 0, 1)
                # 遅い原資料を一度だけ順次読み込み、ハッシュと PDFium で共用する。
                data, stat_after = read_pdf(path, expected)
                if progress:
                    progress("PDF の読み込み", 1, 1)
                doc_id = hashlib.sha256(data).hexdigest()
                generation = self.config.generation(doc_id)
                # 抽出の結果は wiki のあいだで共有する。使っているあいだは、ほかの取り込みの後始末で消させない。
                held.enter_context(self._extraction_lock(doc_id))
                cache = self.config.extraction_dir(doc_id)
                self._adopt_legacy_extraction(folder, self._legacy_generations(folder, doc_id, stale), cache)
                markdown = cache / "document.md"
                existing = None if stale else connection.execute("SELECT * FROM documents WHERE doc_id=?", (doc_id,)).fetchone()
                if existing:
                    pages_count, chunks_count = existing["pages"], existing["chunks"]
                    # 索引の行は、記録した generation で入っている（抽出の版を上げる前の式のこともある）。
                    generation = existing["generation"]
                    skipped = True
                    if not markdown.exists():
                        # 索引にはあるが、今の抽出の設定の結果がない（抽出の版を上げた、結果を消したなど）。
                        # 索引は作り直さず、返す本文のために抽出だけをやり直す。
                        self._write_markdown(markdown, self.extractor(data, self.config, cache, progress))
                else:
                    skipped = False
                    if not stale:
                        connection.execute("INSERT OR IGNORE INTO jobs(generation) VALUES (?)", (generation,))
                        connection.commit()
                    try:
                        pages = self.extractor(data, self.config, cache, progress)
                        title = title.strip() or path.stem
                        chunks = chunks_for(pages, title, self.config)
                        if not chunks:
                            raise ValueError("検索できるテキストがありません。取り込みは完了していません。")
                        pages_count, chunks_count = len(pages), len(chunks)
                        if not markdown.exists():
                            self._write_markdown(markdown, pages)
                        # 方針が変わった索引は、最初のバッチの埋め込みが済んでから空にする。モデルの取得や読み込みに
                        # 失敗しても、前の索引を壊さない。設定を戻せば、前の索引をそのまま使える。
                        table = None if stale else self._table(folder, create=True)
                        completed = 0 if stale else connection.execute(
                            "SELECT completed FROM jobs WHERE generation=?", (generation,)).fetchone()[0]
                        for start in range(completed, len(chunks), self.config.batch_size):
                            if progress:
                                progress("埋め込み", start, len(chunks))
                            batch = chunks[start:start + self.config.batch_size]
                            vectors = self.embedder.encode([chunk["embedding_text"] for chunk in batch])
                            if len(vectors) != len(batch):
                                raise ValueError("埋め込みの件数がチャンク数と一致しません。")
                            rows = []
                            for number, (chunk, vector) in enumerate(zip(batch, vectors), start):
                                vector = list(map(float, vector))
                                if len(vector) != self.config.dimension or not all(__import__("math").isfinite(v) for v in vector):
                                    raise ValueError("埋め込みの次元数または数値が不正です。")
                                rows.append({"chunk_id": f"{generation}:{number}", "doc_id": doc_id, "generation": generation,
                                             "page": chunk["page"], "section": chunk["section"], "title": title,
                                             "text": chunk["text"], "terms": self.tokenize(chunk["embedding_text"]), "vector": vector})
                            if stale:
                                self._reset_index(folder, connection, stale)
                                stale, index_reset = None, True
                                connection.execute("INSERT OR IGNORE INTO jobs(generation) VALUES (?)", (generation,))
                                connection.commit()
                            if table is None:
                                table = self._table(folder, create=True)
                            table.merge_insert("chunk_id").when_matched_update_all().when_not_matched_insert_all().execute(rows)
                            connection.execute("UPDATE jobs SET completed=?, error=NULL WHERE generation=?", (start + len(batch), generation))
                            connection.commit()
                            if progress:
                                progress("埋め込み", start + len(batch), len(chunks))
                    except Exception as error:
                        connection.execute("UPDATE jobs SET status='failed', error=? WHERE generation=?", (str(error), generation))
                        connection.commit()
                        raise
                self._maintain_indexes(folder,self._table(folder),progress)
                current = os.stat(path)
                if (stat_after.st_size, stat_after.st_mtime_ns) != (current.st_size, current.st_mtime_ns):
                    raise ValueError("処理中に PDF が変更されました。新しいジョブで取り込んでください。")
                if before_publish:
````

- [info-hive-rag/scripts/rag_indexes.py 63 行目から](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/scripts/rag_indexes.py#L63-L82)

````
        self.state['deleted_since_training']+=max(0,self.state.get('rows',0)-rows)
        current={index.name:index for index in table.list_indices()}
        if 'terms_idx' not in current:
            self.operation('全文索引の作成',['terms_idx'],lambda:table.create_fts_index('terms',base_tokenizer='whitespace',stem=False,remove_stop_words=False,ascii_folding=False))
        if 'generation_idx' not in current:
            self.operation('世代索引の作成',['generation_idx'],lambda:table.create_scalar_index('generation',index_type='BITMAP',replace=False))
        names=sorted({index.name for index in table.list_indices()})
        if not self.healthy(names,rows):
            self.operation('索引の更新',names,lambda:table.optimize(cleanup_older_than=timedelta(days=self.config.index_cleanup_age_days),delete_unverified=False))
        current={index.name:index for index in table.list_indices()}
        vector=current.get('vector_idx')
        trained=self.state.get('trained_rows',0)
        wrong_type=vector and vector.index_type.lower().replace('_','')!='ivfsq'
        grew=trained and rows>=trained*self.config.ann_rebuild_growth
        shrank=trained and rows*self.config.ann_rebuild_growth<=trained
        many_deleted=trained and self.state['deleted_since_training']>=max(self.config.ann_min_rows,trained//4)
        if rows>=self.config.ann_min_rows and (vector is None or wrong_type or grew or shrank or many_deleted):
            partitions=max(1,min(4096,math.ceil(math.sqrt(rows))))
            self.operation('ANN の作成' if vector is None else 'ANN の再構築',['vector_idx'],
                lambda:table.create_index(vector_column_name='vector',metric='cosine',index_type='IVF_SQ',num_partitions=partitions,name='vector_idx',replace=True),
````

- [info-hive-rag/scripts/rag_index.py 601 行目から](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/scripts/rag_index.py#L601-L640)

````
                # 新しい索引が揃うまでは旧版を検索対象として残す。
                reviews = {page for old_id in old_ids for page in self._mark_reviews(wiki, connection, old_id)}
                # 索引を空にしたあとは、この場所の前の版を台帳で引けない。取り込み直しの一覧から引く。
                for item in self._previous_documents(folder).values():
                    if item["sha256"] != doc_id and path.as_posix() in item["paths"]:
                        reviews.update(self._mark_reviews(wiki, connection, item["sha256"], item["source_pages"]))
                reviews = sorted(reviews)
                connection.execute("""INSERT OR REPLACE INTO documents
                    (doc_id,generation,title,pages,chunks,fingerprint,ingested_at)
                    VALUES (?,?,?,?,?,?,?)""",
                                   (doc_id, generation, existing["title"] if existing else title,
                                    pages_count, chunks_count, self.config.fingerprint, time.time()))
                now = time.time()
                for place in [location, *aliases]:
                    connection.execute("INSERT OR REPLACE INTO locations VALUES (?,?,?,?,?,?,?)",
                                       (place, doc_id, stat_after.st_size, stat_after.st_mtime_ns,
                                        now if place == location else now - 1e-6, *(same_file or (None, None))))
                connection.execute("INSERT OR IGNORE INTO citations VALUES (?,?)", (doc_id, source_page))
                # 索引を空にする前に、この文書を出典にしていたページも戻す。版が変わったときの要再確認の印に使う。
                restored = self._previous_documents(folder).get(doc_id)
                for page in restored["source_pages"] if restored else []:
                    connection.execute("INSERT OR IGNORE INTO citations VALUES (?,?)", (doc_id, page))
                # 改名した同じ内容の資料は、存在しなくなった旧パスだけを台帳から外す。
                for row in connection.execute("SELECT path FROM locations WHERE doc_id=?", (doc_id,)).fetchall():
                    if not os.path.exists(row["path"]):
                        connection.execute("DELETE FROM locations WHERE path=?", (row["path"],))
                connection.execute("UPDATE jobs SET status='complete', error=NULL WHERE generation=?", (generation,))
                removed = []
                old_rows = {old_id: connection.execute("SELECT generation FROM documents WHERE doc_id=?", (old_id,)).fetchall()
                            for old_id in old_ids}
                for old_id in old_ids:
                    if not connection.execute("SELECT 1 FROM locations WHERE doc_id=?", (old_id,)).fetchone():
                        connection.execute("DELETE FROM documents WHERE doc_id=?", (old_id,))
                        # 内部の途中経過も消す。同じ内容に戻したとき、埋め込みを最初からやり直すため。
                        # 記録した generation は、抽出の版を上げる前の式のこともあるので、今の式の値と両方を消す。
                        old_generations = {self.config.generation(old_id), *(row[0] for row in old_rows.get(old_id, []))}
                        connection.executemany("DELETE FROM jobs WHERE generation=?", [(value,) for value in old_generations])
                        removed.append((old_id, self._legacy_generations(folder, old_id, None)))
                connection.commit()
                # コミット後の保守が失敗しても、新版は検索できる。旧行は active generation の条件で除外する。
````

- [info-hive-rag/scripts/rag_index.py 660 行目から](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/scripts/rag_index.py#L660-L697)

````
                return {"status": "unchanged" if skipped else "indexed", "document_id": doc_id,
                        "raw": path.as_posix(), "sha256": doc_id, "pages": pages_count, "chunks": chunks_count,
                        "extracted_markdown": str(markdown), "source_page": source_page,
                        "review_pages": reviews, "cleanup_error": cleanup_error, "index_reset": index_reset,
                        "indexes":json.loads((folder/'index-state.json').read_text(encoding='utf-8'))}

    def search(self, wiki_root: str, query: str, limit: int = 10) -> dict:
        if not query.strip() or not 1 <= limit <= 50:
            raise ValueError("空でない質問と、1〜50 の limit を指定してください。")
        folder = self.config.workspace(wiki_root)
        empty={"results":[],"model":self.config.model,"reranker":self.config.reranker,
               "abstained":self.config.min_rerank_score is not None}
        if not (folder / "catalog.sqlite").exists():
            return empty
        with FileLock(str(folder / "write.lock"), timeout=1800):
            self._check_policy(folder)
            with self._catalog(folder) as connection:
                documents = {row["doc_id"]: dict(row) for row in connection.execute("SELECT * FROM documents")}
                if not documents:
                    return empty
                active = "generation IN (" + ",".join("'" + row["generation"] + "'" for row in documents.values()) + ")"
                table = self._table(folder)
                vector = self.embedder.encode([query], query=True)[0].tolist()
                candidates = max(limit, min(200, limit * 10))
                columns = ["chunk_id", "doc_id", "page", "section", "title", "text"]
                dense_query = table.search(vector).distance_type("cosine").where(active, prefilter=True).select(columns)
                if any("vector" in index.columns for index in table.list_indices()):
                    dense_query = dense_query.nprobes(self.config.search_nprobes).refine_factor(self.config.search_refine_factor)
                dense = dense_query.limit(candidates).to_list()
                terms = self.tokenize(query)
                lexical = table.search(terms, query_type="fts", fts_columns="terms").where(active, prefilter=True).select(columns).limit(candidates).to_list() if terms else []
                scores, rows = {}, {}
                for ranking in (dense, lexical):
                    for rank, row in enumerate(ranking, 1):
                        key = row["chunk_id"]
                        rows[key] = row
                        scores[key] = scores.get(key, 0) + 1 / (60 + rank)
                ranked = sorted(scores, key=lambda k: (-scores[k], k))
````

- [info-hive-rag/scripts/rag_index.py 708 行目から](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/scripts/rag_index.py#L708-L717)

````
                results = []
                for key in ranked[:limit]:
                    row = rows[key]
                    found = self._location(connection, row["doc_id"])
                    sources = [item[0] for item in connection.execute("SELECT source_page FROM citations WHERE doc_id=?", (row["doc_id"],))]
                    results.append({**{k: v for k, v in row.items() if not k.startswith("_")}, "score": scores[key],
                                    "raw": Path(found).as_posix() if found else None, "sha256": row["doc_id"],
                                    "source_pages": sources,
                                    "rerank_score": reranked_scores.get(key)})
                return {"results": results, "model": self.config.model, "reranker":self.config.reranker,
````

## wiki との受け渡しと設計記録

- [info-hive-wiki/commands/ingest.md 78 行目から](https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/commands/ingest.md#L78-L84)

````
## PDF の登録（rag が有効な場合）

1. `python "${CLAUDE_PLUGIN_ROOT}/skills/info-hive/scripts/wiki_raw_ingest.py" pdf --wiki "<WIKI_ROOT>" --raw-root "<RAW_ROOT>" --source "<ユーザーが指定した PDF>"` を実行する。失敗したら理由を伝えて止まる。成功したら要約ページのスラッグを決め、`rag` MCP サーバーの `register_pdf` に `wiki_root=<WIKI_ROOT の絶対パス>`、`source=<検査の JSON が返した source>`、`source_page="sources/<スラッグ>.md"`、`title=<題名>` を渡す。`source` はスクリプトが返したパスの綴りを使う。ユーザーが指定していない PDF は登録しない。ツール名は接続に表示されたものを使う。別プラグインの内部パスを組み立ててスクリプトを実行しない。PDF を閲覧するだけの場合は登録しない。
2. 応答の `job_id` を記録する。`queued`、`running`、`paused` は受付・処理中であり、索引化や wiki の取り込み完了と報告しない。原本を `<RAW_ROOT>` へコピーしない。登録を拒まれたら、理由（絶対パスでない、PDF でない、UNC パス、rag の派生データの中にある、など）をそのまま伝える。
3. `job_status(wiki_root, job_id)` で進捗を確認する。短時間待つ場合は `wait_seconds=30` を使い、細かい連続呼び出しを避ける。処理中に会話を終える場合はジョブ ID と再開待ちの状態を報告し、ここで手順を止める。次回 rag の MCP 接続時に未完了ジョブは自動再開する。キャンセル済みのジョブは自動再開しない。
4. `completed` のときだけ `result.extracted_markdown` を分割して読み、通常の手順 4〜8 に進む。要約ページの `raw` には `result.raw`（`/` 区切りの絶対パス）を、`raw_sha256` には `result.sha256` を、`rag_job_id` にはジョブ ID を書く。値は二重引用符で囲み、`\` は `\\`、`"` は `\"` と書く。内容を読む前に要約を作らない。
5. `failed` は理由を報告し、修正後は `retry_job` で再試行する。`cancelled` の再試行は明示的に依頼された場合だけ行う。
````

- [info-hive-wiki/skills/info-hive/references/ingest-workflow.md 13 行目から](https://github.com/to884/info-hive-wiki/blob/b8596d1888035769528cb74e35bda51c9d9c40a0/skills/info-hive/references/ingest-workflow.md#L13-L35)

````
### PDF と rag の連携

`rag` の MCP ツールが使える場合、PDF は原本の場所に置いたまま登録する。先に `python "<skill-root>/scripts/wiki_raw_ingest.py" pdf --wiki "<WIKI_ROOT>" --raw-root "<RAW_ROOT>" --source "<指定された PDF>"` を実行する。失敗したら理由を伝えて止まる。成功したら `register_pdf(wiki_root, source, source_page, title)` を呼ぶ。
`wiki_root` は特定した wiki の絶対パス、`source` は検査の JSON が返した `source`、`source_page` は `sources/<スラッグ>.md` である。
検査が返したパスの綴りを使う。ユーザーが指定していない PDF は登録しない。
rag は、登録のときに、拡張子が `.pdf` の通常のファイルだけを受け付け、UNC パスと rag の派生データの中の PDF を拒む。
PDF のヘッダー（`%PDF-`）は、登録のあとの処理で確かめ、ヘッダーがなければジョブが `failed` になる。rag 0.5.1 以降は、`%PDF-` の前にあるバイトが 1024 バイト以下なら受け付ける（先頭に改行や空白があるだけの PDF も読む）。rag 0.5.0 以前は、先頭がちょうど `%PDF-` の PDF だけを受け付ける。
登録を拒まれたり、ジョブが `failed` になったりしたら、理由をそのまま伝える。
この呼び出しを、コマンドと自然言語による取り込みの両方で実行する。PDF を読むだけの依頼では呼ばない。
原本を `raw/` へコピーせず、別プラグインの内部スクリプトも直接呼ばない。

返された `job_id` を保持し、`job_status(wiki_root, job_id)` で進捗を確かめる。
短時間待つ場合は `wait_seconds=30` を使い、細かい連続呼び出しを避ける。
`queued`、`running`、`paused` の間は受付・処理中であり、索引化完了でも wiki の取り込み完了でもない。
会話を終える場合はジョブ ID を報告して手順を止める。次回 rag の MCP 接続時に、未完了ジョブが保存済みのページと埋め込みバッチから自動再開する。
`failed` の理由を直した後は `retry_job` を使う。`cancelled` は明示的な依頼なしに再試行しない。

`completed` になったら `result.extracted_markdown` を分割して読み、手順 2 の「PDF を読む」の「rag で取り込んだとき」で読めないページを確かめてから、手順 3 以降へ進む。
ソースの要約ページには `raw: "<result.raw>"`、`raw_sha256: "<result.sha256>"`、`rag_job_id: "<job_id>"` を書く。
`result.raw` は `/` 区切りの絶対パス（Windows では `C:/Books/本.pdf`）で、`result.sha256` は PDF の内容の SHA-256 である。
値の中の `\` は `\\`、`"` は `\"` と書く（`page-conventions.md` の frontmatter の決まり）。
別の PC では PDF の場所が違うことがある。同じ PDF を取り込み直すと、`raw_sha256` で同じ出典と分かる。
rag が使えない場合は、下の通常手順を使える。ただし RAG 連携を求められた場合は rag の有効化を案内し、索引化済みとは報告しない。
````

- [info-hive-rag/scripts/rag_index.py 443 行目から](https://github.com/to884/info-hive-rag/blob/4fabe3294d86a367e635bc18635af6e7132a8d93/scripts/rag_index.py#L443-L479)

````
    def _mark_reviews(self, wiki: Path, connection, doc_id: str, cited=()) -> list[str]:
        import yaml

        direct = {row[0] for row in connection.execute("SELECT source_page FROM citations WHERE doc_id=?", (doc_id,))}
        direct.update(cited)
        slugs = {Path(page).stem for page in direct}
        affected = []
        for page in wiki.rglob("*.md"):
            if not page.resolve().is_relative_to(wiki) or any(part.startswith(".") for part in page.relative_to(wiki).parts):
                continue
            text = page.read_text(encoding="utf-8-sig")
            match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
            if not match:
                continue
            meta = yaml.safe_load(match.group(1)) or {}
            if not isinstance(meta, dict):
                continue
            sources = meta.get("sources", meta.get("出典", []))
            if isinstance(sources, str):
                sources = [sources]
            sources = {str(value).strip("[]").split("|")[0] for value in sources or []}
            relative = page.relative_to(wiki).as_posix()
            if relative not in direct and not (sources & slugs):
                continue
            frontmatter = match.group(1)
            for key, value in {"review_required": "true", "review_reason": json.dumps("参照する PDF の内容が変わりました。出典を確認してください。", ensure_ascii=False)}.items():
                pattern = rf"(?m)^{key}:.*$"
                if re.search(pattern, frontmatter):
                    frontmatter = re.sub(pattern, f"{key}: {value}", frontmatter)
                else:
                    frontmatter += f"\n{key}: {value}"
            replacement = "---\n" + frontmatter + "\n---\n" + text[match.end():]
            temporary = page.with_suffix(".md.rag-tmp")
            temporary.write_text(replacement, encoding="utf-8")
            temporary.replace(page)
            affected.append(relative)
        return affected
````

- [info-hive-dev/docs/adr/0012-wiki-owns-local-mcp-index-server.md 22 行目から](https://github.com/to884/info-hive-dev/blob/23abeb19e1fa42cd4d974c99bb9c0d44f5bec000/docs/adr/0012-wiki-owns-local-mcp-index-server.md#L22-L32)

````
| 持ち主 | wiki のプラグインが、127.0.0.1 で待ち受ける streamable HTTP の MCP サーバーを持つ。モデルの読み込み、埋め込み、索引の書き込み（初回の再埋め込みを含む）は、このサーバーだけが行う |
| 入口 | wiki に `.mcp.json` を足し、stdio の中継を登録する。中継はロックファイルを取り、`server.json`（ポート、トークン、pid）の指すサーバーが生きていればそれを使い、いなければ起動する。同時に起動された中継が、サーバーを 2 つ起動しないようにする |
| 起動のしかた | サーバーは中継の子として、Windows では窓のない自分のコンソール（`CREATE_NO_WINDOW`）と新しいプロセスグループで起動する。`DETACHED_PROCESS` は使わない（2026年11月11日に改めた。info-hive-wiki#36、理由の節）。起動の前にロックの中で `server.json` を消し、新しく現れた `server.json` を今起動したサーバーのものとみなす。venv の `python.exe` は本体を子プロセスとして起動するので、`Popen` の pid では確かめない。WMI のように、ホストの外からプロセスを起動する方式は使わない |
| 寿命 | 要求がない状態が一定の時間続いたら、サーバーは自分で止まる。次の呼び出しで中継が起動し直す。OS のサービスとしては登録しない |
| 防御 | 127.0.0.1 だけで待ち受ける。起動ごとにトークンを作り、Bearer で確かめる。Host ヘッダーを確かめ、DNS rebinding を防ぐ。認証は ASGI のミドルウェアで書く |
| 応答 | streamable HTTP の応答は、SSE ではなく JSON にする |
| 上乗せの目安 | 関数の直接呼び出しに対する、中継経由の上乗せの p95 は 15 ms 以内とする（最初の目安の 10 ms から緩めた） |
| ツール | `query`、`get_page`、`list_index`、`lint`、`stats`、`graph`、`index_chunks`。`lint` は検査だけで、直す操作は持たない。統一の測定が挙げた `ingest_source` は外す |
| 索引の置き場所 | wiki ごとに `%LOCALAPPDATA%/info-hive/index/<wiki のハッシュ>/`（macOS と Linux は XDG の data ディレクトリ）に置く。wiki の中の `.wiki-cache/` には置かない。`server.json` は `%LOCALAPPDATA%/info-hive/` に置く |
| rag | rag は wiki のサーバーの MCP クライアントになる。rag の子ワーカーは抽出と OCR を行い、チャンクを `index_chunks` でサーバーに渡す。rag の `search` ツールは窓口として残し、中で wiki のサーバーに頼む。wiki が無効なら、検索できないと報告する |
| コマンド | `/wiki:query` などのコマンドは MCP のツールを呼ぶように移す。MCP が使えないときは今の CLI に戻る |
````
