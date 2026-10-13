#!/data/data/com.termux/files/usr/bin/python3
"""PreToolUse-хук (НЕ блокує): ворота 3 «перед правкою» (M11.3) + «Паспорт задачі».

Навіщо: сесія e3a33280 (trees/pam-yat-proyektu.md, M11 «evidence 2026-10-12»): план правки
tools/deepseek-search.py — без повного читання й без пошуку залежних (скіл deepseek-search
читає скрипт); знімки baton перенесено mv без пошуку читачів (їх читають 3 скрипти).
Правило є (RULES.md «Перед зміною того, як ми використовуємо…»: «Grep не замінює читання»),
але в момент дії не спрацьовує. verify-nudge-hook.py покриває лише захищені файли й
нагадує про звірку плану, а не про читання; trash-md-guard — лише rm і TRASH.md.

Три нагадування (кожне — раз на ключ за сесію, лише коли доказу в журналі немає):
  read   — Edit/Write наявного файлу в tools/, .claude/hooks/, .claude/skills/ без повного
           Read (без offset/limit) чи `cat` у журналі сесії, або без grep за його назвою.
  movers — Bash mv/rm файлу проєкту (не tmp, не .trash/) без grep за його назвою.
  passport — Edit/Write у trees/*.md додає новий вузол «- [ ] ID», а в доданому тексті
           немає «ціль:» / «звідки:» / «зв'язки:» / «UP:».
  siblings — правка хука .claude/hooks/X.py: перелік сусідніх хуків на ту саму подію (з
           settings.local.json) і рядків, де вони читають вхід (last_assistant_message,
           transcript_path, tool_input…). Ключ — хук + день. (2026-10-13: голос черги хибно
           спрацював, бо читав transcript_path, хоча number-claim-shadow-hook:358 уже брав
           last_assistant_message; 23.09 shlex-фікс двох хуків не дійшов до третього.)
Bash-правки (2026-10-13): python open(…,"w"), sed -i, > / >>, tee, cp у файл коду — теж
правка (до того ворота їх не бачили: за 12–13.10 лише 3 спрацювання, хоча правок було багато).
Лог: .claude/logs/edit-gate.log (сесія, ключ, час) — для підрахунку марних спрацювань.
Бектест: python3 <цей файл> --backtest <jsonl>. Будь-яка помилка — мовчки (fail-open).
"""
import json
import os
import re
import shlex
import sys
import time

PROJECT = "/data/data/com.termux/files/home/AgentReachProject"
LOG = os.path.join(PROJECT, ".claude", "logs", "edit-gate.log")
EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
CODE_DIRS = ("tools/", ".claude/hooks/", ".claude/skills/")
SAFE_PREFIXES = ("/data/data/com.termux/files/usr/tmp/", "/tmp/")
RE_NODE = re.compile(r"^\s*- \[ \] [A-Z]+\d[\w.]*\s", re.M)
RE_PASSPORT = re.compile(r"ціль:|звідки:|зв['’]яз\w*:|\bUP:", re.I)
RE_CODEPATH = re.compile(r"((?:tools|\.claude/hooks|\.claude/skills)/[\w./-]+\.(?:py|sh|md|mjs|json))")
INPUT_FIELDS = re.compile(r"last_assistant_message|transcript_path|stop_hook_active|tool_input|"
                          r"tool_name|session_id|hook_event_name|\"prompt\"")
SETTINGS = os.path.join(PROJECT, ".claude", "settings.local.json")
RE_MOVER = re.compile(r"(?:^|[;&|(]\s*|\bthen\s+|\bdo\s+)(mv|rm)\s+([^;&|\n]+)", re.M)


def rel(path, cwd=None):
    if not path:
        return None
    path = os.path.expanduser(path)
    if not os.path.isabs(path):
        path = os.path.join(cwd or PROJECT, path)
    path = os.path.normpath(path)
    if not path.startswith(PROJECT + os.sep):
        return None
    return path[len(PROJECT) + 1:]


def stem(r):
    b = os.path.basename(r)
    return os.path.splitext(b)[0] or b


class Evidence:
    """Що агент уже зробив у сесії: повні читання, grep-и, записи файлів."""

    def __init__(self):
        self.full_read, self.written, self.greps = set(), set(), []

    def add(self, name, inp):
        inp = inp or {}
        if name == "Read":
            r = rel(inp.get("file_path"))
            if r and not inp.get("offset") and not inp.get("limit"):
                self.full_read.add(r)
        elif name in EDIT_TOOLS:
            r = rel(inp.get("file_path"))
            if r and name == "Write":
                self.written.add(r)
        elif name == "Grep":
            self.greps.append(str(inp.get("pattern", "")))
        elif name == "Bash":
            cmd = str(inp.get("command", ""))
            if re.search(r"\b(grep|rg)\b", cmd):
                self.greps.append(cmd)
            for m in re.finditer(r"\bcat\s+([^\s|;&>]+)", cmd):
                r = rel(m.group(1))
                if r:
                    self.full_read.add(r)

    def grepped(self, r):
        s = stem(r)
        return any(s in g for g in self.greps)


RE_HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n(.*?)\n\1\b", re.S)
RE_PYASSIGN = re.compile(r"""(\w+)\s*=\s*['"]([^'"]+)['"]""")


def bash_written(cmd, cwd=None):
    """Файли коду, які Bash-команда справді записує (2026-10-13, v2: ціль — у тій самій
    частині команди; v1 плутала `sed -i trees/…; grep tools/x.py` із правкою tools/x.py)."""
    found = []

    def add(path):
        r = rel(path, cwd)
        if (r and r.startswith(CODE_DIRS) and r not in found and "/tests/" not in r
                and "__pycache__" not in r):
            found.append(r)
    # python-вставки: лише шлях, який відкривається на запис (прямо чи через змінну)
    for m in RE_HEREDOC.finditer(cmd):
        body = m.group(2)
        vars_ = dict(RE_PYASSIGN.findall(body))
        for w in re.finditer(r"open\(\s*([^,)]+)\s*,\s*['\"][wa]", body):
            arg = w.group(1).strip()
            path = arg.strip("'\"") if arg[:1] in "'\"" else vars_.get(arg)
            if path:
                add(path)
        for w in re.finditer(r"(\w+)\.write_text\(", body):
            if w.group(1) in vars_:
                add(vars_[w.group(1)])
    rest = RE_HEREDOC.sub(" ", cmd)
    for seg in re.split(r"&&|\|\||[;|\n]", rest):
        seg = seg.strip()
        if re.match(r"(?:sudo\s+)?sed\s+(?:-\w*\s+)*-i", seg) or re.match(r"sed\s+-i", seg):
            for c in RE_CODEPATH.findall(seg):
                add(c)
        for m in re.finditer(r"(?<![<>&\d])>>?\s*([^\s;&|]+)", seg):
            add(m.group(1))
        m = re.match(r"tee\s+(?:-a\s+)?([^\s;&|]+)", seg)
        if m:
            add(m.group(1))
        m = re.match(r"cp\s+(?:-\w+\s+)*\S+\s+([^\s;&|]+)$", seg)
        if m:
            add(m.group(1))
    return found


def hook_events():
    """{файл хука: [події]} з settings.local.json — робоче джерело реєстрації."""
    try:
        d = json.load(open(SETTINGS, encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    out = {}
    for ev_name, arr in (d.get("hooks") or {}).items():
        for a in arr or []:
            for h in a.get("hooks") or []:
                m = re.search(r"\.claude/hooks/([\w.-]+\.py)", str(h.get("command", "")))
                if m:
                    out.setdefault(m.group(1), []).append(ev_name)
    return out


def siblings_msg(r):
    """Текст: сусіди на ту саму подію і де вони читають вхід."""
    hook = os.path.basename(r)
    evs = hook_events()
    mine = evs.get(hook)
    if not mine:
        return None
    lines = []
    for other, oe in sorted(evs.items()):
        common = sorted(set(oe) & set(mine))
        if other == hook or not common:
            continue
        refs = []
        try:
            for i, l in enumerate(open(os.path.join(PROJECT, ".claude", "hooks", other),
                                       encoding="utf-8", errors="ignore"), 1):
                f = sorted(set(INPUT_FIELDS.findall(l)))
                if f and not l.lstrip().startswith("#"):
                    refs.append(f"{i}:{'/'.join(f)}")
        except OSError:
            continue
        lines.append(f"{other} [{','.join(common)}] " + (" ".join(refs[:4]) or "—"))
    if not lines:
        return None
    return (f"Сусіди {hook} на {','.join(mine)} — як вони читають вхід (перевір, чи вже не "
            "розв'язано те, що робиш): " + "; ".join(lines[:6]))


def check(name, inp, ev, cwd=None, exists=None, day=None):
    """[(ключ, текст нагадування)] для одного виклику інструмента."""
    out = []
    inp = inp or {}
    day = day or time.strftime("%Y-%m-%d")
    targets = []
    if name in EDIT_TOOLS:
        r = rel(inp.get("file_path"), cwd)
        if r:
            targets.append(r)
    elif name == "Bash":
        # лише наявні файли: створення нового — не правка (і шлях із тексту коментаря — не ціль)
        targets = [t for t in bash_written(str(inp.get("command", "")), cwd)
                   if exists is None and os.path.exists(os.path.join(PROJECT, t))
                   or exists is not None and t not in ev.written]
    for r in targets:
        if r.startswith(".claude/hooks/") and r.endswith(".py") and not (name == "Write" and not (
                exists if exists is not None else os.path.exists(os.path.join(PROJECT, r)))):
            msg = siblings_msg(r)
            if msg:
                out.append((f"siblings\t{r}\t{day}", msg))
        if name == "Bash" and r.startswith(CODE_DIRS) and r not in ev.written:
            miss = []
            if r not in ev.full_read:
                miss.append("файл не прочитано повністю (Read без offset/limit або cat)")
            if not ev.grepped(r):
                miss.append(f"залежних не шукано (grep -rn {stem(r)} tools .claude *.md)")
            if miss:
                out.append((f"read\t{r}", f"Ворота «перед правкою» ({r}, правка через Bash): "
                            + "; ".join(miss) + ". RULES.md «Перед зміною того, як ми "
                            "використовуємо…»: «Grep не замінює читання»."))
    if name in EDIT_TOOLS:
        r = rel(inp.get("file_path"), cwd)
        if not r:
            return out
        if exists is None:
            exists = os.path.exists(os.path.join(PROJECT, r))
        if r.startswith(CODE_DIRS) and exists and r not in ev.written:
            miss = []
            if r not in ev.full_read:
                miss.append("файл не прочитано повністю (Read без offset/limit або cat)")
            if not ev.grepped(r):
                miss.append(f"залежних не шукано (grep -rn {stem(r)} tools .claude *.md)")
            if miss:
                out.append((f"read\t{r}", f"Ворота «перед правкою» ({r}): " + "; ".join(miss)
                            + ". RULES.md «Перед зміною того, як ми використовуємо…»: "
                            "«Grep не замінює читання»."))
        if r.startswith("trees/") and r.endswith(".md"):
            new = inp.get("new_string") if name == "Edit" else inp.get("content")
            old = inp.get("old_string", "") if name == "Edit" else ""
            new, old = str(new or ""), str(old or "")
            added = len(RE_NODE.findall(new)) - len(RE_NODE.findall(old))
            if added > 0 and not RE_PASSPORT.search(new):
                out.append((f"passport\t{r}\t{len(new)}",
                            f"Паспорт задачі ({r}): новий вузол без рядків «ціль:» · «звідки:» · "
                            "«зв'язки:» (або UP:) — допиши, звідки запит і чому служить "
                            "(RULES.md «Формат взаємодії», пам'ять every-action-needs-project-goal)."))
    elif name == "Bash":
        cmd = str(inp.get("command", ""))
        for m in RE_MOVER.finditer(cmd):
            op = m.group(1)
            try:
                args = [a for a in shlex.split(m.group(2)) if not a.startswith("-")]
            except ValueError:
                continue
            if op == "mv" and len(args) > 1:
                args = args[:-1]
            for a in args:
                if a.startswith(SAFE_PREFIXES):
                    continue
                r = rel(a, cwd)
                if not r or r.startswith(".trash/") or ev.grepped(r):
                    continue
                out.append((f"movers\t{r}", f"Перед {op} {r}: хто його читає? "
                            f"grep -rn {stem(r)} tools .claude *.md — до перенесення "
                            "(випадок 12.10: знімки baton читають 3 скрипти)."))
    return out


def iter_tool_uses(path):
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if not isinstance(d, dict) or d.get("type") != "assistant":
                continue
            for x in (d.get("message") or {}).get("content") or []:
                if isinstance(x, dict) and x.get("type") == "tool_use":
                    yield d.get("timestamp", ""), x.get("name", ""), x.get("input") or {}


def seen_keys(sid):
    if not os.path.exists(LOG):
        return set()
    out = set()
    with open(LOG, encoding="utf-8", errors="ignore") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if p and p[0] == sid:
                out.add("\t".join(p[1:-1]))
    return out


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--backtest":
        return backtest(sys.argv[2])
    data = json.load(sys.stdin)
    name, inp = data.get("tool_name", ""), data.get("tool_input") or {}
    if name not in EDIT_TOOLS and name != "Bash":
        return
    ev = Evidence()
    tp = data.get("transcript_path")
    if isinstance(tp, str) and os.path.isfile(tp):
        for _, n, i in iter_tool_uses(tp):
            if n == name and i == inp:
                continue  # поточний виклик уже може бути в журналі
            ev.add(n, i)
    sid = data.get("session_id", "?")
    seen = seen_keys(sid)
    msgs = []
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    for key, msg in check(name, inp, ev, data.get("cwd")):
        if key in seen:
            continue
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"{sid}\t{key}\t{time.strftime('%Y-%m-%dT%H:%M:%S')}\n")
        msgs.append(msg)
    if msgs:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse", "additionalContext": "\n".join(msgs)}},
            ensure_ascii=False))


def backtest(path):
    ev, seen, n = Evidence(), set(), 0
    for ts, name, inp in iter_tool_uses(path):
        # Існування файлу в минулому невідоме: Write рахуємо новим файлом, Edit — наявним.
        for key, msg in check(name, inp, ev, exists=(name != "Write"), day=ts[:10]):
            if key not in seen:
                seen.add(key)
                n += 1
                print(f"{ts[11:19]}  {name:<5} {key.replace(chr(9), ' ')}")
        ev.add(name, inp)
    print(f"нагадувань: {n}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
