#!/usr/bin/env python3
"""Перевірка зв'язків проєкту: чи ніщо не посилається в нікуди.

Запуск: python3 ~/AgentReachProject/tools/check-links.py
Код виходу 0 — усе ціле, 1 — є проблеми (перелік у виводі).
Викликається в session-close (крок 2.5) перед baton_pass.

Лише читає: файли, git, settings. Хуки запускає на нейтральному вході
(ls / правка TROUBLES.md) і перевіряє, що вони не падають і не блокують;
delegate-prompt-improver (викликає модель) і delegate-outcome-logger
(пише лог) пропускає — побічні ефекти.
"""
import glob
import json
import os
import re
import subprocess
import sys

P = os.environ.get("CHECK_ROOT") or os.path.expanduser("~/AgentReachProject")
MEM = os.path.expanduser(
    "~/.claude/projects/-data-data-com-termux-files-home-AgentReachProject/memory")
SKIP_RUN = ("prompt-improver", "outcome-logger")
ok, bad = 0, []


def chk(cond, msg):
    global ok
    if cond:
        ok += 1
    else:
        bad.append(msg)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def exists_glob(path):
    return bool(glob.glob(os.path.join(P, re.sub(r"<[^>]+>", "*", path))))


def main():
    os.chdir(P)
    rules = read("RULES.md")
    why = read("RULES-WHY.md")
    heads = re.findall(r"^#+ (.+)$", rules, re.M)

    # 1. симлінки на RULES.md
    real = os.path.realpath("RULES.md")
    for name in ("CLAUDE.md", "AGENTS.md"):
        chk(os.path.realpath(name) == real, f"{name} не веде на RULES.md")

    # 2. файли з великих літер (*.md), названі в RULES.md / RULES-WHY.md
    for src, text in (("RULES.md", rules), ("RULES-WHY.md", why)):
        for name in sorted(set(re.findall(r"\b([A-Z][A-Z_]+(?:-[A-Z]+)?\.md)\b", text))):
            found = glob.glob(name) + glob.glob("*/" + name)
            chk(bool(found), f"{src}: файл {name} не знайдено")

    # 3. шляхи в `лапках` у RULES.md (крім системних tmp і .trash/, що
    #    створюється лише при потребі)
    for p in sorted(set(re.findall(r"`([\w.<>/-]+/[\w.<>/-]*)`", rules))):
        if p.startswith("/") or p == ".trash/":
            continue
        chk(exists_glob(p), f"RULES.md: шлях {p} не існує")

    # 4. розділи RULES.md, на які посилаються правила й session-close
    refs = ["Навігац", "Checkpoint", "Робота з відкладеними", "DeepSeek", "Git",
            "Журнал vs знімок", "Видалення файлів"]
    for ref in refs:
        chk(any(ref in h for h in heads), f"RULES.md: розділ «{ref}» зник")

    # 5. хуки, названі в RULES.md, існують
    for h in sorted(set(re.findall(r"хук (?:у )?([a-z][a-z-]+)", rules))):
        chk(os.path.exists(f".claude/hooks/{h}-hook.py"), f"RULES.md: хук {h} — файлу немає")

    # 6. settings: команди хуків ведуть на наявні файли; кожен хук-файл підключений
    s = json.load(open(".claude/settings.local.json", encoding="utf-8"))
    hook_paths = []
    for ev, entries in s.get("hooks", {}).items():
        for e in entries:
            for h in e.get("hooks", []):
                for tok in h.get("command", "").replace("'", " ").split():
                    if tok.startswith("/") and tok.endswith((".py", ".mjs", ".sh")):
                        hook_paths.append(tok)
                        chk(os.path.exists(tok), f"settings {ev}: {tok} не існує")
    for f in sorted(glob.glob(os.path.join(P, ".claude/hooks/*.py"))):
        chk(f in hook_paths, f"хук {os.path.basename(f)} не підключений у settings")
        r = subprocess.run([sys.executable, "-m", "py_compile", f], capture_output=True)
        chk(r.returncode == 0, f"{os.path.basename(f)} не компілюється")

    # 7. хуки на нейтральному вході не падають і не блокують
    neutral = [
        {"tool_name": "Bash", "tool_input": {"command": "ls"}},
        {"tool_name": "Edit", "tool_input": {"file_path": P + "/TROUBLES.md",
                                             "old_string": "a", "new_string": "b"}},
    ]
    for f in sorted(set(p for p in hook_paths if p.endswith(".py"))):
        if any(s_ in f for s_ in SKIP_RUN):
            continue
        for n in neutral:
            n = dict(n, cwd=P, hook_event_name="PreToolUse", session_id="check",
                     transcript_path="/dev/null")
            r = subprocess.run([sys.executable, f], input=json.dumps(n),
                               capture_output=True, text=True, timeout=20)
            chk(r.returncode == 0 and '"deny"' not in r.stdout,
                f"{os.path.basename(f)} на нейтральному {n['tool_name']}: "
                f"rc={r.returncode} {r.stderr.strip()[:100]}")

    # 8. коміти, на які посилається RULES-WHY.md, існують
    for h in sorted(set(re.findall(r"\(([0-9a-f]{7})\)", why))):
        r = subprocess.run(["git", "cat-file", "-e", h + "^{commit}"], capture_output=True)
        chk(r.returncode == 0, f"RULES-WHY.md: коміт {h} не існує")

    # 9. шляхи проєкту в пам'яті Claude Code
    if os.path.isdir(MEM):
        for mf in sorted(glob.glob(os.path.join(MEM, "*.md"))):
            for p in sorted(set(re.findall(r"`((?:script-agent|reference-analyzer|tools|\.claude)/[\w.<>/-]*)`", read(mf)))):
                chk(exists_glob(p), f"пам'ять {os.path.basename(mf)}: шлях {p} не існує")

    # 10. menu.sh: цілі пунктів існують
    for p in re.findall(r"(~/AgentReachProject/[\w./-]+)", read("menu.sh")):
        fp = os.path.expanduser(p)
        chk(os.path.exists(fp), f"menu.sh: {p} не існує")
        if fp.endswith(".sh"):
            chk(os.access(fp, os.X_OK), f"menu.sh: {p} не виконуваний")

    print(f"check-links: OK перевірок {ok}, проблем {len(bad)}")
    for b in bad:
        print(" -", b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
