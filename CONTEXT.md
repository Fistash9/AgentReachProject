# Agent Reach — Контекст проєкту

> Паспорт проєкту. Читається на початку нової сесії, щоб агент одразу
> розумів, де ми, що робимо і як тут усе влаштовано.
>
> **Оновлюється ДО стиснення контексту.** Коли діалог наближається до
> межі (60-70% заповнення) — робимо checkpoint: підсумовуємо важливе
> у файл, комітимо, і тільки потім продовжуємо. Так нічого не губиться,
> навіть якщо далі контекст стиснеться.

## Про мене (автора)
- Ім'я: Саша (Fistash9)
- Локація: Україна
- Мова спілкування: українська (технічні терміни — англійською, де звичніше)
- Режим роботи: «активний коли вийде» — без фіксованого графіка
- Рівень: впевнений користувач, не професійний розробник

## Що це за проєкт
Agent Reach — персональний AI-агент у Termux (Android).
Довгострокова мета: побудувати екосистему агентів, де «агент вищого
порядку» (делегуючий) розподіляє задачі між іншими агентами, обираючи
найкращий варіант для кожної підзадачі. Agent Reach — перший у цій
екосистемі і шаблон для наступних.

## Архітектура (станом на 2026-09-16)
- **Папка:** ~/AgentReachProject
- **GitHub:** git@github.com:Fistash9/AgentReachProject.git
- **Твій агент:** команда `agent` (alias на start.sh), модель DeepSeek chat
- **Claude Code:** встановлено, працює через підписку Claude Pro
- **MCP-сервер:** my_mcp_server.py (той самий для обох агентів)
- **Інструменти MCP (agent-reach):** read (сторінки через r.jina.ai), transcribe, status
- **MCP (transcriptor):** хостований, транскрипція YouTube/TikTok/X/Instagram (11 платформ). URL: https://transcriptor.gateway.mcpal.io/mcp

## Принципи роботи
- Все робимо **покроково**: одна дія — один результат — перевірка
- Складні задачі — розбиваємо на етапи
- Перед новою дією — grep по TROUBLES.md
- Перед git add — завжди git status
- Раціональність важливіша за швидкість
- Пояснення — достатні, щоб я розумів «чому», без зайвої води

## Що НЕ робити (жорсткі правила)
- ❌ Не ставити DSH на Termux (падає через glibc-runner)
- ❌ Не ставити mcp 2.x — ламає list_tools
- ❌ Не ставити openai через pip (тягне Rust-залежність jiter)
- ❌ Не ставити cryptography через pip — тільки pkg install python-cryptography
- ❌ Не комітити agent.py (ключ!)
- ❌ Не використовувати agent_reach.integrations.mcp_server (тільки get_status)
- ❌ Не вигадувати agent-reach rss/read — таких команд немає
- ❌ Не вставляти команди терміналу у вікно `Ви:` агента

## Робоче середовище
- **Запуск:** при відкритті Termux автоматично з'являється menu.sh
- **tmux:** 3 вікна — 0:claude, 1:agent, 2:shell
- **Шпаргалка:** Ctrl+B, ? → popup з HELP.txt (q = закрити)
- **Статус-бар:** AR · вікна · C-b ?=help · годинник

## Поточний фокус (2026-09-16)
Транскрипція аудіо/відео з різних джерел — БАЗОВО ПРАЦЮЄ через
джерел (YouTube, TikTok, X, подкасти тощо) — і додавати нові джерела
без переписування логіки.

## Відкриті питання / ідеї на майбутнє
- Екосистема агентів: делегуючий агент розподіляє задачі між іншими
- Telegram-бот для керування Claude Code (відкладено)
- Делегування задач на DeepSeek (deepseek-mcp) — економія токенів Claude

## Історія сесій (останні)
- 2026-09-16: Підключено Claude Code + MCP, створено tmux-меню та HELP.txt
- 2026-09-17: Підключено transcriptor MCP, перевірено транскрипцію YouTube

## Оновлення 2026-09-17 (композиція агентних систем)

### Додано
- ECOSYSTEM.md — концептуальний документ про композицію агентів
- Описує: MCP + A2A, FastMCP mount/import_server, реєстри (Glama,
  Smithery, AWS), чекліст сумісності нового агента

### Принцип
Кожен новий проєкт в екосистемі Agent Reach має:
1. Унікальний простір імен (наприклад, agent_reach:read)
2. Структурований I/O (JSON Schema)
3. Маніфест з версією та залежностями
4. Сумісну версію MCP-протоколу

Деталі — в ECOSYSTEM.md.

## Оновлення 2026-09-17 (memory MCP + BACKLOG)

### Додано
- **memory MCP** — knowledge graph пам'ять (9 інструментів)
- **Запуск:** через `run-memory.sh` (обгортка, обходить баг Claude Code #22571)
- **Файл пам'яті:** `memory.jsonl` у папці проєкту (у .gitignore)
- **BACKLOG.md** — список відкладених задач

### MCP-сервери (4 підключені)
- agent-reach (3 tools) — read, transcribe, status
- memory (9 tools) — knowledge graph
- transcriptor (8 tools) — транскрипція 11 платформ
- claude.ai Claude Docs (8 tools) — вбудований

### Правила активовані
- CLAUDE.md → RULES.md (симлінк, автозавантаження)
- Перевірка через /context → Memory files

### Відкладено (в BACKLOG.md)
- Instagram Reels, DeepSeek CLI, A2A, skills/agents, MCP-маніфест

## Оновлення 2026-09-17 (делегування DeepSeek)

### Додано
- **Delegate MCP** — claude-code-deepseek-delegator (делегування на DeepSeek)
- **Скрипт:** run-delegate.sh (читає ключ з agent.py, обхід бага #22571)
- **Hook:** файли > 300 рядків → питає «Delegate? (y/n)»
- **Економія:** 98% vs Opus (перевірено: 500 рядків → $0.0002 замість $0.0095)

### MCP-сервери (5 підключені)
- agent-reach (3 tools) — read, transcribe, status
- memory (9 tools) — knowledge graph
- transcriptor (8 tools) — транскрипція 11 платформ
- **delegate** — делегування важких задач на DeepSeek ← новий
- claude.ai Claude Docs (8 tools) — вбудований

### Скрипти-обгортки (обидва через баг #22571)
- run-memory.sh — для memory MCP
- run-delegate.sh — для delegate MCP

### Відкладено (в BACKLOG.md)
- Instagram Reels, DeepSeek CLI, A2A, skills/agents, MCP-маніфест

## Оновлення 2026-09-17 (Baton — cross-agent handoff)

### Додано
- **Baton MCP** — zero-dependency, передача контексту між агентами
- **Скрипт:** run-baton.sh (обхід таймауту npx)
- **Файли:** .baton/ (стан), HANDOFF.md (авто-генерований), AGENTS.md -> CLAUDE.md
- **6 інструментів:** baton_status, baton_pick_up, baton_pass,
  baton_log, baton_history, baton_init

### MCP-сервери (6 підключені)
- agent-reach (3 tools)
- memory (9 tools)
- transcriptor (8 tools)
- delegate — делегування на DeepSeek (економія 98%)
- **baton** — cross-agent handoff ← новий
- claude.ai Claude Docs (8 tools)

### Правила Baton (у RULES.md)
- На старті сесії — baton_pick_up
- Перед завершенням — baton_pass
- .baton/ і HANDOFF.md — у .gitignore

### Скрипти-обгортки (усі через баг #22571)
- run-memory.sh
- run-delegate.sh
- run-baton.sh

## Оновлення 2026-09-17 (deepseek — під-сесія на DeepSeek)

### Додано
- **deepseek MCP** — 7-й MCP-сервер, під-сесія Claude Code на DeepSeek
  (для розмов/рутини, окремо від delegate)
- **Скрипт:** run-deepseek.sh (4-та обгортка, читає ключ з agent.py)
- **Відкинуто:** deep-claude — MCP-сервери несумісні з
  DeepSeek Anthropic-сумісним шаром (офіційна документація DeepSeek)

### MCP-сервери (7 підключені)
- agent-reach (3 tools)
- memory (9 tools)
- transcriptor (8 tools)
- delegate — делегування на DeepSeek (економія 98%)
- baton — cross-agent handoff
- **deepseek** — сесія-чат на DeepSeek ← новий
- claude.ai Claude Docs (8 tools)

### Скрипти-обгортки (усі через баг #22571)
- run-memory.sh
- run-delegate.sh
- run-baton.sh
- run-deepseek.sh

## Навігація
- README.md — карта документації та Quick Start
- RULES.md — правила роботи
- TROUBLES.md — підводні камені
- BACKLOG.md — відкладені задачі
- ECOSYSTEM.md — концепції композиції агентів
- SERVER.md — опис MCP-сервера
- HANDOFF.md — стан передачі контексту (Baton)

## Оновлення 2026-09-17 (після deepseek)

- Fix deepseek TMPDIR (коміт 12d4329)
- mcp-probe перевірка всіх 7 MCP-серверів (5 PASS, 2 вбудовані)
- Відхилення llm-routing і chuzom-router (конфлікт mcp>=2.0.0)
- Рішення: залишитись на mcp<2.0.0, міграція готова під ключ
- session-timer.sh з EMA-прогнозом (α=0.3)
- Instagram Reels — вирішено для публічних (без cookies)
- Виявлено вбудовані Skills (perevirka-dzherel, skill-creator)

## Оновлення 2026-09-18

- session-close Skill створено (перший власний Skill,
  `.claude/skills/session-close/`)
- Skills security audit: 3 скіли перевірено (2 низький, 1 середній)
