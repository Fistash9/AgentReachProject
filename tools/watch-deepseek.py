#!/usr/bin/env python3
"""Живе стеження за кроками під-сесій deepseek.

Запуск в окремій вкладці Termux ДО виклику deepseek:
    python3 ~/AgentReachProject/tools/watch-deepseek.py

Стежить за новими журналами сесій у ~/.claude/projects/<проєкт>/ і показує
лише ті, де модель deepseek (сесії хука delegate-prompt-improver на Haiku
пропускає). Працює безперервно — ловить усі наступні виклики, Ctrl+C для виходу.
"""
import glob
import json
import os
import sys
import time

DIR = os.environ.get("WATCH_DIR") or os.path.expanduser(
    "~/.claude/projects/-data-data-com-termux-files-home-AgentReachProject")
MARK = '"model":"deepseek'


def show(line):
    try:
        d = json.loads(line)
    except ValueError:
        return
    m = d.get("message")
    if not isinstance(m, dict) or not isinstance(m.get("content"), list):
        return
    ts = d.get("timestamp", "")[11:19]
    for x in m["content"]:
        t = x.get("type")
        if t == "tool_use":
            inp = json.dumps(x.get("input"), ensure_ascii=False)[:100]
            print(ts, "🔧", x.get("name"), inp, flush=True)
        elif t == "text" and d.get("type") == "assistant":
            print(ts, "💬", x.get("text", "")[:150].replace("\n", " "), flush=True)


def main():
    old = set(glob.glob(os.path.join(DIR, "*.jsonl")))
    pending = set()   # нові файли, модель ще не відома
    followed = {}     # deepseek-файл -> прочитаний зсув
    print("чекаю виклик deepseek... (Ctrl+C — вихід)", flush=True)
    while True:
        for f in set(glob.glob(os.path.join(DIR, "*.jsonl"))) - old:
            old.add(f)
            pending.add(f)
        for f in list(pending):
            try:
                with open(f, encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
            except OSError:
                pending.discard(f)
                continue
            if MARK in text:
                pending.discard(f)
                followed[f] = 0
                print("\n== deepseek-сесія", os.path.basename(f)[:8], flush=True)
            elif '"model":"claude' in text:
                pending.discard(f)  # не deepseek (напр. Haiku-хук)
        for f, pos in followed.items():
            try:
                with open(f, encoding="utf-8", errors="replace") as fh:
                    fh.seek(pos)
                    chunk = fh.read()
            except OSError:
                continue
            complete = chunk[:chunk.rfind("\n") + 1]
            for line in complete.splitlines():
                show(line)
            followed[f] = pos + len(complete.encode("utf-8"))
        time.sleep(0.5)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
