# Вкладка «Браузер» — спостереження за agent-browser (дослідження + проба, 2026-10-28)

Мета (запит 28.10): «вкладка з браузером, щоб я бачив процес роботи агентів у браузері».
Автор: [claude-code (під-агент), 2026-10-28]. Пробу зроблено в пісочниці, живу tmux-сесію й ~/.tmux.conf не чіпано.

## Висновок (головне)
Для Lightpanda картинки сторінки НЕ буде: стрім кадрів не працює (`screencasting:false`, жодного `frame` за ~7 с).
Працює потік ДІЙ: що відкрив, яку команду виконав, скільки тривала, заголовок/URL. Тому рекомендую
**текстову вкладку tmux** — маленький Node-скрипт читає WebSocket-стрім сесії agent-browser і друкує живий журнал.
Нуль нових фонових процесів (лише 1 процес node у самій вкладці), дашборд не потрібен.

## Що дає agent-browser (першоджерело: README + docs/dashboard.mdx, streaming.mdx, engines/lightpanda.mdx)
- Кожна сесія сама піднімає WebSocket-сервер стріму на випадковому порту (`stream status` показує порт; порт також у `~/.agent-browser/default.stream`). Повідомлення: `frame` (JPEG), `status`, `tabs`, `url`, `command`, `result`, `console`.
- `agent-browser dashboard start [--port N]` — вебдашборд на 4848: жива картинка (canvas), стрічка дій з часом, консоль, створення сесій. Вбудований у бінарник, окремого встановлення нема.
- Окремого файлового журналу дій нема (`~/.agent-browser/` — лише .pid/.sock/.stream/.config; `*.log` відсутні). Консоль сторінки — `agent-browser console`; відео — `record start` (потрібен ffmpeg; для Lightpanda не перевірялось).
- Дока про Lightpanda: скріншоти «залежать від підтримки CDP у Lightpanda»; headed/--profile/--state/extensions не підтримуються.

## Що ПЕРЕВІРЕНО (вивід цієї сесії)
Процеси користувача: до 19; після `dashboard start` 20; після `open` 22 (+ lightpanda, +демон agent-browser); у кінці після close/stop — 19, залишків немає.
| Перевірка | Результат |
|---|---|
| `dashboard start` → `curl http://127.0.0.1:4848/` | відповідає, HTML (`<!DOCTYPE html>… Next.js`) |
| `curl 4848/api/sessions` без Origin | `{"success":false,"error":"Origin, Referer, or dashboard access token is invalid."}` |
| те саме з `Origin: http://127.0.0.1:4848` | `[{"engine":"lightpanda","port":37621,"session":"default"}]` — дашборд бачить сесію Lightpanda |
| `open https://example.com`, `snapshot`, `get title` | працюють (Example Domain) |
| `stream status` | `ws://127.0.0.1:37621`, Connected: true, **Screencasting: false** |
| WS-клієнт (node) 7 с під час команд | отримано: status 2, tabs 7, command 6, result 6, url 1; **frame 0** |
| `screenshot …/ab-shot.png` | файл 59520 байт (з Lightpanda створюється). Що саме на картинці — НЕ ПЕРЕГЛЯДАВ (не перевірено) |
| прототип-спостерігач (нижче) | друкує рядки дій у реальному часі |

Зауваження з проби:
- У `result` поле `success` = false навіть для успішних команд (title повернув «Example Domain») — це дивність 0.40.0; покладатися на `success` не можна, скрипт дивиться на `data.error`.
- Перед кожною командою приходить службовий `launch` (reused) — скрипт його ховає.
- `click e1` без попереднього snapshot-посилання показав «ok» — чи справді клік вдався, не перевірено.
- Вебсокет-порт сесії змінюється при кожному новому запуску браузера; скрипт перечитує `~/.agent-browser/default.stream` і перепідключається.
- Інші сесії (`--session X`) мають свої `X.stream`; прототип стежить лише за `default`.

## Варіанти показу
| Варіант | Що видно | Процесів | З Lightpanda |
|---|---|---|---|
| (а) **Вкладка tmux із скриптом** (рекомендую) | рядки: час, команда і параметри, тривалість, заголовок/URL, консоль сторінки | +1 (node) | так — перевірено |
| (б) Дашборд у Chrome телефона: `agent-browser dashboard start` + `termux-open-url http://127.0.0.1:4848` | стрічка дій + консоль + вкладки; **полотно картинки буде порожнє** | +1 (демон дашборда) | частково: curl-перевірка пройшла, Chrome не відкривав |
| (в) `watch -n2 agent-browser get url` / `tail -f` | нічого цінного: журналу-файлу нема | +1 | — |
| (г) Відео `record start` | запис пізніше, не наживо | ffmpeg | не перевірялось |
Якщо колись перейдемо на Chrome-движок (`AGENT_BROWSER_ENGINE=chrome`, на Termux не встановлено/не перевірялось) — тоді дашборд (б) покаже і картинку.

## Рекомендація і команди
Причина: картинки Lightpanda не дає, а текстовий потік дій дає все, що в нього є, дешево й без дашборда (дашборд — ще один фоновий процес на телефоні з ліміт-обмеженням процесів).

1) Файл скрипта (покласти, напр., у `~/AgentReachProject/tools/ab-watch.js` — створення за погодженням; зараз лежить копією в `/data/data/com.termux/files/usr/tmp/wp-watch.keep.js`):
```js
const fs=require('fs'),os=require('os'),sf=os.homedir()+'/.agent-browser/default.stream';
const T=()=>new Date().toTimeString().slice(0,8);
let last='';
function connect(){
  let port; try{port=fs.readFileSync(sf,'utf8').trim()}catch{ if(last!=='w'){console.log(T(),'чекаю на сесію agent-browser...');last='w'} return setTimeout(connect,1500)}
  const ws=new WebSocket('ws://127.0.0.1:'+port+'/'); last='';
  ws.onopen=()=>console.log(T(),'підключено, порт',port);
  ws.onmessage=e=>{let m;try{m=JSON.parse(e.data)}catch{return}
    if(m.type==='command'&&m.action!=='launch')console.log(T(),'>>',m.action,JSON.stringify(m.params||{}).replace(/"(id|action|executablePath)":"[^"]*",?/g,'').slice(0,120));
    else if(m.type==='result'&&m.action!=='launch'){const d=m.data||{};const x=d.error||m.error;console.log(T(),'<<',m.action,x?'ПОМИЛКА '+String(x).slice(0,100):'ok',(m.duration_ms??'')+'мс',d.title?('«'+d.title+'»'):(d.url||''));}
    else if(m.type==='url')console.log(T(),'URL',m.url);
    else if(m.type==='console')console.log(T(),'console',m.level,m.text);
    else if(m.type==='error')console.log(T(),'error',e.data.slice(0,150));};
  ws.onclose=()=>setTimeout(connect,1500); ws.onerror=()=>{};
}
connect();
```
(потрібен Node з глобальним `WebSocket` — тут v26.4.0.)

2) Команда вкладки: `node ~/AgentReachProject/tools/ab-watch.js`
3) Пропонований пункт у меню `bind N` у `~/.tmux.conf` (НЕ застосовано; додати рядок поруч з рядками 37–40, перед останнім без `\` — слідкувати за `\` в кінці):
```
  "Браузер (дії)" b "new-window -n browser -c /data/data/com.termux/files/home/AgentReachProject 'exec node /data/data/com.termux/files/home/AgentReachProject/tools/ab-watch.js'" \
```
Для виходу: Ctrl+C у вкладці — скрипт сам нічого не залишає.

## Не працює / не перевірено
- Жива картинка сторінки (кадри) — з Lightpanda немає (screencasting:false, 0 кадрів).
- Дашборд у справжньому Chrome — не відкривав (заборонено); лише curl.
- Вміст скріншота (чи не порожній) — не дивився.
- `success:false` у `result` — вважати артефактом 0.40.0 (причину не з'ясовано).
- Спостереження за кількома сесіями (`--session`) — не реалізовано.
- Після проби лишився `~/.agent-browser/default.target` (малий службовий файл від `close`); процесів нема.

## Відкрите питання до користувача
Зробити вкладку (а) — текстову — і додати скрипт у tools/ та пункт меню? (створення файлу в tools/ і правка ~/.tmux.conf — лише після «так»; коміт — лише зі словом «коміт»).
