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
FOREIGN = "script-agent/output/"  # чужа тека, завжди поза git
NODE = re.compile(r"^(\s*)- \[(.)\] (\S+)\s+(.*)$")
OWNER = re.compile(r"\s@([\w-]+)\s*$")  # «@dsh» у кінці рядка вузла — чий він
RULE = ("Нове питання → вузол у кінець черги (якщо поточний може йти без "
        "нього — інакше скажи вголос); беручись за вузол — [>], на воротах — "
        "[x] (лише після перевірки); зроблено, але не перевірено — [?]; "
        "після відповіді покажи чергу.")


def short(s, n):
    return s if len(s) <= n else s[:n - 1] + "…"


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
                short(f"{n['id']} {n['name']}", 40) if start else n["id"]
                for n in path)
            if start:
                nxt = next_node(nodes, i)
                if nxt:
                    line += f" (далі: {short(nxt['id'] + ' ' + nxt['name'], 40)})"
            work.append(line)
        waiting += [short(f"{n['id']} {n['name']}", 45) if start else n["id"]
                    for n in nodes if n["st"] == "?"]
        if start and paths:
            q = [n for n in nodes if n["st"] == " " and n["depth"] == 0]
            if q:
                queues.append(f"Черга «{title}» ({os.path.relpath(card, cwd)}): "
                              + "; ".join(short(f"{n['id']} {n['name']}", 30)
                                          for n in q[:MAX_NODES]) + more(q, MAX_NODES))

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
                           + "; ".join(short(f"{n['id']} {n['name']}", 30)
                                       for n in q[:MAX_NODES]))
        out.append(RULE)
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event,
                                             "additionalContext": "\n".join(out)}},
                     ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
