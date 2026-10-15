#!/data/data/com.termux/files/usr/bin/python3
"""stance-gate: питання з метою і позиція на вільну відповідь (M11, 2026-10-14).

Навіщо: користувач 14.10 — «ти постійно губиш ціль… зі всім погоджуєшся, хоча створюється
ілюзія що я щось тут вирішую». Сесія e629c562: 14 з 16 питань AskUserQuestion без мети;
вільні відповіді («роби через опус 5.5», «навіщо їх прибирати?») — я дію або розвертаюсь без
позиції. Правило «ціль не названо — не пропонувати» вже є (RULES.md) і не тримає; самі
правила без замка не працюють (TROUBLES «Написано, не практикується»).

Дві події, один файл:
  PreToolUse  AskUserQuestion — питання без рядка «Ціль:» → запис у журнал (ТІНЬ, не блокує).
  PostToolUse AskUserQuestion — відповідь не з варіантів (вільний текст) → нагадування мені:
              спершу переформулювати як питання, першим рядком «Згоден / Не згоден, бо <доказ>»
              (arXiv 2602.23971 «Ask don't tell»: перетворити не-питання на питання перед
              відповіддю — сильніше за «не підлабузнюйся»). + запис у журнал.
Журнал: .claude/logs/stance-gate.jsonl. Будь-яка помилка — мовчки (fail-open).
Відкат: прибрати два записи stance-gate з .claude/settings.json.
"""
import datetime
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG = os.path.join(ROOT, ".claude", "logs", "stance-gate.jsonl")
RE_GOAL = re.compile(r"Ціль\s*:", re.I)
NUDGE = ("stance-gate: відповідь користувача — не з запропонованих варіантів: «{a}». Перш ніж діяти, "
         "переформулюй її як питання (що саме він хоче і чи це служить меті вузла?) і почни відповідь "
         "рядком «Згоден / Не згоден, бо <доказ>». Не згоден — скажи це до виконання, а не після.")


def log(rec):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    rec["t"] = datetime.datetime.now().isoformat(timespec="seconds")
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def answers_of(resp):
    """tool_response AskUserQuestion: формат у доці не описано — беремо і dict answers, і текст."""
    if isinstance(resp, dict):
        a = resp.get("answers")
        if isinstance(a, dict):
            return [str(v) for v in a.values()]
        resp = json.dumps(resp, ensure_ascii=False)
    if isinstance(resp, list):
        resp = " ".join(x.get("text", "") if isinstance(x, dict) else str(x) for x in resp)
    return re.findall(r'"=\s*"(.*?)"(?:\.|,| You|$)', str(resp or ""), re.S)


def main():
    d = json.load(sys.stdin)
    if d.get("tool_name") != "AskUserQuestion":
        return
    qs = (d.get("tool_input") or {}).get("questions") or []
    ev = d.get("hook_event_name")
    if ev == "PreToolUse":
        miss = [q.get("header", "") for q in qs if not RE_GOAL.search(str(q.get("question", "")))]
        log({"session": d.get("session_id"), "event": "ask", "n": len(qs), "no_goal": miss})
    elif ev == "PostToolUse":
        labels = {str(o.get("label", "")).strip() for q in qs for o in q.get("options") or []}
        free = [a for a in answers_of(d.get("tool_response")) if a.strip() and a.strip() not in labels]
        log({"session": d.get("session_id"), "event": "answer", "free": [a[:120] for a in free],
             "resp_type": type(d.get("tool_response")).__name__})
        if free:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                              "additionalContext": NUDGE.format(a=free[0][:200])}}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
