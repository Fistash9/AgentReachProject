#!/data/data/com.termux/files/usr/bin/python3
"""
PreToolUse Bash (БЛОКУЄ, deny): два запобіжники від «вбивці дочірніх процесів» Android (межа 32 на всі
застосунки) — рецензія сесії 940a8b9a (DeepSeek, 22.10, механізми M1 і M2; рішення користувача «Усі 4 зараз»).

1. Самозбіг: `pgrep -f`/`pkill -f` без `-A` (--ignore-ancestors) і без `[x]` у шаблоні знаходить власну
   оболонку, бо шаблон є в її командному рядку. 22.10 двічі: хибне «Obsidian працює» і `pkill` убив мою ж
   оболонку (код 144); рецепт TROUBLES:4871 був, але не застосовувався. procps-ng 4.0.7 у Termux має `-A`
   (перевірено: без -A 3 хибні збіги, з -A 0; `pkill -A -f` убив ціль, оболонка жива).
2. Установка (pkg/apt/pip/npm… — розбір з install-check-hook, не копія): якщо процесів користувача > LIMIT
   або працює Obsidian (/opt/obsidian) — deny. 22.10 13:11 `pkg install` поверх «закритого» Obsidian дав
   27 → 38 процесів за <11 с, Android убив tmux і сесію (TROUBLES «Збій 22.10 13:11»). Сплеск установки ~11,
   тож LIMIT = 32 − 11 = 21.

Лог: .claude/logs/proc-guard.log. Будь-яка помилка — мовчить (fail-open).
Тест: echo '{"tool_name":"Bash","tool_input":{"command":"pkill -f x"}}' | python3 proc-guard-hook.py
"""
import importlib.util
import json
import os
import re
import subprocess
import sys
import time

PROJECT = "/data/data/com.termux/files/home/AgentReachProject"
LOG = os.path.join(PROJECT, ".claude", "logs", "proc-guard.log")
LIMIT = 21
WRAPPERS = {"sudo", "env", "command", "nohup", "time", "timeout", "setsid"}


def install_check():
    spec = importlib.util.spec_from_file_location(
        "install_check", os.path.join(PROJECT, ".claude", "hooks", "install-check-hook.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def selfmatch(cmd, ic):
    """Перший сегмент pgrep/pkill з -f без -A і без «[» у шаблоні → текст сегмента, інакше None."""
    try:
        segs = list(ic.segments(ic.strip_heredocs(cmd)))
    except ValueError:
        return None
    for seg in segs:
        while seg and (seg[0] in WRAPPERS or re.match(r"^\w+=", seg[0]) or re.match(r"^\d+[smh]?$", seg[0])):
            seg = seg[1:]
        if not seg or os.path.basename(seg[0]) not in ("pgrep", "pkill"):
            continue
        opts = [w for w in seg[1:] if w.startswith("-") and not w.startswith("--")]
        longs = [w for w in seg[1:] if w.startswith("--")]
        full = "--full" in longs or any("f" in o[1:] for o in opts)
        anc = "--ignore-ancestors" in longs or any("A" in o[1:] for o in opts)
        pats = [w for w in seg[1:] if not w.startswith("-")]
        if full and not anc and not any("[" in p for p in pats):
            return " ".join(seg)
    return None


def own_procs():
    out = subprocess.run(["ps", "-e", "-o", "user=,args="], capture_output=True, text=True, timeout=5).stdout
    me = subprocess.run(["id", "-un"], capture_output=True, text=True, timeout=5).stdout.strip()
    rows = [l.split(None, 1) for l in out.splitlines() if l.strip()]
    mine = [r[1] if len(r) > 1 else "" for r in rows if r[0] == me]
    obsidian = sum(1 for a in mine if a.startswith("/opt/obsidian"))
    return len(mine), obsidian


def log(kind, detail):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f:
        f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')}\t{kind}\t{detail[:200]}\n")


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": reason}}, ensure_ascii=False))


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash":
        return
    cmd = (data.get("tool_input") or {}).get("command") or ""
    ic = install_check()
    seg = selfmatch(cmd, ic)
    if seg:
        log("selfmatch", seg)
        return deny(f"proc-guard: `{seg}` — -f без -A знайде і власну оболонку (шаблон є в її командному рядку; "
                    "22.10 двічі: хибне «працює» і вбита оболонка, код 144). Додай -A (--ignore-ancestors), "
                    "напр. `pkill -A -f '…'`, або шаблон з [x]: '/opt/[o]bsidian'.")
    mgr = ic.pkg_install(cmd)
    if mgr:
        n, obs = own_procs()
        if obs or n > LIMIT:
            log("install", f"{mgr} procs={n} obsidian={obs}")
            why = f"працює Obsidian ({obs} процесів)" if obs else f"процесів уже {n} > {LIMIT}"
            return deny(f"proc-guard: установка ({mgr}) зараз небезпечна — {why}. Установка додає ~11 процесів за "
                        "секунди; понад 32 Android убиває найстаріші (tmux, сесію) — 22.10 13:11. Спершу закрити "
                        "Obsidian (`pkill -A -f /opt/obsidian`) і попросити користувача закрити DSH та agent.py, "
                        f"перерахувати `ps -e -o user= | grep -c \"$(id -un)\"` (≤ {LIMIT}).")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
