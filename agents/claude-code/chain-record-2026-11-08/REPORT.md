# chain-record — звіт (2026-11-08, під-агент claude-code)

Служить: Перше довге відео › ланцюжок за курсом › «записав ланку» = «оновив каркас» однією дією.
Стан: скрипт і тести лише в пісочниці; живі файли не змінено (cmp: усі 4 живі = fixtures), нічого не ввімкнено, без git add/commit.

## Що зроблено
- fixtures/ — cp 4 живих файлів (CHAIN.md, PROMPT-v3.md, BACKLOG.md, GAPS.md). Усі 4 під git (git ls-files) → .bak не робиться.
- chain-record.py — `--link N --decision "…" [--passed] [--evidence "…"] [--dry-run]`, плюс `--check` (відставання каркаса), `--date` і `--root/--chain/--prompt/--backlog/--gaps` (шляхи параметрами).
  1. CHAIN: дописує `\nЛанка N (дд.мм, decision): evidence — [claude-code, РРРР-ММ-ДД]` (лише кінець файлу).
  2. Каркас: рядок `| N. ` у розділі «## Каркас: жорстке і змінне»; в «Доказ» дописує `; дд.мм: C:<№ нового рядка CHAIN>, evidence`; з --passed — `[не пройдено …]` / `[частково пройдено …]` → `[пройдено дд.мм]` лише в цьому рядку.
  3. BACKLOG: `  - Статус змінився (дд.мм): ланка N — decision` ПІСЛЯ наявних підпунктів рядка «ПЕРШИМ У НАСТУПНІЙ СЕСІЇ» (там уже є підпункт рядка 9).
  4. GAPS: лише друк відкритих `- [ ]`, де є «ланк* N» (5 ≠ 5б) або ≥2 слова (≥6 літер) з decision.
  5. Атомарність: усі 4 файли читаються й нові тексти будуються в пам'яті; помилка (ланки нема, нема якоря) → код 2, нічого не записано; запис — tmp+os.replace.
- `--check` на fixtures знайшов справжнє відставання: `ВІДСТАЄ: CHAIN:40 ланка 5 — C:40 нема в «Доказ» рядка 5` (запис «Ланка 5, вибір сценарію» не процитовано в каркасі), код 1.

## Тести — новий стан (python3 -m unittest -v test_chain_record), дослівно
```
test_check_mode_exit_code (test_chain_record.ChainRecordTest.test_check_mode_exit_code) ... ok
test_dry_run_writes_nothing (test_chain_record.ChainRecordTest.test_dry_run_writes_nothing) ... ok
test_gaps_matching (test_chain_record.ChainRecordTest.test_gaps_matching) ... ok
test_lag_check_red_on_manual_append_green_via_script (test_chain_record.ChainRecordTest.test_lag_check_red_on_manual_append_green_via_script) ... ok
test_link5_chain_and_backlog_plus_one (test_chain_record.ChainRecordTest.test_link5_chain_and_backlog_plus_one) ... ok
test_link5_passed_changes_only_its_row (test_chain_record.ChainRecordTest.test_link5_passed_changes_only_its_row) ... ok
test_old_state_row_still_unverified (test_chain_record.ChainRecordTest.test_old_state_row_still_unverified)
Старий стан: ланку 5б пройшли б, але рядок каркаса досі «не перевірено». ... ok
test_passed_replaces_mark_only_in_row (test_chain_record.ChainRecordTest.test_passed_replaces_mark_only_in_row) ... ok
test_passed_without_evidence_rejected (test_chain_record.ChainRecordTest.test_passed_without_evidence_rejected) ... ok
test_unknown_link_fails_and_writes_nothing (test_chain_record.ChainRecordTest.test_unknown_link_fails_and_writes_nothing) ... ok

----------------------------------------------------------------------
Ran 10 tests in 0.107s

OK
```

## Тести — старий стан (заглушка: та сама логіка, але агент дописує лише CHAIN, каркас і BACKLOG не чіпає; тека /data/data/com.termux/files/usr/tmp/cr-old-0811-chsy), дослівно grep
```
FAIL: test_lag_check_red_on_manual_append_green_via_script (test_chain_record.ChainRecordTest.test_lag_check_red_on_manual_append_green_via_script)
FAIL: test_link5_chain_and_backlog_plus_one (test_chain_record.ChainRecordTest.test_link5_chain_and_backlog_plus_one)
FAIL: test_link5_passed_changes_only_its_row (test_chain_record.ChainRecordTest.test_link5_passed_changes_only_its_row)
FAIL: test_passed_replaces_mark_only_in_row (test_chain_record.ChainRecordTest.test_passed_replaces_mark_only_in_row)
Ran 10 tests in 0.094s
FAILED (failures=4)
```
Червоні 4: відставання не впіймано/лишилось, каркас не змінився, BACKLOG без підпункту. Тест `test_old_state_row_still_unverified` фіксує, що на старому стані рядок 5б досі має «не перевірено]»; `test_lag_check_red_on_manual_append_green_via_script` — ручний запис у CHAIN дає нове відставання {48}, запис скриптом — ні.

## Приклад --dry-run на копіях (ланка 7, --passed), вивід обрізано до 220 симв./рядок
```
--- fixtures/CHAIN.md
+++ fixtures/CHAIN.md (нове)
@@ -46,0 +47,2 @@
+
+Ланка 7 (08.11, голос af_bella на повному тексті): ~/video-work/golos/KEY.md:1 — [claude-code, 2026-11-08]
--- fixtures/PROMPT-v3.md
+++ fixtures/PROMPT-v3.md (нове)
@@ -181 +181 @@
-| 7. Озвучка | Kokoro локально на телефоні (~/sandboxes/kokoro; моделі звірені sha256 з digest GitHub API; GitHub release давав 504 → дзеркало зі звіркою sha); браузерна WebGPU-версія не працює. Параметра емоції нема — 
+| 7. Озвучка | Kokoro локально на телефоні (~/sandboxes/kokoro; моделі звірені sha256 з digest GitHub API; GitHub release давав 504 → дзеркало зі звіркою sha); браузерна WebGPU-версія не працює. Параметра емоції нема — 
--- fixtures/BACKLOG.md
+++ fixtures/BACKLOG.md (нове)
@@ -9,0 +10 @@
+  - Статус змінився (08.11): ланка 7 — голос af_bella на повному тексті
```
Зміни в рядку 7: `[частково пройдено: абзаци й одна сцена]` → `[пройдено 08.11]`; Доказ `| C:13, C:32–38, P:33–35, P:52–53 |` → `| C:13, C:32–38, P:33–35, P:52–53; 08.11: C:48, ~/video-work/golos/KEY.md:1 |`. Після dry-run md5 усіх 4 fixtures — OK.

## Відомі межі й відхилення від брифу
- Позначка «пройдено» записується як `[пройдено дд.мм]` (замінює всю дужку); дата в тексті — дд.мм (як у наявних записах CHAIN/BACKLOG), у тезі — ISO.
- `--passed` без `--evidence` — відмова (argparse, код 2): «пройдено» без доказу не пишу. Без --passed доказ необов'язковий («доказ не вказано», у «Доказ» — лише C:№).
- Атомарність між 4 файлами — лише «перевір усе, потім пиши»; збій ОС посеред трьох os.replace може лишити частину записаною (git покаже).
- `--check` рахує лише цитати `C:n` / `C:a–b`; запис CHAIN, процитований інакше, вважається відставанням. Рядки CHAIN, що не починаються з «Ланка N», не перевіряються.
- GAPS-збіг за ключовими словами грубий (≥2 слова ≥6 літер) — лише нагадування.
- Якір BACKLOG — перший рядок із «ПЕРШИМ У НАСТУПНІЙ СЕСІЇ»; коли його перейменують, скрипт дасть код 2 (не запише навмання).
- На момент копіювання git status показував M також у BACKLOG.md, GAPS.md, trees/kurs-media-bazar.md (на старті сесії їх не було) — це не мої зміни: я в живі файли не писав; fixtures = їхній поточний стан.
- Не ввімкнено: живий шлях tools/chain-record.py не створено; перенесення — рішенням користувача.
