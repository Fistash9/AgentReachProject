#!/usr/bin/env python3
"""Перевірка підключених хуків на відомих входах (Q9, 2026-10-06).

Навіщо: хуки fail-open (`except Exception: pass`) — зламаний хук мовчить, а
тестів хуків не було. «Не впав» тут нічого не доводить, тому кожен випадок
перевіряє ОЧІКУВАНУ відповідь (підказка / блок / тиша). Команди беруться з
живих налаштувань (.claude/settings.local.json, ~/.claude/settings.json) —
битий шлях теж ловиться.

Не ганяються наживо (побічні дії; лише перевірка, що файл існує й компілюється):
переписувач промптів delegate (платна модель), логери результатів delegate
(статистика), таймер сесії (лічильник користувача), спрацювання verify-nudge
на захищеному файлі (журнал проби «доказ ужитку»).

  python3 tools/hooks-smoke.py        # код 0 — усе ціле, 1 — є поломки
Лише stdlib.
"""
import json
import os
import py_compile
import re
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SID = "hooks-smoke-" + time.strftime("%Y%m%d%H%M%S")
SKIP = {
    "delegate-prompt-improver-hook.py": "може викликати платну модель",
    "delegate-outcome-logger-hook.py": "пише статистику delegate",
    "session-timer.sh": "збиває лічильник часу користувача",
}


def hooks():
    """[(подія, matcher, команда)] з обох налаштувань."""
    out = []
    # HOOKS_SMOKE_SETTINGS — інші файли налаштувань (через «:») для мутаційної
    # перевірки самого тесту: чи ловить він навмисно зламаний хук.
    paths = os.environ.get("HOOKS_SMOKE_SETTINGS")
    for p in (paths.split(":") if paths else
              (os.path.join(ROOT, ".claude", "settings.local.json"),
               os.path.expanduser("~/.claude/settings.json"))):
        try:
            d = json.load(open(p, encoding="utf-8")).get("hooks", {})
        except (OSError, ValueError) as e:
            out.append(("?", "?", f"НЕ ЧИТАЄТЬСЯ {p}: {e}"))
            continue
        for ev, arr in d.items():
            for m in arr:
                for h in m.get("hooks", []):
                    out.append((ev, m.get("matcher", ""), h.get("command", "")))
    return out


def find(hs, event, needle, matcher=None):
    for ev, mt, cmd in hs:
        if ev == event and needle in cmd and (matcher is None or matcher == mt):
            return cmd
    return None


def run(cmd, payload, env=None, timeout=20):
    e = dict(os.environ, **(env or {}))
    t = time.time()
    r = subprocess.run(cmd, shell=True, input=json.dumps(payload, ensure_ascii=False),
                       capture_output=True, text=True, timeout=timeout, cwd=ROOT, env=e)
    return r.returncode, r.stdout, r.stderr, time.time() - t


def ctx(out):
    """additionalContext або permissionDecision з JSON-виводу хука."""
    try:
        d = json.loads(out).get("hookSpecificOutput", {})
        return d.get("additionalContext", ""), d.get("permissionDecision")
    except ValueError:
        return out, None


def main():
    hs = hooks()
    tmp = tempfile.mkdtemp(prefix="hooks-smoke-")
    fake = os.path.join(tmp, "t.jsonl")
    with open(fake, "w", encoding="utf-8") as f:
        f.write(json.dumps({"type": "user", "message": {"content": "тест"}}) + "\n")
        f.write(json.dumps({"type": "assistant", "message": {"content": [
            {"type": "text", "text": "Далі **T5** — скіл пошуку."}]}}) + "\n")
    envf = os.path.join(tmp, "env")
    base = {"session_id": SID, "cwd": ROOT, "transcript_path": fake}

    def bash(c):
        return {**base, "hook_event_name": "PreToolUse", "tool_name": "Bash",
                "tool_input": {"command": c}}

    # (назва, подія, частина команди, matcher, вхід, env, перевірка(rc, out, err) -> bool, що очікуємо)
    cases = [
        ("unset grep/find (старт)", "SessionStart", "CLAUDE_ENV_FILE", None,
         {**base, "hook_event_name": "SessionStart"}, {"CLAUDE_ENV_FILE": envf},
         lambda rc, o, e: rc == 0 and "unset -f grep" in open(envf).read(), "рядок у CLAUDE_ENV_FILE"),
        ("tree-focus старт", "SessionStart", "tree-focus-hook.py", None,
         {**base, "hook_event_name": "SessionStart"}, None,
         lambda rc, o, e: "Як застосовувати" in ctx(o)[0] and "trees-index" in ctx(o)[0],
         "фокус + «Як застосовувати» + рядок trees-index"),
        ("tree-focus повідомлення", "UserPromptSubmit", "tree-focus-hook.py", None,
         {**base, "hook_event_name": "UserPromptSubmit", "prompt": "тест"}, None,
         lambda rc, o, e: ("В роботі" in ctx(o)[0] or "Жоден" in ctx(o)[0]) and len(ctx(o)[0]) < 600,
         "короткий рядок фокусу (<600 симв.)"),
        ("node-label-shadow (бектест)", None, None, None, None, None, None, "1 розбіжність на «T5 — скіл пошуку»"),
        ("unlazy Stop", "Stop", "stop-hook.mjs", None,
         {**base, "hook_event_name": "Stop", "stop_hook_active": True}, None,
         lambda rc, o, e: rc == 0, "код 0 при stop_hook_active"),
        ("pkgtruth: звичайна команда", "PreToolUse", "pkgtruth", "Bash", bash("echo smoke"), None,
         lambda rc, o, e: rc == 0 and ctx(o)[1] != "deny", "пропускає"),
        ("troubles-grep", "PreToolUse", "troubles-grep-hook.py", "Bash", bash("yt-dlp --version"), None,
         lambda rc, o, e: "TROUBLES.md має релевантні записи" in ctx(o)[0], "підказка з TROUBLES"),
        ("baton-reminder: не push", "PreToolUse", "baton-reminder-hook.py", "Bash", bash("echo smoke"), None,
         lambda rc, o, e: rc == 0 and not o.strip(), "тиша"),
        ("trash-md-guard: rm у проєкті", "PreToolUse", "trash-md-guard-hook.py", "Bash",
         bash(f"rm {ROOT}/hooks-smoke-не-існує.txt"), None,
         lambda rc, o, e: rc == 2 or ctx(o)[1] == "deny", "блок (TRASH.md не свіжий)"),
        ("trash-md-guard: rm у tmp", "PreToolUse", "trash-md-guard-hook.py", "Bash",
         bash(f"rm {tmp}/x"), None,
         lambda rc, o, e: rc == 0 and ctx(o)[1] != "deny", "пропускає tmp"),
        ("git-add-status: звичайний add", "PreToolUse", "git-add-status-hook.py", "Bash",
         bash("git add tools/hooks-smoke.py"), None,
         lambda rc, o, e: ctx(o)[1] != "deny", "не блокує (статус — якщо дерево брудне)"),
        ("git-add-status: agent.py", "PreToolUse", "git-add-status-hook.py", "Bash",
         bash("git add agent.py"), None,
         lambda rc, o, e: ctx(o)[1] == "deny", "блок"),
        ("rules-why-guard: Bash у RULES.md", "PreToolUse", "rules-why-guard-hook.py", "Bash",
         bash("echo x >> RULES.md"), None,
         lambda rc, o, e: rc == 2 or ctx(o)[1] == "deny" or "RULES-WHY" in (o + e),
         "блок, якщо RULES-WHY.md не свіжий"),
        ("rules-why-guard: Edit іншого файлу", "PreToolUse", "rules-why-guard-hook.py",
         "Edit|Write|MultiEdit|NotebookEdit",
         {**base, "hook_event_name": "PreToolUse", "tool_name": "Edit",
          "tool_input": {"file_path": f"{tmp}/x.md", "old_string": "a", "new_string": "b"}}, None,
         lambda rc, o, e: rc == 0 and ctx(o)[1] != "deny", "пропускає"),
        ("verify-nudge: незахищений файл", "PreToolUse", "verify-nudge-hook.py",
         "Edit|Write|MultiEdit|NotebookEdit",
         {**base, "hook_event_name": "PreToolUse", "tool_name": "Write",
          "tool_input": {"file_path": f"{tmp}/x.md", "content": "x"}}, None,
         lambda rc, o, e: rc == 0 and not o.strip(), "тиша (журнал проби не чіпається)"),
        ("request-brief-reminder: Write", "PreToolUse", "request-brief-reminder-hook.py", "Edit|Write",
         {**base, "hook_event_name": "PreToolUse", "tool_name": "Write",
          "tool_input": {"file_path": f"{tmp}/x.md", "content": "x"}}, None,
         lambda rc, o, e: rc == 0 and ctx(o)[1] != "deny", "не блокує"),
        ("request-brief-reminder: Bash", "PreToolUse", "request-brief-reminder-hook.py", "Bash",
         bash("echo smoke"), None,
         lambda rc, o, e: rc == 0 and ctx(o)[1] != "deny", "не блокує"),
        ("глобальний Read", "PreToolUse", "node -e", "Read",
         {**base, "hook_event_name": "PreToolUse", "tool_name": "Read",
          "tool_input": {"file_path": f"{ROOT}/README.md"}}, None,
         lambda rc, o, e: rc == 0, "код 0"),
        ("глобальний Skill", "PreToolUse", "node -e", "Skill",
         {**base, "hook_event_name": "PreToolUse", "tool_name": "Skill",
          "tool_input": {"skill": "unlazy"}}, None,
         lambda rc, o, e: rc == 0, "код 0"),
        ("classify-task", "UserPromptSubmit", "classify-task.sh", None,
         {**base, "hook_event_name": "UserPromptSubmit", "prompt": "привіт"}, None,
         lambda rc, o, e: rc == 0, "код 0"),
    ]

    bad, rows = 0, []
    used = set()
    for name, ev, needle, mt, payload, env, ok, want in cases:
        if needle is None:  # бектест тіньового хука — без запису в його лог
            p = os.path.join(ROOT, ".claude", "hooks", "node-label-shadow-hook.py")
            r = subprocess.run([sys.executable, p, "--backtest", fake], capture_output=True, text=True)
            good = "усього розбіжностей: 1" in r.stdout
            used.add("node-label-shadow-hook.py")
            rows.append(("✅" if good else "❌", name, want, r.stdout.strip().splitlines()[-1:] or r.stderr[-200:]))
            bad += not good
            continue
        cmd = find(hs, ev, needle, mt)
        if not cmd:
            rows.append(("❌", name, want, "хук не знайдено в налаштуваннях"))
            bad += 1
            continue
        used.add(cmd)
        try:
            rc, o, e, dt = run(cmd, payload, env)
            good = ok(rc, o, e)
            note = f"код {rc}, {dt:.1f} с" + (f", stderr: {e.strip()[:120]}" if e.strip() and not good else "")
        except subprocess.TimeoutExpired:
            good, note = False, "ТАЙМАУТ"
        except Exception as ex:  # noqa — перевірка не має падати сама
            good, note = False, f"{type(ex).__name__}: {ex}"
        rows.append(("✅" if good else "❌", name, want, note))
        bad += not good

    # Решта: пропущені навмисно й ті, для яких випадку немає — лише «файл є і компілюється»
    for ev, mt, cmd in hs:
        if cmd in used or any(u in cmd for u in used if u.endswith(".py")):
            continue
        files = re.findall(r"(/\S+\.(?:py|sh|mjs|js))", cmd.replace("'", " "))
        why = next((v for k, v in SKIP.items() if k in cmd), "немає тест-випадку")
        state = "ok"
        for fpath in files:
            if not os.path.isfile(fpath):
                state = f"ФАЙЛУ НЕМАЄ: {fpath}"
            elif fpath.endswith(".py"):
                try:
                    py_compile.compile(fpath, doraise=True)
                except py_compile.PyCompileError as ex:
                    state = f"НЕ КОМПІЛЮЄТЬСЯ: {ex.msg[:80]}"
        mark = "⏭" if state == "ok" else "❌"
        bad += state != "ok"
        label = files[-1].split("/")[-1] if files else cmd[:40]
        rows.append((mark, f"{ev} {mt} {label}", f"не ганяється: {why}", state))

    for r in rows:
        print(f"{r[0]} {r[1]} — очікую: {r[2]} — {r[3]}")
    print(f"\nхуків у налаштуваннях: {len(hs)}; поломок: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
