"""Сліпа вибірка: 12 перших спрацювань копії + 28 випадкових інших повідомлень, перемішано; вердикти — у key.json."""
import json, random, re, sys
sys.path.insert(0, "."); from scan import load, messages
o = load("../../../../tools/error-registry.py", "orig"); c = load("error-registry.py", "copy")
ms = messages(o)
new = [x for x in ms if c.is_correction(x[2]) and not o.is_correction(x[2])]
rest = [x for x in ms if not (c.is_correction(x[2]) and not o.is_correction(x[2]))]
print("повідомлень:", len(ms), "| нових спрацювань копії:", len(new),
      "| копія всього:", sum(c.is_correction(x[2]) for x in ms), "| оригінал всього:", sum(o.is_correction(x[2]) for x in ms))
random.seed(20261027)
pick = random.sample(new, min(12, len(new))) + random.sample(rest, 40 - min(12, len(new)))
random.shuffle(pick)
key = {}
with open("sample.txt", "w", encoding="utf-8") as f:
    for i, (sid, t, s) in enumerate(pick, 1):
        a = o.answer_part(s)
        key[i] = {"sid": sid, "t": t, "orig": o.is_correction(s), "copy": c.is_correction(s), "copy_class": c.classify(s)}
        f.write(f"S{i:02d} | {sid} {t} | {re.sub(chr(10)+'|\\s+', ' ', a)[:300]}\n")
json.dump(key, open("key.json", "w"), ensure_ascii=False, indent=1)
with open("new-triggers.txt", "w", encoding="utf-8") as f:
    for sid, t, s in new:
        f.write(f"{sid} {t} | {c.classify(s)} | {re.sub(r'\\s+', ' ', o.answer_part(s))[:200]}\n")
