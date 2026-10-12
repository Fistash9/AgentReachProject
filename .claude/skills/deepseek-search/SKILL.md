---
name: deepseek-search
description: Web research through DeepSeek's own server-side search with conversation memory (tools/deepseek-search.py) — finds primary sources the built-in WebSearch misses and labels every claim [першоджерело]/[третя сторона]/[не перевірено]. Use when the user asks to research, find reviews, compare tools, check whether a package/repo/claim is real, or "пошукай через діпсік"; also before recommending or rejecting a tool. Paid (~$0.01–0.03 per call) — ask the user first. Do NOT use for facts already in project files or for a single URL you can fetch directly.
---

# Пошук через DeepSeek (T6.4, trees/pidrozdil-deepseek.md)

Дисципліна пошуку — одне джерело: `agents/deepseek-search/discipline.md` (скрипт
читає її як system). Міняєш правила пошуку — міняй той файл, не цей.

## Перед викликом
1. Спершу власні записи: `grep` по BACKLOG/TROUBLES/trees — чи шукали вже.
2. **Платно.** Спитати користувача з ціною (≈$0.01–0.03 за виклик; рядок «== Ціна»
   у виводі — оцінка за тарифом flash, без вартості самих пошуків).
3. Одне вузьке питання на виклик. 3–4 питання — 3–4 виклики, не один великий.

## Виклик
```
python3 tools/deepseek-search.py --uses 4 "питання"          # нова розмова
python3 tools/deepseek-search.py -c <ID> "уточнення"           # та сама розмова
```
- `--uses` — побажання: сервер його не тримає (рядок «УВАГА» покаже перевищення).
- Великий текст (експорт сесії, звіт) — `--file ШЛЯХ` (можна кілька разів): вміст іде
  в повідомлення, аргументом лізе лише ~120 КБ. Рецензія файлу без пошуку —
  `--no-search --raw --file …` (2026-10-12, T8).
- `-c` найкорисніший як **крок звірки**: «які з твоїх тверджень підтверджено
  першоджерелом, а які лише статтями?» — так було знайдено retired `/orchestrate` (T9).
- `--raw` — без дисципліни: для порівняння і для рецензії файлу (дисципліна — про пошук).

## Після виклику, ДО звіту користувачу
- Код виходу ≠ 0 або «УВАГА: відповідь могла обірватись» — назвати це, не ховати.
- Вибірково відкрити 3–5 URL першоджерел (`curl -s -o /dev/null -w '%{http_code}'`) і
  `grep` 2–3 цитати там, де можна.
- Числа (зірки, версії) — звірити з `gh api` / `npm view`, не зі звіту.
- У звіті: ціна з рядка «== Ціна», ID розмови для `-c`.
