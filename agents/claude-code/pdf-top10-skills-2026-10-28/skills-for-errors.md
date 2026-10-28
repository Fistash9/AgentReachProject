# Скіли під повторювані помилки (Р1, Р4, Р5, Р9, Р10) — тільки пошук, нічого не встановлено
— [claude-code, 2026-10-28]

Мета: знайти готові скіли, що прибирають класи з реєстру помилок, де наші ліки не діють. Фільтр (PDF «10 AI Skills», стор. 13): «Яку повторювану помилку цей скіл має прибрати? Якщо відповіді немає — встановлювати рано».

## 1. Класи (tools/error-registry.py, CLASSES, рядки 66–90; замір 27.10)
- Р1 (60) — «Дія чи висновок до перевірки»: сказав/зробив, не перевіривши.
- Р4 (15) — «Зроблено частково / латка замість системи»: лишив хвости, лікує симптом.
- Р5 (13) — «Розфокус: черга й пріоритет на око»: порядок задач без критеріїв.
- Р9 (32) — «Не той шлях чи інструмент; свої записи не підняв»: робить сам замість агентів/скілів/готового.
- Р10 (12) — «Урок не засвоєно: не вчиться й не запам'ятовує».

## 2. Що вже є в нас (ls .claude/skills/)
deepseek-search, grill-me, grilling, llm-council, request-brief, session-close, unlazy, verify-before-show.
BACKLOG «Скіли за зразком» (Далі №15): скіл-диригент «зміна механізму»; superpowers — лише за правилом «Перед ВСТАНОВЛЕННЯМ». Дублі не пропоную: verify-before-show (Р1), request-brief, unlazy.

## 3. Кандидати (зірки/останній коміт — gh api, 28.10)
Репо: mattpocock/skills 305103★, коміт 2026-10-27; obra/superpowers 306713★, коміт 2026-10-21; anthropics/skills 184327★, коміт 2026-10-09.

### Р1
1. verification-before-completion (obra/superpowers). Цитата: «NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE» і «If you haven't run the verification command in this message, you cannot claim it passes.» Прибирає: перед «готово/працює» змушує назвати команду-доказ, запустити, прочитати вивід. НЕ спрацює: чистий текст; у нас вже є claimcheck + verify-before-show + правило «Кожне твердження спирається на вивід»; агент пропускав і їх. Заточений під тести/білд, не під «твердження про файли/числа».
2. ask-matt (mattpocock). Цитата: «Before stating what a skill does or recommending a step be skipped, read that skill's SKILL.md: the summaries here are for orientation only.» Лише один рядок, прив'язаний до його репо-маршрутизатора. Слабка.
3. discernment-nudge (anthropics). Цитата: «append 2-3 short follow-up questions … Do this at most once per conversation.» Це питання до користувача, а не перевірка агентом. Не про нашу помилку.

### Р4
1. verification-before-completion (obra) — таблиця «Bug fixed | Test original symptom: passes | Code changed, assumed fixed». Ловить «виправив = перевірив», але не «латка замість системи». Часткова.
2. retro (mattpocock). Цитата: «You are suggesting improvements to the coding agent's environment to improve future runs.» + «are there automated checks that could catch errors the agent made?» Пропонує автоперевірку замість латки — це наш підхід (замок/хук), але скіл лише пропонує, `disable-model-invocation: true` (викликає людина).
3. Немає третього.

### Р5
1. wayfinder (mattpocock). Цитата: «Plan a huge chunk of work (more than one agent session can hold) as a shared map of decision tickets on your issue tracker, and resolve them one at a time until the way to the destination is clear.» Дає карту рішень замість черги на око. НЕ спрацює: прив'язаний до issue tracker (у нас BACKLOG/дерево), `disable-model-invocation`; критеріїв пріоритету не задає — лише послідовність рішень. Слабка/часткова.
2. triage (mattpocock) — «Move issues … through a small state machine of triage roles»; теж issue tracker. Слабка.
3. Немає.

### Р9
1. using-superpowers (obra). Цитата: «If you think there is even a 1% chance a skill might apply to what you are doing, you ABSOLUTELY MUST invoke the skill.» Прямо б'є в «не скористався скілом/інструментом». НЕ спрацює: чистий текст-вказівка; ми вже маємо хуки-підказки (роутинг-нагадування) і агент їх пропускає; тягне весь superpowers (BACKLOG: лише за правилом «Перед ВСТАНОВЛЕННЯМ»); агресивний тон може конфліктувати з нашими «ворота y/n».
2. dispatching-parallel-agents (obra). Цитата: «Dispatch one agent per independent problem domain. Let them work concurrently.» Підштовхує віддавати агентам, а не робити самому. НЕ спрацює: описує, як віддавати, а не змушує; у нас це вже правило + нагадування.
3. ask-matt (mattpocock) — «You don't remember every skill, so ask.» Маршрутизатор лише по його скілах. Для нас не підходить напряму; ідею (маршрутизатор «яка задача → який скіл/інструмент») можна взяти самим.

### Р10
1. retro (mattpocock) — див. вище; дає «що змінити в середовищі після сесії», ближче до ліків, ніж «запам'ятай». Часткова.
2. diagnosing-superpowers (obra). Цитата: «Every finding cites path:line. No citation, no finding. Every number comes from the transcript or from a command you ran, never from memory.» Розбір минулої сесії з доказами; заточений під баги superpowers. Часткова/слабка.
3. Немає: скіл, що змушує агента вчитись між сесіями, не знайдено (механізм пам'яті — не скіл, а MEMORY/хуки, які в нас є).

## 4. Таблиця
| Клас | Кандидати | Відповідність |
|---|---|---|
| Р1 | verification-before-completion (obra); ask-matt, discernment-nudge — слабкі | часткова (текст-нагадування, дублює наше) |
| Р4 | verification-before-completion; retro (mattpocock) | часткова |
| Р5 | wayfinder; triage (mattpocock) | часткова/слабка (issue tracker) |
| Р9 | using-superpowers; dispatching-parallel-agents (obra) | часткова (тільки текст; наші хуки-нагадування вже пропускаються) |
| Р10 | retro; diagnosing-superpowers | часткова/слабка; прямого немає |
Прямої відповідності (скіл, що сам прибирає клас) — жодної.

## 5. Висновок і межі пошуку
- Усі кандидати — текст-інструкції; наші провальні класи — там, де нагадування агент пропускає. Скіл без хука/замка той самий механізм, що й наше правило. За фільтром «яку помилку прибере?» — жоден не дає нового механізму; найближчий — verification-before-completion (Р1/Р4) і ідея retro (Р4/Р10: «замінювати правило автоперевіркою»).
- Не вдалося: skills.sh через curl повернув лише «Redirecting...» (каталог не переглянуто; WebFetch не пробував); gh search code не використовував; пошук репо за «claude skills» дав лише добірки (awesome-*, alirezarezvani/claude-skills 380 скілів — не переглядав, [не перевірено]); тематичні запити (lessons/self-improving) релевантного не дали. Повний SKILL.md прочитано лише частково (початок ~1500 байт кожного + retro 20–44), цитати вище дослівні з прочитаного.
