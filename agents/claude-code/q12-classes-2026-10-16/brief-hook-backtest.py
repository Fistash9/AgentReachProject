"""Бектест правки А хука request-brief-reminder (2026-10-16, рішення користувача «Сліпа звірка, потім
бриф-хук»; випадок: сесія 0577c90b — 12 спрацювань, справжня потреба 1, на неї хук мовчав).
Стара логіка: останній запис last-prompt (лише набраний текст). Нова: останнє рішення людини —
набраний текст АБО відповідь у віконці AskUserQuestion; обраний готовий варіант → мовчати,
вписаний текст → те саме правило «≤12 слів і не голе підтвердження». Лише читає журнали."""
import glob, importlib.util, json, os, re, sys

LOGS = os.path.expanduser("~/.claude/projects/-data-data-com-termux-files-home-AgentReachProject")
HOOK = "/data/data/com.termux/files/home/AgentReachProject/.claude/hooks/request-brief-reminder-hook.py"
sp = importlib.util.spec_from_file_location("rb", HOOK)
rb = importlib.util.module_from_spec(sp)
sp.loader.exec_module(rb)

SYS = re.compile(r"^\s*<(?:system-reminder|command-|local-command|task-notification|bash-)")
ANS = re.compile(r"\s*(?:User has answered your questions|The user answered|Your questions have been answered):(.*)", re.S)


def decision_from(d, labels):
    """(тип, текст) людського рішення в записі журналу або None."""
    if d.get("type") != "user" or d.get("isMeta"):
        return None
    c = d.get("message", {}).get("content")
    if isinstance(c, str):
        return None if SYS.match(c) or not c.strip() else ("typed", c)
    for b in c or []:
        if b.get("type") == "text" and b["text"].strip() and not SYS.match(b["text"]):
            return ("typed", b["text"])
        if b.get("type") == "tool_result" and b.get("tool_use_id") in labels:
            t = b.get("content")
            t = t if isinstance(t, str) else " ".join(x.get("text", "") for x in t or [] if isinstance(x, dict))
            m = ANS.match(t)
            if not m:
                return None
            body = re.split(r"You can now continue|Read the answers carefully", m.group(1))[0]
            answers = re.findall(r'"=\s*"(.*?)"(?=\s*(?:,\s*"|\.|$))', body, re.S) or [body]
            if all(a.strip() in labels[b["tool_use_id"]] for a in answers):
                return ("option", " / ".join(answers))
            return ("free", " ".join(a for a in answers if a.strip() not in labels[b["tool_use_id"]]))
    return None


def is_confirmation(text):
    """Голе підтвердження АБО «так, <коротке доручення>» (≤6 слів, перше — слово згоди):
    за SKILL.md request-brief бриф не потрібен для підтвердження вже запропонованого."""
    w = re.findall(r"[a-zA-Zа-яіїєґА-ЯІЇЄҐ']+", text.lower())
    return rb.is_bare_confirmation(text) or (0 < len(w) <= 6 and (w[0] in rb.AGREE_WORDS or w[0] in RECORD))


# коротке пряме доручення записати / закомітити / закрити — ясне, бриф не потрібен
RECORD = {"запиши", "записуй", "допиши", "дописуй", "коміть", "комить", "закомить", "зберігай", "збережи",
          "закрий", "закривай", "пуш", "запуш"}


def fires(text):
    w = text.split()
    if rb.DELEGATE_RE.search(text) and len(w) <= rb.DELEGATE_MAX_WORDS:
        return True
    return not (len(w) > rb.WORD_LIMIT or is_confirmation(text))


def main():
    files = sorted(glob.glob(LOGS + "/*.jsonl"))
    old = new = edits = 0
    both = only_old = only_new = 0
    samples_new = []
    new_dec = set()
    sess = 0
    for f in files:
        labels, last_prompt, last_dec = {}, None, None
        is_cli = None
        for line in open(f, encoding="utf-8"):
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get("type") == "user" and is_cli is None:
                is_cli = d.get("entrypoint") == "cli"
                if not is_cli:
                    break
            if d.get("type") == "last-prompt":
                last_prompt = d.get("lastPrompt")
            dec = decision_from(d, labels)
            if dec:
                last_dec = dec
            if d.get("type") != "assistant":
                continue
            for b in d["message"].get("content") or []:
                if b.get("type") != "tool_use":
                    continue
                if b["name"] == "AskUserQuestion":
                    labels[b["id"]] = {o.get("label", "").strip() for q in b["input"].get("questions", []) for o in q.get("options", [])}
                if b["name"] not in ("Edit", "Write"):
                    continue
                ch, nl = rb.edit_size(b["name"], b["input"])
                if ch < rb.CHAR_THRESHOLD and nl < rb.LINE_THRESHOLD:
                    continue
                edits += 1
                o = bool(last_prompt) and not (len(last_prompt.split()) > rb.WORD_LIMIT or rb.is_bare_confirmation(last_prompt))  # як у хуку
                n = bool(last_dec) and last_dec[0] != "option" and fires(last_dec[1])
                old += o; new += n
                if n:
                    new_dec.add((f, last_dec[1][:200]))
                both += o and n; only_old += o and not n; only_new += n and not o
                if n and len(samples_new) < 40:
                    samples_new.append((os.path.basename(f)[:8], last_dec[0], re.sub(r"\s+", " ", last_dec[1])[:110]))
        sess += bool(is_cli)
    print(f"сесій cli {sess}; помітних правок {edits}; стара логіка спрацювала {old}, нова {new}")
    print(f"різних рішень, на які нова логіка нагадала б: {len(new_dec)}")
    print(f"обидві {both}; лише стара (зникне) {only_old}; лише нова (з'явиться) {only_new}")
    seen = set()
    for s in samples_new:
        if s in seen:
            continue
        seen.add(s)
        print("  НОВА:", *s)


if __name__ == "__main__":
    main()
