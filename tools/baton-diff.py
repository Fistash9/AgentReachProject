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
# Записка handoffNote: сервер ЗАМІНЮЄ її щоразу (server.mjs:156), повна записка кожної передачі — у ledger (:168).
# Пункт записки — речення з ознакою незробленого кроку (25.10, m3-diag: #78→#79 і #80→#81 губили такі речення).
# (?<!\w): «незакомічене закомічено» містить «не закомічено» всередині слова — хибна тривога S1 бектесту 25.10
STEP = re.compile(r"(?<!\w)(у новій сесії|першим|ще не виправлено|не звірен|не закомічено|перевірити)", re.I)
POOL_KEYS = ("next", "openQuestions", "done", "watchOut")


def sentences(text):
    """Речення записки: межа — «.!?» + пробіл або «;» поза дужками (у дужках «;» — частина речення)."""
    out, cur, depth, t = [], [], 0, norm(text)
    for i, ch in enumerate(t):
        cur.append(ch)
        depth += (ch in "([«") - (ch in ")]»")
        nxt = t[i + 1] if i + 1 < len(t) else " "
        if nxt == " " and (ch in ".!?" or (ch == ";" and depth <= 0)):
            out.append("".join(cur).strip())
            cur = []
    if "".join(cur).strip():
        out.append("".join(cur).strip())
    return out


def note_items(note):
    return [x for x in sentences(note or "") if STEP.search(x)]


def note_lost(old_note, pool):
    """Пункти старої записки, яких нема в pool (рядки нової естафети) — та сама same(), що й для next."""
    return [it for it in note_items(old_note) if not any(same(it, y) for y in pool if y)]


def norm(s):
    return " ".join(str(s).split())


def words(s):
    # тег власника «@claude-code»/«@dsh» на початку не рахуємо: він давав кожній парі 2 спільні слова, і короткий
    # новий пункт «накривав» старий (живий тест baton-guard 23.10: 10 зниклих → показано 9)
    return {w for w in re.findall(r"\w+", re.sub(r"^\s*@[\w-]+", "", norm(s)).lower()) if len(w) > 2}


def same(a, b, threshold=0.5):
    """Старий пункт a живе в новому тексті b (навіть переформульований): частка слів a, знайдених у b.
    До 2026-10-23 ділили на min(|a|,|b|) — короткий b («тест», «@claude-code …») «накривав» довгий a, і зниклий
    пункт не показувався (живий тест baton-guard: 10 зниклих → 9; з історії #66…#73 — 5 прихованих)."""
    wa, wb = words(a), words(b)
    if not wa or not wb:
        return norm(a) == norm(b)
    return len(wa & wb) / len(wa) >= threshold


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def ledger_pairs(path):
    """Сусідні передачі з ledger: [(old_row, new_row)], new.pass == old.pass + 1 (скидання лічильника — розрив)."""
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                if r.get("event") == "pass":
                    rows.append(r)
    return [(o, n) for o, n in zip(rows, rows[1:]) if n.get("pass") == (o.get("pass") or 0) + 1]


def snapshots_by_time(dirs, current):
    """Знімок естафети за updatedAt (= t події pass у ledger; номери pass повторюються після скидання 28.09)."""
    out = {}
    for d in dirs:
        for p in glob.glob(os.path.join(d, "**", "*.json"), recursive=True) + [current]:
            try:
                v = load(p)
            except (OSError, ValueError):
                continue
            if isinstance(v, dict) and v.get("updatedAt"):
                out[v["updatedAt"]] = v
    return out


def pair_pool(new_row, snap_old, snap_new):
    """Рядки нової естафети: записка з ledger + поля знімка (done/watchOut — лише додане цією передачею)."""
    pool = [str(new_row.get("note") or "")]
    if snap_new:
        for k in POOL_KEYS:
            items = snap_new.get(k) or []
            if k in ("done", "watchOut") and snap_old:
                items = items[len(snap_old.get(k) or []):]
            pool += [str(x) for x in items]
    return pool


def note_check(ledger, snapdirs, current, last=0):
    """[(old_row, new_row, повний_знімок?, [втрачені пункти])] для сусідніх передач."""
    pairs = ledger_pairs(ledger)
    if last:
        pairs = pairs[-last:]
    snaps = snapshots_by_time(snapdirs, current)
    res = []
    for o, n in pairs:
        so, sn = snaps.get(o.get("t")), snaps.get(n.get("t"))
        res.append((o, n, bool(sn), note_lost(o.get("note"), pair_pool(n, so, sn))))
    return res


def note_report(a):
    if not os.path.exists(a.ledger):
        return
    res = note_check(a.ledger, a.snapdirs or [a.history], a.current, a.note_last)
    total = 0
    for o, n, full, lost in res:
        if lost:
            src = "" if full else " (знімка нової нема — звірено лише з запискою)"
            print(f"== записка #{o['pass']} → #{n['pass']}: випало {len(lost)}{src}")
            for it in lost:
                print(f"   - [Записка] {it}")
            total += len(lost)
    print(f"baton-diff: записки — передач {len(res)}, випало пунктів {total}.")


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--history", default=os.path.join(root, ".baton", "history"))
    ap.add_argument("--current", default=os.path.join(root, ".baton", "baton.json"))
    ap.add_argument("--ledger", default=os.path.join(root, ".baton", "ledger.jsonl"))
    ap.add_argument("--note-last", type=int, default=1, help="скільки останніх передач перевіряти за запискою (0 — усі)")
    ap.add_argument("--snapdirs", nargs="*", default=None,
                    help="теки зі знімками pass-*.json для повної нової естафети (за замовч. --history)")
    a = ap.parse_args()
    note_report(a)

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
