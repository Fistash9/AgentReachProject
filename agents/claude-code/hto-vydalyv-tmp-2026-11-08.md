# Хто і коли видалив kokoro-sandbox і minute1-0711 — [claude-code, під-агент, 2026-11-08]

## Висновок
Команди видалення в журналах НЕ знайдено (0). Звужено ВІКНО: обидві теки (і vbs-0711) ще були
на місці 08.11 ~10:26 (київський; vbs-0711 успішно прочитано в c5d4f555, рядок 1229-1230,
08:26Z) і зникли до 08.11 ~11:16 (09:16Z, c5d4f555, субагент a331151182781c313: `ls minute1* kokoro-sandbox` -> "No such file").
Тобто видалення — між 10:26 і 11:16 за Києвом 08.11, не вночі 07->08.11.

## Збіг за часом (непряма ознака, не доказ)
- Сесію c5d4f555 перервано: рядок 1484, `model: <synthetic>`, ts 08:52:28Z; прогалина 08:48:58Z -> 08:52:28Z.
- tmux-сесія `work`, `bash -l` і claude-процес живуть 1950-1954 с на момент перевірки 11:21:58 -> старт ~10:49:20 (за Києвом).
- У usr/tmp файли tmp4wxghnog і tmpcdzwidd0 створені 10:49 (старт нового терміналу).
- TROUBLES.md:3051 (2026-09-27/28): "$PREFIX/tmp Termux очищає при перезапуску терміналу: тека dsh-check у ньому зникла двічі" — прецедент.
- Проти повного «очищено все»: уціліли теки, старші за 10:49 (kurs-media-bazar 07.11 20:31, close-0711, hfgen-sandbox 07.11 13:33,
  hooks-smoke-* 30.10, vbs-centre 03.11 тощо). Правило вибірковості невідоме [unverified]; джерело Termux не читав.

## Перевірено — результат
1. Журнали сесій з 07.11 (70 файлів .jsonl, з підтеками/subagents): grep назв -> 3 сесії (cc6d15d4, 27c0c551, c5d4f555) + їхні субагенти.
   Усі tool_use Bash з rm/rmdir/rmtree/-delete/shutil/rimraf поруч з tmp/kokoro/minute1/sandbox: 0 стосуються цих тек.
   Єдині rm у вікні: `rm $P/hxhoEfhcC7Q.mp4 $P/wFbhqyr98Do.mp4` (konkurenty-0711/ochi-proba, 08:56:55Z), `rm -rf dl` (konkurenty-0711/chain/blind, 09:13Z, відносний шлях),
   `rm -f $F` (prompt-v3/flat.txt, 07.11 18:07Z), `rm -rf $R/.claude/hooks/__pycache__` (agents-gate-fix-0711/root-*, 06.11 23:31Z). mv: лише у .trash/baton-history* та `.env.bak-0711`.
2. Без фільтра за tmp: усі rm/mv/-delete/.trash у tool_use з 07.11 — те саме, нічого по цих теках.
3. Записи проєкту: TROUBLES.md:6983,6998; BACKLOG.md:9,12,33 лише описують; TRASH.md, CONTEXT.md, HANDOFF.md, GAPS.md — 0 збігів із видаленням.
   close-0711/ (report.txt) — лише цитати BACKLOG; кроку «прибрати tmp» / ~/.cache/pip нема.
4. DSH: agents/dsh/JOURNAL.md (остання зміна 31.10), agents/ grep назв — 0. ~/.dsh містить лише profiles/. Сесій DSH після 07.11 не було.
5. Хуки/скрипти: SessionStart-хуки (settings.local.json) — `unset -f ...` і tree-focus-hook.py (без rm); SessionEnd немає; Stop-хуки без видалень.
   grep rm/rmtree/unlink у .claude/hooks і tools: лише edit-gate, git-add-status, install-check, trash-md-guard (перевіряють, не видаляють), check-links, hooks-smoke, provider-switch, test_turn_state — не торкаються usr/tmp цих тек.
   crontab: немає команди; ~/.termux/boot: немає; termux-job-scheduler -p: лише власний опитувач.
6. find у ~ (depth 4) і ~/.trash, AgentReachProject/.trash: kokoro-sandbox / minute1-0711 не знайдено (ні переміщено, ні в .trash).
   Інша «зникла» тека minimax-conveyor-0711 НЕ втрачена: скопійовано в ~/minimax-conveyor-0711 (є src, TEST-REPORT.md).
7. Останні докази існування: minute1-0711 — `ls` субагентом ae44c9797be9c907b 07.11 17:43Z (виведено build.sh, gen.py, scenes.json, minute1_v2.mp4...);
   kokoro-sandbox — використано в build.sh 07.11 12:50Z.
8. Масштаб: аудит координатора — 52 з 63 тек зниклі; в usr/tmp вціліло лише частину тек 07.11 (hfgen-sandbox, review-0711, notoken-tools-0711,
   kurs-media-bazar, close-0711, image-pick-0711, autoresume-0711...), зникли kokoro-sandbox, minute1-0711, prompt-v3, agents-gate-fix-0711, minimax-review-0711, vbs-0711, vbs-haiku-*, imagegen-*.

## Що не перевірено
- Ручні команди користувача в Termux (поза журналами Claude), код Termux-застосунку (чи чистить TMPDIR; за яким правилом вибірково) — [не перевірено].
- Для перевірки гіпотези «перезапуск Termux ~10:49»: зафіксувати ознаки (Termux-сесії вручну), а не гадати.
