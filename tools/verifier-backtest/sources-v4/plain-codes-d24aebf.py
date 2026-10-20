#!/usr/bin/env python3
"""plain-codes — коди задач без назви словами в тексті для користувача (2026-10-16).

Навіщо: користувач 15–16.10 — «я вже казав що не розумію шифри … і відповідаю не
зрозумівши»; правило: «розшифровувати потрібно раз у повідомленні, або залишати дерево».
Пам'ять ask-questions-one-at-a-time-plainly (калібрування 07.10) мала це правило, але без
перевірки: у сесії 0d07dbd7 код без назви — у 21 з 49 блоків, у 5 минулих — 92 з 338.

Код (G2.5, M4.4, T11…) вважається розшифрованим, якщо в тому самому тексті хоча б раз
  - після нього йдуть ≥2 слова («G2.4 нагадування при переході», рядок дерева «[ ] T7 Відео-агент…»), або
  - він стоїть у дужках після слів («перевірка підказки в DeepSeek-сесіях (M4.4)»).
Інлайн `команди й шляхи` не рахуються; блоки ``` (дерева) — рахуються.
Читачі: .claude/hooks/plain-ask-hook.py (питання — до показу), answer-gate-shadow-hook.py
(відповідь — голос «codes»). Лише stdlib.

  python3 tools/plain-codes.py <jsonl>   # бектест журналу сесії
"""
import json
import re
import sys

CODE = r"[GMQTZ]\d{1,2}(?:\.\d{1,2}){0,2}"
TOK = re.compile(r"(?<![\w./#-])(" + CODE + r")(?![\w])")
WORD = r"[A-Za-zА-Яа-яІіЇїЄєҐґʼ'«-]{3,}"


def visible(text):
    return re.sub(r"`[^`\n]*`", "", text.replace("```", ""))


def undecoded(text):
    """Відсортований список кодів без жодного розшифрування в тексті."""
    t = visible(text)
    found, ok = set(TOK.findall(t)), set()
    for c in found:
        e = re.escape(c)
        # назва — у тому самому рядку (не слова з наступних рядків, напр. варіанти «Так»)
        after = re.compile(r"(?<![\w.])" + e + r"(?![\w.])[ \t\]\[x?>~*:—–-]*(?:" + WORD
                           + r")(?:[ \t,]+" + WORD + r")")
        before = re.compile(WORD + r"[^\n()]{0,80}\([^()\n]*(?<![\w.])" + e
                            + r"(?![\w.])[^()\n]*\)")
        if after.search(t) or before.search(t):
            ok.add(c)
    return sorted(found - ok)


def ask_text(tool_input):
    """Увесь текст питань AskUserQuestion, який бачить користувач."""
    parts = []
    for q in (tool_input or {}).get("questions") or []:
        parts += [str(q.get("question", "")), str(q.get("header", ""))]
        for o in q.get("options") or []:
            parts += [str(o.get("label", "")), str(o.get("description", "")),
                      str(o.get("preview", ""))]
    return "\n".join(parts)


def backtest(path):
    blocks = hits = 0
    for line in open(path, encoding="utf-8", errors="ignore"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("type") != "assistant":
            continue
        for b in (d.get("message") or {}).get("content") or []:
            if b.get("type") == "text":
                t, kind = b["text"], "текст"
            elif b.get("type") == "tool_use" and b.get("name") == "AskUserQuestion":
                t, kind = ask_text(b.get("input")), "питання"
            else:
                continue
            blocks += 1
            u = undecoded(t)
            if u:
                hits += 1
                print(kind, ", ".join(u)[:90])
    print(f"блоків {blocks}; з кодами без назви {hits}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        backtest(sys.argv[1])
