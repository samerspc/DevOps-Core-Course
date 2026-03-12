# Monitoring Stack - Loki, Promtail, Grafana

Централизованная система логирования для приложений DevOps курса.

## Быстрый старт

```bash
# Запуск стека
cd monitoring
docker compose up -d

# Проверка статуса
docker compose ps

# Просмотр логов
docker compose logs -f

# Остановка
docker compose down
```

## Доступ к сервисам

- **Grafana**: http://localhost:3000 (анонимный доступ включен для разработки)
- **Loki API**: http://localhost:3100
- **Promtail API**: http://localhost:9080
- **Python App**: http://localhost:8000
- **Go App**: http://localhost:8001

## Настройка Grafana

1. Откройте http://localhost:3000
2. Перейдите в **Connections** → **Data sources** → **Add data source**
3. Выберите **Loki**
4. URL: `http://loki:3100`
5. Нажмите **Save & Test**

## Генерация тестовых логов

```bash
# Генерируем трафик
for i in {1..20}; do curl http://localhost:8000/; done
for i in {1..20}; do curl http://localhost:8000/health; done
```

## Проверка в Grafana Explore

Query: `{app="devops-python"}`

## Документация

Подробная документация: [docs/LAB07.md](docs/LAB07.md)
