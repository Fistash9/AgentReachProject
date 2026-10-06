# Скіли DSH: звідки він їх бере і чому зараз 0 (2026-10-06)

Запит користувача: «а у дш теж є скіли , ти знаєш як ним користуватись на повну ?)».
Джерело: README пакета `@deepseek-ai/dsh-skill-filesystem` у proot
(`/root/dsh-app/node_modules/@deepseek-ai/dsh-skill-filesystem/README.md`, 162 рядки).

## Факти (перевірено командами 2026-10-06)
- Вікно DSH (tmux work:3, tui, тека `~/dsh-app`): `mcp 0 · skills 0/0 · plugins 3`.
- Корені пошуку скілів (README «Roots and priority»): `<корінь>/.dsh/skills` (100),
  `<корінь>/.agents/skills` (200), `Config.customSkillDirs` (300), `~/.dsh/skills` (400),
  `~/.agents/skills` (500). Корінь — «the nearest ancestor containing `.git`».
- `.claude/skills` у списку НЕМАЄ. У нас немає ні `.dsh/skills`, ні `.agents/skills`;
  у proot немає `/root/.dsh/skills`, `/root/.agents`; `/root/dsh-app/.git` немає;
  `customSkillDirs` у профілях не знайдено (grep). Тому — 0 скілів.
- Формат: `<name>/SKILL.md` або `<name>.md`; frontmatter `name` (kebab-case) +
  `description`, необов'язкові `whenToUse`, `disable-model-invocation`, `user-invocable`.
  Наші 6 скілів мають `name`+`description` — формат сумісний.
- Скіли підхоплюються без перезапуску (watch), тіло перечитується при кожному виклику.

## Виправлення власної помилки
Я сказав «DSH писав: список скілів 11 %» (JOURNAL.md:269) як про скіли DSH. Це хибно:
start-load — його замір старту CLAUDE CODE (там же Artifact, CLAUDE_CODE_DISABLE_ARTIFACT).

## Як дати DSH наші скіли (варіанти, не вирішено)
1. `customSkillDirs` у профілі DSH → `.../AgentReachProject/.claude/skills` (одне джерело).
2. Симлінк `AgentReachProject/.agents/skills → .claude/skills` + запуск DSH у теці проєкту.
3. Окремі скіли для DSH у `~/.dsh/skills`.
[не перевірено]: як задати customSkillDirs у профілі tui (docs/config-catalog.md пакета);
чи всі наші скіли мають сенс для DSH (session-close — про Claude Code в Termux).
— [claude-code, 2026-10-06]

## Виправлення і пропозиція DSH (cc-nodeids-2, 2026-10-06)
- «0 скілів» — ХИБНО: «skills 0/0» — це ~/.agents/skills (total) проти ~/.dsh/skills
  (installed), startup-info.js:11-13,300-301; у каталозі DSH є 1 скіл (dsh-tui-pi-config,
  реєструє плагін). /skills керує симлінками — конфіг правити не треба.
- Мірило ефективності скіла (домовити ДО старту): ціна (токени завантаження), покриття (скільки
  разів завантажено на N задач), ефект (≥5 задач зі скілом / ≥5 без: правки користувача,
  виправлення після показу, непідтверджені твердження за класами claimcheck, кроки до done),
  критерій провалу (0 дельти при вимірюваній ціні, або обов'язкові кроки пропущено ≥k разів).
- Доказ користувачу: таблиця на скіл «name | виклики | задачі | ціна | дельта | джерело | verdict».
- Ризики: заміна без мірила = «зміст за ярликом» на метриках; DSH тіло скіла не версіонує
  (README:152) → показ старого/нового, «так» користувача, коміт як версія; рішення про заміну —
  з бектестом по журналах, не з пам'яті сесії.
— [claude-code, 2026-10-06]

