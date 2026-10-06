#!/usr/bin/env python3
"""Перевірка ключів у доданих рядках коміту (git pre-commit, 2026-10-06).

Навіщо: git-add-status-hook бачить лише ТЕКСТ команди git add і ловить
назву agent.py; ключ, вставлений в інший файл, чи `git add .` він пропускає.
Ідея — з ECC (BACKLOG «ECC: 6 ідей», п.1); прецедент — TROUBLES #11.

Ловить у рядках, що ДОДАЮТЬСЯ (git diff --cached):
  1) точні значення наших ключів (agent.py, .env) — читаються локально,
     ніде не друкуються;
  2) шаблони чужих ключів: sk-, ghp_, AKIA, nvapi-, AIza (перед ними не
     може стояти літера/цифра — інакше «ask-questions…» спрацьовувало).
Перевірено на історії: 393 коміти — 0 спрацювань.

  python3 tools/secret-scan.py            # як pre-commit: код 1 = знайдено
  обійти свідомо: git commit --no-verify
Лише stdlib.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATTERN = re.compile(
    r"(?<![A-Za-z0-9])(sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{36}|AKIA[0-9A-Z]{16}"
    r"|nvapi-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{35})")


def known_secrets():
    vals = set()
    try:
        vals.update(re.findall(r"sk-[A-Za-z0-9]{20,}",
                               open(os.path.join(ROOT, "agent.py"), encoding="utf-8").read()))
    except OSError:
        pass
    try:
        for line in open(os.path.join(ROOT, ".env"), encoding="utf-8"):
            if "=" in line and not line.lstrip().startswith("#"):
                v = line.split("=", 1)[1].strip().strip("'\"")
                if len(v) >= 16:
                    vals.add(v)
    except OSError:
        pass
    return vals


def mask(s):
    return s[:4] + "…" + f"({len(s)} симв.)"


def main():
    diff = subprocess.run(["git", "-C", ROOT, "diff", "--cached", "-U0", "--no-color"],
                          capture_output=True, text=True, errors="replace").stdout
    secrets = known_secrets()
    hits, path, lineno = [], "?", 0
    for line in diff.splitlines():
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else line[4:]
            continue
        m = re.match(r"@@ -\S+ \+(\d+)", line)
        if m:
            lineno = int(m.group(1))
            continue
        if not line.startswith("+"):
            continue
        body = line[1:]
        for s in secrets:
            if s in body:
                hits.append((path, lineno, "наш ключ", mask(s)))
        for p in PATTERN.findall(body):
            if p not in secrets:
                hits.append((path, lineno, "шаблон ключа", mask(p)))
        lineno += 1
    if not hits:
        return 0
    print("secret-scan: КОМІТ ЗУПИНЕНО — у доданих рядках схоже на ключ:", file=sys.stderr)
    for path, n, kind, m in hits:
        print(f"  {path}:{n} — {kind} {m}", file=sys.stderr)
    print("Прибери ключ (git restore --staged <файл>) або, якщо це хибне\n"
          "спрацювання, свідомо: git commit --no-verify. TROUBLES #11.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
