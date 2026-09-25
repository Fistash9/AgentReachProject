#!/data/data/com.termux/files/usr/bin/python3
"""Перемикач провайдера для delegate і хука-переписувача: DeepSeek ↔ NVIDIA.

Навіщо (2026-09-25): на балансі DeepSeek мало грошей; NVIDIA build.nvidia.com
безкоштовний (умови й ліміти — ECOSYSTEM.md «NVIDIA API»). Модель NVIDIA —
openai/gpt-oss-20b (вибір користувача після живого прогону nvidia-live.py).

Що перемикає:
  - ~/.claude/delegator.json — провайдер і routing delegate (діє з наступного
    виклику, без перезапуску; перед кожною зміною — .bak з часом);
  - ~/AgentReachProject/.provider — стан для хука delegate-prompt-improver.
Що НЕ перемикає: під-сесії `deepseek` (MCP) і claude-deepseek.sh — їм потрібен
формат Anthropic, якого в NVIDIA немає (/v1/messages → 404); вони завжди на DeepSeek.

Запуск:  python3 tools/provider-switch.py            # стан + меню
         python3 tools/provider-switch.py nvidia|deepseek|status
"""
import json
import os
import re
import shutil
import sys
import time

HOME = os.path.expanduser("~")
ROOT = os.path.join(HOME, "AgentReachProject")
STATE = os.path.join(ROOT, ".provider")
DELEG = os.path.join(HOME, ".claude/delegator.json")
DELEG_DS = os.path.join(HOME, ".claude/delegator.deepseek.json")  # збережена конфігурація DeepSeek
PROVIDERS = os.path.join(HOME, ".claude/delegator-providers.json")
NV_MODEL = "openai/gpt-oss-20b"

NVIDIA_PROVIDER = {  # catwalk-схема, як у delegate v3.0.0 (src/providers/registry.mjs)
    "name": "NVIDIA build.nvidia.com (безкоштовно, trial)",
    "id": "nvidia",
    "type": "openai-compat",
    "api_key": "$NVIDIA_API_KEY",
    "api_endpoint": "https://integrate.api.nvidia.com/v1",
    "default_large_model_id": NV_MODEL,
    "default_small_model_id": NV_MODEL,
    "models": [{
        "id": NV_MODEL, "name": "gpt-oss-20b (NVIDIA free)",
        "cost_per_1m_in": 0, "cost_per_1m_out": 0,
        "cost_per_1m_in_cached": 0, "cost_per_1m_out_cached": 0,
        "context_window": 128000, "default_max_tokens": 8192,
        "can_reason": True, "supports_attachments": False,
    }],
}


def read_json(p):
    return json.load(open(p, encoding="utf-8"))


def write_json(p, data):
    tmp = p + ".tmp"
    json.dump(data, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    os.replace(tmp, p)


def backup(p):
    if os.path.exists(p):
        b = f"{p}.bak-{time.strftime('%Y%m%d-%H%M%S')}"
        shutil.copy2(p, b)
        return b


def current():
    try:
        return open(STATE).read().strip() or "deepseek"
    except OSError:
        return "deepseek"


def delegate_has_nvidia_key():
    """Чи бачить запущений процес delegate змінну NVIDIA_API_KEY (інакше треба перезапуск)."""
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            cmd = open(f"/proc/{pid}/cmdline", "rb").read()
            if b"claude-code-deepseek-delegator" not in cmd:
                continue
            return b"NVIDIA_API_KEY=" in open(f"/proc/{pid}/environ", "rb").read()
        except OSError:
            continue
    return None  # процес не знайдено


def status():
    cfg = read_json(DELEG)
    env = open(os.path.join(ROOT, ".env")).read() if os.path.exists(os.path.join(ROOT, ".env")) else ""
    print(f"Провайдер (хук): {current()}")
    print(f"delegate: provider={cfg.get('provider')} routing={cfg.get('routing')}")
    print(f"Ключ NVIDIA у .env: {'є' if re.search(r'^NVIDIA_API_KEY=nvapi-', env, re.M) else 'НЕМАЄ'}")
    k = delegate_has_nvidia_key()
    print("Процес delegate бачить NVIDIA_API_KEY: " +
          {True: "так", False: "НІ — потрібен перезапуск Claude Code (або /mcp → delegate → reconnect)",
           None: "процес не знайдено"}[k])
    print("Під-сесії deepseek і claude-deepseek.sh — завжди DeepSeek (NVIDIA не має формату Anthropic).")


def to_nvidia():
    if not os.path.exists(PROVIDERS):
        write_json(PROVIDERS, [NVIDIA_PROVIDER])
        print(f"Створено {PROVIDERS}")
    cfg = read_json(DELEG)
    if cfg.get("provider") != "nvidia":
        b = backup(DELEG)
        shutil.copy2(DELEG, DELEG_DS)
        print(f"Бекап: {b}; конфігурацію DeepSeek збережено в {DELEG_DS}")
    spec = f"nvidia:{NV_MODEL}"
    cfg.update({"provider": "nvidia", "shortlist": [], "routing": {"read": spec, "write": spec, "reason": spec}})
    write_json(DELEG, cfg)
    open(STATE, "w").write("nvidia\n")
    print(f"→ NVIDIA ({NV_MODEL})")


def to_deepseek():
    if read_json(DELEG).get("provider") != "deepseek":
        b = backup(DELEG)
        if os.path.exists(DELEG_DS):
            shutil.copy2(DELEG_DS, DELEG)
            print(f"Бекап: {b}; відновлено {DELEG_DS}")
        else:
            cfg = read_json(DELEG)
            f = "deepseek-v4-flash"
            cfg.update({"provider": "deepseek", "routing": {"read": f, "write": f, "reason": f}})
            write_json(DELEG, cfg)
            print(f"Бекап: {b}; збереженої конфігурації не було — поставлено deepseek-v4-flash скрізь")
    open(STATE, "w").write("deepseek\n")
    print("→ DeepSeek")


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    if arg is None:
        status()
        arg = {"1": "deepseek", "2": "nvidia"}.get(
            input("\n1) DeepSeek (платно)   2) NVIDIA gpt-oss (безкоштовно)   Enter — нічого не міняти: ").strip())
        if not arg:
            return
    if arg == "nvidia":
        to_nvidia()
    elif arg == "deepseek":
        to_deepseek()
    elif arg != "status":
        sys.exit("Аргумент: nvidia | deepseek | status")
    print()
    status()


if __name__ == "__main__":
    main()
