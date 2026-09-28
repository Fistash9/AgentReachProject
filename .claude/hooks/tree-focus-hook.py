#!/data/data/com.termux/files/usr/bin/python3
"""
UserPromptSubmit hook: «фокус дерева» — на кожне повідомлення користувача
нагадує активне дерево задач і чергу відкритих вузлів.

Навіщо (2026-09-28, M4 у trees/pam-yat-proyektu.md): режим дерева і правило
«нове питання — в кінець черги» жили лише текстом (пам'ять, RULES) і в
довгих темах не вмикались — фокус губився тричі за сесію. Прецедент:
request-brief «не мав жодного автоматичного тригера… тому регулярно
пропускався» (шапка request-brief-reminder-hook.py) — вирішено хуком.

Як працює:
- вказівник <cwd>/.claude/active-tree — один рядок, шлях до картки дерева
  відносно кореня проєкту. Немає вказівника — хук мовчить.
- з картки бере назву (перший рядок "# ") і відкриті вузли ("- [ ] ID …")
  у порядку картки (порядок = черга), до MAX_NODES.
- під-сесії DeepSeek (ANTHROPIC_BASE_URL містить deepseek) — мовчить, як
  classify-task.sh.
- будь-яка помилка — мовчить (fail-open), нічого не блокує.
"""
import json
import os
import re
import sys

MAX_NODES = 6
NODE = re.compile(r"^\s*- \[ \] (\S+)\s+(.*)$")


def main():
    if "deepseek" in os.environ.get("ANTHROPIC_BASE_URL", ""):
        return
    data = json.load(sys.stdin)
    cwd = data.get("cwd") or os.getcwd()
    pointer = os.path.join(cwd, ".claude", "active-tree")
    if not os.path.isfile(pointer):
        return
    rel = open(pointer, encoding="utf-8").read().strip()
    card = os.path.join(cwd, rel)
    lines = open(card, encoding="utf-8").read().split("\n")
    title = next((l[2:].strip() for l in lines if l.startswith("# ")), rel)
    nodes = []
    for l in lines:
        m = NODE.match(l)
        if m:
            nodes.append(f"{m.group(1)} {m.group(2)[:50]}")
    if not nodes:
        return
    more = f" (+{len(nodes) - MAX_NODES})" if len(nodes) > MAX_NODES else ""
    text = (f"Активне дерево: {title} ({rel}). Відкриті вузли по черзі: "
            + "; ".join(nodes[:MAX_NODES]) + more + ". "
            "Нове питання користувача → вузол у кінець черги, якщо поточний "
            "вузол може йти без нього (інакше скажи це вголос). Після відповіді "
            "покажи чергу зі статусами. Картку оновлюй лише на воротах.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                             "additionalContext": text}},
                     ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
