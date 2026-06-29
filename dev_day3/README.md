# Quick Start

## Docker Compose (PostgreSQL + Nginx)
```bash
cp .env.example .env   # Edit passwords if desired
docker compose up -d
# Frontend: http://localhost
# API:      http://localhost/health
```


## Running Tests

```bash
# All tests
pytest test/ -v

# With coverage report
pytest test/ -v --cov=internal --cov-report=html

# Specific test module
pytest test/test_model.py -v
pytest test/test_scanners.py -v
```

---

## Project Structure

```
. 
├── app.py                          # Entry point
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Multi-stage Docker build
├── docker-compose.yml              # Full stack (postgres + backend + nginx)
├── nginx.conf                      # Reverse proxy & security headers config
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore rules
├── migrations/
│   ├── 001_create_assets.up.sql    # Schema creation (PostgreSQL/SQLite)
│   └── 001_create_assets.down.sql  # Schema rollback
├── internal/
│   ├── model/
│   │   └── asset.py                # Asset & ScanJob models
│   ├── storage/
│   │   ├── database.py             # SQLite/PostgreSQL storage driver
│   │   └── memory.py               # In-memory storage (baseline/tests)
│   ├── service/
│   │   ├── analyzer.py             # Compare historical results (Delta/Diff)
│   │   ├── scanners.py             # Scanner implementations & Security guards
│   │   └── scan_service.py         # Background scan thread orchestration
│   └── handler/
│       └── router.py               # Flask API endpoints routing
├── web/
│   ├── index.html                  # Frontend SPA dashboard
│   └── app.js                      # Frontend Vanilla JavaScript logic
├── test/
│   ├── test_model.py               # Model validation unit tests
│   ├── test_storage.py             # Storage layer unit tests
│   ├── test_scanners.py            # Scanner & security checks unit tests
│   ├── test_service.py             # Service background thread tests
│   └── test_handler.py             # API route tests via Flask test_client
└── .github/
    └── workflows/
        └── ci.yml                  # GitHub Actions CI/CD pipeline (Lint, Test, Trivy)
```
