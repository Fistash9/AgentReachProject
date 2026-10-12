#!/usr/bin/env python3
"""focus-tree — зведене дерево: ціль → напрями → відкриті вузли + пункти батона (2026-10-12).

Навіщо (G2.5, trees/derevo-i-golograma.md): п'ять карток trees/*.md мають кожна
свою чергу, спільної немає; GOALS.md лише посилається на них. Користувач
12.10: «дерево в якому … головна ціль, і сортування що до чого відноситься і що
зараз потрібніше за все … цей єлемент звязаний зі всіма іншими».

Що робить (лише читає, нічого не пише):
- групує картки за розділами GOALS.md (Головна / Зараз / Чекають / поза цілями);
- для кожного відкритого вузла ([ ], [>], [?]) рахує ЗВ'ЯЗКИ — скільки ІНШИХ
  вузлів (не свій рід: батько/діти) і чи GOALS.md згадують його код у своєму
  тексті; окремо — згадки в BACKLOG.md;
- пункти, що випали з батона (логіка baton-diff.py), чіпляє до вузлів за кодом
  у тексті пункту; групи, закриті в картках («група #A→#B … закрит…»), — окремо.
Порядок вузлів у картці НЕ змінює: черга — правило Q10 і рішення користувача.
Число зв'язків — ознака, не бал.

  python3 tools/focus-tree.py            # зведене дерево + топ зв'язаних + батон
  python3 tools/focus-tree.py --top 15   # інший розмір топу
Лише stdlib.
"""
import argparse
import glob
import importlib.util
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPEN = {" ", ">", "?", "●", "⏸"}          # ✓/x/~ — закрито
IDRE = re.compile(r"(?<![\w#-])([GQZTM]\d{1,2}(?:\.\d{1,2}){0,2})(?![\w])")


def _mod(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"),
                                                  os.path.join(ROOT, "tools", name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


TI = _mod("trees-index")
BD = _mod("baton-diff")


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def parse_card(path):
    """Вузли картки: id, статус, назва (як у trees-index), батько, текст блоку."""
    names = {nid: (st, name) for nid, st, name in TI.nodes(path)}
    lines = read(path).split("\n")
    # шапка картки (до першого вузла: UP, ЗВ'ЯЗАНЕ, KILL…) — теж джерело зв'язків, не вузол
    out, stack = [], []
    cur = {"id": "шапка", "st": "", "name": "", "parent": None, "header": True,
           "file": os.path.relpath(path, ROOT), "text": []}
    out.append(cur)
    for ln in lines:
        m = TI.NODE.match(ln)
        a = None if m else TI.ARROW.match(ln)
        if m or a:
            indent = len(m.group(1)) if m else len(ln) - len(ln.lstrip())
            nid = m.group(3) if m else a.group(1)
            while stack and stack[-1][0] >= indent:
                stack.pop()
            parent = stack[-1][1] if stack else None
            st, name = names.get(nid, (m.group(2) if m else a.group(2), ""))
            cur = {"id": nid, "st": st, "name": name, "parent": parent,
                   "file": os.path.relpath(path, ROOT), "text": [ln]}
            out.append(cur)
            stack.append((indent, nid))
        elif cur is not None:
            cur["text"].append(ln)
    for n in out:
        n["text"] = "\n".join(n["text"])
        own = n["text"].split("\n", 1)[0]
        n["owner"] = (re.search(r"@([\w-]+)", own) or [None, ""])[1]
    return out


def family(a, b):
    return a == b or b.startswith(a + ".") or a.startswith(b + ".")


def goals_sections():
    """trees/<файл> → (розділ GOALS.md, рядок-мітка)."""
    sec, res = "", {}
    for ln in read(os.path.join(ROOT, "GOALS.md")).split("\n"):
        if ln.startswith("## "):
            sec = ln[3:].strip()
        for f in re.findall(r"trees/[\w/-]+\.md", ln):
            res.setdefault(f, (sec, ln.strip()[:90]))
    return res


def baton_dropped():
    """[(#старий, #новий, мітка, пункт)] — та сама логіка, що в baton-diff.py main()."""
    hist = os.path.join(ROOT, ".baton", "history")
    cur_p = os.path.join(ROOT, ".baton", "baton.json")
    if not os.path.exists(cur_p):
        return []
    snaps = sorted((int(m.group(1)), p) for p in glob.glob(os.path.join(hist, "pass-*.json"))
                   for m in [re.search(r"pass-(\d+)\.json$", p)] if m)
    cur = BD.load(cur_p)
    vers = [(n, BD.load(p)) for n, p in snaps]
    if not vers or vers[-1][0] != cur.get("passCount"):
        vers.append((cur.get("passCount"), cur))
    out = []
    for i in range(len(vers) - 1):
        (n_old, old), later = vers[i], vers[i + 1:]
        for key, label in BD.FIELDS:
            for item in old.get(key) or []:
                if not any(BD.same(item, x) for _, v in later for x in (v.get(key) or [])):
                    out.append((n_old, vers[i + 1][0], label, BD.norm(item)))
    return out


def closed_groups(alltext):
    """Пари (A, B), для яких у картках є «#A→#B» і слово «закрит…» у межах 700 симв. після."""
    res = set()
    for m in re.finditer(r"#(\d+)\s*→\s*#(\d+)", alltext):
        if re.search(r"[Зз]акрит", alltext[m.end():m.end() + 700]):
            res.add((int(m.group(1)), int(m.group(2))))
    return res


def short(s, n=78):
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + " …"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=10)
    a = ap.parse_args()

    cards = sorted(glob.glob(os.path.join(ROOT, "trees", "**", "*.md"), recursive=True))
    allnodes = [n for p in cards for n in parse_card(p)]
    nodes = [n for n in allnodes if not n.get("header")]
    by_id = {}
    for n in nodes:
        by_id.setdefault(n["id"], []).append(n)
    goals_txt = read(os.path.join(ROOT, "GOALS.md"))
    backlog = read(os.path.join(ROOT, "BACKLOG.md"))

    # зв'язки: хто з інших вузлів (не з роду) згадує код
    for n in nodes:
        n["refs"] = set()
    for src in allnodes:
        for nid in set(IDRE.findall(src["text"])):
            for tgt in by_id.get(nid, []):
                # рід (батько/діти) — за кодом, незалежно від файлу: G2.x у trees/g2/ — частини G2
                if tgt is src or tgt.get("header") or family(tgt["id"], src["id"]):
                    continue
                tgt["refs"].add(f'{src["file"].split("/")[-1][:-3]}:{src["id"]}')
    for nid in set(IDRE.findall(goals_txt)):
        for tgt in by_id.get(nid, []):
            tgt["refs"].add("GOALS.md")
    bl = {nid: len(re.findall(r"(?<![\w#-])" + re.escape(nid) + r"(?![\w.]\d|\w)", backlog))
          for nid in by_id}

    gs = goals_sections()
    order = {"Головна": 0, "Зараз": 1, "Чекають": 2}
    def sec_key(f):
        s = gs.get(f, ("", ""))[0]
        return next((v for k, v in order.items() if s.startswith(k)), 3)

    files = sorted({n["file"] for n in nodes}, key=lambda f: (sec_key(f), f))
    head = re.search(r"^## Головна.*\n(.+)", goals_txt, re.M)
    print("ЦІЛЬ (GOALS.md):", short(head.group(1).strip(), 100) if head else "—")
    last = None
    for f in files:
        sk = sec_key(f)
        if sk != last:
            print("\n" + {0: "ГОЛОВНА", 1: "ЗАРАЗ", 2: "ЧЕКАЮТЬ"}.get(sk, "ПОЗА ЦІЛЯМИ GOALS.md (згадка лише в примітках або ніде)"))
            last = sk
        ns = [n for n in nodes if n["file"] == f]
        op = [n for n in ns if n["st"] in OPEN]
        title = read(os.path.join(ROOT, f)).split("\n", 1)[0].lstrip("# ").strip()
        print(f"  ■ {short(title, 70)} — {f} · відкритих {len(op)} з {len(ns)}")
        for n in op:
            depth = 0
            p = n["parent"]
            while p:
                depth += 1
                p = next((x["parent"] for x in ns if x["id"] == p), None)
            own = f' @{n["owner"]}' if n["owner"] else ""
            print(f'    {"  " * depth}[{n["st"]}] {n["id"]} {short(n["name"], 64)}{own}'
                  f' · зв\'язків {len(n["refs"])}' + (f' · BACKLOG {bl[n["id"]]}' if bl[n["id"]] else ""))

    print(f"\nНАЙЗВ'ЯЗАНІШІ ВІДКРИТІ (скільки інших вузлів/GOALS згадують; топ {a.top}):")
    op = sorted((n for n in nodes if n["st"] in OPEN), key=lambda n: -len(n["refs"]))
    for n in op[:a.top]:
        cards_from = sorted({r.split(":")[0] for r in n["refs"]})
        print(f'  {len(n["refs"]):>3}  [{n["st"]}] {n["id"]} {short(n["name"], 56)} — з: {", ".join(cards_from)}')

    alltext = "\n".join(read(p) for p in cards)
    closed = closed_groups(alltext)
    drop = baton_dropped()
    print(f"\nБАТОН: випало пунктів {len(drop)}; закриті групи в картках: "
          + (", ".join(f"#{x}→#{y}" for x, y in sorted(closed)) or "жодної"))
    groups = {}
    for o, nw, lab, item in drop:
        groups.setdefault((o, nw), []).append((lab, item))
    for (o, nw), items in groups.items():
        mark = "закрита" if (o, nw) in closed else f"відкрита, {len(items)}"
        print(f"  #{o}→#{nw} ({mark})")
        if (o, nw) in closed:
            continue
        for lab, item in items:
            ids = [i for i in dict.fromkeys(IDRE.findall(item)) if i in by_id]
            where = ", ".join(f'{i}[{by_id[i][0]["st"]}]' for i in ids) or "без вузла"
            print(f"    → {where:<18} {short(item, 70)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
