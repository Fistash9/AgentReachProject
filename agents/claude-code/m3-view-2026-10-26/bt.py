import json,sys,math,importlib.util as u
s=u.spec_from_file_location('hv','/data/data/com.termux/files/usr/tmp/m3-view-2610/handoff-view.py');m=u.module_from_spec(s);s.loader.exec_module(m)
f=sys.argv[1]; d=json.load(open(f,encoding='utf-8'))
targets=[int(x) for x in sys.argv[2].split(',')] if len(sys.argv)>2 else []
tn=int(sys.argv[3]) if len(sys.argv)>3 else 1
c=m.pair_candidates(d)
print(f, 'next',len(d.get('next') or []),'wo',len(d.get('watchOut') or []),'кандидатів пар',len(c),'унікальних wo',len({x[1] for x in c}))
print('пар на next:', [sum(1 for x in c if x[0]==i) for i in range(len(d.get('next') or []))])
print('Далі',tn,'→', [(x[1]+1, round(x[2],1)) for x in c if x[0]==tn-1])
# raw scores of targets for next tn
wo=[str(x).lower() for x in d['watchOut']]; N=len(wo); st=m.stems(d['next'][tn-1])
for t in targets:
    hit=[w for w in st if w in wo[t-1]]
    df={w:sum(1 for x in wo if w in x) for w in hit}
    print(' ціль #%d: збіги %s вага %.1f'%(t,hit,sum(math.log((N+1)/(df[w]+1)) for w in hit)))
for bud in (15000, 20000, 40000):
    text,nw,nd=m.build(d,bud); print('budget',bud,'size',m.b(text),'пар показано',len(m.build.pairs),'wo усього',nw,'done',nd)
