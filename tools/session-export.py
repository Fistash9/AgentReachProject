#!/usr/bin/env python3
"""Експорт журналу сесії Claude Code у текст для зовнішнього рецензента (2026-10-06).

Навіщо: рецепт session-close (крок «Зовнішня перевірка») щоразу виконувався
вручну, і 2026-10-06 ручний експорт загубив назви інструментів (рецензент
DeepSeek прийняв ToolSearch за «битий WebSearch»), повідомлення посеред ходу
(queued_command) і підказки хуків. Цей скрипт робить рецепт однаково щоразу.

  python3 tools/session-export.py [JSONL] [--from "фраза"] [-o файл]

JSONL за замовчуванням — найновіший журнал проєкту. --from — почати з першого
блоку, що містить фразу. Виводи інструментів не обрізаються. Особисте
(email, git-логін, ключі sk-/ghp_/AKIA, auth-коди) вирізається. Лише stdlib.
"""
import argparse
import glob
import json
import os
import re
import sys

PROJ = os.path.expanduser(
    "~/.claude/projects/-data-data-com-termux-files-home-AgentReachProject")
REDACT = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "[email]"),
    (re.compile(r"sk-[A-Za-z0-9_-]{16,}"), "[ключ]"),
    (re.compile(r"ghp_[A-Za-z0-9]{20,}"), "[ключ]"),
    (re.compile(r"AKIA[A-Z0-9]{16}"), "[ключ]"),
    (re.compile(r"(?i)(auth_?code|code)=[A-Za-z0-9_-]{12,}"), r"\1=[код]"),
    (re.compile(r"Fistash9"), "[логін]"),
    (re.compile(r"mur4ik93"), "[логін]"),
]


def text_of(c):
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "\n".join(x.get("text", "") if isinstance(x, dict) else str(x) for x in c)
    return json.dumps(c, ensure_ascii=False)


def blocks(path):
    names = {}
    for line in open(path, encoding="utf-8"):
        d = json.loads(line)
        t = d.get("type")
        if t == "attachment":
            a = d.get("attachment", {})
            if a.get("type") == "hook_additional_context":
                yield "ПІДКАЗКА ХУКА (бачив асистент)", text_of(a.get("content"))
            elif a.get("type") == "queued_command":
                yield "КОРИСТУВАЧ (посеред ходу)", a.get("prompt", "")
            continue
        if t not in ("user", "assistant"):
            continue
        c = d["message"]["content"]
        if isinstance(c, str):
            yield ("КОРИСТУВАЧ" if t == "user" else "АСИСТЕНТ"), c
            continue
        for b in c:
            k = b.get("type")
            if k == "text":
                yield ("КОРИСТУВАЧ" if t == "user" else "АСИСТЕНТ"), b["text"]
            elif k == "tool_use":
                names[b["id"]] = b["name"]
                yield f"АСИСТЕНТ → {b['name']}", json.dumps(b["input"], ensure_ascii=False)
            elif k == "tool_result":
                n = names.get(b.get("tool_use_id"), "?")
                err = " (ПОМИЛКА)" if b.get("is_error") else ""
                yield f"РЕЗУЛЬТАТ {n}{err}", text_of(b.get("content"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonl", nargs="?")
    ap.add_argument("--from", dest="start")
    ap.add_argument("-o", "--out")
    a = ap.parse_args()
    path = a.jsonl or max(glob.glob(os.path.join(PROJ, "*.jsonl")), key=os.path.getmtime)
    out, on = [], a.start is None
    for who, body in blocks(path):
        if not on and a.start in body:
            on = True
        if on:
            out.append(f"### {who}\n{body}\n")
    if not out:
        sys.exit(f"session-export: фразу не знайдено в {path}")
    s = "\n".join(out)
    for rx, rep in REDACT:
        s = rx.sub(rep, s)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(s)
    else:
        sys.stdout.write(s)
    print(f"session-export: {os.path.basename(path)} → блоків {len(out)}, "
          f"символів {len(s)}, байт {len(s.encode())}", file=sys.stderr)


if __name__ == "__main__":
    main()
