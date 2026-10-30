# Чи всю користь дістали з даних REA (cc-3010-2)

Звіт про цінність залишків: `/tmp/rea-obs`, `/tmp/Obsidian-1.14.4.apk`, `/root/.npm/_npx`. Нічого не видаляв.

## (А) Ключове
1. **Головне втрачалося**: `run1.json` — єдиний артефакт із **повним семантичним графом** (15 783 вузли, 20 350 зв'язків) по **32 файлах**; у `run2/run3` зв'язків **0**. Цього в моєму звіті немає.
2. **Код графа Obsidian лежить окремими файлами**: `sim.js` 17 693 Б (d3-quadtree/Barnes-Hut), `worker.js` 239 777 Б (Metadata Cache) — читабельніші за app.js, і саме вони потрібні задачам 2 і 3.
3. **Що не подумали порахувати корисним**: `assets/public/app.css` (662 509 Б) — токени теми для Replica; `capacitor.config.json` з `webContentsDebuggingEnabled: true` → живий WebView-дебаг замість статичного реверсу; 195 module-id як база для діфу версій Obsidian.
4. **Кеш npx (510 MB) — без втрат**: два однакові каталоги по 251 MB, відтворюються `npx rea-agents`, версія пінована 6.8.0.
5. Разом до витягу ~2–3 MB із 107 MB; решта — сміття, яке відтворюється.

## (Б) Таблиця цінності
| файл | що корисного містить | задача (1–4) | чи вже записано у звіті | рішення |
|---|---|---|---|---|
| `run1.json` (39 MB) | семантика: 15 783 вузли / 20 350 зв'язків, 9 розібраних JS із 32, 3017 findings — база «що аналізатор витягує з мініфікованого бандла» | 1, 3 | **ні** (звіт згадує лише ім'я файлу, рядок 33) | витягти зведення + граф → видалити |
| `run2.json` (18 MB) | аналіз `app.js` як є: 195 модулів, 2424 вузли/3115 ребер, 2918 findings | 3 | так (рядки 12–20) | витягти `summary`+`statistics` → видалити |
| `run3.json` (18 MB) | те саме на prettified — доводить, що js-beautify не додає фактів | 3 | так (рядок 34, «майже ні») | **видалити** (дубль run2) |
| `pretty/app.pretty.js` (7.8 MB, 150 414 рядків) | людино-читабельні номери рядків: `Metadata Cache Worker` — 68 169; `Graph Worker`/`sim.js` — 92 489-92 490, 93 050-93 051 | 1, 2, 3 | **ні** (у звіті лише назви воркерів, рядок 20) | витягти 3 фрагменти → видалити |
| `apk/assets/public/sim.js` (17 693 Б) | сила-граф: quadtree/Barnes-Hut, як Obsidian рахує розкладку вузлів | 1, 2, 3 | **ні** | **лишити** (перенести в дослідження) |
| `apk/assets/public/worker.js` (239 777 Б) | Metadata Cache Worker: як будується індекс файлів/посилань — модель для живого дерева | 1, 3 | **ні** (лише назва) | **лишити** |
| `apk/assets/public/app.css` (662 509 Б) | дизайн-токени, розміри, теми — візуальна відповідність Replica | 2 | **ні** | витягти `:root`-змінні → видалити |
| `apk/assets/public/app.js` (3 968 611 Б) | сам бандл; без мап, мініфікований — джерело істини, але вже описаний | 3 | так | видалити (APK лишається) |
| `apk/` решта + `index.html`, `i18n.js`, `lib/` | стороннє (pixi, codemirror) і локалі | — | ні | **видалити** |
| `/tmp/Obsidian-1.14.4.apk` (15 177 776 Б) | першоджерело, sha256, відтворюване з офіційного релізу | — | так (рядок 4) | видалити (посилання в звіті) |
| `/root/.npm/_npx/af75…`, `/da7c…` (251 MB × 2) | однакові копії `rea-agents@6.8.0` — інструмент, не дані | 4 | ні | **видалити** (ставиться `npx`) |
| `/root/.npm/_npx/8289…` (9.1 MB) | `js-beautify` — 1 команда відновлення | — | ні | видалити |
| `run*.err`, `peak*_kb` (кілька КБ) | докази запусків (таймаут 300 с, RSS 1 681 MB) | — | так (рядки 12, 21) | **лишити** (докази до звіту) |

## (В) Витягти перед видаленням
1. З `run1.json` — зведення і сам граф:
   `python3 -c "import json;d=json.load(open('/tmp/rea-obs/run1.json'));nr=d['details']['partial_observation']['normalized_result'];json.dump({'statistics':nr['statistics'],'semantic_graph':nr['semantic_graph'],'limitations':nr['limitations']},open('/tmp/extract/run1-graph.json','w'),ensure_ascii=False)"` → перевірено: `/tmp/extract/run1-graph.json` = **31 MB**, зберігає всі 20 350 зв'язків (з 39 MB втрачається лише обгортка evidence).
2. З `pretty/app.pretty.js` — три фрагменти з номерами рядків:
   `sed -n '68140,68200p'` (Metadata Cache Worker), `sed -n '92460,92520p'` і `sed -n '93020,93080p'` (Graph Worker, `/sim.js`).
3. `apk/assets/public/sim.js` + `apk/assets/public/worker.js` — перенести цілими (257 KB).
4. З `app.css` — блок змінних: `sed -n '1,120p' apk/assets/public/app.css` (теми/кольори Replica).
5. З `run2.json` — `summary`, `statistics`, `limitations`, `route_inventory` (доказова база звіту).
6. Одним рядком — ідея на майбутнє: `capacitor.config.json` → `webContentsDebuggingEnabled: true`; це шлях «під'єднати devtools до WebView» замість реверсу (перевірити на живому пристрої — [unverified]).

## (Г) Докази чисел
- `du -sh /tmp/rea-obs apk pretty *.json; du -sh /root/.npm/_npx/*`
- `ls -lS apk/assets/public | head -15` → app.js 3 968 611, app.css 662 509, worker.js 239 777, i18n.js 132 996, sim.js 17 693
- `python3 -c "…run1…nr['statistics']"` → `relevant_files 32, parsed_javascript_files 9, skipped 21, visited_ast_nodes 1 227 601, findings 3017, modules 195`; `len(semantic nodes)=15 783, len(relations)=20 350`
- `python3 -c "…run2/run3…"` → `nodes 2480/2424, edges 3177/3115, limitations 8/7`
- `grep -n 'Graph Worker\|Metadata Cache Worker\|sim\.js' pretty/app.pretty.js` → 68169, 92489-92490, 93050-93051
- `wc -l pretty/app.pretty.js` → 150 414; `head -c 700 apk/assets/public/sim.js` → quadtree/force-layout
- `sha256sum /tmp/Obsidian-1.14.4.apk | cut -c1-16` → b3e5bfa107bb01c4

## (Е) Витяг (числа; код не скопійовано)
### run1.json — повний прогін по теці (32 файли)
`relevant_files 32 · parsed_javascript_files 9 · skipped_javascript_files 21 · text_bytes_read 14 839 815 · visited_ast_nodes 1 227 601 · findings 3017 · modules 195 · parse_failures 0`
`graph: nodes 2537 · edges 3279 · coverage partial` · `semantic: nodes 15 783 · relations 20 350` · `limitations 11` · `route_inventory: sources ≥1 (inventory_id jsri:f02d9518…)`

### run2.json — один файл `app.js` (baseline)
`relevant_files 32 · parsed_javascript_files 1 · visited_ast_nodes 1 130 503 · findings 2918 · modules 195`
`graph: nodes 2480 · edges 3177` · `semantic: nodes 4029 · relations 0 · truncated true` · `routes 0` · `limitations 8`

### Порівняння (головне)
- Семантика: run1 **20 350 зв'язків** проти **0** у run2 — уся втрата при звуженні до одного файлу.
- AST-вузлів: 1 227 601 проти 1 130 503 (+8,6 %); findings 3017 проти 2918 (+99); модулів однаково 195.
- Висновок: `run1` цінний саме зв'язками, не кількістю вузлів.

### Номери рядків у `app.pretty.js` (150 414 рядків)
- `Metadata Cache Worker` — **68 169**
- `Graph Worker` / `new Worker("/sim.js")` — **92 489-92 490** і **93 050-93 051**

### `app.css` — дизайн-токени
- Розмір 662 491 байт; **1 177 унікальних CSS-змінних** виду `--name:`.
- Приклади назв: `--accent-h`, `--accent-l`, `--accent-s`, `--anim-duration-fast`, `--anim-duration-slow`, `--anim-motion-delay`, `--anim-motion-swing`.
- Найчастші префікси (вимір, не оцінка): `--bases-*` 77, `--metadata-*` 46, `--tab-*` 46, `--csstools-*` 43, `--table-*` 39, `--color-*` 37, `--nav-*` 36, `--font-*` 33, `--button-*` 28, `--callout-*` 27.
- Для Replica корисно: `--color-*` (37), `--font-*` (33), `--callout-*` (27) плюс тріада `--accent-h/l/s` — з них складається тема; `--anim-*` задають тривалості й криві.

## (Д) Підсумок
Оброблено 4 з 4 задач; кроків 7.

Тег: — [dsh, 2026-10-30T12:43+0200]

ЗВІТ ГОТОВО
