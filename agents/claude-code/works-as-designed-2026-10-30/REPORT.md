# Що працює як задумано і має алгоритм — 2026-10-30 [claude-code, субагент]
Ціль: відповісти «що з системи має алгоритм і працює за задумом» → вузол yakist-roboty-agentiv Q4. Джерело: tools/parts-passport.py (журнали 272 осн. + 221 субагентних) + .claude/logs + trees/. Лічильники — зі скрипта/wc/grep цієї сесії.

## А. Алгоритм є, працює за задумом — 13 хуків/скриптів з логом ≥7 днів
- Ворота перед питанням ask-gate: 679 записів, 293 за 24–30.10; v2 зняло 15 хибних на 1643 питаннях, справжніх зниклих 0 (trees/yakist-roboty-agentiv.md:639).
- plain-ask (293/7д), answer-gate-shadow (387/7д), node-label-shadow (304/7д), number-claim-shadow (455/7д) — тіньові: пишуть лог, не блокують.
- commit-consent (97/7д), edit-gate (142/7д), free-answer (50/7д), personal-guard (76/7д), delegate-outcome-logger (76/7д).
- Скрипти, які викликають скіли/хуки: check-links 122, hooks-smoke 102 (поломок 0, trees/derevo-i-golograma.md:296), baton-diff 77, claimcheck 63, deepseek-search 93; скіли verify-before-show, session-close, deepseek-search, request-brief, unlazy, llm-council, grilling використовуються.
- statusline-cost 13849 викликів.
## Б. Алгоритм є, але не за задумом
- Ворота «агенти» — хибних 7+ на пробі, рішення відкладене (yakist:639); лишилось 4 хибні класи ворін питань (напр. «Записи переглянуто:»).
- edit-gate правило C: з 4 спрацювань 2 хибні (yakist:577).
- Тіньові ворота: точність ≈44–57 % (yakist:759) — тому лише тінь, не блок.
- delegate: 99 PostToolUseFailure з 365 записів у delegate-calls.jsonl.
- delegate-prompt-improver: останній запис 23.10, rewrite через NVIDIA ok=false; 8 невдач у improver.log.
## В. Алгоритм є, 0 викликів
- Скрипти: commit-node-check.py (git-хук, лог не ведеться — ймовірно хибний «0»), deepseek-thinking-proxy.py, mechanisms-backtest-2026-10-13.py (разовий).
- Скіл grill-me — 0 викликів.
- MCP: 37 з 67 без викликів у журналах.
- Не вимірюється (8 хуків без логу): baton-guard, baton-reminder, cost-nudge, git-add-status, request-brief-reminder, rules-why-guard, trash-md-guard, troubles-grep — можуть працювати, доказу нема. Також 53 вузли trees/ і 5 пісочниць не вимірюються.
## Г. Лише текст, без алгоритму (grep назв у .claude/hooks/*.py: 0 збігів)
- Premortem перед нетривіальною дією; перевірка «bypassPermissions для deepseek»; бекап .bak перед зміною файлів поза git; рівні знань Sourced/Unverified (лише побічні згадки); «одна дія — одне повідомлення»; рівні effort/модель під-агента (лише згадка в tree-focus); перевірка пакета перед рекомендацією (є install-check, але лише на встановлення).
- Частково з хуком: TRASH, git add, коміт, RULES-WHY, baton_pass, push — А/без логу.
Обмеження: «за 7 днів» — за рядками з датою у логах; влучність відома лише для частини воріт; кошик Г не вичерпний (grep по 8 розділах, не по кожному рядку).
