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
