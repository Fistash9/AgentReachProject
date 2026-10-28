# agent-browser на телефоні (Termux): обхід відсутнього android-бінарника — план

— [claude-code, 2026-10-28; підзавдання «знайди обхідний шлях, як дати доступ до браузера на андроід»; лише дослідження,
нічого не встановлено; завантажені файли — у `$PREFIX/tmp/ab-research/` (поза проєктом, не запускались)]

Мета: скіл agent-browser (текст у ~/.agents/skills/agent-browser) має реально працювати на цьому телефоні.
Умова зупинки: план записано. Обмеження користувача 22.10: спершу рішення всередині Termux; ADB/режим розробника — останнім і з позначкою.

## 1. Що кажуть наші записи (grep TROUBLES/BACKLOG)
- Рецепт «неставне»: TROUBLES «Картка: як ставити «неставне» в Termux» (~5376), п.2 — linux-збірка через `grun` (Freebuff 2517, iwe 3119);
  аргументи з пробілами ламає grun (3523) → запуск `env -u LD_PRELOAD $PREFIX/glibc/lib/ld-linux-aarch64.so.1 --library-path …`.
- Браузера в Termux ми НЕ пробували: grep chromium/playwright/puppeteer у TROUBLES/BACKLOG/CONTEXT/ECOSYSTEM/GOALS дає лише
  Electron (Obsidian) і BACKLOG ~770–785 (план «Chrome телефона через adb + chrome-devtools-mcp», не перевірено).
- Найближчий досвід — Obsidian (Electron = Chromium) у proot-debian: 13 процесів на сам обвіс, решта Termux ≈20; Android (HyperOS 3) вбиває
  сесію при >~32 процесів (TROUBLES 5775, 5802). Фантом-ліміт без ADB не змінити. Висновок: кількість процесів браузера — головний ризик.
- proot Ubuntu (DSH) і контейнер obsidian-debian (debian:trixie) існують (3453, 5700): bwrap/user-namespace там немає (3590) → браузер лише з `--no-sandbox`.

## 2. Що вміє agent-browser v0.40.0 (першоджерело: README + cli/src, vercel-labs/agent-browser)
- Власний Chromium: `--executable-path <шлях>` / `AGENT_BROWSER_EXECUTABLE_PATH`; `--args "--no-sandbox,--disable-dev-shm-usage"`.
  Запускає Chromium з `--headless=new --remote-debugging-port=0` (cdp/chrome.rs:466,509); `--no-sandbox` сам додає лише в контейнері/root (585).
- Підключення до вже запущеного браузера: ТАК — `agent-browser connect 9222`, `--cdp <порт|ws-URL>`, `--auto-connect`.
- Рушії: `--engine chrome|lightpanda|obscura`. Хмарні провайдери (`-p`): browserless, browserbase, browseruse, kernel, agentcore (+ плагіни).
- Assets v0.40.0: agent-browser-{darwin-arm64,darwin-x64,linux-arm64,linux-musl-arm64,linux-musl-x64,linux-x64,win32-x64.exe}. android — нема.
- Issues на цю тему (відкриті): #1477 (баг: getBinaryName без android), #1500 (PR dpersek: android→linux + запуск через grun; не змерджено;
  автор «не міг зробити реальний smoke-тест на Termux»), #1587 (Unsupported platform android-arm64; npm-пакет має порожній agent-browser-android-arm64).
  У v0.40.0 лаунчер bin/agent-browser.js grun не викликає (grep: 0 збігів). Рядки «97–100 з grun» з #1477 — з іншої версії.
- Ключове спостереження (перевірено readelf): лаунчер JS — лише обгортка; сам бінарник можна запускати напряму, в обхід `npm`/JS.
  - `agent-browser-linux-arm64` (15 947 504 Б, sha256 f33b4dd9…9e53): динамічний glibc — INTERP `/lib/ld-linux-aarch64.so.1`,
    NEEDED libm/libc/libpthread/libdl, символи до GLIBC_2.28 (у Termux glibc 2.44 — достатньо).
  - `agent-browser-linux-musl-arm64` (15 763 544 Б): **статичний** — ні INTERP, ні DYNAMIC (readelf -l: 0 збігів), тип EXEC. Запускається
    ядром напряму, без grun і без glibc. [Не запускалось — тільки статичний аналіз.]
- Підводний камінь grun: CLI запускає демон як `env::current_exe()` + `AGENT_BROWSER_DAEMON=1` (cli/src/connection.rs:929–966). Під `grun`
  /proc/self/exe — завантажувач ld.so, тому демон не стартує [висновок з коду; не запускалось]. До того ж grun скидає LD_PRELOAD, додає
  `$PREFIX/glibc/bin` у PATH і preload glibc-termux-exec — це успадкує Termux-Chromium (bionic). Отже «бінарник через grun» (варіант а) гірший за статичний musl.
- Chrome for Testing (`agent-browser install`) тепер має linux-arm64 (curl JSON google), але це glibc-Chrome, якому потрібні nss/gtk у glibc-світі —
  у Termux їх нема. `agent-browser install` НЕ запускати.

## 3. Середовище (лише читання)
- aarch64, node v26.4.0, x11-repo і glibc-repo встановлені, grun є, patchelf-glibc 0.19.1, cargo 1.98.1 / rustc 1.98.1 є, вільно 281 ГБ.
- `pkg show chromium`: версія 156.0.8078.47, завантаження 160 МБ, у системі 678 МБ (+ залежності: gtk3, pipewire, cups, mesa, nss… — скільки
  з них ще не стоїть, `pkg install -s` не рахував). Репо: termux-x11 (x11/main). Не встановлено.
- Збірка пакета (termux-packages x11-packages/chromium/build.sh:373,439): збирає `chrome` і **`headless_shell`**, `ozone_platform_headless=true`;
  команди `chromium-browser` (скрипт-обгортка) і `headless_shell` у $PREFIX/bin. Тобто headless у пакеті є; запуск без X-сервера — за доками
  Chromium, у Termux [не перевірено]. Issues termux-packages за запитом «chromium headless» — лише авто-апдейти host-tools, живих скарг нема (відгуків немає ≠ працює).
- Процеси зараз: 19 (ps -e).

## 4. Варіанти
Критерій безпеки для всіх: перед кожним запуском браузера — `ps -e | wc -l` (база 19–26), під час — сторож (див. п.6); не запускати разом із Obsidian/DSH-піком.

### (а) glibc-бінарник linux-arm64 через grun + Chromium з x11-repo
- Кроки: завантажити бінарник (16 МБ, sha256 звірити); `pkg install chromium` (160 МБ → 678 МБ + залежності); запуск `grun ./agent-browser … --executable-path $PREFIX/bin/chromium-browser`.
- Ризики: демон через current_exe не стартує (див. п.2); grun-оточення псує дочірній bionic-Chromium; процесів Chromium багато.
- Налаштування телефона: ні. Відкат: `rm` бінарника (TRASH.md ДО), `pkg uninstall chromium`.
- Тест: `grun ./agent-browser --version` (має вивести 0.40.0), потім `… open about:blank`. Очікую збій на демоні → переходити до (а′).
- Варіант-ремонт (а″): копія бінарника з `patchelf --set-interpreter $PREFIX/glibc/lib/ld-linux-aarch64.so.1 --set-rpath $PREFIX/glibc/lib` і
  запуск через `env -u LD_PRELOAD`. Тоді current_exe = сам файл. Слабке місце — зміна 16-МБ бінарника (контрольна сума інша). [не перевірено]

### (а′) СТАТИЧНИЙ musl-бінарник напряму + Chromium з x11-repo  ← найкращий кандидат
- Кроки: `agent-browser-linux-musl-arm64` (15,8 МБ) → `~/sandbox-browser/ab` + `chmod +x`; `pkg install chromium`. Ніякого grun/npm.
- Чому має працювати: нема динамічного завантажувача; current_exe = сам файл → демон стартує; PATH/LD_PRELOAD Termux не псуються.
- Ризики: (1) musl-статик читає /etc/resolv.conf, якого на Android нема — DNS самого CLI може не працювати, але CDP іде на 127.0.0.1, а мережу веде Chromium (bionic, свій резолвер); (2) seccomp Android може вбити рідкісний syscall («Bad system call» — бачили у Freebuff при відкритті браузера); (3) Chromium: процеси (browser, gpu, network, renderer, zygote), `/dev/shm` нема → `--disable-dev-shm-usage`; (4) `--headless=new` у Termux-збірці — не перевірено;
  (5) PIE/exec-права: EXEC не-PIE, база 0x1000000 — ядро має завантажити, але SELinux/мапи Android [не перевірено].
- Налаштування телефона: ні. Відкат: `pkg uninstall chromium`; rm пісочниці (запис у TRASH.md ДО).
- Тест (по порядку, зупинитись на першому збої): 
  1. `~/sandbox-browser/ab --version`
  2. `chromium-browser --headless=new --no-sandbox --disable-dev-shm-usage --dump-dom about:blank` (Chromium окремо від agent-browser; `ps -e | wc -l` до/після)
  3. `~/sandbox-browser/ab --executable-path $PREFIX/bin/chromium-browser --args "--no-sandbox,--disable-dev-shm-usage" open https://example.com && ab snapshot -i && ab close`

### (б) `cargo install agent-browser` (рідна збірка під android)
- На crates.io лише 0.19.0 (одна версія, оновлено 2026-03-14; npm — 0.40.0) → потрібен `cargo install --git https://github.com/vercel-labs/agent-browser --tag v0.40.0` (шлях до Cargo.toml у cli/).
- Ризики: збірка 15–40 хв (TROUBLES #07), не вбивати; чимало коду під `cfg(target_os = "linux")` (9 файлів: chrome.rs, browser.rs, connection.rs, install.rs…) — для android-таргета ці гілки вимкнуться, поведінка не перевірена; залежності можуть не збиратись (bionic).
- Налаштування: ні. Відкат: `cargo uninstall agent-browser`. Тест: збірка + `agent-browser --version`. Не рекомендую: довго, а готовий статичний musl-бінарник робить те саме.

### (в) proot (debian/ubuntu) + chromium всередині + linux-arm64 бінарник
- Кроки: контейнер obsidian-debian (debian:trixie, вже є) або новий; `apt install chromium` (справжній deb у Debian; в Ubuntu `chromium-browser` — snap-заглушка [не перевірено]); `agent-browser-linux-arm64` усередині (рідний glibc, current_exe працює); виклик з Termux: `proot-distro login obsidian-debian -- …`.
- Плюси: найближче до «як на Linux»; підтверджено, що Electron там працює. Мінуси: розмір (сотні МБ, debian-chromium — [не перевірено]), `--no-sandbox` обов'язково, proot+ptrace повільніше, proot-допоміжні процеси додають до лічильника; «виміряне в proot ≠ Termux» (TROUBLES 4172).
- Налаштування: ні. Відкат: `proot-distro remove` (для obsidian-debian — це зламає Obsidian-пісочницю; краще окремий контейнер) .
- Тест: `proot-distro login <c> -- agent-browser --version`, далі `open example.com` з `--args "--no-sandbox"`.

### (г) хмарний браузер (CLI лишається локальний — потрібен (а′) або (а″) для самого бінарника)
- Провайдери в agent-browser: browserless, browserbase, browseruse, kernel, agentcore. Усі — акаунт/API-ключ (agentcore — AWS).
- Безкоштовні рівні — за третіми сторонами, суперечливо (агрегатори, не сторінки вендорів): Browserbase ≈1 браузер-година/міс, сесія ≤15 хв;
  Browserless ≈1000 одиниць/міс (1 од.=30 с), 2 одночасних, сесія ≤1 хв; Kernel і Browser Use — безкоштовні ліміти не знайдено. [не перевірено на сторінках вендорів]
- Плюси: на телефоні 1–2 процеси замість десятка, нуль 678 МБ. Мінуси: сторінки й логіни йдуть до стороннього; акаунт — рішення користувача; платне — спершу «так» (правило проєкту).
- Налаштування телефона: ні. Відкат: видалити змінну `*_API_KEY`. Тест: `BROWSERLESS_API_KEY=… ab -p browserless open https://example.com` (після (а′) кроку 1).

### (ґ) Chrome самого телефона через CDP
- agent-browser вміє `--cdp`/`connect`/`--auto-connect`, але Chrome Android віддає DevTools лише через abstract-сокет `chrome_devtools_remote`, доступний через `adb forward` (BACKLOG ~770). **Потрібна зміна налаштувань телефона**: режим розробника + бездротове налагодження + adb pair (рішення користувача 22.10 — останній варіант). Ризик: доступ до всіх вкладок/сесій. Статус: не пробувати, поки (а′)/(д) не провалились.

### (д) Інше знайдене
- **Lightpanda** (`--engine lightpanda`, документовано в agent-browser): реліз 1.0.2 має `lightpanda-aarch64-linux` (73,8 МБ, glibc-динамічний: INTERP /lib/ld-linux-aarch64.so.1; NEEDED libm/libc/ld-linux). Один процес, за заявою авторів у 10× менше пам'яті (твердження авторів). Мінуси: не Chrome — немає --profile/--state/--extension, скріншоти «залежать від підтримки CDP»; потрібен `patchelf --set-interpreter … --set-rpath …` на копії (бо поряд з musl-CLI нема glibc-завантажувача). Це найкращий запасний варіант саме через ліміт процесів.
- Obscura (`--engine obscura`, експериментальний) — не досліджував.
- Окремий запуск `chromium-browser --headless=new --remote-debugging-port=9222 &` + `ab --cdp 9222 …` — розв'язує «хто запускає браузер»: можна тестувати Chromium і CLI окремо.

## 5. Рекомендація
**(а′): статичний `agent-browser-linux-musl-arm64` напряму + `pkg install chromium` (≈160 МБ завантаження / 678 МБ на диску + залежності) і `--executable-path`** — бо це єдиний варіант без grun і npm, де демон отримує коректний current_exe, і без зміни налаштувань телефона. Запасний: Lightpanda (патчений glibc-бінарник, 74 МБ), якщо Chromium впирається в ліміт процесів.

## 6. План проби в пісочниці (поза проєктом)
Пісочниця `~/sandbox-browser/` (нова, порожня; файли ззовні — untrusted: запускати лише після sha256). Мета проби: `snapshot` реальної сторінки зі скіла agent-browser на телефоні. Зупинка: перший збій кроку → запис у TROUBLES, не «спробуємо ще».
0. Перед стартом: ворота (пам'ять «підтвердити зміну» — `pkg install` вимагає «так» користувача; pkgtruth-перевірка пакета `chromium`); `ps -e | wc -l` → записати базу.
1. Скопіювати з `$PREFIX/tmp/ab-research/bin/` musl-файл → `~/sandbox-browser/ab`, `chmod +x`, `sha256sum` (звірити з релізом), `./ab --version`. Збій тут → (а″) патч-glibc.
2. Сторож процесів: цикл `ps -e | wc -l >> procs.log` кожні 2 с у фоні (як mem.log в sandbox-obsidian); поріг ручної зупинки — 28.
3. `pkg install chromium` (одна дія; дивитись, що доставить зі залежностей: `pkg install -s chromium` спершу — лічильник пакетів).
4. `chromium-browser --headless=new --no-sandbox --disable-dev-shm-usage --dump-dom about:blank` → код 0? Піки в procs.log?
5. `./ab --executable-path $PREFIX/bin/chromium-browser --args "--no-sandbox,--disable-dev-shm-usage" open https://example.com`, `./ab snapshot -i`, `./ab close`; після — `ps -e | wc -l` має повернутись до бази (демон гасне сам через 1 год — `close` обов'язково).
6. Якщо 1–5 ок: обгортка `$PREFIX/bin/agent-browser` (записати в tmp і `mv -f`, не `>` — TROUBLES картка п.8) з `AGENT_BROWSER_EXECUTABLE_PATH`/`AGENT_BROWSER_ARGS`; скіл агента перевірити однією реальною задачею.
Відкат усього: `pkg uninstall chromium`, видалити пісочницю й обгортку (TRASH.md ДО видалення), `ps -e` чисто.

## 7. Premortem
Якщо це провалилось — найімовірніше, Chromium (десяток процесів) разом із базою Termux перевищить фантом-ліміт 32, Android вб'є сесію ще до першої сторінки (як 21–22.10 з Obsidian); тоді — Lightpanda або хмарний браузер.

## 8. Не перевірено (чесно)
- Жоден бінарник не запускався (заборона) — «працює» не стверджується; musl-статик на Android і демон-через-current_exe — висновки з readelf/коду.
- Чи Termux-Chromium справді запускається headless без X-сервера і скільки процесів дає (оцінка 5–8 — здогадка, не вимір).
- Залежності chromium у pkg (скільки ще не встановлено); фактичний розмір завантаження.
- Free-tier хмарних провайдерів — лише з агрегаторів.
- debian-chromium у proot (розмір, робота); Ubuntu `chromium-browser`=snap — з пам'яті.
- Чи vercel-labs змерджить PR #1500 (тоді лаунчер npm запрацює сам).
- Джерела: github.com/vercel-labs/agent-browser (README, cli/src/connection.rs, cli/src/native/cdp/chrome.rs, docs/content/docs/engines/lightpanda.mdx,
  issues #1477 #1500 #1587), github.com/termux/termux-packages x11-packages/chromium/build.sh, github.com/lightpanda-io/browser release 1.0.2,
  crates.io/api/v1/crates/agent-browser, googlechromelabs.github.io/chrome-for-testing; вендорські ціни — агрегатори (agentdeals.dev, tinyfish.ai та ін.).
