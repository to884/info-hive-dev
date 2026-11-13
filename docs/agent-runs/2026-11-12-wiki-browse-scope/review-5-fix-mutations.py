"""5 回目のレビューの直しで足した試験が、わざと壊した実装を見つけるかを確かめる。

ソースは書き換えず、モックで実装を差し替えてから試験を 1 つずつ流す。どれも「落ちた（失敗: ...）」になれば、
試験はその壊し方を見つける。結果は review-5-fix-mutations-output.txt に残した。

実行（リポジトリのルートで）:
    uv run --python 3.12 --with pyyaml==6.0.3 python -X utf8 docs/agent-runs/2026-11-12-wiki-browse-scope/review-5-fix-mutations.py
"""
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import tests.wiki.test_browse as tb  # noqa: E402
import tests.wiki.test_browse_server as ts  # noqa: E402

core = tb.core
wb = tb.wiki_browse
real_snapshot = core.take_snapshot


def read_config(root):
    # 作業領域の設定を読んで捨てる
    (Path(root).parent / ".info-hive" / "workspace.json").read_text(encoding="utf-8")
    return real_snapshot(root)


def stat_git(root):
    # .git があるかだけを調べる
    (Path(root).parent.parent / ".git").exists()
    return real_snapshot(root)


def list_parent(root):
    # 祖先を一覧して、名前で .git を探す（おとりそのものには触れない）
    [e.name for e in os.scandir(Path(root).parent.parent) if e.name == ".git"]
    return real_snapshot(root)


def run(case, name):
    result = unittest.TextTestRunner(verbosity=0, stream=io.StringIO()).run(unittest.TestSuite([case(name)]))
    probs = result.failures + result.errors
    why = probs[0][1].strip().splitlines()[-1] if probs else ""
    tmp = os.path.normcase(tempfile.gettempdir())
    for form in (tmp.replace(os.sep, os.sep * 2), tmp):   # 記録に一時ディレクトリの絶対パスを残さない
        why = why.replace(form, "<tmp>")
    kind = "失敗" if result.failures else ("例外" if result.errors else "")
    return "通った（見逃した）" if result.wasSuccessful() else f"落ちた（{kind}: {why}）"


cases = []
for label, fake in (("設定を読んで捨てる", read_config), ("stat で .git を調べる", stat_git),
                    ("祖先を一覧して .git を探す", list_parent)):
    with mock.patch.object(core, "take_snapshot", side_effect=fake):
        cases.append((label, run(tb.ScopeTest, "test_scope_is_not_inferred_from_the_surroundings")))

# 新しく起動したときの出力に、そろえていない引数をそのまま書く
real_emit = wb._emit
real_serve = wb.serve


def raw_serve(root, page, open_browser, idle, verbose=False, scope=None):
    def emit(url, port, reused, state, ob, drawn):
        return real_emit(url, port, reused, state, ob, drawn if reused else scope)
    with mock.patch.object(wb, "_emit", side_effect=emit):
        return real_serve(root, page, open_browser, idle, verbose, scope)


with mock.patch.object(wb, "serve", side_effect=raw_serve):
    cases.append(("新しく起動したときの出力に引数をそのまま書く",
                  run(ts.ServeScopeTest, "test_server_keeps_one_normalized_scope")))

# 中核がないあいだ、操作の口がスコープを答えない
real_control = wb.Handler._control


def control_without_scope_before_build(self, rest):
    app = self.server.app
    if rest and rest[0] == "status" and app.state.current is None:
        return self._json(200, {"instance": app.instance, "wiki_key": app.key, "scope": None})
    return real_control(self, rest)


with mock.patch.object(wb.Handler, "_control", control_without_scope_before_build):
    cases.append(("組み立てる前は、操作の口がスコープを答えない",
                  run(ts.ServeScopeTest, "test_output_is_the_scope_drawn_once_built_even_while_the_first_build_fails")))

for label, verdict in cases:
    print(f"{label}: {verdict}")
