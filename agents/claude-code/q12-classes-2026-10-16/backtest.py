"""Q12 крок 3 — бектест (2026-10-16, план у trees/yakist-roboty-agentiv.md, рішення користувача
«Так, у фоні + бектест»). Лише читає журнали сесій. Етап А: виймає поправки користувача
(слова-тригери повтору/докору) разом із попередньою реплікою асистента і питанням: чи назвав
асистент сам повтор/клас ДО поправки (критерій Q12 «повтор помічено раніше за користувача»).
Вихід: corrections.jsonl + зведення в stdout."""
import glob, json, os, re, sys

LOGS = os.path.expanduser("~/.claude/projects/-data-data-com-termux-files-home-AgentReachProject")
OUT = "/data/data/com.termux/files/usr/tmp/q12/corrections.jsonl"  # дослівні слова користувача — поза git

# поправка-докір користувача (не просте питання)
TRIG = re.compile(
    r"знов|знову|вже казав|вже говорил|ми ж (?:вже|домовл)|скільки раз|ти перевіря|ти не перевір|"
    r"не перевірив|як ти міг|чому ти не|чому не спитав|ти що (?:придум|вигад)|ти придумав|"
    r"я ж казав|я казав|забув|пропустив|на око|не розумію шифр|навіщо ти", re.I)
# асистент сам називає повтор/клас до поправки
SELF = re.compile(r"повтор|той самий клас|той самий патерн|знову я|удруге|утретє|вже раз|"
                  r"клас «|вже траплял|як і (?:раніше|\d)", re.I)
SYS = re.compile(r"^\s*<(?:system-reminder|command-|local-command|task-notification|bash-)")


def user_texts(d):
    """Справжній текст користувача з запису журналу: рядок або text-блоки, плюс відповіді у віконцях."""
    c = d.get("message", {}).get("content")
    if isinstance(c, str):
        return [c]
    out = []
    for b in c or []:
        if b.get("type") == "text":
            out.append(b["text"])
        elif b.get("type") == "tool_result":
            t = b.get("content")
            t = t if isinstance(t, str) else " ".join(x.get("text", "") for x in t or [] if isinstance(x, dict))
            # лише справжня відповідь у віконці: результат ПОЧИНАЄТЬСЯ з фрази (не експорт сесії, прочитаний файлом)
            m = re.match(r"\s*(?:User has answered your questions|The user answered|Your questions have been answered):(.*)", t, re.S)
            if m:
                out.append(re.split(r"You can now continue|Read the answers carefully", m.group(1))[0])
    return out


def asst_text(d):
    c = d.get("message", {}).get("content")
    if isinstance(c, str):
        return c
    return "\n".join(b.get("text", "") for b in c or [] if b.get("type") == "text")


def main():
    files = sorted(glob.glob(LOGS + "/*.jsonl"))
    n_sess = n_user = 0
    rows = []
    for f in files:
        sid = os.path.basename(f)[:8]
        prev_asst = []  # останні тексти асистента в цій сесії
        had_user = False
        for line in open(f, encoding="utf-8"):
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get("type") == "user" and d.get("entrypoint") != "cli":
                break  # sdk-cli — під-сесії помічників (промпт делегата, не користувач); 16.10: 172 з 240
            if d.get("isMeta") or d.get("isSidechain"):
                continue
            t = d.get("type")
            if t == "assistant":
                s = asst_text(d)
                if s.strip():
                    prev_asst = (prev_asst + [s])[-3:]
            elif t == "user" or (t == "attachment" and d.get("attachment", {}).get("type") == "queued_command"):
                texts = [d["attachment"].get("prompt", "")] if t == "attachment" else user_texts(d)
                for s in texts:
                    if not isinstance(s, str):  # queued_command.prompt буває списком блоків
                        s = " ".join(x.get("text", "") if isinstance(x, dict) else str(x) for x in s)
                    if not s.strip() or SYS.match(s):
                        continue
                    had_user = True
                    n_user += 1
                    if TRIG.search(s):
                        ctx = "\n".join(prev_asst)
                        rows.append({
                            "session": sid, "t": d.get("timestamp", "")[:16],
                            "user": s.strip()[:500], "trigger": TRIG.search(s).group(0),
                            "asst_before": ctx[-600:],
                            "self_named": bool(SELF.search(ctx)),
                        })
        n_sess += had_user
    with open(OUT, "w", encoding="utf-8") as o:
        for r in rows:
            o.write(json.dumps(r, ensure_ascii=False) + "\n")
    selfn = sum(r["self_named"] for r in rows)
    print(f"журналів {len(files)}, сесій з повідомленнями користувача {n_sess}, повідомлень {n_user}")
    print(f"поправок за тригерами {len(rows)}; з них асистент назвав повтор/клас у 3 попередніх репліках: {selfn}")
    from collections import Counter
    print("тригери:", Counter(r["trigger"].lower() for r in rows).most_common(12))
    print("за місяцем-днем:", sorted(Counter(r["t"][:10] for r in rows).items())[-12:])


if __name__ == "__main__":
    main()
