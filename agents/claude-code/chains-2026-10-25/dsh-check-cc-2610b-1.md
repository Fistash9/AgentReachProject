# Звірка DSH 7 незвірених пунктів карти ланцюжків (лист cc-2610b-1, 2026-10-26)

Служить: Якість роботи агентів › Q4.3 Карта ланцюжків і обхід системи. Запит: рішення користувача «Так, платно: звірка карти». Відповідь DSH — дослівно з його журналу (сесія a93d4639, --root-dsh-app--).

cc-2610b-1 ВІДПОВІДЬ

| пункт | вердикт | команда | вивід |
|---|---|---|---|
| A4 | частково | `find ~ -maxdepth 6 -name 'hook-test.log' \| xargs wc -c; du -ch .claude/logs/L0-achieved-*.json \| tail -1; du -ch .claude/logs/review-*.txt \| tail -1; du -sh .claude/logs/deepseek-search` | 5612990 /data/data/com.termux/files/home/.claude/hook-test.log<br>1.9M total · 912K total · 21M .claude/logs/deepseek-search |
| A5 | частково | `for f in mcp_run.sh run-telegram-bot.sh run-dsh-isolated.sh test-hook.sh cost-report.py; do find . -name "$f" \| head -1; done; ls .claude/settings.local.json.bak* \| wc -l; ls /root/.dsh/AGENTS.md.bak* \| wc -l; ss -ltn \| grep -E '8799\|8788'` | mcp_run.sh, run-telegram-bot.sh, agents/claude-code/run-dsh-isolated.sh, /home/.claude/hooks/test-hook.sh, tools/cost-report.py; bak=29; AGENTS.bak=3; no 8799/8788 |
| Б2 | так | `find . -name 'trees-index*' -o -name 'parse.ts'; grep -c 'g2' .claude/hooks/tree-focus-hook.py; ls trees; grep -rl '◐' --include=*.ts --include=*.py` | tree-focus-hook.py g2count=0; trees-index.py, mods/agents-status/hooks/parse.ts; trees/…g2…; ◐ у parse.ts, parse.test.ts |
| Б4 | частково | `grep -rn '0\.80' tools/project-audit.py; grep -n 'threshold=0.5' tools/baton-diff.py; grep -n 'max(glob' tools/session-export.py` | project-audit.py:106 similar(...)>=0.80; baton-diff.py:65 def same(a,b,threshold=0.5); session-export.py:82 max(glob("*.jsonl"), key=os.path.getmtime) |
| Б5 | так | `wc -c RULES.md /root/.dsh/AGENTS.md; grep -c 'RULES' /root/.dsh/AGENTS.md; grep -c 'baton_pick_up' /root/.dsh/AGENTS.md` | 24566 RULES.md · 9875 /root/.dsh/AGENTS.md; 8; 2 |
| Б6 | так | `ls .claude/hooks/*ask-gate* *plain-ask* *commit-consent* *free-answer* *verify-nudge* *edit-gate*; ls .claude/logs` | 6/6 хуків; ask-gate.jsonl+plain-ask.jsonl; commit-consent.log+free-answer.log; edit-gate.log |
| В4 | частково | `wc -l .claude/logs/answer-gate-shadow.jsonl; grep -c 'no-transcript' …; grep -rl 'queued_command' .claude/hooks` | 490; 97; files=1 (лише commit-consent-hook.py) |

Нотатки: A4 — hook-test.log 5,61 МБ і review 912 КБ збігаються, але L0-achieved усього 1,9 МБ (не 1,45 МБ; 14 файлів, найбільший 242 КБ), deepseek-search 21 МБ (не 19 МБ). A5 — test-hook.sh існує (~/.claude/hooks), mcp_run.sh/run-telegram-bot.sh/run-dsh-isolated.sh/cost-report.py існують, .bak×3 підтверджено, портів 8799/8788 нема; але теки `exp/` і `profiles/web.backup` не знайдено (є лише ~/.dsh/profiles/web), settings.local.json.bak = 29 (числа в пункті нема).
Б4 — пороги 0.5/0.80 є, але в різних інструментах (baton-diff vs project-audit, не три порівняння знімків baton); session-export бере найновіший *.jsonl без фільтра моделі — «4 способи» не підтверджено. В4 — 97/490 = 19,8%, не 21%; «iter_turns не бачить queued_command» підтверджено: згадка лише в commit-consent-hook.py.
cc-2610b-1 КІНЕЦЬ

Два застереження від оркестратора: у Б2 команда й вивід не дають прямого доказу заявленого (вердикт «так» слабкий — варто перевірити повторно перед рішенням), а Б6 доводить лише існування хуків/логів, не їхню поведінку. Бюджет: 1 під-агент, ~8 кроків, ліміт не вичерпано.

## Звірка claude-code (2026-10-26, повтором команд з Termux)
- В4: 490 рядків, 97 no-transcript, queued_command лише в commit-consent-hook.py — збіглось.
- A4: L0-achieved 1.9M — збіглось; deepseek-search: agents/deepseek-search = 23K, а DSH пише 21 МБ — шлях не той самий [не з'ясовано].
- Б5: RULES.md 24 566 Б — збіглось. Б2: 'g2' у tree-focus-hook.py — 0, хук глобить trees/*.md, а trees/g2 — тека — збіглось.
— [claude-code, 2026-10-26]
