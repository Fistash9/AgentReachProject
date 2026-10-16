import re,sys
out=open(sys.argv[1],encoding='utf-8').read().splitlines()
src=open(sys.argv[2],encoding='utf-8').read()
norm=lambda s:re.sub(r'[«»"“”`\s]+',' ',s).strip()
S=norm(src)
ok=bad=0
for i,l in enumerate(out,1):
    if not l.startswith('- 2026') and not l.startswith('- (') and '— «' not in l: continue
    m=re.search(r'— «(.*)»(?:\s*\(помітив|\s*$|\s*\()',l)
    if not m: continue
    q=norm(m.group(1))
    # try full, then longest 4-word window
    if q in S: ok+=1; continue
    w=q.split(); hit=any(' '.join(w[j:j+4]) in S for j in range(max(1,len(w)-3)))
    print(('ЧАСТКОВО' if hit else 'НЕМАЄ'),i,q[:90]); bad+=1
print('повних',ok,'не повних',bad)
