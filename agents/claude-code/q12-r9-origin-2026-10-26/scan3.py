import json,sys,re,glob,collections
RE_READ_BASH = re.compile(r"(?:^|[;&|(]\s*|\n\s*)(grep|rg|cat|sed\s+-n|head|tail|ls|find|wc|python3\s+-c)\b")
def is_read(n,i): return n in("Read","Grep","Glob") or (n=="Bash" and bool(RE_READ_BASH.search(str((i or {}).get("command","")))))
P="/data/data/com.termux/files/home/.claude/projects/-data-data-com-termux-files-home-AgentReachProject/"
for sid in sys.argv[1:]:
    rows=[json.loads(l) for l in open(glob.glob(P+sid+"*.jsonl")[0])]
    print("=====",sid)
    turns=[]; cur=None; askid={}
    for d in rows:
        if d.get("isSidechain"): continue
        t=d.get("type"); ts=d.get("timestamp","")[11:19]
        m=d.get("message") if isinstance(d.get("message"),dict) else {}
        c=m.get("content")
        if t=="user" and not d.get("isMeta"):
            txt=None
            if isinstance(c,str): txt=c
            elif isinstance(c,list) and not any(isinstance(x,dict) and x.get("type")=="tool_result" for x in c):
                txt=" ".join(x.get("text","") for x in c if isinstance(x,dict))
            if txt is not None and not txt.startswith("<task-notification"):
                cur={"ts":ts,"msg":txt[:40],"ev":[]}; turns.append(cur); continue
        if not cur or not isinstance(c,list): continue
        for x in c:
            if not isinstance(x,dict): continue
            if x.get("type")=="tool_use":
                inp=x.get("input") or {}
                if x["name"]=="AskUserQuestion": askid[x["id"]]=ts
                cur["ev"].append((ts,x["name"],inp))
            if x.get("type")=="tool_result" and x.get("tool_use_id") in askid:
                s=json.dumps(x.get("content"),ensure_ascii=False)
                if re.search(r"агент",s,re.I): print("  ASK-ANSWER",ts,s[:300])
    for tu in turns:
        ev=tu["ev"]; reads=0; byp=0; agent_at=None; nonread=collections.Counter(); deny_pos=[]
        for k,(ts,n,i) in enumerate(ev):
            if n in("Agent","Task"):
                agent_at = agent_at or (ts,reads); continue
            if is_read(n,i):
                reads+=1
                if "без агента" in str(i.get("description","")): byp+=1
            else:
                nonread[n]+=1
                if n=="Bash" and "без агента" in str(i.get("description","")): nonread["Bash(non-read, з «без агента»)"]+=1
        print(f"TURN {tu['ts']} {tu['msg']!r}: tools={len(ev)} reads={reads} reads_with_bypass={byp} first_Agent={agent_at} nonread={dict(nonread)}")
