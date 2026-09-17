#!/data/data/com.termux/files/usr/bin/bash
# Обгортка для baton MCP — запускає встановлений сервер через node
# (обхід таймауту npx у Claude Code, як з memory і delegate)

export BATON_AGENT="claude-code"

exec /data/data/com.termux/files/usr/bin/node \
  /data/data/com.termux/files/usr/lib/node_modules/@timurabi3/baton-mcp/server.mjs
