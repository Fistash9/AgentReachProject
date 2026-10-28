"""ПРОТОТИП «момент збою» для Bash (проба на копії; НЕ зареєстрований хук; лежить поза .claude/).
Задум (agents/claude-code/obhid-2026-10-28/PLAN.md): PostToolUse + PostToolUseFailure на Bash →
(1) сигнатура збою середовища (клас з whitelist) → (2) рецепт за індексом → 1 рядок «шлях:рядок» →
(3) 2-й/3-й збій того ж класу підряд → текст тригера Т2 (triggers-kod-zbiy-2026-10-25.md). Лише additionalContext, нічого не блокує."""
import sys, os, json, re, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from bt_common import SIGS, SOFT_RX, SOFT_OK, VIEWER
from bt_snap import parse
TROUBLES = "/data/data/com.termux/files/home/AgentReachProject/TROUBLES.md"
STATE_DIR = "/data/data/com.termux/files/usr/tmp/obhid/"
ENV_CLASSES = {"SHLIB", "BADINTERP", "ENV_NOFILE", "NOTFOUND", "PERM", "SHSYNTAX"}
SHEB = r"^MCP-probe результати|^pkgtruth MCP|^Картка: як ставити"
# (клас, regex у рядку помилки, regex у команді або None, regex заголовка рецепта, мітка)
INDEX = [
 ("SHLIB",      r"^-\w: error while loading", None, r"^grep і find не працюють", "grep/find-обгортка"),
 ("SHLIB",      r"error while loading shared libraries", None, r"^Freebuff у Termux працює через офіційну збірку|^Картка: як ставити", "glibc-бінарник без grun"),
 ("BADINTERP",  r"bad interpreter", None, SHEB, "shebang"),
 ("ENV_NOFILE", r"/usr/bin/env", None, SHEB, "нема /usr/bin/env"),
 ("NOTFOUND",   r"sh: \d+: [\w.@+-]+: not found", r"\bnpx\b|\bnode\b|\bnpm\b", SHEB, "shebang через sh -c"),
]
DEBUG2 = "Другий збій {} підряд. Стоп: назви гіпотезу одним реченням і що її спростує — не повторюй команду наосліп."
DEBUG3 = "Збій {} уже {}-й підряд. Стоп-правило (ідея obra/systematic-debugging «≥3: stop and question the architecture»): не наступна спроба, а інший підхід або питання користувачу."
WINDOW = 3600
def classify(cmd, text, is_error):
    if not is_error and VIEWER.match(cmd): return None, None
    for cls, rx in SIGS:
        if cls not in ENV_CLASSES: continue
        if not is_error:
            if cls not in SOFT_OK: continue
            rx = SOFT_RX[cls]
        m = rx.search(text)
        if m:
            s = text.rfind("\n", 0, m.start()) + 1; e = text.find("\n", m.end())
            return cls, text[s: e if e != -1 else len(text)].strip()[:200]
    return None, None
def lookup(cls, line, cmd, secs):
    for c, rl, rc, rh, label in INDEX:
        if c != cls or not re.search(rl, line): continue
        if rc and not re.search(rc, cmd): continue
        for s in secs:
            if re.search(rh, s["h"]): return s, label
    return None, None
def recipe_line(sec):
    pri = re.compile(r"ОБХІД|Обхід|обхід|Рішення|Рецепт|рецепт", )
    for i, l in enumerate(sec["body"]):
        if pri.search(l) and len(l.strip()) > 15: return sec["n"] + 1 + i, l.strip()
    for i, l in enumerate(sec["body"]):
        if l.strip() and not l.startswith("TAGS:") and not l.startswith("—"): return sec["n"] + 1 + i, l.strip()
    return sec["n"], sec["h"]
def render(label, sec):
    ln, txt = recipe_line(sec)
    return f"Збій «{label}» — у TROUBLES є обхід: {sec['h'][:60]} (TROUBLES:{ln}) ↳ {re.sub(chr(32)+'+', ' ', txt)[:150]}"
def decide(cmd, text, is_error, secs):
    cls, line = classify(cmd, text, is_error)
    if not cls: return None, None, None
    sec, label = lookup(cls, line, cmd, secs)
    return cls, (render(label, sec) if sec else None), line
def main():
    t0 = time.time()
    try: d = json.load(sys.stdin)
    except Exception: return
    if d.get("tool_name") != "Bash": return
    ev = d.get("hook_event_name", ""); cmd = (d.get("tool_input") or {}).get("command", "")
    if ev == "PostToolUseFailure": text, err = str(d.get("error", "")), True
    else:
        tr = d.get("tool_response"); err = False
        text = (str(tr.get("stdout", "")) + "\n" + str(tr.get("stderr", ""))) if isinstance(tr, dict) else str(tr or "")
    cls, line = classify(cmd, text, err)
    if not cls: return                                  # швидкий вихід: TROUBLES не читаємо
    sf = STATE_DIR + "state-" + re.sub(r"\W", "", d.get("session_id", "x")) + ".json"
    try: st = json.load(open(sf))
    except Exception: st = {}
    now = time.time(); hist = [t for t in st.get(cls, []) if now - t <= WINDOW] + [now]; st[cls] = hist
    try: json.dump(st, open(sf, "w"))
    except Exception: pass
    secs = parse(open(TROUBLES, encoding="utf-8").read())
    _, msg, _ = decide(cmd, text, err, secs)
    parts = []
    if msg: parts.append(msg)
    if len(hist) == 2: parts.append(DEBUG2.format(cls))
    elif len(hist) >= 3: parts.append(DEBUG3.format(cls, len(hist)))
    if not parts: return
    print(json.dumps({"hookSpecificOutput": {"hookEventName": ev or "PostToolUse", "additionalContext": " ".join(parts)}}, ensure_ascii=False))
if __name__ == "__main__": main()
