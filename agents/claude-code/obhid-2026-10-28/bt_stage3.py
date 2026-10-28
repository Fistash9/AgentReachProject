import sys, re, json, collections
sys.path.insert(0, "/data/data/com.termux/files/home/AgentReachProject/agents/claude-code/obhid-2026-10-28")
from bt_common import *
EV = json.load(open(TMP + "ev.json")); rows, u = load_calls()
seqs = collections.defaultdict(list)
for r in rows:
    seqs[(r["sid"], r.get("agent"))].append(r)
BYID = {r["id"]: r for r in u}
CONF = {"shlib-wrapper": r"grep і find не працюють|unset -f", "shlib-binary": r"grun|freebuff", "bad interpreter": r"MCP-probe результати|pkgtruth MCP",
        "/usr/bin/env": r"MCP-probe результати|pkgtruth MCP"}
def confirmed(e):
    for h, n, sn in e["struct"]:
        k = e["key"]
        if k in CONF and re.search(CONF[k], h, re.I): return h
    return None
K = []
for e in EV:
    if not e["env"]: continue
    h = confirmed(e)
    if e["key"] == "nf:skills": h = "MCP-probe результати / pkgtruth (shebang) — ключ за текстом помилки НЕ знаходить"   # ручна позначка: корінь той самий
    if h: e["recipe"] = h; K.append(e)
print("K (рецепт існував на момент і стосується цієї помилки):", len(K), "| з них HARD:", sum(1 for e in K if e["hard"]), "SOFT:", sum(1 for e in K if not e["hard"]))
print("env-подій:", sum(1 for e in EV if e["env"]), "| env HARD:", sum(1 for e in EV if e["env"] and e["hard"]), "SOFT:", sum(1 for e in EV if e["env"] and not e["hard"]))
print("за ключем:", dict(collections.Counter(e["key"] for e in K)))
def heads(pre):
    return [m[0][:40] for m in re.findall(r"- ([^\\]*?) \(тег: ([^)]*)\)", pre)][:3]
def after(e, n=4):
    r = BYID[e["id"]]; sq = seqs[(r["sid"], r.get("agent"))]
    j = [k for k, x in enumerate(sq) if x["id"] == r["id"]][0]
    out = []
    for x in sq[j + 1: j + 1 + n]:
        out.append(f'{x["name"][:4]}{"!" if x.get("is_error") else ""}:{x["brief"][:62]}'.replace("\n", " "))
    return out, sq[j + 1: j + 9]
TR = re.compile(r"TROUBLES")
res = collections.Counter(); 
for e in K:
    a4, a8 = after(e)
    look = any(TR.search(x["brief"]) for x in a8)
    e["looked"] = look
    print(f"\n{e['ts'][5:16]} {e['who'][:6]} {e['key']:14s} {'HARD' if e['hard'] else 'soft'} | pre-хук показав: {heads(e['pre']) or '—'} | глянув TROUBLES у наступних 8 кроках: {look}")
    for x in a4: print("     →", x[:96])
print("\nЗ K: після помилки відкрив/grep TROUBLES у наступних 8 викликах:", sum(1 for e in K if e["looked"]), "з", len(K))
json.dump(K, open(TMP + "K.json", "w"), ensure_ascii=False)
