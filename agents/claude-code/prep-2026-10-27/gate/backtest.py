"""Бектест воріт «агенти»: оригінал vs копія П1 vs копія П1+П3. Для кожного Bash/Edit/Write виклику головного
журналу пише в tmp рядки поточного ходу ДО цього виклику і кличе справжній agents_check відповідного модуля."""
import importlib.util, json, os, re, sys, glob
os.environ.pop("ANTHROPIC_BASE_URL", None); os.environ.pop("EDIT_GATE_AGENTS", None)
HERE = os.path.dirname(os.path.abspath(__file__)); ORIG = os.path.join(HERE, "../../../../.claude/hooks")
P = os.path.expanduser("~/.claude/projects/-data-data-com-termux-files-home-AgentReachProject/")
TMP = "/data/data/com.termux/files/usr/tmp/gate-bt-turn.jsonl"
MATCH = re.compile(r"^(Edit|Write|MultiEdit|Bash)$")
def load(d, f, nm):
    s = importlib.util.spec_from_file_location(nm, os.path.join(d, f)); m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m); return m
orig, copy = load(ORIG, "edit-gate-hook.py", "eg_o"), load(HERE, "edit-gate-hook.py", "eg_c")
agv_o, agv_c = load(ORIG, "answer-gate-shadow-hook.py", "ag_o"), load(HERE, "answer-gate-shadow-hook.py", "ag_c")
modes = [("orig", orig, agv_o, None), ("P1", copy, agv_c, False), ("P1+P3", copy, agv_c, True)]
for sid in sys.argv[1:]:
    path = glob.glob(P + sid + "*.jsonl")[0]
    lines = open(path, encoding="utf-8", errors="ignore").read().splitlines()
    start, seen, denies, reproaches = 0, {m[0]: set() for m in modes}, [], []
    for i, l in enumerate(lines):
        try: d = json.loads(l)
        except ValueError: continue
        if not isinstance(d, dict): continue
        if agv_o.starts_turn(d, True): start = i
        a = d.get("attachment") if d.get("type") == "attachment" else None
        if isinstance(a, dict) and a.get("type") == "queued_command" and copy.RE_REPROACH.search(str(a.get("prompt", ""))) \
                and not str(a.get("prompt", "")).startswith("<"):
            reproaches.append((d["timestamp"], a["prompt"][:50]))
        if d.get("type") != "assistant" or d.get("isSidechain"): continue
        for x in (d.get("message") or {}).get("content") or []:
            if not (isinstance(x, dict) and x.get("type") == "tool_use" and MATCH.match(x.get("name", ""))): continue
            open(TMP, "w").write("\n".join(lines[start:i]) + "\n")
            data = {"tool_name": x["name"], "tool_input": x.get("input") or {}, "transcript_path": TMP, "session_id": sid + "-0000-0000-0000-000000000000"[:36-len(sid)] if len(sid) < 36 else sid}
            data["session_id"] = "00000000-0000-0000-0000-000000000000"
            for mn, mod, agv, p3 in modes:
                if p3 is not None: mod.P3_ON = p3
                try: r = mod.agents_check(data, agv)
                except Exception as e: r = None; print("ERR", mn, e)
                if r and r[0] not in seen[mn]:
                    seen[mn].add(r[0]); inp = x.get("input") or {}
                    denies.append((d["timestamp"], mn, r[0].split("\t")[0], r[1], inp.get("description", "")[:70],
                                   str(inp.get("command", ""))[:70].replace("\n", " ")))
    print(f"===== {sid}  докорів (queued, шаблон П3): {len(reproaches)}")
    for t, q in reproaches: print(f"  ДОКІР {t[5:19]} «{q}»")
    for mn, *_ in modes: print(f"  deny[{mn}] = {sum(1 for x in denies if x[1] == mn)}")
    for t, mn, k, n, desc, cmd in denies:
        print(f"  {t[5:19]} {mn:<6} {k:<9} n={n:<3} {desc} | {cmd}")
    for t, q in reproaches:
        prev = [x for x in denies if x[0] < t and x[0] >= t[:11] + "00" and x[1] != "orig"]
        print(f"  до докору {t[5:19]}: deny копії того дня раніше — " + (", ".join(f"{x[0][11:19]}({x[1]})" for x in prev) or "немає"))
