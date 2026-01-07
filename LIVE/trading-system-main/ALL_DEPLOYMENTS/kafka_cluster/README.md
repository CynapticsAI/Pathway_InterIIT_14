# Shared Kafka Cluster

This is the centralized Kafka cluster for all deployments in the system.

## Architecture

- **1 Zookeeper instance** - Manages Kafka cluster state
- **1 Kafka broker** - Handles all message streaming
- **Kafka UI** (optional) - Web interface for monitoring at `http://server_host:8090`

## Network

All services connect via the `global_kafka_network` Docker network.

| Service | Internal Address | External Address |
|---------|------------------|------------------|
| Kafka | `kafka:9090` | `server_host:29092` |
| Zookeeper | `zookeeper:2181` | `server_host:2181` |
| Kafka UI | - | `server_host:8090` |

## Usage

### Start the Kafka Cluster

```bash
cd kafka_cluster
docker compose -f docker compose.kafka.yml up -d
```

### Verify Health

```bash
# To Check if Kafka is healthy
docker exec global-kafka kafka-broker-api-versions --bootstrap-server server_host:9090

# List topics
docker exec global-kafka kafka-topics --bootstrap-server server_host:9090 --list
```

### Create Topics (Optional - Auto-create is enabled)

```bash
# To Create a topic manually
docker exec global-kafka kafka-topics --bootstrap-server server_host:9090 \
  --create --topic my-topic --partitions 3 --replication-factor 1
```

## Topics Used by Deployments

| Topic | Producer | Consumers |
|-------|----------|-----------|
| `stock_data` | common_finnhub_producer | chronos, sarimax, portfolio, spike_detector |
| `news_data` | common_news_producer | chronos, sarimax |
| `sentiment_scores` | common_sentiment_producer | portfolio |
| `fred_economic_data` | common_macro_producer | aws_macro_deployment |
| `volume_volatility_data` | common_spike_detector | sarimax |
| `stock_scores` | portfolio/scorer | portfolio |
| `sarimax_forecast` | sarimax | select_model |
| `chronos_infer_preds` | chronos | select_model |

## Connecting Services

All services must:

1. Use the external network:
```yaml
networks:
  global_kafka_network:
    external: true
```

2. Set the bootstrap servers:
```yaml
environment:
  KAFKA_BOOTSTRAP_SERVERS: kafka:9090
```

## Stopping the Cluster

```bash
docker compose -f docker compose.kafka.yml down

# To remove volumes (data):
docker compose -f docker compose.kafka.yml down -v
```
