#!/data/data/com.termux/files/usr/bin/bash
# menu.sh — стартове меню Agent Reach

clear
echo "========================================"
echo "   Agent Reach — стартове меню"
echo "========================================"
echo ""
echo "  1) Claude Code  +  Agent  +  Shell  (tmux)"
echo "  2) Тільки Agent (DeepSeek)"
echo "  3) Тільки Claude Code"
echo "  4) Чистий термінал (без агентів)"
echo "  5) Приєднатися до tmux-сесії 'work'"
echo "  0) Вийти з меню"
echo ""
read -p "Вибір: " choice

case "$choice" in
    1) exec ~/AgentReachProject/tmux-work.sh ;;
    2) cd ~/AgentReachProject && exec agent ;;
    3) cd ~/AgentReachProject && exec claude ;;
    4) ;;  # просто виходимо з меню — користувач отримує чистий bash
    5) exec tmux attach -t work ;;
    0|*) ;;
esac
