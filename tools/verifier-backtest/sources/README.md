# Джерела бектесту

У git лежать лише власні виводи: `memory-ls.txt`, `npm-claude-mem.txt`.
Чужі тексти (репозиторій публічний) у .gitignore. Щоб відновити їх,
запусти з цієї теки:

```bash
# сторінки → текст (той самий спосіб, що 2026-09-24)
curl -sL https://arxiv.org/abs/2512.08296  -o arxiv-2512.08296-abs.html
curl -sL https://arxiv.org/html/2512.08296 -o arxiv-2512.08296.html
curl -sL https://www.anthropic.com/engineering/multi-agent-research-system -o anthropic-multi-agent.html
python3 - <<'P'
import re,html,glob
for f in glob.glob('*.html'):
    t=open(f,encoding='utf-8',errors='ignore').read()
    t=re.sub(r'(?s)<(script|style)[^>]*>.*?</\1>','',t); t=html.unescape(re.sub(r'<[^>]+>',' ',t)); t=re.sub(r'\s+',' ',t)
    open(f[:-5]+'.txt','w').write(t)
P
# baton-mcp v0.1.0 (MIT, @timurabi3)
B=$(npm root -g)/@timurabi3/baton-mcp
cp $B/server.mjs baton-server.mjs.txt; cp $B/PROTOCOL.md baton-PROTOCOL.md
# FreeLLMAPI README (MIT, tashfeenahmed/freellmapi)
curl -sL https://raw.githubusercontent.com/tashfeenahmed/freellmapi/HEAD/README.md -o freellmapi-README.md
```

Сторінки з часом змінюються, тож цитати з results*.md можуть
розійтися з новою копією. Копії станом на 2026-09-24 є в гілці
`backup/before-sources-filter-2026-09-24` (локальна, не пушиться).
