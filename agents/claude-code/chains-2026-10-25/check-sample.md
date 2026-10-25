# check-sample — вибіркова звірка тверджень зі звітів «обходу системи» (25.10)

Мета: збирати карту ланцюжків із перевірених фактів, а не зі слів агентів. Вузол: «Якість роботи агентів › Карта ланцюжків і обхід усієї системи в обидва боки».
Звіти: I = scout-instrumenty-git, P = scout-povidomlennya-stop, S = scout-sesiya, K = scout-vid-kintsya, D = agents/dsh/chains-2026-10-25.md.
Шляхи відносно /data/data/com.termux/files/home/AgentReachProject. Лише читання; цей файл — єдиний створений.

| № | Твердження | Чий звіт | Вердикт | Команда → що надрукувала |
|---|---|---|---|---|
| 1 | ~10 логів без читача (answer-gate-shadow, node-label-shadow, number-claim-shadow, ask-gate, plain-ask, commit-consent, personal-guard, delegate-calls, improver, proc-guard) | I, P, S, K | ПІДТВЕРДЖЕНО (застереження: «читача» шукав у .py/.sh/.mjs/.ts за ім'ям файла) | `grep -rIl -F "<ім'я логу>" .claude/hooks tools mods .claude/skills *.sh` для кожного → усюди лише хук-автор (commit-consent.log ще й копія автора в tools/verifier-backtest/sources-v4/); жодного стороннього коду. Паспорт рахує рядки за іншим шляхом (не збігся за ім'ям) |
| 2 | Ворота unlazy на Stop мертві: 4 теки, жодна не прив'язана до сесії | P, K | ПІДТВЕРДЖЕНО | `ls -d .unlazy/*/` → bash-request-brief, classify-task-fix, passport, q6 (+locks); `ls .unlazy/*/session` → No such file; `grep unlazy ~/.claude/settings.json` → порожньо, у settings.local.json:50 хук є; `gate-check.mjs:217-224` → `--bind` єдине місце, що пише `<scope>/session`; у журналі сесії 4cab3538 `grep -c "none bound"` → 91 (звіт казав 23, лічильник росте) |
| 3 | Переписувач промптів DeepSeek на nvidia чекає 45 с і падає | I | ПІДТВЕРДЖЕНО | `improver.log` (python-лічильник): 6 записів rewrite / tool mcp__deepseek__deepseek / provider nvidia / ok false; хвіст: secs 45.3, 45.2, 45.2, 45.2, 45.3, 45.5 (останній 2026-10-23); `TIMEOUT = 45` у delegate-prompt-improver-hook.py:38; `./.provider` → nvidia; `~/.claude/delegator.json` → "provider": "bazaarlink"; `grep -c bazaarlink tools/provider-switch.py` → 0. Примітка: файл `.provider` лежить у корені, не в .claude/ |
| 4 | Improver «не покриває delegate» — прогалина (matcher лише mcp__deepseek__deepseek, а заголовок хука обіцяє й delegate) | I | СПРОСТОВАНО (факт вірний, висновок «прогалина» — ні) | settings.local.json ~118 → `"matcher": "mcp__deepseek__deepseek"`; хук рядок 3: «на mcp__delegate__delegate / mcp__deepseek__deepseek(-reply)» (заголовок застарів); hook-підказка TROUBLES:2476: «переписувач знято з delegate (2026-09-25, за згодою користувача)»; останній rewrite для delegate 2026-09-25T10:50 — збігається. Це свідоме рішення, не дірка; реальна вада — застарілий заголовок |
| 5 | dsh-line.jsonl не існує, хоча tree-focus його пише | I, P, S, K | ПІДТВЕРДЖЕНО | `ls -la .claude/logs/dsh-line.jsonl` → No such file; `grep -n dsh-line tree-focus-hook.py` → :268 DSH_LOG задано |
| 6 | Git-хуки (pre-commit, commit-msg) лежать поза git; settings.local.json і .claude/logs/ не версіонуються | I | ПІДТВЕРДЖЕНО | `ls -la .git/hooks` → commit-msg (223 Б), pre-commit (188 Б); `git ls-files .git/hooks` → 0; `git ls-files \| grep -ci "pre-commit\|commit-msg"` → 0; `git check-ignore -v` → .gitignore:24 (settings.local.json), :30 (.claude/logs) |
| 7 | answer-gate-shadow названий «тінню», але друкує decision:block | I, P | ПІДТВЕРДЖЕНО | `grep -n '"decision"' answer-gate-shadow-hook.py` → :472 `print(json.dumps({"decision": "block", ...}))`; шапка :1-8 досі каже «ТІНЬОВИЙ режим… НІЧОГО не блокує», хоча рядок 13 вже описує голос |
| 8 | hooks-smoke «unlazy Stop» не може впасти: stop-hook.mjs не читає stop_hook_active | P | ПІДТВЕРДЖЕНО | `grep -c stop_hook_active .claude/skills/unlazy/scripts/stop-hook.mjs` → 0; `tools/hooks-smoke.py:150-151` → тест передає `stop_hook_active: True`, очікує `rc == 0` |
| 9 | Усі 24 файли в .claude/hooks підключені в settings.local.json | I | ПІДТВЕРДЖЕНО | `ls .claude/hooks/*.py *.sh *.mjs \| wc -l` → 24; цикл `grep -q "$f" settings.local.json` → не знайдені лише `__pycache__` і `tests` (теки, не хуки) |
| 10 | .claude/active-tree: читає tree-focus, писача немає, файл від 28.09 | P, S, K | ПІДТВЕРДЖЕНО | `ls -la .claude/active-tree` → 26 Б, Sep 28 10:44; `git ls-files` → відстежується; `grep -rIn active-tree` по .py/.sh/.mjs/.ts/.tsx → лише tree-focus-hook.py:34 (коментар) і :416 (читання) |
| 11 | mcp_run.sh мертвий: викликів нема, вказує на неіснуючий config/yt-dlp.conf; живий agent-reach MCP — my_mcp_server.py | I | ПІДТВЕРДЖЕНО | `cat mcp_run.sh` → YT_DLP_CONFIG=…/config/yt-dlp.conf; `ls config/yt-dlp*` → лише тека yt-dlp (файла .conf нема); `grep -c mcp_run ~/.claude.json` → 0; `grep my_mcp_server ~/.claude.json` → :1588; єдина згадка в коді — pathspec у session-report.sh:63 (git log), не виклик; `git log -1 -- mcp_run.sh` → 29d1b09 |
| 12 | ~/.claude/hook-test.log 5,5 МБ без ротації, пише classify-task.sh, читача нема | I, P | ПІДТВЕРДЖЕНО | `ls -la` → 5575827 Б; `wc -l` → 46133 рядків (P казав 46004 — росте); `grep -rIl hook-test.log` по tools/.claude/hooks/skills/mods/~/.claude/hooks → лише ~/.claude/hooks/classify-task.sh:15 (запис) |
| 13 | answer-gate: 85 із 398 записів `error:no-transcript` (21%) | P | ПІДТВЕРДЖЕНО (число зсунулось через ріст логу) | `wc -l answer-gate-shadow.jsonl` → 420; `grep -c 'error:no-transcript'` → 87 (20,7%) |
| 14 | settings.local.json.bak* — 37 файлів, 284 КБ, не читає ніхто | K | СПРОСТОВАНО (кількість) | `ls .claude \| grep -c bak` → 33; `find . -maxdepth 3 -name "*.bak*" -path "*claude*"` → 34; `du -ck .claude/*bak*` → 284 КБ (розмір збігся). 37 — не відтворено |
| 15 | dsh-enable-now.sh:34-35 шукає `DSH_TUI_RETENTION_MAX_COUNT=0 npx dsh`, якого в run-dsh.sh:9 немає → скрипт падає, mcp-baton не додається | D | НЕ ПЕРЕВІРЕНО (скрипт не знайдено) | `find ~ -maxdepth 4 -name dsh-enable-now.sh` і `find . -name …` → порожньо (імовірно в proot /root/dsh-app, звідси недоступно). Друга половина підтверджена: `run-dsh.sh:9` = `…DSH_TUI_RETENTION_MAX_COUNT=0 exec /root/dsh-app/node_modules/.bin/dsh --profile tui` (без `npx`) |

## Збіги й суперечності

Збіги (те саме знайшли двоє чи більше):
- Лог dsh-line.jsonl не створюється: I, P, S, K (чотири звіти). Перевірено (№5).
- active-tree «читають — ніхто не пише»: P, S, K. Перевірено (№10).
- Тіньові логи й ask/plain-ask/commit-consent без читача: I, P, S, K. Перевірено (№1).
- Ворота unlazy не спрацьовують самі: P (точно, 4 теки, none bound), K («через неоднозначність 4 тек ніколи не спрацьовує»). Перевірено (№2).
- Екран DSH читається кілька разів і парситься двічі (◐): P (tf + mods/parse.ts), S (tfh, register.tsx, SKILL.md). Не перевіряв командою.
- Парсинг ledger «останній pass» продубльовано (baton-guard і baton-reminder): P, S. Не перевіряв.
- Чотири подання стану baton (baton.json, HANDOFF.md, HANDOFF-view.md, pass-N): K; D бачить пару baton.json ≈ pass-75.json. Не перевіряв розміри.
- Вікно tmux 3 = dsh: S (перевірено tmux), D (dsh-direct-channel.md:91-92). Збігаються.
- tui-профіль DSH без baton MCP: S (B7: «у tui baton нема, вузол Z8 відкритий»), D (L5). Збігаються; мою перевірку не робив (тека ~/.dsh у proot).
- Тестове забруднення бойових shadow-логів: S і K, але з різними числами (див. нижче).

Суперечності й розбіжності:
- Чи «живий» baton-diff.py: S пише «ніхто не запускає автоматично: baton-diff.py (60 викликів вручну)», але той самий S у B4 каже, що його імпортує baton-guard-hook:92 на кожному baton_pass, а I — «baton-guard на кожну передачу». Тобто «вручну» і «автоматично» в одному й тому ж файлі — S суперечить сам собі.
- Тестові рядки в shadow-логах: S — session="check": 82 з 398 (answer-gate), 146 з 542 (number-claim); K — «check/smoke/test»: 101 з 397 і 156 з 541. Різні фільтри, різні моменти зрізу. Моя перевірка: `"session": "check"` у answer-gate = 84 з 420 — ближче до S.
- Кількість записів у логах: P — 398/542 (запусків), K — 397/541; різниця в 1 — момент зрізу. Зараз answer-gate = 420.
- Кількість .bak: K — 37, факт — 33/34 (№14).
- Improver і delegate: I подає це як дірку («заголовок хука обіцяє…»), але TROUBLES:2476 фіксує свідоме зняття 25.09. Інші звіти (K) лише згадують improver як «лог без читача».
- Unlazy: I пише «unlazy stop-hook.mjs працює зі станом у .unlazy/», P і K — що ворота мертві. Правильно P/K (№2).
- Нумерація pass: S каже «поточний pass-75, passCount 76»; зараз у .baton/history є pass-79.json, у ledger 255 рядків (S — 250). Звіт S застарів за кілька годин (хтось робив baton_pass). Не плутати зі справжньою розбіжністю.
- delegate-викликів: I — 275; `delegate-calls.jsonl` зараз 296 рядків, з них tool=mcp__delegate__delegate — 240. Що саме рахував I — незрозуміло, не звіряв.
- I про `mcp__deepseek__deepseek-reply` («19 викликів не в delegate-calls.jsonl»): структурно підтверджено — `grep -c deepseek-reply delegate-calls.jsonl` → 0, а settings.local.json:224 тримає matcher `mcp__deepseek__deepseek|mcp__deepseek__deepseek-reply` лише для commit-consent; саме число 19 не перевірено.

## Підсумкові числа

Твердженнь у вибірці: 15 (команда: рядки таблиці 1-15).
- ПІДТВЕРДЖЕНО: 12 (№1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13)
- СПРОСТОВАНО: 2 (№4 — трактування «прогалина», №14 — кількість .bak 37 проти 33)
- НЕ ПЕРЕВІРЕНО: 1 (№15 — скрипту dsh-enable-now.sh не знайдено)
