"""Допоміжне: усі повідомлення користувача, що пройшли фільтри corrections() (ті самі, що й лічильник).
python3 scan.py <модуль.py> <regex>  — повідомлення, де regex є, а is_correction модуля = False."""
import importlib.util, glob, json, os, re, sys
def load(p, name):
    s = importlib.util.spec_from_file_location(name, p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def messages(m):
    """(сесія, час, текст) для кожного повідомлення, що пройшло фільтри corrections() модуля m."""
    out = []
    for f in sorted(glob.glob(m.LOGS + "/*.jsonl"), key=os.path.getmtime):
        sid = os.path.basename(f)[:8]; buf = []
        for line in open(f, encoding="utf-8"):
            try: d = json.loads(line)
            except ValueError: continue
            if d.get("type") == "user" and d.get("entrypoint") not in (None, "cli"):
                buf = None; break
            if d.get("type") == "attachment" and d.get("attachment", {}).get("type") == "queued_command":
                if d["attachment"].get("origin", {}).get("kind", "human") != "human": continue
                q = d["attachment"].get("prompt", "")
                texts = [q if isinstance(q, str) else " ".join(x.get("text", "") if isinstance(x, dict) else str(x) for x in q)]
            elif d.get("type") == "user" and not d.get("isMeta"):
                texts = m.user_texts(d)
            else: continue
            for s in texts:
                if not isinstance(s, str) or not s.strip() or m.SYS.match(s) or len(s.split()) > m.LONG: continue
                buf.append((sid, d.get("timestamp", "")[:16], s.strip()))
        if buf: out += buf
    return out
if __name__ == "__main__":
    m = load(sys.argv[1], "reg"); rx = re.compile(sys.argv[2], re.I)
    ms = messages(m); print("повідомлень:", len(ms))
    for sid, t, s in ms:
        a = m.answer_part(s)
        if rx.search(a) and not m.is_correction(s):
            print(sid, t, "«" + re.sub(r"\s+", " ", a)[:150] + "»")
