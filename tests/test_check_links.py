import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path
import pytest


def load_check_links_module():
    script_path = Path(__file__).parent.parent / "tools" / "check-links.py"
    spec = importlib.util.spec_from_file_location("check_links", script_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class FakeProjectEnv:
    def __init__(self, mod, proj_dir, home_dir, commit_hash):
        self.mod = mod
        self.proj_dir = proj_dir
        self.home_dir = home_dir
        self.commit_hash = commit_hash

    def reset_counters(self):
        self.mod.ok = 0
        self.mod.bad.clear()


@pytest.fixture
def env(tmp_path, monkeypatch):
    home_dir = tmp_path / "home"
    proj_dir = home_dir / "AgentReachProject"
    hooks_dir = proj_dir / ".claude" / "hooks"
    tools_dir = proj_dir / "tools"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    tools_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("HOME", str(home_dir))
    monkeypatch.setenv("CHECK_ROOT", str(proj_dir))
    monkeypatch.chdir(tmp_path)

    subprocess.run(["git", "init"], cwd=proj_dir, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=proj_dir, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=proj_dir, check=True)

    dummy = proj_dir / "dummy.txt"
    dummy.write_text("hello")
    subprocess.run(["git", "add", "dummy.txt"], cwd=proj_dir, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=proj_dir, check=True, stdout=subprocess.DEVNULL)
    commit_hash = subprocess.check_output(["git", "rev-parse", "--short=7", "HEAD"], cwd=proj_dir, text=True).strip()

    hook_file = hooks_dir / "sample-hook.py"
    hook_file.write_text("import sys\nsys.exit(0)\n")

    settings_file = proj_dir / ".claude" / "settings.local.json"
    settings_file.write_text(json.dumps({
        "hooks": {
            "PreToolUse": [
                {"hooks": [{"command": f"python3 {hook_file}"}]}
            ]
        }
    }))

    rules_content = """# Навігація
# Checkpoint
# Робота з відкладеними
# DeepSeek
# Git
# Журнал vs знімок
# Видалення файлів

хук sample
`tools/helper.py`
"""
    (proj_dir / "RULES.md").write_text(rules_content)
    (tools_dir / "helper.py").write_text("# helper")
    (proj_dir / "RULES-WHY.md").write_text(f"Commit ({commit_hash})")
    (proj_dir / "README.md").write_text("[RULES.md] [RULES-WHY.md] [tools/]")

    run_sh = proj_dir / "run.sh"
    run_sh.write_text("#!/bin/sh\nexit 0")
    run_sh.chmod(0o755)
    (proj_dir / "menu.sh").write_text("~/AgentReachProject/run.sh")

    os.symlink("RULES.md", proj_dir / "CLAUDE.md")
    os.symlink("RULES.md", proj_dir / "AGENTS.md")

    mod = load_check_links_module()
    fake_env = FakeProjectEnv(mod, proj_dir, home_dir, commit_hash)
    fake_env.reset_counters()
    return fake_env


def test_main_success(env):
    rc = env.mod.main()
    assert rc == 0
    assert env.mod.bad == []
    assert env.mod.ok > 0


def test_group_1_pass_and_fail(env):
    env.reset_counters()
    assert env.mod.main() == 0

    (env.proj_dir / "CLAUDE.md").unlink()
    os.symlink("README.md", env.proj_dir / "CLAUDE.md")

    env.reset_counters()
    rc = env.mod.main()
    assert rc == 1
    assert "CLAUDE.md не веде на RULES.md" in env.mod.bad


def test_group_2_pass_and_fail(env):
    rules = (env.proj_dir / "RULES.md").read_text()
    (env.proj_dir / "RULES.md").write_text(rules + "\nDOC.md")
    (env.proj_dir / "DOC.md").write_text("content")
    readme = (env.proj_dir / "README.md").read_text()
    (env.proj_dir / "README.md").write_text(readme + " [DOC.md]")

    env.reset_counters()
    assert env.mod.main() == 0

    (env.proj_dir / "RULES.md").write_text(rules + "\nMISSING.md")
    env.reset_counters()
    rc = env.mod.main()
    assert rc == 1
    assert "RULES.md: файл MISSING.md не знайдено" in env.mod.bad


def test_group_3_pass_and_fail(env):
    env.reset_counters()
    assert env.mod.main() == 0

    rules = (env.proj_dir / "RULES.md").read_text()
    (env.proj_dir / "RULES.md").write_text(rules + "\n`tools/nonexistent.py`\n")

    env.reset_counters()
    rc = env.mod.main()
    assert rc == 1
    assert "RULES.md: шлях tools/nonexistent.py не існує" in env.mod.bad


def test_group_4_pass_and_fail(env):
    env.reset_counters()
    assert env.mod.main() == 0

    rules = (env.proj_dir / "RULES.md").read_text()
    bad_rules = "\n".join([line for line in rules.splitlines() if line != "# Git"])
    (env.proj_dir / "RULES.md").write_text(bad_rules)

    env.reset_counters()
    rc = env.mod.main()
    assert rc == 1
    assert "RULES.md: розділ «Git» зник" in env.mod.bad


def test_group_5_pass_and_fail(env):
    env.reset_counters()
    assert env.mod.main() == 0

    rules = (env.proj_dir / "RULES.md").read_text()
    (env.proj_dir / "RULES.md").write_text(rules + "\nхук missing\n")

    env.reset_counters()
    rc = env.mod.main()
    assert rc == 1
    assert "RULES.md: хук missing — файлу немає" in env.mod.bad


def test_group_6_pass_and_fail(env):
    env.reset_counters()
    assert env.mod.main() == 0

    # Fail 1: unlinked hook
    unlinked = env.proj_dir / ".claude" / "hooks" / "unlinked-hook.py"
    unlinked.write_text("import sys\nsys.exit(0)\n")

    env.reset_counters()
    rc = env.mod.main()
    assert rc == 1
    assert "хук unlinked-hook.py не підключений у settings" in env.mod.bad

    # Clean up unlinked hook
    unlinked.unlink()

    # Fail 2: missing target in settings
    settings_file = env.proj_dir / ".claude" / "settings.local.json"
    settings_file.write_text(json.dumps({
        "hooks": {
            "PreToolUse": [
                {"hooks": [{"command": "python3 /nonexistent/hook.py"}]}
            ]
        }
    }))

    env.reset_counters()
    rc = env.mod.main()
    assert rc == 1
    assert "settings PreToolUse: /nonexistent/hook.py не існує" in env.mod.bad

    # Fail 3: compilation failure
    hook_file = env.proj_dir / ".claude" / "hooks" / "sample-hook.py"
    hook_file.write_text("def bad_syntax(")
    settings_file.write_text(json.dumps({
        "hooks": {
            "PreToolUse": [
                {"hooks": [{"command": f"python3 {hook_file}"}]}
            ]
        }
    }))

    env.reset_counters()
    rc = env.mod.main()
    assert rc == 1
    assert "sample-hook.py не компілюється" in env.mod.bad


def test_group_7_pass_and_fail(env):
    env.reset_counters()
    assert env.mod.main() == 0

    hook_file = env.proj_dir / ".claude" / "hooks" / "sample-hook.py"

    # Fail 1: non-zero exit code
    hook_file.write_text("import sys\nsys.exit(1)\n")
    env.reset_counters()
    rc = env.mod.main()
    assert rc == 1
    assert any("sample-hook.py на нейтральному" in msg for msg in env.mod.bad)

    # Fail 2: exit 0 but prints permission decision "deny" to stdout
    hook_file.write_text('import json\nprint(json.dumps({"hookSpecificOutput": {"permissionDecision": "deny"}}))\n')
    env.reset_counters()
    rc = env.mod.main()
    assert rc == 1
    assert any("sample-hook.py на нейтральному" in msg for msg in env.mod.bad)


def test_group_8_pass_and_fail(env):
    env.reset_counters()
    assert env.mod.main() == 0

    (env.proj_dir / "RULES-WHY.md").write_text("See commit (0000000)")

    env.reset_counters()
    rc = env.mod.main()
    assert rc == 1
    assert "RULES-WHY.md: коміт 0000000 не існує" in env.mod.bad


def test_group_9_pass_and_fail(env):
    mem_dir = env.home_dir / ".claude" / "projects" / "-data-data-com-termux-files-home-AgentReachProject" / "memory"
    mem_dir.mkdir(parents=True, exist_ok=True)
    mem_file = mem_dir / "mem.md"
    mem_file.write_text("Ref: `tools/helper.py`\n")

    env.reset_counters()
    assert env.mod.main() == 0

    mem_file.write_text("Ref: `tools/missing.py`\n")

    env.reset_counters()
    rc = env.mod.main()
    assert rc == 1
    assert "пам'ять mem.md: шлях tools/missing.py не існує" in env.mod.bad


def test_group_10_pass_and_fail(env):
    env.reset_counters()
    assert env.mod.main() == 0

    # Fail 1: missing target
    (env.proj_dir / "menu.sh").write_text("~/AgentReachProject/missing.sh")

    env.reset_counters()
    rc = env.mod.main()
    assert rc == 1
    assert "menu.sh: ~/AgentReachProject/missing.sh не існує" in env.mod.bad

    # Fail 2: non-executable target
    run_sh = env.proj_dir / "run.sh"
    run_sh.chmod(0o644)
    (env.proj_dir / "menu.sh").write_text("~/AgentReachProject/run.sh")

    env.reset_counters()
    rc = env.mod.main()
    assert rc == 1
    assert "menu.sh: ~/AgentReachProject/run.sh не виконуваний" in env.mod.bad


def test_group_11_pass_and_fail(env):
    env.reset_counters()
    assert env.mod.main() == 0

    # Fail 1: missing .md in readme map
    (env.proj_dir / "EXTRA.md").write_text("extra")

    env.reset_counters()
    rc = env.mod.main()
    assert rc == 1
    assert "README.md: у карті немає [EXTRA.md]" in env.mod.bad

    # Clean up EXTRA.md
    (env.proj_dir / "EXTRA.md").unlink()

    # Fail 2: missing [tools/] in readme map
    (env.proj_dir / "README.md").write_text("[RULES.md] [RULES-WHY.md]")

    env.reset_counters()
    rc = env.mod.main()
    assert rc == 1
    assert "README.md: у карті немає [tools/]" in env.mod.bad
