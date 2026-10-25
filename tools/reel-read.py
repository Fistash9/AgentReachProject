#!/usr/bin/env python3
"""Розбір рілса/відео за посиланням: опис + розшифровка звуку + перевірка переліку (Q4.4, 2026-10-25).

Навіщо (користувач 2026-10-25: «і ти чомусь навчився з останнього відео?» → «вчитись і робити дії а не балакати»):
розборів рілсів у TROUBLES 8, щоразу вручну (yt-dlp → ffmpeg → whisper), шлях до whisper шукав заново; 24.10
`-l auto` мовчки загубив перші ~28 с (рілс Deh5yf2xL3s, пункти 1–3). Тому: мова визначається окремим кроком (-dl),
розшифровка йде з ЯВНОЮ мовою, а нумерований перелік перевіряється на суцільність — пропуск названо, а не тиша
(whisper перекручує й самі номери: «Первое» → «Ярою», TROUBLES 2026-10-03 «Whisper перекручує назви й числа»).

Запуск:  python3 tools/reel-read.py <URL> [--lang ru|uk|en] [--out DIR]
Вихід: DIR/meta.txt (автор, дата, тривалість, опис), DIR/t.txt (текст з таймкодами); на екран — те саме + перелік.
Тека за замовчуванням — $PREFIX/tmp/reel-<id> (завантажене — недовірене: окрема тека, скрипт поза нею).
"""
import argparse, glob, json, os, re, subprocess, sys

W = os.path.expanduser("~/termux-whisper/whisper.cpp")
WHISPER = os.path.join(W, "build", "bin", "whisper-cli")  # у PATH немає (TROUBLES 2026-09-17 «Локальна транскрипція»)
MODEL = os.path.join(W, "models", "ggml-small.bin")
TMP = os.environ.get("PREFIX", "/data/data/com.termux/files/usr") + "/tmp"

# порядкові 1–10 (ru, uk) на початку речення: «Второе он…», «В четвертой…», «Шостий…»
ORD = [("перв", "перш"), ("втор", "друг"), ("трет",), ("четв",), ("пят", "п'ят", "пʼят"), ("шест", "шост"),
       ("седьм", "сьом"), ("восьм",), ("девят", "дев'ят", "девʼят"), ("десят",)]
CARD = ("пят", "п'ят", "пʼят", "шест", "девят", "дев'ят", "девʼят", "десят")
PREP = {"в", "во", "у", "на", "и", "і", "а", "ну", "та", "й"}  # слово перед порядковим: «В четвертой…», «А третье…»
DRUG = ("другий", "друге", "друга", "другі", "другу", "другої")  # «друг*» без цього — «друг», «с другом», не порядкове
LAST = re.compile(r"^(?:ну\s+)?(?:и\s+|і\s+)?(?:последн|останн)", re.I)


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def numbers(lines):
    """Номери пунктів переліку за першими двома словами кожного речення; повертає (знайдені, чи є «останнє»)."""
    found, last, prev = {}, False, ""
    for ts, text in lines:
        fresh = not prev or prev[-1] in ".!?:"  # перше речення рядка починається тут, а не триває з минулого («…вместо\n20.»)
        prev = text.strip() or prev
        for k, sent in enumerate(re.split(r"(?<=[.!?])\s+", text)):
            words = sent.strip().lower().split()
            head = words[:2]
            if not head:
                continue
            if LAST.match(" ".join(sent.strip().lower().split()[:3])):
                last = True
            # цифра — лише «N.» / «N)» / «пункт N»; голе «10 сервисов», «20 кусков» — число з розповіді, не пункт
            m = re.match(r"^(\d{1,2})[.)]$", head[0])
            if m and k == 0 and not fresh:
                m = None
            if not m and head[0] in ("пункт", "пункта", "пункти") and len(head) > 1:
                m = re.match(r"^(\d{1,2})[.)]?$", head[1])
            if m:
                found.setdefault(int(m.group(1)), ts)
                continue
            # порядкове слово — перше в реченні або після прийменника/сполучника («друг» у «с другом» не береться)
            cand = [words[0]] + ([words[1]] if len(words) > 1 and words[0] in PREP else [])
            for w in cand:
                for n, stems in enumerate(ORD, 1):
                    # «ь» після основи — кількісне («п'ять», «шесть», «девять»), не порядкове (перевірка 25.10, DdQxr38AcHT);
                    # лише для основ, спільних з кількісними: «третье» — порядкове (рілс Deh5yf2xL3s)
                    if stems == ("втор", "друг") and not (w.startswith("втор") or w in DRUG):
                        continue
                    if any(w.startswith(s) and not (s in CARD and w[len(s):].startswith("ь")) for s in stems):
                        found.setdefault(n, ts)
    return found, last


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--lang", help="мова звуку; без неї — визначення окремим кроком")
    ap.add_argument("--out")
    a = ap.parse_args()
    rid = re.search(r"/(?:reel|p|shorts)/([^/?#]+)", a.url)
    out = a.out or os.path.join(TMP, "reel-" + (rid.group(1) if rid else "x"))
    os.makedirs(out, exist_ok=True)

    r = run(["yt-dlp", "-q", "--no-warnings", "--write-info-json", "-f", "ba", "-o", "a.%(ext)s", a.url], cwd=out)
    info = glob.glob(os.path.join(out, "a.info.json"))
    audio = [p for p in glob.glob(os.path.join(out, "a.*")) if not p.endswith((".json", ".wav"))]
    if not info or not audio:
        sys.exit(f"yt-dlp не дав звуку/опису: {r.stderr.strip()[:300]}")
    d = json.load(open(info[0], encoding="utf-8"))
    wav = os.path.join(out, "a.wav")
    run(["ffmpeg", "-loglevel", "error", "-y", "-i", audio[0], "-ar", "16000", "-ac", "1", wav])
    dur = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", wav]).stdout.strip()
    meta = (f"автор: {d.get('uploader')} ({d.get('channel')}) · дата: {d.get('upload_date')} · тривалість: "
            f"{float(dur or 0):.0f} с\nопис: {d.get('description')}\n")

    lang = a.lang
    if not lang:
        det = run([WHISPER, "-m", MODEL, "-l", "auto", "-dl", "-f", wav]).stderr
        m = re.search(r"auto-detected language: (\w+) \(p = ([\d.]+)\)", det)
        lang = m.group(1) if m else "ru"
        meta += f"мова: {lang} (визначено, p={m.group(2) if m else '?'}; розшифровка — з явною мовою)\n"
    else:
        meta += f"мова: {lang} (задано)\n"

    t = run([WHISPER, "-m", MODEL, "-l", lang, "-f", wav]).stdout
    lines = re.findall(r"^\[(\d\d:\d\d:\d\d)\.\d+ --> [^\]]+\]\s*(.*)$", t, re.M)
    open(os.path.join(out, "meta.txt"), "w", encoding="utf-8").write(meta)
    open(os.path.join(out, "t.txt"), "w", encoding="utf-8").write(t)
    print(meta)
    print("\n".join(f"[{ts}] {x}" for ts, x in lines))

    found, last = numbers(lines)
    # тривога лише за справжнього переліку: ≥2 порядкових/нумерованих пункти (інакше це числа з розповіді)
    if len(found) >= 2:
        top = max(found)
        miss = [n for n in range(1, top + 1) if n not in found]
        print(f"\nперелік: знайдено {', '.join(f'{n} ({found[n]})' for n in sorted(found))}"
              + ("; є «останнє»" if last else ""))
        print(f"⚠ пропущено номери {', '.join(map(str, miss))} — шукай біля сусідніх таймкодів (whisper перекручує "
              f"номери) або в кадрах" if miss else "перелік суцільний")
    print(f"\nтека: {out}")


if __name__ == "__main__":
    main()
