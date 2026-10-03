#!/usr/bin/env python3
"""L0-мапа «що вже досягнуто» — збирає досягнуте з трьох джерел і міряє опору.

Навіщо: пункти `done` у baton, «Завершено» у BACKLOG і вузли [x] у дереві
(усі рівні вкладеності) живуть у трьох різних місцях і ніде не зведені. Проста звірка
показала, що дослівно збігається ~1% — тобто це не «одне й те саме,
записане тричі», а три майже неперетинні списки.

Форма взята з C4-проби: рівень «знизу вгору» + чек-ліст критеріїв.
Наш критерій рівня L0 — ОПОРА: у кожного досягнутого пункту має бути
адреса (коміт, файл або запис у журналі). Пункт без адреси — не доказ,
а спогад.

Запуск:  python3 tools/achieved-map.py [--json <шлях>]
"""

import argparse
import glob
import json
import os
import re
import subprocess
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Було \b[0-9a-f]{7,40}\b — ловило не-хеші (20260930, 1000000). Тепер: чистий hex
# (не самі цифри) + обов'язкова перевірка, що об'єкт справді є комітом (is_commit).
COMMIT = re.compile(r"\b(?![0-9]+\b)[0-9a-f]{7,40}\b")
PATHRE = re.compile(r"[A-Za-z0-9_./-]+\.(?:md|py|sh|js|json|yml|yaml|jsonl)")

GROUPS = [
    ("DSH / платформа", r"dsh|proot|beads|bd |пісочниц|profiles|плагін"),
    ("Пам'ять і дерево", r"дерев|картц|голограм|kb-map|tree|пам'ят|M\d|G\d|T\d"),
    ("DeepSeek / моделі", r"deepseek|thinking|effort|максимум токен|max_tokens|nvidia"),
    ("Baton / процес", r"baton|естафет|pass|хук|скіл|rules|troubles|journal"),
    ("Інше / зовнішнє", r".*"),
]


def external_entries():
    """Докази, що фізично лежать ПОЗА проєктом: конфіг dsh, профілі, дошка Beads.

    Навіщо: звірка L0 показала 4 досягнуті пункти, чия правда не в нашому
    репо — правило в ~/.dsh/AGENTS.md, DSH_PERMISSION_MODE у коді dsh,
    профіль exp, дошка tree-qis. Без цих коренів пошук адрес їх не бачить.
    """
    home = os.path.expanduser("~")
    out = []
    md_like, yaml_like, line_like = [], [], []
    md_like.append(os.path.join(home, ".dsh", "AGENTS.md"))
    for p in glob.glob(os.path.join(home, ".dsh", "profiles", "*", "*.yml")):
        yaml_like.append(p)
    for p in glob.glob(os.path.join(home, ".dsh", "profiles", "*", "package.json")):
        line_like.append(p)
    yaml_like.append(os.path.join(home, "dsh-app/node_modules/@deepseek-ai/dsh-base/cordis.patch.yml"))
    line_like += sorted(glob.glob(os.path.join(home, "beads-export-*.jsonl")))

    import importlib.util
    spec = importlib.util.spec_from_file_location("kbmap_ext", os.path.join(ROOT, "tools", "kb-map.py"))
    kb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(kb)
    for p in md_like:
        if os.path.isfile(p):
            out += kb.entries_md(p, "##")
    for p in yaml_like:
        # рядок за рядком: блочний індекс давав адресу «початок блока» (рядок 15)
        # замість рядка, де справді лежить факт (DSH_PERMISSION_MODE — 232)
        if not os.path.isfile(p):
            continue
        for i, l in enumerate(open(p, encoding="utf-8"), 1):
            if l.strip() and not l.strip().startswith("#"):
                out.append({"file": p, "line": i, "title": l.strip()[:110], "date": "",
                            "section": "external yaml", "tags": "", "status": "", "body": []})
    for p in line_like:
        if not os.path.isfile(p):
            continue
        for i, l in enumerate(open(p, encoding="utf-8"), 1):
            if l.strip():
                out.append({"file": p, "line": i, "title": l.strip()[:110], "date": "",
                            "section": "external line", "tags": "", "status": "",
                            "body": []})
    return [e for e in out if e["body"] or e["title"]]


def group_of(text):
    low = text.lower()
    for name, pat in GROUPS:
        if re.search(pat, low):
            return name
    return "Інше / зовнішнє"


STOP = set("""і та в у на що це як до з за по не але для від про при або чи вже ще всі все було
бути його її їх ми він вона так ні то ж би щоб після перед через між під над без саме лише
тільки дуже можна треба потрібно стало зроблено тому коли де куди який яка які цей ця ці той
те ті свій своє свої всіх ніж якщо раз разом далі потім також йому їм мене нам вас них
the and for with that this from have has was were not are but all one two into out
більше менше повинен має мають був була були буде будуть кожно кожен кожна
""".split())


def addresses(order):
    """Шукає адресу для пунктів без опори — через kb-map (build()), не своїм кодом."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("kbmap", os.path.join(ROOT, "tools", "kb-map.py"))
    kb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(kb)
    entries = kb.build()
    # kb-map бере з cards лише заголовок файлу (рядок 1) — для дерев це марна
    # адреса: матчилось «Ідея: дерево задач + голограма» замість конкретного
    # вузла. Тому для trees/ індексуємо КОЖЕН вузол окремо.
    tree_entries = []
    for p in sorted(glob.glob(os.path.join(ROOT, "trees", "*.md"))):
        lines = open(p, encoding="utf-8").read().split("\n")
        cur = None
        for i, l in enumerate(lines, 1):
            m = re.match(r"^\s*- \[( |x|>)\] (.+)$", l)
            if m:
                if cur:
                    tree_entries.append(cur)
                cur = {"file": os.path.relpath(p, ROOT), "line": i, "title": m.group(2).strip()[:110],
                       "date": "", "section": "вузол дерева", "tags": "",
                       "status": "", "body": []}
            elif cur is not None and l.startswith(("  ", "\t")):
                cur["body"].append((i, l))
        if cur:
            tree_entries.append(cur)
    entries = [e for e in entries if not (e["file"].startswith("trees/") and e["line"] == 1)]
    entries += tree_entries
    ext = external_entries()
    # kb.entries_md дає шлях відносно ROOT — для зовнішніх файлів це «../../..»;
    # робимо абсолютним, щоб адреса була придатною для копіювання
    for e in ext:
        if not os.path.isabs(e["file"]):
            e["file"] = os.path.abspath(os.path.join(ROOT, e["file"]))
    entries += ext
    texts = [(e, (e["title"] + " " + e["tags"] + " " +
                  " ".join(l for _, l in e["body"])).lower()) for e in entries]
    ext_ids = {id(e) for e in ext}

    tok = re.compile(r"[a-zа-яїієґ0-9_]{5,}")
    out = []
    for it in order:
        if it["has_support"]:
            continue
        words = {w for w in tok.findall(it["text"].lower()) if w not in STOP}
        if not words:
            out.append({**it, "address": None, "why": "немає слів для пошуку"})
            continue
        df = {w: sum(1 for _, t in texts if w in t) for w in words}
        rare = sorted((w for w in words if 1 <= df[w] <= 25), key=lambda w: df[w])[:6]
        if not rare:
            out.append({**it, "address": None, "why": "усі слова надто часті"})
            continue
        best = None
        for e, t in texts:
            head = (e["title"] + " " + e["tags"]).lower()
            hits = [w for w in rare if w in t]
            in_head = [w for w in hits if w in head]
            # СТРОГІШЕ: мало 2 збігів; або один, але в заголовку/тегах запису
            if not (len(hits) >= 3 or (len(hits) >= 2 and in_head) or (len(in_head) == 1 and df[in_head[0]] <= 3)):
                continue
            score = len(hits) + 2 * len(in_head)
            if best is None or score > best[0]:
                best = (score, e, hits, in_head)
        if best is None:
            out.append({**it, "address": None, "why": f"нічого переконливого за словами: {', '.join(rare[:3])}"})
        else:
            _, e, hits, in_head = best
            out.append({**it, "address": f'{e["file"]}:{e["line"]}',
                        "title": e["title"][:80], "hits": hits, "in_head": in_head,
                        "external": id(e) in ext_ids,
                        "score": best[0], "confidence": "висока" if in_head else "низька"})
    return out


_COMMIT_CACHE = {}


def is_commit(sha):
    """Чи справді існує такий коміт. Самого regex мало: він ловив дати (20260930),
    суми (1000000) і id сесій (5389f068) — через це 3 пункти мали хибну опору «коміт»."""
    if sha not in _COMMIT_CACHE:
        r = subprocess.run(["git", "cat-file", "-e", f"{sha}^{{commit}}"],
                           cwd=ROOT, capture_output=True)
        _COMMIT_CACHE[sha] = (r.returncode == 0)
    return _COMMIT_CACHE[sha]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None)
    ap.add_argument("--addresses", action="store_true",
                    help="шукати адресу для пунктів без опори (через kb-map)")
    a = ap.parse_args()

    seen, order = set(), []
    snaps = sorted(glob.glob(os.path.join(ROOT, ".baton", "history", "pass-*.json")),
                   key=lambda p: int("".join(c for c in os.path.basename(p) if c.isdigit())))
    snaps.append(os.path.join(ROOT, ".baton", "baton.json"))
    for f in snaps:
        try:
            d = json.load(open(f, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for x in d.get("done", []):
            x = str(x).strip()
            if x and x not in seen:
                seen.add(x)
                order.append({"text": x, "first_seen": os.path.basename(f)})

    backlog = open(os.path.join(ROOT, "BACKLOG.md"), encoding="utf-8").read()
    bl_items = []
    if "## Завершено" in backlog:
        # Межа розділу — до наступного «## ». Без цього «Завершено» тяглось до кінця
        # файлу й прихоплювало чужі розділи (Unverified Claims, Аналізатор, Відкладено):
        # 56 замість 41.
        sec = backlog.split("## Завершено", 1)[-1]
        nxt = re.search(r"\n## ", sec)
        if nxt:
            sec = sec[:nxt.start()]
        bl_items = [l[2:].strip() for l in sec.split("\n") if l.startswith("- ")]
    TX_NODE = re.compile(r"^\s*- \[x\]\s*(.+)$")
    tx = []
    for p in glob.glob(os.path.join(ROOT, "trees", "*.md")):
        for l in open(p, encoding="utf-8"):
            m = TX_NODE.match(l.rstrip("\n"))
            if m:  # усі рівні: було l.startswith("- [x]") — тільки верхній, 7 замість 19
                tx.append({"text": m.group(1).strip(), "file": os.path.relpath(p, ROOT)})

    def norm(s):
        return re.sub(r"\s+", " ", re.sub(r"[`*_«»\"'(),:;!?…—–-]", " ", s.lower())).strip()

    backlog_norm = norm(backlog)  # ОДИН раз: раніше norm(backlog) кликався на кожне вікно

    for it in order:
        t = it["text"]
        files = PATHRE.findall(t)
        it["commits"] = [c for c in COMMIT.findall(t) if is_commit(c)]
        it["files"] = [f for f in files if os.path.exists(os.path.join(ROOT, f.lstrip("./")))]
        # опора трьох класів: коміт · файл · згадка журналу (журнали без .md теж рахуються)
        it["journal"] = bool(re.search(r"TROUBLES|BACKLOG|CONTEXT|HANDOFF|RULES-WHY|WEEKLY|"
                                       r"trees/|картц|журнал", t, re.I))
        it["group"] = group_of(t)
        it["support_class"] = ("коміт" if it["commits"] else
                               "файл" if it["files"] else
                               "журнал" if it["journal"] else "немає")
        it["has_support"] = it["support_class"] != "немає"
        # дослівна присутність у BACKLOG (6 слів) — по заздалегідь нормованому тексту
        w = norm(t).split()
        it["in_backlog"] = any(" ".join(w[i:i + 6]) in backlog_norm
                               for i in range(max(1, len(w) - 5)))

    by_group = {}
    for it in order:
        g = by_group.setdefault(it["group"], {"n": 0, "with_support": 0})
        g["n"] += 1
        g["with_support"] += 1 if it["has_support"] else 0

    unsupported = [it for it in order if not it["has_support"]]
    classes = {}
    for it in order:
        classes[it["support_class"]] = classes.get(it["support_class"], 0) + 1
    rep = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "baton_done_unique": len(order),
           "backlog_done": len(bl_items),
           "tree_done_nodes": len(tx),
           "support_classes": classes,
           "with_support": sum(1 for it in order if it["has_support"]),
           "support_share": round(sum(1 for it in order if it["has_support"]) / len(order), 3) if order else None,
           "in_backlog": sum(1 for it in order if it["in_backlog"]),
           "by_group": by_group, "unsupported": unsupported,
           "baton_items": order, "backlog_items": bl_items, "tree_items": tx}

    print("== L0 · ЩО ВЖЕ ДОСЯГНУТО ==")
    print(f"джерела: baton done {len(order)} унікальних · BACKLOG «Завершено» {len(bl_items)}"
          f" · вузлів [x] {len(tx)}")
    print(f"з них дослівно в BACKLOG: {rep['in_backlog']} ({round(rep['in_backlog']/len(order)*100)}%)"
          " ← списки майже не перетинаються")
    print(f"\nопора (коміт / наявний файл / згадка журналу): {rep['with_support']}/{len(order)}"
          f" = {round(rep['support_share']*100)}%   {classes}")
    print("\nза темами:")
    for g, v in sorted(by_group.items(), key=lambda kv: -kv[1]["n"]):
        print(f"  {v['n']:>3}  з опорою {v['with_support']:>3}  {g}")
    if unsupported:
        print(f"\nбез опори ({len(unsupported)}) — перші 8:")
        for it in unsupported[:8]:
            print(f"  · {it['text'][:100]}")

    path = a.json or os.path.join(ROOT, ".claude", "logs",
                                  f"L0-achieved-{datetime.now().strftime('%Y%m%d-%H%M')}.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)

    if a.addresses:
        found = addresses(order)
        rep["address_search"] = found
        ok = [f for f in found if f.get("address")]
        print(f"\n== АДРЕСИ ДЛЯ ПУНКТІВ БЕЗ ОПОРИ ({len(found)}) ==")
        for f in ok:
            print(f'  {f["address"]:<28} ← {f["text"][:70]}')
            print(f'      {f["title"]}  [збіг: {", ".join(f["hits"][:3])}]')
        bad = [f for f in found if not f.get("address")]
        if bad:
            print(f"\n  без адреси ({len(bad)}):")
            for f in bad:
                print(f'   · {f["text"][:70]} ← {f["why"]}')
        new_cov = (rep["with_support"] + len(ok)) / len(order)
        print(f"\nопора стане: {rep['with_support']}+{len(ok)} = "
              f"{round(new_cov*100)}% (було {round(rep['support_share']*100)}%)"
              "  ← це КАНДИДАТИ, не підтверджені адреси")

    json.dump(rep, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\nзнімок: {path}")


if __name__ == "__main__":
    main()
