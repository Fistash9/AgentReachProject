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

КРИТИЧНО: підпроцес запускається з `--tools ""` — без цього він мав
ПОВНИЙ доступ до всіх MCP-інструментів проєкту (включно з deepseek/
delegate) і міг сам, непомітно, викликати їх замість того, щоб
просто переписати текст. Знайдено 2026-09-23 через живі log-записи
з невідомими session_id (модель "default"), яких сама сесія не
викликала.

Не блокує — якщо покращення не вдалось (порожній вивід, помилка,
таймаут), пропускає оригінальний prompt без змін (fail-open).
"""
import os
import re
import sys
import json
import urllib.request

# 2026-09-24 (вибір користувача): переписує DeepSeek flash прямим HTTP-викликом
# Anthropic-ендпоінта DeepSeek, а не `claude -p` на Claude. Причина: на Haiku
# ~$0.048, на Opus ~$0.26 з ліміту claude.ai за виклик (журнали сесій хука),
# тоді як сам делегований виклик коштує ~$0.003. Історія: haiku → claude-opus-5-5
# → deepseek-flash. Мислення вимкнено (`thinking: disabled`, TROUBLES.md).
IMPROVER_MODEL = "deepseek-flash"
DEEPSEEK_URL = "https://api.deepseek.com/anthropic/v1/messages"
AGENT_PY = os.path.expanduser("~/AgentReachProject/agent.py")  # ключ, як у run-deepseek.sh
TIMEOUT = 45
SYSTEM_PROMPT = "Ти переписуєш промпти для делегованих AI-викликів. Виводь лише текст промпту, без пояснень."

META_INSTRUCTIONS = """Ти переписуєш промт для делегованого AI-виклику (DeepSeek). Твій єдиний вивід — новий текст промту, БЕЗ жодних пояснень, преамбул чи лапок навколо.

Спочатку перевір: чи це вже тривіальний, короткий чи розмовний запит (одне слово, пряме просте питання, звертання "як людина/по-людськи", прохання щось просто сказати чи показати)? Якщо так — виведи ОРИГІНАЛ ПОВНІСТЮ БЕЗ ЗМІН, нічого з пунктів нижче не застосовуй. Чек-лист — лише для дослідницьких/аналітичних задач, де він реально щось додає.

Якщо запит НЕ тривіальний, застосуй:
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


def call_deepseek(instruction):
    """Один запит до DeepSeek; повертає текст або "" (будь-яка помилка → fail-open)."""
    try:
        m = re.search(r"sk-[a-zA-Z0-9]+", open(AGENT_PY, encoding="utf-8").read())
        if not m:
            return ""
        body = json.dumps({
            "model": IMPROVER_MODEL,
            "max_tokens": 8192,
            "system": SYSTEM_PROMPT,
            "thinking": {"type": "disabled"},
            "messages": [{"role": "user", "content": instruction}],
        }).encode("utf-8")
        req = urllib.request.Request(DEEPSEEK_URL, data=body, headers={
            "content-type": "application/json",
            "x-api-key": m.group(0),
            "anthropic-version": "2023-06-01",
        })
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.load(resp)
        return "".join(b.get("text", "") for b in data.get("content", [])
                       if b.get("type") == "text").strip()
    except Exception:
        return ""


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

    improved = call_deepseek(instruction)
    if not improved:
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
