#!/usr/bin/env python3
# Служить: Q6 (trees/yakist-roboty-agentiv.md). Рахує паспорти документів. Лише читання.
import re,glob,os,sys
os.chdir('/data/data/com.termux/files/home/AgentReachProject')
docs={}
for m in re.finditer(r'\[[^\]]*\]\(\./([^)#]+?\.md)\)',open('README.md').read()):
    docs.setdefault(m.group(1),set()).add('readme')
for d in glob.glob('agents/claude-code/*/')+glob.glob('agents/dsh/'):
    if '.trash' in d or 'node_modules' in d: continue
    for f in glob.glob(d+'*.md'): docs.setdefault(f,set()).add('agents')
docs={k:v for k,v in docs.items() if os.path.isfile(k)}
mech=[f for f in glob.glob('tools/*.py')+glob.glob('.claude/hooks/*')+glob.glob('.claude/skills/*/SKILL.md') if os.path.isfile(f)]
rec=glob.glob('trees/*.md')+[f for f in ['RULES.md','RULES-WHY.md','BACKLOG.md','README.md','.baton/HANDOFF-view.md'] if os.path.isfile(f)]
tx={}
def T(f):
    if f not in tx:
        try: tx[f]=open(f,errors='ignore').read()
        except: tx[f]=''
    return tx[f]
def pat(p):
    b=re.escape(os.path.basename(p))
    if '/' in p: return re.compile(re.escape(p)+r'(?![\w-])|(?<![\w.\-])'+b+r'(?![\w-])')
    return re.compile(r'(?:^|[^\w.\-/]|\./)'+b+r'(?![\w-])')
rows=[]
for p in sorted(docs):
    head=''.join(open(p,errors='ignore').readlines()[:15])
    sl=bool(re.search(r'Служить:|Навіщо|Мета:',head))
    r=pat(p)
    nm=sum(1 for f in mech if os.path.abspath(f)!=os.path.abspath(p) and r.search(T(f)))
    nr=sum(1 for f in rec if os.path.abspath(f)!=os.path.abspath(p) and r.search(T(f)))
    nt=sum(1 for f in glob.glob('trees/*.md') if os.path.abspath(f)!=os.path.abspath(p) and r.search(T(f)))
    rows.append((p,sl,nm,nr,nt,'readme' in docs[p]))
if len(sys.argv)>1:
    for r in rows:
        if r[0]==sys.argv[1]: print(r)
    sys.exit()
print('| документ | джерело | служить | механізми | записи | вузол |\n|---|---|---|---|---|---|')
for p,sl,nm,nr,nt,rd in rows:
    print(f"| {p} | {'README' if rd else 'agents'} | {'так' if sl else 'ні'} | {nm} | {nr} | {'так' if nt else 'ні'} |")
print()
print('Всього документів:',len(rows),'(з карти README:',sum(r[5] for r in rows),')')
print('Без «служить»:',sum(1 for r in rows if not r[1]))
print('0 механізмів-читачів:',sum(1 for r in rows if r[2]==0))
print('Повні сироти (0 механізмів і 0 записів):',sum(1 for r in rows if r[2]==0 and r[3]==0))
print('Без вузла (жоден trees/*.md не згадує):',sum(1 for r in rows if r[4]==0))
print('Повні сироти з карти README:')
for r in rows:
    if r[5] and r[2]==0 and r[3]==0: print('-',r[0])
