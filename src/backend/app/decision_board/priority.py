from __future__ import annotations


def build_priority_items(board: dict) -> list[dict]:
    items = []

    for risk in board.get("risks", []):
        items.append({
            "level": "NOW",
            "type": "risk",
            "title": risk.get("title"),
            "reason": risk.get("summary"),
            "action": "确认风险处理方案"
        })

    for action in board.get("actions", []):
        items.append({
            "level": "NEXT",
            "type": "action",
            "title": action.get("text"),
            "reason": "当前会议下一步行动",
            "action": action.get("text")
        })

    for todo in board.get("todos", []):
        items.append({
            "level": "LATER",
            "type": "todo",
            "title": todo.get("text"),
            "reason": todo.get("reason"),
            "action": "后续确认"
        })

    return items
