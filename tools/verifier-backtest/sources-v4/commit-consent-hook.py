#!/data/data/com.termux/files/usr/bin/python3
"""
PreToolUse hook (Bash): git commit без «коміт» в останньому рішенні користувача → запит на дозвіл.
Причина (2026-10-16, проблема 3 baton #50; рецензія сесії 0577c90b): 3 коміти (6f0c67d, a45e26b,
915e452) після «роби як краще» / «Так, у фоні + бектест» — дозвіл на роботу прийнято за дозвіл на коміт.
Рішення користувача: «Слово «коміт» у питанні + замок» — агент питає «…і закомітити?», замок ловить
решту. Бектест: tools/… немає, див. TROUBLES 2026-10-16 «Замок комітів». Проба 3 сесії; журнал —
.claude/logs/commit-consent.log.

Дозвіл є, якщо останнє рішення користувача (набране повідомлення, повідомлення посеред ходу або
відповідь у віконці) — (а) сам каже «коміт/commit» без заперечення, або (б) у віконці питання
про коміт, а відповідь починається з «так/yes/коміть». Будь-яка помилка — мовчить (fail-open).

Перевірку «коміт механізму без вузла» (cfd43bd) звідси прибрано 2026-10-18: за текстом команди її обходили
git add -A / . / commit -am / pathspec і вона хибно блокувала -F файл і власний текст (аудит DSH, перевірено
запуском). Тепер — git-хук commit-msg → tools/commit-node-check.py (фактичний індекс і повідомлення).
ОБХІД ХУКІВ (2026-10-19, зовнішня перевірка сесії 1fe9acd7, п.17; рішення «Так, 1–3 зараз»): git commit
--no-verify / -n / -c core.hooksPath=… вимикає і commit-msg (вузол), і pre-commit (сканування ключів) —
запит на дозвіл, якщо в останньому рішенні користувача нема «no-verify». Тіла heredoc не перевіряються (текст).
"""
import json
import os
import re
import sys
import time

PROJECT = "/data/data/com.termux/files/home/AgentReachProject"
LOG = os.path.join(PROJECT, ".claude", "logs", "commit-consent.log")
RE_COMMIT = re.compile(r"(?:^|[;&|(\n]|\$\()\s*git(?:\s+-C\s+\S+|\s+-c\s+\S+)*\s+commit\b")
RE_YES = re.compile(r"коміт|закоміт|commit", re.I)
RE_NO = re.compile(r"(?:не|без|ні,?)\s+(?:за)?коміт|не\s+commit|don'?t\s+commit|no\s+commit", re.I)
RE_ANSWERED = re.compile(r"\s*(?:User has answered your questions|The user answered|"
                         r"Your questions have been answered):(.*)", re.S)
RE_HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?\n(.*?)\n\1\b", re.S)


def bypass(cmd):
    """Чи обходить коміт git-хуки: лише сегменти, що починаються з git … commit (дозволено VAR=x перед git) (не текст у grep/heredoc);
    -c core.hooksPath до commit, --no-verify / -n серед прапорців після commit (без тексту -m)."""
    for seg in re.split(r"&&|\|\||;|\n", RE_HEREDOC.sub(" ", cmd)):
        m = re.match(r"\s*(?:\w+=\S+\s+)*git((?:\s+-[Cc]\s+\S+)*)\s+commit\b(.*)", seg, re.S)
        if not m:
            continue
        if "core.hooksPath" in m.group(1):
            return True
        tail = re.sub(r"(?:-m|--message)(?:=|\s*)(\"(?:[^\"\\]|\\.)*\"|'[^']*')", " ", m.group(2))
        if re.search(r"--no-verify\b|(?<!\S)-[a-zA-Z]*n[a-zA-Z]*(?!\S)", tail):
            return True
    return False


RE_PAIR = re.compile(r'"((?:[^"\\]|\\.)*)"\s*=\s*"((?:[^"\\]|\\.)*)"', re.S)


def consent(text, labels=()):
    """Чи дає це рішення користувача дозвіл на коміт.
    М2 (2026-10-19, рецензія сесії 1fe9acd7, рішення «М2: коміт лише з голого «так»»): вибраний у віконці
    ВАРІАНТ, який написав агент («Так, внести і закомітити»), дозволом не є, якщо саме питання не про коміт —
    інакше агент сам вирішує, чи стрельне замок. Свій текст користувача («Other») з «коміт» — дозвіл, як раніше."""
    m = RE_ANSWERED.match(text)
    if not m:  # набране повідомлення
        return bool(RE_YES.search(text)) and not RE_NO.search(text)
    body = re.split(r"You can now continue|Read the answers carefully", m.group(1))[0]
    for q, a in RE_PAIR.findall(body):
        if RE_NO.search(a):
            continue
        own = a
        for lb in sorted(labels, key=len, reverse=True):  # вибрані варіанти (і кілька через «, ») — текст агента
            own = own.replace(lb, " ")
        if RE_YES.search(own):  # власні слова користувача
            return True
        if RE_YES.search(q) and (re.match(r"\s*(?:так|yes|добре|коміть)\b", a, re.I) or RE_YES.search(a)):
            return True  # питання саме про коміт: «так» або вибраний варіант зі словом «коміт» (не «без коміту»)
    return False


def last_decision(transcript_path):
    """Останнє рішення користувача в журналі сесії (без системних вставок) і підписи варіантів віконця,
    на яке воно відповідає (М2: щоб відрізнити вибраний варіант агента від власних слів користувача)."""
    last, labels, opts = "", (), {}
    with open(transcript_path, encoding="utf-8") as f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get("type") == "assistant":
                for x in (d.get("message") or {}).get("content") or []:
                    if isinstance(x, dict) and x.get("type") == "tool_use" and x.get("name") == "AskUserQuestion":
                        opts[x.get("id")] = tuple(str(o.get("label", "")) for q in (x.get("input") or {}).get(
                            "questions") or [] for o in q.get("options") or [] if isinstance(o, dict))
                continue
            if d.get("type") == "attachment" and d.get("attachment", {}).get("type") == "queued_command":
                q = d["attachment"].get("prompt", "")
                if isinstance(q, str) and q.strip() and not q.lstrip().startswith("<"):  # не task-notification
                    last, labels = q, ()
                continue
            if d.get("type") != "user" or d.get("isMeta"):
                continue
            c = d.get("message", {}).get("content")
            blocks = [{"type": "text", "text": c}] if isinstance(c, str) else (c or [])
            for b in blocks:
                if b.get("type") == "text" and not b.get("text", "").lstrip().startswith("<"):
                    last, labels = b["text"], ()
                elif b.get("type") == "tool_result":
                    t = b.get("content")
                    t = t if isinstance(t, str) else " ".join(
                        x.get("text", "") for x in t or [] if isinstance(x, dict))
                    if RE_ANSWERED.match(t):
                        last, labels = t, opts.get(b.get("tool_use_id"), ())
    return last, labels



def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash":
        return
    cmd = str((data.get("tool_input") or {}).get("command", ""))
    if not RE_COMMIT.search(cmd):
        return
    tp = data.get("transcript_path")
    if not (isinstance(tp, str) and os.path.isfile(tp)):
        return
    last, labels = last_decision(tp)
    if bypass(cmd) and "no-verify" not in last.lower():
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a") as f:
            f.write(f"{data.get('session_id', '?')}\tbypass-ask\t{time.strftime('%Y-%m-%dT%H:%M:%S')}\t"
                    f"{re.sub(r'\s+', ' ', cmd)[:120]}\n")
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse", "permissionDecision": "ask",
            "permissionDecisionReason": ("Коміт з обходом git-хуків (--no-verify / -n / core.hooksPath): вимикає й "
                                         "перевірку вузла, й сканування ключів (pre-commit). Дозволити? «Ні» — "
                                         "агент комітить без обходу.")}}, ensure_ascii=False))
        return
    ok = consent(last, labels)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f:
        f.write(f"{data.get('session_id', '?')}\t{'ok' if ok else 'ask'}\t{time.strftime('%Y-%m-%dT%H:%M:%S')}\t"
                f"{re.sub(r'\s+', ' ', last)[:120]}\n")
    if ok:
        return
    reason = ("Коміт без слова «коміт» у вашому останньому рішенні (RULES-WHY 2026-10-16: дозвіл на роботу ≠ "
              "дозвіл на коміт). Дозволити коміт? «Ні» — агент спершу спитає «закомітити?».")
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "ask",
        "permissionDecisionReason": reason}}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
