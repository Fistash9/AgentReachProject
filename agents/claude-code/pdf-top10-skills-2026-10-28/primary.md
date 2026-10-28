# Першоджерела з GitHub (2026-10-28)

## Репозиторії (дослівний вивід gh api)
```
{"full_name":"mattpocock/skills","license":"MIT","pushed_at":"2026-10-27T07:44:25Z","stargazers_count":305091}
{"full_name":"vercel-labs/skills","license":"MIT","pushed_at":"2026-10-28T04:18:52Z","stargazers_count":36909}
{"full_name":"vercel-labs/agent-browser","license":"Apache-2.0","pushed_at":"2026-10-28T03:33:29Z","stargazers_count":44735}
{"full_name":"anthropics/skills","license":null,"pushed_at":"2026-10-09T18:45:52Z","stargazers_count":184321}
```
| Репо | PDF | GitHub | Висновок |
|---|---|---|---|
| mattpocock/skills | 303,2 тис. | 305 091 | збіг (+0,6%) |
| vercel-labs/skills | 36,6 тис. | 36 909 | збіг (+0,8%) |
| vercel-labs/agent-browser | 44,6 тис. | 44 735 | збіг |
| anthropics/skills | 183,7 тис. | 184 321 | збіг; ліцензія в API = null |

## Де лежать скіли
mattpocock/skills (шляхи, потрібні нам): skills/productivity/{handoff,grilling}, skills/engineering/{grill-with-docs,domain-modeling,tdd,improve-codebase-architecture}. Усього SKILL.md у репо: 38 (engineering 20, in-progress 7, misc 4, productivity 7; пораховано awk).
vercel-labs/skills: skills/find-skills/SKILL.md (+ 2 службові в .automations/).

## Збережені скіли (sources/<назва>.SKILL.md, повністю)
| Скіл | Збережено | Рядків | Останній коміт файлу | Інші файли в теці (не качано) |
|---|---|---|---|---|
| handoff | так | 16 | 2026-10-06 | agents |
| grill-with-docs | так | 7 | 2026-08-15 | agents |
| grilling | так | 30 | 2026-10-07 | agents |
| domain-modeling | так | 74 | 2026-09-17 | ADR-FORMAT.md, GLOSSARY-FORMAT.md, agents |
| tdd | так | 38 | 2026-10-07 | mocking.md, tests.md, agents |
| improve-codebase-architecture | так | 71 | 2026-09-17 | HTML-REPORT.md, agents |
| find-skills | так | 141 | 2026-07-10 | — |
Разом 7 з 7. (grill-with-docs лише 7 рядків — можливо, перенаправлення на інші скіли; не перевірялося.)

## find-skills: що велить запускати (дослівно з SKILL.md)
- `npx skills find [query] [--owner <owner>]` (Step 3, пошук)
- `npx skills add <owner/repo@skill> -g -y` (Step 6, ВСТАНОВЛЕННЯ глобально без підтвердження; лише «if the user wants to proceed»)
- у тексті також: `npx skills update`, `npx skills init my-xyz-skill`; приклад для користувача `npx skills add vercel-labs/agent-skills@react-best-practices`.
- Також велить перевіряти https://skills.sh/ (лідерборд) перед пошуком. curl не використовується.
- Встановлює: так, через `npx skills add` (завантажує код з npm/GitHub), але лише після згоди користувача за текстом скіла.

## Наш .claude/skills/grilling vs mattpocock grilling
diff -u: 11 рядків (sources/grilling.diff). Єдина різниця: в оригіналі є додатковий рядок «Word each question so "yes" accepts your recommended answer.»; решта ідентична. Наш файл узято з mattpocock/skills (старіша версія до рядка), git: d9081e7.

## Відкриті issues (заголовки)
mattpocock/skills:
1338 codebase-design: design-it-twice sub-agents can build on conflicting facts, and the comparison doesn't check them
1337 grilling: one-question-at-a-time opt-out ignored in a real session (follow-up to #997)
1336 PR skill: before/after in a single line, hard to read on bitbucket
1332 Phrase for GLOSSARY-MAP.md missing in some skills
1331 pr skill: body can faithfully describe a scope the branch doesn't have (branch ancestry contamination)
1330 implement and code-review don't tick the list of acceptance criteria that to-tickets creates
1329 implement-spec: isolated implementer worktrees branch from the default branch and trip Claude Code's isolation checks
1328 implement-spec: make subagent lifecycles explicit per ticket
1327 grilling: original information is lost during long multi-round interviews
1325 writing-for-agents: Pruning tests lines, so a true row under a false heading is not a finding

vercel-labs/skills:
2609 [Bug]: Skills that are also Claude Code plugins lose plugin.json and hooks on install
2608 fix(install): print the restore plan with --dry-run instead of installing
2607 fix(update): keep copied skills as copies by recording installMode in the lock
2606 fix(add): report lock file write failures instead of ignoring them
2603 fix(install): skip skills that are already installed when restoring from the lock
2600 [skills.sh] Reindex namegarage/skills/catalog: stored snapshot still matches v1.0.0
2599 [skills.sh] Remove 3 listings for huntie/skills
2598 fix: upgrade tar to 7.5.21 (CVE-2026-73566)
2597 fix(list): honor agent filters in fallback directory scans
2596 fix: discover explicitly requested skills below a root skill

## Не вдалося / не перевірено
Нічого не впало. Не перевірено: вміст agents/-тек скілів; agent-browser не досліджувався глибше за метадані.
