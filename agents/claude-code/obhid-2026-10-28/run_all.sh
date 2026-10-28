#!/data/data/com.termux/files/usr/bin/bash
# Відтворює весь бектест «пошук обходу» (2026-10-28). Читає журнали сесій лише на читання; пише тільки в $T і в цю теку.
D=/data/data/com.termux/files/home/AgentReachProject/agents/claude-code/obhid-2026-10-28
T=/data/data/com.termux/files/usr/tmp/obhid
mkdir -p $T && cd $T || exit 1
echo "######## extract"; python3 -I $D/extract.py > $T/extract.log 2>&1; grep -E "^(files|lines|parse_err|hint_attachments|tool_use:Bash)" $T/extract.log
for s in bt_stage1 bt_stage1b bt_stage2 bt_stage3 bt_stage4 bt_stage5 bt_stage6; do echo; echo "######## $s"; python3 -I $D/$s.py 2>&1; done
