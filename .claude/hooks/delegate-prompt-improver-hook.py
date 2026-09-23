#!/data/data/com.termux/files/usr/bin/python3
"""
PreToolUse hook на mcp__delegate__delegate / mcp__deepseek__deepseek(-reply):
автоматично переписує поле "prompt" перед кожним викликом делегата,
застосовуючи принцип Metaprompt (Anthropic: перетворити звичайну
задачу на чітко структурований промт) + чек-лист із TROUBLES.md
("Делегування deepseek: зайві під-агенти й марна пауза
підтвердження", 2026-09-22/23).

Реалізовано через command-хук + `claude -p --model haiku` (не
agent-хук: той відзначений у документації як "experimental and may
change", механізм updatedInput для нього не задокументований).

Не блокує — якщо покращення не вдалось (порожній вивід, помилка,
таймаут), пропускає оригінальний prompt без змін (fail-open).
"""
import sys
import json
import subprocess

IMPROVER_MODEL = "haiku"
TIMEOUT = 45

META_INSTRUCTIONS = """Ти переписуєш промт для делегованого AI-виклику (DeepSeek). Твій єдиний вивід — новий текст промту, БЕЗ жодних пояснень, преамбул чи лапок навколо.

Застосуй:
1. Metaprompt-принцип (Anthropic): перетвори завдання на чітко структурований запит — мета, формат виводу, межі задачі. Якщо оригінал уже чіткий і повний — залиш зміст як є, лише прибери зайве.
2. Чек-лист делегування (TROUBLES.md):
   - Якщо оригінальний запит УЖЕ однозначний — додай "це остаточний, повний запит — не питай підтвердження розуміння, виконуй одразу". Якщо запит справді неоднозначний — НЕ додавай цю фразу (нехай делегат перепитає).
   - Додай бюджет зусиль: проста задача — без паралельних під-агентів, 3-8 викликів WebSearch/WebFetch; для складної — прямо вкажи вищий бюджет.
   - Додай вимогу: первинні джерела пріоритетні над агрегаторами й SEO-контентом.
   - Додай вимогу: для кожного факту вказати, ЯК саме перевірено (яку сторінку відкрито, що побачено).
   - Додай вимогу: без вигаданих URL/назв — позначати [unverified] або пропускати.
   - Додай формат відповіді: стисло, окремий розділ "Джерела" з URL.
3. Не вигадуй новий зміст задачі, тільки структуруй і додай перелічені вимоги.

Оригінальний промт:
---
{prompt}
---

Виведи ЛИШЕ покращений промт."""


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return

    tool_input = data.get("tool_input", {})
    original_prompt = tool_input.get("prompt", "")
    if not original_prompt or not original_prompt.strip():
        return

    instruction = META_INSTRUCTIONS.format(prompt=original_prompt)

    try:
        result = subprocess.run(
            ["claude", "-p", instruction, "--model", IMPROVER_MODEL],
            capture_output=True, text=True, timeout=TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired):
        return

    improved = result.stdout.strip()
    if result.returncode != 0 or not improved:
        return  # fail-open: не вдалось покращити — пропускаємо оригінал

    new_input = dict(tool_input)
    new_input["prompt"] = improved

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "updatedInput": new_input,
        }
    }))


if __name__ == "__main__":
    main()
