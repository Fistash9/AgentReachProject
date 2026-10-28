import sys, re, json, collections
HERE = "/data/data/com.termux/files/home/AgentReachProject/agents/claude-code/obhid-2026-10-28"; sys.path.insert(0, HERE)
from bt_common import *; from bt_snap import *; import proto_failure_moment as P
EV = json.load(open(TMP + "ev.json")); K = json.load(open(TMP + "K.json")); rows, u = load_calls(); BY = {r["id"]: r for r in u}
seqs = collections.defaultdict(list)
for r in rows: seqs[(r["sid"], r.get("agent"))].append(r)
print("== (1) позиція K-подій у серії того ж класу (≤60 хв) — коли спрацював би і Т2 ==")
EVs = sorted(EV, key=lambda e: (e["who"], e["cls"], e["ep"])); pos = {}; prev = {}
for e in EVs:
    kk = (e["who"], e["cls"]); p = prev.get(kk); pos[e["id"]] = (pos[p["id"]] + 1) if (p and e["ep"] - p["ep"] <= 3600) else 1; prev[kk] = e
c = collections.Counter(min(pos[e["id"]], 3) for e in K)
print(f"K: 1-ша={c[1]} 2-га={c[2]} 3-тя+={c[3]}; усі збої: pos>=2: {sum(1 for e in EV if pos[e['id']]>=2)} з {len(EV)}; pos>=3: {sum(1 for e in EV if pos[e['id']]>=3)}")
print("\n== (2) прецедент для варіанту «лише скіл»: Skill у наступних 8 викликах після env-збою ==")
env = [e for e in EV if e["env"]]; n = 0
for e in env:
    r = BY[e["id"]]; sq = seqs[(r["sid"], r.get("agent"))]; j = [k for k, x in enumerate(sq) if x["id"] == r["id"]][0]
    if any(x["name"] == "Skill" for x in sq[j + 1: j + 9]): n += 1
print(f"env-збоїв {len(env)}; з викликом Skill у наступних 8 кроках: {n}")
print("\n== (3) вкидання прототипу за сесію (M11.2: ≤2 за сесію) ==")
fires = collections.defaultdict(list); rec = collections.defaultdict(list)
for e in EV:
    r = BY[e["id"]]; k, secs = troubles_at(e["ep"]); cls, msg, line = P.decide(r["brief"], text_of(r), bool(r["is_error"]), secs)
    if cls:
        fires[e["sid"]].append(e["key"])
        if msg: rec[e["sid"]].append(e["key"])
nsess = len({r["sid"] for r in u if r["name"] == "Bash"})
print(f"сесій з Bash: {nsess}; сесій зі спрацюванням: {len(fires)}; макс за сесію: {max(len(v) for v in fires.values())}; сесій з >2: {sum(1 for v in fires.values() if len(v) > 2)}")
dd = {s: len(set(v)) for s, v in rec.items()}
print(f"вкидання З РЕЦЕПТОМ: сесій {len(rec)}; усього {sum(len(v) for v in rec.values())}; після дедупа (сесія, ключ) {sum(dd.values())}; макс за сесію {max(dd.values())}")
print("\n== (4) що лишилось без рецепта: env-ключі, події (з виводу stage2) ==")
cnt = collections.Counter(e["key"] for e in env if e["id"] not in {k["id"] for k in K})
print(dict(cnt.most_common()))
print("env без рецепта:", sum(cnt.values()), "з", len(env))
