#!/data/data/com.termux/files/usr/bin/python3
"""PreToolUse delegate/deepseek: особисте в промпті чи files[] — маскувати (delegate) або не відправляти (deepseek) (2026-10-19).

Навіщо: 19.10 я надіслав NVIDIA вивід `git show` з рядком Author (логін і пошта користувача);
до того фрагменти логіна пішли в експорт до DeepSeek (TROUBLES «Зовнішня перевірка сесії
0a207074», п.7.1). Маска жила лише в session-export.py, на виклики назовні охоронця не було.
Рішення користувача 19.10 «Так, усі 4 пункти» → «А. Сам маскує» (логін є в TROUBLES/CONTEXT/
SERVER/USER_PROFILE — блок зупиняв би кожен аудит цих файлів).
Перевірка — tools/personal-scan.py (фрагменти з ~/.config/agent-reach/personal-patterns.txt,
поза git). delegate: збіг → копії files[] у $TMPDIR/personal-guard/ і промпт з [особисте]
(updatedInput) + підказка «замасковано». deepseek: deny — там паралельно працює переписувач,
його updatedInput перебив би маску. Файлу шаблонів немає — пропускаю з підказкою. Інша
помилка — мовчки (fail-open), як у сусідніх хуків.
Межа: інструмент deepseek (під-сесія) може сам читати файли — це хук не бачить.
Журнал: .claude/logs/personal-guard.jsonl. Відкат: прибрати запис personal-guard-hook з
PreToolUse у .claude/settings.local.json.
"""
import datetime
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG = os.path.join(ROOT, ".claude", "logs", "personal-guard.jsonl")
MASK = "[особисте]"


def load():
    spec = importlib.util.spec_from_file_location("personal_scan",
                                                  os.path.join(ROOT, "tools", "personal-scan.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    data = json.load(sys.stdin)
    name = data.get("tool_name", "")
    if not (name.startswith("mcp__delegate__") or name.startswith("mcp__deepseek__")):
        return
    ps = load()
    frags = ps.load()
    inp = data.get("tool_input") or {}
    if frags is None:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": f"personal-guard: немає {ps.PATTERNS} — особисте не перевірено"}},
            ensure_ascii=False))
        return
    rx = ps.regex(frags)
    hits = []
    for k in ("prompt", "system", "message"):
        if isinstance(inp.get(k), str):
            hits += ps.scan_text(inp[k], rx, k)
    hits += ps.scan_files([p for p in inp.get("files") or [] if isinstance(p, str)], rx)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"t": datetime.datetime.now().isoformat(timespec="seconds"),
                            "session": data.get("session_id"), "tool": name, "hits": hits},
                           ensure_ascii=False) + "\n")
    if not hits:
        return
    if name.startswith("mcp__deepseek__"):
        reason = ("personal-guard: у тому, що йде назовні, є особисте користувача: "
                  + "; ".join(hits[:10]) + ". Прибери його (для git show — --format без автора) і повтори виклик.")
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                                 "permissionDecision": "deny",
                                                 "permissionDecisionReason": reason}},
                         ensure_ascii=False))
        return
    new = dict(inp)
    for k in ("prompt", "system", "message"):
        if isinstance(inp.get(k), str):
            new[k] = rx.sub(MASK, inp[k])
    tmp = os.path.join(os.environ.get("TMPDIR", "/tmp"), "personal-guard")
    os.makedirs(tmp, exist_ok=True)
    files = []
    for p in inp.get("files") or []:
        if isinstance(p, str) and ps.scan_files([p], rx):
            with open(p, encoding="utf-8", errors="replace") as f:
                body = rx.sub(MASK, f.read())
            q = os.path.join(tmp, datetime.datetime.now().strftime("%H%M%S-") + os.path.basename(p))
            with open(q, "w", encoding="utf-8") as f:
                f.write(body)
            files.append(q)
        else:
            files.append(p)
    if inp.get("files"):
        new["files"] = files
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "updatedInput": new,
        "additionalContext": (f"personal-guard: замасковано {len(hits)} збіг(ів) особистого як {MASK} "
                              "(" + "; ".join(hits[:5]) + "); цитати з цих місць у відповіді будуть з маскою.")}},
        ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
