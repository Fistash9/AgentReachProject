#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""memory-audit.py — повторюваний аудит пам'яті claude-code проєкту AgentReachProject.

ЛИШЕ ЧИТАННЯ: скрипт не пише нічого — ані в пам'ять, ані в проєкт (open(..., "r")).
Код виходу (як у tools/check-links.py): 0 — знахідок немає, 1 — є знахідки.

Запуск (шляхи абсолютні, CWD/HOME/proot значення не мають):
  python3 /data/data/com.termux/files/home/AgentReachProject/tools/memory-audit.py
  python3 /data/data/com.termux/files/home/AgentReachProject/tools/memory-audit.py --pairs
  python3 .../tools/memory-audit.py --pairs --only snapshot-baton-before-pass
  python3 .../tools/memory-audit.py --list

Що перевіряється:
  (1) frontmatter: наявність name, description, metadata.node_type (+ name == ім'я файлу);
  (2) description <= 300 символів (поріг лінту Claude Code);
  (3) посилання на файли проєкту існують, а "file:рядок"/"file:A-B" — у межах файлу;
  (4) [[ім'я]] веде на наявний запис пам'яті.

--pairs друкує для кожного запису: опис + тіло + текст цитованих рядків file:N —
щоб модель могла звірити зміст окремо (скрипт моделей не викликає).

Як бібліотека (файл має дефіс, тому звичайний import не працює):
  import importlib.util
  spec = importlib.util.spec_from_file_location(
      "memory_audit", "<root>/tools/memory-audit.py")
  m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
  findings = m.audit()            # -> list[dict]: file, check, msg
  pairs = m.pairs()               # -> list[dict]: name, desc, body, refs
"""
import argparse
import glob
import os
import re
import sys

# --- шляхи: абсолютні, без "~" (у proot "~" = /root — пастка) -----------------
MEM_DIR_DEFAULT = ("/data/data/com.termux/files/home/.claude/projects/"
                   "-data-data-com-termux-files-home-AgentReachProject/memory")


def _mem_dir():
    """Каталог пам'яті: env-перевизначення -> абсолютна константа -> HOME-fallback."""
    env = os.environ.get("MEMORY_AUDIT_MEM")
    if env:
        return os.path.abspath(env)
    if os.path.isdir(MEM_DIR_DEFAULT):
        return MEM_DIR_DEFAULT
    # fallback: той самий proєктний слаг під поточним HOME (напр. інший хост)
    slug = "-data-data-com-termux-files-home-AgentReachProject"
    return os.path.join(os.path.dirname(os.path.dirname(MEM_DIR_DEFAULT)),
                        slug, "memory")


def _project_dir():
    """Корінь проєкту від __file__ (скрипт лежить у <root>/tools/)."""
    env = os.environ.get("MEMORY_AUDIT_ROOT")
    if env:
        return os.path.abspath(env)
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.dirname(here)


MEM_DIR = _mem_dir()
PROJECT_DIR = _project_dir()

DESC_MAX = 300          # поріг лінту Claude Code для description
CITE_MAX_LINES = 60     # скільки рядків цитати друкувати на одне посилання
SKIP_FILES = {"MEMORY.md"}

# префікси проєктних шляхів, які реально вживані в пам'яті
PATH_PREFIXES = ("trees/", "tools/", "agents/", "script-agent/",
                 "reference-analyzer/", ".baton/", ".claude/", ".trash/")
# кореневі документи проєкту, на які посилаються як NAME:N або NAME.md
ROOT_DOCS = {"BACKLOG", "RULES", "RULES-WHY", "TROUBLES", "CONTEXT", "WEEKLY",
             "HANDOFF", "USER_PROFILE", "README", "TRASH", "JOURNAL"}

TOKEN_RE = re.compile(
    r"(?<![\w/.\-])((?:\.?[\w\-]+/)*[\w\-]+(?:\.[\w\-]+)*)(?::(\d+)(?:-(\d+))?)?")


def resolve_ref(project, ref):
    """Шлях посилання -> абсолютний шлях (BACKLOG:90 -> BACKLOG.md)."""
    path = ref["path"]
    target = os.path.join(project, path)
    if (not os.path.exists(target) and ref["start"] is not None
            and not path.endswith(".md") and path in ROOT_DOCS):
        target = os.path.join(project, path + ".md")
    return target


# ------------------------------------------------------------------ розбір ----
def split_front(text):
    """-> (рядки frontmatter, тіло). frontmatter — між першими двома '---'."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i], "\n".join(lines[i + 1:])
    return None, text


def unquote(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1]
    return v.replace('\\"', '"')


def fm_value(fm, key, indent=0):
    """Значення ключа на заданому рівні відступу (підтримує блокові |- / >-)."""
    if fm is None:
        return None
    pat = re.compile(r"^ {%d}%s:\s*(.*)$" % (indent, re.escape(key)))
    for idx, line in enumerate(fm):
        m = pat.match(line)
        if not m:
            continue
        val = m.group(1).strip()
        if val in ("|", ">", "|-", ">-", "|+", ">+"):
            parts = []
            for nxt in fm[idx + 1:]:
                if nxt.strip() == "" or len(nxt) - len(nxt.lstrip()) > indent:
                    parts.append(nxt.strip())
                else:
                    break
            return unquote(" ".join(p for p in parts if p))
        return unquote(val)
    return None


def fm_node_type(fm):
    if fm is None:
        return None
    for idx, line in enumerate(fm):
        if re.match(r"^metadata:\s*$", line):
            for nxt in fm[idx + 1:]:
                if nxt.strip() == "":
                    continue
                if not nxt.startswith((" ", "\t")):
                    break
                m = re.match(r"^\s+node_type:\s*(.*)$", nxt)
                if m:
                    return unquote(m.group(1))
    return None


def is_ref(path, start):
    """Чи схожий токен на посилання на файл проєкту (а не на прозу)."""
    if any(c in path for c in "<>*"):
        return False
    if path.endswith("/"):                      # каталог — не перевіряємо
        return False
    if path.startswith(PATH_PREFIXES):
        # проза на кшталт "tools/solutions" не має розширення -> не чіпаємо
        return bool(os.path.splitext(path)[1]) or start is not None
    stem = path[:-3] if path.endswith(".md") else path
    if stem in ROOT_DOCS and (start is not None or path.endswith(".md")):
        return True
    return False


def extract_refs(text):
    """-> список {'raw','path','start','end'} — посилання в тексті (без дублів)."""
    out, seen = [], set()
    for m in TOKEN_RE.finditer(text):
        path, start, end = m.group(1), m.group(2), m.group(3)
        if not is_ref(path, start):
            continue
        key = (path, start, end)
        if key in seen:
            continue
        seen.add(key)
        out.append({"raw": m.group(0), "path": path,
                    "start": int(start) if start else None,
                    "end": int(end) if end else None})
    return out


def read_file(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def memory_files(mem=None):
    mem = mem or MEM_DIR
    return [p for p in sorted(glob.glob(os.path.join(mem, "*.md")))
            if os.path.basename(p) not in SKIP_FILES]


# ------------------------------------------------------------------ аудит -----
def audit(mem_dir=None, project=None):
    """Перевірки (1)-(4). -> список знахідок [{'file','check','msg'}]."""
    mem = mem_dir or MEM_DIR
    proj = project or PROJECT_DIR
    files = memory_files(mem)
    findings = []

    def bad(fname, check, msg):
        findings.append({"file": fname, "check": check, "msg": msg})

    if not os.path.isdir(mem):
        return [{"file": "-", "check": "0",
                 "msg": "каталог пам'яті не знайдено: %s" % mem}]

    stems = {os.path.basename(p)[:-3] for p in files}

    for path in files:
        fname = os.path.basename(path)
        try:
            text = read_file(path)
        except OSError as e:
            bad(fname, "0", "не читається: %s" % e)
            continue
        fm, body = split_front(text)

        # (1) обов'язкові поля
        if fm is None:
            bad(fname, "1", "немає frontmatter (--- ... ---)")
            fm = []
        name = fm_value(fm, "name")
        desc = fm_value(fm, "description")
        ntype = fm_node_type(fm)
        if not name:
            bad(fname, "1", "немає поля name")
        elif name != os.path.basename(path)[:-3]:
            bad(fname, "1", "name=%r не збігається з іменем файлу" % name)
        if not desc:
            bad(fname, "1", "немає поля description")
        if not ntype:
            bad(fname, "1", "немає metadata.node_type")

        # (2) довжина опису
        if desc and len(desc) > DESC_MAX:
            bad(fname, "2", "description %d символів > %d" % (len(desc), DESC_MAX))

        # (3) посилання на файли проєкту (і в описі, і в тілі)
        for ref in extract_refs((desc or "") + "\n" + body):
            target = resolve_ref(proj, ref)
            if not os.path.exists(target):
                bad(fname, "3", "шлях не існує: %s" % ref["path"])
                continue
            if ref["start"] is None or os.path.isdir(target):
                continue
            try:
                n = len(read_file(target).splitlines())
            except OSError as e:
                bad(fname, "3", "не читається %s: %s" % (ref["path"], e))
                continue
            end = ref["end"] or ref["start"]
            if ref["start"] < 1 or end < ref["start"] or end > n:
                bad(fname, "3", "рядки %s:%s поза межами (у файлі %d рядків)"
                    % (ref["path"], ref["raw"].split(":", 1)[1], n))

        # (4) [[ім'я]] -> наявний запис пам'яті
        for link in sorted(set(re.findall(r"\[\[([^\]\[|]+?)\]\]", body))):
            if link.strip() not in stems:
                bad(fname, "4", "[[%s]] — такого запису пам'яті немає"
                    % link.strip())

    return findings


def pairs(mem_dir=None, project=None, only=None):
    """Пари для звірки моделлю: опис + тіло + цитовані рядки file:N."""
    mem = mem_dir or MEM_DIR
    proj = project or PROJECT_DIR
    out = []
    for path in memory_files(mem):
        stem = os.path.basename(path)[:-3]
        if only and stem not in only:
            continue
        try:
            text = read_file(path)
        except OSError as e:
            out.append({"name": stem, "path": path, "desc": "", "body": "",
                        "refs": [], "error": str(e)})
            continue
        fm, body = split_front(text)
        refs = []
        for ref in extract_refs((fm_value(fm, "description") or "") + "\n" + body):
            target = resolve_ref(proj, ref)
            item = dict(ref)
            if not os.path.exists(target):
                item["note"] = "НЕ ІСНУЄ: %s" % ref["path"]
            elif ref["start"] is None:
                try:
                    item["note"] = "файл існує, %d рядків (без :N)" % len(
                        read_file(target).splitlines())
                except OSError:
                    item["note"] = "файл є, не читається"
            else:
                lines = read_file(target).splitlines()
                end = ref["end"] or ref["start"]
                chunk = lines[ref["start"] - 1:end]
                item["cited"] = [("%d: %s" % (ref["start"] + i, ln))
                                 for i, ln in enumerate(chunk)]
                if len(chunk) > CITE_MAX_LINES:
                    item["cited"] = item["cited"][:CITE_MAX_LINES] + \
                        ["... (%d рядків пропущено)" % (len(chunk) - CITE_MAX_LINES)]
            refs.append(item)
        out.append({"name": stem, "path": path, "desc": fm_value(fm, "description") or "",
                    "body": body.strip(), "refs": refs, "error": None})
    return out


# ------------------------------------------------------------------ CLI -------
def print_report(findings):
    print("memory-audit: пам'ять %s" % MEM_DIR)
    print("memory-audit: проєкт %s" % PROJECT_DIR)
    total = len(memory_files())
    print("memory-audit: файлів пам'яті %d, знахідок %d" % (total, len(findings)))
    for f in findings:
        print(" - [%s] %s: %s" % (f["check"], f["file"], f["msg"]))
    return 1 if findings else 0


def print_pairs(items):
    print("# memory-audit --pairs: пам'ять %s" % MEM_DIR)
    print("# проєкт %s" % PROJECT_DIR)
    print("# записів: %d" % len(items))
    for it in items:
        print("")
        print("=" * 72)
        print("### %s   (%s)" % (it["name"], it["path"]))
        print("ОПИС: %s" % it["desc"])
        print("ТІЛО:")
        print(it["body"])
        print("ПОСИЛАННЯ (шлях + цитовані рядки):")
        if not it["refs"]:
            print("  — немає посилань на файли проєкту")
        for ref in it["refs"]:
            if "cited" in ref:
                print("  * %s:" % ref["raw"])
                for ln in ref["cited"]:
                    print("      %s" % ln)
            else:
                print("  * %s -> %s" % (ref["raw"], ref.get("note", "")))
        if it["error"]:
            print("ПОМИЛКА ЧИТАННЯ: %s" % it["error"])
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Аудит пам'яті claude-code (лише читання)")
    ap.add_argument("--pairs", action="store_true",
                    help="опис + тіло + цитовані рядки file:N (для звірки моделлю)")
    ap.add_argument("--only", default="",
                    help="через кому: обмежити --pairs цими записами")
    ap.add_argument("--list", action="store_true", help="лише перелік файлів пам'яті")
    args = ap.parse_args(argv)

    if args.list:
        for p in memory_files():
            print(os.path.basename(p))
        return 0

    findings = audit()
    if args.pairs:
        only = {n.strip() for n in args.only.split(",") if n.strip()}
        print_pairs(pairs(only=only))
        print("")
        print("memory-audit: знахідок %d (код виходу %d)"
              % (len(findings), 1 if findings else 0))
        return 1 if findings else 0
    return print_report(findings)


if __name__ == "__main__":
    try:
        code = main()
        sys.stdout.flush()
    except BrokenPipeError:      # напр. "| head" — без шуму в stderr
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        code = 0
    except KeyboardInterrupt:
        code = 130
    sys.exit(code)
