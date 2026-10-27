# tree-focus: «2 за роботою + 1 сталий», урок до повідомлення вимкнено — правка в копії (27.10)
— [claude-code, під-агент, 2026-10-27]. Запит: оркестратор. Ярлик: Пам'ять проєкту › M3 Легкий стан › хук фокусу: варіант «2 за роботою + 1 сталий». Оригінал .claude/hooks/tree-focus-hook.py НЕ змінено.
Записав оркестратор із тексту звіту під-агента (середовище під-агента заборонило Write). Звірено командою: check-out.txt — 21 ✅ / 0 ❌; smoke — «ПОЛОМОК: 0»; `git status --short .claude/hooks/` порожній.

## Ціль
GOALS.md:11–13 (делегуючий агент; Agent Reach — шаблон екосистеми) → вузол M3 «Легкий стан „що зараз“» (trees/pam-yat-proyektu.md:169) → хук фокусу на старті показує уроки пам'яті, дотичні до роботи, і не втрачає сталого уроку. Основа — prep-копія (agents/claude-code/prep-2026-10-27/focus/REPORT.md).

## Що змінено (від prep +21 −6, 3 ділянки — diff-vs-prep.diff; від оригіналу +114 −16, 6 ділянок — diff-vs-original.diff, diff-stats.txt)
1. `WORK_RULES = 2`: у howto_section за роботою (rank_rules) — не більше 2. Далі 1 місце завжди за першим із HOWTO_RULES, якого ще нема серед обраних. Вільні місця (за роботою <2) — решта HOWTO_RULES, як у prep; якщо й їх бракує — наступні за роботою. Разом рівно 3, без дублів. «(за [>]: N)» рахує лише вибрані за роботою.
2. `MSG_LESSON_ENV = "TREE_FOCUS_MSG_LESSON"`: prompt_lesson викликається лише при значенні «1». Інакше пам'ять не читається, а вивід повідомлення збігається з оригіналом.
3. Решту prep не чіпав: парсер RE_APPLY, rank_rules, RULE_CAP=360, дедуп shown_rules.

## Таблиця
| вхід | оригінал | prep-копія | нова копія |
|---|---|---|---|
| старт, весь вивід / «Як застосовувати», симв. | 2653 / 1190 | 2609 / 1146 | 2547 / 1084 |
| 3 уроки старту | check-content-not-titles, fix-root-cause, read-dsh-channel-map | work-multistep, labels-follow-tree-path, reports-as-live-tree | work-multistep, labels-follow-tree-path, check-content-not-titles (сталий) |
| повідомлення «тест», симв. | 167 | 167 | 167, збігається з оригіналом (і зі змінною =1) |
| №5 без змінної | 167, уроку нема | 506, reports-as-live-tree | 167, збігається з оригіналом (і з =0) |
| №5 з TREE_FOCUS_MSG_LESSON=1 | — | — | 506, reports-as-live-tree (як у prep) |

Числа старту трохи відрізняються від prep REPORT: дерево змінилося.

## Перевірки
- check.py: 21 ✅ / 0 ❌ (check-out.txt), серед них 7 межових випадків вибору уроків; частина старту до «Як застосовувати» збігається з оригіналом.
- hooks-smoke, база: «39; поломок: 0» (smoke-base-full.txt).
- hooks-smoke з копією: HOOKS_SMOKE_SETTINGS (рядок 42) і HOOKS_SMOKE_ONLY=tree-focus; налаштування — /usr/tmp/focus-v2/settings-v2.json, обгортка wrap.py (DSH_LOG у копії рахується від теки). Результат: 2/2 ✅ без змінної і з =1 (smoke-v2-treefocus*.txt). «DSH насправді» відтворено в check.py (2/2).

## Головне для рішення
Перший незайнятий із HOWTO_RULES — check-content-not-titles, тож fix-root-cause-of-every-bug на старті не з'являється. Якщо потрібен саме він — поставити його першим у HOWTO_RULES (зміниться й запас, коли активних [>] нема).

## Ризики
- [не перевірено] Час виконання не міряв.
- RULE_CAP=360 обрізає й сталі уроки (успадковано з prep).
- [не перевірено] Дедуп уроку при =1 тут не повторював.
- [не перевірено] Як саме задавати TREE_FOCUS_MSG_LESSON для Claude Code — через оточення процесу чи через команду хука.
- У теці лишився __pycache__ (видалення — лише із записом у TRASH.md).

## Перенос (лише після «так» користувача) і відкат
cp agents/claude-code/focus-v2-2026-10-27/tree-focus-hook.py .claude/hooks/tree-focus-hook.py && python3 tools/hooks-smoke.py && python3 -B agents/claude-code/focus-v2-2026-10-27/check.py

Відкат: `git checkout -- .claude/hooks/tree-focus-hook.py` або `git revert <коміт>`. Частковий відкат: WORK_RULES=0 — лишаються сталі уроки й новий парсер.

## Файли теки
tree-focus-hook.py, harness.py (з prep, без змін), check.py, check-out.txt, smoke-base-full.txt, smoke-base-treefocus.txt, smoke-v2-treefocus.txt, smoke-v2-treefocus-env1.txt, diff-vs-original.diff, diff-vs-prep.diff, diff-stats.txt.
