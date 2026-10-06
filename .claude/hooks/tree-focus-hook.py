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
"""
import glob
import json
import os
import re
import subprocess
import sys

MAX_NODES = 6
MAX_WORK = 3
MAX_HOWTO = 1600  # 1600: щоб влазили всі три правила списку HOWTO_RULES (M11.1, 2026-10-03)
HOWTO_RULES = ("check-content-not-titles",
               "fix-root-cause-of-every-bug",
               "read-dsh-channel-map-before-planning")
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
    """Правило → (опис, рядок «How to apply») з memory-файлів (M11.1).

    Читає лише ті файли, де є рядок «How to apply:»; будь-яка помилка —
    мовчки (fail-open), як і решта хука.
    """
    out = {}
    mem_dir = next((d for d in MEM_CANDIDATES if d and os.path.isdir(d)), None)
    if mem_dir is None:
        return out
    for p in sorted(glob.glob(os.path.join(mem_dir, "*.md"))):
        try:
            txt = open(p, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        lines = txt.split("\n")
        apply_line = next((l.strip() for l in lines
                           if l.startswith("How to apply:")), None)
        if not apply_line:
            continue  # правила без «як застосовувати» в контекст не вносимо
        desc = next((l.strip()[len("description:"):].strip().strip('"')
                     for l in lines if l.startswith("description:")), "")
        out[os.path.basename(p)[:-3]] = (desc, apply_line)
    return out


def howto_section():
    """Секція «Як застосовувати:» — короткий список правил, <= MAX_HOWTO симв.

    Бере лише правила з HOWTO_RULES, у заданому порядку; відсутній файл або
    файл без рядка «How to apply:» — пропускається. Якщо немає жодного —
    повертає "".
    """
    mem = mem_howto()
    picked = [(nm, mem[nm]) for nm in HOWTO_RULES if nm in mem]
    if not picked:
        return ""
    head = "Як застосовувати:"
    out, used = [head], len(head)
    for nm, (_, apply_line) in picked:
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
    cwd = data.get("cwd") or os.getcwd()
    me = os.environ.get("BATON_AGENT") or "claude-code"
    work, waiting, queues, others, unowned = [], [], [], {}, []
    # hits: з 5777421 (2026-10-03, M11.1) «Як застосовувати» показувалось лише при
    # активному вузлі. З d7f2fae (2026-10-06, порада DSH cc-nodeids-1) — завжди
    # (`if True` нижче); hits збирається, але не читається. Повернути задум
    # M11.1: `if True:` → `if hits:`.
    hits = []  # активні вузли — для секції «Як застосовувати»
    for card in sorted(glob.glob(os.path.join(cwd, "trees", "*.md"))):
        try:
            title, nodes = parse(card)
        except Exception:
            continue  # битий файл не глушить інші картки
        paths = active_paths(nodes)
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
    if start:
        out += queues
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
            howto = howto_section()
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
