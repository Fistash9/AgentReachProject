# Зв'язок двох агентів › перевірка «Full access» перед листом DSH › план

Запит: рішення користувача 28.10 «Вручну + перевірка» (BACKLOG.md:7; «Далі» 1 естафети #99).
Мета: лист у вікно DSH не йде, поки DSH без повного доступу (інакше він не може писати, комітити, запускати
shell — роздача задач ламається). Служить: головна ціль (агент вищого порядку роздає задачі іншим агентам).
Умова зупинки: хук у settings, hooks-smoke зелений, імітація входу обома шляхами (пропуск / відмова) дає
очікуване; живий лист DSH — лише з «так» користувача окремо.
— [claude-code, 2026-10-28; сесія 86fab127; факти — 3 під-агенти, вибірково звірено]

## Факти (з доказами)

1. Напис режиму в TUI DSH (пакет dsh-tui-pi — це TUI): `/root/.dsh/profiles/tui/node_modules/@aiwayds/dsh-tui-pi/lib/permission.js:23` —
   `return value === 'danger-full-access' ? 'Full access' : displayPresetName(name);`
2. Де він на екрані: `…/dsh-tui-pi/lib/editor.js:142–144` — рядок з 📁 (на живому екрані 28.10 — верхня межа поля
   вводу, над статус-рядком `dsh ▸ …`):
   `📁 ${formatCwd(this.sessionCwd)}` + (permission непорожній ? ` (${permission})` : '').
   Отже повний доступ = `📁 ~/dsh-app (Full access)`; обмежений = `(Workspace Write)` (TROUBLES.md:6058);
   без дужок = режим не визначено (зараз на екрані саме так — `─ 📁 ~/dsh-app ───`).
3. Хто шле листи: рецепт `tmux send-keys -t work:3 -l "$T"`, потім окремо `Enter`
   (.claude/skills/session-close/SKILL.md:22; TROUBLES.md:3961 «Листи у вікно DSH»). В .claude/hooks і tools/
   send-keys ніхто не шле — лише ворота «агенти» розпізнають його як нагляд (edit-gate-hook.py:396 RE_COORD,
   без розбору цілі -t).
4. Назва вікна — `dsh` (~/.tmux.conf:38 `new-window -n dsh`; `tmux display -p -t work:3 '#{window_name}'` → dsh).
   Номер 3 не гарантований.
5. Хуки реєструються лише в .claude/settings.local.json (поза git); tools/hooks-smoke.py бере їх звідти;
   шаблон випадку — hooks-smoke.py:523–537 (importlib + eg.check(...) з модуля хука + rows.append);
   «лише в settings.local.json» — за `ls .claude/settings*.json` (є тільки settings.local.json).

Звірено перед показом: 5 тверджень — 1 так (4), 1 виправлено (5: eg.check), 3 «не можу» → опори уточнено (1, 2, 3);
DeepSeek — 429 (денний ліміт BazaarLink 60), далі Haiku з порожньої теки, $0.02024 за 5 запусків; цитати grep — 5/5.

## Що зробити

1. Новий окремий хук `.claude/hooks/dsh-access-guard-hook.py` (PreToolUse, Bash) — окремим файлом, щоб відкат
   був одним рядком у settings:
   - у команді нема `tmux send-keys` → пропуск;
   - ціль `-t X`: назва вікна через `tmux display -p -t X '#{window_name}'`; не `dsh` → пропуск;
   - усі аргументи — назви клавіш (Enter, C-*, M-*, Escape, BSpace, Tab, Up/Down/Left/Right) → пропуск
     (другий крок рецепта, Enter, не блокуємо);
   - інакше (текст): `tmux capture-pane -p -t X`, рядок з `📁`; містить `(Full access)` → пропуск;
     інакше → deny: «У вікні DSH нема «(Full access)» (на екрані: <рядок 📁 або «рядка теки не видно»>).
     Попроси користувача ввести у вікні DSH `/permission danger-full-access`, потім повтори лист».
   - функція check(command, screen_fn) — екран підставляється в тестах, без справжнього tmux.
2. Реєстрація в .claude/settings.local.json (PreToolUse, matcher Bash) — перед правкою .bak-копія.
3. hooks-smoke.py — випадки: текст у work:3 + «(Full access)» → пропуск; + «(Workspace Write)» → відмова;
   + без дужок → відмова; `send-keys -t work:3 Enter` → пропуск; send-keys у work:0 → пропуск;
   команда без send-keys → пропуск.
4. Імітація входу обома шляхами: `echo '{"tool_name":"Bash","tool_input":{"command":"…"}}' | python3 хук` —
   пропуск і відмова (з підставленим екраном через змінну середовища лише для тесту).
5. Записи: FACTS.md (факти 1–2), TROUBLES (новий механізм, відкат), BACKLOG.md:7 — статус.

## Рішення, які треба погодити

- Р1. Помилка всередині хука (tmux не відповів, виняток): пропускати з попередженням (не ламати роботу через
  баг хука) — пропоную; або блокувати.
- Р2. Ціль у змінній (`-t "$W"`), яку не розібрати: перевіряти вікно `dsh`, якщо воно є (обережно) — пропоную;
  або пропускати з попередженням.

## Відкат

Прибрати рядок хука з .claude/settings.local.json (є .bak); файл хука — у .trash/ з записом у TRASH.md;
випадки hooks-smoke — git revert.

## Не робимо

Не тиснемо клавіш у вікні DSH (TROUBLES:3766); режим не вмикаємо за користувача; RULES.md не змінюємо.
