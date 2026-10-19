#!/data/data/com.termux/files/usr/bin/python3
"""
Нагадування ціни сесії (2026-10-19, BACKLOG «Механізми класів помилок сесії
1fe9acd7» п.2; рішення користувача «Так, $10 і $20»).

UserPromptSubmit: бере останній запис цієї сесії з .claude/logs/session-cost.jsonl
(пише статуслайн statusline-cost.py — із запізненням на одне оновлення) і, коли
ціна вперше перетнула поріг THRESHOLDS, один раз на поріг показує користувачу
(systemMessage) і агенту (additionalContext): закрити тему й почати нову сесію.

Чому так (бектест журналу 2026-10-19, verify-before-show): з 44 сесій $10
досягла 21, $20 — 13; після $10 лише 2 подорожчали менше ніж на $2 (1fe9acd7 ще
+$33.5, 3efa3a9d ще +$44.4). Текстове «радити закрити раніше» (watch-out 16.10)
не спрацювало — тому повідомлення бачить сам користувач. Паузу не нагадуємо:
35 пауз ≥1 год дали приріст ≤$2.23 (понад $0.35 — двічі). Fail-open.
"""
import json
import os
import sys

REPO = "/data/data/com.termux/files/home/AgentReachProject"
LOG = os.environ.get("COST_NUDGE_LOG") or f"{REPO}/.claude/logs/session-cost.jsonl"
STATE = os.environ.get("COST_NUDGE_STATE") or f"{REPO}/.claude/logs/cost-nudge-state.json"
THRESHOLDS = (10, 20)
TAIL = 65536


def last_record(sid):
    try:
        with open(LOG, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - TAIL))
            lines = f.read().decode("utf-8", "ignore").splitlines()
    except OSError:
        return None
    for line in reversed(lines):
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if rec.get("session_id") == sid:
            return rec
    return None


def main():
    try:
        data = json.load(sys.stdin)
    except (ValueError, OSError):
        return
    sid = data.get("session_id") or ""
    rec = last_record(sid) if sid else None
    if not rec:
        return
    cost, pct = float(rec.get("cost") or 0), rec.get("pct")
    try:
        state = json.load(open(STATE, encoding="utf-8"))
    except (OSError, ValueError):
        state = {}
    shown = state.get(sid, [])
    new = [t for t in THRESHOLDS if cost >= t and t not in shown]
    if not new:
        return
    state[sid] = shown + new
    state = dict(list(state.items())[-30:])
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(state, f)
    ctx = f", контекст {pct}%" if pct is not None else ""
    msg = (f"💸 Сесія вже ${cost:.2f}{ctx} (поріг ${max(new)}). Кожна нова тема тут "
           f"перечитує весь контекст. Рекомендація: закрити тему (session-close) і "
           f"почати нову сесію — естафета перенесе стан.")
    print(json.dumps({
        "systemMessage": msg,
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": msg + " Скажи це користувачу одним рядком на початку "
                                       "відповіді і запропонуй закриття, коли поточний "
                                       "крок дійде до воріт.",
        },
    }, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
