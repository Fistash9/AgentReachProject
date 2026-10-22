#!/usr/bin/env python3
"""Перевірка заяв агента за журналом сесії — лише звіт, не хук.

Запуск (session-close, крок 2.6):
    python3 ~/AgentReachProject/tools/claimcheck/claimcheck.py            # поточна сесія
    python3 ~/AgentReachProject/tools/claimcheck/claimcheck.py <file.jsonl>
Виводить відповіді з позначками — кандидати на перечитування, НЕ вирок:
  E1 — число з іменником, якого нема як окремого токена у виводі
       інструментів цього ходу чи в повідомленнях користувача;
  E3 — "працює/перевірено" у ході без жодного запуску Bash;
  E5 — "неможливо/не існує" у ході без пошуку (Web*, deepseek, curl…);
  E6 — заява про СТАН ("закрито/не працює/даних немає/недоступно") у БУДЬ-ЯКОМУ тексті ходу, а в
       командах ходу менше двох різних доказів (ps/pgrep, tail/cat/wc логу, ls/find, curl). Рецензія
       сесії 940a8b9a (DeepSeek, 22.10, механізм M3): «Obsidian закрито» за одним ps (процеси жили),
       «точного списку немає» без ls теки, «github.com не відповідає» після одного збою.
Код виходу завжди 0. Нічого не пише, не блокує.

Тест на історії (2026-09-23, TROUBLES.md): E1 шумить (~1/3 відповідей
у сесії з багатьма підрахунками), E3 ловить погано, E5 точний (2 з 2,
0 хибних, але налаштований на цих даних). Тому це звіт у кінці сесії,
а не Stop-хук. Каркас — ідеї provenly claim-check (decide,
stripQuoted), розбір журналу — як у groundtruth (обидва MIT).
"""
import glob
import json
import os
import re
import sys

# --- stripQuoted (provenly claim-check.mjs:54-59, перенесено) ---
def strip_quoted(t):
    t = re.sub(r"```[\s\S]*?```", " ", t)
    t = re.sub(r"`[^`\n]*`", " ", t)
    t = re.sub(r'"[^"\n]{0,200}"', " ", t)
    t = re.sub(r"[«“][^»”\n]{0,200}[»”]", " ", t)
    t = re.sub(r"(\*\*|__|~~)", "", t)  # markdown-розмітка не розриває фрази
    return t

NOUNS = (r"(коміт\w*|перевір\w*|файл\w*|рядк\w*|рядок|місц\w*|хук\w*|тест\w*|"
         r"знахід\w*|запис\w*|помил\w*|відповід\w*|виклик\w*|сесі\w*|пакет\w*|"
         r"правил\w*|скіл\w*|ход\w*|раз\w*|розрив\w*|пункт\w*|проблем\w*|блок\w*)")
E1_RE = re.compile(r"(?<![\w.:/#-])(\d{1,5})\s+" + NOUNS, re.I)
E3_RE = re.compile(r"\b(працю[єю]\w*|запускаю?ть?ся|перевірено|спрацюва\w*|пройшл[иао]|"
                   r"works|verified|passes|passed)\b", re.I)
E5_RE = re.compile(r"(неможлив\w*|зробити не можна|не існує|не маю підтверджених|"
                   r"impossible|can't be done|cannot be done)", re.I)
SEARCH_TOOLS = ("WebSearch", "WebFetch", "mcp__deepseek__deepseek", "mcp__delegate__delegate")
SEARCH_CMD = re.compile(r"\b(curl|wget|gh |npm view|pip index)\b")
E6_RE = re.compile(r"(закрито|закритий|закрита|закриті|закрився|закрилась|закрилися|не працює|не запущен\w*|"
                   r"(?:списку|даних|логу|запису|знімка)\b[^.\n]{0,40}немає|немає (?:даних|списку)|"
                   r"недоступн\w*|не відповіда\w*|зупинено|убито|вбито)", re.I)
E6_KINDS = {"ps": re.compile(r"\b(ps|pgrep|pidof)\b"),
            "log": re.compile(r"\b(tail|cat|head|sed -n)\b[^|;\n]*\.(log|jsonl|txt)\b"),
            "ls": re.compile(r"(^|[;&|]\s*|\s)ls\s|\bfind\s|\bstat\s"),
            "net": re.compile(r"\b(curl|wget|ping)\b")}
E6_WINDOW = 3  # доказ — лише останні 3 Bash-команди ПЕРЕД текстом із заявою (хід з віконцями триває годинами)


def parse_turns(path):
    """Хід = від справжнього повідомлення користувача (рядок, не tool_result)
    до наступного. Повертає список ходів: user_text, final_text, tools, evidence, model."""
    turns, cur = [], None
    for line in open(path, encoding="utf-8"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        m = d.get("message")
        if not isinstance(m, dict):
            continue
        if d.get("type") == "user":
            c = m.get("content")
            if isinstance(c, str) and not d.get("isMeta"):
                cur = {"user": c, "final": "", "tools": [], "evidence": [], "model": "",
                       "ts": d.get("timestamp", ""), "texts": [], "cmds": [], "seq": []}
                turns.append(cur)
            elif isinstance(c, list) and cur is not None:
                for x in c:
                    if x.get("type") == "tool_result":
                        v = x.get("content")
                        s = v if isinstance(v, str) else " ".join(
                            y.get("text", "") for y in (v or []) if isinstance(y, dict))
                        cur["evidence"].append(s)
        elif d.get("type") == "assistant" and cur is not None:
            cur["model"] = m.get("model", cur["model"])
            for x in m.get("content", []):
                if x.get("type") == "text":
                    cur["final"] = x.get("text", "")  # останній текстовий блок = відповідь на Stop
                    cur["texts"].append(x.get("text", ""))
                    cur["seq"].append(("text", x.get("text", "")))
                elif x.get("type") == "tool_use":
                    cur["tools"].append(x.get("name", ""))
                    if x.get("name") == "Bash":
                        cur["cmds"].append(str((x.get("input") or {}).get("command", "")))
                        cur["seq"].append(("cmd", cur["cmds"][-1]))
                    cur["evidence"].append(json.dumps(x.get("input", ""), ensure_ascii=False))
    return turns


def decide(final, tools, evidence, user_texts, model=""):
    """Чиста функція: позначки для однієї відповіді."""
    if model.startswith("deepseek"):
        return []
    text = strip_quoted(final)
    ev = "\n".join(evidence)
    allowed = ev + "\n" + "\n".join(user_texts)
    flags = []
    for m in E1_RE.finditer(text):
        n = m.group(1)
        if not re.search(r"(?<![\w.:/-])" + n + r"(?![\w.:/-])", allowed):
            flags.append(("E1", f"{n} {m.group(2)}"))
    searched = any(t in SEARCH_TOOLS for t in tools) or bool(SEARCH_CMD.search(ev))
    for m in E5_RE.finditer(text):
        if not searched:
            flags.append(("E5", m.group(1)))
    ran = any(t in ("Bash",) for t in tools)
    for m in E3_RE.finditer(text):
        if re.search(r"\bне\s+(?:\w+\s+)?$", text[max(0, m.start() - 20):m.start()]):
            continue  # заперечення: "ще не пройшли"
        if not ran:
            flags.append(("E3", m.group(1)))
    return flags


def decide_e6(seq):
    """E6: для кожного тексту із заявою про стан — різновиди доказів у E6_WINDOW Bash-командах перед ним."""
    found, cmds = [], []
    for kind, val in seq:
        if kind == "cmd":
            cmds.append(val)
            continue
        m = E6_RE.search(strip_quoted(val))
        if not m:
            continue
        recent = cmds[-E6_WINDOW:]
        kinds = {k for k, r in E6_KINDS.items() if any(r.search(c) for c in recent)}
        if len(kinds) < 2:
            found.append(("E6", f"{m.group(1)} (доказів: {', '.join(sorted(kinds)) or 'жодного'})"))
    return found[:3]


PROJECT_LOGS = os.path.expanduser(
    "~/.claude/projects/-data-data-com-termux-files-home-AgentReachProject")


def session_model(path):
    """Модель першої відповіді асистента у файлі ('' якщо нема)."""
    for line in open(path, encoding="utf-8"):
        if '"type":"assistant"' not in line and '"type": "assistant"' not in line:
            continue
        try:
            m = json.loads(line).get("message") or {}
        except ValueError:
            continue
        if m.get("model"):
            return m["model"]
    return ""


def current_session():
    """Найсвіжіший журнал основної сесії: модель claude-*, не haiku
    (haiku — хук delegate-prompt-improver), не deepseek (під-сесії)."""
    files = sorted(glob.glob(os.path.join(PROJECT_LOGS, "*.jsonl")),
                   key=os.path.getmtime, reverse=True)
    for f in files[:40]:
        model = session_model(f)
        if model.startswith("claude-") and "haiku" not in model:
            return f
    return None


def main(argv):
    path = argv[1] if len(argv) > 1 else current_session()
    if not path or not os.path.exists(path):
        print("claimcheck: журнал сесії не знайдено")
        return 0
    turns = parse_turns(path)
    users, rows = [], []
    for i, t in enumerate(turns, 1):
        users.append(t["user"])
        fl = decide(t["final"], t["tools"], t["evidence"], users, t["model"])
        if not t["model"].startswith("deepseek"):
            fl += decide_e6(t["seq"])
        if fl:
            rows.append((i, t["ts"][11:16], fl))
    print(f"claimcheck: {os.path.basename(path)[:8]} — відповідей {len(turns)}, "
          f"з позначками {len(rows)} (кандидати на перечитування, не вирок)")
    for i, ts, fl in rows:
        print(f"  #{i} {ts} " + "; ".join(f"{c}: {w}" for c, w in fl[:5]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
