#!/data/data/com.termux/files/usr/bin/python3
"""Звірка цитат у відповідях перевіряльників (T11, 2026-10-20).

Навіщо: вердикт «НІ» на E зараховувався попередньо — чи цитата справді є в джерелі, ніхто не
перевіряв (BACKLOG 2026-10-14 «ручна звірка 18 відповідей»). run_api_v3.py рахує quotes_found
лише для API-прогонів і в таблицю це не йде; прогони Claude (run_claude_v3.py) цитат не звіряють.
Тут — однаково для всіх: кожна цитата в лапках (≥12 символів) шукається в джерелах кейсу після
нормалізації (пробіли, **, \\", «…»); не знайдена цілком — шукаються її шматки між «…»/«...».

  python3 quote_audit.py            # набір v3;  VBT_SET=v4 python3 quote_audit.py — v4
  python3 quote_audit.py --list     # + перелік відповідей без жодної знайденої цитати

Вихід: на модель — цитат усього / знайдено цілком / частково / не знайдено, і скільки вердиктів
(за прогонами) не мають жодної знайденої цитати, окремо для «НІ» на E (опора зарахованого бала).
«нема» ≠ «вигадано»: на 20.10 серед них є переказ (регістр, пропущена дужка — E1 gpt-oss v4) і склейки
шматків коду; «частк.» — регістр змінено, «…» або склейка двох цитат, кожен шматок є в джерелі.
"""
import argparse, collections, os, re

import run_claude_v3 as rc
import table_v3 as tb

# цитата — те, що в лапках перед «(файл…)»: так пишуть формат v2 і розмітник; без якоря парсер брав
# за цитату текст МІЖ двома цитатами (« (файл); ») — перевірено 2026-10-20 на виводі DeepSeek v4
# gpt-oss пише «(current_session)» без розширення і обгортає цитату в «<…>» — якір: будь-яка дужка одразу після лапок
QRE = re.compile(r'[“"«](.{12,}?)[”"»]\s*\([^()]*\)', re.S)


def norm(s):
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)  # markdown-посилання → текст (Opus цитує відрендерене, E6 v3)
    s = s.replace('\\\\', '\\').replace('\\"', '"').replace('\\n', '\n').replace("**", "").replace("`", "")
    return re.sub(r"\s+", " ", s).strip()


def check(q, src):
    q = norm(q).strip("<>").replace("<…>", "…").strip()
    if q in src:
        return "full"
    if q.lower() in src.lower():
        return "part"  # регістр змінено
    # «…»/«...» усередині і склеєні дві цитати («a" (файл); "b» — лапки без якоря файлу)
    parts = [p.strip(" .,;:\"«»") for p in re.split(r'…|\.\.\.|"\s*(?:\([^)]*\))?\s*[;,і/]?\s*"|"\s*/\s*"\d+:\s*', q)]
    parts = [p for p in parts if len(p) >= 12]
    if parts and any(p in src for p in parts):
        return "part"
    return "none"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    cases = {c["id"]: c for c in rc.cases()}
    srcs = {cid: norm("\n".join(open(os.path.join(rc.SRC, f), encoding="utf-8").read()
                                for f in c["files"])) for cid, c in cases.items()}
    print(f"набір {rc.SET}")
    print(f"{'модель':<44} цитат цілком частк. нема  без-опори(відп.) з них НІ-на-E")
    for name, by in tb.load().items():
        cnt = collections.Counter()
        bare = []
        for cid, rs in by.items():
            if cid not in cases:
                continue
            for r in rs:
                text = r.get("content") or r.get("result") or ""
                qm = re.search(r"QUOTES:(.*?)(?:\nREASON:|\Z)", text, re.S)
                qs = QRE.findall(qm.group(1) if qm else text)
                res = [check(q, srcs[cid]) for q in qs]
                cnt["q"] += len(res)
                for x in res:
                    cnt[x] += 1
                # «НЕ МОЖУ» без цитати — законно (джерело мовчить); без опори рахуються лише ТАК і НІ
                if r.get("verdict") in ("ТАК", "НІ") and not any(x != "none" for x in res):
                    cnt["bare"] += 1
                    nie_e = cid[0] == "E" and r.get("verdict") == "НІ"
                    cnt["bareE"] += nie_e
                    bare.append(f"{cid}:{r.get('verdict')}{'*' if nie_e else ''}")
        print(f"{name:<44} {cnt['q']:>5} {cnt['full']:>6} {cnt['part']:>6} {cnt['none']:>4} "
              f"{cnt['bare']:>16} {cnt['bareE']:>13}")
        if a.list and bare:
            print(f"   без опори: {' '.join(bare)}")
    print("\n* — «НІ» на E без жодної знайденої цитати: бал зараховано, опори в тексті немає.")


if __name__ == "__main__":
    main()
