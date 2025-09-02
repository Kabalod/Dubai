# Система аутентификации

## Обзор

Подробное описание системы аутентификации и авторизации проекта Dubai.

## Архитектура аутентификации

### JWT токены
```typescript
interface JWTToken {
  access_token: string;    // Короткоживущий токен (15 мин)
  refresh_token: string;   // Долгоживущий токен (7 дней)
  expires_in: number;      // Время жизни в секундах
  token_type: string;      // Тип токена (Bearer)
}
```

### Структура JWT payload
```json
{
  "user_id": 123,
  "username": "john_doe",
  "email": "john@example.com",
  "role": "user",
  "permissions": ["read", "write"],
  "iat": 1640995200,
  "exp": 1640996100
}
```

## Endpoints аутентификации

### Регистрация
```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "secure_password123",
  "first_name": "John",
  "last_name": "Doe"
}
```

### Вход в систему
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "john_doe",
  "password": "secure_password123"
}
```

### Обновление токена
```http
POST /api/auth/refresh
Authorization: Bearer <refresh_token>
```

### Выход из системы
```http
POST /api/auth/logout
Authorization: Bearer <access_token>
```

### Проверка токена
```http
GET /api/auth/verify
Authorization: Bearer <access_token>
```

## Роли и разрешения

### Система ролей
```typescript
enum UserRole {
  ADMIN = 'admin',           // Полный доступ
  MODERATOR = 'moderator',   // Модерация контента
  AGENT = 'agent',           // Агент недвижимости
  USER = 'user'              // Обычный пользователь
}
```

### Разрешения
```typescript
interface Permission {
  resource: string;          // Ресурс (real_estate, users, etc.)
  action: string;            // Действие (read, write, delete)
  conditions?: object;       // Условия доступа
}

const permissions = {
  admin: ['*:*'],                    // Все разрешения
  moderator: ['*:read', 'content:write'],
  agent: ['real_estate:*', 'clients:read'],
  user: ['real_estate:read', 'profile:*']
};
```

## Middleware аутентификации

### Django Middleware
```python
## middleware.py
from django.http import JsonResponse
from django.conf import settings
import jwt
from functools import wraps

def jwt_auth_middleware(get_response):
    def middleware(request):
        # Пропускаем публичные endpoints
        if request.path.startswith('/api/auth/'):
            return get_response(request)
        
        # Проверяем токен
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            request.user_id = payload['user_id']
            request.user_role = payload['role']
        except jwt.ExpiredSignatureError:
            return JsonResponse({'error': 'Token expired'}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({'error': 'Invalid token'}, status=401)
        
        return get_response(request)
    
    return middleware
```

### FastAPI Middleware
```python
## dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from typing import Optional

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(
            credentials.credentials, 
            SECRET_KEY, 
            algorithms=[ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
```

## Безопасность

### Хеширование паролей
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
```

### Rate Limiting
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, user_credentials: UserLogin):
    # Логика входа
    pass
```

### Защита от брутфорса
```python
import time
from datetime import datetime, timedelta

class BruteForceProtection:
    def __init__(self):
        self.failed_attempts = {}
        self.lockout_duration = timedelta(minutes=15)
        self.max_attempts = 5
    
    def is_locked_out(self, username: str) -> bool:
        if username in self.failed_attempts:
            attempts, last_attempt = self.failed_attempts[username]
            if attempts >= self.max_attempts:
                if datetime.now() - last_attempt < self.lockout_duration:
                    return True
                else:
                    # Сброс блокировки
                    del self.failed_attempts[username]
        return False
    
    def record_failed_attempt(self, username: str):
        if username in self.failed_attempts:
            attempts, _ = self.failed_attempts[username]
            self.failed_attempts[username] = (attempts + 1, datetime.now())
        else:
            self.failed_attempts[username] = (1, datetime.now())
```

## Интеграция с фронтендом

### React Hook для аутентификации
```typescript
import { useState, useEffect, createContext, useContext } from 'react';

interface AuthContextType {
  user: User | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const login = async (credentials: LoginCredentials) => {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        
        // Получаем информацию о пользователе
        const userResponse = await fetch('/api/auth/me', {
          headers: { 'Authorization': `Bearer ${data.access_token}` }
        });
        
        if (userResponse.ok) {
          const userData = await userResponse.json();
          setUser(userData);
          setIsAuthenticated(true);
        }
      }
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated }}>
      {children}
    </AuthContext.Provider>
  );
};
```

### Защищенные маршруты
```typescript
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './useAuth';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: string;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requiredRole 
}) => {
  const { isAuthenticated, user } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requiredRole && user?.role !== requiredRole) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <>{children}</>;
};
```

## Мониторинг и логирование

### Логирование аутентификации
```python
import logging
from datetime import datetime

auth_logger = logging.getLogger('authentication')

def log_auth_event(event_type: str, username: str, success: bool, ip_address: str):
    auth_logger.info(
        f"Auth event: {event_type} | User: {username} | Success: {success} | IP: {ip_address} | Time: {datetime.now()}"
    )

## Использование
@limiter.limit("5/minute")
async def login(request: Request, user_credentials: UserLogin):
    try:
        # Логика входа
        log_auth_event("login", user_credentials.username, True, request.client.host)
        return {"access_token": token}
    except Exception as e:
        log_auth_event("login", user_credentials.username, False, request.client.host)
        raise HTTPException(status_code=401, detail="Invalid credentials")
```

### Метрики безопасности
```python
from prometheus_client import Counter, Histogram

## Метрики для мониторинга
login_attempts = Counter('auth_login_attempts_total', 'Total login attempts', ['status'])
auth_duration = Histogram('auth_request_duration_seconds', 'Authentication request duration')

## Использование в коде
@auth_duration.time()
async def authenticate_user(credentials: UserLogin):
    start_time = time.time()
    try:
        # Логика аутентификации
        login_attempts.labels(status='success').inc()
        return user
    except Exception:
        login_attempts.labels(status='failure').inc()
        raise
```

## Связанные документы

- [Обзор системы](./OVERVIEW.md)
- [Backend сервисы](./backend-services.md)
- [Frontend API](./frontend-api.md)
- [База данных](./database-schema.md)
- [AI агенты](./ai-agents.md)

---

**Статус**: Активный  
**Последнее обновление**: Август 2025

