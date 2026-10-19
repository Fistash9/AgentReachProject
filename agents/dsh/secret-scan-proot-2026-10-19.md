# Проба: чи зупиняє pre-commit secret-scan коміт із проот (2026-10-19)

Задача cc-19-2 (рішення користувача «DSH — так»), пункт 9 тріажу
(`agents/dsh/baton-diff-triage-2026-10-19.md`). Питання безпеки з BACKLOG: ключ уже раз
потрапляв у git (TROUBLES #11), а наживо перевірки з проот не було.

**Відповідь: ТАК, зупиняє.** Коміт із фальшивим ключем у проот завершився кодом **1**,
коміту не створено; контрольний коміт без ключа пройшов із кодом **0**.

## Середовище (перевірено командами)

| Що | Значення | Як перевірено |
|---|---|---|
| Де виконувалось | `root`, `Linux … PRoot-Distro` — тобто **Ubuntu/proot**, не Termux | `whoami`, `uname -a` |
| git | `git version 2.53.0` (Ubuntu) | `git --version` |
| python3, який бачить хук | **`/usr/bin/python3`, Python 3.14.4 — Ubuntu** | `command -v python3`, `python3 -V` |
| python3 Termux (для порівняння, не використовувався) | `/data/data/com.termux/files/usr/bin/python3 -> python3.14` | `ls -l` |

Хук викликає голий `python3`, тому в проот це `/usr/bin/python3` (Ubuntu). Termux-пітон у прогоні
не брав участі.

## Що саме перевіряли

`.git/hooks/pre-commit` робочого репозиторію (хук поза git, тому в клоні його немає):

```sh
#!/bin/sh
# Перевірка ключів перед комітом (tools/secret-scan.py, 2026-10-06; TROUBLES #11)
exec python3 "$(git rev-parse --show-toplevel)/tools/secret-scan.py"
```

`git config --get core.hooksPath` у робочому репо порожній (стандартна тека `.git/hooks`).
`tools/secret-scan.py` (86 рядків) дивиться `git diff --cached -U0` і ловить:
(1) точні значення наших ключів із `agent.py` і `.env` (читає локально, не друкує);
(2) шаблони `sk-…{20,}`, `ghp_…`, `AKIA…`, `nvapi-…`, `AIza…` (secret-scan.py:25-27). Код 1 = знайдено.

## Команди прогону

```sh
# клон (НЕ робочий репозиторій)
git clone --no-hardlinks /data/data/com.termux/files/home/AgentReachProject /root/tmp/ss-test-1910
cp /data/.../AgentReachProject/.git/hooks/pre-commit /root/tmp/ss-test-1910/.git/hooks/pre-commit
chmod +x /root/tmp/ss-test-1910/.git/hooks/pre-commit
cd /root/tmp/ss-test-1910 && git config user.email test@local && git config user.name test
```

Граблі: звичайний `git clone` упав — `fatal: hardlink different from source at
…/.git/objects/pack/pack-e7ac742a….rev` (Termux-ФС і `/root/tmp` — різні шари proot).
`--no-hardlinks` вирішив, код 0.

Фальшивий ключ згенеровано тут же (`secrets.choice`, 24 латинські літери/цифри після `sk-`),
справжні ключі не читались і не копіювались; файл `agent.py`/`.env` у клоні відсутні.

```
FAKE_TOKEN=sk-N…(27 симв.)   # повне значення — у виводі прогону, тут навмисно скорочено
```

### Тест 1 — коміт із фальшивим ключем

```sh
git add fake-key.txt
git commit -m "test: fake key"
```

Вивід (stderr):

```
secret-scan: КОМІТ ЗУПИНЕНО — у доданих рядках схоже на ключ:
  fake-key.txt:2 — шаблон ключа sk-N…(27 симв.)
Прибери ключ (git restore --staged <файл>) або, якщо це хибне
спрацювання, свідомо: git commit --no-verify. TROUBLES #11.
EXIT_CODE=1
```

Стан після блокування: `git log --oneline -1` → `247a35a …` (той самий HEAD, що й до проби —
коміт **не** створено), `git status --porcelain` → `A  fake-key.txt` (файл лишився в індексі).

### Тест 2 — контроль, той самий коміт без ключа

```sh
git restore --staged fake-key.txt; rm fake-key.txt
echo "контрольний рядок без ключа" > control.txt
git add control.txt
git commit -m "test: control without key"
```

Вивід:

```
[main a6a0ce4] test: control without key
 1 file changed, 1 insertion(+)
 create mode 100644 control.txt
EXIT_CODE=0
```

## Висновки (з межами)

1. **Pre-commit secret-scan у проот працює й блокує** коміт із ключем у доданих рядках: код 1,
   коміт не створюється, повідомлення українське з шляхом і номером рядка.
2. Спрацювала **Ubuntu-пітон** `/usr/bin/python3` 3.14.4; Termux-пітон не задіяний.
3. Перевірено лише **шаблонну** гілку (`sk-`). Гілка «наш ключ із `agent.py`/`.env`» у клоні не
   перевірялась — цих файлів там немає (і я їх свідомо не копіював). Для неї доказ лишається
   попередній: `TROUBLES.md:4051-4056` (тести 5/5, історія 393 коміти — 0 спрацювань).
4. Обхід можливий свідомо: `git commit --no-verify` (сам скрипт це підказує) — захист не
   криптографічний, а «проти випадковості».
5. Не перевірено: поведінка, якщо `python3` немає в PATH (тоді `exec` провалиться — коміт,
   скоріш за все, теж не пройде, але це не заміряно); коміт із **Termux**-боку (там свій git і
   свій python3) — окрема проба, якщо потрібна.
6. Робочий репозиторій не змінювався: проба йшла в клоні. Клон **лишено**:
   `/root/tmp/ss-test-1910` (у ньому один тестовий коміт `a6a0ce4`).

Джерела: `.git/hooks/pre-commit` (188 Б), `tools/secret-scan.py:25-27,52-82`,
`TROUBLES.md:4051-4056,4369`.
