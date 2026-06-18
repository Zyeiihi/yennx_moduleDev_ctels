# Homework Submission - Day 3

**Họ tên:** [Tên của bạn]

## Các bài đã hoàn thành

- [x] Bài 1: Migrate sang Database (SQLite default + PostgreSQL optional)
- [x] Bài 2: Mở rộng Scan API (DNS, WHOIS, Subdomain, SSL, IP, Port, Tech, CVE)
- [x] Bài 3: Viết Unit Tests (76 tests, 5 modules, mock service & handler)
- [x] Bài 4: Tích hợp Frontend (delete, CVE display, all scan types)
- [x] Bài 5: CI/CD với GitHub Actions (lint + test + Gitleaks + Trivy + Docker build)
- [x] Bài 6: Deploy với Docker Compose (postgres + backend + nginx)
- [x] Bài 7: Tính năng EASM mới (CVEScanner wired into scan workflow)
- [ ] Bài 8: Deploy lên Cloud VM (requires real VM — config prepared in DEPLOYMENT.md)
- [ ] Bài 9: Domain & TLS/HTTPS (requires domain — config prepared in DEPLOYMENT.md)
- [ ] Bài 10: Auto Deploy on Merge (requires live server — workflow template in DEPLOYMENT.md)

## Link Repository

[Link GitHub repository]

## Link Demo (nếu có)

[Link deployed application]

## Test Results

```
76 passed, 0 failed
Coverage: internal/ modules
```

## Quick Start

```bash
# Dev mode (SQLite, no Docker)
pip install -r requirements.txt
python app.py

# Production mode (Docker + PostgreSQL + Nginx)
docker compose up -d
```
