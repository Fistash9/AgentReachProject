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

ВУЗОЛ (2026-10-18, рішення користувача «Так, з пробою», проба 3 сесії): коміт, що змінює механізми
(хуки, скіли, налаштування, tools/, mods/, RULES/RULES-WHY/CLAUDE/AGENTS), без коду вузла (Q12, M11.4…)
чи «без вузла: причина» у повідомленні — deny з підказкою; агент дописує сам, користувача не питає.
Правило RULES.md:29 «ціль записується… коміт» механізму не мало: бектест — 24 з 54 комітів механізмів
без вузла; 82 зі 123 команд коміту механізмів у журналах. Клас «працював повз дерево» (вузол Q12, 18.10).
Критерій проби: «без вузла» ≤ 1 з 5 зупинок (журнал — той самий LOG, мітки node-deny / no-node).
"""
import json
import os
import re
import shlex
import subprocess
import sys
import time

PROJECT = "/data/data/com.termux/files/home/AgentReachProject"
LOG = os.path.join(PROJECT, ".claude", "logs", "commit-consent.log")
RE_COMMIT = re.compile(r"(?:^|[;&|(\n]|\$\()\s*git(?:\s+-C\s+\S+|\s+-c\s+\S+)*\s+commit\b")
RE_YES = re.compile(r"коміт|закоміт|commit", re.I)
RE_NO = re.compile(r"(?:не|без|ні,?)\s+(?:за)?коміт|не\s+commit|don'?t\s+commit|no\s+commit", re.I)
RE_ANSWERED = re.compile(r"\s*(?:User has answered your questions|The user answered|"
                         r"Your questions have been answered):(.*)", re.S)
RE_PAIR = re.compile(r'"((?:[^"\\]|\\.)*)"\s*=\s*"((?:[^"\\]|\\.)*)"', re.S)
RE_NODE = re.compile(r"(?<![\w.])[GMTQZ]\d+(?:\.\d+)*(?![\w])")
RE_NO_NODE = re.compile(r"без\s+вузла\s*:\s*(.{0,80})", re.I)
RE_MECH = re.compile(r"^(?:\./)?(?:\.claude/(?:hooks|skills|settings)|tools/|mods/|RULES\.md|RULES-WHY\.md|"
                     r"CLAUDE\.md|AGENTS\.md)")
RE_HEREDOC = re.compile(r"<<-?\s*'?(\w+)'?\n(.*?)\n\1\b", re.S)


def message(cmd):
    """Текст повідомлення коміту з команди: тіла heredoc і аргументи -m."""
    parts = [b for _, b in RE_HEREDOC.findall(cmd)]
    parts += re.findall(r"-m\s+\"((?:[^\"\\]|\\.)*)\"", cmd) + re.findall(r"-m\s+'([^']*)'", cmd)
    return "\n".join(parts)


def commit_paths(cmd, cwd):
    """Шляхи з git add у тій самій команді (на PreToolUse вони ще не в індексі) + уже проіндексовані."""
    out = []
    for seg in re.split(r"&&|\|\||;|\n", RE_HEREDOC.sub(" ", cmd)):
        m = re.search(r"\bgit(?:\s+-C\s+\S+)?\s+add\s+(.*)", seg)
        if m:
            try:
                out += [a for a in shlex.split(m.group(1)) if not a.startswith("-")]
            except ValueError:
                out += m.group(1).split()
    r = subprocess.run(["git", "-C", cwd or PROJECT, "diff", "--cached", "--name-only"],
                       capture_output=True, text=True, timeout=10)
    return out + r.stdout.split()


def consent(text):
    """Чи дає це рішення користувача дозвіл на коміт."""
    m = RE_ANSWERED.match(text)
    if not m:  # набране повідомлення
        return bool(RE_YES.search(text)) and not RE_NO.search(text)
    body = re.split(r"You can now continue|Read the answers carefully", m.group(1))[0]
    for q, a in RE_PAIR.findall(body):
        if RE_NO.search(a):
            continue
        if RE_YES.search(a):
            return True
        if RE_YES.search(q) and re.match(r"\s*(?:так|yes|добре|коміть)\b", a, re.I):
            return True
    return False


def last_decision(transcript_path):
    """Останнє рішення користувача в журналі сесії (без системних вставок)."""
    last = ""
    with open(transcript_path, encoding="utf-8") as f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get("type") == "attachment" and d.get("attachment", {}).get("type") == "queued_command":
                q = d["attachment"].get("prompt", "")
                if isinstance(q, str) and q.strip() and not q.lstrip().startswith("<"):  # не task-notification
                    last = q
                continue
            if d.get("type") != "user" or d.get("isMeta"):
                continue
            c = d.get("message", {}).get("content")
            blocks = [{"type": "text", "text": c}] if isinstance(c, str) else (c or [])
            for b in blocks:
                if b.get("type") == "text" and not b.get("text", "").lstrip().startswith("<"):
                    last = b["text"]
                elif b.get("type") == "tool_result":
                    t = b.get("content")
                    t = t if isinstance(t, str) else " ".join(
                        x.get("text", "") for x in t or [] if isinstance(x, dict))
                    if RE_ANSWERED.match(t):
                        last = t
    return last


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash":
        return
    cmd = str((data.get("tool_input") or {}).get("command", ""))
    if not RE_COMMIT.search(cmd):
        return
    sid, now = data.get("session_id", "?"), time.strftime("%Y-%m-%dT%H:%M:%S")
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    if any(RE_MECH.match(p) for p in commit_paths(cmd, data.get("cwd"))):
        msg = message(cmd) or cmd
        no_node = RE_NO_NODE.search(msg)
        if not (RE_NODE.search(msg) or no_node):
            with open(LOG, "a") as f:
                f.write(f"{sid}\tnode-deny\t{now}\t{msg.splitlines()[0][:120] if msg.strip() else ''}\n")
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse", "permissionDecision": "deny",
                "permissionDecisionReason": (
                    "Коміт змінює механізми (хуки/скіли/налаштування/tools/mods/правила), а в повідомленні нема "
                    "коду вузла (RULES.md:29 «ціль записується… коміт»). Допиши код вузла словами (напр. "
                    "«Q12 — …», назва: python3 tools/trees-index.py <код>) і запис у сам вузол, або рядок "
                    "«без вузла: <чому>», і закоміть знову.")}}, ensure_ascii=False))
            return
        if no_node and not RE_NODE.search(msg):
            with open(LOG, "a") as f:
                f.write(f"{sid}\tno-node\t{now}\t{no_node.group(1).strip()}\n")
    tp = data.get("transcript_path")
    if not (isinstance(tp, str) and os.path.isfile(tp)):
        return
    last = last_decision(tp)
    ok = consent(last)
    with open(LOG, "a") as f:
        f.write(f"{sid}\t{'ok' if ok else 'ask'}\t{now}\t"
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
