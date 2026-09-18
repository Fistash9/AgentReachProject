# AGENTS.md — Router

## 1. Хто я
- Ім'я: Саша (Fistash9), Україна
- Мова спілкування: українська (технічні терміни — англійською, де звичніше)
- Рівень: впевнений користувач, не професійний розробник

## 2. Що таке Agent Reach
Персональний AI-агент у Termux (Android). Довгострокова мета — екосистема
агентів, де «агент вищого порядку» розподіляє задачі між іншими агентами.

## 3. Куди йти за деталями
- **RULES.md** — правила роботи (формат взаємодії, заборони, checkpoint)
- **CONTEXT.md** — паспорт проєкту, архітектура, історія сесій
- **BACKLOG.md** — відкладені задачі і статуси
- **TROUBLES.md** — підводні камені й рецепти рішень
- **HANDOFF.md** — стан передачі контексту між сесіями (Baton)
- **ECOSYSTEM.md** — концепції композиції агентів
- **README.md** — карта документації, Quick Start

## 4. Ключові команди
- `baton_pick_up` — підхопити контекст на старті сесії
- `baton_pass` — передати контекст перед завершенням
- `/cost` — витрати поточної сесії
- `/mcp` — стан MCP-серверів
- `/skills` — доступні Skills
- `/exit` — вихід із Claude Code
- `Ctrl+B, ?` — шпаргалка tmux (HELP.txt), `q` — закрити

## 5. Що НЕ робити
- ❌ Ставити `mcp` 2.x — ламає `list_tools` (agent-reach вимагає `mcp<2.0.0`)
- ❌ Використовувати deep-claude — MCP-сервери несумісні з DeepSeek Anthropic-шаром
- ❌ Тиснути Ctrl+C, щоб вийти з Claude Code на Termux — не реагує, треба `/exit`
- ❌ Комітити `agent.py` (містить ключ)
- ❌ Комітити/редагувати `memory.jsonl` вручну — локальний файл пам'яті, у .gitignore

## 6. BACKLOG — топ-5 (Активні)
1. llm-cost-router-mcp — MCP для cost-awareness
2. SERVER.md — доповнити розділом про tools
3. HELP.txt — оновити (delegate, baton, deepseek, Ctrl+B)
4. RULES.md — правило про повний промпт з межами для безпечних задач
5. Дослідити вбудовані Skills (anthropic-skills:*)

Деталі й повний список: див. BACKLOG.md.

## 7. Стан на сьогодні (2026-09-18)
- **Git:** чисто, останній коміт `3fd374f` (Add session-close Skill), запушено
- **Baton:** passed #12, status `in_progress`
- **MCP:** 7 серверів підключено (agent-reach, memory, transcriptor, delegate, baton, deepseek, Claude Docs)

---
Детальніше: див. RULES.md
