#!/data/data/com.termux/files/usr/bin/python3
"""
PreToolUse hook на Bash: перед git add ЗАВЖДИ показує git status
(правило RULES.md "Перед git add — завжди git status") і БЛОКУЄ
команду, якщо вона явно називає agent.py (ключ, RULES.md розділ "Git": "agent.py містить ключ і живе
поза git"; прецедент — TROUBLES.md #11, ключ уже раз
потрапив у git до того, як файл додали в .gitignore).

Звичайний git add НЕ блокується — лише показує статус як контекст.

2026-10-26: друга перевірка copy_risk — cp/rsync/tar/zip/scp/mv, що копіює agent.py
або весь корінь проєкту (cp -r . $T/ 25.10, TROUBLES 2026-10-25 «Скопіював увесь
проєкт (cp -r .)…»), дає «ask» (віконце), не deny. Виняток: --exclude/-x з agent.py.
Вимикач: KEYGUARD=0. Межі (find -exec, xargs, змінні в джерелі) — див. copy_risk.
"""
import os
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


COPY_PROGS = {"cp", "rsync", "tar", "zip", "scp", "mv"}
WRAPPERS = {"sudo", "env", "command", "nohup", "time"}
REDIR_RE = re.compile(r"^\d*(>>?|<<?-?|>&|<&)(.*)$")
# опції, що беруть НАСТУПНИЙ токен як значення (не джерело)
OPT_ARG = {
    "cp": {"-t", "--target-directory", "-S", "--suffix"},
    "scp": {"-P", "-i", "-o", "-F", "-c", "-l", "-S", "-J", "-D", "-X"},
    "rsync": {"-e", "--rsh", "--exclude", "--include", "--filter", "-f", "--exclude-from",
              "--include-from", "--files-from", "--link-dest", "--compare-dest", "--copy-dest",
              "--backup-dir", "--suffix", "--chmod", "--chown", "-T", "--temp-dir", "--partial-dir",
              "--log-file", "--password-file", "--port", "--timeout", "-M", "--remote-option",
              "--rsync-path"},
    "zip": {"-b", "-n", "-t", "-tt", "-O", "--out", "-P", "--password", "-Z"},
    "mv": {"-t", "--target-directory", "-S", "--suffix"},
}
TAR_ARG_LETTERS = set("fCTXbKNgLV")
TAR_LONG_ARG = {"--file", "--directory", "--exclude", "--files-from", "--exclude-from",
                "--transform", "--xform", "--owner", "--group", "--mode", "--newer", "--after-date"}


def _tokens(command):
    """shlex-токени з роздільниками ;&|() окремо (redirect-и типу 2>/dev/null — одним словом)."""
    command = command.replace("$(pwd)", "$PWD").replace("`pwd`", "$PWD")
    command = command.replace("\\\n", " ").replace("\n", " ; ")
    lex = shlex.shlex(command, posix=True, punctuation_chars=";&|()")
    lex.whitespace_split = True
    lex.commenters = ""
    return list(lex)


def _segments(tokens):
    seg = []
    for tok in tokens:
        if tok and set(tok) <= set(";&|()"):
            if seg:
                yield seg
            seg = []
        else:
            seg.append(tok)
    if seg:
        yield seg


def _clean(seg):
    """Прибирає коментар (#…), redirect-и (2>/dev/null, > f) і обгортки sudo/env/VAR=."""
    out, skip = [], False
    for i, t in enumerate(seg):
        if skip:
            skip = False
            continue
        if t.startswith("#"):
            break
        m = REDIR_RE.match(t)
        if m:
            skip = not m.group(2)  # «>» окремо — ціль у наступному токені
            continue
        out.append(t)
    assigns = []
    while out and (out[0] in WRAPPERS or re.match(r"^\w+=", out[0])):
        if re.match(r"^\w+=", out[0]):
            assigns.append(out[0])
        out = out[1:]
    # присвоєння змінюють shell-змінні лише в сегменті без команди (VAR=x; …), не в «VAR=x cmd»
    return out, (assigns if not out else [])


def _subst(s, cwd, shvars):
    """$VAR/${VAR}: PWD → cwd, HOME → ~, прості присвоєння цієї ж команди → їх значення.
    Невідомі лишаються як є (далі _resolve поверне None)."""
    home = os.path.expanduser("~")

    def rep(m):
        name = m.group(1) or m.group(2)
        if name == "PWD":
            return cwd if cwd is not None else m.group(0)
        if name in (shvars or {}):
            return shvars[name]
        if name == "HOME":
            return home
        return m.group(0)
    return re.sub(r"\$\{(\w+)\}|\$(\w+)", rep, s)


def _is_key(arg, cwd, shvars):
    """Аргумент — саме файл agent.py (./agent.py, dir/agent.py, $F з F=agent.py), не підрядок."""
    a = os.path.expanduser(_subst(arg, cwd, shvars))
    return os.path.basename(os.path.normpath(a)) == "agent.py" if a else False


def _resolve(path, cwd, shvars=None):
    """Шлях → абсолютний (None, якщо не розв'язати: змінна, невідомий cwd)."""
    path = os.path.expanduser(_subst(path, cwd, shvars))
    if path == "*":
        path = "."
    elif path.endswith("/*"):
        path = path[:-2] or "/"
    if "$" in path or "*" in path or "?" in path or ":" in path.split("/")[0]:
        return None  # невідома змінна, складний глоб, віддалений host:path (scp/rsync)
    if not os.path.isabs(path):
        if cwd is None:
            return None
        path = os.path.join(cwd, path)
    return os.path.normpath(path)


def _covers_root(path):
    """Джерело = корінь проєкту або його предок (~, / …) — копія міститиме agent.py."""
    roots = {os.path.normpath(REPO), os.path.realpath(REPO)}
    for cand in {path, os.path.realpath(path)}:
        for r in roots:
            if cand == r or r.startswith(cand.rstrip("/") + "/"):
                return True
    return False


def _excludes_key(prog, args):
    for i, a in enumerate(args):
        nxt = args[i + 1] if i + 1 < len(args) else ""
        if prog in ("rsync", "tar"):
            if a.startswith("--exclude=") and "agent.py" in a:
                return True
            if a == "--exclude" and "agent.py" in nxt:
                return True
        if prog == "zip" and a in ("-x", "--exclude"):
            for p in args[i + 1:]:
                if p.startswith("-"):
                    break
                if "agent.py" in p:
                    return True
    return False


def _sources(prog, args, cwd):
    """Не-опційні аргументи-ДЖЕРЕЛА як пари (сирий, база для резолву)."""
    if prog == "tar":
        return _tar_sources(args, cwd)
    pos, target_given, i, ends = [], False, 0, False
    while i < len(args):
        a = args[i]
        if not ends and a == "--":
            ends = True
        elif not ends and a.startswith("-") and a != "-":
            if a.startswith("--target-directory") or a == "-t":
                target_given = True
            if a in OPT_ARG.get(prog, ()):
                i += 1
            elif prog == "zip" and a in ("-x", "-i", "--exclude", "--include"):
                while i + 1 < len(args) and not args[i + 1].startswith("-"):
                    i += 1
        else:
            pos.append(a)
        i += 1
    if prog == "zip":
        srcs = pos[1:]  # перший — ім'я архіву
    elif target_given:
        srcs = pos
    else:
        srcs = pos[:-1] if len(pos) >= 2 else []  # останній — призначення
    names = srcs if prog == "zip" else pos  # для перевірки імені agent.py (архів zip — не джерело)
    return [(s, cwd) for s in srcs], names


def _tar_sources(args, cwd):
    srcs, base, i, mode_ok, first = [], cwd, 0, True, True
    while i < len(args):
        a = args[i]
        if a.startswith("--"):
            name = a.split("=", 1)[0]
            if name in ("--extract", "--get", "--list", "--diff", "--compare"):
                mode_ok = False
            if name == "--directory":
                val = a.split("=", 1)[1] if "=" in a else (args[i + 1] if i + 1 < len(args) else "")
                base = _resolve(val, base) if base or os.path.isabs(val) else None
            if name in TAR_LONG_ARG and "=" not in a:
                i += 1
        elif (a.startswith("-") and a != "-") or (first and re.match(r"^[A-Za-z]+$", a)):
            letters = a.lstrip("-")
            dash = a.startswith("-")
            for k, ch in enumerate(letters):
                if ch in "xtd":
                    mode_ok = False
                if ch in TAR_ARG_LETTERS:
                    if dash and k < len(letters) - 1:  # -fARCHIVE / -Cdir
                        val = letters[k + 1:]
                    else:
                        i += 1
                        val = args[i] if i < len(args) else ""
                    if ch == "C":
                        base = _resolve(val, base) if base or os.path.isabs(val) else None
                    if dash:
                        break
        else:
            srcs.append((a, base))
        first = False
        i += 1
    return (srcs if mode_ok else []), [s for s, _ in srcs]  # імена — без архіву після -f


def copy_risk(command, cwd, shvars=None):
    """2026-10-26. Повертає опис ризику (рядок) або None.
    Ловить сегмент, програма якого (після sudo/env/command/nohup/time, basename) — cp/rsync/
    tar/zip/scp/mv і (а) аргумент — саме файл agent.py (basename; архів після tar -f і перший
    аргумент zip не рахуються), або (б) джерело (і для mv)
    резолвиться в корінь проєкту чи його предка (., ./, ./., $PWD, *, ./*, повний
    шлях, ~/AgentReachProject, ..). cwd — з input JSON; «cd X» у тій самій команді зсуває cwd
    для наступних сегментів (лінійно, без урахування підоболонок; cd -/без шляху до змінної —
    cwd невідомий, відносні джерела не перевіряються). Вкладене sh/bash -c '…' розбирається.
    Виняток: rsync/tar/zip з --exclude/-x, що містить agent.py. Текст у лапках і тіло
    heredoc — не команда. Прості присвоєння в тій самій команді (D=$PWD; cp -r "$D" …) підставляються.
    НЕ ловить: find -exec cp, xargs cp, змінну з export/сусідньої команди чи $(…)-підстановки,
    складні глоби (.[!.]*, *.py), pushd і повернення з (cd …) підоболонки,
    tar з -T списком, cpio/dd/ln/python shutil, віддалене host:path."""
    shvars = dict(shvars or {})
    tokens = _tokens(strip_heredocs(command))
    for seg in _segments(tokens):
        seg, assigns = _clean(seg)
        for asg in assigns:
            name, val = asg.split("=", 1)
            shvars[name] = _subst(val, cwd, shvars)  # $PWD розкривається в момент присвоєння
        if not seg:
            continue
        head = os.path.basename(seg[0])
        args = seg[1:]
        if head == "cd":
            dests = [a for a in args if not a.startswith("-")]
            if not dests:
                cwd = None if args else os.path.expanduser("~")
            else:
                cwd = _resolve(dests[0], cwd, shvars)
            continue
        for k in range(len(seg) - 2):
            if (os.path.basename(seg[k]) in SHELLS and seg[k + 1].startswith("-")
                    and "c" in seg[k + 1]):
                inner = copy_risk(seg[k + 2], cwd)
                if inner:
                    return inner
        if head not in COPY_PROGS:
            continue
        if head in ("rsync", "tar", "zip") and _excludes_key(head, args):
            continue
        srcs, names = _sources(head, args, cwd)
        if any(_is_key(a, cwd, shvars) for a in names):
            return f"{head}: аргумент — файл agent.py"
        for raw, base in srcs:
            p = _resolve(raw, base, shvars)
            if p and _covers_root(p):
                return f"{head}: джерело «{raw}» — це корінь проєкту (або тека над ним), тобто разом з agent.py"
    return None


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
    # 2026-10-26: копія ключа (cp -r . $T/ 25.10). Рахуємо ДО гілки git add; deny git add agent.py
    # лишається пріоритетним, звичайний git add без копіювання працює як раніше.
    risk = None
    if os.environ.get("KEYGUARD") != "0":
        try:
            risk = copy_risk(raw_command, data.get("cwd") or REPO)
        except Exception:
            risk = None  # fail-open

    command = strip_heredocs(raw_command)
    args = git_add_arg_tokens(command)
    if args is None and not risk:
        return

    if args is not None and any("agent.py" in a for a in args):
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

    if risk:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": (
                    "keyguard: команда копіює ключ agent.py (" + risk + "). RULES.md (розділ Git): "
                    "agent.py містить ключ і живе поза git; TROUBLES 2026-10-25 «Скопіював увесь проєкт "
                    "(cp -r .)…» — копія ключа в незахищену теку. Копіюй лише потрібні файли або додай "
                    "--exclude agent.py (zip: -x agent.py). Вимкнути перевірку: KEYGUARD=0."
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
