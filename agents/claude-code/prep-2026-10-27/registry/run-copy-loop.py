"""Запуск --loop копії з реєстром оригіналу (у копії REGISTRY відносний — веде не туди); копію не змінює."""
import sys; sys.path.insert(0, "."); from scan import load
m = load("error-registry.py", "copy")
real = "/data/data/com.termux/files/home/AgentReachProject/agents/claude-code/q12-classes-2026-10-16/registry-v1.md"
m.REGISTRY = real; m.remedies.__defaults__ = (real,)
m.require_logs(); sys.exit(m.report_loop())
