"""Якість роботи агентів › реєстр класів помилок › місце народження Р1 (2026-10-30, роздача 1 пілоту).
Для кожної поправки класу Р1 (тими самими фільтрами, що tools/error-registry.py corrections()) збирає хід агента,
на який відповідає користувач: інструменти з часу попереднього повідомлення людини і останній текст асистента.
Лише читає журнали. Вихід: r1_context.jsonl (поруч) + короткий друк.

  python3 r1_context.py            # усі поправки Р1
"""
import glob, importlib.util, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
spec = importlib.util.spec_from_file_location("er", os.path.join(ROOT, "tools", "error-registry.py"))
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


def tool_brief(b):
    """Інструмент і головний аргумент одним рядком."""
    i = b.get("input") or {}
    arg = (i.get("command") or i.get("file_path") or i.get("pattern") or i.get("description")
           or i.get("query") or i.get("skill") or json.dumps(i, ensure_ascii=False))
    return b.get("name", "?"), re.sub(r"\s+", " ", str(arg))[:140]


def human_texts(d):
    """Тексти людини в записі (ті самі фільтри, що er.corrections) — або [] якщо запис не від людини."""
    if d.get("type") == "attachment" and d.get("attachment", {}).get("type") == "queued_command":
        if d["attachment"].get("origin", {}).get("kind", "human") != "human":
            return []
        q = d["attachment"].get("prompt", "")
        return [q if isinstance(q, str) else " ".join(
            x.get("text", "") if isinstance(x, dict) else str(x) for x in q)]
    if d.get("type") == "user" and not d.get("isMeta"):
        return er.user_texts(d)
    return []


# позначка агента «я цього не перевірив» у його ж тексті ходу (кандидат К1)
UNVER = re.compile(r"не перевірено|unverified|не вдалося перевірити|не перевіряв|перевірити не вдалося", re.I)


def channel(d):
    """Як прийшли слова людини: ask — відповідь у віконці AskUserQuestion; queued — посеред ходу; typed — набране."""
    if d.get("type") == "attachment":
        return "queued"
    c = d.get("message", {}).get("content")
    return "ask" if isinstance(c, list) and any(b.get("type") == "tool_result" for b in c) else "typed"


def scan(path):
    out, turn, episode, marks, last_text, prev_human, lineno = [], [], [], [], "", "", 0
    for line in open(path, encoding="utf-8"):
        lineno += 1
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("type") == "user" and d.get("entrypoint") not in (None, "cli"):
            return []  # під-сесія
        if d.get("type") == "assistant":
            for b in d.get("message", {}).get("content") or []:
                if b.get("type") == "tool_use":
                    turn.append(tool_brief(b))
                    episode.append(tool_brief(b))
                elif b.get("type") == "text" and b.get("text", "").strip():
                    last_text = b["text"]
                    if UNVER.search(b["text"]):
                        marks.append(UNVER.search(b["text"]).group(0))
            continue
        texts = [s for s in human_texts(d) if isinstance(s, str) and s.strip() and not er.SYS.match(s)
                 and len(s.split()) <= er.LONG]
        for s in texts:
            if er.is_correction(s) and er.classify(s) == "Р1":
                out.append({"session": os.path.basename(path)[:8], "line": lineno, "channel": channel(d),
                            "episode": episode[-25:], "nepisode": len(episode), "unver_marks": marks[:],
                            "ts": d.get("timestamp", "")[:16], "user": s.strip(),
                            "prev_human": prev_human[:200], "tools": turn[-12:], "ntools": len(turn),
                            "last_text": last_text[-600:]})
        if texts:  # нове повідомлення людини — новий хід; епізод — з останнього набраного (не відповідь у віконці)
            prev_human, turn, last_text, marks = texts[-1], [], "", []
            if channel(d) != "ask":
                episode = []
    return out


def main():
    rows = []
    for f in sorted(glob.glob(er.LOGS + "/*.jsonl"), key=os.path.getmtime):
        rows += scan(f)
    with open(os.path.join(HERE, "r1_context.jsonl"), "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"поправок Р1: {len(rows)} у сесіях: {len({r['session'] for r in rows})}")




def around(sid, line, n=8):
    """Останні n подій до рядка line сесії sid: (рядок, вид, зміст) — для посилань у звіті."""
    f = glob.glob(er.LOGS + f"/{sid}*.jsonl")[0]
    ev = []
    for i, l in enumerate(open(f, encoding="utf-8"), 1):
        if i > line:
            break
        try:
            d = json.loads(l)
        except ValueError:
            continue
        if d.get("type") == "assistant":
            for b in d.get("message", {}).get("content") or []:
                if b.get("type") == "tool_use":
                    ev.append((i, "T", " ".join(tool_brief(b))))
                elif b.get("type") == "text" and b.get("text", "").strip():
                    ev.append((i, "A", re.sub(r"\s+", " ", b["text"])[-260:]))
        else:
            for s in human_texts(d):
                if isinstance(s, str) and s.strip() and not er.SYS.match(s):
                    ev.append((i, "U" + ("q" if d.get("type") == "attachment" else ""), re.sub(r"\s+", " ", s)[:160]))
    for e in ev[-n:]:
        print(f"  {e[0]:>5} {e[1]:<2} {e[2][:260]}")


if len(sys.argv) > 2 and sys.argv[1] == "--around":
    around(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]) if len(sys.argv) > 4 else 8)
    sys.exit(0)




# кандидат К2: правка/встановлення (Edit, Write, Bash-запис) і чи була в сесії раніше перевірка історії git
EDIT = re.compile(r"^(?:Edit|Write) |>>|sed -i|\bcp\b|\bmv\b|\brm\b|open\([^)]*[\"'][wa][\"']|\.write\(")
HIST = re.compile(r"git log|git blame|git show|log -S|log -p")


def base_rate():
    """Скільки ходів агента (між повідомленнями людини) мали ознаку і скільки з них дали поправку Р1 — хибні тривоги кандидатів.
    Ознаки ходу: unver — у тексті ходу позначка «не перевірено»; ask — хід закінчився AskUserQuestion; обидві."""
    from collections import Counter
    tot, r1 = Counter(), Counter()
    for f in glob.glob(er.LOGS + "/*.jsonl"):
        turn_unver, last_tool, sub, turn_tools, hist = False, None, False, [], False
        for line in open(f, encoding="utf-8"):
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get("type") == "user" and d.get("entrypoint") not in (None, "cli"):
                sub = True
                break
            if d.get("type") == "assistant":
                for b in d.get("message", {}).get("content") or []:
                    if b.get("type") == "tool_use":
                        last_tool = b.get("name")
                        n, a = tool_brief(b)
                        turn_tools.append(a if n == "Bash" else (n + " " + a if n in ("Edit", "Write") else ""))
                    elif b.get("type") == "text" and UNVER.search(b.get("text", "")):
                        turn_unver = True
                continue
            texts = [s for s in human_texts(d) if isinstance(s, str) and s.strip() and not er.SYS.match(s)
                     and len(s.split()) <= er.LONG]
            if not texts:
                continue
            hist_before = hist
            is_r1 = any(er.is_correction(s) and er.classify(s) == "Р1" for s in texts)
            ed = any(EDIT.search(t) for t in turn_tools)
            hist = hist or any(HIST.search(t) for t in turn_tools)
            for k, v in (("усі ходи", True), ("правка без git log у сесії", ed and not hist_before), ("unver", turn_unver), ("ask", last_tool == "AskUserQuestion"),
                         ("unver і ask", turn_unver and last_tool == "AskUserQuestion"),
                         ("unver або ask", turn_unver or last_tool == "AskUserQuestion")):
                if v:
                    tot[k] += 1
                    r1[k] += is_r1
            turn_unver, last_tool, turn_tools = False, None, []
    for k in tot:
        print(f"  {k:<14} ходів {tot[k]:>5}, з них далі поправка Р1 {r1[k]:>3} ({r1[k] / tot[k]:.1%})")


if len(sys.argv) > 1 and sys.argv[1] == "--base":
    base_rate()
    sys.exit(0)


if __name__ == "__main__":
    main()
