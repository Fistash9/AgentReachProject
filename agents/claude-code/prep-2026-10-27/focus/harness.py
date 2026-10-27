"""Тест-обв'язка: запуск оригіналу й копії tree-focus у процесі (DSH_LOG → tmp, без побічних записів)."""
import importlib.util, io, json, os, sys, contextlib
ROOT = "/data/data/com.termux/files/home/AgentReachProject"
HERE = os.path.dirname(os.path.abspath(__file__))
def load(path, name):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m); m.DSH_LOG = "/data/data/com.termux/files/usr/tmp/focus-dsh-test.jsonl"; return m
ORIG = load(os.path.join(ROOT, ".claude/hooks/tree-focus-hook.py"), "orig")
COPY = load(os.path.join(HERE, "tree-focus-hook.py"), "copy")
def run(m, inp):
    sys.stdin = io.StringIO(json.dumps(inp)); buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        m.main()
    o = buf.getvalue().strip()
    return json.loads(o)["hookSpecificOutput"]["additionalContext"] if o else ""
base = {"session_id": "test", "cwd": ROOT, "transcript_path": ""}
