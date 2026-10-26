import json,sys,re,glob,collections
RE_READ_BASH = re.compile(r"(?:^|[;&|(]\s*|\n\s*)(grep|rg|cat|sed\s+-n|head|tail|ls|find|wc|python3\s+-c)\b")
def is_read(n,i): return n in("Read","Grep","Glob") or (n=="Bash" and bool(RE_READ_BASH.search(str((i or {}).get("command","")))))
P="/data/data/com.termux/files/home/.claude/projects/-data-data-com-termux-files-home-AgentReachProject/"
def real_user(d):
    m=d.get("message"); return d.get("type")=="user" and not d.get("isMeta") and isinstance(m,dict) and isinstance(m.get("content"),str)
def notif(d):
    o=d.get("origin"); return isinstance(o,dict) and bool(o.get("kind")) and o.get("kind")!="human"
for sid in sys.argv[1:]:
    rows=[json.loads(l) for l in open(glob.glob(P+sid+"*.jsonl")[0])]
    turns=[]; cur=None
    for d in rows:
        if d.get("isSidechain"): continue
        if real_user(d) and not notif(d):
            cur={"ts":d["timestamp"][11:19],"ev":[]}; turns.append(cur); continue
        if cur is None: continue
        a=d.get("attachment")
        if isinstance(a,dict) and a.get("type")=="queued_command" and not str(a.get("prompt","")).startswith("<task"):
            cur["ev"].append((d["timestamp"][11:19],"QUEUED",{"t":a["prompt"][:50]}))
        c=(d.get("message") or {}).get("content") if isinstance(d.get("message"),dict) else None
        if isinstance(c,list):
            for x in c:
                if isinstance(x,dict) and x.get("type")=="tool_use": cur["ev"].append((d["timestamp"][11:19],x["name"],x.get("input") or {}))
    print("=====",sid,"ходів (edit-gate, сповіщення злиті):",len(turns))
    for t in turns:
        ev=t["ev"]; n=0; agent=False; last_ag=None; byp=0; blind=0; buckets_noByp=set(); since=0; f1=set(); nonread=collections.Counter()
        for ts,name,inp in ev:
            if name=="QUEUED": print(f"   QUEUED {ts} n={n} agent_in_turn={agent} reads_since_last_Agent={since} «{inp['t']}»"); continue
            if name in("Agent","Task"): agent=True; since=0; continue
            if not is_read(name,inp):
                if name=="Bash":
                    cmd=inp.get("command","").strip(); w=re.split(r"\s",cmd)[0]
                    nonread["Bash:"+("tmux" if "tmux" in cmd else "git" if cmd.startswith("git") or "git " in cmd[:60] else w[:15])]+=1
                else: nonread[name]+=1
                continue
            n+=1; since+=1
            b="без агента" in str(inp.get("description",""))
            byp+=b
            if agent: blind+=1
            if not agent and n>=15 and name!="Read": buckets_noByp.add(n//15)
            if since>=15 and name!="Read": f1.add((last_ag, since//15))
        print(f" TURN {t['ts']}: читань={n}, з «без агента»={byp}, після 1-го Agent (ворота сліпі)={blind}, deny якби причину не приймали={len(buckets_noByp)}, deny якби лічити від останнього Agent={len(f1)}")
        print("   не-читання:",dict(nonread.most_common()))
