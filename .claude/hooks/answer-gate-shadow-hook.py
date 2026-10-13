#!/data/data/com.termux/files/usr/bin/python3
"""Stop-хук, ТІНЬОВИЙ режим (2026-10-12): ворота 4 «перед відповіддю» (M11.4).

Навіщо: сесія e3a33280 — після воріт 1 (старт) у момент дії не спрацювало 7 правил
(trees/pam-yat-proyektu.md, M11 «evidence 2026-10-12»): черга не показана, план
показано без verify-before-show, підказки хуків відхилено мовчки. Хук (до 13.10) НІЧОГО не
блокує й не пише в stdout: лише рядок у .claude/logs/answer-gate-shadow.jsonl на
кожен запуск (порожній `misses` — теж рядок, щоб не плутати зі зламаним хуком).
Спершу міряємо хибні спрацювання в тіні, голос — лише після цифр (M11.4).
ГОЛОС (2026-10-13, рішення користувача «давай голос лічильнику»): лише сигнал queue і лише
на ходах, які почав користувач (origin.kind == "human"; сповіщення фонових задач — ні).
Бектест 13.10: на ходах користувача пропуски черги справжні (#31 #34 #46 #48), хибні були
лише на сповіщеннях. Голос = {"decision":"block","reason":…} — Claude дописує чергу тим
самим ходом; stop_hook_active → повторно не блокує (без циклу). Решта сигналів — тінь.

Сигнали (евристика за словами — саме її і перевіряє тінь):
  queue   — у тексті ходу немає слова «черга» (хук tree-focus: «після відповіді
            покажи чергу»).
  verify  — хід закінчується пропозицією змінити файли (питання + слово зміни),
            а в ході не було ні Skill verify-before-show, ні delegate. Дописування
            запису й коміт показаного — не план (RULES.md:52–53), не рахуються.
  nudge   — у ході була підказка хука (делегувати / request-brief), а текст ходу
            не називає ні виконання, ні причини відмови.
Розбір журналу — iter_turns з number-claim-shadow-hook.py (той самий «хід»),
плюс записи attachment/hook_additional_context.

Запуск: Stop-хук (stdin JSON) або  python3 <цей файл> --backtest <jsonl>
Будь-яка помилка — мовчки (fail-open).
"""
import datetime
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG = os.path.join(ROOT, ".claude", "logs", "answer-gate-shadow.jsonl")
LOG_MAX = 2_000_000

RE_QUEUE = re.compile(r"черг", re.I)
# Без «дописати»/«закомітити»: RULES.md:52–53 (2026-10-12) — дописати запис у картку/журнал
# або закомітити показане — не план. «змінився» (опис стану) — теж не план.
RE_CHANGE = re.compile(r"\b(зміню|змінюю|змінити|правк\w*|правлю|підганя\w*|зареєстр\w*|"
                       r"реєстру\w*|пишу|напишу|додам|переношу|видал\w*|створ\w*)", re.I)
RE_PLAN_Q = re.compile(r"план\w*", re.I)  # «Роблю за цим планом?» без слова зміни
RE_DELEG_HINT = re.compile(r"Делегуй", re.I)
RE_DELEG_ANS = re.compile(r"делег|delegate|підказк\w* хука", re.I)
RE_BRIEF_HINT = re.compile(r"request-brief", re.I)
RE_BRIEF_ANS = re.compile(r"бриф|request-brief", re.I)
VERIFY_TOOLS = ("mcp__delegate__delegate", "mcp__delegate__deepseek")


def is_real_user(d):
    if d.get("type") != "user" or d.get("isMeta"):
        return False
    m = d.get("message")
    return isinstance(m, dict) and isinstance(m.get("content"), str)


def iter_turns(lines):
    """Хід = від справжнього повідомлення користувача до наступного."""
    cur = None
    for line in lines:
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if not isinstance(d, dict):
            continue
        if is_real_user(d):
            if cur is not None:
                yield cur
            org = d.get("origin") if isinstance(d.get("origin"), dict) else {}
            human = org.get("kind") == "human" if org else \
                not d["message"]["content"].lstrip().startswith("<")
            cur = {"user": d["message"]["content"], "ts": d.get("timestamp", ""),
                   "texts": [], "tools": [], "hints": [], "human": human}
            continue
        if cur is None:
            cur = {"user": None, "ts": d.get("timestamp", ""), "texts": [],
                   "tools": [], "hints": [], "human": False}
        if d.get("type") == "attachment":
            a = d.get("attachment") or {}
            if a.get("type") == "hook_additional_context":
                c = a.get("content")
                cur["hints"].append(" ".join(c) if isinstance(c, list) else str(c or ""))
            continue
        if d.get("type") != "assistant":
            continue
        for x in (d.get("message") or {}).get("content") or []:
            if not isinstance(x, dict):
                continue
            if x.get("type") == "tool_use":
                inp = x.get("input") or {}
                cur["tools"].append((x.get("name", ""), str(inp.get("skill", ""))))
            elif x.get("type") == "text" and x.get("text", "").strip():
                cur["texts"].append(x["text"])
    if cur is not None:
        yield cur


def check(turn):
    misses = []
    text = "\n".join(turn["texts"])
    if not text.strip():
        return misses
    last = turn["texts"][-1].strip()
    if not RE_QUEUE.search(text):
        misses.append("queue")
    tail = last  # уся остання відповідь: план часто вище за підсумкове питання
    qline = last.splitlines()[-1] if last else ""
    if last.endswith("?") and (RE_CHANGE.search(tail) or RE_PLAN_Q.search(qline)):
        ok = any(n == "Skill" and s == "verify-before-show" or n in VERIFY_TOOLS
                 for n, s in turn["tools"])
        if not ok:
            misses.append("verify")
    hints = "\n".join(turn["hints"])
    if RE_DELEG_HINT.search(hints) and not RE_DELEG_ANS.search(text):
        misses.append("nudge:delegate")
    if RE_BRIEF_HINT.search(hints) and not RE_BRIEF_ANS.search(text):
        misses.append("nudge:brief")
    return misses


def current_turn_lines(path, chunk=262_144, max_scan=8_000_000):
    with open(path, "rb") as f:
        f.seek(0, 2)
        pos, buf, scanned = f.tell(), b"", 0
        while pos > 0 and scanned < max_scan:
            take = min(chunk, pos)
            pos -= take
            scanned += take
            f.seek(pos)
            buf = f.read(take) + buf
            lines = buf.decode("utf-8", "ignore").splitlines()
            if pos > 0 and lines:
                lines = lines[1:]
            for i in range(len(lines) - 1, -1, -1):
                try:
                    d = json.loads(lines[i])
                except ValueError:
                    continue
                if isinstance(d, dict) and is_real_user(d):
                    return lines[i:]
        lines = buf.decode("utf-8", "ignore").splitlines()
        return lines[1:] if pos > 0 and lines else lines


QUEUE_REASON = ("Ворота 4 (M11.4, голос черги, 2026-10-13): у відповіді користувачу немає черги. "
                "Допиши в кінці рядок «Черга: <вузол у роботі> → <що далі>» (хук tree-focus: "
                "«після відповіді покажи чергу»). Нічого іншого не змінюй і не повторюй відповідь.")


def write_log(session, misses, voice=None):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    if os.path.isfile(LOG) and os.path.getsize(LOG) > LOG_MAX:
        os.replace(LOG, LOG + ".1")
    rec = {"t": datetime.datetime.now().isoformat(timespec="seconds"),
           "session": session, "misses": misses}
    if voice:
        rec["voice"] = voice
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def run(data):
    tp = data.get("transcript_path")
    misses, voice = [], None
    if isinstance(tp, str) and os.path.isfile(tp):
        try:
            turns = list(iter_turns(current_turn_lines(tp)))
            if turns:
                # журнал на Stop може ще не мати фінальної відповіді (доку hooks:
                # transcript_path «may lag»; випадок 13.10 — хибний голос) →
                # остання відповідь з last_assistant_message
                lam = data.get("last_assistant_message")
                if isinstance(lam, str) and lam.strip() and lam not in turns[-1]["texts"]:
                    turns[-1]["texts"].append(lam)
                misses = check(turns[-1])
                if ("queue" in misses and turns[-1].get("human")
                        and not data.get("stop_hook_active")):
                    voice = "queue"
        except OSError:
            misses = ["error:read"]
    else:
        misses = ["error:no-transcript"]
    write_log(data.get("session_id"), misses, voice)
    if voice:
        print(json.dumps({"decision": "block", "reason": QUEUE_REASON}, ensure_ascii=False))


def backtest(path):
    with open(path, encoding="utf-8", errors="ignore") as f:
        turns = list(iter_turns(f.read().splitlines()))
    counts, n = {}, 0
    for i, t in enumerate(turns, 1):
        if not "".join(t["texts"]).strip():
            continue
        n += 1
        m = check(t)
        for k in m:
            counts[k] = counts.get(k, 0) + 1
        u = (t["user"] or "")[:50].replace("\n", " ")
        print(f"#{i:<3} {t['ts'][11:16]}  {','.join(m) or '—':<28} «{u}»")
    print(f"ходів з текстом: {n}; спрацювань: " +
          ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--backtest":
        return backtest(sys.argv[2])
    try:
        data = json.load(sys.stdin)
    except ValueError:
        data = None
    run(data if isinstance(data, dict) else {})


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
