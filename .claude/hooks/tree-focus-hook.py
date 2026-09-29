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
- вузол — рядок "- [x] ID назва" (x: пробіл/x/~/>); глибина — відступ.
- шлях — найглибший `[>]` картки з предками; «далі» — наступний `[ ]` того
  ж рівня (або рівнем вище, якщо рівень скінчився).
- `[>]` ніде немає → нагадування «жоден вузол не в роботі»; запасний
  <cwd>/.claude/active-tree (старий вказівник) дає чергу на SessionStart.
- під-сесії DeepSeek (ANTHROPIC_BASE_URL містить deepseek) — мовчить, як
  classify-task.sh (M4.5 — окремий вузол).
- будь-яка помилка — мовчить (fail-open), нічого не блокує.
"""
import glob
import json
import os
import re
import sys

MAX_NODES = 6
NODE = re.compile(r"^(\s*)- \[(.)\] (\S+)\s+(.*)$")
RULE = ("Нове питання → вузол у кінець черги (якщо поточний може йти без "
        "нього — інакше скажи вголос); беручись за вузол — [>], на воротах — "
        "[x]; після відповіді покажи чергу.")


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
            nodes.append({"depth": len(m.group(1)), "st": m.group(2),
                          "id": m.group(3), "name": m.group(4)})
    return title.split(" · ")[0], nodes


def active_path(nodes):
    """Найглибший [>] і його предки; індекс цього вузла."""
    best = None
    for i, n in enumerate(nodes):
        if n["st"] == ">" and (best is None or n["depth"] > nodes[best]["depth"]):
            best = i
    if best is None:
        return [], None
    path, depth = [nodes[best]], nodes[best]["depth"]
    for n in reversed(nodes[:best]):
        if n["depth"] < depth:
            path.insert(0, n)
            depth = n["depth"]
    return path, best


def next_node(nodes, i):
    """Наступний [ ] того ж рівня; якщо рівень скінчився — рівнем вище."""
    depth = nodes[i]["depth"]
    for n in nodes[i + 1:]:
        if n["depth"] < depth:
            depth = n["depth"]
        if n["depth"] == depth and n["st"] == " ":
            return n
    return None


def main():
    if "deepseek" in os.environ.get("ANTHROPIC_BASE_URL", ""):
        return
    data = json.load(sys.stdin)
    event = data.get("hook_event_name") or "UserPromptSubmit"
    cwd = data.get("cwd") or os.getcwd()
    lines = []
    for card in sorted(glob.glob(os.path.join(cwd, "trees", "*.md"))):
        try:
            title, nodes = parse(card)
        except Exception:
            continue  # битий файл не глушить інші картки
        path, i = active_path(nodes)
        if not path:
            continue
        crumbs = " › ".join(short(f"{n['id']} {n['name']}", 40) for n in path)
        line = f"В роботі: {title} › {crumbs}"
        if event == "SessionStart":
            nxt = next_node(nodes, i)
            if nxt:
                line += f"\n  далі: {short(nxt['id'] + ' ' + nxt['name'], 50)}"
            queue = [n for n in nodes if n["st"] == " " and n["depth"] == 0]
            if queue:
                more = f" (+{len(queue) - MAX_NODES})" if len(queue) > MAX_NODES else ""
                line += "\n  черга картки: " + "; ".join(
                    short(f"{n['id']} {n['name']}", 30) for n in queue[:MAX_NODES]) + more
                line += f" ({os.path.relpath(card, cwd)})"
        lines.append(line)

    if lines:
        text = "\n".join(lines) + ("\n" + RULE if event == "SessionStart" else "")
    else:
        text = ("Жоден вузол не в роботі ([>] у trees/*.md). Перед роботою над "
                "темою: знайди її картку в trees/ або заведи вузол і постав [>].")
        pointer = os.path.join(cwd, ".claude", "active-tree")
        if event == "SessionStart" and os.path.isfile(pointer):
            rel = open(pointer, encoding="utf-8").read().strip()
            title, nodes = parse(os.path.join(cwd, rel))
            queue = [n for n in nodes if n["st"] == " " and n["depth"] == 0]
            text += (f"\nОстання активна картка: {title} ({rel}): "
                     + "; ".join(short(f"{n['id']} {n['name']}", 30)
                                 for n in queue[:MAX_NODES]))
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event,
                                             "additionalContext": text}},
                     ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
