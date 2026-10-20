#!/data/data/com.termux/files/usr/bin/bash
# Read-only fact-gathering for the session-close skill. Never modifies the repo.
# Usage: session-report.sh [<since-iso-timestamp>]
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

SINCE_TS="${1:-}"

# Підсумок першим рядком (2026-10-20): 20.10 вивід обрізали `| head -60`, розділ комітів стояв на 60-му рядку —
# заголовок лишився, список ні, і в TROUBLES пішло хибне «скрипт не бачить коміт». Головне — на початку.
echo "=== ПІДСУМОК ==="
SUM_BASE=""
if [ -n "$SINCE_TS" ]; then
  SUM_BASE="$(git log --before="$SINCE_TS" -1 --format=%H -- . || true)"
fi
if [ -n "$SUM_BASE" ]; then
  echo "Комітів після старту ($SINCE_TS): $(git rev-list --count "$SUM_BASE"..HEAD); незакомічених файлів: $(git status --short | wc -l). Список комітів — у кінці; обрізаний вивід ≠ «немає»."
else
  echo "Комітів після старту: невідомо (точку відліку не задано або не знайдено); незакомічених файлів: $(git status --short | wc -l)."
fi
echo

echo "=== GIT STATUS ==="
STATUS="$(git status --short)"
if [ -z "$STATUS" ]; then
  echo "(чисто, немає незакомічених змін)"
else
  echo "$STATUS"
fi

echo
echo "=== BACKLOG.md: зміни ==="
BASE_COMMIT=""
FALLBACK=0
if [ -n "$SINCE_TS" ]; then
  BASE_COMMIT="$(git log --before="$SINCE_TS" -1 --format=%H -- . || true)"
fi
if [ -z "$BASE_COMMIT" ]; then
  BASE_COMMIT="$(git rev-list --max-parents=0 HEAD | tail -1)"
  FALLBACK=1
  echo "(увага: точку відліку baton не знайдено, порівнюю з першим комітом репо)"
fi
BACKLOG_DIFF="$(git diff "$BASE_COMMIT" -- BACKLOG.md)"
if [ -z "$BACKLOG_DIFF" ]; then
  echo "(без змін у BACKLOG.md)"
else
  echo "$BACKLOG_DIFF"
fi

echo
echo "=== CONTEXT.md: свіжість ==="
CTX_COMMIT="$(git log -1 --format=%H -- CONTEXT.md)"
if [ -z "$CTX_COMMIT" ]; then
  echo "CONTEXT.md ніколи не комітився — рекомендовано створити запис."
else
  CTX_DATE="$(git log -1 --format=%cd --date=short -- CONTEXT.md)"
  CTX_SUBJ="$(git log -1 --format=%s -- CONTEXT.md)"
  echo "Останній запис: $CTX_DATE — \"$CTX_SUBJ\" ($CTX_COMMIT)"
  COMMITS_SINCE="$(git rev-list --count "$CTX_COMMIT"..HEAD)"
  echo "Комітів після цього: $COMMITS_SINCE"

  ARCH_FILES="$(git log "$CTX_COMMIT"..HEAD --name-only --format="" -- run-*.sh mcp_run.sh my_mcp_server.py 2>/dev/null | sort -u)"
  if [ -n "$ARCH_FILES" ]; then
    echo "Архітектурні файли, змінені відтоді:"
    echo "$ARCH_FILES" | sed 's/^/  - /'
  fi

  ARCH_COMMITS="$(git log "$CTX_COMMIT"..HEAD --format="%s" | grep -iE "mcp|hook" || true)"
  if [ -n "$ARCH_COMMITS" ]; then
    echo "Коміти з MCP/hook у повідомленні:"
    echo "$ARCH_COMMITS" | sed 's/^/  - /'
  fi
fi

echo
echo "=== КОМІТИ З ОСТАННЬОГО BATON PICK-UP ==="
if [ -n "$BASE_COMMIT" ]; then
  if [ "$FALLBACK" -eq 1 ]; then
    echo "(увага: фолбек — це НЕ коміти сесії, а історія від першого коміту; показано останні 20)"
    LOG="$(git log "$BASE_COMMIT"..HEAD -n 20 --format='- %s')"
  else
    LOG="$(git log "$BASE_COMMIT"..HEAD --format='- %s')"
  fi
  if [ -z "$LOG" ]; then
    echo "(нових комітів немає)"
  else
    echo "$LOG"
  fi
fi
