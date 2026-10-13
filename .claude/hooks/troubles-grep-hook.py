#!/data/data/com.termux/files/usr/bin/python3
"""
PreToolUse hook: автоматизує правило RULES.md "Перед новою дією — grep
по TROUBLES.md". Шукає слова з Bash-команди проти TAGS: рядків у
TROUBLES.md (той самий метод, що файл сам радить: "шукай по мітці").
Тільки інформує (additionalContext), нічого не блокує.

2026-10-13 (користувач: «зроби щоб підглядалка показувала рядок-відповідь»): під першими
ANSWER_HITS записами — «↳ пункт (TROUBLES:N)»: пункт запису, найближчий до слів команди
(+ маркери «Рецепт/причина/Статус змінився…»). Причина: за сесію e3a33280 хук показав 116
заголовків, відкрито 11; запис «Хук, що перевіряє ВІДПОВІДЬ агента» показано тричі (12.10
13:23 — за 4 хв до створення answer-gate), а рядок «transcript_path може відставати»
лишився всередині — і 13.10 голос черги хибно спрацював саме на цьому.
"""
import sys
import json
import re

TROUBLES_PATH = "/data/data/com.termux/files/home/AgentReachProject/TROUBLES.md"
MAX_HITS = 5
ANSWER_HITS = 3     # під скількома записами показувати пункт-відповідь
ANSWER_LEN = 220    # межа довжини пункту (контекст дорогий)
RE_MARK = re.compile(r"рецепт|причина|висновок|лікуванн|статус змінився|правильно|не працює|"
                     r"виправлено|відстава|замість|не можна|хибн|не віддає|падає", re.I)

# Занадто загальні теги — збігаються майже з будь-якою командою,
# дають шум замість сигналу (знайдено емпірично 2026-09-19)
GENERIC_TAGS = {
    "pip", "npm", "node", "exit", "mcp", "hook", "agents", "path",
    "env", "timeout", "verification", "unverified", "backlog",
    "termux", "install", "config", "git", "python",
}


HINT_PREFIX = "TROUBLES.md має релевантні записи"


def already_shown(transcript_path):
    """Заголовки, які цей хук уже показав після останнього стиснення
    контексту. Як Claude Code для SubagentStart: не повторювати копію,
    що вже в контексті; після compaction показати знову. Журнал пишеться
    асинхронно, тож зрідка підказка повториться — це безпечно. Будь-яка
    помилка → порожня множина (поведінка як до правки)."""
    shown = set()
    if not transcript_path:
        return shown
    try:
        with open(transcript_path, "rb") as f:
            raw = f.read()
        start = raw.rfind(b'"subtype":"compact_boundary"')
        start = raw.rfind(b"\n", 0, start) + 1 if start != -1 else 0
        marker = HINT_PREFIX.encode("utf-8")
        for line in raw[start:].splitlines():
            if marker not in line or b"hook_additional_context" not in line:
                continue
            try:
                att = json.loads(line).get("attachment") or {}
            except ValueError:
                continue
            content = att.get("content")
            parts = content if isinstance(content, list) else [content]
            for part in parts:
                if not isinstance(part, str) or HINT_PREFIX not in part:
                    continue
                for item in part.split("\n- ")[1:]:
                    shown.add(item.rsplit(" (тег: ", 1)[0].strip())
    except Exception:
        return set()
    return shown


def records(text):
    """{заголовок: [(номер рядка, пункт)]} — пункти склеєно з перенесених рядків."""
    out, cur, item, start = {}, None, [], 0

    def flush():
        if cur is not None and item:
            out.setdefault(cur, []).append((start, " ".join(x.strip() for x in item)))
    for n, line in enumerate(text.splitlines(), 1):
        if line.startswith("## "):
            flush(); item = []
            cur = line[3:].strip()
            continue
        if cur is None or line.startswith(("TAGS:", "Запит", "— [")) or not line.strip():
            flush(); item = []
            continue
        if re.match(r"\s*(- |\d+\. |\* )", line) or not item:
            flush(); item, start = [line], n
        else:
            item.append(line)
    flush()
    return out


def best_item(items, words):
    """Пункт з найбільшою вагою: слова команди (довші за 3) + маркери відповіді."""
    best, score = None, 0
    for n, it in items:
        low = it.lower()
        sc = sum(2 for w in words if len(w) > 3 and w in low) + (3 if RE_MARK.search(it) else 0)
        if len(it) < 25 or it.lstrip().startswith(("—", "#")):
            continue
        if sc > score:
            best, score = (n, it), sc
    return best


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return
    command = data.get("tool_input", {}).get("command", "")
    if not command:
        return

    try:
        with open(TROUBLES_PATH, encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        return

    sections = []
    current_header = None
    for line in text.splitlines():
        if line.startswith("## "):
            current_header = line[3:].strip()
        elif line.startswith("TAGS:"):
            tags = [t.strip().lower() for t in line[len("TAGS:"):].split(",")]
            tags = [t for t in tags if t and t not in GENERIC_TAGS]
            sections.append((current_header, tags))

    words = set(re.findall(r"[a-zA-Zа-яіїєА-ЯІЇЄ0-9_-]{3,}", command.lower()))

    hits = []
    seen_headers = set()
    for header, tags in sections:
        if header in seen_headers:
            continue
        for tag in tags:
            if tag in words:
                hits.append(f"{header} (тег: {tag})")
                seen_headers.add(header)
                break

    # Не повторювати записи, які агент уже бачить у контексті
    # (92% підказок були повторами в межах сесії, заміряно 2026-09-26)
    shown = already_shown(data.get("transcript_path"))
    hits = [h for h in hits if h.rsplit(" (тег: ", 1)[0] not in shown]

    if not hits:
        return

    try:
        recs = records(text)
        # 2026-10-13: найдотичніші першими (раніше — порядок у файлі, і потрібний запис
        # випадав за межу MAX_HITS)
        def rel_score(h):
            b = best_item(recs.get(h.rsplit(" (тег: ", 1)[0], []), words)
            return sum(1 for w in words if len(w) > 3 and b and w in b[1].lower()) if b else 0
        hits.sort(key=rel_score, reverse=True)
    except Exception:
        recs = {}
    hits = hits[:MAX_HITS]
    try:
        for i, h in enumerate(hits[:ANSWER_HITS]):
            b = best_item(recs.get(h.rsplit(" (тег: ", 1)[0], []), words)
            if b:
                it = re.sub(r"\s+", " ", b[1]).strip()
                it = it if len(it) <= ANSWER_LEN else it[:ANSWER_LEN - 1] + "…"
                hits[i] = f"{h}\n  ↳ {it} (TROUBLES:{b[0]})"
    except Exception:
        pass  # рядок-відповідь — додаток; без нього поведінка як раніше
    context = "TROUBLES.md має релевантні записи для цієї команди:\n- " + "\n- ".join(hits)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": context,
        }
    }))


if __name__ == "__main__":
    main()
