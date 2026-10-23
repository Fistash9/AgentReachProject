"""Лічильник реєстру класів помилок (Q12, 2026-10-16; запит користувача «зроби як буде краще для реєстру
помилок» → «Спершу 1 і 2, потім покажи»). Класи й ознаки — agents/claude-code/q12-classes-2026-10-16/
registry-v1.md. Лише читає журнали сесій; без моделі (ознаки — слова в поправці).

  python3 tools/error-registry.py                  # поточна (найсвіжіша cli) сесія: поправки і «клас — N-й раз»
  python3 tools/error-registry.py --session <id>   # конкретна сесія (префікс id)
  python3 tools/error-registry.py --all            # підсумок за всіма сесіями
  python3 tools/error-registry.py --loop           # клас → ліки (registry-v1.md «## Ліки») → ⚠ повтор після ліків; частка поправок
  python3 tools/error-registry.py --eval <labels> <corrections.jsonl>  # точність ознак (id|клас)
"""
import glob, json, os, re, sys
from collections import Counter

LOGS = os.path.expanduser("~/.claude/projects/-data-data-com-termux-files-home-AgentReachProject")

# поправка-докір: рядки 1–3 — набір бектесту 16.10 (48 справжніх із 72); рядок 4 — 2026-10-16 (проба Q12:
# лічильник пропустив «чому не зробилось», «воно не працює»; рішення користувача «Так, вносити»). Рядок 4 на
# 2065 повідомленнях: +27 збігів, справжніх 19 (+4 межа) за claude-code, 23 за сліпою звіркою DeepSeek
TRIG = re.compile(
    r"знов|знову|вже казав|вже говорил|ми ж (?:вже|домовл)|скільки раз|ти перевіря|ти не перевір|"
    r"не перевірив|як ти міг|чому ти не|чому не спитав|ти що (?:придум|вигад)|ти придумав|"
    r"я ж казав|я казав|забув|пропустив|на око|не розумію шифр|навіщо ти|"
    r"чому ти\b|чому не\b|як так вийшло|не зробилось|не спрацювал|воно не працює|не зробив|"
    r"перевір(?:ив|яв|ено)\s*\?|і що\s*\?\s*$|не скористал", re.I)
REPEAT = re.compile(r"знов|знову|я казав|я ж казав|вже казав|вже казали|вже говорил|ми ж|скільки раз", re.I)
SYS = re.compile(r"^\s*<(?:system-reminder|command-|local-command|task-notification|bash-|pasted_content)")
LONG = 120  # довші за це — вставки/постановки, не поправка (бектест: шум 24 з 72)

# порядок = пріоритет = порядок таблиці (registry-v1.md «Правило розкладки»: Р1 першим)
CLASSES = [
    ("Р1", "Дія чи висновок до перевірки",
     r"перевір|історі\w* створ|зламат|неможлив|не можливо|придум|не побачив|по частинам|"
     r"не повним|не дивився|не шукав|не впевнений|баланс"),
    ("Р2", "Дія без прямого «так»", r"не спитав|сам вирішив|не чекаш|не чекаєш|ліміти ставиш|без мене"),
    ("Р3", "Переказ губить деталі", r"переказ|перекрут|не так написав"),
    ("Р4", "Зроблено частково / латка замість системи",
     r"хвост|висять|глобально|симптом|не лікує|закривати|обіця"),
    ("Р5", "Розфокус: черга й пріоритет на око", r"розфокус|поярусн|на око|критері|рівнев"),
    ("Р6", "Незрозуміла мова для користувача", r"шифр|не розумію"),
    ("Р7", "Позначка чи назва замість змісту", r"позначк|за назвою|значок"),
    ("Р8", "Дія без цілі", r"\bціль|основн\w* ціл"),
    ("Р9", "Не той шлях чи інструмент; свої записи не підняв",
     r"(?:знов|не через|не на пряму|навіщо ти)[^.?!]{0,40}(?:діпсік|deepseek|делегатор|веб ?серч)|"
     r"чому ти не (?:запропонував|користувався|згадав)|не користувався|не згадав|вже розглядали|"
     r"в арсеналі|пам.?ять не та|скіли|"
     r"не віддаєш[^.?!]{0,30}агент|агент\w*[^.?!]{0,12}не користу"),  # 23.10: «чому не віддаєш процеси агенту опусу?», «знов агентами не користуєшся?»
]
CLASSES = [(c, n, re.compile(p, re.I)) for c, n, p in CLASSES]
NAMES = {c: n for c, n, _ in CLASSES}


def answer_part(text):
    """Відповідь у віконці приходить як «"питання"="відповідь"» — класифікуємо лише слова користувача."""
    parts = re.findall(r'"=\s*"(.*?)"(?=\s*(?:,\s*"|\.|$))', text, re.S)
    return " ".join(parts) if parts else text


def classify(text):
    text = answer_part(text)
    for c, _, rx in CLASSES:
        if rx.search(text):
            return c
    return None


def user_texts(d):
    c = d.get("message", {}).get("content")
    if isinstance(c, str):
        return [c]
    out = []
    for b in c or []:
        if b.get("type") == "text":
            out.append(b["text"])
        elif b.get("type") == "tool_result":
            t = b.get("content")
            t = t if isinstance(t, str) else " ".join(x.get("text", "") for x in t or [] if isinstance(x, dict))
            m = re.match(r"\s*(?:User has answered your questions|The user answered|"
                         r"Your questions have been answered):(.*)", t, re.S)
            if m:
                out.append(re.split(r"You can now continue|Read the answers carefully", m.group(1))[0])
    return out


def corrections(path, counts=None):
    """Поправки користувача в одній cli-сесії: [(час, текст, клас, повтор)]. counts (dict) — сюди
    «msgs»: скільки всього повідомлень користувача пройшло ті самі фільтри (знаменник частки поправок)."""
    rows = []
    for line in open(path, encoding="utf-8"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("type") == "user" and d.get("entrypoint") not in (None, "cli"):
            if counts is not None:
                counts["msgs"] = 0
            return []  # під-сесія помічника
        if d.get("type") == "attachment" and d.get("attachment", {}).get("type") == "queued_command":
            q = d["attachment"].get("prompt", "")  # повідомлення посеред ходу (бектест: 5 справжніх поправок)
            texts = [q if isinstance(q, str) else " ".join(
                x.get("text", "") if isinstance(x, dict) else str(x) for x in q)]
        elif d.get("type") == "user" and not d.get("isMeta"):
            texts = user_texts(d)
        else:
            continue
        for s in texts:
            if not isinstance(s, str) or not s.strip() or SYS.match(s) or len(s.split()) > LONG:
                continue
            if counts is not None:
                counts["msgs"] = counts.get("msgs", 0) + 1
            if TRIG.search(answer_part(s)):  # лише слова користувача, не питання асистента у віконці (16.10: 4 хибні)
                rows.append((d.get("timestamp", "")[:16], s.strip(), classify(s), bool(REPEAT.search(s))))
    return rows


def all_sessions():
    out = {}
    for f in sorted(glob.glob(LOGS + "/*.jsonl"), key=os.path.getmtime):
        r = corrections(f)
        if r:
            out[os.path.basename(f)[:8]] = r
    return out


def current_session():
    cli = []
    for f in sorted(glob.glob(LOGS + "/*.jsonl"), key=os.path.getmtime, reverse=True):
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                d = json.loads(line) if line.strip().startswith("{") else {}
                if d.get("type") == "user":
                    if d.get("entrypoint") == "cli":
                        return os.path.basename(f)[:8]
                    break
    return None


def report_session(sid):
    sess = all_sessions()
    if sid not in sess:
        print(f"сесія {sid}: поправок за тригерами немає")
        return
    before = Counter()
    for s, rows in sess.items():
        if s == sid:
            break
        before.update(r[2] for r in rows)
    now = Counter()
    print(f"Реєстр помилок — сесія {sid}: поправок {len(sess[sid])}")
    for t, text, c, rep in sess[sid]:
        now[c] += 1
        n = before[c] + now[c]
        name = NAMES.get(c, "без класу (перевір вручну)")
        print(f"  {t[5:]}  {c or '—'} {name} — {n}-й раз{' · повтор (каже користувач)' if rep else ''}")
        print(f"         «{re.sub(chr(10), ' ', text)[:110]}»")


def report_all():
    sess = all_sessions()
    tot, rep, first, last = Counter(), Counter(), {}, {}
    for s, rows in sess.items():
        for t, _, c, r in rows:
            tot[c] += 1
            rep[c] += r
            first.setdefault(c, t[:10])
            last[c] = t[:10]
    print(f"Реєстр помилок — усі сесії: {len(sess)} з поправками, поправок {sum(tot.values())}")
    for c, n in tot.most_common():
        print(f"  {c or '—'} {NAMES.get(c, 'без класу'):<48} {n:>3}  (повтор за словами: {rep[c]}; "
              f"{first[c]} … {last[c]})")


REGISTRY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "agents", "claude-code", "q12-classes-2026-10-16", "registry-v1.md")


def remedies(path=REGISTRY):
    """{клас: [(час коміту, коміт, ліки)]} з розділу «## Ліки» реєстру; час — з git (UTC)."""
    import subprocess
    from datetime import datetime, timezone
    out, on = {}, False
    for l in open(path, encoding="utf-8"):
        on = on or l.startswith("## Ліки")
        m = on and re.match(r"\|\s*(Р\d)\s*\|\s*(\d{4}-\d\d-\d\d)\s*\|\s*([0-9a-f]{7,})\s*\|\s*(.+?)\s*\|", l)
        if m:
            r = subprocess.run(["git", "-C", os.path.dirname(path), "log", "-1", "--format=%ct", m.group(3)],
                               capture_output=True, text=True)
            ts = (datetime.fromtimestamp(int(r.stdout.strip()), timezone.utc).strftime("%Y-%m-%dT%H:%M")
                  if r.stdout.strip().isdigit() else m.group(2) + "T23:59")  # без git — кінець дня (суворіше)
            out.setdefault(m.group(1), []).append((ts, m.group(3), m.group(4)))
    return out


def report_loop():
    """Коло «клас → ліки → повторилось після ліків?» + частка поправок від повідомлень по тижнях (2026-10-19;
    ідея — cc-retrospective-learner «昇格», мірило — shenxingy/Clade «correction rate»)."""
    from datetime import date
    rem = remedies()
    sess, week = {}, {}
    for f in sorted(glob.glob(LOGS + "/*.jsonl"), key=os.path.getmtime):
        cnt = {}
        rows = corrections(f, cnt)
        if rows:
            sess[os.path.basename(f)[:8]] = rows
        if cnt.get("msgs"):
            with open(f, encoding="utf-8") as fh:  # тиждень — за першим повідомленням сесії
                first = next((t for t in (json.loads(l).get("timestamp", "") for l in fh
                                          if '"timestamp"' in l and l.strip().startswith("{")) if t), "")
            if first:
                wk = "%d-W%02d" % date.fromisoformat(first[:10]).isocalendar()[:2]
                w = week.setdefault(wk, [0, 0])
                w[0] += len(rows)
                w[1] += cnt["msgs"]
    allrows = [r for rows in sess.values() for r in rows]
    print(f"Коло реєстру: поправок {len(allrows)} у {len(sess)} сесіях; ліки — {REGISTRY.split('/')[-1]} «## Ліки»")
    warn = 0
    for c, name, _ in CLASSES:
        rs = [r for r in allrows if r[2] == c]
        lk = sorted(rem.get(c, []))
        if not rs and not lk:
            continue
        if not lk:
            print(f"  {c} {name}: поправок {len(rs)}; ліків-механізмів немає")
            continue
        last = lk[-1][0]
        after = [r for r in rs if r[0] > last]
        mark = "⚠ ліки не діють" if after else "ок: після ліків повторів нема"
        warn += bool(after)
        print(f"  {c} {name}: поправок {len(rs)} (до останніх ліків {len(rs) - len(after)}, після {len(after)}); "
              f"ліків {len(lk)}, останні {last[:10]} {lk[-1][1]} — {mark}")
        for t, text, _, rep in after[:3]:
            print(f"      {t[:16]}{' · повтор' if rep else ''}  «{re.sub(chr(10), ' ', text)[:90]}»")
    print(f"⚠ класів з повтором після ліків: {warn}")
    print("Частка поправок (поправки / повідомлення користувача) по тижнях:")
    for wk in sorted(week):
        n, m = week[wk]
        print(f"  {wk}: {n}/{m} = {n / m:.1%}")


def evaluate(labels_path, jsonl_path):
    """Точність ознак проти ручної розкладки: labels — рядки «id|клас», jsonl — вихід бектесту 16.10
    (agents/claude-code/q12-classes-2026-10-16/backtest.py; id = номер рядка)."""
    lab = {}
    for l in open(labels_path, encoding="utf-8"):
        m = re.match(r"\s*(\d+)\s*\|\s*(Р\d)", l)
        if m:
            lab[int(m.group(1))] = m.group(2)
    rows = [json.loads(l)["user"] for l in open(jsonl_path, encoding="utf-8")]
    ok, bad = 0, []
    for i, lb in sorted(lab.items()):
        got = classify(rows[i - 1])
        ok += got == lb
        if got != lb:
            bad.append((i, lb, got, re.sub(r"\s+", " ", rows[i - 1])[:90]))
    print(f"збіг ознак з ручною розкладкою: {ok} з {len(lab)}")
    for b in bad:
        print("  ", *b)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["--all"]:
        report_all()
    elif a[:1] == ["--loop"]:
        report_loop()
    elif a[:1] == ["--eval"] and len(a) > 2:
        evaluate(a[1], a[2])
    elif a[:1] == ["--session"] and len(a) > 1:
        report_session(a[1][:8])
    else:
        sid = current_session()
        report_session(sid) if sid else print("cli-сесію не знайдено")
