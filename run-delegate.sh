#!/data/data/com.termux/files/usr/bin/bash
# Обгортка для delegate MCP — читає ключ з agent.py динамічно
# (обходить баг Claude Code #22571: env не передаються в stdio)

export DEEPSEEK_API_KEY=$(grep -oE 'sk-[a-zA-Z0-9]+' ~/AgentReachProject/agent.py | head -1)
# NVIDIA (build.nvidia.com, безкоштовно) — провайдер "nvidia" з ~/.claude/delegator-providers.json;
# перемикач: tools/provider-switch.py (2026-09-25). Ключ лежить у .env (у .gitignore).
export NVIDIA_API_KEY=$(grep -oE '^NVIDIA_API_KEY=nvapi-[A-Za-z0-9_-]+' ~/AgentReachProject/.env 2>/dev/null | cut -d= -f2)

exec /data/data/com.termux/files/usr/bin/node \
  /data/data/com.termux/files/usr/lib/node_modules/claude-code-deepseek-delegator/src/index.mjs
