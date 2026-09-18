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

## Локальна транскрипція аудіо/відео (налаштовано 2026-09-17)

### Що це
Повний офлайн-цикл: URL → аудіо → текст. Без хмарних сервісів.

### Компоненти
- **yt-dlp** — завантаження відео/аудіо (вже був у Termux)
- **ffmpeg** — конвертація форматів (pkg install ffmpeg)
- **termux-whisper** — обгортка над whisper.cpp
- **Моделі Whisper** — ggml-base.bin (~142 МБ), ggml-small.bin (~465 МБ)

### Встановлення termux-whisper
curl -sL https://raw.githubusercontent.com/itsmuaaz/termux-whisper/main/install.sh | bash
pkg install ncurses-utils -y

### Моделі — де лежать
~/termux-whisper/whisper.cpp/models/ggml-{base,small}.bin

### Як завантажити модель (якщо треба)
cd ~/termux-whisper/whisper.cpp && bash ./models/download-ggml-model.sh small

⚠️ Пряме завантаження з hf-mirror.com і github.com/releases часто
обривається. Офіційний скрипт download-ggml-model.sh працює надійно.

### Використання (приклад)
mkdir -p ~/tmp && cd ~/tmp
yt-dlp -x --audio-format mp3 --download-sections "*0-30" -o "test.%(ext)s" "<URL>"
whisper ~/tmp/test.mp3 --model small

### Результат
~/tmp/test_TRANSCRIPT.txt (або .srt, .vtt — залежно від прапорців)

### Підводні камені
- /tmp у Termux недоступний для запису → використовувати ~/tmp
- У меню Actions після транскрипції НЕ тиснути 1, 2, 3 — можуть
  зависнути (Open/Clipboard/Share). Тільки 4 = вихід.
- Модель base на музиці плутає слова. Для мовлення краще small.
- Whisper — для МОВЛЕННЯ, не для пісень. На співі помиляється
  навіть large.
- DNS у Termux іноді відвалюється: тоді
  echo 'nameserver 8.8.8.8' > $PREFIX/etc/resolv.conf
  echo 'nameserver 1.1.1.1' >> $PREFIX/etc/resolv.conf

### Порівняння моделей (RAM / розмір / якість)
- tiny:   ~1 ГБ  / 75 МБ  / базова
- base:   ~1 ГБ  / 142 МБ / хороша
- small:  ~2 ГБ  / 465 МБ / краща  ← використовуємо
- medium: ~5 ГБ  / 1.5 ГБ / висока (повільно на телефоні)
- large:  ~10 ГБ / 3 ГБ   / найкраща (не для мобільного)

## Claude Code MCP — підводні камені (2026-09-17)

### Синтаксис `claude mcp add`
- Назва сервера йде ПЕРЕД опціями:
  `claude mcp add NAME --transport stdio -e KEY=value -- command args`
- `--env` НЕ працює — тільки `-e`
- Якщо `-e` поставити перед назвою — парсер з'їдає назву як значення

### Node-сервери
- Claude Code має мінімальний PATH → симвлінки не знаходяться
- Треба АБСОЛЮТНІ шляхи:
  `/data/data/.../bin/node /data/data/.../node_modules/.../dist/index.js`
- Симлінк `mcp-server-memory` не працює → `ENOENT: posix_spawn`

### Баг: env-змінні не передаються
- Claude Code (issue #22571) НЕ передає env з конфігу в stdio-процес
- Наслідок: `MEMORY_FILE_PATH` ігнорується, файл створюється в папці пакета
- Обхід: скрипт-обгортка, який сам ставить змінну і запускає сервер

### Несумісний MCP
- `maxylev/modelcontextprotocol` — stateless MCP 2026-07-28, без `initialize`
- Claude Code для stdio очікує `initialize` → `-32601: initialize`
- `MCP_PROTOCOL_NEGOTIATION=auto` не допомагає, якщо сервер не має initialize

### server-memory (офіційний)
- Файл пам'яті: `memory.jsonl` (НЕ `memory.json`!)
- Читає `MEMORY_FILE_PATH`, якщо абсолютний шлях
- Але Claude Code його не передає (див. баг вище)

### CLAUDE.md (автозавантаження)
- Claude Code автоматично читає `CLAUDE.md` з кореня проєкту
- Перевірка: команда `/context` → секція `Memory files`
- Симлінк краще робити ВІДНОСНИМ (`RULES.md`, не абсолютний шлях)
- Git зберігає симлінк з `create mode 120000`

### termux-whisper — меню Actions
- Після транскрипції НЕ тиснути 1, 2, 3 — можуть зависнути
- Тільки 4 (Main Menu / Exit)
- Результат читати через `cat ~/tmp/*_TRANSCRIPT.txt`

### Візуальні артефакти при вставці виводу в чат
- **Симптом:** `cat file` у чаті показує «сміттєві» рядки (наприклад, `cat > ... << 'EOF'` посеред вмісту) і склеєні рядки — хоча у файлі їх немає.
- **Причина:** склеювання/спотворення при копіюванні виводу терміналу у вікно чату.
- **Правило:** НЕ робити деструктивних операцій (sed/tail/truncate) на основі побаченого у вставці.
- **Перевірка перед будь-яким редагуванням:** `wc -l file && grep -c "підозрілий_рядок" file` — цифри не брешуть, на відміну від відображення.
- **Перед редагуванням — бекап:** `cp file file.bak` (врятувало цього разу).
- **Дата:** 2026-09-17

## Baton MCP — cross-agent handoff (2026-09-17)

### Що це
Zero-dependency MCP-сервер для передачі контексту між агентами
(Claude Code, Codex, DeepSeek, будь-який MCP-клієнт).
Репозиторій: github.com/timurabi3/baton-mcp
Версія: 0.1.0

### Як працює
- Створює .baton/ у проєкті (baton.json, ledger.jsonl)
- Генерує HANDOFF.md у корені — читають усі агенти
- Створює симлінк AGENTS.md -> CLAUDE.md (універсальний стандарт)
- 6 інструментів: baton_status, baton_pick_up, baton_pass,
  baton_log, baton_history, baton_init

### Встановлення (Termux)
npm install -g github:timurabi3/baton-mcp

### Скрипт-обгортка (обхід таймауту npx)
~/AgentReachProject/run-baton.sh:
  #!/data/data/com.termux/files/usr/bin/bash
  export BATON_AGENT="claude-code"
  exec /data/data/.../bin/node /data/data/.../node_modules/@timurabi3/baton-mcp/server.mjs

### Реєстрація
claude mcp add baton --transport stdio -- ~/AgentReachProject/run-baton.sh

### Що ігнорувати в git
- .baton/ (стан handoff)
- HANDOFF.md (авто-генерований, змінюється часто)
- AGENTS.md — НЕ ігнорувати (це симлінк на CLAUDE.md)

### Підводні камені
- npx напряму з GitHub НЕ працює (CONNECTION_CLOSED — таймаут)
- Рішення: глобальна установка + скрипт-обгортка (як memory, delegate)
- baton_init не приймає ціль — тільки створює .baton/
  Ціль задається через baton_pass
- Після init треба зробити baton_pass, щоб з'явився HANDOFF.md

## deepseek-mcp — під-сесія на DeepSeek (2026-09-17)
TAGS: deepseek, deepseek-mcp, run-deepseek.sh, deep-claude

### Встановлення
npm install -g deepseek-mcp

### Скрипт-обгортка run-deepseek.sh
export DEEPSEEK_API_KEY (читається з agent.py) + PATH, потім exec
запускає deepseek-mcp сервер (та сама схема обходу бага #22571,
що й у run-memory.sh / run-delegate.sh / run-baton.sh).

### Факт: deep-claude несумісний з MCP
За офіційною документацією DeepSeek, MCP-сервери не працюють через
Anthropic-сумісний шар DeepSeek — тому deep-claude як обгортку
відкинуто. Використовувати deepseek-mcp напряму.

## Claude Code на Termux — вихід (2026-09-17)

- Ctrl+C НЕ виходить з Claude Code на Termux (не реагує)
- Треба використовувати /exit + Enter
- Виявилено емпірично (Саша)

## MCP-probe результати 2026-09-17
TAGS: mcp-probe, health-check, schema, validation

### Встановлення
npm install -g @incultnitollc/mcp-probe — встановився без помилок (113 пакетів).
На Termux/ARM64 бінарник `mcp-probe` не запускається напряму:
  /usr/bin/env: bad interpreter: No such file or directory
Причина: shebang `#!/usr/bin/env node`, а в Termux немає /usr/bin/env
(шлях інший: /data/data/com.termux/files/usr/bin/env).
ОБХІД: запускати напряму через node:
  node /data/data/com.termux/files/usr/bin/mcp-probe test "<команда>"

### Результати по серверах

| Сервер | Tools | Схема | Виклики | Статус |
|---|---|---|---|---|
| agent-reach | 3/3 | 0 помилок, 0 попереджень | 3/3 callable (макс. 5428ms — status) | ✅ PASS |
| memory | 9/9 | 0 помилок, 4 попередження | 9/9 callable | ✅ PASS (з попередженнями) |
| delegate | 4/4 | 0 помилок, 0 попереджень | 4/4 callable (макс. 3537ms — delegate) | ✅ PASS |
| baton | 6/6 | 0 помилок, 9 попереджень | 6/6 callable (усі <10ms) | ✅ PASS (з попередженнями) |
| deepseek | 2 знайдено | 0 помилок, 0 попереджень | 0/2 callable | ❌ FAIL |
| Claude Docs | — | — | — | не тестувалось (вбудований сервер claude.ai, немає окремого запускного скрипта/шляху — mcp-probe тестує лише локальні процеси) |
| transcriptor | — | — | — | не тестувалось (не було в списку команд, хостований сервер) |

### memory — попередження (не критично)
Property "entities"/"relations"/"observations"/"deletions" missing description
— 4 поля в JSON Schema без опису. Функціонал не порушено.

### baton — попередження (не критично)
9 полів без опису (project, status, openQuestions, note, limit тощо)
у baton_pick_up/baton_pass/baton_log/baton_history/baton_init.
Функціонал не порушено.

### deepseek — помилка виклику tools
FAIL deepseek і deepseek-reply: з'єднання і listing tools пройшли ОК,
але виклик інструменту падає:
  claude exited with code 1: ⚠ claude.ai connectors are disabled
  because ANTHROPIC_API_KEY or another auth source is set...
  EACCES: permission denied, mkdir '/tmp/claude-10599'
Причина (гіпотеза, не перевірялась): сабпроцес claude, який запускає
run-deepseek.sh, намагається створити свою scratchpad-теку в /tmp,
куди немає прав запису в середовищі, де його спускає mcp-probe;
плюс конфлікт ANTHROPIC_API_KEY з підключеними claude.ai-конекторами.
Не виправлялось за завданням — лише зафіксовано.

## MCP SDK 2.x — дослідження (2026-09-17)
TAGS: mcp, mcp 2.x, list_tools, Server, migration, lowlevel

### Факти
- Наш my_mcp_server.py використовує lowlevel Server (не FastMCP)
- У v2 видалено декоратори @server.list_tools() / @server.call_tool()
- Handler тепер передається через конструктор Server(on_list_tools=, on_call_tool=)
- Tool(inputSchema=) → Tool(input_schema=) (camelCase → snake_case)
- Автоматична валідація JSON Schema прибрана — треба робити вручну
- stdio_server() + server.run() — не змінилось
- Compatibility shim: НЕМАЄ
- Оцінка міграції: 20-30 рядків з 55, 15-20 хв, ризик низький
- Джерело: github.com/modelcontextprotocol/python-sdk, migration guide
  (https://py.sdk.modelcontextprotocol.io/migration/)

### Рішення
Залишитися на mcp<2.0.0. Мігрувати тільки коли з'явиться конкретний
інструмент, що вимагає mcp 2.x. Тоді — або міграція (готовий
before/after), або ізоляція через venv/pipx.

## Claude Code Skills (2026-09-17)
TAGS: skills, anthropic-skills, perevirka-dzherel, skill-creator

- Вбудовані Skills доступні через префікс anthropic-skills:*
- Перелік (назви, з поточної сесії): docs, docx, import-memory, morning,
  pdf, perevirka-dzherel, pptx, skill-creator, xlsx, zvirka-bazy
- Приклад: perevirka-dzherel (перевірка джерел) — виявив і виправив
  реальну помилку (хибне сумнівання в існуванні GPT-6 Astra) в цій сесії
- Автозавантажуються при потребі (Claude Code сам вирішує, коли викликати)
- skill-creator схоже саме те, що треба для «чи можна створювати власні» —
  «Create new skills, modify and improve existing skills, and measure
  skill performance»
- Як створювати власні — дослідити в наступній сесії (почати з skill-creator)

## Перевірка вбудованих Skills (2026-09-18)
TAGS: skills, security, perevirka-dzherel, zvirka-bazy, skill-creator, deepseek

Три Skills перевірено на безпеку (read-only, через DeepSeek):

1. perevirka-dzherel — низький ризик
   - Тільки SKILL.md (102 рядки), без скриптів
   - Мережа: немає прямих викликів (текстові рекомендації)
   - MCP: не згадується

2. zvirka-bazy — низький ризик
   - Тільки SKILL.md (100 рядків), без скриптів
   - MCP: memory_list, project_info, project_search
   - Ризик низький — сам скіл нічого не виконує

3. skill-creator — середній ризик
   - 8 Python-скриптів (subprocess, browser, файлова система)
   - Мережа: через зовнішній Claude CLI (subprocess), не прямий HTTP
   - Небезпечні примітиви (eval/exec/os.system/shutil.rmtree) — НЕ знайдено
   - Ризик середній через потужність (очікувано для skill-creator)

Загальний висновок: прихованого ексфільтру, eval/exec, shell-ін'єкцій
не виявлено. Skills безпечні для використання.

## Router-паттерн і /cost (2026-09-18)
TAGS: router, AGENTS.md, RULES.md, /cost, /usage, /context, /mcp

- Router (AGENTS.md як окремий файл) НЕ підходить для малих
  проєктів (RULES.md < 200 рядків) — правила перестають
  завантажуватись. Рішення: один файл (навігація + правила).
- /cost — UI-команда Claude Code, AI не може викликати.
  Тільки користувач вручну. Аналогічно: /usage, /context, /mcp.

## Урок: неверифіковані твердження (2026-09-18)
- Твердження "chuzom-router = llm-routing" потрапило в BACKLOG
  як факт, хоча було припущенням AI (джерело невідоме)
- Наслідок: довелось перевіряти через npm (404 Not Found)
- Рішення: впроваджено трирівневу систему знань (Sourced/Unverified/
  Hallucinated) з позначкою [unverified]
