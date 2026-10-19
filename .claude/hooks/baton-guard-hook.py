#!/data/data/com.termux/files/usr/bin/python3
"""
Охоронець естафети (2026-10-19, BACKLOG «Механізми класів помилок сесії
1fe9acd7» п.1; TROUBLES «Обидва агенти підхопили ту саму естафету #52»).

Сервер baton (@timurabi3/baton-mcp 0.1.0) — естафета «активний один», але
блокування не має, а пункти next — рядки без власника. 18.10 обидва агенти
підхопили pass #52 за 6 хв і взяли той самий next 1. Три події:

1. PreToolUse mcp__baton__baton_pass — кожен ПЕРЕДАНИЙ пункт next має
   починатися з «@агент» (@claude-code, @dsh), інакше deny з поясненням.
   next не передано — сервер лишає попередні пункти; не перевіряємо.
2. PostToolUse mcp__baton__baton_pick_up — ⚠, якщо поточний pass за останні
   WINDOW_H год підхопив інший агент (одразу, ще до роботи в цьому ході).
3. UserPromptSubmit — той самий ⚠, поки після подвійного pick_up не було pass
   (ловить і порядок «DSH підхопив після мене»).

Бектест на .baton/ledger.jsonl (219 записів): подвійні pick_up — #11 (11 днів),
#16 (7 хв), #35 (39 хв), #52 (6 хв); вікно 12 год ловить 16/35/52. Пункти next
без @ — у знімках pass-39…53 усі, pass-54 1 з 9 (verify-before-show 3/3 ТАК).
DSH працює не на хуках Claude — ворота 1 його pass не зупиняють.
Fail-open: будь-яка помилка читання — тиша.
"""
import json
import os
import re
import sys
from datetime import datetime, timedelta

REPO = "/data/data/com.termux/files/home/AgentReachProject"
LEDGER = os.environ.get("BATON_GUARD_LEDGER") or f"{REPO}/.baton/ledger.jsonl"
WINDOW_H = 12
OWNER = re.compile(r"\s*@[\w-]+")


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def double_pickup():
    """(pass, [(агент, час)]) якщо останній pass підхопили ≥2 агенти в межах
    WINDOW_H год і нового pass ще не було; інакше None."""
    try:
        with open(LEDGER, encoding="utf-8") as f:
            rows = [json.loads(l) for l in f if l.strip()]
    except (OSError, ValueError):
        return None
    last_pass = None
    picks = []
    for r in rows:
        if r.get("event") == "pass":
            last_pass, picks = r.get("pass"), []
        elif r.get("event") == "pick_up" and r.get("pass") == last_pass:
            picks.append((r.get("agent"), r.get("t")))
    first = {}
    for a, t in picks:
        first.setdefault(a, t)
    if len(first) < 2:
        return None
    times = sorted(ts(t) for t in first.values())
    if times[-1] - times[0] > timedelta(hours=WINDOW_H):
        return None
    return last_pass, sorted(first.items(), key=lambda x: x[1])


def warn_text(dp):
    p, who = dp
    lst = ", ".join(f"{a} о {t[11:16]} UTC" for a, t in who)
    return (f"⚠ Естафету #{p} підхопили кілька агентів: {lst}. Протокол baton — "
            f"«активний один», блокування немає (18.10 так обидва взяли той самий "
            f"next). Перш ніж братися за пункт — звір з іншим агентом, чий він "
            f"(@власник у next), або скажи користувачу.")


def emit(event, **extra):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event, **extra}},
                     ensure_ascii=False))


def main():
    try:
        data = json.load(sys.stdin)
    except (ValueError, OSError):
        return
    event = data.get("hook_event_name", "")
    tool = data.get("tool_name", "")

    if event == "PreToolUse" and tool.endswith("baton_pass"):
        nxt = (data.get("tool_input") or {}).get("next")
        if not isinstance(nxt, list):
            return
        bad = [str(x)[:60] for x in nxt if not OWNER.match(str(x))]
        if bad:
            emit("PreToolUse", permissionDecision="deny",
                 permissionDecisionReason=(
                     "baton-guard: кожен пункт next починається з власника "
                     "(«@claude-code …», «@dsh …») — інакше обидва агенти беруть "
                     "той самий пункт (18.10, #52). Без власника: "
                     + " | ".join(bad) + ". Допиши @агент і передай знову."))
        return

    if (event == "PostToolUse" and tool.endswith("baton_pick_up")) or \
            event == "UserPromptSubmit":
        dp = double_pickup()
        if dp:
            emit(event, additionalContext=warn_text(dp))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
