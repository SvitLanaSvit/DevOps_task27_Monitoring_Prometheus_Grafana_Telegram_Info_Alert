# Monitoring Stack (Prometheus + Grafana + Alertmanager)

Цей репозиторій — виконання ДЗ з моніторингу в Docker: Prometheus, Grafana, Alertmanager + експортери.

## Етапи

- [Етап 1 — Prometheus](docs/01-stage-prometheus.md)
- [Етап 2 — Alert rules у Prometheus](docs/02-stage-alert-rules.md)
- [Етап 3 — Grafana: Data Source + Dashboards](docs/03-stage-grafana-dashboards.md)
- [Етап 4 — Telegram нотифікації](docs/04-stage-telegram-alerts.md)

## Як запустити локально

### Вимоги

- Docker Desktop (Windows) або Docker Engine (Linux/macOS)
- Docker Compose v2 (`docker compose ...`)

### Клонування

```bash
git clone <REPO_URL>
cd 27_monitoring
```

### Налаштування Telegram (обов’язково для етапу 4)

1) Створи Telegram бота через `@BotFather` і отримай токен.

2) Обов’язково напиши будь-яке повідомлення в чаті з ботом (наприклад `/start`).
Без цього Telegram API часто не повертає `chat.id`.

3) Отримай `chat_id` через Telegram Bot API:

- Відкрий у браузері:
	- `https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getUpdates`
- У відповіді знайди `message.chat.id`.

4) Створи файл [telegram-webhook/.env](telegram-webhook/.env) на основі прикладу [telegram-webhook/.env.example](telegram-webhook/.env.example):

```env
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

Примітка: [telegram-webhook/.env](telegram-webhook/.env) не комітиться (додано в `.gitignore`).

### Запуск

```bash
docker compose up -d --build
```

Веб-інтерфейси:

- Prometheus: http://localhost:9090
- Alertmanager: http://localhost:9093
- Grafana: http://localhost:3000 (login `admin`, password `admin`)
- cAdvisor: http://localhost:8080

### Тест алертів (з Telegram)

1) `TargetDown` (реальний тест):

```bash
docker compose stop node-exporter
```

Почекай ~1–2 хв (бо `for: 1m`), має прийти повідомлення в Telegram.

Повернути експортер:

```bash
docker compose start node-exporter
```

2) CPU/Disk (безпечний демо-тест без навантаження на ПК):

```bash
curl -X POST http://localhost:9093/api/v2/alerts \
	-H "Content-Type: application/json" \
	-d '[{"labels":{"alertname":"HighCPUUsage","severity":"warning","job":"demo"},"annotations":{"summary":"DEMO: CPU usage > 80%"},"startsAt":"2026-01-25T00:00:00Z"}]'

curl -X POST http://localhost:9093/api/v2/alerts \
	-H "Content-Type: application/json" \
	-d '[{"labels":{"alertname":"DiskFreeLessThan15Percent","severity":"critical","job":"demo"},"annotations":{"summary":"DEMO: Disk free < 15%"},"startsAt":"2026-01-25T00:00:00Z"}]'
```

Деталі та “RESOLVED” приклад є в [docs/04-stage-telegram-alerts.md](docs/04-stage-telegram-alerts.md).

## Reference

- Приклад docker-compose, який використано як основу: https://github.com/vegasbrianc/prometheus/blob/master/docker-compose.yml
