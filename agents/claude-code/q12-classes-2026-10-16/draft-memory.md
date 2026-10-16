<!-- Чернетка DeepSeek flash (deepseek-search.py --raw --no-search --file), 2026-10-16, запит claude-code для Q12 крок 1. Цитати звірено скриптом qcheck: див. README.md цієї теки. Поля «хто помітив» / «повтор після ліків» — судження делегата, НЕ звірені. -->
deepseek-search: перший шматок 1.1 с, усе 130.2 с
**K2. Записане правило не спрацювало в момент дії** — 10 випадків
Механізм: правило/конвенція вже лежить у пам'яті чи хуку, але в момент дії його не застосовано.
- 2026-09-20 · `memory/follow-or-explain-tool-routing-rules.md` · «ти вже не користуєшся діп сіком?» · помітив: користувач
- 2026-09-24 · `memory/commit-trailer-convention.md` · «the user chose to amend all four to the `Claude Opus 5.5` form» · помітив: користувач
- 2026-09-27 · `memory/deepseek-helpers-keep-conversation.md` · «це ти знов по частинам аналізуєш не повним текстом» · помітив: користувач
- 2026-09-28 · `memory/read-own-records-before-measuring.md` · «ти перечитуєш все підряд, витрачаються токени і контекст» · помітив: користувач
- 2026-09-29 · `memory/learn-tool-design-before-changing-usage.md` · «ми вже казали… потрібно перевіряти історію створення» · помітив: користувач
- 2026-10-03 · `memory/commit-trailer-convention.md` · «then dropped it for 8 commits» · помітив: DSH (після мого зауваження йому)
- 2026-10-03 · `memory/always-state-understanding-first.md` + `trees/pam-yat-proyektu.md` М11 · «яка кінцева ціль твоїх дій» · помітив: користувач
- 2026-10-07 · `memory/history-before-proposing-removal.md` · «ти знов не шукав навіть історію щоб дізнатись чому це зявилось» · помітив: користувач
- 2026-10-12 · `memory/commit-trailer-convention.md` · «привило що каже, що хто комітить?» · помітив: користувач
- 2026-10-13 · `memory/open-hinted-answer-before-acting.md` · «troubles-grep hook showed me 116 record titles, I opened 11» · помітив: агент (сам замірив)
Ліки: хуки troubles-grep/edit-gate, пам'ять, правило трейлера · Повтор після ліків: **так** (жовтневі випадки — після вересневих ліків).

**K1. Дія або висновок без перевірки (здогад як факт)** — 8 випадків
Механізм: гіпотеза/невідоме подається як факт, перевірку відкладено або замінено позначкою.
- 2026-09-23 · `memory/self-check-report-before-sending.md` · «ти знов сказав що не можливо і не перевірив» · помітив: користувач
- 2026-09-25 · `memory/resolve-uncertainty-before-reporting.md` · «розберись у тому що не впевнений» · помітив: користувач
- 2026-09-26 · там же · «як тільки з'являється припущення — маєш перевірити» · помітив: користувач
- 2026-09-27 · там же · «я не знаю що відповісти, ми це не перевіряли» · помітив: користувач
- 2026-10-01 · там же · «спочатку перевір все що не перевірене» · помітив: користувач
- 2026-10-03 · там же · «толку від того що ти записуєш що воно не перевірено?» · помітив: користувач
- 2026-10-13 · там же · «не можу перевірити це найпростіше і не відповідь» · помітив: користувач
- 2026-10-13 · `trees/pam-yat-proyektu.md` М11 (хвіст) · «Чому схудло — не перевірено» · помітив: рецензент (зовнішня рецензія e3a33280)
Ліки: скіл verify-before-show, правило «перевіряй або пропонуй перевірити» · Повтор після ліків: **так**.

**K3. Переказ/зведення губить або спотворює деталі** — 7 випадків
Механізм: у звіті число/твердження/цитата не збігається з джерелом або втрачає обмовку.
- 2026-09-23 · `memory/self-check-report-before-sending.md` · «a count ("18 commits") that the checking script never printed» · помітив: агент (при перевірці)
- 2026-09-26 · там же · «a model dismissed as "needs a GPU"» · помітив: користувач (спитав «чи все перевірено»)
- 2026-09-29 · `memory/deepseek-own-search-for-research.md` · «it also gave a narrower rule than the truth» · помітив: агент (порівняння двох пошуків)
- 2026-10-01 · `memory/self-check-report-before-sending.md` · «A command counter gave 10/2/3» · помітив: агент
- 2026-10-07 · `agents/dsh/mistakes-2026-10-07.md` №12 · «Незалежна перевірка знайшла розбіжність у підрахунку» · помітив: незалежна перевірка
- 2026-10-07 · там же №13 · «тест MoSCoW узятий із попереднього звіту» · помітив: незалежна перевірка
- 2026-10-13 · `memory/paraphrase-keeps-qualifiers.md` · «two of my "true" control cases in cases-v3 were false» · помітив: сліпа розмітка Sonnet + рада
Ліки: крок «числа» в session-close, скрипт check-links, правило «кваліфікатори списком» · Повтор після ліків: **так** (парафраз 13.10 — після ліків 26.09–07.10).

**K4. Дію/рішення ухвалено без прямого «так» користувача** — 7 випадків
Механізм: агент сам вирішує питання, що належить користувачу (гроші, обсяг, коміт), або читає «так» як згоду.
- 2026-09-26 · `memory/surface-implementation-decisions-before-applying.md` · «ти прийняв рішення сьогодні без мене, які могли змінити систему?» · помітив: користувач
- 2026-09-27 · `memory/user-owned-decisions-not-self-answered.md` · «питання створені для мене я маю на них відповідати» · помітив: користувач
- 2026-09-29 · `memory/surface-implementation-decisions-before-applying.md` · «мислення у прямому пошуку не вимикай, і чому не спитав?» · помітив: користувач
- 2026-10-01 · `memory/mixed-answer-is-not-approval.md` · «ти робиш дію на яку не отримав прямого так» · помітив: користувач
- 2026-10-01 · `memory/close-loose-ends-immediately.md` · «ті два процеси, з якими я хотів розібратись, висять» · помітив: користувач
- 2026-10-03 · `memory/user-owned-decisions-not-self-answered.md` · «ти сам вирішив що не запускаш навіщо відкладати» · помітив: користувач
- 2026-10-03 · там же · «а зараз перевірити, навіщо відкладати?» · помітив: користувач
Ліки: AskUserQuestion, ask-locks (push/deepseek), правило «кожна пропозиція — питання» · Повтор після ліків: **так** (тричі за 03.10, після ліків 26.09).

**K8. Черга, розмір і пріоритет «на око» (розфокус)** — 6 випадків
Механізм: порядок/клас задачі обирається чуттям, без критеріїв; кілька рівнів змішуються в одну чергу.
- 2026-09-26 · `memory/work-open-decisions-as-a-queue.md` · «щоб ми вирішували задачу в середині задачі» · помітив: користувач
- 2026-09-28 · `memory/work-multistep-topics-as-tree.md` · «знов не включився режим поярусної роботи і знов ловимо розфокус» · помітив: користувач
- 2026-09-29 · там же · «ми ловимо розфокус знов» · помітив: користувач
- 2026-10-01 · там же · «ти мені знов задаєш питання з різних рівнів» · помітив: користувач
- 2026-10-07 · `memory/criteria-never-by-eye.md` · «щоб не було на око ніде і ніколи» · помітив: користувач
- 2026-10-12 · там же · «як це можна класифікувати на око?» · помітив: користувач
Ліки: файл `poradnyk-kryteriyi-2026-10-07.md`, дерево-картки, правило черги · Повтор після ліків: **так**.

**K11. Твердження про адресу/властивість, якої агент не міг бачити** — 6 випадків
Механізм: названо рядок, шлях, тип файлу або стан без прогону команди чи з чужого боку.
- 2026-09-23 · `memory/self-check-report-before-sending.md` · «"two places" for a stale path that actually appeared in nine» · помітив: агент
- · `memory/dont-attribute-blocking-to-user.md` · «коли я заблокував, як я це зробив, мені здається ти це придумав» · помітив: користувач
- 2026-10-07 · `agents/dsh/mistakes-2026-10-07.md` №2 · «кількох шляхів: `tree-focus-hook.py.bak-20261003` названо «ярликом»» · помітив: незалежна перевірка
- 2026-10-07 · там же №10 · ««`~/.claude/logs/` немає» — і водночас лог у проєкті є» · помітив: незалежна перевірка
- 2026-10-07 · там же №11 · «Шукали фразу, якої в репозиторії немає» · помітив: незалежна перевірка
- 2026-10-07 · там же №13 · «Хибна адреса рядків + тест приписано не тому джерелу» · помітив: незалежна перевірка
Ліки: правило «паспорт факту» (сторона, яка бачить), check-links, зовнішня перевірка curl · Повтор після ліків: **невідомо** (усі DSH-випадки одного дня).

**K5. Зміну/фікс зроблено частково (сусідні файли, хвости, борг)** — 5 випадків
Механізм: правка не доходить до інших файлів, залежних місць або тимчасового стану.
- 2026-09-25 · `memory/close-loose-ends-immediately.md` · «а хвости потрібно зразу закривати» · помітив: користувач
- 2026-09-29 · `memory/learn-tool-design-before-changing-usage.md` · «three other files (launcher comment, proxy docstring, TROUBLES) described the old behaviour» · помітив: агент
- 2026-10-07 · `agents/dsh/mistakes-2026-10-07.md` №8 · «Тіньовий хук написано, але не підключено» · помітив: незалежна перевірка
- 2026-10-07 · там же №9 · «Незакомічені зміни без названого власника» · помітив: незалежна перевірка
- 2026-10-08 · `memory/fix-root-cause-of-every-bug.md` · «ами зараз щось локально змінюємо щоб потім на граблі настурати» · помітив: користувач
Ліки: hooks-smoke, рядок боргу «шлях — власник — дата» (пропозиція) · Повтор після ліків: **так**.

**K6. Позначка стану ≠ записи (назва замість вмісту)** — 4 випадки
Механізм: заголовок, номер або ярлик вважається доказом, що зміст є або робота зроблена.
- 2026-09-28 · `memory/check-content-not-titles.md` · «I matched them to the tree card by node title alone» · помітив: користувач
- 2026-09-30 · там же · «a different topic that only shared a keyword» · помітив: агент
- 2026-10-07 · `agents/dsh/mistakes-2026-10-07.md` №5 · «Handoff каже «ЗРОБЛЕНО І ЗАКОМІЧЕНО», а коміт з'явився після передачі» · помітив: незалежна перевірка
- 2026-10-07 · там же №15 · «трейлера немає в **8 з 10** останніх комітів» · помітив: агент (після питання про авторство)
Ліки: правило показувати рядок цільового тексту, grep замість назв · Повтор після ліків: **так**.

**K9. Дія або пропозиція без цілі проєкту** — 4 випадки
Механізм: крок робиться, але не названо, якій меті він служить; обсяг росте сам.
- 2026-09-20 · `memory/research-must-end-with-goal-conclusion-next-step.md` · «аналіз робився щоб щось зрозуміти, а не щоб просто поговорити» · помітив: користувач
- 2026-10-03 · `memory/every-action-needs-project-goal.md` · «яка кінцева ціль твоїх дій… навіщо» · помітив: користувач
- 2026-10-03 · там же · «і ціль записувати теж» · помітив: користувач
- 2026-10-13 · `memory/scope-side-questions-to-the-item.md` · «за метадані я казав виключно до розбору відео» · помітив: користувач
Ліки: «паспорт задачі» (Ціль/Звідки/Зв'язки), рядок «Мета:» в перевірці розуміння · Повтор після ліків: **так** (13.10 — після 03.10).

**K10. Коди/шифри без пояснення користувачу** — 3 випадки
Механізм: у відповідь переносяться коди G2.5/M4.4/T7 та таблиці без розшифровки.
- 2026-10-07 · `memory/ask-questions-one-at-a-time-plainly.md` · «розшифруй всі зашифровані назви» · помітив: користувач
- 2026-10-07 · `memory/short-main-point-first.md` · «tables full of node codes, then a glossary» · помітив: користувач
- 2026-10-15 · `memory/ask-questions-one-at-a-time-plainly.md` · «я вже казав що не розумію шифри» · помітив: користувач
Ліки: правило «прості слова, код лише в дужках», hook queue-voice — джерело кодів · Повтор після ліків: **так** (15.10 — після 07.10).

**K7. Записаний рецепт/крок скіла сприйнято як доказ** — 2 випадки
Механізм: рядок у TROUBLES або крок скіла виконується без перевірки, що він чинний і безпечний.
- 2026-10-07 · `memory/recorded-recipe-is-not-proof.md` · «I ran `git checkout --` on 4 l2s symlinks of DSH» · помітив: користувач
- 2026-09-25 · `memory/check-prescribed-steps-against-rules-and-history.md` · «ти перевіряв в інтернеті, в наших правилах чи історії?» · помітив: користувач
Ліки: обов'язковий рядок «перевірено чим»; аудит `presc-audit-2026-10-07.md` · Повтор після ліків: **невідомо**.

**K13. Висновок на розрізаному/усіченому матеріалі** — 2 випадки
Механізм: сесію або документ ділять чи скорочують, і рецензент не бачить джерел.
- 2026-09-25 · `memory/deepseek-helpers-keep-conversation.md` · «splitting into chunks produced 9 of 25 false findings» · помітив: агент
- 2026-10-07 · `memory/session-review-send-whole.md` · «I split the 372 KB export into two parts» · помітив: користувач
Ліки: правило «відправляти тільки цілим», mask лише персонального · Повтор після ліків: **невідомо** (правило з'явилося того ж дня, пізніших випадків у джерелі нема).

**Класи з 1 випадком (назви):**
«Застаріле число як підстава» (`resolve-uncertainty-before-reporting`, калібрування 03.10 — баланс $0.32); «Пошук підтвердження відсутності замість рішення» (`failure-triggers-solution-search`, 25.09 — NVIDIA/Frebuff); «Оцінка вартості без заміру» (`cost-discipline-sessions`, 13.10 — рада 11 агентів); «Приписування дії користувачу» (`dont-attribute-blocking-to-user`); «Змішано ролі агентів» (`always-show-who-is-speaking`); «Перевірка інструмента окремим викликом» (`verify-tools-in-real-use`, виняток 16.10); «Роздування пісочниці всередині проєкту» (`sandboxes-outside-project-then-promote`).

**п.5. Групи записів пам'яті, що описують ОДИН клас під різними назвами:**
- K1: `resolve-uncertainty-before-reporting.md` + `self-check-report-before-sending.md` + `recorded-recipe-is-not-proof.md`
- K2: `follow-or-explain-tool-routing-rules.md` + `read-own-records-before-measuring.md` + `learn-tool-design-before-changing-usage.md` + `history-before-proposing-removal.md` + `open-hinted-answer-before-acting.md` + `always-state-understanding-first.md` + `commit-trailer-convention.md` + `deepseek-helpers-keep-conversation.md`
- K3: `paraphrase-keeps-qualifiers.md` + `self-check-report-before-sending.md` + `session-review-send-whole.md`
- K4: `mixed-answer-is-not-approval.md` + `surface-implementation-decisions-before-applying.md` + `user-owned-decisions-not-self-answered.md` + `close-loose-ends-immediately.md` (калібрування)
- K5: `close-loose-ends-immediately.md` + `learn-tool-design-before-changing-usage.md` + `fix-root-cause-of-every-bug.md` + `check-prescribed-steps-against-rules-and-history.md`
- K8: `criteria-never-by-eye.md` + `work-open-decisions-as-a-queue.md` + `work-multistep-topics-as-tree.md`
- K9: `every-action-needs-project-goal.md` + `research-must-end-with-goal-conclusion-next-step.md` + `scope-side-questions-to-the-item.md`
- K10: `ask-questions-one-at-a-time-plainly.md` + `short-main-point-first.md` + `reports-as-live-tree.md`
- K11: `self-check-report-before-sending.md` + `dont-attribute-blocking-to-user.md`
- K13: `session-review-send-whole.md` + `deepseek-helpers-keep-conversation.md`

Класів: 12; випадків: 64; переглянуто: усе (усі секції «=== FILE …», зокрема `agents/dsh/mistakes-2026-10-07.md` і `trees/pam-yat-proyektu.md` М11). Назви класів і межі — моя чернетка; числа можуть змінитись після рознесення одного випадку між двома класами.

== Джерела (0):

== Розмова: 20261016-140742 | вх 55337 (з кешу 0) | вих 30620 | пошуків ?
== Ціна ≈$0.0267 (не пік; без вартості пошуків)
