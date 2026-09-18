#!/data/data/com.termux/files/usr/bin/bash
# Запуск Telegram <-> DeepSeek оркестратора (MVP, див. ECOSYSTEM.md).
# Читає секрети з .env (не з agent.py — окремий файл, той самий gitignore).

set -a
source ~/AgentReachProject/.env
set +a

export PATH="/data/data/com.termux/files/home/.local/bin:/data/data/com.termux/files/usr/bin:$PATH"

exec python3 ~/AgentReachProject/telegram_deepseek_bot.py
