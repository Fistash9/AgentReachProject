# Agent Reach — Опис MCP-сервера

> **Не претендує на офіційний стандарт.** Це внутрішній опис власного
> MCP-сервера `my_mcp_server.py`. Офіційного маніфесту для локального
> stdio-сервера без публікації в реєстрі наразі не існує (issue #2963).

## Загальні відомості

- **Внутрішнє ім'я:** `agent-reach-tools` (з `Server("agent-reach-tools")`)
- **Версія опису:** `0.1.0`
- **Транспорт:** `stdio`
- **Точка входу:** `my_mcp_server.py`
- **Репозиторій:** `git@github.com:Fistash9/AgentReachProject.git`
- **Версія MCP-протоколу:** `2025-11-25`

## Залежності

- Python-пакет `mcp` версії `1.30.0`
- `curl` — для інструмента `read` (через `r.jina.ai`)
- CLI `agent-reach` — для інструментів `transcribe` та `status`

## Tools

### read
Отримує будь-яку веб-сторінку або RSS/Atom-стрічку як чистий текст/markdown
через Jina Reader (`curl -sL "https://r.jina.ai/<url>"`).

**Вхід:**
```json
{
  "type": "object",
  "properties": {
    "url": { "type": "string", "description": "URL of page or RSS feed" }
  },
  "required": ["url"]
}
```
**Вихід:** `TextContent` — текст сторінки/стрічки (обрізається до 8000 символів).

### transcribe
Транскрибує YouTube-відео або локальний аудіофайл (Whisper через Groq/OpenAI),
викликаючи `agent-reach transcribe "<url>"`.

**Вхід:**
```json
{
  "type": "object",
  "properties": {
    "url": { "type": "string", "description": "YouTube URL or local audio file path" }
  },
  "required": ["url"]
}
```
**Вихід:** `TextContent` — текст транскрипції (обрізається до 8000 символів).

### status
Показує статус Agent Reach: які канали встановлені й активні
(`agent-reach doctor`).

**Вхід:**
```json
{
  "type": "object",
  "properties": {}
}
```
**Вихід:** `TextContent` — вивід `agent-reach doctor`.
