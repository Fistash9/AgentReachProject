# Аудит зниклих пунктів baton — 2026-09-26

Мета: з'ясувати, що з пунктів «Далі» / «Відкриті питання», які були в
передачах стану (baton #1–#70) і зникли з нього, зроблено, а що
загубилось (запит користувача 2026-09-26).

Як: 69 з 70 передач відновлено з журналів сесій (#6 — без джерела) у
.baton/history/ (локально). Скрипт зібрав 240 унікальних пунктів, 233 з
них зникли до #70. Класифікував DeepSeek flash (під-сесія з пам'яттю,
2 порції: сесія dfec7950, Read-only). Оркестратор звірив: хеші «зроблено»
(8 з 8 вибірково — `git cat-file`), усі «забуто» — grep по BACKLOG,
TROUBLES, CONTEXT, RULES, скілу session-close і baton done.
Вартість: $0.068 без ціни кешу (журнал: 10 запитів, 164 101 вхід +
990 080 кеш, 72 576 вихід); оцінка до запуску ($0.02–0.05) була заниженою.

## Підсумок (після звірки)
Зроблено 45 · відкладено (живе в BACKLOG/дереві) 60 · дублі 88 ·
**забуто 8** · неясно 4. Поправка звірки: №18 (session-timer) — зроблено
(baton done: «session-timer.sh hook created and verified live in UI»).

## Забуто (8) — перевірено grep
1. №1 — тест повної передачі стану (baton) Claude ↔ DeepSeek.
2. №57 — проба `unlazy --bind` на реальній кодовій задачі (лише план у
   TROUBLES «Toil + Shelfware», рядки ~689–691).
3. №74 — session-close крок 3 «Не редагуй CONTEXT.md сам» (SKILL.md
   рядок 67) проти бажання користувача — не вирішено.
4. №97 — чи окупаються правило опори й claimcheck за кілька сесій.
5. №104 — чи діє `skillOverrides` на скіли плагіна (TROUBLES ~1928 —
   «НЕ перевірено»).
6. №132 — check-links: формулювання PROTOCOL.md у RULES-WHY.md (хибна
   тривога групи 2); повтори №194, №200.
7. №211 — чи робити тижневий відбір (WEEKLY.md) регулярно.
8. №227 — чи впливає effort max у deepseek-mcp (env.js) на ціну
   DeepSeek (TROUBLES ~2868 — «НЕ перевірено»).

## Неясно (4)
№11 «або почати нову фічу» (без змісту); №31 RULES.md clean-up (доказу
немає); №65 TRASH/USER_PROFILE у «Навігації» (CONTEXT.md не звірявся
DeepSeek); №177 урок «який пункт мав запитати» (пам'ять поза наданими).

## Закономірність (висновок DeepSeek, збігається зі звіркою)
Губляться дрібні «перевірити / вирішити» без якоря в BACKLOG
«Активні»/«Дослідити»; усе з якорем (рядок BACKLOG, хук, крок скілу)
вижило навіть при десятках повторів. 88 з 233 — копії: список «далі»
роздувався копіюванням. Висновок для процесу: кожен новий пункт «далі»
чи відкрите питання — одразу рядком у BACKLOG (див. «check-links —
«далі» з baton має бути в BACKLOG»).

## Додаток А — зниклі пункти (номери для таблиць)
    1. [next, baton #2–#2] Test full handoff between Claude and DeepSeek
    2. [next, baton #2–#2] Instagram Reels cookies task
    3. [next, baton #3–#3] Update CONTEXT.md with deepseek info
    4. [next, baton #3–#3] Update BACKLOG.md with deepseek info
    5. [next, baton #3–#3] Update TROUBLES.md with deepseek info
    6. [next, baton #3–#3] Update RULES.md with deepseek info
    7. [next, baton #3–#4] Test Instagram Reels cookies
    8. [next, baton #4–#4] Implement llm-cost-router-mcp for cost awareness
    9. [next, baton #5–#5] Implement llm-cost-router-mcp
    10. [next, baton #5–#5] Test Instagram Reels cookies (Kiwi Browser + yt-dlp --cookies)
    11. [next, baton #5–#5] Or start a new feature
    12. [next, baton #7–#11] SERVER.md — add tools section
    13. [next, baton #7–#10] HELP.txt — update (delegate, baton, deepseek, Ctrl+B ?)
    14. [next, baton #7–#7] llm-cost-router-mcp implementation
    15. [next, baton #7–#7] Instagram Reels cookies (Kiwi Browser + yt-dlp --cookies)
    16. [next, baton #8–#10] RULES.md — add prompt-boundaries rule
    17. [next, baton #8–#9] tscribe / Instagram Reels cookies
    18. [next, baton #8–#8] Verify session-timer.sh across multiple real turns in UI
    19. [next, baton #10–#10] Explore skill-creator to build custom skills
    20. [next, baton #11–#11] Обговорити з користувачем межі аудиту через Claude in Chrome (що саме досліджувати, обсяг чатів/налаштувань)
    21. [next, baton #11–#11] HELP.txt — update
    22. [next, baton #11–#11] Дослідити skill-creator для власних skills
    23. [next, baton #12–#12] Закомітити і запушити .claude/skills/session-close/ (SKILL.md + scripts/session-report.sh)
    24. [next, baton #12–#12] У BACKLOG.md позначити пункт 'Дослідити вбудовані Skills' як завершений — аудит безпеки вже зроблено
    25. [next, baton #12–#12] llm-cost-router-mcp — MCP для cost-awareness
    26. [next, baton #12–#13] SERVER.md — доповнити розділом про tools
    27. [next, baton #12–#12] HELP.txt — оновити (delegate, baton, deepseek, Ctrl+B)
    28. [next, baton #12–#12] RULES.md — правило про повний промпт з межами для безпечних задач
    29. [next, baton #12–#12] velocity-mcp, task-progress-bar — після timer-хука
    30. [next, baton #13–#13] HELP.txt — оновити
    31. [next, baton #13–#13] RULES.md clean-up
    32. [next, baton #13–#30] tscribe
    33. [next, baton #14–#14] chrome-bridge-mcp
    34. [next, baton #14–#14] Freebuff (PR #1377)
    35. [next, baton #14–#14] classify-task calibration
    36. [next, baton #16–#16] llm-cost-router-mcp (MCP для cost-awareness)
    37. [next, baton #16–#16] tscribe / Instagram Reels — приватні акаунти (cookies), дослідження
    38. [next, baton #16–#16] chrome-bridge-mcp — потребує окремого комп'ютера
    39. [next, baton #16–#16] Freebuff — чекати PR #1377 (ARM Linux fix)
    40. [next, baton #16–#16] classify-task.sh калібрування (delegate-хук)
    41. [next, baton #16–#16] ⚠️ BACKLOG.md 'Активні' містить застарілі пункти (SERVER.md, HELP.txt, RULES.md правило, session-timer-hook) — уже виконані, потребують прибирання
    42. [next, baton #27–#27] Дослідити вбудовані Skills Claude Code (anthropic-skills:*)
    43. [next, baton #27–#27] pkgtruth — автоматична перевірка пакетів (дослідити, не встановлювати)
    44. [next, baton #27–#27] transcriptor — тест TikTok/X
    45. [next, baton #27–#30] chrome-bridge-mcp (потребує комп'ютера)
    46. [next, baton #27–#30] Freebuff — чекати PR #1377
    47. [next, baton #27–#27] Автоматизація git-хуків/SessionEnd — розглянути безпечність (guard) перед встановленням
    48. [next, baton #27–#27] claude-archive-kb — чекає на Export data від користувача
    49. [next, baton #27–#27] ⚠️ CONTEXT.md застарів — 17 комітів після останнього запису, включно MCP/hook-коміти — рекомендовано оновити
    50. [next, baton #28–#28] ⚠️ НЕ ЗАВЕРШЕНО: правило 'Журнал vs знімок стану' ще не записано в RULES.md — було запропоновано та погоджено користувачем, але не записано
    51. [next, baton #28–#28] ⚠️ НЕ ЗАВЕРШЕНО: 3 конкретні питання з попереднього відкоту — (1) BACKLOG Instagram Reels: лишити деталь 'не перевірено приватні акаунти' активною чи перенести все в Завершено, (2) memory.jsonl — переносити повністю чи скоротити, (3) CONTEXT.md 'Архітектура' — дописати нижче чи замінити
    52. [next, baton #28–#28] Залишається з попереднього батону: tscribe, chrome-bridge-mcp, Freebuff PR #1377, classify-task калібрування, pkgtruth дослідження, transcriptor TikTok/X тест
    53. [next, baton #29–#29] classify-task.sh калібрування
    54. [next, baton #29–#29] pkgtruth дослідження
    55. [next, baton #29–#30] transcriptor TikTok/X тест
    56. [next, baton #29–#29] ECOSYSTEM.md Telegram-концепція — залишається концепцією, не планом реалізації
    57. [next, baton #30–#30] Unlazy --bind — спробувати на наступній реальній кодовій задачі
    58. [next, baton #30–#30] claude-mem / claude-code-auto-memory — дослідити
    59. [next, baton #33–#33] Вирішити з користувачем: додати 'tscribe (rvben/tscribe)' у BACKLOG.md 'Дослідити' як [unverified]-кандидат, чи прибрати як мертвий пункт остаточно
    60. [next, baton #33–#33] Instagram Reels — приватні акаунти не перевірено (cookies через Kiwi Browser + yt-dlp, окремо не тестувалось)
    61. [next, baton #33–#33] Вирішити, чи починати реально викликати deepseek tool для рутинних/розмовних задач з наступної сесії (самокорекція щойно записана, ще не застосована на практиці)
    62. [next, baton #34–#34] Нова сесія: перевірити фікс grep/find трьома командами з TROUBLES.md (echo $CLAUDE_CODE_EXECPATH; grep -rli 'DeepSeek' .claude; find .claude -maxdepth 1 -name 'settings*') і дописати результат новим рядком у TROUBLES.md
    63. [next, baton #34–#34] Перший важкий тригер — делегувати без y/n і побачити, чи глобальний CLAUDE.md та хуки не суперечать RULES.md; перевірити рядок DeepSeek у наступному session-close
    64. [next, baton #34–#34] CONTEXT.md: новий checkpoint (6 комітів після 623f122: skill request-brief, правило делегування, env-фікс, ECC/Hermes)
    65. [next, baton #34–#34] Вирішити з користувачем: додати TRASH.md і USER_PROFILE.md в розділ 'Навігація' CONTEXT.md
    66. [next, baton #34–#34] Живий тест request-brief на реальних запитах; вирішити про автозапуск (хук) і спростити формат брифу до питань по одному
    67. [next, baton #34–#34] Instagram Reels — приватні акаунти (BACKLOG, Активні)
    68. [next, baton #34–#34] ECC/Hermes: за потреби брати окремі ідеї (перевірка секретів, AgentShield), не ставити цілком
    69. [openQuestions, baton #34–#34] Чи змінювати глобальний блок делегатора в ~/.claude/CLAUDE.md і текст хука, щоб вони не вимагали y/n, як тепер вимагає RULES.md?
    70. [next, baton #35–#35] Відповісти на питання кроку 6: закомітити CONTEXT.md і TROUBLES.md (y/n)
    71. [next, baton #35–#35] Вирішити, чи записувати в BACKLOG.md пропоновані пункти: (а) нездійснені знахідки аудиту скілів, (б) узгодження PreToolUse-хуків із правилом автоделегування
    72. [next, baton #35–#35] Активний пункт BACKLOG: Instagram Reels — приватні акаунти не перевірено (cookies через Kiwi Browser + yt-dlp), без змін
    73. [next, baton #36–#36] На початку сесії викликати baton_pick_up
    74. [next, baton #36–#36] Вирішити розбіжність кроку 3 session-close ('не редагуй CONTEXT.md сам') і бажанням користувача залишати це агенту
    75. [next, baton #36–#36] BACKLOG (Дослідити): нездійснені знахідки аудиту скілів; розбіжність хуків із правилом автоделегування
    76. [next, baton #36–#36] BACKLOG (Активні): Instagram Reels — приватні акаунти не перевірено
    77. [next, baton #37–#38] Отримати від користувача: хто автор каналу (питання 4), особливі правила каналу (питання 10), чи канал про птахів чи про рідкісних тварин загалом, і підтвердження чернетки відповідей
    78. [next, baton #37–#38] Отримати ще 1-2 референси з дикторським текстом і наявними субтитрами; тоді оформити STYLE PROFILE і видати SAVED PROFILE
    79. [next, baton #37–#37] Закомітити script-agent/AGENT.md, BACKLOG.md, TROUBLES.md після підтвердження користувача (без agent.py, без пушу)
    80. [next, baton #37–#37] Коли користувач захоче: повернутися до відео й звуку для ШІ-птахів (перше питання: чим збирає відео)
    81. [next, baton #37–#40] Активні з BACKLOG: Instagram Reels приватні акаунти не перевірено; на початку кожної сесії викликати baton_pick_up
    82. [next, baton #38–#38] Коли користувач захоче: повернутися до відео й звуку для ШІ-птахів (перше питання: чим користувач збирає відео)
    83. [next, baton #40–#40] Тестовий сценарій 8–10 хв: користувач дає тему й хронометраж; запустити агента з AGENT.md + SAVED PROFILE, перевірити голос за профілем і відсутність вигаданої біографії автора
    84. [next, baton #40–#40] Доробити ANALYZER.md під жанр історій (список прогалин у кінці script-agent/analyses/stories-refs_2026-09-21.md)
    85. [next, baton #40–#40] Назва каналу, ширший перелік тем, підтвердження полів PACING і AUTHOR PERSONALITY
    86. [next, baton #43–#43] Наступний кандидат на такий же хук: rm/rmdir -> TRASH.md ДО виконання (детермінований тригер, задокументований прецедент випадкового видалення домашньої директорії)
    87. [next, baton #43–#43] Другий кандидат: git add -> нагадування про git status
    88. [next, baton #43–#43] Тема 'Закинутий готель у Вісконсині' лишається ВІДКЛАДЕНА за словом користувача — M1-M3/P1-P3/P5-P7 з постмортему не застосовувати без нового прямого запиту
    89. [next, baton #43–#46] Наступна сесія: почати з baton_pick_up
    90. [openQuestions, baton #43–#43] Чи додавати хук №1 (rm/rmdir -> TRASH.md) тим самим способом (pipe-test -> валідація -> live-fire) зараз чи в наступній сесії — користувач ще не відповів
    91. [openQuestions, baton #43–#43] Чи потрібні ще незалежні джерела поза Anthropic/OpenAI/Cognition про 'subagent sprawl'
    92. [next, baton #44–#44] Перевірити delegate-prompt-improver-hook.py на більш різних типах запитів (зараз перевірено лише один випадок)
    93. [next, baton #44–#44] Тема 'Закинутий готель у Вісконсині' лишається ВІДКЛАДЕНА — не чіпати без нового прямого запиту
    94. [next, baton #45–#45] claude-code-termux install 2.1.280 -> doctor -> тест deepseek -> якщо погано, install 2.1.273 назад
    95. [next, baton #45–#45] Тема 'Закинутий готель' лишається відкладена — не чіпати без нового прямого запиту
    96. [next, baton #45–#45] AI-атрибуція в комітах — відкрите питання, чекає рішення користувача
    97. [next, baton #46–#46] Кілька сесій жити з правилом опори й claimcheck: чи рідше доводиться питати «перевір ще раз»; чи окупається перечитування позначок
    98. [next, baton #46–#46] E5-хук (неможливо без пошуку): знайти 2-3 старі сесії з такими помилками, прогнати tools/claimcheck/backtest.py без змін шаблонів
    99. [next, baton #46–#46] Перевірити вартість deepseek-v4-pro vs flash (запит користувача), потім вирішити дефолт
    100. [next, baton #46–#46] claude-setup: уточнити в користувача, який саме мався на увазі; grill-me — ставити вибірково (--scope local)
    101. [next, baton #46–#48] AI-атрибуція в комітах — рішення користувача
    102. [next, baton #46–#46] Тема «Закинутий готель» — відкладена, не чіпати без прямого запиту
    103. [openQuestions, baton #46–#46] Який claude-setup мав на увазі користувач (HOPLAtools, npm AbdoKnbGit чи /setup-matt-pocock-skills)?
    104. [openQuestions, baton #46–#52] Чи діє skillOverrides на скіли плагіна (дока прямо не каже)?
    105. [openQuestions, baton #46–#46] Хук-підказка «Цей запит простий. Делегуй на DeepSeek» на кожне повідомлення розходиться з практикою — змінити хук чи правило?
    106. [next, baton #47–#48] Обговорити й створити claude-anthropic.sh (Opus 5.5 vs Opus 5; доступ залежить від плану claude.ai)
    107. [next, baton #47–#47] Вирішити роутинг: лишити flash-скрізь чи повернути важкі задачі (write/reason) на pro або Opus 5.5
    108. [next, baton #47–#47] Вирішити долю застарілих доків: глобальний ~/.claude/CLAUDE.md routing + таблиця цін delegate-пакета
    109. [next, baton #47–#49] E5-хук: знайти 2-3 старі сесії з помилками «неможливо без пошуку», прогнати tools/claimcheck/backtest.py
    110. [next, baton #47–#49] claude-setup уточнити в користувача; grill-me — вибірково (--scope local)
    111. [next, baton #47–#49] «Закинутий готель» (script-agent/output/) — не чіпати без прямого запиту
    112. [next, baton #47–#49] Наступна сесія — почати з baton_pick_up
    113. [next, baton #48–#48] Закомітити узгоджені доки окремими комітами з «Відкат: git revert» (.gitignore, CONTEXT.md, BACKLOG.md, TROUBLES.md)
    114. [next, baton #49–#49] ВИРІШИТИ важіль мислення: effort=low глобально / DART-проксі / лишити як є (дані є, рішення за користувачем)
    115. [next, baton #49–#49] Полагодити claimcheck: вибір журналу основної сесії (зараз мовчки бере чужу сесію, коли основна на DeepSeek)
    116. [next, baton #49–#49] Обговорити й створити claude-anthropic.sh (Opus 5.5 vs Opus 5) — на паузі з попередньої частини сесії
    117. [next, baton #50–#50] Закомітити BACKLOG.md (план claimcheck) і TROUBLES.md (розбір витрат сесії), якщо ще не зроблено; вирішити push 3–5 комітів
    118. [next, baton #50–#50] Полагодити claimcheck за планом у BACKLOG (CLAUDE_CODE_SESSION_ID + G1–G5); спершу можна перевірити, чи є змінна в DeepSeek-сесіях
    119. [next, baton #50–#50] Обговорити: чи користуватись auto mode у DeepSeek-сесіях (BACKLOG, новий пункт)
    120. [next, baton #50–#50] Хук «Делегуй на DeepSeek»: вимикати в DeepSeek-сесіях? (BACKLOG «Розбіжність хуків…»)
    121. [next, baton #50–#50] CONTEXT.md: дописати «Оновлення 2026-09-24 (друга сесія)» — рішень цієї сесії там немає
    122. [next, baton #50–#50] «Закинутий готель» (script-agent/output/) — не чіпати
    123. [next, baton #50–#50] Наступна сесія — почати з baton_pick_up; effort за замовчуванням (medium), не max
    124. [next, baton #51–#51] ПЕРШЕ в новій сесії: задача «Зменшити те, що вантажиться на старті сесії» (BACKLOG, Активні) — поміряти, дослідити через DeepSeek, показати план
    125. [next, baton #51–#52] Полагодити claimcheck за планом у BACKLOG
    126. [next, baton #51–#51] Обговорити auto mode у DeepSeek-сесіях; хук «Делегуй на DeepSeek» у DeepSeek-сесіях
    127. [next, baton #51–#51] CONTEXT.md: дописати «Оновлення 2026-09-24 (друга сесія)»
    128. [next, baton #51–#51] Закинутий готель (script-agent/output/) — не чіпати
    129. [next, baton #52–#52] Обрати з користувачем спосіб скорочення baton (3 варіанти в BACKLOG, Активні)
    130. [next, baton #52–#52] Частини B/C плану: закріплена пам'ять і RULES.md — спершу історія кожного правила
    131. [next, baton #52–#52] Прочитати код sam-illingworth/audit-setup, потім read-only прогін
    132. [next, baton #52–#52] check-links: RULES-WHY.md згадує PROTOCOL.md (файл пакета baton, не репо) — вирішити формулювання
    133. [next, baton #52–#52] CONTEXT.md: дописати «Оновлення 2026-09-24» (8 комітів після останнього запису)
    134. [openQuestions, baton #52–#55] Як скорочувати baton: вибіркове читання, архів старих Done чи нова естафета на тему?
    135. [openQuestions, baton #52–#55] Хук-підказка «Делегуй на DeepSeek» на кожне повідомлення — змінити хук чи правило?
    136. [next, baton #53–#53] ПЕРШЕ в новій сесії: аудит проєкту (BACKLOG, Активні, перший пункт)
    137. [next, baton #53–#53] Обрати з користувачем спосіб скорочення baton (3 варіанти в BACKLOG)
    138. [next, baton #53–#53] Частини B/C: закріплена пам'ять і RULES.md — спершу історія кожного правила
    139. [next, baton #53–#53] Прочитати код sam-illingworth/audit-setup
    140. [next, baton #53–#53] check-links: формулювання PROTOCOL.md у RULES-WHY.md
    141. [next, baton #53–#53] Полагодити claimcheck; CONTEXT.md «Оновлення 2026-09-24»
    142. [next, baton #54–#54] ПЕРШЕ: верифікатор — етап 1 бектест (BACKLOG, перший пункт Активні)
    143. [next, baton #54–#54] ДРУГЕ: аудит проєкту (BACKLOG Активні)
    144. [next, baton #54–#54] Обрати спосіб скорочення baton (3 варіанти в BACKLOG)
    145. [next, baton #54–#54] Частини B/C: закріплена пам'ять і RULES.md (вже 226 рядків)
    146. [next, baton #54–#54] check-links: PROTOCOL.md у RULES-WHY.md; полагодити claimcheck
    147. [next, baton #55–#55] ДРУГЕ з BACKLOG: аудит проєкту (Активні) — тепер можна перевіряти висновки скілом verify-before-show
    148. [next, baton #55–#55] Обрати спосіб скорочення baton (3 варіанти в BACKLOG); RULES.md вже 230 рядків (частина C)
    149. [next, baton #55–#55] FreeLLMAPI і Reset for free — у BACKLOG «Дослідити», коли дійде черга
    150. [next, baton #55–#55] Полагодити claimcheck (план G1–G5 у BACKLOG)
    151. [openQuestions, baton #55–#55] Лишати improver-хук на Opus 5.5 з огляду на тижневий ліміт (попередження: закінчиться в неділю)?
    152. [next, baton #56–#56] ПЕРШЕ: після перезапуску — provider-switch.py status і один живий delegate-виклик на NVIDIA
    153. [next, baton #56–#56] Вирішити з користувачем: push 16 комітів
    154. [next, baton #56–#56] A/B хука-переписувача (раунд 2 з ним і без нього) — чи він узагалі потрібен
    155. [next, baton #56–#56] Аудит проєкту (BACKLOG Активні) — з verify-before-show
    156. [next, baton #56–#56] Скорочення baton (3 варіанти); claimcheck-фікс; PROTOCOL.md у RULES-WHY (check-links)
    157. [openQuestions, baton #56–#56] Пушити 16 комітів (у results-nvidia-*.jsonl — короткі цитати джерел, репо публічне)?
    158. [openQuestions, baton #56–#56] Чи потрібен хук-переписувач взагалі (A/B не робили)?
    159. [openQuestions, baton #56–#56] Як скорочувати baton?
    160. [next, baton #57–#57] Рішення користувача: основний провайдер delegate — DeepSeek flash (платно, ~$0.25) чи лишити NVIDIA (BACKLOG Активні)
    161. [next, baton #57–#57] Рішення користувача: фікс Node keep-alive у run-delegate.sh (node --require, keepAlive:false)
    162. [next, baton #57–#57] Коли delegate відповідає — перевірити наживо фікс UTF-8 3.0.1 довгою українською відповіддю
    163. [next, baton #57–#57] Push 7 комітів — окреме питання користувачу
    164. [next, baton #57–#57] Оновити CONTEXT.md (7 комітів після останнього запису)
    165. [next, baton #57–#57] Пробний FreeLLMAPI у ~/freellmapi лише з ключем NVIDIA
    166. [next, baton #57–#58] RULES.md: прибрати «пошук» з тригерів delegate (через RULES-WHY, зі згоди)
    167. [next, baton #57–#57] Аудит проєкту (BACKLOG) — з verify-before-show
    168. [openQuestions, baton #57–#57] Основний провайдер delegate: DeepSeek (платно, надійно) чи NVIDIA (безкоштовно, нестабільно)?
    169. [openQuestions, baton #57–#57] Чи потрібен переписувач узагалі для агента deepseek?
    170. [openQuestions, baton #57–#57] Яку частину скидає картка «Reset for free» — сесію чи тиждень (користувач подивиться в Settings → Usage)?
    171. [next, baton #58–#58] provider-switch.py: додати bazaarlink (інакше `nvidia` перезапише delegator.deepseek.json); .provider для хука-переписувача агента deepseek досі nvidia
    172. [next, baton #58–#58] Freebuff: постійне місце для програми (зараз $PREFIX/tmp/fb-1790340155/bin) і перевірка freebuff-mcp — агент на безкоштовних моделях для Claude Code
    173. [next, baton #58–#58] Push 10 комітів — окреме питання користувачу
    174. [next, baton #58–#58] Оновити CONTEXT.md (багато комітів після останнього запису)
    175. [next, baton #58–#58] Node keep-alive 39 с — актуально лише для повільних провайдерів; з BazaarLink відповіді 3–21 с
    176. [next, baton #58–#58] Аудит проєкту (BACKLOG)
    177. [next, baton #59–#59] Відповідь користувача: який пункт я мав запитати → зберегти урок у пам'ять
    178. [next, baton #59–#61] Розширити session-close (BACKLOG)
    179. [next, baton #59–#59] provider-switch.py: додати bazaarlink
    180. [next, baton #59–#59] freebuff-mcp: агент на безкоштовних моделях для Claude Code
    181. [next, baton #59–#59] RULES.md: прибрати «пошук» з тригерів delegate (через RULES-WHY)
    182. [next, baton #59–#60] Аудит проєкту
    183. [next, baton #60–#60] Jules: з'ясувати можливості — які задачі проєкту можна давати (запит користувача)
    184. [next, baton #60–#60] Push незапушених комітів — спитати
    185. [next, baton #60–#60] Розширити session-close (BACKLOG): /cost + effort, прибирання, повторне закриття, журнал рішень, зовнішня перевірка сесії
    186. [next, baton #60–#60] provider-switch.py: додати bazaarlink і запасний deepseek при відмовах BazaarLink
    187. [next, baton #60–#60] freebuff-mcp: агент на безкоштовних моделях
    188. [next, baton #60–#60] RULES.md: прибрати «пошук» з тригерів delegate
    189. [next, baton #61–#61] Push: локальний main розійшовся з origin (ahead 1+, behind 3 — злитий PR #1): git pull --rebase, потім push — спитати
    190. [next, baton #61–#61] Браузер на телефоні (BACKLOG Активні): окрема сесія, adb → тунель → chrome-devtools-mcp, спершу лише читання; перевірити обмеження доступу до вкладок
    191. [next, baton #61–#61] CONTEXT.md: оновлення (7+ комітів після останнього запису, Jules/pytest/tests/)
    192. [next, baton #61–#61] Jules: наступні вузькі задачі з тестами (tools/*.py)
    193. [next, baton #61–#61] provider-switch.py: bazaarlink + запасний deepseek
    194. [next, baton #61–#61] check-links: група 2 хибно ловить PROTOCOL.md у RULES-WHY.md (файл пакета baton, не проєкту)
    195. [next, baton #62–#62] Push коміту BACKLOG (розбір уроків), якщо не запушено — спитати
    196. [next, baton #62–#62] Розширити session-close: зовнішня перевірка сесії + /cost і effort (ПЕРШЕ)
    197. [next, baton #62–#62] Перевірка засвоєння уроків — вирішити з користувачем: крок session-close чи окремий скіл
    198. [next, baton #62–#62] Браузер на телефоні (adb → тунель → chrome-devtools-mcp), спершу лише читання; обмеження доступу до вкладок
    199. [next, baton #62–#62] CONTEXT.md: оновлення
    200. [next, baton #62–#64] check-links: хибна тривога PROTOCOL.md (група 2)
    201. [next, baton #63–#63] CONTEXT.md: оновлення (18 комітів після 2026-09-25) — рішення користувача
    202. [next, baton #63–#63] Тиждень спостереження за статуслайном → Stop-хук з порогами контексту 40/65% (не частіше раз на 30 хв), BACKLOG «Розширити session-close»
    203. [next, baton #63–#63] Решта session-close: прибирання tmp і бекапів, повторне закриття, журнал рішень, межа розміру сесії
    204. [next, baton #63–#64] Перевірка засвоєння уроків — крок чи скіл (BACKLOG)
    205. [next, baton #63–#63] Браузер на телефоні (BACKLOG Активні) — окремою сесією
    206. [next, baton #64–#64] Браузер на телефоні (BACKLOG Активні) — новою сесією
    207. [next, baton #64–#65] Тиждень спостереження за статуслайном → Stop-хук з порогами 40/65%
    208. [next, baton #64–#64] Решта session-close: прибирання tmp/бекапів, повторне закриття, журнал рішень, межа розміру сесії
    209. [next, baton #65–#65] troubles-grep-hook — шукати й по файлах пам'яті (BACKLOG Активні; спершу прочитати хук повністю)
    210. [next, baton #65–#65] check-links — пункти «далі» з baton мають бути в BACKLOG (BACKLOG Активні)
    211. [next, baton #65–#65] Після цих двох — вирішити, чи робити тижневий відбір регулярно (WEEKLY.md)
    212. [next, baton #65–#65] Браузер на телефоні (BACKLOG Активні)
    213. [next, baton #66–#66] A7 — дерево задач: «задачі всередині задач» (рівні, блокує/у чергу, повернення); спершу готові підходи; опора ECOSYSTEM «дерева задач» + unlazy Depth Tree (BACKLOG «Черга з сесії 2026-09-26»)
    214. [next, baton #66–#66] Проба «картки» в TROUBLES на 10 записах (BACKLOG)
    215. [next, baton #66–#66] Авто-перемикання моделі/мислення за складністю; Opus-охоронець для DeepSeek-сесій; проба зору для аналізатора (BACKLOG, черга)
    216. [next, baton #66–#66] Рішення: чи покриває автоделегування (RULES.md, без y/n) платні виклики; чи піднімати «спершу питати» в RULES.md
    217. [next, baton #66–#66] check-links — «далі» з baton має бути в BACKLOG (BACKLOG Активні)
    218. [next, baton #66–#68] CONTEXT.md — оновлення за 2026-09-26 (друга сесія)
    219. [openQuestions, baton #66–#66] Чи покриває правило автоделегування (без y/n) платні виклики DeepSeek, чи платне — завжди з дозволу?
    220. [openQuestions, baton #66–#66] Піднімати «важливі дії — спершу питати» в RULES.md для оркестратора?
    221. [openQuestions, baton #66–#66] Прибирати рядок Claude-Session: <URL> з комітів публічного репо?
    222. [next, baton #67–#68] Вирішити з користувачем, що першим: A7 дерево задач чи проба ask-правил (обидва — BACKLOG Активні)
    223. [next, baton #67–#68] Перед пробою ask-правил — відкриті рішення: платні виклики vs автоделегування; «спершу питати» в RULES.md; Claude-Session у комітах
    224. [next, baton #67–#67] $0.50: звірити з кабінетом DeepSeek, коли користувач подивиться Usage
    225. [next, baton #67–#68] Проба «картки» в TROUBLES; складність / Opus-охоронець / зір (BACKLOG черга)
    226. [next, baton #67–#68] check-links — «далі» з baton має бути в BACKLOG
    227. [next, baton #67–#68] Чи effort max у deepseek-mcp (env.js) впливає на ціну на DeepSeek — не перевірено
    228. [next, baton #69–#69] T4 дерева trees/pidrozdil-deepseek.md: показати користувачу текст інструкції deepseek-search (П1 + 5 прийомів з T2.1), створити теку agents/deepseek-search/ (П1–П3), платна проба з критеріями ДО старту (вхід < 21,6 тис., не називає себе Claude Code, claudeMdExcludes діє, нічого поза текою)
    229. [next, baton #69–#69] Черга рішень: замок на mcp__deepseek__deepseek-reply; «так» на формат картки дерева
    230. [next, baton #69–#69] CONTEXT.md — оновлення за 2026-09-26 (18+ комітів після останнього запису)
    231. [next, baton #69–#69] Підсумок проби ask-правил ~2026-10-03 і рішення про «спершу питати» в RULES.md
    232. [openQuestions, baton #69–#69] Додати mcp__deepseek__deepseek-reply у ask-замок?
    233. [openQuestions, baton #69–#69] Чи виключає claudeMdExcludes користувацький ~/.claude/CLAUDE.md (документація — висновком, перевірити в T4)

## Додаток Б — таблиці DeepSeek (сирі, до звірки)

N | статус | доказ (хеш / розділ / шукані слова) | суть

1 | ЗАБУТО | не знайдено; шукав «handoff», «Claude↔DeepSeek», «тест» (у tree.md T1.2 — лише baton_pick_up у під-сісіях) | тест повної передачі стану Claude↔DeepSeek
2 | ЗРОБЛЕНО | fe66072; BACKLOG «Завершено» 17.09 — публічні Reels без cookies, гіпотеза хибна | Reels: cookies для публічних не потрібні
3 | ЗРОБЛЕНО | 2acd89d — CONTEXT.md, deepseek MCP як 7-й сервер | CONTEXT.md отримав опис deepseek
4 | ЗРОБЛЕНО | 1da6d05 — deepseek MCP вирішено, deep-claude відкинуто | BACKLOG.md оновлено про deepseek
5 | ЗРОБЛЕНО | ac6fdf8 — рецепт deepseek-mcp у TROUBLES.md | TROUBLES.md отримав рецепт deepseek
6 | ЗРОБЛЕНО | f45b24c — правило вибору інструмента DeepSeek у RULES.md | RULES.md отримав правило про deepseek
7 | ДУБЛЬ (2) | те саме, що №2, baton #4 | повтор «тест Reels cookies»
8 | ВІДКЛАДЕНО | BACKLOG «Unverified Claims»: не ставити без репо/авторства | llm-cost-router-mcp заморожено до верифікації
9 | ДУБЛЬ (8) | той самий пункт у baton #5 | повтор llm-cost-router-mcp
10 | ВІДКЛАДЕНО | BACKLOG «Активні»: приватні Reels (Kiwi Browser + yt-dlp --cookies) | приватні акаунти Reels — живий пункт
11 | НЕЯСНО | «або почати нову фічу» — не дія, а альтернатива без змісту | «нова фіча» — нічого не названо
12 | ЗРОБЛЕНО | 36777ab; BACKLOG «Завершено» 18.09 — розділ Tools | SERVER.md доповнено розділом Tools
13 | ЗРОБЛЕНО | 36777ab; BACKLOG «Завершено» 18.09 — HELP.txt оновлено | HELP.txt (delegate, baton, deepseek)
14 | ДУБЛЬ (8) | baton #7 | повтор llm-cost-router-mcp
15 | ДУБЛЬ (10) | baton #7, той самий текст із Kiwi Browser | повтор тесту cookies
16 | ЗРОБЛЕНО | 1ecc310; BACKLOG «Завершено» 18.09 — правило меж | RULES.md: повний промпт з межами
17 | ВІДКЛАДЕНО | BACKLOG «Дослідити» → tscribe [unverified]; приватні Reels — «Активні» | tscribe і приватні Reels — живі
18 | ЗАБУТО | не знайдено; шукав «session-timer», «UI», «реальні ходи» | перевірка session-timer.sh у живих ходах
19 | ЗРОБЛЕНО | 02af290, 18bfc0e; BACKLOG «Завершено» 18.09 — власні скіли можливі | skill-creator: скіли створюються
20 | ВІДКЛАДЕНО | BACKLOG «Дослідити» → chrome-bridge-mcp: «відкладено до комп'ютера» | межі аудиту через Chrome — на паузі
21 | ДУБЛЬ (13) | baton #11 | повтор HELP.txt
22 | ДУБЛЬ (19) | baton #11 | повтор skill-creator
23 | ЗРОБЛЕНО | 3fd374f — Add session-close Skill (перший власний) | session-close закомічено
24 | ЗРОБЛЕНО | BACKLOG «Завершено» 18.09: skills-пункт закрито, аудит безпеки є | пункт skills позначено завершеним
25 | ДУБЛЬ (8) | baton #12 | повтор llm-cost-router-mcp
26 | ДУБЛЬ (12) | baton #12–#13 | повтор SERVER.md
27 | ДУБЛЬ (13) | baton #12 | повтор HELP.txt
28 | ДУБЛЬ (16) | baton #12 | повтор правила меж
29 | ЗРОБЛЕНО | aa56ca0; TROUBLES «Вигадані пакети» — обидва 404 на npm | velocity-mcp/task-progress-bar не існують
30 | ДУБЛЬ (13) | baton #13 | повтор HELP.txt
31 | НЕЯСНО | єдиний кандидат 6b74092 «refactor(rules)… без дубля переліку»; «clean-up» не конкретний | RULES.md clean-up — доказу немає
32 | ВІДКЛАДЕНО | BACKLOG «Дослідити» → tscribe (кандидат 040421f) | tscribe чекає рішення
33 | ВІДКЛАДЕНО | BACKLOG «Дослідити» → chrome-bridge-mcp, план є, чекає комп'ютера | chrome-bridge — на паузі
34 | ЗРОБЛЕНО | 066615a; TROUBLES «Freebuff у Termux…» — PR #1377 не знадобився | Freebuff працює в Termux
35 | ЗРОБЛЕНО | b65091d, f70e3ed — фікс шуму + GATES.md, 4 ворота | калібрування classify-task завершено
36 | ДУБЛЬ (8) | baton #16 | повтор llm-cost-router-mcp
37 | ВІДКЛАДЕНО | BACKLOG «Дослідити» (tscribe) + «Активні» (приватні Reels) | tscribe і приватні Reels — живі
38 | ДУБЛЬ (33) | baton #16 | повтор chrome-bridge
39 | ДУБЛЬ (34) | baton #16 | повтор Freebuff/PR #1377
40 | ДУБЛЬ (35) | baton #16 | повтор калібрування
41 | ЗРОБЛЕНО | c6b2254 — BACKLOG cleanup: прибрано 3 застарілі пункти «Активних» | застарілі пункти «Активних» прибрано
42 | ДУБЛЬ (19) | baton #27 | повтор вбудованих Skills
43 | ЗРОБЛЕНО | 0b71688, 14eb3f8; BACKLOG «Завершено» 19.09 | pkgtruth встановлено 8-м сервером
44 | ВІДКЛАДЕНО | BACKLOG «Дослідити» → transcriptor: YouTube/IG працюють, TikTok/X — ні | тест TikTok/X не робився
45 | ДУБЛЬ (33) | baton #27–#30 | повтор chrome-bridge
46 | ДУБЛЬ (34) | baton #27–#30 | повтор Freebuff/PR #1377
47 | ВІДКЛАДЕНО | BACKLOG «Дослідити»: «Автоматизація git» + «baton_pass через SessionEnd» | git/SessionEnd-хуки — без guard не ставити
48 | ВІДКЛАДЕНО | BACKLOG «Дослідити» → claude-archive-kb: чекає Export data | архів чатів чекає експорту
49 | ЗРОБЛЕНО | 27ab365, 35f46a5, 8597f40 — оновлення CONTEXT.md | CONTEXT.md наздогнав коміти
50 | ЗРОБЛЕНО | 587144c — journal-vs-snapshot rule | правило «Журнал vs знімок» записано
51 | ВІДКЛАДЕНО | (1)(2) закрито (BACKLOG «Завершено» 17.09; memory.jsonl ✅); (3) живе: «Активні» — лад у CONTEXT.md | 3 питання: лишилось третє
52 | ДУБЛЬ (32,33,34,35,43,44) | той самий перелік «залишається» | збірка вже врахованих пунктів
53 | ДУБЛЬ (35) | baton #29 | повтор калібрування
54 | ДУБЛЬ (43) | baton #29 | повтор pkgtruth
55 | ДУБЛЬ (44) | baton #29–#30 | повтор transcriptor TikTok/X
56 | ВІДКЛАДЕНО | BACKLOG «Дослідити» → A2A-апгрейд telegram_deepseek_bot.py (концепція) | Telegram-концепція лишається концепцією
57 | ЗАБУТО | не знайдено; шукав «unlazy --bind», «кодова задача» — лишився план у TROUBLES «Toil+Shelfware» | проба unlazy --bind не робилась
58 | ЗРОБЛЕНО | 7a3cb5e; BACKLOG «Дослідити»: «досліджено, жоден не знімає біль» | claude-mem/auto-memory досліджено
59 | ЗРОБЛЕНО | 040421f — tscribe як [unverified]-кандидат у «Дослідити» | tscribe занесено, не викинуто
60 | ВІДКЛАДЕНО | BACKLOG «Активні»: приватні Reels (Kiwi + yt-dlp cookies) | приватні акаунти Reels — відкрито
61 | ЗРОБЛЕНО | f45b24c (правило); практика — TROUBLES «відмовні режими deepseek» 23.09, «Ціна інструмента» 26.09 | deepseek tool реально викликають
62 | ЗРОБЛЕНО | 8ef6c8a, c1b734d; TROUBLES «SessionStart-хук підтверджено (20.09)» | фікс grep/find перевірено трьома командами
63 | ВІДКЛАДЕНО | конфлікт хуків — BACKLOG «Дослідити» («не досліджувалось»); рядок DeepSeek — TROUBLES 23.09 (22 виклики) | перевірка конфлікту хуків — досі немає
64 | ЗРОБЛЕНО | 3bb1a4b — CONTEXT/TROUBLES/BACKLOG за результатами сесії після 623f122 | checkpoint після 623f122 зроблено
65 | НЕЯСНО | CONTEXT.md не серед наданих файлів; у gitlog/журналах рішення не видно | TRASH/USER_PROFILE у «Навігації» — не звірити
66 | ЗРОБЛЕНО | 71ef592, 09c9be7 — хук-нагадування request-brief (автозапуск) | request-brief дійшов до хука
67 | ДУБЛЬ (60) | baton #34 | повтор приватних Reels
68 | ВІДКЛАДЕНО | BACKLOG «Дослідити» → ECC: «окремі ідеї, не весь пакет» | ECC/Hermes ідеї — відкладені
69 | ВІДКЛАДЕНО | BACKLOG «Дослідити» «Розбіжність хуків…» + «Відкриті рішення» (1) | y/n у блоці делегатора/хуку — відкрито
70 | ЗРОБЛЕНО | 3bb1a4b — CONTEXT.md і TROUBLES.md закомічено | коміт CONTEXT+TROUBLES зроблено
71 | ЗРОБЛЕНО | обидва пункти є в BACKLOG «Дослідити» (аудит скілів; розбіжність хуків) | пропоновані пункти записано
72 | ДУБЛЬ (60) | baton #35 | повтор приватних Reels
73 | ВІДКЛАДЕНО | BACKLOG «Активні»: нагадування викликати baton_pick_up | baton_pick_up на старті — нагадування живе
74 | ЗАБУТО | не знайдено; шукав «session-close крок 3», «хто редагує CONTEXT.md» | розбіжність про редагування CONTEXT.md
75 | ВІДКЛАДЕНО | BACKLOG «Дослідити»: обидва розділи живі, статуси «не робилось»/«не досліджувалось» | аудит скілів і хуки — у «Дослідити»
76 | ДУБЛЬ (60) | baton #36 | повтор приватних Reels
77 | ЗРОБЛЕНО | BACKLOG «Налаштування каналу…» 21.09 — автор/правила підтверджено; 11957b5 | питання 4/10 закрито користувачем
78 | ЗРОБЛЕНО | 11957b5 — профіль каналу історій; TROUBLES «Субтитри в файл через yt-dlp» | референси й SAVED PROFILE видано
79 | ЗРОБЛЕНО | e92f85c — AGENT.md + BACKLOG + TROUBLES | коміт script-agent без agent.py
80 | ВІДКЛАДЕНО | BACKLOG «Дослідити»: «Відео і звук… відкладено» (статус 21.09 — довідка) | тема птахів — довідка, не в роботі
81 | ДУБЛЬ (60,73) | baton #37–#40 | повтор «Активних» переліком
82 | ДУБЛЬ (80) | baton #38 | повтор теми відео/звуку
83 | ВІДКЛАДЕНО | BACKLOG «Дослідити»: «Наступні кроки (1) тестовий сценарій 8–10 хв» | тестовий сценарій так і не зроблено
84 | ВІДКЛАДЕНО | BACKLOG «Аналізатор винесено в reference-analyzer/»: «ще не зроблено» | ANALYZER.md під історії — не дороблено
85 | ВІДКЛАДЕНО | BACKLOG «Наступні кроки (3)»: назва каналу, PACING, AUTHOR PERSONALITY | поля профілю не підтверджено
86 | ЗРОБЛЕНО | 7a86726 — блокуючий хук rm/rmdir → TRASH.md | хук rm/rmdir → TRASH.md зроблено
87 | ЗРОБЛЕНО | a9d2938 — git add → git status + блок agent.py | хук git add → git status зроблено
88 | ВІДКЛАДЕНО | BACKLOG «Відкладено: Закинутий готель…» — не чіпати без запиту | «Закинутий готель» — заборонено чіпати
89 | ДУБЛЬ (73) | baton #43–#46 | повтор baton_pick_up
90 | ЗРОБЛЕНО | 7a86726; TROUBLES «Блокуючі хуки…» — 16/16 + живий rm | питання про спосіб хука закрито
91 | ЗРОБЛЕНО | aef5ef0; TROUBLES «Незалежна перевірка шаблону (22.09)» | незалежні джерела знайдено
92 | ЗРОБЛЕНО | 6143025/6150491; TROUBLES — тести на 7 входах (C1–C4) | improver перевірено на різних запитах
93 | ДУБЛЬ (88) | baton #44 | повтор «Закинутого готелю»
94 | ЗРОБЛЕНО | TROUBLES «Дрібні факти 23.09» (2.1.280) + «22 виклики DeepSeek, 0 помилок» | install 2.1.280 + тест deepseek
95 | ДУБЛЬ (88) | baton #45 | повтор «Закинутого готелю»
96 | ЗРОБЛЕНО | TROUBLES «Claude-Session у комітах вимкнено (26.09)»; 851a9ac | атрибуцію вирішено: Claude-Session прибрано
97 | ЗАБУТО | не знайдено; шукав «окупається», «перевір ще раз», «перечитування позначок» (лише TROUBLES 23.09) | оцінка опори/claimcheck за кілька сесій
98 | ВІДКЛАДЕНО | BACKLOG «Дослідити» → E5-хук: «перед будівництвом знайти 2–3 сесії» | E5-хук чекає старих сесій
99 | ЗРОБЛЕНО | 88cd9ed, 02f3f6b; BACKLOG «Завершено» 24.09 — flash скрізь | ціни pro/flash звірено, дефолт flash
100 | ВІДКЛАДЕНО | BACKLOG «Дослідити» → «Встановити grill-me і claude-setup» | claude-setup уточнено, не встановлено
101 | ДУБЛЬ (96) | baton #46–#48 | повтор теми атрибуції
102 | ДУБЛЬ (88) | baton #46 | повтор «Закинутого готелю»
103 | ЗРОБЛЕНО | BACKLOG «Дослідити»: уточнення користувача 24.09 — плагін-аудитор | який claude-setup — з'ясовано
104 | ЗАБУТО | не знайдено; шукав «skillOverrides», «скіл плагіна» (лише TROUBLES «НЕ перевірено») | skillOverrides для скілів плагіна не перевірено
105 | ВІДКЛАДЕНО | BACKLOG «Дослідити» → «classify-task.sh: правило довжини розходиться з RULES.md» | хук-підказка vs RULES.md — відкрито
106 | ЗРОБЛЕНО | a008ff1; BACKLOG «Завершено» 24.09 — не потрібен | claude-anthropic.sh закрито рішенням
107 | ЗРОБЛЕНО | 02f3f6b, 88cd9ed; BACKLOG «Завершено» 24.09 | роутинг: flash скрізь
108 | ЗРОБЛЕНО | a851609; TROUBLES «Дефолт делегування…» — managed-блок виправлено | застарілі доки цін — вирішено
109 | ДУБЛЬ (98) | baton #47–#49 | повтор E5-хука
110 | ДУБЛЬ (100) | baton #47–#49 | повтор claude-setup/grill-me
111 | ДУБЛЬ (88) | baton #47–#49 | повтор «Закинутого готелю»
112 | ДУБЛЬ (73) | baton #47–#49 | повтор baton_pick_up
113 | ЗРОБЛЕНО | 9ba2e1f (.gitignore), 35f46a5 (CONTEXT), 3299845 (BACKLOG), 58bee72 (TROUBLES) — окремо, 25.09; TROUBLES «git revert не має -q» | доки закомічено окремими комітами
114 | ЗРОБЛЕНО | dfed51e; BACKLOG «Завершено» 24.09 — «лишити як є» | важіль мислення — пункт закрито
115 | ВІДКЛАДЕНО | BACKLOG «Активні» → «Полагодити claimcheck» (план G1–G5); TROUBLES 24.09 | claimcheck: фікс вибору сесії чекає
116 | ДУБЛЬ (106) | baton #49 | повтор claude-anthropic.sh
117 | ЗРОБЛЕНО | 69ecdde — план claimcheck + розбір витрат сесії | коміт BACKLOG/TROUBLES зроблено

Підсумок за статусами (1–117): ЗРОБЛЕНО — 44; ВІДКЛАДЕНО — 27; ДУБЛЬ — 37; ЗАБУТО — 6; НЕЯСНО — 3. Разом 117.

ЗАБУТО (6):
- №1 — тест повної передачі стану (baton) між Claude і DeepSeek; шукав «handoff», «Claude and DeepSeek», «тест».
- №18 — верифікація session-timer.sh на кількох реальних ходах в UI; шукав «session-timer», «UI», «ходи».
- №57 — проба unlazy --bind на реальній кодовій задачі; шукав «--bind», «кодова задача» (лишився лише план у TROUBLES «Toil + Shelfware»).
- №74 — розбіжність кроку 3 session-close («не редагуй CONTEXT.md сам») із бажанням користувача; шукав «session-close крок 3», «хто редагує CONTEXT.md».
- №97 — оцінка за кілька сесій, чи окупається правило опори й claimcheck; шукав «окупається», «перевір ще раз», «перечитування позначок».
- №104 — чи діє skillOverrides на скіли плагіна; шукав «skillOverrides», «скіл плагіна» (у TROUBLES лише позначка «НЕ перевірено»).

ЗВІТ · інстр: Read 10, Grep 0 (інструмента Grep у цьому середовищі немає — читав файли повністю, пошук робив по прочитаному) · файли: прочитано 5 (vanished.txt, BACKLOG.md, TROUBLES.md, gitlog.txt, tree.md) / записано 0 · відповідь ≈ 1900 слів · токени: не рахую — див. журнал

---

Звірку зроблено з урахуванням done.txt. Одразу фіксую: №18 (порція 1) — ЗРОБЛЕНО (done.txt 21–24: «session-timer.sh hook created and verified live in UI» + EMA-прогноз); решта 5 ЗАБУТО першої порції підтверджені.

N | статус | доказ (хеш / розділ / шукані слова) | 5–10 слів суті

118 | ВІДКЛАДЕНО | BACKLOG «Активні» → «Полагодити claimcheck… (2026-09-24)», план G1–G5; done.txt 147 «код відкладено» | фікс вибору сесії claimcheck — відкладено
119 | ВІДКЛАДЕНО | BACKLOG «Активні» → «Auto mode у DeepSeek-сесіях — чи користуватись» | auto mode у DeepSeek-сесіях — відкрито
120 | ЗРОБЛЕНО | tree.md П4 (хук мовчить за ANTHROPIC_BASE_URL=deepseek; бекап .bak-20260926-201310; рядок SKIP наживо); fa17666 | хук «Делегуй на DeepSeek» мовчить у DeepSeek-сесіях
121 | ЗРОБЛЕНО | 27ab365; done.txt 154 — «Оновлення 2026-09-24 (друга і третя сесії)» | CONTEXT.md: оновлення 24.09
122 | ДУБЛЬ (№88, порція 1) | BACKLOG «Відкладено: Закинутий готель…» | повтор «не чіпати готель»
123 | ВІДКЛАДЕНО | BACKLOG «Активні» — нагадування baton_pick_up; effort max у deepseek-mcp — TROUBLES «НЕ перевірено» | baton_pick_up живе; effort medium — без запису
124 | ВІДКЛАДЕНО | BACKLOG «Активні» → «Зменшити, що вантажиться на старті»: кроки 1–2 є, спосіб baton не обрано | стартове навантаження — не завершено
125 | ДУБЛЬ (118) | той самий план у BACKLOG «Активні» | повтор фіксу claimcheck
126 | ДУБЛЬ (119, 120) | — | auto mode + хук — ті самі два
127 | ДУБЛЬ (121) | — | повтор CONTEXT 24.09
128 | ДУБЛЬ (№88, порція 1) | — | повтор «готель»
129 | ВІДКЛАДЕНО | BACKLOG «Активні» — «спосіб скорочення baton НЕ обрано» (3 варіанти) | вибір способу скорочення baton
130 | ЗРОБЛЕНО | 8b07ad0 (RULES-WHY.md + guard), 6b74092; done.txt 121, 231 (пам'ять закріплено) | історія правил у RULES-WHY; пам'ять закріплено
131 | ВІДКЛАДЕНО | BACKLOG «Дослідити» → «Встановити grill-me і claude-setup»: «наступний крок — прочитати код audit-setup»; done.txt 149 | код audit-setup ще не читано
132 | ЗАБУТО | не знайдено; шукав «PROTOCOL.md», «RULES-WHY», «група 2» — рішення немає; повтори під №194, 200 | формулювання PROTOCOL.md у check-links не вирішено
133 | ЗРОБЛЕНО | 27ab365; done.txt 154 | CONTEXT.md «Оновлення 2026-09-24»
134 | ДУБЛЬ (129) | — | те саме питання про baton
135 | ДУБЛЬ (№105, порція 1) | BACKLOG «Дослідити» → classify-task.sh | хук vs правило — те саме
136 | ВІДКЛАДЕНО | BACKLOG «Активні» → «Аудит проєкту» (повтори 143, 147, 155, 167, 176, 182) | аудит проєкту — так і не зроблено
137 | ДУБЛЬ (129) | — | повтор baton
138 | ДУБЛЬ (130) | — | повтор частин B/C
139 | ДУБЛЬ (131) | — | повтор audit-setup
140 | ДУБЛЬ (132) | — | повтор PROTOCOL.md
141 | ДУБЛЬ (118, 121) | — | повтор claimcheck + CONTEXT
142 | ЗРОБЛЕНО | 719a832, c236ebb, 71154c2 (v1 2/4 → v2 4/4); BACKLOG «Верифікатор…» — «план виконано повністю» | верифікатор, етап 1 бектест — зроблено
143 | ДУБЛЬ (136) | — | повтор аудиту проєкту
144 | ДУБЛЬ (129) | — | повтор baton
145 | ДУБЛЬ (130) | — | повтор B/C
146 | ДУБЛЬ (132, 118) | — | повтор PROTOCOL + claimcheck
147 | ДУБЛЬ (136) | — | повтор аудиту (з verify-before-show)
148 | ДУБЛЬ (129, 130) | — | повтор baton + RULES.md
149 | ВІДКЛАДЕНО | BACKLOG «Дослідити» → FreeLLMAPI та «Resets — Reset for free» | FreeLLMAPI/Reset for free — у черзі
150 | ДУБЛЬ (118) | — | повтор claimcheck
151 | ЗРОБЛЕНО | d8c356c — improver на DeepSeek flash (ліміт claude.ai не витрачається); TROUBLES «Хук improver: ціна…» | переписувач знято з Opus — ліміт не їсть
152 | ЗРОБЛЕНО | TROUBLES «Перемикач провайдера…» + «Живий показ delegate на NVIDIA»; done.txt 168 | після перезапуску — статус і живий виклик NVIDIA
153 | ЗРОБЛЕНО | BACKLOG «Відкриті рішення…» (3) — «запушено «як є» за рішенням користувача»; done.txt 206 | push комітів вирішено користувачем
154 | ВІДКЛАДЕНО | BACKLOG «Активні» → «A/B хука-переписувача»: лишилось — чи потрібен агенту deepseek | A/B переписувача — лишилось питання
155 | ДУБЛЬ (136) | — | повтор аудиту
156 | ДУБЛЬ (129, 118, 132) | — | збірка: baton + claimcheck + PROTOCOL
157 | ДУБЛЬ (153) | — | повтор питання про push
158 | ДУБЛЬ (154) | — | повтор переписувача
159 | ДУБЛЬ (129) | — | повтор baton
160 | ЗРОБЛЕНО | BACKLOG «Активні» → «Основний провайдер delegate»: зроблено — BazaarLink, NVIDIA запасний; 053ed57, 972b9b3; done.txt 181 | основний провайдер — BazaarLink
161 | ВІДКЛАДЕНО | BACKLOG «Активні» → «Node keep-alive… Рішення користувача»; TROUBLES «не зроблено» | фікс keep-alive не зроблено
162 | ЗРОБЛЕНО | TROUBLES «Безкоштовний DeepSeek… BazaarLink»: 757 слів укр., 0 символів �; done.txt 181 | UTF-8 3.0.1 перевірено наживо
163 | ЗРОБЛЕНО | BACKLOG «Відкриті рішення…» (3); done.txt 206 (push 3d353be..09ec8de — попередні вже на origin) | push 7 комітів — питання закрито
164 | ЗРОБЛЕНО | 35f46a5; done.txt 187 | CONTEXT.md оновлено (25.09)
165 | ВІДКЛАДЕНО | BACKLOG «Дослідити» → FreeLLMAPI: «далі — пробний запуск у ~/freellmapi» | проба FreeLLMAPI не робилась
166 | ВІДКЛАДЕНО | BACKLOG «Активні» → «RULES.md: пошук у тригерах delegate» | «пошук» у тригерах — не вирішено
167 | ДУБЛЬ (136) | — | повтор аудиту
168 | ДУБЛЬ (160) | — | повтор провайдера
169 | ДУБЛЬ (154) | — | повтор переписувача
170 | ВІДКЛАДЕНО | BACKLOG «Дослідити» → Reset for free: «яку частину скидає наша картка — не видно» | картка Reset for free — чекає користувача
171 | ВІДКЛАДЕНО | BACKLOG «Активні» → «provider-switch.py: додати bazaarlink» | bazaarlink у перемикачі — не додано
172 | ВІДКЛАДЕНО | місце зроблено — TROUBLES «Freebuff у ~/freebuff», done.txt 189; freebuff-mcp — BACKLOG «Дослідити» → Freebuff | Freebuff перенесено; freebuff-mcp не перевірено
173 | ЗРОБЛЕНО | BACKLOG «Відкриті рішення…» (3) — «10 комітів 26.09 запушено «як є» за рішенням користувача» | push 10 комітів — за рішенням користувача
174 | ЗРОБЛЕНО | 8597f40; done.txt 209 | CONTEXT.md оновлено (26.09)
175 | ДУБЛЬ (161) | — | той самий keep-alive
176 | ДУБЛЬ (136) | — | повтор аудиту
177 | НЕЯСНО | можливий слід — TROUBLES 26.09 (третя перевірка): правило every-proposal-ends-with-recommended-question у пам'ять; файли пам'яті поза наданими | урок «який пункт мав запитати» — не звірити
178 | ВІДКЛАДЕНО | BACKLOG «Активні» → «Розширити session-close»: «лишилось — прибирання, повторне закриття, журнал рішень, межа» | session-close розширено частково
179 | ДУБЛЬ (171) | — | повтор provider-switch
180 | ДУБЛЬ (172) | — | повтор freebuff-mcp
181 | ДУБЛЬ (166) | — | повтор «пошук» у тригерах
182 | ДУБЛЬ (136) | — | повтор аудиту
183 | ЗРОБЛЕНО | BACKLOG «Дослідити» → Jules (доку прочитано, пробу зроблено; 759d198, d39dc45); done.txt 192 | можливості Jules з'ясовано, проба є
184 | ЗРОБЛЕНО | BACKLOG «Відкриті рішення…» (3); done.txt 206 | push комітів відбувся
185 | ДУБЛЬ (178) | частину зроблено — 73a24ec (/cost+effort), b5815ac (статуслайн) | решта session-close лишається
186 | ДУБЛЬ (171) | — | повтор provider-switch + запасний
187 | ДУБЛЬ (172) | — | повтор freebuff-mcp
188 | ДУБЛЬ (166) | — | повтор «пошук»
189 | ЗРОБЛЕНО | 0009e6b (злито PR #1); done.txt 206 — push 3d353be..09ec8de після PR | розбіжність з origin усунено (rebase+push)
190 | ВІДКЛАДЕНО | BACKLOG «Активні» → «Браузер на телефоні під керуванням агента» (план: окрема сесія) | браузер на телефоні — не почато
191 | ЗРОБЛЕНО | 8597f40; done.txt 209 | CONTEXT.md оновлено (26.09)
192 | ВІДКЛАДЕНО | BACKLOG «Дослідити» → Jules: «далі — давати Jules інші вузькі задачі з тестами» | наступні задачі Jules — у черзі
193 | ДУБЛЬ (171) | — | повтор provider-switch
194 | ДУБЛЬ (132) | — | повтор PROTOCOL.md (група 2)
195 | ЗРОБЛЕНО | done.txt 206 — push 3d353be..09ec8de (охоплює 0ff55f8 «розбір уроків») | коміт BACKLOG запушено
196 | ЗРОБЛЕНО | 73a24ec (кроки 3.9/3.10), b5815ac (статуслайн); BACKLOG — «зроблено два забуті кроки» | /cost+effort і зовнішня перевірка у session-close
197 | ВІДКЛАДЕНО | BACKLOG «Активні» → «Перевірка засвоєння уроків — крок або скіл»: «Не створено — рішення користувача» | скіл/крок перевірки уроків не створено
198 | ДУБЛЬ (190) | — | повтор браузера на телефоні
199 | ДУБЛЬ (191) | — | повтор CONTEXT
200 | ДУБЛЬ (132) | — | повтор PROTOCOL.md
201 | ЗРОБЛЕНО | 8597f40; done.txt 209 | CONTEXT.md «Оновлення 2026-09-26»
202 | ВІДКЛАДЕНО | BACKLOG «Активні» → «Розширити session-close»: «наступний крок після тижня спостереження — Stop-хук 40/65%» | Stop-хук порогів — після тижня спостереження
203 | ВІДКЛАДЕНО | BACKLOG «Активні» → «Розширити session-close»: «Лишилось: tmp/бекапи, повторне закриття, журнал рішень, межа» | решта session-close — живе
204 | ДУБЛЬ (197) | — | повтор перевірки уроків
205 | ДУБЛЬ (190) | — | повтор браузера
206 | ДУБЛЬ (190) | — | повтор браузера
207 | ДУБЛЬ (202) | — | повтор Stop-хука
208 | ДУБЛЬ (203) | — | повтор решти session-close
209 | ВІДКЛАДЕНО | BACKLOG «Активні» → troubles-grep-hook: теги для пам'яті — «не робимо» (1f88bb7); живе — блокуюча перевірка confirm-before-lossy-edits (be89aff) | troubles-grep по пам'яті — «ні»; інші варіанти живі
210 | ВІДКЛАДЕНО | BACKLOG «Активні» → «check-links — «далі» з baton має бути в BACKLOG», «окремою сесією» | check-links для baton next — не почато
211 | ЗАБУТО | WEEKLY.md зроблено (67985e7; done.txt 210–211), але рішення про регулярність немає; шукав «WEEKLY», «регулярно», «тижневий відбір» | чи робити тижневий відбір регулярно
212 | ДУБЛЬ (190) | — | повтор браузера
213 | ВІДКЛАДЕНО | BACKLOG «Активні» → «Черга з сесії 2026-09-26» (1) дерево задач; tree.md — проба триває (T4/T5) | дерево задач — у роботі
214 | ВІДКЛАДЕНО | BACKLOG «Активні» → «Проба «картки» в TROUBLES… Нова сесія» | картки TROUBLES — не робились
215 | ВІДКЛАДЕНО | BACKLOG «Активні» → «Черга з сесії 2026-09-26» (2)(3)(4) | складність/охоронець/зір — у черзі
216 | ВІДКЛАДЕНО | (1) закрито — cd3c922; (2) живе — BACKLOG «Відкриті рішення…» (2), до ~03.10 | «спершу питати» в RULES — після проби
217 | ДУБЛЬ (210) | — | повтор «далі» з baton
218 | ЗРОБЛЕНО | 8597f40; done.txt 209 | CONTEXT.md — оновлення 26.09
219 | ЗРОБЛЕНО | cd3c922 (правило + RULES-WHY); BACKLOG «Відкриті рішення…» — «Рішення (1): платне — завжди питати» | платні виклики — завжди з дозволу
220 | ВІДКЛАДЕНО | BACKLOG «Активні» → «Відкриті рішення…» (2) — відкладено до підсумку проби | «спершу питати» в RULES.md — відкладено
221 | ЗРОБЛЕНО | TROUBLES «Claude-Session у комітах вимкнено (2026-09-26)» (sessionUrl:false); 851a9ac; done.txt 225 | Claude-Session прибрано з майбутніх комітів
222 | ЗРОБЛЕНО | BACKLOG «Активні» → «Проба ask-правил»: «ПРОБУ ЗАПУЩЕНО»; done.txt 224 (три замки наживо) | обрано ask-правила; пробу запущено
223 | ВІДКЛАДЕНО | (1)(3) закрито — cd3c922, 851a9ac; (2) живе — BACKLOG «Відкриті рішення…» (2) | з трьох рішень лишилось «спершу питати»
224 | ЗРОБЛЕНО | d7a0f47; TROUBLES «$0.50 закрито — помилка пам'яті, не списання» | $0.50 — питання закрито користувачем
225 | ДУБЛЬ (214, 215) | — | повтор картки + черги
226 | ДУБЛЬ (210) | — | повтор «далі» з baton
227 | ЗАБУТО | TROUBLES «Пропущене в сесії… effort max у deepseek-mcp» — «НЕ перевірено»; живого пункту немає; шукав «effort max», «env.js», «ціна deepseek» | вплив effort max на ціну deepseek
228 | ВІДКЛАДЕНО | tree.md — T4 (критерії записано ДО старту, «ПЛАТНО — окреме «так»»); тека agents/deepseek-search/ не створена | проба deepseek-search (T4) — чекає «так»
229 | ВІДКЛАДЕНО | замок на deepseek-reply — зроблено (b25efc2; done.txt 234); «так» на формат картки — tree.md «Поза деревом (черга рішень)» | замок є; формат картки — у черзі
230 | ЗРОБЛЕНО | 8597f40; done.txt 209 | CONTEXT.md — оновлення 26.09
231 | ВІДКЛАДЕНО | BACKLOG «Активні» → «Проба ask-правил»: підсумок ~2026-10-03 + рішення (2) | підсумок проби ask-правил — попереду
232 | ЗРОБЛЕНО | b25efc2; BACKLOG «Активні» — «діру закрито… .bak-20260926-211810»; done.txt 234 | deepseek-reply у ask-замку
233 | ВІДКЛАДЕНО | tree.md — критерій T4 «claudeMdExcludes діє» (T2: «висновком → перевірити в T4») | claudeMdExcludes — перевірка в T4

Підсумок за статусами (118–233): ЗРОБЛЕНО — 28; ВІДКЛАДЕНО — 33; ДУБЛЬ — 51; ЗАБУТО — 3; НЕЯСНО — 1. Разом 116.
Разом із першою порцією (з поправкою №18 → ЗРОБЛЕНО): ЗРОБЛЕНО 45, ВІДКЛАДЕНО 60, ДУБЛЬ 88, ЗАБУТО 8, НЕЯСНО 4.

ЗАБУТО (3):
- №132 — check-links: формулювання PROTOCOL.md (файл пакета baton, не репо) у RULES-WHY.md; шукав «PROTOCOL.md», «RULES-WHY», «група 2»; повтори під №194, 200.
- №211 — чи робити тижневий відбір регулярно (WEEKLY.md); шукав «WEEKLY», «регулярно», «тижневий відбір» — підсумок один раз зроблено (67985e7), рішення про регулярність немає.
- №227 — чи effort max у deepseek-mcp (env.js) впливає на ціну на DeepSeek; шукав «effort max», «env.js», «ціна deepseek» — лишився позначкою «НЕ перевірено» в TROUBLES.

Закономірність: губляться не «справи», а мікро-питання типу «перевірити/вирішити» — ті, що не мають файла-носія (жодного коміту, жодного рядка в BACKLOG «Активні»/«Дослідити»), сформульовані як openQuestions/«далі» в момент швидкого запису батна наприкінці сесії і виглядають занадто дрібними, щоб заводити запис; усе, що отримало механізм (хук, скіл, крок session-close, рядок у BACKLOG), виживає навіть при десятках повторів (tscribe, chrome-bridge, аудит проєкту), а що мало лише «якір-умову» («коли користувач захоче», «після X») — зникає, якщо умову не продубльовано в BACKLOG (у першій порції так загинули тест handoff і проба unlazy --bind, тут — PROTOCOL.md, WEEKLY, effort-ціна; при цьому №18 насправді було виконано, просто ніде не записано, тож «забуте» часто означає «не задокументоване»); окремо видно, що 51 із 116 пунктів другої порції (44%) — чисті повтори вже наявних пунктів, тобто список «далі» роздувається копіюванням, а не роботою — саме проти цього й заведено пункт «check-links — «далі» з baton має бути в BACKLOG» (#210), який досі не виконано.

ЗВІТ · інстр: Read 11, Grep 0 (інструмента Grep немає — читав файли повністю) · файли: прочитано 6 (vanished.txt, done.txt, BACKLOG.md, TROUBLES.md, gitlog.txt, tree.md) / записано 0 · відповідь ≈ 2000 слів · токени: не рахую — див. журнал
