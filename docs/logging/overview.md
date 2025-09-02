# Система логирования

## Обзор

Подробное описание системы логирования проекта Dubai.

## 🏗️ Архитектура логирования

### Компоненты системы
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Приложения    │    │   Filebeat      │    │   Logstash      │
│   (Логи)        │    │   (Сбор)        │    │   (Обработка)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Elasticsearch  │
                    │   (Хранение)    │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │     Kibana      │
                    │  (Визуализация) │
                    └─────────────────┘
```

### Источники логов
- **Real Estate API** - Django приложение
- **Analytics Service** - FastAPI сервис
- **AI Gateway** - AI сервисы
- **Memory LLM Service** - Java сервис
- **PostgreSQL** - База данных
- **Redis** - Кэш и очереди
- **Nginx** - Reverse proxy
- **Docker** - Контейнеры

## 📝 Типы логов

### Application Logs
```python
import logging
import json
from datetime import datetime

## Структурированное логирование
class StructuredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # JSON форматтер
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
        )
        
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_request(self, method, endpoint, status, duration, user_id=None):
        log_data = {
            "event_type": "http_request",
            "method": method,
            "endpoint": endpoint,
            "status": status,
            "duration_ms": duration,
            "user_id": user_id
        }
        self.logger.info(json.dumps(log_data))
    
    def log_error(self, error, context=None):
        log_data = {
            "event_type": "error",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context
        }
        self.logger.error(json.dumps(log_data))

## Использование
logger = StructuredLogger('dubai_api')
logger.log_request('GET', '/api/properties', 200, 150, user_id=123)
```

### Business Logs
```python
## Логи бизнес-событий
class BusinessLogger:
    def __init__(self):
        self.logger = logging.getLogger('business')
    
    def log_property_created(self, property_id, user_id, price, location):
        log_data = {
            "event_type": "property_created",
            "property_id": property_id,
            "user_id": user_id,
            "price": price,
            "location": location,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.logger.info(json.dumps(log_data))
    
    def log_user_login(self, user_id, ip_address, user_agent):
        log_data = {
            "event_type": "user_login",
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.logger.info(json.dumps(log_data))
    
    def log_ai_query(self, user_id, query, agent_type, response_time):
        log_data = {
            "event_type": "ai_query",
            "user_id": user_id,
            "query": query,
            "agent_type": agent_type,
            "response_time_ms": response_time,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.logger.info(json.dumps(log_data))

business_logger = BusinessLogger()
```

### System Logs
```python
## Системные логи
class SystemLogger:
    def __init__(self):
        self.logger = logging.getLogger('system')
    
    def log_database_connection(self, status, connection_count):
        log_data = {
            "event_type": "database_connection",
            "status": status,
            "connection_count": connection_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.logger.info(json.dumps(log_data))
    
    def log_memory_usage(self, memory_mb, threshold_mb):
        log_data = {
            "event_type": "memory_usage",
            "memory_mb": memory_mb,
            "threshold_mb": threshold_mb,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.logger.info(json.dumps(log_data))
    
    def log_service_health(self, service_name, status, response_time):
        log_data = {
            "event_type": "service_health",
            "service_name": service_name,
            "status": status,
            "response_time_ms": response_time,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.logger.info(json.dumps(log_data))

system_logger = SystemLogger()
```

## 🔧 Настройка логирования

### Django настройки
```python
## settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/dubai_api.log',
            'maxBytes': 10*1024*1024,  # 10MB
            'backupCount': 5,
            'formatter': 'json',
        },
        'elastic': {
            'class': 'logging.handlers.HTTPHandler',
            'host': 'localhost:9200',
            'url': '/dubai-logs/_doc',
            'method': 'POST',
            'formatter': 'json',
        },
    },
    'loggers': {
        'dubai_api': {
            'handlers': ['console', 'file', 'elastic'],
            'level': 'INFO',
            'propagate': False,
        },
        'dubai_auth': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'dubai_property': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'dubai_ai': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### FastAPI настройки
```python
## main.py
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time
import json

app = FastAPI()

## Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)

## Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Логирование входящего запроса
    logger.info(json.dumps({
        "event_type": "request_start",
        "method": request.method,
        "url": str(request.url),
        "client_ip": request.client.host,
        "user_agent": request.headers.get("user-agent")
    }))
    
    response = await call_next(request)
    
    # Логирование завершения запроса
    duration = time.time() - start_time
    logger.info(json.dumps({
        "event_type": "request_end",
        "method": request.method,
        "url": str(request.url),
        "status_code": response.status_code,
        "duration_ms": round(duration * 1000, 2)
    }))
    
    return response

## Логирование ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(json.dumps({
        "event_type": "exception",
        "method": request.method,
        "url": str(request.url),
        "error_type": type(exc).__name__,
        "error_message": str(exc)
    }))
    raise exc
```

### Java Spring Boot настройки
```xml
<!-- logback-spring.xml -->
<configuration>
    <appender name="CONSOLE" class="ch.qos.logback.core.ConsoleAppender">
        <encoder class="net.logstash.logback.encoder.LoggingEventCompositeJsonEncoder">
            <providers>
                <timestamp/>
                <logLevel/>
                <loggerName/>
                <message/>
                <mdc/>
                <stackTrace/>
            </providers>
        </encoder>
    </appender>
    
    <appender name="FILE" class="ch.qos.logback.core.rolling.RollingFileAppender">
        <file>logs/dubai_memory_llm.log</file>
        <rollingPolicy class="ch.qos.logback.core.rolling.TimeBasedRollingPolicy">
            <fileNamePattern>logs/dubai_memory_llm.%d{yyyy-MM-dd}.log</fileNamePattern>
            <maxHistory>30</maxHistory>
        </rollingPolicy>
        <encoder class="net.logstash.logback.encoder.LoggingEventCompositeJsonEncoder">
            <providers>
                <timestamp/>
                <logLevel/>
                <loggerName/>
                <message/>
                <mdc/>
                <stackTrace/>
            </providers>
        </encoder>
    </appender>
    
    <logger name="com.dubai.memoryllm" level="INFO"/>
    
    <root level="INFO">
        <appender-ref ref="CONSOLE"/>
        <appender-ref ref="FILE"/>
    </root>
</configuration>
```

## 📊 Ротация и архивирование

### Настройка ротации логов
```python
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import gzip
import os

## Ротация по размеру
def setup_size_rotation_logger(name, log_file, max_bytes=10*1024*1024, backup_count=5):
    logger = logging.getLogger(name)
    handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    
    formatter = logging.Formatter(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

## Ротация по времени
def setup_time_rotation_logger(name, log_file, when='midnight', interval=1, backup_count=30):
    logger = logging.getLogger(name)
    handler = TimedRotatingFileHandler(
        log_file,
        when=when,
        interval=interval,
        backupCount=backup_count
    )
    
    formatter = logging.Formatter(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

## Сжатие старых логов
def compress_old_logs(log_directory):
    for filename in os.listdir(log_directory):
        if filename.endswith('.log') and not filename.endswith('.gz'):
            filepath = os.path.join(log_directory, filename)
            with open(filepath, 'rb') as f_in:
                with gzip.open(filepath + '.gz', 'wb') as f_out:
                    f_out.writelines(f_in)
            os.remove(filepath)

## Использование
api_logger = setup_size_rotation_logger('dubai_api', 'logs/api.log')
system_logger = setup_time_rotation_logger('dubai_system', 'logs/system.log')
```

### Автоматическая очистка
```python
import os
import time
from datetime import datetime, timedelta

def cleanup_old_logs(log_directory, days_to_keep=30):
    """Удаление логов старше указанного количества дней"""
    cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
    
    for filename in os.listdir(log_directory):
        filepath = os.path.join(log_directory, filename)
        
        # Проверяем время последнего изменения
        if os.path.isfile(filepath):
            if os.path.getmtime(filepath) < cutoff_time:
                try:
                    os.remove(filepath)
                    print(f"Удален старый лог: {filename}")
                except OSError as e:
                    print(f"Ошибка при удалении {filename}: {e}")

def cleanup_by_size(log_directory, max_size_mb=1000):
    """Очистка логов по общему размеру"""
    total_size = 0
    files = []
    
    # Собираем информацию о файлах
    for filename in os.listdir(log_directory):
        filepath = os.path.join(log_directory, filename)
        if os.path.isfile(filepath):
            size = os.path.getsize(filepath)
            files.append((filepath, size, os.path.getmtime(filepath)))
            total_size += size
    
    # Сортируем по времени изменения (старые сначала)
    files.sort(key=lambda x: x[2])
    
    # Удаляем старые файлы, пока не достигнем нужного размера
    max_size_bytes = max_size_mb * 1024 * 1024
    for filepath, size, _ in files:
        if total_size <= max_size_bytes:
            break
        
        try:
            os.remove(filepath)
            total_size -= size
            print(f"Удален лог для освобождения места: {os.path.basename(filepath)}")
        except OSError as e:
            print(f"Ошибка при удалении {filepath}: {e}")

## Планировщик очистки
import schedule

def schedule_log_cleanup():
    # Ежедневная очистка в 2:00
    schedule.every().day.at("02:00").do(cleanup_old_logs, 'logs', 30)
    
    # Еженедельная очистка по размеру
    schedule.every().sunday.at("03:00").do(cleanup_by_size, 'logs', 1000)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

## Запуск в отдельном потоке
import threading
cleanup_thread = threading.Thread(target=schedule_log_cleanup, daemon=True)
cleanup_thread.start()
```

## 🔍 Поиск и анализ логов

### ELK Stack конфигурация
```yaml
## docker-compose.logging.yml
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.17.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:7.17.0
    volumes:
      - ./monitoring/logstash/pipeline:/usr/share/logstash/pipeline
      - ./logs:/logs
    ports:
      - "5044:5044"
      - "5000:5000/tcp"
      - "5000:5000/udp"
      - "9600:9600"
    environment:
      LS_JAVA_OPTS: "-Xmx256m -Xms256m"

  kibana:
    image: docker.elastic.co/kibana/kibana:7.17.0
    ports:
      - "5601:5601"
    environment:
      ELASTICSEARCH_URL: http://elasticsearch:9200
      ELASTICSEARCH_HOSTS: '["http://elasticsearch:9200"]'

  filebeat:
    image: docker.elastic.co/beats/filebeat:7.17.0
    volumes:
      - ./monitoring/filebeat/filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
      - ./logs:/logs:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro

volumes:
  elasticsearch_data:
```

### Filebeat конфигурация
```yaml
## filebeat.yml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /logs/*.log
  json.keys_under_root: true
  json.add_error_key: true
  json.message_key: message

- type: container
  paths:
    - '/var/lib/docker/containers/*/*.log'

processors:
- add_host_metadata: ~
- add_cloud_metadata: ~
- add_docker_metadata: ~
- add_kubernetes_metadata: ~

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  indices:
    - index: "dubai-logs-%{+yyyy.MM.dd}"

setup.kibana:
  host: "kibana:5601"

setup.dashboards.enabled: true
setup.template.enabled: true
```

### Logstash pipeline
```ruby
## pipeline/logstash.conf
input {
  beats {
    port => 5044
  }
}

filter {
  if [fields][service] == "dubai_api" {
    json {
      source => "message"
    }
    
    date {
      match => [ "timestamp", "ISO8601" ]
    }
    
    if [event_type] == "http_request" {
      mutate {
        add_field => { "log_type" => "api_request" }
      }
    }
    
    if [event_type] == "error" {
      mutate {
        add_field => { "log_type" => "error" }
      }
    }
  }
  
  if [fields][service] == "dubai_ai" {
    json {
      source => "message"
    }
    
    date {
      match => [ "timestamp", "ISO8601" ]
    }
    
    mutate {
      add_field => { "log_type" => "ai_service" }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "dubai-logs-%{+YYYY.MM.dd}"
  }
}
```

## 📈 Визуализация в Kibana

### Основные дашборды

#### 1. API Requests Dashboard
```json
{
  "dashboard": {
    "title": "API Requests Overview",
    "panels": [
      {
        "title": "Requests per Second",
        "type": "visualization",
        "visState": {
          "type": "line",
          "aggs": [
            {
              "id": "1",
              "enabled": true,
              "type": "count",
              "schema": "metric",
              "params": {}
            },
            {
              "id": "2",
              "enabled": true,
              "type": "date_histogram",
              "schema": "segment",
              "params": {
                "field": "timestamp",
                "timeRange": {
                  "from": "now-1h",
                  "to": "now"
                },
                "useNormalizedEsInterval": true,
                "scaleMetricValues": false,
                "interval": "auto",
                "drop_partials": false,
                "min_doc_count": 1,
                "extended_bounds": {}
              }
            }
          ]
        }
      }
    ]
  }
}
```

#### 2. Error Analysis Dashboard
```json
{
  "dashboard": {
    "title": "Error Analysis",
    "panels": [
      {
        "title": "Error Count by Type",
        "type": "visualization",
        "visState": {
          "type": "pie",
          "aggs": [
            {
              "id": "1",
              "enabled": true,
              "type": "count",
              "schema": "metric",
              "params": {}
            },
            {
              "id": "2",
              "enabled": true,
              "type": "terms",
              "schema": "segment",
              "params": {
                "field": "error_type",
                "size": 10,
                "order": "desc",
                "orderBy": "1"
              }
            }
          ]
        }
      }
    ]
  }
}
```

## 🚀 Развертывание

### Запуск системы логирования
```bash
## Запуск ELK Stack
docker-compose -f docker-compose.logging.yml up -d

## Проверка статуса
docker-compose -f docker-compose.logging.yml ps

## Просмотр логов
docker-compose -f docker-compose.logging.yml logs -f elasticsearch
```

### Проверка работоспособности
```bash
## Elasticsearch
curl http://localhost:9200/_cluster/health

## Kibana
open http://localhost:5601

## Проверка индексов
curl http://localhost:9200/_cat/indices?v
```

## 📚 Дополнительные ресурсы

### Документация
- [ELK Stack Documentation](https://www.elastic.co/guide/)
- [Filebeat Documentation](https://www.elastic.co/guide/en/beats/filebeat/current/index.html)
- [Logstash Documentation](https://www.elastic.co/guide/en/logstash/current/index.html)

### Полезные запросы
- [Elasticsearch Query DSL](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html)
- [Kibana Query Language](https://www.elastic.co/guide/en/kibana/current/kuery-query.html)

---

**Статус**: Активный  
**Последнее обновление**: Август 2025

