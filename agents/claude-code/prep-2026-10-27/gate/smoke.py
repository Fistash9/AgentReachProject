"""Імітація входу PreToolUse (як tools/hooks-smoke.py): копія vs оригінал, тимчасовий журнал і лог."""
import json, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); ORIG = os.path.join(HERE, "../../../../.claude/hooks/edit-gate-hook.py")
COPY = os.path.join(HERE, "edit-gate-hook.py"); SID = "11111111-2222-3333-4444-555555555555"
def tl(kind, **k):
    if kind == "user": return {"type": "user", "message": {"role": "user", "content": k["text"]}, "timestamp": "2026-10-27T10:00:00Z", "origin": {"kind": "human"}}
    if kind == "tool": return {"type": "assistant", "timestamp": "2026-10-27T10:00:01Z", "message": {"content": [{"type": "tool_use", "id": "t", "name": k["name"], "input": k["inp"]}]}}
    if kind == "queued": return {"type": "attachment", "timestamp": "2026-10-27T10:00:02Z", "attachment": {"type": "queued_command", "prompt": k["text"]}}
rd = lambda i: tl("tool", name="Bash", inp={"command": f"grep -n x f{i}.py", "description": f"read {i}"})
def run(hook, lines, name, inp, env=None):
    d = tempfile.mkdtemp(dir="/data/data/com.termux/files/usr/tmp"); tp = os.path.join(d, "t.jsonl")
    open(tp, "w").write("\n".join(json.dumps(x, ensure_ascii=False) for x in lines) + "\n")
    e = dict(os.environ, EDIT_GATE_LOG=os.path.join(d, "eg.log"), **(env or {})); e.pop("ANTHROPIC_BASE_URL", None)
    r = subprocess.run([sys.executable, hook], input=json.dumps({"session_id": SID, "transcript_path": tp, "tool_name": name,
                       "tool_input": inp, "cwd": "/data/data/com.termux/files/home/AgentReachProject"}), capture_output=True, text=True, timeout=20)
    o = r.stdout.strip(); return json.loads(o)["hookSpecificOutput"].get("permissionDecision", "hint") if o else "тиша"
after_agent = [tl("user", text="зроби аудит"), tl("tool", name="Agent", inp={"description": "x", "prompt": "y"})] + [rd(i) for i in range(14)]
cases = [
 ("1 читання №15 після Agent", after_agent, "Bash", {"command": "grep -n y z.py", "description": "read 15"}, None, "deny", "тиша"),
 ("2 те саме з «без агента:»", after_agent, "Bash", {"command": "grep -n y z.py", "description": "read 15 без агента: друк одного рядка"}, None, "тиша", "тиша"),
 ("3 нейтральна команда", after_agent, "Bash", {"command": "echo ok", "description": "echo"}, None, "тиша", "тиша"),
 ("4 П3: докір посеред ходу → читання", [tl("user", text="почни"), rd(0), tl("queued", text="агентами не користуєшся ?")], "Bash", {"command": "cat a.py", "description": "c"}, None, "deny", "тиша"),
 ("5 П3 вимкнено (EDIT_GATE_P3=0)", [tl("user", text="почни"), rd(0), tl("queued", text="агентами не користуєшся ?")], "Bash", {"command": "cat a.py", "description": "c"}, {"EDIT_GATE_P3": "0"}, "тиша", "тиша"),
 ("6 П3: після докору вже був Agent", [tl("user", text="почни"), tl("queued", text="ти знов робиш сам"), tl("tool", name="Agent", inp={"description": "x"})], "Bash", {"command": "cat a.py", "description": "c"}, None, "тиша", "тиша"),
]
bad = 0
for nm, lines, name, inp, env, want_c, want_o in cases:
    c, o = run(COPY, lines, name, inp, env), run(ORIG, lines, name, inp, env)
    ok = c == want_c and o == want_o; bad += not ok
    print(f"{'OK ' if ok else 'BAD'} {nm}: копія={c} (чекали {want_c}); оригінал={o} (чекали {want_o})")
print("поломок:", bad)
