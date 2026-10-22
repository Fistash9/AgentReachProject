#!/data/data/com.termux/files/usr/bin/python3
"""
PostToolUse AskUserQuestion (НЕ блокує, підказка): якщо користувач відповів у віконці ВЛАСНИМ текстом, а не
варіантом — підказка в момент дії: спершу назвати, як зрозумів відповідь і до якого пункту вона стосується.

Причина — рецензія сесії 940a8b9a (DeepSeek, 22.10, затик 1.1; рішення користувача «Усі 4 зараз»): на
питання «Пункт 1 з 4 … Черга: … → обхід Obsidian» відповідь «пошукай можливо є рішення в інтернеті…» я
віддав естафеті, а користувач мав на увазі Obsidian («а казав пошук звязаний з обходом обсідіана») —
2–3 ходи не за адресою. Готові практики (ACL 2026 SAGE-Agent; arXiv 2609.02054 «Intent Confirmation»):
одне питання — один об'єкт, підтвердження наміру перед дією. Stop-голос не годиться: журнал губить
частину видимих відповідей (TROUBLES 2026-10-06), а тут відповідь і варіанти приходять у самому виклику.

Формат tool_response не перевірено на живому записі → перший запис сесії пишеться сирим у лог
(.claude/logs/free-answer.log), розбір — і словник answers, і текст «"питання"="відповідь"».
Будь-яка помилка — мовчить (fail-open).
"""
import json
import os
import re
import sys
import time

LOG = "/data/data/com.termux/files/home/AgentReachProject/.claude/logs/free-answer.log"
PAIR = re.compile(r'"((?:[^"\\]|\\.)*?)"="((?:[^"\\]|\\.)*?)"(?=[.\s]|$)')


def answers(resp):
    """Відповіді користувача з tool_response: словник answers або пари «"…"="…"» у тексті."""
    if isinstance(resp, dict) and isinstance(resp.get("answers"), dict):
        return [str(v) for v in resp["answers"].values()]
    text = resp if isinstance(resp, str) else json.dumps(resp, ensure_ascii=False)
    return [a for _, a in PAIR.findall(text)]


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") != "AskUserQuestion":
        return
    inp = data.get("tool_input") or {}
    resp = data.get("tool_response")
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    sid = data.get("session_id", "?")
    seen = open(LOG, encoding="utf-8").read() if os.path.exists(LOG) else ""
    if f"raw\t{sid}" not in seen:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"raw\t{sid}\t{json.dumps(resp, ensure_ascii=False)[:1500]}\n")
    labels = {o.get("label", "") for q in inp.get("questions", []) for o in q.get("options", [])}
    free = [a for a in answers(resp) if a and a not in labels]
    if not free:
        return
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"free\t{sid}\t{time.strftime('%Y-%m-%dT%H:%M:%S')}\t{free[0][:200]}\n")
    msg = (f"free-answer: користувач відповів СВОЇМ текстом, не варіантом: «{free[0][:160]}». Перш ніж діяти — "
           "першим реченням назви, як ти це зрозумів і ДО ЯКОГО пункту воно стосується (якщо пункт не названо — "
           "до голови черги з тексту питання, а не до першого об'єкта питання; 22.10: «пошукай…» стосувалося "
           "Obsidian, я віддав естафеті). Якщо прочитань два — спитай віконцем, не вгадуй. Питання, рада, "
           "зауваження або «так, але…» — не дозвіл (пам'ять mixed-answer-is-not-approval).")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}},
                     ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
