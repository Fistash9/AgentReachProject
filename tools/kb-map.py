#!/usr/bin/env python3
"""kb-map — карта-покажчик знань проєкту (лише читає, нічого не пише).

Навіщо: не перечитувати великі файли підряд. Одна команда дає адреси
записів (файл:рядок), далі читається лише потрібний розділ:
    sed -n '<рядок>,+30p' <файл>

Використання:
    python3 tools/kb-map.py <слово> [слово2 ...]  # записи, де є всі слова
    python3 tools/kb-map.py --all                 # уся карта (лише заголовки)
    python3 tools/kb-map.py -n 20 <слово>         # інший ліміт виводу

Пошук — без урахування регістру, за підрядком: у назві, TAGS і тексті
запису. Для різних форм слова беріть корінь ("дедуп", не "дедуплікація").
Карта будується щоразу з самих файлів, тож не застаріває.
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMORY = os.path.expanduser(
    "~/.claude/projects/-data-data-com-termux-files-home-AgentReachProject/memory")
DATE = re.compile(r"\((20\d\d-\d\d-\d\d)")
STATUS = re.compile(r"статус змінився", re.I)


def entries_md(path, level):
    """Записи файлу: заголовки рівня `level` (## або ###); розділ — найближчий ## вище."""
    try:
        lines = open(path, encoding="utf-8").read().split("\n")
    except OSError:
        return []
    rel = os.path.relpath(path, ROOT)
    out, cur, section = [], None, ""
    for i, line in enumerate(lines, 1):
        is_h2 = line.startswith("## ")
        is_entry = line.startswith(level + " ") if level != "#" else line.startswith("# ")
        if is_h2:
            section = line[3:].strip()
        if is_entry or (level == "###" and is_h2):
            if cur:
                out.append(cur)
            cur = None
            if is_entry:
                title = line.lstrip("#").strip()
                m = DATE.search(title)
                cur = {"file": rel, "line": i, "title": title, "date": m.group(1) if m else "",
                       "section": section if level == "###" else "", "tags": "",
                       "status": "", "body": []}
            continue
        if cur:
            cur["body"].append((i, line))
            s = line.strip()
            if s.startswith("TAGS:") and not cur["tags"]:
                cur["tags"] = s[5:].strip()
            if STATUS.search(s):
                cur["status"] = s.lstrip("-* ")[:70]
    if cur:
        out.append(cur)
    return out


def entries_memory():
    out = []
    for path in sorted(glob.glob(os.path.join(MEMORY, "*.md"))):
        text = open(path, encoding="utf-8").read()
        m = re.search(r"^description:\s*(.+)$", text, re.M)
        body = [(i, l) for i, l in enumerate(text.split("\n"), 1)]
        out.append({"file": "memory/" + os.path.basename(path), "line": 1,
                    "title": os.path.basename(path)[:-3], "date": "", "section": "пам'ять",
                    "tags": (m.group(1).strip('"') if m else "")[:90], "status": "", "body": body})
    return out


def build():
    e = []
    e += entries_md(os.path.join(ROOT, "TROUBLES.md"), "##")
    e += entries_md(os.path.join(ROOT, "BACKLOG.md"), "###")
    e += entries_md(os.path.join(ROOT, "RULES-WHY.md"), "##")
    e += entries_md(os.path.join(ROOT, "README.md"), "##")
    e += entries_md(os.path.join(ROOT, "GOALS.md"), "##")
    for p in sorted(glob.glob(os.path.join(ROOT, "agents", "*", "*.md"))):
        e += entries_md(p, "#")
    for p in sorted(glob.glob(os.path.join(ROOT, "trees", "*.md"))):
        e += entries_md(p, "#")
    e += entries_memory()
    return e


def fmt(x, hit=None):
    meta = x["tags"] or x["section"]
    s = f'{x["file"]}:{x["line"]} | {x["date"] or "—"} | {x["title"][:80]} | {meta[:60]}'
    if x["status"]:
        s += f' | {x["status"]}'
    if hit:
        s += f" | збіг у тексті: рядок {hit}"
    return s


def main(argv):
    limit = 10
    if argv[:1] == ["-n"] and len(argv) > 2:
        limit, argv = int(argv[1]), argv[2:]
    if not argv:
        print(__doc__)
        return 2
    entries = build()
    if argv == ["--all"]:
        for x in entries:
            print(fmt(x))
        return 0
    words = [w.lower() for w in argv]
    found = []
    for x in entries:
        head = (x["title"] + " " + x["tags"]).lower()
        text = head + " " + " ".join(l for _, l in x["body"]).lower()
        if not all(w in text for w in words):
            continue
        hit = None
        if not all(w in head for w in words):
            hit = next((i for i, l in x["body"] if words[0] in l.lower()), None)
        found.append((0 if hit is None else 1, x, hit))
    found.sort(key=lambda t: t[0])  # спершу збіги в назві/тегах
    for _, x, hit in found[:limit]:
        print(fmt(x, hit))
    if len(found) > limit:
        print(f"… ще {len(found) - limit} (уточніть слово або -n {len(found)})")
    if not found:
        print(f"Не в карті. Запасний шлях: grep -n -i '{argv[0]}' TROUBLES.md BACKLOG.md "
              "RULES-WHY.md trees/*.md; або коротший корінь слова.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
