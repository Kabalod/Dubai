### MCP Jira Server (Cursor)

Что это
- Лёгкий MCP-сервер для Jira, чтобы Cursor мог:
  - искать задачи по JQL,
  - добавлять комментарии,
  - переводить задачи по переходам статусов.

Где лежит
- Готовый сервер: `tools/jira-mcp` (cosmix/jira-mcp)

Переменные окружения
- `JIRA_SITE` — пример: `kbalodk.atlassian.net`
- `JIRA_EMAIL` — email аккаунта Jira
- `JIRA_TOKEN` — API Token Jira

Установка
```bash
cd tools
git clone https://github.com/cosmix/jira-mcp.git
cd jira-mcp
bun install
bun run build
```

Запуск локально
```bash
cd tools/mcp-jira
JIRA_SITE=... JIRA_EMAIL=... JIRA_TOKEN=... npm start
```

Подключение в Cursor (пример config)
```json
{
  "mcpServers": {
    "jira": {
      "command": "node",
      "args": ["D:/project/DUBAI_MVP/tools/jira-mcp/build/index.js"],
      "env": {
        "JIRA_API_TOKEN": "<token>",
        "JIRA_BASE_URL": "https://kbalodk.atlassian.net",
        "JIRA_USER_EMAIL": "<email>",
        "JIRA_TYPE": "cloud",
        "JIRA_AUTH_TYPE": "basic"
      }
    }
  }
}
```

Инструменты
- `jira_search_issues(jql)` → `{ count, issues[] }`
- `jira_add_comment(key, body)` → "Comment added"
- `jira_move_issue_status(key, transitionName)` → "Issue moved"

Примеры
```text
"Найди все задачи проекта KAN в статусе 'To Do'" → jira_search_issues("project = KAN AND status = 'To Do'")
"Переведи KAN-4 в 'In Progress'" → jira_move_issue_status({ key: "KAN-4", transitionName: "In Progress" })
"Добавь комментарий 'Готово' в KAN-4" → jira_add_comment({ key: "KAN-4", body: "Готово" })
```


Ссылки
- Документация MCP в Cursor: https://docs.cursor.com/en/context/mcp
- Готовый сервер Jira: https://github.com/cosmix/jira-mcp?ysclid=mervb6gt1r111273818


