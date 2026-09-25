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
# 2026-09-25: перемикач провайдера (tools/provider-switch.py пише .provider).
# nvidia → gpt-oss-20b на build.nvidia.com (формат OpenAI, ключ NVIDIA_API_KEY у .env).
PROVIDER_FILE = os.path.expanduser("~/AgentReachProject/.provider")
ENV_FILE = os.path.expanduser("~/AgentReachProject/.env")
NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_MODEL = "openai/gpt-oss-20b"
LOG_FILE = os.path.expanduser("~/AgentReachProject/.claude/logs/improver.log")
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


NO_IMPROVE_MARKER = "[no-improve]"
MIN_WORDS_STRUCTURED = 120
MIN_STRUCTURE_CUES = 2
STRUCTURE_CUES = [  # різні ознаки структури; рахуємо, скільки з них є
    r"\bмета\b|\bgoal\b",
    r"формат|\bformat\b",
    r"\bкрок|\bsteps?\b",
    r"джерел|\bsources?\b",
    r"бюджет|\bbudget\b",
    r"\bмеж[іа]\b|обмежен|boundar",
    r"вердикт|verdict|умова зупинки|stop condition",
]


def is_structured(prompt):
    """Довгий (≥120 слів) і з ≥2 різними ознаками структури — не переписувати."""
    if len(prompt.split()) < MIN_WORDS_STRUCTURED:
        return False
    low = prompt.lower()
    cues = sum(1 for p in STRUCTURE_CUES if re.search(p, low))
    return cues >= MIN_STRUCTURE_CUES


def provider():
    try:
        return open(PROVIDER_FILE).read().strip() or "deepseek"
    except OSError:
        return "deepseek"


def log(event, **kw):
    """Один рядок JSON на подію — щоб було видно, куди пішов виклик (tail -F)."""
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        import time as _t
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": _t.strftime("%Y-%m-%dT%H:%M:%S"), "event": event, **kw},
                               ensure_ascii=False) + "\n")
    except Exception:
        pass


def call_nvidia(instruction):
    """Один запит до NVIDIA (формат OpenAI); повертає текст або "" (fail-open)."""
    try:
        m = re.search(r"^NVIDIA_API_KEY=(\S+)", open(ENV_FILE, encoding="utf-8").read(), re.M)
        if not m:
            return ""
        body = json.dumps({
            "model": NVIDIA_MODEL,
            "max_tokens": 8192,
            "temperature": 0.3,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                         {"role": "user", "content": instruction}],
        }).encode("utf-8")
        req = urllib.request.Request(NVIDIA_URL, data=body, headers={
            "content-type": "application/json",
            "Authorization": "Bearer " + m.group(1),
        })
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.load(resp)
        return (data["choices"][0]["message"].get("content") or "").strip()
    except Exception:
        return ""


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

    # 1) Позначка «не чіпати» на початку промпту: прибрати її й пропустити решту
    #    дослівно (делегат отримує рівно той текст, що написано, — напр.
    #    заморожений промпт verify-before-show).
    stripped = original_prompt.lstrip()
    tool = data.get("tool_name", "")
    if stripped.startswith(NO_IMPROVE_MARKER):
        log("skip_marker", tool=tool)
        new_input = dict(tool_input)
        new_input["prompt"] = stripped[len(NO_IMPROVE_MARKER):].lstrip()
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "updatedInput": new_input,
            }
        }))
        return

    # 2) «Рідко втручатися» (принцип severity1/claude-code-prompt-improver):
    #    довгий структурований промпт уже чіткий — пропускаємо без змін.
    if is_structured(original_prompt):
        log("skip_structured", tool=tool, words=len(original_prompt.split()))
        return

    instruction = META_INSTRUCTIONS.format(prompt=original_prompt)

    prov = provider()
    import time as _t
    t0 = _t.time()
    improved = call_nvidia(instruction) if prov == "nvidia" else call_deepseek(instruction)
    log("rewrite", tool=tool, provider=prov, ok=bool(improved), secs=round(_t.time() - t0, 1))
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
