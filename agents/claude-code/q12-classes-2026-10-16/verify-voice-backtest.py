"""Бектест правки голосу verify у answer-gate (2026-10-16, рішення користувача «Звірити зараз + бектест
голосу»; випадок: бриф зі зміною session-close показано у віконці без verify-before-show, тінь — misses []).
Стара умова: остання текстова відповідь закінчується «?» + слово зміни, а в ході немає verify/delegate.
Нова: те саме АБО питання у віконці (AskUserQuestion), у питанні/описах варіантів чи в тексті перед ним —
слово зміни, і ДО цього питання в ході не було verify-before-show / delegate. Лише читає журнали."""
import glob, importlib.util, json, os, re

LOGS = os.path.expanduser("~/.claude/projects/-data-data-com-termux-files-home-AgentReachProject")
G = "/data/data/com.termux/files/home/AgentReachProject/.claude/hooks/answer-gate-shadow-hook.py"
sp = importlib.util.spec_from_file_location("g", G)
g = importlib.util.module_from_spec(sp)
sp.loader.exec_module(g)
# зміна саме конфігурації/коду/правил — інакше «створю запис» теж план
CFG = re.compile(r"\.claude/hooks|\bхук\w*|\bhook|settings(?:\.local)?\.json|налаштуван\w*|SKILL\.md|\bскіл\w*|"
                 r"RULES\.md|CLAUDE\.md|ANALYZER\.md|AGENT\.md|\w+\.py\b|\w+\.sh\b|ENABLE_\w+", re.I)


def is_verify(name, inp):
    return (name == "Skill" and str(inp.get("skill", "")) == "verify-before-show") or name in g.VERIFY_TOOLS


def main():
    old = new = turns = 0
    samples = []
    for f in sorted(glob.glob(LOGS + "/*.jsonl")):
        lines = open(f, encoding="utf-8").read().splitlines()
        first = next((json.loads(l) for l in lines if '"type":"user"' in l.replace(" ", "")), {})
        if first.get("entrypoint") != "cli":
            continue
        # старий сигнал — як у хуку
        for t in g.iter_turns(lines):
            if not "".join(t["texts"]).strip():
                continue
            turns += 1
            old += "verify" in g.check(t)
        # новий: пройти записи по порядку в межах ходу
        verified, last_text = False, ""
        for l in lines:
            try:
                d = json.loads(l)
            except ValueError:
                continue
            if g.is_real_user(d):
                verified, last_text = False, ""
                continue
            if d.get("type") != "assistant":
                continue
            for x in (d.get("message") or {}).get("content") or []:
                if not isinstance(x, dict):
                    continue
                if x.get("type") == "text" and x.get("text", "").strip():
                    last_text = x["text"]
                elif x.get("type") == "tool_use":
                    inp = x.get("input") or {}
                    if is_verify(x.get("name"), inp):
                        verified = True
                    elif x.get("name") == "AskUserQuestion":
                        qs = " ".join(q.get("question", "") + " " + " ".join(
                            o.get("label", "") + " " + o.get("description", "") for o in q.get("options", []))
                            for q in inp.get("questions", []))
                        # ціль і дія — у самому віконці (текст перед ним дає забагато шуму: 386/1210)
                        if not verified and g.RE_CHANGE.search(qs) and CFG.search(qs):
                            new += 1
                            if len(samples) < 400:
                                samples.append((os.path.basename(f)[:8], d.get("timestamp", "")[:16],
                                                re.sub(r"\s+", " ", qs)[:120]))
    print(f"ходів з текстом {turns}; старий сигнал verify {old}; новий (питання у віконці) {new}")
    import random
    random.seed(16)
    for s in random.sample(samples, min(15, len(samples))):
        print("  ", *s)


if __name__ == "__main__":
    main()
