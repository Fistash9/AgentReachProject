# COMPARE: три пошуки «статус зі стану» (2026-10-30)
Усі числа з виводу curl/grep цієї сесії (work/*.live, work/gh_res.txt).

| пошук | кандидатів | живих посилань (2xx) | дослівних цитат з 3 | унікальне | ціна |
|---|---|---|---|---|---|
| П (FOUND) | 7 GitHub-репо + 6 сторінок доків | 5 з 6 сторінок (mods=404); репо 7 з 7 | 0 цитат (їх нема); 3 ключові слова з 4 знайдено на заявлених сторінках | subagent-ledger, claude-ledger, task-tracker | токени під-агента, ціни у файлі нема |
| Д1 | 42 різних URL; 12 GH-репо (11 живі; erk — на PyPI, не dagster-io/erk-statusline) | 33 з 42 (404: 1; 402/403/521 = блок ботів, не перевірено) | 3 з 3 | claude-hooks-sdk, рецепт singhlabs, Dev-GOM | ≈$0.0269 |
| Д2 | 38 різних URL; 8 GH-репо (8 з 8) | 30 з 38 (404: 6 — усі mintlify.wiki; 403/429 блок) | 3 з 3 (одна — з розмітки; ще одна, 4-та, перевірена — переказ) | cc-audit, managed settings, sandbox+deny, ConfigChange | ≈$0.0323 |

## Цитати
- Д1: hooks docs «Run the build before stopping», «StopFailure hooks have no decision control» — дослівна; singhlabs «A better one: hold the summary against the diff» — дослівна; Dev-GOM «Scans and reports TODOs when session ends» — дослівна.
- Д2: permission-modes «permissions.allow rules in settings files do not pre-approve protected-path writes» — дослівна; classmethod «I could write directly via Bash» — дослівна; cc-audit PyPI «Self-protection… cc-audit uninstall» — дослівна (у першоджерелі з markdown-бектиками, у JSON PyPI API). Додатково: «never lets a permissions.allow rule…» — не знайдено дослівно, у доках інше формулювання («No PreToolUse hook that returns "allow" approves one either») = переказ; рядок «Protected path checks are also skipped» на permission-modes не знайдено (Д2 приписала sandboxing-сторінці — не перевірено окремо).
- П: цитат нема; `last_assistant_message`, `agent_transcript_path`, `refreshInterval` знайдено в доках; `allowManagedHooksOnly` на /permissions — не знайдено (є на /hooks і /settings-reference).

## Репо (stars / pushed / ліцензія)
sirmalloc/ccstatusline 13467 / 2026-10-29 / MIT; Haleclipse/CCometixLine 3512 / 10-24 / нема; pchalasani/claude-code-tools 2024 / 10-29 / MIT; him0/claude-code-statusline 3; NYCU-Chung/cc-statusline 265 / 05-22 / MIT; MMSs/claude-task-progress 0 / MIT; jackywooks/task-tracker 0 / MIT; KilimcininKorOglu/claude-code-mods 12 / MIT; DerekTM17/claude-ledger 0 / без ліцензії; mcorbett51090/RavenClaude 9 / 10-28; Dev-GOM 97 / 01-17 / Apache-2.0; ericbuess/claude-code-docs 996. Д1 у тексті дала ccstatusline 1471…11984; реальне 13467 (Д1 сама попередила, що агрегатори ненадійні).

## Збіг
Усі три: повного готового «one-stop» нема. П: статуслайни + хуки; захисту від підробки готового нема. Д1: зібрати власний Stop-хук (рецепт singhlabs + claude-hooks-sdk) + мінімальний статуслайн. Д2: managed settings + sandbox + deny + хук поза репо; cc-audit як журнал.

## Не перевірено
Termux-сумісність усього; позиція ключів allowManaged*; Codex/Gemini (Д2 не шукала); npm-сторінки (403).
