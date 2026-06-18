# Changelog — Mini ASM

## [2.0.0] — 2026-06-18

### Added
- **Database storage** (Bài 1): SQLite (default) and PostgreSQL support via `internal/storage/database.py`
- **Migration files** (Bài 1): `migrations/001_create_assets.up.sql` / `down.sql`
- **Environment config** (Bài 1): All DB settings read from env vars (`DB_DRIVER`, `DB_HOST`, etc.)
- **DELETE /assets/{id}** endpoint (Bài 2 / Bài 4)
- **GET /assets/{id}** endpoint (Bài 2)
- **GET /assets/{id}/results** — aggregate all scan results (Bài 2)
- **GET /assets/{id}/dns|whois|subdomains** — latest scan result shortcuts (Bài 2)
- **Real DNS scanner** using dnspython + socket fallback (Bài 2)
- **Real WHOIS scanner** via port 43 socket query (Bài 2)
- **Subdomain scanner** using crt.sh certificate transparency (Bài 2)
- **CVE scanner** with service→CVE correlation database (Bài 7)
- `cve` scan type added to SCAN_TYPES (Bài 2 / Bài 7)
- **Comprehensive unit tests** — 76 tests across 5 modules (Bài 3)
  - `test_model.py` — Asset & ScanJob model validation
  - `test_storage.py` — MemoryStorage CRUD
  - `test_scanners.py` — All scanner types + security guards
  - `test_service.py` — Service layer with mock storage (bonus)
  - `test_handler.py` — Flask route tests with mock storage (bonus)
- **Frontend delete button** for asset removal (Bài 4)
- **CVE display** in scan results panel (Bài 4)
- All scan types in frontend dropdown (Bài 4)
- Auto-detect API URL in frontend JS (Bài 4)
- **docker-compose.yml** updated with `db` (PostgreSQL) + `nginx` services (Bài 6)
- **nginx.conf** reverse proxy configuration (Bài 6)
- **CI/CD pipeline** (.github/workflows/ci.yml) with lint, test, Gitleaks, Trivy (Bài 5)
- **DEPLOYMENT.md** with Cloud VM, TLS, and auto-deploy instructions (Bài 8-10)
- Multi-stage **Dockerfile** for smaller production images (Bài 6)
- `.env.example` environment template

### Fixed
- **Critical bug**: `Asset.__init__` referenced `tags` variable that was not in the method signature → `NameError` on every asset creation
- `ScanService` now accepts injectable storage (testability)
- `to_dict()` on `ScanJob` now returns `results` count (not raw list) per API spec
- CI test command fixed: `python -m pytest test/` (was using wrong path)

### Preserved
- All existing scanner implementations (IPScanner, PortScanner, SSLScanner, TechScanner)
- CORS middleware behavior
- Flask architecture and Clean Architecture layout
- Docker healthcheck on backend service
- CVEScanner class (was present but not wired — now fully wired)

## [1.0.0] — Initial implementation (by previous AI)
- Flask backend with in-memory storage
- IPScanner, PortScanner, SSLScanner, TechScanner
- Basic frontend dashboard
- Docker single-service compose
- GitHub Actions basic CI
