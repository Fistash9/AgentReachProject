#!/data/data/com.termux/files/usr/bin/python3
"""
PreToolUse hook на Bash: перед git add ЗАВЖДИ показує git status
(правило RULES.md "Перед git add — завжди git status") і БЛОКУЄ
команду, якщо вона явно називає agent.py (ключ, RULES.md розділ "Git": "agent.py містить ключ і живе
поза git"; прецедент — TROUBLES.md #11, ключ уже раз
потрапив у git до того, як файл додали в .gitignore).

Звичайний git add НЕ блокується — лише показує статус як контекст.
"""
import sys
import json
import re
import shlex
import subprocess

REPO = "/data/data/com.termux/files/home/AgentReachProject"
MAX_LINES = 30

HEREDOC_START_RE = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?")
SEPARATORS = {";", "&&", "||", "&", "|", "(", ")", "\n"}
SHELLS = {"sh", "bash", "dash", "zsh"}


def strip_heredocs(command):
    """Прибирає тіло heredoc (між <<'EOF' і рядком EOF), щоб текст
    усередині (напр. commit-повідомлення) не тригерив паттерни
    команд нижче — інакше опис 'git add agent.py' у тексті коміту
    сприймається як реальна команда."""
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
            i += 1  # пропускаємо й сам рядок-роздільник
            continue
        i += 1
    return "\n".join(out)


def git_add_arg_tokens(command):
    """Повертає ОБ'ЄДНАНИЙ список аргументів УСІХ реальних викликів
    'git add' у команді (кожен окремо обмежений наступним
    роздільником ;/&&/||/|/\\n, не хапає токени сусідніх команд), або
    None, якщо жодного такого виклику немає. Токенізація через shlex
    (поважає лапки), тому 'echo "git add agent.py"' НЕ розпізнається
    як виклик — весь вміст лапок стає одним токеном-аргументом echo,
    не окремими словами git/add/agent.py."""
    # 2026-10-16: shlex з whitespace_split бачить «\n» як пробіл — команда з нового
    # рядка ховалась (rmdir після heredoc пройшов). Той самий фікс, що 0450781 (23.09)
    # у request-brief-reminder-hook.py; тоді до цього хука не дійшов.
    command = command.replace("\\\n", " ").replace("\n", " ; ")
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return None  # незбалансовані лапки — не наш формат, пропускаємо

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
            if j < len(tokens) and tokens[j] == "git":
                j += 1
                if j < len(tokens) and tokens[j] == "-C":
                    j += 2
                if j < len(tokens) and tokens[j] == "add":
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

    # Вкладена оболонка: `sh -c '<скрипт>'`, `bash -lc …`, зокрема після
    # `proot-distro login ubuntu --` — рядок після -c один токен у лапках,
    # git add у ньому вище не видно. Розбираємо тією ж функцією (TROUBLES
    # «trash-md-guard не бачить rm усередині sh -c», 2026-10-12 — той самий клас).
    for k in range(len(tokens) - 2):
        if (tokens[k].rsplit("/", 1)[-1] in SHELLS and tokens[k + 1].startswith("-")
                and "c" in tokens[k + 1]):
            inner = git_add_arg_tokens(tokens[k + 2])
            if inner is not None:
                found = True
                combined_args.extend(inner)
    return combined_args if found else None


def l2s_links(args, status_lines, cwd):
    """Ярлики серед шляхів, які додасть git add (2026-10-20, рішення користувача «Так, зробити»): у cf52c36
    звіт DSH пішов у git як symlink на rootfs/.l2s. Шляхи — з git status (тип «T» і нові), що підпадають під
    аргументи; ярлик рахується, якщо він у agents/dsh/ або веде в .l2s."""
    import os
    # Власний виклик з --untracked-files=all: --short згортає нову теку в «?? agents/» (тест 2026-10-20: 2/7).
    try:
        status_lines = subprocess.run(["git", "-C", REPO, "status", "--porcelain", "--untracked-files=all"],
                                      capture_output=True, text=True, timeout=10).stdout.splitlines()
    except (OSError, subprocess.SubprocessError):
        return []
    paths = [ln[3:].strip().strip('"') for ln in status_lines if len(ln) > 3]
    specs = [a for a in args if not a.startswith("-")]
    every = any(a in ("-A", "--all", "-u", "--update") for a in args)
    rels = []
    for a in specs:
        r = os.path.normpath(os.path.relpath(os.path.join(cwd, a), REPO))
        rels.append("" if r == "." else r)
    out = []
    for p in paths:
        if not (every or any(r == "" or p == r or p.startswith(r.rstrip("/") + "/") for r in rels)):
            continue
        full = os.path.join(REPO, p)
        if os.path.islink(full) and (p.startswith("agents/dsh/") or ".l2s" in os.readlink(full)):
            out.append(p)
    return out


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return

    raw_command = data.get("tool_input", {}).get("command", "")
    if not raw_command:
        return
    command = strip_heredocs(raw_command)
    args = git_add_arg_tokens(command)
    if args is None:
        return

    if any("agent.py" in a for a in args):
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    "Заблоковано: команда явно згадує agent.py. RULES.md "
                    "(розділ Git): agent.py містить ключ і живе поза git — прецедент "
                    "TROUBLES.md #11, ключ уже раз потрапив у git. Якщо це "
                    "помилка — прибери agent.py з команди."
                ),
            }
        }))
        return

    try:
        result = subprocess.run(
            ["git", "-C", REPO, "status", "--short"],
            capture_output=True, text=True, timeout=10,
        )
        lines = result.stdout.splitlines()
    except (OSError, subprocess.SubprocessError):
        return

    links = l2s_links(args, lines, data.get("cwd") or REPO)
    if links:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": (
                    "git add додасть ЯРЛИК, а не файл: " + ", ".join(links[:5]) + ". Файли DSH з Termux — "
                    "ярлики l2s (TROUBLES 2026-10-20 «Закомітив ярлик l2s…»): у коміт піде symlink 120000. "
                    "Спершу cp --remove-destination \"$(readlink F)\" F і звір md5."
                ),
            }
        }))
        return

    if not lines:
        return  # чисте дерево — нема на що дивитись

    shown = lines[:MAX_LINES]
    more = f"\n... ще {len(lines) - MAX_LINES} рядків" if len(lines) > MAX_LINES else ""
    context = "git status перед git add (правило RULES.md):\n" + "\n".join(shown) + more

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": context,
        }
    }))


if __name__ == "__main__":
    main()
