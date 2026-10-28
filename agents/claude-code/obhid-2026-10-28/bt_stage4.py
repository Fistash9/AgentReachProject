import sys, re, json, collections, subprocess, time, statistics, os
HERE = "/data/data/com.termux/files/home/AgentReachProject/agents/claude-code/obhid-2026-10-28"; sys.path.insert(0, HERE)
from bt_common import *; from bt_snap import *; import proto_failure_moment as P
EV = json.load(open(TMP + "ev.json")); K = json.load(open(TMP + "K.json")); rows, u = load_calls(); BY = {r["id"]: r for r in u}
CONF = {"shlib-wrapper": r"grep і find не працюють|unset -f", "shlib-binary": r"grun|freebuff", "bad interpreter": r"MCP-probe результати|pkgtruth MCP",
        "/usr/bin/env": r"MCP-probe результати|pkgtruth MCP", "nf:skills": r"MCP-probe результати|pkgtruth MCP"}
BIRTH = {"shlib-wrapper": r"^grep і find не працюють", "shlib-binary": r"^Freebuff у Termux працює через офіційну збірку", "bad interpreter": r"^MCP-probe результати",
         "/usr/bin/env": r"^MCP-probe результати", "nf:skills": r"^MCP-probe результати"}
birth = {k: first_commit_with(v) for k, v in BIRTH.items()}
print("народження рецептів (коміт):", {k: (datetime.datetime.fromtimestamp(v, datetime.timezone.utc).strftime("%m-%d %H:%MZ") if v else None) for k, v in birth.items()})
sstart = {}
for r in u: sstart[r["sid"]] = min(sstart.get(r["sid"], "9"), r["ts"])
cross = [e for e in K if epoch(sstart[e["sid"]]) > birth[e["key"]]]
print(f"K={len(K)}: сесія почалась ПІСЛЯ появи рецепта (довелось дістати з файлів): {len(cross)}; рецепт з'явився за час сесії (він у контексті): {len(K)-len(cross)}")
print("cross-session K за ключем:", dict(collections.Counter(e["key"] for e in cross)), "| HARD:", sum(1 for e in cross if e["hard"]), "SOFT:", sum(1 for e in cross if not e["hard"]))
def found(e, field):
    hs = e[field] if isinstance(e[field], list) else []
    return any(re.search(CONF[e["key"]], h, re.I) for h in hs)
print("знайшов би правильний рецепт: naive(теги∩слова помилки) %d/%d | clean %d/%d | PreToolUse чинного хука (за командою) %d/%d" % (
    sum(found(e, "naive") for e in K), len(K), sum(found(e, "clean") for e in K), len(K),
    sum(any(re.search(CONF[e["key"]], m[0], re.I) for m in re.findall(r"- ([^\\]*?) \(тег: ([^)]*)\)", e["pre"])) for e in K), len(K)))
# хибні підказки (naive/clean) на всіх 232: ≥1 підказка, а правильного рецепта серед них нема
Kids = {e["id"] for e in K}
for fld in ("naive", "clean"):
    A = [e for e in EV if e[fld]]; T = [e for e in A if e["id"] in Kids and found(next(k for k in K if k["id"] == e["id"]), fld)]
    print(f"{fld}: подій з ≥1 підказкою {len(A)} з {len(EV)}; серед них з правильним рецептом {len(T)}; ХИБНИХ (підказка без правильного рецепта) {len(A)-len(T)} = {100*(len(A)-len(T))/len(EV):.0f}% усіх збоїв")
# повтор прототипу на всіх збоях
fires = recipe = nr = 0; lens = []; miss = []
for e in EV:
    r = BY[e["id"]]; k, secs = troubles_at(e["ep"])
    cls, msg, line = P.decide(r["brief"] if len(r["brief"]) < 700 else r["brief"], text_of(r), bool(r["is_error"]), secs)
    if cls:
        fires += 1
        if msg: recipe += 1; lens.append(len(msg))
        elif e["id"] in Kids: miss.append((e["ts"][:16], e["key"]))
print(f"прототип на {len(EV)} збоях: спрацьовує (клас середовища) {fires}; з рецептом {recipe}; довжина підказки: мін {min(lens)} / сер {statistics.mean(lens):.0f} / макс {max(lens)} симв.; K без рецепта від прототипу: {miss}")
print(f"частка Bash-викликів, де прототип заговорить: {fires}/{sum(1 for r in u if r['name']=='Bash' and 'is_error' in r)} = {1000*fires/sum(1 for r in u if r['name']=='Bash' and 'is_error' in r):.1f} на 1000; з рецептом {recipe} = {1000*recipe/sum(1 for r in u if r['name']=='Bash' and 'is_error' in r):.1f} на 1000")
for e in K:
    if e["key"] in ("nf:skills", "bad interpreter") or e["ts"].startswith("2026-09-26"):
        r = BY[e["id"]]; k, secs = troubles_at(e["ep"]); cls, msg, line = P.decide(r["brief"], text_of(r), bool(r["is_error"]), secs)
        print("  приклад", e["ts"][:16], e["key"], "→", msg)
print("\n== env SOFT-події після якорів (ручна перевірка на хибні спрацювання) ==")
for e in EV:
    if e["env"] and not e["hard"]: print(f"{e['ts'][5:16]} {e['who'][:6]} {e['key'] or '-':13s}| {e['cmd'][:58].replace(chr(10),' ')} || {e['sig'][:70]}")
# латентність
def run(payload, n=15):
    ts = []
    for _ in range(n):
        t = time.time(); subprocess.run([sys.executable, "-I", HERE + "/proto_failure_moment.py"], input=json.dumps(payload), text=True, capture_output=True); ts.append((time.time() - t) * 1000)
    return statistics.median(ts), max(ts)
silent = {"hook_event_name": "PostToolUse", "tool_name": "Bash", "tool_input": {"command": "ls"}, "tool_response": {"stdout": "a\nb", "stderr": ""}, "session_id": "lat-silent"}
rec = {"hook_event_name": "PostToolUse", "tool_name": "Bash", "tool_input": {"command": "npx --yes skills@1.7.4 add vercel-labs/skills@find-skills -g -y 2>&1 | tail -60; echo EXIT=${PIPESTATUS[0]}"}, "tool_response": {"stdout": "sh: 1: skills: not found\nEXIT=127", "stderr": ""}, "session_id": "lat-rec"}
print("\nлатентність (мс, медіана/макс із 15; повний інтерпретатор з -I):  тиша:", [round(x) for x in run(silent)], "| рецепт (читає TROUBLES.md 7 тис. рядків):", [round(x) for x in run(rec)])
out = subprocess.run([sys.executable, "-I", HERE + "/proto_failure_moment.py"], input=json.dumps(dict(rec, session_id="lat-rec2")), text=True, capture_output=True).stdout
print("вивід прототипу (E3):", out.strip()[:420])
