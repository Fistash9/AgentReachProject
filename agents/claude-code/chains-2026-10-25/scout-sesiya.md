# scout-sesiya — звіт розвідника (обхід системи, 25.10, Explore/sonnet)

Розвідка ділянки «точки входу: сесія». Нічого не змінено і не створено. Скрипти не запускалися, лише grep, sed, cat, ls, tmux list-windows і tmux capture-pane. settings = .claude/settings.local.json, tfh = .claude/hooks/tree-focus-hook.py, bgh = .claude/hooks/baton-guard-hook.py, srv = /data/data/com.termux/files/usr/lib/node_modules/@timurabi3/baton-mcp/server.mjs (baton MCP, пакет поза репозиторієм).

1) ЛАНЦЮЖКИ
A1 SessionStart#1 → shell-рядок `echo 'unset -f grep find rg pkill'` → пише в $CLAUDE_ENV_FILE → читає харнес (споживання не кодом проєкту; рецепт TROUBLES.md:1071) — settings:25-31
A2 SessionStart#2 → tfh (запускає харнес, settings:38-40, timeout 5). Читає stdin JSON, trees/*.md (tfh:328), GOALS.md (:219), memory/*.md рядок «How to apply:» (:164; 3 правила HOWTO_RULES :57), .claude/active-tree (:416), `git status` (:143), tmux list-windows і capture-pane (:297,:303), $BATON_AGENT (:320). Пише в stdout additionalContext (:431), його читає модель. Пише ще dsh-line.jsonl (:380), див. ГЛУХІ КУТИ.
A3 SessionStart-подібний вхід поза settings-хуками: плагін agents-status (settings:319 enabledPlugins) → mods/agents-status/hooks/register.tsx:15 on('session.start') → grep `[>]` у trees/ (:16) + tmux capture-pane work:3 (:19) → смуга над промптом (:30 AbovePrompt)
A4 Старт → baton: жоден SessionStart-хук не викликає baton. baton_pick_up запускається лише за текстом RULES.md:175 (+ allow-правило settings:11) → B1
B1 baton_pick_up (MCP: ~/.claude.json:1594 → run-baton.sh:7 → srv) читає baton.json (srv:32) і ledger (srv:37), пише в ledger рядок pick_up (srv:126), повертає renderHandoff зі стану baton.json (srv:128)
B2 PostToolUse pick_up (settings:246-250) → bgh:149 → double_pickup читає ledger.jsonl (bgh:58) → ⚠ additionalContext (bgh:158). Далі view_hint: subprocess tools/handoff-view.py --check (bgh:168) → читає baton.json (handoff-view.py:132) → пише .baton/HANDOFF-view.md (:139) → модель читає за підказкою (bgh:177)
B3 UserPromptSubmit (settings:290) → bgh:149 → double_pickup (лише ledger) → ⚠ на кожен промпт
B4 baton_pass: PreToolUse (settings:195-199) → bgh:121-147: deny без @власник у next. lost_items (bgh:91-94) імпортує tools/baton-diff.py через spec_from_file_location, читає baton.json (bgh:96), deny при втраті пункту. Після дозволу srv пише baton.json (srv:166), HANDOFF.md у корені (srv:167), ledger-рядок pass (srv:168)
B5 PreToolUse Bash (settings:87) → baton-reminder-hook.py: діє лише на «git push» (:55), читає ledger (:24) + git log (:39), ⏰ additionalContext (:70)
B6 baton-diff.py: хук не запускає, лише людина/модель за текстом RULES.md:181. Читає history/pass-*.json (:59) + baton.json (:64), друкує в stdout. Імпортують його bgh:92 і tools/focus-tree.py:44. Знімки history/pass-* читають ще achieved-map.py:198 і project-audit.py:67
B7 DSH пише в той самий baton з BATON_AGENT=dsh (agents/dsh/JOURNAL.md:4). Лише профіль web; у tui baton нема, вузол Z8 відкритий. Ledger: dsh pass 10, pick_up 5
C0 «Закрий сесію» — лише фраза користувача (description SKILL.md:3). Жоден .py/.sh/.json скіл не запускає (grep session-close: самі згадки). Settings не має SessionEnd-хука (події: SessionStart, Stop, Pre/PostToolUse, PostToolUseFailure, UserPromptSubmit).
C1 Крок 0 SKILL.md:19-31: tmux list-windows, capture-pane, send-keys work:3 → DSH пише JOURNAL.md/pass → читає крок 4 (SKILL.md:31)
C2 Крок 1-2: baton_history (читає ledger) → session-report.sh (SKILL.md:43): git status/diff/log, лише stdout
C3 Крок 2.5: check-links.py (SKILL.md:55) читає RULES*.md, settings, README, menu.sh, py_compile (:104) і запускає кожен .py-хук із settings на нейтральному вході (:119). memory-audit.py (SKILL.md:70) читає memory/*.md
C4 Кроки 2.6-2.7: claimcheck.py читає ~/.claude/projects/…/*.jsonl (:142,:163); error-registry.py (+--loop) читає ті ж jsonl (:14), registry-v1.md (:172), git log (:185). Результат — лише stdout
C5 Крок 3.9: inline-python читає session-cost.jsonl (SKILL.md:189) ← пише statusline-cost.py (:66; settings:309). Читає ще cost-nudge-hook (:22) і tools/cost-report.py
C6 Крок 3.10: session-export.py → jsonl → personal-scan.py (spec :95) → -o файл. deepseek-search.py --file → personal-scan (:190-192) → ~/.config/agent-reach/personal-patterns.txt (існує) → пише .claude/logs/deepseek-search/<ID>.json (:258)
C7 Крок 4: `cp baton.json → history/pass-N.json` (SKILL.md:256, bash агента) → baton_pass → B4. Крок 5: звіт у чат, читач — користувач. Крок 6: git add/commit/push → хуки git-add-status-hook і commit-consent-hook (пише commit-consent.log, :186)
C8 Дописування TROUBLES/BACKLOG/CONTEXT/USER_PROFILE/memory — це інструкції тексту скіла, не код-ланки.

2) ГЛУХІ КУТИ
- Пишуть, ніхто не читає:
  - dsh-line.jsonl: пише tfh:380, читача в коді нема, файла нема. Пишеться лише коли на екрані DSH є «◐»; зараз capture-pane дає 0 збігів.
  - HANDOFF.md у корені: пише srv:167, код проєкту не читає. pick_up бере стан з baton.json (srv:128), хоча RULES.md:175 каже «підхопити HANDOFF.md».
  - .baton/HANDOFF-view.md: код-читача нема, лише підказка моделі (bgh:177), ефективність не логується.
  - history/archive-2026-09-28/ і HANDOFF-pre-pass30/32/33.md: усі глоби нерекурсивні (baton-diff:59, achieved-map:198, project-audit:67-71), тож не читає ніхто. project-audit.py:13 згадує archive лише в тексті.
  - commit-consent.log (:186), ask-gate.jsonl (:130), plain-ask.jsonl (:38): лише дописуються, читачів нема (grep по tools/.claude/mods).
  - .claude/logs/L0-achieved-*.json і project-audit-*.json: пишуть achieved-map.py:291 і project-audit.py:431, читачів у коді нема.
- Читають, ніхто не пише: .claude/active-tree (читає tfh:416, писача в коді нема; «старий вказівник», tfh:34).
- Ніхто не запускає автоматично: baton-diff.py (60 викликів вручну, passport), handoff-view.py (окрім bgh), baton-split.py, baton_status (10 викликів), сам session-close, baton_pick_up/baton_pass (лише текст RULES.md:175-176).

3) ДУБЛІ
- Екран DSH читають тричі: tfh:296-305 (вікно за назвою dsh*), register.tsx:19 (work:3 жорстко), SKILL.md:20 (work:3). Парсинг «◐» — двічі (tfh:277 і parseDshTodo у mod; tfh:272-275 каже, що розбір перенесено з нього).
- «Поточна сесія» визначають чотирма способами: SKILL.md:189 (CLAUDE_CODE_SESSION_ID), claimcheck.py:158-168 (claude-*, не haiku), error-registry.py:123-133 (entrypoint cli), session-export.py:82 (max mtime без фільтра). Останній може взяти сесію haiku-поліпшувача.
- Порівняння знімків baton: baton-diff.py:76-91 ↔ focus-tree.py:100-120 (копія циклу, «та сама логіка») ↔ project-audit.py queue() (своя подібність ≥0.80 проти 0.5 у baton-diff.same).
- Парсинг ledger «останній pass»: bgh:54-77 і baton-reminder-hook.py:22-35, два незалежні.
- Прогін хуків на тестовому вході: check-links.py:107-123 ↔ tools/hooks-smoke.py:68.
- git status: tfh:141, session-report.sh:25, git-add-status-hook:118.
- Обхід shim-ів: хук unset -f (settings:25-31) ↔ env CLAUDE_CODE_DISABLE_SEARCH_SHIMS=1 (settings:4). TROUBLES.md:1012 каже, що змінна не діє, тож реально працює хук.

4) РОЗРИВИ
- Старт і закриття без автотригера: baton_pick_up та закриття сесії тримаються на тексті RULES.md:175-176 і фразі користувача. Вузол M11.5 «baton-reminder на Stop» — [ ] (passport). Нагадування про pass працює лише на git push (baton-reminder:55).
- check-links.py:9 каже «Лише читає», але запускає хуки: у shadow-логах session="check" 82 з 398 рядків (answer-gate-shadow.jsonl) і 146 з 542 (number-claim-shadow.jsonl). Це завищує «calls» у passport.
- Падіння хука check-links не бачить: перевіряє rc==0 і відсутність deny (:121), а tfh завжди exit 0 і глушить помилки (tfh:436-441). bgh:133-136 так само мовчки дає lost=[], якщо baton-diff.py зникне.
- tfh на SessionStart має timeout 5 (settings:40), а всередині git 3 с + tmux 2+2 с (tfh:144,298,304) = до 7 с.
- SKILL.md:20-21 і mod жорстко беруть work:3. Нині 3=dsh (перевірено tmux), але tfh шукає за назвою — при зсуві вікон розбіжність.
- Крок 3.9: порожній CLAUDE_CODE_SESSION_ID дає `'' in l` істинним для кожного рядка → береться останній запис чужої сесії (SKILL.md:189). Зараз змінна є (4cab3538…), працює.
- session-report.sh відсутній у passport (grep=0), тобто скрипт скіла поза інвентарем.
- Нумерація passCount скинута 28.09: у archive лежать pass-74/75.json від 28.09, а поточний pass-75 від 24.10. Ledger має 250 рядків, з них 152 pass, при passCount=76, тож поле pass у ledger не унікальне. bgh бере лише останній pass — безпечно.

5) НЕ ПЕРЕВІРЕНО
- Поведінка харнеса (читання $CLAUDE_ENV_FILE, автовиклик скіла за фразою): доказу з коду проєкту нема, лише TROUBLES.md:1071.
- Stop-хуки (unlazy stop-hook.mjs, node-label/number-claim/answer-gate-shadow) пофразові, не «закриття сесії» — не проходив.
- ~/.claude/hooks/classify-task.sh і session-timer.sh (SKILL.md:308): файли існують, але чи підключені в ~/.claude/settings.json — не дивився.
- memory-audit.py і deepseek-search.py прочитано вибірково (шапка, ввід/вивід).
- Чому .baton/HANDOFF-view.md має mtime 25.10 03:45 при останньому pick_up 24.10 18:35: гіпотеза, що це hooks-smoke.py:261-267 (зберігає й повертає файл), не підтверджена.
- Чи читає HANDOFF.md Codex (зовнішній агент) — поза репозиторієм.
- Відсоток «pick_up на сесію» не рахував: passport має 61 виклик pick_up на 261 журнал головних сесій, без урахування коротких сесій.
