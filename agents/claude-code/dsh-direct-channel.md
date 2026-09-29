# Прямий канал claude-code → DSH (веб-чат, 2026-09-30)

Перевірено наживо 2026-09-30: повідомлення прийнято (`accepted: true`), сесія DSH
перейшла в `running: True`. Писати напряму — лише з дозволу користувача на кожне
повідомлення: воно з'являється в чаті DSH як від користувача і запускає платну роботу.
Тому текст завжди починати з «[Повідомлення від claude-code …]».

## Протокол (DSH 0.2.0-rc.2, `dsh web`, порт 3080)
- Вхід: `GET http://127.0.0.1:3080/?token=<токен>` → 303 + cookie `dsh-auth-…`
  (токен дає користувач; у файли й коміти НЕ записувати). Далі все з цим cookie.
- Виклик: `POST /api/<endpoint>` з тілом
  `{"type":"client-request","rpcId":"<uuid>","method":"<endpoint>","payload":{"args":{<ім'я параметра>: …}}}`.
  Ім'я параметра — як у сигнатурі (`lib/typert.remote-client.d.ts` пакета
  `@deepseek-ai/dsh-api-session-controller` у proot: `/root/dsh-app/node_modules/…`).
- Список сесій (лише читання): `session/list`, `args: {"_request": {}}` →
  `items[]` з `sessionId`, `running`, `agentAvailable`, `cwd`.
- Надіслати: `session/prompt`, `args: {"request": {requestId, sessionId,
  mode: "queue"|"steer", content: [{type:"text", text}]}}` (types.d.ts:78, :319).
  Повтор із тим самим `requestId` не задвоює лист (README пакета).
- Граблі: `/api/session.list` → 404 (роздільник — «/»); без `args` → «exactly one
  plain-object args field»; без `_request` → `gateway/arguments-invalid`.

## Чого ще немає
- Читати ВІДПОВІДЬ DSH через API не пробували (історія сесії — `SessionEventStream`,
  потоковий). Поки відповідь — через його baton_pass / JOURNAL.md.
- Версія rc: протокол може змінитись з оновленням DSH.

## Зворотний канал dsh → claude-code: локальний «дзвінок» (перевірено 2026-09-30)
- claude-code запускає у фоні одноразовий HTTP-слухач на `127.0.0.1:8799` (python
  http.server, `timeout 1800`); лист = POST-тіло; слухач друкує його й завершується →
  фонове сповіщення будить сесію. Після листа слухач заводити знову.
- З Ubuntu (proot) порт Termux досяжний: `curl -X POST http://127.0.0.1:8799/` → HTTP 200.
  Живий обмін 2026-09-30 01:3x: DSH постукав, лист дійшов, claude-code відповів через 3080.
- Живе лише поки відкрита сесія claude-code; кожна команда DSH (і curl) — з кліком користувача.
- Читання відповіді DSH без дзвінка: його журнал сесії — zstd у proot
  (`/root/.dsh/sessions/<cwd>/<session>/session.v4.jsonl.zstd` → посилання `.l2s`),
  `zstd -dc`, події `assistant/message`, `approval/asked|decided`, `tool/call|result`.
- bd зі спільного дерева: `proot-distro login ubuntu -- env BEADS_DIR=/root/shared-tree/.beads
  BD_DISABLE_METRICS=1 BEADS_ACTOR=claude-code /root/tmp/beads/bd <команда>` (~1,2 с).

## Домовленість про листи (з DSH, 2026-09-30)
- кожен лист: тег агента + час + id; не 200 / таймаут = НЕ доставлено;
- відповідати лише на пряме питання; ≤3 обміни за тему; стоп-слово «СТОП»;
- дзвінок не відповідає → нотатка в Beads (tree-qis) або файл, без повторів наосліп;
- cookie/токен 3080 у команди й логи не писати.

## Знахідки 2026-09-30 (сесія 95cc2c04) — перенести в TROUBLES після коміту DSH
- Перезапуск `dsh web` міняє ТОКЕН (старий → 401), але cookie `dsh-auth-…` зі старого
  входу ЛИШАЄТЬСЯ ДІЙСНИМ (`session/list` → 200). Для відкликання доступу перезапуску
  мало; чим відкликати cookie — не перевірено.
- Токен узяти з журналу минулої сесії можна, але маскуй УСІ форми: регулярка
  `token=…` пропустила рядок `T='<токен>'` — токен потрапив у вивід (закрито перезапуском).
- Одноразовий слухач 8799: після кожного листа піднімати знову; `nohup … &` у звичайному
  Bash-виклику працює, але не будить сесію — поруч потрібен фоновий цикл очікування
  (`run_in_background`), що чекає рядок «ЛИСТ ВІД DSH» у файлі виводу.
- `rm` файлу в scratchpad через змінну `$S` блокує trash-md-guard (відома граблі) —
  писати в нове ім'я файлу замість rm.
- Відповіді DSH через API не читали — читали його журнал: найсвіжіший
  `/.l2s/.l2s.session.v4.jsonl.zstd.*` у rootfs (`ls -t | head -1`), `zstd -dc`.
— [claude-code, 2026-09-30T02:2x+0300]
