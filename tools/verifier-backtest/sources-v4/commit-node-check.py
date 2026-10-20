#!/usr/bin/env python3
"""git commit-msg: коміт механізму без коду вузла → відмова (Q12, 2026-10-18).

Механізми — хуки, скіли, правила, налаштування, tools/, mods/, tests/, config/, RULES/CLAUDE/AGENTS.
Повідомлення має містити код вузла ([GMTQZ]число, напр. Q12, M11.4) або «без вузла: <чому>».
Чому git-хук, а не PreToolUse: замок за текстом команди (cfd43bd) обходили git add -A / . /
commit -am / pathspec / абсолютний шлях і хибно блокував -F файл і власний текст команди (аудит DSH,
CONTEXT.md «Оновлення 2026-10-18», перевірено запуском). Тут — фактичний індекс і фактичне повідомлення.
Коміти DSH (Agent: dsh) не перевіряються, доки він не погодиться (правило про його робочий процес).
Обхід свідомо: git commit --no-verify. Підключення: .git/hooks/commit-msg (поза git), як pre-commit."""
import re
import subprocess
import sys

RE_NODE = re.compile(r"(?<![\w.])[GMTQZ]\d+(?:\.\d+)*(?![\w])")
RE_NO_NODE = re.compile(r"без\s+вузла\s*:", re.I)
RE_MECH = re.compile(r"^(?:\.claude/(?:hooks|skills|settings|rules)|tools/|mods/|tests/|config/|"
                     r"RULES\.md|RULES-WHY\.md|CLAUDE\.md|AGENTS\.md)")


def main(path):
    msg = open(path, encoding="utf-8", errors="replace").read()
    body = "\n".join(l for l in msg.splitlines() if not l.startswith("#"))
    if re.search(r"^Agent:\s*dsh\b", body, re.M | re.I) or body.lstrip().startswith(("Merge ", "Revert ")):
        return 0
    files = subprocess.run(["git", "diff", "--cached", "--name-only"],
                           capture_output=True, text=True, check=True).stdout.split()  # збій git → виняток → stderr
    mech = [f for f in files if RE_MECH.match(f)]
    if not mech or RE_NODE.search(body) or RE_NO_NODE.search(body):
        return 0
    sys.stderr.write(
        "commit-msg: коміт змінює механізми (" + ", ".join(mech[:4]) + ("…" if len(mech) > 4 else "")
        + "), а в повідомленні нема коду вузла.\nRULES.md:29 «ціль записується… коміт». Допиши код вузла "
        "(назва: python3 tools/trees-index.py <код>) і запис у вузол, або рядок «без вузла: <чому>».\n")
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1]))
    except Exception as e:  # збій перевірки не блокує коміт (fail-open), але кажемо про нього
        sys.stderr.write(f"commit-msg: перевірку вузла пропущено ({type(e).__name__}: {e})\n")
        sys.exit(0)
