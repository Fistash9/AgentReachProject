# Два тригери «момент + ворота»: рецензія перед комітом коду і порядок дебагу на збій (2026-10-25)

Мета (користувач 25.10, дослівно): «ти знайшов скіли які мали бути використані і знов їх не примінив і навіть не зробив для них опис і виклик по прикладу робочих зв'язок?» — [claude-code, 2026-10-25]
Стан: ПІДГОТОВЛЕНО, НЕ ЗАСТОСОВАНО. У `.claude/` і налаштуваннях нічого не змінено; усе зроблено на копіях у `/data/data/com.termux/files/usr/tmp/triggers-kod-zbiy/` (там же `tests.py`, `bt1.py`, `bt2.py`, `patch.py`, `t1.diff`, `t2.diff`). Служить вузлу «Якість роботи агентів» (дебаг/якість коду: `debug-yakist-2026-10-25.md`).

Зразок зв'язки (з роботи): verify-before-show — момент «план змінює файли» + замок ask-gate-hook; session-close — момент «закриваємо» + фраза-тригер. Тут: момент, що настає сам (коміт коду; другий збій підряд) + підказка/ворота саме в ньому. Обидва — підказка/запит, не заборона (RULES-WHY: ворота-дозвіл, не заборона).

## Тригер 1. /code-review перед комітом коду

### Задум
Момент: `git commit`, у якому є `.py/.sh/.mjs`. Ворота: у журналі сесії після останнього УСПІШНОГО коміту нема виклику Skill `code-review`/`simplify` (або слеш-команди користувача, або під-агента `code-review`) → `ask` з текстом «запусти /code-review <файл>». Виняток: у останньому рішенні користувача «без рецензії». Чому в commit-consent-hook, а не окремий хук: хук уже розбирає команду коміту, читає журнал сесії (last_decision) і має логер/тести; окремий хук дублював би RE_COMMIT і обхід лапок/heredoc (клас TROUBLES 2026-09-23 «Блокуючі хуки на regex по сирому рядку»). Це ДОДАТОК після перевірки згоди: якщо «коміту» нема — спрацьовує старий deny, нова гілка не чіпається.

Історія хука прочитана цілим (217 рядків) і `git log -p` (останній зміст: коміт 918dade, ask→deny; до того 2026-10-16 створення, 10-18 прибрано перевірку вузла, 10-19 bypass/М2). TROUBLES: `grep -n commit-consent` → записи 2026-10-16 «Замок комітів», 10-19 (bypass, М2), «Висновки сесії cfca89fe» п.1 (запити погоджували за звичкою → тому тут ask лише для НОВОЇ гілки, але див. ризик 1).

### Дрібні правки копії (3 місця + нові функції)
- `LOG` береться з env `COMMIT_CONSENT_LOG` (щоб тести не писали у справжній лог) — безпечно, за замовчуванням як було.
- `import subprocess`.
- Нові `code_files_in_commit` (індекс; з `-a` — змінені відстежувані; з `git add` у тій самій команді — аргументи add, для `-A`/`.` — `git status --porcelain`), `review_seen`, `review_gate` (будь-яка помилка → тиша) і виклик у `main` після циклу згод.

Diff (повний, `t1.diff`):
```diff
--- commit-consent-hook.orig.py	2026-10-25 10:06:06.805851912 +0200
+++ commit-consent-hook.py	2026-10-25 10:06:06.865851912 +0200
@@ -27,11 +27,12 @@
 import json
 import os
 import re
+import subprocess
 import sys
 import time
 
 PROJECT = "/data/data/com.termux/files/home/AgentReachProject"
-LOG = os.path.join(PROJECT, ".claude", "logs", "commit-consent.log")
+LOG = os.environ.get("COMMIT_CONSENT_LOG") or os.path.join(PROJECT, ".claude", "logs", "commit-consent.log")
 RE_COMMIT = re.compile(r"(?:^|[;&|(\n]|\$\()\s*git(?:\s+-C\s+\S+|\s+-c\s+\S+)*\s+commit\b")
 RE_YES = re.compile(r"коміт|закоміт|commit", re.I)
 RE_NO = re.compile(r"(?:не|без|ні,?)\s+(?:за)?коміт|не\s+commit|don'?t\s+commit|no\s+commit", re.I)
@@ -164,6 +165,78 @@
 
 
 
+# ТРИГЕР «рецензія перед комітом коду» (2026-10-25, ворота за зразком verify-before-show): коміт, у якому є
+# .py/.sh/.mjs, без виклику Skill code-review/simplify після попереднього успішного коміту → запит (ask), не заборона.
+RE_CODE = re.compile(r"\.(?:py|sh|mjs)$")
+REVIEW_SKILLS = ("code-review", "simplify")
+RE_REVIEW_SKIP = re.compile(r"без\s+рецензі|skip\s+review|no\s+review", re.I)
+RE_SLASH_REVIEW = re.compile(r"<command-name>\s*/?(?:code-review|simplify)\b")
+
+
+def code_files_in_commit(cmd, cwd):
+    """.py/.sh/.mjs, що потраплять у цей коміт: індекс; з -a/--all — і змінені відстежувані; з git add у тій самій
+    команді — аргументи add (для -A / . — усі зміни git status)."""
+    c = re.sub(r"\"(?:[^\"\\]|\\.)*\"|'[^']*'", " ", RE_HEREDOC.sub(" ", cmd))
+    def git(*a):
+        return subprocess.run(["git", "-C", cwd, *a], capture_output=True, text=True, timeout=5).stdout.splitlines()
+    names = set(git("diff", "--cached", "--name-only"))
+    m = re.search(r"\bcommit\b([^;&|\n]*)", c)
+    if m and re.search(r"(?<!\S)-[a-zA-Z]*a[a-zA-Z]*(?!\S)|--all\b", m.group(1)):
+        names |= set(git("diff", "--name-only"))
+    for add in re.findall(r"\bgit(?:\s+-C\s+\S+)?\s+add\b([^;&|\n]*)", c):
+        toks = [t for t in add.split() if not t.startswith("-") or t in ("-A", "--all")]
+        if any(t in (".", "-A", "--all") for t in toks):
+            names |= {l[3:].strip() for l in git("status", "--porcelain")}
+        else:
+            names |= set(toks)
+    return sorted(n for n in names if RE_CODE.search(n))
+
+
+def review_seen(transcript_path):
+    """Чи був виклик code-review/simplify (Skill, /команда користувача, під-агент code-review) після останнього
+    УСПІШНОГО git commit у журналі сесії."""
+    seen, pend = False, set()
+    with open(transcript_path, encoding="utf-8") as f:
+        for line in f:
+            try:
+                d = json.loads(line)
+            except ValueError:
+                continue
+            c = (d.get("message") or {}).get("content")
+            blocks = [{"type": "text", "text": c}] if isinstance(c, str) else (c or [])
+            for b in blocks:
+                if not isinstance(b, dict):
+                    continue
+                if b.get("type") == "tool_use":
+                    inp = b.get("input") or {}
+                    if b.get("name") == "Skill" and str(inp.get("skill", "")).split(":")[-1] in REVIEW_SKILLS:
+                        seen = True
+                    elif b.get("name") == "Agent" and "code-review" in str(inp.get("subagent_type", "")):
+                        seen = True
+                    elif b.get("name") == "Bash" and RE_COMMIT.search(str(inp.get("command", ""))):
+                        pend.add(b.get("id"))
+                elif b.get("type") == "text" and d.get("type") == "user" and RE_SLASH_REVIEW.search(b.get("text", "")):
+                    seen = True
+                elif b.get("type") == "tool_result" and b.get("tool_use_id") in pend and not b.get("is_error"):
+                    seen = False
+    return seen
+
+
+def review_gate(data, cmd, last):
+    """Текст запиту, якщо потрібна рецензія; інакше None. Будь-яка помилка — None (тиша)."""
+    try:
+        if RE_REVIEW_SKIP.search(last):
+            return None
+        files = code_files_in_commit(cmd, data.get("cwd") or PROJECT)
+        if not files or review_seen(data["transcript_path"]):
+            return None
+        return ("Коміт коду без рецензії: у комітi " + ", ".join(files[:5]) + " і немає виклику code-review/simplify "
+                "після попереднього коміту. Запусти /code-review " + files[0] + " (або /simplify), виправ знахідки й "
+                "коміть знову. Дозволити без рецензії? «Ні» — спершу рецензія.")
+    except Exception:
+        return None
+
+
 REASONS = {
     "commit": ("Коміт заборонено: у останньому рішенні користувача немає слова «коміт» (RULES-WHY 2026-10-16: дозвіл "
                "на роботу ≠ дозвіл на коміт; з 2026-10-23 — заборона замість запиту). Спитай віконцем «…і закомітити?»."),
@@ -205,6 +278,11 @@
             log(data, ("" if k == "commit" else k + ":") + ("ok" if ok else "deny"), last)
             if not ok:
                 return out("deny", REASONS[k])
+        if "commit" in kinds:
+            msg = review_gate(data, cmd, last)
+            if msg:
+                log(data, "review-ask", cmd)
+                return out("ask", msg)
     except Exception as ex:  # збій розбору для важливої дії — запит, не тиша (2026-10-23)
         out("ask", f"Замок згоди ({', '.join(kinds)}) не зміг перевірити рішення користувача: "
                    f"{type(ex).__name__}. Дозволити?")
```

### Тести (обидва боки; `python3 tests.py`, відома відповідь)
Мають спрацювати (ask): 1 `.py` без рецензії; 4 рецензія була ДО попереднього успішного коміту; 9 `commit -am` зі зміненим відстежуваним `.sh`.
Мають мовчати: 2 `.py` + Skill code-review; 3 лише `.md`; 5 рецензія, потім НЕВДАЛИЙ коміт (рецензія зберігається); 6 «без рецензії» від користувача; 7 слеш-команда користувача; 10 не-коміт (ls); 11 під-агент code-review; 12 `-m 'fix a.py'` при staged `.md` (текст у лапках не рахується).
Старе не зламано: 8 нема слова «коміт» → deny як раніше.
Результат: 12/12 для тригера 1 (разом з тригером 2: 20/20 PASS). Не зроблено: прогін `tools/hooks-smoke.py` і мутант-перевірка на копії (поза межею 25 викликів) — зробити при застосуванні.

### Бектест (`bt1.py`, 262 журнали сесій, відтворення поведінки хука по кожному успішному коміту; файли коміту — `git show --numstat`)
- Успішних комітів у журналах: 103 (хешів нерозв'язаних 0).
- Комітів із `.py/.sh/.mjs`: 20. З них із рецензією в відрізку: 0. Спрацювань: 20 (19% усіх комітів; ~1 на 5).
- Доречні (≥20 змінених рядків коду): 15 (напр. ddada00 213 рядків, a9d2938 211, 71ef592 112). Дрібні (<20 рядків: 10, 9, 5, 1, 1): 5 — формально без рецензії, але цінність мала (сумнівні/«шум»). Хибні за суттю «ніхто не просив рецензію» — не вимірювані; чесно: усі 20 справді були без рецензії.
- Пропуски: 0 комітів з іншими «кодовими» розширеннями (js/ts/json/html/css/toml/yaml) без рецензії — список `.py/.sh/.mjs` на цій історії нічого не втрачає. Не виміряно: коміт, зроблений поза Bash-інструментом; коміт з `git add` + `commit` у різних викликах (індекс читається у момент коміту — це покрито).
- Використання скілів у всіх журналах: Skill `code-review` — 1 виклик (на 103 коміти), слеш-команд `/code-review`/`/simplify` — 0, `simplify` — 0. Тобто «скіл мав бути і не застосований» підтверджено числом.
- Відзнака до завдання: efc905e (Q4.4) — ТАК, змінив `tools/reel-read.py` (27 рядків) і пішов без рецензії: тригер спрацював би. 679f9b3 — `git show` не знайшов жодного `.py/.sh/.mjs` у цьому коміті (лише `.md` у agents/ і trees/), тож за формулою тригера він би МОВЧАВ; твердження «пішов без рецензії коду» щодо 679f9b3 цим бектестом не підтверджене [перевірено: список файлів комітa виведено, кодових нема]. Якщо код правився у ході сесії й потрапив в інший коміт — це 69d8108/ac9a691, не 679f9b3.

### Ціна
Один зайвий хід на коміт коду (запуск /code-review або відповідь «без рецензії»): ~1 з 5 комітів. Час хука: +0.11 с на найбільшому журналі (11 МБ) + git diff ~10 мс. Токени: сам /code-review — ціна рев'ю (це і є мета).

### Ризики
1. Новий `ask` — те саме, що колись погоджували «за звичкою» (TROUBLES «Висновки сесії cfca89fe» п.1). Пом'якшення: ask несе конкретну дію («запусти /code-review файл»), а винятком є слова користувача. Якщо за пробу «Дозволити» тиснуть без рецензії >50% — замінити на підказку (additionalContext) або зняти.
2. Дрібні коміти (<20 рядків) — 5 з 20: можна додати поріг (пропускати, якщо змінено <10 рядків коду) — рішення користувача, не додано.
3. `git add -A && git commit` в одній команді: беремо `git status --porcelain` (верхня межа) → можливий зайвий ask, якщо серед змін є код, який насправді не додається.
4. Рецензія «для цих файлів» (з завдання) не перевіряється — достатньо будь-якого виклику в відрізку; точніше означало б розбір аргументів Skill, який журнал не містить. Спрацьовує як ворота-нагадування, а не доказ якості.
5. Побічно: merge/amend-коміти без нових файлів у індексі — тиша (індекс порожній).

### Відкат
Нічого не застосовано. Після застосування: `cp commit-consent-hook.orig.py .claude/hooks/commit-consent-hook.py` (перед цим — `.bak`; хук у git, тож і `git checkout -- .claude/hooks/commit-consent-hook.py`). Швидке вимкнення без відкату: слова «без рецензії» у рішенні; або тимчасово `return None` у першому рядку `review_gate`. Журнал: рядки `review-ask` у `.claude/logs/commit-consent.log`.

## Тригер 2. Порядок дебагу на збій (2-й збій підряд)

### Задум
Момент: PostToolUseFailure інструмента, що вже падав перед тим підряд (без успіху між ними, проміжки ≤60 хв). Наявний хук: `grep -rn PostToolUseFailure .claude/settings.local.json .claude/hooks` → `settings.local.json:265` (matcher `mcp__delegate__delegate|mcp__deepseek__deepseek`) → `delegate-outcome-logger-hook.py` (уже логер + підказка FAIL_HINT на 429/мережу, коміт cc82a23, урок 2026-10-23 у TROUBLES «Висновки сесії cfca89fe» п.3–4 — саме «збій → підказка»). Розширюємо його, налаштувань не чіпаємо. Стан «підряд» береться з уже наявного `delegate-calls.jsonl` (хук сам туди пише) — нових файлів нема.
- 2-й збій: «Стоп: глянь лог (…), назви гіпотезу одним реченням і що її спростує — не повторюй виклик наосліп.»
- 3-й і далі: «≥3 невдач — не наступна спроба, а інший підхід (інша ланка/модель, менший вхід, чекати скидання ліміту) або питання користувачу.»
Джерела чек-листа — `debug-yakist-2026-10-25.md` розд. 4 («Дебаг-8» + стоп-правило), superpowers systematic-debugging, Zeller, SRE (там лежать посилання; тут їх не перевіряв повторно).

### Diff копії (`t2.diff`)
```diff
--- logger.orig.py	2026-10-25 10:06:06.813851912 +0200
+++ logger.py	2026-10-25 10:06:06.865851912 +0200
@@ -12,12 +12,13 @@
 результат фонової задачі приходить окремим каналом (task-notification),
 який цей хук не бачить.
 """
+import os
 import sys
 import json
 import re
-from datetime import datetime, timezone
+from datetime import datetime, timezone, timedelta
 
-LOG_PATH = "/data/data/com.termux/files/home/AgentReachProject/.claude/logs/delegate-calls.jsonl"
+LOG_PATH = os.environ.get("DELEGATE_LOG") or "/data/data/com.termux/files/home/AgentReachProject/.claude/logs/delegate-calls.jsonl"
 ERROR_RE = re.compile(r'\b(error|failed|exception)\b|"exit_code"\s*:\s*[1-9]', re.IGNORECASE)
 BACKGROUND_RE = re.compile(r"moved to (?:the )?background", re.IGNORECASE)
 # 2026-10-23 (TROUBLES «Висновки сесії cfca89fe…» п.3–4): після 429 BazaarLink я вирішив «незалежної звірки сьогодні
@@ -30,6 +31,36 @@
              "лише з «так» користувача і ціною з виходу минулого прогону.")
 
 
+# ТРИГЕР «порядок дебагу на збій» (2026-10-25; agents/claude-code/debug-yakist-2026-10-25.md розд. 4): 2-й збій
+# того самого інструмента підряд → підказка «стоп: лог, гіпотеза»; 3-й і далі → «змін підхід». Лише підказка.
+STREAK_WINDOW = timedelta(minutes=60)
+DEBUG_HINT2 = ("Другий збій {} підряд. Стоп: глянь лог (.claude/logs/delegate-calls.jsonl, response_preview), назви "
+               "гіпотезу одним реченням і що її спростує — не повторюй виклик наосліп.")
+DEBUG_HINT3 = ("Збій {} уже {}-й підряд. Стоп-правило: ≥3 невдач — не наступна спроба, а інший підхід (інша ланка/"
+               "модель, менший вхід, чекати скидання ліміту) або питання користувачу.")
+
+
+def error_streak(tool):
+    """Скільки останніх записів логу — підряд помилки цього інструмента (проміжки ≤ STREAK_WINDOW; успіх обриває)."""
+    n, prev = 0, None
+    try:
+        with open(LOG_PATH, encoding="utf-8") as f:
+            rows = [json.loads(l) for l in f.readlines()[-30:] if l.strip()]
+    except (OSError, ValueError):
+        return 0
+    for r in reversed(rows):
+        if r.get("tool") != tool:
+            continue
+        try:
+            t = datetime.fromisoformat(r["ts"])
+        except (KeyError, ValueError):
+            break
+        if r.get("outcome") != "error" or (prev and prev - t > STREAK_WINDOW):
+            break
+        n, prev = n + 1, t
+    return n
+
+
 def as_text(value):
     if value is None:
         return ""
@@ -90,10 +121,18 @@
     except OSError:
         pass
     if outcome == "error":
+        parts = []
         m = FAIL_RE.search(resp)
         if m:
+            parts.append(FAIL_HINT.format(m.group(0)))
+        k = error_streak(tool_name)
+        if k == 2:
+            parts.append(DEBUG_HINT2.format(tool_name))
+        elif k >= 3:
+            parts.append(DEBUG_HINT3.format(tool_name, k))
+        if parts:
             print(json.dumps({"hookSpecificOutput": {"hookEventName": hook_event or "PostToolUseFailure",
-                                                     "additionalContext": FAIL_HINT.format(m.group(0))}},
+                                                     "additionalContext": " ".join(parts)}},
                              ensure_ascii=False))
```
(`LOG_PATH` з env `DELEGATE_LOG` — лише для тестів; за замовчуванням як було.)

### Тести (в обидва боки)
Мають додати підказку: T2-2 другий збій; T2-3 третій; T2-7 другий збій без «429» (debug-підказка є, старої нема).
Мають мовчати щодо debug: T2-1 перший збій (лишається лише стара FAIL_HINT); T2-4 успіх між збоями; T2-5 попередній збій ІНШОГО інструмента; T2-6 попередній збій 5 год тому; T2-8 PostToolUse-успіх (нічого не друкує).
Результат: 8/8 PASS (разом із тригером 1: 20/20).

### Бектест
А) Журнал `delegate-calls.jsonl` (300 записів: 91 error, 140 success, 69 backgrounded; 82 записи PostToolUseFailure), відтворення логіки: підказка №2 — 27 разів, №3+ — 15 разів (разом 42 спрацювання на 91 збій). Сьогоднішній випадок: помилки 25.10 о 00:31:13, 00:31:32, 00:35:23 (стрейк 3→4→5) і 07:27:24, 07:27:30, 07:27:48, 07:52:52 → підказки були б на 07:27:30 (№2), 07:27:48 (№3), 07:52:52 (№4; проміжок до попереднього 25 хв < 60). Тобто «429 тричі о 07:27 і о 07:52» ловиться.
Б) Журнали сесій, усі інструменти (`bt2.py`; 456 tool_result з is_error, 160 виключено як відмови хуків/замків/дозволів — це не збої інструмента): 64 події «2-й+ збій підряд того самого інструмента»; 22 з них n≥3. Що робив агент далі (наступний виклик того ж інструмента: майже та сама вхідна команда = «наосліп», схожість ≥0.9):
- delegate: 38 подій → наосліп 12, змінив вхід 15, далі виклику не було 11. Тобто підказка потрібна у 12 (доречні, ~32% подій; 44% серед тих, де був наступний виклик), зайва але нешкідлива у 15 (вже міняв підхід), ще 11 — невідомо.
- deepseek MCP: 2 події (0 / 1 / 1).
- ПОЗА зоною чинного matcher: 24 події (Bash 17: наосліп 5, змінив 12; Write 3 — усі 3 наосліп; Read 1 наосліп; WebFetch, chrome-find, transcriptor — по 1). Bash шумить: серед його «збоїв» є «auto mode classifier gave no verdict» — не вина агента.
- Пропуски поточного matcher: Write ×3 і Read ×1 (усі «наосліп» повтори) — найчистіші випадки, поза зоною; розширення matcher на `Write|Edit|Read|WebFetch|WebSearch` (не Bash) дало б ще ~6 подій; Bash не додавати, поки не відфільтровано classifier-помилки.
- Хибні тривоги: події, де агент уже змінив вхід (delegate 15) — підказка йому нічого нового, але читається за секунди; хибних «не про той інструмент» нема (лічильник по імені).
Обмеження вимірювання: «наосліп» — наближення (схожість рядків вхідного JSON), а не прочитаний зміст; 11 подій без продовження не класифіковано.

### Ціна
Нуль зайвих ходів для агента (підказка в тому ж місці, де вже друкувалась FAIL_HINT). Додатковий текст ≈70 слів на 2-й+ збій (42 рази за місяць у delegate). Час: читання 30 останніх рядків логу — мілісекунди.

### Ризики
1. Підказка не примушує: агент може проігнорувати (це підказка, не ворота; за RULES-WHY ворота-дозвіл тут не потрібні, бо повтор не небезпечний). Перевірка дієвості — після пробою: у журналі частка «наосліп» серед подій має впасти з 12/27 (44%).
2. Стан у спільному логу: якщо лог ротують/чистять, лічильник скидається (це безпечна сторона).
3. Збої фонових задач не потрапляють у PostToolUseFailure (лишаються `backgrounded_unknown`) — тригер їх не бачить.
4. Дві підказки в одному повідомленні (FAIL_HINT + №2/№3) на 429 — довше, але різні за змістом.
5. Тексти підказок рекомендують «чекати скидання ліміту» — коректно лише для 429/capacity; для інших помилок вона загальна («інший підхід або питання»).

### Відкат
Нічого не застосовано. Після застосування: `cp logger.orig.py .claude/hooks/delegate-outcome-logger-hook.py` (`git checkout --` теж; хук у git, історія cc82a23). Швидке вимкнення: у `error_streak` повернути `return 0` — debug-підказки зникнуть, стара FAIL_HINT і логування лишаються.

## Підсумок і наступний крок
- Тригер 1: 20 спрацювань на 103 коміти (20 комітів коду, 0 з рецензією); 15 доречних, 5 дрібних; пропусків за розширеннями 0; тести 12/12.
- Тригер 2: 42 спрацювання на 91 збій у логу delegate; у сесіях 64 події, з них у зоні matcher 40 (наосліп 12 із 38 delegate); тести 8/8.
- Не перевірено: hooks-smoke на копіях, мутант, чи справжній Claude Code передає `cwd` у PreToolUse (код має запасний PROJECT) [не перевірено].
- Питання користувачу (рекомендація: так): застосувати тригер 2 пробою на 3 сесії (нуль ходів, безпечний), а тригер 1 — теж пробою, з порогом «менше 10 рядків — мовчати»? Застосування (правка `.claude/hooks/*`) і коміт — лише після вашого «так» і слова «коміт».
