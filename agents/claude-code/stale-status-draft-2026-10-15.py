import re,glob,os,sys
ROOT=sys.argv[1]
NODE=re.compile(r"^(\s*)- \[(.)\] (\S+)\s+(.*)$")
DATE=re.compile(r"20\d\d-(\d\d)-(\d\d)")
DONE=re.compile(r"пройдено|2/2|закрит|зроблено ✓|\bdone\b ✓|ЗАКРИТО|вирішено|виконано", re.I)
for p in sorted(glob.glob(os.path.join(ROOT,"trees","*.md"))):
    lines=open(p,encoding="utf-8").read().split("\n")
    nodes=[]
    for i,l in enumerate(lines):
        m=NODE.match(l)
        if m: nodes.append(dict(i=i,d=len(m.group(1)),st=m.group(2),id=m.group(3),name=m.group(4)[:60]))
    for k,n in enumerate(nodes):
        end=nodes[k+1]["i"] if k+1<len(nodes) else len(lines)
        block="\n".join(lines[n["i"]:end])
        dates=sorted((int(a),int(b)) for a,b in DATE.findall(block))
        last=f"{dates[-1][1]:02d}.{dates[-1][0]:02d}" if dates else "—"
        f=os.path.basename(p)
        kids=[]
        for m in nodes[k+1:]:
            if m["d"]<=n["d"]: break
            kids.append(m)
        if n["st"]=="?": print(f"A [?] {f}:{n['i']+1} {n['id']} останній запис {last}")
        if n["st"] in " >" and kids and all(c["st"] in "x~" for c in kids):
            print(f"B батько відкритий, діти закриті: {f}:{n['i']+1} {n['id']} ({len(kids)} дітей)")
        if n["st"]==">" and dates and dates[-1] < (10,10):
            print(f"C [>] старий: {f}:{n['i']+1} {n['id']} останній запис {last}")
        if n["st"] in " >?":
            own="\n".join(lines[n["i"]:(kids[0]["i"] if kids else end)])
            hits=DONE.findall(own)
            if hits: print(f"D відкритий зі словами завершення: {f}:{n['i']+1} [{n['st']}] {n['id']} {sorted(set(hits))} останній {last}")
