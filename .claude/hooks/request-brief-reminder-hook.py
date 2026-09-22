#!/data/data/com.termux/files/usr/bin/python3
"""
PreToolUse hook: нагадує про критерії скіла request-brief ПЕРЕД
нетривіальною правкою (Edit/Write), коли повідомлення користувача,
що передувало правці, коротке/неоднозначне.

P4 з постмортему (TROUBLES.md, "Прогін сценариста..."): request-brief
не мав жодного автоматичного тригера, на відміну від делегатора
DeepSeek (UserPromptSubmit-хук), тому регулярно пропускався.

Евристика (без LLM, нічого не блокує):
- бере останній людський запит з transcript_path (запис "last-prompt",
  формат JSONL — перевірено на реальному транскрипті цієї сесії)
- короткий/неоднозначний: <=12 слів і НЕ голе підтвердження вже
  запропонованого ("так", "роби", "коміть" тощо)
- нетривіальна правка: >300 символів нового тексту або >5 нових рядків

НЕ вміє: розпізнати, що асистент сам мовчки звузив варіанти в
попередній рекомендації (це семантичне судження, не текстовий
паттерн) — окрема проблема, вже записана в пам'ять асистента, не
автоматизована тут.
"""
import sys
import json
import re

WORD_LIMIT = 12
CHAR_THRESHOLD = 300
LINE_THRESHOLD = 5

CONFIRM_WORDS = {
    "так", "yes", "ok", "окей", "ок", "да", "давай", "го", "добре",
    "роби", "зроби", "коміть", "закомить", "пуш", "запуш",
    "згоден", "згодна", "підтверджую", "продовжуй", "нехай",
}


def last_user_prompt(transcript_path):
    try:
        with open(transcript_path, encoding="utf-8") as f:
            lines = f.readlines()
    except (FileNotFoundError, OSError, TypeError):
        return None
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("type") == "last-prompt":
            return entry.get("lastPrompt")
    return None


def is_bare_confirmation(text):
    words = re.findall(r"[a-zA-Zа-яіїєА-ЯІЇЄ]+", text.lower())
    if not words or len(words) > 4:
        return False
    return all(w in CONFIRM_WORDS for w in words)


def edit_size(tool_name, tool_input):
    if tool_name == "Edit":
        new = tool_input.get("new_string", "")
    elif tool_name == "Write":
        new = tool_input.get("content", "")
    else:
        return 0, 0
    return len(new), new.count("\n")


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return

    tool_name = data.get("tool_name")
    if tool_name not in ("Edit", "Write"):
        return

    chars, newlines = edit_size(tool_name, data.get("tool_input", {}))
    if chars < CHAR_THRESHOLD and newlines < LINE_THRESHOLD:
        return  # тривіальна правка

    prompt = last_user_prompt(data.get("transcript_path", ""))
    if not prompt:
        return

    words = prompt.split()
    if len(words) > WORD_LIMIT or is_bare_confirmation(prompt):
        return  # достатньо розгорнутий запит або голе підтвердження

    context = (
        "P4 (постмортем): останній запит користувача короткий/можливо "
        "неоднозначний, а правка нетривіальна. Перевір критерії скіла "
        "request-brief (мета, межі, критерій готовності) перед тим, як "
        "продовжити — або явно поясни в тому ж повідомленні, чому це "
        "не потрібно."
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": context,
        }
    }))


if __name__ == "__main__":
    main()
