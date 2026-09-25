#!/data/data/com.termux/files/usr/bin/python3
"""Живий прогін моделі NVIDIA в консолі: відповідь іде потоком (stream).

Навіщо: подивитися наживо, як модель на build.nvidia.com думає й
відповідає, перш ніж перемикати на неї delegate/хук (2026-09-25).
Нічого не змінює: лише читає .env (NVIDIA_API_KEY) і файли-джерела.

Запуск (в окремій сесії Termux):
  python3 ~/AgentReachProject/tools/nvidia-live.py                  # меню: модель → кейс → відповідь, по колу
                                                                    # Ctrl+C під час відповіді — назад у меню; q — вихід
  python3 ~/AgentReachProject/tools/nvidia-live.py --case N-K1      # один прогін без меню
  python3 ~/AgentReachProject/tools/nvidia-live.py --ask "питання" --model moonshotai/kimi-k3

Замір 2026-09-25: на довгому промпті верифікатора glm-5.3-flash думає
навіть з enable_thinking/thinking=false (параметр, схоже, ігнорується)
і відповідає ~85 с (перший токен ~75 с) — безкоштовний рівень.
"""
import argparse
import json
import os
import re
import sys
import threading
import time
import urllib.request

MODELS = [  # доступність перевірено викликом 2026-09-25, крім позначених «?»
    ("z-ai/glm-5.3-flash", "GLM-5.3 flash — найшвидша з перевірених"),
    ("openai/gpt-oss-20b", "gpt-oss 20B — швидка"),
    ("moonshotai/kimi-k3", "Kimi K3 — повільна (~54 с на коротке)"),
    ("z-ai/glm-5.3", "GLM-5.3 повна — ?"),
    ("nvidia/llama-3.1-nemotron-ultra-253b-v1", "Nemotron Ultra 253B — ?"),
    ("deepseek-ai/deepseek-v4.1-flash", "DeepSeek v4.1 flash — на NVIDIA зависала (72 с / таймаути)"),
]

ROOT = os.path.expanduser("~/AgentReachProject")
URL = "https://integrate.api.nvidia.com/v1/chat/completions"
SRC = os.path.join(ROOT, "tools/verifier-backtest/sources")
PROMPT_FILE = os.path.join(ROOT, ".claude/skills/verify-before-show/verifier-prompt.md")

# Кейси з tools/verifier-backtest/cases-v2.md (очікуваний вердикт моделі НЕ передається)
CASES = {
    "N-E1": ("Якщо HANDOFF.md випадково видалити, історія Done втрачається назавжди, тож цей файл треба окремо бекапити.",
             "Порада агента щодо бекапів.", ["baton-server.mjs.txt", "baton-PROTOCOL.md"], "НІ"),
    "N-E3": ("Anthropic пише, що мульти-агентні системи добре підходять і для досліджень, і для більшості задач із кодом.",
             "Огляд підходів.", ["anthropic-multi-agent.txt"], "НІ"),
    "N-K1": ("Під час baton_pass нові пункти done дописуються до старих, а next, якщо його передано, повністю замінює попередній список.",
             "Пояснення, як працює baton.", ["baton-server.mjs.txt"], "ТАК"),
    "N-K2": ("За даними Anthropic, мульти-агентні системи витрачають приблизно в 15 разів більше токенів, ніж звичайний чат.",
             "Огляд витрат.", ["anthropic-multi-agent.txt"], "ТАК"),
}

GREY, BOLD, GREEN, RED, RESET = "\033[90m", "\033[1m", "\033[32m", "\033[31m", "\033[0m"


def key():
    m = re.search(r"^NVIDIA_API_KEY=(\S+)", open(os.path.join(ROOT, ".env")).read(), re.M)
    if not m:
        sys.exit("Немає NVIDIA_API_KEY у ~/AgentReachProject/.env")
    return m.group(1)


def case_prompt(cid):
    claim, context, files, expected = CASES[cid]
    tpl = re.search(r"```\n(.*?)```", open(PROMPT_FILE, encoding="utf-8").read(), re.S).group(1)
    prompt = tpl.replace("{claim}", claim).replace("{context}", context)
    for f in files:  # як delegate: вміст файлів-джерел додається до промпту
        prompt += f"\n\n=== Файл-джерело: {f} ===\n" + open(os.path.join(SRC, f), encoding="utf-8").read()
    return prompt, claim, files, expected


def run_once(model, case=None, ask=None, thinking=False, max_tokens=2000):
    if ask:
        prompt, expected = ask, None
        print(f"{BOLD}Питання:{RESET} {ask}")
    else:
        prompt, claim, files, expected = case_prompt(case)
        print(f"{BOLD}Кейс {case}{RESET} (очікую: {expected})\n{BOLD}Твердження:{RESET} {claim}\n"
              f"{BOLD}Джерела:{RESET} {', '.join(files)}  ({len(prompt)} символів промпту)")
    print(f"{BOLD}Модель:{RESET} {model} | мислення: {'так' if thinking else 'просимо вимкнути'}\n" + "-" * 60)

    body = {"model": model, "stream": True, "max_tokens": max_tokens, "temperature": 0.3,
            "messages": [{"role": "user", "content": prompt}],
            "chat_template_kwargs": {"enable_thinking": thinking},
            "stream_options": {"include_usage": True}}
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={
        "Authorization": "Bearer " + key(), "content-type": "application/json", "accept": "text/event-stream"})

    t0 = time.time(); first = None; text = []; usage = None; in_reason = False
    started = threading.Event()

    def ticker():  # показує, що скрипт живий, поки модель мовчить
        while not started.wait(5):
            print(f"{GREY}… чекаю першого токена {time.time()-t0:.0f} с{RESET}", flush=True)
    threading.Thread(target=ticker, daemon=True).start()
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            for raw in resp:
                line = raw.decode("utf-8", "ignore").strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                ev = json.loads(data)
                usage = ev.get("usage") or usage
                for ch in ev.get("choices", []):
                    d = ch.get("delta", {})
                    r, c = d.get("reasoning_content"), d.get("content")
                    if (r or c) and first is None:
                        first = time.time() - t0; started.set()
                    if r:
                        if not in_reason:
                            print(f"{GREY}[мислення] ", end=""); in_reason = True
                        print(f"{GREY}{r}{RESET}", end="", flush=True)
                    if c:
                        if in_reason:
                            print(f"{RESET}\n[відповідь] ", end=""); in_reason = False
                        text.append(c); print(c, end="", flush=True)
    except KeyboardInterrupt:  # Ctrl+C — перервати лише цей прогін, повернутись у меню
        started.set()
        print(f"\n{RED}Перервано через {time.time()-t0:.0f} с (Ctrl+C){RESET}")
        return
    except urllib.error.HTTPError as e:
        started.set()
        print(f"\n{RED}HTTP {e.code}: {e.read()[:300]!r}{RESET}")
        return
    except Exception as e:
        started.set()
        print(f"\n{RED}Помилка: {e} (через {time.time()-t0:.0f} с){RESET}")
        return
    started.set()

    total = time.time() - t0
    print(f"{RESET}\n{'-'*60}\nПерший токен: {first or 0:.1f} с | усього: {total:.1f} с | usage: {usage}")
    if expected:
        m = re.search(r"VERDICT:\s*(ТАК|НІ|НЕ МОЖУ ПЕРЕВІРИТИ)", "".join(text))
        got = m.group(1) if m else "не знайдено"
        ok = got == expected
        print(f"{BOLD}Вердикт:{RESET} {got} | очікував: {expected} → {GREEN+'збіг' if ok else RED+'НЕ збіг'}{RESET}")


def menu():
    model, case, thinking = MODELS[0][0], "N-E1", False
    while True:
        print(f"\n{BOLD}=== Моделі ==={RESET}")
        for i, (mid, note) in enumerate(MODELS, 1):
            print(f"  {i}. {mid}  {GREY}{note}{RESET}{'  ←' if mid == model else ''}")
        print(f"  0. ввести інший id моделі")
        s = input(f"Модель [Enter = {model}]: ").strip()
        if s.lower() in ("q", "й"):
            return
        if s == "0":
            model = input("id моделі: ").strip() or model
        elif s.isdigit() and 1 <= int(s) <= len(MODELS):
            model = MODELS[int(s) - 1][0]

        print(f"\n{BOLD}=== Що питати ==={RESET}")
        for cid, (claim, _, _, exp) in CASES.items():
            print(f"  {cid}  (очікую {exp})  {GREY}{claim[:70]}…{RESET}")
        print("  або будь-який свій текст питання")
        s = input(f"Кейс чи питання [Enter = {case}]: ").strip()
        if s.lower() in ("q", "й"):
            return
        ask = None
        if s.upper() in CASES:
            case = s.upper()
        elif s:
            ask = s

        t = input(f"Мислення показати/увімкнути? (т/н) [Enter = {'т' if thinking else 'н'}]: ").strip().lower()
        if t in ("т", "t", "y", "так"):
            thinking = True
        elif t in ("н", "n", "ні"):
            thinking = False

        print()
        run_once(model, case=None if ask else case, ask=ask, thinking=thinking)
        if input(f"\n{BOLD}Enter — ще раз (інша модель/кейс), q — вихід:{RESET} ").strip().lower() in ("q", "й"):
            return


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", choices=sorted(CASES))
    ap.add_argument("--ask")
    ap.add_argument("--model", default=MODELS[0][0])
    ap.add_argument("--thinking", action="store_true", help="увімкнути мислення (повільніше)")
    ap.add_argument("--max-tokens", type=int, default=2000)
    a = ap.parse_args()
    if not a.case and not a.ask:
        try:
            menu()
        except (KeyboardInterrupt, EOFError):
            print("\nВихід.")
        return
    run_once(a.model, case=a.case, ask=a.ask, thinking=a.thinking, max_tokens=a.max_tokens)


if __name__ == "__main__":
    main()
