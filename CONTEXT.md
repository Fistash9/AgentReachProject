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

## Архітектура (оновлення 2026-09-18)
Знімок вище — стан на 2026-09-16, лишено без змін для історії.
Актуальний стан:
- **MCP-сервери (7 підключено):** agent-reach (3 tools), memory
  (9 tools, knowledge graph), transcriptor (8 tools, хостований,
  11 платформ), delegate (делегування на DeepSeek, ~98% економія
  vs Opus), baton (cross-agent handoff), deepseek (під-сесія на
  DeepSeek), claude.ai Claude Docs (8 tools, вбудований)
- **Python `mcp`:** встановлено 1.30.0, пінований `<2.0.0` (latest
  на pip зараз 2.2.0 — перевірено 2026-09-18, див. TROUBLES.md)
- **Скрипти-обгортки (усі через баг Claude Code #22571):**
  run-memory.sh, run-delegate.sh, run-baton.sh, run-deepseek.sh
- **Перший власний Skill:** session-close (закриття сесії,
  checkpoint, baton_pass)
- **Система верифікації:** RULES.md — "Рівні знань" (Sourced/
  Unverified/Hallucinated) + правило "Перед рекомендацією
  пакета/URL" + "Журнал vs знімок стану"

## Архітектура (оновлення 2026-09-19)
Знімки вище — стани на 2026-09-16 і 2026-09-18, лишено без змін.
Додано пізніше того самого дня (2026-09-18), не потрапило в
попередній знімок:
- **telegram_deepseek_bot.py** — MVP Telegram↔DeepSeek оркестратор,
  делегує кодові задачі Claude Code через `claude -p`. Секрети в
  `.env` (gitignored). Дефолт `CLAUDE_PERMISSION_MODE=plan` (безпечно,
  без виконання) — див. ECOSYSTEM.md, розділ про ризики
- **Другий власний Skill:** unlazy (anti-laziness, acceptance gates,
  встановлено project-scoped через `.claude/settings.local.json`)
- **MCP-сервери (8 підключено):** + pkgtruth (верифікація пакетів
  проти галюцинацій, wrapper run-pkgtruth.sh через баг shebang)

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

## Поточний фокус (оновлення 2026-09-18)
Гігієна документації та дисципліна верифікації: перевірка тверджень
перед записом у BACKLOG/TROUBLES (перевірка пакетів/URL, рівні знань
Sourced/Unverified/Hallucinated), розрізнення "журнал vs знімок стану"
у файлах проєкту, дослідження автоматизації рутинних процесів
(git-цикл, baton_pass). Транскрипція (YouTube/Instagram публічні) —
базово працює, TikTok/X і приватні Instagram-акаунти не тестовано.

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

## Оновлення 2026-09-20

Checkpoint: у файлі бракувало записів про 17 комітів (14eb3f8..040421f)
після останнього оновлення (0b71688, pkgtruth як 8-й MCP).

### Хуки (project-scoped, `.claude/settings.local.json`, gitignored)
Усі три — PreToolUse на Bash:
- **pkgtruth hook** — блокує інстал неіснуючих пакетів (14eb3f8)
- **troubles-grep-hook.py** — автоматизує правило "grep по
  TROUBLES.md перед дією" (d7b9b24)
- **baton-reminder-hook.py** — нагадує про baton_pass, якщо
  git push зроблено при застарілому baton (7ec9fa7)

### Нові файли
- **TRASH.md** — журнал видалень, записується ДО rm (2397883)
- **USER_PROFILE.md** — портрет користувача з реальних цитат
  транскрипту, прогнози позначені як гіпотези (2a3c69e, перебудовано
  4f637c0); перевірка підв'язана до session-close Skill (5cfea29)

### Нові правила в RULES.md
- Premortem перед нетривіальною дією (74401c4)
- Перевірка потрібна і перед "не варто", не тільки перед "варто"
  (f818ff9)
- Правила видалення файлів і .trash/ (2397883)

### BACKLOG / TROUBLES
- BACKLOG: A2A-апгрейд для telegram_deepseek_bot.py (421f430),
  tscribe (rvben/tscribe) як [unverified] кандидат (040421f),
  відновлено втрачений запис про pkgtruth (50876f8)
- TROUBLES: аудит транскрипту на повторювані/втрачені проблеми
  (99f1aa8), розслідування "tscribe" у baton next-полях (4ed6df4)

### Поточний фокус (оновлення 2026-09-20)
Перетворення написаних правил на автоматичні механізми (хуки,
skill-кроки) там, де правило виявилось "записаним, але не
практикованим".

## Оновлення 2026-09-20 (друга половина сесії)

Checkpoint: у файлі бракувало записів про 9 комітів (1c83cd7..b627629)
після попереднього оновлення (623f122).

### Хуки і обхід grep/find
- **SessionStart-хук** у `.claude/settings.local.json` (gitignored)
  дописує `unset -f grep find rg pkill` у `$CLAUDE_ENV_FILE` — обхід
  shim у Bash-інструменті Claude Code на Termux. Підтверджено в новій
  сесії: `grep` і `find` повертають код 0 (5a36bd9, 8ef6c8a, c1b734d).
  Першопричина (`CLAUDE_CODE_EXECPATH` = ld.so) не усунена, лише
  прихована

### Skills
- **request-brief** (прототип v0, b184914) — бриф перед роботою і
  звірка після
- **session-close** виправлено (b627629): крок 3.7 (перевірка
  TROUBLES.md/BACKLOG.md), попередження й ліміт 20 у фолбеку комітів
  скрипта, покажчик на правила видалення замість неповного переказу
- Аудит `.claude/skills` через delegate (2 виклики DeepSeek): з 12
  вибірково перевірених тверджень 6 підтверджено, 1 слабка, 1 без
  висновку, 4 спростовано (див. TROUBLES.md). Решта знахідок не
  застосована

### DeepSeek-делегування
- Правило "автоделегування за тригером без y/n" (19b039b) уперше
  застосоване на практиці: 2 виклики `delegate`, без y/n
- Хуки PreToolUse (читання великих файлів, Skill) досі виводять
  нагадування про y/n gate, що розходиться з правилом проєкту;
  узгодження не зроблено

### BACKLOG / ECOSYSTEM
- BACKLOG: дослідження everything-claude-code (91d4971)
- ECOSYSTEM: механізми перевірки розуміння запиту (1c83cd7), Hermes
  Agent / agent offices (8053fd0)

### Поточний фокус (оновлення 2026-09-20, друга половина)
Перевірка, що автоматизація працює в нових сесіях (SessionStart-хук,
автоделегування, крок 3.7), і доведення знахідок аудиту скілів до
рішення.

## Оновлення 2026-09-23
(22–23.09 до цієї сесії — див. baton ledger і TROUBLES.md записи з
датою 2026-09-22/23: хуки trash-md-guard, git-add-status,
delegate-prompt-improver, delegate-outcome-logger, request-brief-reminder
на Bash, env-фікси run-deepseek.sh.)

### Інфраструктура
- Claude Code **2.1.280** (було 2.1.273), `claude-code-termux doctor` —
  "All checks passed". Попередження VERSION DRIFT (npm-пакет 2.1.273)
  НЕ лікувати `claude-code-termux update` — він відкотить бінарник до
  2.1.273 (TROUBLES.md). `unrecognized_model` лишився й на 2.1.280.
- `menu.sh`: пункт 6 — `tools/watch-deepseek.py` (живі кроки під-сесій
  deepseek), пункт 7 — `claude-deepseek.sh` (інтерактивний Claude Code
  на DeepSeek; MCP на DeepSeek працює — правило про deep-claude має
  примітку).
- Під-сесії deepseek виконують хуки проєкту (UserPromptSubmit,
  PreToolUse, Stop/unlazy) — будь-який новий хук має це враховувати.

### Правила і їх історія
- **RULES-WHY.md** — чому кожне правило RULES.md таке (коміти, випадки,
  слова користувача). Хук **rules-why-guard** блокує правку RULES.md без
  свіжого запису там.
- RULES.md: перші правила переформульовано з поясненнями користувача
  («скоріш за все», «кілька команд» = задачі для користувача, «зараз
  спробуємо ще»); розділи «Задачі для користувача», «Git»; виняток
  tmp у видаленнях; точні шляхи в «Правилі 4»; правило «кожне
  твердження у звіті — з опорою на вивід сесії».

### Інструменти перевірки (tools/)
- `tools/check-links.py` — зв'язки проєкту (session-close, крок 2.5).
- `tools/claimcheck/` — заяви без опори в моїх відповідях за журналом
  сесії (крок 2.6). Звіт, НЕ хук: тест на історії показав, що Stop-хук
  не проходить пороги (E1 шумить, E3 не ловиться); E5-хук — BACKLOG.

### Дослідження (ECOSYSTEM/TROUBLES)
- Скіли Matt Pocock vs наша система (ECOSYSTEM.md): не замінювати,
  адаптувати RULES.md; плагін — вибірково.
- Готові рішення перевірки заяв агента (groundtruth, provenly,
  claude-integrity-gate) — TROUBLES.md; жоден не підходить як є.

### Поточний фокус (оновлення 2026-09-23)
Жити з новими правилами й звітом claimcheck кілька сесій і дивитися,
чи рідше треба питати «перевір ще раз». Відкрито: E5-хук (потрібні
дані), вартість pro/flash, grill-me/claude-setup, AI-атрибуція в комітах.
