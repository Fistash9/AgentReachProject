"""Знімки TROUBLES.md за датою коміту (git) + розбір на розділи — спільне для бектесту й прототипу."""
import subprocess, bisect, datetime, re
PROJ = "/data/data/com.termux/files/home/AgentReachProject"
def _commits():
    out = subprocess.check_output(["git", "-C", PROJ, "log", "--format=%H %ct", "--", "TROUBLES.md"], text=True).split("\n")
    return sorted((int(l.split()[1]), l.split()[0]) for l in out if l.strip())
COMMITS = None; SNAP = {}
def parse(text):
    secs, cur = [], None
    for n, line in enumerate(text.splitlines(), 1):
        if line.startswith("## "):
            cur = {"h": line[3:].strip(), "n": n, "tags": [], "body": []}; secs.append(cur); continue
        if cur is None: continue
        if line.startswith("TAGS:"): cur["tags"] += [t.strip().lower() for t in line[5:].split(",") if t.strip()]
        cur["body"].append(line)
    for s in secs: s["text"] = (s["h"] + "\n" + "\n".join(s["body"])).lower()
    return secs
def snap_by_key(k):
    if k not in SNAP:
        if k == "WT": txt = open(PROJ + "/TROUBLES.md", encoding="utf-8").read()
        elif k == "none": txt = ""
        else: txt = subprocess.check_output(["git", "-C", PROJ, "show", k + ":TROUBLES.md"], text=True, errors="replace")
        SNAP[k] = parse(txt)
    return SNAP[k]
def troubles_at(epoch):
    global COMMITS
    if COMMITS is None: COMMITS = _commits()
    cts = [c[0] for c in COMMITS]; i = bisect.bisect_right(cts, epoch) - 1
    k = "WT" if (i == len(COMMITS) - 1 and epoch > cts[-1]) else (COMMITS[i][1] if i >= 0 else "none")
    return k, snap_by_key(k)
def first_commit_with(head_rx):
    """Час (epoch) першого коміту, у знімку якого є розділ із заголовком за head_rx (журнал лише дописується → монотонно)."""
    global COMMITS
    if COMMITS is None: COMMITS = _commits()
    lo, hi = 0, len(COMMITS) - 1
    if not any(re.search(head_rx, s["h"]) for s in snap_by_key(COMMITS[hi][1])): return None
    while lo < hi:
        mid = (lo + hi) // 2
        if any(re.search(head_rx, s["h"]) for s in snap_by_key(COMMITS[mid][1])): hi = mid
        else: lo = mid + 1
    return COMMITS[lo][0]
def epoch(ts): return datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
