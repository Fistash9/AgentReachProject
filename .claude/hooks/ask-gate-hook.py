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
  records — (2026-10-20) питання показує бриф чи план («бриф», «план»), а у відрізку немає пошуку в моїх записах
           (kb-map.py / trees-index.py / grep по TROUBLES|BACKLOG|ECOSYSTEM|CONTEXT / Read цих файлів) і рядка
           «Записи не потрібні: <чому>». Причина: клас Р1 «дія до перевірки» — ⚠ ліки не діють (error-registry --loop
           20.10); бриф v1 проби Graphify без уроків TROUBLES; рішення користувача «Так, зараз».
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
RE_BRIEF = re.compile(r"бриф\w*", re.I)
RE_PLAN_WORD = re.compile(r"план\w*", re.I)
RE_COMMIT_Q = re.compile(r"коміт", re.I)  # «закомітити… план уже звірено» — питання про коміт, не план (бектест 20.10)
RE_SKIP_RECORDS = re.compile(r"Записи не потрібні:", re.I)
# 2026-10-22 (сесія 940a8b9a; користувач: «правила перечитай…» → «Виправити зараз»): рядок «Звірка не потрібна:»
# пропустив 4 плани змін механізмів (запуск, 2 хуки, claimcheck, plain-codes) — verify-before-show 0 викликів; а «Робимо ці
# зміни запуску?» / «Які механізми робимо?» RE_CHANGE не бачив зовсім. Тепер зміна механізму впізнається й за ВАРІАНТАМИ
# (механізм + дієслово зміни), і для неї «Звірка не потрібна» не приймається (крім питань про коміт). Бектест сесії:
# справжніх/сумнівних 5, хибних 2 («замки» в описі відповіді), старе правило — 1.
RE_MECH = re.compile(r"хук\w*|скрипт\w*|\.py\b|\.sh\b|RULES|settings|налаштуван\w*|замк\w*|замок|tmux-work|run-dsh|"
                     r"claimcheck|plain-codes", re.I)
RE_MECH_VERB = re.compile(r"правлю|правк\w*|зміни\b|змін\w*|додати|додам|додаю|підключ\w*|вмика\w*|переписа\w*|"
                          r"розшир\w*|ставлю|exec\b|зробити зараз|Усі 4", re.I)
# 2026-10-24 (рецензія сесії 67228d1a, S8; користувач: «так, починай з ask-gate» → «Так, вносити»): «…і закомітити?» у
# питанні про механізм вимикало вимогу звірки («Внести ці дві поправки в RULES.md … і закомітити замок?» 23.10 пройшло),
# а «поправки» RE_CHANGE не бачить (\b перед «правк»). Тепер коміт знімає вимогу лише як питання саме про коміт; у
# складеному «… і закомітити» механізм шукається в самому питанні без рядка «Черга: …» (у варіантах «замок» — хибні 22.10).
# «поправк» — лише тут: спільну RE_CHANGE читає ще Stop-перевірка answer-gate. Бектест 1381 питання: змін 5 (справжніх 3).
RE_CHANGE_LOCAL = re.compile(r"поправк\w*", re.I)
RE_COMMIT_COMPOUND = re.compile(r"\b(?:і|й|та)\s+(?:за)?коміт", re.I)
RE_QUEUE_LINE = re.compile(r"Черга:.*?(?:[.?](?=\s|$)|$)")
RE_RECORDS_CMD =re.compile(r"kb-map\.py|trees-index\.py|\b(grep|rg)\b[^\n]*\b(TROUBLES|BACKLOG|ECOSYSTEM|CONTEXT)\.md")
RE_RECORDS_FILE = re.compile(r"(TROUBLES|BACKLOG|ECOSYSTEM|CONTEXT)\.md$")


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
    commit_q = RE_COMMIT_Q.search(q0)
    scope = RE_QUEUE_LINE.sub("", q0) if commit_q else text
    mech = bool(RE_MECH.search(scope) and RE_MECH_VERB.search(scope)) and not (commit_q and not RE_COMMIT_COMPOUND.search(q0))
    if ag.RE_CHANGE.search(q0) or RE_CHANGE_LOCAL.search(q0) or ag.RE_PLAN_Q.search(q0) or mech:
        ok = any(n == "Skill" and s == "verify-before-show" or n in ag.VERIFY_TOOLS
                 for n, s in seg["tools"]) or (RE_SKIP_VERIFY.search(text) and not mech)
        if not ok:
            out.append("verify")
    brief = RE_BRIEF.search(q0) or (RE_PLAN_WORD.search(q0) and not RE_COMMIT_Q.search(q0))
    if brief and not RE_SKIP_RECORDS.search(text):
        found = False
        for ev in seg.get("events", []):
            if ev[0] != "tool" or not isinstance(ev[2], dict):
                continue
            if ev[1] == "Bash" and RE_RECORDS_CMD.search(str(ev[2].get("command", ""))):
                found = True
            if ev[1] == "Read" and RE_RECORDS_FILE.search(str(ev[2].get("file_path", ""))):
                found = True
        if not found:
            out.append("records")
    return out


REASONS = {
    "queue": "немає черги (пам'ять «після кожної відповіді — черга», підказка tree-focus) — допиши "
             "рядок «Черга: <назва словами> → <що далі>» У ТЕКСТ ПИТАННЯ (текст перед віконцем хук не бачить)",
    "verify": "питання пропонує зміну, а звірки плану в цьому відрізку немає (RULES.md: verify-before-show) — "
              "звір план або допиши в текст питання «Звірка не потрібна: <чому>» (дописування запису й коміт "
              "показаного — не план). Для змін хуків, скриптів, правил і налаштувань цей рядок не приймається — "
              "лише Skill verify-before-show або delegate (2026-10-22)",
    "records": "питання показує бриф чи план, а пошуку в моїх записах у цьому відрізку немає (клас Р1 «дія до "
               "перевірки», 20.10) — спершу python3 tools/kb-map.py <тема> або grep по TROUBLES/BACKLOG і врахуй "
               "знайдене; якщо пошук справді не потрібен — допиши «Записи не потрібні: <чому>»",
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
