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
# Проксі скорочує старе мислення (tools/deepseek-thinking-proxy.py): без нього
# контекст росте квадратично, бо кожен хід пересилає мислення всіх попередніх.
# Вимкнути для одного запуску: DEEPSEEK_NO_TRIM=1 claude-deepseek.sh
PROXY_PORT=$(python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1]);s.close()')
PROXY_ON=0
if [ -z "$DEEPSEEK_NO_TRIM" ]; then
    python3 ~/AgentReachProject/tools/deepseek-thinking-proxy.py \
        --port "$PROXY_PORT" --trim-thinking \
        --log ~/AgentReachProject/.claude/logs/deepseek-thinking-proxy.jsonl \
        >/dev/null 2>&1 &
    PROXY_PID=$!
    trap 'kill "$PROXY_PID" 2>/dev/null' EXIT
    trap 'exit 130' INT TERM
    for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
        if python3 -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:$PROXY_PORT/',timeout=1)" 2>/dev/null; then
            PROXY_ON=1
            break
        fi
        sleep 0.1
    done
fi
if [ "$PROXY_ON" = 1 ]; then
    # префікс /deepseek лишає адресу впізнаваною для хуків tree-focus і classify-task
    # (2026-09-29: tree-focus тут уже НЕ мовчить — глушить лише помічників; префікс
    #  потрібен для classify-task. TROUBLES «ПАСТКА ПРЕФІКСА», примітка)
    export ANTHROPIC_BASE_URL="http://127.0.0.1:$PROXY_PORT/deepseek"
else
    echo "claude-deepseek: проксі не піднявся — працюю напряму (контекст ростиме швидше)" >&2
    export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
fi
export ANTHROPIC_MODEL="deepseek-flash"
export ANTHROPIC_DEFAULT_OPUS_MODEL="deepseek-flash"
export ANTHROPIC_DEFAULT_SONNET_MODEL="deepseek-flash"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="deepseek-flash"
export CLAUDE_CODE_SUBAGENT_MODEL="deepseek-flash"
export CLAUDE_CODE_DISABLE_TERMINAL_TITLE=1
# Вікно DeepSeek V4 — 1M (рішення користувача 2026-10-01, baton-diff п.15/22).
# Раніше тут стояв DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT=1: попередження не
# прибирав, а автокомпакт вимикав (TROUBLES «Прапорець вікна…», env-vars.md:269).
export CLAUDE_CODE_MAX_CONTEXT_TOKENS=1000000
# Інструменти підвантажувати на вимогу (ToolSearch), а не всі наперед: на не-первинній
# адресі Claude Code вантажить їх усі (env-vars.md:141). Виміряно 2026-10-03: 54 → 12
# інструментів, схеми 86 702 → 26 869 симв.; виклик прихованого MCP через DeepSeek
# пройшов (HTTP 200). Рішення користувача 2026-10-03 (M3.1 п.17). Вимкнути — видалити рядок.
export ENABLE_TOOL_SEARCH=true

cd ~/AgentReachProject
# без exec: інакше trap не спрацює і проксі лишиться висіти після виходу
claude --permission-mode manual "$@"
