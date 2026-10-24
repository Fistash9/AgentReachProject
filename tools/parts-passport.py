#!/usr/bin/env python3
"""Паспорт частин системи: мета · зв'язки · виклики · останній ужиток — одна таблиця.

Навіщо (запит користувача 2026-10-23: «правила для виклику кожного із інструментів… більшість лежить і ми
забуваємо ними користуватись» + «що можна глобально комбінувати, щоб не дублювати задачі»): замість правила
на кожен інструмент — один паспорт. Вузли trees/yakist-roboty-agentiv.md Q4 «ОБ'ЄДНАННЯ» (1) і Q3 (done when:
перелік з числом викликів за журналами). Перший крок; діри потім підуть у check-links і в рішення користувача.

Частини: tools/* · .claude/hooks/*.py|sh|mjs · .claude/skills/*/SKILL.md · відкриті вузли trees/*.md і
trees/g2/*.md ([ ], [>], [?]) · MCP-інструменти з журналів (викликані або оголошені в deferred-списках) ·
пісочниці ~/sandbox-* (тека, розмір, дата).

Як рахує (лише факти, без оцінок «прибрати»):
  - виклики — журнали сесій ~/.claude/projects/<проєкт>/*.jsonl (основні) і */subagents/*.jsonl (окремо);
    tool_use дедуплікується за id (у журналі записи задвоюються — Q3 evidence 03.10).
    Скрипт tools/X рахується, лише коли Bash-команда ЙОГО ЗАПУСКАЄ (python3/bash/./ шлях), не grep/cat/sed.
    Скіл — tool_use Skill (input.skill) + <command-name>/скіл</command-name>. MCP — ім'я tool_use.
  - хуки: у журналі сесії ім'я хука не пишеться (лише подія, напр. «Stop») — тому спрацювання беремо з
    власних логів хуків у .claude/logs/ (ім'я лога — з коду хука); хук без лога → «не логуються».
  - зв'язки — хто згадує частину: вузли trees/, RULES.md, RULES-WHY.md, скрипти tools/, хуки, скіли
    (згадка в самій частині не рахується).
Перевикористано: tools/project-audit.py — inventory() (реєстрація хуків у settings.local.json і загальний
лічильник згадок project-audit); розбір вузлів — за .unlazy/q6/l2.py (той самий regex і поля мети/зв'язків).

Запуск:  python3 tools/parts-passport.py [--out-dir .unlazy/passport]
"""

import argparse
import ast
import bisect
import glob
import importlib.util
import json
import os
import re
import shlex
import time
from collections import defaultdict
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOME = os.path.expanduser("~")
# харнес замінює на «-» кожен не-алфавітно-цифровий символ шляху (і «/», і «.» у com.termux)
JDIR = os.path.join(HOME, ".claude", "projects", re.sub(r"[^A-Za-z0-9]", "-", ROOT))
LOGS = os.path.join(ROOT, ".claude", "logs")
# хук лише ЧИТАЄ цей лог (пише statusline-cost.py) — не його спрацювання
READ_ONLY_LOGS = {"cost-nudge-hook.py": {"session-cost.jsonl"}}

# з .unlazy/q6/l2.py
NODE_RE = re.compile(r"^(\s*)- \[([ >?x~])\] ([A-Z]\d+(?:\.\d+)*)\b(.*)")
GOAL_RE = re.compile(r"ідея користувача|запит|UP:|звідки|запит користувача|користувач \d{4}|ціль:|служить|навіщо", re.I)
LINK_RE = re.compile(r"будувати на|\bДО |ПІСЛЯ|ЗВ'ЯЗАНЕ|ЗВ’ЯЗАНЕ|служить|залежить|впливає|зв'язан", re.I)
DATE_RE = re.compile(r"\b(20\d\d-[01]\d-[0-3]\d)")


def read(p):
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def rel(p):
    return os.path.relpath(p, ROOT)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ------------------------------------------------------------------ мета з шапки файлу
def header_goal(path):
    src = read(path)
    if path.endswith(".py"):
        try:
            doc = ast.get_docstring(ast.parse(src))
        except (SyntaxError, ValueError):
            doc = None
        if doc and doc.strip():
            return "docstring: " + doc.strip().splitlines()[0][:110]
    lines = src.splitlines()
    for ln in lines[:15]:
        s = ln.strip()
        if s.startswith("#!") or not s:
            continue
        if s.startswith(("#", "//")):
            t = s.lstrip("#/ ").strip()
            if len(t) > 8:
                return "коментар у шапці: " + t[:110]
        else:
            break
    return None


# ------------------------------------------------------------------ частини
def collect_parts():
    parts = []
    tdir = os.path.join(ROOT, "tools")
    for name in sorted(os.listdir(tdir)):
        p = os.path.join(tdir, name)
        if name.startswith("__") or name.startswith("."):
            continue
        if os.path.isdir(p):
            pys = sorted(glob.glob(os.path.join(p, "*.py")))
            main = os.path.join(p, name + ".py")
            cand = ([main] if main in pys else []) + [x for x in pys if x != main]
            goal = next((g for g in (header_goal(x) for x in cand) if g), None)
            parts.append({"type": "tool", "name": name + "/", "path": rel(p), "goal": goal, "is_dir": True})
        else:
            parts.append({"type": "tool", "name": name, "path": rel(p), "goal": header_goal(p), "is_dir": False})
    for p in sorted(glob.glob(os.path.join(ROOT, ".claude", "hooks", "*"))):
        if os.path.isfile(p) and p.endswith((".py", ".sh", ".mjs")):
            parts.append({"type": "hook", "name": os.path.basename(p), "path": rel(p), "goal": header_goal(p)})
    for p in sorted(glob.glob(os.path.join(ROOT, ".claude", "skills", "*", "SKILL.md"))):
        name = os.path.basename(os.path.dirname(p))
        m = re.search(r"^description:\s*(.+)$", read(p), re.M)
        goal = ("SKILL.md description: " + m.group(1).strip()[:110]) if m else None
        parts.append({"type": "skill", "name": name, "path": rel(p), "goal": goal})
    return parts


def parse_nodes():
    """Вузли за .unlazy/q6/l2.py: заголовок + тіло до наступного вузла або «#»-заголовка."""
    files = sorted(glob.glob(os.path.join(ROOT, "trees", "*.md")) + glob.glob(os.path.join(ROOT, "trees", "g2", "*.md")))
    nodes, segs = [], []
    for f in files:
        if "baton-audit" in f:  # як у l2.py: знімок аудиту, не дерево
            continue
        lines = read(f).split("\n")
        cur, pre = None, []
        for i, line in enumerate(lines, 1):
            m = NODE_RE.match(line)
            if m:
                if cur:
                    nodes.append(cur)
                cur = {"file": rel(f), "line": i, "st": m.group(2), "id": m.group(3),
                       "title": m.group(4).strip()[:70], "text": [line]}
            elif cur is not None:
                if line.startswith("#"):
                    nodes.append(cur)
                    cur = None
                    pre.append(line)
                else:
                    cur["text"].append(line)
            else:
                pre.append(line)
        if cur:
            nodes.append(cur)
        segs.append({"label": rel(f), "kind": "дерева", "owner": None, "text": "\n".join(pre)})
    return nodes, segs


# ------------------------------------------------------------------ журнали
TOOL_RUNNERS = {"python3", "python", "bash", "sh", "node", "pypy3"}
SEG_SPLIT = re.compile(r"\|\||&&|[;|&\n()`]|\$\(")
HEREDOC = re.compile(r"<<-?[ \t]*(['\"]?)(\w+)\1([^\n]*)\n.*?\n[ \t]*\2[ \t]*(?=\n|$)", re.S)
PREFIX = {"time", "nohup", "exec", "env", "command", "then", "do", "else", "!", "{", "}", "if", "while"}


def scripts_in_command(cmd, tool_names):
    """Які tools/X ЗАПУСКАЄ Bash-команда (не читає/греп-ає). Повертає множину назв частин."""
    found, in_tools = set(), False
    # тіло heredoc — дані, не команди: «cat >> TROUBLES.md <<'EOF' … python3 tools/x.py … EOF» — це текст запису,
    # а не запуск (перевірка 3, 2026-10-24: 8 хибних «запусків» check-links/trees-index/watch-deepseek/hooks-smoke)
    cmd = HEREDOC.sub(lambda m: m.group(3), cmd)
    for seg in SEG_SPLIT.split(cmd):
        try:
            toks = shlex.split(seg)
        except ValueError:
            toks = seg.split()
        i = 0
        while i < len(toks):
            t = toks[i]
            if re.match(r"^[A-Za-z_]\w*=", t) or t in PREFIX:
                i += 1
            elif t == "timeout":
                i += 1
                while i < len(toks) and (toks[i].startswith("-") or re.match(r"^\d+[smh]?$", toks[i])):
                    i += 1
            else:
                break
        rest = toks[i:]
        if not rest:
            continue
        if rest[0] == "cd":
            in_tools = len(rest) > 1 and rest[1].rstrip("/").endswith("tools")
            continue
        target = rest[0]
        if os.path.basename(target) in TOOL_RUNNERS:
            j = 1
            while j < len(rest) and rest[j].startswith("-"):
                if rest[j] in ("-c", "-m", "-e"):
                    j = None
                    break
                j += 1
            if j is None or j >= len(rest):
                continue
            target = rest[j]
        m = re.search(r"(?:^|/)tools/([^/\s]+)(?:/[^\s]*)?$", target)
        if m and (m.group(1) in tool_names or m.group(1) + "/" in tool_names):
            found.add(m.group(1) if m.group(1) in tool_names else m.group(1) + "/")
        elif in_tools and "/" not in target.lstrip("./") and target.lstrip("./") in tool_names:
            found.add(target.lstrip("./"))
    return found


def local_date(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone().strftime("%Y-%m-%d")
    except (ValueError, AttributeError):
        return ""


def scan_journals(tool_names, skill_names):
    main = sorted(glob.glob(os.path.join(JDIR, "*.jsonl")))
    sub = sorted(glob.glob(os.path.join(JDIR, "*", "subagents", "*.jsonl")))
    stat = defaultdict(lambda: {"calls": 0, "sessions": set(), "last": "", "sub_calls": 0, "sub_last": ""})
    mcp_declared, seen = set(), set()
    cmd_re = re.compile(r"<command-name>/?([\w:-]+)</command-name>")
    for is_sub, files in ((False, main), (True, sub)):
        for path in files:
            sid = os.path.basename(path)[:8]
            with open(path, encoding="utf-8", errors="replace") as f:
                for line in f:
                    tu, dfr, cmn = '"tool_use"' in line, '"deferred_tools' in line, "<command-name>" in line
                    if not (tu or dfr or cmn):
                        continue
                    try:
                        d = json.loads(line)
                    except ValueError:
                        continue
                    keys = []
                    if d.get("type") == "assistant":
                        for c in (d.get("message") or {}).get("content") or []:
                            if not isinstance(c, dict) or c.get("type") != "tool_use":
                                continue
                            if c.get("id") in seen:
                                continue
                            seen.add(c.get("id"))
                            n, inp = c.get("name", ""), c.get("input") or {}
                            if n.startswith("mcp__"):
                                keys.append(("mcp", n))
                            elif n == "Skill":
                                s = str(inp.get("skill", "")).lstrip("/")
                                if s in skill_names:
                                    keys.append(("skill", s))
                            elif n == "Bash":
                                for t in scripts_in_command(str(inp.get("command", "")), tool_names):
                                    keys.append(("tool", t))
                    elif d.get("type") == "attachment":
                        a = d.get("attachment") or {}
                        if a.get("type") == "deferred_tools_record":
                            mcp_declared |= {e.get("name", "") for e in a.get("entries") or [] if str(e.get("name", "")).startswith("mcp__")}
                        elif a.get("type") == "deferred_tools_delta":
                            mcp_declared |= {x for x in a.get("addedNames") or [] if str(x).startswith("mcp__")}
                    elif d.get("type") == "user" and cmn and d.get("uuid") not in seen:
                        seen.add(d.get("uuid"))
                        msg = (d.get("message") or {}).get("content")
                        txt = msg if isinstance(msg, str) else json.dumps(msg, ensure_ascii=False)
                        for s in cmd_re.findall(txt):
                            if s in skill_names:
                                keys.append(("skill", s))
                    if not keys:
                        continue
                    day = local_date(d.get("timestamp", ""))
                    for k in keys:
                        st = stat[k]
                        if is_sub:
                            st["sub_calls"] += 1
                            st["sub_last"] = max(st["sub_last"], day)
                        else:
                            st["calls"] += 1
                            st["sessions"].add(sid)
                            st["last"] = max(st["last"], day)
    return stat, mcp_declared, len(main), len(sub)


# ------------------------------------------------------------------ логи хуків
def hook_logs(hook_path):
    name = os.path.basename(hook_path)
    src = read(os.path.join(ROOT, hook_path))
    named = sorted(set(re.findall(r"([\w.-]+\.(?:log|jsonl|json))\b", src)) - READ_ONLY_LOGS.get(name, set()))
    named = [n for n in named if not n.endswith(".json") or "state" in n]
    have = [n for n in named if os.path.isfile(os.path.join(LOGS, n))]
    missing = [n for n in named if n not in have and ("logs/" + n in src or '"' + n + '"' in src)]
    if not have:
        note = ("лог названо в коді, файла нема: " + ", ".join(missing)) if missing else "спрацювання не логуються"
        return None, None, note
    calls, last = 0, ""
    for n in have:
        p = os.path.join(LOGS, n)
        if n.endswith(".json"):
            last = max(last, datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d"))
            continue
        for line in open(p, encoding="utf-8", errors="replace"):
            if line.strip():
                calls += 1
                ds = DATE_RE.findall(line)
                if ds:
                    last = max(last, max(ds))
    if all(n.endswith(".json") for n in have):
        return None, last or None, "стан-файл " + ", ".join(have) + " (лише дата зміни; кількість не вимірюється)"
    return calls, last or None, "лог: " + ", ".join(have) + " (записів у лозі, не сесій)"


# ------------------------------------------------------------------ зв'язки
def build_corpus(nodes, tree_segs, parts_by_path):
    segs = list(tree_segs)
    for n in nodes:
        segs.append({"label": f"{n['file']}:{n['id']}", "kind": "дерева", "owner": ("node", n["key"]),
                     "text": "\n".join(n["text"])})
    for f, kind in (("RULES.md", "RULES"), ("RULES-WHY.md", "RULES-WHY")):
        segs.append({"label": f, "kind": kind, "owner": None, "text": read(os.path.join(ROOT, f))})
    files = []
    for p in glob.glob(os.path.join(ROOT, "tools", "**", "*"), recursive=True):
        if os.path.isfile(p) and p.endswith((".py", ".sh", ".md")) and "__pycache__" not in p:
            files.append((p, "скрипти"))
    for p in glob.glob(os.path.join(ROOT, ".claude", "hooks", "*")):
        if os.path.isfile(p) and p.endswith((".py", ".sh", ".mjs")):
            files.append((p, "хуки"))
    for p in glob.glob(os.path.join(ROOT, ".claude", "skills", "**", "*"), recursive=True):
        if os.path.isfile(p) and p.endswith((".md", ".py", ".sh")):
            files.append((p, "скіли"))
    for p, kind in sorted(files):
        r = rel(p)
        owner = parts_by_path.get(r)
        if owner is None:  # файл усередині теки-частини (tools/claimcheck/x.py, skills/x/…)
            for pp, key in parts_by_path.items():
                base = os.path.dirname(pp) if pp.endswith("SKILL.md") else pp
                if r.startswith(base.rstrip("/") + "/"):
                    owner = key
        segs.append({"label": r, "kind": kind, "owner": owner, "text": read(p)})
    starts, buf, pos = [], [], 0
    for s in segs:
        starts.append(pos)
        buf.append(s["text"])
        pos += len(s["text"]) + 2
    return segs, starts, "\n\n".join(buf)


def mention_pattern(row, skill_names, hook_stems):
    t, n = row["type"], row["name"]
    if t == "tool":
        stem = n.rstrip("/")
        stem = re.sub(r"\.(py|sh)$", "", stem)
        if stem in skill_names or stem in hook_stems:
            return re.escape(n) if not row.get("is_dir") else re.escape(stem) + r"/"
        return r"(?<![\w-])" + re.escape(stem) + r"(?:\.py|\.sh)?(?![\w-])"
    if t == "hook":
        stem = re.sub(r"(-hook)?\.(py|sh|mjs)$", "", n)
        return r"(?<![\w-])" + re.escape(stem) + r"(?:-hook)?(?:\.py|\.sh|\.mjs)?(?![\w-])"
    if t == "skill":
        return r"(?<![\w.-])" + re.escape(n) + r"(?![\w-]|\.py)"
    if t == "node":
        return r"(?<![\w.])" + re.escape(row["id"]) + r"(?![\w]|\.\d)"
    if t == "mcp":
        short = n.split("__")[-1]
        alts = [re.escape(n)] + ([re.escape(short)] if "_" in short and len(short) >= 6 else [])
        return r"(?<![\w])(?:" + "|".join(alts) + r")(?![\w])"
    if t == "sandbox":
        return re.escape(n) + r"(?![\w-])"
    return None


def links(row, pat, segs, starts, corpus):
    hits, kinds = [], defaultdict(int)
    seen = set()
    for m in re.finditer(pat, corpus):
        i = bisect.bisect_right(starts, m.start()) - 1
        if i in seen:
            continue
        seen.add(i)
        s = segs[i]
        if s["owner"] == row["key"]:
            continue
        hits.append(s["label"])
        kinds[s["kind"]] += 1
    return len(hits), hits[:3], dict(kinds)


# ------------------------------------------------------------------ main
def dir_stats(p):
    size, newest = 0, os.path.getmtime(p)
    for base, dirs, files in os.walk(p):
        for f in files:
            try:
                st = os.lstat(os.path.join(base, f))
            except OSError:
                continue
            size += st.st_size
            newest = max(newest, st.st_mtime)
    return size, datetime.fromtimestamp(newest).strftime("%Y-%m-%d")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=os.path.join(ROOT, ".unlazy", "passport"))
    a = ap.parse_args()
    t0 = time.time()

    pa = load_module("project_audit", os.path.join(ROOT, "tools", "project-audit.py"))
    inv = pa.inventory(ROOT)
    not_reg_local = set(inv["hooks"]["files_not_registered"])
    glob_raw = read(os.path.join(HOME, ".claude", "settings.json"))
    glob_reg = {os.path.basename(x) for x in re.findall(r"[\w./-]+\.(?:py|sh|js|mjs)", glob_raw)}

    rows = collect_parts()
    tool_names = {r["name"] for r in rows if r["type"] == "tool"}
    skill_names = {r["name"] for r in rows if r["type"] == "skill"}
    hook_stems = {re.sub(r"(-hook)?\.(py|sh|mjs)$", "", r["name"]) for r in rows if r["type"] == "hook"}

    stat, mcp_declared, n_main, n_sub = scan_journals(tool_names, skill_names)

    for r in rows:
        r["key"] = (r["type"], r["name"].rstrip("/") if r["type"] != "tool" else r["name"])
        if r["type"] == "tool":
            s = stat.get(("tool", r["name"]))
            r["audit_mentions"] = inv["tools"].get(r["name"])
        elif r["type"] == "skill":
            s = stat.get(("skill", r["name"]))
            r["audit_mentions"] = inv["skills"].get(r["name"])
        else:
            s = None
        if r["type"] in ("tool", "skill"):
            r["calls"] = s["calls"] if s else 0
            r["sessions"] = len(s["sessions"]) if s else 0
            r["last"] = (s["last"] or None) if s else None
            r["sub_calls"] = s["sub_calls"] if s else 0
            r["calls_source"] = "журнали сесій"
            r["wired"] = None
        else:  # hook
            calls, last, note = hook_logs(r["path"])
            r["calls"], r["sessions"], r["last"], r["sub_calls"], r["calls_source"] = calls, None, last, None, note
            w = []
            if r["name"] not in not_reg_local:
                w.append("settings.local.json")
            if r["name"] in glob_reg:
                w.append("~/.claude/settings.json")
            r["wired"] = " + ".join(w) if w else "ні"

    mcp_names = sorted({k[1] for k in stat if k[0] == "mcp"} | mcp_declared)
    rules_text = read(os.path.join(ROOT, "RULES.md")) + "\n" + read(os.path.join(ROOT, "RULES-WHY.md"))
    for n in mcp_names:
        s = stat.get(("mcp", n))
        server = n.split("__")[1] if n.count("__") >= 2 else n
        g = None
        for fname in ("RULES.md", "RULES-WHY.md"):
            for i, line in enumerate(read(os.path.join(ROOT, fname)).splitlines(), 1):
                if re.search(r"(?<![\w-])" + re.escape(server) + r"(?![\w-])", line, re.I):
                    g = f"{fname}:{i} згадує сервер {server}"
                    break
            if g:
                break
        rows.append({"type": "mcp", "name": n, "path": None, "goal": g, "key": ("mcp", n),
                     "calls": s["calls"] if s else 0, "sessions": len(s["sessions"]) if s else 0,
                     "last": (s["last"] or None) if s else None, "sub_calls": s["sub_calls"] if s else 0,
                     "calls_source": "журнали сесій" + ("" if s else " (лише оголошено в deferred-списку)"),
                     "wired": None})

    nodes, tree_segs = parse_nodes()
    by_id = {(n["file"], n["id"]): n for n in nodes}
    for n in nodes:
        n["key"] = ("node", f"{n['file']}:{n['id']}")
    for n in nodes:
        if n["st"] not in " >?":
            continue
        body = "\n".join(n["text"])
        g = None
        for i, line in enumerate(n["text"]):
            if GOAL_RE.search(line):
                g = f"рядок {n['line'] + i}: " + line.strip()[:100]
                break
        if not g and "." in n["id"]:
            par = by_id.get((n["file"], n["id"].rsplit(".", 1)[0]))
            if par and GOAL_RE.search("\n".join(par["text"])):
                g = f"через батька {par['id']}"
        ds = DATE_RE.findall(body)
        rows.append({"type": "node", "name": f"{n['file']}:{n['id']} [{n['st']}] {n['title']}", "id": n["id"],
                     "path": f"{n['file']}:{n['line']}", "goal": g, "key": n["key"],
                     "calls": None, "sessions": None, "last": max(ds) if ds else None, "sub_calls": None,
                     "calls_source": "н/з (вузол); останній ужиток = найпізніша дата в тілі вузла",
                     "wired": "поле зв'язків у тілі" if LINK_RE.search(body) else "поля зв'язків нема"})

    for p in sorted(glob.glob(os.path.join(HOME, "sandbox-*"))):
        if not os.path.isdir(p):
            continue
        size, newest = dir_stats(p)
        rows.append({"type": "sandbox", "name": os.path.basename(p), "path": p, "goal": None,
                     "key": ("sandbox", os.path.basename(p)), "calls": None, "sessions": None,
                     "last": newest, "sub_calls": None, "size_kb": size // 1024,
                     "calls_source": "н/з (лише тека, розмір, найновіша дата файлу)", "wired": None})

    # зв'язки
    parts_by_path = {r["path"]: r["key"] for r in rows if r["type"] in ("tool", "hook", "skill") and r["path"]}
    segs, starts, corpus = build_corpus(nodes, tree_segs, parts_by_path)
    for r in rows:
        pat = mention_pattern(r, skill_names, hook_stems)
        r["links"], r["link_examples"], r["link_kinds"] = links(r, pat, segs, starts, corpus)

    # мета з RULES-WHY / вузла, якщо в шапці нема (для скриптів і хуків)
    for r in rows:
        if r["type"] in ("tool", "hook") and not r["goal"]:
            pat = mention_pattern(r, skill_names, hook_stems)
            for i, line in enumerate(read(os.path.join(ROOT, "RULES-WHY.md")).splitlines(), 1):
                if re.search(pat, line):
                    r["goal"] = f"RULES-WHY.md:{i}"
                    break
            if not r["goal"]:
                ex = [x for x in r["link_examples"] if x.startswith("trees/")]
                if ex:
                    r["goal"] = f"згадка у вузлі {ex[0]}"

    for r in rows:
        r.pop("key", None)
        r.pop("is_dir", None)
        r.pop("id", None)
    elapsed = time.time() - t0

    # ---------------- вихід
    os.makedirs(a.out_dir, exist_ok=True)
    TYPES = [("tool", "Скрипти tools/"), ("hook", "Хуки .claude/hooks/"), ("skill", "Скіли .claude/skills/"),
             ("mcp", "MCP-інструменти (з журналів)"), ("node", "Відкриті вузли trees/"), ("sandbox", "Пісочниці ~/sandbox-*")]

    def order(r):
        return (0 if r["calls"] == 0 else 1, 0 if not r["goal"] else 1, -(r["calls"] or 0), r["name"])

    summary = {}
    for t, _ in TYPES:
        g = [r for r in rows if r["type"] == t]
        summary[t] = {"parts": len(g),
                      "zero_calls": sum(1 for r in g if r["calls"] == 0),
                      "calls_not_measured": sum(1 for r in g if r["calls"] is None),
                      "no_goal": sum(1 for r in g if not r["goal"]) if t != "sandbox" else None,
                      "no_links": sum(1 for r in g if r["links"] == 0)}
    data = {"journals": {"main": n_main, "subagents": n_sub, "dir": JDIR},
            "summary": summary, "parts": sorted(rows, key=lambda r: (r["type"], r["name"]))}
    with open(os.path.join(a.out_dir, "passport.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, sort_keys=True)

    def cell(x):
        return str(x).replace("|", "\\|").replace("\n", " ") if x not in (None, "") else "—"

    md = [f"# Паспорт частин — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
          f"Журнали: {n_main} основних + {n_sub} субагентних (*.jsonl). Згенеровано tools/parts-passport.py; "
          "«виклики» = основні журнали, «суб» = субагенти. Лише факти, без рекомендацій.", ""]
    for t, title in TYPES:
        g = sorted((r for r in rows if r["type"] == t), key=order)
        s = summary[t]
        md += [f"## {title} — {s['parts']} (0 викликів: {s['zero_calls']}, без мети: {s['no_goal']}, "
               f"без зв'язків: {s['no_links']})", "",
               "| назва | мета | зв'язки (к-ть: приклади) | виклики | сесій | суб | останній ужиток | підключено / примітка |",
               "|---|---|---|---|---|---|---|---|"]
        for r in g:
            note = r["wired"] or ""
            if t == "hook":
                note = f"{r['wired']}; {r['calls_source']}"
            if t == "sandbox":
                note = f"{r['size_kb']} КБ"
            lk = f"{r['links']}" + (": " + ", ".join(r["link_examples"]) if r["link_examples"] else "")
            md.append("| " + " | ".join(cell(x) for x in (
                r["name"], r["goal"] or "НЕМА", lk, r["calls"] if r["calls"] is not None else "не вимірюється",
                r["sessions"], r["sub_calls"], r["last"], note)) + " |")
        md.append("")
    with open(os.path.join(a.out_dir, "passport.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print(f"== ПАСПОРТ ЧАСТИН · журнали {n_main} основних + {n_sub} субагентних ==")
    for t, title in TYPES:
        s = summary[t]
        print(f"  {title:<32} частин {s['parts']:>3} | 0 викликів {s['zero_calls']:>3} | не вимірюється "
              f"{s['calls_not_measured']:>3} | без мети {s['no_goal'] if s['no_goal'] is not None else '—':>3} | "
              f"без зв'язків {s['no_links']:>3}")
    print(f"вихід: {rel(os.path.join(a.out_dir, 'passport.md'))}, passport.json")
    print(f"час прогону: {elapsed:.1f} с")


if __name__ == "__main__":
    main()
