import json, sys, glob, os, collections, re
P = os.path.expanduser("~/.claude/projects/-data-data-com-termux-files-home-AgentReachProject/")
files = sorted(glob.glob(P + "*.jsonl")) + sorted(glob.glob(P + "*/subagents/*.jsonl"))
OUT_CALLS = open("calls2.jsonl", "w", encoding="utf-8")
OUT_HINTS = open("hints2.jsonl", "w", encoding="utf-8")
stats = collections.Counter()
att_sample_printed = False
def rtext(c):
    if isinstance(c, str): return c
    if isinstance(c, list):
        return "\n".join((x.get("text") or "") for x in c if isinstance(x, dict))
    return str(c)
def brief(name, inp):
    if not isinstance(inp, dict): return str(inp)[:300]
    if name == "Bash": return (inp.get("command") or "")[:700]
    for k in ("file_path", "path", "pattern", "url", "query", "description", "prompt"):
        if inp.get(k): return (str(inp[k]))[:300]
    return json.dumps(inp, ensure_ascii=False)[:300]
for f in files:
    sid = os.path.basename(f)[:-6]; sub = ("/subagents/" in f); psid = f.split("/")[-3] if sub else sid
    calls = {}      # tool_use_id -> record
    order = []
    stats["files"] += 1
    for line in open(f, encoding="utf-8", errors="replace"):
        stats["lines"] += 1
        try:
            d = json.loads(line)
        except Exception:
            stats["parse_err"] += 1
            continue
        t = d.get("type")
        if t == "assistant":
            for b in (d.get("message", {}).get("content") or []):
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    rec = {"sid": psid, "agent": (sid if sub else None), "i": len(order), "ts": d.get("timestamp"), "name": b.get("name"),
                           "brief": brief(b.get("name"), b.get("input")), "id": b.get("id"),
                           "side": bool(d.get("isSidechain"))}
                    calls[b["id"]] = rec; order.append(rec)
                    stats["tool_use:" + str(b.get("name"))] += 1
        elif t == "user":
            c = d.get("message", {}).get("content")
            if isinstance(c, list):
                for b in c:
                    if isinstance(b, dict) and b.get("type") == "tool_result":
                        rec = calls.get(b.get("tool_use_id"))
                        if rec is None:
                            stats["result_without_use"] += 1; continue
                        txt = rtext(b.get("content"))
                        rec["is_error"] = bool(b.get("is_error"))
                        rec["rts"] = d.get("timestamp")
                        rec["len"] = len(txt)
                        tur = d.get("toolUseResult")
                        if rec["is_error"] or rec["name"] == "Bash":
                            rec["head"] = txt[:600]
                            rec["tail"] = txt[-400:] if len(txt) > 600 else ""
                        if isinstance(tur, dict):
                            se = tur.get("stderr")
                            if se: rec["stderr"] = str(se)[:400]
                            if tur.get("interrupted"): rec["interrupted"] = True
        elif t == "attachment":
            a = d.get("attachment") or {}
            if a.get("type") == "hook_additional_context":
                if not att_sample_printed:
                    att_sample_printed = True
                    print("ATTACHMENT SAMPLE keys:", sorted(a.keys()), "| top keys:", sorted(d.keys()))
                    print("ATTACHMENT SAMPLE (800):", json.dumps(a, ensure_ascii=False)[:800])
                stats["hint_attachments"] += 1
                OUT_HINTS.write(json.dumps({"sid": sid, "ts": d.get("timestamp"), "a": {k: (v if k != "content" else (json.dumps(v, ensure_ascii=False)[:900])) for k, v in a.items()}}, ensure_ascii=False) + "\n")
    for rec in order:
        OUT_CALLS.write(json.dumps(rec, ensure_ascii=False) + "\n")
OUT_CALLS.close(); OUT_HINTS.close()
for k, v in sorted(stats.items()): print(k, v)
