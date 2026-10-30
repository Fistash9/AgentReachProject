#!/usr/bin/env python3
"""Мітка «кінець ходу»: (a) AskUserQuestion з відповіддю, (b) текст-пропозиція без віконця, (c) звіт.
Запуск: python3 analyze.py [--samples] ; журнали — основні *.jsonl без subagents/."""
import json, glob, re, os, sys, random, collections, datetime as dt
D = os.path.expanduser('~/.claude/projects/-data-data-com-termux-files-home-AgentReachProject/')
GATE = 'ask-gate (ворота перед питанням'
CRIT = re.compile(r'що ти від мене хоч|не питай|зроби сам|знов\w* питаєш|забагато питань|навіщо (ти )?питаєш|чому (ти )?питаєш|навіщо ти в мене питаєш|ти ж? знаєш (правила|ідеї|ціль|все)|тобі знати|ти знаешь|у тебе є все|обирай логічно|роби як звичайно|я не чітаю', re.I)
DET = os.environ.get('DET', 'v2')  # v1: лише останній абзац; v2: + «пропоную/можу/хочеш/напишіть» у 2 останніх текстових блоках ходу
PROP2 = re.compile(r'пропоную|запропоную|пропозиц|хочеш|хочете|можу |напишіть «|напиши «', re.I)
PROP = re.compile(r'пропоную|пропозиц|хочеш|хочете|можу |зробити\?|\?', re.I)
def local(ts):
    t = dt.datetime.fromisoformat(ts.replace('Z', '+00:00'))
    off = 3 if t < dt.datetime(2026, 10, 25, 1, tzinfo=dt.timezone.utc) else 2
    return t + dt.timedelta(hours=off)
def last_para(text):
    lines = [l for l in text.strip().split('\n') if not re.match(r'\W*(Черга|Словами)', l.strip())]
    paras = [p for p in re.split(r'\n\s*\n', '\n'.join(lines)) if p.strip()]
    return paras[-1].strip() if paras else ''
def real_prompt(r):
    if r.get('isMeta') or r.get('isCompactSummary'): return None
    c = r['message'].get('content')
    if isinstance(c, list):
        if any(b.get('type') == 'tool_result' for b in c): return None
        c = ' '.join(b.get('text', '') for b in c if b.get('type') == 'text')
    if not isinstance(c, str) or not c.strip(): return None
    s = c.lstrip()
    if s.startswith(('<', 'Stop hook feedback', '[Request interrupted', 'Caveat:', 'This session is being continued')): return None
    return c
def events_of(f):
    ev = []; last = None; auq = {}
    for line in open(f):
        try: r = json.loads(line)
        except Exception: continue
        if r.get('isSidechain'): continue
        t = r.get('type'); ts = r.get('timestamp')
        if t == 'assistant':
            for b in r['message'].get('content', []) or []:
                if b.get('type') == 'text' and b['text'].strip():
                    prev = last[1] if last else ''
                    last = (ts, b['text'], prev)
                if b.get('type') == 'tool_use' and b.get('name') == 'AskUserQuestion': auq[b['id']] = ts
        elif t == 'user':
            c = r['message'].get('content')
            if isinstance(c, list):
                for b in c:
                    if b.get('type') == 'tool_result' and b.get('tool_use_id') in auq:
                        body = json.dumps(b.get('content'), ensure_ascii=False)
                        if b.get('is_error'):
                            ev.append(dict(ts=ts, k='deny' if GATE in body else 'auqerr', text=body[:200]))
                        else:
                            ev.append(dict(ts=auq[b['tool_use_id']], k='a', text=body[:200]))
                            ans = body.split('"=\\"', 1)[-1] if '"=\\"' in body else ''
                            if CRIT.search(ans): ev.append(dict(ts=ts, k='crit', text=ans[:150]))
                            last = None
            if isinstance(c, str) and r.get('isMeta') and 'питання без кнопок' in c:
                ev.append(dict(ts=ts, k='voice', text=''))
            p = real_prompt(r)
            if p is not None:
                if CRIT.search(p): ev.append(dict(ts=ts, k='crit', text=p[:150]))
                if last:
                    lp = last_para(last[1])
                    hit = PROP.search(lp) or (DET == 'v2' and PROP2.search(last_para(last[1]) + '\n' + '\n'.join(last[2].strip().split('\n\n')[-2:])))
                    ev.append(dict(ts=last[0], k='b' if hit else 'c', text=lp))
                last = None
    return ev
S = {}
for f in glob.glob(D + '*.jsonl'):
    if '"entrypoint":"cli"' not in open(f).read(): continue  # лише інтерактивні сесії (sdk-cli = headless-делегати)
    ev = events_of(f)
    if ev: S[os.path.basename(f)[:8]] = sorted(ev, key=lambda e: e['ts'])
def tally(evs):
    c = collections.Counter(e['k'] for e in evs); ab = c['a'] + c['b']
    return c, (c['b'] / ab if ab else float('nan'))
allev = [e for v in S.values() for e in v]
c, sh = tally(allev); print('ВСЬОГО', dict(c), 'b/(a+b)=%.2f' % sh)
if '--list' in sys.argv:
    for sid, ev in sorted(S.items(), key=lambda x: x[1][0]['ts']):
        for e in ev:
            if e['ts'] >= sys.argv[2] and e['k'] in ('b','crit','voice'): print(sid, local(e['ts']).strftime('%m-%d %H:%M'), e['k'], repr(e['text'][-170:]))
    sys.exit()
if '--samples' in sys.argv:
    random.seed(30)
    for k in 'bc':
        print('\n=== 10 випадкових класу', k)
        for e in random.sample([e for e in allev if e['k'] == k], 10):
            print('-', e['ts'][:16], repr(e['text'][-220:]))
    sys.exit()
print('\nДЕНЬ        a   b   c  deny crit voice  b/(a+b)')
byday = collections.defaultdict(list)
for e in allev: byday[local(e['ts']).date().isoformat()].append(e)
for d in sorted(byday):
    if '2026-10-01' <= d <= '2026-10-30':
        c, sh = tally(byday[d]); print(d, '%3d %3d %3d %4d %4d %4d   %.2f' % (c['a'], c['b'], c['c'], c['deny'], c['crit'], c['voice'], sh))
print('\nСЕСІЇ 28–30.10 (за першою подією)')
for sid, ev in sorted(S.items(), key=lambda x: x[1][0]['ts']):
    d0 = local(ev[0]['ts']).date().isoformat()
    if d0 >= '2026-10-28':
        c, sh = tally(ev); print(sid, local(ev[0]['ts']).strftime('%m-%d %H:%M'), 'a=%d b=%d c=%d deny=%d crit=%d voice=%d b/(a+b)=%.2f' % (c['a'], c['b'], c['c'], c['deny'], c['crit'], c['voice'], sh))
def after(ev, trig, K):
    """мітки a/b: у вікні K наступних передач після trig vs решта"""
    inw = 0; g = {'after': collections.Counter(), 'other': collections.Counter()}; nxt = collections.Counter()
    pend_next = False
    for e in ev:
        if e['k'] == trig: inw = K; pend_next = True; continue
        if e['k'] in 'ab':
            g['after' if inw > 0 else 'other'][e['k']] += 1
            if pend_next: nxt[e['k']] += 1; pend_next = False
            inw = max(0, inw - 1)
    return g, nxt
def show(name, evs):
    for trig, K in (('crit', 10), ('deny', 5)):
        g, nxt = after(evs, trig, K)
        fmt = lambda x: 'b=%d/n=%d (%.2f)' % (x['b'], x['a'] + x['b'], x['b'] / (x['a'] + x['b']) if x['a'] + x['b'] else float('nan'))
        print(' ', name, trig, 'K=%d' % K, 'після:', fmt(g['after']), 'решта:', fmt(g['other']), '| наступна одразу:', dict(nxt))
print('\nГІПОТЕЗИ (Г1=crit, K=10; Г2=deny, K=5)')
for sid in sys.argv[1:] or ['f98f7337', 'a11c12e0', '86fab127', 'a62774d0']:
    if sid in S: show(sid, S[sid])
show('УСІ', [e for v in S.values() for e in v])
show('УСІ з 16.10', [e for v in S.values() for e in v if e['ts'] >= '2026-10-16'])  # вікна не переходять межу сесії? — див. нижче
tot = {'after': collections.Counter(), 'other': collections.Counter()}
for v in S.values():
    g, _ = after(v, 'deny', 5)
    for k in tot: tot[k].update(g[k])
print('  УСІ (по сесіях) deny after', dict(tot['after']), 'other', dict(tot['other']))
tot = {'after': collections.Counter(), 'other': collections.Counter()}
for v in S.values():
    g, _ = after(v, 'crit', 10)
    for k in tot: tot[k].update(g[k])
print('  УСІ (по сесіях) crit after', dict(tot['after']), 'other', dict(tot['other']))
print('\nКРИТИКА (усі):')
for e in allev:
    if e['k'] == 'crit': print(' ', local(e['ts']).strftime('%m-%d %H:%M'), repr(e['text'][:110]))
