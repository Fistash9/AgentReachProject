#!/usr/bin/env python3
"""Самозвіти «питаю текстом, бо ворота/віконце…» (текстові блоки асистента, з 16.10, без дублів) + частка відмов воріт по днях + Г1 у 23–30.10."""
import json, glob, re, os, collections, importlib.util, sys, io, contextlib
D = os.path.expanduser('~/.claude/projects/-data-data-com-termux-files-home-AgentReachProject/')
pat = re.compile(r'текстом', re.I); why = re.compile(r'ворота|віконц[^\s]* (не |знову |зупин)|зарахують', re.I)
seen = set(); per = collections.Counter()
for f in sorted(glob.glob(D + '*.jsonl')):
    if '"entrypoint":"cli"' not in open(f).read(): continue
    for line in open(f):
        try: r = json.loads(line)
        except Exception: continue
        if r.get('type') != 'assistant' or r.get('isSidechain') or r.get('timestamp', '') < '2026-10-16': continue
        for b in r['message'].get('content', []):
            t = b.get('text', '')
            sents = re.split(r'(?<=[.!?:])\s+', t)
            for i, s in enumerate(sents):
                ctx = ' '.join(sents[max(0, i - 1):i + 1])  # речення + попереднє
                if pat.search(s) and why.search(ctx) and re.search(r'(питаю|питав|спитаю)', s, re.I):
                    key = (os.path.basename(f)[:8], s[:60])
                    if key not in seen: seen.add(key); per[r['timestamp'][:10]] += 1; print(key[0], r['timestamp'][:16], repr(s[:160]))
print('САМОЗВІТИ по днях (UTC):', dict(sorted(per.items())), 'всього', sum(per.values()))
sys.argv = ['x', '--none']; spec = importlib.util.spec_from_file_location('a', os.path.join(os.path.dirname(__file__) or '.', 'analyze.py')); a = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()): spec.loader.exec_module(a)
byd = collections.defaultdict(collections.Counter)
for v in a.S.values():
    for e in v: byd[a.local(e['ts']).date().isoformat()][e['k']] += 1
print('ВІДМОВИ ВОРІТ deny/(a+deny):', ' '.join('%s:%d/%d' % (d[8:], c['deny'], c['a'] + c['deny']) for d, c in sorted(byd.items()) if d >= '2026-10-16'))
a.show('23–30.10', [e for v in a.S.values() for e in v if e['ts'] >= '2026-10-22T21'])
a.show('16–22.10', [e for v in a.S.values() for e in v if '2026-10-15T21' <= e['ts'] < '2026-10-22T21'])
