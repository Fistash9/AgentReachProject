#!/usr/bin/env python3
"""chain-record — одна дія «записав ланку відео» = оновлено журнал, каркас і BACKLOG.

2026-11-08: створено (служить: Перше довге відео › ланцюжок за курсом ›
автоматизація). Корінь: записи CHAIN.md, каркас у PROMPT-v3.md, BACKLOG і
GAPS відставали, бо оновлювались лише з пам'яті агента.

Що робить за один запуск:
  1. CHAIN.md — дописує рядок «Ланка N (дата, decision): evidence — [тег]».
  2. PROMPT-v3.md, таблиця «## Каркас: жорстке і змінне» — у рядку ланки N
     дописує в комірку «Доказ» «; дата: C:<новий рядок>[, evidence]»;
     з --passed міняє «[не пройдено …]» / «[частково пройдено …]» на
     «[пройдено дата]» лише в цьому рядку.
  3. BACKLOG.md — підпункт «Статус змінився (дата): ланка N — decision» під
     рядком «ПЕРШИМ У НАСТУПНІЙ СЕСІЇ» (після його наявних підпунктів).
  4. GAPS.md — лише друкує відкриті «- [ ]», що стосуються ланки.
Режим --check — друкує рядки CHAIN «Ланка N», не процитовані як C:<рядок>
у «Доказ» рядка N (відставання каркаса), код 1, якщо такі є.

Атомарність: усі нові тексти будуються й перевіряються в пам'яті ДО першого
запису; помилка (ланки нема в таблиці тощо) → код 2, жоден файл не змінено.
"""
import argparse
import datetime
import difflib
import os
import re
import sys
import tempfile

# 2026-11-08: позначки «не пройдено» в каркасі мають різний хвіст
# («— з курсу, не перевірено», «— у курсі нема, не перевірено», «: абзаци…»).
PENDING_MARK_RE = re.compile(r"\[(?:не пройдено|частково пройдено)[^\]]*\]")
SECTION_HEADING = "## Каркас: жорстке і змінне"
BACKLOG_ANCHOR = "ПЕРШИМ У НАСТУПНІЙ СЕСІЇ"
AUTHOR = "claude-code"


class RecordError(Exception):
    """Помилка, після якої нічого не записується (код 2)."""


def read_text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def write_text_atomic(path, text):
    # 2026-11-08: запис через тимчасовий файл у тій самій теці + os.replace,
    # щоб обрив посеред запису не лишив напівфайл.
    folder = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=folder, prefix=".chain-record-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def link_pattern(link):
    """Регекс «ланка N» без збігу 5 ↔ 5б (2026-11-08)."""
    return re.compile(r"ланк\w*\s+" + re.escape(link) + r"(?![\w])", re.IGNORECASE)


def table_row_index(lines, link):
    """Індекс рядка таблиці каркаса для ланки link; RecordError, якщо нема."""
    try:
        start = next(i for i, l in enumerate(lines) if l.startswith(SECTION_HEADING))
    except StopIteration:
        raise RecordError(f"розділ «{SECTION_HEADING}» не знайдено") from None
    row_re = re.compile(r"^\|\s*" + re.escape(link) + r"\.\s")
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("## "):
            break
        if row_re.match(lines[i]):
            return i
    raise RecordError(f"ланки «{link}» нема в таблиці каркаса")


def cited_chain_lines(cell):
    """Множина номерів рядків CHAIN, процитованих у комірці як C:n або C:a–b."""
    cited = set()
    for a, b in re.findall(r"C:(\d+)(?:[–-](\d+))?", cell):
        cited.update(range(int(a), int(b or a) + 1))
    return cited


def update_table_row(row, short_date, chain_line_no, evidence, passed):
    """Новий текст рядка таблиці: дописаний «Доказ» і, з passed, нова позначка."""
    cells = row.rstrip("\n").split("|")
    # cells: ['', ланка, жорстке, змінне, перевірка, доказ, ''] — 2026-11-08
    if len(cells) < 4 or cells[-1].strip():
        raise RecordError("рядок таблиці не закінчується на «|»: " + row[:60])
    proof = f"C:{chain_line_no}" + (f", {evidence}" if evidence else "")
    cells[-2] = cells[-2].rstrip() + f"; {short_date}: {proof} "
    new_row = "|".join(cells)
    if passed:
        new_row = PENDING_MARK_RE.sub(f"[пройдено {short_date}]", new_row)
    return new_row + "\n"


def build_chain(text, line):
    """CHAIN.md + новий запис через порожній рядок; повертає (текст, № рядка)."""
    body = text if text.endswith("\n") else text + "\n"
    body += "\n" + line + "\n"
    return body, body.count("\n")


def build_backlog(text, short_date, link, decision):
    lines = text.splitlines(keepends=True)
    try:
        anchor = next(i for i, l in enumerate(lines) if BACKLOG_ANCHOR in l)
    except StopIteration:
        raise RecordError(f"у BACKLOG нема рядка «{BACKLOG_ANCHOR}»") from None
    pos = anchor + 1
    # наявні підпункти — рядки з відступом одразу після якоря (2026-11-08)
    while pos < len(lines) and lines[pos].startswith((" ", "\t")):
        pos += 1
    sub = f"  - Статус змінився ({short_date}): ланка {link} — {decision}\n"
    return "".join(lines[:pos] + [sub] + lines[pos:])


def open_gaps(text, link, decision):
    """Відкриті «- [ ]» GAPS, де є «ланк* N» або ≥2 слова (≥6 літер) з decision."""
    pat = link_pattern(link)
    words = {w.lower() for w in re.findall(r"\w{6,}", decision)}
    hits = []
    for no, line in enumerate(text.splitlines(), 1):
        if not line.startswith("- [ ]"):
            continue
        low = line.lower()
        if pat.search(line) or sum(w in low for w in words) >= 2:
            hits.append((no, line))
    return hits


def lagging_entries(chain_text, prompt_text):
    """Рядки CHAIN «Ланка N…», яких не цитує «Доказ» рядка N каркаса.

    Повертає список (№ рядка CHAIN, ланка, причина). 2026-11-08.
    """
    lines = prompt_text.splitlines(keepends=True)
    out = []
    for no, line in enumerate(chain_text.splitlines(), 1):
        m = re.match(r"^Ланка\s+(\w+)[,\s(]", line)
        if not m:
            continue
        link = m.group(1)
        try:
            row = lines[table_row_index(lines, link)]
        except RecordError as exc:
            out.append((no, link, str(exc)))
            continue
        if no not in cited_chain_lines(row.split("|")[-2]):
            out.append((no, link, f"C:{no} нема в «Доказ» рядка {link}"))
    return out


def plan_changes(paths, link, decision, evidence, passed, today):
    """Усі нові тексти в пам'яті: {path: (старий, новий)}. Нічого не пише."""
    short = today.strftime("%d.%m")
    old = {k: read_text(p) for k, p in paths.items()}

    prompt_lines = old["prompt"].splitlines(keepends=True)
    row_i = table_row_index(prompt_lines, link)  # спершу перевірка — 2026-11-08

    entry = (f"Ланка {link} ({short}, {decision}): "
             f"{evidence or 'доказ не вказано'} — [{AUTHOR}, {today.isoformat()}]")
    chain_new, chain_no = build_chain(old["chain"], entry)

    prompt_lines[row_i] = update_table_row(prompt_lines[row_i], short, chain_no,
                                           evidence, passed)
    new = {
        "chain": chain_new,
        "prompt": "".join(prompt_lines),
        "backlog": build_backlog(old["backlog"], short, link, decision),
    }
    return {paths[k]: (old[k], new[k]) for k in new}, open_gaps(old["gaps"], link, decision)


def print_diff(changes):
    for path, (before, after) in changes.items():
        sys.stdout.writelines(difflib.unified_diff(
            before.splitlines(keepends=True), after.splitlines(keepends=True),
            fromfile=path, tofile=path + " (нове)", n=0))


def parse_args(argv):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--link", help="ланка, напр. 5 або 5б")
    p.add_argument("--decision", help="рішення/подія словами користувача")
    p.add_argument("--passed", action="store_true", help="ланку пройдено")
    p.add_argument("--evidence", default="", help="доказ, напр. файл:рядок")
    p.add_argument("--dry-run", action="store_true", help="лише diff")
    p.add_argument("--check", action="store_true", help="знайти відставання каркаса")
    p.add_argument("--date", help="дата YYYY-MM-DD (для тестів; типово — сьогодні)")
    p.add_argument("--root", default=".", help="корінь проєкту")
    p.add_argument("--chain", default="agents/claude-code/lancyuzhok-kursu-2026-11-08/CHAIN.md")
    p.add_argument("--prompt", default="agents/claude-code/video-links-2026-11-07/PROMPT-v3.md")
    p.add_argument("--backlog", default="BACKLOG.md")
    p.add_argument("--gaps", default="GAPS.md")
    args = p.parse_args(argv)
    if not args.check and not (args.link and args.decision):
        p.error("потрібні --link і --decision (або --check)")
    if args.passed and not args.evidence:
        p.error("--passed без --evidence: «пройдено» без доказу не записую")
    return args


def main(argv=None):
    args = parse_args(argv)
    paths = {k: os.path.join(args.root, getattr(args, k))
             for k in ("chain", "prompt", "backlog", "gaps")}
    try:
        if args.check:
            lag = lagging_entries(read_text(paths["chain"]), read_text(paths["prompt"]))
            for no, link, why in lag:
                print(f"ВІДСТАЄ: CHAIN:{no} ланка {link} — {why}")
            print(f"відстає записів: {len(lag)}")
            return 1 if lag else 0
        today = (datetime.date.fromisoformat(args.date) if args.date
                 else datetime.date.today())
        changes, gaps = plan_changes(paths, args.link, args.decision,
                                     args.evidence, args.passed, today)
    except (RecordError, OSError) as exc:
        print(f"ПОМИЛКА: {exc}; нічого не записано", file=sys.stderr)
        return 2
    if args.dry_run:
        print_diff(changes)
    else:
        for path, (_, text) in changes.items():
            write_text_atomic(path, text)
        print("записано: " + ", ".join(changes))
    for no, line in gaps:
        print(f"GAPS:{no} відкрито — закрити? {line[:160]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
