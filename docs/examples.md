# Примеры использования

## Обзор

Практические примеры использования различных функций проекта Dubai.

## 🏠 Примеры работы с недвижимостью

### Создание объекта недвижимости
```python
import requests

## Создание нового объекта
new_property = {
    "title": "Роскошная квартира в Downtown Dubai",
    "description": "Современная 3-комнатная квартира с видом на Burj Khalifa",
    "price": 2500000,
    "price_currency": "AED",
    "property_type": "apartment",
    "bedrooms": 3,
    "bathrooms": 2,
    "area_sqft": 1800,
    "location": "Downtown Dubai",
    "district": "Downtown",
    "city": "Dubai",
    "country": "UAE",
    "latitude": 25.1972,
    "longitude": 55.2744
}

response = requests.post(
    "http://localhost:8000/api/real-estate/",
    json=new_property,
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

if response.status_code == 201:
    property_id = response.json()["id"]
    print(f"Объект создан с ID: {property_id}")
```

### Поиск недвижимости
```python
## Поиск по параметрам
search_params = {
    "location": "Dubai Marina",
    "min_price": 1000000,
    "max_price": 5000000,
    "property_type": "apartment",
    "bedrooms": 2
}

response = requests.get(
    "http://localhost:8000/api/real-estate/",
    params=search_params
)

properties = response.json()["results"]
for prop in properties:
    print(f"{prop['title']} - {prop['price']} AED")
```

### Обновление объекта
```python
## Обновление цены
update_data = {
    "price": 2400000,
    "status": "under_negotiation"
}

response = requests.patch(
    f"http://localhost:8000/api/real-estate/{property_id}/",
    json=update_data,
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

if response.status_code == 200:
    print("Объект успешно обновлен")
```

## 🤖 Примеры работы с AI

### Запрос к AI ассистенту
```python
## Простой запрос
ai_query = {
    "query": "Какие районы Dubai самые популярные для инвестиций в недвижимость?",
    "context": {
        "user_id": 123,
        "preferences": ["investment", "luxury"]
    },
    "agent_type": "market_analyst"
}

response = requests.post(
    "http://localhost:8003/api/ai/query",
    json=ai_query
)

ai_response = response.json()
print(f"AI ответ: {ai_response['response']}")
print(f"Уверенность: {ai_response['confidence']}")
```

### Использование AI агентов
```python
## Market Analyst Agent
market_query = {
    "query": "Проанализируйте тренды цен в Dubai Marina за последние 6 месяцев",
    "agent_type": "market_analyst"
}

response = requests.post(
    "http://localhost:8003/api/ai/query",
    json=market_query
)

## Property Recommender Agent
recommendation_query = {
    "query": "Порекомендуйте объекты в пределах 2M AED в Downtown Dubai",
    "context": {
        "user_id": 123,
        "budget": 2000000,
        "preferred_areas": ["Downtown Dubai", "Dubai Marina"]
    },
    "agent_type": "property_recommender"
}

response = requests.post(
    "http://localhost:8003/api/ai/query",
    json=recommendation_query
```

### Работа с Memory LLM Service
```python
## Сохранение информации в память
memory_data = {
    "content": "Пользователь интересуется инвестициями в недвижимость Dubai",
    "content_type": "user_preference",
    "metadata": {
        "user_id": 123,
        "timestamp": "2025-01-15T10:00:00Z",
        "category": "investment_preference"
    }
}

response = requests.post(
    "http://localhost:8080/api/memory/store",
    json=memory_data
)

## Поиск в памяти
search_query = {
    "query": "инвестиции недвижимость Dubai",
    "limit": 5
}

response = requests.post(
    "http://localhost:8080/api/memory/search",
    json=search_query
)

memories = response.json()
for memory in memories:
    print(f"Найдено: {memory['content']}")
```

## 📊 Примеры аналитики

### Получение рыночных данных
```python
## Рыночная аналитика
response = requests.get(
    "http://localhost:8001/api/analytics/market/",
    params={
        "area": "Dubai Marina",
        "property_type": "apartment",
        "period": "6months"
    }
)

market_data = response.json()
print(f"Средняя цена: {market_data['avg_price']} AED")
print(f"Объем продаж: {market_data['volume']}")
print(f"Дни на рынке: {market_data['days_on_market']}")
```

### Анализ трендов
```python
## Тренды цен
response = requests.get(
    "http://localhost:8001/api/analytics/trends/",
    params={
        "area": "Downtown Dubai",
        "property_type": "apartment",
        "metric": "price_per_sqft"
    }
)

trends = response.json()
for trend in trends:
    print(f"{trend['date']}: {trend['value']} AED/sqft")
```

### Кастомные аналитические запросы
```python
## Сложный аналитический запрос
analytics_query = {
    "query": """
        SELECT 
            area,
            property_type,
            AVG(price) as avg_price,
            COUNT(*) as volume,
            AVG(days_on_market) as avg_days
        FROM market_data 
        WHERE date >= '2024-07-01'
        GROUP BY area, property_type
        ORDER BY avg_price DESC
    """,
    "format": "json"
}

response = requests.post(
    "http://localhost:8001/api/analytics/query",
    json=analytics_query
)

results = response.json()
for result in results:
    print(f"{result['area']} - {result['property_type']}: {result['avg_price']} AED")
```

## 🔐 Примеры аутентификации

### Регистрация пользователя
```python
## Регистрация
registration_data = {
    "username": "john_doe",
    "email": "john@example.com",
    "password": "secure_password123",
    "first_name": "John",
    "last_name": "Doe"
}

response = requests.post(
    "http://localhost:8000/api/auth/register",
    json=registration_data
)

if response.status_code == 201:
    print("Пользователь успешно зарегистрирован")
```

### Вход в систему
```python
## Вход
login_data = {
    "username": "john_doe",
    "password": "secure_password123"
}

response = requests.post(
    "http://localhost:8000/api/auth/login",
    json=login_data
)

if response.status_code == 200:
    tokens = response.json()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    print("Успешный вход в систему")
```

### Использование токена
```python
## Запрос с аутентификацией
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

response = requests.get(
    "http://localhost:8000/api/real-estate/",
    headers=headers
)

if response.status_code == 200:
    properties = response.json()["results"]
    print(f"Найдено {len(properties)} объектов")
```

## 📱 Примеры фронтенда

### React компонент для поиска
```typescript
import React, { useState, useEffect } from 'react';

interface Property {
  id: number;
  title: string;
  price: number;
  location: string;
  bedrooms: number;
  bathrooms: number;
}

const PropertySearch: React.FC = () => {
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchParams, setSearchParams] = useState({
    location: '',
    minPrice: '',
    maxPrice: '',
    propertyType: ''
  });

  const searchProperties = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      Object.entries(searchParams).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });

      const response = await fetch(`/api/real-estate/?${params}`);
      const data = await response.json();
      setProperties(data.results);
    } catch (error) {
      console.error('Ошибка поиска:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="property-search">
      <div className="search-filters">
        <input
          type="text"
          placeholder="Локация"
          value={searchParams.location}
          onChange={(e) => setSearchParams({
            ...searchParams,
            location: e.target.value
          })}
        />
        <input
          type="number"
          placeholder="Мин. цена"
          value={searchParams.minPrice}
          onChange={(e) => setSearchParams({
            ...searchParams,
            minPrice: e.target.value
          })}
        />
        <input
          type="number"
          placeholder="Макс. цена"
          value={searchParams.maxPrice}
          onChange={(e) => setSearchParams({
            ...searchParams,
            maxPrice: e.target.value
          })}
        />
        <button onClick={searchProperties} disabled={loading}>
          {loading ? 'Поиск...' : 'Найти'}
        </button>
      </div>

      <div className="search-results">
        {properties.map(property => (
          <div key={property.id} className="property-card">
            <h3>{property.title}</h3>
            <p>Цена: {property.price.toLocaleString()} AED</p>
            <p>Локация: {property.location}</p>
            <p>Спальни: {property.bedrooms}, Ванные: {property.bathrooms}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PropertySearch;
```

### AI чат компонент
```typescript
import React, { useState } from 'react';

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
}

const AIChat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async () => {
    if (!inputText.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputText,
      isUser: true,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/ai/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          query: inputText,
          agent_type: 'general'
        })
      });

      const data = await response.json();
      
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: data.response,
        isUser: false,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Ошибка AI:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="ai-chat">
      <div className="chat-messages">
        {messages.map(message => (
          <div
            key={message.id}
            className={`message ${message.isUser ? 'user' : 'ai'}`}
          >
            <div className="message-content">
              {message.text}
            </div>
            <div className="message-timestamp">
              {message.timestamp.toLocaleTimeString()}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message ai">
            <div className="message-content">
              <span className="typing-indicator">AI печатает...</span>
            </div>
          </div>
        )}
      </div>

      <div className="chat-input">
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Задайте вопрос AI ассистенту..."
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
        />
        <button onClick={sendMessage} disabled={isLoading}>
          Отправить
        </button>
      </div>
    </div>
  );
};

export default AIChat;
```

## 🧪 Примеры тестирования

### Unit тесты для API
```python
import pytest
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

class RealEstateAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.property_data = {
            "title": "Тестовая квартира",
            "price": 1000000,
            "location": "Test Location",
            "bedrooms": 2,
            "bathrooms": 1
        }

    def test_create_property(self):
        """Тест создания объекта недвижимости"""
        response = self.client.post(
            reverse('real-estate-list'),
            self.property_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Тестовая квартира')
        self.assertEqual(response.data['price'], 1000000)

    def test_list_properties(self):
        """Тест получения списка объектов"""
        response = self.client.get(reverse('real-estate-list'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_property_detail(self):
        """Тест получения деталей объекта"""
        # Сначала создаем объект
        create_response = self.client.post(
            reverse('real-estate-list'),
            self.property_data,
            format='json'
        )
        property_id = create_response.data['id']
        
        # Получаем детали
        response = self.client.get(
            reverse('real-estate-detail', args=[property_id])
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], property_id)
```

### Тесты для AI агентов
```python
import pytest
from unittest.mock import Mock, patch
from ai_agents.market_analyst import MarketAnalystAgent

class TestMarketAnalystAgent:
    def setup_method(self):
        self.agent = MarketAnalystAgent()

    @patch('ai_agents.market_analyst.requests.get')
    def test_analyze_market(self, mock_get):
        """Тест анализа рынка"""
        # Мокаем ответ API
        mock_response = Mock()
        mock_response.json.return_value = {
            "avg_price": 1500000,
            "volume": 50,
            "trend": "increasing"
        }
        mock_get.return_value = mock_response

        result = self.agent.analyze_market("Dubai Marina", "apartment")
        
        assert "Dubai Marina" in result
        assert "apartment" in result
        assert "1500000" in result

    def test_agent_initialization(self):
        """Тест инициализации агента"""
        assert self.agent.agent.role == 'Market Analyst'
        assert 'market_data_tool' in [tool.name for tool in self.agent.agent.tools]
        assert 'trend_analysis_tool' in [tool.name for tool in self.agent.agent.tools]
```

## 📚 Дополнительные ресурсы

### Документация
- [API Reference](./api/overview.md)
- [Database Schema](./database-schema.md)
- [Authentication](./authentication.md)

### Код
- [GitHub Repository](https://github.com/your-username/dubai-project)
- [API Examples](./api/examples.md)
- [Frontend Components](./frontend-api.md)

---

**Статус**: Активный  
**Последнее обновление**: Август 2025

