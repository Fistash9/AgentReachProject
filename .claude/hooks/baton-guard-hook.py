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
   2026-10-23: ask → deny (BACKLOG «План на наступну сесію…», доповнення 23.10 п.2; TROUBLES
   «Висновки сесії cfca89fe…» п.1: запити «ask» погоджують за звичкою). Статус — текстом пункту в done/handoffNote.
5. PostToolUse baton_pick_up — будує .baton/HANDOFF-view.md і підказує прочитати його цілим (23.10).
   «view FAIL» (не вмістилось / неповний) — підказка «НЕПОВНИЙ», а не тиша (23.10, рецензія cfca89fe).
6. (2026-10-25, m3-diag варіант Б) PreToolUse baton_pass — handoffNote сервер ЗАМІНЮЄ (server.mjs:156):
   речення поточної записки з ознакою кроку (STEP у baton-diff.py), яких нема в новому
   next/openQuestions/done/watchOut/handoffNote (та сама same()), — ПІДКАЗКА (additionalContext), не ask/deny.
   Чому не deny: на краю ліміту deny може не дати передати (#81 — «на 5% ліміту»). Чому не ask: бектест
   155 сусідніх передач ledger — 44 тривоги у 36 передачах (кожна ~4-та), у вибірці 10 (seed 2510) хибних 9;
   ask на 90% хибних погоджують за звичкою (23.10). Відома відповідь: #78→#79 1, #80→#81 1, #76→#77 0.
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


DIFF = os.environ.get("BATON_GUARD_DIFF") or f"{REPO}/tools/baton-diff.py"


def _ctx(new):
    """(baton_diff, поточна естафета, рядки нової естафети) або None."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("baton_diff", DIFF)
    bd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bd)
    try:
        with open(CURRENT, encoding="utf-8") as f:
            old = json.load(f)
    except (OSError, ValueError):
        return None
    # непередане поле сервер лишає як було (server.mjs:158-159)
    pool = [str(x) for k in ("next", "openQuestions") for x in
            (new[k] if isinstance(new.get(k), list) else old.get(k) or [])]
    pool += [str(x) for k in ("done", "watchOut") for x in new.get(k) or []] + [str(new.get("handoffNote") or "")]
    return bd, old, pool


def lost_items(new):
    """[(мітка, пункт)] з поточної естафети, яких нема в переданому pass."""
    c = _ctx(new)
    if not c:
        return []
    bd, old, pool = c
    return [(label, str(item)) for key, label in FIELDS if isinstance(new.get(key), list)
            for item in old.get(key) or [] if not any(bd.same(item, y) for y in pool)]


def lost_note(new):
    """Пункти поточної записки (речення з ознакою кроку), яких нема в переданому pass (6)."""
    c = _ctx(new)
    if not c:
        return []
    bd, old, pool = c
    return bd.note_lost(old.get("handoffNote") or "", pool)


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
        try:
            note = lost_note(ti)
        except Exception:
            note = []
        note_txt = " | ".join(f"[Записка] {' '.join(i.split())[:90]}" for i in note)
        if lost:
            emit("PreToolUse", permissionDecision="deny",
                 permissionDecisionReason=(
                     f"baton-guard: передача прибирає {len(lost)} пункт(ів) поточної естафети без статусу — "
                     "вони зникнуть (19.10: 4 відкриті питання #56→#57 жили лише в TROUBLES; 23.10: «ask» "
                     "погоджують за звичкою — тому deny). Для кожного: лиши в next/openQuestions, або перенеси його "
                     "ДОСЛІВНИЙ текст (не скорочений вказівник — він не пройде: рахується частка слів пункту) у "
                     "done («зроблено: <текст>»), watchOut або handoffNote («відкинуто: <текст> — причина» / "
                     "«у BACKLOG: <текст>») і передай знову: "
                     + " | ".join(f"[{l}] {' '.join(i.split())[:70]}" for l, i in lost)
                     + (f". Також із записки (підказка, не блок): {note_txt}" if note else "")))
        elif note:
            emit("PreToolUse", additionalContext=(
                f"baton-guard (підказка): нова записка замінює стару, і {len(note)} крок(и) з неї ніде в новій естафеті "
                "не видно (у #78→#79 і #80→#81 такі губились). Якщо крок ще відкритий — додай його в next/handoffNote "
                "наступною передачею або в BACKLOG; якщо зроблено/відкинуто — нічого. Бектест: 9 з 10 таких підказок "
                "хибні (стан змінився, переформульовано) — перевір, не переписуй навмання: " + note_txt))
        return

    if (event == "PostToolUse" and tool.endswith("baton_pick_up")) or \
            event == "UserPromptSubmit":
        dp = double_pickup()
        parts = [warn_text(dp)] if dp else []
        if event == "PostToolUse":
            v = view_hint()
            if v:
                parts.append(v)
        if parts:
            emit(event, additionalContext="\n".join(parts))


def view_hint():
    """5. (2026-10-23, BACKLOG «План на наступну сесію…» п.1) Після pick_up — стислий вигляд
    .baton/HANDOFF-view.md (≤15 000 Б, tools/handoff-view.py): повний вивід pick_up 23.10 —
    87 338 симв., не вміщувався в одне читання, «Обережно» не прочитано. Помилка — тиша."""
    import subprocess
    out = f"{REPO}/.baton/HANDOFF-view.md"
    try:  # власний try: збій тут не має глушити попередження про подвійний pick_up (звірка Haiku 23.10)
        r = subprocess.run([sys.executable, f"{REPO}/tools/handoff-view.py", "--in", CURRENT,
                            "--out", out, "--check"], capture_output=True, text=True, timeout=4)
    except Exception:
        return ""
    if r.stdout.startswith("view FAIL"):  # 23.10 рецензія cfca89fe: при FAIL була тиша — агент не знав, що вигляд неповний
        return (f"Стислий стан естафети НЕПОВНИЙ ({r.stdout.strip()[10:]}): {out} прочитай, а чого в ньому бракує "
                "(«Далі», «Відкриті питання», «Обережно») — з повного виводу pick_up частинами (Read з offset).")
    if not r.stdout.startswith("view ok"):
        return ""
    return (f"Стислий стан естафети — {out} ({r.stdout.split(' Б')[0][8:]} Б): прочитай його ЦІЛИМ одним "
            "Read до плану (у ньому всі «Далі», «Відкриті питання» і «Обережно» за словами задачі); "
            "повний вивід pick_up — лише коли бракує деталей.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
