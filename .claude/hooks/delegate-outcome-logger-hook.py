#!/data/data/com.termux/files/usr/bin/python3
"""
PostToolUse hook на mcp__delegate__delegate / mcp__deepseek__deepseek(-reply):
логує кожен виклик у .claude/logs/delegate-calls.jsonl (час, tool, модель,
task, прев'ю промту, результат) — щоб мати РЕАЛЬНІ дані про частоту
збоїв і сильні/слабкі сторони моделей, а не здогадки заднім числом.

Чесне обмеження: для викликів, що йдуть у фон (>120с), tool_response
цього PostToolUse може містити лише проміжне "moved to background"
повідомлення, а не фінальний результат — такі записи позначаються
outcome="backgrounded_unknown", не "success"/"error". Фінальний
результат фонової задачі приходить окремим каналом (task-notification),
який цей хук не бачить.
"""
import sys
import json
import re
from datetime import datetime, timezone

LOG_PATH = "/data/data/com.termux/files/home/AgentReachProject/.claude/logs/delegate-calls.jsonl"
ERROR_RE = re.compile(r'\b(error|failed|exception)\b|"exit_code"\s*:\s*[1-9]', re.IGNORECASE)
BACKGROUND_RE = re.compile(r"moved to (?:the )?background", re.IGNORECASE)


def as_text(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(value)


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return

    tool_name = data.get("tool_name", "")
    if "delegate" not in tool_name and "deepseek" not in tool_name:
        return

    tool_input = data.get("tool_input", {}) or {}
    # Різні поля залежно від події — PostToolUse дає tool_response,
    # PostToolUseFailure може давати error/tool_error/reason/message.
    # Беремо все, що є, а не покладаємось на одну конкретну назву.
    resp = " ".join(filter(None, [
        as_text(data.get("tool_response")),
        as_text(data.get("error")),
        as_text(data.get("tool_error")),
        as_text(data.get("reason")),
        as_text(data.get("message")),
    ]))
    hook_event = data.get("hook_event_name", "")

    if hook_event == "PostToolUseFailure":
        outcome = "error"
    elif BACKGROUND_RE.search(resp):
        outcome = "backgrounded_unknown"
    elif ERROR_RE.search(resp):
        outcome = "error"
    else:
        outcome = "success"

    entry = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tool": tool_name,
        "hook_event": hook_event,
        "model": tool_input.get("model") or "default",
        "task": tool_input.get("task"),
        "prompt_preview": (tool_input.get("prompt") or "")[:100],
        "outcome": outcome,
        "response_preview": resp[:200],
    }

    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass


if __name__ == "__main__":
    main()
