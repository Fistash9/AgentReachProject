#!/data/data/com.termux/files/usr/bin/python3
"""Тест install-check-hook.py імітацією входу (без реальних встановлень).
Друкує кожен випадок і INSTALL_CHECK_OK / INSTALL_CHECK_FAIL N.
Лог хука не забруднює: свій session_id, рядки після прогону видаляються."""
import json
import os
import subprocess
import sys
import uuid

PROJECT = "/data/data/com.termux/files/home/AgentReachProject"
HOOK = os.path.join(PROJECT, ".claude/hooks/install-check-hook.py")
LOG = os.path.join(PROJECT, ".claude/logs/install-check.log")
SKILLS = os.path.join(PROJECT, ".claude/skills")

CASES = [  # (інструмент, вхід, очікування)
    # має спрацювати
    ("Bash", "mkdir -p .claude/skills/llm-council && cp ~/tmp/council/SKILL.md .claude/skills/llm-council/SKILL.md", True),
    ("Bash", "git clone https://github.com/x/y ~/.claude/skills/y", True),
    ("Bash", "sudo cp -r y ~/.claude/skills/", True),
    ("Bash", "curl -sL https://x/SKILL.md -o .claude/skills/z/SKILL.md", True),
    ("Bash", "claude mcp add foo -- npx foo", True),
    ("Bash", "claude mcp add-json foo '{}'", True),
    ("Bash", "claude plugin install bar", True),
    ("Bash", "claude plugin i bar", True),
    ("Bash", "claude plugins update bar", True),
    ("Bash", "claude plugin marketplace add owner/repo", True),
    ("Bash", "python3 -c \"import os;os.makedirs('.claude/skills/x');open('.claude/skills/x/SKILL.md','w').write('a')\"", True),
    ("Bash", "node -e \"require('fs').mkdirSync('.claude/skills/y',{recursive:true})\"", True),
    ("Bash", "python3 tools/installer.py --dest .claude/skills", True),
    ("Write", os.path.join(SKILLS, "brand-new-skill/SKILL.md"), True),
    # має мовчати
    ("Bash", "ls .claude/skills/ | grep council", False),
    ("Bash", "cat .claude/skills/verify-before-show/verifier-prompt.md", False),
    ("Bash", "git add .claude/skills/llm-council/SKILL.md TROUBLES.md", False),
    ("Bash", "grep -l -i skills .claude/hooks/*.py", False),
    ("Bash", "claude mcp add --help", False),
    ("Bash", "claude plugin list", False),
    ("Bash", "python3 tools/check.py .claude/skills/llm-council/SKILL.md", False),
    ("Bash", "echo '{\"tool_input\":{\"command\":\"mkdir -p .claude/skills/x && cp a .claude/skills/x/SKILL.md\"}}' | node pkgtruth.js hook", False),
    ("Bash", "git commit -m \"встановлено: mkdir + cp у .claude/skills/llm-council\"", False),
    ("Bash", "cat >> TROUBLES.md <<'EOF'\nвстановлено (mkdir && cp) у .claude/skills/llm-council/\nEOF", False),
    ("Write", os.path.join(SKILLS, "verify-before-show/SKILL.md"), False),  # наявний скіл — справа verify-nudge
    ("Write", os.path.join(PROJECT, "TROUBLES.md"), False),
]


def run(tool, val, sid):
    inp = {"command": val} if tool == "Bash" else {"file_path": val, "content": "x"}
    data = {"tool_name": tool, "tool_input": inp, "session_id": sid, "cwd": PROJECT}
    out = subprocess.run([sys.executable, HOOK], input=json.dumps(data),
                         capture_output=True, text=True).stdout
    return bool(out.strip())


def main():
    fails = 0
    for i, (tool, val, want) in enumerate(CASES, 1):
        sid = f"selftest-{uuid.uuid4().hex[:8]}"  # окрема сесія — без дедупу між випадками
        got = run(tool, val, sid)
        ok = got == want
        fails += not ok
        print(f"{i:2} {'ok ' if ok else 'FAIL'} want={'FIRE' if want else 'quiet'} "
              f"got={'FIRE' if got else 'quiet'} :: {tool} {val[:70]!r}")
    # дедуп: друга та сама ціль у тій самій сесії — тиша
    sid = f"selftest-{uuid.uuid4().hex[:8]}"
    first, second = run("Bash", "claude plugin install z", sid), run("Bash", "claude plugin install z", sid)
    ok = first and not second
    fails += not ok
    print(f"{len(CASES) + 1:2} {'ok ' if ok else 'FAIL'} дедуп у сесії: {first}/{second}")
    if os.path.exists(LOG):
        keep = [ln for ln in open(LOG) if not ln.startswith("selftest-")]
        open(LOG, "w").writelines(keep)
    print("INSTALL_CHECK_OK" if not fails else f"INSTALL_CHECK_FAIL {fails}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
