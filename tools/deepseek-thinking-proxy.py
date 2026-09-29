#!/usr/bin/env python3
"""Локальний проксі між Claude Code і DeepSeek: скорочує старе мислення.

НАВІЩО. DeepSeek V4 повертає thinking-блоки повним текстом (Anthropic API їх
редагує, сторонні провайдери — ні), Claude Code їх зберігає і пересилає назад
кожним запитом. За виміром 2026-09-29 мислення — близько двох третин того, що
бачить модель, і контекст росте квадратично: хід N пересилає мислення всіх
попередніх ходів.

ЧОМУ НЕ ВИРІЗАТИ. Прибравши блок, отримуємо 400 «The `content[].thinking` in
the thinking mode must be passed back to the API». Тригер — не виклик
інструмента, а САМ ПАРАМЕТР `tools` у запиті: за офіційною документацією
(api-docs.deepseek.com/guides/thinking_mode) з `tools` треба повертати
reasoning_content усіх попередніх ходів — «навіть для ходів, де модель не
виконувала виклик інструмента»; там же сказано, що він «вплітається в
контекст». Claude Code шле `tools` завжди, тож правило діє на кожен хід.
Тому блок ЛИШАЄТЬСЯ, а скорочується тільки його текст:
поле на місці (400 немає), `tool_use`/`tool_result` не порушені, а підпис
DeepSeek не перевіряє (у нього там UUID, не криптографія).

Перевірено 2026-09-29 прямими запитами до api.deepseek.com: плейсхолдер
замість тексту старого ходу — HTTP 200, вхідні токени 1429 → 772.
Останній асистентський хід лишається повним (семантика clear_thinking keep=1).

ПРО ПРЕФІКС `/deepseek`. Два хуки (tree-focus і класифікатор задач) визначають
DeepSeek-сесію за підрядком "deepseek" в ANTHROPIC_BASE_URL. Тому лончер
указує не на голий 127.0.0.1, а на `http://127.0.0.1:<порт>/deepseek` —
підрядок лишається на місці, і хуки поводяться як досі.
[2026-09-29: tree-focus відтоді в головній DeepSeek-сесії говорить, глушить
лише помічників deepseek-mcp — рішення користувача, M4.5; префікс лишається
потрібним для classify-task.] Цей префікс зрізається
тут перед відправкою нагору.

ЗАПУСК (це робить claude-deepseek.sh, руками не треба):
    python3 tools/deepseek-thinking-proxy.py --port 8799 [--log <шлях>]

Режим без правок — щоб вимкнути, досить не передавати --trim-thinking.
"""
import argparse
import http.client
import http.server
import json
import os
import sys
import time

UPSTREAM = "api.deepseek.com"
SKIP_UP = {"host", "content-length", "connection"}
SKIP_DOWN = {"transfer-encoding", "content-length", "connection"}
PLACEHOLDER = "(thinking omitted)"
PREFIX = "/deepseek"          # щоб ANTHROPIC_BASE_URL лишався впізнаваним для хуків


def trim_thinking(body):
    """Замінює текст thinking-блоків у ВСІХ асистентських ходах, крім останнього.

    Повертає (скільки блоків скорочено, скільки символів зекономлено).
    Будь-яка несподівана форма → 0, тіло лишається як було (проксі не має
    ламати сесію, якщо формат зміниться).
    """
    msgs = body.get("messages")
    if not isinstance(msgs, list):
        return 0, 0
    last_assistant = None
    for i, m in enumerate(msgs):
        if isinstance(m, dict) and m.get("role") == "assistant":
            last_assistant = i
    if last_assistant is None:
        return 0, 0
    blocks = saved = 0
    for i, m in enumerate(msgs):
        if i == last_assistant or not isinstance(m, dict):
            continue
        if m.get("role") != "assistant":
            continue
        content = m.get("content")
        if not isinstance(content, list):
            continue
        for b in content:
            if not isinstance(b, dict) or b.get("type") != "thinking":
                continue
            text = b.get("thinking") or ""
            if len(text) > len(PLACEHOLDER):
                saved += len(text) - len(PLACEHOLDER)
                b["thinking"] = PLACEHOLDER
                blocks += 1
    return blocks, saved


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    trim = False
    log_path = None

    def _log(self, rec):
        if not self.log_path:
            return
        try:
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except OSError:
            pass

    def do_POST(self):
        n = int(self.headers.get("content-length") or 0)
        raw = self.rfile.read(n)
        blocks = saved = 0
        try:
            body = json.loads(raw.decode("utf-8"))
        except Exception:  # noqa: BLE001
            body = None
        if self.trim and isinstance(body, dict):
            blocks, saved = trim_thinking(body)
            if blocks:
                raw = json.dumps(body).encode("utf-8")
        self._log({"ts": time.strftime("%H:%M:%S"), "path": self.path,
                   "model": (body or {}).get("model"),
                   "messages": len((body or {}).get("messages") or []),
                   "trimmed_blocks": blocks, "chars_saved": saved})

        target = self.path
        if target.startswith(PREFIX):
            target = target[len(PREFIX):] or "/"

        hdrs = {k: v for k, v in self.headers.items()
                if k.lower() not in SKIP_UP}
        hdrs["content-length"] = str(len(raw))
        try:
            conn = http.client.HTTPSConnection(UPSTREAM, timeout=600)
            conn.request("POST", "/anthropic" + target, body=raw, headers=hdrs)
            resp = conn.getresponse()
        except Exception:  # noqa: BLE001
            self.send_response(502)
            self.send_header("content-length", "0")
            self.send_header("connection", "close")
            self.end_headers()
            self.close_connection = True
            return
        self.send_response(resp.status)
        for k, v in resp.getheaders():
            if k.lower() not in SKIP_DOWN:
                self.send_header(k, v)
        self.send_header("connection", "close")
        self.end_headers()
        self.close_connection = True
        try:
            while True:
                chunk = resp.read(2048)
                if not chunk:
                    break
                self.wfile.write(chunk)
                self.wfile.flush()
        except OSError:
            pass
        try:
            conn.close()
        except Exception:  # noqa: BLE001
            pass

    def do_GET(self):
        self.send_response(200)
        self.send_header("content-length", "2")
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *a):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--trim-thinking", action="store_true")
    ap.add_argument("--log", default=None)
    a = ap.parse_args()
    Handler.trim = a.trim_thinking
    Handler.log_path = a.log
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    print(f"deepseek-thinking-proxy: 127.0.0.1:{a.port}, "
          f"режим {'скорочення мислення' if a.trim_thinking else 'без правок'}",
          flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    sys.exit(main())
