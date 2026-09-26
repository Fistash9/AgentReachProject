#!/usr/bin/env python3
"""Статуслайн: показує модель, вартість і заповнення контексту;
дописує зміни в .claude/logs/session-cost.jsonl (для кроку 3.9 session-close).

Вхід — JSON статуслайна Claude Code на stdin (поля cost.total_cost_usd,
context_window.used_percentage, session_id — див. code.claude.com/docs/en/statusline).
Рядок у журнал — лише коли змінилась вартість (до цента) або відсоток контексту
(до цілого) для цієї сесії. Будь-яка помилка — тихо, статуслайн не ламається.
"""
import json
import os
import sys
import time

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs", "session-cost.jsonl")


def last_for_session(sid):
    """Останній запис цієї сесії з хвоста журналу (до 16 КБ)."""
    try:
        with open(LOG, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - 16384))
            lines = f.read().decode("utf-8", "ignore").splitlines()
    except OSError:
        return None
    for line in reversed(lines):
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if rec.get("session_id") == sid:
            return rec
    return None


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        print("statusline: немає даних")
        return
    model = (data.get("model") or {}).get("display_name", "?")
    cost = float((data.get("cost") or {}).get("total_cost_usd") or 0)
    pct = (data.get("context_window") or {}).get("used_percentage")
    pct_i = int(pct) if pct is not None else None
    sid = data.get("session_id", "")

    ctx = f"{pct_i}% ctx" if pct_i is not None else "ctx ?"
    print(f"[{model}] ${cost:.2f} · {ctx}")

    try:
        prev = last_for_session(sid)
        if prev and round(prev.get("cost", -1), 2) == round(cost, 2) and prev.get("pct") == pct_i:
            return
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        rec = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "session_id": sid,
            "model": model,
            "cost": round(cost, 4),
            "pct": pct_i,
            "exceeds_200k": data.get("exceeds_200k_tokens"),
        }
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


if __name__ == "__main__":
    main()
