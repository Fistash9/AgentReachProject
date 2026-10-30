# Система › хуки › що злити, що розділити (під-агент claude-code, 29.10; лише читання)
Опори: settings.local.json (hooks), докстрінги 24 .py (23 хуки + statusline-cost.py), grep, журнали .claude/logs.
На кожен Bash — 12 процесів PreToolUse (8 в одному блоці + install-check, edit-gate, verify-nudge, proc-guard).

## A. Суперечності
1. Stop-голос «питання без кнопок» ↔ ask-gate. answer-gate-shadow:333 (ask), ASK_REASON :432 «Постав віконцем… рядок Черга» — про звірку й записи ні слова. ask-gate:114–120 далі вимагає verify/records, а для механізмів «Звірка не потрібна» не приймає (:116, :39). Журнал a11c12e0: 16:33:36 Stop-голос queue+ask → 16:33:42 deny [verify,records], 16:40:00 deny [verify]. За 29.10: 52 віконця, 11 deny. Що саме спрацювало: verify ловить будь-яке «план\w*» (RE_PLAN_Q answer-gate:60) чи RE_CHANGE, records — «бриф/план» (ask-gate:119); текст самих питань 16:33/16:40 не дивився [не перевірено].
2. Ворота «агенти» v2 ↔ пряме питання користувача. edit-gate:390–393: причина приймається лише за RE_WL_CLOSE/CHECK/EDIT; «читання для звіту» не має «перевір|звір» → deny. Людське повідомлення знімає вимогу лише як закриття (RE_CLOSE_H :394). Діагноз DIAG.md:31–33 (К1–К3: причину шукають лише в description; гілка C раніше за білий список; git через .match).
3. Подвійні «агенти»: Stop-голос agents (answer-gate:34–37) + deny edit-gate — два пороги, дві фрази обходу («Агентів не запускаю:» проти «без агента:»).

## B. Дублі
- strip_heredocs ×5: git-add-status:31, install-check:53, request-brief:52, rules-why:49, trash-md:35; HEREDOC_START_RE ×4; segments ×2 (install-check:68, rules-why:68); shlex у 6 хуках.
- Розбір журналу сесії: transcript_path читають 10 хуків; is_real_user/iter_turns/current_turn_lines ×2 (answer-gate:243/262/366, number-claim:228/238/293) — баг task-notification (TROUBLES:4996) треба лікувати двічі; last_decision ×2 (commit-consent:129, request-brief:184).
- «Що далі» — 5 носіїв: GOALS «Зараз» (:16), BACKLOG «Активні» вгорі, baton next, tree-focus-hook (кожне повідомлення), focus-tree.py.
- Черга перевіряється тричі: tree-focus (підказка), answer-gate queue (Stop), ask-gate queue (deny).

## C1. Злити
- hooklib.py: strip_heredocs/segments/last_decision/transcript-читач. Виграш: −5 копій, один фікс бага. Ризик: помилка імпорту гасить усі (fail-open прихує). Перевірка: tools/hooks-smoke.py до/після + бектест на старих журналах.
- Один диспетчер PreToolUse Bash замість 12 процесів. Виграш: менше старту python [час не перевірено]. Ризик: один збій = всі замки. Перевірка: заміряти time на фіктивному stdin.
- Одна «політика питання»: ask-gate і Stop-голос ask беруть вимоги з одного місця; ASK_REASON перелічує всі умови ask-gate. Перевірка: прогін ask-gate.jsonl 29.10 (11 deny) симуляцією.

## C2. Розділити
- За роллю: замки deny (trash-md, git-add, commit-consent, rules-why, proc-guard, personal-guard) — окремо від підказок (troubles-grep, verify-nudge, install-check, request-brief, free-answer) і голосів Stop. Правило: підказка/голос не можуть вимагати дії, яку замок блокує.
- За напрямами GOALS: якість C (answer-gate, number-claim, ask-gate, edit-gate), пам'ять A (baton-guard, baton-reminder, tree-focus), агенти/делегати (delegate-*, personal-guard).
- edit-gate (620 рядків, 3 ролі: паспорт, ворота 3, агенти) розділити на файли.

## [не перевірено]
Час запуску 12 хуків; чи pkgtruth дублює install-check; чи всі 5 strip_heredocs ідентичні.
