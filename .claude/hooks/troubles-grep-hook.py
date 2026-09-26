#!/data/data/com.termux/files/usr/bin/python3
"""
PreToolUse hook: автоматизує правило RULES.md "Перед новою дією — grep
по TROUBLES.md". Шукає слова з Bash-команди проти TAGS: рядків у
TROUBLES.md (той самий метод, що файл сам радить: "шукай по мітці").
Тільки інформує (additionalContext), нічого не блокує.
"""
import sys
import json
import re

TROUBLES_PATH = "/data/data/com.termux/files/home/AgentReachProject/TROUBLES.md"
MAX_HITS = 5

# Занадто загальні теги — збігаються майже з будь-якою командою,
# дають шум замість сигналу (знайдено емпірично 2026-09-19)
GENERIC_TAGS = {
    "pip", "npm", "node", "exit", "mcp", "hook", "agents", "path",
    "env", "timeout", "verification", "unverified", "backlog",
    "termux", "install", "config", "git", "python",
}


HINT_PREFIX = "TROUBLES.md має релевантні записи"


def already_shown(transcript_path):
    """Заголовки, які цей хук уже показав після останнього стиснення
    контексту. Як Claude Code для SubagentStart: не повторювати копію,
    що вже в контексті; після compaction показати знову. Журнал пишеться
    асинхронно, тож зрідка підказка повториться — це безпечно. Будь-яка
    помилка → порожня множина (поведінка як до правки)."""
    shown = set()
    if not transcript_path:
        return shown
    try:
        with open(transcript_path, "rb") as f:
            raw = f.read()
        start = raw.rfind(b'"subtype":"compact_boundary"')
        start = raw.rfind(b"\n", 0, start) + 1 if start != -1 else 0
        marker = HINT_PREFIX.encode("utf-8")
        for line in raw[start:].splitlines():
            if marker not in line or b"hook_additional_context" not in line:
                continue
            try:
                att = json.loads(line).get("attachment") or {}
            except ValueError:
                continue
            content = att.get("content")
            parts = content if isinstance(content, list) else [content]
            for part in parts:
                if not isinstance(part, str) or HINT_PREFIX not in part:
                    continue
                for item in part.split("\n- ")[1:]:
                    shown.add(item.rsplit(" (тег: ", 1)[0].strip())
    except Exception:
        return set()
    return shown


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return
    command = data.get("tool_input", {}).get("command", "")
    if not command:
        return

    try:
        with open(TROUBLES_PATH, encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        return

    sections = []
    current_header = None
    for line in text.splitlines():
        if line.startswith("## "):
            current_header = line[3:].strip()
        elif line.startswith("TAGS:"):
            tags = [t.strip().lower() for t in line[len("TAGS:"):].split(",")]
            tags = [t for t in tags if t and t not in GENERIC_TAGS]
            sections.append((current_header, tags))

    words = set(re.findall(r"[a-zA-Zа-яіїєА-ЯІЇЄ0-9_-]{3,}", command.lower()))

    hits = []
    seen_headers = set()
    for header, tags in sections:
        if header in seen_headers:
            continue
        for tag in tags:
            if tag in words:
                hits.append(f"{header} (тег: {tag})")
                seen_headers.add(header)
                break

    # Не повторювати записи, які агент уже бачить у контексті
    # (92% підказок були повторами в межах сесії, заміряно 2026-09-26)
    shown = already_shown(data.get("transcript_path"))
    hits = [h for h in hits if h.rsplit(" (тег: ", 1)[0] not in shown]

    if not hits:
        return

    hits = hits[:MAX_HITS]
    context = "TROUBLES.md має релевантні записи для цієї команди:\n- " + "\n- ".join(hits)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": context,
        }
    }))


if __name__ == "__main__":
    main()
