# Повтор живих зупинок: журнал обрізано до рядка перед зупиненим викликом (копія в tmp), вхід = той самий tool_use.
import json,os,subprocess,sys
D=os.path.dirname(os.path.abspath(__file__)); P=os.path.expanduser("~/.claude/projects/-data-data-com-termux-files-home-AgentReachProject/")
cases=[("86fab127-6cda-48ed-b3a5-65656cd24d62",843),("86fab127-6cda-48ed-b3a5-65656cd24d62",1274),("86fab127-6cda-48ed-b3a5-65656cd24d62",1824),
 ("a62774d0-a461-4ec4-80e4-2bd64bda03c8",157),("a62774d0-a461-4ec4-80e4-2bd64bda03c8",278),("a62774d0-a461-4ec4-80e4-2bd64bda03c8",365),
 ("a62774d0-a461-4ec4-80e4-2bd64bda03c8",858),("a62774d0-a461-4ec4-80e4-2bd64bda03c8",969),("a62774d0-a461-4ec4-80e4-2bd64bda03c8",1430),
 ("a11c12e0-fbbf-421b-82cf-ef510cdcc651",196)]
for sid,ln in cases:
    L=open(P+sid+".jsonl",encoding="utf-8").read().splitlines()
    d=json.loads(L[ln-1]); tu=[x for x in d["message"]["content"] if x.get("type")=="tool_use"][0]
    tp=os.path.join(D,"r.jsonl"); open(tp,"w",encoding="utf-8").write("\n".join(L[:ln-1])+"\n")
    res=[]
    for v in ("orig","fix"):
        log=os.path.join(D,"r.log"); os.path.exists(log) and os.remove(log)
        env=dict(os.environ,EDIT_GATE_LOG=log); env.pop("ANTHROPIC_BASE_URL",None)
        o=subprocess.run([sys.executable,os.path.join(D,v,"edit-gate-hook.py")],input=json.dumps({"session_id":sid,"transcript_path":tp,"cwd":"/data/data/com.termux/files/home/AgentReachProject","tool_name":tu["name"],"tool_input":tu["input"]}),capture_output=True,text=True,env=env).stdout
        res.append("DENY" if '"deny"' in o else "pass")
    print(sid[:8],ln,tu["name"],"orig="+res[0],"fix="+res[1])
# одиниці перед case (a)
sys.path.insert(0,os.path.join(D,"orig")); import importlib.util
s=importlib.util.spec_from_file_location("g",os.path.join(D,"orig","edit-gate-hook.py")); g=importlib.util.module_from_spec(s); s.loader.exec_module(g)
L=open(P+"a11c12e0-fbbf-421b-82cf-ef510cdcc651.jsonl",encoding="utf-8").read().splitlines(); tp=os.path.join(D,"r.jsonl"); open(tp,"w").write("\n".join(L[:195])+"\n")
ev,anc=g.v2_window(tp); u=[e for e in ev if e[0]=="tool" and e[2] in g.V2_WORK and not (e[2]=="Bash" and (g.RE_GIT_OWN.match(e[3].get("command","")) or g.RE_COORD.search(e[3].get("command",""))))]
print("case(a) якір:",anc,"одиниць:",len(u)); [print("  ",e[2],(e[3].get("description") or e[3].get("file_path",""))[:60]) for e in u]
