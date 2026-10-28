import sys; sys.path.insert(0, "/data/data/com.termux/files/home/AgentReachProject/agents/claude-code/obhid-2026-10-28")
from bt_common import *
rows, u = load_calls()
bash = [r for r in u if r["name"] == "Bash" and "is_error" in r]
print("== ПЕРЕПИС (унікальні tool_use_id) ==")
print("усього викликів інструментів:", len(rows), "| унікальних:", len(u), "| Bash з результатом:", len(bash),
      "| з них під-агентів:", sum(1 for r in bash if r.get("agent")))
err = [r for r in bash if r["is_error"]]
K = collections.Counter(kind(r) for r in err)
print("is_error:", len(err), dict(K))
real = [r for r in err if kind(r) == "REAL"]
hard, nosig = [], []
for r in real:
    c, s = signature(r)
    (hard if c else nosig).append((r, c, s))
soft = []
for r in bash:
    if r["is_error"]: continue
    c, s = signature(r)
    if c: soft.append((r, c, s))
print(f"REAL без сигнатури збою (ненульовий код при валідному виводі): {len(nosig)} | REAL зі сигнатурою (HARD): {len(hard)} | м'які (код 0, сигнатура в тексті, SOFT): {len(soft)}")
allf = hard + soft
print("N_збоїв (HARD+SOFT) =", len(allf), "| унікальних сесій/агентів:", len({(r.get('agent') or r['sid']) for r, _, _ in allf}))
print("\n== за класом (hard / soft) ==")
ch = collections.Counter(c for _, c, _ in hard); cs = collections.Counter(c for _, c, _ in soft)
for c in sorted(set(ch) | set(cs), key=lambda x: -(ch[x] + cs[x])): print(f"{c:11s} hard={ch[c]:3d} soft={cs[c]:3d}")
print("\n== перша/остання дата класу ==")
by = collections.defaultdict(list)
for r, c, s in allf: by[c].append(r["ts"][:10])
for c, ds in sorted(by.items()): print(f"{c:11s} {min(ds)} … {max(ds)}  n={len(ds)}")
json.dump([{"id": r["id"], "sid": r["sid"], "agent": r.get("agent"), "ts": r["ts"], "cls": c, "sig": s, "hard": bool(r["is_error"]), "cmd": r["brief"][:300]} for r, c, s in allf],
          open(TMP + "fails.json", "w"), ensure_ascii=False)
print("\n== SOFT: усі (для перевірки хибних спрацювань вручну) ==")
for r, c, s in soft:
    print(f"{r['ts'][:16]} {(r.get('agent') or r['sid'])[:8]} {c:9s} | {r['brief'][:80].replace(chr(10),' ')} || {s[:90]}")
print("\n== REAL без сигнатури: 8 випадкових (перевірка, що це не пропущені збої) ==")
import random; random.seed(7)
for r, c, s in random.sample(nosig, 8):
    bl = body_lines(r)
    print(f"{r['ts'][:16]} ex={exitcode(r)} | {r['brief'][:70].replace(chr(10),' ')} || {(bl[-1] if bl else '')[:80]}")
