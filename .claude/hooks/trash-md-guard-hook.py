#!/data/data/com.termux/files/usr/bin/python3
"""
PreToolUse hook (БЛОКУЄ): вимагає свіжий запис у TRASH.md ПЕРЕД
виконанням rm/rmdir у Bash. Правило RULES.md: "Кожне видалення
(rm/rmdir) — записати в TRASH.md ДО виконання, не після". Прецедент
(RULES.md): інший AI-агент випадково видалив цілу домашню
директорію через зайвий символ у rm -rf.

Пропускає (не блокує): команди, чиї цілі — ВИКЛЮЧНО файли всередині
scratchpad_dir поточної сесії або системних tmp-каталогів —
одноразові тестові артефакти сесії, не проєктні чи домашні дані.
Якщо ціль незрозуміла (немає шляху з "/", напр. голий "rm -rf ." чи
"rm -rf *") — вважається НЕ безпечною (консервативний дефолт).
"""
import sys
import json
import re
import os
import time

TRASH_PATH = "/data/data/com.termux/files/home/AgentReachProject/TRASH.md"
FRESH_SECONDS = 300  # 5 хвилин

RM_RE = re.compile(r"(?:^|[;&|\n]|\bsudo\s+)\s*(rm|rmdir)\b")

SAFE_PREFIXES = (
    "/data/data/com.termux/files/usr/tmp/",
    "/tmp/",
)


def targets_are_safe(command, scratchpad_dir):
    prefixes = list(SAFE_PREFIXES)
    if scratchpad_dir:
        prefixes.append(scratchpad_dir)
    tokens = command.split()
    paths = [t for t in tokens if "/" in t and not t.startswith("-")]
    if not paths:
        return False  # немає явного шляху — не ризикуємо, перевіряємо TRASH.md
    return all(any(p.startswith(prefix) for prefix in prefixes) for p in paths)


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return

    command = data.get("tool_input", {}).get("command", "")
    if not command or not RM_RE.search(command):
        return

    scratchpad_dir = data.get("scratchpad_dir", "")
    if targets_are_safe(command, scratchpad_dir):
        return

    try:
        mtime = os.path.getmtime(TRASH_PATH)
    except OSError:
        mtime = 0

    age = time.time() - mtime
    if age <= FRESH_SECONDS:
        return  # TRASH.md щойно оновлено — вважаємо, що запис зроблено

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Заблоковано: RULES.md вимагає запис у TRASH.md ДО rm/rmdir, "
                f"а TRASH.md не оновлювався останні {FRESH_SECONDS}с. Спочатку "
                f"допиши запис (шлях, причина), потім повтори команду."
            ),
        }
    }))


if __name__ == "__main__":
    main()
