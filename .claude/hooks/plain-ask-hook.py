#!/data/data/com.termux/files/usr/bin/python3
"""PreToolUse AskUserQuestion: питання з кодом задачі без назви словами — не показувати (2026-10-16).

Навіщо: користувач 15.10 — «я вже казав що не розумію шифри … і відповідаю не зрозумівши»:
«так» на питання з шифром — не його рішення. Правило 16.10: «розшифровувати потрібно раз у
повідомленні, або залишати дерево». Перевірка — tools/plain-codes.py (undecoded, ask_text).
Знайшов код без назви → deny з причиною: Claude переписує питання (документація хуків:
PreToolUse «Matches on any tool name… AskUserQuestion»; «"deny" prevents the tool call»).
Журнал: .claude/logs/plain-ask.jsonl (кожен запуск). Будь-яка помилка — мовчки (fail-open).
Відкат: прибрати запис plain-ask-hook з PreToolUse у .claude/settings.local.json.
"""
import datetime
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG = os.path.join(ROOT, ".claude", "logs", "plain-ask.jsonl")


def load():
    spec = importlib.util.spec_from_file_location("plain_codes",
                                                  os.path.join(ROOT, "tools", "plain-codes.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") != "AskUserQuestion":
        return
    pc = load()
    codes = pc.undecoded(pc.ask_text(data.get("tool_input")))
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"t": datetime.datetime.now().isoformat(timespec="seconds"),
                            "session": data.get("session_id"), "codes": codes},
                           ensure_ascii=False) + "\n")
    if codes:
        reason = ("plain-ask: у питанні коди задач без назви словами: " + ", ".join(codes)
                  + ". Користувач їх не розуміє і відповідає не зрозумівши. Перепиши питання: "
                  "назва словами, код — хіба в дужках після неї (назву бери з "
                  "python3 tools/trees-index.py <код>), і задай його знову.")
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                                 "permissionDecision": "deny",
                                                 "permissionDecisionReason": reason}},
                         ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
