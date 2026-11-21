"""実行時に参照する作業ツリー内のPythonコードを固定する。"""

from hashlib import sha256
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
SEEN = {}
EXPECTED = None
original_spec = importlib.util.spec_from_file_location


def local(path):
    if path is None:
        return None
    found = Path(path).resolve()
    if found.suffix == ".py" and found.is_relative_to(ROOT):
        return found
    return None


def register(location):
    path = local(location)
    if path is None:
        return
    name = str(path)
    fingerprint = sha256(path.read_bytes()).hexdigest()
    if EXPECTED is not None and EXPECTED.get(name) != fingerprint:
        raise ValueError(f"事前固定していない監査コードを読み込もうとした {name}")
    if SEEN.setdefault(name, fingerprint) != fingerprint:
        raise ValueError(f"実行中に同じ監査コードが変化した {name}")


def traced_spec(name, location=None, **kwargs):
    register(location)
    return original_spec(name, location, **kwargs)


def install():
    importlib.util.spec_from_file_location = traced_spec


def snapshot():
    for module in tuple(sys.modules.values()):
        register(getattr(module, "__file__", None))
    return dict(sorted(SEEN.items()))


def enforce(files):
    global EXPECTED
    EXPECTED = files
    for filename in tuple(SEEN):
        register(filename)
    snapshot()
