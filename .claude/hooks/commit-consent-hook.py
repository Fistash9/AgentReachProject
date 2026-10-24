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
ASK → DENY (2026-10-23, план виправлень п.3; рішення «Так, старі запити прибрати»): запит погоджували «за звичкою»
(TROUBLES «Висновки сесії cfca89fe…» п.1), тому без слова — заборона, а питає агент у розмові. Той самий замок —
на git push (слово «пуш/push») і платний DeepSeek (mcp__deepseek__deepseek/-reply і Bash tools/deepseek-search.py:
«платн» у словах користувача або питання з «платн»/ціною «$» + «так»); permissions.ask для них прибрано. Лазівка
«commit у питанні агента» (п.2): у тексті питання не рахуються `…`, команди git commit/push, рядки «Черга:» і
«Звірка не потрібна:». Збій розбору для цих дій — запит (ask), не тиша.
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
RE_PUSH = re.compile(r"(?:^|[;&|(\n]|\$\()\s*git(?:\s+-C\s+\S+|\s+-c\s+\S+)*\s+push\b")
RE_PAID_CMD = re.compile(r"^\s*(?:\w+=\S+\s+)*(?:(?:\S*/)?python3?(?:\s+-\w+)*\s+)?\S*deepseek-search\.py\b")
PAID_TOOLS = ("mcp__deepseek__deepseek", "mcp__deepseek__deepseek-reply")
# слово користувача (yes), заперечення (no), ознака того, що ПИТАННЯ агента саме про цю дію (q)
KINDS = {
    "commit": (RE_YES, RE_NO, RE_YES),
    "push": (re.compile(r"пуш|push", re.I),
             re.compile(r"(?:не|без|ні,?)\s+(?:за)?пуш|не\s+push|don'?t\s+push|no\s+push", re.I),
             re.compile(r"пуш|push", re.I)),
    "paid": (re.compile(r"(?<!без)платн|paid", re.I),
             re.compile(r"(?:не|без|ні,?)\s+платн|безкоштовн|безплатн", re.I),
             re.compile(r"(?<!без)платн|\$\s?\d", re.I)),
}


def clean_question(q):
    """Текст питання без місць, де «commit/push» — назва, а не прохання (лазівка 23.10: «так» на питання про
    `git commit --dry-run` зараховано як згоду): `…`, команди git, рядки «Черга:» і «Звірка не потрібна:»."""
    q = re.sub(r"`[^`]*`", " ", q)
    q = re.sub(r"\bgit(?:\s+-\S+)*\s+(?:commit|push)\b\S*(?:\s+-\S+)*", " ", q)
    q = re.sub(r"Черга:[^?\n]*?(?:\.(?:\s|$)|\n|$)", " ", q)
    return re.sub(r"Звірка не потрібна:.*", " ", q, flags=re.S)


def kinds_of(data):
    """Які важливі дії в цьому виклику: commit / push / paid."""
    if data.get("tool_name") in PAID_TOOLS:
        return ["paid"]
    if data.get("tool_name") != "Bash":
        return []
    # тіла heredoc — текст, не команди (23.10: python-скрипт з рядком «Bash(git push *)» хибно дав «push»;
    # той самий клас, що TROUBLES 2026-09-23 «Блокуючі хуки на regex по сирому рядку команди»)
    # і текст у лапках (23.10: рядок багаторядкового -m "…" почався з «tools/deepseek-search.py» → хибне «платне»)
    cmd = RE_HEREDOC.sub(" ", str((data.get("tool_input") or {}).get("command", "")))
    cmd = re.sub(r"\"(?:[^\"\\]|\\.)*\"|'[^']*'", " ", cmd)
    out = []
    if RE_COMMIT.search(cmd):
        out.append("commit")
    if RE_PUSH.search(cmd):
        out.append("push")
    if any(RE_PAID_CMD.match(s) for s in re.split(r"&&|\|\||;|\n|\|", cmd)):
        out.append("paid")
    return out


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


def consent(text, labels=(), kind="commit"):
    """Чи дає це рішення користувача дозвіл на коміт.
    М2 (2026-10-19, рецензія сесії 1fe9acd7, рішення «М2: коміт лише з голого «так»»): вибраний у віконці
    ВАРІАНТ, який написав агент («Так, внести і закомітити»), дозволом не є, якщо саме питання не про коміт —
    інакше агент сам вирішує, чи стрельне замок. Свій текст користувача («Other») з «коміт» — дозвіл, як раніше."""
    yes, no, qyes = KINDS[kind]
    m = RE_ANSWERED.match(text)
    if not m:  # набране повідомлення
        return bool(yes.search(text)) and not no.search(text)
    body = re.split(r"You can now continue|Read the answers carefully", m.group(1))[0]
    for q, a in RE_PAIR.findall(body):
        if no.search(a):
            continue
        own = a
        for lb in sorted(labels, key=len, reverse=True):  # вибрані варіанти (і кілька через «, ») — текст агента
            own = own.replace(lb, " ")
        if yes.search(own):  # власні слова користувача
            return True
        # питання саме про цю дію І у вибраній відповіді її слово («Так, закомітити»; не «без коміту»). Голе «так»
        # не рахується з 2026-10-23: питання «замки на push?» + «Так» інакше було б згодою на push.
        if qyes.search(clean_question(q)) and yes.search(a):
            return True
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



REASONS = {
    "commit": ("Коміт заборонено: у останньому рішенні користувача немає слова «коміт» (RULES-WHY 2026-10-16: дозвіл "
               "на роботу ≠ дозвіл на коміт; з 2026-10-23 — заборона замість запиту). Спитай віконцем «…і закомітити?»."),
    "push": ("git push заборонено: у останньому рішенні користувача немає слова «пуш/push» (2026-10-23). Спитай "
             "віконцем «…і запушити?»."),
    "paid": ("Платний виклик DeepSeek заборонено: у останньому рішенні немає «платн», а питання не про платне з ціною "
             "«$» (CLAUDE.md «Платне — завжди спершу питати», 2026-10-23). Назви ціну з виходу минулого прогону і спитай."),
    "bypass": ("Коміт з обходом git-хуків (--no-verify / -n / core.hooksPath) заборонено: вимикає й перевірку вузла, й "
               "сканування ключів (pre-commit). Дозвіл — лише словом «no-verify» від користувача; інакше комітити без обходу."),
}


def out(decision, reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision,
                                             "permissionDecisionReason": reason}}, ensure_ascii=False))


def log(data, status, text):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f:
        f.write(f"{data.get('session_id', '?')}\t{status}\t{time.strftime('%Y-%m-%dT%H:%M:%S')}\t"
                f"{re.sub(r'\s+', ' ', text)[:120]}\n")


def main():
    data = json.load(sys.stdin)
    kinds = kinds_of(data)
    if not kinds:
        return
    try:
        tp = data.get("transcript_path")
        last, labels = last_decision(tp) if isinstance(tp, str) and os.path.isfile(tp) else ("", ())
        cmd = str((data.get("tool_input") or {}).get("command", ""))
        if "commit" in kinds and bypass(cmd) and "no-verify" not in last.lower():
            log(data, "bypass-deny", cmd)
            return out("deny", REASONS["bypass"])
        for k in kinds:
            ok = consent(last, labels, k)
            log(data, ("" if k == "commit" else k + ":") + ("ok" if ok else "deny"), last)
            if not ok:
                return out("deny", REASONS[k])
    except Exception as ex:  # збій розбору для важливої дії — запит, не тиша (2026-10-23)
        out("ask", f"Замок згоди ({', '.join(kinds)}) не зміг перевірити рішення користувача: "
                   f"{type(ex).__name__}. Дозволити?")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
