#!/data/data/com.termux/files/usr/bin/python3
"""PreToolUse-хук (НЕ блокує): ворота 3 «перед правкою» (M11.3) + «Паспорт задачі».

Навіщо: сесія e3a33280 (trees/pam-yat-proyektu.md, M11 «evidence 2026-10-12»): план правки
tools/deepseek-search.py — без повного читання й без пошуку залежних (скіл deepseek-search
читає скрипт); знімки baton перенесено mv без пошуку читачів (їх читають 3 скрипти).
Правило є (RULES.md «Перед зміною того, як ми використовуємо…»: «Grep не замінює читання»),
але в момент дії не спрацьовує. verify-nudge-hook.py покриває лише захищені файли й
нагадує про звірку плану, а не про читання; trash-md-guard — лише rm і TRASH.md.

Три нагадування (кожне — раз на ключ за сесію, лише коли доказу в журналі немає):
  read   — Edit/Write наявного файлу в tools/, .claude/hooks/, .claude/skills/ без повного
           Read (без offset/limit) чи `cat` у журналі сесії, або без grep за його назвою.
  movers — Bash mv/rm файлу проєкту (не tmp, не .trash/) без grep за його назвою.
  passport — Edit/Write у trees/*.md додає новий вузол «- [ ] ID», а в доданому тексті
           немає «ціль:» / «звідки:» / «зв'язки:» / «UP:».
  siblings — правка хука .claude/hooks/X.py: перелік сусідніх хуків на ту саму подію (з
           settings.local.json) і рядків, де вони читають вхід (last_assistant_message,
           transcript_path, tool_input…). Ключ — хук + день. (2026-10-13: голос черги хибно
           спрацював, бо читав transcript_path, хоча number-claim-shadow-hook:358 уже брав
           last_assistant_message; 23.09 shlex-фікс двох хуків не дійшов до третього.)
  agents — (2026-10-25, рішення «Обидві частини»; користувач уп'яте: «знов не користуєшся агентами?») у
           ПОТОЧНОМУ ході (від справжнього повідомлення людини; iter_turns з answer-gate) n читань і жодного
           Agent/Task → на 15, 30, 45… permissionDecision "deny" (≤2 рядки). Повтор після deny — пропуск (ключ
           «agents\t<хід>\t<n//15>» у LOG); «без агента: <причина>» у description — пропуск. Мовчить: DeepSeek
           (ANTHROPIC_BASE_URL), під-агент (agent_id), не-UUID session_id. Вимикач: EDIT_GATE_AGENTS=0.
           Read/Grep/Glob ворота бачать, лише якщо matcher у settings їх містить (зараз Edit|Write|MultiEdit|Bash).
Bash-правки (2026-10-13): python open(…,"w"), sed -i, > / >>, tee, cp у файл коду — теж
правка (до того ворота їх не бачили: за 12–13.10 лише 3 спрацювання, хоча правок було багато).
Лог: .claude/logs/edit-gate.log (сесія, ключ, час) — для підрахунку марних спрацювань.
Бектест: python3 <цей файл> --backtest <jsonl>. Будь-яка помилка — мовчки (fail-open).
"""
import json
import os
import re
import shlex
import sys
import time

PROJECT = "/data/data/com.termux/files/home/AgentReachProject"
LOG = os.environ.get("EDIT_GATE_LOG") or os.path.join(PROJECT, ".claude", "logs", "edit-gate.log")
READ_TOOLS = {"Read", "Grep", "Glob"}
AGENTS_REASON = ("Ворота «агенти»: у ході {n} читань і жодного Agent. Віддай обмежену частину під-агенту або повтори "
                 "виклик, додавши в description «без агента: <причина>».")
EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
CODE_DIRS = ("tools/", ".claude/hooks/", ".claude/skills/")
SAFE_PREFIXES = ("/data/data/com.termux/files/usr/tmp/", "/tmp/")
RE_NODE = re.compile(r"^\s*- \[ \] [A-Z]+\d[\w.]*\s", re.M)
RE_PASSPORT = re.compile(r"ціль:|звідки:|зв['’]яз\w*:|\bUP:", re.I)
RE_CODEPATH = re.compile(r"((?:tools|\.claude/hooks|\.claude/skills)/[\w./-]+\.(?:py|sh|md|mjs|json))")
INPUT_FIELDS = re.compile(r"last_assistant_message|transcript_path|stop_hook_active|tool_input|"
                          r"tool_name|session_id|hook_event_name|\"prompt\"")
SETTINGS = os.path.join(PROJECT, ".claude", "settings.local.json")
RE_MOVER = re.compile(r"(?:^|[;&|(]\s*|\bthen\s+|\bdo\s+)(mv|rm)\s+([^;&|\n]+)", re.M)
# 2026-10-19 (5-й випадок класу «mv знімків baton до пошуку читачів», TROUBLES; рішення «Так, роби»): mv/rm у
# .baton/history/ — ask зі списком читачів, а не підказка. Підказка приходила в тій самій команді — запізно;
# grep за stem («pass-$i») не ловив. Із 10 підказок movers з 12.10 знімків стосувалась 1 — решта лишаються підказками.
HISTORY = ".baton/" + "history/"
RE_HISTORY = re.compile(r"\.baton/history|[\"']\.baton[\"']\s*,\s*[\"']history[\"']")


def history_readers():
    """Файли tools/, .claude/hooks/, .claude/skills/, що згадують теку знімків (крім цього хука)."""
    out, me = [], os.path.abspath(__file__)
    for d in CODE_DIRS:
        for root, _, files in os.walk(os.path.join(PROJECT, d)):
            for fn in files:
                p = os.path.join(root, fn)
                if p == me or "__pycache__" in p or not fn.endswith((".py", ".md", ".sh", ".mjs")):
                    continue
                try:
                    # і os.path.join(…, ".baton", "history", …) — так читає tools/achieved-map.py (рецензія 19.10, п.15)
                    if RE_HISTORY.search(open(p, encoding="utf-8", errors="ignore").read()):
                        out.append(rel(p))
                except OSError:
                    pass
    return sorted(out)


def rel(path, cwd=None):
    if not path:
        return None
    path = os.path.expanduser(path)
    if not os.path.isabs(path):
        path = os.path.join(cwd or PROJECT, path)
    path = os.path.normpath(path)
    if not path.startswith(PROJECT + os.sep):
        return None
    return path[len(PROJECT) + 1:]


def stem(r):
    b = os.path.basename(r)
    return os.path.splitext(b)[0] or b


class Evidence:
    """Що агент уже зробив у сесії: повні читання, grep-и, записи файлів."""

    def __init__(self):
        self.full_read, self.written, self.greps = set(), set(), []

    def add(self, name, inp):
        inp = inp or {}
        if name == "Read":
            r = rel(inp.get("file_path"))
            if r and not inp.get("offset") and not inp.get("limit"):
                self.full_read.add(r)
        elif name in EDIT_TOOLS:
            r = rel(inp.get("file_path"))
            if r and name == "Write":
                self.written.add(r)
        elif name == "Grep":
            self.greps.append(str(inp.get("pattern", "")))
        elif name == "Bash":
            cmd = str(inp.get("command", ""))
            if re.search(r"\b(grep|rg)\b", cmd):
                self.greps.append(cmd)
            for m in re.finditer(r"\bcat\s+(?:-\w+\s+)*([^\s|;&>-][^\s|;&>]*)", cmd):  # cat -n теж (13.10)
                r = rel(m.group(1))
                if r:
                    self.full_read.add(r)

    def grepped(self, r):
        s = stem(r)
        return any(s in g for g in self.greps)


RE_HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n(.*?)\n\1\b", re.S)
RE_PYASSIGN = re.compile(r"""(\w+)\s*=\s*['"]([^'"]+)['"]""")


def bash_written(cmd, cwd=None):
    """Файли коду, які Bash-команда справді записує (2026-10-13, v2: ціль — у тій самій
    частині команди; v1 плутала `sed -i trees/…; grep tools/x.py` із правкою tools/x.py)."""
    found = []

    def add(path):
        r = rel(path, cwd)
        if (r and r.startswith(CODE_DIRS) and r not in found and "/tests/" not in r
                and "__pycache__" not in r):
            found.append(r)
    # python-вставки: лише шлях, який відкривається на запис (прямо чи через змінну)
    for m in RE_HEREDOC.finditer(cmd):
        body = m.group(2)
        vars_ = dict(RE_PYASSIGN.findall(body))
        for w in re.finditer(r"open\(\s*([^,)]+)\s*,\s*['\"][wa]", body):
            arg = w.group(1).strip()
            path = arg.strip("'\"") if arg[:1] in "'\"" else vars_.get(arg)
            if path:
                add(path)
        for w in re.finditer(r"(\w+)\.write_text\(", body):
            if w.group(1) in vars_:
                add(vars_[w.group(1)])
    rest = RE_HEREDOC.sub(" ", cmd)
    for seg in re.split(r"&&|\|\||[;|\n]", rest):
        seg = seg.strip()
        if re.match(r"(?:sudo\s+)?sed\s+(?:-\w*\s+)*-i", seg) or re.match(r"sed\s+-i", seg):
            for c in RE_CODEPATH.findall(seg):
                add(c)
        for m in re.finditer(r"(?<![<>&\d])>>?\s*([^\s;&|]+)", seg):
            add(m.group(1))
        m = re.match(r"tee\s+(?:-a\s+)?([^\s;&|]+)", seg)
        if m:
            add(m.group(1))
        m = re.match(r"cp\s+(?:-\w+\s+)*\S+\s+([^\s;&|]+)$", seg)
        if m:
            add(m.group(1))
    return found


def hook_events():
    """{файл хука: [події]} з settings.local.json — робоче джерело реєстрації."""
    try:
        d = json.load(open(SETTINGS, encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    out = {}
    for ev_name, arr in (d.get("hooks") or {}).items():
        for a in arr or []:
            for h in a.get("hooks") or []:
                m = re.search(r"\.claude/hooks/([\w.-]+\.py)", str(h.get("command", "")))
                if m:
                    out.setdefault(m.group(1), []).append(ev_name)
    return out


def siblings_msg(r):
    """Текст: сусіди на ту саму подію і де вони читають вхід."""
    hook = os.path.basename(r)
    evs = hook_events()
    mine = evs.get(hook)
    if not mine:
        return None
    lines = []
    for other, oe in sorted(evs.items()):
        common = sorted(set(oe) & set(mine))
        if other == hook or not common:
            continue
        refs = []
        try:
            for i, l in enumerate(open(os.path.join(PROJECT, ".claude", "hooks", other),
                                       encoding="utf-8", errors="ignore"), 1):
                f = sorted(set(INPUT_FIELDS.findall(l)))
                if f and not l.lstrip().startswith("#"):
                    refs.append(f"{i}:{'/'.join(f)}")
        except OSError:
            continue
        lines.append(f"{other} [{','.join(common)}] " + (" ".join(refs[:4]) or "—"))
    if not lines:
        return None
    return (f"Сусіди {hook} на {','.join(mine)} — як вони читають вхід (перевір, чи вже не "
            "розв'язано те, що робиш): " + "; ".join(lines[:6]))


def check(name, inp, ev, cwd=None, exists=None, day=None):
    """[(ключ, текст нагадування)] для одного виклику інструмента."""
    out = []
    inp = inp or {}
    day = day or time.strftime("%Y-%m-%d")
    targets = []
    if name in EDIT_TOOLS:
        r = rel(inp.get("file_path"), cwd)
        if r:
            targets.append(r)
    elif name == "Bash":
        # лише наявні файли: створення нового — не правка (і шлях із тексту коментаря — не ціль)
        targets = [t for t in bash_written(str(inp.get("command", "")), cwd)
                   if exists is None and os.path.exists(os.path.join(PROJECT, t))
                   or exists is not None and t not in ev.written]
    for r in targets:
        if r.startswith(".claude/hooks/") and r.endswith(".py") and not (name == "Write" and not (
                exists if exists is not None else os.path.exists(os.path.join(PROJECT, r)))):
            msg = siblings_msg(r)
            if msg:
                out.append((f"siblings\t{r}\t{day}", msg))
        if name == "Bash" and r.startswith(CODE_DIRS) and r not in ev.written:
            miss = []
            if r not in ev.full_read:
                miss.append("файл не прочитано повністю (Read без offset/limit або cat)")
            if not ev.grepped(r):
                miss.append(f"залежних не шукано (grep -rn {stem(r)} tools .claude *.md)")
            if miss:
                out.append((f"read\t{r}", f"Ворота «перед правкою» ({r}, правка через Bash): "
                            + "; ".join(miss) + ". RULES.md «Перед зміною того, як ми "
                            "використовуємо…»: «Grep не замінює читання»."))
    if name in EDIT_TOOLS:
        r = rel(inp.get("file_path"), cwd)
        if not r:
            return out
        if exists is None:
            exists = os.path.exists(os.path.join(PROJECT, r))
        if r.startswith(CODE_DIRS) and exists and r not in ev.written:
            miss = []
            if r not in ev.full_read:
                miss.append("файл не прочитано повністю (Read без offset/limit або cat)")
            if not ev.grepped(r):
                miss.append(f"залежних не шукано (grep -rn {stem(r)} tools .claude *.md)")
            if miss:
                out.append((f"read\t{r}", f"Ворота «перед правкою» ({r}): " + "; ".join(miss)
                            + ". RULES.md «Перед зміною того, як ми використовуємо…»: "
                            "«Grep не замінює читання»."))
        if r.startswith("trees/") and r.endswith(".md"):
            new = inp.get("new_string") if name == "Edit" else inp.get("content")
            old = inp.get("old_string", "") if name == "Edit" else ""
            new, old = str(new or ""), str(old or "")
            added = len(RE_NODE.findall(new)) - len(RE_NODE.findall(old))
            if added > 0 and not RE_PASSPORT.search(new):
                out.append((f"passport\t{r}\t{len(new)}",
                            f"Паспорт задачі ({r}): новий вузол без рядків «ціль:» · «звідки:» · "
                            "«зв'язки:» (або UP:) — допиши, звідки запит і чому служить "
                            "(RULES.md «Формат взаємодії», пам'ять every-action-needs-project-goal)."))
    elif name == "Bash":
        cmd = str(inp.get("command", ""))
        for m in RE_MOVER.finditer(cmd):
            op = m.group(1)
            try:
                args = [a for a in shlex.split(m.group(2)) if not a.startswith("-")]
            except ValueError:
                continue
            if op == "mv" and len(args) > 1:
                args = args[:-1]
            for a in args:
                if a.startswith(SAFE_PREFIXES):
                    continue
                r = rel(a, cwd)
                if r and r.startswith(HISTORY):  # ask, не підказка — і без огляду на grep (див. history_readers)
                    out.append((f"ask-history\t{r}", f"{op} {r} — знімок естафети. Читачі "
                                f"{HISTORY}: {', '.join(history_readers()) or 'не знайдено'}. Перевір, що "
                                "перенесення їх не зламає (baton-diff порівнює сусідні знімки), і запис у TRASH.md до дії."))
                    continue
                if not r or r.startswith(".trash/") or ev.grepped(r):
                    continue
                out.append((f"movers\t{r}", f"Перед {op} {r}: хто його читає? "
                            f"grep -rn {stem(r)} tools .claude *.md — до перенесення "
                            "(випадок 12.10: знімки baton читають 3 скрипти)."))
    return out


def iter_tool_uses(path):
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if not isinstance(d, dict) or d.get("type") != "assistant":
                continue
            for x in (d.get("message") or {}).get("content") or []:
                if isinstance(x, dict) and x.get("type") == "tool_use":
                    yield d.get("timestamp", ""), x.get("name", ""), x.get("input") or {}


def seen_keys(sid):
    if not os.path.exists(LOG):
        return set()
    out = set()
    with open(LOG, encoding="utf-8", errors="ignore") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if p and p[0] == sid:
                out.add("\t".join(p[1:-1]))
    return out


def answer_gate():
    """Модуль answer-gate-shadow-hook.py поруч: iter_turns/current_turn_lines (межі ходу) і count_reads."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "agv", os.path.join(os.path.dirname(os.path.abspath(__file__)), "answer-gate-shadow-hook.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def agents_check(data, agv=None):
    """(ключ, n) — якщо цей виклик треба зупинити воротами «агенти», інакше None."""
    if os.environ.get("EDIT_GATE_AGENTS") == "0" or data.get("agent_id"):
        return None
    if "deepseek" in os.environ.get("ANTHROPIC_BASE_URL", ""):
        return None
    name, inp = data.get("tool_name", ""), data.get("tool_input") or {}
    if "без агента:" in str(inp.get("description", "")):
        return None
    tp = data.get("transcript_path")
    if not (isinstance(tp, str) and os.path.isfile(tp)):
        return None
    agv = agv or answer_gate()
    if agv.is_test_session(data.get("session_id")):
        return None
    # сповіщення фонових задач хід не відкривають — лише повідомлення людини
    turns = list(agv.iter_turns(agv.current_turn_lines(tp, merge_notifications=True), merge_notifications=True))
    if not turns or not turns[-1].get("user"):
        return None
    ev = turns[-1]["events"]
    tools = [e for e in ev if e and e[0] == "tool"]
    if tools and tools[-1][1] == name and tools[-1][2] == inp:  # поточний виклик уже може бути в журналі
        ev = [e for e in ev if e is not tools[-1]]
    reads, agent = agv.count_reads(ev)
    n = reads + (1 if agv.is_read(name, inp) else 0)
    if agent or n < agv.AGENTS_N or not agv.is_read(name, inp):
        return None
    return f"agents\t{turns[-1]['ts']}\t{n // agv.AGENTS_N}", n


# ======== Ворота «агенти» v2 (2026-10-27; КОПІЯ в agents/claude-code/gate-v2-2026-10-27/, у .claude/ не перенесено) ========
# Від центру (GOALS.md:11–13 «агент вищого порядку розподіляє задачі»): міряти не «читання в ході», а «роблю сам» —
# власну роботу оркестратора від останньої роздачі задачі. Прапорці (env EDIT_GATE_V2_<X>=0/1), щоб міряти поодинці й разом:
#   A  одиниці роботи: Bash/Read/Grep/Glob/Edit/Write/MultiEdit (а не лише читання); deny на будь-якій з них
#   S  лічильник через усю сесію від останньої роздачі (повідомлення користувача його не скидає; хід = вся сесія)
#   B  «без агента:» обходить лише з причиною з білого списку: закриття/естафета/коміт/крок скіла; перевірка звіту
#      під-агента (кількість — під C); Edit/Write ≤ V2_EDIT_LINES рядків. Без причини зі списку — як без обходу
#   C  після звіту під-агента (task-notification Agent/delegate, hand-back) — V2_K вільних кроків, далі deny «доробка —
#      віддай наступному агенту»; вікно закриває нова роздача або нове повідомлення користувача (не репліка посеред ходу)
#   G  роздача = Agent/Task + delegate/deepseek/SendMessage (усі способи віддати задачу агенту) — за замовчуванням
#      ВИМКНЕНО: бектест 27.10 — delegate частіше звірка (verify-before-show), ніж роздача, і скидає лічильник
#   Z  законна робота оркестратора без обходу: після «закрий сесію…»/Skill session-close у поточному ході — тиша;
#      git status/add/commit/log/diff/show — не одиниця роботи (коміт і огляд стану — справа оркестратора);
#      нагляд за іншим агентом (tmux capture-pane/list-windows/send-keys, цикл очікування зі sleep) — теж ні
# EDIT_GATE_V2=0 — повернутися до старих воріт (agents_check). Аварійно все — EDIT_GATE_AGENTS=0.
V2_ON = os.environ.get("EDIT_GATE_V2", "1") != "0"
V2_FLAGS = {k: os.environ.get("EDIT_GATE_V2_" + k, "0" if k == "G" else "1") != "0" for k in "ASBCGZ"}
V2_N = int(os.environ.get("EDIT_GATE_V2_N", "12"))
V2_K = int(os.environ.get("EDIT_GATE_V2_K", "2"))
V2_EDIT_LINES = 10
V2_WORK = {"Bash", "Read", "Grep", "Glob", "Edit", "Write", "MultiEdit", "NotebookEdit"}
V2_DELEG = {"Agent", "Task"}
V2_DELEG_G = V2_DELEG | {"mcp__delegate__delegate", "mcp__delegate__deepseek", "mcp__deepseek__deepseek",
                         "mcp__deepseek__deepseek-reply", "SendMessage"}
RE_WL_CLOSE = re.compile(r"закрит|закрива|session-close|baton|естафет|handoff|коміт|commit|git status|"
                         r"крок\w*\s*\d*\s*скіл", re.I)
RE_WL_CHECK = re.compile(r"(?:перевір|звір)\w*[^,;)]{0,30}(?:звіт|чис|під-?агент|делегат)", re.I)
RE_WL_EDIT = re.compile(r"правк|рядк|рядок|запис", re.I)
RE_CLOSE_H = re.compile(r"закр\w* сесі|завершуєм|закриваєм|на сьогодні все|згортаєм|checkpoint|wrap up|close the session", re.I)
# нагляд за іншим агентом (DSH у tmux, очікування фонового) — це роздача, а не «роблю сам» (бектест 27.10: 3 хибні deny)
RE_COORD = re.compile(r"tmux\s+(?:capture-pane|list-windows|send-keys)|^\s*(?:end=|until\s|while\s)[^\n]*\n?[^\n]*sleep", re.M)
RE_GIT_OWN = re.compile(r"\s*(?:cd \S+ && )?git (?:status|add|commit|log|diff|show)\b")
RE_REPORT = re.compile(r"<summary>(?:Agent \"|MCP task \S+ \((?:delegate|deepseek))|Subagent hand-back", re.I)
V2_A_REASON = ("Ворота «агенти» v2: {n} власних кроків (команди, читання, правки) від останньої роздачі задачі. "
               "Віддай наступну обмежену частину під-агенту (Agent) або повтори виклик з «без агента: <причина>», "
               "де причина — закриття сесії/естафета/коміт, перевірка звіту під-агента або правка ≤{e} рядків.")
V2_C_REASON = ("Ворота «агенти» v2: після звіту під-агента вже {n} власних кроків — це доробка (перенос, повтори, "
               "записи). Віддай її наступному агенту одним брифом; точкова перевірка звіту — до {k} кроків.")


def v2_line_events(d):
    """Події одного запису журналу: ("tool", ts, name, inp) | ("human", ts, text, "user"|"queued") | ("report", ts, text)."""
    if not isinstance(d, dict):
        return []
    t, ts = d.get("type"), d.get("timestamp", "")
    if t == "assistant" and not d.get("isSidechain"):
        return [("tool", ts, x.get("name", ""), x.get("input") or {}) for x in (d.get("message") or {}).get("content") or []
                if isinstance(x, dict) and x.get("type") == "tool_use"]
    if t == "attachment":
        a = d.get("attachment") or {}
        if a.get("type") != "queued_command":
            return []
        p = a.get("prompt", "")
        p = p if isinstance(p, str) else json.dumps(p, ensure_ascii=False)
        kind = (a.get("origin") or {}).get("kind", "human")
        if RE_REPORT.search(p[:2000]):
            return [("report", ts, p[:120])]
        if kind == "human" and not p.lstrip().startswith("<"):
            return [("human", ts, p, "queued")]  # посеред ходу: хід (у v1) не відкриває
        return []
    if t == "user" and not d.get("isMeta"):
        c = (d.get("message") or {}).get("content")
        if not isinstance(c, str):
            return []
        kind = (d.get("origin") or {}).get("kind") if isinstance(d.get("origin"), dict) else None
        if RE_REPORT.search(c[:2000]):
            return [("report", ts, c[:120])]
        if kind == "human" or (kind is None and not c.lstrip().startswith("<")):
            return [("human", ts, c, "user")]
    return []


def v2_window(path, flags=None):
    """Події від останньої роздачі задачі (без неї) до кінця журналу, у прямому порядку; (події, якір = ts роздачі)."""
    flags = flags or V2_FLAGS
    deleg = V2_DELEG_G if flags.get("G") else V2_DELEG
    with open(path, encoding="utf-8", errors="ignore") as f:
        lines = f.read().splitlines()
    out, anchor = [], "start"
    for line in reversed(lines):
        if '"tool_result"' in line[:600] and '"type":"assistant"' not in line[:200]:
            continue  # результати інструментів подій не дають — не розбираємо (швидкість)
        try:
            d = json.loads(line)
        except ValueError:
            continue
        evs = v2_line_events(d)
        hit = next((e for e in reversed(evs) if e[0] == "tool" and e[2] in deleg), None)
        if hit:
            out += [e for e in reversed(evs[evs.index(hit) + 1:])]
            anchor = hit[1]
            break
        out += list(reversed(evs))
    return list(reversed(out)), anchor


def v2_whitelisted(reason, name, inp):
    if RE_WL_CLOSE.search(reason):
        return "close"
    if RE_WL_CHECK.search(reason):
        return "check"
    if name in ("Edit", "Write", "MultiEdit") and RE_WL_EDIT.search(reason):
        body = str(inp.get("new_string", "") or inp.get("content", "")) + "".join(
            str(e.get("new_string", "")) for e in inp.get("edits", []) or [] if isinstance(e, dict))
        if body.count("\n") + 1 <= V2_EDIT_LINES:
            return "edit"
    return None


def v2_decide(ev, name, inp, anchor, flags=None, agv=None, n_lim=None, k_lim=None):
    """Чисте рішення v2 (спільне для хука і бектесту): (ключ, n, причина) або None.
    ev — події від останньої роздачі БЕЗ поточного виклику."""
    flags, n_lim, k_lim = flags or V2_FLAGS, n_lim or V2_N, k_lim or V2_K
    agv = agv or answer_gate()
    inp = inp or {}
    is_unit = (lambda nm, i: nm in V2_WORK) if flags.get("A") else (lambda nm, i: agv.is_read(nm, i))
    if not is_unit(name, inp):
        return None
    if not flags.get("S"):  # без S — як у v1: лише поточний хід (від останнього повідомлення людини)
        hs = [i for i, e in enumerate(ev) if e[0] == "human" and e[3] == "user"]  # межі ходу як у v1 (iter_turns)
        if hs:
            ev = ev[hs[-1] + 1:]
    last_h = max([i for i, e in enumerate(ev) if e[0] == "human"], default=-1)
    if flags.get("Z"):
        lu = max([i for i, e in enumerate(ev) if e[0] == "human" and e[3] == "user"], default=-1)
        if lu >= 0 and RE_CLOSE_H.search(ev[lu][2]) or any(
                e[0] == "tool" and e[2] == "Skill" and "session-close" in str(e[3].get("skill", "")) for e in ev[lu + 1:]):
            return None
        own = lambda nm, i: nm == "Bash" and bool(RE_GIT_OWN.match(str(i.get("command", ""))) or
                                                  RE_COORD.search(str(i.get("command", ""))))
        if own(name, inp):
            return None
        base_unit = is_unit
        is_unit = lambda nm, i: base_unit(nm, i) and not own(nm, i)
    desc = str(inp.get("description", ""))
    wl = None
    if "без агента:" in desc:
        if not flags.get("B"):
            return None
        wl = v2_whitelisted(desc.split("без агента:", 1)[1], name, inp)
        if wl in ("close", "edit"):
            return None
    if not flags.get("S"):  # ключ дедупу — у межах ходу, як у v1
        hs = [i for i, e in enumerate(ev) if e[0] == "human" and e[3] == "user"]
        anchor = f"{anchor}|{ev[hs[-1]][1] if hs else 'turn'}"
    units = [i for i, e in enumerate(ev) if e[0] == "tool" and is_unit(e[2], e[3])]
    if flags.get("C"):
        last_u = max([i for i, e in enumerate(ev) if e[0] == "human" and e[3] == "user"], default=-1)
        reps = [i for i, e in enumerate(ev) if e[0] == "report" and i > last_u]  # репліка посеред ходу вікно не закриває
        if reps:
            m = sum(1 for i in units if i > reps[-1]) + 1
            if m > k_lim:
                return f"agents-c\t{anchor}\t{ev[reps[-1]][1]}", m, V2_C_REASON.format(n=m, k=k_lim)
            return None  # точкова перевірка звіту — вільна
    if wl == "check" and not flags.get("C"):
        return None
    n = len(units) + 1
    if n < n_lim:
        return None
    return f"agents-a\t{anchor}\t{n // n_lim}", n, V2_A_REASON.format(n=n, e=V2_EDIT_LINES)


def v2_check(data, agv=None):
    """Обгортка для хука: ті самі вимикачі, що й agents_check, далі v2_window + v2_decide."""
    if os.environ.get("EDIT_GATE_AGENTS") == "0" or data.get("agent_id"):
        return None
    if "deepseek" in os.environ.get("ANTHROPIC_BASE_URL", ""):
        return None
    tp = data.get("transcript_path")
    if not (isinstance(tp, str) and os.path.isfile(tp)):
        return None
    agv = agv or answer_gate()
    if agv.is_test_session(data.get("session_id")):
        return None
    name, inp = data.get("tool_name", ""), data.get("tool_input") or {}
    ev, anchor = v2_window(tp)
    tools = [e for e in ev if e[0] == "tool"]
    if tools and tools[-1][2] == name and tools[-1][3] == inp:  # поточний виклик уже може бути в журналі
        ev = [e for e in ev if e is not tools[-1]]
    return v2_decide(ev, name, inp, anchor, agv=agv)


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--backtest":
        return backtest(sys.argv[2])
    data = json.load(sys.stdin)
    name, inp = data.get("tool_name", ""), data.get("tool_input") or {}
    if name not in EDIT_TOOLS and name != "Bash" and name not in READ_TOOLS:
        return
    try:
        ag = v2_check(data) if V2_ON else agents_check(data)  # v2 (2026-10-27) — копія; v1 лишається для відкату
    except Exception:
        ag = None
    if ag and ag[0] not in seen_keys(data.get("session_id", "?")):
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"{data.get('session_id', '?')}\t{ag[0]}\t{time.strftime('%Y-%m-%dT%H:%M:%S')}\n")
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse", "permissionDecision": "deny",
            "permissionDecisionReason": ag[2] if len(ag) > 2 else AGENTS_REASON.format(n=ag[1])}}, ensure_ascii=False))
        return
    if name in READ_TOOLS:
        return
    ev = Evidence()
    tp = data.get("transcript_path")
    if isinstance(tp, str) and os.path.isfile(tp):
        for _, n, i in iter_tool_uses(tp):
            if n == name and i == inp:
                continue  # поточний виклик уже може бути в журналі
            ev.add(n, i)
    sid = data.get("session_id", "?")
    seen = seen_keys(sid)
    msgs, asks = [], []
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    for key, msg in check(name, inp, ev, data.get("cwd")):
        if key.startswith("ask-history"):  # питає щоразу, без дедупу за сесію
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(f"{sid}\t{key}\t{time.strftime('%Y-%m-%dT%H:%M:%S')}\n")
            asks.append(msg)
            continue
        if key in seen:
            continue
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"{sid}\t{key}\t{time.strftime('%Y-%m-%dT%H:%M:%S')}\n")
        msgs.append(msg)
    if asks:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse", "permissionDecision": "ask",
            "permissionDecisionReason": "edit-gate: " + " | ".join(asks),
            "additionalContext": "\n".join(msgs + asks)}}, ensure_ascii=False))
    elif msgs:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse", "additionalContext": "\n".join(msgs)}},
            ensure_ascii=False))


def backtest(path):
    ev, seen, n = Evidence(), set(), 0
    for ts, name, inp in iter_tool_uses(path):
        # Існування файлу в минулому невідоме: Write рахуємо новим файлом, Edit — наявним.
        for key, msg in check(name, inp, ev, exists=(name != "Write"), day=ts[:10]):
            if key not in seen:
                seen.add(key)
                n += 1
                print(f"{ts[11:19]}  {name:<5} {key.replace(chr(9), ' ')}")
        ev.add(name, inp)
    print(f"нагадувань: {n}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
