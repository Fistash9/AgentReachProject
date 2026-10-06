#!/data/data/com.termux/files/usr/bin/python3
"""Stop-хук, ТІНЬОВИЙ режим (2026-10-06): лише лог, нічого не показує й не блокує.

Навіщо: клас помилки «зміст за ярликом» — агент написав «T5 — скіл пошуку»,
а T5 = «Зошит і куратор: перший урок…» (trees/pidrozdil-deepseek.md, T6.4).
Хук на запис файлів дірявий (python/heredoc невидимі) — рецензія DSH
cc-nodeids-1 запропонувала дивитись на ВІДПОВІДЬ агента і спершу міряти
хибні спрацювання в тіні. Порівнює опис поруч з ID («T5 — …», «T5 («…»)»,
«… (T5)») зі справжньою назвою (tools/trees-index.py); розбіжність — коли в
описі ≥2 змістовні слова і жодне не збігається з назвою.

Лог: .claude/logs/node-label-shadow.jsonl. Також: python3 <цей файл> --backtest <jsonl>.
Будь-яка помилка — мовчки (fail-open).
"""
import datetime
import importlib.util
import json
import os
import re
import sys

ROOT = "/data/data/com.termux/files/home/AgentReachProject"
LOG = os.path.join(ROOT, ".claude", "logs", "node-label-shadow.jsonl")
ID = r"\*{0,2}([TQGMZ]\d+(?:\.\d+)*)\*{0,2}"
AFTER = re.compile(ID + r"\s*(?:—|-|:)\s*([^.;|\n«»()]{3,60})")
QUOTE = re.compile(ID + r"\s*\(?«([^»]{3,60})»")
BEFORE = re.compile(r"([\wʼ'-]+(?:\s+[\wʼ'-]+){1,4})\s*\(" + ID + r"\)")
STOP = set("це для що як або вже ще так ні не на в у з із до від по за the and".split())


def load_index():
    spec = importlib.util.spec_from_file_location("ti", os.path.join(ROOT, "tools", "trees-index.py"))
    ti = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ti)
    idx = {}
    import glob
    for p in glob.glob(os.path.join(ROOT, "trees", "**", "*.md"), recursive=True):
        for nid, _, name in ti.nodes(p):
            idx.setdefault(nid, []).append(name)
    return idx


def stems(text):
    return {w[:5].lower() for w in re.findall(r"[\wʼ']{4,}", text) if w.lower() not in STOP}


def check(text, idx):
    out = []
    pairs = [(m.group(1), m.group(2)) for m in AFTER.finditer(text)]
    pairs += [(m.group(1), m.group(2)) for m in QUOTE.finditer(text)]
    pairs += [(m.group(2), m.group(1)) for m in BEFORE.finditer(text)]
    for nid, desc in pairs:
        if nid not in idx:
            continue
        d = stems(desc)
        if len(d) < 2:
            continue
        if not any(d & stems(n) for n in idx[nid]):
            out.append({"id": nid, "desc": desc.strip()[:60], "name": idx[nid][0][:60]})
    return out


def last_text(path):
    texts = []
    for line in open(path, encoding="utf-8"):
        d = json.loads(line)
        if d.get("type") == "user" and isinstance(d["message"]["content"], str):
            texts = []
        if d.get("type") == "assistant":
            texts += [b["text"] for b in d["message"]["content"] if b.get("type") == "text"]
    return "\n".join(texts)


def backtest(path, idx):
    n = 0
    for line in open(path, encoding="utf-8"):
        d = json.loads(line)
        if d.get("type") != "assistant":
            continue
        for b in d["message"]["content"]:
            if b.get("type") == "text":
                for h in check(b["text"], idx):
                    n += 1
                    print(d.get("timestamp", "")[11:19], h)
    print("усього розбіжностей:", n)


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--backtest":
        return backtest(sys.argv[2], load_index())
    data = json.load(sys.stdin)
    if data.get("stop_hook_active"):
        return
    tp = data.get("transcript_path")
    if not tp or not os.path.isfile(tp):
        return
    hits = check(last_text(tp), load_index())
    if hits:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"t": datetime.datetime.now().isoformat(timespec="seconds"),
                                "session": data.get("session_id"), "hits": hits},
                               ensure_ascii=False) + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
