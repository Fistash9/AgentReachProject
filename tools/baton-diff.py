#!/usr/bin/env python3
"""baton-diff: що випало з baton між передачами.

Порівнює знімки .baton/history/pass-<N>.json між собою і з поточним
.baton/baton.json. Для «Далі» (next) і «Відкриті питання» (openQuestions)
друкує пункти, які були в старішій версії й зникли в наступній і більше
не з'являлись до поточної. Лише читає файли, нічого не змінює.

Навіщо: baton_pass замінює next/openQuestions, а baton_pick_up показує
лише останній стан — забуте в новій записці ніхто не помічає (аудит
2026-09-26: 8 забутих пунктів, trees/baton-audit-2026-09-26.md).
Запуск: після baton_pick_up, до прибирання знімків (RULES.md «Baton»).

  python3 tools/baton-diff.py [--history DIR] [--current FILE]
"""
import argparse
import glob
import json
import os
import re
import sys

FIELDS = (("next", "Далі"), ("openQuestions", "Відкрите питання"))


def norm(s):
    return " ".join(str(s).split())


def words(s):
    return {w for w in re.findall(r"\w+", norm(s).lower()) if len(w) > 2}


def same(a, b, threshold=0.5):
    """Той самий пункт, навіть переформульований: частка спільних слів."""
    wa, wb = words(a), words(b)
    if not wa or not wb:
        return norm(a) == norm(b)
    return len(wa & wb) / min(len(wa), len(wb)) >= threshold


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--history", default=os.path.join(root, ".baton", "history"))
    ap.add_argument("--current", default=os.path.join(root, ".baton", "baton.json"))
    a = ap.parse_args()

    snaps = []
    for p in glob.glob(os.path.join(a.history, "pass-*.json")):
        m = re.search(r"pass-(\d+)\.json$", p)
        if m:
            snaps.append((int(m.group(1)), p))
    snaps.sort()
    if not os.path.exists(a.current):
        print(f"baton-diff: немає {a.current}")
        return 1
    cur = load(a.current)
    versions = [(n, load(p)) for n, p in snaps]
    cur_n = cur.get("passCount")
    if not versions or versions[-1][0] != cur_n:
        versions.append((cur_n, cur))
    if len(versions) < 2:
        print(f"baton-diff: знімків для порівняння немає (є лише #{cur_n}).")
        return 0

    # для кожного пункту — у яких версіях він був
    total = 0
    for i in range(len(versions) - 1):
        n_old, old = versions[i]
        n_new, new = versions[i + 1]
        later = versions[i + 1:]
        dropped = []
        for key, label in FIELDS:
            for item in old.get(key) or []:
                if not any(same(item, x) for _, v in later for x in (v.get(key) or [])):
                    dropped.append((label, item))
        if dropped:
            print(f"== #{n_old} → #{n_new}: випало {len(dropped)}")
            for label, item in dropped:
                print(f"   - [{label}] {norm(item)}")
            total += len(dropped)
    print(f"baton-diff: версій {len(versions)} (#{versions[0][0]}…#{versions[-1][0]}), "
          f"випало пунктів {total}. Для кожного: зроблено / у BACKLOG / відкинути "
          f"— вирішити з користувачем, потім прибрати старі знімки (TRASH.md).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
