# Вкладки tmux не закриваються на exit + меню «Відкрити» (2026-10-28) — [claude-code]
Мета: запит користувача 28.10. Живу систему не чіпали; чернетка: tmux.conf.draft (повний ~/.tmux.conf + додане).

## Що є (перевірено)
- tmux 3.7c (display-menu, remain-on-exit, respawn-pane — є). Скрипт: ~/AgentReachProject/tmux-work.sh; його ніхто не викликає з ~/.bashrc/.profile/.termux (grep порожній) — запуск руками / menu.sh.
- Вікна стартують так: `new-window` (shell) + `send-keys "exec claude"` / `"exec ~/AgentReachProject/start.sh"` / `"exec ~/AgentReachProject/run-dsh.sh"`, cwd ~/AgentReachProject. exec — щоб було менше процесів (TROUBLES.md:5817).
- Клавіші N і R у prefix вільні (list-keys); c/o/m/t зайняті стандартними.

## Рекомендація: (а) remain-on-exit on + `Ctrl+B R`
Причина: нуль додаткових процесів (мертва панель — без процесу), exec-економія 22.10 не ламається.
Користувач бачить: після exit вікно лишається, у ньому текст «Вихід (код N). Ctrl+B, R = оживити, Ctrl+B, & = закрити»; R запускає знову.
Нюанс: вікна з tmux-work.sh мають командою shell (claude у них — через send-keys), тому R у них оживляє shell, а не claude; claude/DSH знову — через меню. Вікна, створені меню, оживають тією самою командою.
Закрити вкладку остаточно: Ctrl+B & (було й раніше).

Відхилено: (б) `claude; exec bash` — sh -c лишається батьком на весь час роботи програми: +1 процес на вікно (+3 при трьох), проти ліміту 32 — саме те, що 22.10 прибирали. (в) hook pane-died → авто-respawn: exit у shell миттєво дає новий shell (нема «виходу» взагалі), ризик циклу при падінні програми — не беремо.

## Меню: Ctrl+B N «Відкрити»
Claude Code (c), DSH (d), Agent (a), Shell (s), роздільник, Оживити вкладку (r). Команди ті самі, що в tmux-work.sh, з `exec` (new-window виконує через sh -c; exec замінює його — зайвого процесу нема).

## Diff до ~/.tmux.conf (дописати в кінець; повний текст — tmux.conf.draft)
```
set -g remain-on-exit on
set -g remain-on-exit-format 'Вихід (код #{pane_dead_status}). Ctrl+B, R = оживити, Ctrl+B, & = закрити'
bind R respawn-pane -k
bind N display-menu -T "Відкрити" \
  "Claude Code" c "new-window -n claude -c ~/AgentReachProject 'exec claude'" \
  "DSH"         d "new-window -n dsh -c ~/AgentReachProject 'exec ~/AgentReachProject/run-dsh.sh'" \
  "Agent"       a "new-window -n agent -c ~/AgentReachProject 'exec ~/AgentReachProject/start.sh'" \
  "Shell"       s "new-window -c ~/AgentReachProject" \
  "" \
  "Оживити вкладку" r "respawn-pane -k"
```
tmux-work.sh не змінюється (лише застарілий коментар рядка 4 «вийшли з програми — вікно закривається» — дописати «(після remain-on-exit — лишається, Ctrl+B R)»; за бажанням).

## HELP.txt — додати в розділ «ВИХІД / ВІД'ЄДНАННЯ» і «ВІКНА»
```
   Ctrl+B, N      → меню «Відкрити»: Claude Code / DSH / Agent / Shell
   Ctrl+B, R      → оживити вкладку після exit (вона лишається, не закривається)
```
І змінити в HELP.txt «Ctrl+B, & → закрити ПОТОЧНЕ вікно» — лишається, це тепер єдиний спосіб закрити вкладку після exit.

## Як застосувати / відкотити
1. `cp ~/.tmux.conf ~/.tmux.conf.bak-20261028`
2. Дописати блок із чернетки (або `cp tmux.conf.draft ~/.tmux.conf`) → `tmux source-file ~/.tmux.conf` (або Ctrl+B r). remain-on-exit діє на вже існуючі вікна одразу (глобальна опція).
3. Відкат: `cp ~/.tmux.conf.bak-20261028 ~/.tmux.conf && tmux source-file ~/.tmux.conf && tmux set -g remain-on-exit off && tmux unbind N && tmux unbind R`. (source-file не знімає старі бінди — тому unbind.)
Побічне: уже мертві панелі лишаться мертвими до закриття.

## Перевірено на окремому сервері `tmux -L test -f tmux.conf.draft` (kill-server після)
- `show-options -g remain-on-exit` → `remain-on-exit on`; list-keys: є `N display-menu -T Відкрити "Claude Code" c … DSH d … Agent a … Shell s … "Оживити вкладку" r …` і `R respawn-pane -k` (конфіг без помилок).
- `send-keys exit` у вікні 0 → `dead=1 st=0` (вікно живе); `new-window "exec sh -c 'exit 3'"` → `x dead=1 st=3`.
- `respawn-pane -k -t t:0` → `dead=0 cmd=bash` (ожило). Для вікна x команда сама одразу виходить → знову dead (очікувано).
- Процеси користувача: до 19, під час 20, після kill-server 19 (межа 21 не досягнута).
- НЕ перевірено: візуальний вигляд display-menu на телефоні (клавіші/дотик) і текст remain-on-exit-format у живому клієнті — потрібен справжній клієнт; меню запускає реальні claude/DSH лише після застосування.

## Застосовано 28.10
Бекап: ~/.tmux.conf.bak-20261028. Додано блок з чернетки (рядки 27–42), шляхи повні /data/data/com.termux/files/home/AgentReachProject (grep '~/AgentReachProject' = 0).
- Тест-сервер (`tmux -L chk -f ~/.tmux.conf new-session ...`): remain-on-exit on; prefix N (display-menu Відкрити) і prefix R (respawn-pane -k) є.
- Живий: `tmux source-file ~/.tmux.conf` → exit=0; remain-on-exit on; prefix N і R є в list-keys.
- HELP.txt: дописано два рядки (Ctrl+B N, Ctrl+B R) в кінець.
Відкат: `cp ~/.tmux.conf.bak-20261028 ~/.tmux.conf && tmux source-file ~/.tmux.conf`; remain-on-exit вимкнути: `tmux set -g remain-on-exit off` (бінди N/R зняти: `tmux unbind N; tmux unbind R`).
