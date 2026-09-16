#!/data/data/com.termux/files/usr/bin/bash
export MCPORTER_CONFIG="$HOME/AgentReachProject/config/mcporter.json"
export GH_CONFIG_DIR="$HOME/AgentReachProject/config/gh"
export YT_DLP_CONFIG="$HOME/AgentReachProject/config/yt-dlp.conf"
cd "$HOME/AgentReachProject"
exec python -m agent_reach.integrations.mcp_server
