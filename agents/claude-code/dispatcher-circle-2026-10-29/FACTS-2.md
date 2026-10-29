# FACTS-2: факти для шести правок «механізму засвоєння помилок»

Формат: файл:рядок — `цитата`. Усе виведено командами цієї сесії; змін у файлах, крім цього звіту, нема.
Контекст плану кола (PLAN.md, «Порядок» 1–6: ворота 1а–1б → стан DSH → ворота 1в → страховка → розбір → переоцінка; «Перевірка»: hooks-smoke, імітація входу echo JSON | python3 хук, проба 2–3 сесії).

## 1. Скіл звірки (verify-before-show)
- .claude/skills/verify-before-show/SKILL.md:52 — `На кожне твердження — окремий виклик, усі паралельно:`
- SKILL.md:54 — `- `files`: не більше 2 джерел (правило RULES.md про ліміт deepseek);` — це межа на файли, НЕ на кількість одночасних викликів.
- grep по «одночасн|максимум|не більше|межа» у SKILL.md дав лише рядок 54. Межі на кількість паралельних викликів у скілі немає.
- Запис про 429 є, правки в місці народження — ні: TROUBLES.md:4735 (цитата з хука-підказки) `Не зроблено: рядок «усі паралельно» ... не змінено — правка скіла лише з рішення користувача (Правило 4).`; перелік 29.10 (TROUBLES.md, розділ «Що сесія a62774d0 (29.10) не засвоїла») `Записано 15.10 (:4725) і 28.10 (:6726), а SKILL.md крок 2 досі «усі паралельно»`.

## 2. Лист DSH
- Скрипта-відправника в tools/ чи .claude/ немає. `grep -rln "send-keys" tools .claude` (без логів і pycache): лише .claude/skills/session-close/SKILL.md і .claude/hooks/edit-gate-hook.py.
- session-close/SKILL.md:22 — `3. Лист з межами за рецептом TROUBLES «Листи у вікно DSH» (текст з файлу → `tmux send-keys -t work:3 -l` →` / :23 `окремо Enter; перед тим — не зайнятий і поле вводу порожнє, копія в полі — Ctrl+K)`
- edit-gate-hook.py:379 і :396 — лише розпізнає tmux-команди як «нагляд за іншим агентом»: `RE_COORD = re.compile(r"tmux\s+(?:capture-pane|list-windows|send-keys)|...` (відправки не робить).
- Рецепт (TROUBLES.md:3958 «Листи у вікно DSH — доповнення до рецепту (2026-10-03, увечері)»), кроки:
  - :3961 `T=$(tr '\n' ' ' < лист.txt); tmux send-keys -t work:3 -l "$T"`, потім окремо `Enter`; не вписувати текст у лапки (`$0.42`).
  - :3964 «Зайнятий»: шукати `● Question` / `Queue as follow-up` / `working…` / `thinking ·` на всьому екрані.
  - :3966 перед відправкою поле вводу порожнє; копія листа в полі — Ctrl+K.
  - :3969 доставка — `user/message` з id у журналі DSH і довжина = файл.
- TROUBLES.md:6751 `## Лист DSH: Enter пішов, хоча перевірка поля вводу дала 0 (2026-10-29)`; :6755 `Що: `tmux capture-pane … | grep -c "cc-2910-1"; tmux send-keys -t work:3 Enter` — grep дав 0 ..., але Enter пішов: команди не зв'язані умовою.`; :6756 `Рецепт: Enter лише за умовою — `tmux capture-pane -p -t work:3 | grep -q -F "<перші ~20 символів листа>" && tmux send-keys -t work:3 Enter || echo "НЕ В ПОЛІ — не відправляю"`; після — звірка в журналі DSH (`zstd -dc …session.v4.jsonl.zstd`...)`.
- Доповнення 29.10 (перелік a62774d0, у TROUBLES.md після :6760): zstd з Termux дає 0, бо найновіший session.v4.jsonl.zstd — ярлик (`zstd ярлики пропускає (:5533)`), треба `readlink -f`; перевірку «лист у полі» повторювати до 3 разів з паузою 1 с; у листі писати «оброблено K з N; з них тримається X».

## 3. Коди вузлів у підказках
- Рядок «В роботі»: .claude/hooks/tree-focus-hook.py:466 — `out.append("В роботі: " + " | ".join(work[:MAX_WORK]) + more(work, MAX_WORK))`.
- Формування елемента: :443–446 `# кожне повідомлення — лише ID (бюджет M4: ≤3–4 тис. ток./сесію);` / `# повні назви — на SessionStart` / `line = f"{title} › " + " › ".join(label(n) if start else n["id"] for n in path)`. Тобто на UserPromptSubmit — тільки id (G2, M3), назви (label) — лише на SessionStart. Назв поруч із кодами у повідомленнях користувача НЕМАЄ (:446 `n["id"]`).
- На SessionStart (:416 `start = event == "SessionStart"`) label(n) даються і назва, і «(далі: …)» (:448–451).
- «Зараз (голова черги)»: :335 `"Зараз (голова черги): " + "; ".join(heads)`; голова будується :330 `heads.append(f"{title}: " + (short(f"{h['id']} {h['name']}", 60) ...` — тут код і назва (обрізана до 60).
- Порожній випадок: :468 `Жоден твій вузол не в роботі ([>] … @{me} у trees/*.md) — ...`.
- plain-ask: .claude/hooks/plain-ask-hook.py:36 — `codes = pc.strict(pc.ask_text(data.get("tool_input")))  # 2026-10-20: і коди в дужках («знов шифри»)`; :37–43 при `codes` — deny з причиною `plain-ask: у питанні коди задач: ...`. Лише питання AskUserQuestion (:33 `tool_name != "AskUserQuestion"`).
- Регекси: tools/plain-codes.py:27 `TOK = re.compile(r"(?<![\w./#:-])(" + CODE + r")(?![\w])")`; :30 `HASH = re.compile(r"(?<![\w/.-])((?=[0-9a-f]*\d)(?=[0-9a-f]*[a-f])[0-9a-f]{7,12})...`; :48 `after = re.compile(...)` / :50 `before = re.compile(WORD + r"[^\n()]{0,80}\([^()\n]*...` (код «з назвою» поруч до/після; strict — :57 `def strict(text):` вважає і код у дужках після назви порушенням); :65 `def ask_text(tool_input)`.
- Те саме для відповідей (Stop): answer-gate-shadow-hook.py:326 `misses.append("codes:" + ",".join(codes))` через `plain_codes().undecoded(text)`.

## 4. Ворота питань (.claude/hooks/ask-gate-hook.py)
Перевірки в `misses_for` (:101–131), тексти — `REASONS` (:134):
- queue — :105–106 `if not ag.RE_QUEUE.search(text): out.append("queue")`; причина :135.
- verify — :115–119 (`ag.RE_CHANGE`, `RE_CHANGE_LOCAL` «поправк», `ag.RE_PLAN_Q`, `mech` = RE_MECH+RE_MECH_VERB :39–41) → `out.append("verify")`; обходи: `RE_SKIP_VERIFY` :29 `Звірено перед показом|Звірка не потрібна:` (для mech не приймається, :117 `and not mech`).
- records — :120–131: `brief = RE_BRIEF.search(q0c) or (RE_PLAN_WORD...)`, шукає Bash з RE_RECORDS_CMD (:76 `kb-map\.py|trees-index\.py|grep ... (TROUBLES|BACKLOG|ECOSYSTEM|CONTEXT)\.md`) або Read цих файлів (:77); обхід `RE_SKIP_RECORDS` :33 `Записи не потрібні:`.
- Журнал: :7–8 docstring `Журнал: .claude/logs/ask-gate.jsonl`; deny — :162–166.
- Перевірки ПРИЧИНИ питання («чому питаю»: гроші/правило/втрати/механізм/коміт) НЕМАЄ: у файлі лише queue, verify, records. Слова «гроші/платн/втрат» не використовуються як перевірка (grep по «причин|чому питаю|гроші|reason» дав лише змінну `reason` у :162). «Коміт» тут — лише виняток у verify (:32 `RE_COMMIT_Q`, :49 `RE_COMMIT_COMPOUND`), а не категорія причини.

## 5. Числа без опори
- tools/claimcheck/claimcheck.py:1–12 — `Перевірка заяв агента за журналом сесії — лише звіт, не хук.` Позначки: `E1 — число з іменником, якого нема як окремого токена у виводі інструментів цього ходу`, `E3 — "працює/перевірено" ... без жодного запуску Bash`, `E5 — "неможливо/не існує" ... без пошуку`, `E6 — заява про СТАН ...`. Виклик: `python3 ~/AgentReachProject/tools/claimcheck/claimcheck.py [file.jsonl]`. Також backtest.py, number-backtest.py.
- session-close/SKILL.md:80 `## Крок 2.6 — Перевірити власні заяви за журналом сесії (read-only)`; :84 команда; :91 `E1 шумить (тест на історії, TROUBLES.md 2026-09-23)`; :93 `"claimcheck: позначено N, справжніх помилок M"`.
- Рішення «Stop-хук НЕ будуємо» (TROUBLES.md:1891 за підказкою): `Взято: tools/claimcheck/ як ЗВІТ у session-close (крок 2.6)`.
- Stop-хук для чисел ЄСТЬ, але тіньовий: .claude/hooks/number-claim-shadow-hook.py:2 `Stop-хук, ТІНЬОВИЙ режим, версія 2 (2026-10-07): «число-твердження без опори».`; :8–9 `НІЧОГО не блокує й нічого не пише в stdout: лише рядок у .claude/logs/number-claim-shadow.jsonl`.
- answer-gate-shadow-hook.py (Stop; «голос» = decision block, :10 docstring) — сигнали у `check()` (:313–362) і голос (:502–506 `voice = "+".join(...)`):
  - queue :320 — ГОЛОС (з 13.10);
  - codes :326 — ГОЛОС (з 16.10, «Словами: …»);
  - ask :335 — ГОЛОС (20.10);
  - ask-req :339 — ТІНЬ;
  - verify :343 — тінь у check; у голос іде через nudges (:515 `NUDGE_REASON.format(which="verify-before-show")`);
  - unverified :346 — тінь (не входить у voice-список :502–507);
  - single :350 — ГОЛОС (20.10: ефект числом без вибірки; саме «числа» тут про ефект %, не про будь-яке число);
  - nudge:delegate :354, nudge:brief :356, nudge:verify :358 — ГОЛОС на проігноровані підказки (16.10);
  - agents:<n> :362 — ГОЛОС (25.10), не для під-агентів і не в DeepSeek-сесіях (:498–500).
- Висновок: сигналу «будь-яке число у відповіді без лічильника» з голосом немає; E1 живе лише в звіті кроку 2.6 і в тіні number-claim.

## 6. Крок черги (0)
- `grep -rn "черга (0)\|давні \[>\]"` по .claude/hooks і tools — 0 збігів. Хуку/скрипта, що друкує нагадування «давні [>] — робити чи зняти» на старті, немає. Поза записами (agents/, TROUBLES, BACKLOG, trees/) рядок «черга (0)» є лише в HANDOFF.md.
- Старт друкує лише tree-focus (SessionStart): :335 `Зараз (голова черги)` і `Черга «{title}» (...)` :456–458 — це черга [ ] глибини 0 по картках, без перевірки давніх [>].
- Крок (0) тримається лише на пам'яті session-start-queue-step-zero (MEMORY.md) і на практиці ручного запису «черга (0) <дата>» у trees/*.md. Перевірки, що такий рядок за сьогодні записано, немає ні в хуках, ні в tools (пошук по «черга (0)» у .claude/hooks, tools — 0). У перелік a62774d0: `Пропущено на старті: крок черги (0) (grep «черга (0) 29.10» у trees/*.md — 0 у 6 файлах)`.

## 7. Реєстрація хуків (.claude/settings.local.json)
Події/matcher за розбором JSON (рядок command у файлі):
- tree-focus-hook.py — SessionStart (рядок 39, matcher немає) і UserPromptSubmit (рядок 282, matcher немає).
- number-claim-shadow-hook.py — Stop (рядок 60, без matcher).
- answer-gate-shadow-hook.py — Stop (рядок 65, без matcher).
- edit-gate-hook.py — PreToolUse, matcher `Edit|Write|MultiEdit|Bash` (рядок 165).
- plain-ask-hook.py — PreToolUse, matcher `AskUserQuestion` (рядок 175).
- ask-gate-hook.py — PreToolUse, matcher `AskUserQuestion` (рядок 180).
(Блоки подій: SessionStart :25, Stop :45, PreToolUse :71, UserPromptSubmit :277.)

## Неясне
- Чи є в .claude/hooks окремий хук поза переліком, що теж друкує нагадування старту (перевірено лише grep по «В роботі», «Зараз (голова», «черга (0)», «давні [>]»).
- Доповнення до п.6: HANDOFF.md:426, :446, :457 — ручні записи «черга (0)» у старті сесій (`черга (0) — давніх [>] нема`); це не автоматика.
- Точні рядки TROUBLES для доповнень 29.10 (перелік a62774d0) — знайдено заголовок, але номер рядка кожного пункту не встановлено (виведено частково).
- Чи tools/plain-codes.py :48/:50 регекси — повна логіка «код з назвою»; прочитано лише рядки з re.compile, не всю функцію.
- Закрито: label() — tree-focus-hook.py:108 `def label(n):` / :109 `s = f"{n['id']} {n['name']}"` / :110 `if len(s) <= NAME_CAP:` (обрізає за NAME_CAP; значення не друкував).

— [claude-code (під-агент за брифом координатора), 2026-10-29]
