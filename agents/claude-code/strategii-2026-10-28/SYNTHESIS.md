# Як передові компанії, фабрика й прораб роздають роботу — і що з цього взяти оркестратору (28.10)

— [claude-code, під-агент, 2026-10-28]. Запит користувача: «якими перевіреними часом системами організації й роздачі
роботи користуються найуспішніші й найшвидші передові компанії, що в них спільного, і як працюють фабрика (Toyota) і
прораб». Служить: GOALS.md:11–13 (E, «агент вищого порядку… розподіляє задачі між іншими агентами»).
Нічого, крім цієї теки, не змінено.

**Як читати мітки.** `[A7 · grep 1]` = цитату (фрагмент між «») знайдено командою `grep -F -c` у збереженому тексті
сторінки, лічильник 1. Повна таблиця перевірки: `raw/quotes-check.tsv` (id, файл сторінки, лічильник, фрагмент).
Тексти сторінок лежать у `/data/data/com.termux/files/usr/tmp/stale-links-2810/pages/<файл>.txt` (у проєкт не
копіювали). Відповіді DeepSeek (`raw/ds-q1…q4.txt`) тут лише підказували, ЩО шукати. Їхні цитати, яких у тексті
сторінки нема, винесено в розділ E.

**Підсумок звірки (надруковано лічильником):** цитат у таблиці 60, звірено 60, не знайдено 0. Перший прохід був
56/52/4: дві цитати Anthropic DeepSeek подав неточно («poka-yoke», «more time optimizing tools»), їх замінено точним
текстом сторінки (C5, C7). Ще дві з MAST («41% to 86.7%», «organizational understanding») в анотації arXiv
відсутні, тож вони перейшли в E.

---

## Ціль (GOALS.md:11–13) › Якість роботи агентів › «Призначити виконавця»

### A. Що спільного в найшвидших і передових компаніях

Побутова картинка: добра кухня ресторану. Шеф один, і саме він вирішує, що піде в меню. Кожен кухар знає свою
станцію. Замовлення приходить на папірці з точним описом, а на кожну страву є свій час.

**A.1. Мала порція роботи і жорсткий строк. Обсяг ріжуть під строк, а не навпаки.**
- Linear: «completed in 1–3 weeks with a team of 1–3 people» [A1 · grep 1] — https://linear.app/method/scope-projects
- Linear: «In cycles, you can decide priorities and assign responsibilities.» [A3 · grep 1] — https://linear.app/method/introduction
- Shape Up (Basecamp): «Appetites start with a number and end with a design.» [A4 · grep 1] — https://basecamp.com/shapeup/1.2-chapter-03
- Shape Up: якщо не встигли, «by default the project doesn[’t get an extension]» [A5 · grep 1] — https://basecamp.com/shapeup/2.2-chapter-08
- Ramp: «Our entire planning process is optimized toward product velocity.» [A12 · grep 1] — https://ramp.com/blog/how-we-build-product-at-ramp

**A.2. Рішення ухвалює одна людина, а виконавець відповідає за все виконання.**
- Atlassian DACI: «The one person (yes: one!) who makes the decision.» [A8 · grep 1]; дорадники — «they have a voice, but not a vote» [A9 · grep 1] — https://www.atlassian.com/team-playbook/plays/daci
- Shape Up: «teams are given full responsibility for executing projects» [A6 · grep 1]; «no “step two” to validate the plan or get approval» [A19 · grep 1] — https://basecamp.com/shapeup/2.2-chapter-08
- Linear: «We only have a single product team» (і одна дорожня карта) [A15 · grep 1] — https://www.lennysnewsletter.com/p/how-linear-builds-product

**A.3. Задачу пишуть так, щоб виконавець зміг її зробити без перепитувань.**
- Linear: «It needs to be clear enough so that the assignee can perform it» [A2 · grep 1] — https://linear.app/method/write-issues-not-user-stories
- Shape Up: «Shipping means merging into the main codebase» (тобто «готово» означає злито, а не «майже») [A7 · grep 1] — https://basecamp.com/shapeup/2.3-chapter-09

**A.4. Без привратників: усе відкрито, рішення ухвалюють там, де роблять роботу.**
- Ramp: «Teams farm for dissent, not approval.» [A11 · grep 1]; «Eliminating gatekeepers ensures that things keep moving forward.» [A13 · grep 1] — https://ramp.com/blog/how-we-build-product-at-ramp
- GitLab TeamOps: «Teams must be informed by an objective, shared reality.» [A10 · grep 1] — https://handbook.gitlab.com/teamops/
- Perplexity (Срінівас): «extreme bias for action» [A16 · grep 1]; CEO не мусить бути «the one who solves every problem» [A17 · grep 1] — https://www.gsb.stanford.edu/insights/perplexitys-aravind-srinivas-infinite-value-knowledge
- Linear: формальних OKR нема, «For goals, we like to keep it simple» [A14 · grep 1] — lennysnewsletter (вище)
- Shopify: «reflexive AI usage is now a baseline expectation» [A18 · grep 1] — https://www.shopify.com/news/unserious-exploration

### B. Фабрика (Toyota), прораб (Last Planner) і вузьке місце

Побутова картинка: черга до каси в супермаркеті. Касир сам кличе «наступний!», а не отримує покупців поштовхом.
Коли каса зламалась, вмикають лампу, і касир чекає, поки її не полагодять, а не пробиває «на око».

**B.1. Toyota: зупинитися на першій помилці; право зупинити лінію має той, хто біля роботи.**
- «stopping immediately when abnormalities are detected» [B1 · grep 1]; «the operator can stop the line by pulling the stop cord» [B2 · grep 1] — https://global.toyota/en/company/vision-and-philosophy/production-system/
- Andon: робота не відновлюється, «until the problem is resolved» [B4 · grep 1] — https://global.toyota/en/company/plant-tours/production-system/
- Межа, яку визнає сама Toyota: автоматизувати можна лише те, що вмієш «first be able to do the work smoothly and correctly by hand» [B7 · grep 1] — global.toyota (вище)

**B.2. Toyota: «витягування» замість «штовхання» і рівно стільки, скільки треба.**
- «the following process goes to the preceding process to pull the parts» [B5 · grep 1] — plant-tours (вище)
- «making only what is needed, when it is needed, and in the amount needed» [B3 · grep 1]; «Make them at the pace at which they[’re sold]» [B6 · grep 1] — production-system (вище)

**B.3. Прораб (Last Planner System, LCI Standard Work 2023): у план іде лише готове, а виконавець сам дає обіцянку.**
Джерело: https://leanconstruction.org/wp-content/uploads/2023/10/2023_LCI_LeanConstructionPlannerStandard-Work.pdf.
Текст PDF витягнуто власним скриптом на stdlib (`tmp/.../scripts/pdftext.py`), бо pdftotext нема.
- Make-ready, тобто зняти перешкоди до того, як задачу видали: «is to take actions needed to remove constraints from assignments» [B13 · grep 1]
- План тижня складають разом: «collaboratively developed by the team» [B12 · grep 1]; кожен пункт є «personal commitment from a team member» [B8 · grep 1]; «commitment based planning» [B11 · grep 1]
- Щоденна нарада «5 to 8-minute stand-up» [B9 · grep 1]; якщо не встиг, просять «for a new promise» [B10 · grep 1], а не сварять
- Метрика: «Measure promises kept» (PPC, частка виконаних обіцянок і причини зриву) [B14 · grep 1]

**B.4. Вузьке місце (теорія обмежень, Goldratt).** Першоджерела не відкрито (tocico.org DeepSeek не знайшов,
а Wikipedia — це третя сторона). Тому тут жодної звіреної цитати нема, див. E. Саму ідею «темп усієї системи
задає її найповільніша ланка» нижче вжито лише як рамку, без цитати.

### C. Агенти: коли віддавати під-агенту, скільки паралельно, як перевіряти, відомі провали

Побутова картинка: ремонт квартири. Обдзвонити п'ять магазинів і порівняти ціни на плитку легко роздати п'ятьом
людям одночасно. Класти плитку в одній ванній удвох, коли кожен робить «по-своєму», виходить гірше, ніж самому.

**C.1. За замовчуванням — просто, без зайвих агентів.**
Anthropic, https://www.anthropic.com/research/building-effective-agents (з /engineering/ перекидає сюди):
- «consider adding complexity only when it demonstrably improves outcomes» [C1 · grep 1]; «Start with simple prompts, optimize them with comprehensive evaluation» [C2 · grep 1]
- Агент потрібен там, де «difficult or impossible to predict the required number of steps» [C3 · grep 1]; ціна цього — «potential for compounding errors» [C4 · grep 1]

**C.2. Коли віддавати і коли ні.**
Anthropic, https://www.anthropic.com/research/multi-agent-research-system:
- Віддавати варто при «heavy parallelization, information that exceeds single context windows» [C8 · grep 1]
- Не віддавати, коли агентам потрібен спільний контекст і в них багато залежностей: такі задачі «not a good fit for multi-agent systems» [C17 · grep 1]; «most coding tasks involve fewer truly parallelizable tasks than research» [C26 · grep 1]
- Чи окупиться, вирішує ціна: агенти потребують задач, де «value of the task is high enough» [C16 · grep 1], бо мультиагентна система витрачає «15× more tokens than chats» [C12 · grep 1]

**C.3. Скільки паралельно і як дозувати.**
- «spins up 3-5 subagents in parallel» [C9 · grep 1]; «Scale effort to query complexity» [C18 · grep 1]; «Simple fact-finding requires just 1 agent» (з 3–10 викликами; порівняння — 2–4 під-агенти) [C19 · grep 1]
- Відомий провал: «spawning 50 subagents for simple queries» [C11 · grep 1]
- «Teach the orchestrator how to delegate» [C20 · grep 1]. Кожному під-агенту потрібні «an objective, an output format» (далі на сторінці: інструменти і межі задачі) [C10 · grep 1]
- Якість тримається на бюджеті: «token usage by itself explains 80% of the variance» [C27 · grep 1; C14 · grep 1]
- Склад, що виграв: Opus-ведучий із Sonnet-під-агентами переміг одного Opus «by 90.2%» [C13 · grep 1]

**C.4. Інструменти і перевірка.**
- «Poka-yoke your tools. Change the arguments so that it is harder to make mistakes.» [C5 · grep 1]; на SWE-bench команда «spent more time optimizing our tools than the overall prompt» [C7 · grep 1]; правило «absolute filepaths» прибрало помилки [C6 · grep 1] — building-effective-agents
- Людина ловить те, що пропускає автоматика: «human testers noticed» (агенти обирали SEO-ферми замість першоджерел) [C15 · grep 1] — multi-agent-research-system
- Cognition: «Context Rot is a well-documented phenomenon» [C23 · grep 1]; рецензент із «completely clean context» бачить глибше [C22 · grep 1]; головна складність — «how does a dumber model know» (що досягла своєї межі) [C21 · grep 1] — https://cognition.com/blog/multi-agents-working
- MAST (NeurIPS 2025, анотація): виграш мультиагентних систем «their performance gains on popular benchmarks are often minimal» [C24 · grep 1]; база — «comprehensive dataset of 1600+ annotated traces» [C25 · grep 1] — https://arxiv.org/abs/2503.13657 (анотацію взято curl, бо браузер отримав 403)

---

### D. Що це означає для нас. Принцип → наша проблема → механізм

Порядок узято з CRITERIA.md розділ 2 (від найбільшої шкоди цілі E). Посилання `CRITERIA:NN` ведуть на рядок у
`agents/claude-code/handoff-criteria-2026-10-28/CRITERIA.md`. Тут лише пропозиції: жодного хука чи правила не
змінено, і кожна зміна хука або правила потребує «так» користувача.

1. **K27, хибні зупинки воріт v2 (CRITERIA:49, корінь CRITERIA:42).**
   Принцип: andon працює, лише поки шнуру довіряють (B1, B4). Кожна хибна зупинка привчає ігнорувати лампу.
   Poka-yoke виправляє інтерфейс, а не людину (C5).
   Механізм: виправити винятки в коді edit-gate-hook.py:462–471 і :520 (як радить live…md:54). Додатково вести
   «PPC воріт» (B14): після кожної зупинки рядок «влучна/хибна + причина» у журнал зупинок, а скрипт рахує частку.
   Тоді рішення «вимкнути C» спиратиметься на число за тиждень, а не на 11 подій.
2. **K22, на новій задачі ніхто не вирішує «кому віддати» (CRITERIA:50, :37).**
   Принцип: make-ready і бриф до старту (B13, C10). Дозування за складністю (C18, C19): 1 агент / 2–4 / більше.
   Механізм: підказка на новій задачі (UserPromptSubmit), яка вимагає картку «мета · формат виходу · інструменти ·
   межі · масштаб (сам / 1 / 2–4 агенти) · причина». Зараз ворота спрацьовують лише після 12 власних кроків
   (CRITERIA:26), тобто вже по факту.
   **Суперечність:** C1/C2 і C17/C26 кажуть «за замовчуванням просто і не для спільного контексту». Наше
   use-subagents-for-bounded-work (CRITERIA:26) і RULES.md:205–210 («Тригер є — викликаю delegate одразу») задають
   протилежний дефолт, тобто «віддай». У картці потрібна графа «спільний контекст / правки одного файлу →
   сам» як законна причина.
3. **K25, на карті нема виконавців (CRITERIA:51, :40).**
   Принцип: одна дошка і один, хто вирішує (A8, A15, A19). Pull замість push: наступний сам бере з черги готового
   (B5). Обіцянка виконавця (B8).
   Механізм: один файл-дошка, який скрипт збирає з живих під-агентів (task-id, вузол, старт, бюджет) і з листів
   DSH. DSH отримує не разову задачу, а чергу «готових» (make-ready пройдено) і сам бере наступну. Це прямо лікує
   «DSH простоював 19–20.10». Під-агенти Claude «витягувати» не вміють (у джерелах C цього нема), тож для них
   лишається push із дошки.
4. **K28, smoke для v2 (CRITERIA:52, :43).**
   Принцип: якість вбудовують у процес, а помилки, якщо їх не ловити, накопичуються (B1, C4).
   Механізм: кейси v2 у tools/hooks-smoke.py, а саме 11 записаних живих зупинок як вхід і очікуваний вердикт. Без
   цього пункт 1 небезпечний.
5. **K10 + K26, effort і ціна (CRITERIA:53, :25, :41).**
   Принцип: якість задає бюджет токенів (C27), а мультиагентність коштує ×15 (C12), тож окупається лише цінна задача
   (C16). Склад «сильний ведучий + дешевші під-агенти» виграв (C13).
   Механізм: cost-report з розбивкою за effort/model під-агента і звірка з якістю звіту (влучно/доробка) раз на 3
   сесії. Це вже записано (RULES.md:236), але не зроблено.
   **Суперечність:** RULES.md:231–235 знає лише low/medium/high. C27 підтримує «складне → більший бюджет», тобто
   прохання користувача «максимальний» (CRITERIA:41), але правило рівнів цього не дозволяє, а слово користувача
   ніде не записане.
6. **K21, бюджет при >1 під-агенті (CRITERIA:54, :36).**
   Принцип: провал «50 subagents for simple queries» (C11) стався, бо ліміт був лише в промпті. Норма — 3–5 (C9).
   Механізм: лічильник одночасних Agent-викликів у хуку: понад N (наприклад, 3) — питання про ціну. Ліміт у коді, а
   не в тексті.
7. **K23, вузькі агенти (CRITERIA:55, :38).**
   Принцип: чіткі межі задачі (C10) і чистий контекст рецензента (C22). Context rot (C23) пояснює, чому 26 тис.
   токенів старту шкодять, а не лише коштують.
   Механізм: визначення в `.claude/agents/` з білим списком tools і без CLAUDE.md для збирання й рецензії
   (прогалина CRITERIA:69: теку ще не переглянуто).
8. **K24, MCP вузьким агентам (CRITERIA:56, :39).**
   Принцип: на інструменти варто витрачати більше уваги, ніж на промпт (C7), і робити їх такими, щоб помилитися
   було важче (C5).
   Механізм: рідкісні MCP лише у вузьких агентів (як у BACKLOG.md:87–92), спершу бектест.
9. **Перевірка звіту під-агента (CRITERIA:64, суперечність 3.5).**
   Принцип: рецензент із чистим контекстом (C22), людина ловить те, що пропускає автоматика (C15), а слабша ланка
   не знає своїх меж (C21).
   Механізм: для звітів, на яких тримається висновок, окремий рецензент-агент із чистим контекстом (звіт + джерела)
   замість K=2 власних кроків оркестратора. У брифі — andon-рядок: «знайшов перешкоду → зупинись і назви її» (B4,
   B10), бо питати агента «чи впорався» марно (C21).
10. **Бриф під-агента ≤25 кроків тримається лише текстом (CRITERIA:28).**
    Принцип: «апетит» і circuit breaker, тобто фіксований строк і змінний обсяг, а продовження за замовчуванням
    нема (A4, A5).
    Механізм: у брифі бюджет викликів і правило «не встиг → звіт про зроблене, без продовження». Оркестратор не
    продовжує автоматично, а нове завдання ставить окремим брифом.

### E. Не підтверджено, спростовано, не знайдено

- **GitLab OKR (ds-q1):** «The GitLab OKRs run for one quarter (3 months).», «Engineering Managers score and update
  their OKRs on a monthly cadence.», «Create no more than three to five Key Results per objective». Сторінка дає 404,
  company/okrs/ каже «Remove OKR process from the Public Handbook Pages» (02.03.2026), Wayback через браузер — 404
  (sources-check.md). У ds-q2 GitLab-колонку таблиці «що спільного» побудовано на цих цитатах, тому вона не
  підтверджена.
- **MAST (ds-q4):** «41% to 86.7%» і «organizational understanding» в анотації відсутні (grep 0). «+9.4%» і
  «+15.6%» теж (grep «+9.4%» → 0). Повний текст не відкрито: arXiv через браузер дав 403, HTML-версію не пробували.
- **LCI 2001 (ASCLCI2.pdf):** curl → 404. Цитати «Activities are made ready to be assigned by removing
  constraints.», «Maintain a backlog of ready work», «Target PPC=50%… PPC=90%» не звірено. Make-ready підтверджено
  іншою цитатою, з LCI 2023 (B13).
- **Теорія обмежень:** жодного першоджерела (tocico.org не знайдено). Wikipedia, дисертації й мета-аналіз Mabin &
  Balderstone (лише анотація в переказі DeepSeek) не відкрито. «П'ять кроків» — [unverified].
- **Не відкрито (цитати DeepSeek не звірено):** Linear «project lead» (lenny.productbuilder.net); Cursor/Truell
  (techflowpost, stratechery, YC, Fortune); Ramp (Redpoint, next.ramp.com); Shopify-меморандум про штат (inc.com,
  mashable); Johnny Ho (лише китайський переклад); Toyota UK glossary (kanban/heijunka); visilean (PPC-критика);
  MetaGPT arXiv 2308.00352; Cognition «Don't Build Multi-Agents» (була лише репродукція).
- **Висновки DeepSeek, а не джерел:** «pull не перенісся в агентів», «jidoka інвертовано», «Shopify = крок 2 TOC»,
  «найшвидші не мають писаної системи». Це аналітика моделі, тут не використано як факт. Тезу «80% дисперсії»
  тепер звірено напряму в Anthropic (C27), а не через beri.net.
- **Не знайдено зовсім:** Deel і Databricks (слова засновників про організацію роботи), OpenAI і Google
  (керівництва з агентів). Цифри росту з ds-q1 (Deloitte, Cloud 100) у цьому зведенні не використано й не звірено.

### F. Ціна

- 4 пошуки DeepSeek ≈ $0.0685 (0.0128 + 0.0137 + 0.0220 + 0.0200), розмова 20261028-144241. Сервер перевищив ліміт
  пошуків (6–8 при --uses 4–5), про це пише рядок «УВАГА» у raw/ds-q*.txt.
- Браузер agent-browser (10 сторінок у цій сесії + 15 раніше), curl (2 PDF, 1 arXiv) — $0. Платних інструментів
  цей під-агент не викликав.

### E2. Раунд 5 DeepSeek (докази для непідтвердженого) — звірка 2026-10-28
Метод: кожен «✅» DeepSeek (ds-q5.txt) — лише кандидат; доказ — `grep -F` цитати у тексті, який ми самі завантажили 28.10 (curl/pdftotext, пробіли нормалізовано; файли — stale-links-2810/pages5/). Рядки HTML — після зняття тегів.

| Пункт | URL | Цитата | grep | Статус |
|---|---|---|---|---|
| GitLab OKR | handbook.gitlab.com/…/engineering-managers/okrs/ | «The GitLab OKRs run for one quarter» · «monthly cadence» · «no more than nine Key Results» | 0 / 0 / 0 | DeepSeek: ✅ жива сторінка; curl 2026-10-28 → 404 («404 Page not found \| The GitLab Handbook»), grep 0 — СПРОСТОВАНО |
| TOC п'ять кроків (дзеркало) | bipulse.ru/app/dictionary/docs/five%20focusing%20steps | «A systematic five-step approach…» | — | мережа (curl 000, exit 6, повтор 000; також http://) — не відкривали |
| TOC (стаття) | repository.up.ac.za … pretorius_introducing_2014.pdf | «Many people required to perform tasks for which the reason no longer exists» | 1 | підтверджено (PDF — через DSpace API bitstream, бо вказаний URL віддає 404/SPA); але «IDENTIFY/SUBORDINATE/ELEVATE» заглавними — 0; з малою/Title-регістром Identify·Exploit·Subordinate·Elevate·«go back to step 1» — по 1 (кроки є, але не дослівним словниковим текстом TOCICO) |
| Ballard, backlog | navarra.fundacionlaboral.org …ARCH5bfd504d29db2.pdf | «Maintain a backlog of ready work» | 1 | підтверджено (pdftotext, 1,8 МБ) |
| Ballard, правило 3 | там само | «only if all constraints have been removed» (+ «Rule 3») | 1 (і 1) | підтверджено |
| PPC > 90% | repositorio.upn.edu.pe …Matos López.pdf | «este indicador este sobre el 90%» | — | мережа/доступ: 1-й запит 200 але 834 Б (SPA-оболонка без PDF), без isAllowed → 403 — не підтверджено, PDF не отримано |
| MAST числа (arxiv HTML v3) | arxiv.org/html/2503.13657v3 | «41%» · «86.7%» · «9.4%» · «15.6%» · «+9.4» · «+15.6» | 1 · 1 · 1 · 1 · 1 · 1 | підтверджено (DeepSeek казав «HTML не відкрився» — відкрився, це перше джерело) |
| MAST abs | arxiv.org/abs/2503.13657 | «41%», «86.7%» | 0 / 0 | не підтверджено на abs-сторінці (там лише анотація; числа є в HTML) |
| MAST по фреймворках | niteagent.com/blog/why-multi-agent-systems-fail-mast-taxonomy/ | «ChatDev fails 41.4%» · «MetaGPT fails 56.4%» · «Magentic-One fails 78.6%» · «OpenManus fails 86.7%» · «15.7%» · «0.85%» | 1·1·1·1·1·1 | підтверджено (третя сторона) |
| MAST (агрегатор) | moltbook-observatory…/a47896f9-… | «41% to 86.7%» · «9.4%» · «15.6%» | 1·1·1 | підтверджено (третя сторона) |
| Cognition | cognition.com/blog/multi-agents-working | «Context Rot is a well-documented phenomenon» · «…less intelligent decisions at longer and longer context lengths» · «how does a dumber model know it's at its limits» | 1·1·1 | підтверджено (першоджерело) |
| Cognition тред | x.com/walden_yan/status/2047054401341370639 | — | — | не відкривали (x.com пропущено за межами завдання) |
| Toyota UK glossary | toyotauk.com/…/glossary | «Heijunka means production levelling» · «Kanban is a tool used in the Toyota Production System» | 1 · 1 | підтверджено (DeepSeek це «не перевірив» — ми перевірили) |

Підсумок (лічильником): з 7 ✅-тверджень DeepSeek, які ми могли перевірити (GitLab, Pretorius, Ballard backlog, Ballard rule 3, PPC, niteagent, Cognition) — підтвердилось 5 (Pretorius частково: цитата про inertia так, кроки є лише в Title-регістрі, не дослівним словником), спростовано 1 (GitLab — 404), не отримано PDF 1 (PPC). Додатково підтверджено те, що DeepSeek не зміг: MAST arxiv HTML, Toyota UK, moltbook. Мережа: bipulse.ru недоступний (DNS/exit 6), x.com не відкривали.
