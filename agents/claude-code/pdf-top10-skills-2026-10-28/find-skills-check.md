# find-skills (vercel-labs/skills) — перевірка перед встановленням (2026-10-28)

Мета: кроки 1–3 правила «Перед ВСТАНОВЛЕННЯМ стороннього». Нічого не встановлено (npx/npm install/node на чужому коді не запускались; лише `npm pack` + `tar -xzf` у /data/data/com.termux/files/usr/tmp/skills-audit/pkg/). Рекомендації «ставити/не ставити» тут немає.
Посилання `cli.mjs:N` = рядок у `dist/cli.mjs` з тарбола skills@1.7.4 (8943 рядки, розпакований у пісочницю).

## 1. SKILL.md

Автор і версія файлу:
- Репо vercel-labs/skills, власник — `Organization` (`gh api repos/vercel-labs/skills --jq .owner.type`), homepage https://skills.sh, відкритих issues+PR у лічильнику API: 1211.
- Шлях `skills/find-skills/SKILL.md`; в теці скіла лише один файл (`gh api .../contents/skills/find-skills` → `SKILL.md file 5472`). Інших файлів (скриптів, references) немає.
- Наш сирий файл збігається з репо дослівно: `git hash-object sources/find-skills.SKILL.md` = `a41bdd074bb587afd861332cf2f473f3154de4d7` = `gh api .../contents/skills/find-skills/SKILL.md --jq .sha`.
- Останні коміти файлу: `773fb2c7 2026-07-10 docs(find-skills): remove redundant check command`; `ceea0088 2026-06-23 init`; `0b8fb22a 2026-03-13 docs(find-skills): add quality verification and leaderboard check (#547)`. Тобто це остання версія; файл не змінювався з 10.07.

Прочитано повністю (141 рядок). Команди, які він велить запускати (дослівно):
- рядок 27: `npx skills find [query] [--owner <owner>]`
- рядок 28: `npx skills add <package>`
- рядок 29: `npx skills update`
- рядок 56 (Step 3): ```npx skills find [query] [--owner <owner>]```; приклади 61–63: `npx skills find react performance`, `npx skills find pr review`, `npx skills find changelog`
- рядок 90 (приклад відповіді користувачу): `npx skills add vercel-labs/agent-skills@react-best-practices`
- рядок 100 (Step 6): ```npx skills add <owner/repo@skill> -g -y```
- рядок 131/140: `npx skills init` / `npx skills init my-xyz-skill`
- Також велить дивитись https://skills.sh/ (лідерборд, рядки 31, 45) — як посилання; curl/WebFetch не наказано.

Місця, де діяти без питання:
- Рядок 103: «The `-g` flag installs globally (user-level) and `-y` skips confirmation prompts.» Тобто саме встановлення в SKILL.md — з `-y` (без підтвердження CLI).
- Але рядок 95–97: «### Step 6: Offer to Install — If the user wants to proceed, you can install the skill for them» — тобто за текстом скіла встановлення лише після згоди користувача; Step 5 (рядки 73–80) велить спершу показати варіанти й команду.
- Step 4 (рядки 65–71): «Do not recommend a skill based solely on search results» — перевірка інсталів (≥1K), репутації джерела, зірок (≥100).
- Жодних інших «без питання» (прихованих curl, eval, записів у файли, мережевих дій окрім npx skills) у файлі немає — перевірено читанням усіх 141 рядка.

Висновок по кроку 1: SKILL.md сам нічого не виконує; усе виконання — через `npx skills …`, тобто через npm-пакет `skills` (розділ 2). Кожен `npx skills …` при першому запуску завантажує й виконує код пакета з npm.

## 2. CLI skills: find / add -g / телеметрія / скрипти / Termux

### Метадані npm (дослівно `npm view skills name version maintainers bin dependencies scripts time.modified dist.tarball repository.url`)
```
name = 'skills'
version = '1.7.4'
maintainers = [ 'rauchg <rauchg@gmail.com>', 'quuu <qual1337@gmail.com>' ]
bin = { skills: 'bin/cli.mjs', 'add-skill': 'bin/cli.mjs' }
dependencies = { tar: '^7.5.20', yaml: '^2.8.3' }
scripts = { dev, test, build: 'node scripts/generate-licenses.ts && obuild', format, prepare: 'husky', 'exec:test', 'type-check', 'format:check', prepublishOnly: 'npm run build', 'publish:snapshot': ..., 'generate-licenses' }
time.modified = '2026-10-19T20:35:25.624Z'
dist.tarball = 'https://registry.npmjs.org/skills/-/skills-1.7.4.tgz'
repository.url = 'git+https://github.com/vercel-labs/skills.git'
```
Додатково: `dist.attestations.provenance.predicateType = https://slsa.dev/provenance/v1` (є провенанс-атестація; сам запис НЕ верифіковано); `gitHead = a80e4c9d12d607631249d4d7d059f835d4b2f13a`; dist-tags `latest: 1.7.4`; реліз v1.7.4 — 2026-10-19T20:34:33Z (gh releases). maintainers rauchg (Guillermo Rauch, засновник Vercel — з публічних знань, [не перевірено в цій сесії]) і quuu.
Вміст тарбола: bin/cli.mjs (305 байт, лише enableCompileCache + `await import('../dist/cli.mjs')`), dist/cli.mjs (343 926 байт, 8943 рядки, не мініфікований), 10 чанків залежностей у dist/_chunks/libs (simple-git, @clack, picocolors, xdg-basedir, @vercel/detect-agent…), docs/, README, LICENSE. Мінімізованого/обфускованого коду немає.

### (г) Скрипти встановлення
- У package.json тарбола немає `preinstall`/`install`/`postinstall` (дивись scripts вище). Є `prepare: husky` і `prepublishOnly` — це скрипти розробки; `prepublishOnly` — тільки при публікації. `prepare` за документацією npm не запускається для пакета, встановленого з реєстру, тільки для локального/git [не перевірено запуском — npx не запускали].
- Залежності: `tar ^7.5.20`, `yaml ^2.8.3` (у dist вшито ще simple-git тощо). Відкритий PR #2598 «fix: upgrade tar to 7.5.21 (CVE-2026-73566)» (open, 2026-10-27) — тобто для tar ^7.5.20 є відомий CVE-фікс, ще не злитий [деталі CVE не читались].
- `engines.node >=22.20.0`; тут `node -v` = v26.4.0, `git --version` = 2.55.0 (git потрібен: клонування — cli.mjs:758 `git.fetch(--depth 1 …)`, cli.mjs:983 `execFile("git", …rev-parse)`).

### (а) Що робить `find` і куди йдуть мережеві запити
- cli.mjs:6001 `const SEARCH_API_BASE = process.env.SKILLS_API_URL || "https://skills.sh";` (перевизначається змінною SKILLS_API_URL).
- cli.mjs:6048–6070 `searchSkillsAPI`: `GET ${SEARCH_API_BASE}/api/search?q=<запит>&limit=…[&owner=…]`; повертає name/id/source/installs. Тобто текст пошукового запиту йде на skills.sh.
- cli.mjs:6217 `track({event:"find", query, resultCount})` і 6245 `track({event:"find", query:"", resultCount, interactive:"1"})` — запит `find` також надсилається в телеметрію (на www.skills.sh/tele/t).
- Скільки доменів у коді взагалі (grep `https?://`): api.github.com (cli.mjs:82, 3837), github.com (240), gitlab.com (214), raw.githubusercontent.com (4054), skills.sh (3831), www.skills.sh (2798–2799), connectors-skills.zapier.com (3832, лише для зареєстрованого `zapier/connectors`), notion.so/developers.notion.com (8701, 4284; через бінарник `ntn`, cli.mjs:4248 `spawn$1("ntn", …)`). Для `find` задіяно лише skills.sh (+ www.skills.sh для телеметрії).

### (б) Що робить `add <owner/repo@skill> -g -y`
- `-y` → `options.yes` (cli.mjs:5943); `-g` → global.
- Джерело: GitHub-репо клонується через simple-git `fetch --depth 1` у тимчасову теку (cli.mjs:758); для деяких власників — завантаження snapshot із skills.sh (`DOWNLOAD_BASE_URL = process.env.SKILLS_DOWNLOAD_URL || "https://skills.sh"`, cli.mjs:3832) [не простежено, які саме]. Також до `https://api.github.com/repos/<o>/<r>` для визначення приватності (cli.mjs:82–85 `isRepoPrivate`).
- Вибір агентів при `-y` без `--agent`: cli.mjs:5484 `detectInstalledAgents()` (2157–2161: для кожного агента `config.detectInstalled()`); якщо знайдено ≥1 — `targetAgents = ensureUniversalAgents(installedAgents)` (cli.mjs:5525–5527; 4663–4667 додає ВСІХ «універсальних» агентів з `skillsDir === ".agents/skills"` навіть без встановлення); якщо жодного не знайдено і `-y` — `targetAgents = validAgents` = усі агенти (cli.mjs:5509–5511 «Installing to all agents»).
- Claude Code: cli.mjs:1400 `claudeHome = process.env.CLAUDE_CONFIG_DIR?.trim() || join(home, ".claude")`; 1509–1519: `"claude-code": { skillsDir: ".claude/skills", globalSkillsDir: join(claudeHome, "skills"), detectInstalled: existsSync(claudeHome) }`. На цій машині `~/.claude` існує (ls), `~/.codex`, `~/.agents`, `~/.gemini`, `~/.cursor`, `~/.config/opencode` — НЕ існують (ls). Решту ~40 агентів (detectInstalled) не перевіряв — [не перевірено], які ще будуть виявлені.
- Куди пише (глобально): канонічна копія — cli.mjs:2210–2212 `getCanonicalSkillsDir`: `join(homedir(), ".agents", "skills")` → `~/.agents/skills/<skill>/` (AGENTS_DIR=".agents", SKILLS_SUBDIR="skills", cli.mjs:1186–1187). Для не-універсальних агентів (у т.ч. claude-code) — режим за замовчуванням `symlink` (cli.mjs:2288 `options.mode ?? "symlink"`): у `~/.claude/skills/<skill>` створюється відносний симлінк на канонічну копію (cli.mjs:2269–2270 `symlink(relativePath, linkPath)`; `junction` лише на win32). Якщо симлінк не вдався — fallback на копіювання (cli.mjs:2354 `copyDirectory`, `symlinkFailed: true`).
- Лок-файл: cli.mjs:3753–3759 `~/.agents/.skill-lock.json` (або `$XDG_STATE_HOME/skills/.skill-lock.json`). Лок також зберігає `dismissed` прапорці (cli.mjs:3817–3822). Проектний `skills-lock.json` — у cwd лише для не-global.
- Чи чіпає ~/.claude/ поза skills: у коді шляхів до ~/.claude, окрім `claudeHome/skills`, за grep не знайдено (cli.mjs:1400, 1511; ще `.claude-plugin/…` — це читання manifest у ЧУЖОМУ репо, cli.mjs:1048–1083, не запис). Але інші агенти пишуть у свої теки (~/.codex тощо), якщо виявлені/універсальні; універсальні агенти пишуть у спільний ~/.agents/skills.
- Копіювання вмісту: cli.mjs:2401–2425 `copyDirectory` використовує `cp(srcPath, destPath, { dereference: true, recursive: true })` — БЕЗУМОВНО розіменовує симлінки зі скіла. У репо виправлення злито 2026-10-26: PR #2589 «fix: confine skill symlink dereferencing to the skill directory (VULN-16995)» (`gh api repos/vercel-labs/skills/pulls/2589 --jq .merged_at` → 2026-10-26T19:42:30Z; опис: шкідливий скіл міг покласти симлінк `data -> ../../../.env` і отримати копію файлу поза теку скіла). Реліз 1.7.4 вийшов 2026-10-19, тобто ДО фіксу: npm-версія 1.7.4 вразлива (підтверджено читанням cli.mjs:2413 `dereference: true` без перевірки меж). Для find-skills з vercel-labs/skills ризик малий (єдиний файл SKILL.md, без симлінків — `contents` не показав), але стосується будь-якого скіла з чужого репо, який `find-skills` порадить поставити.
- Попередження самого CLI (cli.mjs:5058, 5876, 6922, вивід «Done!»): «Review skills before use; they run with full agent permissions.»
- Додатково: після `add` (інтерактивно, TTY, без -y) CLI одноразово пропонує поставити find-skills (cli.mjs:5898–5932 `promptForFindSkills`; з `-y` або без TTY — return). Для нашого випадку неактуально.

### (в) Телеметрія
- Є. cli.mjs:2798 `TELEMETRY_URL = "https://www.skills.sh/tele/t"`, 2799 `AUDIT_URL = "https://www.skills.sh/tele/audit"`.
- Вимкнення: cli.mjs:2808–2810 `isEnabled() { return !process.env.DISABLE_TELEMETRY && !process.env.DO_NOT_TRACK; }`. Достатньо будь-якої з двох змінних (`DISABLE_TELEMETRY=1` або `DO_NOT_TRACK=1`); README.md:104–105: «Set DISABLE_TELEMETRY=1 or DO_NOT_TRACK=1 to disable telemetry and security-audit requests.»
- Що надсилається (cli.mjs:2832–2843 `track` → `fetch(TELEMETRY_URL?params)`): версія CLI `v`, `ci=1` (якщо CI-змінні), `agent` (ім'я виявленого ШІ-агента, `@vercel/detect-agent`), плюс поля події. Події: `find` (query, resultCount — cli.mjs:6217, 6245), `install` (source, skills, agents, global, skillFiles = JSON списку файлів, installUrl, metadata — cli.mjs:4975, 5702, 5711), `update` (scope, лічильники — 7424/8208), `remove`, `experimental_sync`. Для GitHub-репо identifier надсилається лише якщо GitHub підтвердив, що репо публічне (cli.mjs:5702 `if (await repoPrivacyPromise === false) track(…)`; docs/troubleshooting.md:38–40); для інших типів джерела може піти source/skill без перевірки (cli.mjs:5711 `else track(…)`, 4975 для well-known). Тобто не лише «анонімний лічильник»: пошукові запити `find` і імена поставлених скілів відправляються.
- Також `fetchAuditData` (cli.mjs:2814–2830) при add робить GET на `…/tele/audit?source=…&skills=…` (security-оцінки); теж вимикається цими змінними.
- Параметра user id у `track` (cli.mjs:2833–2843) немає; IP, як і будь-який HTTP-запит, бачить сервер — [не перевірено, серверна сторона]. Фінальне очікування: `main().finally(() => flushTelemetry()…)` (cli.mjs:8942) чекає до 5 с.
- docs/troubleshooting.md:36–40 підтверджує існування телеметрії й змінних.

### (ґ) Termux / Android
- Єдина залежність від ОС в коді: cli.mjs:2269 `platform() === "win32" ? "junction" : void 0` (на Android/Linux → звичайний symlink). `process.platform` у коді не використовується (grep порожній). Шляхи — через `homedir()` (на Termux = /data/data/com.termux/files/home).
- Потрібні: Node ≥22.20 (є v26.4.0) і git (є 2.55.0). Симлінки на FS Termux: у проекті TROUBLES.md є записи про проблеми з симлінками зсередини proot (інший контекст — proot/git, не Termux-нативний); для `~/.claude/skills/` у самому Termux не перевірялось.
- Прямих термукс-звітів у issues немає (розділ 3). Реально запустити CLI на Termux НЕ пробували (заборонено) — [не перевірено].

## 3. Issues і відгуки

Лічильники (gh api search/issues): відкритих issues у vercel-labs/skills — 809 (`is:issue is:open`), відкритих PR — 402 (`is:pr is:open`). Репо: 36 909 зірок, ліцензія MIT, останній пуш 2026-10-28T04:18:52Z (primary.md).

Пошук по репо (`search/issues?q=repo:vercel-labs/skills+<слово>`, повний збіг лічильників; пошук нечіткий — багато збігів нерелевантні):
- telemetry — 233 збіги. Релевантні: #2525 [open] «Indexing request: mkayander/resale-ops installs successfully, but telemetry receives HTTP 403». Решта (#2560 lockfile, #2305, #780 …) стосуються листингів/lock, не приватності.
- security — 298 збігів. Релевантні: #2598 [open] «fix: upgrade tar to 7.5.21 (CVE-2026-73566)»; #2589 [closed] «fix: confine skill symlink dereferencing to the skill directory (VULN-16995)»; #2378 [open] «Review test-fixture malware classification in Archify Socket audit»; #2585 [open] «Request security re-audit: shiquda/open-pptd-skill/open-pptd»; #2230 [open] «Re-index ramus-dev/android-use and re-run Socket/Snyk audits…».
- termux — 2 збіги, обидва нерелевантні: #1010 [open] «spawn git ENOENT on Windows without git, and blob fast path is org-allowlisted»; #2441 [open] «Remove stale … listing».
- android — 20 збігів; релевантних до CLI на Android немає (#1010 Windows; решта — листинги скілів).
- symlink — 277 збігів. Релевантні: #456 [open] «[Bug]: Relative symlinks break when agent skills directory is itself a symlink»; #2594 [open] «`skills update` still skips mirrored skills from generic Git sources»; #2607 [open] «fix(update): keep copied skills as copies by recording installMode in the lock»; #2083 [closed] «do not skip symlink creation for non-Claude agents on project installs»; #2609 [open] «Skills that are also Claude Code plugins lose plugin.json and hooks on install» (з primary.md).
Вебпошуки (WebSearch) не виконувались — [не перевірено]: зовнішніх відгуків/статей про телеметрію й безпеку Vercel skills CLI немає в цьому звіті.

## 4. Ризики (кожен з доказом)

1. Автозапуск встановлення: SKILL.md Step 6 велить `npx skills add <owner/repo@skill> -g -y` (find-skills.SKILL.md:100–103) — `-y` пропускає підтвердження CLI; захист тільки текст «If the user wants to proceed» (рядок 97). Доказ: файл:рядки.
2. `-y` без `--agent` розкидає скіл по кількох агентах: ensureUniversalAgents додає всіх універсальних навіть без їх встановлення (cli.mjs:4663–4667, 5525–5527) → створення `~/.agents/skills/` (на цій машині `~/.agents` НЕ існує, ls) + лок `~/.agents/.skill-lock.json`; якщо жодного агента не виявлено — «all agents» (cli.mjs:5509–5511). Для Claude Code — симлінк `~/.claude/skills/<skill>` → `../../.agents/skills/<skill>` (cli.mjs:2269–2270, 2288). Наслідок для нашого проекту: це в ~/.claude/skills (глобальна тека), а не в `.claude/skills` проекту; симлінки в проєкті в минулому давали проблеми (TROUBLES.md, теги symlink) — але стосовно git/proot.
3. Телеметрія за замовчуванням увімкнена і включає текст `find`-запитів та імена поставлених скілів (cli.mjs:6217, 5702–5711, 2808–2810); вимикається `DISABLE_TELEMETRY=1`/`DO_NOT_TRACK=1`. Скіл не вказує вимкнути; змінну треба виставити самому в оточенні запуску.
4. Відома вразливість symlink-dereference у опублікованій 1.7.4: cli.mjs:2413 `dereference: true`; фікс злитий у main 2026-10-26 (PR #2589), npm-реліз 1.7.4 від 2026-10-19 його не містить (npm `latest` = 1.7.4, `npm view skills dist-tags`). Стосується скілів із чужих репо (не find-skills).
5. Залежність tar ^7.5.20 з відкритим CVE-PR #2598 (package.json тарбола: `"tar": "^7.5.20"`); npx встановить найновіший 7.x за semver, тож фактична версія tar залежить від реєстру на момент запуску [не перевірено].
6. `npx skills …` кожного разу виконує код з npm (мейнтейнери rauchg, quuu; є SLSA-провенанс-запис, не верифіковано) — підвищена довіра до Vercel, але SKILL.md не фіксує версію (`npx skills`, не `skills@1.7.4`).
7. Скіли, які CLI встановлює, — це ще більше інструкцій для агента («they run with full agent permissions», вивід CLI); `find-skills` у Step 4 радить критерії довіри (≥1K інсталів, офіційні джерела), але це самоперевірка моделі, не механізм.
8. Termux: симлінки/ОС-залежності в коді мінімальні (єдине `platform()` у cli.mjs:2269), але CLI на Android не запускали.

## 5. Не перевірено
- Реальний запуск `npx skills find/add` на Termux (заборонено): чи працюють симлінки у ~/.claude/skills, чи нормально поводиться Node 26 + simple-git.
- Які саме з ~40 агентів CLI виявить на цій машині через `detectInstalled` (перевірено лише існування ~/.claude, ~/.codex, ~/.agents, ~/.gemini, ~/.cursor, ~/.config/opencode).
- Чи запускає npx `prepare: husky` (за документацією npm — ні для реєстрового пакета; запуском не перевірялось).
- Що саме має CVE-2026-73566 у tar і яку версію tar візьме npx; SLSA-атестація (не верифікована).
- Серверна сторона skills.sh/tele/t: що зберігається, чи IP логується; відповідь /api/search.
- Шлях `DOWNLOAD_BASE_URL` (skills.sh snapshot) — для яких власників використовується (cli.mjs:3832) не простежено.
- Зовнішні відгуки поза репо (WebSearch не виконувався).
- Особа maintainer `rauchg` = Guillermo Rauch з Vercel — з загальних знань, не перевірено.
