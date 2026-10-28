# Скіли під 5 класів помилок — пошук v2 (npx skills find, 2026-10-28)

Фільтр (PDF «10 AI Skills», стор. 13): скіл брати, лише якщо він прибирає конкретну повторювану помилку. Нічого не встановлювалось.
Сирий вивід пошуку (11 запитів, перші ~7 рядків кожного): `/data/data/com.termux/files/usr/tmp/fs/find.txt` (тимчасовий).

## Запити і що знайшлося (дослівні назви, установки)
- "verify before claiming": azure-validate 569.1K; project-min-evaluation 3.3K; pythia-verify 61; verify-before-merge (jan-jan/guardrails) 35; dual-verifier 32; oisincoveney/verify 27.
- "evidence before completion": verification-before-completion (obra) 255.7K; unlazy (leonxlnx) 9.6K; verifying-before-completion (osmontero) 157.
- "fact check claims": fact-check (elvisun 807; jwynia 751), fact-check-workflow 582 — журналістика, не про дії агента.
- "root cause" / "systematic debugging": debugging-and-error-recovery (addyosmani) 64.1K; diagnosing-bugs (mattpocock) 852.3K; systematic-debugging (obra) 310.8K; debugging-strategies (wshobson) 13.6K.
- "prioritize tasks": time-management 409; discover-tasks 62; things-morning-organizer 33; prioritize (forsvn-labs/meta-skills) 31.
- "task triage": triage (mattpocock) 1M; github-triage 2.7K (усе про issue tracker).
- "delegate subagents": subagents (waishnav/devspace) 468; delegation-templates (ohyeh/agent-scripts) 257; launch-subagent 128; subagent-driven-development (hermes) 104.
- "parallel agents": dispatching-parallel-agents (obra) 221K; herdr 74K.
- "learn from mistakes": learn-rule (rohitg00/pro-workflow) 174; metacognition 83; self-improving-agent 41.
- "session retrospective memory": retro (mattpocock) 290.7K; groove-utilities-memory-retrospective 516; retro (netresearch) 37.

## Прочитані ПОВНІСТЮ SKILL.md (зірки репо / останній коміт)
jan-jan/guardrails verify-before-merge (1★, 2026-10-25); thaildhe172591/pythia pythia-verify (4★, 2026-10-27); addyosmani/agent-skills debugging-and-error-recovery (111255★, 2026-10-13); obra/superpowers systematic-debugging (306738★, 2026-10-23); mattpocock/skills triage (305124★, 2026-10-27); waishnav/devspace subagents (5300★, 2026-10-28); ohyeh/agent-scripts delegation-templates (0★, 2026-10-28); rohitg00/pro-workflow learn-rule (2930★, 2026-09-29); andreadellacorte/groove retrospective (6★, 2026-07-24).
НЕ вдалося: forsvn-labs/meta-skills `prioritize` — у дереві репо (git/trees, grep "prioriti") файлу немає, SKILL.md не прочитано [не перевірено]. obra verification-before-completion і mattpocock retro — прочитані у минулому звіті, тут не перечитувались. diagnosing-bugs, dispatching-parallel-agents, osmontero verifying-before-completion — не читались (ліміт кроків).

## Кандидати по класах

### Р1 «Дія чи висновок до перевірки»
1. **jan-jan/guardrails@verify-before-merge** — «Evidence before assertions, always. A claim of "done", "fixed", or "passing" without freshly executed command output is a violation.» Механізм: є — окремий підагент-«ворота» запускає перелік перевірок і повертає фіксований «gate summary»; «Read the verdict from the reported pass/fail counts, never from the status code»; але перевірки прив'язані до `.guardrails/config.yaml`, `check-trace.sh`, worktree-ів — це їхня інфраструктура (не наша). Прибрав би клас частково: ідея «підагент збирає докази, головний бачить лише підсумок» збігається з нашим verify-before-show. Не спрацює: без їхніх скриптів і конфігу половина кроків порожня; 1★. Оцінка: **часткова (ідея, не придатний як є)**.
2. **pythia-verify** — «NO COMPLETION CLAIM WITHOUT EVIDENCE FROM THIS SESSION»; звіт зі зарезервованими словами done/broken/not verified і рядком «Not verified:». Але чек-ліст — для бази Oracle (`pythia errors/invalid/lint`). Корисне лише формат звіту «Done / Evidence / Not verified». Оцінка: **часткова/слабка (формат звіту)**.

### Р4 «Латка замість системи»
1. **obra/superpowers@systematic-debugging** — «NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST»; «If ≥ 3: STOP and question the architecture»; червоні прапорці «Quick fix for now, investigate later». Механізм: лише текст (чотири фази, таблиця відмов), хуків немає; допоміжні файли root-cause-tracing.md тощо не читались. Прибирає клас найближче за змістом: правило «3 невдалі латки → питати про архітектуру» прямо проти «лікує симптом». Не спрацює: текст-нагадування, як і наші правила; для поведінки «лишив хвости» нічого немає. Оцінка: **часткова (найкраща в класі)**.
2. **addyosmani/agent-skills@debugging-and-error-recovery** — «STOP adding features… PRESERVE evidence… FIX the root cause… GUARD against recurrence»; чеклист «Verification» (root cause задокументовано, регресійний тест). Знов лише текст; «guard» = тест на код, не запис у реєстр. Оцінка: **часткова, дублює obra**.

### Р5 «Черга й пріоритет на око»
1. **mattpocock/skills@triage** — «Move issues … through a small state machine of triage roles»; ролі needs-triage / needs-info / ready-for-agent / ready-for-human / wontfix; «Every triaged issue should carry exactly one category role and one state role». Механізм: машина станів з рівно одним станом на елемент і перевіркою конфлікту («If state roles conflict, flag it»), але прив'язана до issue tracker (GitHub), без числових критеріїв пріоритету. Корисна ідея: «рівно один стан на задачу» + «ready-for-agent / ready-for-human» як явний розподіл виконавця. Не прибирає «порядок на око» — критеріїв черговості в ньому немає. Оцінка: **слабка/часткова**.
2. forsvn-labs/meta-skills@prioritize (31 уст.) — SKILL.md не знайдено в дереві репо, не прочитано. Оцінка: **не перевірено**.

### Р9 «Не той шлях; роблю сам замість агентів/готового»
1. **ohyeh/agent-scripts@delegation-templates** — «Invoke BEFORE writing any delegation prompt … so the prompt ships with explicit GOAL, ACCEPTANCE, and REPORT sections»; «A delegation without objective acceptance criteria is a guess you outsourced.» Шаблони SEARCH/IMPLEMENT/REFACTOR/RESEARCH/REVIEW; «Zero-result duty: before reporting zero matches, prove each search pattern works on a known positive»; «unknown ≠ PASS». Механізм: текст-шаблони (є згадки про gate, що перевіряє бриф — `check-bol-prompt.sh`, — але це їхня інфраструктура). Явно «Not for deciding WHETHER to delegate» — тобто клас «роблю сам» не прибирає, прибирає лише якість брифів. Також їхній скіл прив'язаний до їхнього tmux-оточення; 0★. Оцінка: **часткова (бриф, не рішення «делегувати»)**.
2. **waishnav/devspace@subagents** — «Subagents are optional. Use your normal tools for routine work; delegate only when a separate worker materially helps» — навпаки, стримує делегування; потрібен CLI `devspace`. Оцінка: **немає**.

### Р10 «Урок не засвоєно»
1. **rohitg00/pro-workflow@learn-rule** — «Capture a lesson from the current session into permanent memory»; формат «[LEARN] Category: One-line rule / Mistake / Correction»; «Always wait for user approval before persisting.» Механізм: «capture hook» згадано (у репо pro-workflow), у самому SKILL.md лише процедура; зберігає правила за категоріями. У нас те саме робить MEMORY.md/RULES-WHY.md. Не прибирає клас: запис ≠ дія в потрібний момент (це наш «fixed = works automatically»). Оцінка: **часткова/слабка**.
2. **andreadellacorte/groove@memory-retrospective** — читає `signals.md`, інциденти, learned/*.md і виводить «recurring mistake patterns» («Group by title keywords to identify recurring patterns»). Механізм: read-only звіт за період; залежить від їхньої структури `.groove/memory/` і task backend (beans). Ідея корисна: рахувати повтори помилок за періодом — у нас це робить реєстр помилок. Оцінка: **часткова (ідея)**.

## Таблиця «клас → кандидат → оцінка»
| Клас | Кандидат | Оцінка |
|---|---|---|
| Р1 | verify-before-merge (jan-jan); pythia-verify | часткова (ідея підагента-воріт; формат «Not verified») |
| Р4 | systematic-debugging (obra); debugging-and-error-recovery (addyosmani) | часткова (правило «3 латки → архітектура»; лише текст) |
| Р5 | triage (mattpocock); prioritize (forsvn) не прочитано | слабка / не перевірено |
| Р9 | delegation-templates (ohyeh); subagents (waishnav) | часткова (якість брифу) / немає |
| Р10 | learn-rule (rohitg00); memory-retrospective (groove) | часткова/слабка (запис і підрахунок повторів) |

## Що нового проти минулого звіту
Минулий звіт: verification-before-completion, retro, wayfinder, triage, using-superpowers, dispatching-parallel-agents, diagnosing-superpowers. Нове тут (прочитано повністю): verify-before-merge (підагент-ворота, «exit 0 ≠ pass»), systematic-debugging (правило «3 фікси → архітектура» — найближче до Р4), delegation-templates («zero-result duty», «unknown ≠ PASS»), learn-rule, memory-retrospective. Каталог skills.sh відкрито через `npx skills find` — підтверджено.

## Висновок
Прямої відповіді (скіл, що сам прибирає клас) знову немає: усі кандидати — текст-нагадування або прив'язані до чужої інфраструктури (guardrails, tmux, Oracle, issue tracker, beans), тобто фільтр стор. 13 («прибирає конкретну повторювану помилку») проходять лише частково. Найближчі за змістом: obra systematic-debugging для Р4 (правило «3 невдалі латки → зупинитись і питати про архітектуру», якого в нашому RULES.md, за цим пошуком, не перевірялось — [не перевірено]) і jan-jan verify-before-merge для Р1 (підагент збирає докази, головний бачить фіксований підсумок; у нас це verify-before-show). Для Р5, Р9, Р10 готового скіла немає; ліки лишаються нашими (хуки, замки, реєстр). Рекомендація: нічого не ставити; за бажанням — перевірити, чи правило «3 латки → питати» вже є в RULES.md, і лише тоді розглядати його перенесення (не скіл).
