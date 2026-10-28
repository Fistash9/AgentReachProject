# OmniRoute — розбір (2026-10-28, лише читання)
Репо (GitHub API, repo.json): https://github.com/cheaper-inference/OmniRoute — MIT, створено 2026-02-13, pushed_at 2026-10-28, зірок 82064, форків 12093, open_issues 507 (разом з PR), релізи v3.8.52 (2026-10-19), v3.8.51 (09-30), v3.8.50 (08-26). Docker Hub у README: diegosouzapw/omniroute (автор початкового проєкту, ймовірно diegosouzapw — не перевірено).
Джерело нашого запису: issue #6846 "feat(providers): NVIDIA NIM adaptive client-side rate tracking" (i6846.json, closed, автор steveepreston, 2026-07-11) https://github.com/cheaper-inference/OmniRoute/issues/6846
## Що це
repo.json description: "Never stop coding. Free MIT AI gateway: one endpoint, 375 providers (150+ free), 1,400+ models" (grep -F у repo.json OK).
## Встановлення / Termux (README.md, TERMUX_GUIDE.md)
- "pkg install nodejs && npx -y omniroute" (README) — "Runs <b>on your phone</b>, 24/7, no root".
- "The Electron desktop app is not supported in Termux" (TERMUX_GUIDE); потрібен Node >=22.22.2 <23 || >=24; "Termux's `nodejs-lts` typically ships Node 20 LTS" — не підходить; потрібна збірка native-залежностей (better-sqlite3, build-essential, python).
- Фон: "nohup omniroute > omniroute.log 2>&1 &" — тобто потрібен постійно запущений сервер localhost:20128. Є "omniroute serve --headless" (лише /v1 проксі).
- README: "The project may generate a local <code>.env</code> file during npm install/postinstall" — postinstall-скрипти (npm 11 блокує, треба --allow-scripts для keytar, onnxruntime-node, esbuild тощо).
## API і ліміти
- "OpenAI-compatible — chat, embeddings, images, audio, OCR" (/v1/*), база http://localhost:20128/v1 — наш delegate сумісний за форматом.
- NVIDIA NIM у списку: "GLM, MiniMax<br/>~40 RPM free". BazaarLink у README не знайдено (grep: 0).
- 429: "429 honors Retry-After" (шар 2 — cooldown ключа/акаунта), шар 3 — блок однієї моделі, шар 1 — circuit breaker на 408/5xx; fallback по 4 рівнях Subscription→API Key→Cheap→Free.
## Свіжі issues (issues.json, 2026-10-28; більшість — PR)
- #18445 dashboard SSE streams leak timers/queues on half-open TCP peers https://github.com/cheaper-inference/OmniRoute/issues/18445
- #18444 no runtime liveness probe outside systemd — wedged-but-alive server (59-min wedge on v3.8.52) https://github.com/cheaper-inference/OmniRoute/issues/18444
- #18441 PR: gate the utilization and provider-stats routes with requireManagementAuth (була дірка в авторизації) https://github.com/cheaper-inference/OmniRoute/pull/18441
- #18443 PR: nvidia: drop retired free endpoints https://github.com/cheaper-inference/OmniRoute/pull/18443
- #18436 Generate video via gemini-omni not working https://github.com/cheaper-inference/OmniRoute/issues/18436
## Для нас
Дало б: один локальний endpoint із автоперемиканням між багатьма безкоштовними провайдерами при 429 (замість ручного provider-switch), клієнтський облік лімітів NVIDIA (#6846).
Ризики: у ньому лежать усі ключі провайдерів (README: "AES-256-GCM encrypted keys"); величезна кодова база, 507 відкритих, релізи щотижня, нещодавня правка авторизації; сервер-процес + Node 22+ + native-збірка на Android; послуги спонсорів/афіліат-посилання в README; частина "безкоштовних" — реселери, що ходять через чужі проксі ("TLS stealth").
## Не перевірено
Чи збереться на цьому телефоні (Node версія, better-sqlite3); реальні відгуки третіх сторін; безпекові advisories; якість безкоштовних моделей; чи справжній автор diegosouzapw vs org cheaper-inference; не читав PROVIDER_REFERENCE.md і лімітів Free-рівня окремо; не запускав.

Поправка claude-code (2026-10-28): цитату «Runs on your phone, 24/7, no root» grep -F у збережених README.md/TERMUX_GUIDE.md не знайшов (0); є README:766 «From a global npm install to **your phone** via Termux.» і README:775 `pkg install nodejs && npx -y omniroute`.
