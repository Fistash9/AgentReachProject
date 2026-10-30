#!/usr/bin/env python3
"""turn-state v0.1 — стан сесії, порахований кодом із фактів, а не агентом (пісочниця 2026-10-30).

Навіщо: прибрати причину рутинних питань користувача «все записано?» і «що лишилось?»
(agents/claude-code/user-questions-2026-10-30/REPORT.md); план — agents/claude-code/status-mech-2026-10-30/PLAN.md.
Кожне поле = значення + джерело; невідоме = «не виміряно» з причиною, а не порожньо
(застереження DSH: «зелений рядок, що бреше»). None або "" у полі теж = «не виміряно».
Журнал — лише дописування, з ланцюгом хешів (prev_hash, hash, script_sha256) як свідком проти підміни;
канон хешу — CANON нижче; перевірка ланцюга — --verify.
Нічого не блокує: вихід 0 (крім --verify: 0 — ланцюг цілий, 1 — розрив).

v0.1 — за рецензією радника ($PREFIX/tmp/ready-status/ADVISOR-3.md): 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.9, §2.
Не взято 1.1 (.claude/logs/ у .gitignore), 1.8 (індекс) — лише заміряно час.

  turn-state.py --replay <transcript.jsonl> --cwd <репо> [--out <jsonl>] [--at <ISO>]
  turn-state.py --hook [--out <jsonl>]   # stdin: JSON хука (session_id, transcript_path, cwd) → systemMessage
  turn-state.py --verify <jsonl>         # перевірка ланцюга prev_hash/hash; код 0/1
"""
import argparse, datetime, hashlib, json, os, re, subprocess, sys

TMP = os.environ.get("PREFIX", "/data/data/com.termux/files/usr") + "/tmp/"
# Шлях іде до лапки/зворотної риски/кінця рядка — пробіл у назві не обриває (1.5).
RE_TMP_RUN = re.compile(re.escape(TMP) + r"[^\"'`\\\n\r<>|]*")
RE_MD_END = re.compile(r"\.md(?![\w.-])")
CANON = dict(ensure_ascii=False, sort_keys=True, separators=(",", ":"))
NM = "не виміряно"


def git(cwd, *args):
    # --no-optional-locks: читання не оновлює .git/index (не змінюємо репо, яке міряємо)
    r = subprocess.run(["git", "--no-optional-locks", "-C", cwd, *args],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()[:200]}")
    return r.stdout


def read_transcript(path):
    recs = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                recs.append(json.loads(line))
            except ValueError:
                continue
    return recs


def first_last_ts(recs):
    ts = [r["timestamp"] for r in recs if isinstance(r, dict) and r.get("timestamp")]
    return (ts[0], ts[-1]) if ts else (None, None)


def field(fn, source):
    try:
        v = fn()
    except Exception as e:  # невідоме не ховаємо і не фарбуємо в «добре»
        return {"value": NM, "source": source, "error": str(e)[:200]}
    if v is None or v == "":  # 1.3: тихе None/"" — теж «не виміряно», з причиною
        return {"value": NM, "source": source, "error": "порожньо: джерело не дало значення"}
    return {"value": v, "source": source}


def git_status(cwd):
    """git status -z → [(XY, path, orig_or_None)]. У -z для R/C спершу ціль, потім джерело (перевірено тестом)."""
    out = git(cwd, "-c", "core.quotePath=false", "status", "--porcelain", "-uall", "-z")
    parts, res, i = out.split("\0"), [], 0
    while i < len(parts):
        e = parts[i]
        i += 1
        if not e:
            continue
        xy, path, orig = e[:2], e[3:], None
        if "R" in xy or "C" in xy:
            orig = parts[i] if i < len(parts) else None
            i += 1
        res.append((xy, path, orig))
    return res


def iter_strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from iter_strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from iter_strings(v)


def tmp_paths_in(s):
    """Шляхи $PREFIX/tmp/…md у рядку. Пробіл не обриває; з кількох кінців «.md» — найкоротший наявний файл."""
    found = set()
    for m in RE_TMP_RUN.finditer(s):
        run = m.group(0)
        starts = [k.start() for k in re.finditer(re.escape(TMP), run)] + [len(run)]
        for a, b in zip(starts, starts[1:]):
            seg = run[a:b]
            cands = [seg[:e.end()] for e in RE_MD_END.finditer(seg)]
            if not cands:
                continue
            existing = [c for c in cands if os.path.isfile(c)]
            found.add(existing[0] if existing else cands[0])
    return found


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def measure(cwd, recs):
    t0, t1 = first_last_ts(recs)

    def anchor_fn():
        if not t0:
            raise RuntimeError("у журналі нема таймстемпів")
        v = git(cwd, "rev-list", "-1", f"--before={t0}", "HEAD").strip()
        if not v:
            raise RuntimeError(f"нема коміту до {t0}")
        return v
    anchor = field(anchor_fn, f"git rev-list -1 --before=<перший запис журналу {t0}> HEAD")
    a = anchor["value"]
    fields = {"anchor": anchor}

    st = {}

    def changed():
        st["v"] = git_status(cwd)
        return sorted(p for _, p, _ in st["v"])
    fields["changed"] = field(changed, "git -c core.quotePath=false status --porcelain -uall -z (для R/C — ціль)")

    def commits():
        if a == NM:
            raise RuntimeError("нема якоря")
        out = git(cwd, "log", "--format=%h %s", f"{a}..HEAD")
        return [l for l in out.splitlines() if l]
    fields["commits"] = field(commits, "git log --format='%h %s' <якір>..HEAD")

    def without_node():
        c = fields["commits"]["value"]
        if not isinstance(c, list):
            raise RuntimeError("коміти не виміряно")
        tdir = os.path.join(cwd, "trees")
        if not os.path.isdir(tdir):
            raise RuntimeError("нема теки trees/")
        texts = []
        for root, dirs, files in os.walk(tdir):  # 1.4: рекурсивно
            dirs.sort()
            for n in sorted(files):
                if n.endswith(".md"):
                    with open(os.path.join(root, n), encoding="utf-8", errors="replace") as f:
                        texts.append(f.read())
        trees = "\n".join(texts)
        return [x.split()[0] for x in c if x.split()[0] not in trees]
    fields["commits_without_node"] = field(
        without_node, "коміти, чий хеш не згаданий у trees/**/*.md (це не «вузол записано»: хеш міг бути дописаний пізніше)")

    def tmp_saved():
        seen = set()
        for r in recs:
            for s in iter_strings(r):
                if TMP in s:
                    seen |= tmp_paths_in(s)
        seen = {p for p in seen if "/bundled-skills/" not in p}  # кеш скілів Claude Code — не звіти
        existing = sorted(p for p in seen if os.path.isfile(p))
        if "v" not in st:
            raise RuntimeError("git status не виміряно")
        repo = [p for p in git(cwd, "ls-files", "-z").split("\0") if p]
        repo += [p for xy, p, _ in st["v"] if xy == "??"]
        tmp_hash = {p: sha256_file(p) for p in existing}
        sizes = {os.path.getsize(p) for p in existing}
        repo_hashes = set()
        for p in set(repo):  # хешуємо лише файли репо з тим самим розміром
            fp = os.path.join(cwd, p)
            try:
                if os.path.isfile(fp) and os.path.getsize(fp) in sizes:
                    repo_hashes.add(sha256_file(fp))
            except OSError:
                continue
        return {"found_in_log": len(seen), "still_exists": len(existing),
                "unsaved": sorted(p for p in existing if tmp_hash[p] not in repo_hashes)}
    fields["tmp_not_saved"] = field(
        tmp_saved, "шляхи $PREFIX/tmp/*.md з журналу; unsaved = файл є, але sha256 вмісту нема серед файлів репо "
                   "(git ls-files -z + untracked зі status -z)")
    return t1, fields


def last_hash(out):
    try:
        with open(out, encoding="utf-8") as f:
            lines = [l for l in f if l.strip()]
        return json.loads(lines[-1])["hash"] if lines else None
    except (OSError, ValueError, KeyError):
        return None


def rec_hash(rec):
    body = {k: v for k, v in rec.items() if k != "hash"}
    return hashlib.sha256(json.dumps(body, **CANON).encode("utf-8")).hexdigest()


def record(session, measured_at, last_event_at, fields, out):
    with open(os.path.abspath(__file__), "rb") as f:
        me = f.read()
    rec = {"session": session, "measured_at": measured_at, "last_event_at": last_event_at, "fields": fields,
           "prev_hash": last_hash(out), "script_sha256": hashlib.sha256(me).hexdigest()}
    rec["hash"] = rec_hash(rec)
    return rec


def verify(path):
    prev, n = None, 0
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except ValueError as e:
                print(f"broken at line {i}: не JSON ({e})")
                return 1
            if n and rec.get("prev_hash") != prev:
                print(f"broken at line {i}: prev_hash={rec.get('prev_hash')} ≠ hash попереднього {prev}")
                return 1
            if rec.get("hash") != rec_hash(rec):
                print(f"broken at line {i}: hash не збігається з перерахованим")
                return 1
            prev, n = rec["hash"], n + 1
    print(f"ok: {n} ланок")
    return 0


def summary(fields):
    def v(k, sub=None):
        x = fields[k]["value"]
        if x == NM:
            return x
        return len(x[sub]) if sub else len(x)
    unm = [k for k, f in fields.items() if f["value"] == NM]
    t = fields["tmp_not_saved"]["value"]
    tmp_line = (f"Звітів лише в tmp (вміст не знайдено в проєкті): {v('tmp_not_saved', 'unsaved')}"
                + (f" (у журналі {t['found_in_log']}, ще існують {t['still_exists']})" if t != NM else ""))
    lines = [f"Не закомічено файлів: {v('changed')}",
             f"Комітів сесії: {v('commits')}; чий хеш не згаданий у trees/: {v('commits_without_node')}",
             tmp_line]
    if unm:
        lines.append("Не виміряно: " + ", ".join(f"{k} ({fields[k].get('error', '')[:60]})" for k in unm))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay")
    ap.add_argument("--cwd")
    ap.add_argument("--hook", action="store_true")
    ap.add_argument("--out", default=None)
    ap.add_argument("--at", default=None, help="ISO-час вимірювання замість поточного UTC (для відтворюваних тестів)")
    ap.add_argument("--verify", metavar="JSONL")
    a = ap.parse_args()
    if a.verify:
        try:
            return verify(a.verify)
        except OSError as e:
            print(f"broken: {e}")
            return 1
    try:
        if a.hook:
            inp = json.load(sys.stdin)
            tpath, cwd = inp.get("transcript_path"), inp.get("cwd") or os.getcwd()
            session = inp.get("session_id") or (os.path.basename(tpath).split(".")[0] if tpath else None)
        else:
            tpath, cwd = a.replay, a.cwd or os.getcwd()
            session = os.path.basename(tpath).split(".")[0]
        out = a.out or os.path.join(cwd, ".claude", "logs", "turn-state.jsonl")
        measured_at = a.at or datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
        last_event_at, fields = measure(cwd, read_transcript(tpath))
        rec = record(session, measured_at, last_event_at, fields, out)
        with open(out, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, **CANON) + "\n")
        text = summary(fields)
        print(json.dumps({"systemMessage": text}, ensure_ascii=False) if a.hook else text)
    except Exception as e:  # хук не має ламати хід
        print(json.dumps({"systemMessage": f"turn-state: не виміряно ({str(e)[:120]})"}, ensure_ascii=False) if a.hook
              else f"turn-state: помилка {e}", file=sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
