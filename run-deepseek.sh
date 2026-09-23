#!/data/data/com.termux/files/usr/bin/bash
# Обгортка для deepseek-mcp — читає ключ з agent.py, додає PATH для claude
# (обхід таймауту npx + мінімального PATH у Claude Code)

export DEEPSEEK_API_KEY=$(grep -oE 'sk-[a-zA-Z0-9]+' ~/AgentReachProject/agent.py | head -1)
export PATH="/data/data/com.termux/files/home/.local/bin:/data/data/com.termux/files/usr/bin:$PATH"
export TMPDIR="/data/data/com.termux/files/usr/tmp"
export CLAUDE_CODE_DISABLE_TERMINAL_TITLE=1
export CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT=1

exec /data/data/com.termux/files/usr/bin/node \
  /data/data/com.termux/files/usr/lib/node_modules/deepseek-mcp/dist/index.js
