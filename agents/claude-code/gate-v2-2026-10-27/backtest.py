"""Бектест воріт «агенти» v2 (2026-10-27; Якість роботи агентів › Q12 Реєстр помилок › ворота «агенти» v2 від центру).
Для кожного власного виклику оркестратора (головний ланцюжок, не isSidechain) будує вікно подій «від останньої роздачі»
тим самим розбором, що й хук (v2_line_events), і кличе те саме рішення (v2_decide) з копії edit-gate-hook.py.
Мірить в обидва боки: (і) докори Р9 «агенти/робиш сам» без deny у вікні перед собою; (іі) нові deny і їхня мітка
(влучний / хибний / напівхибний — ОЦІНКА під-агента: правило за описом і контекстом + ручні поправки MANUAL нижче).
Запуск: python3 backtest.py [--sweep]   (вивід → backtest.out / sweep.out)"""
import glob, importlib.util, json, os, re, sys
os.environ.pop("ANTHROPIC_BASE_URL", None); os.environ.pop("EDIT_GATE_AGENTS", None)
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "../../.."))
P = os.path.expanduser("~/.claude/projects/-data-data-com-termux-files-home-AgentReachProject/")


def load(path, nm):
    s = importlib.util.spec_from_file_location(nm, path); m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m); return m


eg = load(os.path.join(HERE, "edit-gate-hook.py"), "eg_v2")
agv = load(os.path.join(HERE, "answer-gate-shadow-hook.py"), "agv_v2")
er = load(os.path.join(ROOT, "tools/error-registry.py"), "er")
TRAIN = ["6b187e96", "2487d837"]
HOLD = ["cfca89fe", "4cab3538", "cb82f9d3", "4dc8a94e"]  # відкладені: на них поріг не підбирається
RE_AG = re.compile(r"агент|робиш\s+сам|сам\s+робиш|віддаєш", re.I)
ANY_DELEG = eg.V2_DELEG_G
HOOKED = {"Edit", "Write", "MultiEdit", "Bash"}  # PreToolUse matcher edit-gate (перевірено 27.10)
RE_CLOSE_H = re.compile(r"закр\w* сесі|завершуєм|закриваєм|на сьогодні все|згортаєм|checkpoint", re.I)
RE_CLOSE_D = re.compile(r"baton|естафет|закрит|session|claimcheck|handoff|HANDOFF|git status|git log|git diff|коміт|"
                        r"commit|TRASH|cost-report|link|memory|пам.ят", re.I)
RE_CHECK_D = re.compile(r"перевір|звір|check|verify|звіт|report|число|чисел|diff", re.I)
# Ручні поправки мітки (сесія, час до секунди) → (мітка, чому); оцінка під-агента за описом і контекстом.
MANUAL = {
    ("6b187e96", "2026-10-26T08:39:57"): ("напів", "запис у TROUBLES разом з комітом: запис — доробка, коміт — законний"),
    ("2487d837", "2026-10-26T14:37:34"): ("напів", "читання відповіді DSH — нагляд за агентом"),
    ("2487d837", "2026-10-26T14:38:35"): ("напів", "3-й крок після звіту: перевірка чисел делегата кодом (правило проєкту)"),
    ("2487d837", "2026-10-26T14:48:05"): ("напів", "крок скіла verify-before-show"),
    ("2487d837", "2026-10-26T15:20:38"): ("хибний", "очікування DSH — нагляд, не робота"),
    ("2487d837", "2026-10-27T06:02:52"): ("напів", "діагноз замка — можна віддати, але це розбір відмови користувачу"),
    ("2487d837", "2026-10-27T06:52:46"): ("влучний", "записи у вузол/пам'ять за 12 с до докору"),
    ("cb82f9d3", "2026-10-25T07:53:27"): ("влучний", "аналіз журналів delegate — обмежена задача для агента"),
    ("4dc8a94e", "2026-10-25T19:38:01"): ("напів", "звірка заміни сервера baton — не закриття, а перевірка"),
}


def events(sid):
    path = glob.glob(P + sid + "*.jsonl")[0]
    ev = []
    for line in open(path, encoding="utf-8", errors="ignore"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        ev += eg.v2_line_events(d)
    return ev


def reproaches(ev):
    return [i for i, e in enumerate(ev) if e[0] == "human" and er.is_correction(e[2]) and er.classify(e[2]) == "Р9"
            and RE_AG.search(e[2])]


def closing_zone(ev):
    """Індекси подій у зоні закриття: від слів «закрий сесію…» / Skill session-close до наступного baton_pass."""
    z, on = set(), False
    for i, e in enumerate(ev):
        if e[0] == "human" and RE_CLOSE_H.search(e[2]) or e[0] == "tool" and e[2] == "Skill" and \
                "session-close" in str(e[3].get("skill", "")):
            on = True
        if on:
            z.add(i)
        if e[0] == "tool" and e[2] == "mcp__baton__baton_pass":
            on = False
    return z


def label(sid, ev, j, zone):
    e = ev[j]; inp = e[3]; desc = str(inp.get("description", "")); cmd = str(inp.get("command", ""))
    k = (sid, e[1][:19])
    if k in MANUAL:
        return MANUAL[k][0] + "*"
    if j in zone or re.search(r"baton|закрит|claimcheck|HANDOFF|session-close|естафет", desc, re.I):
        return "хибний"  # рутина закриття сесії
    if re.search(r"\bgit (?:status|add|commit)\b", cmd):
        return "хибний"  # коміт — дія оркестратора
    back = ev[max(0, j - 4):j]
    if any(x[0] == "report" for x in back) and RE_CHECK_D.search(desc):
        return "напів"  # точкова перевірка свіжого звіту
    hs = [i for i in range(j) if ev[i][0] == "human"]
    if hs and sum(1 for x in ev[hs[-1] + 1:j] if x[0] == "tool" and x[2] in eg.V2_WORK) < 3 and "?" in ev[hs[-1]][2]:
        return "напів"  # перший крок відповіді на питання користувача
    return "влучний"


def run(sid, flags, n_lim, k_lim, ev=None, verbose=False):
    ev = ev or events(sid)
    deleg = eg.V2_DELEG_G if flags.get("G") else eg.V2_DELEG
    zone = closing_zone(ev)
    seen, denies, last_d = set(), [], -1
    for j, e in enumerate(ev):
        if e[0] != "tool":
            continue
        if e[2] in deleg:
            last_d = j
            continue
        if e[2] not in HOOKED:  # matcher хука в settings.local.json — лише ці; Read/Grep/Glob хук не бачить (рахуються)
            continue
        anchor = ev[last_d][1] if last_d >= 0 else "start"
        r = eg.v2_decide(ev[last_d + 1:j], e[2], e[3], anchor, flags=flags, agv=agv, n_lim=n_lim, k_lim=k_lim)
        if r and r[0] not in seen:
            seen.add(r[0]); denies.append((j, r[0].split("\t")[0], r[1], label(sid, ev, j, zone)))
    reps = reproaches(ev)
    caught = []
    for ri, r in enumerate(reps):
        prev_d = max([i for i in range(r) if ev[i][0] == "tool" and ev[i][2] in ANY_DELEG], default=-1)
        start = max(prev_d, reps[ri - 1] if ri else -1)
        caught.append(any(start < j < r for j, *_ in denies))
    work = sum(1 for e in ev if e[0] == "tool" and e[2] in eg.V2_WORK)
    if verbose:
        print(f"  ===== {sid}: викликів роботи {work}, усіх інструментів {sum(1 for e in ev if e[0] == 'tool')}, "
              f"deny {len(denies)}, докорів Р9-агенти {len(reps)}")
        for (j, kind, n, lab) in denies:
            inp = ev[j][3]
            print(f"    {ev[j][1][5:19]} {kind:<8} n={n:<3} {lab:<8} {ev[j][2]:<5} {str(inp.get('description', ''))[:75]}"
                  f" | {str(inp.get('command', inp.get('file_path', '')))[:60]!r}")
        for ri, r in enumerate(reps):
            prev = max([i for i in range(r) if ev[i][0] == "tool" and ev[i][2] in ANY_DELEG], default=-1)
            u = sum(1 for x in ev[prev + 1:r] if x[0] == "tool" and x[2] in eg.V2_WORK)
            print(f"    ДОКІР {ev[r][1][5:19]} «{ev[r][2][:45]}» — {'ВПІЙМАНО ДО' if caught[ri] else 'пропущено'}; "
                  f"кроків від останньої роздачі {u} (з {ev[prev][1][11:19] if prev >= 0 else 'початку'})")
    labs = [d[3].rstrip("*") for d in denies]
    return {"caught": sum(caught), "missed": len(caught) - sum(caught), "deny": len(denies), "work": work,
            "hit": labs.count("влучний"), "false": labs.count("хибний"), "half": labs.count("напів")}


def F(s):
    return {k: k in s for k in "ASBCGZ"}


VARIANTS = [  # (назва, прапорці, поріг N, K)
    ("v1 П1 (читання, хід)", F(""), 15, 2),
    ("(а) A: кроки, хід", F("A"), 12, 2),
    ("(а) A+S: кроки, сесія", F("AS"), 12, 2),
    ("(б) B: білий список", F("B"), 15, 2),
    ("(в) C: після звіту", F("C"), 15, 2),
    ("(г1) G: delegate теж роздача", F("G"), 15, 2),
    ("(г2) Z: закриття й коміт", F("Z"), 15, 2),
    ("A+S+B", F("ASB"), 12, 2),
    ("A+S+B+C", F("ASBC"), 12, 2),
    ("A+S+B+C+Z", F("ASBCZ"), 12, 2),
    ("A+S+B+C+Z+G", F("ASBCZG"), 12, 2),
]


def table(sessions, cache, variants):
    print(f"  {'варіант':<32} {'N':>3} {'K':>2} | упійм ДО | пропущ | deny | влуч | хиб | напів | кроків")
    for name, fl, n, k in variants:
        tot = {"caught": 0, "missed": 0, "deny": 0, "hit": 0, "false": 0, "half": 0, "work": 0}
        for sid in sessions:
            r = run(sid, fl, n, k, ev=cache[sid])
            for x in tot:
                tot[x] += r[x]
        print(f"  {name:<32} {n:>3} {k:>2} | {tot['caught']:>8} | {tot['missed']:>6} | {tot['deny']:>4} | "
              f"{tot['hit']:>4} | {tot['false']:>3} | {tot['half']:>5} | {tot['work']:>6}")


if __name__ == "__main__":
    cache = {s: events(s) for s in TRAIN + HOLD}
    if "--sweep" in sys.argv:
        print("ПІДБІР ПОРОГУ — лише навчальні сесії", TRAIN)
        vs = [(f"{nm} N={n} K={k}", F(fl), n, k) for nm, fl in (("A+S+B+C+Z", "ASBCZ"), ("A+S+B+Z", "ASBZ"),
              ("A+S+B+C", "ASBC")) for n in (6, 8, 10, 12, 15, 20) for k in (1, 2, 3)]
        table(TRAIN, cache, vs)
        sys.exit()
    best = os.environ.get("BEST", "ASBCZ:12:2").split(":")
    VARIANTS.append((f"ОБРАНЕ {best[0]}", F(best[0]), int(best[1]), int(best[2])))
    for title, ss in (("НАВЧАЛЬНІ", TRAIN), ("ВІДКЛАДЕНІ (поріг на них не підбирався)", HOLD)):
        print(f"\n######## {title}: {ss}")
        table(ss, cache, VARIANTS)
    for name, fl, n, k in [VARIANTS[0], VARIANTS[-1]]:
        print(f"\n######## ДЕТАЛІ: {name} (N={n}, K={k})")
        for sid in TRAIN + HOLD:
            run(sid, fl, n, k, ev=cache[sid], verbose=True)
