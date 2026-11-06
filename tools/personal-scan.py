#!/usr/bin/env python3
"""Пошук особистого в тому, що йде назовні (2026-10-19).

Навіщо: 19.10 у звірку verify-before-show пішов вивід `git show` з рядком Author (логін і
пошта) — до NVIDIA; напередодні фрагменти логіна стояли в моїй grep-команді й пішли в експорт
до DeepSeek (TROUBLES «Зовнішня перевірка сесії 0a207074», п.7.1). Маска була лише в
session-export.py, і логіни вписано в код під git. Тепер фрагменти — у файлі поза git, а
перевіряють один і той самий список: хук personal-guard (delegate/deepseek), deepseek-search.py
(--file), session-export.py (маска) і крок 3.10 session-close.

  python3 tools/personal-scan.py ФАЙЛ...   → код 1 і «файл:рядок» на кожен збіг; 0 — чисто

Самі фрагменти не друкуються (вивід потрапляє в журнал сесії) — лише перші 2 символи. Лише stdlib.
"""
import os
import re
import sys

PATTERNS = os.path.expanduser("~/.config/agent-reach/personal-patterns.txt")


def load(path=PATTERNS):
    """Фрагменти з файлу; None — файлу немає (перевірка вимкнена, про це треба сказати)."""
    try:
        with open(path, encoding="utf-8") as f:
            return [s.strip() for s in f if s.strip() and not s.lstrip().startswith("#")]
    except OSError:
        return None


# (2026-11-06) Крипто-адреси — будь-які, не лише зі списку: адреса гаманця з повідомлення
# користувача двічі пішла в DeepSeek, бо списку фрагментів вона не знала (TROUBLES «Зовнішня
# перевірка сесії 1a543a43», п.31). Біткоїн bc1…, ефір 0x…; старі «1…/3…» і трон «T…» не беремо —
# ловили шматки посилань (builder.aws.com/content/3Fz…, 5 хибних на експорті 1a543a43).
CRYPTO = r"\b(?:bc1[a-z0-9]{25,87}|0x[0-9a-fA-F]{40})\b"


def regex(frags):
    parts = [re.escape(p) for p in frags or []] + [CRYPTO]
    return re.compile("|".join(parts), re.I)


def hide(s):
    return s[:2] + "…"


def scan_text(text, rx, where="текст"):
    hits = []
    if rx is None:
        return hits
    for n, line in enumerate(text.splitlines(), 1):
        for m in rx.finditer(line):
            hits.append(f"{where}:{n} ({hide(m.group(0))})")
    return hits


def scan_files(paths, rx):
    hits = []
    for p in paths:
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                hits += scan_text(f.read(), rx, p)
        except OSError:
            continue
    return hits


def main():
    frags = load()
    if frags is None:
        sys.exit(f"personal-scan: немає {PATTERNS} — перевірка не виконана")
    hits = scan_files(sys.argv[1:], regex(frags))
    for h in hits:
        print(h)
    print(f"personal-scan: файлів {len(sys.argv) - 1}, збігів {len(hits)}", file=sys.stderr)
    sys.exit(1 if hits else 0)


if __name__ == "__main__":
    main()
