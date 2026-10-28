# Перевірка Б2 і Б6 (лист cc-2810-1) + звірка 13 пунктів BACKLOG

**Автор:** dsh (DSH / DeepSeek Harness, профіль `tui`, proot).
**Репозиторій:** `/data/data/com.termux/files/home/AgentReachProject`.
**Цільовий шлях:** `agents/claude-code/chains-2026-10-25/dsh-check-cc-2810-1.md` — **не записано**, цей файл лежить у робочій теці сесії `/root/dsh-app/` (причина — розділ 0).
**Межі:** ≤20 кроків, ≤$0.30 на все дерево. Витрачено: 16 кроків (з них 1 під-агент), оцінка ≈$0.05 — у межах.

---

## 0. Блокер середовища (через нього «стоп-умова» не виконана)

Реальний shell у цій сесії **не запускається** — перша ж команда:

```
$ date +%FT%H:%M%z
Error: sandbox mode "workspace-write" is requested but no sandbox backend is usable on this host;
refusing to run the command unconfined. Install bubblewrap or run a Landlock-enforcing kernel...
```

Спроба підвищити права (двічі, окремо для `bash` і для `edit`):

```
$ bash -c 'date ...'  ->  Error: sandbox escalation to "danger-full-access" requires approval,
                            but no approval channel is available
$ edit synthesis.md   ->  Error: sandbox escalation to "danger-full-access" requires approval,
                            but no approval channel is available
```

Запис файлів дозволено лише під `/root/dsh-app`; репозиторій — поза нею:

```
$ edit agents/claude-code/chains-2026-10-25/synthesis.md
Error: [sandbox: file access denied under workspace-write mode]
```

Наслідки: **немає** `date`, `git`, `zstd`. Тому:
1) перевірки зроблено інструментом `grep`/`read` dsh (читання репозиторію працює, номери рядків реальні) —
   у звіті наведено точний виклик і його реальний вивід;
2) правку `synthesis.md` з тегом `[dsh, ЧАС]` **не внесено** — реальний `$(date +%FT%H:%M%z)` отримати
   неможливо, а вигадувати час заборонено (RULES.md:38-43); `/proc` у proot бреше (btime 2023-03-28);
3) `git add`/`commit` і запис у JOURNAL **не зроблено** — коміта немає;
4) журнали сесій dsh (`session.v4.jsonl.zstd`) не читались (немає `zstd`) — Б6 перевірено по журналах хуків
   `.claude/logs/`, які й пишуть ці шість подій.

---

## 1. Б2 (synthesis.md:16) — три парсери + розбір «◐»

### 1.1 Місце 1 — tree-focus
```
grep '^\s*(def |class )' .claude/hooks/tree-focus-hook.py
115: def parse(path):
369: def parse_dsh(screen, ids):
406: def main():
```
### 1.2 Місце 2 — trees-index (окремий регекс для формату g2)
```
grep 'node|ARROW|def ' tools/trees-index.py
23: ARROW = re.compile(r"^\s*[▸▶·]\s+(\S+)\s+(\S)\s+(.*)$")   # формат trees/g2/g2.md
30: def nodes(path):
```
### 1.3 Місце 3 — mods/agents-status/hooks/parse.ts
```
grep 'ARROW|parseTree|◐|\\u25d0' mods/agents-status/hooks
parse.ts:6:  export function parseTree(stdout: string): Node[] {
parse.ts:20:     if (!line.includes('◐')) continue
parse.ts:22:     const i = cells.indexOf('◐')
parse.ts:33:   ... 'DSH насправді: пункту ◐ на екрані нема' ...
register.tsx:5:  import { describe, parseDshTodo, parseTree } from './parse'
register.tsx:22: const value: Lines = describe(parseTree(tree?.stdout ?? ''), ...)
```
Три **різні реалізації**, не реекспорт → «парсер вузла ×3» **підтверджено**.
`register.tsx` лише викликає `parseTree`, власного парсера не має.

### 1.4 «tree-focus не бачить trees/g2»
```
grep 'glob\(|trees/' .claude/hooks/tree-focus-hook.py
426: for card in sorted(glob.glob(os.path.join(cwd, "trees", "*.md"))):
```
Без рекурсії → вузли `trees/g2/g2.md` невидимі. **Підтверджено.**

### 1.5 Скільки місць розбирають «◐» — repo-wide
```
grep '◐' .   (усі файли)
продакшн-код: .claude/hooks/tree-focus-hook.py:376,378   mods/agents-status/hooks/parse.ts:20,22
тести/смоуки: parse.test.ts:12,13   tools/hooks-smoke.py:484
копії-чернетки: agents/claude-code/focus-v2-2026-10-27/tree-focus-hook.py:376,378
                agents/claude-code/prep-2026-10-27/focus/tree-focus-hook.py:362,364
документи: BACKLOG.md:118,119,454   TROUBLES.md:5200,5204   trees/*.md   звіти
кодових форм \u25d0 у коді — 0
```
Розбір «◐» існує рівно у **двох** живих місцях (tfh:376-379, parse.ts:18-26 `parseDshTodo`); третє
«місце» в звітах розвідників (register.tsx:19, SKILL.md:20) — це *читання* екрана, не розбір знака.

**Вердикт Б2: уточнено, не falsify.** «×3» — так; «◐ ×2–3» → **×2**.

---

## 2. Б6 (synthesis.md:20) — пари логів «одного моменту»

### 2.1 ask-gate + plain-ask — ПІДТВЕРДЖЕНО
```
grep '2026-10-25T02:36:06|2026-10-25T03:14:09' .claude/logs/ask-gate.jsonl
403: {"t": "2026-10-25T02:36:06", "session": "4cab3538-d3de-4fe9-833f-385ac831025d", "misses": []}
404: {"t": "2026-10-25T03:14:09", "session": "4cab3538-d3de-4fe9-833f-385ac831025d", "misses": []}

grep '2026-10-25T02:36:06|2026-10-25T03:14:09' .claude/logs/plain-ask.jsonl
453: {"t": "2026-10-25T02:36:06", "session": "4cab3538-d3de-4fe9-833f-385ac831025d", "codes": []}
454: {"t": "2026-10-25T03:14:09", "session": "4cab3538-d3de-4fe9-833f-385ac831025d", "codes": []}
```
Той самий момент (до секунди) і та сама сесія — у двох незалежних логах.

### 2.2 verify-nudge + edit-gate — ПІДТВЕРДЖЕНО
```
grep '2026-10-25T21:20:37|2026-10-25T03:36:30' .claude/logs/verify-nudge.log
 93: 4cab3538-…  .claude/hooks/answer-gate-shadow-hook.py   2026-10-25T03:36:30
100: 4dc8a94e-…  .claude/hooks/edit-gate-hook.py  ask:2026-10-25T19:19:48.055Z  2026-10-25T21:20:37

grep '2026-10-25T21:20:37|2026-10-25T03:36:30' .claude/logs/edit-gate.log
133: 4cab3538-…  siblings  …answer-gate-shadow-hook.py  2026-10-25  2026-10-25T03:36:30
134: 4cab3538-…  read      …answer-gate-shadow-hook.py  2026-10-25T03:36:30
154: 4dc8a94e-…  siblings  …edit-gate-hook.py          2026-10-25  2026-10-25T21:20:37
155: 4dc8a94e-…  read      …edit-gate-hook.py          2026-10-25T21:20:37
```
Той самий файл, та сама сесія, та сама секунда — підказка й ворота на одному кроці.

### 2.3 commit-consent + free-answer — **FALSIFY**
```
grep '2026-10-25T03:20:08|2026-10-25T09:57:18|2026-10-25T09:05:23' .claude/logs/commit-consent.log
No matches found

grep '2026-10-25T03:20:08|2026-10-25T09:57:18|2026-10-25T09:05:23' .claude/logs/free-answer.log
 11: free  4cab3538-…  2026-10-25T03:20:08  "мені здається тобі потрібно подивитись на всю систему…"
 16: free  cb82f9d3-…  2026-10-25T09:57:18  "що це нам дасть якиц Ккд?"

grep '2026-10-25T03:30:13|2026-10-25T10:05:20|2026-10-25T09:37:45' .claude/logs/free-answer.log
No matches found

read .claude/logs/commit-consent.log (130-144)
132: 4cab3538-…  ok    2026-10-25T03:25:40 …
134: 4cab3538-…  push:ok 2026-10-25T03:29:17 …
136: cb82f9d3-…  ok    2026-10-25T09:30:51 …
137: cb82f9d3-…  deny  2026-10-25T10:05:20  "а можна зразу використовувати декілька скілів для задачі…"
```
Обидва логи пишуть ті самі сесії, але **жодного збігу до секунди**: 03:20:08 проти 03:25:40/03:29:17;
09:57:18 проти 10:05:20. Показово: `commit-consent.log:137` записав **вільний текст** користувача зі
статусом `deny`, а `free-answer.log` того самого вислову не має → це не «подвійний запис», а
**розсинхрон двох воріт** (ворота не впізнали відповідь і занесли її як відмову).

**Підсумок Б6:** 2 пари підтверджено, 3-тя — falsify.

---

## 3. BACKLOG: 13 пунктів (лист каже «рядки ~1100–1112»)

Діапазон зсунувся: пункти лежать на **1165–1177** (13 рядків, 13 з 13; рядки 1100–1112 зайняв інший розділ).
Доказ — `read BACKLOG.md 1160-1184`; кожен пункт має маркер `[dsh, 2026-10-26T17:20+0200]` і
`Джерело: рецензія 4cab3538 (№N)`:

| № рецензії | рядок | фрагмент-доказ (з виводу) |
|---|---|---|
| №1 | 1165 | «Виправити суперечність «6 уже виконано» в журналі проти «4 зроблено» у TRASH.md:331» |
| №2 | 1166 | «Зіставити поштучно 21 випалий пункт → 21 носій (файл:рядок)» |
| №4 | 1167 | «Замінити оцінку «занижені на порядки» на замір» |
| №8 | 1168 | «Футер delegate переказувати як «витрата $X (оцінка проти Opus $Y)»» |
| №9 | 1169 | «Твердження «M3 спрацював сам» — лише після другого незалежного випадку» |
| №15 | 1170 | «або ask-gate/commit-consent перевіряє це слово у відповіді» |
| №16 | 1171 | «Питання про бюджет, коли в задачі >1 під-агент» |
| №18 | 1172 | «дописування heredoc `cat >>` для TROUBLES дозволене (уточнити запис №75)» |
| №21 | 1173 | «Підпис коміту не диктувати в тексті питання» |
| №25 | 1174 | «Один пробний запуск termux-speech-to-text і замір якості розпізнавання» |
| №28 | 1175 | «Вкладати бриф і межу кроків у сам виклик Agent» |
| №29 | 1176 | «прогнати бектест воріт питань S8 без змін регулярки» |
| №31 | 1177 | «чи прийшла підказка cost-nudge на $10 і чому не стала питанням» |

Втрачених немає.

---

## 4. Готові правки synthesis.md (чекають сесії з shell — тут не застосовані)

**Рядок 16 (Б2).** Було:
`… і розбір екрана DSH «◐» ×2–3 — P, S — не звірялось — ті самі дані читаються по-різному.`
Стало б:
`… і розбір екрана DSH «◐» ×2 — P, S — так (я: tree-focus:115 def parse; trees-index:30 def nodes + власний ARROW:23; parse.ts:6 parseTree; «◐» лише parse.ts:20,22 і tree-focus:376,378; tree-focus:426 glob(trees/*.md) без рекурсії) [dsh, <$(date +%FT%H:%M%z)>] — ті самі дані читаються по-різному.`

**Рядок 20 (Б6).** Було:
`Б6. Пари логів одного моменту: ask-gate+plain-ask, commit-consent+free-answer, verify-nudge+edit-gate — K:4) — не звірялось — подвійний запис без подвійної користі.`
Стало б:
`Б6. Пари логів одного моменту: ask-gate+plain-ask (так: одна секунда й та сама сесія, ask-gate.jsonl:403 ↔ plain-ask.jsonl:453), verify-nudge+edit-gate (так: verify-nudge.log:100 ↔ edit-gate.log:154, 21:20:37), commit-consent+free-answer (НІ: ті самі сесії, але розбіг у хвилини; commit-consent.log:137 заніс вільний текст як deny → розсинхрон воріт, не дубль) — K:4) — так частково (я: grep по .claude/logs/, докази вище) [dsh, <$(date +%FT%H:%M%z)>] — дубль є в 2 парах із 3.`

---

## 4б. Передача claude-code (рішення користувача)

Рішення: правки застосовує claude-code (у dsh немає shell). Що зробити одним проходом:
1) перенести цей файл у `agents/claude-code/chains-2026-10-25/dsh-check-cc-2810-1.md`;
2) застосувати дві правки з розділу 4, підставивши реальний `$(date +%FT%H:%M%z)` у тег `[dsh, …]`;
3) дописати в `agents/dsh/JOURNAL.md` (лише в кінець):

> `<$(date +%FT%H:%M%z)>` Перевірено лист cc-2810-1: Б2 — «×3» підтверджено (tree-focus:115 `def parse`,
> trees-index:30 `def nodes` + власний `ARROW`:23, parse.ts:6 `parseTree`), «◐ ×2–3» уточнено до **×2**
> (лише tfh:376,378 і parse.ts:20,22; `\u25d0` у коді немає). Б6 — ask-gate+plain-ask і verify-nudge+edit-gate
> **підтверджено** (до секунди: 02:36:06, 21:20:37), commit-consent+free-answer **falsify** (розбіг у хвилини;
> commit-consent.log:137 заніс вільний текст як `deny` — розсинхрон воріт, не дубль). BACKLOG: 13/13 на
> рядках 1165–1177 (діапазон 1100–1112 зсунувся). Звіт: chains-2026-10-25/dsh-check-cc-2810-1.md.
> Shell у моїй сесії заблокований (немає bubblewrap/Landlock, approval-каналу немає) — тому правки й коміт
> за користувачем/claude-code.

4) `git add agents/claude-code/chains-2026-10-25/{synthesis.md,dsh-check-cc-2810-1.md} agents/dsh/JOURNAL.md`
   і коміт із трейлером `Agent: dsh`:
   `git commit -m "..." -m "Agent: dsh"`.

## 5. Собівартість і кроки

- 16 кроків (1 під-агент у чистому контексті + 15 моїх викликів, 3 з них — відмови пісочниці).
- Платних API не викликав. Оцінка дерева: ≈$0.05 (під-агент ≈$0.02–0.04, решта — дрібні grep/read).
- Точну суму не назву: `session-cost` без shell не читається.
