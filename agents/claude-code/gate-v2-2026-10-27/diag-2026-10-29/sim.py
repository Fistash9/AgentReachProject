# Імітація входу хука: синтетичний журнал у tmp, LOG у tmp, session_id-UUID. Без побічних ефектів у проєкті.
import json,os,subprocess,sys,uuid
D=os.path.dirname(os.path.abspath(__file__)); hook=sys.argv[1]
def A(name,inp,ts): return {"type":"assistant","timestamp":ts,"message":{"content":[{"type":"tool_use","id":str(uuid.uuid4()),"name":name,"input":inp}]}}
H=lambda t,ts:{"type":"user","timestamp":ts,"origin":{"kind":"human"},"message":{"content":t}}
R=lambda ts:{"type":"user","timestamp":ts,"message":{"content":'<task-notification><summary>Agent "x" completed</summary></task-notification>'}}
def run(label,lines,name,inp,twice=False):
    tp=os.path.join(D,"t.jsonl"); log=os.path.join(D,"sim.log")
    open(tp,"w").write("\n".join(json.dumps(l,ensure_ascii=False) for l in lines)+"\n")
    if os.path.exists(log): os.remove(log)
    env=dict(os.environ,EDIT_GATE_LOG=log); env.pop("ANTHROPIC_BASE_URL",None)
    data=json.dumps({"session_id":"11111111-2222-3333-4444-555555555555","transcript_path":tp,"cwd":"/data/data/com.termux/files/home/AgentReachProject","tool_name":name,"tool_input":inp},ensure_ascii=False)
    outs=[]
    for _ in range(2 if twice else 1):
        o=subprocess.run([sys.executable,hook],input=data,capture_output=True,text=True,env=env).stdout
        outs.append("DENY" if '"deny"' in o else "pass")
    print(f"{label:<44} {' / '.join(outs)}")
ts=lambda i:f"2026-10-29T10:{i:02d}:00.000Z"
own11=[H("зроби X",ts(0))]+[A("Bash",{"command":f"ls f{i}"},ts(i+1)) for i in range(11)]
win=[H("зроби X",ts(0)),A("Agent",{"prompt":"p"},ts(1)),R(ts(2)),A("Bash",{"command":"grep a b"},ts(3)),A("Bash",{"command":"grep c d"},ts(4))]
run("1 A: Edit 2 рядки (12-й крок)",own11,"Edit",{"file_path":"/data/data/com.termux/files/usr/tmp/x.py","old_string":"a","new_string":"b\nc"})
run("2 A: Bash, причина в описі 'правка ≤10 рядків'",own11,"Bash",{"command":"sed -i s/a/b/ /data/data/com.termux/files/usr/tmp/x.py","description":"без агента: правка ≤10 рядків"})
run("3 A: коміт із префіксом ': \"без агента…\"'",own11,"Bash",{"command":': "без агента: коміт" && git status --short && git commit -m x',"description":"Commit"})
run("4 A: git status без префікса",own11,"Bash",{"command":"git status --short"})
run("5 A: опис 'без агента: естафета' (контроль)",own11,"Bash",{"command":"ls","description":"без агента: естафета"})
run("6 A: grep після 2-рядкової правки (case a)",own11,"Bash",{"command":'grep -n "\\bshort\\b" .claude/hooks/tree-focus-hook.py',"description":"Search for existing uses of short"})
run("7 C: 3-й крок, опис 'перевірка звіту під-агента'",win,"Bash",{"command":"grep e f","description":"без агента: перевірка звіту під-агента"})
run("8 C: 3-й крок, 'крок verify-before-show'",win,"Bash",{"command":"grep e f","description":"без агента: крок verify-before-show"})
run("9 A: дедуп — той самий виклик двічі",own11,"Bash",{"command":"ls z"},twice=True)
