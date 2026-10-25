# scout-povidomlennya-stop — звіт розвідника (обхід системи, 25.10, Explore/sonnet)

Розвідка UserPromptSubmit і Stop хуків. Файли не змінював, хуки не запускав (лише cat, sed, grep, ls, читання журналу цієї сесії 4cab3538). Реєстрація в `.claude/settings.local.json`: UserPromptSubmit рядки 277-299 (3 хуки), Stop рядки 45-65 (4 хуки). Усі 7 пройдені. Позначка «живцем» означає, що факт підтверджено записом у журналі цієї сесії.

1) ЛАНЦЮЖКИ (скорочення: tf = tree-focus-hook.py, ag = answer-gate-shadow-hook.py)
- Повідомлення → tf (settings:282) → stdin JSON (tf:316) і поле prompt (tf:403, рілс-посилання дає підказку). Далі:
  - glob `trees/*.md`, розбір [>] і [?] (tf:328, 96-108);
  - `git status --porcelain` через subprocess (tf:143);
  - `tmux list-windows` і `capture-pane` вікна dsh (tf:297, 303);
  - stdout additionalContext (tf:431-433). Живцем: 22 записи `hook_additional_context` для UserPromptSubmit, 21 з них «В роботі: …».
- Той самий tf на SessionStart (settings:39) додатково читає `GOALS.md` (tf:219), memory-файли «How to apply:» (tf:164) і `.claude/active-tree` (tf:416). Усі три файли існують.
- Повідомлення → `baton-guard-hook.py` (settings:290) → читає `.baton/ledger.jsonl` (baton-guard:43, 58) → double_pickup (:54) → ⚠ у additionalContext (:151-158). Ledger пише зовнішній сервер baton: `appendLedger` у копії `tools/verifier-backtest/sources/baton-server.mjs.txt:36`. Сам хук нічого не пише і логів не має.
- Той самий файл на інших подіях (поза моєю ділянкою): PreToolUse імпортує `tools/baton-diff.py` через spec_from_file_location (:92), PostToolUse запускає `tools/handoff-view.py` через subprocess (:168) і пише `.baton/HANDOFF-view.md`.
- Повідомлення → `cost-nudge-hook.py` (settings:299) → читає `.claude/logs/session-cost.jsonl` (cost-nudge:22, 30) → читає і пише `cost-nudge-state.json` (:57, 66) → systemMessage і additionalContext (:72-80). Живцем: 💸 «$10.39» показано.
- Джерело цього логу: statusLine (settings:307) → `statusline-cost.py` дописує рядок (statusline-cost:66). Без ротації: 1,69 МБ, 10401 рядок.
- Кінець відповіді → `stop-hook.mjs` (settings:50) → імпортує `lib/gates.mjs`, `lib/dispatch.mjs` (stop-hook.mjs:7-10) → `resolveTarget` читає `.unlazy/*` (gates.mjs:621-670). Знаходить 4 теки: bash-request-brief, classify-task-fix, passport, q6. Файлів `<scope>/session` немає, тож гілка ambiguous (stop-hook.mjs:74-77) віддає лише systemMessage і не блокує. Живцем: 23 рази «unlazy: 4 pipelines … none bound to this session; not blocking».
- Кінець відповіді → `node-label-shadow-hook.py` (settings:55) → хвіст журналу сесії 64 КБ (node-label:66-81) → `tools/trees-index.py` через spec_from_file_location (:35) → `nodes()` по `trees/**/*.md` (:40-41) → рядок у `node-label-shadow.jsonl` (:110-116). stdout порожній, нічого не блокує.
- Кінець відповіді → `number-claim-shadow-hook.py` (settings:60) → ходи з `transcript_path` або `last_assistant_message` (number-claim:344-359) → рядок у `number-claim-shadow.jsonl` (:330-337). stdout порожній.
- Кінець відповіді → ag (settings:65) → `current_turn_lines` (ag:324) → `iter_turns` (:223) → `check` (:274) → `tools/plain-codes.py` через spec_from_file_location (ag:195-200, виклик :283) → `write_log` у `answer-gate-shadow.jsonl` (:410-419) → `{"decision":"block"}` у stdout (:~472) при voice. Живцем: 7 `hook_blocking_error` від Stop у цій сесії (5 «коди без назви», 1 «черга», 1 «бриф»).
- Зворотні ланки ag: його імпортують ask-gate-hook.py (:55-57, викликає `ag.iter_turns`, `RE_QUEUE`, `verify_in`) і verify-nudge-hook.py (:79, `ag.current_turn_lines`, `is_verify_call`). Стоп-хук, що веде PreToolUse-хуки. Також його вантажить `tools/hooks-smoke.py:357, 495`.
- ag читає в журналі записи `attachment/hook_additional_context` (ag:248). Це вихід інших хуків: «Захищений файл…» з verify-nudge-hook.py:180, «Ворота «перед правкою»» з edit-gate-hook.py:235 і 251, «request-brief» з request-brief-reminder-hook.py:307. Живцем вони справді лежать у журналі.
- Глобальні UserPromptSubmit-хуки (`~/.claude/settings.json:46, 54`; не з моєї ділянки, але стріляють на тій самій події): `classify-task.sh` пише `~/.claude/hook-test.log`, `session-timer.sh` пише `~/.claude/session-timer.{log,state,ema}`. State і ema читає лише сам session-timer.sh.

2) ГЛУХІ КУТИ (пишуть — ніхто не читає)
- Три тіньові логи `node-label-shadow.jsonl`, `number-claim-shadow.jsonl`, `answer-gate-shadow.jsonl`. Граф-пошук по py, mjs, js, sh, ts, json знайшов лише два зв'язки. `tools/parts-passport.py:283-299` лише рахує рядки для поля `calls` паспорта. `tools/hooks-smoke.py:145` пише тимчасовий лог через env, а не робочий. Ніхто не читає їх як дані, тож «спершу міряємо в тіні» (шапки хуків) без читача — ручний бектест.
- Виходи тіней: node-label 354 запуски, 3 з hits; number-claim 542 запуски, 171 із claims; ag 398 запусків, 59 з voice.
- `.claude/logs/dsh-line.jsonl` (tf:268, 380) файла нема. Нічого не читає навіть теоретично (grep по коду: лише tf). Вимір «проби 3 сесій» (BACKLOG:269) без даних.
- `.claude/active-tree` (tf:416-419): читають — ніхто не пише. Файл від 28.09 (git-tracked). Гілка спрацьовує лише при `not work` на SessionStart, зараз work непорожній.
- `cost-nudge-state.json`: читає лише сам cost-nudge-hook.py (:57). Приватний стан, нормально.
- `~/.claude/hook-test.log` (46004 рядки) і `session-timer.log` (2020 рядків): пишуть classify-task.sh і session-timer.sh. Читача в коді проєкту не знайшов. `~/.claude/hooks/test-hook.sh` не відкривав.
- baton-guard UserPromptSubmit-гілка нічого не логує: на паспорті `calls: null`.

3) ДУБЛІ
- `is_real_user`: ag:204-209 і number-claim:228-236, ідентична логіка.
- `iter_turns`: ag:223-271 і number-claim:238-285. Різні поля (events/hints проти ev/names), однаковий кістяк.
- `current_turn_lines`, читання хвоста блоками від кінця: ag:324-349 (256 КБ / 8 МБ) і number-claim:293-323 (1 МБ / 32 МБ). Третій читач хвоста: node-label `last_text` :66-81 (лише 64 КБ, без перевірки isMeta). Три незалежні читання одного журналу на кожен Stop.
- Ротація логу в `.1` (`os.replace(LOG, LOG + ".1")`): ag:412-413, number-claim:332-333, node-label:111-112. Пороги різні (2 МБ / 512 КБ / 512 КБ). Файлів `.1` зараз немає.
- Шапка ag про «iter_turns з number-claim-shadow-hook.py (той самий «хід»)» (:34) — це не імпорт, а копія.
- `strip_quoted`: number-claim:87-93 і `tools/claimcheck/claimcheck.py:31-37`. Свідома копія за коментарем «дзеркало claimcheck.py:27-33» (number-claim:84), номери рядків застаріли.
- Парсер вузла «- [x] ID назва @власник» у трьох місцях:
  - tf:68-69 (NODE, OWNER) і tf:96-108;
  - `tools/trees-index.py:21-23` (плюс формат ARROW для `trees/g2/g2.md`);
  - `mods/agents-status/hooks/parse.ts:7-16` (parseTree).
  Покриття різне: tf читає лише `trees/*.md` (:328, не бачить `g2/`), node-label і trees-index — `trees/**`.
- Розбір екрана DSH («◐», tmux capture-pane): tf:271-293 і `mods/agents-status/hooks/parse.ts:17-33` (parseDshTodo), `register.tsx:19`. tf:274 сам про це пише.
- Розбір `.baton/ledger.jsonl`: baton-guard:58-68 і baton-reminder-hook.py:22-33. Різна мета, схожий код.

4) РОЗРИВИ
- Stop-ворота unlazy мертві: 4 теки під `.unlazy/`, жодної прив'язки `session` (`gate-check.mjs --bind` ніколи не викликали, див. gate-check.mjs:217-224), гілка not blocking. Живцем 23 рази. `passport` не є пайплайном (там немає GATES.md), але рахується як scope.
- `hooks-smoke.py:149` («unlazy Stop», `stop_hook_active: True`, очікує rc==0): `stop-hook.mjs` не читає `stop_hook_active` взагалі (grep порожній). Тест не може впасти.
- Назва `answer-gate-shadow-hook.py` і шапка «ТІНЬОВИЙ… нічого не блокує» (ag:2-7) застарілі: хук блокує голосом (ag:443-472, 7 блокувань у цій сесії). Сигнали ask-req і unverified лишаються тінню.
- `nudge:delegate` (ag:56 `RE_DELEG_HINT = "Делегуй"`): у `~/.claude/hooks/classify-task.sh` і в хуках проєкту емітера слова «Делегуй» не знайшов, лише слово в коментарях classify-task.sh:6 і 19. У лозі 15 спрацювань, останнє 24.10. Походження вхідного тексту невідоме.
- number-claim:341 стверджує, що node-label «як робить» теж не пропускає `stop_hook_active`, але node-label:102 пропускає. Через це node-label не пише рядок «на кожен запуск» (всупереч :108-109).
- ag: 85 з 398 записів `error:no-transcript` (21%), розподілені по днях 12-24.10. У цих запусках хук сліпий.
- `~/.claude/projects/.../memory`: 3 файли HOWTO_RULES (tf:57-59) існують. Розривів немає.

5) НЕ ПЕРЕВІРЕНО
- Чи Stop-хуки справді працюють паралельно і чи вкладаються в 10 с: number-claim читає до 32 МБ (:75-76). Не міряв.
- Причину 85 `error:no-transcript`, джерело «Делегуй», чому `dsh-line.jsonl` не створено (найімовірніше немає рядка ◐ на екрані DSH, не перевірено).
- Вміст `~/.claude/hooks/test-hook.sh`. Читання `hook-test.log` і `session-timer.log` у не-кодових файлах. Повний вміст `lib/dispatch.mjs` (брав лише імпорт і гілки з `stop-hook.mjs`).
- Поле `links` у `passport.json` рахує текстові згадки (наприклад tf: «скрипти: 4»). Моє зіставлення з ним не робив: тут враховано лише реальні запуски, читання і записи.
