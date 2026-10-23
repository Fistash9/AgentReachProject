#!/usr/bin/env python3
"""handoff-view: стислий вигляд стану естафети (≤15 000 байтів UTF-8).

Читає .baton/baton.json і пише .baton/HANDOFF-view.md: шапка, handoffNote,
усі next, openQuestions і files — дослівно; далі «Обережно» (watchOut) і
«Зроблено» (done) — цілими пунктами, скільки влізе в залишок бюджету.
watchOut: спершу пункти з ≥3 спільними словами (≥5 літер) з task/next/
openQuestions/handoffNote, за спаданням кількості; потім done (найсвіжіші,
до 2 500 Б); потім найсвіжіші watchOut. Лише читає вхід і пише лише --out.

Навіщо: повний вивід baton_pick_up 23.10 — 87 338 симв., нова сесія не
читає його одним читанням (BACKLOG.md «План на наступну сесію (DeepSeek,
звірено)…»; вузол «Легкий стан «що зараз»» у trees/pam-yat-proyektu.md).

  python3 tools/handoff-view.py [--in FILE] [--out FILE] [--check]
"""
import argparse
import json
import os
import re
import sys

BUDGET = 15000
FOOTER_RESERVE = 400  # байтів на підвал (числа ще невідомі)
REL_MIN = 3          # «пов'язаний» пункт watchOut: ≥3 спільних слів (з 1 — 142 з 182, done не влазив)
DONE_RESERVE = 2500  # байтів для найсвіжішого done — інакше watchOut з'їдає весь бюджет (23.10: done 0/344)


def b(s):
    return len(s.encode("utf-8"))


def sig_words(s):
    return {w.lower() for w in re.findall(r"[^\W\d_]{5,}", str(s))}


def item_line(i, s):
    return f"{i}. {s}\n"


def render(d, wo_rel, wo_new, done_sel, footer):
    out = ["# Стан естафети — стислий вигляд\n\n"]
    for k in ("task", "goal", "status", "passCount", "lastAgent", "updatedAt"):
        out.append(f"- **{k}:** {d.get(k, '')}\n")
    out.append("\n## Де зупинились\n\n" + str(d.get("handoffNote", "")) + "\n")
    for key, title in (("next", "Далі"), ("openQuestions", "Відкриті питання"),
                       ("files", "Файли")):
        out.append(f"\n## {title}\n\n")
        out += [item_line(i, s) for i, s in enumerate(d.get(key) or [], 1)]
    if wo_rel or wo_new:
        out.append("\n## Обережно\n")
        if wo_rel:
            out.append("\n### Пов'язані з поточною задачею\n\n")
            out += [item_line(i + 1, s) for i, s in wo_rel]
        if wo_new:
            out.append("\n### Найсвіжіші\n\n")
            out += [item_line(i + 1, s) for i, s in wo_new]
    if done_sel:
        out.append("\n## Зроблено (найсвіжіше)\n\n")
        out += [item_line(i + 1, s) for i, s in done_sel]
    out.append(footer)
    return "".join(out)


def footer_text(nw, Nw, nd, Nd):
    return (f"\n---\nПоказано: watchOut {nw} з {Nw}, done {nd} з {Nd} "
            "(номер пункту — його місце в повному списку).\n"
            "Повний стан — HANDOFF.md у корені проєкту або baton_pick_up\n")


def build(d):
    wo = list(d.get("watchOut") or [])
    done = list(d.get("done") or [])
    base = b(render(d, [], [], [], "")) + FOOTER_RESERVE
    # заголовки підрозділів — грубий запас
    used = base + b("\n## Обережно\n\n### Пов'язані з поточною задачею\n\n"
                    "\n### Найсвіжіші\n\n\n## Зроблено (найсвіжіше)\n\n")
    ctx = sig_words(d.get("task", "")) | sig_words(d.get("handoffNote", ""))
    for k in ("next", "openQuestions"):
        for s in d.get(k) or []:
            ctx |= sig_words(s)
    scored = [(len(sig_words(s) & ctx), i) for i, s in enumerate(wo)]
    rel_order = [i for n, i in sorted(scored, key=lambda t: (-t[0], -t[1])) if n >= REL_MIN]
    taken = set()
    rel, new = [], []
    for i in rel_order:
        c = b(item_line(i + 1, wo[i]))
        if used + c <= BUDGET - DONE_RESERVE:
            used += c
            rel.append(i)
            taken.add(i)
    done_idx, done_used = [], 0
    for i in range(len(done) - 1, -1, -1):
        c = b(item_line(i + 1, done[i]))
        if used + c > BUDGET or done_used + c > DONE_RESERVE:
            break
        used += c
        done_used += c
        done_idx.append(i)
    for i in range(len(wo) - 1, -1, -1):
        if i in taken:
            continue
        c = b(item_line(i + 1, wo[i]))
        if used + c <= BUDGET:
            used += c
            new.append(i)
            taken.add(i)
    wo_rel = [(i, wo[i]) for i in rel]
    wo_new = [(i, wo[i]) for i in sorted(new)]
    done_sel = [(i, done[i]) for i in sorted(done_idx)]
    while True:
        text = render(d, wo_rel, wo_new, done_sel,
                      footer_text(len(wo_rel) + len(wo_new), len(wo),
                                  len(done_sel), len(done)))
        if b(text) <= BUDGET or not (done_sel or wo_new or wo_rel):
            return text, len(wo_rel) + len(wo_new), len(done_sel)
        if done_sel:
            done_sel.pop(0)
        elif wo_new:
            wo_new.pop(0)
        else:
            wo_rel.pop()


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default=os.path.join(root, ".baton", "baton.json"))
    ap.add_argument("--out", default=os.path.join(root, ".baton", "HANDOFF-view.md"))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    with open(a.inp, encoding="utf-8") as f:
        d = json.load(f)
    text, nw, nd = build(d)
    size = b(text)
    if size > BUDGET:
        print(f"handoff-view: УВАГА — обов'язкові розділи {size} Б > {BUDGET} Б",
              file=sys.stderr)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(text)
    if not a.check:
        return 0
    with open(a.out, encoding="utf-8") as f:
        got = f.read()
    real = b(got)
    ok = real <= BUDGET
    for k in ("task", "goal", "status", "handoffNote"):
        ok = ok and str(d.get(k, "")) in got
    counts = {}
    for k in ("next", "openQuestions", "files"):
        items = d.get(k) or []
        n = sum(1 for s in items if str(s) in got)
        counts[k] = (n, len(items))
        ok = ok and n == len(items)
    nwo, ndo = len(d.get("watchOut") or []), len(d.get("done") or [])
    line = (f"{real} Б · next {counts['next'][0]}/{counts['next'][1]} дослівно · "
            f"openQuestions {counts['openQuestions'][0]}/{counts['openQuestions'][1]} · "
            f"watchOut {nw}/{nwo} · done {nd}/{ndo}")
    print(("view ok " if ok else "view FAIL ") + line)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
