#!/usr/bin/env python3
"""Крок 0 аудиту проєкту (BACKLOG.md:295) — суто механічний інвентар.

Навіщо: аудит проєкту стоїть у BACKLOG «Активні» з 2026-09-24 і повторювався
в батні 7 разів (усі — ДУБЛЬ, baton-audit-2026-09-26.md:442). Цей скрипт не
міркує — він рахує те, що можна порахувати з файлів, і дає базову лінію, з
якою порівнювати наступні прогони.

Що міряє (усе з наявних файлів, без моделі й без мережі):
  1. Черга baton: пункти next у знімках .baton/history/pass-*.json —
     дублі, час життя, «носій vs якір», наявність у BACKLOG.
  2. Що є, але не використовується: хуки (файл vs реєстрація), скіли,
     tools/ (сироти без згадок), MCP-сервери.
  3. Застаріле: CONTEXT.md проти історії git, розсинхрон mtime/коміт,
     биті лінки (через наявний tools/check-links.py, свій код не плодимо).
  4. Дерево: статуси вузлів у trees/*.md і скільки вузлів без
     done-when/evidence (тобто без механізму).

Межі чесності: скрипт НЕ доводить, що щось «не потрібне» — він показує
відсутність згадок і відсутність реєстрації. «Не викликалось» з логів тут
не міряється: хуки не пишуть власного журналу, а журнали сесій стиснуті
(zstd) і мають інший формат — це окремий крок.

Запуск:  python3 tools/project-audit.py [--root <шлях>] [--json <шлях>]
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

MEHANIZM = re.compile(r"хук|скіл|скрипт|крок |guard|механізм", re.I)
PATHRE = re.compile(r"[A-Za-z0-9_./-]+\.(?:md|py|sh|js|json|yml|yaml|txt|jsonl)")


def norm(s):
    s = s.lower()
    s = re.sub(r"[`*_«»\"'()\[\],:;!?…—–-]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def sig(s, n=10):
    return " ".join(norm(s).split()[:n])


def similar(a, b):
    import difflib
    return difflib.SequenceMatcher(None, a, b).ratio()


def read_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


# ---------------------------------------------------------------- 1. черга
def queue(root):
    hist = os.path.join(root, ".baton", "history")
    snaps = []
    if os.path.isdir(hist):
        for name in os.listdir(hist):
            m = re.fullmatch(r"pass-(\d+)\.json", name)
            if m:
                snaps.append((int(m.group(1)), os.path.join(hist, name)))
    cur = os.path.join(root, ".baton", "baton.json")
    if os.path.isfile(cur):
        try:
            pc = json.load(open(cur, encoding="utf-8")).get("passCount")
        except (OSError, ValueError):
            pc = None
        if isinstance(pc, int):
            snaps.append((pc, cur))
    snaps.sort()

    passes = []
    for pc, path in snaps:
        try:
            d = json.load(open(path, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        passes.append({"pass": pc, "next": [str(x) for x in d.get("next", [])],
                       "openQuestions": [str(x) for x in d.get("openQuestions", [])]})

    items = []
    for p in passes:
        for text in p["next"]:
            items.append({"pass": p["pass"], "text": text, "sig": sig(text)})

    # кластери: одна позиція = один «пункт», навіть якщо переписаний словами
    clusters = []
    for it in items:
        placed = False
        for c in clusters:
            if it["sig"] == c["sig"] or similar(it["sig"], c["sig"]) >= 0.80:
                c["passes"].add(it["pass"])
                c["variants"].append(it["text"])
                placed = True
                break
        if not placed:
            clusters.append({"sig": it["sig"], "passes": {it["pass"]},
                             "variants": [it["text"]]})

    backlog = norm(read_text(os.path.join(root, "BACKLOG.md")))

    def shingle_hit(text, n):
        words = norm(text).split()
        for i in range(0, max(1, len(words) - n + 1)):
            if " ".join(words[i:i + n]) in backlog:
                return True
        return False

    def carrier(text):
        paths = PATHRE.findall(text)
        existing = [p for p in paths
                    if os.path.exists(os.path.join(root, p.lstrip("./")))]
        mech = bool(MEHANIZM.search(text))
        return {"paths": paths, "paths_exist": existing,
                "in_backlog_strict": shingle_hit(text, 8),
                "in_backlog_loose": shingle_hit(text, 4),
                "names_mechanism": mech,
                "has_carrier": bool(existing) or shingle_hit(text, 6)}

    for c in clusters:
        text = max(c["variants"], key=len)
        c.update(carrier(text))
        c["text"] = text
        c["lifetime"] = len(c["passes"])

    total = len(items)
    dups = sum(1 for c in clusters for _ in range(len(c["variants"]) - 1))
    alive = [c for c in clusters if c["lifetime"] >= 5]
    last_pass = passes[-1]["pass"] if passes else None

    def stats(group):
        if not group:
            return None
        ls = sorted(c["lifetime"] for c in group)
        return {"n": len(ls), "avg": round(sum(ls) / len(ls), 2),
                "median": ls[len(ls) // 2], "max": ls[-1]}

    with_c = [c for c in clusters if c["has_carrier"]]
    without_c = [c for c in clusters if not c["has_carrier"]]
    return {
        "passes": len(passes),
        "pass_range": [passes[0]["pass"], passes[-1]["pass"]] if passes else [],
        "items_total": total,
        "items_unique": len(clusters),
        "duplicates": dups,
        "dup_share": round(dups / total, 3) if total else None,
        "with_carrier": sum(1 for c in clusters if c["has_carrier"]),
        "without_carrier": sum(1 for c in clusters if not c["has_carrier"]),
        "lifetime_with_carrier": stats(with_c),
        "lifetime_without_carrier": stats(without_c),
        "died_with_carrier": sum(1 for c in with_c if last_pass not in c["passes"]),
        "died_without_carrier": sum(1 for c in without_c if last_pass not in c["passes"]),
        "carrier_share": round(sum(1 for c in clusters if c["has_carrier"]) / len(clusters), 3) if clusters else None,
        "in_backlog_share_loose": round(sum(1 for c in clusters if c["in_backlog_loose"]) / len(clusters), 3) if clusters else None,
        "in_backlog_share_strict": round(sum(1 for c in clusters if c["in_backlog_strict"]) / len(clusters), 3) if clusters else None,
        "stuck_5plus": [{"lifetime": c["lifetime"], "text": c["text"][:150]}
                        for c in sorted(alive, key=lambda x: -x["lifetime"])[:10]],
        "oldest_no_carrier": [{"lifetime": c["lifetime"], "text": c["text"][:150]}
                              for c in sorted((c for c in clusters if not c["has_carrier"]),
                                              key=lambda x: -x["lifetime"])[:10]],
    }


# ------------------------------------------------- 2. є, але не використовується
def inventory(root):
    out = {}
    hooks_dir = os.path.join(root, ".claude", "hooks")
    hook_files = []
    if os.path.isdir(hooks_dir):
        hook_files = sorted(f for f in os.listdir(hooks_dir)
                            if f.endswith((".py", ".sh", ".js")))
    settings_raw = read_text(os.path.join(root, ".claude", "settings.local.json"))
    try:
        settings = json.loads(settings_raw)
    except ValueError:
        settings = {}
    # Беремо СТРУКТУРУ, а не текст: раніше settings.count("PreToolUse") давав 1
    # (бо це ім'я ключа), хоч насправді там 4 матчери і 10 команд.
    per_event, registered = {}, set()
    for ev, arr in (settings.get("hooks") or {}).items():
        cmds = []
        for m in arr:
            for hk in m.get("hooks", []):
                cmds.append(hk.get("command", ""))
        for c in cmds:
            for f in re.findall(r"[\w./-]+\.(?:py|sh|js)", c):
                registered.add(os.path.basename(f))
        per_event[ev] = {"matchers": len(arr), "commands": len(cmds)}
    out["hooks"] = {
        "files": hook_files,
        "registered_commands": sum(v["commands"] for v in per_event.values()),
        "per_event": per_event,
        # «не зареєстрований» шукаємо по ВСЬОМУ settings, не лише по hooks:
        # statusline-cost.py підключений ключем statusLine (інакше хибний сигнал)
        "files_not_registered": [f for f in hook_files
                                 if f not in {os.path.basename(x) for x in
                                              re.findall(r"[\w./-]+\.(?:py|sh|js)", settings_raw)}],
        "registered_not_on_disk": sorted(f for f in registered
                                         if not os.path.exists(os.path.join(hooks_dir, f))),
    }

    def mentions(name, extra_dirs=()):
        pat = re.compile(re.escape(name))
        skip = os.path.join(root, ".claude", "logs")  # машинний вивід, не знання проєкту
        n = 0
        for base, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "__pycache__", ".trash")]
            if base.startswith(skip):
                continue
            for f in files:
                p = os.path.join(base, f)
                if os.path.basename(p) == name:
                    continue
                if not f.endswith((".md", ".py", ".sh", ".json", ".yml", ".yaml")):
                    continue
                n += len(pat.findall(read_text(p)))
        return n

    skills_dir = os.path.join(root, ".claude", "skills")
    skills = sorted(d for d in os.listdir(skills_dir)) if os.path.isdir(skills_dir) else []
    out["skills"] = {s: mentions(s) for s in skills}

    tools_dir = os.path.join(root, "tools")
    tool_files, tool_dirs = [], []
    if os.path.isdir(tools_dir):
        tool_files = sorted(f for f in os.listdir(tools_dir)
                            if os.path.isfile(os.path.join(tools_dir, f)) and not f.startswith("__"))
        tool_dirs = sorted(d for d in os.listdir(tools_dir)
                           if os.path.isdir(os.path.join(tools_dir, d)) and d != "__pycache__")
    out["tools"] = {t: mentions(t) for t in tool_files}
    out["tool_dirs"] = tool_dirs

    out["mcp_project"] = sorted((settings.get("mcpServers") or {}).keys())
    # MCP живе не в проєкті, а в профілі DSH — фіксуємо окремо
    dsh_home = os.environ.get("DSH_HOME", os.path.expanduser("~/.dsh"))
    prof, prof_mcp = os.path.join(dsh_home, "profiles"), []
    if os.path.isdir(prof):
        for name in sorted(os.listdir(prof)):
            p = os.path.join(prof, name, "cordis.patch.yml")
            if os.path.isfile(p):
                for s in re.findall(r"serverName:\s*([\w.-]+)", read_text(p)):
                    prof_mcp.append({"profile": name, "server": s})
    out["mcp_dsh_profiles"] = prof_mcp
    return out


# --------------------------------------------------------------- 3. застаріле
def stale(root):
    out = {}
    def git(*args):
        try:
            r = subprocess.run(["git", "-C", root, *args], capture_output=True,
                               text=True, timeout=60)
            return r.stdout.strip() if r.returncode == 0 else None
        except (OSError, subprocess.SubprocessError):
            return None

    ctx = os.path.join(root, "CONTEXT.md")
    last = git("log", "-1", "--format=%cI", "--", "CONTEXT.md")
    out["context_last_commit"] = last
    # Рахуємо від САМОГО коміту CONTEXT (sha..HEAD), а не --since=<дата>: --since
    # включав і його власний коміт, даючи 44 замість 43.
    last_sha = git("log", "-1", "--format=%H", "--", "CONTEXT.md")
    out["context_last_sha"] = last_sha
    if last_sha:
        after = git("rev-list", "--count", f"{last_sha}..HEAD")
        out["commits_after_context"] = int(after) if after and after.isdigit() else None

    hist = git("rev-list", "--count", "HEAD")
    out["commits_total"] = int(hist) if hist and hist.isdigit() else None

    skew = []
    for f in ("RULES.md", "CONTEXT.md", "BACKLOG.md", "TROUBLES.md", "WEEKLY.md"):
        p = os.path.join(root, f)
        if not os.path.isfile(p):
            continue
        mtime = datetime.fromtimestamp(os.path.getmtime(p), timezone.utc)
        lastc = git("log", "-1", "--format=%cI", "--", f)
        uncommitted = git("status", "--porcelain", "--", f)
        skew.append({"file": f,
                     "mtime_days_ago": (datetime.now(timezone.utc) - mtime).days,
                     "last_commit": lastc,
                     "uncommitted": bool(uncommitted)})
    out["files"] = skew

    cl = os.path.join(root, "tools", "check-links.py")
    if os.path.isfile(cl):
        env = dict(os.environ)
        env["CHECK_ROOT"] = root
        # check-links розкриває ~/AgentReachProject, а в proot HOME=/root —
        # без цього він дає хибні «файл не існує» на наявні файли (перевірено).
        env["HOME"] = os.path.dirname(root)
        try:
            r = subprocess.run([sys.executable, cl], cwd=root, capture_output=True,
                               text=True, timeout=180, env=env)
            tail = (r.stdout or r.stderr).strip().splitlines()
            out["check_links"] = {"exit": r.returncode, "tail": tail[-6:]}
        except (OSError, subprocess.SubprocessError) as e:
            out["check_links"] = {"error": str(e)}
    return out


# ------------------------------------------------------------------ 4. дерево
def tree(root):
    tdir = os.path.join(root, "trees")
    files = []
    if os.path.isdir(tdir):
        for base, dirs, fs in os.walk(tdir):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            files += [os.path.join(base, f) for f in fs if f.endswith(".md")]
    nodes = {"open": 0, "active": 0, "done": 0, "parked": 0, "unclear": 0}
    per_file, leaves = {}, []
    # Було \[( |x|>)\] — статуси [~] (поза метою/не кандидат) і [?] (неясно) не
    # розпізнавались зовсім: вузол зникав із підрахунку, а його рядки-поля
    # приписувались сусідньому вузлу (50 із 53).
    NODE = re.compile(r"^(\s*)- \[( |x|>|~|\?)\] (.+)$")
    STATUS = {" ": "open", "x": "done", ">": "active", "~": "parked", "?": "unclear"}
    for p in sorted(files):
        lines = read_text(p).splitlines()
        found = []
        for i, line in enumerate(lines):
            m = NODE.match(line)
            if m:
                st = STATUS[m.group(2)]
                nodes[st] += 1
                found.append({"depth": len(m.group(1)), "i": i, "st": st,
                              "name": m.group(3).strip()[:90], "fields": set()})
        for k, n in enumerate(found):
            # поля вузла — рядки з відступом глибше за сам вузол, до наступного вузла
            end = found[k + 1]["i"] if k + 1 < len(found) else len(lines)
            for line in lines[n["i"] + 1:end]:
                low = line.lower()
                for key in ("done when", "evidence", "up:", "зв'язане", "пастк"):
                    if key in low:
                        n["fields"].add(key)
            nxt = found[k + 1] if k + 1 < len(found) else None
            is_leaf = nxt is None or nxt["depth"] <= n["depth"]
            if is_leaf:  # батько без done-when — нормально, міряємо лише листя
                leaves.append({"file": os.path.relpath(p, root), "name": n["name"],
                               "fields": n["fields"]})
        per_file[os.path.relpath(p, root)] = len(found)
    missing = [n for n in leaves if not ({"done when", "evidence"} & n["fields"])]
    return {"files": [os.path.relpath(p, root) for p in files],
            "per_file": per_file,
            "nodes": nodes,
            "nodes_total": sum(nodes.values()),
            "leaves": len(leaves),
            "leaves_without_donewhen_or_evidence": len(missing),
            "examples": [{"file": n["file"], "name": n["name"]} for n in missing[:8]]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    root = os.path.abspath(a.root)

    rep = {"root": root, "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "queue": queue(root), "inventory": inventory(root),
           "stale": stale(root), "tree": tree(root)}

    q = rep["queue"]
    print(f"== КРОК 0 АУДИТУ · {root} ==")
    print(f"\n[1] ЧЕРГА BATON — знімків: {q['passes']}, pass {q['pass_range']}")
    print(f"    пунктів усього: {q['items_total']}  | унікальних: {q['items_unique']}"
          f"  | повторів: {q['duplicates']} ({q['dup_share']})")
    print(f"    з носієм (файл/рядок у BACKLOG): {q['with_carrier']}"
          f"  | без носія: {q['without_carrier']} (носій у {q['carrier_share']})")
    print(f"    присутність у BACKLOG.md — строго (8 слів): {q['in_backlog_share_strict']},"
          f" м'яко (4 слова): {q['in_backlog_share_loose']}  ← межа, не точне число")
    print(f"    час життя пункту: з носієм {q['lifetime_with_carrier']},"
          f" без носія {q['lifetime_without_carrier']}")
    print(f"    зникли до останньої передачі: з носієм {q['died_with_carrier']},"
          f" без носія {q['died_without_carrier']}")
    if q["stuck_5plus"]:
        print("    живуть ≥5 передач (застрягли):")
        for s in q["stuck_5plus"][:6]:
            print(f"      · {s['lifetime']}× {s['text'][:110]}")
    if q["oldest_no_carrier"]:
        print("    найдовше без носія:")
        for s in q["oldest_no_carrier"][:5]:
            print(f"      · {s['lifetime']}× {s['text'][:110]}")

    inv = rep["inventory"]
    print("\n[2] ЩО Є, АЛЕ НЕ ВИКОРИСТОВУЄТЬСЯ")
    h = inv["hooks"]
    print(f"    хуки: файлів {len(h['files'])}, зареєстровано команд {h['registered_commands']}"
          f" | файл без реєстрації: {h['files_not_registered']}"
          f" | реєстрація без файлу: {h['registered_not_on_disk']}")
    for ev, v in h["per_event"].items():
        print(f"      {ev}: матчерів {v['matchers']}, команд {v['commands']}")
    dead = [k for k, v in inv["skills"].items() if v == 0]
    print(f"    скіли: {len(inv['skills'])} | без згадок поза собою: {dead or '—'}")
    deadt = [k for k, v in inv["tools"].items() if v == 0]
    print(f"    tools/: файлів {len(inv['tools'])} (теки: {inv['tool_dirs']})"
          f" | сироти (0 згадок): {deadt or '—'}")
    print(f"    MCP: у проєкті {inv['mcp_project'] or '—'}"
          f" | у профілях DSH {[m['server'] for m in inv['mcp_dsh_profiles']] or '—'}")

    st = rep["stale"]
    print("\n[3] ЗАСТАРІЛЕ / РОЗСИНХРОН")
    print(f"    CONTEXT.md: останній коміт {st.get('context_last_commit')}"
          f" | комітів після нього: {st.get('commits_after_context')} з {st.get('commits_total')}")
    for f in st["files"]:
        flag = " [НЕЗАКОМІЧЕНО]" if f["uncommitted"] else ""
        print(f"    {f['file']}: mtime {f['mtime_days_ago']} дн. тому, коміт {f['last_commit']}{flag}")
    print(f"    check-links: {st.get('check_links')}")

    t = rep["tree"]
    print("\n[4] ДЕРЕВО")
    print(f"    файлів: {len(t['files'])} | вузлів: {t['nodes_total']} {t['nodes']}"
          f" | листових: {t['leaves']}")
    print(f"    листових без done-when/evidence: {t['leaves_without_donewhen_or_evidence']}")
    for e in t["examples"][:5]:
        print(f"      · {e['file']}: {e['name'][:80]}")

    path = a.json or os.path.join(root, ".claude", "logs",
                                  f"project-audit-{datetime.now().strftime('%Y%m%d-%H%M')}.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=1)
    print(f"\nзнімок: {path}")


if __name__ == "__main__":
    main()
