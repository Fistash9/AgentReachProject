#!/data/data/com.termux/files/usr/bin/python3
"""Бектест верифікатора (раунд 2, кейси cases-v2.md) на моделі NVIDIA.

Промпт — дослівно з .claude/skills/verify-before-show/verifier-prompt.md,
файли-джерела вставляються в тому ж форматі, що й delegate v3.0.0
(`## FILES:` + `### <шлях>` + блок коду), щоб результат можна було
порівняти з раундом 2 на DeepSeek (results-v2.md).

Кожен кейс проганяється двічі. Збій (таймаут, 5xx, 429 після повторів,
відповідь без VERDICT) — це збій, а не «НІ».

Запуск:  python3 tools/verifier-backtest/run_nvidia.py [--model openai/gpt-oss-20b]
Вивід:   results-nvidia-<модель>.jsonl (сирі відповіді) + зведення в stdout.
"""
import argparse
import concurrent.futures as cf
import json
import os
import re
import time
import urllib.request

ROOT = os.path.expanduser("~/AgentReachProject")
HERE = os.path.join(ROOT, "tools/verifier-backtest")
SRC = os.path.join(HERE, "sources")
URL = "https://integrate.api.nvidia.com/v1/chat/completions"


def load_cases():
    rows = []
    for line in open(os.path.join(HERE, "cases-v2.md"), encoding="utf-8"):
        if line.startswith("| N-"):
            c = [x.strip() for x in line.strip().strip("|").split("|")]
            rows.append({"id": c[0], "claim": c[2], "context": c[3],
                         "files": [f.strip() for f in c[4].split(",")], "expected": c[5]})
    return rows


def template():
    t = open(os.path.join(ROOT, ".claude/skills/verify-before-show/verifier-prompt.md"), encoding="utf-8").read()
    return re.search(r"```\n(.*?)```", t, re.S).group(1)


def build_prompt(tpl, case):
    prompt = tpl.replace("{claim}", case["claim"]).replace("{context}", case["context"])
    sections = []
    for f in case["files"]:
        p = os.path.join(SRC, f)
        ext = os.path.splitext(f)[1].lstrip(".")
        sections.append(f"### {p}\n```{ext}\n{open(p, encoding='utf-8').read()}\n```")
    return prompt + "\n\n## FILES:\n\n" + "\n\n".join(sections)


def call(key, model, prompt, timeout, retries=2):
    body = {"model": model, "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3, "max_tokens": 8192}
    last = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={
            "Authorization": "Bearer " + key, "content-type": "application/json"})
        t0 = time.time()
        try:
            d = json.load(urllib.request.urlopen(req, timeout=timeout))
            m = d["choices"][0]["message"]
            return {"ok": True, "secs": round(time.time() - t0, 1), "attempts": attempt + 1,
                    "content": m.get("content") or "", "reasoning_len": len(m.get("reasoning_content") or ""),
                    "usage": d.get("usage")}
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code} {e.read()[:150]!r}"
            if e.code not in (429, 500, 502, 503, 504):
                break
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
        time.sleep(min(2 ** attempt * 5, 30))  # пауза перед повтором
    return {"ok": False, "error": last, "attempts": retries + 1}


def norm(s):
    return re.sub(r"\s+", " ", s.replace("**", "")).strip()


def check_quotes(content, files):
    src = norm("\n".join(open(os.path.join(SRC, f), encoding="utf-8").read() for f in files))
    quotes = re.findall(r'"([^"]{12,})"', content)
    res = []
    for q in quotes:
        nq = norm(q.replace('\\"', '"'))
        found = nq in src or (len(nq) > 60 and nq[:60] in src) or (len(nq) > 40 and nq[-40:] in src)
        res.append(found)
    return len(res), sum(res)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="openai/gpt-oss-20b")
    ap.add_argument("--workers", type=int, default=4)   # практика NIM: 4–8 паралельно
    ap.add_argument("--timeout", type=int, default=180)
    a = ap.parse_args()
    key = re.search(r"^NVIDIA_API_KEY=(\S+)", open(os.path.join(ROOT, ".env")).read(), re.M).group(1)
    tpl, cases = template(), load_cases()
    assert len(cases) == 8, f"очікую 8 кейсів, знайдено {len(cases)}"
    jobs = [(c, run) for c in cases for run in (1, 2)]
    out_path = os.path.join(HERE, f"results-nvidia-{a.model.split('/')[-1]}.jsonl")
    results = []
    t0 = time.time()
    with cf.ThreadPoolExecutor(a.workers) as ex, open(out_path, "w", encoding="utf-8") as out:
        futs = {ex.submit(call, key, a.model, build_prompt(tpl, c), a.timeout): (c, r) for c, r in jobs}
        for fut in cf.as_completed(futs):
            c, r = futs[fut]
            res = fut.result()
            m = re.search(r"VERDICT:\s*\**\s*(ТАК|НІ|НЕ МОЖУ ПЕРЕВІРИТИ)", res.get("content", ""))
            res.update({"case": c["id"], "run": r, "expected": c["expected"],
                        "verdict": m.group(1) if m else ("збій" if not res["ok"] else "без VERDICT")})
            if res["ok"]:
                res["quotes_total"], res["quotes_found"] = check_quotes(res["content"], c["files"])
            results.append(res)
            out.write(json.dumps(res, ensure_ascii=False) + "\n"); out.flush()
            print(f"{c['id']} №{r}: {res['verdict']:<20} очікую {c['expected']:<4} "
                  f"{res.get('secs', '-')} с, спроб {res['attempts']}, цитати "
                  f"{res.get('quotes_found', '-')}/{res.get('quotes_total', '-')} {res.get('error', '')}", flush=True)

    print(f"\n=== Зведення ({a.model}, {time.time()-t0:.0f} с) ===")
    caught = alarms = 0
    for c in cases:
        rs = sorted([x for x in results if x["case"] == c["id"]], key=lambda x: x["run"])
        vs = [x["verdict"] for x in rs]
        if c["expected"] == "НІ":
            ok = all(v == "НІ" for v in vs); caught += ok
        else:
            ok = not any(v == "НІ" for v in vs); alarms += (not ok)
        print(f"{c['id']:<5} очікую {c['expected']:<4} → {' / '.join(vs):<30} {'✓' if ok else '✗'}")
    print(f"Упіймано E: {caught} з 4 | хибних тривог на K: {alarms} | поріг (≥3/4 і 0 тривог): "
          f"{'ПРОЙДЕНО' if caught >= 3 and alarms == 0 else 'НЕ пройдено'}")
    print(f"Сирі відповіді: {out_path}")


if __name__ == "__main__":
    main()
