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

4. (2026-10-19, TROUBLES «Втрати естафети при передачі») PreToolUse
   mcp__baton__baton_pass — передане next/openQuestions ЗАМІНЮЄ список
   (server.mjs:158-159), тож пункт поточного .baton/baton.json, якого нема
   в новому next/openQuestions/done/handoffNote (схожість — same() з
   tools/baton-diff.py), зникає. Є такі — ask зі списком (рішення
   користувача «Будь-яку втрату»). Бектест 45 передач #1…#58: питав би
   в 31, ловить 4 відкриті питання #56→#57.
Fail-open: будь-яка помилка читання — тиша.
"""
import json
import os
import re
import sys
from datetime import datetime, timedelta

REPO = "/data/data/com.termux/files/home/AgentReachProject"
LEDGER = os.environ.get("BATON_GUARD_LEDGER") or f"{REPO}/.baton/ledger.jsonl"
CURRENT = os.environ.get("BATON_GUARD_CURRENT") or f"{REPO}/.baton/baton.json"
FIELDS = (("next", "Далі"), ("openQuestions", "Відкрите питання"))
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


def lost_items(new):
    """[(мітка, пункт)] з поточної естафети, яких нема в переданому pass."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("baton_diff", f"{REPO}/tools/baton-diff.py")
    bd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bd)
    try:
        with open(CURRENT, encoding="utf-8") as f:
            old = json.load(f)
    except (OSError, ValueError):
        return []
    # непередане поле сервер лишає як було (server.mjs:158-159)
    pool = [str(x) for k in ("next", "openQuestions") for x in
            (new[k] if isinstance(new.get(k), list) else old.get(k) or [])]
    pool += [str(x) for x in new.get("done") or []] + [str(new.get("handoffNote") or "")]
    return [(label, str(item)) for key, label in FIELDS if isinstance(new.get(key), list)
            for item in old.get(key) or [] if not any(bd.same(item, y) for y in pool)]


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
        ti = data.get("tool_input") or {}
        nxt = ti.get("next")
        bad = [str(x)[:60] for x in nxt if not OWNER.match(str(x))] if isinstance(nxt, list) else []
        if bad:
            emit("PreToolUse", permissionDecision="deny",
                 permissionDecisionReason=(
                     "baton-guard: кожен пункт next починається з власника "
                     "(«@claude-code …», «@dsh …») — інакше обидва агенти беруть "
                     "той самий пункт (18.10, #52). Без власника: "
                     + " | ".join(bad) + ". Допиши @агент і передай знову."))
            return
        try:
            lost = lost_items(ti)
        except Exception:
            lost = []
        if lost:
            emit("PreToolUse", permissionDecision="ask",
                 permissionDecisionReason=(
                     f"baton-guard: передача прибирає {len(lost)} пункт(ів) поточної естафети — "
                     "вони зникнуть (19.10: 4 відкриті питання #56→#57 жили лише в TROUBLES). "
                     "Кожен — зроблено / у BACKLOG / відкинути: "
                     + " | ".join(f"[{l}] {' '.join(i.split())[:70]}" for l, i in lost)
                     + ". Дозволити передачу?"))
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
