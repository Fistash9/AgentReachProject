"""Перевірки focus-v2 (27.10): оригінал / prep-копія / нова копія — у процесі, DSH_LOG → tmp.
Пам'ять проєкту › M3 Легкий стан › хук фокусу: варіант «2 за роботою + 1 сталий».
Нічого не пише в проєкт; вивід — stdout (перенаправляється у check-out.txt)."""
import contextlib, importlib.util, io, json, os, re, sys
ROOT = "/data/data/com.termux/files/home/AgentReachProject"
HERE = os.path.dirname(os.path.abspath(__file__))
TMP = "/data/data/com.termux/files/usr/tmp/focus-v2-dsh.jsonl"
ENV = "TREE_FOCUS_MSG_LESSON"


def load(path, name):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m); m.DSH_LOG = TMP; return m


V = {"оригінал": load(os.path.join(ROOT, ".claude/hooks/tree-focus-hook.py"), "orig"),
     "prep": load(os.path.join(ROOT, "agents/claude-code/prep-2026-10-27/focus/tree-focus-hook.py"), "prep"),
     "v2": load(os.path.join(HERE, "tree-focus-hook.py"), "v2")}


def run(m, inp, env1=False):
    os.environ.pop(ENV, None)
    if env1:
        os.environ[ENV] = "1"
    sys.stdin = io.StringIO(json.dumps(inp, ensure_ascii=False)); buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        m.main()
    os.environ.pop(ENV, None)
    o = buf.getvalue().strip()
    return json.loads(o)["hookSpecificOutput"]["additionalContext"] if o else ""


def howto(ctx):
    i = ctx.find("Як застосовувати")
    return ctx[i:] if i != -1 else ""


def rules(sec):
    return re.findall(r"^• (\S+) — ", sec, re.M)


base = {"session_id": "test", "cwd": ROOT, "transcript_path": ""}
P5 = ("зроби в агентах ключове те що може знов затертись ,або відкластись , зараз мені подобається "
      "навіть дерево яке ти видав і те як логічно і зрозуміло все написано ,для мене зараз все "
      "зрозуміло і мені від цього радісно")
fails = []


def check(cond, what):
    print(("✅ " if cond else "❌ ") + what)
    if not cond:
        fails.append(what)


print("== 1. SessionStart ==")
st = {}
for k, m in V.items():
    c = run(m, {**base, "hook_event_name": "SessionStart"})
    st[k] = c
    sec = howto(c)
    print(f"{k}: весь вивід {len(c)} симв.; «Як застосовувати» {len(sec)}; заголовок: {sec.splitlines()[0] if sec else '—'}")
    print(f"   уроки: {', '.join(rules(sec))}")
r2 = rules(howto(st["v2"]))
check(len(r2) == 3 and len(set(r2)) == 3, "v2: рівно 3 уроки, без дублів")
check(any(n in V["v2"].HOWTO_RULES for n in r2), "v2: є сталий урок із HOWTO_RULES")
check("fix-root-cause-of-every-bug" in r2 or r2[2] in V["v2"].HOWTO_RULES, "v2: третє місце — сталий")
check("trees-index" in st["v2"] and "Як застосовувати" in st["v2"], "v2: hooks-smoke «tree-focus старт» (Як застосовувати + trees-index)")
# частина до «Як застосовувати» — однакова з оригіналом (решту поведінки не чіпали)
check(st["v2"].split("Як застосовувати")[0] == st["оригінал"].split("Як застосовувати")[0],
      "v2: старт до секції «Як застосовувати» = оригінал")

print("\n== 2. UserPromptSubmit «тест» ==")
t = {k: run(m, {**base, "hook_event_name": "UserPromptSubmit", "prompt": "тест"}) for k, m in V.items()}
t["v2+env"] = run(V["v2"], {**base, "hook_event_name": "UserPromptSubmit", "prompt": "тест"}, env1=True)
for k, c in t.items():
    print(f"{k}: {len(c)} симв.")
check(len(t["v2"]) < 600 and ("В роботі" in t["v2"] or "Жоден" in t["v2"]), "v2: hooks-smoke «tree-focus повідомлення» (<600)")
check(t["v2"] == t["оригінал"], "v2 без змінної: «тест» = оригінал")
check(t["v2+env"] == t["оригінал"], "v2 з =1: «тест» = оригінал (уроку на «тест» нема)")

print("\n== 3. Повідомлення №5 (бектест REPORT prep) ==")
p = {k: run(m, {**base, "hook_event_name": "UserPromptSubmit", "prompt": P5}) for k, m in V.items()}
p["v2+env"] = run(V["v2"], {**base, "hook_event_name": "UserPromptSubmit", "prompt": P5}, env1=True)
os.environ[ENV] = "0"
p["v2 env=0"] = run(V["v2"], {**base, "hook_event_name": "UserPromptSubmit", "prompt": P5})
for k, c in p.items():
    les = [l for l in c.splitlines() if l.startswith("Урок до повідомлення:")]
    print(f"{k}: {len(c)} симв.; урок: {les[0][:80] + '…' if les else '—'}")
check(p["v2"] == p["оригінал"], "v2 без змінної: №5 = оригінал")
check(p["v2 env=0"] == p["оригінал"], "v2 з =0: №5 = оригінал")
check("Урок до повідомлення: reports-as-live-tree" in p["v2+env"], "v2 з =1: урок reports-as-live-tree на №5")
check(p["v2+env"] == p["prep"], "v2 з =1: №5 = prep-копія")

print("\n== 4. Межові випадки вибору (rank_rules підмінено) ==")
m = V["v2"]; real = m.rank_rules; mem = m.mem_howto()
others = [n for n in sorted(mem) if n not in m.HOWTO_RULES][:4]
H = list(m.HOWTO_RULES)
cases = {"0 за роботою": [], "1": others[:1], "2": others[:2], "4": others[:4],
         "сталий №1 серед перших 2": [H[0], others[0], others[1]],
         "два сталих серед перших 2": [H[0], H[1], others[0]],
         "сталий на 3-му місці": [others[0], others[1], H[0]]}
for nm, lst in cases.items():
    m.rank_rules = lambda q, mm, lst=lst: [(9.0, n, ["x"]) for n in lst]
    got = rules(m.howto_section("будь-що"))
    head = m.howto_section("будь-що").splitlines()[0]
    ok = (len(got) == 3 and len(set(got)) == 3 and got[:min(2, len(lst))] == lst[:2]
          and any(g in H and g not in lst[:2] for g in got))
    check(ok, f"{nm}: {got} | {head}")
m.rank_rules = real
check(rules(m.howto_section("")) == H, "query '' → три сталі HOWTO_RULES (як prep)")

print("\n== 5. hooks-smoke «tree-focus: DSH насправді» на копії ==")
scr = "│   4 │ ☑  │ Чернетка патчу │\n│   5 │ ◐  │ Чекаю явного «так» на verify-nudge │\n"
res = [m.parse_dsh(scr, ["T7"])[1] == ["mismatch", "waiting"], m.parse_dsh("dsh ▸\n", ["T7"])[0] is None]
check(all(res), f"DSH насправді: {sum(res)}/{len(res)} випадків")

print(f"\nПОЛОМОК: {len(fails)}")
