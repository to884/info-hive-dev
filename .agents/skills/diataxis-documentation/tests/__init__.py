"""Shared bootstrap for the test suite.

`unittest discover -s tests` imports this package before any test module, so
the `sys.path` entry below is in place by the time a module does
`import diataxis_audit`. Keeping it here means the four test modules do not
each repeat the same four lines.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

# The labeled corpus is distributed with the skill, so the README tutorial can
# reach it from any install. The tests use the same pages.
AUDIT_CORPUS = REPO_ROOT / "assets" / "examples" / "audit-corpus"
