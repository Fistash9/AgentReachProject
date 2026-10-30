#!/usr/bin/env python3
"""Тести turn-state v0.1 (пісочниця). Запуск: python3 test_turn_state.py. Усі виходи — у $PREFIX/tmp/turn-state/."""
import json, os, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "turn-state.py")
PROJECT = "/data/data/com.termux/files/home/AgentReachProject"
JOURNAL = os.path.expanduser(
    "~/.claude/projects/-data-data-com-termux-files-home-AgentReachProject/a11c12e0-fbbf-421b-82cf-ef510cdcc651.jsonl")
STAMP = time.strftime("%Y%m%d-%H%M%S")
ART = os.path.join(os.environ.get("PREFIX", "/data/data/com.termux/files/usr"), "tmp", "turn-state-tests")  # артефакти тестів — поза репо (2026-10-30: у tools/ вони ламали детермінізм)
os.makedirs(ART, exist_ok=True)
WORK = os.path.join(ART, f"run-{STAMP}")
os.makedirs(WORK)
results = []


def run(*args, stdin=None):
    r = subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True, input=stdin, timeout=300)
    return r.returncode, r.stdout


def lines(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def check(name, ok, detail=""):
    results.append(ok)
    print(f"[{'OK' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


def sh(cwd, *cmd):
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True)


# Копія журналу: живий журнал росте, а детермінізм міряємо на незмінному вході.
JCOPY = os.path.join(WORK, "session.jsonl")
shutil.copyfile(JOURNAL, JCOPY)

# (1) детермінізм
out1 = os.path.join(WORK, "t1.jsonl")
for _ in range(2):
    run("--replay", JCOPY, "--cwd", PROJECT, "--out", out1, "--at", "2026-10-30T00:00:00+00:00")
r = lines(out1)
strip = lambda x: {k: v for k, v in x.items() if k not in ("hash", "prev_hash")}
check("1 детермінізм", len(r) == 2 and strip(r[0]) == strip(r[1]),
      f"записів {len(r)}, однакові без hash/prev_hash: {len(r) == 2 and strip(r[0]) == strip(r[1])}")

# (2) ланцюг
out2 = os.path.join(WORK, "t2.jsonl")
for i in range(3):
    run("--replay", JCOPY, "--cwd", PROJECT, "--out", out2, "--at", f"2026-10-30T00:00:0{i}+00:00")
rc_ok, o_ok = run("--verify", out2)
bad = os.path.join(WORK, "t2-bad.jsonl")
with open(out2, encoding="utf-8") as f:
    ls = f.readlines()
ls[1] = ls[1].replace('"measured_at":"2026-10-30T00:00:01+00:00"', '"measured_at":"2026-10-30T00:00:09+00:00"', 1)
with open(bad, "w", encoding="utf-8") as f:
    f.writelines(ls)
rc_bad, o_bad = run("--verify", bad)
check("2 ланцюг", len(ls) == 3 and rc_ok == 0 and rc_bad == 1,
      f"цілий: rc={rc_ok} «{o_ok.strip()}»; зіпсований середній: rc={rc_bad} «{o_bad.strip()}»")

# (3) кирилиця і пробіл (+ перейменування для перевірки порядку полів у -z)
repo = os.path.join(ART, f"repo-{STAMP}")
os.makedirs(repo)
sh(repo, "git", "init", "-q")
sh(repo, "git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "base")
with open(os.path.join(repo, "старий файл.md"), "w") as f:
    f.write("x\n")
sh(repo, "git", "add", "-A")
sh(repo, "git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "one")
sh(repo, "git", "mv", "старий файл.md", "новий файл.md")
with open(os.path.join(repo, "звіт з пробілом.md"), "w") as f:
    f.write("y\n")
tj = os.path.join(WORK, "t3.jsonl")
with open(tj, "w") as f:
    f.write(json.dumps({"timestamp": "2026-10-30T23:59:00Z", "x": 1}) + "\n")
out3 = os.path.join(WORK, "t3-out.jsonl")
rc3, o3 = run("--replay", tj, "--cwd", repo, "--out", out3, "--at", "2026-10-30T00:00:00+00:00")
ch = lines(out3)[-1]["fields"]["changed"]["value"]
check("3 кирилиця/пробіл", rc3 == 0 and "звіт з пробілом.md" in ch and "новий файл.md" in ch
      and not any("\\" in p or "->" in p for p in ch), f"changed={ch}")

# (4) порожній журнал і репо без комітів
repo4 = os.path.join(ART, f"repo-{STAMP}-empty")
os.makedirs(repo4)
sh(repo4, "git", "init", "-q")
ej = os.path.join(WORK, "empty.jsonl")
open(ej, "w").close()
out4 = os.path.join(WORK, "t4-out.jsonl")
rc4, o4 = run("--replay", ej, "--cwd", repo4, "--out", out4)
f4 = lines(out4)[-1]["fields"] if os.path.exists(out4) else {}
nm = {k: v["value"] for k, v in f4.items() if v["value"] == "не виміряно"}
check("4 порожнє", rc4 == 0 and {"anchor", "commits", "commits_without_node"} <= set(nm)
      and all(f4[k].get("error") for k in nm), f"rc={rc4}, не виміряно: {sorted(nm)}; вивід: {o4.strip()!r}")

# (5) реальний прогін на журналі сесії
out5 = os.path.join(WORK, "t5-out.jsonl")
t = time.monotonic()
rc5, o5 = run("--replay", JCOPY, "--cwd", PROJECT, "--out", out5)
dt = time.monotonic() - t
c5 = lines(out5)[-1]["fields"]["commits"]["value"]
hs = [x.split()[0] for x in c5] if isinstance(c5, list) else []
need = ["4108c83", "008a27e", "332373f", "f7b8a6e"]
check("5 реальний журнал", rc5 == 0 and all(h in hs for h in need), f"commits={hs}; {dt:.1f} с; вивід:\n{o5.strip()}")

print(f"\nПідсумок: {sum(results)}/{len(results)} зелених; файли — {WORK}")
sys.exit(0 if all(results) else 1)
