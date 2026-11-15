"""実装のレビューの 1 回目の重大（試験）と 2 回目の軽微（試験）の順序で、UnreadableRecordTest の 3 件を流す。

stop が止める要求を送ったあと、要求の戻りを遅らせる（補助のスレッドが先に進める順）。1 回目の反例は 1.5 秒、
2 回目の反例は 21 秒（合図を待つ 20 秒を超える）だった。試験が時間ではなく合図で順を決めていれば、どちらでも通る。

    python -X utf8 -B docs/agent-runs/2026-11-15-wiki-browse-stop-record-read/delayed_http_check.py [秒]
"""
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tests.wiki import test_browse_server as t  # noqa: E402

real_http = t.wiki_browse._http
DELAY = float(sys.argv[1]) if len(sys.argv) > 1 else 1.5


def delayed_http(*args, **kwargs):
    result = real_http(*args, **kwargs)
    time.sleep(DELAY)
    return result


class Delayed(t.UnreadableRecordTest):
    def setUp(self):
        super().setUp()
        patcher = mock.patch.object(t.wiki_browse, "_http", delayed_http)
        patcher.start()
        self.addCleanup(patcher.stop)


if __name__ == "__main__":
    names = ["test_stop_waits_while_the_finishing_server_removes_the_record",
             "test_control_stop_fails_while_the_finishing_server_removes_the_record",
             "test_stop_waits_while_the_record_is_delete_pending"]
    suite = unittest.TestSuite(Delayed(n) for n in names)
    sys.exit(0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1)
