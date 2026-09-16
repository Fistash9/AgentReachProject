#!/data/data/com.termux/files/usr/bin/bash
export MCPORTER_CONFIG="$HOME/AgentReachProject/config/mcporter.json"
export GH_CONFIG_DIR="$HOME/AgentReachProject/config/gh"
export YT_DLP_CONFIG="$HOME/AgentReachProject/config/yt-dlp/config"
agent-reach "$@"
