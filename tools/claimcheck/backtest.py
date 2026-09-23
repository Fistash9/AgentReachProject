#!/usr/bin/env python3
"""Тест на історії: прогін decide() по всіх відповідях сесії."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from claimcheck import parse_turns, decide

path, labels = sys.argv[1], set(int(x) for x in sys.argv[2].split(",") if x)
turns = parse_turns(path)
flagged, hit = 0, set()
users = []
for i, t in enumerate(turns, 1):
    users.append(t["user"])
    fl = decide(t["final"], t["tools"], t["evidence"], users, t["model"])
    if fl:
        flagged += 1
        mark = "ПОМИЛКА(розмічена)" if i in labels else "без розмітки"
        if i in labels:
            hit.add(i)
        print(f"#{i} {t['ts'][11:16]} [{mark}] {fl[:6]}")
print(f"\nвідповідей: {len(turns)}, з позначками: {flagged}, розмічених помилок: {len(labels)}, "
      f"впіймано: {sorted(hit)}, пропущено: {sorted(labels - hit)}")
