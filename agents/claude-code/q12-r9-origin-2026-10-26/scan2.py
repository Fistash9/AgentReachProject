import json,sys,re,glob,collections
P="/data/data/com.termux/files/home/.claude/projects/-data-data-com-termux-files-home-AgentReachProject/"
for sid in sys.argv[1:]:
    rows=[json.loads(l) for l in open(glob.glob(P+sid+"*.jsonl")[0])]
    print("=====",sid)
    for d in rows:
        if d.get("isSidechain"): continue
        t=d.get("type"); ts=d.get("timestamp","")[:19]
        m=d.get("message") if isinstance(d.get("message"),dict) else {}
        c=m.get("content")
        if t=="user" and not d.get("isMeta"):
            if isinstance(c,str): txt=c
            elif isinstance(c,list) and not any(isinstance(x,dict) and x.get("type")=="tool_result" for x in c):
                txt=" ".join(x.get("text","") for x in c if isinstance(x,dict))
            else: continue
            print("U",ts,repr(txt[:170]))
        elif t not in("user","assistant"):
            raw=json.dumps(d,ensure_ascii=False)
            if "агент" in raw.lower() and ("Stop" in raw or "hook" in raw.lower()):
                print("S",ts,t,d.get("subtype"),raw[:260])
