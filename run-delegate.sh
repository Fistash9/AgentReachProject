#!/data/data/com.termux/files/usr/bin/bash
# Обгортка для delegate MCP — запускає claude-code-deepseek-delegator
# в MCP-режимі (без аргументів). Обходить таймаут npx у Claude Code.

exec /data/data/com.termux/files/usr/bin/node \
  /data/data/com.termux/files/usr/lib/node_modules/claude-code-deepseek-delegator/src/index.mjs
