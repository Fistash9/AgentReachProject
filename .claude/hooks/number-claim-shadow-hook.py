#!/data/data/com.termux/files/usr/bin/python3
"""Stop-хук, ТІНЬОВИЙ режим, версія 2 (2026-10-07): «число-твердження без опори».

Навіщо: клас помилки «число-твердження без доказу» — у звіті закриття сесії
було «7 записів TROUBLES» (grep давав 5), «≈12 викликів DeepSeek» (не рахував
ніхто) і «38 підключених хуків» (число взято з `grep -c '"command"'` — воно
рахує не хуки). Хук НІЧОГО не блокує й нічого не пише в stdout: лише рядок у
.claude/logs/number-claim-shadow.jsonl на кожен запуск (навіть із порожнім
`claims`) — щоб порожній лог не плутати зі зламаним хуком.

ДЖЕРЕЛО ТЕКСТУ — ДВА ШЛЯХИ (обидва реалізовані й задокументовані):
  A. Основний: `transcript_path` з payload. Беремо УСІ текстові блоки
     ПОТОЧНОГО ходу, а не лише останній. Хід = від останнього СПРАВЖНЬОГО
     повідомлення користувача (isMeta і tool_result не рахуються) до кінця
     файлу. Причина: Stop не стріляє/не віддає тексту, коли відповідь
     завершується викликом інструмента (напр. AskUserQuestion) — у звіті
     закриття сесії `last_assistant_message` цього тексту НІКОЛИ не містить
     (перевірено: транскрипт e8409204, рядки 2081-2082). Тому єдине надійне
     джерело — журнал, і саме всі блоки ходу (твердження часто в середині).
  B. Деградація: якщо `transcript_path` немає / не читається / поточний хід
     не дав жодного текстового блоку — беремо `last_assistant_message`.
     У цьому разі доказів ходу немає (ev порожній), тож кожне твердження
     дістане клас «немає в жодному виводі»; це видимий, а не тихий зсув.

ПРАВИЛО ОПОРИ (доведене прототипом; заміняє хибне «число є десь у виводах»):
  Твердження вважається опертим, лише якщо в ДЕЯКОМУ РЯДКУ виводу є ПАРА
  «число + іменник» — в обидва боки: `38 хуків` або `хуків: 38`. Між числом і
  іменником дозволені лише розділювачі (пробіл, двокрапка, тире, дужки…), не
  слова: інакше рядок-дамп `38→23 визнано … 'Хуків насправді'` (транскрипт
  e8409204:2058) «оправдав» би «38 хуків», чого він не робить. Іменники
  порівнюються за основою слова — перші 4 символи (`хуків`→`хукі`).
  З доказів ВИКЛЮЧЕНО:
    (а) результати AskUserQuestion — туди повертається текст самого агента
        (відлуння), а не вивід інструмента;
    (б) вміст кодових лапок (`` ` `` і ```-блоків) та кутових лапок («…»)
        всередині рядків виводу — інакше переказ власного твердження у
        виводі (рецензія цитує «38 хуків») ставав би доказом;
    (в) `input` викликів tool_use (це теж власний текст агента: команда,
        heredoc, запис у файл) — опорою є лише ВИВІД, тобто tool_result.

КЛАСИФІКАЦІЯ кожного твердження (обидва класи потрапляють у лог):
  * «немає в жодному виводі» — числа немає як окремого токена в жодному рядку;
  * «число є, пари з іменником немає» — число у виводах є, але пари з
    відповідним іменником немає (саме випадок «38» з `grep -c`).
  Твердження зі знайденою парою в лог не потрапляють.

СВІДОМО НЕ ВИКОРИСТОВУЄТЬСЯ: правило «порожній хід → усі числа підозрілі» —
0 спрацювань на 85 ходах, тому викинуте.

Межі методу: перевіряється НАЯВНІСТЬ пари в рядку виводу, не сенс. Число,
взяте зі справжнього виводу, але приписане не тому іменнику, не ловиться;
твердження без іменника (голе «≈$0.25») не є твердженням.

Запуск:
  * як Stop-хук: JSON payload на stdin;
  * вручну: python3 <цей файл> --backtest <транскрипт.jsonl> [--turn N]
    друкує по кожному ходу знайдені твердження з класом і підсумок.
Будь-яка помилка — мовчки (fail-open), код виходу завжди 0, stdout порожній.
"""
import datetime
import json
import os
import re
import sys

ROOT = "/data/data/com.termux/files/home/AgentReachProject"
LOG = os.environ.get("NUMBER_CLAIM_SHADOW_LOG") or os.path.join(
    ROOT, ".claude", "logs", "number-claim-shadow.jsonl")  # env — для тестів
LOG_MAX = 512 * 1024  # більше — переносимо в .1 (ротація)

# Читання хвоста журналу: шукаємо останнє справжнє повідомлення користувача
# блоками від кінця файлу, доки не знайдемо (хід мусить бути ЦІЛИМ: у
# e8409204 хід закриття займає ~1.6 МБ, тож фіксований хвіст 256 КБ різав
# би його посеред ходу). Межа 32 МБ — запобіжник на патологічний файл.
CHUNK = 1024 * 1024
MAX_SCAN = 32 * 1024 * 1024

CLS_NO_NUM = "немає в жодному виводі"
CLS_NO_PAIR = "число є, пари з іменником немає"

# Результати цих інструментів не є опорою (див. докстрінг, п. а).
EXCLUDED_TOOLS = frozenset({"AskUserQuestion"})

# --- дзеркало tools/claimcheck/claimcheck.py:27-33 ---
# Свідома копія: Stop-хук мусить працювати навіть коли tools/ недоступний
# (fail-open інакше перетворився б на «хук просто ніколи не спрацьовує»).
def strip_quoted(t):
    t = re.sub(r"```[\s\S]*?```", " ", t)
    t = re.sub(r"`[^`\n]*`", " ", t)
    t = re.sub(r'"[^"\n]{0,200}"', " ", t)
    t = re.sub(r"[«“][^»”\n]{0,200}[»”]", " ", t)
    t = re.sub(r"(\*\*|__|~~)", "", t)
    return t


_FENCE = re.compile(r"```[\s\S]*?```")
_TICK = re.compile(r"`[^`\n]*`")
_GUILL = re.compile(r"[«“][^»”\n]{0,200}[»”]")


def evidence_lines(s):
    """Рядки виводу інструмента як доказова база. З рядків вирізано вміст
    кодових лапок (``…`` і ```-блоків) та кутових лапок («…») — переказ
    власного твердження у виводі не має ставати доказом. Межі рядків
    зберігаємо: пара не повинна «зшитися» через вирізаний фрагмент."""
    s = _FENCE.sub("\n", s or "")
    s = _TICK.sub(" ", s)
    s = _GUILL.sub(" ", s)
    return s.splitlines()


NOUNS = (r"(коміт\w*|перевір\w*|файл\w*|рядк\w*|рядок|місц\w*|хук\w*|тест\w*|"
         r"знахід\w*|запис\w*|помил\w*|відповід\w*|виклик\w*|сесі\w*|пакет\w*|"
         r"правил\w*|скіл\w*|ход\w*|раз\w*|розрив\w*|пункт\w*|проблем\w*|блок\w*)")
E1_RE = re.compile(r"(?<![\w.:/#-])(\d{1,5})\s+" + NOUNS, re.I)
# Дробові — окремо, бо E1_RE навмисне не пропускає крапку всередині токена.
E1_DEC_RE = re.compile(r"(?<![\w.:/#-])(\d{1,6}[.,]\d{1,3})\s+" + NOUNS, re.I)
# Розрядність через пробіл («22 222 рядки»). Без цього E1 ловив «222» з
# «22 222» — систематичне хибне спрацювання на кожному великому числі.
GROUP_E1_RE = re.compile(r"(?<![\w.:/#-])(\d{1,3}(?:[ \u00a0]\d{3})+)\s+" + NOUNS, re.I)
GROUP_RE = re.compile(r"(?<![\w.:/#-])(\d{1,3}(?:[ \u00a0]\d{3})+)(?![\w.:/-])")
CTX_BEFORE, CTX_AFTER = 32, 44


def ctx(text, start, end):
    return re.sub(r"\s+", " ", text[max(0, start - CTX_BEFORE):end + CTX_AFTER]).strip()


def stem(word):
    """Основа слова для порівняння: перші 4 символи (доведене правило)."""
    w = re.sub(r"\W", "", word.lower())
    return w[:4] if w else word.lower()[:4]


def stem_match(a, b):
    """Основи збігаються або одна є початком іншої (для коротких слів:
    «хук» проти «хуків», «раз» проти «разів»)."""
    if a == b:
        return True
    return min(len(a), len(b)) >= 3 and (a.startswith(b) or b.startswith(a))


def extract_claims(text):
    """Числа-твердження: число + іменник зі списку NOUNS (E1), у т.ч. з
    префіксом наближення («≈12 викликів») і дробові. Дедуп за (число, основа
    іменника): різні іменники при тому самому числі — різні твердження,
    а повтор того самого твердження в кількох текстових блоках ходу — одне."""
    t = strip_quoted(text or "")
    groups = [(m.start(1), m.end(1)) for m in GROUP_RE.finditer(t)]
    seen, out = set(), []

    def inside_group(s, e):
        return any(ga <= s and e <= gb for ga, gb in groups)

    def add(num, noun, s, e):
        k = (num, stem(noun))
        if k in seen:
            return
        seen.add(k)
        out.append({"num": num, "ctx": ctx(t, s, e), "noun": noun})

    for rx in (GROUP_E1_RE, E1_RE, E1_DEC_RE):
        for m in rx.finditer(t):
            if rx is not GROUP_E1_RE and inside_group(m.start(1), m.end(1)):
                continue  # «222» з «22 222» — не окреме число
            add(m.group(1), m.group(2), m.start(1), m.end(1))
    return out


def _lit(num):
    """Число як регексп-літерал; пробіл-розрядність стає НЕобов'язковою:
    «2 667» і «2667» — те саме число."""
    body = re.sub(r"\\([ \u00a0])", r"\1", re.escape(num))
    return re.sub(r"[ \u00a0]", "[ \u00a0]?", body)


def number_in(num, ev_text):
    """Чи є число окремим токеном десь у виводах ходу."""
    return bool(re.search(r"(?<![\w.,])" + _lit(num) + r"(?![\w.,])", ev_text))


# Між числом і іменником у парі — лише розділювачі (не слова!), до 6 символів.
_GAP = r"[\s:=\-–—|,()\[\]./]{0,6}"
_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)


def pair_supported(num, noun, ev_lines):
    """Чи є в якомусь ОДНОМУ рядку виводу пара «число + іменник» (в обидва
    боки), з основою іменника за 4 символами."""
    st = stem(noun)
    numre = re.compile(r"(?<![\w.,])" + _lit(num) + r"(?![\w.,])")
    gapre = re.compile(r"^" + _GAP + r"$")
    for line in ev_lines:
        nums = list(numre.finditer(line))
        if not nums:
            continue
        for wm in _WORD.finditer(line):
            if not stem_match(st, stem(wm.group())):
                continue
            for nm in nums:
                if nm.end() <= wm.start() and gapre.match(line[nm.end():wm.start()]):
                    return True
                if wm.end() <= nm.start() and gapre.match(line[wm.end():nm.start()]):
                    return True
    return False


def check(text, ev_lines):
    """Твердження ходу, яких не оперто парою «число+іменник» у виводах.
    Повертає список {num, ctx, cls}."""
    ev = ev_lines or []
    joined = "\n".join(ev)
    out = []
    for c in extract_claims(text):
        if pair_supported(c["num"], c["noun"], ev):
            continue
        cls = CLS_NO_NUM if not number_in(c["num"], joined) else CLS_NO_PAIR
        out.append({"num": c["num"], "ctx": c["ctx"], "cls": cls})
    return out


def _text(v):
    if isinstance(v, str):
        return v
    return " ".join(y.get("text", "") for y in (v or []) if isinstance(y, dict))


def is_real_user(d):
    """Справжнє повідомлення користувача: текст рядком, не isMeta.
    tool_result (content-список) і службові рядки (mode, attachment…)
    хід не відкривають."""
    if d.get("type") != "user" or d.get("isMeta"):
        return False
    m = d.get("message")
    return isinstance(m, dict) and isinstance(m.get("content"), str)


def iter_turns(lines):
    """Ходи з рядків журналу. Хід = від справжнього повідомлення користувача
    до наступного. Текстові блоки — УСІ (texts), докази — рядки виводів
    tool_result (ev), без AskUserQuestion і без input tool_use.
    Якщо файл починається з середини ходу (обрізаний хвіст), хід
    відкривається неявно — докази не губляться."""
    cur = None
    for line in lines:
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if not isinstance(d, dict):
            continue
        m = d.get("message")
        if not isinstance(m, dict):
            continue
        tn = d.get("type")
        c = m.get("content")
        if is_real_user(d):
            if cur is not None:
                yield cur
            cur = {"user": c, "ts": d.get("timestamp", ""), "texts": [],
                   "ev": [], "names": {}}
            continue
        if tn not in ("user", "assistant"):
            continue  # службові рядки (mode, attachment, last-prompt…)
        if cur is None:
            cur = {"user": None, "ts": d.get("timestamp", ""), "texts": [],
                   "ev": [], "names": {}}
        if tn == "user" and isinstance(c, list):
            for x in c:
                if not isinstance(x, dict) or x.get("type") != "tool_result":
                    continue
                if cur["names"].get(x.get("tool_use_id")) in EXCLUDED_TOOLS:
                    continue  # відлуння власного тексту, не вивід
                cur["ev"].extend(evidence_lines(_text(x.get("content"))))
        elif tn == "assistant":
            for x in (c or []):
                if not isinstance(x, dict):
                    continue
                if x.get("type") == "tool_use":
                    cur["names"][x.get("id")] = x.get("name", "")
                elif x.get("type") == "text" and x.get("text", "").strip():
                    cur["texts"].append(x["text"])
    if cur is not None:
        yield cur


def read_all(path):
    """Усі рядки журналу (для --backtest)."""
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.read().splitlines()


def current_turn_lines(path):
    """Рядки від останнього справжнього повідомлення користувача.
    Читаємо блоками від кінця, доки не знайдемо його (див. CHUNK/MAX_SCAN).
    Якщо не знайшли — повертаємо те, що прочитали (зсув у бік ЗАЙВИХ
    спрацювань, безпечний бік для тіньового режиму)."""
    with open(path, "rb") as f:
        f.seek(0, 2)
        pos = f.tell()
        buf = b""
        scanned = 0
        while pos > 0 and scanned < MAX_SCAN:
            take = min(CHUNK, pos)
            pos -= take
            scanned += take
            f.seek(pos)
            buf = f.read(take) + buf
            lines = buf.decode("utf-8", "ignore").splitlines()
            if pos > 0 and lines:
                lines = lines[1:]  # перший рядок може бути обрізаний
            for i in range(len(lines) - 1, -1, -1):
                try:
                    d = json.loads(lines[i])
                except ValueError:
                    continue
                if is_real_user(d):
                    return lines[i:]
        lines = buf.decode("utf-8", "ignore").splitlines()
        if pos > 0 and lines:
            lines = lines[1:]
        return lines


def last_turn(path):
    turns = list(iter_turns(current_turn_lines(path)))
    return turns[-1] if turns else None


def write_log(session, claims):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    if os.path.isfile(LOG) and os.path.getsize(LOG) > LOG_MAX:
        os.replace(LOG, LOG + ".1")
    rec = {"t": datetime.datetime.now().isoformat(timespec="seconds"),
           "session": session, "runs": 1, "claims": claims}
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def run(data):
    """Один запуск Stop. `stop_hook_active` не пропускаємо (як робить
    node-label-shadow-hook.py): наш хук не блокує, рекурсії з нього немає,
    а вимога «рядок на кожен запуск» інакше не виконується."""
    tp = data.get("transcript_path")
    turn = None
    if isinstance(tp, str) and os.path.isfile(tp):
        try:
            turn = last_turn(tp)
        except OSError:
            turn = None
    texts, ev = "", []
    if turn is not None:
        texts = "\n".join(turn["texts"])
        ev = turn["ev"]
    if not texts.strip():
        # Шлях B: журналу немає / поточний хід без тексту — деградація на
        # last_assistant_message (доказів ходу тоді немає: ev порожній).
        lam = data.get("last_assistant_message")
        texts = lam if isinstance(lam, str) else ""
    claims = check(texts, ev) if texts.strip() else []
    write_log(data.get("session_id"), claims)


def backtest(argv):
    path = argv[0]
    sel = set()
    if "--turn" in argv:
        try:
            sel = {int(x) for x in argv[argv.index("--turn") + 1].split(",") if x.strip()}
        except (ValueError, IndexError):
            sel = set()
    lines = read_all(path)
    turns = list(iter_turns(lines))
    total, with_claims, bycls = 0, 0, {}
    rows, sel_claims, sel_nums = [], [], []
    for i, t in enumerate(turns, 1):
        claims = check("\n".join(t["texts"]), t["ev"])
        total += len(claims)
        with_claims += 1 if claims else 0
        for c in claims:
            bycls[c["cls"]] = bycls.get(c["cls"], 0) + 1
        if i in sel:
            sel_claims += claims
            sel_nums += [c["num"] for c in claims]
        rows.append((i, t, claims))
    for i, t, claims in rows:
        if sel and i not in sel:
            continue
        if not claims and not sel:
            continue
        print(f"#{i} {t['ts'][11:19]}  тверджень {len(claims)}")
        for c in claims:
            print(f"    {c['num']}  «{c['ctx']}»  — {c['cls']}")
    print(f"джерело тексту: усі текстові блоки ходу; ходів {len(turns)}")
    print(f"усього тверджень: {total}; ходів із твердженнями: {with_claims}")
    for k in (CLS_NO_NUM, CLS_NO_PAIR):
        if bycls.get(k):
            print(f"  {k}: {bycls[k]}")
    if sel:
        print(f"вибрані ходи {sorted(sel)}: тверджень {len(sel_claims)}; "
              f"числа: " + " ".join(sel_nums))


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--backtest":
        return backtest(sys.argv[2:])
    try:
        data = json.load(sys.stdin)
    except ValueError:
        data = None
    if not isinstance(data, dict):
        data = {}  # сміття на stdin — усе одно рядок у лог (вимога «на кожен запуск»)
    run(data)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
