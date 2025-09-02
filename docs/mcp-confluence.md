### Confluence MCP Server

Основано на проекте: [cosmix/confluence-mcp](https://github.com/cosmix/confluence-mcp?ysclid=mervdnwmcd206282598)

Требования
- Bun >= 1.0
- Аккаунт Confluence + API token

Установка
```bash
cd tools
git clone https://github.com/cosmix/confluence-mcp.git
cd confluence-mcp
bun install
bun run build
```

Переменные окружения
- `CONFLUENCE_API_TOKEN`
- `CONFLUENCE_BASE_URL` (например, `https://<org>.atlassian.net/wiki`)
- `CONFLUENCE_USER_EMAIL`

Подключение в Cursor (пример mcp.json)
```json
{
  "mcpServers": {
    "confluence": {
      "command": "node",
      "args": ["D:/project/DUBAI_MVP/tools/confluence-mcp/dist/index.js"],
      "env": {
        "CONFLUENCE_API_TOKEN": "<token>",
        "CONFLUENCE_BASE_URL": "https://<org>.atlassian.net/wiki",
        "CONFLUENCE_USER_EMAIL": "<email>"
      }
    }
  }
}
```

Примеры использования
- Получить страницу: `get_page({ pageId: "123", format: "markdown" })`
- Поиск: `search_pages({ query: "space = DEV AND label = docs", limit: 10 })`
- Комментарий: `add_comment({ pageId: "123", content: "<p>Текст</p>" })`

Ссылки
- Документация MCP в Cursor: [Cursor MCP docs](https://docs.cursor.com/en/context/mcp)

