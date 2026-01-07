# 📊 Real-Time Monitoring Stack

This monitoring stack provides comprehensive observability for your Kafka-based trading system using **Prometheus**, **Grafana**, and **Loki**.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MONITORING STACK                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │  Grafana    │    │ Prometheus  │    │    Loki     │    │ Alertmanager│  │
│  │  :3000      │◄───│   :9091     │    │   :3100     │    │   :9093     │  │
│  │ Dashboards  │    │  Metrics    │    │    Logs     │    │   Alerts    │  │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └─────────────┘  │
│         │                  │                  │                             │
│         │     ┌────────────┴────────────┐     │                             │
│         │     │                         │     │                             │
│         ▼     ▼                         ▼     ▼                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                     │
│  │   Kafka     │    │    Node     │    │  Promtail   │                     │
│  │  Exporter   │    │  Exporter   │    │  (Logs)     │                     │
│  │   :9308     │    │   :9100     │    │             │                     │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                     │
│         │                  │                  │                             │
└─────────┼──────────────────┼──────────────────┼─────────────────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
    ┌──────────┐      ┌──────────┐       ┌───────────┐
    │  Kafka   │      │  Host    │       │  Docker   │
    │ Cluster  │      │ System   │       │ Containers│
    └──────────┘      └──────────┘       └───────────┘
```

## 🚀 Quick Start

### 1. Start the Monitoring Stack

```bash
cd ALL_DEPLOYMENTS/monitoring

# Start all monitoring services
docker compose -f docker-compose.monitoring.yml up -d
```

### 2. Access the Dashboards

| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana** | http://localhost:3000 | admin / admin |
| **Prometheus** | http://localhost:9091 | - |
| **Alertmanager** | http://localhost:9093 | - |
| **Loki** | http://localhost:3100 | - |

### 3. Pre-configured Dashboards

Grafana comes with three pre-configured dashboards:

1. **Kafka Overview** - Real-time Kafka metrics
   - Broker status
   - Topic message rates
   - Consumer group lag
   - Partition distribution

2. **Logs Explorer** - Centralized log viewing
   - Error/warning filtering
   - Service-based log streams
   - Real-time log tailing

3. **Container Metrics** - Resource monitoring
   - CPU/Memory usage per container
   - Network I/O
   - Trading system container summary

## 📦 Components

### Prometheus (Metrics Collection)
- **Port**: 9091
- **Retention**: 15 days
- **Scrape interval**: 15 seconds
- Collects metrics from:
  - Kafka Exporter (Kafka metrics)
  - Node Exporter (host metrics)
  - cAdvisor (container metrics)
  - Self-metrics

### Grafana (Visualization)
- **Port**: 3000
- **Default login**: admin/admin
- Pre-provisioned with:
  - Prometheus datasource
  - Loki datasource
  - Custom dashboards

### Loki (Log Aggregation)
- **Port**: 3100
- **Retention**: 7 days
- Aggregates logs from all Docker containers
- Supports LogQL queries

### Promtail (Log Collector)
- Automatically discovers Docker containers
- Extracts labels (service, container, component)
- Parses log levels
- Filters health check noise

### Alertmanager
- **Port**: 9093
- Routes alerts based on severity
- Supports Slack, email, PagerDuty (configure in `alertmanager/alertmanager.yml`)

### Kafka Exporter
- **Port**: 9308
- Exports Kafka metrics:
  - Broker count
  - Topic partitions
  - Consumer group lag
  - Message rates

### Node Exporter
- **Port**: 9100
- Host system metrics:
  - CPU, memory, disk
  - Network statistics
  - System load

### cAdvisor
- **Port**: 8081
- Container resource metrics:
  - CPU/memory per container
  - Network I/O
  - Filesystem usage

## 🔔 Alerting

### Pre-configured Alerts

| Alert | Severity | Condition |
|-------|----------|-----------|
| KafkaBrokerDown | Critical | No brokers available |
| KafkaConsumerLagHigh | Warning | Lag > 10,000 |
| KafkaConsumerLagCritical | Critical | Lag > 50,000 |
| KafkaTopicNoMessages | Warning | No messages for 15min |
| ContainerHighCPU | Warning | CPU > 80% for 5min |
| ContainerHighMemory | Warning | Memory > 80% |
| HostHighCPU | Warning | Host CPU > 80% |
| HostLowDiskSpace | Warning | Disk < 15% free |

### Configure Alert Notifications

Edit `alertmanager/alertmanager.yml` to add your notification channels:

#### Slack
```yaml
receivers:
  - name: 'slack-notifications'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
        channel: '#alerts'
        send_resolved: true
```

#### Email
```yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@your-domain.com'
  smtp_auth_username: 'your-email@gmail.com'
  smtp_auth_password: 'your-app-password'

receivers:
  - name: 'email-notifications'
    email_configs:
      - to: 'team@your-domain.com'
```

## 📊 Using Grafana

### Exploring Logs

1. Go to **Explore** (compass icon)
2. Select **Loki** datasource
3. Use LogQL queries:

```logql
# All error logs
{container=~".+"} |~ "(?i)error"

# Kafka logs
{container=~".*kafka.*"}

# Producer logs with topic
{container=~".*producer.*"} |= "stock_data"

# Filter by service
{service="common-finnhub-producer"} | json | level="error"
```

### Exploring Metrics

1. Go to **Explore**
2. Select **Prometheus** datasource
3. Use PromQL queries:

```promql
# Kafka message rate by topic
sum by (topic) (rate(kafka_topic_partition_current_offset[1m]))

# Consumer lag
kafka_consumergroup_lag{consumergroup="your-group"}

# Container CPU usage
sum(rate(container_cpu_usage_seconds_total{name!=""}[3m])) by (name) * 100

# Container memory
container_memory_usage_bytes{name=~".*kafka.*"}
```

### Creating Custom Dashboards

1. Click **+ Create** → **Dashboard**
2. Add panels using the query builder
3. Save and organize in folders

## 🔧 Configuration

### Adding Custom Application Metrics

If your Python services expose Prometheus metrics, add them to `prometheus/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'my-api'
    static_configs:
      - targets: ['my-api-container:8000']
    metrics_path: /metrics
```

#### Example: Adding Prometheus metrics to a Flask/FastAPI app

```python
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import FastAPI, Response

app = FastAPI()

# Define metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'Request latency')

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")

@app.middleware("http")
async def track_requests(request, call_next):
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    with REQUEST_LATENCY.time():
        response = await call_next(request)
    return response
```

### Adjusting Log Retention

Edit `loki/loki-config.yml`:

```yaml
limits_config:
  reject_old_samples_max_age: 336h  # 14 days

table_manager:
  retention_period: 336h  # 14 days
```

### Adjusting Metrics Retention

Edit `docker-compose.monitoring.yml`:

```yaml
prometheus:
  command:
    - '--storage.tsdb.retention.time=30d'  # 30 days
```

## 🛠️ Operations

### View Logs

```bash
# All monitoring services
docker compose -f docker-compose.monitoring.yml logs -f

# Specific service
docker logs -f prometheus
docker logs -f grafana
```

### Restart Services

```bash
# Restart all
docker compose -f docker-compose.monitoring.yml restart

# Restart specific service
docker compose -f docker-compose.monitoring.yml restart prometheus
```

### Stop Monitoring

```bash
# Stop services (keep data)
docker compose -f docker-compose.monitoring.yml down

# Stop and remove all data
docker compose -f docker-compose.monitoring.yml down -v
```

### Backup Data

```bash
# Prometheus data
docker run --rm -v monitoring_prometheus_data:/data -v $(pwd):/backup alpine tar cvf /backup/prometheus-backup.tar /data

# Grafana data
docker run --rm -v monitoring_grafana_data:/data -v $(pwd):/backup alpine tar cvf /backup/grafana-backup.tar /data
```

## 🔗 Integration with Trading System

### Start Everything Together

```bash
cd ALL_DEPLOYMENTS

# 1. Start monitoring first
cd monitoring && docker compose -f docker-compose.monitoring.yml up -d && cd ..

# 2. Start Kafka and producers
docker compose -f docker-compose.global.yml up -d

# 3. Start individual deployments
cd portfolio_2 && docker compose up -d && cd ..
cd chronos_deploy_main && docker compose up -d && cd ..
```

### Verify Integration

1. Check Kafka exporter is scraping:
   - Visit http://localhost:9091/targets
   - Verify `kafka-exporter` is UP

2. Check logs are flowing:
   - Visit Grafana → Logs Explorer dashboard
   - Verify container logs appear

3. Check container metrics:
   - Visit Grafana → Container Metrics dashboard
   - Verify all trading system containers appear

## 📈 Best Practices

### 1. Set Up Alerts Early
Configure alert notifications before production deployment.

### 2. Monitor Consumer Lag
Consumer lag is the key metric for Kafka health. Set appropriate thresholds.

### 3. Use Labels
Use Grafana labels to filter logs by:
- `service` - Docker Compose service name
- `container` - Container name
- `component` - kafka/producer/consumer/api
- `level` - Log level (error/warn/info)

### 4. Dashboard Variables
Create dashboard variables for:
- Time range selection
- Service/container filtering
- Topic selection

### 5. Regular Reviews
- Weekly: Review consumer lag trends
- Monthly: Review disk usage and retention settings
- Quarterly: Review alert thresholds

## 🐛 Troubleshooting

### Kafka Exporter Not Connecting

```bash
# Check if Kafka is accessible
docker exec kafka-exporter kafka-exporter --kafka.server=kafka:9090 --log.level=debug
```

### Promtail Not Collecting Logs

```bash
# Check Promtail targets
curl http://localhost:9080/targets

# Verify Docker socket access
docker logs promtail
```

### Grafana Dashboard Not Loading

```bash
# Check datasource connectivity
curl http://localhost:9091/api/v1/query?query=up

# Restart Grafana
docker compose -f docker-compose.monitoring.yml restart grafana
```

### High Memory Usage

Reduce retention periods in Prometheus and Loki configuration.

## 📚 Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Loki Documentation](https://grafana.com/docs/loki/)
- [LogQL Query Language](https://grafana.com/docs/loki/latest/logql/)
- [PromQL Query Language](https://prometheus.io/docs/prometheus/latest/querying/basics/)
