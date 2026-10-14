#!/data/data/com.termux/files/usr/bin/python3
"""Прогін cases-v3 безкоштовними перевіряльниками через API (T11, 2026-10-14).

Навіщо: run_nvidia.py знає лише cases-v2 (8 кейсів), а DeepSeek flash через delegate
32×k викликами з чату забив би контекст. Тут — той самий запит, що робить delegate 3.0.1
(src/tools.mjs + client.mjs): user-повідомлення = промпт + «## FILES:» + «### <шлях>» з
блоком коду; temperature 0.3; max_tokens 8192; файли понад бюджет delegate
(context_window моделі з delegator-providers.json /2*3) delegate НЕ надсилає — тут так само, якщо не
передати --full-files. Промпт — заморожений v2 з cases-v2.md (як run_claude_v3.py).

  python3 run_api_v3.py --provider bazaarlink --dry-run     # перший промпт і розміри, без запиту
  python3 run_api_v3.py --provider nvidia --k 3 [--only E1,K1]
Вивід: results-<provider>-<модель>-v3.jsonl (дописує; готові пари кейс/прогін пропускає —
можна продовжити наступного дня після денного ліміту BazaarLink).
"""
import argparse, concurrent.futures as cf, json, os, random, re, sys, time, urllib.request

import run_claude_v3 as rc

ROOT = os.path.expanduser("~/AgentReachProject")
PROVIDERS = {
    "bazaarlink": ("https://api.bazaarlink.ai/v1/chat/completions", "BAZAARLINK_API_KEY",
                   "deepseek/deepseek-v4-flash-0731free:free"),
    "nvidia": ("https://integrate.api.nvidia.com/v1/chat/completions", "NVIDIA_API_KEY",
               "openai/gpt-oss-20b"),
    # платний прямий API (рішення користувача 14.10, ~$0.16): це DeepSeek-V4.1-Flash, НЕ
    # v4-flash-0731 з BazaarLink — у таблиці окремим рядком; вікно 1M (deepseek-pricing.txt)
    "deepseek": ("https://api.deepseek.com/chat/completions", "DEEPSEEK_API_KEY", "deepseek-flash"),
}


def budget(provider, model):
    """maxFileBytes delegate: context_window моделі з ~/.claude/delegator-providers.json / 2 * 3."""
    if provider == "deepseek":
        return 1_000_000 // 2 * 3
    cfg = json.load(open(os.path.expanduser("~/.claude/delegator-providers.json"), encoding="utf-8"))
    for p in cfg:
        for m in p["models"] if p["id"] == provider else []:
            if m["id"] == model:
                return (m.get("context_window") or 128_000) // 2 * 3
    sys.exit(f"run_api_v3: {provider}:{model} немає в delegator-providers.json")
LIMIT_RE = re.compile(r"daily limit|capacity full", re.I)


def build_prompt(pv2, case, full, limit):
    prompt = pv2.replace("{claim}", case["claim"]).replace("{context}", case["context"])
    total, sections, dropped = 0, [], []
    for f in case["files"]:
        p = os.path.join(rc.SRC, f)
        size = os.path.getsize(p)
        if not full and total + size > limit:
            sections.append(f"### {p}\n(skipped: would exceed context window — {size / 1024:.1f}KB)")
            dropped.append(f)
            continue
        total += size
        ext = os.path.splitext(f)[1].lstrip(".")
        sections.append(f"### {p}\n```{ext}\n{open(p, encoding='utf-8').read()}\n```")
    return prompt + "\n\n## FILES:\n\n" + "\n\n".join(sections), dropped


def call(url, key, model, prompt, timeout, retries=2):
    body = {"model": model, "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3, "max_tokens": 8192}
    last = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={
            "Authorization": "Bearer " + key, "content-type": "application/json"})
        t0 = time.time()
        try:
            d = json.load(urllib.request.urlopen(req, timeout=timeout))
            m = d["choices"][0]["message"]
            return {"ok": True, "secs": round(time.time() - t0, 1), "attempts": attempt + 1,
                    "content": m.get("content") or "", "finish": d["choices"][0].get("finish_reason"),
                    "reasoning_len": len(m.get("reasoning_content") or m.get("reasoning") or ""),
                    "usage": d.get("usage")}
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code} {e.read()[:200]!r}"
            if LIMIT_RE.search(last) or e.code not in (429, 500, 502, 503, 504):
                break
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
        time.sleep(min(2 ** attempt * 5, 30))
    return {"ok": False, "error": last, "attempts": attempt + 1}


def quotes(content, files):
    norm = lambda s: re.sub(r"\s+", " ", s.replace("**", "")).strip()
    src = norm("\n".join(open(os.path.join(rc.SRC, f), encoding="utf-8").read() for f in files))
    qs = [norm(q) for q in re.findall(r'[“"]([^"”]{12,})[”"]', content)]
    return len(qs), sum(q in src for q in qs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", choices=PROVIDERS, required=True)
    ap.add_argument("--model")
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--only", default="")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--full-files", action="store_true", help="не різати файли бюджетом delegate")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    url, keyname, model = PROVIDERS[a.provider]
    model = a.model or model
    limit = budget(a.provider, model)
    pv2, rows = rc.prompt_v2(), rc.cases()
    if a.only:
        rows = [r for r in rows if r["id"] in set(a.only.split(","))]
    path = os.path.join(rc.HERE, f"results-{a.provider}-{model.split('/')[-1].split(':')[0]}-v3.jsonl")
    done = set()
    if os.path.exists(path):
        for l in open(path, encoding="utf-8"):
            d = json.loads(l)
            if d.get("ok") and d.get("full_files") == a.full_files:
                done.add((d["id"], d["run"]))
    jobs = [(r, k) for k in range(1, a.k + 1) for r in rows if (r["id"], k) not in done]
    random.Random(int(time.strftime("%Y%m%d"))).shuffle(jobs)
    if a.dry_run:
        for r in rows:
            p, dropped = build_prompt(pv2, r, a.full_files, limit)
            if dropped:
                print(f"{r['id']}: delegate не надішле {dropped}")
        print(f"{path}\nготово {len(done)}, до запуску {len(jobs)}; перший {jobs[0][0]['id'] if jobs else '-'}:")
        print(build_prompt(pv2, jobs[0][0], a.full_files, limit)[0][:700] if jobs else "")
        return
    if a.provider == "deepseek":  # як tools/deepseek-search.py: змінна або agent.py
        key = os.environ.get(keyname) or re.search(r"sk-[a-zA-Z0-9]+",
                                                   open(os.path.join(ROOT, "agent.py")).read()).group(0)
    else:
        key = re.search(rf"^{keyname}=(\S+)", open(os.path.join(ROOT, ".env")).read(), re.M).group(1)
    stop = False
    with cf.ThreadPoolExecutor(a.workers) as ex, open(path, "a", encoding="utf-8") as out:
        futs = {}
        for r, k in jobs:
            p, dropped = build_prompt(pv2, r, a.full_files, limit)
            futs[ex.submit(call, url, key, model, p, a.timeout)] = (r, k, dropped)
        for i, fut in enumerate(cf.as_completed(futs), 1):
            r, k, dropped = futs[fut]
            res = fut.result()
            m = re.search(r"VERDICT:\s*\**\s*(ТАК|НІ|НЕ МОЖУ ПЕРЕВІРИТИ)", res.get("content", ""))
            res.update(id=r["id"], run=k, expected=r["expected"], model=model, dropped=dropped,
                       full_files=a.full_files,
                       verdict=m.group(1) if m else ("збій" if not res["ok"] else "без VERDICT"))
            if res["ok"]:
                res["quotes_total"], res["quotes_found"] = quotes(res["content"], r["files"])
            out.write(json.dumps(res, ensure_ascii=False) + "\n"); out.flush()
            print(f"[{i}/{len(jobs)}] {r['id']} №{k}: очікую {r['expected']} → {res['verdict']} "
                  f"({res.get('secs', '-')} с) {res.get('error', '')}", flush=True)
            if not res["ok"] and LIMIT_RE.search(res.get("error") or ""):
                stop = True
                print("денний ліміт — зупиняю; решту запусти тим самим рядком пізніше", flush=True)
                for f in futs:
                    f.cancel()
                break
    print("результат:", path)
    sys.exit(2 if stop else 0)


if __name__ == "__main__":
    main()
