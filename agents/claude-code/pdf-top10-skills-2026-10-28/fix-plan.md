# find-skills: як змусити `npx skills find …` працювати в Bash Claude Code на Termux (план, 2026-10-28)

— [claude-code (під-агент), 2026-10-28]. Мета: НАЙМЕНША правка, щоб команда зі скіла працювала тут із вимкненою телеметрією, без зміни тексту скіла автора. Нічого в системі не змінено (лише читання; цей файл — єдиний запис).

## 1. Наші записи (grep по TROUBLES.md, RULES-WHY.md)
- TROUBLES.md:6672–6678 (сьогодні): сам цей баг для find-skills; обхід через `node …/cli.mjs`. `npx skills find` зі скіла «тут не спрацює без правки».
- TROUBLES.md:353–359 (mcp-probe) і 702–714 (pkgtruth): той самий shebang-баг `#!/usr/bin/env node`; лікування в обох — **запуск напряму через node** (у settings pkgtruth викликається через node). Обгортки/termux-fix-shebang у записах не застосовували.
- TROUBLES.md:3523–3526: `env -u LD_PRELOAD …` як обхід для glibc-програм (grun) — LD_PRELOAD уже мішав glibc-бінарникам.
- TROUBLES.md:989–991: `claude-exec.c` скидає `LD_PRELOAD`/`LD_LIBRARY_PATH`.
- RULES-WHY.md: збігів на ці слова нема (grep порожній).

## 2. Факти середовища (перевірено в цій сесії)
- termux-exec Є: пакет `termux-exec/stable 1:2.5.0-1` (+ `termux-exec-glibc 1.0`); у `$PREFIX/lib/` є `libtermux-exec-ld-preload.so`, `libtermux-exec-direct-ld-preload.so`, `libtermux-exec-linker-ld-preload.so`, `libtermux-exec.so` [ls, pkg list-installed].
- `LD_PRELOAD` порожній: і в Bash Claude Code (`env | grep` — порожньо), і в `bash -lc 'echo $LD_PRELOAD'` → `[]` (у login-shell цього середовища теж порожній). Звичайне вікно Termux окремо не перевіряли [не перевірено].
- ЧОМУ порожній: лаунчер `~/.local/bin/claude` останнім рядком робить `exec env -u LD_PRELOAD -u LD_LIBRARY_PATH "$GLIBCLD" --library-path … claude-native` — Claude Code тут це glibc-бінарник, і bionic-прелоад свідомо скидається [прочитано: ~/.local/bin/claude]. Тобто «термукс-exec не діє» — не випадковість, а наслідок запуску через glibc-лінкер.
- `/usr/bin/env` нема (`ls` → No such file). `$PREFIX/bin/npx` має shebang `#!/data/data/com.termux/files/usr/bin/env node` (тому сам npx запускається). node v26.4.0, npm 11.20.0, `$PREFIX=/data/data/com.termux/files/usr`.
- `$PREFIX/bin/skills` нема. Глобально пакет skills не стоїть (`npm ls -g` без нього). У кеші: `~/.npm/_npx/0757c8f0298e564a/node_modules/.bin/skills -> ../skills/bin/cli.mjs`, у cli.mjs shebang `#!/usr/bin/env node`.
- Env для Bash: `~/.claude/settings.json` env-ключі: `USE_BUILTIN_RIPGREP`; `.claude/settings.local.json` проєкту: `CLAUDE_CODE_EXECPATH`, `CLAUDE_CODE_DISABLE_SEARCH_SHIMS`; `.claude/settings.json` проєкту нема. Змінних *telemetry*/*do_not_track*/*preload* у поточному env нема.
- Причина «skills: not found» (виведено з коду npm, не з вгадування): npx запускає `sh -c "skills find …"` з PATH, де першим стоїть `…/_npx/<хеш>/node_modules/.bin`; там `skills` — симлінк на cli.mjs; ядро не може виконати shebang `/usr/bin/env` → sh друкує «not found», 127.
- Телеметрія пакета: `isEnabled(){return !process.env.DISABLE_TELEMETRY && !process.env.DO_NOT_TRACK}` — достатньо будь-якої з двох [перевірено: grep у ~/.npm/_npx/0757…/skills/dist/cli.mjs, рядок 2809].

## 3. Як npx шукає бінарник (з коду встановленого npm 11.20.0)
[перевірено: $PREFIX/lib/node_modules/npm/node_modules/libnpmexec/lib/index.js:160–175 і lib/commands/exec.js:61–75]
Якщо передано команду без `--package`: (1) шукає bin з такою назвою у локальних пакетах проєкту; (2) шукає `node_modules/.bin/<назва>` вгору від cwd; (3) **`globalPath && fileExists(globalBin/<назва>)` → кладе `globalBin` (`$PREFIX/bin`) у PATH і запускає одразу, без мережі й кешу**. `fileExists` = `stat().isFile()` (симлінк на файл проходить). `globalPath` задано, коли localPrefix ≠ globalPrefix (звичайний випадок поза `$PREFIX`). (4) інакше — ставить у `_npx`-кеш (шлях, що падає зараз).
Висновки:
- Виконуваний файл `$PREFIX/bin/skills` npx ПІДХОПИТЬ для `npx skills …` (гілка 3). Він потрапляє в PATH першим (binPaths ставляться перед рештою — set-path.js).
- Глобально встановлений пакет npx теж бере — але лише через наявність файла `$PREFIX/bin/skills` (гілка 3 дивиться на файл, не на manifest).
- ПАСТКА: `npx skills@1.7.4 …` (зі версією) → `args[0]`=«skills@1.7.4», файла з такою назвою нема → йде гілка 4 (кеш), тобто обгортка НЕ спрацює. Скіл автора пише `npx skills …` без версії — цього досить.
- Кеш-гілка: без обгортки `npx skills` без версії може знову питати реєстр про «latest» і створювати нову теку-хеш у `_npx`.

## 4. Варіанти

### (а) Обгортка `$PREFIX/bin/skills`
- Що/де: новий файл `/data/data/com.termux/files/usr/bin/skills` (chmod +x), приблизно:
```sh
#!/data/data/com.termux/files/usr/bin/sh
# Termux: обгортка для `npx skills` (нема /usr/bin/env); телеметрію вимкнено тут, не глобально
export DISABLE_TELEMETRY=1 DO_NOT_TRACK=1
for f in /data/data/com.termux/files/usr/lib/node_modules/skills/bin/cli.mjs \
         /data/data/com.termux/files/home/.npm/_npx/*/node_modules/skills/bin/cli.mjs; do
  [ -f "$f" ] && exec node "$f" "$@"
done
echo "skills: cli.mjs не знайдено (кеш _npx очищено?). Відновити: DISABLE_TELEMETRY=1 npx --yes skills@1.7.4 --version" >&2
exit 127
```
- npx підхопить: так (розд. 3, гілка 3) [перевірено кодом; сам запуск ще не пробували].
- Відкіт: видалити один файл (за правилом — запис у TRASH.md до `rm`).
- Переживе очищення кешу `_npx`: ні, якщо cli.mjs лише там; тоді обгортка друкує підказку (127). Пакет skills при цьому не оновлюється сам — обгортка бере те, що в кеші/глобально (оновлення = нова тека-хеш; glob бере першу за алфавітом — якщо хешів кілька, може взяти старий) [ризик, не перевірено на практиці].
- Телеметрія: вимкнена всередині обгортки (лише для процесу skills).
- Інші програми/Claude Code: ніяк, крім того, що команда `skills` у PATH стає «нашою»; нічого глобально в env не міняється.
- Ризики: (і) pin версії не виконується; (іі) `npx skills@версія` обгортку обходить (див. пастку); (ііі) обгортка виконує код з кешу — той самий, що й так виконували б.

### (б) `npm i -g skills@1.7.4` + `termux-fix-shebang`
- Що/де: ставить пакет у `$PREFIX/lib/node_modules/skills`, симлінк `$PREFIX/bin/skills`; `termux-fix-shebang` переписує перший рядок cli.mjs на `#!/data/data/com.termux/files/usr/bin/env node` [термукс-fix-shebang існує: ls $PREFIX/bin/termux-fix-shebang].
- npx підхопить: так (файл `$PREFIX/bin/skills` існує і виконується).
- Телеметрія: НЕ вимикає — потрібне ще DISABLE_TELEMETRY (обгортка або env). Тобто саме по собі не вирішує мету.
- Відкіт: `npm rm -g skills`. Переживе очищення `_npx`: так. Оновлення пакета (`npm i -g skills@…`) затре правку shebang — треба повторити.
- Ризики: це npm install у глобальний простір (потрібне окреме «так»); змінюється файл пакета; з рамкою «найменша правка» — більше за (а). Хук install-check/pkgtruth може спрацювати на `npm i` [у записах: pkgtruth блокує лише підозрілі пакети; для skills — не перевірено].
- Комбінація (б)+(а): після глобального встановлення обгортка (а) знаходить cli.mjs за стабільним шляхом (перший у glob-списку), кеш `_npx` більше не критичний. Але npm не перезапише чужий файл `bin/skills` без `--force`, а симлінк npm створить сам — потрібно спершу покласти обгортку або замінити симлінк (ще одне видалення).

### (в) LD_PRELOAD termux-exec в env Claude Code
- Що/де: `env.LD_PRELOAD=…/libtermux-exec-ld-preload.so` у settings.json. Тоді exec з shebang `/usr/bin/env` перепише termux-exec [за документацією termux-exec — не перевірено в цій сесії].
- Ризики (оцінка, НЕ перевірено запуском і навряд чи варто пробувати): Claude Code — glibc-бінарник, лаунчер навмисно робить `env -u LD_PRELOAD` (розд. 2); settings `env` записується в process.env і діє на ВСІ підпроцеси (за code.claude.com/docs/en/env-vars: «writes each env entry into the process environment»). Підпроцеси, що йдуть через glibc-лінкер (CLAUDE_CODE_EXECPATH=claude-exec для grep/find-обгорток, glibc-программи типу backlog через grun), отримали б bionic-бібліотеку → ймовірні збої. Наш запис TROUBLES 3523–3526 уже фіксує, що LD_PRELOAD ламає glibc-запуск. Зачіпає всі команди, не лише skills. Найширша зміна, найбільший ризик — НЕ рекомендую.
- Відкіт: прибрати ключ; переживе все (бо не залежить від кешу). Телеметрію не вимикає.

### (г) DO_NOT_TRACK=1 / DISABLE_TELEMETRY=1 в env Claude Code
- Вимикає телеметрію skills (розд. 2), але НЕ лікує «not found» (лише телеметрія, не shebang) — це половина задачі.
- Зачіпає сам Claude Code: з code.claude.com/docs/en/env-vars (прочитано лише перші 100000 з 186764 символів сторінки): `DISABLE_TELEMETRY` — з тих змінних, що діють за фактом наявності («any non-empty value including 0»); `DISABLE_TELEMETRY`/`DO_NOT_TRACK` вимикають опитування (feedback survey) [цитата з сторінки]. Повний перелік того, що ще вимикається, у непрочитаній частині — [не перевірено]. Тобто змінює поведінку самого Claude Code (мінімум опитування, ймовірно й телеметрію) — ширше, ніж потрібно. Якщо потрібно — краще вузько в обгортці (а).
- Відкіт: прибрати ключ у settings.

### (ґ) Інші
- (ґ1) `termux-fix-shebang` прямо на файл у кеші `_npx/…/skills/bin/cli.mjs`: найменша дія, але правка зникає при оновленні/очищенні кешу; телеметрію не вимикає; змінює файл стороннього пакета. Гірше за (а).
- (ґ2) Не міняти нічого, а викликати `DISABLE_TELEMETRY=1 DO_NOT_TRACK=1 node …/cli.mjs find …` (поточний обхід, TROUBLES 6676): працює, але команда не збігається з текстом скіла, і хеш у шляху може змінитися; для моделі — додаткова примітка в пам'ять/правило замість зміни системи. Якщо обгортка не потрібна — це «нульова» правка.
- (ґ3) Власний шлях без хеша (симлінк `~/.local/share/skills-cli -> …/_npx/<хеш>/node_modules/skills`) — те саме, що (а), але гірше: ще один файл.
- (ґ4) /usr/bin/env створити — на не-root Termux неможливо (корінь `/usr` недоступний) [не перевірено повторно; proot-distro дає окреме середовище, не це].

## 5. Рекомендація
Варіант (а): обгортка `$PREFIX/bin/skills` — єдина зміна — один файл; npx підхоплює її за кодом (розд. 3), телеметрія вимикається лише для цього процесу, Claude Code і решта програм не зачеплені, відкіт = видалення файла.
Додатково (без коду): не писати `npx skills@<версія> …` — це обходить обгортку.

### Перевірка після застосування (точні команди, у такому порядку)
1. `ls -l /data/data/com.termux/files/usr/bin/skills` — файл виконуваний (-rwx).
2. `env -i PATH=/data/data/com.termux/files/usr/bin sh -c 'command -v skills'` — друкує `…/usr/bin/skills`.
3. `npx skills find handoff` — має вивести список скілів, exit 0 (раніше: «sh: 1: skills: not found», 127). Перевірити код: `npx skills find handoff >/dev/null; echo exit=$?`.
4. Що телеметрія вимкнена: `sh -c 'grep -c "DISABLE_TELEMETRY=1" /data/data/com.termux/files/usr/bin/skills'` → 1; прямий доказ відсутності запитів на www.skills.sh/tele — [не перевірено; можна лише через `strace`/мережевий монітор, на Termux недоступно без додаткового ПЗ].
5. Негативний тест: `npx skills@1.7.4 --version` має й далі падати (127) — підтвердження пастки «зі версією обгортка не діє» (запускати лише з DISABLE_TELEMETRY=1 DO_NOT_TRACK=1 у змінних).

## 6. Що не перевірено
- Чи справді `npx skills find` через обгортку працює (код npm читали, не запускали — заборонено).
- Поведінка в звичайному вікні Termux (там LD_PRELOAD, можливо, є).
- Повний текст env-vars документації Claude Code (прочитано 100000 з 186764 симв.): чи DISABLE_TELEMETRY/DO_NOT_TRACK вимикають ще щось у Claude Code.
- Наслідки LD_PRELOAD для glibc-підпроцесів Claude Code (оцінка, не запуск).
- Чи очищує `npm cache clean` теку `~/.npm/_npx`.
- Чи хук install-check реагує на `npm i -g skills`.
