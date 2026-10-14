#!/usr/bin/env python3
"""Прогін cases-v3 агентами Claude з ПОРОЖНЬОЇ теки (T11, 2026-10-13).

Навіщо: агенти, запущені в проєкті, бачать CLAUDE.md з відповідями на кейси (рада 13.10);
сліпа розмітка Sonnet 13.10 робилась кодом прямо з чату — тут він збережений, щоб нова
сесія не писала його заново. Промпт — заморожений v2, дослівно з cases-v2.md.

  python3 run_claude_v3.py --model haiku --dry-run      # показати перший промпт, без запуску
  python3 run_claude_v3.py --model haiku [--only E1,K1]  # прогін; результат — results-claude-<model>.jsonl
  python3 run_claude_v3.py --model opus --only K4 --suffix=-repeat  # повтор розбіжних (протокол)
  python3 run_claude_v3.py --blind                       # лише зібрати сліпу теку для розмітника

Тека: $TMPDIR/verifier-v3 (копії sources-v3, нічого з проєкту). Кожен кейс — окремий
`claude -p` (Read/Grep/Glob, без мережі й запису), порядок перемішано (seed у виводі).
Коштує ліміт Pro: оцінка з 13.10 — Opus ≈31 тис. токенів на кейс (v2), Sonnet-розмітка
32 кейсів ≈690 тис. (майже все кеш). Перед прогоном — tools/agent-probe.sh на теці.
"""
import argparse, json, os, random, re, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "sources-v3")
TMP = os.environ.get("TMPDIR", "/data/data/com.termux/files/usr/tmp")
WORK = os.path.join(TMP, "verifier-v3")


def prompt_v2():
    t = open(os.path.join(HERE, "cases-v2.md"), encoding="utf-8").read()
    m = re.search(r"## Промпт верифікатора v2[^\n]*\n+```\n(.*?)\n```", t, re.S)
    if not m:
        sys.exit("run_claude_v3: не знайдено блок промпта v2 у cases-v2.md")
    return m.group(1)


def cases():
    rows = []
    for l in open(os.path.join(HERE, "cases-v3.md"), encoding="utf-8"):
        m = re.match(r"\| ([EUPK]\d+) \| [^|]* \| (.+?) \| (.+?) \| (.+?) \| (.+?) \| (.+?) \|$", l.strip())
        if m:
            cid, claim, ctx, srcs, exp, _ = m.groups()
            files = [s.strip() for s in re.sub(r"\([^)]*\)", "", srcs).split(",") if s.strip()]
            rows.append({"id": cid, "claim": claim, "context": ctx, "files": files, "expected": exp})
    if len(rows) != 32:
        print(f"увага: кейсів {len(rows)}, очікувалось 32", file=sys.stderr)
    return rows


def build_dir(rows):
    os.makedirs(WORK, exist_ok=True)
    for r in rows:
        for f in r["files"]:
            shutil.copy(os.path.join(SRC, f), WORK)
    return WORK


def blind(rows, seed):
    random.Random(seed).shuffle(rows)
    with open(os.path.join(WORK, "claims.md"), "w", encoding="utf-8") as f, \
         open(os.path.join(HERE, f"blind-map-seed{seed}.tsv"), "w", encoding="utf-8") as mp:
        f.write("# Твердження для розмітки\n\nДля кожного дивися ЛИШЕ файли з рядка «ДЖЕРЕЛА».\n\n")
        for i, r in enumerate(rows, 1):
            f.write(f"## B{i:02d}\nТВЕРДЖЕННЯ: {r['claim']}\nКОНТЕКСТ: {r['context']}\n"
                    f"ДЖЕРЕЛА: {', '.join(r['files'])}\n\n")
            mp.write(f"B{i:02d}\t{r['id']}\t{r['expected']}\n")
    print(f"сліпа тека: {WORK}/claims.md; карта: blind-map-seed{seed}.tsv (поза текою)")


def run_case(r, model, pv2):
    p = (pv2.replace("{claim}", r["claim"]).replace("{context}", r["context"])
         + f"\n\nФАЙЛИ-ДЖЕРЕЛА (у поточній теці): {', '.join(r['files'])}")
    t0 = time.time()
    pr = subprocess.run(
        ["claude", "-p", p, "--model", model, "--allowedTools", "Read Grep Glob",
         "--disallowedTools", "Bash Write Edit WebFetch WebSearch Task NotebookEdit",
         "--output-format", "json"], cwd=WORK, capture_output=True, text=True, timeout=900)
    out = {"id": r["id"], "expected": r["expected"], "model": model, "rc": pr.returncode,
           "sec": round(time.time() - t0, 1)}
    try:
        d = json.loads(pr.stdout)
        out.update(result=d.get("result", ""), cost=d.get("total_cost_usd"),
                   usage={k: v for k, v in (d.get("usage") or {}).items() if "token" in k})
        m = re.search(r"VERDICT:\s*(ТАК|НІ|НЕ МОЖУ ПЕРЕВІРИТИ)", out["result"])
        out["verdict"] = m.group(1) if m else None
    except ValueError:
        out.update(result=None, stderr=pr.stderr[-500:])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model")
    ap.add_argument("--only", default="")
    ap.add_argument("--seed", type=int, default=int(time.strftime("%Y%m%d")))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--blind", action="store_true")
    ap.add_argument("--suffix", default="", help="окремий файл, напр. --suffix=-repeat (повтор розбіжних кейсів)")
    a = ap.parse_args()
    rows = cases()
    build_dir(rows)
    if a.blind:
        return blind(rows, a.seed)
    if not a.model:
        sys.exit("потрібен --model (haiku|sonnet|opus) або --blind")
    pv2 = prompt_v2()
    if a.only:
        keep = set(a.only.split(","))
        rows = [r for r in rows if r["id"] in keep]
    random.Random(a.seed).shuffle(rows)
    if a.dry_run:
        r = rows[0]
        print(f"тека {WORK}; кейсів {len(rows)}; seed {a.seed}; перший {r['id']}:\n")
        print(pv2.replace("{claim}", r["claim"]).replace("{context}", r["context"])[-600:])
        return
    path = os.path.join(HERE, f"results-claude-{a.model}{a.suffix}.jsonl")
    with open(path, "a", encoding="utf-8") as f:
        for i, r in enumerate(rows, 1):
            res = run_case(r, a.model, pv2)
            f.write(json.dumps(res, ensure_ascii=False) + "\n"); f.flush()
            print(f"[{i}/{len(rows)}] {r['id']} очікую {r['expected']} → {res.get('verdict')} "
                  f"({res['sec']} с)")
    print("результат:", path)


if __name__ == "__main__":
    main()
