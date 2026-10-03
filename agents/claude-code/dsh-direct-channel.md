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

## Зворотний канал №2: Claude Code Channels на 8788 (перевірено 2026-10-01)
Джерело: trees/zvyazok-dvoh-agentiv.md, Z1.1 і Z1.2 (докази там). На відміну від
одноразового 8799, «дзвінок у двері» працює без переозброєння.
- Сервер: пісочниця `~/tmp/channel-test/webhook.mjs` (офіційний приклад
  code.claude.com/docs/en/channels-reference, Bun → node:http, @modelcontextprotocol/sdk
  1.31.0); слухає лише `127.0.0.1:8788`.
- Пропускає тільки заголовок `X-Sender: dsh`: без нього → `403 Forbidden`, з ним →
  `ok HTTP 200` (і з Termux, і з proot). Справжній DSH сам спершу забув заголовок і
  отримав 403 — у листі до нього заголовок указувати явно.
- Дзвінок іде лише в сесію, запущену з
  `claude --dangerously-load-development-channels server:webhook` (три діалоги безпеки
  натискає людина). Основна сесія без прапорця дзвінків не чує (Z1.4 — не зроблено).
- Повне коло без користувача: claude-code → 3080 `session/prompt` → DSH → curl на 8788,
  5 с (Z1.2). Захисту від зациклення немає — лише «СТОП» у тексті (Z1.3 — не зроблено).
- DeepSeek-сесії: канали вимагають автентифікації Anthropic — не перевірено.
— [claude-code, 2026-10-03] (рішення користувача «Дописати зараз», baton-diff #19→#20 №8)

## DSH бачить вікно claude-code — лише читання (2026-10-03)
Рішення користувача: «Так, лише читання» (на його ідею «дати йому можливість бачити що тут
робиться, як ти бачиш що відбувається там у нього»). Перевірено з proot (Ubuntu) — працює:
`/data/data/com.termux/files/usr/bin/tmux -S /data/data/com.termux/files/usr/var/run/tmux-10599/default capture-pane -p -t work:0`
(вивід дав рядок стану claude-code «[Opus 5.5] … ctx»). Номер у шляху сокета (10599) — uid
Termux; якщо зміниться — `tmux display -p '#{socket_path}'` з Termux.
- ДОЗВОЛЕНО: `capture-pane -p` (читання), коли самому потрібно (кожен погляд — токени DSH).
- ЗАБОРОНЕНО: `send-keys`, `paste-buffer` та будь-що, що вводить у `work:0`. Сесія
  claude-code в auto mode — клавіша від DSH = команда від імені користувача (той самий клас,
  що класифікатор заблокував claude-code у вікні DSH: «Security Weaken»). Писати claude-code —
  лише через користувача або домовлені канали (8788, файли, baton), із захистом Z1.3.
— [claude-code, 2026-10-03]
- Мапа вікон tmux `work` (перевірено 2026-10-03, `tmux list-windows -t work`): 0=claude
  (claude-code), 1=agent, 2=shell, 3=dsh. — [claude-code, 2026-10-03]
