# Система мониторинга

## Обзор

Подробное описание системы мониторинга и алертинга проекта Dubai.

## 🏗️ Архитектура мониторинга

### Компоненты системы
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Prometheus    │    │     Grafana     │    │   Alertmanager  │
│   (Метрики)     │    │ (Визуализация)  │    │   (Алерты)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Pushgateway   │
                    │ (Batch метрики) │
                    └─────────────────┘
```

### Источники метрик
- **Real Estate API** - Django приложение
- **Analytics Service** - FastAPI сервис
- **AI Gateway** - AI сервисы
- **Memory LLM Service** - Java сервис
- **PostgreSQL** - База данных
- **Redis** - Кэш и очереди
- **Nginx** - Reverse proxy

## 📊 Основные метрики

### API метрики
```python
from prometheus_client import Counter, Histogram, Gauge

## Счетчики запросов
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

## Время ответа
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

## Активные соединения
http_connections_active = Gauge(
    'http_connections_active',
    'Active HTTP connections'
)
```

### Бизнес метрики
```python
## Метрики недвижимости
properties_total = Gauge('properties_total', 'Total properties')
properties_by_status = Gauge(
    'properties_by_status',
    'Properties by status',
    ['status']
)

## Метрики пользователей
users_total = Gauge('users_total', 'Total users')
active_users = Gauge('active_users', 'Active users in last 24h')

## AI метрики
ai_queries_total = Counter(
    'ai_queries_total',
    'Total AI queries',
    ['agent_type', 'status']
)

ai_response_time = Histogram(
    'ai_response_time_seconds',
    'AI response time',
    ['agent_type']
)
```

### Системные метрики
```python
## База данных
db_connections_active = Gauge('db_connections_active', 'Active DB connections')
db_query_duration = Histogram('db_query_duration_seconds', 'DB query duration')

## Redis
redis_connections = Gauge('redis_connections', 'Redis connections')
redis_memory_usage = Gauge('redis_memory_bytes', 'Redis memory usage')

## Системные ресурсы
cpu_usage_percent = Gauge('cpu_usage_percent', 'CPU usage percentage')
memory_usage_bytes = Gauge('memory_usage_bytes', 'Memory usage in bytes')
disk_usage_percent = Gauge('disk_usage_percent', 'Disk usage percentage')
```

## 🔧 Настройка Prometheus

### Конфигурация prometheus.yml
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alerts.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'real-estate-api'
    static_configs:
      - targets: ['real-estate-api:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'analytics-service'
    static_configs:
      - targets: ['analytics-service:8001']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'ai-gateway'
    static_configs:
      - targets: ['ai-gateway:8003']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'memory-llm-service'
    static_configs:
      - targets: ['memory-llm-service:8080']
    metrics_path: '/actuator/prometheus'
    scrape_interval: 15s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
    scrape_interval: 30s

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:9113']
    scrape_interval: 30s
```

### Docker Compose для Prometheus
```yaml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'

  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:latest
    environment:
      DATA_SOURCE_NAME: "postgresql://user:pass@postgres:5432/dubai?sslmode=disable"
    ports:
      - "9187:9187"

  redis-exporter:
    image: oliver006/redis_exporter:latest
    environment:
      REDIS_ADDR: "redis://redis:6379"
    ports:
      - "9121:9121"

  nginx-exporter:
    image: nginx/nginx-prometheus-exporter:latest
    command:
      - -nginx.scrape-uri=http://nginx/nginx_status
    ports:
      - "9113:9113"

volumes:
  prometheus_data:
```

## 📈 Настройка Grafana

### Основные дашборды

#### 1. API Overview Dashboard
```json
{
  "dashboard": {
    "title": "API Overview",
    "panels": [
      {
        "title": "HTTP Requests per Second",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])",
            "legendFormat": "5xx errors"
          }
        ]
      }
    ]
  }
}
```

#### 2. Business Metrics Dashboard
```json
{
  "dashboard": {
    "title": "Business Metrics",
    "panels": [
      {
        "title": "Properties by Status",
        "type": "piechart",
        "targets": [
          {
            "expr": "properties_by_status",
            "legendFormat": "{{status}}"
          }
        ]
      },
      {
        "title": "Active Users",
        "type": "stat",
        "targets": [
          {
            "expr": "active_users",
            "legendFormat": "Active Users"
          }
        ]
      },
      {
        "title": "AI Queries",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(ai_queries_total[5m])",
            "legendFormat": "{{agent_type}}"
          }
        ]
      }
    ]
  }
}
```

#### 3. System Health Dashboard
```json
{
  "dashboard": {
    "title": "System Health",
    "panels": [
      {
        "title": "CPU Usage",
        "type": "gauge",
        "targets": [
          {
            "expr": "cpu_usage_percent",
            "legendFormat": "CPU %"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "type": "gauge",
        "targets": [
          {
            "expr": "memory_usage_bytes / 1024 / 1024 / 1024",
            "legendFormat": "Memory GB"
          }
        ]
      },
      {
        "title": "Database Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "db_connections_active",
            "legendFormat": "Active Connections"
          }
        ]
      }
    ]
  }
}
```

### Импорт дашбордов
```bash
## Создание папки для дашбордов
mkdir -p monitoring/grafana/dashboards

## Копирование JSON файлов дашбордов
cp api-overview.json monitoring/grafana/dashboards/
cp business-metrics.json monitoring/grafana/dashboards/
cp system-health.json monitoring/grafana/dashboards/

## Импорт через Grafana API
curl -X POST \
  -H "Content-Type: application/json" \
  -d @monitoring/grafana/dashboards/api-overview.json \
  http://admin:admin@localhost:3000/api/dashboards/db
```

## 🚨 Система алертов

### Конфигурация alerts.yml
```yaml
groups:
  - name: api_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }} seconds"

  - name: business_alerts
    rules:
      - alert: NoNewProperties
        expr: increase(properties_total[1h]) == 0
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "No new properties added"
          description: "No new properties have been added in the last hour"

      - alert: LowActiveUsers
        expr: active_users < 10
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Low active users"
          description: "Only {{ $value }} active users"

  - name: system_alerts
    rules:
      - alert: HighCPUUsage
        expr: cpu_usage_percent > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage"
          description: "CPU usage is {{ $value }}%"

      - alert: HighMemoryUsage
        expr: memory_usage_bytes / 1024 / 1024 / 1024 > 8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value }} GB"

      - alert: DatabaseConnectionHigh
        expr: db_connections_active > 50
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High database connections"
          description: "{{ $value }} active database connections"
```

### Настройка Alertmanager
```yaml
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@dubai-project.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
  - name: 'web.hook'
    webhook_configs:
      - url: 'http://localhost:5001/'

  - name: 'email'
    email_configs:
      - to: 'admin@dubai-project.com'
        send_resolved: true

  - name: 'slack'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
        channel: '#alerts'
        send_resolved: true
```

## 📝 Логирование

### Structured Logging
```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)

## Настройка логгера
logger = logging.getLogger('dubai_api')
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)

## Использование
logger.info('User login successful', extra={
    'user_id': 123,
    'request_id': 'req_456'
})
```

### Логирование в файлы
```python
import logging
from logging.handlers import RotatingFileHandler

## Настройка ротации логов
file_handler = RotatingFileHandler(
    'logs/dubai_api.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)

file_handler.setFormatter(JSONFormatter())
logger.addHandler(file_handler)

## Отдельные логгеры для разных компонентов
auth_logger = logging.getLogger('dubai_auth')
property_logger = logging.getLogger('dubai_property')
ai_logger = logging.getLogger('dubai_ai')
```

## 🔍 Поиск и анализ логов

### ELK Stack конфигурация
```yaml
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.17.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
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

volumes:
  elasticsearch_data:
```

### Logstash pipeline
```ruby
input {
  file {
    path => "/logs/*.log"
    type => "dubai_logs"
    start_position => "beginning"
  }
}

filter {
  if [type] == "dubai_logs" {
    json {
      source => "message"
    }
    
    date {
      match => [ "timestamp", "ISO8601" ]
    }
    
    if [user_id] {
      mutate {
        add_field => { "user_id" => "%{[user_id]}" }
      }
    }
    
    if [request_id] {
      mutate {
        add_field => { "request_id" => "%{[request_id]}" }
      }
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

## 🚀 Развертывание

### Запуск мониторинга
```bash
## Запуск всех сервисов мониторинга
docker-compose -f docker-compose.monitoring.yml up -d

## Проверка статуса
docker-compose -f docker-compose.monitoring.yml ps

## Просмотр логов
docker-compose -f docker-compose.monitoring.yml logs -f prometheus
```

### Проверка работоспособности
```bash
## Prometheus
curl http://localhost:9090/api/v1/targets

## Grafana
open http://localhost:3000
## Логин: admin, Пароль: admin

## Elasticsearch
curl http://localhost:9200/_cluster/health

## Kibana
open http://localhost:5601
```

## 📚 Дополнительные ресурсы

### Документация
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [ELK Stack Documentation](https://www.elastic.co/guide/)

### Полезные запросы
- [Prometheus Query Examples](https://prometheus.io/docs/prometheus/latest/querying/examples/)
- [Grafana Dashboard Examples](https://grafana.com/grafana/dashboards/)

---

**Статус**: Активный  
**Последнее обновление**: Август 2025

