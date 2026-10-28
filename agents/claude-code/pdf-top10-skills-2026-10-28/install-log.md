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
