# Frontend API

## Обзор

Документация по API для фронтенд приложения Dubai Project.

## Основные endpoints

### Аутентификация
- `POST /api/auth/login` - Вход в систему
- `POST /api/auth/logout` - Выход из системы
- `POST /api/auth/refresh` - Обновление токена

### Недвижимость
- `GET /api/real-estate` - Список объектов недвижимости
- `GET /api/real-estate/{id}` - Детали объекта
- `POST /api/real-estate` - Создание объекта
- `PUT /api/real-estate/{id}` - Обновление объекта
- `DELETE /api/real-estate/{id}` - Удаление объекта

### Аналитика
- `GET /api/analytics/market` - Рыночная аналитика
- `GET /api/analytics/trends` - Тренды рынка
- `GET /api/analytics/reports` - Аналитические отчеты

### AI сервисы
- `POST /api/ai/query` - Запрос к AI ассистенту
- `GET /api/ai/memory` - Доступ к памяти AI
- `POST /api/ai/agents` - Взаимодействие с AI агентами

## Аутентификация

### JWT токены
```typescript
interface AuthResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}
```

### Заголовки запросов
```typescript
headers: {
  'Authorization': `Bearer ${accessToken}`,
  'Content-Type': 'application/json'
}
```

## Обработка ошибок

### Стандартные коды ошибок
- `400` - Неверный запрос
- `401` - Не авторизован
- `403` - Доступ запрещен
- `404` - Не найдено
- `500` - Внутренняя ошибка сервера

### Формат ошибки
```typescript
interface ApiError {
  error: string;
  message: string;
  details?: any;
  timestamp: string;
}
```

## Примеры использования

### React Hook для API
```typescript
import { useState, useEffect } from 'react';

const useApi = <T>(url: string) => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(url)
      .then(res => res.json())
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false));
  }, [url]);

  return { data, loading, error };
};
```

### Запрос с аутентификацией
```typescript
const fetchWithAuth = async (url: string, options: RequestInit = {}) => {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  if (response.status === 401) {
    // Попытка обновить токен
    await refreshToken();
    return fetchWithAuth(url, options);
  }

  return response;
};
```

## Связанные документы

- [Обзор системы](./OVERVIEW.md)
- [Backend сервисы](./backend-services.md)
- [AI агенты](./ai-agents.md)
- [База данных](./database-schema.md)
- [Аутентификация](./authentication.md)

---

**Статус**: Активный  
**Последнее обновление**: Август 2025
