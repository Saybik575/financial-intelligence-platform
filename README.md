# 🏦 Financial Intelligence Platform

> A production-style fintech analytics platform built using Django, PostgreSQL, Redis, Celery, Docker, and Machine Learning — providing company financial analytics, screening tools, partner APIs, automated ETL pipelines, ML-based health scoring, webhook infrastructure, and operational dashboards.

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)
![Django](https://img.shields.io/badge/Django-4.x-green?style=flat-square&logo=django)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-316192?style=flat-square&logo=postgresql)
![Redis](https://img.shields.io/badge/Redis-Celery-red?style=flat-square&logo=redis)
![License](https://img.shields.io/badge/License-Educational-lightgrey?style=flat-square)

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Core Capabilities](#-core-capabilities)
- [Local Setup](#-local-setup)
- [Docker Setup](#-docker-setup)
- [Deployment](#-deployment)
- [API Reference](#-api-reference)
- [Future Improvements](#-future-improvements)
- [Author](#-author)

---

## ✨ Features

### 📊 Financial Analytics
- Historical balance sheet analysis
- Profit & loss analytics
- Cash flow analytics
- Ratio analysis
- Sector-wise comparison
- Multi-company comparison engine

### 🤖 ML & Scoring Engine
- Financial health scoring
- Automated company classification
- Anomaly detection framework
- Scheduled ML rescoring pipeline

### 🔌 Partner API Platform
- HMAC-SHA256 authenticated APIs
- Bulk financial APIs
- Company full-data APIs
- Screening APIs
- API key management
- Webhook subscriptions

### 🏗️ Platform Infrastructure
- Dockerized architecture
- PostgreSQL warehouse
- Redis integration
- Celery background workers
- Celery Beat scheduler
- Async API logging
- Redis-backed rate limiting

### 📈 Admin & Monitoring
- Operational dashboards
- API analytics
- Webhook monitoring
- Data quality tracking
- Celery monitoring
- KPI dashboards

---

## 🛠️ Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Django · Django REST Framework · Gunicorn |
| **Database** | PostgreSQL · SQLite (free deployment mode) |
| **Async** | Redis · Celery · Celery Beat |
| **DevOps** | Docker · Docker Compose · Nginx · Render |
| **Data & ML** | Pandas · NumPy · Scikit-learn · Power BI |

---

## 🏛️ Architecture

```
Internet
    ↓
  Nginx
    ↓
Gunicorn
    ↓
Django Application
    ↓
PostgreSQL

Redis
    ↓
Celery Workers
    ↓
Scheduled ETL & ML Jobs
```

---

## 📁 Project Structure

```
financial-intelligence-platform/
│
├── webapp/
│   ├── api/            # REST API views & serializers
│   ├── companies/      # Company models & views
│   ├── dashboard/      # Dashboard app
│   ├── financials/     # Financial data models
│   ├── ml/             # ML scoring pipeline
│   ├── partners/       # Partner API layer
│   ├── config/         # Settings & configuration
│   └── templates/      # HTML templates
│
├── sql/                # Raw SQL scripts
├── nginx/              # Nginx configuration
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## ⚙️ Core Capabilities

### 🔄 ETL Pipeline
Automated ETL pipeline for:
- Extracting financial datasets
- Transforming and cleaning data
- Loading into warehouse tables

### ⏰ Scheduled Jobs
- Nightly ETL refresh
- Scheduled ML rescoring
- Automated background processing

### 🔐 API Security
- HMAC request signing
- Nonce replay protection
- Timestamp validation
- Rate limiting

### 🚀 Deployment Modes

| Mode | Stack | Use Case |
|------|-------|----------|
| **Local Full Infrastructure** | PostgreSQL · Redis · Celery · Docker | Development / production parity |
| **Free Cloud Deployment** | SQLite · Gunicorn · WhiteNoise | Render / PaaS free tier |

---

## 💻 Local Setup

### 1. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/financial-intelligence-platform.git
cd financial-intelligence-platform
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

Activate:

```bash
# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
DEBUG=True
SECRET_KEY=your_secret_key

DB_NAME=fintech
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

### 7. Start Development Server

```bash
python manage.py runserver
```

---

## 🐳 Docker Setup

Start the full stack — Django · PostgreSQL · Redis · Celery · Celery Beat · Nginx:

```bash
docker compose up --build
```

---

## ☁️ Deployment

### Render (Free Tier)

The platform supports free deployment on [Render](https://render.com) using:

| Component | Purpose |
|-----------|---------|
| **Gunicorn** | Production WSGI server |
| **SQLite** | Lightweight DB for free tier |
| **WhiteNoise** | Static file serving |

> Production-style local infrastructure remains fully implemented.

---

## 🔌 API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/partner/v1/scores/` | `GET` | Retrieve partner ML scores |
| `/api/partner/v1/bulk-financials/?symbols=TCS,INFY` | `GET` | Bulk financial data by symbols |
| `/api/partner/v1/companies/TCS/full/` | `GET` | Full company data profile |

---

## 🔭 Future Improvements

- [ ] Real-time streaming analytics
- [ ] Kubernetes deployment
- [ ] CI/CD pipelines
- [ ] Prometheus & Grafana monitoring
- [ ] Kafka event streaming
- [ ] Advanced ML models
- [ ] React / Next.js frontend separation

---

## 👤 Author

**Satvik Kumar**

Built for educational, portfolio, and internship purposes.

---

## 📄 License

This project is for educational, portfolio, and internship use only.
