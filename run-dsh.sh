#!/data/data/com.termux/files/usr/bin/bash
# run-dsh.sh — запуск DSH (агент у proot) у терміналі. Створено [dsh, 2026-09-30].
# DSH_TUI_RETENTION_MAX_COUNT=0 вимикає janitor ретенції — єдиний незворотний
# механізм плагіна (rm -rf каталогів сесій без бекапу). Див. .baton/ledger.jsonl.
cd ~/AgentReachProject || exit 1
exec proot-distro login ubuntu -- bash -lc \
  'cd /root/dsh-app && DSH_TUI_RETENTION_MAX_COUNT=0 npx dsh --profile tui'
