# Крок 1 плану кола диспетчера — три правки в копії, нічого не ввімкнено

Ідея: дерево задач + голограма › G3 Конвеєр живої гілки › крок 1 PLAN-COMBINED.md (1.1–1.3).
Служить: помилки виправляються в місці народження (429 «concurrent» утретє; листи DSH; ярлики l2s у комітах).
Оригінали (.claude/skills, .claude/hooks), settings, tools/ — не змінено; git add/commit не було; у вікно DSH (work:3) нічого не надсилалось.

Файли пісочниці:
- `SKILL.md.new` — копія .claude/skills/verify-before-show/SKILL.md (1.1)
- `dsh-send.sh` — новий скрипт листа DSH (1.2)
- `git-add-status-hook.py.new` — копія .claude/hooks/git-add-status-hook.py (1.3)

---

## 1.1 Скіл звірки: «усі паралельно» → «не більше 2 одночасно на BazaarLink»

Команда: `diff -u .claude/skills/verify-before-show/SKILL.md step1/SKILL.md.new` (код виходу 1 — є різниця).

```diff
--- .claude/skills/verify-before-show/SKILL.md	2026-10-20 16:07:51.775248683 +0300
+++ agents/claude-code/dispatcher-circle-2026-10-29/step1/SKILL.md.new	2026-10-29 13:22:58.165598631 +0200
@@ -49,7 +49,7 @@
 
 ## Крок 2 — верифікатор (DeepSeek flash)
 
-На кожне твердження — окремий виклик, усі паралельно:
+На кожне твердження — окремий виклик; на безкоштовному провайдері (BazaarLink) — не більше 2 одночасно, наступний — після відповіді (429 «Too many concurrent» — TROUBLES 15.10, 28.10, 29.10):
 - `mcp__delegate__delegate`, `task: "reason"`, `temperature: 0.3`;
 - `files`: не більше 2 джерел (правило RULES.md про ліміт deepseek);
 - `prompt`: дослівно блок із `verifier-prompt.md` цієї теки, де
```

Лічильник: змінених рядків «-» = 1, «+» = 1 (`grep -c '^-[^-]'` / `grep -c '^+[^+]'` по diff).
Тестувати нема чим, крім diff: доказ дії — наступна звірка без 429 «concurrent» (критерій проби PLAN-COMBINED).

---

## 1.2 Скрипт листа DSH: `dsh-send.sh`

Замінює рецепти TROUBLES.md:3958–3970 («Листи у вікно DSH — доповнення…», 2026-10-03) і :6751–6760 («Enter пішов, хоча перевірка поля вводу дала 0», 2026-10-29).

Поведінка:
- `dsh-send.sh <файл листа> [--target <tmux-ціль>] [--no-journal]`; ціль за замовчуванням — перше вікно сесії work з назвою `dsh*` (`tmux list-windows -t work -F '#{window_index} #{window_name}'`).
- `dsh-send.sh --check-delivery <id>` — лише читання журналу DSH, нічого не шле (додано для тесту (в) без надсилання).
- Рядок «📁» з екрана → у stderr; без «(Full access)» — лише ПОПЕРЕДЖЕННЯ (блок відкладено, BACKLOG «Режим DSH»).
- id — перше слово файлу без кінцевої крапки.
- Вставка `tmux send-keys -t T -l "$TEXT"`; перевірка поля до 3 спроб по 1 с — екран містить останні 20 символів листа; Enter лише якщо знайдено, інакше код 2 «НЕ В ПОЛІ — не відправляю».
- Доставка (без --no-journal): до 15 с, найновіший `…/.dsh/sessions/*/*/session.v4.jsonl.zstd` → `readlink -f` → `zstd -dc | grep -c -F id`; ≥1 — «доставлено: N», інакше код 3.
- `DSH_SEND_CAPTURE_FILE` — «екран» з файлу замість capture-pane.
- Коди: 0 ок; 1 аргументи/ціль; 2 не в полі (Enter не пішов); 3 доставку не підтверджено.

**Відхилення від брифу (одне):** текст береться як `tr '\n' ' ' < файл` (без кінцевих пробілів), а не дослівно `$(cat файл)` — так велить рецепт 2026-10-03, який скрипт замінює: перенос рядка в `send-keys -l` = натискання Enter, багаторядковий лист відправився б частинами. Хвіст для перевірки береться з цього ж зведеного тексту.

Тести (тимчасове вікно `work:sendtest` з `cat`; лист-зразок у $TMPDIR, id test-1, 2 рядки; вікно DSH не чіпалось):

Вікна до тесту: `0 claude / 1 sendtest / 2 shell / 3 dsh`.

(а) успіх — `./dsh-send.sh $L --target work:sendtest --no-journal`:
```
ціль work:sendtest; рядок 📁: <нема>
ПОПЕРЕДЖЕННЯ: у рядку 📁 нема «(Full access)» — DSH може не мати доступу (лист усе одно шлю)
id: test-1; хвіст для перевірки: «інець листа XYZ-0042»
Enter надіслано (test-1)
код=0
--- capture-pane work:sendtest після (а):
test-1. Лист-зразок для перевірки dsh-send: другий рядок, кінець листа XYZ-0042
test-1. Лист-зразок для перевірки dsh-send: другий рядок, кінець листа XYZ-0042
рядків з XYZ-0042: 2
```
Два рядки = відлуння набраного + повтор від `cat` → Enter пішов, лист в один рядок. ПРОЙШОВ.

(б) провал — `DSH_SEND_CAPTURE_FILE=<порожній файл> ./dsh-send.sh $L --target work:sendtest --no-journal`:
```
ціль work:sendtest; рядок 📁: <нема>
ПОПЕРЕДЖЕННЯ: у рядку 📁 нема «(Full access)» — DSH може не мати доступу (лист усе одно шлю)
id: test-1; хвіст для перевірки: «інець листа XYZ-0042»
НЕ В ПОЛІ — не відправляю (хвіст «інець листа XYZ-0042» не знайдено за 3 спроби; текст лишився в полі — Ctrl+K)
код=2
--- capture-pane work:sendtest після (б):
test-1. Лист-зразок для перевірки dsh-send: другий рядок, кінець листа XYZ-0042
test-1. Лист-зразок для перевірки dsh-send: другий рядок, кінець листа XYZ-0042
test-1. Лист-зразок для перевірки dsh-send: другий рядок, кінець листа XYZ-0042
рядків з XYZ-0042: 3 (було 2; 3 = текст у полі без Enter; 4 = Enter пішов)
```
Третій рядок — текст у полі, повтору від `cat` нема → Enter не пішов. ПРОЙШОВ.

(в) журнал, лише читання (справжній журнал DSH):
```
найновіший: …/rootfs/root/.dsh/sessions/--root-dsh-app--/6b20910d-fc24-4e95-b096-fbe8c5e1c726/session.v4.jsonl.zstd
lrwxrwxrwx.
readlink -f: …/rootfs/.l2s/.l2s.session.v4.jsonl.zstd.e151f90f4661.tmp0001.0001
zstd -dc на ярлику (без readlink): 0
cc-2910-3 → 5
контроль, неіснуючий id zz-0000-0 → 0
=== ціль за замовчуванням (лише пошук, без надсилання):
work:3
```
cc-2910-3 дав 5 (≥1), контрольний id — 0; без `readlink -f` — 0 (підтверджує TROUBLES:5533). ПРОЙШОВ.

Прибрано: `tmux kill-window -t work:sendtest` (після — `0 claude / 2 shell / 3 dsh`), тимчасові файли в $TMPDIR видалено (`ls …/step1-*` — No such file).

Неясне / межі:
- `grep -c` рахує РЯДКИ журналу з id (5), а не саме записи `user/message` (рецепт 29.10 вимагав «user/message з id = 1»): згадка id у відповіді DSH теж дає ≥1. Строгіша перевірка — розбір JSON за типом запису; не робив, бо формат запису в цьому кроці не друкував (правило «спершу надрукуй реальний запис»).
- «Найновіший журнал» — за mtime; якщо DSH щойно відкрив нову сесію, а лист пішов у стару (або навпаки) — хибний код 3.
- Перевірка «поле порожнє перед вставкою» і «DSH зайнятий» (рецепт 2026-10-03) у скрипт не входили за брифом — не реалізовано.
- Реальна вставка в DSH-поле (обрізаний один рядок, прокрутка) не перевірялась — лише `cat`; хвіст 20 символів обрано за брифом.

---

## 1.3 Замок на ярлики l2s при git add: `git-add-status-hook.py.new`

**Розбіжність із брифом/планом (важливо):** хук уже має перевірку ярликів — `l2s_links()` (2026-10-20, рішення користувача «Так, зробити»), але з рішенням **ask** (віконце), а не deny, і рецептом `readlink F` (без `-f`). PLAN-COMBINED 1.3 пише «додати перевірку» — фактично це посилення наявної. Новий парсер не писав: використано наявні `git_add_arg_tokens()` + `l2s_links()` (вона вже бере файли всередині доданих тек з `git status --porcelain --untracked-files=all`).

Що змінено (3 місця):
1. Нова `is_l2s_link(full)`: `os.path.islink` і ціль (`os.readlink` або `os.path.realpath`) містить «/.l2s/» або ім'я починається на «.l2s.».
2. `l2s_links()`: явні шляхи-аргументи git add перевіряються напряму (ярлик, якого git status не показав би, напр. уже відстежуваний).
3. `main()`: ярлики l2s → **deny** з повідомленням «Ярлик l2s замість файлу: <шлях>. Лікування: cp --remove-destination "$(readlink -f <шлях>)" <шлях> (TROUBLES 20.10)»; інші ярлики в agents/dsh/ (не l2s) — **ask**, як було.

```diff
--- .claude/hooks/git-add-status-hook.py	2026-10-26 10:39:28.461955295 +0200
+++ agents/claude-code/dispatcher-circle-2026-10-29/step1/git-add-status-hook.py.new	2026-10-29 13:25:36.149598571 +0200
@@ -364,6 +364,19 @@
     return None
 
 
+def is_l2s_link(full):
+    """2026-10-29 (крок 1.3 плану кола диспетчера): ярлик, ціль якого — .l2s proot
+    (тека «/.l2s/» або ім'я «.l2s.…»). os.readlink — як записано, realpath — кінцева ціль."""
+    if not os.path.islink(full):
+        return False
+    try:
+        targets = [os.readlink(full), os.path.realpath(full)]
+    except OSError:
+        return False
+    return any("/.l2s/" in t or os.path.basename(t).startswith(".l2s.") or "/.l2s." in t
+               for t in targets)
+
+
 def l2s_links(args, status_lines, cwd):
     """Ярлики серед шляхів, які додасть git add (2026-10-20, рішення користувача «Так, зробити»): у cf52c36
     звіт DSH пішов у git як symlink на rootfs/.l2s. Шляхи — з git status (тип «T» і нові), що підпадають під
@@ -383,7 +396,13 @@
         r = os.path.normpath(os.path.relpath(os.path.join(cwd, a), REPO))
         rels.append("" if r == "." else r)
     out = []
+    for a in specs:  # 2026-10-29: явний аргумент-ярлик — навіть якщо git status його не показав
+        full = os.path.normpath(a if os.path.isabs(a) else os.path.join(cwd, a))
+        if is_l2s_link(full):
+            out.append(os.path.relpath(full, REPO))
     for p in paths:
+        if p in out:
+            continue
         if not (every or any(r == "" or p == r or p.startswith(r.rstrip("/") + "/") for r in rels)):
             continue
         full = os.path.join(REPO, p)
@@ -455,6 +474,20 @@
         return
 
     links = l2s_links(args, lines, data.get("cwd") or REPO)
+    l2s = [p for p in links if is_l2s_link(os.path.join(REPO, p))]
+    if l2s:
+        p0 = l2s[0]
+        print(json.dumps({
+            "hookSpecificOutput": {
+                "hookEventName": "PreToolUse",
+                "permissionDecision": "deny",
+                "permissionDecisionReason": (
+                    f"Ярлик l2s замість файлу: {', '.join(l2s[:5])}. Лікування: "
+                    f"cp --remove-destination \"$(readlink -f {p0})\" {p0} (TROUBLES 20.10)"
+                ),
+            }
+        }))
+        return
     if links:
         print(json.dumps({
             "hookSpecificOutput": {
```

Тести — імітація входу (`echo '{"tool_name":"Bash","cwd":"<корінь>","tool_input":{"command":"git add …"}}' | python3 <хук>`), оригінал і копія на тому самому вході. Фікстури: `step1/test/link.md` → `$TMPDIR/x/.l2s/.l2s.report.md.0001`; `step1/test/dir/inner-link.md` → `$TMPDIR/x/.l2s/.l2s.inner.md.0002`; `step1/test/plain.md`, `step1/test/dir2/plain2.md` — звичайні файли.

```
### вхід: git add agents/claude-code/dispatcher-circle-2026-10-29/step1/test/link.md
--- оригінал:
ask | git add додасть ЯРЛИК, а не файл: agents/claude-code/dispatcher-circle-2026-10-29/step1/test/link.md. Файли DSH з Termux — ярлики l2s (TROUBLES 2026-10-20 «Закомітив ярлик l2s…»): у коміт піде symlink 120000. Спершу cp --remove-destination "$(readlink F)" F і звір md5.
--- копія:
deny | Ярлик l2s замість файлу: agents/claude-code/dispatcher-circle-2026-10-29/step1/test/link.md. Лікування: cp --remove-destination "$(readlink -f agents/claude-code/dispatcher-circle-2026-10-29/step1/test/link.md)" agents/claude-code/dispatcher-circle-2026-10-29/step1/test/link.md (TROUBLES 20.10)
=== вивід РІЗНИЙ
### вхід: git add agents/claude-code/dispatcher-circle-2026-10-29/step1/test/dir
--- оригінал:
ask | git add додасть ЯРЛИК, а не файл: agents/claude-code/dispatcher-circle-2026-10-29/step1/test/dir/inner-link.md. Файли DSH з Termux — ярлики l2s (TROUBLES 2026-10-20 «Закомітив ярлик l2s…»): у коміт піде symlink 120000. Спершу cp --remove-destination "$(readlink F)" F і звір md5.
--- копія:
deny | Ярлик l2s замість файлу: agents/claude-code/dispatcher-circle-2026-10-29/step1/test/dir/inner-link.md. Лікування: cp --remove-destination "$(readlink -f agents/claude-code/dispatcher-circle-2026-10-29/step1/test/dir/inner-link.md)" agents/claude-code/dispatcher-circle-2026-10-29/step1/test/dir/inner-link.md (TROUBLES 20.10)
=== вивід РІЗНИЙ
### вхід: git add agents/claude-code/dispatcher-circle-2026-10-29/step1/test/plain.md
--- оригінал:
(без рішення) | git status перед git add (правило RULES.md):
?? agents/claude-code/dispatcher-circle-2026-10-29/step1/
--- копія:
(без рішення) | git status перед git add (правило RULES.md):
?? agents/claude-code/dispatcher-circle-2026-10-29/step1/
=== вивід оригіналу і копії ІДЕНТИЧНИЙ (байт у байт)
### вхід: git add agents/claude-code/dispatcher-circle-2026-10-29/step1/test/dir2
--- оригінал:
(без рішення) | git status перед git add (правило RULES.md):
?? agents/claude-code/dispatcher-circle-2026-10-29/step1/
--- копія:
(без рішення) | git status перед git add (правило RULES.md):
?? agents/claude-code/dispatcher-circle-2026-10-29/step1/
=== вивід оригіналу і копії ІДЕНТИЧНИЙ (байт у байт)
### вхід: git status && git add agent.py
--- оригінал:
deny | Заблоковано: команда явно згадує agent.py. RULES.md (розділ Git): agent.py містить ключ і живе поза git — прецедент TROUBLES.md #11, ключ уже раз потрапив у git. Якщо це помилка — прибери agent.py з команди.
--- копія:
deny | Заблоковано: команда явно згадує agent.py. RULES.md (розділ Git): agent.py містить ключ і живе поза git — прецедент TROUBLES.md #11, ключ уже раз потрапив у git. Якщо це помилка — прибери agent.py з команди.
=== вивід оригіналу і копії ІДЕНТИЧНИЙ (байт у байт)
### вхід: echo 'git add x'
--- оригінал:
(без рішення) | (порожньо)
--- копія:
(без рішення) | (порожньо)
=== вивід оригіналу і копії ІДЕНТИЧНИЙ (байт у байт)
### вхід: cd agents/claude-code/dispatcher-circle-2026-10-29/step1 && git add test/link.md
--- оригінал:
(без рішення) | git status перед git add (правило RULES.md):
?? agents/claude-code/dispatcher-circle-2026-10-29/step1/
--- копія:
(без рішення) | git status перед git add (правило RULES.md):
?? agents/claude-code/dispatcher-circle-2026-10-29/step1/
=== вивід оригіналу і копії ІДЕНТИЧНИЙ (байт у байт)
```

Підсумок: ярлик → deny (ПРОЙШОВ); тека з ярликом → deny (ПРОЙШОВ); звичайний файл і тека без ярлика → пропуск, вивід git status байт у байт як в оригіналу (ПРОЙШОВ); `git add agent.py` → той самий deny, `echo 'git add x'` → тиша, як в оригіналу (ПРОЙШОВ).

Неясне / межі:
- `cd <тека> && git add <відносний шлях>` — ярлик НЕ ловить ні оригінал, ні копія (останній тест): `l2s_links` бере cwd з JSON і не враховує `cd` у команді (`copy_risk` враховує, `git_add_arg_tokens` — ні). Вада давня, не з цієї правки; виправлення — передати cwd після `cd` з `git_add_arg_tokens`, окремим рішенням.
- `git add -A` без шляхів: ярлики l2s з git status теж дають deny (поведінка `every` збережена, лише ask→deny).
- Перехід ask→deny — зміна поведінки замка; вмикати (копіювати в .claude/hooks/) — лише з рішення користувача.
- Тестові фікстури після прогону прибрано (перенесено в $TMPDIR і видалено там), щоб ярлик не лишився в робочому дереві.

— [claude-code (під-агент за брифом координатора), 2026-10-29]
