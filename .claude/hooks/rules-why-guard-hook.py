#!/data/data/com.termux/files/usr/bin/python3
"""
PreToolUse hook (БЛОКУЄ): правку RULES.md (і симлінків CLAUDE.md /
AGENTS.md) дозволено лише якщо RULES-WHY.md оновлено за останні
FRESH_SECONDS — тобто "чому" нового/зміненого правила вже записано.
Причина (RULES-WHY.md, 2026-09-23): агент запропонував скоротити
правила, не знаючи їхньої історії; історія була лише в git або ніде.

Ловить:
- Edit / Write / MultiEdit / NotebookEdit з file_path → RULES.md;
- Bash: перенаправлення > / >> / >| у RULES.md; sed/perl -i, tee,
  truncate з аргументом RULES.md; cp/mv/install з RULES.md як ціллю
  (останній аргумент).
НЕ ловить (відома межа): запис із python/node-скрипта чи іншої
програми — такий виклик не видно з рядка команди.

Коли дозволяє — додає в контекст останні коміти RULES.md, щоб правка
спиралась на історію.
"""
import json
import os
import re
import shlex
import subprocess
import sys
import time

PROJECT = "/data/data/com.termux/files/home/AgentReachProject"
RULES_REAL = os.path.realpath(os.path.join(PROJECT, "RULES.md"))
WHY_PATH = os.environ.get("RULES_WHY_PATH") or os.path.join(PROJECT, "RULES-WHY.md")
FRESH_SECONDS = 300  # 5 хвилин

EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
HEREDOC_START_RE = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?")
SEPARATORS = {";", "&&", "||", "&", "|", "(", ")", "\n", "|&"}
REDIRECTS = {">", ">>", ">|", "&>", "&>>"}
WRAPPERS = {"sudo", "env", "command", "nohup"}


def is_rules(path, cwd):
    if not path:
        return False
    path = os.path.expanduser(path)
    if not os.path.isabs(path):
        path = os.path.join(cwd or PROJECT, path)
    return os.path.realpath(path) == RULES_REAL


def strip_heredocs(command):
    """Прибирає тіло heredoc, щоб текст усередині (commit-повідомлення,
    вміст файлу) не читався як команда. Рядок із << лишається — там
    стоїть реальне перенаправлення (cat >> RULES.md <<'EOF')."""
    lines = command.split("\n")
    out = []
    i = 0
    while i < len(lines):
        out.append(lines[i])
        m = HEREDOC_START_RE.search(lines[i])
        i += 1
        if m:
            delim = m.group(1)
            while i < len(lines) and lines[i].strip() != delim:
                i += 1
            i += 1
    return "\n".join(out)


def segments(command):
    """Токени shlex (поважає лапки), розбиті на окремі команди за
    роздільниками. Кожна команда — список токенів."""
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    segs, cur = [], []
    for tok in lexer:
        if tok in SEPARATORS:
            if cur:
                segs.append(cur)
            cur = []
        else:
            cur.append(tok)
    if cur:
        segs.append(cur)
    return segs


def bash_writes_rules(command, cwd):
    try:
        segs = segments(strip_heredocs(command))
    except ValueError:
        return False
    for seg in segs:
        # перенаправлення в будь-якому місці сегмента
        for i, tok in enumerate(seg[:-1]):
            if tok in REDIRECTS and is_rules(seg[i + 1], cwd):
                return True
        # пропустити обгортки (sudo, env X=Y, timeout N)
        j = 0
        while j < len(seg):
            if seg[j] in WRAPPERS or "=" in seg[j] and not seg[j].startswith("-"):
                j += 1
            elif seg[j] == "timeout":
                j += 2
            else:
                break
        if j >= len(seg):
            continue
        cmd, args = os.path.basename(seg[j]), seg[j + 1:]
        files = [a for a in args if not a.startswith("-")]
        if cmd in ("sed", "perl") and any(a.startswith("-i") or a == "--in-place" for a in args):
            if any(is_rules(a, cwd) for a in files):
                return True
        elif cmd in ("tee", "truncate"):
            if any(is_rules(a, cwd) for a in files):
                return True
        elif cmd in ("cp", "mv", "install"):
            if files and is_rules(files[-1], cwd):
                return True
    return False


def git_log():
    try:
        r = subprocess.run(
            ["git", "-C", PROJECT, "log", "-5", "--date=short",
             "--format=%h %ad %s", "--", "RULES.md"],
            capture_output=True, text=True, timeout=5)
        return r.stdout.strip()
    except Exception:
        return ""


def why_headings():
    try:
        with open(WHY_PATH, encoding="utf-8") as f:
            return [l[3:].strip() for l in f if l.startswith("## ")]
    except OSError:
        return []


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return
    tool = data.get("tool_name", "")
    tin = data.get("tool_input", {}) or {}
    cwd = data.get("cwd", PROJECT)

    if tool in EDIT_TOOLS:
        hit = is_rules(tin.get("file_path") or tin.get("notebook_path"), cwd)
    elif tool == "Bash":
        hit = bash_writes_rules(tin.get("command", ""), cwd)
    else:
        hit = False
    if not hit:
        return

    try:
        age = time.time() - os.path.getmtime(WHY_PATH)
    except OSError:
        age = float("inf")

    if age > FRESH_SECONDS:
        heads = why_headings()
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "Заблоковано: правка RULES.md без запису «чому». Спершу "
                "прочитай RULES-WHY.md (записи про правила, які змінюєш), "
                "допиши туди причину зміни — слова користувача дослівно / "
                "випадок / дата — і повтори правку протягом "
                f"{FRESH_SECONDS // 60} хв. Розділи RULES-WHY.md: "
                + ("; ".join(heads) if heads else "(файл відсутній — створи)")
            ),
        }}, ensure_ascii=False))
        return

    log = git_log()
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "additionalContext": (
            "rules-why-guard: RULES-WHY.md оновлено — правку RULES.md "
            "дозволено. Останні коміти RULES.md:\n" + (log or "(git log недоступний)")
        ),
    }}, ensure_ascii=False))


if __name__ == "__main__":
    main()
