#!/data/data/com.termux/files/usr/bin/python3
"""Розклад пунктів естафети «Зроблено»/«Обережно» на порції для делегата (вузол «Легкий стан», 2026-10-20).

Навіщо: перед архівом естафети кожен пункт має отримати статус із доказом — «записано (де)» / «частково» /
«лише в естафеті». Пункти з хешем коміту, що є в git, вважаються записаними; для решти скрипт підбирає по 3
найближчі абзаци з TROUBLES/BACKLOG/CONTEXT/GOALS/trees/agents (рідкісні слова, вага 1/(1+df)) — делегат
судить лише за цими кандидатами. Типово — ОДИН файл (усі пункти): великий вхід делегату — цілим і з
stream: true (пам'ять session-review-send-whole; 20.10 порції по ~137 КБ без stream — read ETIMEDOUT, це
обрив очікування, а не ліміт розміру). Ділити — лише явним --per і лише з дозволу користувача.

  python3 tools/baton-split.py [--per N] [--out $TMPDIR/bsplit]
"""
import argparse, collections, json, math, os, re, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per", type=int, default=0, help="0 = один файл (типово)")
    ap.add_argument("--out", default=os.path.join(os.environ.get("TMPDIR", "/data/data/com.termux/files/usr/tmp"), "bsplit"))
    a = ap.parse_args()
    os.chdir(ROOT)
    os.makedirs(a.out, exist_ok=True)
    d = json.load(open(".baton/baton.json", encoding="utf-8"))
    run = lambda *c: subprocess.run(c, capture_output=True, text=True).stdout
    allh = set(run("git", "log", "--all", "--format=%h %H").split())
    files = ["TROUBLES.md", "BACKLOG.md", "CONTEXT.md", "GOALS.md"] + run(
        "git", "ls-files", "trees/*.md", "trees/*/*.md", "agents/*/*.md").split()
    paras = []
    for f in files:
        ln = 1
        for p in re.split(r"(\n\s*\n)", open(f, encoding="utf-8").read()):
            if p.strip() and not re.fullmatch(r"\n\s*\n", p):
                paras.append((f, ln, p))
            ln += p.count("\n")
    W = lambda s: set(w for w in re.findall(r"[\w.\-/]{5,}", s.lower()) if not w.isdigit())
    pw = [W(p) for _, _, p in paras]
    df = collections.Counter(w for ws in pw for w in ws)
    items, in_git = [], 0
    for key in ("done", "watchOut"):
        for i, it in enumerate(d[key]):
            if any(any(x.startswith(h) for x in allh) for h in re.findall(r"\b[0-9a-f]{7,12}\b", it)):
                in_git += 1
                continue
            items.append((f"{key[0].upper()}{i:03d}", key, it))
    per = a.per or len(items)
    for b in range(math.ceil(len(items) / per)):
        with open(os.path.join(a.out, f"batch{b:02d}.md"), "w", encoding="utf-8") as fo:
            for iid, key, it in items[b * per:(b + 1) * per]:
                ws = W(it)
                sc = sorted(((sum(1 / (1 + df[w]) for w in ws & pw[k]), k) for k in range(len(paras))
                             if ws & pw[k]), reverse=True)
                fo.write(f"## {iid} [{'Зроблено' if key == 'done' else 'Обережно'}]\nПУНКТ: {it}\n")
                for _, k in sc[:3]:
                    f, ln, p = paras[k]
                    # Вікно з 10 рядків, де найбільше слів пункту, а не перші 700 символів (2026-10-20): вузол
                    # дерева — один абзац на десятки рядків, потрібний рядок був за обрізом (D128 → :43 при :31).
                    # Вибірка 10 «лише в естафеті»: справжнє місце видно делегату 3/10 → 7/10.
                    lines = p.split("\n")
                    s = max(range(max(1, len(lines) - 9)), key=lambda j: (
                        sum(1 / (1 + df[w]) for w in ws & W("\n".join(lines[j:j + 10]))), -j))
                    fo.write(f"КАНДИДАТ {f}:{ln + s}: {chr(10).join(lines[s:s + 10]).strip()[:900]}\n")
                fo.write("\n")
    print(f"з комітом у git: {in_git}; на делегата: {len(items)} у {math.ceil(len(items) / per)} файлі(ах) → {a.out}")


if __name__ == "__main__":
    main()
