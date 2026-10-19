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


def regex(frags):
    return re.compile("|".join(re.escape(p) for p in frags), re.I) if frags else None


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
