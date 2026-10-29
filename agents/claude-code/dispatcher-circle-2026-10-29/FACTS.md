# Факти для плану «кола диспетчера» (2026-10-29)
Мета: точні опори для плану з 3 частин (ворота v2 + дошка; autosave «хто що зробив»; переоцінка рішень). Усе виміряно цієї сесії (sed/grep). Файл ворiт: `.claude/hooks/edit-gate-hook.py` (620 рядків; далі «хук»).

## A. Ворота v2 — як рахується
- хук:386 — `V2_WORK = {"Bash", "Read", "Grep", "Glob", "Edit", "Write", "MultiEdit", "NotebookEdit"}` — що є «одиницею роботи» (прапорець A).
- хук:511 — `units = [i for i, e in enumerate(ev) if e[0] == "tool" and is_unit(e[2], e[3])]`; хук:522 — `n = len(units) + 1`; хук:523 — `if n < n_lim:` (return None).
- хук:383–384 — `V2_N = int(os.environ.get("EDIT_GATE_V2_N", "12"))`, `V2_K = int(os.environ.get("EDIT_GATE_V2_K", "2"))` (n_lim=12, k_lim=2).
- хук:525 — `return f"agents-a\t{anchor}\t{n // n_lim}", n, V2_A_REASON...` (повторний deny на кожні 12).
- Роздача (що скидає лічильник): хук:387–389 `V2_DELEG = {"Agent", "Task"}`; `V2_DELEG_G = V2_DELEG | {"mcp__delegate__delegate", "mcp__delegate__deepseek", "mcp__deepseek__deepseek", "mcp__deepseek__deepseek-reply", "SendMessage"}`. Вибір: хук:441 `deleg = V2_DELEG_G if flags.get("G") else V2_DELEG`; G за замовчуванням вимкнено (хук:382 `"0" if k == "G" else "1"`). Тобто скидають лише Agent/Task. Пошук якоря: `v2_window` хук:438–459 іде журналом від кінця до останнього tool_use з name у deleg: `hit = next((e for e in reversed(evs) if e[0] == "tool" and e[2] in deleg), None)`.
- tmux send-keys (лист DSH) роздачею НЕ є: хук:396 `RE_COORD = re.compile(r"tmux\s+(?:capture-pane|list-windows|send-keys)|...` — лише виключає такі Bash з одиниць (прапорець Z), лічильник не скидає.
- RE_WL_*: хук:390 `RE_WL_CLOSE = re.compile(r"закрит|закрива|session-close|baton|естафет|handoff|коміт|commit|git status|"`; хук:392 `RE_WL_CHECK = re.compile(r"(?:перевір|звір)\w*[^,;)]{0,30}(?:звіт|чис|під-?агент|делегат)", re.I)`; хук:393 `RE_WL_EDIT = re.compile(r"правк|рядк|рядок|запис", re.I)`.
- v2_whitelisted: хук:462–472 — `if RE_WL_CLOSE.search(reason): return "close"` / `RE_WL_CHECK … return "check"` / для Edit|Write|MultiEdit + RE_WL_EDIT і ≤ `V2_EDIT_LINES` (=10, хук:385) рядків — `"edit"`.
- Гілка C: хук:513–520 — `reps = [i … if e[0] == "report" and i > last_u]` … `m = sum(1 for i in units if i > reps[-1]) + 1` / `if m > k_lim: return f"agents-c\t…", m, V2_C_REASON…` / `return None  # точкова перевірка звіту — вільна`. Звіт під-агента розпізнає хук:398 `RE_REPORT = re.compile(r"<summary>(?:Agent \"|MCP task \S+ \((?:delegate|deepseek))|Subagent hand-back", re.I)`.
- Гілка A: хук:522–525 (див. вище). Обхід «без агента:» — хук:503–508: `wl = v2_whitelisted(desc.split("без агента:", 1)[1], name, inp)`; `if wl in ("close", "edit"): return None`.
- Звідки історія кроків: з ТРАНСКРИПТА сесії, `data.get("transcript_path")` — хук:534 (v2_check) → `v2_window(tp)` читає jsonl цілком (хук:443–444 `lines = f.read().splitlines()`), події будує `v2_line_events` (хук:406–436; лише `type=="assistant"` без `isSidechain`, tool_use; плюс human/report із `queued_command`/`user`). Пропуск, якщо `data.get("agent_id")` (під-агенти не рахуються) — хук:530 (v2_check, перший `if`).
- Чи хук читає файли стану проєкту: так, але не дошку/естафету. Читає: `SETTINGS = os.path.join(PROJECT, ".claude", "settings.local.json")` (хук:53, використ. хук:175), лог `.claude/logs/edit-gate.log` (хук:41), сусідні хуки/tools для пошуку читачів історії (хук:62–75, `os.walk`). Згадок BOARD/дошки в хуку: `grep -n "BOARD" хук` → 0 збігів (перевірено).
- Дошка: `agents/claude-code/doshka-2026-10-28/BOARD.md` існує, рядок 1: `# Дошка сесії «хто що робить» — проба 28.10 вечір (сесія 86fab127)` (формат смуг/виконавців не розбирав — це вже для плану).

## B. Відомі корені хибних зупинок (live-2026-10-28-eve.md:30–32 називає :514–519, :522–523, :392, :462–471, :520)
Звірено з поточним кодом — рядки ті самі (код не зсунувся):
- хук:514–519 — `m = sum(1 for i in units if i > reps[-1]) + 1` / `if m > k_lim:` / `return f"agents-c…` — deny ДО перегляду `wl` (Е2, Е3). Трохи точніше: `if reps:` на 515, `m` 516, `if m > k_lim:` 517, `return` 518, `return None` 519.
- хук:520 — `    if wl == "check" and not flags.get("C"):` — виняток «check» діє лише коли C вимкнено.
- хук:522–523 — `n = len(units) + 1` / `if n < n_lim:` (Е1: кроки старту сесії рахуються).
- хук:392 — `RE_WL_CHECK` (не знає «verify-before-show»).
- хук:462–471 — `v2_whitelisted` (початок :462 `def v2_whitelisted(reason, name, inp):`, кінець `return None` на :472).
- Звіт: agents/claude-code/gate-v2-2026-10-27/live-2026-10-28-eve.md:30 `1. \`edit-gate-hook.py:514-519\` (гілка C, \`m > k_lim\` до перевірки \`wl\`): Е2, Е3.`

## C. autosave.py
- Єдина копія: `find ~ -name 'autosave*.py' -not -path '*/node_modules/*'` → лише `/data/data/com.termux/files/home/sandbox-graphify/sessionend/autosave.py` (51 рядок). Нічого не змінював.
- Реєстрація: `grep -n "SessionEnd|autosave"` у `.claude/settings.local.json`, `.claude/settings.json`, `~/.claude/settings.json` → збігів НЕМА (перевірено; `grep -rln autosave` знайшов лише логи deepseek-search). Тобто хук SessionEnd НЕ зареєстрований; це проба (docstring рядок 2: `"""Проба (пісочниця, 2026-10-20): SessionEnd-страховка за ідеєю claude-code-memory-setup Part 5.`). Задуманий вхід: `Вхід хука: JSON зі stdin (transcript_path, reason, session_id)` (рядок 4).
- Що робить: autosave.py:12–23 читає транскрипт (`for line in open(path…)`), рахує `users` (повідомлення-рядки), перший запит `first`, `files` (Edit/Write `file_path`, :21–22), `passed` (`if b["name"] == "mcp__baton__baton_pass": passed = True`, :23–24). Рядок 25: `if users < 2 or passed:  # шум або сесію закрито як слід — сліду не треба` → вихід. Далі (:28–31) коміти й dirty з git (`git log --since=… --format=%h %s`, `git status --short`), пише `logs/<дата>-<id8>-auto.md` у `AUTOSAVE_DIR` (за замовч. `~/sandbox-graphify/vault/logs`, рядок 10).
- Транскрипт бачить: так. Про під-агентів/DSH: НІ — єдині перевірені імена інструментів: Edit, Write, baton_pass (рядки 21–24). Agent/send-keys не рахує.
- Примітка: рядок 15 читає `r["message"]["content"]` без `.get` — але обгорнуто `try/except` у :48–51 (хук не ламає сесію).

## D. Інструменти, що рахують з транскрипту
Команда `grep -ln "send-keys\|\"Agent\"\|tool_use" tools/*.py` → cost-report, deepseek-search, deepseek-thinking-proxy, hooks-smoke, mechanisms-backtest-2026-10-13, parts-passport, plain-codes, session-export, watch-deepseek. Перевірено рядки:
- tools/parts-passport.py:15 — `tool_use дедуплікується за id (у журналі записи задвоюються — Q3 evidence 03.10).`; :17 `MCP — ім'я tool_use`; :239 `if not isinstance(c, dict) or c.get("type") != "tool_use":` — рахує виклики (скіли/MCP) по журналах; Agent/send-keys окремо не виділяє [не перевірено глибше].
- tools/session-export.py:67 — `elif k == "tool_use":` (експорт, не лічильник).
- tools/watch-deepseek.py:33 — `if t == "tool_use":`.
- tools/cost-report.py:11 — про `usage` у записах tool_use (ціна, не кроки).
- tools/claimcheck/claimcheck.py:59 `def parse_turns(path)`, :52 `E6_KINDS = {"ps": re.compile(r"\b(ps|pgrep|pidof)\b"), …` — Bash-докази по ходу, не Agent/DSH.
- хук:300 `def iter_tool_uses(path)` (в edit-gate-hook.py) — генератор (ts, name, inp) усіх tool_use; хук:406 `v2_line_events` — події для v2.
- Готового інструмента, що рахує саме запуски Agent / листи DSH (send-keys) / власні кроки як трійку «хто що зробив» — не знайдено серед перелічених (за виводом grep). Найближче: v2_line_events + v2_decide (units vs deleg).

## E. Пошук записів за файлом/твердженням (для частини 3)
`grep -ln "тримається на\|decision\|рішенн" tools/*.py` → baton-diff, deepseek-search, deepseek-thinking-proxy, error-registry, focus-tree, hooks-smoke, parts-passport. Рядки, що стосуються теми (збіги ПОВЕРХНЕВІ, це не пошук рішень за файлом):
- tools/baton-diff.py:194 — `…відкинути — лише рішенням користувача; потім старі знімки в .trash/ (TRASH.md).`
- tools/error-registry.py:17 — коментар про «рішення користувача «Так, вносити»».
- tools/focus-tree.py:16 — `Порядок вузлів у картці НЕ змінює: черга — правило Q10 і рішення користувача.`
- tools/parts-passport.py:7 — `…діри потім підуть у check-links і в рішення користувача.`
- Фраза «тримається на» у tools/*.py окремо не підтверджена. Інструмента «знайди рішення, що спираються на файл X / твердження Y» немає за результатом grep. Суміжне: хук:62–75 `history_readers()` (шукає по `.py/.md/.sh/.mjs` у проєкті, хто читає історію) — шаблон обходу файлів.

## Неясне
- Чому autosave не зареєстрований (проба не просунута чи знята) — в settings нема; історію в TROUBLES (теги sessionend) не читав.
- Формат смуг/статусів у BOARD.md не розбирав.
- Чи є копії autosave у .trash/ чи поза ~ — `find ~` знайшов одну.

— [claude-code (під-агент за брифом координатора), 2026-10-29]
