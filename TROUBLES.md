# TROUBLES — база знань проєкту Agent Reach

Як шукати (не читає весь файл, тільки знайдені рядки):
  grep -i "mcp 2" TROUBLES.md -A 6
  grep -i "cryptography" TROUBLES.md -A 6
  grep -i "dsh" TROUBLES.md -A 6

Кожен запис має мітку TAGS — шукай по ній.

---
## #01 — mcp 2.x: Server has no attribute list_tools
TAGS: mcp, list_tools, Server, AttributeError, версія
СИМПТОМ: AttributeError: 'Server' object has no attribute 'list_tools'
ПРИЧИНА: mcp 2.x видалив старий API, agent-reach його не підтримує
РІШЕННЯ: pip install "mcp<2.0.0"

---
## #02 — DSH на Termux падає
TAGS: dsh, glibc, glibc-runner, patch, glibc.node
СИМПТОМ: failed to patch glibc-runner / No command dsh found
ПРИЧИНА: DSH потребує glibc-patch, який не працює на Android
РІШЕННЯ: НЕ встановлювати DSH. Використовувати власний agent.py з requests

---
## #03 — pip install openai падає на jiter
TAGS: openai, jiter, Rust, maturin, build dependencies
СИМПТОМ: ERROR: Failed to build installable... jiter
ПРИЧИНА: openai тягне Rust-пакет jiter, який довго компілюється і падає
РІШЕННЯ: Не ставити openai. Використовувати requests + прямий HTTP до API

---
## #04 — cryptography: cannot locate symbol PyModule_Type
TAGS: cryptography, PyModule_Type, _rust.abi3.so, dlopen
СИМПТОМ: ImportError: dlopen failed: cannot locate symbol "PyModule_Type"
ПРИЧИНА: pip-версія cryptography несумісна з Python 3.14 у Termux
РІШЕННЯ: pkg install python-cryptography -y

---
## #05 — agent-reach rss / read не існують
TAGS: agent-reach, rss, read, команда, CLI
СИМПТОМ: error: argument command: invalid choice: 'rss'
ПРИЧИНА: у CLI agent-reach немає команд rss і read
РЕАЛЬНІ КОМАНДИ: setup, install, configure, doctor, uninstall, skill, format, transcribe, check-update, watch, version
РІШЕННЯ: RSS і сторінки читати через curl https://r.jina.ai/URL

---
## #06 — agent_reach.integrations.mcp_server дає лише get_status
TAGS: mcp_server, get_status, agent_reach.integrations
СИМПТОМ: OK Інструментів доступно: 1
ПРИЧИНА: офіційний MCP-сервер Agent Reach — це лише doctor-обгортка
РІШЕННЯ: писати власний my_mcp_server.py з потрібними tools

---
## #07 — Rust-компіляція здається зависанням
TAGS: Rust, rustc, cargo, maturin, зависання, довго
СИМПТОМ: термінал стоїть без виводу годинами
ПРИЧИНА: компіляція Rust-пакетів на телефоні повільна
РІШЕННЯ: перевірити в новій сесії: ps aux | grep -E 'cargo|rustc'
         Чекати 15–40 хв. Не вбивати сесію.

---
## #08 — DeepSeek: Insufficient Balance
TAGS: DeepSeek, Insufficient Balance, баланс, поповнення
СИМПТОМ: ERROR сервера: {'error': {'message': 'Insufficient Balance'}}
ПРИЧИНА: нульовий баланс на platform.deepseek.com
РІШЕННЯ: поповнити баланс (мін. $2). Модель deepseek-chat дуже дешева.

---
## #09 — команди терміналу вставлені у вікно агента
TAGS: agent.py, Ви:, вставка, shell, галюцинація
СИМПТОМ: агент починає вигадувати XML-синтаксис і коментувати код
ПРИЧИНА: команду введено у `Ви:` замість терміналу
РІШЕННЯ: написати `exit` щоб вийти з агента, потім виконати в shell

---
## #10 — GitHub username плутанина
TAGS: GitHub, Fistash9, i, 1, нікнейм
СИМПТОМ: репозиторій не знайдено при пуші
ПРИЧИНА: у нікнеймі літера i, не цифра 1
РІШЕННЯ: git@github.com:Fistash9/AgentReachProject.git

---
## #11 — agent.py потрапив у git (API-ключ)
TAGS: git, API-ключ, agent.py, .gitignore, секрет
СИМПТОМ: git status показує agent.py серед нових файлів
ПРИЧИНА: agent.py не був у .gitignore
РІШЕННЯ: echo "agent.py" >> .gitignore
         Тримати шаблон agent.py.example без ключа


## Claude Code + MCP (підключено 2026-09-16)

### Встановлення
curl -fsSL https://raw.githubusercontent.com/bd-loser/claude-code-termux/main/install.sh | bash
exec bash

### Реєстрація MCP-сервера
claude mcp add --transport stdio agent-reach -- python ~/AgentReachProject/my_mcp_server.py

### Перевірка
claude mcp list          # має показати ✔ Connected
claude                   # запуск сесії, потім /mcp

### Використання
- Claude Code викликає інструменти як mcp__agent-reach__read / transcribe / status
- Той самий my_mcp_server.py обслуговує і рідний agent, і Claude Code
- Новий інструмент додаєш один раз — бачать обидва агенти

### Підводні камені
- Потрібен mcp 1.x (у нас 1.30.0) — 2.x ламає list_tools
- Без підписки Claude Pro/Max або API-білінгу Anthropic Claude Code не працює
- Тема: Dark mode обрано; довіра до папки ~/AgentReachProject — Yes

### Ідеї на майбутнє (НЕ робити поки що)
- Telegram-бот для керування Claude Code (hoquem/claude-code-telegram-bridge)
- Делегування задач на DeepSeek (deepseek-mcp, claude-code-deepseek-delegator)

## Transcriptor MCP (підключено 2026-09-17)

### Що це
Хостований MCP-сервер для транскрипції відео/аудіо з 11 платформ:
YouTube, Twitter/X, Instagram, TikTok, Twitch, Vimeo, Facebook,
Bilibili, VK, Dailymotion тощо.

### Підключення
claude mcp add --transport http transcriptor https://transcriptor.gateway.mcpal.io/mcp

### Авторизація
1. Запустити `claude`
2. Ввести `/mcp`
3. Обрати `transcriptor` → Enter → `Authenticate`
4. Пройти OAuth у браузері (на Termux може не відкритись — копіювати URL вручну)

### Використання
Попросіть Claude Code: "Use transcriptor to get transcript of <URL>"
Для конкретної мови: додати "in English" або "with lang=en"

### Підводні камені
- За замовчуванням може повернути НЕ ту мову (наприклад, німецьку
  офіційну доріжку замість англійської). Вказуйте мову явно.
- Хостований сервіс — запити йдуть через чужий сервер. Тільки для
  публічних відео.
- Після `claude mcp add` потрібен ПЕРЕЗАПУСК Claude Code, щоб
  сервер з'явився в `/mcp` (у поточній сесії він не підтягується).

### URL gateway
https://transcriptor.gateway.mcpal.io/mcp
