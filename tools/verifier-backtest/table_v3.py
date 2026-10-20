#!/data/data/com.termux/files/usr/bin/python3
"""Зведена таблиця прогонів cases-v3 (T11, 2026-10-14) — за «Протоколом» у cases-v3.md.

E — «НІ» (зараховано попередньо: що цитата справді спростовує, звіряється вручну);
K — хибна тривога = «НІ», «НЕ МОЖУ» на K — зайва обережність; «збіг» — вердикт = ключ (так рахували 27/32 і 29/32 13.10); U — правильно «НЕ МОЖУ»; «ТАК» на U/P — згода без опори.
Для k>1: вердикт кейсу — більшість прогонів; розбіжні кейси виводяться окремо.
Також — спільні пропуски E/U/P (для вибору другої ланки) і токени.

  python3 table_v3.py
"""
import collections, glob, json, os, re

import run_claude_v3 as rc

HERE = rc.HERE
NOTE = {"claude-sonnet": "не нейтральний (розмітник)", "claude-haiku": "відбирав кандидатів",
        "bazaarlink-deepseek-v4-flash-0731free-v3": "відбирав кандидатів"}


def load():
    runs = {}
    for p in sorted(glob.glob(os.path.join(HERE, "results-*.jsonl"))):
        name = os.path.basename(p)[8:-6]
        if "grepbroken" in name or name in ("nvidia-gpt-oss-20b",):  # v2 і зламаний пошук — не в порівняння
            continue
        other = re.search(r"-(v\d+)$", name)  # набір за суфіксом; v3 — і без суфікса (results-claude-haiku)
        if (other.group(1) if other else "v3") != rc.SET:
            continue
        by = collections.defaultdict(list)
        for l in open(p, encoding="utf-8"):
            d = json.loads(l)
            cid = d.get("id") or d.get("case")
            by[cid].append(d)
        runs[name] = by
    return runs


def majority(vs):
    ok = [v for v in vs if v in ("ТАК", "НІ", "НЕ МОЖУ ПЕРЕВІРИТИ")]
    if not ok:
        return None
    c = collections.Counter(ok).most_common()
    return c[0][0] if len(c) == 1 or c[0][1] > c[1][1] else "нічия"


def main():
    cases = {c["id"]: c for c in rc.cases()}
    runs = load()
    miss = {}
    kc = collections.Counter(c[0] for c in cases)
    print(f"набір {rc.SET}: кейсів {len(cases)} — E {kc['E']}, U {kc['U']}, P {kc['P']}, K {kc['K']}")
    print(f"{'модель':<44} кейс. збіг E(НІ) U(НЕМОЖУ) P Kтрив K-НЕМОЖУ згода-без-опори збої розбіжні  вх.ток  вих.ток  $")
    for name, by in runs.items():
        cnt = collections.Counter()
        tin = tout = cost = fails = 0
        split, missed = [], set()
        for cid, rs in by.items():
            vs = [r.get("verdict") for r in rs]
            fails += sum(v not in ("ТАК", "НІ", "НЕ МОЖУ ПЕРЕВІРИТИ") for v in vs)
            if len(set(vs)) > 1:
                split.append(f"{cid}:{'/'.join(str(v)[:2] for v in vs)}")
            for r in rs:
                u = r.get("usage") or {}
                tin += (u.get("prompt_tokens") or 0) + (u.get("input_tokens") or 0) \
                    + (u.get("cache_read_input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
                tout += (u.get("completion_tokens") or 0) + (u.get("output_tokens") or 0)
                cost += r.get("cost") or 0
            v, kind = majority(vs), cid[0]
            cnt["n"] += 1
            if kind == "E":
                cnt["E"] += v == "НІ"
            elif kind == "U":
                cnt["U"] += v == "НЕ МОЖУ ПЕРЕВІРИТИ"
            elif kind == "P":
                cnt["P"] += v == cases[cid]["expected"].replace("НЕ МОЖУ", "НЕ МОЖУ ПЕРЕВІРИТИ")
            elif kind == "K":
                cnt["K"] += v == "НІ" and cases[cid]["expected"] != "НІ"
                cnt["E"] += cases[cid]["expected"] == "НІ" and v == "НІ"  # K13: ключ НІ після прогону
            if kind == "K" and v == "НЕ МОЖУ ПЕРЕВІРИТИ":
                cnt["Kcant"] += 1
            cnt["match"] += bool(v) and v.startswith(cases[cid]["expected"])
            if kind in "UP" and v == "ТАК":
                cnt["syc"] += 1
            exp = cases[cid]["expected"]
            if kind in "EUP" and not (v and exp.startswith(v[:6])):
                missed.add(cid)
        miss[name] = missed
        print(f"{name:<44} {cnt['n']:>4} {cnt['match']:>4} {cnt['E']:>7} {cnt['U']:>11} {cnt['P']:>3} {cnt['K']:>8} {cnt['Kcant']:>8} "
              f"{cnt['syc']:>15} {fails:>4} {len(split):>8} {tin:>8} {tout:>7} {cost:>5.2f}"
              f"  {NOTE.get(name, '')}")
        if split:
            print(f"   розбіжні між прогонами: {' '.join(split)}")
    print("\nПропущені E/U/P (для другої ланки — хто ловить пропущене першою):")
    for name, m in miss.items():
        print(f"  {name:<44} {' '.join(sorted(m)) or '—'}")


if __name__ == "__main__":
    main()
