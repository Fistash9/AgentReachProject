"""Бектест трьох механізмів (2026-10-13, запит користувача «роби бектест двох механізмів
перевірки всього … і відповідь не можу перевірити»). Лише читає журнали й файли.
M1 обмовки: переказ проти речення джерела.  M2 edit-gate: (а) правка хука без пошуку
сусідів на ту саму подію, (б) правка .gitignore без перевірки untracked після.
M3 «не перевірено» без названих спроб."""
import glob, json, os, re, sys

PROJ = "/data/data/com.termux/files/home/AgentReachProject"
LOGS = os.path.expanduser("~/.claude/projects/-data-data-com-termux-files-home-AgentReachProject")

# ---------- M1 ----------
LIMIT = [  # (англ. у джерелі, укр. відповідники в переказі)
    (r"\bexcept\b", r"крім|окрім|за винятком|except"),
    (r"\bonly\b", r"лише|тільки|only"),
    (r"\bIgnored\b", r"ігнор|Ignored"),
    (r"Not Supported", r"не підтрим|Not Supported"),
    (r"\beven\b", r"навіть|even"),
    (r"\bunless\b", r"якщо не|unless"),
    (r"\bmay still\b", r"може|may"),
    (r"by default|default", r"за замовчуванням|default"),
]


def limiters_missing(claim, ctx):
    return [s for s, u in LIMIT if re.search(s, ctx) and not re.search(u, claim, re.I)]


def m1():
    src = PROJ + "/tools/verifier-backtest/sources-v3/"
    # (назва, твердження, файл, якір у джерелі) — старі K4/K1 з чернетки 13.10 + чинні K
    cases = [
        ("K4-старий", "MAX_THINKING_TOKENS=0 вимикає мислення на Anthropic API, але на сторонніх провайдерах Claude Code просто не передає параметр thinking, і модель може міркувати далі.", "claude-model-config-thinking.md", "MAX_THINKING_TOKENS=0"),
        ("K1-старий", "Anthropic-шар DeepSeek ігнорує mcp_servers і не підтримує mcp_tool_use, але звичайні блоки tool_use підтримує повністю.", "deepseek-anthropic-api.txt", 'type = "tool_use"'),
    ]
    for l in open(PROJ + "/tools/verifier-backtest/cases-v3.md", encoding="utf-8"):
        m = re.match(r"\| (K\d+) \| [^|]* \| (.+?) \| .+? \| (.+?) \| ТАК \| (.+?) \|$", l.strip())
        if m:
            q = re.findall(r"«([^»]{6,})»", m.group(4))
            f = re.sub(r"\([^)]*\)", "", m.group(3)).split(",")[0].strip()
            cases.append((m.group(1), m.group(2), f, q[0] if q else None))
    print("== M1 обмовки (контролі K: переказ проти джерела)")
    for name, claim, f, anchor in cases:
        t = open(src + f, encoding="utf-8", errors="ignore").read()
        if not anchor or anchor not in t:
            print(f"  {name}: якір не знайдено — пропуск"); continue
        i = t.index(anchor)
        ctx = t[max(0, i - 40): i + 260]
        miss = limiters_missing(claim, ctx)
        print(f"  {name}: {'СИГНАЛ ' + str(miss) if miss else 'тиша'}")


# ---------- журнали ----------
def sessions():
    return sorted(glob.glob(LOGS + "/*.jsonl"), key=os.path.getmtime)


def events(path):
    for line in open(path, encoding="utf-8", errors="ignore"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if not isinstance(d, dict):
            continue
        yield d


RE_HOOKW = re.compile(r"\.claude/hooks/([\w.-]+\.py)")
RE_WRITE = re.compile(r"open\([^)]*['\"]w['\"]|sed -i|>>?\s*\S*\.claude/hooks/|\.write\(")
RE_EVENT = re.compile(r"\b(Stop|PreToolUse|PostToolUse|UserPromptSubmit|SessionStart)\b")


def hook_event(fname):
    p = PROJ + "/.claude/hooks/" + fname
    if not os.path.exists(p):
        return None
    m = RE_EVENT.search(open(p, encoding="utf-8", errors="ignore").read(1500))
    return m.group(1) if m else None


def m2(paths):
    print("== M2 edit-gate: (а) правка хука без пошуку сусідів на ту саму подію; (б) .gitignore")
    tot_a = tot_b = 0
    for p in paths:
        greps, fired_a, out = [], set(), []
        gi_pending = None
        for d in events(p):
            if d.get("type") != "assistant":
                continue
            for x in (d.get("message") or {}).get("content") or []:
                if not (isinstance(x, dict) and x.get("type") == "tool_use"):
                    continue
                n, inp = x.get("name"), x.get("input") or {}
                ts = d.get("timestamp", "")[5:16]
                cmd = str(inp.get("command", "")) if n == "Bash" else ""
                targets = []
                if n in ("Edit", "Write", "MultiEdit"):
                    fp = str(inp.get("file_path", ""))
                    m = RE_HOOKW.search(fp)
                    if m and n != "Write":
                        targets.append(m.group(1))
                    if fp.endswith("/.gitignore"):
                        gi_pending = ts; out.append(f"    б {ts} правка .gitignore (Edit)")
                elif n == "Bash":
                    if RE_WRITE.search(cmd):
                        targets += [h for h in RE_HOOKW.findall(cmd) if "tests/" not in h]
                    if re.search(r">>?\s*\.gitignore|\.gitignore['\"]?\s*,\s*['\"]a", cmd):
                        gi_pending = ts; out.append(f"    б {ts} правка .gitignore (Bash)")
                    if gi_pending and re.search(r"git status[^|;&]*untracked-files=all|git check-ignore", cmd):
                        out.append(f"      … перевірено untracked о {ts}"); gi_pending = None
                    if re.search(r"\b(grep|rg)\b", cmd):
                        greps.append(cmd)
                elif n == "Grep":
                    greps.append(json.dumps(inp))
                for h in set(targets):
                    ev = hook_event(h)
                    if not ev or h in fired_a:
                        continue
                    sib = any(".claude/hooks" in g and (ev in g or "last_assistant_message" in g
                              or "transcript_path" in g) for g in greps)
                    if not sib:
                        fired_a.add(h); out.append(f"    а {ts} {h} ({ev}) — сусідів не шукано")
        a = sum(1 for o in out if o.startswith("    а")); b = sum(1 for o in out if o.startswith("    б"))
        if out:
            print(f"  {os.path.basename(p)[:8]}: а={a} б={b}")
            for o in out[:12]:
                print(o)
        tot_a += a; tot_b += b
    print(f"  разом: а {tot_a}, б {tot_b} (сесій {len(paths)})")


RE_UNV = re.compile(r"не перевірено|не можу перевірити|НЕ ПЕРЕВІРЕНО|\[unverified\]|не звірено", re.I)
RE_TRIED = re.compile(r"шукав|спробував|перевіряв|маршрут|grep|curl|git log|журнал|у записах|дока|"
                      r"бо |тому що|причина|неможливо в цій сесії|потрібно .{0,20}(тиждень|дані)", re.I)


def m3(paths):
    print("== M3 «не перевірено» без названих спроб чи причини (відповіді користувачу)")
    tot = flag = 0
    for p in paths:
        loc_t = loc_f = 0; ex = []
        for d in events(p):
            if d.get("type") != "assistant":
                continue
            for x in (d.get("message") or {}).get("content") or []:
                if not (isinstance(x, dict) and x.get("type") == "text"):
                    continue
                for para in re.split(r"\n\s*\n|\n- |\n\d+\. ", x.get("text", "")):
                    if RE_UNV.search(para):
                        loc_t += 1
                        if not RE_TRIED.search(para):
                            loc_f += 1
                            if len(ex) < 3:
                                ex.append(re.sub(r"\s+", " ", para)[:170])
        if loc_t:
            print(f"  {os.path.basename(p)[:8]}: згадок {loc_t}, без спроб/причини {loc_f}")
            for e in ex:
                print("     ·", e)
        tot += loc_t; flag += loc_f
    print(f"  разом: згадок {tot}, сигналів {flag}")


if __name__ == "__main__":
    m1()
    ps = sessions()
    m2(ps)
    m3(ps[-6:])
