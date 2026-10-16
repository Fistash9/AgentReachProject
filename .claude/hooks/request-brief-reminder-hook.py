#!/data/data/com.termux/files/usr/bin/python3
"""
PreToolUse hook: нагадує про критерії скіла request-brief ПЕРЕД
нетривіальною правкою (Edit/Write), коли повідомлення користувача,
що передувало правці, коротке/неоднозначне.

P4 з постмортему (TROUBLES.md, "Прогін сценариста..."): request-brief
не мав жодного автоматичного тригера, на відміну від делегатора
DeepSeek (UserPromptSubmit-хук), тому регулярно пропускався.

Евристика для Edit/Write (без LLM, нічого не блокує):
- бере останній людський запит з transcript_path (запис "last-prompt",
  формат JSONL — перевірено на реальному транскрипті цієї сесії)
- короткий/неоднозначний: <=12 слів і НЕ голе підтвердження вже
  запропонованого ("так", "роби", "коміть" тощо)
- нетривіальна правка: >=300 символів нового тексту або >=5 нових рядків

Друга евристика, для Bash (додано 2026-09-23, TROUBLES.md
"Додатковий урок про методологію тестування"): спрацьовує, коли
команда має ознаки "ручного відтворення поведінки іншого
скрипта/процесу без звірки з джерелом" — 2+ `export VAR=` разом із
викликом `claude`. Саме цей патерн сьогодні дав хибну впевненість
"перевірено живим тестом" (ручний тест не мав `--model`, а реальний
скрипт його теж не передає — але це з'ясувалось випадково, не через
нагадування).

НЕ вміє: розпізнати, що асистент сам мовчки звузив варіанти в
попередній рекомендації (це семантичне судження, не текстовий
паттерн) — окрема проблема, вже записана в пам'ять асистента, не
автоматизована тут.
"""
import sys
import json
import re
import shlex

WORD_LIMIT = 12
CHAR_THRESHOLD = 300
LINE_THRESHOLD = 5
EXPORT_THRESHOLD = 2

CONFIRM_WORDS = {
    "так", "yes", "ok", "окей", "ок", "да", "давай", "го", "добре",
    "роби", "зроби", "коміть", "закомить", "пуш", "запуш",
    "згоден", "згодна", "підтверджую", "продовжуй", "нехай",
}

HEREDOC_START_RE = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?")
SEPARATORS = {";", "&&", "||", "&", "|", "(", ")"}


def strip_heredocs(command):
    """Прибирає тіло heredoc (між <<'EOF' і рядком EOF) — інакше
    текст усередині (напр. commit-повідомлення, де описано export/
    claude) сприймається як реальні команди. Той самий підхід, що в
    trash-md-guard-hook.py / git-add-status-hook.py (TROUBLES.md,
    2026-09-23)."""
    lines = command.split("\n")
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        m = HEREDOC_START_RE.search(line)
        if m:
            delim = m.group(1)
            i += 1
            while i < len(lines) and lines[i].strip() != delim:
                i += 1
            i += 1
            continue
        i += 1
    return "\n".join(out)


CMD_SUBST_RE = re.compile(r"\$\([^()]*\)")


def _skip_wrapper_prefix(tokens, i):
    """Пропускає відомі обгортки (`sudo`, `timeout N`), щоб знайти
    токен РЕАЛЬНОЇ програми, яку запускають, а не саму обгортку."""
    if i < len(tokens) and tokens[i] == "sudo":
        i += 1
    if i < len(tokens) and tokens[i] == "timeout":
        i += 1
        if i < len(tokens) and re.fullmatch(r"[\d.]+[smhd]?", tokens[i]):
            i += 1
    return i


def command_start_tokens(command):
    """Токени РЕАЛЬНИХ програм на позиції початку якоїсь команди в
    багатокомандному рядку (після роздільника чи на самому початку),
    з пропуском відомих обгорток (`sudo`, `timeout N`). Токенізація
    через shlex (поважає лапки) — на відміну від "regex по всьому
    рядку", текст у лапках/аргумент іншої команди (напр. echo "...
    claude ...") НЕ розпізнається як реальний виклик. Голі переноси
    рядків замінюються на `;`, бо shlex сприймає `\\n` як звичайний
    пробіл, а не роздільник команд. `$(...)` (без вкладеності)
    прибирається ДО токенізації — shlex не розуміє command
    substitution як єдиний блок, і `|`/`;` усередині неї ламали б
    токенізацію зовнішньої команди."""
    normalized = CMD_SUBST_RE.sub("X", command)
    normalized = normalized.replace("\n", " ; ")
    try:
        lexer = shlex.shlex(normalized, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return []

    starts = []
    at_start = True
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in SEPARATORS:
            at_start = True
            i += 1
            continue
        if at_start:
            j = _skip_wrapper_prefix(tokens, i)
            if j < len(tokens):
                starts.append(tokens[j])
        at_start = False
        i += 1
    return starts


def bash_verification_risk(command):
    """True, якщо команда виглядає як ручне відтворення поведінки
    іншого скрипта/процесу (2+ export + виклик claude, обидва як
    РЕАЛЬНІ команди, не текст у лапках) — сигнал звірити аргументи з
    реальним кодом джерела, не з пам'яті."""
    if not command:
        return False
    starts = command_start_tokens(strip_heredocs(command))
    export_count = starts.count("export")
    return export_count >= EXPORT_THRESHOLD and "claude" in starts


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


SYS_RE = re.compile(r"^\s*<(?:system-reminder|command-|local-command|task-notification|bash-)")
ANSWER_RE = re.compile(r"\s*(?:User has answered your questions|The user answered|"
                       r"Your questions have been answered):(.*)", re.S)
# коротке пряме доручення записати / закомітити / закрити — ясне (рішення користувача 2026-10-16,
# відступ від буквального «голе підтвердження» з SKILL.md — названо в плані)
RECORD_WORDS = {"запиши", "записуй", "допиши", "дописуй", "коміть", "комить", "закомить",
                "зберігай", "збережи", "закрий", "закривай", "пуш", "запуш"}


# лише слова згоди: «зроби аналіз» — доручення, не підтвердження (тест 2026-10-16 впіймав, що з
# CONFIRM_WORDS «зроби/роби/давай + щось» ставало «так»)
AGREE_WORDS = {"так", "yes", "ok", "окей", "ок", "да", "добре", "згоден", "згодна", "підтверджую"}


# Доручення вибору асистенту — двозначне за природою, хоч і довге (2026-10-16, рішення користувача «Так,
# потім жива перевірка»): «як буде раціональніше… так і роби» мала 13 слів, поріг 12 її пропускав. Бектест
# 63 сесій: 17 таких рішень у 13 сесіях, 14 довші за 12 слів. Межа DELEGATE_MAX_WORDS — розписані
# завдання («КРОК 1 — …», 179 слів) уже і є брифом.
DELEGATE_RE = re.compile(r"як (?:буде )?(?:раціональн|краще|вважаєш|правильн)|на твій розсуд|сам виріш|"
                         r"що краще зробити|як що буде корисн|так і роби|обери раціональн", re.I)
DELEGATE_MAX_WORDS = 60


def last_decision(transcript_path):
    """Останнє рішення людини: ("typed", текст) — набране повідомлення; ("option", …) — обрано
    готовий варіант у віконці AskUserQuestion; ("free", текст) — у віконці вписано своє.
    2026-10-16 (сесія 0577c90b, користувач: «і що з брифом повідомлення є але воно не працює»):
    last-prompt не бачить відповідей у віконцях — хук 12 разів нагадав на «почнімо сесію», а на
    єдину справжню потребу (вписану відповідь «як буде раціональніше… так і роби») мовчав.
    Бектест 63 сесій: 298 → 105 нагадувань (agents/claude-code/q12-classes-2026-10-16/)."""
    try:
        with open(transcript_path, encoding="utf-8") as f:
            lines = f.readlines()
    except (FileNotFoundError, OSError, TypeError):
        return None
    labels, dec = {}, None
    for line in lines:
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("type") == "assistant":
            for b in d.get("message", {}).get("content") or []:
                if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "AskUserQuestion":
                    labels[b.get("id")] = {o.get("label", "").strip()
                                           for q in b.get("input", {}).get("questions", [])
                                           for o in q.get("options", [])}
            continue
        if d.get("type") != "user" or d.get("isMeta"):
            continue
        c = d.get("message", {}).get("content")
        if isinstance(c, str):
            if c.strip() and not SYS_RE.match(c):
                dec = ("typed", c)
            continue
        for b in c or []:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "text" and b.get("text", "").strip() and not SYS_RE.match(b["text"]):
                dec = ("typed", b["text"])
            elif b.get("type") == "tool_result" and b.get("tool_use_id") in labels:
                t = b.get("content")
                t = t if isinstance(t, str) else " ".join(
                    x.get("text", "") for x in t or [] if isinstance(x, dict))
                m = ANSWER_RE.match(t)
                if not m:
                    continue
                body = re.split(r"You can now continue|Read the answers carefully", m.group(1))[0]
                answers = re.findall(r'"=\s*"(.*?)"(?=\s*(?:,\s*"|\.|$))', body, re.S) or [body]
                own = [a for a in answers if a.strip() not in labels[b["tool_use_id"]]]
                dec = ("free", " ".join(own)) if own else ("option", " / ".join(answers))
    return dec


def is_bare_confirmation(text):
    words = re.findall(r"[a-zA-Zа-яіїєА-ЯІЇЄ]+", text.lower())
    if not words or len(words) > 4:
        return False
    return all(w in CONFIRM_WORDS for w in words)


def is_confirmation(text):
    """Голе підтвердження АБО «так, <коротке доручення>» / «запиши…» (≤6 слів)."""
    w = re.findall(r"[a-zA-Zа-яіїєґА-ЯІЇЄҐ']+", text.lower())
    return is_bare_confirmation(text) or (
        0 < len(w) <= 6 and (w[0] in AGREE_WORDS or w[0] in RECORD_WORDS))


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

    if tool_name == "Bash":
        command = data.get("tool_input", {}).get("command", "")
        if not bash_verification_risk(command):
            return
        context = (
            "Ручне відтворення поведінки іншого скрипта/процесу (кілька "
            "export + виклик claude) — перед тим як вважати це "
            "'перевіреним живим тестом', звір аргументи виклику з "
            "РЕАЛЬНИМ кодом джерела (grep реального скрипта), не з "
            "пам'яті. TROUBLES.md: 'Додатковий урок про методологію "
            "тестування' (2026-09-23)."
        )
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": context,
            }
        }))
        return

    if tool_name not in ("Edit", "Write"):
        return

    chars, newlines = edit_size(tool_name, data.get("tool_input", {}))
    if chars < CHAR_THRESHOLD and newlines < LINE_THRESHOLD:
        return  # тривіальна правка

    dec = last_decision(data.get("transcript_path", ""))
    if not dec or dec[0] == "option":
        return  # немає рішення або обрано готовий варіант з описом (він і є бриф)
    prompt = dec[1]

    words = prompt.split()
    delegated = DELEGATE_RE.search(prompt) and len(words) <= DELEGATE_MAX_WORDS
    if not delegated and (len(words) > WORD_LIMIT or is_confirmation(prompt)):
        return  # достатньо розгорнутий запит або підтвердження вже запропонованого

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
