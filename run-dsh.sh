#!/data/data/com.termux/files/usr/bin/bash
# run-dsh.sh — запуск DSH (агент у proot) у терміналі. Створено [dsh, 2026-09-30].
# DSH_TUI_RETENTION_MAX_COUNT=0 вимикає janitor ретенції — єдиний незворотний
# механізм плагіна (rm -rf каталогів сесій без бекапу). Див. .baton/ledger.jsonl.
# exec + абсолютний шлях замість npx: мінус npm exec і sh -c (межа Android 32), і npx не піде в реєстр
# (рішення користувача 2026-10-22 «Обидва файли зараз»; DSH ще не підтвердив) [claude-code, 2026-10-22]
cd ~/AgentReachProject || exit 1
exec proot-distro login ubuntu -- bash -lc \
  'cd /root/dsh-app && DSH_TUI_RETENTION_MAX_COUNT=0 exec /root/dsh-app/node_modules/.bin/dsh --profile tui'
