# FOUND: готові рішення "стан, обчислений кодом" (2026-10-30)
Джерела: code.claude.com/docs (hooks, statusline, permissions, checkpointing, interactive-mode, mods), GitHub API (зірки/дата/ліцензія).
Топ: sirmalloc/ccstatusline (13467*, MIT, push 2026-10-29); NYCU-Chung/cc-statusline (265*, MIT, 2026-05-22); MMSs/claude-task-progress (0*, MIT, 2026-10-26); jackywooks/task-tracker (0*, MIT, 2026-10-27); KilimcininKorOglu/claude-code-mods subagent-ledger (12*, MIT, 2026-10-04); DerekTM17/claude-ledger (0*, без ліцензії, 2026-10-30); disler/claude-code-hooks-multi-agent-observability (1563*, 2026-02-08).
Вбудоване: Stop/SubagentStop хуки (last_assistant_message, agent_transcript_path, systemMessage, decision:block), statusline (stdin JSON, refreshInterval), Ctrl+T task list, /rewind (Bash-зміни не відстежує), managed settings (allowManagedHooksOnly, deny-правила).
Termux-сумісність усього: [не перевірено] (нічого не запускали).
Захист: першоджерела не знайшли готового "антипідробного" механізму для хуків; є лише permissions deny Edit/Write на шляхи + managed settings (Linux/Android managed path - не перевірено).
