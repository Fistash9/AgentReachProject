"""
Telegram <-> DeepSeek оркестратор, що делегує кодові задачі Claude Code.

MVP-версія (2026-09-18, концепція — ECOSYSTEM.md "DeepSeek-оркестратор
+ Claude Code через Telegram"): без авто-ротації контексту, без
reflection-циклу, без нагадувань — тільки основний потік: Telegram ->
DeepSeek chat -> (опційно) claude -p -> назад у Telegram.

Секрети — тільки з .env (TELEGRAM_BOT_TOKEN, TELEGRAM_ALLOWED_USER_ID,
DEEPSEEK_API_KEY), .env у .gitignore. Нічого не хардкодити тут.
"""
import os
import re
import subprocess
import time

import requests

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ALLOWED_USER_ID = int(os.environ["TELEGRAM_ALLOWED_USER_ID"])
DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]

# ⚠️ Ризик (задокументовано в ECOSYSTEM.md, п.2 і п.5): headless claude
# без TTY не може підтвердити дозволи, тому для реального виконання
# потрібен bypassPermissions. Дефолт тут — "plan" (безпечний, тільки
# формує план, нічого не виконує) — свідомо, поки немає шару перевірки
# інструкцій DeepSeek. Змінити на bypassPermissions — на власний ризик.
CLAUDE_PERMISSION_MODE = os.environ.get("CLAUDE_PERMISSION_MODE", "plan")
CLAUDE_CWD = os.environ.get("CLAUDE_CWD", os.path.expanduser("~/AgentReachProject"))

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
DEEPSEEK_API = "https://api.deepseek.com/chat/completions"

SYSTEM_PROMPT = (
    "Ти — DeepSeek-оркестратор для персонального проєкту Agent Reach. "
    "Спілкуйся з користувачем звичайно. Якщо задача потребує реальної "
    "роботи з кодом/файлами в проєкті — не намагайся вигадати відповідь "
    "сам, а сформулюй промпт для Claude Code за правилами:\n"
    "- Завжди вказуй цільовий стан (що має бути результатом) і умову "
    "зупинки (коли зупинитись і доповісти, а не намагатись обійти).\n"
    "- Якщо задача включає деструктивні дії (видалення файлів, git push, "
    "зміна залежностей чи конфігурації MCP) — додатково вкажи явно "
    "дозволені і заборонені дії.\n"
    "- Для звичайних дослідницьких/аналітичних задач цього достатньо: "
    "мета + умова зупинки, без зайвих обмежень.\n\n"
    "Виведи РІВНО один рядок у форматі:\n"
    "CLAUDE_CODE: <промпт за правилами вище>\n"
    "Нічого більше в цьому рядку. Інакше відповідай як звичайний чат."
)

CLAUDE_CODE_RE = re.compile(r"^CLAUDE_CODE:\s*(.+)$", re.MULTILINE)


def call_deepseek(history: list[dict]) -> str:
    resp = requests.post(
        DEEPSEEK_API,
        headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
        json={
            "model": "deepseek-chat",
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + history,
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def call_claude_code(prompt: str) -> str:
    try:
        result = subprocess.run(
            [
                "claude", "-p", prompt,
                "--permission-mode", CLAUDE_PERMISSION_MODE,
            ],
            cwd=CLAUDE_CWD,
            capture_output=True,
            text=True,
            timeout=600,
        )
        output = result.stdout.strip() or result.stderr.strip()
        return output[:3500] if output else "(claude code: порожній вивід)"
    except subprocess.TimeoutExpired:
        return "ERROR: claude code timeout (>600с)"
    except FileNotFoundError:
        return "ERROR: команда 'claude' не знайдена (перевір PATH)"


def send_message(chat_id: int, text: str) -> None:
    for i in range(0, len(text), 4000):
        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": chat_id, "text": text[i:i + 4000]},
            timeout=30,
        )


def handle_message(chat_id: int, user_id: int, text: str, history: list[dict]) -> None:
    if user_id != ALLOWED_USER_ID:
        return  # мовчки ігноруємо будь-кого, крім власника

    history.append({"role": "user", "content": text})
    reply = call_deepseek(history)
    history.append({"role": "assistant", "content": reply})

    match = CLAUDE_CODE_RE.search(reply)
    if match:
        claude_prompt = match.group(1).strip()
        send_message(chat_id, f"→ Claude Code ({CLAUDE_PERMISSION_MODE}): {claude_prompt}")
        result = call_claude_code(claude_prompt)
        history.append({"role": "user", "content": f"[Claude Code виконав]:\n{result}"})
        send_message(chat_id, result)
    else:
        send_message(chat_id, reply)


def main() -> None:
    print(f"Bot started. Allowed user: {ALLOWED_USER_ID}. Claude permission mode: {CLAUDE_PERMISSION_MODE}")
    offset = 0
    history: list[dict] = []
    while True:
        try:
            resp = requests.get(
                f"{TELEGRAM_API}/getUpdates",
                params={"offset": offset, "timeout": 30},
                timeout=40,
            )
            resp.raise_for_status()
            for update in resp.json().get("result", []):
                offset = update["update_id"] + 1
                msg = update.get("message")
                if not msg or "text" not in msg:
                    continue
                handle_message(msg["chat"]["id"], msg["from"]["id"], msg["text"], history)
        except requests.RequestException as e:
            print(f"Network error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
