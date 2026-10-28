# Установка find-skills «як у автора» — журнал (claude-code, 2026-10-28)

Мета: рішення користувача «можна 2» — ставити в справжню домашню теку, телеметрія вимкнена (DISABLE_TELEMETRY=1 DO_NOT_TRACK=1).

## Передумови
- `ps -e -o user= | grep -c "$(id -un)"` → 18 (поріг «>18 — не ставити»: не перевищено; перед установкою і після — 18).
- `ps -A -o args | grep -c '[o]bsidian'` → 0.
- `node -v` → v26.4.0; `npm -v` → 11.20.0. (skills@1.7.4 вимагає node >=22.20.0 — ок.)
- До: `~/.agents` не існувало; `~/.claude/skills` містив лише `synced`; у домі 20 тек-крапок.

## Команда і вивід
1. Команда автора (SKILL.md, рядки ~100–103), дослівно:
   `DISABLE_TELEMETRY=1 DO_NOT_TRACK=1 timeout 300 npx --yes skills@1.7.4 add vercel-labs/skills@find-skills -g -y 2>&1 | tail -60`
   Вивід: `sh: 1: skills: not found`, EXIT=127.
   Причина (перевірено): npx завантажив пакет у `~/.npm/_npx/0757c8f0298e564a/node_modules/skills` і створив `.bin/skills -> ../skills/bin/cli.mjs`, але файл починається з `#!/usr/bin/env node`, а `/usr/bin/env` у Termux не існує (`ls /usr/bin/env` → No such file). Тобто **команда автора на Termux не працює як є** (npx не патчить шебанг, як це робить npm install у Termux).
2. Обхід — той самий пакет skills@1.7.4 з кешу npx, запуск через node напряму (поведінка пакета не змінена, змінено лише спосіб запуску):
   `DISABLE_TELEMETRY=1 DO_NOT_TRACK=1 timeout 300 node ~/.npm/_npx/0757c8f0298e564a/node_modules/skills/bin/cli.mjs add vercel-labs/skills@find-skills -g -y 2>&1 | tail -60`
   EXIT=0. Суттєвий вивід (без керівних послідовностей):
   - `claude-code_2-1-296_agent  Agent detected — installing non-interactively`
   - `Source: https://github.com/vercel-labs/skills.git @find-skills` → `Found 1 skill` → `79 agents` → `Installing to: Claude Code`
   - Installation Summary: `~/.agents/skills/find-skills` — `universal: Amp, Antigravity, Antigravity CLI, Cline, Codex +17 more`; `symlink → Claude Code`
   - `✓ ~/.agents/skills/find-skills` ... `symlinked: Claude Code`
   - `■ Failed to install 1: ✗ find-skills → PromptScript: PromptScript does not support global skill installation`
   - `Done! Review skills before use; they run with full agent permissions.`
   Інтерактивних питань не було, зависання не було.

## Що з'явилося в домі (повний перелік)
Теки-крапки: diff до/після → лише `+ /data/data/com.termux/files/home/.agents` (було 20, стало 21).
`find ~ -newer fs-marker` (без проєкту, `.npm`, `.claude/projects`, tmp) → рівно:
- `~/.agents/` (нова тека, 23K)
- `~/.agents/.skill-lock.json` (429 байт)
- `~/.agents/skills/find-skills/SKILL.md` (5472 байти)
- `~/.claude/skills/find-skills` (симлінк)
Окремо в `.npm` (не в find-виводі, бо виключено): `~/.npm/_npx/0757c8f0298e564a/` (5.8M, кеш npx пакета skills + залежності tar, yaml та ін.) і 3 файли в `~/.npm/_logs/`.
Нових тек для інших агентів (.cursor, .codex, .cline тощо) НЕ створено: 22 «universal» агентів читають спільну `~/.agents/skills`, окремих тек не потребують.
Вміст `~/.agents/.skill-lock.json`: version 3, skills.find-skills {source vercel-labs/skills, sourceType github, sourceUrl https://github.com/vercel-labs/skills.git, skillPath skills/find-skills/SKILL.md, skillFolderHash 76a98a285cb0434f3d39e1a873823556330e398b, installedAt/updatedAt 2026-10-28T07:32:45.879Z}, dismissed {}.
Процесів після установки: 18 (без змін).

## Симлінк і збіг SKILL.md
- `~/.claude/skills/find-skills -> ../../.agents/skills/find-skills` (відносний симлінк); `readlink -f` → `/data/data/com.termux/files/home/.agents/skills/find-skills`. Симлінк ок.
- `cmp ~/.claude/skills/find-skills/SKILL.md .../sources/find-skills.SKILL.md` → збігається побайтово (CMP_SAME).
- Скіл одразу з'явився у списку скілів поточної сесії (find-skills з описом «Helps users discover and install agent skills...»).

## Тест find
`DISABLE_TELEMETRY=1 DO_NOT_TRACK=1 timeout 120 node .../skills/bin/cli.mjs find handoff` → EXIT=0, не інтерактивний, не завис. Видав 20 результатів з кількістю установок і URL skills.sh. Перші: `mattpocock/skills@handoff 1.1M installs`, `mattpocock/skills@claude-handoff 431.7K installs`; серед нижчих: `vinvcn/mattpocock-skills-zh-cn@handoff 5.9K`, `softaworks/agent-toolkit@session-handoff 4.2K`, `wshobson/agents@on-call-handoff-patterns 10.4K`. Видно й нерелевантне (`livekit/agent-skills@livekit-agents`, `earthtojake/text-to-cad@sdf`) — пошук нечіткий. find нічого не встановлює і нових файлів у домі не створив (перевірено повторним find -newer: той самий перелік).
(Запускався тричі — для запису виводу — усі з DISABLE_TELEMETRY=1.)

## Чого не видно було з коду
Лише факти, яких немає в find-skills-check.md:
1. Команда автора `npx ... skills@1.7.4 add` на Termux падає `sh: 1: skills: not found` (шебанг `/usr/bin/env` відсутній); потрібен обхід через `node .../cli.mjs`. Скіл автора на цій платформі «як є» не працює.
2. Створено лише одну нову теку в домі — `~/.agents`; додатково симлінк у `~/.claude/skills`. Тек для інших агентів немає (22 «universal» ділять `~/.agents/skills`).
3. Інсталятор розпізнав нас як агента (`claude-code_2-1-296_agent`) і працював без питань; `-g -y` не знадобилися для обходу питань, але і не заважали.
4. Один з 79 «агентів» (PromptScript) дав помилку «не підтримує глобальне встановлення» — нешкідлива, EXIT=0.
5. Установка не додала процесів (18 до і після); Obsidian не живий; сесію не вбито.
6. `skills find` без телеметрії працює, виводить 20 рядків без інтерактиву.

## Як відкотити (НЕ виконано)
Кожне видалення — спершу запис у TRASH.md (правило проєкту), нетривіальне — через `.trash/`:
1. `~/.claude/skills/find-skills` — симлінк (rm лише самого симлінка, не цілі).
2. `~/.agents/` — уся тека (skills/find-skills/SKILL.md + .skill-lock.json); вона створена установкою, раніше не існувала.
3. Необов'язково: `~/.npm/_npx/0757c8f0298e564a/` (кеш npx, 5.8M) і `~/.npm/_logs/2026-10-28T07_32_*-debug-0.log` (3 файли).
Інші зміни в домі не виявлені.

## Обгортка як з pkgtruth (28.10)
Передумови: процесів 18 (ліміт >18 зупинка), obsidian 0. Перша спроба npm зупинена хуком proc-guard (він бачив 27 > 21), повторний підрахунок 18 — друга спроба пройшла.
- `npm i -g --ignore-scripts skills@1.7.4` -> "added 8 packages in 3s"; $PREFIX/bin/skills було симлінком на ../lib/node_modules/skills/bin/cli.mjs; cli.mjs: `#!/usr/bin/env node`.
- TRASH.md: запис додано ДО заміни. Обгортку записано в usr/tmp/skills-wrapper, chmod 755, mv -f у $PREFIX/bin/skills (399 Б, звичайний файл). cli.mjs після цього й далі `#!/usr/bin/env node` (цілий).
- Тести: `npx skills find handoff` exit=0, результатів (рядків skills.sh/) = 20; `skills --version` -> 1.7.4, exit=0. Нових файлів у ~ (поза проєктом): лише ~/.npm/_logs (журнал npm).
- Встановлено: $PREFIX/lib/node_modules/skills, 5.8 МБ.
- Відкат: rm обгортки (спершу запис у TRASH.md) + `npm rm -g skills`.
- Кеш ~/.npm/_npx/0757c8f0298e564a (5,8 МБ) тепер зайвий — НЕ видалено, лише записано.
— [claude-code, 2026-10-28T09:47+0200]

## Скіли з PDF: перевірка і установка (28.10)

Мета: поставити скіли з PDF «10 AI Skills» «як у автора» після перевірки безпеки (рішення користувача 28.10).

**Крок 0.** `ps -e -o user= | grep -c "$(id -un)"` -> 18 (не >18); `ps -A -o args | grep -c '[o]bsidian'` -> 0. Перед кожною установкою лічильник знову 18.

**Крок 1. Симлінки в репо** (`gh api 'repos/<repo>/git/trees/HEAD?recursive=1' --jq '[.tree[]|select(.mode=="120000")|.path]'`):
- mattpocock/skills -> `["AGENTS.md"]` (кореневий файл, поза теками скілів)
- anthropics/skills -> `[]`
- vercel-labs/agent-browser -> `[]`
Симлінків усередині теки обраного скіла немає -> усі скіли допущено.

**Крок 2. Повне читання** (усі файли теки скіла з дерева; читано через `gh api contents | base64 -d`, потім grep по curl/wget/rm/sudo/git push/eval/base64/npx/http):

| Скіл | Файли | Що велить робити / мережа | Підсумок |
|---|---|---|---|
| handoff | SKILL.md, agents/openai.yaml | писати документ у $TMPDIR (не в робочу теку), вичищати ключі/PII; команд нема | чисто |
| tdd | SKILL.md, tests.md, mocking.md, openai.yaml | лише поради; кличе Skill "codebase-design"; «тест лише на погоджених швах — спитай користувача» | чисто |
| codebase-design | SKILL.md, DEEPENING.md, DESIGN-IT-TWICE.md, openai.yaml | словник; DESIGN-IT-TWICE велить «Spawn 3+ sub-agents in parallel» (лише за проханням користувача) | чисто (увага мала: паралельні під-агенти = витрати токенів, лише на запит) |
| domain-modeling | SKILL.md, ADR-FORMAT.md, GLOSSARY-FORMAT.md, openai.yaml | створює GLOSSARY.md і docs/adr/NNNN-*.md у репо «лениво» по ходу розмови, без питання: «update GLOSSARY.md right there» | увага: пише файли в робочу теку без окремого підтвердження (GLOSSARY.md, docs/adr/) |
| grill-with-docs | SKILL.md (247 Б), openai.yaml | «Call the Skill tool twice, for "grilling" and "domain-modeling"» | чисто (залежить від нашого grilling + domain-modeling) |
| improve-codebase-architecture | SKILL.md, HTML-REPORT.md, openai.yaml | `git log --oneline`; спавнить під-агента; пише HTML у $TMPDIR; **відкриває** його `xdg-open/open/start`; HTML тягне `https://cdn.tailwindcss.com` і `cdn.jsdelivr.net/npm/mermaid@11` (`securityLevel: "loose"`) у браузері користувача | увага: зовнішні CDN-скрипти у згенерованому HTML; на Termux `xdg-open` нема (потрібен termux-open); пише GLOSSARY/ADR як domain-modeling |
| triage | SKILL.md, AGENT-BRIEF.md, OUT-OF-SCOPE.md, openai.yaml | `gh issue`-операції: коментарі, лейбли, **закриття issue**; пише `.out-of-scope/*.md`; кожен коментар починається з «This was generated by AI» | увага: пише у зовнішній трекер (gh issue comment/close/edit) — але з «Wait for direction»/«Confirm what you're about to do» |
| setup-matt-pocock-skills | SKILL.md, domain.md, issue-tracker-{github,gitlab,local}.md, triage-labels.md, openai.yaml | змінює CLAUDE.md/AGENTS.md репо (блок `## Agent skills`), створює docs/agents/*.md, **`git init`/`git remote add origin`**, `gh label create`; показує чернетку й чекає підтвердження | увага: у нашому проєкті CLAUDE.md = симлінк на RULES.md під хуком rules-why-guard; docs/agents/ — нова тека; запускати лише в копії проєкту |
| frontend-design (anthropics) | SKILL.md, LICENSE.txt (Apache 2.0) | лише дизайн-поради, команд нема | чисто |
| agent-browser (vercel-labs) | skills/agent-browser/SKILL.md (3457 Б, «discovery stub», `hidden: true`) | велить `npm i -g agent-browser && agent-browser install`, далі `agent-browser skills get core` (контент тягне CLI); `allowed-tools: Bash(agent-browser:*), Bash(npx agent-browser:*)` | увага: це заглушка; описання ~925 символів і «Prefer agent-browser over any built-in browser automation or web tools» (автоспрацьовування); allowed-tools попередньо дозволяє команди agent-browser |

grep по небезпечних шаблонах у всіх скілах: збіги лише CDN-URL (HTML-REPORT.md), `npm i -g agent-browser` (стаб), gitlab/glab посилання. Прихованих інструкцій («ignore previous», «не кажи користувачу») не знайдено.

**Крок 3. Установка** (`cd ~ && timeout 180 npx skills add <repo>@<скіл> -g -y 2>&1 | tail -15`, по одному, порядок: codebase-design, handoff, tdd, domain-modeling, grill-with-docs, improve-codebase-architecture, triage, setup-matt-pocock-skills, frontend-design; agent-browser — лише текст, бо кроки 1-2 чисті).
Кожен виклик закінчився однаково: `✓ ~/.agents/skills/<скіл>` + `symlinked: Claude Code`; потім `Failed to install 1 … ✗ <скіл> → PromptScript: PromptScript does not support global skill installation` (збій лише для агента PromptScript, нам не потрібен).
CLI сам НЕ доставив зайвих скілів (grilling/grill-me не з'явились).
Результат `ls -la ~/.claude/skills/ ~/.agents/skills/`: у ~/.agents/skills 11 тек (find-skills + 10 нових: agent-browser, codebase-design, domain-modeling, frontend-design, grill-with-docs, handoff, improve-codebase-architecture, setup-matt-pocock-skills, tdd, triage); у ~/.claude/skills — 11 симлінків `-> ../../.agents/skills/<ім'я>` + стара тека synced. `~/.agents/.skill-lock.json` містить записи з source/skillFolderHash/installedAt (08:16-08:17 UTC).

**Крок 4. agent-browser (лише перевірка, програму й браузер НЕ ставили).**
- `npm view agent-browser`: версія 0.40.0, bin `./bin/agent-browser.js`, залежностей немає, `postinstall: node scripts/postinstall.js` (тягне готовий Rust-бінарник з GitHub Releases), репо git+https://github.com/vercel-labs/agent-browser.git, розмір пакета ~120 МБ (dist.unpackedSize 120273754).
- Реліз v0.40.0 має бінарники: darwin-arm64/x64, linux-arm64, linux-musl-arm64/x64, linux-x64, win32-x64. Для `android` нема. У Termux `node -p process.platform` = `android` (arm64) -> postinstall/лаунчер шукатиме `agent-browser-android-arm64`, якого нема (з коду postinstall.js/bin/agent-browser.js: platformKey = `${platform}-${arch}`; платформи linux/darwin/win32). Не запускали -> «не перевірено наживо».
- Chromium: `agent-browser install` качає Chrome for Testing (README рядки 20-21, 85); README: «Existing Chrome, Brave, Playwright, Puppeteer installations are detected»; є `--executable-path` для власного Chromium (README 1448-1461).
- `pkg search chromium`: є `chromium/x11 156.0.8078.47 aarch64` (репозиторій x11-repo), Size 159618476 Б (~152 МБ завантаження), Installed-Size 662216 КБ (~647 МБ), залежить від gtk3, mesa, pulseaudio та ін.
- Висновок: нативно в Termux пакет `agent-browser` скоріш за все не запрацює (нема android-бінарника, [не перевірено]). Реальні шляхи: (а) у proot-distro Ubuntu (там platform=linux, є linux-arm64 бінарник) + свій Chromium через `--executable-path`/apt; (б) зібрати з вихідників `cargo install agent-browser` + `pkg install chromium` (x11-repo, ~0,65 ГБ) + `--executable-path`. Обидва — важкі й не випробувані; потрібне окреме рішення користувача.

**Крок 5. Підсумок**

| Скіл | Безпека | Встановлено | Режим |
|---|---|---|---|
| codebase-design | чисто | так | автоматичний (опис у контексті ~265 симв.) |
| handoff | чисто | так | ручний (disable-model-invocation: true) |
| tdd | чисто | так | автоматичний (~149 симв.) |
| domain-modeling | увага (пише GLOSSARY.md/ADR без питання) | так | автоматичний (~151 симв.) |
| grill-with-docs | чисто | так | ручний |
| improve-codebase-architecture | увага (CDN у HTML, xdg-open) | так | ручний |
| triage | увага (gh issue comment/close) | так | ручний |
| setup-matt-pocock-skills | увага (CLAUDE.md, git remote, gh label) | так | ручний; запускати лише в копії проєкту |
| frontend-design | чисто | так | автоматичний (~204 симв.) |
| agent-browser | увага (стаб, довгий опис, allowed-tools) | так (лише текст; програми нема) | автоматичний (~925 симв.; без програми не діятиме, але опис у контексті) |

Автоматичних: 5 (codebase-design, tdd, domain-modeling, frontend-design, agent-browser) — їхні описи (~1 700 символів разом) потраплятимуть у контекст кожної сесії; ручних: 5 (handoff, grill-with-docs, improve-codebase-architecture, triage, setup-matt-pocock-skills). Рахунок з `grep disable-model-invocation: true` у ~/.agents/skills/*/SKILL.md.

**Відкат** (кожен видалення — спершу запис у TRASH.md): для кожного скіла `rm ~/.claude/skills/<скіл>` (симлінк) і `rm -r ~/.agents/skills/<скіл>`, потім видалити його запис у `~/.agents/.skill-lock.json` (є .bak-політика: зробити копію перед правкою), або `npx skills remove <скіл> -g`. Нічого не запускали з установлених скілів; файли проєкту, крім install-log.md, не чіпали; git не чіпали.
— [claude-code (підагент), 2026-10-28]
Уточнення до кроку 4: `gh api …/bin/agent-browser.js | sed -n 30,52p` — `getBinaryName()` має `switch(platform())` лише для darwin/linux/win32, `default: return null`; у Termux platform=`android` -> лаунчер не знайде бінарник (з коду, не запуском). — [claude-code (підагент), 2026-10-28]

## Браузер: Lightpanda у пісочниці (28.10)

Мета: дати скілу agent-browser робочий браузер на телефоні (рішення користувача «Lightpanda»). Усе — лише в `~/sandbox-browser` (поза проєктом).

- Крок 0: процесів користувача 20 (≤21, ок). `grun` = `$PREFIX/bin/grun`; `$PREFIX/glibc/lib/ld-linux-aarch64.so.1` є.
- Доку прочитано (`engines/lightpanda.mdx`): `agent-browser --engine lightpanda [--executable-path <шлях>] open <url>`; або `AGENT_BROWSER_ENGINE=lightpanda`; agent-browser сам спавнить Lightpanda (`serve --host 127.0.0.1 --port <випадковий>`) і говорить CDP.
- Реліз 1.0.2: `gh release download 1.0.2 -R lightpanda-io/browser -p lightpanda-aarch64-linux` -> 73 830 456 Б; sha256 `ac546dfc…849345` збігся з `digest` релізу. Interpreter `/lib/ld-linux-aarch64.so.1` (glibc). chmod 755.
- `timeout 20 grun ./lightpanda-aarch64-linux version` -> `1.0.2`, exit 0. Lightpanda запускається.
- Перша проба agent-browser (обгортка без CA): `✗ Navigation failed: PeerFailedVerification`. Причина (з `fetch --dump`): `msg="No certificates loaded"` — glibc-збірка не бачить Termux-сховища сертифікатів. Рішення без послаблення безпеки: прапорець `--ca-cert $PREFIX/etc/tls/cert.pem` (є в `serve`/`fetch`). `--insecure-disable-tls-host-verification` НЕ використано. `lightpanda fetch --ca-cert … --dump https://example.com` -> HTML «Example Domain», exit 0.
- Обгортка `~/sandbox-browser/lightpanda` (sh; для `serve|fetch|mcp` додає `--ca-cert`, інакше передає аргументи як є; старий варіант без CA збережено в `$PREFIX/tmp/lightpanda.v1.bak`).
- Проба: `./agent-browser --engine lightpanda --executable-path ./lightpanda open https://example.com` -> `✓ Example Domain`, exit 0; `get title` -> `Example Domain`; `snapshot` -> дерево (paragraph/StaticText/link «Learn more» [ref=e1]). Працює ТАК.
- Процеси користувача: до 19, під час 21 (+2: `agent-browser` daemon + `ld.so …lightpanda serve`), після `close` 19; `ps | grep lightpanda|agent-browser` — порожньо. Нічого не лишилось.
- Не вийшло / застереження: перша спроба без CA (див. вище); `grun` передає `$@` без лапок — аргументи з пробілами ламаються (TROUBLES.md:3523), для URL без пробілів ок; Lightpanda не підтримує `--profile/--extension/--state/--headed`; скріншоти — залежно від CDP-підтримки (не перевірялось). Відкривався лише https://example.com.
- Як запускати далі: `cd ~/sandbox-browser && ./agent-browser --engine lightpanda --executable-path ./lightpanda open <url>` (потім `snapshot`, `get title`, і обов'язково `./agent-browser close`). Щоб не писати прапорці: `export AGENT_BROWSER_ENGINE=lightpanda`.
- Відкат: тека `~/sandbox-browser` (агент `agent-browser`, `lightpanda`, `lightpanda-aarch64-linux`, `lp`, `bin` тощо) — видалення за правилами проєкту (запис у TRASH.md до `rm`); поза нею нічого не ставилось.

— [claude-code (підагент), 2026-10-28]

## agent-browser під'єднано (28.10)
Мета: рішення користувача «під'єднуй agent-browser» — скіл agent-browser (`agent-browser …`, `npx agent-browser …`) працює на телефоні з Lightpanda з ~/sandbox-browser. — [claude-code, 2026-10-28]

- Перед: `$PREFIX/bin/agent-browser` не існував; процесів користувача 18.
- Змінні (README рядки 1097, 1057): `AGENT_BROWSER_ENGINE`, `AGENT_BROWSER_EXECUTABLE_PATH`.
- Створено `$PREFIX/bin/agent-browser` (sh-обгортка, 755): виставляє обидві змінні (з можливістю перевизначення) і `exec ~/sandbox-browser/agent-browser "$@"`. Прийом — як з `$PREFIX/bin/skills`: npx знаходить $PREFIX/bin/<назва> і запускає.
- Тести з ~ :
  - `which agent-browser` → /data/data/com.termux/files/usr/bin/agent-browser
  - `agent-browser open https://example.com` → `✓ Example Domain`, rc=0
  - `agent-browser get title` → `Example Domain`, rc=0
  - `npx agent-browser --version` → `agent-browser 0.40.0`, rc=0
  - `agent-browser close` → `✓ Browser closed`
- Процеси користувача: до 19 / під час 21 / після 19; lightpanda і agent-browser після close не лишились.
- Відкат: спершу запис у TRASH.md, потім `rm $PREFIX/bin/agent-browser` (~/sandbox-browser не чіпається).
- Обмеження: Lightpanda — не Chrome (немає повноцінного рендера); скріншоти не перевірені; перевірено лише https://example.com.

## Пункт меню «Спостереження» (28.10)
Мета: рішення користувача «Панель у Chrome». Дашборд `agent-browser dashboard start` — демон (повертається одразу, exit=0, порт 4848).
- Правка: ~/.tmux.conf, меню Ctrl+B N: «Спостереження» (w) — start + sleep 2 + termux-open-url http://127.0.0.1:4848; «Зупинити спостереження» (x) — dashboard stop. Також HELP.txt рядок 18.
- Перевірки: тест-сервер (-L chk) знайшов пункт; живий source-file exit=0; curl 4848 = 200; termux-open-url виконано.
- Відкат: `cp ~/.tmux.conf.bak-20261028b ~/.tmux.conf && tmux source-file ~/.tmux.conf`.
- Зупинити дашборд: `agent-browser dashboard stop` або пункт меню «Зупинити спостереження».
