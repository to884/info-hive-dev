"""ADR-0007 のジョブ保存を試す共通コア。製品コードとは独立した PoC。"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import uuid
from contextlib import closing
from pathlib import Path


class Store:
    def __init__(self, path: str):
        self.path = str(Path(path).resolve())
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
            CREATE TABLE IF NOT EXISTS jobs (
              id TEXT PRIMARY KEY, wiki TEXT, source TEXT, size INTEGER, mtime INTEGER,
              policy TEXT, status TEXT, owner TEXT, deadline REAL DEFAULT 0,
              completed INTEGER DEFAULT 0, total INTEGER DEFAULT 0, error TEXT,
              attempts INTEGER DEFAULT 0, digest TEXT);
            CREATE TABLE IF NOT EXISTS checkpoints (
              job TEXT, step INTEGER, output TEXT, PRIMARY KEY(job,step));
            CREATE TABLE IF NOT EXISTS executions (
              job TEXT, step INTEGER, owner TEXT, at REAL);
            CREATE TABLE IF NOT EXISTS published (
              wiki TEXT, source TEXT, job TEXT, PRIMARY KEY(wiki,source));
            """)

    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=15000")
        return db

    def submit(self, wiki: str, source: str, policy: str = "protocol-v1") -> dict:
        wiki, source = str(Path(wiki).resolve()), str(Path(source).resolve())
        stat = Path(source).stat()
        key = json.dumps([wiki, source, stat.st_size, stat.st_mtime_ns, policy])
        identity = hashlib.sha256(key.encode()).hexdigest()
        with self.connect() as db:
            db.execute("INSERT OR IGNORE INTO jobs(id,wiki,source,size,mtime,policy,status) VALUES (?,?,?,?,?,?,?)",
                       (identity, wiki, source, stat.st_size, stat.st_mtime_ns, policy, "queued"))
        return self.status(identity)

    def status(self, identity: str) -> dict:
        with self.connect() as db:
            row = db.execute("SELECT * FROM jobs WHERE id=?", (identity,)).fetchone()
            if row is None:
                raise ValueError("ジョブがありません。")
            return dict(row)

    def run_sync(self, wiki: str, source: str, policy: str = "protocol-v1") -> dict:
        job = self.submit(wiki, source, policy)
        while self.status(job["id"])["status"] in {"queued", "running"}:
            self.work_once(delay=.03)
        return self.status(job["id"])

    def cancel(self, identity: str) -> dict:
        with self.connect() as db:
            db.execute("UPDATE jobs SET status='cancelled' WHERE id=? AND status IN ('queued','running','failed')", (identity,))
        return self.status(identity)

    def retry(self, identity: str) -> dict:
        with self.connect() as db:
            db.execute("UPDATE jobs SET status='queued',owner=NULL,deadline=0,error=NULL WHERE id=? AND status='failed'", (identity,))
        return self.status(identity)

    def active(self, wiki: str, source: str) -> list[dict]:
        with self.connect() as db:
            return [json.loads(row[0]) for row in db.execute("""
              SELECT c.output FROM checkpoints c JOIN published p ON p.job=c.job
              WHERE p.wiki=? AND p.source=? ORDER BY c.step
              """, (str(Path(wiki).resolve()), str(Path(source).resolve())))]

    def claim(self, owner: str, lease: float) -> dict | None:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM jobs WHERE status='queued' OR (status='running' AND deadline<?) ORDER BY rowid LIMIT 1", (time.time(),)).fetchone()
            if row is None:
                return None
            db.execute("UPDATE jobs SET status='running',owner=?,deadline=?,attempts=attempts+1 WHERE id=?",
                       (owner, time.time() + lease, row["id"]))
            return dict(row)

    def work_once(self, *, delay: float = 0, lease: float = 2, fail_at: int = -1) -> bool:
        # 疑似的な埋め込みの代わりに、実際の PDF 抽出結果のハッシュを保存する。
        # この出力を、意味検索の精度やモデル性能の評価には使わない。
        import pypdfium2 as pdfium

        owner = uuid.uuid4().hex
        job = self.claim(owner, lease)
        if not job:
            return False
        identity = job["id"]
        try:
            payload = Path(job["source"]).read_bytes()
            stat = Path(job["source"]).stat()
            if (stat.st_size, stat.st_mtime_ns) != (job["size"], job["mtime"]):
                raise ValueError("登録後に原資料が変わりました。新しいジョブを作ってください。")
            digest = hashlib.sha256(payload).hexdigest()
            with pdfium.PdfDocument(payload) as pdf:
                with self.connect() as db:
                    db.execute("UPDATE jobs SET total=?,digest=? WHERE id=? AND owner=?", (len(pdf), digest, identity, owner))
                for step in range(job["completed"], len(pdf)):
                    with self.connect() as db:
                        state = db.execute("SELECT status,owner FROM jobs WHERE id=?", (identity,)).fetchone()
                    if state["status"] != "running" or state["owner"] != owner:
                        return True
                    if step == fail_at:
                        raise RuntimeError("PoC の障害注入")
                    with closing(pdf[step]) as page, closing(page.get_textpage()) as textpage:
                        text = textpage.get_text_range()
                    output = json.dumps({"page": step + 1, "text_hash": hashlib.sha256(text.encode()).hexdigest(), "chars": len(text)}, ensure_ascii=False)
                    time.sleep(delay)
                    with self.connect() as db:
                        db.execute("BEGIN IMMEDIATE")
                        changed = db.execute("UPDATE jobs SET completed=?,deadline=? WHERE id=? AND owner=? AND status='running'",
                                             (step + 1, time.time() + lease, identity, owner)).rowcount
                        if not changed:
                            return True
                        db.execute("INSERT OR REPLACE INTO checkpoints VALUES (?,?,?)", (identity, step, output))
                        db.execute("INSERT INTO executions VALUES (?,?,?,?)", (identity, step, owner, time.time()))
                with self.connect() as db:
                    db.execute("BEGIN IMMEDIATE")
                    changed = db.execute("UPDATE jobs SET status='completed',deadline=0 WHERE id=? AND owner=? AND status='running'", (identity, owner)).rowcount
                    if changed:
                        db.execute("INSERT OR REPLACE INTO published VALUES (?,?,?)", (job["wiki"], job["source"], identity))
            return True
        except Exception as error:
            with self.connect() as db:
                db.execute("UPDATE jobs SET status='failed',error=?,deadline=0 WHERE id=? AND owner=? AND status='running'", (str(error), identity, owner))
            return True
