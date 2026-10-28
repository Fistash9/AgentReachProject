import sys, random; sys.path.insert(0, "/data/data/com.termux/files/home/AgentReachProject/agents/claude-code/obhid-2026-10-28")
from bt_common import *
F = json.load(open(TMP + "fails.json"))
print("fails:", len(F))
env = {"SHLIB","BADINTERP","ENV_NOFILE","NOTFOUND","PERM","SHSYNTAX","NPM","PKG","NET","USAGE","TIMEOUT"}
print("class env-type:", sum(1 for f in F if f["cls"] in env), "| own-type (NOFILE+TRACEBACK):", sum(1 for f in F if f["cls"] not in env))
print("\n== SOFT, env-type (усі) ==")
for f in sorted(F, key=lambda x: x["ts"]):
    if not f["hard"] and f["cls"] in env:
        print(f"{f['ts'][:16]} {(f['agent'] or f['sid'])[:6]} {f['cls']:9s}| {f['cmd'][:75].replace(chr(10),' ')} || {f['sig'][:85]}")
random.seed(3)
for cls in ("NOFILE","TRACEBACK"):
    s=[f for f in F if not f["hard"] and f["cls"]==cls]
    print(f"\n== SOFT {cls}: вибірка 7 із {len(s)} ==")
    for f in random.sample(s, 7):
        print(f"{f['ts'][:16]} | {f['cmd'][:70].replace(chr(10),' ')} || {f['sig'][:85]}")
print("\n== HARD, env-type (усі) ==")
for f in sorted(F, key=lambda x: x["ts"]):
    if f["hard"] and f["cls"] in env:
        print(f"{f['ts'][:16]} {(f['agent'] or f['sid'])[:6]} {f['cls']:9s}| {f['cmd'][:70].replace(chr(10),' ')} || {f['sig'][:80]}")
# join with PreToolUse troubles-grep hints
H = {}
for l in open(TMP + "hints2.jsonl", encoding="utf-8"):
    d = json.loads(l); a = d["a"]
    if "TROUBLES.md має релевантні записи" in a.get("content", "") and a.get("toolUseID"):
        H[a["toolUseID"]] = a["content"]
print("\nPreToolUse troubles-grep hints in logs:", len(H))
hinted = [f for f in F if f["id"] in H]
print("fail events that had a troubles-grep hint at call time:", len(hinted), "of", len(F))
bash = [r for r in load_calls()[1] if r["name"] == "Bash" and "is_error" in r]
print("all Bash calls with a hint:", sum(1 for r in bash if r["id"] in H), "of", len(bash))
