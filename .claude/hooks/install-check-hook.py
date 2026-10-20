#!/data/data/com.termux/files/usr/bin/python3
"""
PreToolUse hook (НЕ блокує): перед встановленням стороннього — скіла,
плагіна, MCP-сервера — нагадує 4 кроки з RULES.md «Перед ВСТАНОВЛЕННЯМ
стороннього». Раз на ціль за сесію.
Причина (RULES-WHY.md, 2026-10-09): скіл llm-council поставлено через
Bash `mkdir … && cp …` до повної перевірки; verify-nudge-hook бачить
.claude/skills/ лише через Edit/Write, тож мовчав.

Ловить:
- Write у нову (ще не існуючу) теку чи файл під .claude/skills/ або
  .claude/plugins/ (проєкт чи ~); правку наявного скіла — ні (це
  verify-nudge);
- Bash: сегмент команди, що ПОЧИНАЄТЬСЯ з cp/mv/rsync/ln/install/unzip/
  tar/mkdir/curl/wget/git clone і має .claude/skills чи .claude/plugins;
  python/node/bash/sh з таким шляхом і ознакою запису (makedirs, open(…'w'),
  writeFile, shutil, --dest…); `claude mcp add*`, `claude plugin(s)
  install|i|update|marketplace add`. З --help/-h — ні.
Команда розбирається з урахуванням лапок (shlex): текст у лапках
(echo '{…}', -m "…") і тіло heredoc не дають хибних спрацювань (клас
TROUBLES 2026-09-23). /plugin у вікні набирає користувач — це не виклик
інструмента, PreToolUse його не бачить (code.claude.com/docs/en/hooks).
Друга гілка (2026-10-20): установка ПАКЕТА (pip/pip3/pipx/uv/npm/pkg/apt/cargo install, python -m pip
install) → раз на сесію картка TROUBLES «Картка: як ставити «неставне» в Termux». Причина: рецепти (pkg
python-*, grun/glibc, npm linux-arm64…) були, а troubles-grep на установку мовчить навмисно (pip/npm/
install/termux — GENERIC_TAGS), тож 20.10 при пробі Graphify я їх не взяв (користувач: «встановлювали,
працює, а ти не користуєшся»).
Лог: .claude/logs/install-check.log. Будь-яка помилка — мовчить (fail-open).
"""
import json
import os
import re
import shlex
import sys
import time

PROJECT = "/data/data/com.termux/files/home/AgentReachProject"
LOG = os.path.join(PROJECT, ".claude", "logs", "install-check.log")
TARGET = re.compile(r"\.claude/(skills|plugins)(/[^\s'\";|&]*)?")
VERBS = {"cp", "mv", "rsync", "ln", "install", "unzip", "tar", "mkdir", "curl", "wget"}
WRAPPERS = {"sudo", "env", "command", "nohup", "time"}
SCRIPTS = {"python", "python3", "node", "bash", "sh"}
# запис зі скрипта: makedirs/mkdir, open(..., 'w'/'a'), writeFile, copy, shutil, --dest/--out
WRITE_MARK = re.compile(r"makedirs|mkdir|open\([^)]*['\"][wa]|write(File|_text)?|copy|shutil|--dest|--out")
# claude mcp add|add-json|add-from-claude-desktop; claude plugin(s) install|i|update|marketplace add
CARD = "## Картка: як ставити «неставне» в Termux"
PKG_MGR = {"pip": {"install"}, "pip3": {"install"}, "pipx": {"install"}, "uv": {"pip", "tool", "add"},
           "npm": {"install", "i", "add"}, "pkg": {"install", "i"}, "apt": {"install"}, "apt-get": {"install"},
           "cargo": {"install"}}
CLI = re.compile(r"(mcp\s+add(-json|-from-claude-desktop)?|plugins?\s+(install|i|update|marketplace\s+add))\b")


def strip_heredocs(cmd):
    out, lines, i = [], cmd.split("\n"), 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        m = re.search(r"<<-?\s*['\"]?(\w+)['\"]?", line)
        i += 1
        if m:
            end = m.group(1)
            while i < len(lines) and lines[i].strip() != end:
                i += 1
            i += 1
    return "\n".join(out)


def segments(cmd):
    """Команда → сегменти (списки слів) з урахуванням лапок: текст у лапках
    (echo '{…cp … .claude/skills…}', -m "…") лишається одним словом."""
    lex = shlex.shlex(cmd, posix=True, punctuation_chars=";&|")
    lex.whitespace_split = True
    lex.commenters = ""
    seg = []
    for tok in lex:
        if tok and set(tok) <= set(";&|"):
            if seg:
                yield seg
            seg = []
        else:
            seg.append(tok)
    if seg:
        yield seg


def bash_target(cmd):
    cmd = strip_heredocs(cmd)
    try:
        segs = list(segments(cmd))
    except ValueError:  # незакриті лапки — грубий розбір рядками
        segs = [ln.split() for ln in cmd.split("\n")]
    for seg in segs:
        while seg and (seg[0] in WRAPPERS or re.match(r"^\w+=", seg[0])):
            seg = seg[1:]  # sudo / env / VAR=… перед командою
        if not seg or "--help" in seg or "-h" in seg:
            continue
        head = os.path.basename(seg[0])
        rest = " ".join(seg[1:])
        if head == "claude" and CLI.match(rest):
            return "claude " + CLI.match(rest).group(0)
        t = TARGET.search(rest)
        if not t:
            continue
        if head in VERBS or (head == "git" and seg[1:2] == ["clone"]):
            return t.group(0)
        if head in SCRIPTS and WRITE_MARK.search(rest):
            return t.group(0)
    return None


def pkg_install(cmd):
    """Сегмент, що ставить пакет: «pip install …», «python3 -m pip install …», «venv/bin/pip install …»."""
    try:
        segs = list(segments(strip_heredocs(cmd)))
    except ValueError:
        return None
    for seg in segs:
        while seg and (seg[0] in WRAPPERS or re.match(r"^\w+=", seg[0]) or seg[0] == "timeout" or re.match(r"^\d+$", seg[0])):
            seg = seg[1:]
        if len(seg) >= 3 and os.path.basename(seg[0]).startswith("python") and seg[1] == "-m":
            seg = seg[2:]
        if len(seg) >= 2 and "--help" not in seg and seg[1] in PKG_MGR.get(os.path.basename(seg[0]), ()):
            return os.path.basename(seg[0])
    return None


def card():
    text = open(os.path.join(PROJECT, "TROUBLES.md"), encoding="utf-8").read()
    i = text.find(CARD)
    if i < 0:
        return None
    body = text[i:].split("\n## ", 1)[0]
    lines = [l for l in body.splitlines() if re.match(r"^\d\. ", l) or l.startswith("   ")]
    return "\n".join(lines)


def write_target(path, cwd):
    path = os.path.abspath(os.path.join(cwd or PROJECT, os.path.expanduser(path)))
    m = re.search(r"/\.claude/(skills|plugins)/([^/]+)", path)
    if not m:
        return None
    top = path[:m.end()]
    return None if os.path.exists(top) else top


def main():
    data = json.load(sys.stdin)
    tool = data.get("tool_name")
    inp = data.get("tool_input") or {}
    if tool == "Bash":
        mgr = pkg_install(inp.get("command") or "")
        if mgr:
            key = f"{data.get('session_id', '?')}\tpkg-card"
            seen = open(LOG).read() if os.path.exists(LOG) else ""
            body = card()
            if body and key + "\t" not in seen:
                os.makedirs(os.path.dirname(LOG), exist_ok=True)
                with open(LOG, "a") as f:
                    f.write(f"{key}\t{time.strftime('%Y-%m-%dT%H:%M:%S')}\n")
                print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext":
                    f"install-check: установка пакета ({mgr}). Перш ніж збирати чи обходити — рецепти, що вже "
                    f"працюють у Termux (TROUBLES «Картка: як ставити…»):\n{body}"}}, ensure_ascii=False))
                return
        target = bash_target(inp.get("command") or "")
    elif tool == "Write":
        target = write_target(inp.get("file_path") or "", data.get("cwd"))
    else:
        return
    if not target:
        return
    key = f"{data.get('session_id', '?')}\t{target}"
    seen = open(LOG).read() if os.path.exists(LOG) else ""
    if key + "\t" in seen:
        return
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f:
        f.write(f"{key}\t{time.strftime('%Y-%m-%dT%H:%M:%S')}\n")
    msg = (f"install-check: схоже на встановлення стороннього ({target}). "
           "RULES.md «Перед ВСТАНОВЛЕННЯМ»: (1) прочитано ПОВНІСТЮ? (2) звірено, що це "
           "те саме джерело/автор і нема новішої чи виправленої версії? (3) відгуки, "
           "issues, PR переглянуто? (4) підсумок показано і є «так» користувача? "
           "Якщо ні — зупинись і зроби спершу. Власний файл, не стороннє — ігноруй.")
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "additionalContext": msg}}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
