### MCP: обзор и подключение в Cursor

Что такое MCP
- Протокол для подключения внешних инструментов к Cursor через stdio/SSE/HTTP. См. официальную документацию: [Cursor MCP docs](https://docs.cursor.com/en/context/mcp).

Где хранить конфиг
- Глобально: `~/.cursor/mcp.json` (Windows: `C:\Users\<USER>\.cursor\mcp.json`)
- Проектно: `.cursor/mcp.json` внутри репозитория

Пример структуры `mcp.json`
```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "mcp-server"],
      "env": { "API_KEY": "value" }
    }
  }
}
```

Аутентификация
- Рекомендуется хранить секреты в переменных окружения ОС, а не в файле `mcp.json`.

Отладка
- В Cursor → Output → MCP Logs: смотрите запуск, аргументы инструментов и ошибки.


