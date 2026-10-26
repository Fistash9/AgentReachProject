import importlib.util, json, re, sys
D = "/data/data/com.termux/files/usr/tmp/q12-ad-2610"; B = "/data/data/com.termux/files/usr/tmp/q12-blind-2610"
def load(n, p):
    s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
o = load("o", "/data/data/com.termux/files/home/AgentReachProject/tools/error-registry.py")
c = load("c", D + "/error-registry.py")
k = json.load(open(B + "/key.json"))
lab = {l.split()[0]: l.split()[1] for l in open(B + "/labels.txt") if l.strip()}
print("== (1) сліпа розмітка")
print("Bxx | було (class_now) | стало | DeepSeek | збіг")
okn = okc = 0; sane = 0
for b in sorted(k):
    t = k[b]["text"]; was = o.classify(t) or "без класу"; now = c.classify(t) or "без класу"
    sane += was == k[b]["class_now"]
    okn += now == lab[b]; okc += (k[b]["class_now"]) == lab[b]
    print(f"{b} | {k[b]['class_now']} | {now} | {lab[b]} | {'так' if now == lab[b] else 'НІ'}")
print(f"збіг з DeepSeek: було {okc} з {len(k)}, стало {okn} з {len(k)}; оригінал classify == class_now: {sane} з {len(k)}")
print("== (2) усі поправки з журналів")
sess = o.all_sessions(); n = ch = 0; ch9 = 0; lst = []
from collections import Counter
cb, ca = Counter(), Counter()
for s, rows in sess.items():
    for t, text, cl, rep in rows:
        n += 1; nw = c.classify(text); cb[cl] += 1; ca[nw] += 1
        if nw != cl:
            ch += 1; lst.append((s, t, re.sub(r"\s+", " ", o.answer_part(text)).strip()[:100], cl or "—", nw or "—"))
print(f"поправок {n}, змінили клас {ch}")
for x in lst: print(" ", x[0], x[1], f"«{x[2]}»", x[3], "→", x[4])
print("класи до:", sorted(((k or '—'), v) for k, v in cb.items()))
print("класи після:", sorted(((k or '—'), v) for k, v in ca.items()))
