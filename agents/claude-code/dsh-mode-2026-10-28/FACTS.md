# Як запускати DSH — факти для рішення (2026-10-28)

Напрям «Якість роботи агентів» › пункт «Далі» №1 естафети #98 (HANDOFF.md:457) › збір фактів.
Автор: під-агент claude-code, лише читання. — [claude-code, 2026-10-28]

Скорочення: `R` = `$PREFIX/var/lib/proot-distro/containers/ubuntu/rootfs` (TROUBLES.md:6694 — НЕ installed-rootfs);
`N` = `R/root/dsh-app/node_modules/@deepseek-ai`.

## 1. Факти з опорою

### 1.1 Режими доступу DSH
- Три пресети в базовому конфігу: `N/dsh-base/cordis.patch.yml:254-262` — `read-only` (sandbox read-only, approval ask),
  `workspace-write` (sandbox workspace-write, approval ask), `danger-full-access` (sandbox danger-full-access, approval never).
- Що кожен дозволяє (`N/dsh-sandbox/README.md:58-60`): read-only — «Denies writes except required sinks such as /dev/null»;
  workspace-write — «Allows writes under the workspace root plus a backend-defined temp area»; danger-full-access —
  «Bypasses confinement; the consumer spawns its original argv».
- Корінь workspace = тека запуску: `cordis.patch.yml:233` `workspaceRoot: !!js process.cwd()`.
- Режим за замовчуванням = змінна середовища: `cordis.patch.yml:232`
  `mode: !!js process.env.DSH_PERMISSION_MODE ?? 'workspace-write'`; approval — `:248`: `'never'` лише якщо змінна =
  `danger-full-access`, інакше `'ask'`.
- Драбина підвищення: «`workspace-write` only to `danger-full-access`» (`N/dsh-sandbox/README.md:100`).
- Нема бекенда пісочниці → відмова, а не запуск без обмежень: «fails with SANDBOX_UNAVAILABLE rather than running
  unconfined» (`N/dsh-sandbox/README.md:70`). На цьому хості бекенда (bwrap/Landlock) немає фізично — TROUBLES.md:3591-3597.
  Тобто і `workspace-write`, і `read-only` на цьому телефоні = bash не працює взагалі; працюють лише файлові інструменти
  (in-process fence) — TROUBLES.md:3598-3601.
- Пресет за замовчуванням можна задати і через налаштування `permission.defaultPreset` (`N/dsh-permission-presets/README.md:64`:
  «holds defaultPreset for future sessions… Later settings changes never alter an existing session»).

### 1.2 Як DSH запускається зараз
- tmux-work.sh:26-27 — вікно `dsh`, `exec ~/AgentReachProject/run-dsh.sh`.
- run-dsh.sh:8-9 — `proot-distro login ubuntu -- bash -lc 'cd /root/dsh-app && DSH_TUI_RETENTION_MAX_COUNT=0 exec
  /root/dsh-app/node_modules/.bin/dsh --profile tui'` — `DSH_PERMISSION_MODE` НЕ задано → workspace-write, корінь `/root/dsh-app`.
- Профіль tui (`R/root/.dsh/profiles/tui/cordis.patch.yml:1-18`) містить лише модель/reasoningEffort і askUser — режиму доступу немає.
- `/permission danger-full-access` не зберігається між сесіями — TROUBLES.md:3972-3974; JOURNAL DSH:280.
- run-dsh.sh створив DSH (run-dsh.sh:2); правку 22.10 (exec) внесено без його підтвердження (run-dsh.sh:6, TROUBLES.md:5824).

### 1.3 Що сталося в cc-2810-1 (28.10)
`agents/claude-code/chains-2026-10-25/dsh-check-cc-2810-1.md:12-40`: `date` → SANDBOX_UNAVAILABLE; підвищення для bash і edit →
«sandbox escalation to "danger-full-access" requires approval, but no approval channel is available»; edit synthesis.md →
«file access denied under workspace-write mode» («Запис файлів дозволено лише під /root/dsh-app»); наслідки — немає date, git,
zstd, запису в JOURNAL і коміту. Також 23.10: екран `📁 ~/dsh-app (Workspace Write)`, журнал і коміт не зроблено (TROUBLES.md:6057-6061).
26.10 екран показував «Full access» (BACKLOG.md:42).

### 1.4 Що писали раніше
- 01.10: лікування — користувач змінив політику на danger-full-access + approval never; «sandbox_permissions просити не можна
  (апруви вимкнено — дія, що їх вимагає, падає одразу)» — TROUBLES.md:3602-3605; те саме HANDOFF.md:544 («Обережно #56»).
- 30.09: «у моїй сесії немає кліків (danger-full-access + approval: never)» — agents/dsh/README.md:87.
- 25.10 DSH: «проєктні RULES.md до DSH не доходять: cwd /root/dsh-app, .git там немає, читається лише ~/.dsh/AGENTS.md» —
  agents/dsh/JOURNAL.md:600; варіанти — «запускати DSH з теки проєкту (щоб діяли RULES.md) чи через customSkillDirs» — :601.
- 26.10/27.10: headless без змінної «тихо нічого не виконує»; агент обходить через glob/read і подає здогад як факт —
  TROUBLES.md:6583-6589; JOURNAL DSH:680; `R/root/.dsh/AGENTS.md:74-76`.
- JOURNAL DSH:299: «run-dsh.sh досі без DSH_PERMISSION_MODE… чекає рішення користувача»; готовий скрипт dsh-enable-now.sh,
  але він зламаний під прямий лончер (шукає `npx dsh`) — JOURNAL DSH:600.
- Ланцюг інструкцій dsh: `$DSH_HOME/AGENTS.md` + кожен AGENTS.md/CLAUDE.md «from the project root down to the session working
  directory»; корінь — тека з `.git` (`N/dsh-agent-instructions/README.md:32,36,63-64`). У проєкті `AGENTS.md -> CLAUDE.md -> RULES.md`
  (ls -la; RULES.md 25 909 Б; `R/root/.dsh/AGENTS.md` 10 455 Б; ліміт `maxBytes: 65536` — cordis.patch.yml, блок agent-instructions).

### 1.5 Попередні рішення користувача
- 30.09 «Проба: DSH без кліків в ізоляції — етап 1 ПРОЙДЕНО (рішення користувача)» — BACKLOG.md:625-638; етап 2 (справжній
  проєкт) не почато: «вирішити стоп-механізм…, сесія бачить cwd як /root/proj-trial (наслідки не перевірено)».
- 03.10: «повний доступ DSH — «Ні, лишити вручну»» — коміт 617d390 (git show); HANDOFF.md:154.
- 25.10: «Так, платно — введу /permission» — TROUBLES.md:6252 (користувач вмикав доступ руками під конкретний лист).
- Загальний принцип: «не заборона…, а потрібно у важливих питаннях питати» — пам'ять permission-gates-not-bans.
- Клавіші/зміну дозволів у вікні DSH дає лише користувач — TROUBLES.md:3766-3772.

### 1.6 Ризики за записами
- Хуки Claude Code у DSH не стріляють: «усі 10 хуків (16 команд) у dsh не стріляють… trash-md-guard, rules-why-guard,
  troubles-grep не захищають: у dsh це дисципліна» — TROUBLES.md:3672-3676 (перевірено 01.10; новіші хуки — не перевірено).
- Git-хуки діють і для DSH (commit-msg, pre-commit секрети) — TROUBLES.md:5872.
- Ярлики l2s: файли DSH з proot стають симлінками (git status → T), з proot не видно, лагодить лише зовнішній — TROUBLES.md:3969-3970,
  4146-4156; причина — `--link2symlink` + linkFile у dsh-fs-local (HANDOFF.md:151).
- danger-full-access: підпроцеси без меж — Termux-ФС видима й доступна на запис з proot (TROUBLES.md:3473); обіцянки «запис лише
  під workspace» немає (TROUBLES.md:3603-3604). У тій самій ФС лежить agent.py з ключем (RULES.md, розділ Git).
- Випадків шкоди від DSH у Full access пошуком не знайдено (grep «DSH … без згоди|без дозволу|видалив|rm -rf» по TROUBLES/BACKLOG/
  RULES-WHY — 0 про DSH); є порушення меж листа (роздав під-агентів усупереч листу — TROUBLES.md:6250-6253).

## 2. Варіанти

| Варіант | Що дозволяє | Чим ризикує (опора) | Що змінити | Відкат |
|---|---|---|---|---|
| (г) Як зараз: workspace-write + користувач вводить `/permission danger-full-access` у вікні DSH, коли треба | Права вмикає людина під задачу; рішення 03.10 «лишити вручну» (617d390) | Забули ввести → shell/git/date мертві, DSH обходить і вгадує (cc-2810-1:12-40; TROUBLES:6583-6589); після ввімкнення — ті самі ризики, що в (а) | Нічого; перед листом — перевірка екрана DSH на «Full access» | Перезапуск DSH → знову workspace-write (TROUBLES:3972) |
| (а) Постійно danger-full-access | bash/git/date без кліків з першого кроку (cordis.patch.yml:232,248) | Запис будь-куди, зокрема Termux-home (TROUBLES:3473, 3603); guard-хуки Claude не діють (TROUBLES:3672-3676), лише git-хуки (5872); l2s (3969); підвищення не попросити (3604); суперечить рішенню 03.10 (617d390) | run-dsh.sh:9 — додати `DSH_PERMISSION_MODE=danger-full-access` перед `exec`; згода DSH на правку його скрипта (TROUBLES:5824) | `git checkout -- run-dsh.sh` (файл під git: git log 8d6206b) і перезапуск вікна dsh |
| (б) Запуск з теки проєкту, режим той самий | Файлові інструменти пишуть у проєкт (workspaceRoot = cwd, cordis.patch.yml:233); діє ланцюг проєкту AGENTS.md→RULES.md (agent-instructions README:32,36) | bash/git/date однаково НЕ працюють — бекенда нема незалежно від cwd (TROUBLES:3583-3586, 3591-3597) → проблему cc-2810-1 вирішує лише наполовину; запис у `/root/dsh-app`, `/root/.dsh` стане поза workspace [не перевірено]; RULES.md написано для Claude Code (хуки, скіли) — як DSH це сприйме [не перевірено]; тека сесій зміниться з `--root-dsh-app--` (TROUBLES:6509) — хто на неї спирається [не перевірено] | run-dsh.sh:9 — `cd /data/data/com.termux/files/home/AgentReachProject` замість `cd /root/dsh-app` | `git checkout -- run-dsh.sh` |
| (в) = (а)+(б) | Повний shell + проєктні RULES.md як інструкції | Сума ризиків (а) і (б); workspaceRoot у danger-full-access не обмежує (README:60) | run-dsh.sh:9 — обидві правки | `git checkout -- run-dsh.sh` |
| (д) Ізольований DSH (agents/claude-code/run-dsh-isolated.sh) | danger-full-access на КОПІЇ проєкту в `proot --isolated` (run-dsh-isolated.sh:14-17); етап 1 пройдено (BACKLOG:625-634) | Зміни не потрапляють у справжній проєкт; етап 2 не почато, відкриті питання — стоп-механізм, baton, cwd (BACKLOG:636-638); копії прибирати через TRASH.md | Запуск run-dsh-isolated.sh замість run-dsh.sh; перенесення змін з копії — механізм не визначено | Повернутися до run-dsh.sh; копію `/root/proj-trial` — у .trash/ із записом у TRASH.md |
| (е) `permission.defaultPreset` у налаштуваннях | Пресет для нових сесій без зміни скрипта (presets README:64) | Як (а), якщо `danger-full-access`; як цей ключ взаємодіє зі змінною `cordis.patch.yml:232` і approval `:248` — НЕ перевірено | Невідомо, в якому файлі профілю tui (не перевірено) | Видалити ключ [не перевірено] |

## 3. Не знайдено / не перевірено
- Чому в cc-2810-1 «no approval channel is available» — тобто чому в workspace-write+ask DSH не зміг попросити підвищення
  у користувача (через лист у tmux? через TUI?). Не перевірено; від цього залежить, чи (г) взагалі може працювати «з питанням».
- Чи щось (cost-report, baton, хуки) прив'язане до шляху сесій `--root-dsh-app--` — для (б)/(в) не перевірено
  (tools/cost-report.py:68 згадує лише /root/dsh-app/cost-waste.md).
- Чи нові хуки після 01.10 так само не діють у DSH — перевірки після TROUBLES:3672 не знайдено.
- Механізм і файл для `permission.defaultPreset` (варіант е) — не перевірено.
- Чи DSH дасть згоду на правку run-dsh.sh (його скрипт) — не питали; домовленості з DSH потребують його підтвердження.
- Повного аудиту «чи шкодив DSH у Full access» немає — лише grep з п.1.6.
Рішення 28.10: «Вручну + перевірка» — BACKLOG «Активні» (перший пункт). — [claude-code, 2026-10-28]
