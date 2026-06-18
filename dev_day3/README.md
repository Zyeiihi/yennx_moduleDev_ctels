# 🔍 Mini ASM — External Attack Surface Management Tool

A Python/Flask EASM tool for discovering and monitoring assets (domains and IPs).

## Features

- **Asset Management** — Add, list, and delete domains/IP assets
- **Scan Types** — DNS, WHOIS, Subdomain enumeration, SSL/TLS audit, Tech fingerprinting, IP GeoIP, Port scan (local only), CVE correlation
- **Persistent Storage** — SQLite (dev) or PostgreSQL (production)
- **Frontend Dashboard** — Built-in dark-themed web UI
- **REST API** — Full JSON API
- **Docker support** — Single-command full-stack deployment

---

## Quick Start

### Option A — SQLite (no database setup needed)
```bash
pip install -r requirements.txt

# Run server
python app.py

# Open browser at http://localhost:8080
```

### Option B — Docker Compose (PostgreSQL + Nginx)
```bash
cp .env.example .env   # Edit passwords if desired
docker compose up -d
# Frontend: http://localhost
# API:      http://localhost/health
```

---

## Environment Variables

| Variable       | Default       | Description                     |
|----------------|---------------|---------------------------------|
| `DB_DRIVER`    | `sqlite`      | `sqlite` or `postgres`          |
| `SQLITE_PATH`  | `./mini_asm.db` | SQLite file path              |
| `DB_HOST`      | `localhost`   | PostgreSQL host                 |
| `DB_PORT`      | `5432`        | PostgreSQL port                 |
| `DB_USER`      | `postgres`    | PostgreSQL user                 |
| `DB_PASSWORD`  | `postgres`    | PostgreSQL password             |
| `DB_NAME`      | `mini_asm`    | Database name                   |
| `PORT`         | `8080`        | Flask server port               |
| `FLASK_DEBUG`  | `false`       | Enable debug mode               |

---

## API Endpoints

| Method | Endpoint                      | Description                       |
|--------|-------------------------------|-----------------------------------|
| GET    | `/health`                     | Health check                      |
| POST   | `/assets`                     | Create asset                      |
| GET    | `/assets`                     | List all assets                   |
| GET    | `/assets/{id}`                | Get asset by ID                   |
| DELETE | `/assets/{id}`                | Delete asset                      |
| POST   | `/assets/{id}/scan`           | Start scan job                    |
| GET    | `/assets/{id}/scans`          | List all scans for asset          |
| GET    | `/assets/{id}/results`        | Get all results for asset         |
| GET    | `/assets/{id}/dns`            | Latest DNS results                |
| GET    | `/assets/{id}/whois`          | Latest WHOIS results              |
| GET    | `/assets/{id}/subdomains`     | Latest subdomain results          |
| GET    | `/scan-jobs/{id}`             | Get scan job status               |
| GET    | `/scan-jobs/{id}/results`     | Get scan job results              |

### Scan Types
| `scan_type`  | Description                          | Safe for public IPs |
|--------------|--------------------------------------|---------------------|
| `dns`        | DNS record lookup (A, MX, NS, TXT)   | ✅ Yes              |
| `whois`      | WHOIS registration data              | ✅ Yes              |
| `subdomain`  | Subdomain enumeration via crt.sh     | ✅ Yes              |
| `ssl`        | TLS certificate analysis             | ✅ Yes              |
| `tech`       | HTTP tech fingerprinting             | ✅ Yes              |
| `ip`         | GeoIP & ASN lookup                   | ✅ Yes              |
| `port`       | TCP port scan (**local IPs only**)   | ⚠️ Local only       |
| `cve`        | CVE vulnerability correlation        | ✅ Yes              |
| `all`        | All passive scans combined           | ✅ Yes              |

---

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
├── requirements.txt
├── Dockerfile
├── docker-compose.yml              # Full stack (postgres + nginx)
├── nginx.conf                      # Reverse proxy config
├── .env.example                    # Environment variables template
├── migrations/
│   ├── 001_create_assets.up.sql    # Schema creation
│   └── 001_create_assets.down.sql  # Schema rollback
├── internal/
│   ├── model/asset.py              # Asset & ScanJob models
│   ├── storage/
│   │   ├── database.py             # SQLite/PostgreSQL storage
│   │   └── memory.py               # In-memory storage (tests)
│   ├── service/
│   │   ├── scanners.py             # Scanner implementations
│   │   └── scan_service.py         # Background scan orchestration
│   └── handler/router.py           # Flask routes
├── web/
│   ├── index.html                  # Frontend dashboard
│   └── app.js                      # Frontend JavaScript
├── test/
│   ├── test_model.py               # Model validation tests
│   ├── test_storage.py             # Storage layer tests
│   ├── test_scanners.py            # Scanner unit tests
│   ├── test_service.py             # Service layer tests (mock)
│   └── test_handler.py             # Handler tests (Flask test client)
└── .github/workflows/ci.yml        # CI/CD pipeline
```

---

## Security Notes

- Port scanning is **restricted to private/localhost IP ranges** (RFC 1918)
- CORS is configured to allow all origins (suitable for development; restrict in production)
- No authentication required (add JWT/API key middleware for production)

See [DEPLOYMENT.md](DEPLOYMENT.md) for cloud deployment instructions.
