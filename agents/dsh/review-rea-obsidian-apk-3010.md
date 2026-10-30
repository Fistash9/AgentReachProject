# Перевірка інструмента з відео (REA) на APK Obsidian — 30.10.2026

Що перевіряли: чи здатен `morluto/rea` («Reverse Engineer Anything», `rea-agents@6.8.0`, MCP+CLI) розібрати APK застосунку Obsidian і показати, «як зібрана функція». Перевірка — запуском, не з опису.

## Об'єкт
- `Obsidian-1.14.4.apk`, 15 177 776 Б, sha256 `b3e5bfa107bb01c4…`, з релізу `obsidianmd/obsidian-releases` (офіційне посилання з obsidian.md/download).
- Це Capacitor/WebView-обгортка: `assets/capacitor.config.json` (`appId md.obsidian`, `webDir mobile`), `assets/capacitor.plugins.json` — 13 плагінів, `assets/public/index.html` вантажить `app.js`.
- Логіка — в `assets/public/app.js`: 3 968 611 Б, **0 переносів рядків**, **0 файлів `.map`** (є 1 посилання `sourceMappingURL` на неіснуючу мапу).
- Нативний шар тонкий: `classes.dex` — 10 425 класів, з них `Lmd/obsidian/` ≈ 30 (MainActivity, віджети, QS-tiles), `Lcom/getcapacitor/` 87, решта `androidx`.

## Що дав REA (фактичний запуск)
- Прогін по всій теці `assets/public` з дефолтами: **exit 1**, `code: provider_timeout` (`7 300 000 ms` default… фактично 300 000 мс per-source), 560 с, 40 063 212 Б error-envelope.
- Робоча конфігурація: `--source-path app.js --analysis-timeout-ms 540000` → exit 0, 229 с, 18 257 109 Б; з `js-beautify` (150 414 рядків) — exit 0, 206 с.
- Результат: `modules: 195` (AST точніший за regex: мій regex — 135, REA ⊃ regex, +60), `visited_ast_nodes: 1 130 503`, `findings: 2918`, `parse_failures: 0`.
- Граф: `nodes: 2424, edges: 3115`, з них `imports: 2878`, але справжніх цільових модулів лише 501 (≈17 %); 2199 вузлів — нерезольвнуті `require(<вираз>)`.
- **Семантика: `relations: 0`, `truncated: true`** — графа викликів немає.
- Назв немає: ідентифікатори лише числові (`134 … 9941`); `source_map_reference: 0`.
- Ендпоінти: 21 «кандидат» — усі хибнопозитиви (`rowHeight`, `columnWidth`, `imageAspectRatio`), справжніх маршрутів 0.
- Блок `summary` (IPC, preload, context bridge, browser_windows, native_addon_bindings) — **усі нулі**: модель Electron-на, Obsidian на Android — Cordova/Capacitor.
- Реально нове: worker-и з назвами — `Metadata Cache Worker` (`worker.js`), `Graph Worker` (`/sim.js`); 1 `indexed-db` storage-вузол; 29 asset-вузлів.
- Ціна: ~17 хв, пік RSS 1 681 MB, npx-кеш 510 MB.

## Чому шлях JADX не рятує
REA-Android — обгортка над headless JADX (`docs/android-analysis.md`). На цьому APK дасть маніфест, підпис і місток `WebView`→JS, тобто «як обгортка викликає JS», а не «як зібрана функція». Ціна: JDK 17 headless 121.8 MB + `jadx-headless-mcp` 42.6 MB, RAM на межі (вільно ~2.5 GB).

## Правова межа
Terms Obsidian, п. (iii): заборонено «disassemble, reverse engineer or decompile… **except for the purpose of developing Third Party Plugins for non-commercial use**»; п. (iv) — доступ «in order to develop a competing product». Отже аналіз під власний некомерційний плагін — єдиний явно дозволений мотив.

## Висновок
REA на web-шарі Obsidian **працює, але користі мало**: 195 безіменних модулів і 0 семантичних зв'язків. Для практики швидше дають `unzip` + `js-beautify` + `grep` по `app.js`. Сильні сторони REA (підписи APK, firmware, нативні бінарники) тут не задіяні.

## Артефакти
- `/tmp/rea-obs/` — 107 MB: `apk/` (розпаковане), `pretty/app.pretty.js`, `run1.json` (39 MB), `run2.json`, `run3.json`, `.err`-логи, `peak*_kb`.
- `/tmp/Obsidian-1.14.4.apk` — 15 177 776 Б.
- `/root/.npm/_npx` — 510 MB (два однакові npx-каталоги `rea-agents` по 251 MB); не чистив.

## [не перевірено]
- `capture-adb-*` / `decode-android-resources` на APK-шарі — не запускав.
- Десктопний `obsidian-1.14.5.asar.gz` (9.0 MB) — не завантажував; чи є там source maps — невідомо.
- Чи дасть JADX-шлях щось понад маніфест на практиці — не запускав (RAM-ризик).
- Нічого в `AgentReachProject` / `/root/dsh-app` не змінено, комітів нема; цей файл — єдина зміна в проєкті.

ЗВІТ ГОТОВО
