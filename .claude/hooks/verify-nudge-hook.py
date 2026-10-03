#!/data/data/com.termux/files/usr/bin/python3
"""
PreToolUse hook (НЕ блокує): перед правкою захищеного файлу нагадує про
скіл verify-before-show (RULES.md:44). Вузько — лише захищені файли, раз
на файл за сесію; P4 стріляє на кожну правку, і на нього перестали
зважати.
Причина (trees/yakist-roboty-agentiv.md, Q3, 2026-10-03): скіл вжито у 2
з 48 сесій; того дня план змін ANALYZER.md і картки показано без звірки.
Кожне спрацювання пишеться в .claude/logs/verify-nudge.log — доказ для
воріт «доказ ужитку» (проба на 3 сесії).
Межа: правку через Bash (python/sed) не бачить — захищені файли правити
інструментом Edit/Write.
Будь-яка помилка — мовчить (fail-open).
"""
import fnmatch
import json
import os
import sys
import time

PROJECT = "/data/data/com.termux/files/home/AgentReachProject"
PROTECTED = [
    "RULES.md", "RULES-WHY.md", "CLAUDE.md", "AGENTS.md",
    "reference-analyzer/ANALYZER.md", "script-agent/AGENT.md",
    ".claude/hooks/*", ".claude/settings*.json", ".claude/skills/*/SKILL.md",
]
LOG = os.path.join(PROJECT, ".claude", "logs", "verify-nudge.log")
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def rel(path, cwd):
    path = os.path.expanduser(path)
    if not os.path.isabs(path):
        path = os.path.join(cwd or PROJECT, path)
    path = os.path.abspath(path)  # без realpath: CLAUDE.md — симлінк на RULES.md
    if not path.startswith(PROJECT + os.sep):
        return None
    return path[len(PROJECT) + 1:]


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") not in EDIT_TOOLS:
        return
    inp = data.get("tool_input") or {}
    r = rel(inp.get("file_path") or inp.get("notebook_path") or "", data.get("cwd"))
    if not r or not any(fnmatch.fnmatch(r, p) for p in PROTECTED):
        return
    sid = data.get("session_id", "?")
    key = f"{sid}\t{r}"
    seen = open(LOG).read() if os.path.exists(LOG) else ""
    if key + "\t" in seen:
        return  # раз на файл за сесію
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f:
        f.write(f"{key}\t{time.strftime('%Y-%m-%dT%H:%M:%S')}\n")
    msg = (f"Захищений файл {r}: чи звірено план цієї правки скілом "
           "verify-before-show (RULES.md:44)? Якщо ні — спершу звір; якщо так — "
           "один рядок «Звірено перед показом: …» у відповіді.")
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "additionalContext": msg}}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
