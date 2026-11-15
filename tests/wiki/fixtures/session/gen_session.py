"""合成のセッションの記録（JSONL）を作る生成器。実物の記録は使わない。

- `Builder` で記録を 1 件ずつ足し、`to_bytes()` で JSONL のバイト列にする。
- `generate(seed)` は、設計の試験の節が挙げる記録（知らない type、uuid のない知らない種類、一覧にない attachment、
  queued_command の人・通知・prompt が文字列でないもの、isMeta の伝言、壊れた行、親がアシスタントの連鎖、循環する
  parentUuid、思考に入れた目印、秘密の目印）を、種で決まる順に混ぜる。

目印:
- `NOSHOW` は、raw に出てはならない内容（思考、ツールの結果、通知、伝言、差し込み、知らない記録）にだけ入れる。
- 人の発言には `H<番号>`、アシスタントの本文には `A<番号>` の札を入れる。試験は札から宛先を照らす。
"""
from __future__ import annotations

import json
import random
import uuid as uuidlib
from datetime import datetime, timedelta, timezone

NOSHOW = "NOSHOW-思考の目印"
SESSION_ID = "0b6c7c1e-1111-4222-8333-944455556666"
SECRET_EMAIL = "alice.smith@example.org"
SECRET_KEY = "sk-ant-api03-ABCDEFGHIJKLMNOPQRSTUV"
START = datetime(2026, 11, 14, 0, 0, 0, tzinfo=timezone.utc)


class Builder:
    def __init__(self, session_id: str = SESSION_ID, cwd: str = "C:\\Users\\alice\\proj", branch: str = "main",
                 version: str = "2.1.321", seed: int = 0):
        self.session_id = session_id
        self.cwd = cwd
        self.branch = branch
        self.version = version
        self.lines: list[bytes] = []
        self.records: list[dict] = []
        self.last: str | None = None
        self.count = 0
        self.seed = seed

    # 記録の土台
    def new_uuid(self) -> str:
        self.count += 1
        return str(uuidlib.UUID(int=(self.seed << 64) + self.count))

    def _base(self, rtype: str, parent, **extra) -> dict:
        uid = self.new_uuid()
        rec = {"parentUuid": self.last if parent is ... else parent, "isSidechain": False, "type": rtype,
               "uuid": uid, "timestamp": (START + timedelta(seconds=self.count)).isoformat().replace("+00:00", "Z"),
               "sessionId": self.session_id, "cwd": self.cwd, "gitBranch": self.branch, "version": self.version}
        rec.update(extra)
        return rec

    def add(self, rec: dict) -> str | None:
        self.records.append(rec)
        self.lines.append(json.dumps(rec, ensure_ascii=False).encode("utf-8"))
        if "uuid" in rec:
            self.last = rec["uuid"]
        return rec.get("uuid")

    def raw_line(self, data: bytes) -> None:
        self.lines.append(data)

    def to_bytes(self) -> bytes:
        return b"".join(line + b"\n" for line in self.lines)

    # 人の発言
    def human(self, content, parent=..., **extra) -> str:
        return self.add(self._base("user", parent, message={"role": "user", "content": content},
                                   origin={"kind": "human"}, promptSource="sdk", **extra))

    def queued(self, prompt, origin_kind=None, parent=...) -> str:
        att = {"type": "queued_command", "prompt": prompt}
        if origin_kind is not None:
            att["origin"] = {"kind": origin_kind}
        return self.add(self._base("attachment", parent, attachment=att))

    def user(self, content, parent=..., **extra) -> str:
        return self.add(self._base("user", parent, message={"role": "user", "content": content}, **extra))

    def interrupt(self, parent=..., tool=False) -> str:
        text = "[Request interrupted by user for tool use]" if tool else "[Request interrupted by user]"
        return self.user([{"type": "text", "text": text}], parent)

    def tool_result(self, parent=..., content=NOSHOW) -> str:
        return self.user([{"type": "tool_result", "tool_use_id": "toolu_x", "content": content}], parent)

    # アシスタント
    def assistant(self, blocks, parent=..., model="claude-opus-5-5", **extra) -> str:
        return self.add(self._base("assistant", parent, message={"role": "assistant", "model": model,
                                                                 "content": blocks}, **extra))

    def text(self, text, parent=..., **kw) -> str:
        return self.assistant([{"type": "text", "text": text}], parent, **kw)

    def thinking(self, parent=...) -> str:
        return self.assistant([{"type": "thinking", "thinking": NOSHOW, "signature": "x"}], parent)

    def tool_use(self, name="Bash", inputs=None, parent=...) -> str:
        inputs = {"command": NOSHOW, "description": "一覧を見る"} if inputs is None else inputs
        return self.assistant([{"type": "tool_use", "id": "toolu_x", "name": name, "input": inputs}], parent)

    # そのほか
    def attachment(self, atype="hook_success", parent=..., **att) -> str:
        return self.add(self._base("attachment", parent, attachment={"type": atype, "content": NOSHOW, **att}))

    def system(self, subtype="stop_hook_summary", parent=...) -> str:
        return self.add(self._base("system", parent, subtype=subtype, content=NOSHOW))

    def uuidless(self, rtype="last-prompt") -> None:
        self.add({"type": rtype, "sessionId": self.session_id, "lastPrompt": NOSHOW})


INPUTS = ("human", "human", "human", "human_list", "command", "queued_human", "queued_notification", "queued_none",
          "queued_list", "notification_user", "peer_meta", "skill_meta", "compact", "plain_user", "unknown_type",
          "unlisted_attachment", "system_local", "interrupt")


def emit_input(b: Builder, kind: str, tag: str) -> str:
    if kind == "human":
        return b.human(f"発言 {tag} についての相談")
    if kind == "human_list":
        return b.human([{"type": "text", "text": f"発言 {tag} の図"}, {"type": "image", "source": {"data": NOSHOW}},
                        {"type": "document", "source": {"data": NOSHOW}}])
    if kind == "command":
        return b.human(f"<command-message>x</command-message>\n<command-name>/wiki:query</command-name>\n"
                       f"<command-args>{tag} の答え</command-args>")
    if kind == "queued_human":
        return b.queued(f"発言 {tag} をキューに", "human")
    if kind == "queued_notification":
        return b.queued(NOSHOW, "task-notification")
    if kind == "queued_none":
        return b.queued(NOSHOW)
    if kind == "queued_list":
        return b.queued([{"type": "text", "text": NOSHOW}], "human")
    if kind == "notification_user":
        return b.user(NOSHOW, origin={"kind": "task-notification"})
    if kind == "peer_meta":
        return b.user(NOSHOW, isMeta=True, origin={"kind": "peer"})
    if kind == "skill_meta":
        return b.user(NOSHOW, isMeta=True)
    if kind == "compact":
        return b.user(NOSHOW, isCompactSummary=True)
    if kind == "plain_user":
        return b.user(NOSHOW)
    if kind == "unknown_type":
        return b.add(b._base("mystery-record", ..., content=NOSHOW))
    if kind == "unlisted_attachment":
        return b.attachment("future_thing")
    if kind == "system_local":
        return b.add(b._base("system", ..., subtype="local_command", content=NOSHOW))
    if kind == "interrupt":
        return b.interrupt(tool=bool(len(tag) % 2))
    raise ValueError(kind)


def generate(seed: int, steps: int = 40) -> Builder:
    """種で決まる合成のセッション。H の札は H<n>、A の札は A<n>。"""
    rng = random.Random(seed)
    b = Builder(seed=seed)
    b.uuidless("custom-title")
    b.human(f"発言 H0 から始める。連絡先は {SECRET_EMAIL}、鍵は {SECRET_KEY}")
    a_count = 0
    for step in range(1, steps + 1):
        kind = rng.choice(INPUTS)
        emit_input(b, kind, f"H{step}")
        for _ in range(rng.randint(0, 2)):
            rng.choice([lambda: b.attachment(rng.choice(["hook_success", "edited_text_file", "date_change"])),
                        lambda: b.system("stop_hook_summary")])()
        if rng.random() < 0.1:
            b.raw_line(b'{"broken": ')
        if rng.random() < 0.1:
            b.uuidless(rng.choice(["last-prompt", "never-seen-before"]))
        for _ in range(rng.randint(1, 4)):
            r = rng.random()
            if r < 0.25:
                b.thinking()
            elif r < 0.45:
                b.tool_use()
                b.tool_result()
            elif r < 0.5:
                b.assistant([{"type": rng.choice(["redacted_thinking", "advisor_tool_result", "future_block"]),
                              "data": NOSHOW}])
            else:
                a_count += 1
                b.text(f"返答 A{a_count} です")
    # 循環する parentUuid と、親が範囲にない返答
    u1, u2 = b.new_uuid(), b.new_uuid()
    a_count += 1
    b.add({**b._base("assistant", u2, message={"role": "assistant", "model": "m", "content": [
        {"type": "text", "text": f"返答 A{a_count} です"}]}), "uuid": u1})
    a_count += 1
    b.add({**b._base("assistant", u1, message={"role": "assistant", "model": "m", "content": [
        {"type": "thinking", "thinking": NOSHOW}]}), "uuid": u2})
    a_count += 1
    b.text(f"返答 A{a_count} です", parent="ffffffff-ffff-4fff-8fff-ffffffffffff")
    return b
