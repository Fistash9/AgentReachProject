#!/usr/bin/env python3
"""Перевірка підключених хуків на відомих входах (Q9, 2026-10-06).

Навіщо: хуки fail-open (`except Exception: pass`) — зламаний хук мовчить, а
тести були лише на один хук (.claude/hooks/tests/, request-brief, 2026-09-23 —
їх запускаємо теж). «Не впав» тут нічого не доводить, тому кожен випадок
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
    with open(os.path.join(tmp, "ledger.jsonl"), "w", encoding="utf-8") as f:  # baton-guard: 18.10, #52
        for t, a, ev in (("2026-10-16T14:06:31Z", "claude-code", "pass"), ("2026-10-18T08:13:55Z", "claude-code", "pick_up"),
                         ("2026-10-18T08:20:09Z", "dsh", "pick_up")):
            f.write(json.dumps({"t": t, "agent": a, "event": ev, "pass": 52}) + "\n")
    with open(os.path.join(tmp, "baton-old.json"), "w", encoding="utf-8") as f:  # baton-guard: втрата #56→#57
        json.dump({"passCount": 56, "next": ["@claude-code a"],
                   "openQuestions": ["Розбіжність 486 vs 457 комітів у двох бектестах замка — не пояснено"]}, f)
    # baton-guard: same() 23.10 — короткий «тест» раніше «накривав» довгі пункти (10 зниклих → показано 9).
    # Відома відповідь: 10 викинуто → 10 названо; мутація до старої формули валить випадок (перевірено 23.10).
    old10 = [f"@claude-code {' '.join(w)}" for w in (
        "перевірити журнал подвійних підхоплень естафети після сварки агентів".split(),
        "оновити картку вузла пам'яті проєкту новими висновками сесії".split(),
        "звірити бектест замка комітів на двох різних історіях".split(),
        "прибрати старі знімки передач після рішення користувача щодо випалих".split(),
        "написати рецепт відновлення налаштувань локального сервера через резервну копію".split(),
        "дослідити причину повільного старту хуків на телефоні вранці".split(),
        "переглянути чергу відкритих рішень разом із другим агентом".split(),
        "порахувати витрати безкоштовної квоти делегата за минулий тиждень".split(),
        "скласти короткий план перевірки детектора хибних тривог і пропусків".split(),
        "додати приклад розбору відео для профілю каналу кулінарної ніші".split())]
    with open(os.path.join(tmp, "baton-old2.json"), "w", encoding="utf-8") as f:
        json.dump({"passCount": 70, "next": old10, "openQuestions": []}, f, ensure_ascii=False)
    with open(os.path.join(tmp, "baton-small.json"), "w", encoding="utf-8") as f:  # pick_up → HANDOFF-view
        json.dump({"task": "тест", "goal": "тест", "status": "тест", "handoffNote": "тест",
                   "next": ["@claude-code тест"], "openQuestions": [], "files": [], "done": [],
                   "watchOut": [], "passCount": 1}, f, ensure_ascii=False)
    open(os.path.join(tmp, "empty-ledger.jsonl"), "w").close()
    with open(os.path.join(tmp, "cost.jsonl"), "w", encoding="utf-8") as f:  # cost-nudge: $10.50
        f.write(json.dumps({"session_id": SID, "cost": 10.5, "pct": 25}) + "\n")
    base ={"session_id": SID, "cwd": ROOT, "transcript_path": fake}

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
        ("node-label-shadow наживо (тимч. лог)", "Stop", "node-label-shadow-hook.py", None,
         {**base, "hook_event_name": "Stop"}, {"NODE_LABEL_SHADOW_LOG": os.path.join(tmp, "shadow.jsonl")},
         lambda rc, o, e: rc == 0 and '"runs": 1' in open(os.path.join(tmp, "shadow.jsonl")).read()
         and '"T5"' in open(os.path.join(tmp, "shadow.jsonl")).read(),
         "рядок з runs і T5 у тимчасовому лозі (робочий не чіпається)"),
        ("unlazy Stop", "Stop", "stop-hook.mjs", None,
         {**base, "hook_event_name": "Stop", "stop_hook_active": True}, None,
         lambda rc, o, e: rc == 0, "код 0 при stop_hook_active"),
        ("pkgtruth: звичайна команда", "PreToolUse", "pkgtruth", "Bash", bash("echo smoke"), None,
         lambda rc, o, e: rc == 0 and ctx(o)[1] != "deny", "пропускає"),
        ("troubles-grep", "PreToolUse", "troubles-grep-hook.py", "Bash", bash("yt-dlp --version"), None,
         lambda rc, o, e: "TROUBLES.md має релевантні записи" in ctx(o)[0], "підказка з TROUBLES"),
        ("baton-reminder: не push", "PreToolUse", "baton-reminder-hook.py", "Bash", bash("echo smoke"), None,
         lambda rc, o, e: rc == 0 and not o.strip(), "тиша"),
        ("baton-guard: next без @власника", "PreToolUse", "baton-guard-hook.py", "mcp__baton__baton_pass",
         {**base, "hook_event_name": "PreToolUse", "tool_name": "mcp__baton__baton_pass",
          "tool_input": {"handoffNote": "x", "next": ["@claude-code a", "зробити b"]}}, None,
         lambda rc, o, e: ctx(o)[1] == "deny", "блок"),
        ("baton-guard: next з @власником", "PreToolUse", "baton-guard-hook.py", "mcp__baton__baton_pass",
         {**base, "hook_event_name": "PreToolUse", "tool_name": "mcp__baton__baton_pass",
          "tool_input": {"handoffNote": "x", "next": ["@claude-code a", "@dsh b"]}},
         {"BATON_GUARD_CURRENT": os.path.join(tmp, "немає.json")},
         lambda rc, o, e: rc == 0 and not o.strip(), "тиша"),
        ("baton-guard: втрата відкритого питання (#56→#57)", "PreToolUse", "baton-guard-hook.py", "mcp__baton__baton_pass",
         {**base, "hook_event_name": "PreToolUse", "tool_name": "mcp__baton__baton_pass",
          "tool_input": {"handoffNote": "x", "next": ["@claude-code a"], "openQuestions": []}},
         {"BATON_GUARD_CURRENT": os.path.join(tmp, "baton-old.json")},
         lambda rc, o, e: ctx(o)[1] == "deny" and "486 vs 457" in o, "deny зі списком (23.10: ask → deny)"),
        ("baton-guard: подвійний pick_up (журнал 18.10)", "PostToolUse", "baton-guard-hook.py",
         "mcp__baton__baton_pick_up",
         {**base, "hook_event_name": "PostToolUse", "tool_name": "mcp__baton__baton_pick_up"},
         {"BATON_GUARD_LEDGER": os.path.join(tmp, "ledger.jsonl")},
         lambda rc, o, e: "#52" in ctx(o)[0], "⚠ про #52"),
        ("baton-guard: 10 викинуто → 10 названо (same() 23.10)", "PreToolUse", "baton-guard-hook.py",
         "mcp__baton__baton_pass",
         {**base, "hook_event_name": "PreToolUse", "tool_name": "mcp__baton__baton_pass",
          "tool_input": {"handoffNote": "тест", "next": ["@claude-code тест"]}},
         {"BATON_GUARD_CURRENT": os.path.join(tmp, "baton-old2.json")},
         lambda rc, o, e: ctx(o)[1] == "deny" and "прибирає 10 пункт" in o, "deny, «прибирає 10 пункт»"),
        ("baton-guard: пункт переписано в handoffNote — тиша", "PreToolUse", "baton-guard-hook.py",
         "mcp__baton__baton_pass",
         {**base, "hook_event_name": "PreToolUse", "tool_name": "mcp__baton__baton_pass",
          "tool_input": {"handoffNote": f"відкинуто: {old10[-1]} — причина", "next": old10[:-1]}},
         {"BATON_GUARD_CURRENT": os.path.join(tmp, "baton-old2.json")},
         lambda rc, o, e: rc == 0 and not o.strip(), "тиша"),
        ("baton-guard: після pick_up — підказка стислого стану", "PostToolUse", "baton-guard-hook.py",
         "mcp__baton__baton_pick_up",
         {**base, "hook_event_name": "PostToolUse", "tool_name": "mcp__baton__baton_pick_up"},
         {"BATON_GUARD_LEDGER": os.path.join(tmp, "empty-ledger.jsonl"),
          "BATON_GUARD_CURRENT": os.path.join(tmp, "baton-small.json")},
         lambda rc, o, e: "Стислий стан естафети" in ctx(o)[0],
         "підказка (справжній .baton/HANDOFF-view.md відновлюється після прогону)"),
        ("cost-nudge: поріг $10 (тимч. журнал)", "UserPromptSubmit", "cost-nudge-hook.py", None,
         {**base, "hook_event_name": "UserPromptSubmit", "prompt": "тест"},
         {"COST_NUDGE_LOG": os.path.join(tmp, "cost.jsonl"), "COST_NUDGE_STATE": os.path.join(tmp, "cn.json")},
         lambda rc, o, e: "$10.50" in (json.loads(o).get("systemMessage", "") if o.strip() else ""),
         "systemMessage з ціною"),
        ("trash-md-guard: rm у проєкті", "PreToolUse", "trash-md-guard-hook.py", "Bash",
         bash(f"rm {ROOT}/hooks-smoke-не-існує.txt"), None,
         lambda rc, o, e: rc == 2 or ctx(o)[1] == "deny", "блок (TRASH.md не свіжий)"),
        ("trash-md-guard: rm у sh -c (proot)", "PreToolUse", "trash-md-guard-hook.py", "Bash",
         bash(f"proot-distro login ubuntu -- sh -c 'rm -rf {ROOT}/hooks-smoke-не-існує'"), None,
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
        ("git-add-status: agent.py у sh -c (proot)", "PreToolUse", "git-add-status-hook.py", "Bash",
         bash("proot-distro login ubuntu -- sh -c 'git add agent.py'"), None,
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
    # baton-guard після pick_up пише справжній .baton/HANDOFF-view.md (REPO зашитий у хуку) — зберегти й повернути
    hv = os.path.join(ROOT, ".baton", "HANDOFF-view.md")
    try:
        hv_saved = open(hv, "rb").read()
    except OSError:
        hv_saved = None
    for name, ev, needle, mt, payload, env, ok, want in cases:
        if os.environ.get("HOOKS_SMOKE_ONLY") and os.environ["HOOKS_SMOKE_ONLY"] not in name:
            continue  # прогін одного випадку (мутаційна перевірка)
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
    if hv_saved is not None:
        with open(hv, "wb") as f:
            f.write(hv_saved)
    elif os.path.exists(hv):
        os.remove(hv)  # до прогону файлу не було — створений тестом прибираємо
    if os.environ.get("HOOKS_SMOKE_ONLY"):
        for r in rows:
            print(f"{r[0]} {r[1]} — очікую: {r[2]} — {r[3]}")
        print(f"\nполомок: {bad}")
        return 1 if bad else 0

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

    # Наявні тести хуків (.claude/hooks/tests/*.mjs, 2026-09-23) — одна точка перевірки.
    tdir = os.path.join(ROOT, ".claude", "hooks", "tests")
    for t in sorted(os.listdir(tdir)) if os.path.isdir(tdir) else []:
        if t.endswith(".mjs"):
            r = subprocess.run(["node", os.path.join(tdir, t)], capture_output=True, text=True, cwd=ROOT)
            good = r.returncode == 0
            bad += not good
            rows.append(("✅" if good else "❌", f"тест {t}", "код 0",
                         f"код {r.returncode}" + ("" if good else f": {(r.stderr or r.stdout).strip()[:150]}")))

    # Сповіщення фонової задачі не ховає звірку (2026-10-18, TROUBLES «verify-nudge…»): функції без
    # побічних дій — verify-nudge verified_this_turn і ask-gate misses_for на штучному журналі
    # «людина → delegate → task-notification».
    nt = os.path.join(tmp, "notif.jsonl")
    with open(nt, "w", encoding="utf-8") as f:
        for d in ({"type": "user", "origin": {"kind": "human"}, "message": {"content": "зроби план"}},
                  {"type": "assistant", "message": {"content": [
                      {"type": "tool_use", "name": "mcp__delegate__delegate", "input": {}}]}},
                  {"type": "user", "origin": {"kind": "task-notification"},
                   "message": {"content": "<task-notification>done</task-notification>"}}):
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    try:
        import importlib.util

        def mod(name):
            s = importlib.util.spec_from_file_location(name.replace("-", "_"),
                                                       os.path.join(ROOT, ".claude", "hooks", name))
            m = importlib.util.module_from_spec(s)
            s.loader.exec_module(m)
            return m
        vn, gate, ag = mod("verify-nudge-hook.py"), mod("ask-gate-hook.py"), mod("answer-gate-shadow-hook.py")
        v_ok = vn.verified_this_turn(nt)[0]
        g_ok = "verify" not in gate.misses_for(
            ag, ag.current_turn_lines(nt, merge_notifications=True), "Внести правку?\nЧерга: x → y")
        good, note = v_ok and g_ok, f"verify-nudge бачить звірку: {v_ok}; ask-gate без вимоги звірки: {g_ok}"
    except Exception as ex:  # noqa — перевірка не має падати сама
        good, note = False, f"{type(ex).__name__}: {ex}"
    rows.append(("✅" if good else "❌", "звірка перед сповіщенням фонової задачі",
                 "видно обом хукам", note))
    bad += not good

    # git commit-msg «код вузла в коміті механізму» (2026-10-18): хук поза git — перевіряємо, що він є й
    # викликає скрипт, і ганяємо скрипт у тимчасовому репо (без вузла → 1, з Q12 → 0).
    try:
        gh = open(os.path.join(ROOT, ".git", "hooks", "commit-msg"), encoding="utf-8").read()
        repo = os.path.join(tmp, "cm-repo")
        os.makedirs(os.path.join(repo, "tools"))
        g = lambda *a: subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True)  # noqa: E731
        g("init", "-q")
        open(os.path.join(repo, "tools", "x.py"), "w").write("x\n")
        g("add", "tools/x.py")
        res = []
        for msg in ("fix: x", "fix: Q12 x"):
            mf = os.path.join(tmp, "cm-msg.txt")
            open(mf, "w", encoding="utf-8").write(msg + "\n")
            res.append(subprocess.run([sys.executable, os.path.join(ROOT, "tools", "commit-node-check.py"), mf],
                                      cwd=repo, capture_output=True, text=True).returncode)
        good = "commit-node-check.py" in gh and res == [1, 0]
        note = f"git-хук є: {'commit-node-check.py' in gh}; коди без вузла/з Q12: {res}"
    except Exception as ex:  # noqa — перевірка не має падати сама
        good, note = False, f"{type(ex).__name__}: {ex}"
    rows.append(("✅" if good else "❌", "git commit-msg: код вузла в коміті механізму",
                 "хук є; без вузла → 1, з Q12 → 0", note))
    bad += not good

    # Обхід git-хуків (2026-10-19, рецензія 1fe9acd7 п.17): --no-verify / -n / core.hooksPath → запит;
    # текст у -m, heredoc і grep — ні. Рядки складаються з частин, щоб замок не спрацював на сам тест.
    try:
        import importlib.util
        s = importlib.util.spec_from_file_location("ccons", os.path.join(ROOT, ".claude", "hooks",
                                                                           "commit-consent-hook.py"))
        cc = importlib.util.module_from_spec(s)
        s.loader.exec_module(cc)
        G, NV = "git " + "commit", "--no-" + "verify"
        cases = [(f"{G} {NV} -m x", True), (f"{G} -qnm x", True), ("git -c core.hooksPath=/x " + "commit -m x", True),
                 (f"{G} -m 'про {NV}'", False), (f"grep -n '{G}' f", False), (f"{G} -am x", False)]
        res = [cc.bypass(c) == want for c, want in cases]
        good, note = all(res), f"{sum(res)}/{len(res)} випадків"
    except Exception as ex:  # noqa — перевірка не має падати сама
        good, note = False, f"{type(ex).__name__}: {ex}"
    rows.append(("✅" if good else "❌", "commit-consent: обхід git-хуків", "--no-verify/-n/hooksPath → так; текст → ні",
                 note))
    bad += not good

    # М2 (2026-10-19): варіант агента «…і закомітити» на питання НЕ про коміт — не дозвіл; на питання про
    # коміт «так»/варіант з «коміт» — дозвіл; власні слова користувача з «коміт» — дозвіл.
    try:
        A = lambda q, a: f'Your questions have been answered: "{q}"="{a}". You can now continue.'  # noqa: E731
        cases = [(A("Внести правку?", "Так, внести і закомітити"), ("Так, внести і закомітити", "Ні"), False),
                 (A("Закомітити X?", "Так, коміт"), ("Так, коміт", "Ні"), True),
                 (A("Закомітити?", "Поки без коміту"), ("Так, коміт", "Поки без коміту"), False),
                 (A("Що робимо?", "Інше, і коміть усе"), ("Інше",), True),
                 ("так, коміт", (), True)]
        res = [cc.consent(t, lb) == want for t, lb, want in cases]
        good, note = all(res), f"{sum(res)}/{len(res)} випадків"
    except Exception as ex:  # noqa — перевірка не має падати сама
        good, note = False, f"{type(ex).__name__}: {ex}"
    rows.append(("✅" if good else "❌", "commit-consent: М2 дозвіл на коміт", "варіант агента ≠ дозвіл", note))
    bad += not good

    # Шифри в тексті користувачу (2026-10-19, «знов шифри тільки замітив»): хеш у лапках-коді й кирилична «М2» —
    # ловляться; хеш у дужках після опису, шлях/файл з хешем — ні.
    try:
        import importlib.util
        s = importlib.util.spec_from_file_location("pcodes", os.path.join(ROOT, "tools", "plain-codes.py"))
        pcm = importlib.util.module_from_spec(s)
        s.loader.exec_module(pcm)
        cases = [("віддалений main = `45d5e0e`", ["45d5e0e"]), ("М2 внесено.", ["М2"]),
                 ("Замок на обхід (b66adbf) запушено.", []), ("файл 1f94aac.py тут", [])]
        res = [pcm.undecoded(t) == want for t, want in cases]
        # strict (2026-10-20, питання у віконцях): код у дужках після назви — теж ловиться; шлях і хеш з описом — ні
        sc = [("коротший старт естафети (M14) → перевірка", ["M14"]), ("див. trees/pam-yat-proyektu.md:167", []),
              ("Замок на обхід (b66adbf) запушено.", []), ("віддалений main = `45d5e0e`", ["45d5e0e"])]
        res += [pcm.strict(t) == want for t, want in sc]
        good, note = all(res), f"{sum(res)}/{len(res)} випадків"
    except Exception as ex:  # noqa — перевірка не має падати сама
        good, note = False, f"{type(ex).__name__}: {ex}"
    rows.append(("✅" if good else "❌", "plain-codes: хеші й «М» без назви", "шифр → ловиться; з описом → ні", note))
    bad += not good

    # «DSH насправді» (проба з 2026-10-19): рядок з екрана 18.10 (тести мода agents-status) → обидва ⚠;
    # без списку задач — тиша.
    try:
        import importlib.util
        s = importlib.util.spec_from_file_location("tfh", os.path.join(ROOT, ".claude", "hooks", "tree-focus-hook.py"))
        tf = importlib.util.module_from_spec(s)
        s.loader.exec_module(tf)
        scr = "│   4 │ ☑  │ Чернетка патчу │\n│   5 │ ◐  │ Чекаю явного «так» на verify-nudge │\n"
        res = [tf.parse_dsh(scr, ["T7"])[1] == ["mismatch", "waiting"], tf.parse_dsh("dsh ▸\n", ["T7"])[0] is None]
        good, note = all(res), f"{sum(res)}/{len(res)} випадків"
    except Exception as ex:  # noqa — перевірка не має падати сама
        good, note = False, f"{type(ex).__name__}: {ex}"
    rows.append(("✅" if good else "❌", "tree-focus: «DSH насправді»", "екран 18.10 → обидва ⚠; без списку — тиша", note))
    bad += not good

    # Голос на проігноровані підказки edit-gate (2026-10-19): без дії → nudge:read; з повним Read → тиша.
    try:
        import importlib.util
        s = importlib.util.spec_from_file_location("agv", os.path.join(ROOT, ".claude", "hooks", "answer-gate-shadow-hook.py"))
        agv = importlib.util.module_from_spec(s)
        s.loader.exec_module(agv)
        hint = ("hint", "Ворота «перед правкою» (tools/x.py): файл не прочитано повністю (Read без offset/limit або cat).")
        rd = ("tool", "Read", {"file_path": ROOT + "/tools/x.py"})
        res = [agv.egate_misses({"events": [hint]}, "готово") == ["nudge:read:tools/x.py"],
               agv.egate_misses({"events": [hint, rd]}, "готово") == [],
               agv.egate_misses({"events": [hint]}, "x.py: не дочитував, бо правка в коментарі") == []]
        good, note = all(res), f"{sum(res)}/{len(res)} випадків"
    except Exception as ex:  # noqa — перевірка не має падати сама
        good, note = False, f"{type(ex).__name__}: {ex}"
    rows.append(("✅" if good else "❌", "answer-gate: голос на підказки edit-gate", "без дії → голос; Read/причина → ні", note))
    bad += not good

    # Голос «питання без кнопок» (2026-10-20): «?» у кінці без AskUserQuestion → ask; з віконцем чи без «?» → ні.
    try:
        t = lambda txt, tools: {"texts": [txt], "tools": tools, "hints": [], "events": []}  # noqa
        res = ["ask" in agv.check(t("Черга: x → y. Почати з першого?", [])),
               "ask" not in agv.check(t("Черга: x → y. Почати з першого?", [("AskUserQuestion", "")])),
               "ask" not in agv.check(t("Черга: x → y. Готово.", [])),
               "ask-req" in agv.check(t("Черга: x → y. Скажіть, якщо пушити.", [])),
               "ask-req" not in agv.check(t("Черга: x → y. Ваше рішення — у наступній сесії.", []))]
        good, note = all(res), f"{sum(res)}/{len(res)} випадків"
    except Exception as ex:  # noqa — перевірка не має падати сама
        good, note = False, f"{type(ex).__name__}: {ex}"
    rows.append(("✅" if good else "❌", "answer-gate: голос «питання без кнопок»", "«?» без віконця → ask; інакше → ні", note))
    bad += not good

    # edit-gate: mv/rm у теці знімків естафети → ask зі списком читачів; інший mv — ні (2026-10-19). Рядки з частин.
    try:
        import importlib.util
        s = importlib.util.spec_from_file_location("egh", os.path.join(ROOT, ".claude", "hooks", "edit-gate-hook.py"))
        eg = importlib.util.module_from_spec(s)
        s.loader.exec_module(eg)
        HIS = ".baton/" + "history/"
        ask = lambda c: any(k.startswith("ask-history") for k, _ in eg.check("Bash", {"command": c}, eg.Evidence()))  # noqa
        res = [ask("m" + "v " + HIS + "pass-$i.json .trash/x/"), not ask("m" + "v tools/x.py tools/y.py"),
               "tools/baton-diff.py" in eg.history_readers()]
        good, note = all(res), f"{sum(res)}/{len(res)} випадків"
    except Exception as ex:  # noqa — перевірка не має падати сама
        good, note = False, f"{type(ex).__name__}: {ex}"
    rows.append(("✅" if good else "❌", "edit-gate: mv знімків естафети → ask", "знімок → ask; інше → ні; читачі", note))
    bad += not good

    # Маска експорту сесії (2026-10-18): «task-notification» — не ключ; sk-/nvapi- — ключі.
    try:
        import importlib.util
        s = importlib.util.spec_from_file_location("sexp", os.path.join(ROOT, "tools", "session-export.py"))
        se = importlib.util.module_from_spec(s)
        s.loader.exec_module(se)
        txt = ("<task-notification_abcdefghijklmnopqrst> sk-" + "A1b2C3d4E5f6G7h8I9j0"
               + " nvapi-" + "Z9y8X7w6V5u4T3s2R1q0")
        for rx, rep in se.REDACT:
            txt = rx.sub(rep, txt)
        good = "task-notification_abcdefghijklmnopqrst" in txt and txt.count("[ключ]") == 2
        note = txt[:120]
    except Exception as ex:  # noqa — перевірка не має падати сама
        good, note = False, f"{type(ex).__name__}: {ex}"
    rows.append(("✅" if good else "❌", "session-export: маска ключів",
                 "task-notification цілий; sk-/nvapi- → [ключ]", note))
    bad += not good

    for r in rows:
        print(f"{r[0]} {r[1]} — очікую: {r[2]} — {r[3]}")
    print(f"\nхуків у налаштуваннях: {len(hs)}; поломок: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
