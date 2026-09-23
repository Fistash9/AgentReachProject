#!/data/data/com.termux/files/usr/bin/python3
"""
PreToolUse hook (БЛОКУЄ): вимагає свіжий запис у TRASH.md ПЕРЕД
виконанням rm/rmdir у Bash. Правило RULES.md: "Кожне видалення
(rm/rmdir) — записати в TRASH.md ДО виконання, не після". Прецедент
(RULES.md): інший AI-агент випадково видалив цілу домашню
директорію через зайвий символ у rm -rf.

Пропускає (не блокує): команди, чиї цілі — ВИКЛЮЧНО файли всередині
scratchpad_dir поточної сесії або системних tmp-каталогів —
одноразові тестові артефакти сесії, не проєктні чи домашні дані.
Якщо ціль незрозуміла (немає шляху з "/", напр. голий "rm -rf ." чи
"rm -rf *") — вважається НЕ безпечною (консервативний дефолт).
"""
import sys
import json
import re
import shlex
import os
import time

TRASH_PATH = "/data/data/com.termux/files/home/AgentReachProject/TRASH.md"
FRESH_SECONDS = 300  # 5 хвилин

HEREDOC_START_RE = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?")
SEPARATORS = {";", "&&", "||", "&", "|", "(", ")", "\n"}

SAFE_PREFIXES = (
    "/data/data/com.termux/files/usr/tmp/",
    "/tmp/",
)


def strip_heredocs(command):
    """Прибирає тіло heredoc (між <<'EOF' і рядком EOF), щоб текст
    усередині (напр. commit-повідомлення, де згадується 'rm -rf' як
    опис) не тригерив паттерн команди нижче."""
    lines = command.split("\n")
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        m = HEREDOC_START_RE.search(line)
        if m:
            delim = m.group(1)
            i += 1
            while i < len(lines) and lines[i].strip() != delim:
                i += 1
            i += 1
            continue
        i += 1
    return "\n".join(out)


def rm_arg_tokens(command):
    """Повертає ОБ'ЄДНАНИЙ список аргументів УСІХ реальних викликів
    rm/rmdir у команді (кожен окремо обмежений наступним роздільником
    ;/&&/||/|/\\n, не хапає токени сусідніх команд), або None, якщо
    жодного такого виклику немає. Токенізація через shlex (поважає
    лапки), тому текст на кшталт 'echo "rm -rf agent.py"' НЕ
    розпізнається як виклик."""
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return None

    found = False
    combined_args = []
    at_start = True
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in SEPARATORS:
            at_start = True
            i += 1
            continue
        if at_start:
            j = i
            if tokens[j] == "sudo":
                j += 1
            if j < len(tokens) and tokens[j] in ("rm", "rmdir"):
                found = True
                k = j + 1
                while k < len(tokens) and tokens[k] not in SEPARATORS:
                    combined_args.append(tokens[k])
                    k += 1
                i = k
                at_start = True
                continue
        at_start = False
        i += 1
    return combined_args if found else None


def targets_are_safe(args, scratchpad_dir):
    prefixes = list(SAFE_PREFIXES)
    if scratchpad_dir:
        prefixes.append(scratchpad_dir)
    paths = [t for t in args if "/" in t and not t.startswith("-")]
    if not paths:
        return False  # немає явного шляху — не ризикуємо, перевіряємо TRASH.md
    return all(any(p.startswith(prefix) for prefix in prefixes) for p in paths)


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return

    raw_command = data.get("tool_input", {}).get("command", "")
    if not raw_command:
        return
    command = strip_heredocs(raw_command)
    args = rm_arg_tokens(command)
    if args is None:
        return

    scratchpad_dir = data.get("scratchpad_dir", "")
    if targets_are_safe(args, scratchpad_dir):
        return

    try:
        mtime = os.path.getmtime(TRASH_PATH)
    except OSError:
        mtime = 0

    age = time.time() - mtime
    if age <= FRESH_SECONDS:
        return  # TRASH.md щойно оновлено — вважаємо, що запис зроблено

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Заблоковано: RULES.md вимагає запис у TRASH.md ДО rm/rmdir, "
                f"а TRASH.md не оновлювався останні {FRESH_SECONDS}с. Спочатку "
                f"допиши запис (шлях, причина), потім повтори команду."
            ),
        }
    }))


if __name__ == "__main__":
    main()
