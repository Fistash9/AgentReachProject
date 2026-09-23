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
| [tools/](./tools/) | check-links.py, claimcheck/, watch-deepseek.py — перевірки й стеження |

## Tech Stack

Python · MCP · Claude Code · DeepSeek
