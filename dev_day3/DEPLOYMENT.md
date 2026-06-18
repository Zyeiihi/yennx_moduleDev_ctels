# Deployment Guide — Mini ASM

## Bài 8: Deploy lên Cloud VM

### Option A — DigitalOcean / Linode / Oracle Cloud Free Tier

#### 1. Provision VM
```bash
# Minimum specs: 1 vCPU, 1GB RAM, Ubuntu 22.04
# Open ports: 22 (SSH), 80 (HTTP), 443 (HTTPS)
```

#### 2. Install Docker
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Install Docker Compose v2
sudo apt-get install -y docker-compose-plugin
```

#### 3. Clone & Configure
```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
cp .env.example .env
# Edit .env:
#   DB_PASSWORD=<strong-password>
nano .env
```

#### 4. Start Stack
```bash
docker compose up -d
docker compose ps          # Verify all services healthy
curl http://localhost/health
```

---

## Bài 9: Domain & TLS/HTTPS (with Nginx + Certbot)

### Prerequisites
- A domain name pointing to your server IP (A record set)
- Port 80 and 443 open

### Nginx + Let's Encrypt setup
```bash
sudo apt-get install -y certbot python3-certbot-nginx

# Modify nginx.conf to add server_name
sudo nano nginx.conf  # set: server_name yourdomain.com www.yourdomain.com;

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal cron
sudo certbot renew --dry-run
```

### Or use Traefik (automatic HTTPS)
```yaml
# docker-compose.traefik.yml — add to your compose file:
  traefik:
    image: traefik:v3.0
    command:
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.email=you@example.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "./acme.json:/acme.json"
```

---

## Bài 10: Auto Deploy on Merge (GitHub Actions)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy on Merge to main

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to server via SSH
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SERVER_SSH_KEY }}
          script: |
            cd /opt/mini-asm
            git pull origin main
            docker compose pull
            docker compose up -d --build
            docker compose ps
```

### GitHub Secrets required:
- `SERVER_HOST` — your server IP or hostname
- `SERVER_USER` — SSH username (e.g. `ubuntu`)
- `SERVER_SSH_KEY` — private SSH key (generate with `ssh-keygen -t ed25519`)

### Initial server setup:
```bash
# On server:
sudo mkdir -p /opt/mini-asm
sudo chown $USER /opt/mini-asm
cd /opt/mini-asm
git clone https://github.com/<you>/<repo>.git .
cp .env.example .env && nano .env
docker compose up -d
```
