# scout-instrumenty-git — звіт розвідника (обхід системи, 25.10, Explore/sonnet)

ЗВІТ РОЗВІДНИКА: точки входу «виклик інструмента», git і запускачі. Нічого не змінював; запускав лише читання. Скорочення: S = .claude/settings.local.json, H = .claude/hooks/, T = tools/.

1) ЛАНЦЮЖКИ
Усі 24 файли в H підключені в S (рядки 25-309). Окремо ще два глобальні хуки з ~/.claude/settings.json: classify-task.sh і session-timer.sh. Один виклик Bash запускає 12 хуків (S:73-112, 152, 161, 186, 215).
А. git commit
 - Bash → commit-consent-hook (S:102) → читає transcript_path (H/commit-consent:197,133) → пише commit-consent.log (:34,186).
 - Той самий хук ловить обхід `--no-verify` (:86).
 - Далі справжній git → .git/hooks/pre-commit:3 → T/secret-scan.py:53. Він читає `git diff --cached`, а також agent.py і .env (:34-38).
 - Потім .git/hooks/commit-msg:3 → T/commit-node-check.py:26. Він читає `git diff --cached` і файл повідомлення (:22).
Б. git add
 - git-add-status-hook (S:97) → `git status` (H/git-add-status:118,169) → deny, якщо в команді є agent.py.
В. git push
 - baton-reminder (S:87) → читає .baton/ledger.jsonl (H/baton-reminder:18) і `git log` (:39).
 - Ledger пише baton-сервер (server.mjs:21,36), який стартує через run-baton.sh:7.
Г. baton
 - baton-guard стоїть у трьох подіях: UserPromptSubmit (S:290), PreToolUse baton_pass (S:195), PostToolUse pick_up (S:246).
 - Читає ledger і baton.json (H/baton-guard:43-44) → імпортує T/baton-diff.py (:92).
 - Після pick_up запускає T/handoff-view.py (:168) → пише .baton/HANDOFF-view.md. Його читає агент через підказку view_hint (:162).
Д. AskUserQuestion
 - plain-ask (S:175) → імпортує T/plain-codes.py (H/plain-ask:24) → пише plain-ask.jsonl.
 - ask-gate (S:180) → імпортує answer-gate-shadow-hook (H/ask-gate:56) → читає transcript (:124) → пише ask-gate.jsonl.
 - Після відповіді free-answer (S:260) → пише free-answer.log.
Е. delegate/deepseek
 - improver (S:118) → HTTP на NVIDIA або DeepSeek (H/improver:126,150). Читає .provider (:96), .env (:116), agent.py (:140). Пише improver.log.
 - personal-guard (S:205) → імпортує T/personal-scan.py (H/personal-guard:30) → пише personal-guard.jsonl.
 - commit-consent на платні виклики (S:224).
 - delegate-outcome-logger на Post і PostFailure (S:236, 267) → пише delegate-calls.jsonl (H/delegate-outcome-logger:20,88).
Є. Edit, Write, Bash
 - edit-gate (S:161) читає S (H/edit-gate:166), сусідні хуки (:193) і скан tools, хуків і скілів (:64). Пише edit-gate.log.
 - verify-nudge (S:147, 190) імпортує edit-gate-hook (H/verify-nudge:60) і answer-gate-shadow-hook (:79). Пише verify-nudge.log.
 - proc-guard (S:219) імпортує install-check-hook (H/proc-guard:32,86) і викликає `ps` (:62).
 - rules-why-guard: `git log RULES.md` (H/rules-why-guard:127) плюс перевірка свіжості RULES-WHY.md.
 - trash-md-guard: mtime TRASH.md (H/trash-md-guard:144).
 - troubles-grep: читає TROUBLES.md (H/troubles-grep:118).
Ж. Stop (S:45-65)
 - node-label-shadow імпортує T/trees-index.py (H/node-label-shadow:35) і робить glob по trees.
 - answer-gate-shadow імпортує T/plain-codes.py (:197). У transcript читає hook_additional_context (:248), тобто підказки з Є (request-brief, verify-nudge, edit-gate). Потім друкує `decision:block` (:472).
 - number-claim-shadow пише лише лог.
 - unlazy stop-hook.mjs працює зі станом у .unlazy/ (зверху прочитано).
З. statusLine і UserPromptSubmit
 - statusline-cost (S:309) → session-cost.jsonl (H/statusline-cost:66).
 - Читачі цього журналу: cost-nudge-hook (:30, пише cost-nudge-state.json:66), T/cost-report.py:111 і session-close SKILL.md:186.
 - tree-focus (S:39, 282) читає trees/*.md (:328), GOALS.md (:219) і memory/*.md (:164).
 - Також знімає екран вікна tmux «dsh» через `capture-pane` (:297-303) → dsh-line.jsonl (:380).
Запускачі
 - .bashrc:8 → menu.sh. Пункти меню: 1 → tmux-work.sh:22; 2 → alias agent → start.sh → agent.py (.bashrc:1); 3 → claude; 6 → T/watch-deepseek.py (menu.sh:27); 7 → claude-deepseek.sh; 8 → T/provider-switch.py (menu.sh:29).
 - tmux-work.sh: claude (:16), start.sh (:20), run-dsh.sh (:27). run-dsh.sh:8-9 запускає proot-distro ubuntu → /root/dsh-app/.../dsh --profile tui.
 - claude-deepseek.sh:21 піднімає T/deepseek-thinking-proxy.py (лог .claude/logs/deepseek-thinking-proxy.jsonl). Далі :40 ставить BASE_URL=127.0.0.1:порт/deepseek, :63 запускає `claude`. Цей URL читають classify-task.sh:22 і tree-focus (H/tree-focus:312-315).
 - provider-switch.py пише .provider і ~/.claude/delegator.json (:27-28, 114-115).
 - ~/.claude.json:1584-1608 → run-memory/delegate/baton/deepseek/pkgtruth.sh → node-сервери. run-delegate.sh:5-10 читає agent.py і .env. run-deepseek.sh:15 породжує під-сесії claude, які вантажать ті самі хуки.

2) ЖИВІ, ХОЧА В ПАСПОРТІ «0/мало»
 - commit-node-check.py (0) ← .git/hooks/commit-msg:3, на кожному коміті. З 19.10: 40 комітів механізмів, жоден із «без вузла».
 - secret-scan.py (4) ← .git/hooks/pre-commit:3.
 - deepseek-thinking-proxy.py (0) ← claude-deepseek.sh:21. Його лог змінювався 21.10 09:15.
 - plain-codes.py (2) ← plain-ask (460 записів) і answer-gate (398).
 - trees-index.py (65) ← node-label-shadow (354 записи).
 - personal-scan.py (31) ← personal-guard (46) і improver.
 - baton-diff.py (60) ← baton-guard на кожну передачу.
 - handoff-view.py (3) ← baton-guard на кожен pick_up (61).
 - provider-switch.py (10) і watch-deepseek.py (2) ← menu.sh, тобто людина поза журналом агента.
 - Дев'ять хуків із calls=None: baton-guard, baton-reminder, git-add-status, request-brief-reminder, rules-why-guard, trash-md-guard, troubles-grep, cost-nudge, tree-focus. Вони живі за S, просто без власного логу.
 - mcp memory, delegate, baton, deepseek, pkgtruth стартують через run-*.sh. mcp__delegate__deepseek (0) — псевдонім, його покриває лише personal-guard.
 - У паспорті взагалі немає типів «запускач» і «git-хук»: 0 згадок run-*.sh, menu.sh, tmux-work.sh і .git/hooks.

3) ГЛУХІ КУТИ / ДУБЛІ / РОЗРИВИ
 1. Improver не покриває delegate. Matcher S:118 має лише mcp__deepseek__deepseek, а заголовок хука (:4) обіцяє ще delegate і -reply. Для delegate останній rewrite був 25.09 (improver.log), а викликів delegate 275. Нижче про MCP-інструмент deepseek.
 2. Усі 6 rewrite для mcp__deepseek__deepseek від 26.09 мають provider=nvidia, ok:false, secs≈45. Це TIMEOUT=45 (H/improver:38): кожен виклик чекає 45 с марно. Причина: .provider=nvidia (з 25.09), а ~/.claude/delegator.json має provider=bazaarlink. provider-switch.py про bazaarlink не знає (grep 0).
 3. mcp__deepseek__deepseek-reply має лише commit-consent (S:224). Логера (S:236, 267) і improver немає, тож 19 викликів не в delegate-calls.jsonl.
 4. Git-хуки лежать поза git. `git ls-files` не містить pre-commit і commit-msg, інсталятора немає. S і .claude/logs/ у .gitignore (:24, :30), тому проводка хуків і логи не версіонуються. hooks-smoke.py:368-388 тестує лише commit-msg; для secret-scan автотесту немає (grep 0), є лише ручна проба DSH (agents/dsh/secret-scan-proot-2026-10-19.md).
 5. Логи, які не читає жоден код (лише parts-passport рахує, або `--backtest` вручну): answer-gate-shadow, node-label-shadow, number-claim-shadow, ask-gate, plain-ask, commit-consent, personal-guard, delegate-calls, improver, proc-guard. edit-gate.log, verify-nudge.log, install-check.log і free-answer.log читають лише самі хуки для дедупу.
 6. answer-gate-shadow-hook.py названий «тінь», але друкує decision:block (:472). «Тінь» лише для частини сигналів.
 7. Зв'язок між хуками тримається на тексті, не на коді. Підказки з Є потрапляють у transcript, а Stop шукає їх регулярками (H/answer-gate:58, 65, 318). Зміна фрази в підказці мовчки вимкне голос.
 8. dsh-line.jsonl не існує (writer H/tree-focus:380) попри пробу з 19.10. Гілка tmux→«DSH насправді» жодного разу не дала рядка: тут потрібен екран DSH зі списком задач (знак ◐) (:276-282).
 9. Мертві запускачі й код:
   - mcp_run.sh (викликів нема, :4 вказує на неіснуючий config/yt-dlp.conf, а живий agent-reach MCP — `python my_mcp_server.py` у .claude.json);
   - run.sh (лише фікстури тестів);
   - run-telegram-bot.sh;
   - ~/setup_deepseek.sh;
   - agents/claude-code/run-dsh-isolated.sh (проба 30.09);
   - ~/.claude/hooks/test-hook.sh (не в settings.json);
   - tree-focus: short() (:80, коментар каже «викликів немає») і змінна hits (:326, :355, не читається).
 10. Журнали без ротації: ~/.claude/hook-test.log 5,5 МБ (classify-task.sh:15, пише на кожне повідомлення, читача нема) і session-cost.jsonl 1,7 МБ.
 11. Дублі проводки навмисні, з різними matcher: request-brief-reminder (S:107, 132), rules-why-guard (112, 142), verify-nudge (147, 190), commit-consent (102, 224). Побічний ефект: verify-nudge і proc-guard на кожен виклик виконують модулі edit-gate, answer-gate і install-check.

4) НЕ ПЕРЕВІРЕНО
 - Чи хуки справді виконуються паралельно (12 python на один Bash проти межі Android 32).
 - Точна семантика matcher: «mcp__deepseek__deepseek» як точний збіг чи regex. Від цього залежить, чи -reply не покритий. Документацію Claude Code не звіряв.
 - tmux і ps не запускав: чи існує вікно dsh і чому немає ◐.
 - mods/agents-status (enabledPlugins) теж читає екран DSH; не відкривав.
 - Внутрішності unlazy stop-hook.mjs і зовнішнього `pkgtruth hook` — поверхово.
 - Фактичний routing у ~/.claude/delegator.json (бачив лише provider=bazaarlink).
 - Реальне спрацювання git-хуків під proot (DSH).
 - T/reel-read.py і claimcheck поза моєю ділянкою.
