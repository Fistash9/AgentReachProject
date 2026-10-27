"""Тест-імітація входу воріт «агенти» v2 (2026-10-27): справжній виклик хука-копії як підпроцесу з JSON на stdin
(як його кличе Claude Code), штучний журнал у tmp, лог воріт — у tmp (EDIT_GATE_LOG), не в .claude/logs.
Для порівняння той самий вхід — в оригінал з HEAD (edit-gate-hook.orig.py). Запуск: python3 smoke.py"""
import glob, json, os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
COPY, ORIG = os.path.join(HERE, "edit-gate-hook.py"), os.path.join(HERE, "edit-gate-hook.orig.py")
TMP = "/data/data/com.termux/files/usr/tmp/gate-v2-smoke"
os.makedirs(TMP, exist_ok=True)
SID = "11111111-2222-3333-4444-555555555555"
n_ts = [0]


def ts():
    n_ts[0] += 1
    return f"2026-10-27T10:{n_ts[0] // 60:02d}:{n_ts[0] % 60:02d}.000Z"


def user(text, kind="human"):
    return {"type": "user", "message": {"role": "user", "content": text}, "origin": {"kind": kind}, "timestamp": ts()}


def tool(name, inp, i=[0]):
    i[0] += 1
    return {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": f"t{i[0]}", "name": name, "input": inp}]},
            "timestamp": ts()}


def report():
    return user('<task-notification>\n<task-id>a1</task-id>\n<status>completed</status>\n<summary>Agent "x" finished'
                '</summary>\n</task-notification>', kind="task-notification")


def bash(k, desc="крок"):
    return tool("Bash", {"command": f"python3 tools/x.py --step {k}", "description": desc})


def run(hook, records, name, inp, env=None, data_extra=None):
    tp = os.path.join(TMP, "t.jsonl")
    with open(tp, "w") as f:
        f.write("\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n")
    log = os.path.join(TMP, "edit-gate.log")
    if os.path.exists(log):
        os.remove(log)  # власний тимчасовий файл тесту в tmp
    e = dict(os.environ, EDIT_GATE_LOG=log, **(env or {}))
    e.pop("ANTHROPIC_BASE_URL", None); e.pop("EDIT_GATE_AGENTS", None)
    data = {"tool_name": name, "tool_input": inp, "transcript_path": tp, "session_id": SID,
            "cwd": os.path.abspath(os.path.join(HERE, "../../.."))} | (data_extra or {})
    out = subprocess.run([sys.executable, hook], input=json.dumps(data), capture_output=True, text=True, env=e,
                         timeout=60).stdout
    try:
        o = json.loads(out).get("hookSpecificOutput", {})
    except ValueError:
        return "тиша", ""
    return ("deny" if o.get("permissionDecision") == "deny" else "тиша"), o.get("permissionDecisionReason", "")[:70]


base = [user("зроби аналіз"), tool("Agent", {"description": "аналіз", "prompt": "..."})]
work11 = base + [bash(k) for k in range(11)]
small = {"file_path": os.path.join(TMP, "x.md"), "old_string": "a", "new_string": "b\nc"}
big = dict(small, new_string="\n".join("r" for _ in range(30)))
CASES = [  # (назва, записи, інструмент, вхід, env, data_extra, очікування копії)
    ("1 крок №12 після Agent (команда, не читання)", work11, "Bash", {"command": "python3 tools/y.py"}, None, None, "deny"),
    ("2 те саме, «без агента: один grep» (нема в списку)", work11, "Bash",
     {"command": "python3 tools/y.py", "description": "y (без агента: один grep)"}, None, None, "deny"),
    ("3 те саме, «без агента: закриття сесії»", work11, "Bash",
     {"command": "python3 tools/y.py", "description": "без агента: закриття сесії"}, None, None, "тиша"),
    ("4 крок №12 = git status", work11, "Bash", {"command": "git status --short"}, None, None, "тиша"),
    ("5 закриття: «закрий сесію», крок №12", base + [user("закрий сесію")] + [bash(k) for k in range(11)], "Bash",
     {"command": "python3 tools/y.py"}, None, None, "тиша"),
    ("6 після звіту — 2-й крок вільний", base + [report(), bash(1)], "Bash", {"command": "python3 tools/y.py"},
     None, None, "тиша"),
    ("7 після звіту — 3-й крок (доробка)", base + [report(), bash(1), bash(2)], "Bash",
     {"command": "python3 tools/y.py"}, None, None, "deny"),
    ("8 Edit 2 рядки «без агента: одна правка»", work11, "Edit", dict(small, description="без агента: одна правка"),
     None, None, "тиша"),
    ("9 Edit 30 рядків «без агента: одна правка»", work11, "Edit", dict(big, description="без агента: одна правка"),
     None, None, "deny"),
    ("10 Agent щойно — лічильник з нуля", work11 + [tool("Agent", {"description": "y", "prompt": "."})], "Bash",
     {"command": "python3 tools/y.py"}, None, None, "тиша"),
    ("11 під-агент (agent_id)", work11, "Bash", {"command": "python3 tools/y.py"}, None, {"agent_id": "a1"}, "тиша"),
    ("12 EDIT_GATE_V2=0 → старі ворота (Agent у ході)", work11, "Bash", {"command": "python3 tools/y.py"},
     {"EDIT_GATE_V2": "0"}, None, "тиша"),
    ("13 EDIT_GATE_V2_C=0: 3-й крок після звіту", base + [report(), bash(1), bash(2)], "Bash",
     {"command": "python3 tools/y.py"}, {"EDIT_GATE_V2_C": "0"}, None, "тиша"),
    ("14 нагляд за DSH (tmux capture-pane) крок №12", work11, "Bash", {"command": "tmux capture-pane -p -t work:3"},
     None, None, "тиша"),
]
bad = 0
for nm, rec, tn, inp, env, extra, want in CASES:
    c, why = run(COPY, rec, tn, inp, env, extra)
    o, _ = run(ORIG, rec, tn, inp, env, extra)
    ok = c == want
    bad += not ok
    print(f"{'OK ' if ok else 'ЗБІЙ'} {nm}: копія={c} (очік. {want}), оригінал={o}" + (f" | {why}" if c == "deny" else ""))
# швидкість на справжньому великому журналі (2487d837, ~6.8 МБ): v2_window читає з кінця до останньої роздачі
import importlib.util
s = importlib.util.spec_from_file_location("eg", COPY); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
big_j = glob.glob(os.path.expanduser("~/.claude/projects/-data-data-com-termux-files-home-AgentReachProject/2487d837*.jsonl"))[0]
t = time.time(); ev, anc = m.v2_window(big_j); dt = time.time() - t
print(f"v2_window на {os.path.getsize(big_j)} Б: {dt:.3f} с, подій у вікні {len(ev)}, якір {anc}")
print(f"випадків {len(CASES)}, збоїв {bad}")
