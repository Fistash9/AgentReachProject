"""Спільний код бектесту «пошук обходу» (2026-10-28): читання calls2.jsonl, класифікація помилок Bash."""
import json, re, collections
TMP = "/data/data/com.termux/files/usr/tmp/obhid/"

CUTOFF = "2026-10-28T07:45:58.278Z"   # початок цього завдання: далі в журналах — власна розробка бектесту (не рахуємо)
def load_calls():
    rows = [json.loads(l) for l in open(TMP + "calls2.jsonl", encoding="utf-8")]
    rows = [r for r in rows if (r.get("ts") or "") < CUTOFF]
    seen, out = set(), []
    for r in rows:
        if r["id"] in seen:      # відновлені/форкнуті сесії дублюють tool_use_id
            continue
        seen.add(r["id"]); out.append(r)
    return rows, out

def exitcode(r):
    m = re.match(r"Exit code (\d+)", r.get("head", ""))
    return int(m.group(1)) if m else None

def body_lines(r):
    ls = r.get("head", "").splitlines()
    if ls and ls[0].startswith("Exit code"):
        ls = ls[1:]
    return [l for l in ls if l.strip()]

GATE_FIRST = re.compile(r"^(PreToolUse:\w+ hook error|Заблоковано|Коміт заборонено|Платний виклик|git push заборонено|Ворота|\S+ заборонено|proc-guard|APPROVAL REQUIRED|UNMET GATES)")
def kind(r):
    """Тип is_error-результату."""
    h = r.get("head", ""); bl = body_lines(r); first = bl[0] if bl else ""
    if GATE_FIRST.match(first) or "hook error:" in first: return "GATE"
    if "auto mode classifier" in h or "classifier gave no verdict" in h: return "CLASSIFIER"
    if "doesn't want to proceed" in h or "Request interrupted" in h or "requires approval" in h: return "USERREJECT"
    if "<tool_use_error>" in h: return "TOOLERR"
    if exitcode(r) == 1 and not bl: return "EMPTY1"
    return "REAL"

# сигнатури збою: (клас, regex); для hard — будь-де в тексті, для soft — лише якорені на початок рядка
SIGS = [
 ("SHLIB",      re.compile(r"error while loading shared libraries")),
 ("BADINTERP",  re.compile(r"bad interpreter")),
 ("ENV_NOFILE", re.compile(r"/usr/bin/env: (?:No such file|[\"']?\S+[\"']?: No such file)")),
 ("NOTFOUND",   re.compile(r"(?:^|: )(?:line \d+: |\d+: )?[\w./+@-]+: (?:command )?not found", re.M)),
 ("SHSYNTAX",   re.compile(r"unexpected EOF while looking|syntax error near|unexpected token")),
 ("TRACEBACK",  re.compile(r"^Traceback \(most recent call last\):", re.M)),
 ("PERM",       re.compile(r"^\S[^\n]*: (?:Permission denied|Operation not permitted)", re.M)),
 ("NOFILE",     re.compile(r"^(?:\S+: )?(?:ls|cat|wc|tail|head|sed|cp|mv|rm|cd|grep|find|stat|dirname|which|cannot access|cannot open)[^\n]*(?:No such file or directory|no \S+ in \()", re.M)),
 ("USAGE",      re.compile(r"unrecognized option|invalid option|unrecognized arguments|^usage: ", re.M)),
 ("NET",        re.compile(r"curl: \(\d+\)|Could not resolve|Connection refused|HTTPSConnectionPool|Error reading response")),
 ("TIMEOUT",    re.compile(r"^Terminated|timed out|Killed", re.M)),
 ("NPM",        re.compile(r"npm ERR!|npm error|\bE404\b|ERESOLVE")),
 ("PKG",        re.compile(r"Unable to locate package")),
 ("GIT",        re.compile(r"^fatal: |^error: pathspec", re.M)),
]
SOFT_RX = {
 "SHLIB":     re.compile(r"^\S+: error while loading shared libraries", re.M),
 "BADINTERP": re.compile(r"^\S+: (?:\S+: ){1,2}bad interpreter", re.M),
 "ENV_NOFILE":re.compile(r"^(?:/\S+/)?(?:ba)?sh: (?:line \d+: )?/usr/bin/env: No such file", re.M),
 "NOTFOUND":  re.compile(r"^(?:/\S+/)?(?:ba)?sh: (?:line \d+: |\d+: )?\S+: (?:command )?not found", re.M),
 "SHSYNTAX":  re.compile(r"^(?:/\S+/)?bash: .*(?:unexpected EOF|syntax error)", re.M),
 "TRACEBACK": re.compile(r"^Traceback \(most recent call last\):", re.M),
 "PERM":      re.compile(r"^(?:(?:/\S+/)?(?:ba)?sh: line \d+: \S+: Permission denied|(?:cp|ln|mv|cat|mkdir|touch|rm): [^\n]*Permission denied)", re.M),
 "NOFILE":    re.compile(r"^(?:ls|cat|wc|tail|head|sed|cp|mv|rm|stat|dirname|cd|grep|find): [^\n]*No such file or directory", re.M),
}
SOFT_OK = {"SHLIB", "BADINTERP", "ENV_NOFILE", "NOTFOUND", "SHSYNTAX", "TRACEBACK", "PERM", "NOFILE"}
VIEWER = re.compile(r"^\s*(?::\s*\"[^\"]*\"\s*&&\s*)?(?:cd [^&;]+(?:&&|;)\s*)?(?:cat|sed|head|tail|grep|command grep|awk|less|nl|wc|git (?:show|log|diff|grep)|echo)\b")

def text_of(r):
    return (r.get("head", "") + "\n" + r.get("tail", "") + "\n" + r.get("stderr", ""))

def signature(r):
    """(клас, рядок) або (None, None). Для is_error — будь-яка сигнатура; для успішних — лише «м'які» і не з вигляду файлів."""
    t = text_of(r)
    hard = r.get("is_error")
    if not hard and VIEWER.match(r["brief"]):
        return None, None
    for cls, rx in SIGS:
        if not hard:
            if cls not in SOFT_OK: continue
            rx = SOFT_RX[cls]
        m = rx.search(t)
        if m:
            s = t.rfind("\n", 0, m.start()) + 1; e = t.find("\n", m.end())
            return cls, t[s: e if e != -1 else len(t)].strip()[:200]
    return None, None
