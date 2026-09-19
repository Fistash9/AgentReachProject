#!/data/data/com.termux/files/usr/bin/python3
"""
PreToolUse hook: нагадує про застарілий baton_pass на git push.

Не автоматизує сам baton_pass (потребує LLM-синтезу handoffNote — не
детерміноване завдання). Автоматизує лише ТРИГЕР: рахує коміти від
останнього "pass" у .baton/ledger.jsonl, нагадує, якщо поріг
перевищено. Тільки інформує (additionalContext), нічого не блокує.

Прецедент: Tamircohen28/tamirs-superpowers має "handoff-reminder" —
той самий концепт, підтверджено реальним (2026-09-19).
"""
import sys
import json
import subprocess

REPO = "/data/data/com.termux/files/home/AgentReachProject"
LEDGER = f"{REPO}/.baton/ledger.jsonl"
THRESHOLD = 5  # комітів від останнього pass


def last_pass_time():
    try:
        with open(LEDGER, encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        return None
    for line in reversed(lines):
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("event") == "pass":
            return entry.get("t")
    return None


def commits_since(iso_timestamp):
    result = subprocess.run(
        ["git", "-C", REPO, "log", f"--since={iso_timestamp}", "--oneline"],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode != 0:
        return None
    lines = [l for l in result.stdout.splitlines() if l.strip()]
    return len(lines)


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return
    command = data.get("tool_input", {}).get("command", "")
    if "git push" not in command:
        return

    ts = last_pass_time()
    if ts is None:
        return

    count = commits_since(ts)
    if count is None or count < THRESHOLD:
        return

    context = (
        f"⏰ {count} комітів з останнього baton_pass — розглянь виклик "
        f"baton_pass, щоб handoff не застарів."
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": context,
        }
    }))


if __name__ == "__main__":
    main()
