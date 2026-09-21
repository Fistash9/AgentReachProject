#!/usr/bin/env python3
"""Статистика транскрипту для аналізатора референсів (лише стандартна бібліотека).

Використання:
    python3 transcript_stats.py FILE [--duration СЕКУНДИ] [--marker REGEX]

FILE — .vtt, .srt або звичайний текст. Виводить JSON у stdout.
--duration  тривалість відео в секундах (для перевірки щільності мовлення;
            якщо не задано й файл VTT/SRT, береться кінець останньої репліки)
--marker    регулярний вираз початку блоку (наприклад, "Number [A-Z][a-z]+\\."),
            щоб порахувати слова у вступі й довжину блоків

Числа з цього скрипту — обчислені, а не оцінені на око.
Скрипт не оцінює якість і не перевіряє факти.
"""
import argparse
import json
import re
import statistics
import sys
from collections import Counter

TIMING = re.compile(
    r"(?:(\d+):)?(\d{2}):(\d{2})[.,](\d{3})\s*-->\s*(?:(\d+):)?(\d{2}):(\d{2})[.,](\d{3})"
)
TAG = re.compile(r"<[^>]+>")

PRONOUNS = {
    "first_singular": ["i", "my", "me", "mine", "я", "мій", "моя", "моє", "мене", "мені"],
    "first_plural": ["we", "our", "us", "ours", "ми", "наш", "наша", "наше", "нас", "нам"],
    "second": ["you", "your", "yours", "ти", "ви", "твій", "ваш", "вам", "тебе", "вас"],
}


def to_seconds(h, m, s, ms):
    return int(h or 0) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def read_text(path):
    """Повертає (текст, кінець останньої репліки в секундах або None)."""
    with open(path, encoding="utf-8", errors="replace") as f:
        raw = f.read()
    if not TIMING.search(raw):
        return raw, None
    lines, last_end, prev = [], None, ""
    for line in raw.splitlines():
        m = TIMING.search(line)
        if m:
            g = m.groups()
            last_end = to_seconds(g[4], g[5], g[6], g[7])
            continue
        s = TAG.sub("", line).strip()
        if not s or s.startswith(("WEBVTT", "NOTE", "Kind:", "Language:")) or s.isdigit():
            continue
        # автосубтитри YouTube повторюють рядки: прибираємо дублі й перекриття
        if s == prev or (prev and prev.endswith(s)):
            continue
        if prev and s.startswith(prev):
            lines[-1] = s
        else:
            lines.append(s)
        prev = s
    return " ".join(lines), last_end


def sentences_of(text):
    parts = re.split(r"(?<=[.!?…])\s+(?=[\"'“«(]?[A-ZА-ЯІЇЄҐ0-9])", text.strip())
    return [p for p in parts if p.strip()]


def words_of(text):
    return re.findall(r"[^\W\d_]+(?:['’-][^\W\d_]+)*", text.lower())


def repeated_phrases(words, min_n=4, max_n=6, min_count=3, top=15):
    found = {}
    for n in range(min_n, max_n + 1):
        counts = Counter(tuple(words[i:i + n]) for i in range(len(words) - n + 1))
        for gram, c in counts.items():
            if c >= min_count:
                found[gram] = c
    # прибираємо фрази, що є частиною довшої з тим самим лічильником
    keep = {}
    for gram, c in found.items():
        contained = any(
            len(other) > len(gram) and c == oc and
            any(other[i:i + len(gram)] == gram for i in range(len(other) - len(gram) + 1))
            for other, oc in found.items()
        )
        if not contained:
            keep[gram] = c
    ranked = sorted(keep.items(), key=lambda kv: (-kv[1] * len(kv[0]), -kv[1]))[:top]
    return [{"phrase": " ".join(g), "count": c} for g, c in ranked]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--duration", type=float)
    ap.add_argument("--marker")
    args = ap.parse_args()

    text, last_end = read_text(args.file)
    text = re.sub(r"\s+", " ", text).strip()
    words = words_of(text)
    sents = sentences_of(text)
    lens = [len(words_of(s)) for s in sents] or [0]
    duration = args.duration or last_end

    out = {
        "chars": len(text),
        "words": len(words),
        "sentences": len(sents),
        "sentence_len_words": {
            "mean": round(statistics.mean(lens), 1),
            "median": statistics.median(lens),
            "p90": sorted(lens)[int(0.9 * (len(lens) - 1))],
            "max": max(lens),
        },
        "question_sentences_pct": round(100 * sum(s.rstrip().endswith("?") for s in sents) / max(len(sents), 1), 1),
        "exclamation_sentences_pct": round(100 * sum(s.rstrip().endswith("!") for s in sents) / max(len(sents), 1), 1),
        "pronouns_per_1000_words": {
            k: round(1000 * sum(words.count(w) for w in v) / max(len(words), 1), 1)
            for k, v in PRONOUNS.items()
        },
        "repeated_phrases": repeated_phrases(words),
    }
    if duration:
        minutes = duration / 60
        cpm = len(text) / minutes
        out["duration_min"] = round(minutes, 1)
        out["chars_per_min"] = round(cpm)
        out["words_per_min"] = round(len(words) / minutes)
        out["speech_density_flag"] = "LOW: схоже, це не сценарій (музика/шум)" if cpm < 250 else "ok"
    if args.marker:
        marks = [m.start() for m in re.finditer(args.marker, text)]
        out["marker_count"] = len(marks)
        if marks:
            out["intro_words_before_first_marker"] = len(words_of(text[:marks[0]]))
            blocks = [len(words_of(text[a:b])) for a, b in zip(marks, marks[1:] + [len(text)])]
            out["block_words"] = {
                "mean": round(statistics.mean(blocks)),
                "min": min(blocks),
                "max": max(blocks),
                "last_block_includes_outro": True,
            }
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
