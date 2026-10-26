#!/usr/bin/env python3
"""Перевірка зв'язків проєкту: чи ніщо не посилається в нікуди.

Запуск: python3 ~/AgentReachProject/tools/check-links.py
Код виходу 0 — усе ціле, 1 — є проблеми (перелік у виводі).
Викликається в session-close (крок 2.5) перед baton_pass. Група 11 —
карта README.md (кожен .md у корені і tools/). Група 12 — порядок дерев
(закриті вниз, у кожної відкритої гілки рядок «черга»).

Лише читає: файли, git, settings. Хуки запускає на нейтральному вході
(ls / правка TROUBLES.md) і перевіряє, що вони не падають і не блокують;
delegate-prompt-improver (викликає модель) і delegate-outcome-logger
(пише лог) пропускає — побічні ефекти.

Інша версія без копії проєкту (2026-10-26; 25.10 для порівняння дерев
скопіювали ввесь проєкт разом з agent.py у tmp):
  --rev <ревізія>  розгорнути відстежувані файли ревізії (git archive) у
                   тимчасову теку, перевірити її і прибрати. agent.py, .env,
                   settings.local.json поза git — туди не потрапляють;
                   settings береться живий, шляхи в ньому переносяться на теку.
  --root <тека>    перевірити вказану теку (без копіювання).
Без аргументів — поведінка й вивід ті самі, що й раніше. Примітки режиму —
у stderr, stdout того ж формату.
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

P = os.environ.get("CHECK_ROOT") or os.path.expanduser("~/AgentReachProject")
LIVE = P      # жива тека: git-репозиторій і settings.local.json
ALT = False   # True — перевіряємо іншу теку (--rev / --root)
REPO = P      # де виконувати git (група 8)
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


def remap(tok):
    """Абсолютний шлях живої теки -> той самий шлях у перевірюваній (лише ALT)."""
    if ALT and tok.startswith(LIVE + "/"):
        return P + tok[len(LIVE):]
    return tok


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
    #    Виняток: PROTOCOL.md — ЗОВНІШНІЙ документ baton (The Baton Protocol v0.1),
    #    а не файл проєкту; RULES-WHY.md:200,229 цитує його як джерело, і це правда.
    #    Тому лагодимо перевірку, а не текст: множина токенів мінус {"PROTOCOL.md"}.
    #    SKILL.md лежить у .claude/skills/<скіл>/ — RULES-WHY.md:336,342 (2026-10-13).
    EXTERNAL_DOCS = {"PROTOCOL.md"}
    for src, text in (("RULES.md", rules), ("RULES-WHY.md", why)):
        tokens = set(re.findall(r"\b([A-Z][A-Z_]+(?:-[A-Z]+)?\.md)\b", text)) - EXTERNAL_DOCS
        for name in sorted(tokens):
            found = (glob.glob(name) + glob.glob("*/" + name)
                     + glob.glob(".claude/skills/*/" + name))
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
    sp = ".claude/settings.local.json"
    if ALT and not os.path.exists(sp):
        sp = os.path.join(LIVE, sp)
        print(f"check-links: settings.local.json поза git — беру живий {sp}",
              file=sys.stderr)
    s = json.load(open(sp, encoding="utf-8"))
    hook_paths = []
    for ev, entries in s.get("hooks", {}).items():
        for e in entries:
            for h in e.get("hooks", []):
                for tok in h.get("command", "").replace("'", " ").split():
                    if tok.startswith("/") and tok.endswith((".py", ".mjs", ".sh")):
                        tok = remap(tok)
                        hook_paths.append(tok)
                        chk(os.path.exists(tok), f"settings {ev}: {tok} не існує")
    # статуслайн — не хук: лише «підключений» і «існує», без прогону групи 7
    sl_paths = []
    for tok in s.get("statusLine", {}).get("command", "").replace("'", " ").split():
        if tok.startswith("/") and tok.endswith((".py", ".mjs", ".sh")):
            tok = remap(tok)
            sl_paths.append(tok)
            chk(os.path.exists(tok), f"settings statusLine: {tok} не існує")
    for f in sorted(glob.glob(os.path.join(P, ".claude/hooks/*.py"))):
        chk(f in hook_paths + sl_paths, f"хук {os.path.basename(f)} не підключений у settings")
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
        r = subprocess.run(["git", "cat-file", "-e", h + "^{commit}"], capture_output=True, cwd=REPO)
        chk(r.returncode == 0, f"RULES-WHY.md: коміт {h} не існує")

    # 9. шляхи проєкту в пам'яті Claude Code
    if os.path.isdir(MEM):
        for mf in sorted(glob.glob(os.path.join(MEM, "*.md"))):
            for p in sorted(set(re.findall(r"`((?:script-agent|reference-analyzer|tools|\.claude)/[\w.<>/-]*)`", read(mf)))):
                chk(exists_glob(p), f"пам'ять {os.path.basename(mf)}: шлях {p} не існує")

    # 10. menu.sh: цілі пунктів існують
    for p in re.findall(r"(~/AgentReachProject/[\w./-]+)", read("menu.sh")):
        fp = (P + p[len("~/AgentReachProject"):]) if ALT else os.path.expanduser(p)
        chk(os.path.exists(fp), f"menu.sh: {p} не існує")
        if fp.endswith(".sh"):
            chk(os.access(fp, os.X_OK), f"menu.sh: {p} не виконуваний")

    # 11. карта README.md: кожен .md у корені (не симлінк) і tools/ мають
    #     бути в ній посиланням [назва] — інакше нова сесія про них не знає
    readme = read("README.md")
    for f in sorted(glob.glob("*.md")):
        if f == "README.md" or os.path.islink(f):
            continue
        chk(f"[{f}]" in readme, f"README.md: у карті немає [{f}]")
    chk("[tools/]" in readme, "README.md: у карті немає [tools/]")

    # 12. порядок дерев (G2.6, 2026-10-25): закриті [x]/[~] — після всіх
    #     відкритих; кожна відкрита гілка має рядок «черга» з причиною місця
    for f in sorted(glob.glob("trees/*.md")):
        L = read(f).split("\n")
        st = [i for i, l in enumerate(L) if re.match(r"- \[.\] ", l)]
        seen = False
        for k, s in enumerate(st):
            e = st[k + 1] if k + 1 < len(st) else len(L)
            stt, code = re.match(r"- \[(.)\] (\S+)", L[s]).groups()
            if stt in "x~":
                seen = True
                continue
            chk(not seen, f"{f}: {code} відкрита після закритої — закриті вниз")
            chk(any(re.match(r"\s+черга", l) for l in L[s:e]),
                f"{f}: {code} без рядка «черга» (причина місця)")

    print(f"check-links: OK перевірок {ok}, проблем {len(bad)}")
    for b in bad:
        print(" -", b)
    return 1 if bad else 0


def cli():
    global P, ALT, REPO
    ap = argparse.ArgumentParser(description="Перевірка зв'язків проєкту.")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--rev", help="ревізія git (HEAD~5, хеш, гілка)")
    g.add_argument("--root", help="тека для перевірки замість живої")
    a = ap.parse_args()
    if not (a.rev or a.root):
        return main()
    ALT = True
    if a.root:
        P = os.path.abspath(a.root)
        REPO = P if os.path.exists(os.path.join(P, ".git")) else LIVE
        print(f"check-links: корінь {P}", file=sys.stderr)
        return main()
    r = subprocess.run(["git", "-C", LIVE, "rev-parse", "--verify", "-q",
                        a.rev + "^{commit}"], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"check-links: ревізію {a.rev} не знайдено", file=sys.stderr)
        return 2
    sha = r.stdout.strip()
    tmp = tempfile.mkdtemp(prefix="check-links-rev-")
    try:
        arc = subprocess.Popen(["git", "-C", LIVE, "archive", sha],
                               stdout=subprocess.PIPE)
        tx = subprocess.run(["tar", "-x", "-C", tmp], stdin=arc.stdout)
        arc.stdout.close()
        if arc.wait() != 0 or tx.returncode != 0:
            print("check-links: git archive | tar не вдався", file=sys.stderr)
            return 2
        P, REPO = tmp, LIVE
        print(f"check-links: ревізія {a.rev} ({sha[:7]}) у {tmp}", file=sys.stderr)
        if os.environ.get("CHECK_LINKS_KEEP"):
            print(f"check-links: KEEP — тека лишається", file=sys.stderr)
        return main()
    finally:
        os.chdir(LIVE)
        if not os.environ.get("CHECK_LINKS_KEEP"):
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(cli())
