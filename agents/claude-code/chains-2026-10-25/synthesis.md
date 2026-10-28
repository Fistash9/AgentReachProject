# Збирання головоломки: Q4.3 › перелік проблем системи (25.10, під-агент claude-code)
Мета: дати користувачу один перелік для рішень раундами (trees/yakist-roboty-agentiv.md:143, done when п.3–4).
Звіти: I/P/S/K = agents/claude-code/chains-2026-10-25/scout-{instrumenty-git,povidomlennya-stop,sesiya,vid-kintsya}.md,
D = agents/dsh/chains-2026-10-25.md, B = agent-nudge-backtest (через Q4.3:170-171), CS№ = рядок check-sample.md.
Звірка: «так CS№» / «ні CS№» / «так (я: команда)» = перевірив сам 25.10 / «не звірялось».

## А. Глухі кути (пишуть/нагадують — ніхто не читає й не діє) — 5
A1. 10 логів без читача: 3 тіні, ask-gate, plain-ask, commit-consent, personal-guard, delegate-calls, improver, proc-guard — I:5, P:25, K:43 — так CS1 — тіні створено «щоб порахувати» (BACKLOG M11.4), але рахувати нікому, рішення про них не ухвалюються.
A2. dsh-line.jsonl: пише tree-focus:380, файла нема — I:8, P, S, K — так CS5 — «проба 3 сесій» (BACKLOG:269) не має даних.
A3. .claude/active-tree: читач tree-focus:416, писача нема, файл від 28.09 — P, S, K — так CS10 — фокус може взяти застарілий вказівник.
A4. Артефакти й журнали без читача/межі: hook-test.log 5,5 МБ, L0-achieved 1,45 МБ, review-*.txt 912 КБ, passport.json+md, history/archive+HANDOFF-pre-pass*, deepseek-search/ 19 МБ — I:10, K:24-35 — так CS12 (лише hook-test.log), решта не звірялось — пам'ять телефона росте без користі.
A5. Мертві запускачі й бекапи: mcp_run.sh (+run-telegram-bot.sh, run-dsh-isolated.sh, test-hook.sh), settings.local.json.bak*, DSH AGENTS.md.bak×3, profiles/web.backup, exp/, cost-report.py без автозапуску, канали 8799/8788 описані, але не існують — I:9, K:50, D:16-24 — так CS11 (mcp_run); ні CS14 (кількість .bak: 33, не 37; факт глухого кута лишається); решта не звірялось — документи обіцяють те, чого нема.

## Б. Дублі (дві речі роблять те саме) — 6
Б1. is_real_user / iter_turns / читання хвоста журналу скопійовано в answer-gate і number-claim (+node-label) — P:3 — так (я: grep -n → ag:204,223; nc:228,238) — виправлення в одній копії не дійде до іншої.
Б2. Парсер вузла дерева ×3 (tree-focus, trees-index, mods parse.ts; tree-focus не бачить trees/g2) і розбір екрана DSH «◐» ×2 — P, S — так (я: tree-focus:115 def parse; trees-index:30 def nodes + власний ARROW:23; parse.ts:6 parseTree; «◐» лише parse.ts:20,22 і tree-focus:376,378; tree-focus:426 glob(trees/*.md) без рекурсії) [dsh, звірка cc-2810-1, 2026-10-28; вніс claude-code 2026-10-28T13:13+0200] — ті самі дані читаються по-різному.
Б3. Стан baton у 4 поданнях (baton.json, HANDOFF.md, HANDOFF-view.md, pass-N ≈131–132 КБ) + «останній pass» з ledger парсять двічі, цілим файлом — K, D, P, S — так частково (я: grep LEDGER → baton-guard:43, baton-reminder:18), розміри не звірялось — неясно, яке подання головне.
Б4. «Поточна сесія» визначається 4 способами (session-export може взяти сесію haiku) + порівняння знімків baton ×3 з різним порогом (0.5 / 0.80) — S — не звірялось — інструменти можуть дати різні відповіді на одне питання.
Б5. Правила для DSH двічі: RULES.md і /root/.dsh/AGENTS.md, діє лише другий — D:26 — не звірялось — правка RULES.md до DSH не доходить.
Б6. Пари логів одного моменту: ask-gate+plain-ask (так: одна секунда й та сама сесія, ask-gate.jsonl:403 ↔ plain-ask.jsonl:453), verify-nudge+edit-gate (так: verify-nudge.log:100 ↔ edit-gate.log:154, 21:20:37), commit-consent+free-answer (НІ: ті самі сесії, але розбіг у хвилини; commit-consent.log:137 заніс вільний текст як deny → розсинхрон воріт, не дубль) — K:4) — так частково (я: grep по .claude/logs/, докази вище) [dsh, звірка cc-2810-1, 2026-10-28; вніс claude-code 2026-10-28T13:13+0200] — дубль є в 2 парах із 3.

## В. Розриви (ланцюжок обривається) — 13
В1. Ворота unlazy на Stop мертві (4 теки, жодна не прив'язана) і тест hooks-smoke «unlazy Stop» не може впасти — P, K — так CS2, CS8 — захист мовчить, а тест каже «працює».
В2. Переписувач промптів deepseek на nvidia: 6/6 падінь по 45 с; provider-switch не знає bazaarlink — I:2 — так CS3 — кожен виклик deepseek марно чекає 45 с.
В3. Застарілі шапки: answer-gate-shadow «нічого не блокує», але блокує; improver обіцяє delegate (знято свідомо 25.09) — I:6, P — так CS7; CS4 ні як «прогалина», так як застарілий заголовок — читач коду робить хибні висновки.
В4. Хуки відповіді сліпі: 21% записів answer-gate error:no-transcript; iter_turns не бачить queued_command — P, B — так CS13; queued_command не звірялось — частина слів користувача невидима перевіркам.
В5. Старт/закриття без автотригера; RULES.md:175 «підхопити HANDOFF.md», а pick_up бере baton.json — S:4) — так (я: grep -n RULES.md → :175) — правило описує не той файл, сесію можна почати без pick_up.
В6. check-links «лише читає», але запускає хуки → тестові рядки в бойових логах, завищені calls паспорта — S, K — так (CS, розділ розбіжностей: 84 з 420 «check») — будь-який підрахунок за тінями брудний.
В7. Хуки проєкту спрацьовують у під-агентах (немає перевірки agent_id) — B — так (я: grep -l agent_id .claude/hooks/* → 0) — роздувають токени під-агентів, сміття в логах.
В8. tree-focus на SessionStart: timeout 5 с, а всередині git 3 + tmux 2+2 = до 7 с — S — так (я: settings:40 timeout 5; tfh:144,298,304) — хук може обриватися харнесом мовчки.
В9. Інвентар неповний: git-хуки поза git без інсталятора; паспорт не знає запускачів, git-хуків, session-report.sh — I:4, S — так CS6; так (я: grep -c session-report passport.json → 0) — після переустановки захист git зникне непомітно.
В10. DSH: tui без baton MCP, а ~/.dsh/AGENTS.md вимагає baton_pick_up/pass; dsh-enable-now.sh не знайде рядок запуску — D:30-35, S — ні/невідомо CS15 (скрипт недоступний з Termux) — правила DSH невиконувані.
В11. Вікна tmux: tmux-work.sh підписує «Вікно 3: shell / Вікно 4: DSH», індекс dsh = 3; SKILL.md і mod беруть work:3 жорстко — D:34, S — так (я: grep -n tmux-work.sh → :22,:25) — при зсуві вікон читатимуть не той екран.
В12. Голос «nudge:delegate» шукає «Делегуй», емітер лишився лише в classify-task.sh.bak* — P:4) — так (я: grep -rn → лише .bak і ag:56); звідки 15 спрацювань до 24.10 — не з'ясовано — сигнал фактично мертвий.
В13. mcp__deepseek__deepseek-reply не пишеться в delegate-calls.jsonl (лише commit-consent) — I:3 — так структурно (CS, розбіжності), число 19 не звірялось — облік витрат DeepSeek неповний.

## Що вирішувати першим і чому (правило черги)
1. Залежність: спершу В6+В7 (бруд у бойових логах від check-links і під-агентів) — від них залежать А1 і будь-який підрахунок тіней.
2. Що втратимо: далі В2 (45 с на кожен виклик deepseek щодня) і В1 (обіцяний захист мовчить, тест це маскує).
3. Менше перед більшим: дрібні правки В3, В5, В8, В11 — до злиття дублів Б1–Б4 і прибирання А4–А5 (через історію й TRASH.md).
