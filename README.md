# Agent Reach

Особистий фреймворк для запуску AI-агента (DeepSeek) поруч із Claude Code через MCP.

## Quick Start

Запустити агента напряму:

```bash
agent
```

Або через стартове меню tmux (Claude Code + Agent + Shell в одній сесії):

```bash
~/AgentReachProject/menu.sh
```

## Documentation Map

| Файл | Опис |
|---|---|
| [CONTEXT.md](./CONTEXT.md) | Поточний стан, цілі, архітектура |
| [RULES.md](./RULES.md) | Правила роботи агента |
| [RULES-WHY.md](./RULES-WHY.md) | Чому правила саме такі (читати перед зміною правила) |
| [TROUBLES.md](./TROUBLES.md) | Підводні камені та рішення |
| [BACKLOG.md](./BACKLOG.md) | Відкладені задачі |
| [ECOSYSTEM.md](./ECOSYSTEM.md) | Концепції композиції агентів |
| [SERVER.md](./SERVER.md) | Опис MCP-сервера |
| [HANDOFF.md](./HANDOFF.md) | Стан передачі контексту (Baton) |
| [TRASH.md](./TRASH.md) | Журнал видалень (запис ДО rm) |
| [USER_PROFILE.md](./USER_PROFILE.md) | Портрет користувача |
| [WEEKLY.md](./WEEKLY.md) | Тижневі підсумки й відбір уроків (проба з 2026-09-26) |
| [trees/](./trees/) | Живі дерева великих задач: картки STATUS/done when/evidence (проба з 2026-09-26) |
| [tools/](./tools/) | check-links.py, claimcheck/, watch-deepseek.py — перевірки й стеження |
| [tools/provider-switch.py](./tools/provider-switch.py) | Перемикач провайдера delegate і хука: DeepSeek ↔ NVIDIA gpt-oss (menu.sh п.8) |
| [tools/nvidia-live.py](./tools/nvidia-live.py) | Живий прогін моделей NVIDIA в консолі (меню моделей і кейсів) |
| [tools/verifier-backtest/](./tools/verifier-backtest/) | Бектести верифікатора: кейси, результати (DeepSeek і NVIDIA) |
| [.claude/skills/verify-before-show/](./.claude/skills/verify-before-show/) | Скіл: звірка тверджень з джерелом до показу (промпт v2) |

## Tech Stack

Python · MCP · Claude Code · DeepSeek
