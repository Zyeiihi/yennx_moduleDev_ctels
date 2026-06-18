# GAP Analysis - Mini EASM Project

## Bài 1: Migrate sang Database (30 điểm)
| Sub-requirement | Status | Notes |
|---|---|---|
| 1.1 Database service in docker-compose | **FAIL** | Only backend service, no DB service |
| 1.2 Migration files (migrations/ dir) | **FAIL** | Not present |
| 1.3 DB storage layer (replaces in-memory) | **FAIL** | Still using MemoryStorage |
| 1.4 DB config from env vars | **FAIL** | No DB env var support |
| Asset model `tags` bug | **FAIL** | `self.tags = tags` but `tags` not in signature → NameError on startup |

## Bài 2: Mở rộng Scan API (25 điểm)
| Sub-requirement | Status | Notes |
|---|---|---|
| Existing scans (dns, whois, subdomain) | **PASS** | Implemented (dummy) |
| ip scan (1.1) | **PASS** | IPScanner implemented |
| port scan (1.2) safety check | **PASS** | is_local_host guard present |
| ssl scan (1.3) | **PASS** | SSLScanner implemented |
| tech scan (1.4) | **PASS** | TechScanner implemented |
| GET /assets/{id}/results endpoint | **FAIL** | Missing endpoint |
| GET /assets/{id}/dns, /whois, /subdomains | **FAIL** | Missing endpoints |
| DELETE /assets/{id} endpoint | **FAIL** | Missing (needed by frontend) |
| Real DNS scan (not dummy) | **PARTIAL** | Uses DummyPassiveScanners |

## Bài 3: Viết Unit Tests (20 điểm)
| Sub-requirement | Status | Notes |
|---|---|---|
| 3.1 Model validation tests | **PARTIAL** | test_storage_asset_operations but missing model validation tests |
| 3.4 Scanner tests | **PARTIAL** | Only PortScanner security test, missing IPScanner/SSLScanner/TechScanner |
| 3.2 Handler tests (bonus) | **FAIL** | Missing |
| 3.3 Service tests (bonus) | **FAIL** | Missing |
| CI test command wrong path | **FAIL** | `python -m unittest test_scanners.py` wrong dir |

## Bài 4: Tích hợp Frontend (20 điểm)
| Sub-requirement | Status | Notes |
|---|---|---|
| CORS middleware | **PASS** | after_request handler present |
| Display asset list | **PASS** | loadAssets() present |
| Add new asset | **PASS** | addAsset() present |
| Delete asset | **FAIL** | deleteAsset() missing in frontend + no backend endpoint |
| Start scan | **PASS** | triggerScan() present |
| View scan results | **PASS** | updateJobTable() present |
| Dashboard stats | **PARTIAL** | Widget counters present but not all stats |

## Bài 5: CI/CD GitHub Actions (BONUS)
| Sub-requirement | Status | Notes |
|---|---|---|
| Basic CI (lint + test) | **PASS** | ci.yml exists |
| Security scanning (gosec/trivy/gitleaks) | **FAIL** | No security scan jobs |
| Correct test path | **FAIL** | unittest command uses wrong path |

## Bài 6: Deploy với Docker Compose (BONUS)
| Sub-requirement | Status | Notes |
|---|---|---|
| Backend service | **PASS** | Present |
| Database service | **FAIL** | Missing |
| Persistent volumes | **FAIL** | Missing |
| Health checks | **PARTIAL** | Backend only |
| Nginx reverse proxy | **FAIL** | Missing |

## Bài 7: Tính năng EASM mới (BONUS)
| Sub-requirement | Status | Notes |
|---|---|---|
| CVEScanner implemented | **PARTIAL** | Class exists but not wired to scan workflow |
| CVE scan type endpoint | **FAIL** | Not in SCAN_TYPES, not in ScanService |

## Bài 8-10: Cloud Deploy, TLS, Auto Deploy (BONUS)
| Status | Notes |
|---|---|
| **FAIL** | Requires real cloud VM — documentation/config files can be prepared |

## Critical Bugs Found
1. **asset.py** — `Asset.__init__` references `tags` variable not in signature → server crashes on startup
2. **ci.yml** — test command `python -m unittest test_scanners.py` wrong; should be `python -m pytest test/`
3. **No DB integration** — entire Bài 1 missing
4. **Missing DELETE asset endpoint** — frontend references delete but backend doesn't have it
5. **Missing GET /assets/{id}/results** endpoint
