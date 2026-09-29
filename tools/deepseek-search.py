#!/usr/bin/env python3
"""Прямий веб-пошук DeepSeek з пам'яттю розмови (пілот, 2026-09-29).

Навіщо: власний пошук DeepSeek знаходить першоджерела, яких не показує
WebSearch Claude Code (TROUBLES «Мислення DeepSeek…», дослід 29.09), а прямий
виклик API не платить за обгортку Claude Code.

  python3 tools/deepseek-search.py "питання"            # нова розмова
  python3 tools/deepseek-search.py -c ID "уточнення"     # поглибити ту саму
  --uses N     скільки пошуків дозволено за виклик (за замовчуванням 5)

Історія: .claude/logs/deepseek-search/<ID>.json (під .gitignore). У неї йде
лише текст відповіді + список URL, без сирих результатів пошуку — щоб
продовження були дешеві. Мислення завжди увімкнене (рішення користувача 29.09); його блоки зберігаються: DeepSeek V4
вимагає reasoning назад, коли в запиті є tools (TROUBLES, 2026-09-24/29).
Лише stdlib.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

API = "https://api.deepseek.com/anthropic/v1/messages"
MODEL = "deepseek-flash"  # як у claude-deepseek.sh
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST_DIR = os.path.join(ROOT, ".claude", "logs", "deepseek-search")


def get_key():
    key = os.environ.get("DEEPSEEK_API_KEY")
    if key:
        return key
    with open(os.path.join(ROOT, "agent.py"), encoding="utf-8") as f:
        m = re.search(r"sk-[a-zA-Z0-9]+", f.read())
    if not m:
        sys.exit("deepseek-search: ключ не знайдено в agent.py")
    return m.group(0)


def call(body, key):
    req = urllib.request.Request(
        API, data=json.dumps(body).encode(), method="POST",
        headers={"content-type": "application/json", "x-api-key": key,
                 "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"deepseek-search: HTTP {e.code}: {e.read().decode()[:500]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    ap.add_argument("-c", "--continue", dest="sid")
    ap.add_argument("--uses", type=int, default=5)
    a = ap.parse_args()

    os.makedirs(HIST_DIR, exist_ok=True)
    sid = a.sid or time.strftime("%Y%m%d-%H%M%S")
    path = os.path.join(HIST_DIR, sid + ".json")
    messages = []
    if a.sid:
        if not os.path.exists(path):
            sys.exit(f"deepseek-search: немає розмови {sid}")
        with open(path, encoding="utf-8") as f:
            messages = json.load(f)
    messages.append({"role": "user", "content": a.question})

    body = {
        "model": MODEL, "max_tokens": 32000, "messages": messages,
        "tools": [{"type": "web_search_20250305", "name": "web_search",
                   "max_uses": a.uses}],
        "thinking": {"type": "enabled"},
    }
    resp = call(body, get_key())

    text, sources, keep = [], [], []
    for b in resp.get("content", []):
        t = b.get("type")
        if t == "text":
            text.append(b["text"])
        elif t == "web_search_tool_result":
            for r in b.get("content") or []:
                if isinstance(r, dict) and r.get("url"):
                    sources.append((r.get("title", ""), r["url"]))
        elif t in ("thinking", "redacted_thinking"):
            keep.append(b)
    answer = "".join(text).strip()
    seen, uniq = set(), []
    for title, url in sources:
        if url not in seen:
            seen.add(url)
            uniq.append((title, url))

    u = resp.get("usage", {})
    if not answer:
        print(f"ЗБІЙ: порожня відповідь (stop_reason={resp.get('stop_reason')}); "
              "розмову не збережено.", file=sys.stderr)
    else:
        src_txt = "\n".join(f"- {t} {u_}" for t, u_ in uniq)
        memo = answer + ("\n\nДжерела:\n" + src_txt if src_txt else "")
        messages.append({"role": "assistant",
                         "content": keep + [{"type": "text", "text": memo}]})
        with open(path, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=1)
        print(answer)
        print("\n== Джерела (%d):" % len(uniq))
        for t, url in uniq:
            print(f"- {t} — {url}")

    stu = u.get("server_tool_use") or {}
    print(f"\n== Розмова: {sid} | вх {u.get('input_tokens')} "
          f"(з кешу {u.get('cache_read_input_tokens', 0)}) | вих {u.get('output_tokens')} "
          f"| пошуків {stu.get('web_search_requests', '?')}")


if __name__ == "__main__":
    main()
