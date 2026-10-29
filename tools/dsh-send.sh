#!/data/data/com.termux/files/usr/bin/bash
# dsh-send.sh — лист у вікно DSH з перевіркою поля і доставки (пісочниця кроку 1.2,
# agents/claude-code/dispatcher-circle-2026-10-29/PLAN-COMBINED.md; НЕ ввімкнено).
# Замінює ручний рецепт TROUBLES.md «Листи у вікно DSH — доповнення…» (2026-10-03)
# і «Лист DSH: Enter пішов, хоча перевірка поля вводу дала 0» (2026-10-29).
#
# Використання: dsh-send.sh <файл листа> [--target <tmux-ціль>] [--no-journal]
#   ціль за замовчуванням — вікно сесії work, назва якого починається на «dsh».
#        dsh-send.sh --check-delivery <id>   (лише читання журналу DSH)
#   DSH_SEND_CAPTURE_FILE=<файл> — «екран» читається з файлу (для тестів).
# Коди: 0 — відправлено (і доставку підтверджено, якщо без --no-journal);
#       1 — помилка аргументів/цілі; 2 — лист не в полі, Enter НЕ надіслано;
#       3 — Enter надіслано, але доставку в журналі DSH не підтверджено.
set -u

usage() { echo "Використання: $0 <файл листа> [--target <tmux-ціль>] [--no-journal] | --check-delivery <id>" >&2; exit 1; }

FILE="" TARGET="" JOURNAL=1 CHECK_ID=""
while [ $# -gt 0 ]; do
  case "$1" in
    --target) [ $# -ge 2 ] || usage; TARGET="$2"; shift 2 ;;
    --no-journal) JOURNAL=0; shift ;;
    --check-delivery) [ $# -ge 2 ] || usage; CHECK_ID="$2"; shift 2 ;;
    -h|--help) usage ;;
    -*) echo "Невідомий ключ: $1" >&2; usage ;;
    *) [ -z "$FILE" ] || usage; FILE="$1"; shift ;;
  esac
done
SESS="${PREFIX:-/data/data/com.termux/files/usr}/var/lib/proot-distro/containers/ubuntu/rootfs/root/.dsh/sessions"
delivered() {  # $1 — id; друкує кількість збігів у найновішому журналі DSH
  local newest real
  newest=$(ls -t "$SESS"/*/*/session.v4.jsonl.zstd 2>/dev/null | head -1)
  [ -n "$newest" ] || { echo 0; return; }
  real=$(readlink -f "$newest")   # ярлик l2s: zstd ярлики пропускає (TROUBLES:5533)
  zstd -dc "$real" 2>/dev/null | grep -c -F -- "$1"
}
# Лише читання журналу DSH, нічого не шле: dsh-send.sh --check-delivery <id>
[ -n "$CHECK_ID" ] && { delivered "$CHECK_ID"; exit 0; }

[ -n "$FILE" ] && [ -f "$FILE" ] || { echo "Нема файлу листа: ${FILE:-<не задано>}" >&2; exit 1; }

if [ -z "$TARGET" ]; then
  IDX=$(tmux list-windows -t work -F '#{window_index} #{window_name}' 2>/dev/null \
        | awk '$2 ~ /^dsh/ {print $1; exit}')
  [ -n "$IDX" ] || { echo "Не знайшов вікна з назвою dsh* у сесії work" >&2; exit 1; }
  TARGET="work:$IDX"
fi

screen() {
  if [ -n "${DSH_SEND_CAPTURE_FILE:-}" ]; then cat "$DSH_SEND_CAPTURE_FILE"
  else tmux capture-pane -p -t "$TARGET"; fi
}

# Режим DSH: лише попередження (блок відкладено — BACKLOG «Режим DSH»).
MODE=$(screen | grep -F "📁" | tail -1)
echo "ціль $TARGET; рядок 📁: ${MODE:-<нема>}" >&2
case "$MODE" in
  *"(Full access)"*) ;;
  *) echo "ПОПЕРЕДЖЕННЯ: у рядку 📁 нема «(Full access)» — DSH може не мати доступу (лист усе одно шлю)" >&2 ;;
esac

ID=$(head -c 200 "$FILE" | awk 'NR==1{print $1; exit}' | sed 's/\.$//')
[ -n "$ID" ] || { echo "Порожній лист — нема ідентифікатора" >&2; exit 1; }
# Переноси → пробіли (рецепт TROUBLES 2026-10-03: `tr '\n' ' '`) — інакше перенос у полі = Enter.
TEXT=$(tr '\n' ' ' < "$FILE" | sed 's/[[:space:]]*$//')
# Кінець листа — останні ~20 символів (кінець видно в полі, початок може прокрутитись).
TAIL=$TEXT
TAIL=${TAIL: -20}
echo "id: $ID; хвіст для перевірки: «$TAIL»" >&2

tmux send-keys -t "$TARGET" -l "$TEXT" || { echo "send-keys не вдалося" >&2; exit 1; }

FOUND=0
for _ in 1 2 3; do
  sleep 1
  if screen | grep -q -F -- "$TAIL"; then FOUND=1; break; fi
done
if [ "$FOUND" != 1 ]; then
  echo "НЕ В ПОЛІ — не відправляю (хвіст «$TAIL» не знайдено за 3 спроби; текст лишився в полі — Ctrl+K)" >&2
  exit 2
fi
tmux send-keys -t "$TARGET" Enter
echo "Enter надіслано ($ID)" >&2

[ "$JOURNAL" = 1 ] || exit 0

for _ in $(seq 1 15); do
  sleep 1
  N=$(delivered "$ID")
  if [ "${N:-0}" -ge 1 ]; then echo "доставлено: $N" >&2; exit 0; fi
done
echo "доставку не підтверджено: id $ID не знайдено в найновішому журналі DSH за 15 с" >&2
exit 3
