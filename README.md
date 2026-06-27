# HedgeMind

An intelligent, real-time trading and portfolio management system powered by agentic AI and streaming data pipelines.

🌐 **Live Demo:** [http://13.50.225.240:80](http://13.50.225.240:80)

---

## Table of Contents

- [Overview](#overview)
- [Repository Structure](#repository-structure)
- [Folder Descriptions](#folder-descriptions)
- [Documentation](#documentation)
- [References](#references)

---

## Overview

HedgeMind is one-of-a-kind comprehensive trading intelligence platform that integrates real-time market data processing, machine learning-based forecasting, and agentic decision-making systems. The repository is organized into distinct modules, each serving a specific purpose in the overall architecture.

Each folder contains its own detailed README with implementation specifics, setup instructions, and usage guidelines.

---

## Repository Structure

```
HedgeMind/
│
├── LIVE/                              # Production environment - Live market data
│   ├── Agentic_System/
│   │   ├── chat/
│   │   ├── clarification/
│   │   ├── config.sh
│   │   ├── debezium/
│   │   ├── docker-compose.yml
│   │   ├── macro/
│   │   ├── market_analyzer/
│   │   ├── orch/
│   │   ├── portfolio/
│   │   ├── sql/
│   │   ├── strategy/
│   │   └── utils/
│   ├── ga-strat-app/
│   │   └── ga-strat-app/
│   ├── kubernetes_sarimax/
│   │   ├── README.md
│   │   └── technical_analysis/
│   └── trading-system-main/
│       ├── ALL_DEPLOYMENTS/
│       ├── README.md
│       ├── deploy-kafka.sh
│       └── deploy.sh
│
├── STATIC/                            # Development environment - Simulated streams
│   ├── aws_macro_deployment/
│   │   ├── Dockerfile.api
│   │   ├── Dockerfile.consumer
│   │   ├── Dockerfile.producer
│   │   ├── README.md
│   │   ├── api_server.py
│   │   ├── data/
│   │   ├── deployment.sh
│   │   ├── docker-compose.yaml
│   │   ├── docker-compose.yml
│   │   ├── metrics.py
│   │   ├── models/
│   │   ├── pathway_consumer_training.py
│   │   ├── pathway_fred_producer.py
│   │   └── requirements.txt
│   ├── chronos_static/
│   │   ├── README.md
│   │   ├── chronosConsumer/
│   │   ├── docker-compose.yml
│   │   ├── ohlcProducer/
│   │   ├── output/
│   │   ├── redditProducer/
│   │   ├── sarimaxConsumer/
│   │   ├── selection/
│   │   ├── spike_detector/
│   │   └── tweetProducer/
│   └── portfolio_static/
│       ├── README.md
│       ├── backend/
│       ├── data/
│       ├── docker-compose.yml
│       ├── evaluation/
│       ├── output/
│       └── processing/
│
│
├── MCP/                               # Model Context Protocol implementation
│   ├── mcp_deploy/
│   │   ├── __MACOSX/
│   │   └── mcp_deploy/
│   └── pathway_mcp/
│       ├── __MACOSX/
│       └── pathway_mcp/
│
├── WEBAPP/                            # Web application (Frontend & Backend)
│   ├── Makefile
│   ├── README.md
│   ├── backend/
│   │   ├── Dockerfile
│   │   ├── api/
│   │   ├── config/
│   │   ├── db.sqlite3
│   │   ├── kafka_consumer/
│   │   ├── logs/
│   │   ├── manage.py
│   │   ├── requirements.txt
│   │   ├── schema.yml
│   │   ├── setup_chat.sh
│   │   ├── templates/
│   │   ├── test_email_notifications.py
│   │   ├── test_kafka_connection.py
│   │   ├── test_notifications.py
│   │   ├── test_pnl_websocket.py
│   │   ├── test_portfolio_api.py
│   │   └── users/
│   ├── deploy-commands.txt
│   ├── deploy-kafka-config.sh
│   ├── docker-compose.override.yml.example
│   ├── docker-compose.yml
│   ├── docker-manager.sh
│   ├── frontend/
│   │   ├── Dockerfile
│   │   ├── README.md
│   │   ├── app/
│   │   ├── components/
│   │   ├── contexts/
│   │   ├── eslint.config.mjs
│   │   ├── hooks/
│   │   ├── lib/
│   │   ├── next.config.ts
│   │   ├── package.json
│   │   ├── pnpm-lock.yaml
│   │   ├── postcss.config.mjs
│   │   ├── public/
│   │   ├── theme-preview.html
│   │   ├── tsconfig.json
│   │   ├── types/
│   │   └── utils/
│   ├── health-check.sh
│   ├── models/
│   │   ├── macro/
│   │   └── technical_analysis/
│   ├── nginx.conf
│   ├── setup-kafka-topics.sh
│   ├── test.html
│   ├── test_news_simulator.py
│   ├── websocket-realtime-test.html
│   └── websocket-test.html
│
├── Videos/                        │   └── demo.mp4 
│   └── summary_video.mp4
│
├── Appendix.pdf                          # Supplementary materials & references
│
└── Report.pdf
```

---

## Folder Descriptions

### LIVE

Contains the production-ready codebase that operates on **live market data**. This includes the final agent implementation, orchestration logic, market analysis modules, portfolio management, and trading strategy execution. All services are containerized and deployed via Docker and Kubernetes.

### STATIC

A **development and testing environment** that mirrors the LIVE folder structure. Instead of connecting to live market feeds, it utilizes **Pathway** to simulate data streams. This allows for safe testing, debugging, and experimentation without impacting real trading operations.

### AGENTIC SYSTEM

Houses the **Pathway-based Agentic System** derived from the X Pack framework. This module is responsible for autonomous decision-making, reasoning, and task execution within the HedgeMind pipeline.

### MCP

Contains the custom **Model Context Protocol (MCP)** implementation. This module handles context management and communication between various AI models and system components, enabling seamless integration of multiple intelligent agents.

### WEBAPP

The user-facing application layer comprising:
- **Backend:** Django-based REST API with Kafka consumers, WebSocket support, and user management
- **Frontend:** Next.js application with real-time data visualization and interactive dashboards

### Videos

Contains **demo videos and walkthroughs** showcasing the functionality, features, and usage of the HedgeMind platform.

### Report

The formal **project report** documenting the system design, methodology, implementation details, and evaluation results.

### Appendix

**Supplementary materials** including additional documentation, configurations, and supporting resources. All references cited in the Report are documented here.

---

## Documentation

Each major folder contains its own `README.md` with:
- Setup and installation instructions
- Configuration guidelines
- API documentation (where applicable)
- Deployment procedures

---
