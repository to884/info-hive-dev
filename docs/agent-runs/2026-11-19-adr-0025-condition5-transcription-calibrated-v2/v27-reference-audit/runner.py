"""直前までの準備を固定し、起動境界を外部の台帳に記録する。"""

import os
from pathlib import Path
import subprocess
import tempfile


def publish(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=".write-", dir=path.parent, delete=False) as f:
        first = Path(f.name)
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    try:
        os.link(first, path)
    finally:
        first.unlink()


def read(audit, runtime, role, model, request, cards, folder, before_launch):
    folder.mkdir()
    readers = audit.readers
    exe = Path(runtime["path"])
    payload = readers.request_payload(request, cards, role)
    contract = readers.encoded(audit.SCHEMA_READER.schema(request["ids"]))
    schema = folder / "schema.json"
    publish(schema, contract)
    env = os.environ.copy()
    for name in ("CODEX_WINDOWS_REGISTERED_CORE", "CODEX_WINDOWS_SANDBOX_PACKAGE_FAMILY"):
        env.pop(name, None)
    with tempfile.TemporaryDirectory(prefix="adr0025-structured-") as cwd:
        argv = readers.command(exe, cards, request["images"], model, role, cwd)
        last = folder / "last-message.json"
        if role == "gpt":
            argv[-1:-1] = ["--output-schema", str(schema), "--output-last-message", str(last)]
        else:
            argv.extend(["--json-schema", contract.decode("utf-8").strip()])
        start = folder / "start.json"
        publish(start, readers.encoded({
            "family": role, "model": model, "cwd": cwd, "packet_sha256": readers.sha(payload), "argv": argv,
            "executable_sha256": audit.sha(exe), "image_sha256": request["image_sha256"], "schema_sha256": audit.sha(schema),
        }))
        before_launch(audit.sha(start))
        try:
            result = subprocess.run(argv, input=payload, capture_output=True, cwd=cwd, env=env, timeout=720)
            raw, err, code = result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired as ex:
            raw, err, code = ex.stdout or b"", ex.stderr or b"", -1
    publish(folder / "response.jsonl", raw)
    publish(folder / "stderr.txt", err)
    publish(folder / "process.json", readers.encoded({
        "returncode": code, "response_sha256": readers.sha(raw), "stderr_sha256": readers.sha(err),
        "last_sha256": audit.sha(last) if last.is_file() else None,
    }))
