# scout-vid-kintsya — звіт розвідника (обхід системи, 25.10, Explore/sonnet)

ЗВІТ розвідника «ВІД КІНЦЯ» (логи й виходи). Нічого не змінено. Розміри — на 2026-10-25 ~03:50. Позначки: «пише/читає» — лише справжній код (open/json.load/glob/subprocess/команда в SKILL); «лише паспорт» = читає тільки tools/parts-passport.py:286-300 (рахує рядки логу для паспорта, змісту не використовує).

1) КІНЦІ (.claude/logs)
- session-cost.jsonl (1,69 МБ, 10565 р., з 26.09) ← пише hooks/statusline-cost.py:66 → читає hooks/cost-nudge-hook.py:30 (хвіст 64 КБ), tools/cost-report.py:111, skills/session-close/SKILL.md:189 (python3 -c open(...))
- cost-nudge-state.json (526 Б) ← cost-nudge-hook.py:66 → читає він сам :57 (обрізає до 30 сесій)
- answer-gate-shadow.jsonl (41 КБ, 397 р.) ← answer-gate-shadow-hook.py:418 → не читає ніхто
- ask-gate.jsonl (39 КБ, 409 р.) ← ask-gate-hook.py:130 → не читає ніхто
- plain-ask.jsonl (42,5 КБ, 459 р.) ← plain-ask-hook.py:38 → не читає ніхто
- node-label-shadow.jsonl (37 КБ, 353 р.) ← node-label-shadow-hook.py:113 → не читає ніхто (його --backtest :84 читає журнал сесії, не цей лог)
- number-claim-shadow.jsonl (165 КБ, 541 р.) ← number-claim-shadow-hook.py:336 → не читає ніхто (claimcheck/number-backtest.py:79 читає журнал сесії)
- commit-consent.log (29 КБ, 127 р.) ← commit-consent-hook.py:186 → не читає ніхто (RULES-WHY.md:369 — лише текст)
- delegate-calls.jsonl (176 КБ, 296 р., з 23.09) ← delegate-outcome-logger-hook.py:88 → лише паспорт
- improver.log (6,7 КБ, 32 р.) ← delegate-prompt-improver-hook.py:106 → лише паспорт
- personal-guard.jsonl (6 КБ, 46 р.) ← personal-guard-hook.py:58 → лише паспорт
- proc-guard.log (234 Б, 4 р.) ← proc-guard-hook.py:72 → не читає ніхто
- edit-gate.log (13 КБ, 139 р.) ← edit-gate-hook.py:337,343 → читає сам :306-309 (дедуп «раз на сесію»)
- verify-nudge.log (9,4 КБ, 95 р.) ← verify-nudge-hook.py:163,177 → читає сам :150
- free-answer.log (7,5 КБ, 12 р.) ← free-answer-hook.py:45,51 → читає сам :43
- install-check.log (880 Б) ← install-check-hook.py:158,176 → читає сам :154,:172 і hooks/tests/check-install-check.py:13
- deepseek-thinking-proxy.jsonl (11 КБ, 76 р., остання 21.10) ← tools/deepseek-thinking-proxy.py:100 (шлях дає claude-deepseek.sh:23) → не читає ніхто
- deepseek-search/*.json (43 файли, 18,98 МБ, 01.10–24.10) ← tools/deepseek-search.py:258-259 → читає лише він сам :208 при `-c ID`
- L0-achieved-*.json (12 файлів, 1,45 МБ) ← tools/achieved-map.py:291,312 → не читає ніхто
- project-audit-*.json (11 файлів, 92 КБ) ← tools/project-audit.py:430-434 → не читає ніхто (project-audit.py:216 навмисно пропускає logs/)
- review-2026-09-28.txt (618 КБ) і -part2.txt (311 КБ) ← у коді запису нема (ручне перенаправлення) → не читає ніхто
.baton
- baton.json (131 КБ, 590 р.) ← MCP baton server.mjs:35 → читають: server (loadState), hooks/baton-guard-hook.py:96, tools/handoff-view.py:128, baton-split.py:25, baton-diff.py:55, project-audit.py:77,87, achieved-map.py:200, focus-tree.py:102
- ledger.jsonl (227 КБ, 250 р.) ← server.mjs:36 → читають baton-guard-hook.py:58 (кожен UserPromptSubmit), baton-reminder-hook.py:24 (кожен Bash), server.mjs:40 (baton_history)
- HANDOFF-view.md (14,8 КБ) ← tools/handoff-view.py:139 (запускає baton-guard-hook.py:168 після pick_up) → у коді читача нема; агента змушує прочитати текст підказки baton-guard-hook.py:177
- history/pass-75.json ← cp у session-close/SKILL.md:256 → читають baton-diff.py:59, project-audit.py:71, achieved-map.py:198, focus-tree.py:105
- history/HANDOFF-pre-pass30/32/33.md (203 КБ) і history/archive-2026-09-28/ (4 файли, 285 КБ) ← ручні mv/cp → не читає ніхто (усі glob — лише pass-*.json верхнього рівня)
- HANDOFF.md у корені (129 КБ) ← server.mjs:167 → не читає ніхто в коді
.unlazy
- passport/passport.json (112 КБ) і passport.md (53 КБ) ← tools/parts-passport.py:541,568 → не читає ніхто (є лише згадки в baton.json і тексті)
- q6/layer2/*.verified.md ← q6/verify.py:15 → читає q6/check.py (G3)
- q6/layer2/*.md ← вручну (вивід делегата) → читають q6/verify.py (вхід), q6/check.py (G2)
- q6/GATES.md, bash-request-brief/GATES.md, classify-task-fix/GATES.md → їх мав би читати skills/unlazy/scripts/lib/gates.mjs:559 (listScopes). Живий Stop-хук (settings.local.json:50, stop-hook.mjs:74) бачить 4 теки, не може вибрати і мовчки пропускає. GATES.md читає лише ручний gate-check.mjs --scope.
- q6/decisions.md, self-learning-plan.md → check.py читає лише decisions.md (G5,G6); план — не читає ніхто.
agents/claude-code: 21 файл у корені, 530 КБ. Усі пишуться вручну або як stdout deepseek-search, у коді читача нема (згадки лише в BACKLOG/TROUBLES/trees). Єдиний справжній читач: q12-classes-2026-10-16/registry-v1.md ← tools/error-registry.py:173,181 (remedies()) і skills/session-close/SKILL.md:105.

2) ГЛУХІ КУТИ
Пишуть — ніхто не читає:
- ask-gate, plain-ask, answer-gate-shadow, node-label-shadow, number-claim-shadow, commit-consent, proc-guard, deepseek-thinking-proxy (розміри вище). Три «shadow» створені, щоб потім порахувати (BACKLOG M11.4), але рахувати нікому.
- delegate-calls, improver, personal-guard — лише паспорт.
- L0-achieved (1,45 МБ), project-audit (92 КБ), review-2026-09-28*.txt (912 КБ).
- passport.json/.md (165 КБ).
- HANDOFF.md і HANDOFF-view.md (читач — текст підказки).
- .baton/history: HANDOFF-pre-pass*.md і archive-2026-09-28/ (488 КБ).
- .claude/settings.local.json.bak* — 37 файлів, 284 КБ, не читає ніхто (відкат вручну).
- tree-focus-hook.py:380 пише logs/dsh-line.jsonl, файла нема (гілка не спрацювала). Читача теж нема.
Читають — ніхто не пише:
- .claude/active-tree (26 Б, 28.09): читає tree-focus-hook.py:416. Писати в коді нікому, лише рука.
- .unlazy/*/GATES.md: читач є (gates.mjs), але через неоднозначність 4 тек ніколи не спрацьовує сам.

3) ЩО РОСТЕ БЕЗ МЕЖІ (ротації нема, якщо не вказано)
- deepseek-search/: 18,98 МБ, +1 файл на розмову (до 1,47 МБ), 43 за 24 дні.
- session-cost.jsonl: 1,69 МБ, ≈360 р. на добу (~58 КБ); читають лише хвіст, тож швидкодії не шкодить.
- ledger.jsonl: 227 КБ/250 подій. Два хуки читають його ЦІЛИМ: baton-reminder на кожен Bash, baton-guard на кожен промпт.
- baton.json: done 357 пунктів (54 КБ), watchOut 190 (25 КБ). Обмеження нема; pass-N копіюється вручну.
- delegate-calls.jsonl: 176 КБ, ~550 Б на запис.
- ask-gate, plain-ask: ~40 КБ кожен, ≈90 р. на добу при активній роботі.
- commit-consent.log: 29 КБ, у рядок пишеться повний текст відповіді.
- З ротацією: number-claim-shadow і node-label-shadow (512 КБ → .1, number-claim-shadow-hook.py:332, node-label-shadow-hook.py:111), answer-gate-shadow (2 МБ → .1, :412). Файлів .1 ще немає.
- Забруднення тестами: у «бойових» shadow-логах рядки з сесій check/smoke/test: number-claim 156 з 541, answer-gate 101 з 397, plain-ask 13.

4) ДУБЛІ
- ask-gate.jsonl і plain-ask.jsonl: один хук-момент (PreToolUse AskUserQuestion, settings.local.json:171-180), по запису на кожне питання.
- answer-gate-shadow.jsonl і ask-gate.jsonl: однакова схема {t, session, misses}, ті самі регулярні вирази (ask-gate-hook.py:17,57 вантажить модуль answer-gate).
- commit-consent.log і free-answer.log: обидва зберігають текст відповіді AskUserQuestion.
- verify-nudge.log і edit-gate.log: однакова схема «sid\tключ\tчас», обидва водночас лог і дедуп-кеш.
- passport.json і passport.md: один зміст у двох форматах (parts-passport.py:541,568).
- baton.json, HANDOFF.md, HANDOFF-view.md, history/pass-75.json: чотири подання одного стану (131, 129, 15, 132 КБ).
- agents/claude-code/search-*.txt, review-session-0f35e97e.txt і deepseek-search/*.json: .txt є копією відповіді з .json. Заголовок review-session-0f35e97e є в 20261020-193608.json, search-learning-loop — у 20261019-140957.json, search-cross-review — у 20261012-150202.json.
- L0-achieved-20261003-1702/-1703 (по 87712 Б) і -1705/-1709 (по 88841 Б): однакові розміри, md5 різні. project-audit-20261020-1242/-1243 (по 6761 Б): те саме. Різницю не досліджено.
- review-2026-09-28.txt і -part2.txt: частини одного огляду, читача нема.

5) НЕ ПЕРЕВІРЕНО
- Хто створив review-2026-09-28*.txt і agents/claude-code/*.md: код не знайдено, припускаю ручне перенаправлення виводу.
- Чи читає хтось ці логи не кодом, а агентом уручну (grep/Read за порадою з BACKLOG/RULES): це поза межами «справжньої ланки».
- Вміст файлів-пар (L0/project-audit з однаковим розміром) не порівнював.
- ~/.unlazy/approved (15 файлів, 67 КБ, поза проєктом) і ~/.claude/projects/<проєкт>/ (329 МБ журналів сесій, їх читають parts-passport.py:219, error-registry.py:14, cost-report) — не розбирав як «кінці».
- tools/verifier-backtest/results-*.jsonl, run-*.log, agents/dsh/*, session-exports/2026-09-24 (1,1 МБ), .trash/*, TROUBLES.md (640 КБ), BACKLOG.md (221 КБ) — поза ділянкою.
- Чи реально живі всі хуки за останній тиждень: наявність записів у settings.local.json перевірив, частоту спрацювань — лише за датами в логах.
