import sys, bisect, subprocess, datetime, re, collections, json
sys.path.insert(0, "/data/data/com.termux/files/home/AgentReachProject/agents/claude-code/obhid-2026-10-28")
from bt_common import *
PROJ = "/data/data/com.termux/files/home/AgentReachProject"
GENERIC = {"pip","npm","node","exit","mcp","hook","agents","path","env","timeout","verification","unverified","backlog","termux","install","config","git","python"}
F = json.load(open(TMP + "fails.json")); rows, u = load_calls(); BY = {r["id"]: r for r in u}
H = {}
for l in open(TMP + "hints2.jsonl", encoding="utf-8"):
    a = json.loads(l)["a"]
    if "TROUBLES.md має релевантні записи" in a.get("content", "") and a.get("toolUseID"): H[a["toolUseID"]] = a["content"]
out = subprocess.check_output(["git", "-C", PROJ, "log", "--format=%H %ct", "--", "TROUBLES.md"], text=True).split("\n")
commits = sorted((int(l.split()[1]), l.split()[0]) for l in out if l.strip()); cts = [c[0] for c in commits]
SNAP = {}
def parse(text):
    secs, cur = [], None
    for n, line in enumerate(text.splitlines(), 1):
        if line.startswith("## "):
            cur = {"h": line[3:].strip(), "n": n, "tags": [], "body": []}; secs.append(cur); continue
        if cur is None: continue
        if line.startswith("TAGS:"):
            cur["tags"] += [t.strip().lower() for t in line[5:].split(",") if t.strip()]
        cur["body"].append(line)
    for s in secs: s["text"] = (s["h"] + "\n" + "\n".join(s["body"])).lower()
    return secs
def troubles_at(epoch):
    i = bisect.bisect_right(cts, epoch) - 1
    k = "WT" if (i == len(commits) - 1 and epoch > cts[-1]) else (commits[i][1] if i >= 0 else "none")
    if k not in SNAP:
        if k == "WT": txt = open(PROJ + "/TROUBLES.md", encoding="utf-8").read()
        elif k == "none": txt = ""
        else: txt = subprocess.check_output(["git", "-C", PROJ, "show", k + ":TROUBLES.md"], text=True, errors="replace")
        SNAP[k] = parse(txt)
    return k, SNAP[k]
def epoch(ts): return datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
def words_naive(s): return set(re.findall(r"[a-zA-Zа-яіїєА-ЯІЇЄ0-9_-]{3,}", s.lower()))
STOP = {"line","such","file","files","directory","error","found","command","denied","permission","cannot","access","open","object","shared","bash","traceback","most","recent","call","last","module","name","the","and","for","usr","bin","not"}
def words_clean(s):
    s = re.sub(r"[~$]?[\w.@+-]*/[\w./@+-]+", " ", s); s = re.sub(r"\b[0-9a-f]{7,}\b|\d+", " ", s)
    return {w for w in words_naive(s) if w not in STOP}
def key_of(cls, sig):
    if cls == "SHLIB": return "shlib-wrapper" if re.match(r"^-\w: ", sig) else "shlib-binary"
    if cls == "BADINTERP": return "bad interpreter"
    if cls == "ENV_NOFILE": return "/usr/bin/env"
    if cls == "NOTFOUND":
        m = re.search(r"(\S+): (?:command )?not found", sig); return "nf:" + (m.group(1) if m else "?")
    if cls == "PERM":
        return "perm:/tmp" if "/tmp/" in sig else "perm:/proc" if "/proc/" in sig else "perm:hardlink" if "hard link" in sig else "perm:other"
    if cls == "SHSYNTAX": return "unexpected EOF"
    return None
RECIPE_STR = {"shlib-wrapper": ["error while loading shared", "unset -f"], "shlib-binary": ["error while loading shared", "grun"],
              "bad interpreter": ["bad interpreter", "shebang"], "/usr/bin/env": ["/usr/bin/env"],
              "perm:/tmp": ["/tmp"], "perm:/proc": ["/proc/"], "perm:hardlink": ["hard link", "hardlink", "link2symlink"],
              "unexpected EOF": ["unexpected eof"]}
def struct_hits(key, secs):
    if key is None: return []
    pats = RECIPE_STR.get(key) or ([r"\b" + re.escape(key[3:]) + r"\b"] if key.startswith("nf:") else [])
    hits = []
    for s in secs:
        for p in pats:
            m = re.search(p, s["text"]) if p.startswith(r"\b") else (re.search(re.escape(p), s["text"]))
            if m:
                a = max(0, m.start() - 40); hits.append((s["h"][:62], s["n"], s["text"][a:m.end() + 50].replace("\n", " "))); break
    return hits
def tag_hits(words, secs):
    hs = []
    for s in secs:
        tg = [t for t in s["tags"] if t not in GENERIC]
        if any(t in words for t in tg): hs.append(s["h"][:62])
    return list(dict.fromkeys(hs))
ENV = {"SHLIB","BADINTERP","ENV_NOFILE","NOTFOUND","PERM","SHSYNTAX","NPM","PKG","NET","USAGE","TIMEOUT"}
EV = []
for f in sorted(F, key=lambda x: x["ts"]):
    r = BY[f["id"]]; ep = epoch(f["ts"]); k, secs = troubles_at(ep)
    errtxt = f["sig"]
    if f["cls"] == "TRACEBACK":
        ex = [l for l in text_of(r).splitlines() if re.match(r"^\w*(Error|Exception)\b", l)]
        errtxt += " " + (ex[-1] if ex else "")
    key = key_of(f["cls"], f["sig"])
    e = dict(f); e.update(ep=ep, snap=k, key=key, env=f["cls"] in ENV, naive=tag_hits(words_naive(errtxt), secs), clean=tag_hits(words_clean(errtxt), secs),
                        struct=struct_hits(key, secs), pre=H.get(f["id"], ""), who=(f["agent"] or f["sid"])[:8])
    EV.append(e)
json.dump(EV, open(TMP + "ev.json", "w"), ensure_ascii=False)
tot = len(EV); env = [e for e in EV if e["env"]]; own = [e for e in EV if not e["env"]]
print(f"N={tot} | env-type={len(env)} | own-type={len(own)}")
for nm, grp in (("УСІ", EV), ("env", env), ("own", own)):
    print(f"[{nm}] n={len(grp)} | naive(теги∩слова помилки, як у чинному хуку): ≥1 підказка у {sum(1 for e in grp if e['naive'])} | clean(без шляхів/чисел/сміттєвих слів): ≥1 у {sum(1 for e in grp if e['clean'])} | struct(ключ сигнатури): ≥1 у {sum(1 for e in grp if e['struct'])} | PreToolUse-підказка вже була: {sum(1 for e in grp if e['pre'])}")

byk = collections.defaultdict(list)
for e in env: byk[e["key"] or "-"].append(e)
print("\n== ключі env-подій (n подій / з кандидатом-рецептом НА ТОЙ МОМЕНТ) ==")
for k, es in sorted(byk.items(), key=lambda x: -len(x[1])):
    m = [e for e in es if e["struct"]]
    print(f"{k:16s} n={len(es):2d} {es[0]['ts'][:10]}…{es[-1]['ts'][:10]} | кандидат на момент: {len(m)} | вперше: {min((e['ts'][:16] for e in m), default='-')}")
print("\n== кандидати-рецепти (усі різні заголовки по ключах n>=2) ==")
for k, es in sorted(byk.items(), key=lambda x: -len(x[1])):
    if len(es) < 2 or k == "-": continue
    hs = collections.OrderedDict()
    for e in es:
        for h, n, sn in e["struct"]: hs.setdefault(h, (n, sn))
    for h, (n, sn) in list(hs.items())[:6]: print(f"  {k:14s}| {h} (:{n}) «…{sn[:80]}…»")
# TRACEBACK exception types
ex = collections.Counter()
for e in own:
    if e["cls"] == "TRACEBACK":
        r = BY[e["id"]]; l = [x for x in text_of(r).splitlines() if re.match(r"^\w*(Error|Exception)\b", x)]
        ex[(l[-1].split(":")[0] if l else "?")] += 1
print("\nTRACEBACK: типи винятків:", ex.most_common(8))
# streaks: той самий клас, той самий агент/сесія, проміжок ≤60 хв між сусідніми
EVs = sorted(EV, key=lambda e: (e["who"], e["cls"], e["ep"]))
pos = {}
prev = {}
for e in EVs:
    kk = (e["who"], e["cls"]); p = prev.get(kk)
    pos[e["id"]] = (pos[p["id"]] + 1) if (p and e["ep"] - p["ep"] <= 3600) else 1
    prev[kk] = e
for nm, grp in (("env", env), ("own", own)):
    c = collections.Counter(min(pos[e["id"]], 3) for e in grp)
    print(f"[{nm}] позиція у серії того ж класу (≤60 хв): 1-ша={c[1]} 2-га={c[2]} 3-тя і далі={c[3]}")
print("серії env (довжина ≥3):", sorted(((e['who'], e['cls'], pos[e['id']], e['ts'][:16]) for e in env if pos[e['id']] >= 3))[:12])
print("\n== env-події, де PreToolUse-хук УЖЕ показав підказки (перші 2 заголовки) ==")
for e in env:
    if e["pre"]:
        hs = [l[2:].rsplit(" (тег:", 1)[0][:44] for l in e["pre"].splitlines()[1:] if l.startswith("- ")][:2]
        print(f"{e['ts'][5:16]} {e['who'][:6]} {e['key'] or '-':14s}| " + " ¦ ".join(hs))
