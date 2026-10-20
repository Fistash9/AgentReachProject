# Graphify у проот: проба (2026-10-20, cc-20-2)

1. **Установка — 34 с**, з обхідним шляхом: `python3 -m venv v` падає (`ensurepip` немає: «No module named ensurepip»,
   «No module named pip»; `python3-venv`/`pip` у проот не встановлені, apt — поза межами). Зробив `venv --without-pip`
   і завантажив **pip 26.2.1 із PyPI** (`files.pythonhosted.org`), далі `v/bin/python pip.whl/pip install graphifyy`
   → `graphify 0.9.92`. Termux-ний pip не використовував.
2. **Індексація**: `graphify update .` — **12 с**, 223 файли, `2637 вузлів, 3865 ребер, 237 спільнот`; 8 файлів без
   символів (regex-worker.mjs, qcheck.py, stale-status-draft.py, parse.test.ts, SKILL.md +3). LLM не потрібен.
3. **Q1 (функція ціни DeepSeek і ціни за 1M)**: graphify дав 184 вузли-сусіди (BFS), серед них `cost()` у
   deepseek-search.py, але **прямої відповіді немає**. Правда (grep): `tools/cost-report.py:507 collect_session_cost()`;
   ціни `:140-142` — cache-hit **0.003**, cache-miss **0.15**, output **0.60** $/1M, пік ×2.0 (`:143`).
4. **Q2 (хто в tools/ кличе personal-scan.py)**: graphify знайшов `personal-scan.py`, `scan_text()`, навіть
   `personal-guard-hook.py`, але **справжніх викликачів не назвав** — відповідь неповна. Правда (grep):
   `tools/deepseek-search.py:191` і `tools/session-export.py:96` (обидва через `importlib.util.spec_from_file_location`).
5. **Q3 (константа тиші)**: graphify показав `read_stream()`/`call()`, але **значення не дав**. Правда:
   `tools/deepseek-search.py:94` — `CHUNK_TIMEOUT = 600   # тиша між шматками потоку`.
6. **Висновок**: для проот Graphify працює (індексація швидка, офлайн), але `query` — це обхід сусідів, не відповідь:
   на всі 3 питання точно відповів `grep`, а не він. Для «де це лежить» — годиться; для «яке значення» — ні.
7. Не вдалось: venv без bootstrap (потрібен `python3-venv` або pip-wheel із PyPI); семантичні ребра (потрібен ключ LLM —
   не використовував, мережа лише PyPI). Нічого не видаляв; тека `/root/tmp/graphify-test` (v, repo, pip.whl) лишається.
