#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12,<3.15"
# dependencies = []
# ///
"""UserPromptSubmit のフックの入口（ADR-0032）。hooks/hooks.json から uv で起動する。

標準入力のフックの入力（JSON）を読み、指示に関係しそうな wiki のページの候補を、
hookSpecificOutput.additionalContext として標準出力に書く。足すものがなければ何も書かない。

何が起きても、何も書かずに終了コード 0 で終わる。0 以外を返すと、利用者の画面に hook error の知らせが出て、
2 なら利用者の指示そのものが止まるためである（起動行の uv の段の 2 は、hooks.json の `; exit 0` で 0 にする）。
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

DEADLINE_SECONDS = 2.5


def worker(deadline: float) -> None:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import wiki_initialized
        import wiki_prompt_context as context

        raw = sys.stdin.buffer.read(context.MAX_STDIN_BYTES + 1)
        if len(raw) > context.MAX_STDIN_BYTES:
            return
        hook_input = json.loads(raw.decode("utf-8"))

        def is_wiki(root) -> bool:
            # 初期化された wiki（ルートに SCHEMA.md がある）だけを読む。なければ黙って何もしない。
            return wiki_initialized.check(root) is None

        picked = context.select(hook_input, env=dict(os.environ), is_wiki=is_wiki, deadline=deadline)
        if picked is not None:
            sys.stdout.buffer.write(json.dumps(context.selection_payload(picked), ensure_ascii=True).encode("ascii"))
            sys.stdout.buffer.flush()
    except BaseException:  # noqa: BLE001 - フックは何が起きても黙って 0 で終わる
        return


def main() -> None:
    """解析を別の Python プロセスに閉じ込め、OS の待ちと GIL を保持する処理にも期限を掛ける。"""
    started = time.monotonic()
    try:
        raw = sys.stdin.buffer.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            return
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import wiki_prompt_context as context

        hook_input = json.loads(raw.decode("utf-8"))
        env = dict(os.environ)
        if not isinstance(hook_input, dict) or not context.setting(env, "enabled"):
            return
        if hook_input.get("hook_event_name") not in (None, "UserPromptSubmit"):
            return
        if context.query_text(hook_input.get("prompt")) is None:
            # 飛ばす指示では解析の子を起こさない。既存セッションのターンだけを進める。
            # この分岐は正規表現による解析や wiki の走査をしない。状態の OS の待ちはタイマーで止める。
            import threading
            watchdog = threading.Timer(max(0, DEADLINE_SECONDS - (time.monotonic() - started)),
                                       os._exit, args=(0,))
            watchdog.daemon = True
            watchdog.start()
            try:
                context.tick_existing_state(hook_input, env, time.time())
            finally:
                watchdog.cancel()
            return
        import subprocess

        deadline = started + DEADLINE_SECONDS
        worker_deadline = deadline - 0.2  # 親の受け渡しに残す時間。子にも同じ時計の絶対時刻を渡す。
        remaining = worker_deadline - time.monotonic()
        if remaining <= 0:
            return
        result = subprocess.run(
            [sys.executable, "-I", str(Path(__file__).resolve()), "--worker", str(worker_deadline)],
            input=raw, capture_output=True, timeout=remaining,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        if result.returncode == 0 and result.stdout and time.monotonic() < deadline:
            import threading
            watchdog = threading.Timer(max(0, deadline - time.monotonic()), os._exit, args=(0,))
            watchdog.daemon = True
            watchdog.start()

            def emit(text):
                sys.stdout.buffer.write(context.hook_output(text).encode("ascii"))
                sys.stdout.buffer.flush()

            try:
                context.publish_selection(hook_input, context.selection_from_payload(json.loads(result.stdout)),
                                          env=env, emit=emit, deadline=deadline)
            finally:
                watchdog.cancel()
    except BaseException:  # noqa: BLE001 - 起動失敗とタイムアウトも利用者の指示を止めない
        return


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        worker(float(sys.argv[2]))
    else:
        main()
    # 標準出力の後始末で失敗しても 0 で終わる。
    os._exit(0)
