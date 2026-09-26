#!/data/data/com.termux/files/usr/bin/bash
# Інтерактивний Claude Code на моделях DeepSeek (пункт 7 у menu.sh).
# Змінні — ті самі, що deepseek-mcp задає своїм під-сесіям
# (deepseek-mcp/dist/env.js); ключ читається з agent.py, як у run-deepseek.sh.

unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN ANTHROPIC_BASE_URL ANTHROPIC_MODEL \
      ANTHROPIC_DEFAULT_OPUS_MODEL ANTHROPIC_DEFAULT_SONNET_MODEL \
      ANTHROPIC_DEFAULT_HAIKU_MODEL CLAUDE_CODE_SUBAGENT_MODEL CLAUDE_CODE_EFFORT_LEVEL

export ANTHROPIC_AUTH_TOKEN=$(grep -oE 'sk-[a-zA-Z0-9]+' ~/AgentReachProject/agent.py | head -1)
if [ -z "$ANTHROPIC_AUTH_TOKEN" ]; then
    echo "claude-deepseek: не знайдено ключ DeepSeek в agent.py" >&2
    exit 1
fi
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_MODEL="deepseek-flash"
export ANTHROPIC_DEFAULT_OPUS_MODEL="deepseek-flash"
export ANTHROPIC_DEFAULT_SONNET_MODEL="deepseek-flash"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="deepseek-flash"
export CLAUDE_CODE_SUBAGENT_MODEL="deepseek-flash"
export CLAUDE_CODE_DISABLE_TERMINAL_TITLE=1
export CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT=1

cd ~/AgentReachProject && exec claude --permission-mode manual "$@"
