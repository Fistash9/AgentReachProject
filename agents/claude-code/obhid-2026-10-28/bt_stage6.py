import sys, re, json, collections, statistics
HERE = "/data/data/com.termux/files/home/AgentReachProject/agents/claude-code/obhid-2026-10-28"; sys.path.insert(0, HERE)
from bt_common import *; from bt_snap import *; import proto_failure_moment as P
EV = json.load(open(TMP + "ev.json")); K = json.load(open(TMP + "K.json")); rows, u = load_calls(); BY = {r["id"]: r for r in u}
Hc = {}
for l in open(TMP + "hints2.jsonl", encoding="utf-8"):
    a = json.loads(l)["a"]
    if "TROUBLES.md має релевантні записи" in a.get("content", "") and a.get("toolUseID"): Hc[a["toolUseID"]] = len(a["content"])
bash = [r for r in u if r["name"] == "Bash" and "is_error" in r]; sub = [r for r in bash if r.get("agent")]; main = [r for r in bash if not r.get("agent")]
print(f"troubles-grep: унікальних вкидань {len(Hc)} на {len(bash)} Bash-викликів = {1000*len(Hc)/len(bash):.0f} на 1000; довжина (обрізано на 900): сер {statistics.mean(Hc.values()):.0f}, медіана {statistics.median(Hc.values()):.0f}")
print(f"хуки діють і в під-агентів: main Bash з вкиданням {sum(1 for r in main if r['id'] in Hc)}/{len(main)}; sub-agent Bash {sum(1 for r in sub if r['id'] in Hc)}/{len(sub)}")
nsess = len({r["sid"] for r in bash}); print(f"сесій з Bash: {nsess}; Bash на сесію (сер): {len(bash)/nsess:.0f}; cross-session K на сесію: 11/{nsess} = 1 на {nsess/11:.1f} сесій")
EVs = sorted(EV, key=lambda e: (e["who"], e["cls"], e["ep"])); pos = {}; prev = {}
for e in EVs:
    kk = (e["who"], e["cls"]); p = prev.get(kk); pos[e["id"]] = (pos[p["id"]] + 1) if (p and e["ep"] - p["ep"] <= 3600) else 1; prev[kk] = e
Kids = {e["id"] for e in K}; printed = []; 
for e in EV:
    r = BY[e["id"]]; k, secs = troubles_at(e["ep"]); cls, msg, line = P.decide(r["brief"], text_of(r), bool(r["is_error"]), secs)
    if not cls: continue
    if msg or pos[e["id"]] >= 2: printed.append((e["sid"], bool(msg), pos[e["id"]] >= 2))
bys = collections.Counter(s for s, _, _ in printed)
print(f"вкидань об'єднаного хука (рецепт АБО 2-й+ збій класу середовища): {len(printed)} = {1000*len(printed)/len(bash):.1f} на 1000 Bash; з них рецепт {sum(1 for _, a, _ in printed if a)}, лише Т2-стоп {sum(1 for _, a, b in printed if b and not a)}; макс за сесію {max(bys.values())}; сесій з >2: {sum(1 for v in bys.values() if v > 2)}")
own2 = sum(1 for e in EV if not e["env"] and pos[e["id"]] >= 2)
print(f"для порівняння — Т2-стоп на own-типі (NOFILE/TRACEBACK) 2-й+ збій: {own2} подій (у пілот Bash-гілки НЕ входять)")
src = open("/data/data/com.termux/files/home/AgentReachProject/.claude/hooks/install-check-hook.py", encoding="utf-8").read()
print("install-check-hook.py: згадок npx:", src.count("npx"), "| рядків:", src.count("\n"))
