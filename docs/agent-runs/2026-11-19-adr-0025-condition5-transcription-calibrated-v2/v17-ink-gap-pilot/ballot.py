"""読み手に外部の道具を使わせず、構造化された最終回答を受領する。"""

import json


def unique(pairs):
    result = dict(pairs)
    if len(result) != len(pairs):
        raise ValueError("最終回答に同じJSONのキーが複数ある")
    return result


def session_and_response(events, family, model, last_message=None):
    if family == "gpt":
        (session,) = (x["thread_id"] for x in events if x.get("type") == "thread.started")
        (turn,) = (i for i, x in enumerate(events) if x.get("type") == "turn.completed")
        messages = []
        for i, entry in enumerate(events):
            if not entry["type"].startswith("item."):
                continue
            item = entry["item"]
            if item["type"] not in {"agent_message", "reasoning"}:
                raise ValueError("画像以外を読む道具が実行された")
            if entry["type"] == "item.completed" and item["type"] == "agent_message":
                messages.append((i, item["text"].strip()))
        position, final = messages[-1]
        if position >= turn or last_message is None or final != last_message.strip():
            raise ValueError("最終回答のファイルと正常終了した会話の最後の回答が異なる")
        return session, json.loads(final, object_pairs_hook=unique)
    (opened,) = (e for e in events if e.get("type") == "system" and e.get("subtype") == "init")
    (closed,) = (e for e in events if e.get("type") == "result")
    if (opened["model"] != model or opened.get("tools") != ["StructuredOutput"] or closed.get("is_error")
            or closed.get("subtype") != "success" or closed["session_id"] != opened["session_id"]):
        raise ValueError("構造化出力専用の新規会話として正常終了していない")
    replies = []
    for e in events:
        body = e.get("message", {}).get("content")
        if not isinstance(body, list):
            continue
        for part in body:
            if part.get("type") == "tool_use":
                if part.get("name") != "StructuredOutput":
                    raise ValueError("構造化回答以外の道具が実行された")
                replies.append(part["input"])
    if len(replies) != 1 or replies[0] != closed["structured_output"]:
        raise ValueError("構造化回答のイベントと最終結果が一致しない")
    return opened["session_id"], replies[0]


def entries(value, ids):
    if set(value) != {"answers"} or not isinstance(value["answers"], list):
        raise ValueError("最終回答の構造が違う")
    result = {}
    for row in value["answers"]:
        if set(row) != {"id", "status", "text"} or row["id"] not in ids or row["id"] in result:
            raise ValueError("対象のIDか最終回答の構造が違う")
        status, text = row["status"], row["text"]
        if not isinstance(text, str) or status not in {"empty", "unreadable", "readable"}:
            raise ValueError("行の状態かテキストの型が違う")
        if ((status == "empty" and text) or (status == "unreadable" and text != "?")
                or (status == "readable" and (not text.strip() or text.strip() == "?"))):
            result[row["id"]] = {"status": "unreadable", "text": "?"}
        else:
            result[row["id"]] = {"status": status, "text": text}
    if set(result) != set(ids):
        raise ValueError("最終回答に対象の過不足がある")
    return result
