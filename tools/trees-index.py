#!/usr/bin/env python3
"""Повний список вузлів дерев: файл:ID [статус] назва (2026-10-06).

Навіщо: агент назвав T5 «скілом пошуку» за обрізаною назвою з підказки хука,
не відкривши вузол (trees/pidrozdil-deepseek.md, T6.4). Рецензія DSH
(cc-nodeids-1): потрібне авторитетне джерело назв — рекурсивне (trees/g2/
хук не бачить), з ключем файл:ID (ID повторюються між картками: G2, M1–M3) і
зі зшиванням назв, що тягнуться на кілька рядків (T3, M3).
Замість файлу INDEX.md (пропозиція DSH) — інструмент: список завжди свіжий і
не смітить у git status.

  python3 tools/trees-index.py            # усі вузли
  python3 tools/trees-index.py T5 G2      # лише ці ID (у всіх картках)
Лише stdlib.
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NODE = re.compile(r"^(\s*)- \[(.)\] (\S+)\s+(.*)$")
ARROW = re.compile(r"^\s*[▸▶·]\s+(\S+)\s+(\S)\s+(.*)$")   # формат trees/g2/g2.md
OWNER = re.compile(r"\s@[\w-]+\s*$")
# рядок-поле під вузлом («done when:», «evidence C1 (…):», «UP:») — не продовження назви
FIELD = re.compile(r"^\s*(- \[|[^\s:]{1,25}( [^\s:]{1,15}){0,3}:|\(?[A-ZА-ЯІЇЄ]{3,}\b|—)")
CAP = 200


def nodes(path):
    lines = open(path, encoding="utf-8").read().split("\n")
    out, i = [], 0
    while i < len(lines):
        m = NODE.match(lines[i])
        a = None if m else ARROW.match(lines[i])
        if not (m or a):
            i += 1
            continue
        if m:
            indent, st, nid, name = len(m.group(1)), m.group(2), m.group(3), m.group(4)
            j = i + 1
            while (j < len(lines) and lines[j].strip()
                   and len(lines[j]) - len(lines[j].lstrip()) > indent
                   and not FIELD.match(lines[j])):
                name += " " + lines[j].strip()
                j += 1
        else:
            nid, st, name = a.group(1), a.group(2), a.group(3)
        name = OWNER.sub("", name).strip()
        if len(name) > CAP:
            name = name[:CAP].rsplit(" ", 1)[0] + " …"
        out.append((nid, st, name))
        i += 1
    return out


def main():
    want = set(sys.argv[1:])
    found = set()
    for path in sorted(glob.glob(os.path.join(ROOT, "trees", "**", "*.md"), recursive=True)):
        rel = os.path.relpath(path, ROOT)
        for nid, st, name in nodes(path):
            if want and nid not in want:
                continue
            found.add(nid)
            print(f"{rel}:{nid} [{st}] {name}")
    for nid in sorted(want - found):
        print(f"{nid}: немає в trees/ (жодної картки)")


if __name__ == "__main__":
    main()
