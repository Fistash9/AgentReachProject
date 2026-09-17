#!/data/data/com.termux/files/usr/bin/bash
# Обгортка для memory MCP — встановлює MEMORY_FILE_PATH і запускає сервер
# (обходить баг Claude Code #22571: env-змінні не передаються в stdio)

export MEMORY_FILE_PATH="/data/data/com.termux/files/home/AgentReachProject/memory.jsonl"

exec /data/data/com.termux/files/usr/bin/node \
  /data/data/com.termux/files/usr/lib/node_modules/@modelcontextprotocol/server-memory/dist/index.js
