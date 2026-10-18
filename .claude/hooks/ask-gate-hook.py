#!/data/data/com.termux/files/usr/bin/python3
"""PreToolUse AskUserQuestion: ворота перед питанням у віконці — черга і звірка плану (2026-10-16).

Навіщо (проблема 2 baton #50, сесія cc3de07f): відповіді у віконцях не завершують хід, тож Stop-ворота
answer-gate бачили сесію з 10 віконцями як один хід і перевіряли лише кінець. Бектест 504 питань з 01.10:
без черги 422, план змін без звірки 42. Рішення користувача: «Звірка і черга — ворота + Б».

Перевіряється ТЕКСТ ВІКОНЦЯ (питання + варіанти): текст асистента перед викликом у журнал пишеться не завжди
(живий тест 16.10). З журналу — лише виклики інструментів від останньої відповіді користувача.
  queue  — у відрізку немає «черг» → deny: дописати рядок «Черга: …» і спитати знову.
  verify — питання пропонує зміну (RE_CHANGE / «план», як answer-gate check), а у відрізку немає ні
           verify-before-show / delegate, ні рядка «Звірено перед показом» / «Звірка не потрібна: <чому>».
Перевірки — з answer-gate-shadow-hook.py (ті самі регулярні вирази). Журнал: .claude/logs/ask-gate.jsonl.
Будь-яка помилка — мовчки (fail-open). Відкат: прибрати запис з PreToolUse у .claude/settings.local.json.
"""
import datetime
import importlib.util
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG = os.environ.get("ASK_GATE_LOG") or os.path.join(ROOT, ".claude", "logs", "ask-gate.jsonl")
RE_SKIP_VERIFY = re.compile(r"Звірено перед показом|Звірка не потрібна:", re.I)


def load_ag():
    spec = importlib.util.spec_from_file_location(
        "answer_gate", os.path.join(ROOT, ".claude", "hooks", "answer-gate-shadow-hook.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def question_text(inp):
    """Питання + підписи й описи варіантів. Текст асистента ПЕРЕД викликом у журнал не потрапляє
    (живий тест 2026-10-16: частина текстів випадає, grep 0; TROUBLES 2026-10-06) — бачимо лише віконце."""
    out = []
    for q in (inp or {}).get("questions") or []:
        if isinstance(q, dict):
            out.append(str(q.get("question", "")))
            for o in q.get("options") or []:
                if isinstance(o, dict):
                    out += [str(o.get("label", "")), str(o.get("description", ""))]
    return "\n".join(out)


def misses_for(ag, lines, question):
    turns = list(ag.iter_turns(ag.after_last_answer(lines), merge_notifications=True))
    seg = turns[-1] if turns else {"texts": [], "tools": []}
    text = question  # seg["texts"] у журналі неповні — див. question_text
    out = []
    if not ag.RE_QUEUE.search(text):
        out.append("queue")
    q0 = question.split("\n", 1)[0]  # лише саме питання, не описи варіантів
    if ag.RE_CHANGE.search(q0) or ag.RE_PLAN_Q.search(q0):
        ok = any(n == "Skill" and s == "verify-before-show" or n in ag.VERIFY_TOOLS
                 for n, s in seg["tools"]) or RE_SKIP_VERIFY.search(text)
        if not ok:
            out.append("verify")
    return out


REASONS = {
    "queue": "немає черги (пам'ять «після кожної відповіді — черга», підказка tree-focus) — допиши "
             "рядок «Черга: <назва словами> → <що далі>» У ТЕКСТ ПИТАННЯ (текст перед віконцем хук не бачить)",
    "verify": "питання пропонує зміну, а звірки плану в цьому відрізку немає (RULES.md: verify-before-show) — "
              "звір план або допиши в текст питання «Звірка не потрібна: <чому>» (дописування запису й коміт "
              "показаного — не план)",
}


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") != "AskUserQuestion":
        return
    tp = data.get("transcript_path")
    if not (isinstance(tp, str) and os.path.isfile(tp)):
        return
    ag = load_ag()
    misses = misses_for(ag, ag.current_turn_lines(tp, merge_notifications=True), question_text(data.get("tool_input")))
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"t": datetime.datetime.now().isoformat(timespec="seconds"),
                            "session": data.get("session_id"), "misses": misses},
                           ensure_ascii=False) + "\n")
    if misses:
        reason = ("ask-gate (ворота перед питанням, 2026-10-16): " + "; ".join(REASONS[m] for m in misses)
                  + ". Допиши це в текст питання і задай його знову.")
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
