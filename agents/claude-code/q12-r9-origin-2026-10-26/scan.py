import json,sys,re,collections
P="/data/data/com.termux/files/home/.claude/projects/-data-data-com-termux-files-home-AgentReachProject/"
for sid in sys.argv[1:]:
    import glob
    f=glob.glob(P+sid+"*.jsonl")[0]
    rows=[json.loads(l) for l in open(f)]
    print("=====",sid, len(rows))
    names=collections.Counter(); noag=[]; agents=[]; denies=[]; voices=[]; human=[]
    for i,d in enumerate(rows):
        ts=d.get("timestamp","")[:19]
        m=d.get("message",{}) if isinstance(d.get("message"),dict) else {}
        c=m.get("content")
        if d.get("type")=="user" and not d.get("isMeta") and not d.get("isSidechain"):
            txt = c if isinstance(c,str) else " ".join(x.get("text","") for x in (c or []) if isinstance(x,dict) and x.get("type")=="text")
            if txt and not any(isinstance(x,dict) and x.get("type")=="tool_result" for x in (c or []) if not isinstance(c,str)):
                if re.search(r"агент",txt,re.I) and not txt.startswith("<"): human.append((ts,txt[:160].replace("\n"," ")))
        if isinstance(c,list):
            for x in c:
                if not isinstance(x,dict): continue
                if x.get("type")=="tool_use":
                    names[x["name"]]+=1
                    desc=str((x.get("input") or {}).get("description",""))
                    if "без агента" in desc: noag.append((ts,x["name"],desc))
                    if x["name"] in("Agent","Task"): agents.append((ts,desc))
                if x.get("type")=="tool_result":
                    s=json.dumps(x.get("content"),ensure_ascii=False)
                    if "Ворота «агенти»" in s: denies.append((ts,s[:200]))
        raw=json.dumps(d,ensure_ascii=False)
        if "Голос «агенти»" in raw and d.get("type")!="assistant": voices.append((ts,d.get("type"),d.get("subtype") or d.get("attachment",{}).get("type") if isinstance(d.get("attachment"),dict) else d.get("subtype")))
    print("tools:",dict(names.most_common()))
    print("DENY agents:",len(denies)); [print("  ",*x) for x in denies]
    print("VOICE agents rows:",len(voices)); [print("  ",*x) for x in voices[:10]]
    print("Agent calls:",len(agents)); [print("  ",*x) for x in agents]
    print("без агента:",len(noag)); [print("  ",*x) for x in noag]
    print("human msgs with 'агент':",len(human)); [print("  ",*x) for x in human]
