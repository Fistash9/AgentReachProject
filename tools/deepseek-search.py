#!/usr/bin/env python3
"""Прямий веб-пошук DeepSeek з пам'яттю розмови (пілот, 2026-09-29).

Навіщо: власний пошук DeepSeek знаходить першоджерела, яких не показує
WebSearch Claude Code (TROUBLES «Мислення DeepSeek…», дослід 29.09), а прямий
виклик API не платить за обгортку Claude Code.

  python3 tools/deepseek-search.py "питання"            # нова розмова
  python3 tools/deepseek-search.py -c ID "уточнення"     # поглибити ту саму
  --uses N     max_uses для пошуку (за замовчуванням 5) — ПОБАЖАННЯ: сервер
               його не тримає (2026-10-06: 9 і 6 при 5; T6: 8 і 8)

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


CHUNK_TIMEOUT = 600   # тиша між шматками потоку
TOTAL_TIMEOUT = 900   # весь виклик


def read_stream(r, t0):
    """Збирає SSE-потік назад у звичайну відповідь (content, usage, stop_reason).

    Без stream сервер мовчить, поки думає й шукає, і 600-с таймаут на тишу
    рве довгі пошуки (жива проба 2026-10-06, T6.3). Читання по рядку саме
    склеює data:, що рветься між читаннями сокета."""
    resp, blocks, partial_json, first = {}, {}, {}, None
    for line in r:
        if time.time() - t0 > TOTAL_TIMEOUT:
            raise TimeoutError(f"загальна межа {TOTAL_TIMEOUT} с")
        if not line.startswith(b"data:"):
            continue
        if first is None:
            first = time.time() - t0
        d = json.loads(line[5:])
        t = d.get("type")
        if t == "message_start":
            resp = d["message"]
        elif t == "content_block_start":
            blocks[d["index"]] = dict(d["content_block"])
        elif t == "content_block_delta":
            b, dl = blocks[d["index"]], d["delta"]
            k = dl["type"]
            if k == "text_delta":
                b["text"] = b.get("text", "") + dl["text"]
            elif k == "thinking_delta":
                b["thinking"] = b.get("thinking", "") + dl["thinking"]
            elif k == "signature_delta":
                b["signature"] = b.get("signature", "") + dl["signature"]
            elif k == "input_json_delta":
                partial_json[d["index"]] = partial_json.get(d["index"], "") + dl["partial_json"]
        elif t == "message_delta":
            resp.update({k: v for k, v in d["delta"].items() if v is not None})
            resp["usage"] = {**resp.get("usage", {}), **d.get("usage", {})}
        elif t == "error":
            sys.exit(f"deepseek-search: помилка в потоці: {d.get('error')}")
    for i, raw in partial_json.items():
        try:
            blocks[i]["input"] = json.loads(raw)
        except ValueError:
            pass
    resp["content"] = [blocks[i] for i in sorted(blocks)]
    print(f"deepseek-search: перший шматок {first if first is None else round(first, 1)} с, "
          f"усе {time.time() - t0:.1f} с", file=sys.stderr)
    return resp


def call(body, key):
    req = urllib.request.Request(
        API, data=json.dumps({**body, "stream": True}).encode(), method="POST",
        headers={"content-type": "application/json", "x-api-key": key,
                 "anthropic-version": "2023-06-01"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=CHUNK_TIMEOUT) as r:
            if "text/event-stream" in (r.headers.get("content-type") or ""):
                return read_stream(r, t0)
            return json.load(r)  # сервер проігнорував stream
    except urllib.error.HTTPError as e:
        sys.exit(f"deepseek-search: HTTP {e.code}: {e.read().decode()[:500]}")
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
        sys.exit(f"deepseek-search: збій зв'язку через {time.time() - t0:.0f} с — "
                 f"{type(e).__name__}: {getattr(e, 'reason', e)}")


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
    stop = resp.get("stop_reason")
    if not answer:
        print(f"ЗБІЙ: порожня відповідь (stop_reason={stop}); "
              "розмову не збережено.", file=sys.stderr)
    else:
        if stop != "end_turn":
            print(f"УВАГА: відповідь могла обірватись (stop_reason={stop}).",
                  file=sys.stderr)
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
    if not answer:
        sys.exit(1)


if __name__ == "__main__":
    main()
