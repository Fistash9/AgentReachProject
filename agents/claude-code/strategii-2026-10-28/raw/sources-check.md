# Перевірка першоджерел: організація й розподіл роботи — 2026-10-28
— [claude-code, під-агент, 2026-10-28; мета: принципи з першоджерел для питання користувача про системи організації роботи]

## (2) Цитати GitLab
- «The GitLab OKRs run for one quarter (3 months).» — grep -F у всіх збережених сторінках: 0 → НЕ ЗНАЙДЕНО
- «Engineering Managers score and update their OKRs on a monthly cadence.» — grep -F у всіх збережених сторінках: 0 → НЕ ЗНАЙДЕНО
- «Create no more than three to five Key Results per objective» — grep -F у всіх збережених сторінках: 0 → НЕ ЗНАЙДЕНО
- Причина: задана URL (engineering/devops/dev/create/engineering-managers/okrs/) повертає 404 «Page Not Found» (браузер і curl); сторінка company/okrs/ каже «Last modified March 2, 2026: Remove OKR process from the Public Handbook Pages»; web.archive.org через браузер — 404. Цитати з пошуку DeepSeek НЕ підтверджені.

## (1) Принципи (джерело · категорія · суть · цитата · grep -F -c)
- [gitlab-teamops] Інше — TeamOps: рішення = паливо: «Decisions are the fuel for high-performance teams.» · grep=1
- [gitlab-teamops] Приймання — результат/цілі: «Teams exist to deliver results.» · grep=1
- [gitlab-teamops] Хто вирішує — рівний внесок: «Everyone must be able to equally contribute.» · grep=1
- [gitlab-teamops] Постановка — спільна реальність: «Teams must be informed by an objective, shared reality.» · grep=1
- [linear-scope] Обмеження — проєкт 1-3 тижні, 1-3 люди: «Design projects so that they can be completed in 1–3 weeks with a team of 1–3 people.» · grep=1
- [linear-intro] Обмеження/цикл — цикли замість спринту: «Create momentum – don’t sprint» · grep=1
- [linear-intro] Хто вирішує — у циклах призначають: «In cycles, you can decide priorities and assign responsibilities.» · grep=1
- [linear-intro] Обмеження — 2-тижневі цикли: «2-week cycles are the most common in software building.» · grep=1
- [linear-issues] Постановка — issue = завдання для виконавця: «It needs to be clear enough so that the assignee can perform it» · grep=1
- [linear-issues] Постановка — не завдання - не в трекер: «If it’s not a task, then it doesn’t belong in the issue tracker.» · grep=1
- [linear-intro] Постановка — навіщо backlog короткий: «A more focused backlog makes it easier and faster to plan cycles» · grep=1
- [shapeup-ch03-appetite] Постановка — appetite: «Appetites start with a number and end with a design.» · grep=1
- [shapeup-ch03-appetite] Обмеження — fixed time: «“fixed time, variable scope,”» · grep=1
- [shapeup-ch07-bets] Постановка — без backlog: «Before each six-week cycle, we hold a betting table where stakeholders decide what to do in the next cycle.» · grep=1
- [shapeup-ch07-bets] Постановка — не обрані - відпускаємо: «If we don’t, we let it go.» · grep=1
- [shapeup-ch08-betting-table] Хто вирішує — склад betting table: «Our betting table at Basecamp consists of the CEO» · grep=1
- [shapeup-ch08-betting-table] Хто вирішує — без другого кроку схвалення: «There’s no “step two” to validate the plan or get approval.» · grep=1
- [shapeup-ch08-betting-table] Обмеження — цикл 6 тижнів + 2 cool-down: «we schedule two weeks for cool-down» · grep=1
- [shapeup-ch08-betting-table] Приймання — circuit breaker: «If they don’t finish, by default the project doesn’t get an extension.» · grep=1
- [shapeup-ch08-betting-table] Хто виконує — команда відповідальна: «teams are given full responsibility for executing projects» · grep=1
- [shapeup-ch09-hand-over] Приймання — shipping = merge: «Shipping means merging into the main codebase and expecting not to touch it again.» · grep=1
- [atlassian-daci] Хто вирішує — Approver один: «The one person (yes: one!) who makes the decision.» · grep=1
- [atlassian-daci] Хто виконує — Driver: «The person responsible for corralling stakeholders, collating all the necessary information, determining the scope of the decision, and getting a decision made by the agreed date.» · grep=1
- [atlassian-daci] Хто вирішує — Contributors: «they have a voice, but not a vote.» · grep=1
- [atlassian-daci] Приймання — Informed / фіксація: «whose work may be affected by the decision, and should be informed once it’s been made» · grep=1
- [atlassian-daci] Приймання — деталі рішення: «This should include the current status, impact, all people involved, due date, and the outcome once decided.» · grep=2

Підсумок по джерелах (кількість принципів із grep≥1):
      4 atlassian
      4 gitlab
      7 linear
     10 shapeup

Нульових grep після правки регістру (People→whose…): 0. Усі цитати з grep≥1 (Atlassian: 4, GitLab TeamOps: 4, Linear: 7, Shape Up: 10; GitLab OKR: принципів нема — сторінка вилучена).

## (3) Звіт про браузер (agent-browser 0.40.0 + Lightpanda, обгортка $PREFIX/bin/agent-browser)
- Процесів до старту: 19 (межа брифу 21). Під час роботи 22–26 (+3…+7 до 19; стабільно <32), після closе див. нижче.
- Спрацювало (exit 0 щоразу): `agent-browser open <URL>` (виводить «✓ <title>» + URL) і `agent-browser get text body > файл`. 15+ сторінок підряд, без повторів і без curl.
- Час open+get на сторінку: gitlab 404-сторінка 11 с (перший холодний старт), gitlab company/okrs 15 с (107 КБ), linear 3–5 с, shapeup 3–4 с, atlassian 8 с, teamops 8 с.
- Не спрацювало / обмеження:
  * `agent-browser skills get core` → «Skills directory not found. Set AGENT_BROWSER_SKILLS_DIR or reinstall via npm.» (статичний бінарник без npm-теки скілів; на роботу не впливає).
  * `agent-browser eval 'JSON.stringify([...document.querySelectorAll("a")].map(a=>a.href)...)'` → "[]" (посилання не знайдено; щодо Lightpanda — не з'ясовано, чому порожньо; посилання на розділи Shape Up взято curl-ом з HTML).
  * Задана GitLab-URL (…/engineering-managers/okrs/) → сторінка «404 Page not found» (браузер exit 0; це 404 сайту, не збій браузера); curl теж 404.
  * linear.app/method: `get text body` на головній дав лише зміст (974 Б); потрібні підсторінки відкривав окремо.
  * web.archive.org (через браузер) → «404 Not Found nginx».
- Curl використано лише для: перевірки HTTP-кодів GitLab, списку посилань Shape Up/Linear (HTML), не для збереження текстів. Усі тексти в pages/ — з браузера.
