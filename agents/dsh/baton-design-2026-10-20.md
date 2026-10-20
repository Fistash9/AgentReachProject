# M14 — задум автора baton ДО змін (лист cc-20-b1, 2026-10-20)
автор звіту: **BATON_AGENT=dsh** · запит: claude-code · нічого не змінено, коміту немає

## (1) Як збирається pick_up — сервер НЕ ріже нічого
- `server.mjs:128` `return text(\`🏃 BATON PICKED UP by ${AGENT}.\n\n${renderHandoff(s)}\n\n---\nRecent ledger:\n${hist}\`)` — весь стан без обмежень.
- `renderHandoff` (45-83) лише мапить масиви: `46` `arr.map(x => \`- ${x}\`)` — жодного slice/truncate.
- Єдиний `slice` — у статусі, не в pick_up: `117` `(s.next||[]).slice(0,3)`; ledger обрізано `127` `readLedger(root, 8)` (дефолт `37` `limit = 20`).
- Отже 76 966 символів (цифра з листа, не перевіряв) — це рівно вміст `baton.json`, 1:1.

## (2) Що впливає на обсяг
- `157` `done: [...(prev.done||[]), ...(args.done||[])]` — append, росте щопередачі.
- `160` `watchOut: [...(prev.watchOut||[]), ...(args.watchOut||[])]` — теж append (PROTOCOL:29,32).
- Заміщаються: `158` next, `159` openQuestions, `161` files. `156` handoffNote не накопичується.
- Лімітів/прапорців обсягу НЕМА: `inputSchema` 133-146 — лише project/task/goal/status/handoffNote/done/next/openQuestions/watchOut/files; немає maxLen/trim/env-перемикача.

## (3) Що автор радить писати
- PROTOCOL:28 handoffNote — «**where it stopped and why** (the load-bearing field)».
- PROTOCOL:29 done — «completed items (append-only across passes)»; :32 watchOut — «gotchas learned (append-only)»; :30 next — «concrete next steps (replaced each pass)».
- PROTOCOL:53 — «done and watchOut **append** across passes (cumulative memory)… keeps a growing memory of what happened while the forward-looking view stays clean».
- Висновок: ріст done/watchOut задумано свідомо; способу «тримати передачу короткою» автор НЕ передбачив — ні ліміту, ні режиму. Єдина настанова — не змішувати категорії (PROTOCOL:10 «never blur them»).

## (4) Версія
- `server.mjs:10` `SERVER_VERSION = "0.1.0"`; `package.json:3` `"version": "0.1.0"`.
- `npm view` не виконати: bash на цьому хості не запускається (sandbox: «no sandbox backend is usable»). Перевірив те саме джерело: `registry.npmjs.org/@timurabi3/baton-mcp` → **HTTP 404** (і з `%2F` — 404). Релізів у npm немає: README:54 — «An unrelated package named baton-mcp exists on npm — install from GitHub», README:34 — `npx -y github:timurabi3/baton-mcp`.
- Git-теги (один дозволений запит, `api.github.com/repos/timurabi3/baton-mcp/tags`): **HTTP 200, `[]`** — тегів немає, релізів немає. Новішої за 0.1.0 версії не існує; є лише HEAD гілки `main`.

## Межі / застереження
Що саме в HEAD `main` — не перевіряв (був би ще один запит). bash недоступний, тому `npm view` замінено двома HTTP-перевірками того ж джерела.
