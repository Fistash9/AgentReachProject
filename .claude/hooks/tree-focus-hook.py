#!/data/data/com.termux/files/usr/bin/python3
"""
UserPromptSubmit + SessionStart hook: «фокус дерева» — показує, який вузол
дерева задач зараз у роботі, і що далі.

Навіщо (2026-09-28, M4 у trees/pam-yat-proyektu.md): режим дерева і правило
«нове питання — в кінець черги» жили лише текстом (пам'ять, RULES) і в
довгих темах не вмикались — фокус губився тричі за сесію. Прецедент:
request-brief «не мав жодного автоматичного тригера… тому регулярно
пропускався» (шапка request-brief-reminder-hook.py) — вирішено хуком.

2026-09-29 (M4.4, рішення користувача — «свій механізм за зразком Beads»,
TROUBLES «Beads на Termux…»): замість одного вказівника на одну картку —
позначка `[>]` («в роботі») прямо у вузлі, на кожному рівні, як in_progress
у Beads. Хук шукає `[>]` у всіх trees/*.md; SessionStart (старт, resume,
після стискання — як `bd prime`) показує шлях і чергу, кожне повідомлення —
один короткий рядок.

Як працює:
- вузол — рядок "- [x] ID назва" (x: пробіл/x/~/>/?); глибина — відступ.
- «в роботі» — усі листові `[>]` (до 3, решта +N), кожен зі шляхом предків;
  «далі» (SessionStart) — наступний `[ ]` того ж рівня або рівнем вище.
- `[?]` — зроблено, чекає перевірки: окремий рядок (ставиться вручну).
- `@агент` у кінці рядка вузла — чий він (2026-09-30, два агенти): свої й
  непозначені [>] — «в роботі», чужі — рядком «У dsh в роботі: …»; хто «я» —
  BATON_AGENT, за замовчуванням claude-code.
- «змінено й не закомічено» — сам, з `git status` (~0,03 с), бо «перевірено»
  хук знати не може, а незакриті зміни — може (запит користувача 2026-09-29).
- 2026-09-30 (M4, проба не пройдена): «в роботі» — лише `[>] … @я`; `[>]` без
  `@агент` — рядок «без власника», а не мій. Раніше непозначені вважались
  моїми, і чужий T7 та застарілий M4 глушили нагадування нижче, коли робота
  йшла поза деревом (розбір baton-diff 30.09).
- мого `[>]` немає → нагадування «жоден твій вузол не в роботі»; запасний
  <cwd>/.claude/active-tree (старий вказівник) дає чергу на SessionStart.
- під-сесії-помічники DeepSeek (адреса deepseek + effort або sdk-cli) — мовчить;
  головна DeepSeek-сесія дерево бачить (M4.5, 2026-09-29).
- будь-яка помилка — мовчить (fail-open), нічого не блокує.
- 2026-10-15 (G2.5.3, користувач «фокус увімкнений на глобальній цілі?»): на
  SessionStart замість черг карток з [>] — ціль, «Зараз» (голова черги кожної
  картки), «Чекають» і [>] поза «Зараз» з GOALS.md (goals_lines); без GOALS.md
  чи при помилці — черги, як раніше. Старт 2616 → 2614 симв.
"""
import glob
import json
import math
import os
import re
import subprocess
import sys

MAX_NODES = 6
MAX_WORK = 3
# 2026-10-25 (Q4.4, рішення «Так, вносити»): посилання на рілс/коротке відео → підказка інструмента розбору (урок з
# рілса Deh5yf2xL3s «повторюване — у скіл»: 8 розборів вручну, -l auto губив початок)
RE_REEL = re.compile(r"https?://(?:www\.)?(?:instagram\.com/(?:reels?|p)/\S+|youtube\.com/shorts/\S+|youtu\.be/\S+"
                     r"|(?:vm\.)?tiktok\.com/\S+)")
MAX_HOWTO = 1600  # 1600: щоб влазили всі три правила списку HOWTO_RULES (M11.1, 2026-10-03)
HOWTO_RULES = ("check-content-not-titles",
               "fix-root-cause-of-every-bug",
               "read-dsh-channel-map-before-planning")
# 2026-10-27 (П3 FIX-PLANS, сходинка «залежність»: уроки мають з'являтися в момент дії):
# сталий HOWTO_RULES показував ті самі 3 правила, а парсер не бачив «**How to apply:**»
# (26 з 82 файлів пам'яті). Тепер — вибір за роботою: основи слів активних [>] (старт)
# і повідомлення користувача (UserPromptSubmit) проти тексту файлу пам'яті, вага idf,
# пороги як handoff-view PAIR_MIN_HITS/PAIR_MIN_SCORE; HOWTO_RULES — запас на вільні місця.
MAX_RULES = 3        # правил на старті (вибрані за [>] + сталий + запас HOWTO_RULES)
WORK_RULES = 2       # 2026-10-27 (focus-v2): з MAX_RULES за роботою — не більше 2; третє місце
                     # завжди за першим із HOWTO_RULES, якого ще нема серед обраних (prep-копія
                     # віддала всі 3 вузлу G2 і витіснила fix-root-cause-of-every-bug)
MSG_LESSON_ENV = "TREE_FOCUS_MSG_LESSON"  # урок до повідомлення — лише при =1 (бектест: 1 з 5 влучних)
PROMPT_RULES = 1     # правил на повідомлення — лише сильний збіг зі словами повідомлення
RULE_CAP = 360       # межа тексту одного правила на старті, симв.: вибрані правила довші за
                     # нинішні три (1600 → старт +410 симв., замір 27.10); 3×360 ≈ розмір до правки
PROMPT_HOWTO = 300   # межа рядка уроку на повідомленні, симв. (кожне повідомлення — дороге)
REL_MIN_HITS = 2     # мінімум спільних основ (handoff-view PAIR_MIN_HITS)
REL_MIN_SCORE = 6.0  # мінімум ваги, сума idf (handoff-view PAIR_MIN_SCORE)
RE_APPLY = re.compile(r"^\s*(?:\*\*)?How to apply:(?:\*\*)?\s*")
APPLY_MARK = "Урок до повідомлення:"
MEM_PROJECT = "-data-data-com-termux-files-home-AgentReachProject"
MEM_ENV = os.environ.get("CLAUDE_MEMORY_DIR")
MEM_CANDIDATES = [MEM_ENV] if MEM_ENV else []
MEM_CANDIDATES += [
    "/data/data/com.termux/files/home/.claude/projects/" + MEM_PROJECT + "/memory",
    os.path.expanduser("~/.claude/projects/" + MEM_PROJECT + "/memory"),
]
FOREIGN = "script-agent/output/"  # чужа тека, завжди поза git
NODE = re.compile(r"^(\s*)- \[(.)\] (\S+)\s+(.*)$")
OWNER = re.compile(r"\s@([\w-]+)\s*$")  # «@dsh» у кінці рядка вузла — чий він
RULE = ("Нове питання → вузол у кінець черги (якщо поточний може йти без "
        "нього — інакше скажи вголос); беручись за вузол — [>], на воротах — "
        "[x] (лише після перевірки); зроблено, але не перевірено — [?]; "
        "після відповіді покажи чергу.")


# short(): з 98150fe (2026-09-29, M4.4) обрізала назви на старті. З d7f2fae
# (2026-10-06) викликів немає — її замінила label() (обрізана назва виглядала як
# зміст, T5). Лишено свідомо (рішення користувача «зроби щоб все працювало»,
# Q9): повернути старе — замінити label(n) на short(...) у main().
def short(s, n):
    return s if len(s) <= n else s[:n - 1] + "…"


NAME_CAP = 120  # 2026-10-06: обрізана назва («T5 Зошит і куратор: перший ур…»)
# виглядала як зміст — агент сплутав T5 зі «скілом пошуку». Тепер повна назва
# до 120 симв.; довша — з явною позначкою (план claude-code + DSH, cc-nodeids-1).


def label(n):
    s = f"{n['id']} {n['name']}"
    if len(s) <= NAME_CAP:
        return s
    return s[:NAME_CAP].rsplit(" ", 1)[0] + " …(обрізано — відкрий вузол)"


def parse(path):
    lines = open(path, encoding="utf-8").read().split("\n")
    title = next((l[2:].strip() for l in lines if l.startswith("# ")),
                 os.path.basename(path))
    nodes = []
    for l in lines:
        m = NODE.match(l)
        if m:
            o = OWNER.search(m.group(4))
            nodes.append({"depth": len(m.group(1)), "st": m.group(2),
                          "id": m.group(3), "name": OWNER.sub("", m.group(4)),
                          "owner": o.group(1) if o else None})
    return title.split(" · ")[0], nodes


def active_paths(nodes):
    """Усі «листові» [>] (без [>] нащадків) — кожен зі шляхом предків."""
    out = []
    for i, n in enumerate(nodes):
        if n["st"] != ">":
            continue
        child = next((m for m in nodes[i + 1:] if m["depth"] <= n["depth"]
                      or m["st"] == ">"), None)
        if child is not None and child["st"] == ">" and child["depth"] > n["depth"]:
            continue  # глибше є свій [>] — показуємо його шлях
        path, depth = [n], n["depth"]
        for m in reversed(nodes[:i]):
            if m["depth"] < depth:
                path.insert(0, m)
                depth = m["depth"]
        out.append((path, i))
    return out


def next_node(nodes, i):
    """Наступний [ ] того ж рівня; якщо рівень скінчився — рівнем вище."""
    depth = nodes[i]["depth"]
    for n in nodes[i + 1:]:
        if n["depth"] < depth:
            depth = n["depth"]
        if n["depth"] == depth and n["st"] == " ":
            return n
    return None


def git_dirty(cwd):
    """Змінені й не закомічені файли (крім чужої script-agent/output/)."""
    r = subprocess.run(["git", "status", "--porcelain"], cwd=cwd,
                       capture_output=True, text=True, timeout=3)
    files = [l[3:] for l in r.stdout.splitlines()
             if l[3:] and not l[3:].startswith(FOREIGN)]
    return files


def more(items, n):
    return f" (+{len(items) - n})" if len(items) > n else ""


def mem_howto():
    """Правило → (опис, рядок «How to apply», текст файлу в нижньому регістрі) (M11.1).

    Рядок «How to apply:» приймається в обох форматах — «How to apply: …» і
    «**How to apply:** …», з відступом чи без (2026-10-27, П3); зірочки знято,
    у підказці — «How to apply: …». Будь-яка помилка — мовчки (fail-open).
    """
    out = {}
    mem_dir = next((d for d in MEM_CANDIDATES if d and os.path.isdir(d)), None)
    if mem_dir is None:
        return out
    for p in sorted(glob.glob(os.path.join(mem_dir, "*.md"))):
        if os.path.basename(p) == "MEMORY.md":
            continue  # покажчик, не правило
        try:
            txt = open(p, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        lines = txt.split("\n")
        m_line = next((l for l in lines if RE_APPLY.match(l)), None)
        if not m_line:
            continue  # правила без «як застосовувати» в контекст не вносимо
        apply_line = "How to apply: " + RE_APPLY.sub("", m_line).strip()
        desc = next((l.strip()[len("description:"):].strip().strip('"')
                     for l in lines if l.startswith("description:")), "")
        out[os.path.basename(p)[:-3]] = (desc, apply_line, txt.lower())
    return out


def stems(s):
    """Основи слів ≥5 літер (як handoff-view.stems): «агентів»/«агенти» → «агент»."""
    return {w[:max(5, len(w) - 3)] for w in re.findall(r"[^\W\d_]{5,}", str(s).lower())}


def rank_rules(query, mem):
    """[(вага, правило, спільні основи)] — правила, дотичні до тексту query.

    Збіг — входження основи в текст файлу пам'яті (там і англійський опис, і
    українські цитати користувача); вага — idf по всіх правилах, щоб часті
    («користувача», «session») не важили. Поріг: ≥REL_MIN_HITS основ і
    ≥REL_MIN_SCORE ваги.
    """
    st, N = stems(query), len(mem)
    if not st or not N:
        return []
    df = {t: sum(1 for v in mem.values() if t in v[2]) for t in st}
    out = []
    for nm, v in mem.items():
        hit = sorted(t for t in st if t in v[2])
        sc = sum(math.log((N + 1) / (df[t] + 1)) for t in hit)
        if len(hit) >= REL_MIN_HITS and sc >= REL_MIN_SCORE:
            out.append((round(sc, 2), nm, hit))
    out.sort(key=lambda t: (-t[0], t[1]))
    return out


def howto_section(query=""):
    """Секція «Як застосовувати:» — до MAX_RULES правил, <= MAX_HOWTO симв.

    До WORK_RULES (2) правил, дотичних до активних [>] (rank_rules), потім
    1 сталий — перший із HOWTO_RULES, якого ще нема серед обраних; вільні
    місця — запас HOWTO_RULES у заданому порядку (focus-v2, 2026-10-27). Файл без рядка «How to apply» —
    пропускається. Якщо немає жодного — повертає "".
    """
    mem = mem_howto()
    ranked = [nm for _, nm, _ in rank_rules(query, mem)] if query else []
    work = ranked[:WORK_RULES]  # до 2 за роботою
    steady = [nm for nm in HOWTO_RULES if nm in mem and nm not in work]
    names = work + steady[:1]  # 1 місце — завжди сталий урок (перший ще не обраний)
    # вільні місця (за роботою <2) — запас HOWTO_RULES, як раніше; якщо й запасу бракує
    # (файли сталих уроків без «How to apply») — наступні за роботою
    for nm in steady[1:] + ranked[WORK_RULES:]:
        if len(names) >= MAX_RULES:
            break
        if nm not in names:
            names.append(nm)
    picked = [(nm, mem[nm]) for nm in names]
    if not picked:
        return ""
    n_rel = sum(1 for nm in names if nm in ranked and nm not in steady[:1])
    head = "Як застосовувати:" + (f" (за [>]: {n_rel})" if n_rel else "")
    out, used = [head], len(head)
    for nm, (_, apply_line, _) in picked:
        if len(apply_line) > RULE_CAP:  # повний текст — у файлі пам'яті nm.md
            apply_line = apply_line[:RULE_CAP - 1].rstrip("…") + "…"
        line = "• " + nm + " — " + apply_line
        if used + len(line) + 1 <= MAX_HOWTO:
            out.append(line)
            used += len(line) + 1
            continue
        room = MAX_HOWTO - used - 2 - len(nm) - 5  # -2: newline join + запас
        if room >= 40:
            cut = apply_line[:room]
            if cut.endswith("…"):  # не подвоювати «…», якщо текст правила вже обірвано
                cut = cut[:-1]
            out.append("• " + nm + " — " + cut + "…")
        break
    return "\n".join(out)


def shown_rules(transcript_path):
    """Тексти журналу після останнього стиснення — щоб не повторювати урок,
    уже показаний у цій сесії (як troubles-grep-hook.already_shown). Помилка → b""."""
    if not transcript_path:
        return b""
    try:
        with open(transcript_path, "rb") as f:
            raw = f.read()
        i = raw.rfind(b'"subtype":"compact_boundary"')
        return raw[i:] if i != -1 else raw
    except Exception:
        return b""


def prompt_lesson(data):
    """Один урок, дотичний до слів повідомлення, якщо ще не показаний (П3)."""
    prompt = data.get("prompt") or ""
    mem = mem_howto()
    ranked = rank_rules(prompt, mem)
    if not ranked:
        return ""
    tail = shown_rules(data.get("transcript_path"))
    out = []
    for _, nm, _ in ranked:
        if (APPLY_MARK + " " + nm).encode() in tail or ("• " + nm + " — ").encode() in tail:
            continue
        txt = mem[nm][1][len("How to apply: "):]
        txt = txt if len(txt) <= PROMPT_HOWTO else txt[:PROMPT_HOWTO - 1] + "…"
        out.append(f"{APPLY_MARK} {nm} — {txt}")
        if len(out) >= PROMPT_RULES:
            break
    return "\n".join(out)


def goals_lines(cwd, cards, mine):
    """Ціль і напрями з GOALS.md замість черг окремих карток (G2.5.3, 2026-10-15).

    Користувач 15.10: «фокус увімкнений на глобальній цілі?» — хук показував лише
    картки з [>] (T11 з «Чекають»), а ціль і «Зараз» з GOALS.md — ніде. Для кожної
    картки «Зараз» — голова її черги (перший відкритий вузол верхнього рівня;
    порядок = черга, G2.6). [>] з карток поза «Зараз» — позначка для звірки.
    cards: {relpath: (title, nodes)}; mine: [(relpath, id)]. Без GOALS.md — [].
    """
    sec, head, where, grab = "", "", {}, False
    for ln in open(os.path.join(cwd, "GOALS.md"), encoding="utf-8").read().split("\n"):
        if ln.startswith("## "):
            sec, grab = ln[3:].split("—")[0].split("(")[0].strip(), ln.startswith("## Головна")
            continue
        if grab and ln.strip() and "»" not in head:
            head = (head + " " + ln.strip()).strip()  # цитата цілі — до «»», через рядки
        for f in re.findall(r"trees/[\w-]+\.md", ln):
            where.setdefault(f, sec)
    now = [f for f in cards if where.get(f) == "Зараз"]
    wait = [f for f in cards if where.get(f) == "Чекають"]
    heads = []
    for f in now:
        title, nodes = cards[f]
        h = next((n for n in nodes if n["depth"] == 0 and n["st"] in " >?"), None)
        heads.append(f"{title}: " + (short(f"{h['id']} {h['name']}", 60) if h else "—"))
    if "»" in head:
        head = head[:head.index("»") + 1]
    out = ["Ціль: " + short(head, 150),
           "Зараз (голова черги): " + "; ".join(heads)]
    if wait:
        out.append("Чекають: " + "; ".join(cards[f][0] for f in wait))
    off = [f"{nid} («{where.get(f) or 'поза GOALS'}»: {cards[f][0]})"
           for f, nid in mine if where.get(f) != "Зараз"]
    if off:
        out.append("Твій [>] поза «Зараз»: " + ", ".join(off) + " — звір з GOALS.md.")
    return out


def project_root(cwd):
    """Тека з trees/: cwd або найближчий предок; інакше — корінь за місцем хука.

    2026-10-12 (сесія e3a33280): cwd запиту = тека, куди агент зробив `cd`
    (.claude/hooks) → glob trees/ порожній → хибне «Жоден твій вузол не в
    роботі». Явний cwd проєкту (ручний запуск, hooks-smoke, DSH) працює як був.
    """
    d = os.path.abspath(cwd)
    while True:
        if os.path.isdir(os.path.join(d, "trees")):
            return d
        up = os.path.dirname(d)
        if up == d:
            break
        d = up
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


DSH_SESSION = "work"  # сесія tmux; вікно DSH шукаємо за назвою «dsh…», не за номером
RE_DSH_BUSY = re.compile(r"working…|thinking ·|● Question|Queue as follow-up")
RE_DSH_WAIT = re.compile(r"^\s*(?:Чекаю|чекаю|Жду|Waiting)")
DSH_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs", "dsh-line.jsonl")


def parse_dsh(screen, ids):
    """Рядок «DSH насправді» з екрана DSH (проба 3 сесії з 2026-10-19, BACKLOG «Механізми… 1fe9acd7» п.4;
    чернетка 18.10). 18.10: ярлик «[>] T7 @dsh» брехав, а DSH чекав мого листа — я не бачив (смуга мода
    agents-status показує це лише користувачу). ids — його [>] з дерева. Пункт ◐ зі списку задач
    (розбір як mods/agents-status parseDshTodo); ⚠ якщо не згадує жоден його [>]; ⚠ якщо чекає й не працює."""
    todo = None
    for line in screen.split("\n"):
        if "◐" in line:
            cells = [c.strip() for c in line.split("│") if c.strip()]
            if "◐" in cells and cells.index("◐") + 1 < len(cells):
                todo = cells[cells.index("◐") + 1]
                break
    if todo is None:
        return None, []  # списку задач на екрані нема — мовчимо
    busy = bool(RE_DSH_BUSY.search(screen))
    out, flags = "DSH насправді: " + short(todo, 90) + (" [працює]" if busy else ""), []
    if ids and not any(i in todo for i in ids):
        flags.append("mismatch")
        out += f" — ⚠ не збігається з [>] {', '.join(ids)} (перевір, чи не робите одне й те саме)"
    if not busy and RE_DSH_WAIT.match(todo):
        flags.append("waiting")
        out += " — ⚠ ЧЕКАЄ ВІДПОВІДІ: доставити лист (TROUBLES «Листи у вікно DSH») або сказати користувачу"
    return out, flags


def dsh_now(ids):
    r = subprocess.run(["tmux", "list-windows", "-t", DSH_SESSION, "-F", "#{window_index} #{window_name}"],
                       capture_output=True, text=True, timeout=2)
    win = next((l.split()[0] for l in r.stdout.splitlines()
                if len(l.split()) > 1 and l.split()[1].startswith("dsh")), None)
    if r.returncode != 0 or win is None:
        return None, []
    r = subprocess.run(["tmux", "capture-pane", "-p", "-t", f"{DSH_SESSION}:{win}"],
                       capture_output=True, text=True, timeout=2)
    return parse_dsh(r.stdout, ids) if r.returncode == 0 else (None, [])


def main():
    # Мовчить лише в під-сесіях-помічниках deepseek-mcp: вони завжди мають
    # CLAUDE_CODE_EFFORT_LEVEL (env.js) і entrypoint sdk-cli (перевірено
    # наживо 2026-09-29); головна claude-deepseek.sh effort знімає — дерево бачить.
    helper = (os.environ.get("CLAUDE_CODE_EFFORT_LEVEL")
              or os.environ.get("CLAUDE_CODE_ENTRYPOINT", "cli") != "cli")
    if "deepseek" in os.environ.get("ANTHROPIC_BASE_URL", "") and helper:
        return
    data = json.load(sys.stdin)
    event = data.get("hook_event_name") or "UserPromptSubmit"
    start = event == "SessionStart"
    cwd = project_root(data.get("cwd") or os.getcwd())
    me =os.environ.get("BATON_AGENT") or "claude-code"
    work, waiting, queues, others, unowned = [], [], [], {}, []
    # hits: з 5777421 (2026-10-03, M11.1) «Як застосовувати» показувалось лише при
    # активному вузлі. З d7f2fae (2026-10-06, порада DSH cc-nodeids-1) — завжди
    # (`if True` нижче); hits збирається, але не читається. Повернути задум
    # M11.1: `if True:` → `if hits:`.
    hits = []  # активні вузли — для секції «Як застосовувати»
    cards, mine = {}, []  # для goals_lines (G2.5.3)
    for card in sorted(glob.glob(os.path.join(cwd, "trees", "*.md"))):
        try:
            title, nodes = parse(card)
        except Exception:
            continue  # битий файл не глушить інші картки
        paths = active_paths(nodes)
        rel = os.path.relpath(card, cwd)
        cards[rel] = (title, nodes)
        for path, i in paths:
            owner = path[-1]["owner"]
            if owner is None:  # без @агент — не мій: хто його робить, невідомо
                unowned.append(path[-1]["id"])
                continue
            if owner != me:  # чужий вузол — окремим рядком
                others.setdefault(owner, []).append(path[-1]["id"])
                continue
            # кожне повідомлення — лише ID (бюджет M4: ≤3–4 тис. ток./сесію);
            # повні назви — на SessionStart
            line = f"{title} › " + " › ".join(
                label(n) if start else n["id"]
                for n in path)
            if start:
                nxt = next_node(nodes, i)
                if nxt:
                    line += f" (далі: {label(nxt)})"
            work.append(line)
            mine.append((rel, path[-1]["id"]))
            hits.append((path[-1]["id"], path))  # лише листок: батьки не тягнуть секцію
        waiting += [label(n) if start else n["id"]
                    for n in nodes if n["st"] == "?"]
        if start and paths:
            q = [n for n in nodes if n["st"] == " " and n["depth"] == 0]
            if q:
                queues.append(f"Черга «{title}» ({os.path.relpath(card, cwd)}): "
                              + "; ".join(label(n)
                                          for n in q[:MAX_NODES]) + more(q, MAX_NODES))

    hits = {nid: p for nid, p in hits}  # дедуп за id вузла (стабільно), не за id() обʼєкта
    out = []
    if work:
        out.append("В роботі: " + " | ".join(work[:MAX_WORK]) + more(work, MAX_WORK))
    else:
        out.append(f"Жоден твій вузол не в роботі ([>] … @{me} у trees/*.md) — "
                   "поточна робота невидима. Перед роботою над темою: знайди її "
                   f"картку в trees/ або заведи вузол і постав [>] … @{me}.")
    for who, ids in others.items():
        out.append(f"У {who} в роботі: " + ", ".join(ids))
    if me != "dsh":  # про DSH — лише для інших агентів; лог — для підсумку проби
        try:
            dsh, flags = dsh_now(others.get("dsh", []))
            if dsh:
                out.append(dsh)
                with open(DSH_LOG, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"t": __import__("time").strftime("%Y-%m-%dT%H:%M:%S"),
                                        "session": data.get("session_id", ""), "event": event,
                                        "flags": flags, "line": dsh[:200]}, ensure_ascii=False) + "\n")
        except Exception:
            pass
    if unowned:
        out.append("[>] без власника: " + ", ".join(unowned[:MAX_WORK])
                   + more(unowned, MAX_WORK) + " — познач @агент або зніми [>].")
    if waiting:
        out.append("Чекає перевірки: " + "; ".join(waiting[:MAX_WORK])
                   + more(waiting, MAX_WORK))
    try:
        dirty = git_dirty(cwd)
    except Exception:
        dirty = []
    if dirty:
        out.append(f"Не закомічено: {len(dirty)} ("
                   + ", ".join(os.path.basename(f.rstrip("/")) for f in dirty[:3])
                   + more(dirty, 3) + ")"
                   + (" — перевір і закоміть або познач вузол [?]." if start else ""))
    if not start:
        try:  # окремий try: помилка тут не гасить «В роботі» (звірка Haiku 25.10)
            urls = RE_REEL.findall(data.get("prompt") or "")
            if urls:
                out.append("Посилання на відео → розбір: python3 tools/reel-read.py " + urls[0]
                           + " (мова окремим кроком, перелік на суцільність; не вручну yt-dlp/whisper)")
        except Exception:
            pass
        try:  # 2026-10-27 (П3): урок до слів повідомлення; помилка не гасить решту
            # focus-v2: вимкнено за замовчуванням — лише TREE_FOCUS_MSG_LESSON=1
            lesson = prompt_lesson(data) if os.environ.get(MSG_LESSON_ENV) == "1" else ""
            if lesson:
                out.append(lesson)
        except Exception:
            pass
    if start:
        try:
            goals = goals_lines(cwd, cards, mine)
        except Exception:
            goals = []
        out += goals or queues  # G2.5.3: черги карток — лише запасний шлях
        if not work:
            pointer = os.path.join(cwd, ".claude", "active-tree")
            if os.path.isfile(pointer):
                rel = open(pointer, encoding="utf-8").read().strip()
                title, nodes = parse(os.path.join(cwd, rel))
                q = [n for n in nodes if n["st"] == " " and n["depth"] == 0]
                out.append(f"Остання активна картка: {title} ({rel}): "
                           + "; ".join(label(n)
                                       for n in q[:MAX_NODES]))
        out.append(RULE)
        out.append("Назва вузла — з джерела, не з цього списку: "
                   "python3 tools/trees-index.py <ID> (рекурсивно, файл:ID).")
        if True:  # 2026-10-06: правила — завжди на старті, не лише з [>] (DSH, cc-nodeids-1)
            # 2026-10-27 (П3): правила — за словами активних [>] (назви вузлів шляху)
            query = " ".join(n["name"] for p in hits.values() for n in p)
            howto = howto_section(query)
            if howto:
                out.append(howto)
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event,
                                             "additionalContext": "\n".join(out)}},
                     ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
