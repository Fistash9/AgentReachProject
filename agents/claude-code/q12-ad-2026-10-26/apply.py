import re, sys
D = "/data/data/com.termux/files/usr/tmp/q12-ad-2610"
f = D + "/error-registry.py"
s = open(f, encoding="utf-8").read()
def rep(old, new, cnt=1):
    global s
    assert s.count(old) == cnt, (old, s.count(old))
    s = s.replace(old, new)

# A1: Р9 — агенти в будь-якому порядку слів (форми мн./род.), «робиш сам / сам робиш»
rep('''     r"не віддаєш[^.?!]{0,30}агент|агент\\w*[^.?!]{0,12}не користу"),''',
    '''     r"не віддаєш[^.?!]{0,30}агент|агент\\w*[^.?!]{0,12}не користу|"
     r"агент(?:ам|ами|ів|и|а)\\b|робиш\\s+сам|сам\\s+робиш"),  # 26.10 A (копія): «агентів… не забув запускати?», «ти знов робиш сам»''')
# A2: виняток з порядку — тема «віддати іншому виконавцю» сильніша за загальне «перевір» Р1
rep('''CLASSES = [(c, n, re.compile(p, re.I)) for c, n, p in CLASSES]''',
    '''CLASSES = [(c, n, re.compile(p, re.I)) for c, n, p in CLASSES]
# 26.10 A (копія, пропозиція): виняток із «Правила розкладки» (Р1 першим) — «віддати … діпсіку/делегатору/агенту»
# — це Р9 «роблю сам замість агентів», навіть коли поруч загальне «перевір» (сліпа розмітка B06, 26.10)
PRIORITY = [("Р9", re.compile(r"віддат\\w*[^.?!]{0,30}(?:діпсік|deepseek|делегатор|агент)", re.I))]''')
rep('''    text = answer_part(text)
    for c, _, rx in CLASSES:''', '''    text = answer_part(text)
    for c, rx in PRIORITY:
        if rx.search(text):
            return c
    for c, _, rx in CLASSES:''')

# D0: копія реєстру поза git — час коміту беремо з git проєкту
rep('''REGISTRY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "agents", "claude-code", "q12-classes-2026-10-16", "registry-v1.md")''',
    '''REGISTRY = "/data/data/com.termux/files/usr/tmp/q12-ad-2610/registry-v1.md"  # КОПІЯ; при перенесенні повернути шлях проєкту
GITDIR = "/data/data/com.termux/files/home/AgentReachProject"  # КОПІЯ; у проєкті було os.path.dirname(path)


def target_rx(t):
    """Мішень ліків (26.10 D, пропозиція): «*» — увесь клас; інакше основи через кому — поправка має цю мішень,
    якщо її слова містять хоч одну основу (підрядок, без регістру)."""
    t = (t or "*").strip()
    if t in ("*", "", "—", "-"):
        return None
    return re.compile("|".join(re.escape(x.strip()) for x in t.split(",") if x.strip()), re.I)''')
rep('''    """{клас: [(час коміту, коміт, ліки)]} з розділу «## Ліки» реєстру; час — з git (UTC)."""''',
    '''    """{клас: [(час коміту, коміт, ліки, мішень)]} з розділу «## Ліки» реєстру; час — з git (UTC)."""''')
rep('''(\\d{4}-\\d\\d-\\d\\d)\\s*\\|\\s*([0-9a-f]{7,})\\s*\\|\\s*(.+?)\\s*\\|", l)''',
    '''(\\d{4}-\\d\\d-\\d\\d)\\s*\\|\\s*([0-9a-f]{7,})\\s*\\|\\s*(.+?)\\s*\\|(?:\\s*(.*?)\\s*\\|)?", l)''')
rep('''["git", "-C", os.path.dirname(path), "log"''', '''["git", "-C", GITDIR, "log"''')
rep('''out.setdefault(m.group(1), []).append((ts, m.group(3), m.group(4)))''',
    '''out.setdefault(m.group(1), []).append((ts, m.group(3), m.group(4), m.group(5) or "*"))''')

# D1: «після ліків» — від останніх ліків того самого класу І тієї самої мішені
old_loop = s[s.index("        last = lk[-1][0]\n"):s.index('    print(f"⚠ класів з повтором після ліків: {warn}")')]
new_loop = '''        groups = {}
        for x in lk:
            groups.setdefault(x[3], []).append(x)
        covered, lines = set(), []
        for tg, g in groups.items():
            rx = target_rx(tg)
            rt = [r for r in rs if rx is None or rx.search(answer_part(r[1]))]
            covered.update(id(r) for r in rt)
            after = [r for r in rt if r[0] > g[-1][0]]
            lines.append((tg, rt, g[-1], after))
        outside = [r for r in rs if id(r) not in covered]
        cw = sum(bool(x[3]) for x in lines)
        mark = ("⚠ ліки не діють" if cw else
                "ок? недійсне — детектор зламаний" if broken else "ок: після ліків повторів нема")
        warn += bool(cw)
        print(f"  {c} {name}: поправок {len(rs)}; ліків {len(lk)}, мішеней {len(groups)}, "
              f"поза мішенями {len(outside)} — {mark}")
        for tg, rt, last, after in lines:
            print(f"    мішень «{tg[:40]}»: поправок {len(rt)} (після {len(after)}); "
                  f"останні {last[0][:10]} {last[1]}{' — ⚠' if after else ''}")
            for t, text, _, rep in after[:3]:
                print(f"      {t[:16]}{' · повтор' if rep else ''}  «{re.sub(chr(10), ' ', text)[:90]}»")
'''
s = s.replace(old_loop, new_loop)
open(f, "w", encoding="utf-8").write(s)

# реєстр: колонка «мішень»
g = D + "/registry-v1.md"
r = open(g, encoding="utf-8").read()
T = {"d9081e7": "*", "8b846bb": "встанов", "133d08e": "*", "be2cd2e": "коміт, пуш",
     "de27ed6": "*", "1d270c8": "*", "d24aebf": "*", "678da7c": "*", "059f8c3": "*", "1868413": "*",
     "89d33cf": "*", "61b2f29": "*", "7d558d5": "*", "61393ef": "запис, історі", "09a792c": "*",
     "2c4ed22": "*", "275be07": "гілк, закрит"}
out = []
for l in r.split("\n"):
    if l == "| клас | дата | коміт | ліки |":
        l = "| клас | дата | коміт | ліки | мішень |"
    elif l == "|---|---|---|---|":
        l = "|---|---|---|---|---|"
    else:
        m = re.match(r"\| (Р\d+) \| [\d-]+ \| ([0-9a-f]+) \| (.*) \|$", l)
        if m:
            h, txt = m.group(2), m.group(3)
            if h in T: tg = T[h]
            elif h == "e175cdc": tg = "процес, pkill, obsidian" if txt.startswith("proc-guard") else ("зрозумів" if txt.startswith("free-answer") else "*")
            elif h == "cc82a23": tg = ("обережно, естафет, не прочитав" if m.group(1) == "Р9" and txt.startswith("baton-guard") else
                                       "делегат, haiku, збій" if txt.startswith("delegate") else "пункт, зник, загуб")
            elif h == "1c944d1": tg = "агент, робиш сам, сам робиш, віддат"
            elif h in ("0eece8a", "3bf6a9f"): tg = "agent.py, ключ, копі"
            elif h == "396ae82": tg = "записк, де зупинил, втрат"
            else: raise SystemExit("нема мішені для " + l)
            l = l + f" {tg} |"
    out.append(l)
r = "\n".join(out)
note = ('''Колонка «мішень» (26.10, ПРОПОЗИЦІЯ під-агента, не затверджено): основи слів через кому; поправка має мішень,
якщо її слова містять хоч одну основу; «*» — ліки на весь клас. «Після ліків» рахується від останніх ліків
того самого класу і тієї самої мішені — ліки іншої теми (напр. ключ agent.py) не скидають лічильник «агенти».
''')
r = r.replace("Доповнено на закритті 19.10:", note + "\nДоповнено на закритті 19.10:", 1)
r = r.replace("(Р1 перед рештою: «до перевірки» — найчастіший корінь, бектест 21/48 і сліпо 23/48).",
  "(Р1 перед рештою: «до перевірки» — найчастіший корінь, бектест 21/48 і сліпо 23/48).\n"
  "Виняток (26.10, ПРОПОЗИЦІЯ): «віддати … діпсіку/делегатору/агенту» — Р9 навіть поруч із «перевір» (сліпа розмітка B06).", 1)
open(g, "w", encoding="utf-8").write(r)
print("ok")
