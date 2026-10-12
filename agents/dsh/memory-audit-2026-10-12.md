# Аудит пам'яті: повторюваний скрипт — 2026-10-12

**Хто:** DSH (профіль tui), 2026-10-12, мета M16.1. **Що:** написано повторюваний
read-only аудит пам'яті `tools/memory-audit.py` і прогнано його по групі 3 звіту
`agents/dsh/audit-memory-2026-10-09.md`. Файли пам'яті не змінювались; у проєкті
створено рівно два файли — цей звіт і скрипт.

## 1. Що зроблено

| Що | Шлях |
|---|---|
| Скрипт (єдиний новий код) | `/data/data/com.termux/files/home/AgentReachProject/tools/memory-audit.py` |
| Цей звіт | `/data/data/com.termux/files/home/AgentReachProject/agents/dsh/memory-audit-2026-10-12.md` |
| Каталог пам'яті (константа в скрипті) | `/data/data/com.termux/files/home/.claude/projects/-data-data-com-termux-files-home-AgentReachProject/memory` |

Властивості скрипта (усе — з коду): python3, лише stdlib (`argparse, glob, os, re, sys`);
лише читання (`open(..., encoding="utf-8")`, жодного запису); шлях пам'яті —
абсолютна константа `MEM_DIR_DEFAULT` без `~` з fallback на `$HOME`-слаг і
env-перевизначенням `MEMORY_AUDIT_MEM`; корінь проєкту — `os.path.dirname(os.path.dirname(__file__))`
(скрипт лежить у `<root>/tools/`) з env-перевизначенням `MEMORY_AUDIT_ROOT`;
CWD і HOME не використовуються.

Запуск:

```
python3 /data/data/com.termux/files/home/AgentReachProject/tools/memory-audit.py
python3 /data/data/com.termux/files/home/AgentReachProject/tools/memory-audit.py --pairs
python3 /data/data/com.termux/files/home/AgentReachProject/tools/memory-audit.py --pairs --only <ім'я>,<ім'я>
python3 /data/data/com.termux/files/home/AgentReachProject/tools/memory-audit.py --list
```

Код виходу (як у `tools/check-links.py`): **0 — знахідок немає, 1 — є знахідки**
(в обох режимах, і у звіті, і в `--pairs`).

Для `build.py` (рядок 17 `memsim/build.py` бере `description` у покажчик):
`audit()` і `pairs()` — звичайні функції, що не пишуть нічого; файл має дефіс,
тому потрібен `importlib`:

```python
import importlib.util
spec = importlib.util.spec_from_file_location("memory_audit", "<root>/tools/memory-audit.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
findings = m.audit()      # [{'file','check','msg'}, ...]
items    = m.pairs()      # [{'name','desc','body','refs'}, ...]
```

Перевірки кодом: **(1)** наявність `name`, `description`, `metadata.node_type`
(+ `name` == ім'я файлу); **(2)** `description <= 300` символів (поріг лінту
Claude Code, рахується без лапок); **(3)** посилання на файли проєкту існують, а
`file:рядок` / `file:A-B` — у межах файлу; **(4)** `[[ім'я]]` веде на наявний
запис пам'яті. Моделей скрипт не викликає.

Формати посилань, які скрипт ловить (узяті з реального тексту пам'яті):
`BACKLOG:340-346` і `BACKLOG:90` (без розширення, розв'язується в `BACKLOG.md`),
`RULES.md:173-176`, `.baton/history/pass-69.json`, `trees/*.md`, `tools/*.py`,
`agents/.../*.md`, `.claude/settings.local.json`, `reference-analyzer/ANALYZER.md:25`.
Свідомо **не** вважаються посиланнями: плейсхолдери з `<...>`/`*`
(`.baton/history/pass-<N>.json`, `reference-analyzer/niches/<niche>/profile/`),
URL-и, проза зі слешем без розширення (`tools/solutions`, «nodes/tools») і
каталоги без розширення. Причина: інакше звіт тоне в хибних спрацюваннях
(перевірено синтетичним тестом, розділ 4).

## 2. Фактичний вивід запусків

### 2.1 Без аргументів

```
$ cd /data/data/com.termux/files/home/AgentReachProject && python3 tools/memory-audit.py
memory-audit: пам'ять /data/data/com.termux/files/home/.claude/projects/-data-data-com-termux-files-home-AgentReachProject/memory
memory-audit: проєкт /data/data/com.termux/files/home/AgentReachProject
memory-audit: файлів пам'яті 61, знахідок 2
 - [3] snapshot-baton-before-pass.md: шлях не існує: .baton/history/pass-69.json
 - [2] verify-external-critique-before-accepting.md: description 316 символів > 300
EXIT=1
```

Дві знахідки, обидві реальні:
* `.baton/history/pass-69.json` — доказ: `ls -la .baton/history/` показує
  `HANDOFF-pre-pass30.md, HANDOFF-pre-pass32.md, HANDOFF-pre-pass33.md, archive-2026-09-28/, pass-36.json`
  — файлу `pass-69.json` там немає (це той самий рядок групи 3 звіту 09.10);
* `verify-external-critique-before-accepting.md` — `len(description) = 316`
  (перевірено окремою командою; поріг 300).

Чого **немає** серед знахідок, хоч було у звіті 09.10: «3 файли без `node_type`»
(`mixed-answer-is-not-approval.md`, `supervise-dsh-with-delegated-corrections.md`,
`verify-tools-in-real-use.md`). Самотест: `файлів 61, з node_type 61` — тобто за
три дні після звіту ці записи вже отримали `node_type`, і звіт 09.10 у цій
частині застарів (ім'я `metadata.node_type` шукається вкладено, хибноправдивого
спрацювання немає — див. розділ 4).

### 2.2 `--pairs` (розмір і початок)

```
$ python3 tools/memory-audit.py --pairs | wc -l
958
$ python3 tools/memory-audit.py --pairs | wc -c
179378
$ python3 tools/memory-audit.py --pairs | head -30
# memory-audit --pairs: пам'ять /data/data/com.termux/files/home/.claude/projects/-data-data-com-termux-files-home-AgentReachProject/memory
# проєкт /data/data/com.termux/files/home/AgentReachProject
# записів: 61

========================================================================
### agreements-with-dsh-need-his-confirmation   (.../memory/agreements-with-dsh-need-his-confirmation.md)
ОПИС: When coordinating with the second agent DSH, never close an exchange with new changes he has not confirmed; ...
ТІЛО:
On 2026-09-30 the user asked me to consult DSH (the second agent in AgentReachProject) about an isolation trial ...
ПОСИЛАННЯ (шлях + цитовані рядки):
  — немає посилань на файли проєкту
```

Приклад пари з цитатою (скорочено, з того ж запуску):

```
### always-show-who-is-speaking   (.../memory/always-show-who-is-speaking.md)
ПОСИЛАННЯ (шлях + цитовані рядки):
  * script-agent/AGENT.md -> файл існує, 395 рядків (без :N)
  * reference-analyzer/ANALYZER.md -> файл існує, 321 рядків (без :N)
```

### 2.3 `--pairs` по 7 записах групи 3 (ключові фрагменти)

```
$ python3 tools/memory-audit.py --pairs --only work-multistep-topics-as-tree,deepseek-own-search-for-research,snapshot-baton-before-pass,offer-external-session-review,read-own-records-before-measuring,fix-root-cause-of-every-bug,deepseek-helpers-keep-conversation
# записів: 7
...
### deepseek-own-search-for-research ...
  * BACKLOG.md -> файл існує, 1622 рядків (без :N)
  * tools/deepseek-search.py -> файл існує, 243 рядків (без :N)
  * BACKLOG:340-346:
      340:     `.claude/skills/verify-before-show/SKILL.md` — тригер: план, що
      341:     змінює файли/правила, або висновок із числами/цитатами; витягти
      342:     твердження + опору (файл/команда/URL) → DeepSeek факти, Agent
      343:     судження → вердикт із цитатою → фільтр «опора є/нема» (не стиль).
      344:     Не для звичайних відповідей, нічого не блокує.
      345:   - Етап 3: TROUBLES (результати), рядок-вказівник у RULES.md +
      346:     RULES-WHY — окремим «так»; окремі коміти, відкат перевірити.
...
### snapshot-baton-before-pass ...
  * .baton/baton.json -> файл існує, 341 рядків (без :N)
  * TRASH.md -> файл існує, 217 рядків (без :N)
  * HANDOFF.md -> файл існує, 352 рядків (без :N)
  * .baton/ledger.jsonl -> файл існує, 188 рядків (без :N)
  * RULES.md -> файл існує, 270 рядків (без :N)
  * .baton/history/pass-69.json -> НЕ ІСНУЄ: .baton/history/pass-69.json
...
### fix-root-cause-of-every-bug ...
  * reference-analyzer/ANALYZER.md:25:
      25: - **Чесність про межі.** ... (текст 25-го рядка)
  * RULES.md -> файл існує, 270 рядків (без :N)
...
memory-audit: знахідок 2 (код виходу 1)
EXIT=1
```

Пара `BACKLOG:340-346` — це і є ворота, рядок 2: цитовані рядки 340–346
говорять про скіл `verify-before-show`, а не про пошук DeepSeek.

### 2.4 Незалежність від CWD / HOME / інтерпретатора

```
$ cd / && python3 /data/.../tools/memory-audit.py
memory-audit: пам'ять /data/data/com.termux/files/home/.claude/projects/-data-data-com-termux-files-home-AgentReachProject/memory
memory-audit: проєкт /data/data/com.termux/files/home/AgentReachProject
memory-audit: файлів пам'яті 61, знахідок 2
 - [3] snapshot-baton-before-pass.md: шлях не існує: .baton/history/pass-69.json
 - [2] verify-external-critique-before-accepting.md: description 316 символів > 300
EXIT=1

$ cd /root && python3 /data/.../tools/memory-audit.py            # те саме, EXIT=1
$ cd / && HOME=/nonexistent python3 /data/.../tools/memory-audit.py   # те саме, EXIT=1
$ cd /root && env -u HOME python3 /data/.../tools/memory-audit.py     # те саме, EXIT=1
$ pwd; echo HOME=$HOME
/root
HOME=/root
$ python3 -c "import sys;print(sys.version.split()[0], sys.executable)"
3.14.4 /usr/bin/python3
$ /data/data/com.termux/files/usr/bin/python3 tools/memory-audit.py --list | head -3
agreements-with-dsh-need-his-confirmation.md
always-show-who-is-speaking.md
always-state-understanding-first.md
EXIT=0
```

Тобто вивід ідентичний із `CWD=/`, `CWD=/root`, без `HOME` і з підміненим `HOME`,
а також під **termux-інтерпретатором** (`/data/data/com.termux/files/usr/bin/python3`,
код 0). Робочий інтерпретатор тут — proot-Ubuntu `3.14.4 /usr/bin/python3`.

## 3. Ворота: 8 рядків групи 3 звіту 09.10

Рядки взяті дослівно з таблиці «3. Мертві посилання й застарілі факти (7)»
звіту `agents/dsh/audit-memory-2026-10-09.md` (у таблиці справді **8 рядків**,
заголовок каже «(7)» — це і є та розбіжність, яку не виправляли).

| # | Рядок із звіту 09.10 (дефект) | Вердикт сьогодні |
|---|---|---|
| 1 | `work-multistep-topics-as-tree.md` — секція «ЯК УВІМКНУТИ (не вирішено)» не в названій картці, а в `trees/derevo-i-golograma.md:26` | **видно в --pairs**: тіло друкує фразу «ЯК УВІМКНУТИ (не вирішено)» і файл-ціль `trees/pidrozdil-deepseek.md -> файл існує, 619 рядків`; звірка — grep фрази по картці (кодом не ловиться: обидва файли існують, а «де живе розділ» — семантика) |
| 2 | `deepseek-own-search-for-research.md` — посилання «BACKLOG:340-346» веде не туди | **видно в --pairs**: пара друкує `BACKLOG:340-346` і видно, що це розділ про `verify-before-show`, а не про пошук; кодом не ловиться — діапазон у межах файлу (1622 рядки), а «не той розділ» — зміст |
| 3 | `snapshot-baton-before-pass.md` — `pass-69.json` уже не в `.baton/history/` | **знайдено кодом**: `- [3] snapshot-baton-before-pass.md: шлях не існує: .baton/history/pass-69.json` (і в `--pairs` — `НЕ ІСНУЄ`) |
| 4 | `snapshot-baton-before-pass.md` — умова видалення знімків застаріла: RULES.md:173-176 вимагає спершу `baton-diff` | **не ловиться кодом**: у записі `RULES.md` без `:N` (перевіряти межі нема чого), а сама умова — проза; `--pairs` дає тіло і назву файлу, далі ручне відкриття `RULES.md:173-176`. Доказ, що вимога існує: `sed -n '169,176p' RULES.md` → «Після baton_pick_up — python3 tools/baton-diff.py … Лише потім старіші знімки прибрати — з записом у TRASH.md до rm/mv» |
| 5 | `offer-external-session-review.md` — каже ділити стенограми; рішення 2026-10-07 — надсилати цілим | **видно в --pairs**: обидва записи (`offer-external-session-review` і `session-review-send-whole`) в одному дампі з тілами; суперечність видно очима моделі. Кодом не ловиться: це міжзаписова суперечність, жодного битого шляху немає (у тілі лише `RULES.md`, існує) |
| 6 | `read-own-records-before-measuring.md` — твердить, що карти знань немає — вона є | **не ловиться кодом**: твердження прозою («the missing map of project knowledge»), згадка «kb-map» — без `tools/`, тому мій фільтр не вважає це посиланням; `--pairs` показує тіло, але звірка — окремою перевіркою `tools/kb-map.py` |
| 7 | `fix-root-cause-of-every-bug.md` — каже, що у версії 2.1.280 немає `prompt-audit`; встановлено 2.1.273 | **не ловиться кодом**: версія — факт поза проєктом (джерело — `package.json` встановленого claude-code); `--pairs` друкує тіло з «the installed 2.1.280 does not seem to have it». Доказ фактичної версії (моя команда, не звіт 09.10): `/data/data/com.termux/files/usr/lib/node_modules/@anthropic-ai/claude-code/package.json -> 2.1.273` |
| 8 | `deepseek-helpers-keep-conversation.md` — каже, що замок на `deepseek-reply` — відкрите рішення; замок уже стоїть | **не ловиться кодом**: стан замка живе в `.claude/settings.local.json` і в логіці хука, а не в адресах файлів; у записі шляхи `trees/pidrozdil-deepseek.md` і `TROUBLES.md` живі, тому знахідок немає. `--pairs` показує тіло з «`deepseek-reply` is not covered by the ask-lock (open decision)» |

Підсумок воріт: **1 з 8 — знайдено кодом** (рядок 3), **2 з 8 — видно в `--pairs`**
(рядки 2 і 5, плюс 1 як тіло+файл-ціль), **4 з 8 — не ловиться кодом** із
названою причиною (рядки 4, 6, 7, 8). Інші **5 рядків** таблиці (не в групі 3)
сьогодні кодом не підтверджуються: це суперечності опис↔тіло і міжзаписові —
їх може звіряти лише модель за `--pairs`.

## 4. Самотест перевірок (щоб «працює» було доказом)

Синтетичний запис у пам'яті підмінено на рівні читання (на диск нічого не писано):

```
ЗНАХІДКА 3 fake-note.md | рядки RULES.md:99999-100001 поза межами (у файлі 270 рядків)
ЗНАХІДКА 3 fake-note.md | шлях не існує: trees/nope.md
ЗНАХІДКА 4 fake-note.md | [[missing-link]] — такого запису пам'яті немає
node_type на смітті: None | на справжньому: memory
REF 'RULES.md:99999-100001' -> start 99999 end 100001; REF 'trees/nope.md'; REF '.claude/settings.local.json:5'; REF 'trees/pidrozdil-deepseek.md'
```

Отже перевірки (1)–(4) справді реагують, а проза (`tools/solutions`), URL-и
(`api-docs.deepseek.com/guides/thinking_mode`), плейсхолдер `.baton/history/pass-<N>.json`
і самі `[[...]]` у список посилань не потрапляють. Робочий прогон по всій пам'яті:
`файлів 61, з node_type 61, [[лінків]] 14, посилань на файли 78` — усі 14 лінків
живі, з 78 посилань бите одне (`pass-69.json`).

## 5. Співвідношення з `tools/check-links.py`, група 9

Група 9 (`tools/check-links.py:128-132`) перевіряє в пам'яті **лише** шляхи в
лапках, що починаються з `script-agent/`, `reference-analyzer/`, `tools/`, `.claude/`,
і робить це через `exists_glob` (плейсхолдери `<...>` → `*`). Виміряний перетин
(команда нижче): у пам'яті 25 різних шляхів; група 9 бачить 4; перетин — 3
(`.claude/settings.local.json`, `reference-analyzer/ANALYZER.md`, `script-agent/AGENT.md`);
лише memory-audit — 22; лише група 9 — 1 (`reference-analyzer/niches/<niche>/profile/`,
плейсхолдер, який я свідомо пропускаю).

```
memory-audit: різних шляхів у пам'яті = 25
група 9 check-links: різних шляхів = 4 ['.claude/settings.local.json', 'reference-analyzer/ANALYZER.md', 'reference-analyzer/niches/<niche>/profile/', 'script-agent/AGENT.md']
перетин (є в обох) = 3
лише memory-audit = 22 ['.baton/baton.json', '.baton/history/pass-69.json', '.baton/ledger.jsonl', 'BACKLOG', 'BACKLOG.md', 'CONTEXT.md', 'HANDOFF.md', 'README.md', 'RULES-WHY.md', 'RULES.md', 'TRASH.md', 'TROUBLES.md', 'agents/claude-code/dsh-direct-channel.md', 'agents/claude-code/poradnyk-kryteriyi-2026-10-07.md', 'agents/claude-code/presc-audit-2026-10-07.md', 'tools/deepseek-search.py', 'tools/kb-map.py', 'tools/session-export.py', 'trees/derevo-i-golograma.md', 'trees/pam-yat-proyektu.md', 'trees/pidrozdil-deepseek.md', 'trees/yakist-roboty-agentiv.md']
лише група 9 = 1 ['reference-analyzer/niches/<niche>/profile/']
```

**Перетин:** три шляхи перевіряються двічі, і це не «тихе дублювання»: група 9 —
це session-close-перевірка всього проєкту (вона ганяє ще хуки, settings, git),
а memory-audit — окремий повторюваний прогін по пам'яті. Розходження свідомі:
* memory-audit **не** повторює групу 9 «як є», а розширює її (у 22 шляхи, яких
  група 9 не бачить узагалі: `trees/`, `agents/`, `.baton/`, кореневі `*.md`);
* memory-audit додає те, чого в групі 9 немає принципово: `file:рядок` у межах
  файлу, наявність `name`/`description`/`metadata.node_type`, поріг 300 символів,
  `[[ім'я]]` на наявний запис;
* група 9 має один шлях, якого memory-audit не перевіряє (плейсхолдер
  `reference-analyzer/niches/<niche>/profile/`): тут група 9 сильніша;
* конфлікту немає: якщо обидва скрипти бачать один шлях, вони дадуть те саме
  «існує/немає» (обидва читають від кореня проєкту).

Пропозиція (не робив): у `session-close` викликати memory-audit **після**
check-links як окремий крок — тоді групу 9 з нього можна прибрати, щоб не
тримати дві реалізації одного й того самого.

## 6. Питання до користувача

Записано текстом, без діалогу (як просили в межах задачі):

1. Поріг 300 рахую на значенні **без лапок**. Якщо Claude Code рахує з лапками —
   треба змінити формулу (сьогодні це впливає лише на межові описи).
2. `name` != ім'я файлу зараз **вважаю** знахідкою перевірки (1). Якщо така
   розбіжність допустима — приберу.
3. Посилання без розширення (`agents/deepseek-search`, каталоги `trees/`) не
   перевіряю, щоб не ловити прозу (`tools/solutions`). Чи потрібен окремий
   суворіший режим `--strict`?
4. `description` у `verify-external-critique-before-accepting.md` = 316 символів.
   Скоротити опис (правка пам'яті — це робота claude-code, не моя) чи підняти
   поріг?
5. Три записи зі звіту 09.10 («без `node_type`») сьогодні мають `node_type` —
   хтось їх уже поправив? Звіт 09.10 у цій частині застарів.
6. Канонічна схема лишається невстановленою: 5 записів мають `type: feedback`
   поряд із `metadata.node_type`. Перевіряти це кодом (як зараз) чи чекати
   рішення про канон?
7. Чи має `build.py` не просто показувати `description`, а **падати** на
   знахідках `audit()` (імпорт через `importlib`), чи достатньо покажчика?
8. Кому належить запуск: `session-close` (claude-code) чи мій чек-ліст (DSH)?
   Від цього залежить, чи вписувати виклик у `RULES.md`/`settings`.

## 7. Межі, яких дотримано

Файли пам'яті не змінювались (усі операції — читання). Створено рівно два файли
(скрипт і цей звіт). `TROUBLES.md`, `BACKLOG.md`, `trees/*`, `tools/check-links.py`,
`RULES.md` не чіпано. `git add`/`commit`/`baton_pass` не робились. Під-агенти не
спавнились. Розширені атрибути/ярлики не «лагодились». Діалогових питань не
задано — усі відкриті пункти в розділі 6.

ГОТОВО — [dsh, 14:22]
