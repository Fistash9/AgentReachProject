# Джерела cases-v3 (2026-10-13)

У git — лише наші файли: витяги з git (`*-09c9be7.py`, `*-cf2390d.py`, `RULES-fde585f-deletion.md`)
і вивід `ls-hooks-tests-2026-10-07.txt`. Чужі тексти — у .gitignore; відновити з цієї теки:

```bash
T=$(mktemp -d)
curl -sL https://api-docs.deepseek.com/guides/anthropic_api   -o $T/deepseek-anthropic-api.html
curl -sL https://api-docs.deepseek.com/guides/thinking_mode   -o $T/deepseek-thinking-mode.html
curl -sL https://api-docs.deepseek.com/quick_start/pricing    -o $T/deepseek-pricing.html
curl -sL https://api-docs.deepseek.com/updates                -o $T/deepseek-updates.html
curl -sL https://api-docs.deepseek.com/news/news260910        -o $T/deepseek-news260910.html
curl -sL https://arxiv.org/html/2606.13174v1                  -o $T/arxiv-2606.13174.html
python3 - "$T" <<'P'
import re,html,glob,os,sys
for f in glob.glob(sys.argv[1]+'/*.html'):
    t=open(f,encoding='utf-8',errors='ignore').read()
    t=re.sub(r'(?s)<(script|style)[^>]*>.*?</\1>','',t); t=html.unescape(re.sub(r'<[^>]+>',' ',t)); t=re.sub(r'\s+',' ',t)
    open(os.path.basename(f)[:-5]+'.txt','w').write(t)
P
curl -sL https://code.claude.com/docs/en/hooks.md        -o claude-hooks.md
curl -sL https://code.claude.com/docs/en/model-config.md -o claude-model-config.md
# витяги, які отримує перевіряльник (номери рядків — копія 2026-10-13):
{ sed -n 1,40p claude-hooks.md; echo "[…]"; sed -n 2669,2772p claude-hooks.md; } > claude-hooks-stop.md
sed -n 698,730p claude-model-config.md > claude-model-config-thinking.md
```
Сторінки змінюються — цитати з results-v3 можуть розійтися з новою копією; перед повтором
звірити ключові цитати (колонка «Запис» у cases-v3.md) `grep -F`.

Змінені копії (наші, у git; рада 13.10):
```bash
nl -ba -w3 -s': ' request-brief-reminder-hook-09c9be7.py > request-brief-reminder-hook-09c9be7.numbered.txt
sed '127,128d' claimcheck-cf2390d.py > claimcheck-cf2390d-nodoc.py   # без докстрінга-підказки
```
