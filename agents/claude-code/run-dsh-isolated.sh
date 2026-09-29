#!/data/data/com.termux/files/usr/bin/bash
# run-dsh-isolated.sh — ПРОБА (етап 1): пробний DSH без кліків, але в ізоляції.
# Узгоджено з DSH 2026-09-30 (листи cc-1…cc-4 / dsh-isolation-review, dsh-stage1-review,
# dsh-stage1-copy). [claude-code, 2026-09-30]
#
# - --isolated: гість не бачить Termux (~/.claude, ~/.env тощо);
# - замість справжнього проєкту — копія /root/proj-trial (без .env і agent.py),
#   змонтована тим самим шляхом, тож шляхи з AGENTS.md збігаються;
# - DSH_HOME=/root/.dsh-trial: окремі сесії/сховища, справжній /root/.dsh не чіпається;
# - danger-full-access → approval: never (dsh-base/cordis.patch.yml:232,248);
# - профіль tui: без веб-сервера, тож писати пробному DSH ззовні нікому — циклу нема.
P=/data/data/com.termux/files/home/AgentReachProject
# Джерело --bind proot шукає з боку Termux, тож /root/proj-trial — через шлях до rootfs.
COPY=$PREFIX/var/lib/proot-distro/containers/ubuntu/rootfs/root/proj-trial
exec proot-distro login ubuntu --isolated --bind "$COPY:$P" -- bash -lc \
  "cd '$P' && env DSH_HOME=/root/.dsh-trial DSH_PERMISSION_MODE=danger-full-access \
   DSH_TUI_RETENTION_MAX_COUNT=0 /root/dsh-app/node_modules/.bin/dsh --profile tui"
