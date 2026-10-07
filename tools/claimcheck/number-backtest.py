#!/usr/bin/env python3
"""Бектест «числа без опори» на транскриптах сесії (не хук, лише звіт).

Запуск:
    python3 number-backtest.py <файл.jsonl> [--turn N,...] [--last] [--all]

Що робить: іде по ходах журналу і для кожного ходу шукає числа-твердження
(число + іменник), яких НЕ оперто парою «число+іменник» у рядках виводів
ТОГО САМОГО ходу. Логіка витягу, опори й класифікації — у тіньовому хуку:
модуль .claude/hooks/number-claim-shadow-hook.py імпортується, а не
копіюється (єдине джерело правди, інакше бектест і хук розійдуться).

Ходи й докази беремо з hook.iter_turns (не з claimcheck.parse_turns):
нова логіка вимагає УСІ текстові блоки ходу, а не лише останній, і вивід
tool_result без input-ів tool_use (власний текст агента — не доказ) та без
результатів AskUserQuestion (відлуння власного тексту). claimcheck.py
лишається незмінним і далі обслуговує свої E1/E3/E5.

  --turn N,...  розмічені (еталонні) ходи: ті, де помилка «число без опори»
                справді була. Дає рядок «впіймано / пропущено / хибних», де
                хибні = позначені ходи поза розміткою (як у backtest.py поруч).
  --last        для порівняння: брати лише ОСТАННІЙ текстовий блок ходу (як
                бачив би Stop через last_assistant_message). Типово — усі
                блоки (як тепер робить хук; у звіті закриття сесії текст
                живе в середині ходу, і «останній блок» його не бачить).
  --all-text    застарілий синонім типової поведінки (приймається, нічого не
                змінює) — щоб старі виклики не ламались.
  --all         друкувати й ходи без жодного твердження.

Межа методу (перевірено на живому журналі, див. звіт): перевіряється лише
НАЯВНІСТЬ пари «число+іменник» у рядку виводу, не сенс твердження. Число,
узяте зі справжнього виводу, але приписане не тому іменнику, не ловиться;
голе число без іменника твердженням не вважається.
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

HOOK = os.path.join(ROOT, ".claude", "hooks", "number-claim-shadow-hook.py")


def load_hook():
    spec = importlib.util.spec_from_file_location("number_claim_shadow_hook", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main(argv):
    if len(argv) < 2:
        print(__doc__.strip().splitlines()[2].strip())
        return 2
    path = argv[1]
    labels, last_only, show_all = set(), False, False
    i = 2
    while i < len(argv):
        a = argv[i]
        if a == "--turn" and i + 1 < len(argv):
            labels = {int(x) for x in argv[i + 1].split(",") if x.strip()}
            i += 2
        elif a == "--last":
            last_only, i = True, i + 1
        elif a in ("--all-text", "--all"):
            show_all = show_all or a == "--all"
            i += 1
        else:
            i += 1
    if not os.path.exists(path):
        print(f"number-backtest: файлу немає: {path}")
        return 1
    if not os.path.exists(HOOK):
        print(f"number-backtest: немає хука з логікою: {HOOK}")
        return 1

    hook = load_hook()
    lines = open(path, encoding="utf-8", errors="ignore").read().splitlines()
    turns = list(hook.iter_turns(lines))

    flagged, total, rows, bycls = set(), 0, [], {}
    for n, t in enumerate(turns, 1):
        text = t["texts"][-1] if last_only and t["texts"] else "\n".join(t["texts"])
        claims = hook.check(text, t["ev"])
        for c in claims:
            bycls[c["cls"]] = bycls.get(c["cls"], 0) + 1
        if not claims:
            if show_all:
                rows.append((n, t["ts"][11:19], [], False))
            continue
        total += len(claims)
        flagged.add(n)
        rows.append((n, t["ts"][11:19], claims, True))
    for n, ts, claims, _ in rows:
        if not claims:
            print(f"#{n} {ts}  —")
            continue
        mark = ""
        if labels:
            mark = " [ПОМИЛКА(розмічена)]" if n in labels else " [без розмітки]"
        print(f"#{n} {ts}  тверджень {len(claims)}{mark}")
        for c in claims:
            print(f"    {c['num']}  «{c['ctx']}»  — {c['cls']}")

    src = ("останній блок ходу (--last, як last_assistant_message)"
           if last_only else "усі текстові блоки ходу")
    print(f"джерело тексту: {src}; файл: {os.path.basename(path)}")
    hit, missed, false_pos = flagged & labels, labels - flagged, flagged - labels
    print(f"усього тверджень: {total}; ходів {len(turns)}; "
          f"позначено ходів {len(flagged)}")
    for k in (hook.CLS_NO_NUM, hook.CLS_NO_PAIR):
        if bycls.get(k):
            print(f"  {k}: {bycls[k]}")
    if labels:
        print(f"розмічених ходів {len(labels)}: впіймано {sorted(hit)}, "
              f"пропущено {sorted(missed)}, хибних {sorted(false_pos)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
