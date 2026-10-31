"""Якість роботи агентів › реєстр класів помилок › бектест кандидатів ліків від Р1 (роздача 2 пілоту, 2026-10-30).
Мета: на ВСІХ ходах агента (межі «хід» — як у r1_context.py --base) виміряти, яка ознака стану сесії
відділяє ходи, після яких користувач поправляє класом Р1, від решти. Лише читає журнали; нічого не змінює.

  python3 -I backtest2.py            # таблиця кандидатів
  python3 -I backtest2.py --list K2  # перелік ходів з ознакою (сесія:рядок, Р1?)

Ознаки (спрощення названо в BACKTEST-2.md):
  K1orig   у тексті ходу є позначка «не перевірено…» (як у R1-REPORT, регекс UNVER)
  K1fix    у кінці ходу в ЕПІЗОДІ (від останнього набраного повідомлення; відповіді у віконцях не скидають)
           лишилась невиправлена позначка: після неї не було жодного інструмента-перевірки (Bash-читання, Read,
           WebFetch/Search, Agent, delegate…); позначка шукається у тексті асистента І у вмісті записів
  K1next   позначка в цьому ході, і найближча після неї подія — віконце / запис / кінець ходу (а не перевірка)
  K2nohist правка наявного файлу в межах проєкту/.claude без попереднього в сесії git log/blame/show/grep/rg з ім'ям цього файлу
  K2both   те саме, і ще без попереднього Read/читання саме цього файлу (файл, створений у сесії, вважається «відомим»)
  K3ask    віконце AskUserQuestion зі «записат/закомітит/дописат/коміт» без claimcheck у цьому чи попередньому ході
  K3write  запис у TROUBLES/BACKLOG/trees з числами або причинами без claimcheck у цьому чи попередньому ході
  K3       K3ask або K3write;  K3loose — те саме, але «кредитом» вважається і wc/grep -c/uniq -c/python у ході
"""
import glob, importlib.util, json, os, re, sys
from collections import Counter

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("r1c", os.path.join(HERE, "r1_context.py"))
r1c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r1c)
er = r1c.er
ROOT = r1c.ROOT
CLAUDE_HOME = os.path.expanduser("~/.claude")

UNVER_ORIG = r1c.UNVER
UNVER_FIX = re.compile(r"не перевірено|unverified|не вдалося перевірити|не вдалось перевірити|не перевіряв|не перевірив"
                       r"|перевірити не вдалося|не встиг перевірити|не підтверджено", re.I)
UNVER_NOISE = re.compile(r"\b0\s+не перевірено|не перевірено[:\s]+0\b", re.I)  # лічильник «0 не перевірено» — не позначка
GIT_HIST = re.compile(r"git\s+(?:-C\s+\S+\s+)?(?:log|blame|show)\b|\bgrep\b|\brg\b")
READ_CMD = re.compile(r"\b(?:cat|head|tail|sed\s+-n|less|nl|wc)\b")
BASH_WRITE = re.compile(r"sed\s+-i|>>|(?<![>&\d])>\s*[^\s&|>]|\bcp\b|\btee\b|write_text|\.write\(|open\([^)]*['\"][wa]b?['\"]")
PYWRITE = re.compile(r"write_text|\.write\(|open\([^)]*['\"][wa]b?['\"]")
EXT = r"(?:md|py|json|jsonl|tsv|txt|sh|yml|yaml|toml|js|html|cfg|conf)"
PATHTOK = re.compile(r"[~\w./@+-]+\." + EXT + r"\b")
REDIR = re.compile(r">>?\s*([^\s&|;<>'\"]+)")
K3_ASK = re.compile(r"записат|закомітит|дописат|коміт", re.I)
K3_FILE = re.compile(r"TROUBLES\.md|BACKLOG\.md|trees/")
K3_NUM = re.compile(r"\d{2,}|\d+[,.]\d+|\d+\s*(?:з|%)")
K3_CAUSE = re.compile(r"\bбо\b|через|причин|тому що|корін|унаслідок|внаслідок", re.I)
CLAIMCHECK = re.compile(r"claimcheck")
LOOSE = re.compile(r"claimcheck|\bwc\b|grep\s+-\w*c\b|uniq\s+-c|python3?\b")
VERIFY_TOOLS = {"Read", "WebFetch", "WebSearch", "Agent", "Grep", "Glob", "mcp__delegate__delegate", "mcp__deepseek__deepseek",
                "mcp__agent-reach__read"}


def norm(p):
    p = os.path.expanduser(p)
    return os.path.normpath(p if os.path.isabs(p) else os.path.join(ROOT, p))


def in_scope(p):
    if "/tmp/" in p or p.startswith("/dev/") or "/.trash/" in p:
        return False
    return p.startswith(ROOT + "/") or p.startswith(CLAUDE_HOME + "/")


def bash_targets(cmd):
    """Шляхи, у які Bash-команда імовірно пише (наближення: редирект, sed -i, cp, tee, вікно навколо python-запису)."""
    t = set(m.group(1) for m in REDIR.finditer(cmd))
    for m in re.finditer(r"(?:sed\s+-i|\bcp\b|\btee\b)[^;&|\n]*", cmd):
        t.update(PATHTOK.findall(m.group(0)))
    for m in PYWRITE.finditer(cmd):
        t.update(PATHTOK.findall(cmd[max(0, m.start() - 200):m.end() + 200]))
    out = set()
    for x in t:
        if re.search(r"\." + EXT + r"$", x):
            p = norm(x)
            if in_scope(p):
                out.add(p)
    return out


def scan(path, sid):
    """Повертає список ходів: dict(key, r1, ознаки)."""
    turns = []
    # стан сесії
    known, hist_cmds = set(), []
    ep_events = []          # події епізоду: ("mark"|"verify"|"other", ...)
    turn_ev = []            # події ходу
    turn_edits, turn_k3 = [], []   # k3: (вид, claim_ok, loose_ok)
    claim_prev, claim_turn, loose_turn = False, False, False
    write_ids, wres = {}, {}
    ask_turn = False
    lineno = 0
    for line in open(path, encoding="utf-8"):
        lineno += 1
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("type") == "user" and d.get("entrypoint") not in (None, "cli"):
            return []
        if d.get("type") == "assistant":
            for b in d.get("message", {}).get("content") or []:
                if b.get("type") == "text":
                    tx = b.get("text", "")
                    if UNVER_ORIG.search(tx):
                        turn_ev.append("mark_orig")  # K1orig — лише текст асистента, як у R1-REPORT (523)
                    if UNVER_FIX.search(tx) and not UNVER_NOISE.search(tx):
                        ep_events.append("mark")
                        turn_ev.append("mark_fix")
                elif b.get("type") == "tool_use":
                    name, inp = b.get("name"), b.get("input") or {}
                    cmd = inp.get("command", "") if name == "Bash" else ""
                    blob = json.dumps(inp, ensure_ascii=False)
                    if UNVER_FIX.search(blob) and not UNVER_NOISE.search(blob):
                        ep_events.append("mark")
                        turn_ev.append("mark_fix")
                    writes = []  # (path, existing, content)
                    if name == "Edit" and inp.get("file_path"):
                        p = norm(inp["file_path"])
                        writes.append((p, True, inp.get("new_string", "")))
                    elif name == "Write" and inp.get("file_path"):
                        p = norm(inp["file_path"])
                        writes.append((p, None, inp.get("content", "")))
                        write_ids[b["id"]] = None
                    elif name == "Bash" and BASH_WRITE.search(cmd):
                        for p in bash_targets(cmd):
                            writes.append((p, os.path.exists(p), cmd))
                    is_write = bool(writes)
                    if name == "Bash":
                        if CLAIMCHECK.search(cmd):
                            claim_turn = True
                        if LOOSE.search(cmd):
                            loose_turn = True
                    for p, ex, content in writes:
                        if in_scope(p):
                            base = os.path.basename(p)
                            rec = {"path": p, "ex": ex, "known": p in known,
                                   "hist": any(base in c for c in hist_cmds)}
                            if name == "Write":
                                write_ids[b["id"]] = rec
                            turn_edits.append(rec)
                        if K3_FILE.search(p) and (K3_NUM.search(content) or K3_CAUSE.search(content)):
                            turn_k3.append(("write", claim_turn or claim_prev, claim_turn or claim_prev or loose_turn))
                        known.add(p)
                    if name == "AskUserQuestion" and K3_ASK.search(blob):
                        turn_k3.append(("ask", claim_turn or claim_prev, claim_turn or claim_prev or loose_turn))
                    # читання / історія — після оцінки самої правки
                    if name == "Read" and inp.get("file_path"):
                        known.add(norm(inp["file_path"]))
                    if name == "Bash":
                        if GIT_HIST.search(cmd):
                            hist_cmds.append(cmd)
                        if READ_CMD.search(cmd) and not is_write:
                            for x in PATHTOK.findall(cmd):
                                known.add(norm(x))
                    if name == "AskUserQuestion":
                        turn_ev.append("ask")
                        ep_events.append("other")
                    elif is_write:
                        turn_ev.append("write")
                        ep_events.append("other")
                    elif name in VERIFY_TOOLS or name == "Bash" or name.startswith("mcp__"):
                        turn_ev.append("verify")
                        ep_events.append("verify")
                    else:
                        ep_events.append("other")
            continue
        if d.get("type") == "user":
            c = d.get("message", {}).get("content")
            if isinstance(c, list):
                tur = d.get("toolUseResult")
                for b in c:
                    if b.get("type") == "tool_result" and b.get("tool_use_id") in write_ids:
                        rec = write_ids.pop(b["tool_use_id"])
                        if rec is not None and isinstance(tur, dict):
                            rec["ex"] = (tur.get("type") == "update")
        texts = [s for s in r1c.human_texts(d) if isinstance(s, str) and s.strip() and not er.SYS.match(s)
                 and len(s.split()) <= er.LONG]
        if not texts:
            continue
        is_r1 = any(er.is_correction(s) and er.classify(s) == "Р1" for s in texts)
        # ознаки ходу
        f = {}
        f["K1orig"] = "mark_orig" in turn_ev
        unresolved = False
        for e in ep_events:
            if e == "mark":
                unresolved = True
            elif e == "verify":
                unresolved = False
        f["K1fix"] = unresolved
        # K1next: позначка В ЦЬОМУ ході, і наступна подія після останньої позначки — віконце / запис / кінець ходу
        tail = []
        for e in turn_ev:
            if e == "mark_fix":
                tail = []
            elif e in ("verify", "ask", "write"):
                tail.append(e)
        f["K1next"] = "mark_fix" in turn_ev and (not tail or tail[0] in ("ask", "write"))
        ed = [e for e in turn_edits if e["ex"]]
        f["K2nohist"] = any(not e["hist"] for e in ed)
        f["K2both"] = any(not e["hist"] and not e["known"] for e in ed)
        f["K3ask"] = any(k[0] == "ask" and not k[1] for k in turn_k3)
        f["K3write"] = any(k[0] == "write" and not k[1] for k in turn_k3)
        f["K3"] = f["K3ask"] or f["K3write"]
        f["K3loose"] = any(not k[2] for k in turn_k3)
        f["K3ask_loose"] = any(k[0] == "ask" and not k[2] for k in turn_k3)
        f["K3write_loose"] = any(k[0] == "write" and not k[2] for k in turn_k3)
        f["K1fix&K3"] = f["K1fix"] and f["K3"]
        f["K1fix&K3loose"] = f["K1fix"] and f["K3loose"]
        f["Kany"] = f["K1fix"] or f["K2nohist"] or f["K3"]
        turns.append({"key": (sid, lineno), "r1": is_r1, "f": f})
        # нова межа
        claim_prev = claim_turn
        turn_ev, turn_edits, turn_k3, claim_turn, loose_turn = [], [], [], False, False
        if r1c.channel(d) != "ask":
            ep_events = []
    return turns


def main():
    rows = [json.loads(l) for l in open(os.path.join(HERE, "r1_context.jsonl"), encoding="utf-8")]
    labels = {}
    for l in open(os.path.join(HERE, "r1-labels.tsv"), encoding="utf-8"):
        n, t, _ = l.rstrip("\n").split("\t", 2)
        labels[int(n)] = t
    sample = {(r["session"], r["line"]): 43 + i for i, r in enumerate(rows[42:62])}
    true17 = {k: n for k, n in sample.items() if labels[n] != "T5"}
    allr1 = {(r["session"], r["line"]) for r in rows}

    turns = []
    for p in sorted(glob.glob(er.LOGS + "/*.jsonl"), key=os.path.getmtime):
        turns += scan(p, os.path.basename(p)[:8])
    N = len(turns)
    R = sum(t["r1"] for t in turns)
    by_key = {t["key"]: t for t in turns}
    print(f"усього ходів {N}, з них далі Р1 {R} ({R / N:.1%}); ключів вибірки знайдено {sum(k in by_key for k in sample)}/20, "
          f"усіх 62 поправок як хід: {sum(k in by_key for k in allr1)}/62; справжніх Р1 у вибірці: {len(true17)}")
    if len(sys.argv) > 2 and sys.argv[1] == "--list":
        for t in turns:
            if t["f"][sys.argv[2]]:
                print(t["key"], t["r1"])
        return
    print(f"{'ознака':<14}{'ходів':>6}{'Р1':>4}{'частка':>8}{'лift':>6}{'хибних/100':>11}{'з 17':>6}{'з 62':>6}  номери з 17")
    for k in ("K1orig", "K1fix", "K1next", "K2nohist", "K2both", "K3ask", "K3write", "K3", "K3loose", "K3ask_loose", "K3write_loose", "K1fix&K3", "K1fix&K3loose", "Kany"):
        n = sum(t["f"][k] for t in turns)
        r = sum(t["f"][k] and t["r1"] for t in turns)
        hit17 = sorted(num for key, num in true17.items() if key in by_key and by_key[key]["f"][k])
        hit62 = sum(1 for key in allr1 if key in by_key and by_key[key]["f"][k])
        share = r / n if n else 0
        print(f"{k:<14}{n:>6}{r:>4}{share:>8.1%}{(share / (R / N) if n else 0):>6.2f}{(n - r) / N * 100:>11.1f}{len(hit17):>6}{hit62:>6}  {hit17}")


if __name__ == "__main__":
    main()
