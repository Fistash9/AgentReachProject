#!/data/data/com.termux/files/usr/bin/bash
# tmux-work.sh — 3 вікна: claude / agent / shell

SESSION="work"
cd ~/AgentReachProject || exit 1

# Якщо сесія вже є — просто приєднуємось
if tmux has-session -t "$SESSION" 2>/dev/null; then
    exec tmux attach -t "$SESSION"
fi

# Вікно 1: Claude Code
tmux new-session -d -s "$SESSION" -n "claude" -c ~/AgentReachProject
tmux send-keys -t "$SESSION:claude" "claude" C-m

# Вікно 2: Agent (DeepSeek)
tmux new-window -t "$SESSION" -n "agent" -c ~/AgentReachProject
tmux send-keys -t "$SESSION:agent" "agent" C-m

# Вікно 3: чистий shell
tmux new-window -t "$SESSION" -n "shell" -c ~/AgentReachProject

# Стартуємо на Claude Code
tmux select-window -t "$SESSION:claude"
exec tmux attach -t "$SESSION"
