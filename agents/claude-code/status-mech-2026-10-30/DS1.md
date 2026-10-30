deepseek-search: перший шматок 0.6 с, усе 73.5 с
УВАГА: пошуків 6 при --uses 4 — сервер ліміт не тримає.
Питання — огляд інструментів з кількома вимірами (функція / зірки / дата / ліцензія / Termux). Спершу розбиваю на підпитання: (1) статуслайни-проєкти (ccstatusline тощо), (2) плагіни з маркетплейсу Claude Code, (3) Stop/SessionEnd-хуки з підсумком, (4) стан git/todo, що обчислюється кодом. Шукаю першоджерела.Перший зріз є. Тепер шукаю саме те, що показує стан **після кожного ходу** (хуки Stop/SessionEnd, todo, запуск перевірок) і маркетплейс-плагіни — це окрема ніша від статуслайнів.Маю кілька кандидатів. Тепер уточнюю першоджерела (офіційні доки хуків/статуслайну), а також перевіряю Termux-сумісність і ще кілька проєктів.# Коротка відповідь

Готові інструменти є, але **жоден один не покриває весь ваш список**. Ринок розділений на дві половини:

| Що ви хочете бачити | Чим це робиться готовим | Стан |
|---|---|---|
| git-гілка, dirty, +/− рядків, останній коміт, PR/CI | **статуслайни** (ccstatusline, contextbricks, him0, erk) | зріло, багато проєктів |
| todo, які команди запускались і чим скінчились, підсумок ходу | **Stop-хуки** | переважно рецепти/бібліотеки, не «поставив і працює» |
| усе разом, оновлення **після кожного ходу** | — | **готового не знайшов** |

Ключовий технічний факт: статуслайн у Claude Code — це команда, яку CLI перемальовує (за таймером `refreshInterval`), а не подія «хід завершився». Тому «після кожного ходу» — це саме Stop-хук, а не статуслайн [першоджерело — доки].

---

# Докази

## 1. Офіційна механіка (база, на якій усе тримається)

**1.1** Статуслайн — нативна фіча Claude Code; скрипт отримує JSON на stdin і сам може кликати git.
· [першоджерело] · доки, локалізована сторінка · https://code.claude.com/docs/ja/statusline
· «各スクリプトは現在のディレクトリが git リポジトリであるかどうかを確認し、ステージングされたファイルと変更されたファイルをカウントし、カラーコード化されたインジケーターを表示します» (кожен скрипт перевіряє, чи є тека git-репозиторієм, рахує staged і modified файли).

**1.2** Stop-хук отримує `last_assistant_message`, `transcript_path`, `cwd`, `stop_hook_active`; exit code 2 блокує зупинку й повертає stderr як фідбек.
· [першоджерело] · https://code.claude.com/docs/en/hooks
· «Exit code 2: the teammate receives the stderr message as feedback and continues working instead of going idle.» / «Run the build before stopping." >&2 / exit 2»
· «Unlike Stop and SubagentStop, where this field holds Claude's conversational output, for StopFailure it contains the API error string itself»
→ тобто `transcript_path` + `cwd` — це і є канал, через який хук може обчислити todo/команди/результати кодом.

**1.3** `StopFailure` не має контролю рішень — тільки логування; `TeammateIdle` — окрема подія для субагентів.
· [першоджерело] · там же · «StopFailure hooks have no decision control. They run for notification and logging purposes only.»

## 2. Статуслайни з git-станом

**2.1 ccstatusline** — `sirmalloc/ccstatusline` · TypeScript/Node · **MIT**
· Що: «🎨 A highly customizable status line formatter for Claude Code CLI Display model info, git branch, token usage, and other metrics in your terminal» · [третя сторона — цитата README] · https://www.claude-updates.com/posts/ccstatusline-l9hil
· Git-віджети (з release notes у тому ж README-фрагменті): «Git Staged Files, Git Unstaged Files, Git Untracked Files, and Git Clean Status for file counts and clean/dirty state», а також «Git Insertions», «Git Deletions», «Git PR», «Git CI Status … summarizes failing, pending, and successful checks for the current branch's pull request» · [третя сторона]
· **Важливе обмеження**: «The status line command runs once per repaint, so what it costs to invoke is paid over and over» · [третя сторона — цитата README]. Оновлення прив'язане до перемальовки, не до кінця ходу. `refreshInterval` пишеться лише для Claude Code >= 2.1.97.
· Зірки — **суперечливі**, див. розділ «Суперечності».
· Останній коміт: «Last Commit — 2 months ago» (Snyk) проти «last push was on 2026-09-21, with v2.2.30 published on 2026-09-17» (hysenlabs) — теж суперечність.
· npm: 22,363 завантажень/тиждень, 1 мейнтейнер, 46 open issues, 51 open PR · [третя сторона] · https://security.snyk.io/package/npm/ccstatusline
· Termux: збірка під Node 14, ESM-бандл, ставиться через `npx`/`bunx`; **прямих доказів про Termux немає** (див. розділ Termux).

**2.2 contextbricks** — npm `contextbricks@4.0.0` · **MIT** · потребує `jq` + `git`
· Найближче до «коміти»: 3-рядковий вивід, рядок 2 — `[abc1234] Fix auth redirect loop | +12/-3`, тобто «Latest commit hash + message, lines changed»; рядок 1 — `repo:branch`, `*` = uncommitted, `↑1` = commits ahead · [третя сторона] · https://www.npmjs.com/package/contextbricks/v/4.0.0
· GitHub-URL у сніпеті відсутній → репозиторій, зірки, дата коміту **[не перевірено]**.

**2.3 him0/claude-code-statusline** — `@him0/claude-code-statusline`
· «Line diff for the session (`+added -removed`) inline next to the branch; hidden when both are zero»; clickable PR `#42`; dirty-маркер `*`; `--pr-title` · [першоджерело — README репозиторію] · https://github.com/him0/claude-code-statusline
· Зірки / ліцензія / дата останнього коміту — **[не перевірено]**, у сніпеті немає.

**2.4 CCometixLine** — `Haleclipse/CCometixLine`, npm `ccline`
· «Git Status — Branch name, clean / dirty / conflict state, remote tracking info», TUI `ccline config`, теми · [третя сторона] · https://ofox.ai/docs/integrations/claude-code/contextline
· Зірки / ліцензія / дата — **[не перевірено]**.
· 🚩 Рекомендований там конфіг `"env": {"CLAUDE_CODE_STATUSLINE": "ccline"}` **не відповідає** задокументованій схемі `statusLine.command` (п. 1.1) — ймовірно застарілий або неправильний.

**2.5 erk-statusline** — `dagster-io/erk-statusline`, PyPI, ставиться через `uv tool install`
· Показує `(git:repo)`, worktree, `(br:branch)`, `✗` dirty, і `(gh:#123 st:XX chks:✅)` — стан PR + CI · [першоджерело — README на PyPI] · https://pypi.org/project/erk-statusline/0.4.5/
· Python/uv → для Termux це `uv`+`python`, але **Termux не згадано**.

**2.6 @luport-dev/claude-code-statusline** — **MIT**, Python 3.8+, stdlib only
· «Implemented in Python 3 (standard library only) and works on Linux, macOS, and Windows»; модель/effort/thinking/context/rate-limits/**dir/branch/worktree** · [третя сторона — дзеркало socket.dev з README] · https://socket.dev/npm/package/@luport-dev/claude-code-statusline
· 2 завантаження/тиждень, 1 мейнтейнер, остання публікація 24 May 2026 · [третя сторона]
→ **найкращий кандидат для Termux** за мінімумом залежностей (python3 + git, без Node/jq/curl). Це мій висновок, не факт із джерела.

**2.7 Інші, коротко**
· `shrwnsan/claude-statusline` — «project-branch, git indicators, and context usage. Optimized for speed with bun»; opt-in `prBadge`/`costUsage`/`rateLimit`/`modeIndicators` · [першоджерело — README] · https://github.com/shrwnsan/claude-statusline · зірки/ліцензія **[не перевірено]**
· `@ericcai/claude-statusline` — powerline, git branch + dirty, PR badge; «Prerequisites: jq, curl, git» · [третя сторона] · https://www.npmjs.com/package/@ericcai/claude-statusline/v/1.1.0
· `MadAppGang/claude-code` → плагін `statusline` v1.4.0: «Colorful statusline with worktree awareness, plan limits with reset countdowns, token counts, compaction detection»; репо 248★, 9 плагінів · [третя сторона] · https://claudemarketplaces.com/plugins/madappgang-claude-code
· `Gruku/claude-tools` → плагін `statusline` v1.5.0: «rate-limit bars, git status, context usage … Bash + PowerShell … Requires: jq (Bash only)» · [першоджерело — сайт маркетплейсу] · https://gruku.github.io/claude-tools/
· `pchalasani/claude-code-tools` → статуслайн «model, directory, git branch, uncommitted file count, and a visual token-usage progress bar»; ~1,790★ станом на May 2026 · [третя сторона] · https://dudarik.com/en/blog/claude-code-tools/
· `wolf123450/ClaudeSkills` → `desktop-statusline` (дублює статуслайн у Code-табі десктоп-застосунку) · [першоджерело — README] · https://github.com/wolf123450/ClaudeSkills

## 3. Stop-хуки: todo, підсумок ходу, «що запускалось»

**3.1 Готовий рецепт, не пакет** — Stop-хук на 31 рядок Node без залежностей: звіряє `last_assistant_message` з `git diff`, блокує зупинку, якщо змінений файл не згаданий.
· [третя сторона] · https://singhlabs.dev/blog/claude-code-stop-hook-example/ (дубль: dev.to/manpreet171)
· «A better one: hold the summary against the diff» · код: `changed = [...git('diff --name-only HEAD'), ...git('ls-files --others --exclude-standard')]` → `{"decision":"block","reason":"You said you're done but never mentioned: …"}`
· Показує головну пастку: `if (input.stop_hook_active) process.exit(0);` — без цього цикл.

**3.2 claude-hooks-sdk** — npm, бібліотека для збирання хуків, не готовий плагін
· Трансформи: `ConversationLogger`, `FileChangeTracker`, **`TodoTracker`**, **`AISummarizer` — «Automatic Stop event summaries»**
· `TodoTracker`: `getSnapshot(sessionId)`, `getTodosByStatus(sessionId,'in_progress')`, `getCompletionPercentage(sessionId)`
· `manager.onStop(...)` збирає `todos`, `files`, git-контекст: «Git Context: Track which branch/commit events occurred on»
· [першоджерело — README пакета] · https://www.npmjs.com/package/claude-hooks-sdk/v/0.8.0
→ це найближче до вашого «todo + підсумок ходу», але **вимагає писати код**; і `AISummarizer` — це LLM, а не «обчислено кодом».

**3.3 Dev-GOM/claude-code-marketplace** — маркетплейс із готовими плагінами
· «**TODO Collector**: Scans and reports TODOs when session ends»; «Claude Dev Helper: Automatically reviews git diffs, stages changes, and collects feedback»
· Логи Stop-хука: «`showLogs`: Control Stop hook log visibility (`false` by default to reduce chat clutter)» — конфіг `.plugin-config/hook-todo-collector.json`
· [першоджерело — README] · https://github.com/Dev-GOM/claude-code-marketplace
· Зірки / ліцензія / дата — **[не перевірено]**.
→ Незалежний сигнал: вивід Stop-хука **захаращує чат**, тому автори вимкнули його за замовчуванням.

**3.4 get-shit-done** — керування TODO + Stop-хук
· «delegates TODO list management to Claude and uses a Stop hook to automatically detect unfinished work … inspects for incomplete tasks before a session ends and re-injects a prompt if continuation is needed» · [третя сторона] · https://kga-it.com/en/blog/claude-plugins-ecosystem-2026
· GitHub URL, зірки, ліцензія, дата — **[не перевірено]**, у джерелі їх немає.

**3.5 Completion Guardian** — Stop-хук + SDK-рев'юер, повертає `hookSpecificOutput.additionalContext`
· Вимога: Claude Code >= 2.1.163; жорсткий ліміт 2 повтори; fail-open при таймауті
· [третя сторона, один автор] · http://mp.weixin.qq.com/s?__biz=MzYzMTM0ODkxOQ==&mid=2247490182&idx=1&sn=f5ec2152aad8650695327341b15cc1f9
· Репозиторій не названо → для встановлення **[не перевірено]**.

**3.6 Комерційний кіт** — «Session summary logger (Stop). Appends the final message of every turn to a dated file in `.claude/session-log` and respects `stop_hook_active` so it cannot loop»
· [третя сторона, платно] · https://wowhow.cloud/product/claude-code-hooks-and-plugin-starter-kit-oct-2026

## 4. Termux

**Прямих доказів немає — жодне джерело в результатах не згадує Termux.** Що є з джерел, що впливає на Termux:

· Статуслайн викликається **на кожну перемальовку** → вартість запуску множиться: «`npx -y ccstatusline@latest` … 1082 ms», «`npx -y ccstatusline@2.2.27` … 1135 ms» (замір на Windows, теплий кеш), тоді як pinned-інсталяція `"command": "ccstatusline"` уникає резолвінгу · [третя сторона — цитата README] · https://www.claude-updates.com/posts/ccstatusline-l9hil
· Те саме простими словами: «npm distribution, performance determined by Node.js startup overhead» · [третя сторона] · https://raw.githubusercontent.com/Astro-Han/karpathy-llm-wiki/refs/heads/main/examples/2026-03-19-claude-code-statusline-landscape.md
· Залежності, які треба мати в Termux, з самих проєктів: `jq` + `git` (contextbricks, @ericcai, Gruku), `curl` (@ericcai), `python3` (@luport-dev, erk через `uv`), Node ≥14 (ccstatusline, him0).

Мій висновок (не факт): у Termux реалістичніше за все **Python-stdlib статуслайн** (`@luport-dev`) або власний скрипт на `sh`+`git` — нуль залежностей, крім `python3`/`git`; Node-варіанти вимагатимуть pinned-глобальної інсталяції, а `npx -y` на кожну перемальовку на телефонному CPU — погана ідея. `bun`-орієнтовані (shrwnsan) — під питанням.

---

# Суперечності

**Зірки ccstatusline різняться в 8 разів** — не усереднюю, показую як є:

| Значення | Джерело | Дата/контекст |
|---|---|---|
| 11,867 | Snyk (npm-сторінка) | v2.2.30, «Last Commit 2 months ago» |
| 11,984 (527 форків) | claude-updates.com | v2.2.25, «Updated 2 months ago» |
| 8,094 (352 форки) | skillsllm.com | «Added 12/27/2025» |
| 5,421 | karpathy-llm-wiki market scan | «verified via gh api», 2026-03-19 |
| 1,471 | packages.ecosyste.ms (Go-проксі) | «v2.0.21, about 2 months ago» |

**Дата останнього коміту ccstatusline** — три взаємовиключні твердження: «2 months ago» (Snyk) / «2026-09-21» (hysenlabs, там же «last received commits 1 day ago») / «Updated 2 months ago» (claude-updates).

**CCometixLine**: інструкція ставить `"env": {"CLAUDE_CODE_STATUSLINE": "ccline"}`, тоді як офіційна механіка — `statusLine.command`. Одне з двох хибне; на користь офіційної схеми — доки (п. 1.1).

**«Після кожного ходу» vs статуслайн**: ваш запит передбачає подію завершення ходу; статуслайн оновлюється per-repaint/за таймером (п. 2.1, 1.1). Це різні речі — і саме тому частина «підсумок ходу» не закривається статуслайнами.

---

# Висновок

**висновок.** Готові плагіни закривають **візуалізацію git-стану** (гілка, dirty, +/−, останній коміт, PR/CI) — тут вибір широкий і є зрілі проєкти з MIT і активними релізами. Частина «todo + які команди запускались і чим скінчились + підсумок ходу» **готовими плагінами не закривається**: у наявних Stop-хуках це або (а) рецепт на 30 рядків, який ви копіюєте, (б) бібліотека-конструктор (`claude-hooks-sdk`), (в) вузький плагін (`TODO Collector` — лише todo, `Session summary logger` — лише текст, платно), або (г) згадка без репозиторію (`get-shit-done`, Completion Guardian).

Технічно все, що ви просите, **здійсненно** — Stop-хук отримує `transcript_path` і `cwd`, отже може кодом розпарсити, які Bash-команди викликались і з яким exit-кодом, прочитати TodoWrite-події з транскрипту й порахувати `git diff --numstat`. Але це саме те, що вам доведеться написати або скласти з SDK: **готового «one-stop» плагіна в результатах пошуку немає**.

# Рекомендація

**Рекомендація (не факт).** Двошарова схема, бо один інструмент не покриває:

1. **Статуслайн для git** — `ccstatusline` (Node, MIT, найбагатший набір git-віджетів) або `contextbricks` (jq+git, показує **останній коміт + рядки** — єдиний, що явно це робить). Для Termux — `@luport-dev/claude-code-statusline` (Python stdlib) або власний `sh`+`git` скрипт за офіційним прикладом.
2. **Stop-хук для підсумку** — почати з 30-рядкового рецепта зі singhlabs (він уже робить звірку «заява ↔ diff»), додати читання TodoWrite-подій з `transcript_path`; якщо не хочеться писати з нуля — `claude-hooks-sdk` (`TodoTracker` + `FileChangeTracker`).
3. **Обов'язково** `stop_hook_active` guard + fail-open, інакше отримаєте цикл або мертвий CLI.
4. **Продуктивність**: pinned глобальна інсталяція, не `npx -y` на кожну перемальовку.

Якщо хочете один підхід — пишіть власний Stop-хук (Node або Python) + мінімальний статуслайн; це ~80–120 рядків і повний контроль над тим, що саме виводиться.

# Чого не знайшов

· **Жодного джерела про Termux** для будь-якого з цих інструментів — питання лишається відкритим.
· **Готового плагіна, що показує список виконаних команд/перевірок і їхні результати** — не знайшов нічого, навіть часткового.
· **GitHub URL / зірки / ліцензія / дата** для: contextbricks, him0/claude-code-statusline, CCometixLine, shrwnsan, erk-statusline, Dev-GOM, get-shit-done, Completion Guardian, claude-hooks-sdk.
· **Офіційний маркетплейс Anthropic** — бачив лише сторонні маркетплейси (MadAppGang, Gruku, atournayre, Dev-GOM, wolf123450, samtexas). Чи є там плагіни з підсумком ходу — не перевірено.
· Чи є `get-shit-done` реальним пакетом із Stop-хуком, чи це переказ у блозі.

# Червоні прапорці

· 🚩 **Цифри зірок і дат ненадійні** — розкид 1,471…11,984 для одного репо; частина сторінок-агрегаторів має дати в майбутньому (2026) і явно генерований SEO-контент. Числа беріть з `gh api`, не з цих сторінок.
· 🚩 **ccstatusline: 1 мейнтейнер, 46 issues, 51 open PR** — bus factor.
· 🚩 **Статуслайн = shell-команда з вашими правами на кожну перемальовку** — а плагіни з маркетплейсу додають ще й хуки. Третє джерело описує інцидент Feb 2026 з ексфільтрацією `.ssh/id_rsa` через MCP-сервер **· [третя сторона, не перевірено] · https://kga-it.com/en/blog/claude-plugins-ecosystem-2026**.
· 🚩 **Інструкція «вставте URL у чат Claude Code, і він сам встановить»** (ofox.ai) — це вміст сторінки, не інструкція від Anthropic; виконання такого дає агенту право клонувати й запускати невідомий код.
· 🚩 **Auditability**: «what a user installs contains the built output and nothing else: no `src/`, no `docs/`» (про ccstatusline) · [третя сторона — аналіз] · https://hysenlabs.com/projects/sirmalloc-ccstatusline
· 🚩 Stop-хук, що виводить у чат, **захаращує розмову** — автори плагінів вимикають логи за замовчуванням.
· 🚩 `refreshInterval` вимагає Claude Code >= 2.1.97, `additionalContext` у Stop — >= 2.1.163; на старій версії «тихо не працює».

---

*Питання виглядає таким, що його ставитимуть регулярно (екосистема Claude Code змінюється щотижня) — цифри й дати тут швидко старіють, фіксуйте дату зрізу.*

**[не перевірено]**: усі зірки/дати/ліцензії, взяті з агрегаторів і блогів; існування й вміст репозиторіїв, для яких я бачив лише згадку; будь-яка робота в Termux; згаданий інцидент Feb 2026.

== Джерела (40):
- ccstatusline | Snyk — https://security.snyk.io/package/npm/ccstatusline
- Claude Code Statusline Market Scan — https://raw.githubusercontent.com/Astro-Han/karpathy-llm-wiki/refs/heads/main/examples/2026-03-19-claude-code-statusline-landscape.md#1
- Claude Code 高手都在用，11K Star 状态栏把上下文、Token、成本全部摊开 | ccstatusli - Claude Code 高手都在用，11K Star 状态栏把上下文、Token、成本全部摊开 | ccstatusline — https://blog.csdn.net/edwinjhlee/article/details/163231873#1
- GitHub topics: statusline - Neovim minimal statusline — https://repos.ecosyste.ms/hosts/GitHub/topics/statusline?order=desc&sort=forks_count#2
- themeing | proxy.golang.org keywords — https://packages.ecosyste.ms/registries/proxy.golang.org/keywords/themeing
- 程序员逼格拉满！ccstatusline：让你的 Claude Code 状态栏直接封神！ - 测试开发技术 — https://cloud.tencent.com.cn/developer/article/2670421?policyId=1004#1
- Claude Code JSONL data source + ccstatusline widget catalog — https://raw.githubusercontent.com/oakoss/linesmith/refs/heads/main/docs/research/jsonl-data-source.md#1
- ccstatusline install: widgets, keys and 60s caching — https://hysenlabs.com/projects/sirmalloc-ccstatusline
- ccstatusline - CLI Tools — https://skillsllm.com/skill/ccstatusline
- Ccstatusline — Claude Updates — https://www.claude-updates.com/posts/ccstatusline-l9hil
- erk-statusline - erk-statusline — https://pypi.org/project/erk-statusline/0.4.5/#files#1
- erk-statusline — https://pypi.org/project/erk-statusline/0.4.2/#files#1
- GitHub - him0/claude-code-statusline · GitHub - GitHub - him0/claude-code-statusline · GitHub — https://github.com/him0/claude-code-statusline/tree/main#features#1
- GitHub - shrwnsan/claude-statusline: Simple statusline for Claude Code with project-branch, git indicators, and context usage. Optimized for speed with bun. Just the essentials, none of the bloat. · GitHub — https://github.com/shrwnsan/claude-statusline#readme#1
- ステータスラインをカスタマイズする - Claude Code Docs - !/usr/bin/env node — https://code.claude.com/docs/ja/statusline#3
- @ericcai/claude-statusline - ⚠️ — https://www.npmjs.com/package/@ericcai/claude-statusline/v/1.1.0#1
- CCometixLine — Claude Code Status Bar Enhancement — https://ofox.ai/docs/integrations/claude-code/contextline
- CCometixLine — Claude Code Statusleisten-Erweiterung — https://ofox.ai/de/docs/integrations/claude-code/contextline
- @luport-dev/claude-code-statusline - npm Package Security An... - 🎩 You're Invited:Meet the Socket team at Black Hat in Las Vegas, August 3-6.RSVP → — https://socket.dev/npm/package/@luport-dev/claude-code-statusline#1
- contextbricks — https://www.npmjs.com/package/contextbricks/v/4.0.0
- Claude Code Stop hook example: check the "done" claim. - DEV Community — https://dev.to/manpreet171/claude-code-stop-hook-example-check-the-done-claim-4n16#1
- A Claude Code Stop hook that reads "done" and checks the diff — https://singhlabs.dev/blog/claude-code-stop-hook-example/
- claude-hooks-sdk - ⚠️ — https://www.npmjs.com/package/claude-hooks-sdk/v/0.8.0#1
- JSPM – claude-hooks-sdk@0.8.5 - JSPM — https://jspm-packages.deno.dev/package/claude-hooks-sdk@0.8.5#1
- Claude Code Stop hooks: making the agent finish its homework" - DEV Community — https://dev.to/maddy30445r/claude-code-stop-hooks-making-the-agent-finish-its-homework-hmd#comments#1
- GitHub - Dev-GOM/claude-code-marketplace: Claude Code plugins & extensions - Hooks, commands, and agents for developer productivity and workflow automation · GitHub - GitHub - Dev-GOM/claude-code-marketplace: Claude Code plugins & extensions - Hooks, commands, and agents for developer productiv... — https://github.com/Dev-GOM/claude-code-marketplace#1
- Hooks reference - Claude Code Docs - agent_id | On this event, the common input field identifies the subagent or in-process teammate completing the task — https://code.claude.com/docs/en/hooks?page_id=4838#10
- Claude Code Hooks and Plugin Starter Kit: 8 Production Hooks — https://wowhow.cloud/product/claude-code-hooks-and-plugin-starter-kit-oct-2026
- Claude Plugins Ecosystem: Building MCP Servers, Slash Commands & Hooks — KGA Tech Blog — https://kga-it.com/en/blog/claude-plugins-ecosystem-2026
- Agent说"做完了"，真的做完了吗？ — http://mp.weixin.qq.com/s?__biz=MzYzMTM0ODkxOQ==&mid=2247490182&idx=1&sn=f5ec2152aad8650695327341b15cc1f9
- GitHub - linny006/claude-code-plugin-tracker at eefa28796264b4dbf235846d6dfb706fe8e95c9c · GitHub - GitHub - linny006/claude-code-plugin-tracker at eefa28796264b4dbf235846d6dfb706fe8e95c9c · GitHub — https://github.com/linny006/claude-code-plugin-tracker/tree/eefa28796264b4dbf235846d6dfb706fe8e95c9c#1
- GitHub - atournayre/claude-marketplace: Marketplace de plugins pour Claude Code : dev tools (Git, Symfony, PHPStan, API Platform), customization (hooks, output styles) et documentation interactive · GitHub - GitHub - atournayre/claude-marketplace: Marketplace de plugins pour Claude Code : dev tools (Git, Symfony, PHPStan, API Platform... — https://github.com/atournayre/claude-marketplace#1
- GitHub - wolf123450/ClaudeSkills · GitHub - GitHub - wolf123450/ClaudeSkills · GitHub — https://github.com/wolf123450/ClaudeSkills#1
- Claude Code Plugins Complete Reference (2026-04) — https://raw.githubusercontent.com/codealive-ai/ai-driven-development/refs/heads/main/skills/plugins-management/references/plugin-guide.md#1
- The Claude Code Ecosystem — claude-code-router, SuperClaude, caveman, statusline, awesome lists (2026) — https://aiprimetech.io/claude-code/ecosystem/
- 35 Claude Code Add-Ons: Free Guide | Best Productivity Resources — https://bestproductivityresources.com/guides/35-claude-code-add-ons#s4-mcp-servers
- claude-code-tools: Skills, Hooks, and Agents for Claude Code Workflows — https://dudarik.com/en/blog/claude-code-tools/
- MadAppGang/claude-code Plugins | Claude Code Marketplace — https://claudemarketplaces.com/plugins/madappgang-claude-code
- Claude Tools — https://gruku.github.io/claude-tools/
- claude-code-config | Ecosystem Directory | market.dev - claude-code-config — https://explore.market.dev/ecosystems/python/projects/heysamtexas-claude-code-config#1

== Розмова: 20261030-090246 | вх 39441 (з кешу 67328) | вих 12214 | пошуків 6
== Ціна ≈$0.0269 (пік; без вартості пошуків)
