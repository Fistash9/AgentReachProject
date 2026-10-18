#!/data/data/com.termux/files/usr/bin/python3
"""
PreToolUse hook: перед правкою захищеного файлу нагадує про
скіл verify-before-show (RULES.md:49). Вузько — лише захищені файли, раз
на файл за сесію; P4 стріляє на кожну правку, і на нього перестали
зважати.
Причина (trees/yakist-roboty-agentiv.md, Q3, 2026-10-03): скіл вжито у 2
з 48 сесій; того дня план змін ANALYZER.md і картки показано без звірки.
Кожне спрацювання пишеться в .claude/logs/verify-nudge.log — доказ для
воріт «доказ ужитку» (проба на 3 сесії).
З 2026-10-16 бачить і Bash-правки (python open, sed -i, >, tee, cp) і питає дозволу без звірки.

Будь-яка помилка — мовчить (fail-open).
"""
import fnmatch
import re
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


def _load(name):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"),
                                                  os.path.join(PROJECT, ".claude", "hooks", name))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


RE_ROOT_PROTECTED = re.compile(r"(?<![\w/.-])((?:\./)?(?:RULES|RULES-WHY|CLAUDE|AGENTS)\.md|"
                               r"reference-analyzer/ANALYZER\.md|script-agent/AGENT\.md|"
                               r"\.claude/settings[\w.-]*\.json)")


def bash_targets(cmd, cwd):
    """Захищені файли, які Bash-команда записує. Розбір — bash_written з edit-gate-hook.py (python
    open(…,"w"), sed -i, > / >>, tee, cp), розширений на всі теки; sed -i по файлах у корені — окремо,
    бо RE_CODEPATH edit-gate знає лише теки коду."""
    eg = _load("edit-gate-hook.py")
    eg.CODE_DIRS = ("",)
    found = [r for r in eg.bash_written(cmd, cwd) if any(fnmatch.fnmatch(r, p) for p in PROTECTED)]
    for seg in re.split(r"&&|\|\||[;|\n]", eg.RE_HEREDOC.sub(" ", cmd)):
        if re.match(r"\s*(?:sudo\s+)?sed\s+(?:-\w*\s+)*-i", seg):
            for c in RE_ROOT_PROTECTED.findall(seg):
                r = rel(c, cwd)
                if r and r not in found and any(fnmatch.fnmatch(r, p) for p in PROTECTED):
                    found.append(r)
    return found


def verified_this_turn(transcript_path):
    """Чи була звірка (verify-before-show / delegate) після останнього НАБРАНОГО повідомлення користувача,
    і між нею та правкою — щонайбільше одна відповідь у віконці («так» на звірений план).
    2026-10-18 (рішення користувача «Після 2-го віконця»): до того хід у сесії з віконцями тягнувся від
    набраного повідомлення, і одна звірка накривала всі правки сесії — бектест: 22 з 40 зарахованих
    звірок застарілі (≥2 віконця між звіркою і правкою, 6 сесій). Повертає (чи є звірка, ключ відрізка
    для дедупу запиту — час останньої відповіді у віконці, інакше час ходу)."""
    ag = _load("answer-gate-shadow-hook.py")
    lines = ag.current_turn_lines(transcript_path)
    turn_ts, seg_ts, boxes = "", "", 0
    for l in lines[:1]:
        try:
            turn_ts = json.loads(l).get("timestamp", "")
        except ValueError:
            pass
    for l in reversed(lines):
        try:
            d = json.loads(l)
        except ValueError:
            continue
        if not isinstance(d, dict):
            continue
        if ag.is_box_answer(d):
            boxes += 1
            if boxes == 1:
                seg_ts = d.get("timestamp", "")
            if boxes > 1:
                break
            continue
        if d.get("type") != "assistant":
            continue
        for x in (d.get("message") or {}).get("content") or []:
            if isinstance(x, dict) and x.get("type") == "tool_use":
                n, s = x.get("name", ""), str((x.get("input") or {}).get("skill", ""))
                if (n == "Skill" and s == "verify-before-show") or n in ag.VERIFY_TOOLS:
                    return True, seg_ts or turn_ts
    return False, seg_ts or turn_ts


def log_keys(seen):
    """Ключі журналу як кортежі, а не підрядки. Два формати:
      ok   «sid\\tфайл\\t<мітка часу>»                  (3 поля, 3-є не «ask:»)
      ask  «sid\\tфайл\\task:<ключ відрізка>\\t<мітка часу>»  (4 поля)
    Було порівняння підрядком: ключ нагадування «sid\\tфайл\\t» — префікс ключа ask, тому після ask:
    нагадування для того файлу не з'являлося ніколи. Розбір по полях читає і старі рядки.
    Знахідка й код — DSH (чернетка dsh-app/drafts/verify-nudge-hook.py.new, 2026-10-18)."""
    keys = set()
    for line in seen.splitlines():
        p = line.split("\t")
        if len(p) < 3 or not p[0] or not p[1]:
            continue
        if p[2].startswith("ask:"):
            keys.add((p[0], p[1], "ask", p[2][len("ask:"):]))
        else:
            keys.add((p[0], p[1], "ok", ""))
    return keys


def main():
    data = json.load(sys.stdin)
    tool = data.get("tool_name")
    inp = data.get("tool_input") or {}
    if tool in EDIT_TOOLS:
        r = rel(inp.get("file_path") or inp.get("notebook_path") or "", data.get("cwd"))
        targets = [r] if r and any(fnmatch.fnmatch(r, p) for p in PROTECTED) else []
    elif tool == "Bash":
        targets = bash_targets(str(inp.get("command", "")), data.get("cwd"))
    else:
        return
    if not targets:
        return
    sid = data.get("session_id", "?")
    seen = open(LOG).read() if os.path.exists(LOG) else ""
    keys = log_keys(seen)
    tp = data.get("transcript_path")
    ok, turn_ts = verified_this_turn(tp) if isinstance(tp, str) and os.path.isfile(tp) else (False, "")
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    if not ok:
        # ЗАМОК (2026-10-16, рішення користувача «Так, з Bash-правками»): сесія 0577c90b — план правки
        # session-close показано й виконано без verify-before-show; підказка не блокувала, голос на Stop
        # спрацював уже після коміту. Тепер — запит на дозвіл, раз на файл за хід
        # (з 2026-10-18 — за відрізок після останньої відповіді у віконці).
        new = [r for r in targets if (sid, r, "ask", turn_ts) not in keys]
        if not new:
            return
        with open(LOG, "a") as f:
            for r in new:
                f.write(f"{sid}\t{r}\task:{turn_ts}\t{time.strftime('%Y-%m-%dT%H:%M:%S')}\n")
        reason = (f"Правка захищеного файлу ({', '.join(new)}) без дійсної звірки плану "
                  "(verify-before-show, RULES.md:49): звірки після вашого останнього повідомлення "
                  "немає, або після неї вже було більше однієї відповіді у віконці — план застарів. "
                  "Дозволити без звірки? «Ні» — агент спершу звірить план.")
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse", "permissionDecision": "ask",
            "permissionDecisionReason": reason}}, ensure_ascii=False))
        return
    new = [r for r in targets if (sid, r, "ok", "") not in keys]
    if not new:
        return  # раз на файл за сесію
    with open(LOG, "a") as f:
        for r in new:
            f.write(f"{sid}\t{r}\t{time.strftime('%Y-%m-%dT%H:%M:%S')}\n")
    msg = (f"Захищений файл {', '.join(new)}: звірку в цьому ході є — один рядок "
           "«Звірено перед показом: …» у відповіді (RULES.md:49).")
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "additionalContext": msg}}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
