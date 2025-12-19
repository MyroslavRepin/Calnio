# Deploy Configuration

This directory contains all deployment-related configuration files.

## Structure

```
deploy/
├── nginx/
│   └── conf.d/
│       └── calnio.conf    # Nginx reverse proxy + HTTPS (Let's Encrypt)
├── certbot/
│   ├── conf/              # Let's Encrypt certificates (auto-generated)
│   └── www/               # ACME challenge files (webroot)
└── ngrok.yml              # ngrok tunnel configuration (dev only)
```

## Nginx Configuration

The `nginx/conf.d/calnio.conf` file configures:
- HTTP (80) for ACME challenge and redirect to HTTPS
- HTTPS (443) termination using Let’s Encrypt certificates
- Reverse proxy to `calnio:8000`
- WebSocket support
- Cloudflare real IP support (`CF-Connecting-IP`)

## SSL Certificates (Let’s Encrypt)

This repo uses **certbot webroot (HTTP-01)**.

### 1) Start services (nginx must be reachable on port 80)

```bash
docker compose up -d --build nginx calnio redis
```

### 2) Issue the initial certificate (run once)

```bash
docker compose run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  -d calnio.com -d www.calnio.com \
  --agree-tos --email you@example.com --no-eff-email
```

### 3) Reload nginx

```bash
docker compose restart nginx
```

### Auto-renew

The `certbot` service runs `certbot renew` every 12 hours.

## Cloudflare settings

Recommended:
- **SSL/TLS mode:** Full (strict)
- Make sure ports **80** and **443** are open on the origin server.

## ngrok Configuration (dev only)

The `ngrok.yml` file is used for development/testing tunnels.
It creates a tunnel from `calnio.ngrok.dev` to the calnio backend.

Run it with Compose profile:

```bash
docker compose --profile dev up -d ngrok
```

## Deployment Commands

```bash
# Verify nginx config exists
ls -la ./deploy/nginx/conf.d

# Test nginx configuration
docker compose exec nginx nginx -t

# Reload nginx (no restart needed)
docker compose exec nginx nginx -s reload

# View nginx logs
docker compose logs -f nginx

# Test locally
curl -v http://127.0.0.1/
curl -H "Host: calnio.com" -v http://127.0.0.1/
```

## Troubleshooting

**Problem:** `/etc/nginx/conf.d` is empty in container
**Cause:** Volume mount replaces the entire directory. If `./deploy/nginx/conf.d` doesn't exist on the host, Docker creates an empty directory.
**Solution:** Ensure `./deploy/nginx/conf.d/calnio.conf` exists before starting the container.

**Problem:** `502 Bad Gateway`
**Cause:** Backend service (calnio) is not running or not reachable.
**Solution:** Check `docker compose logs calnio` and ensure the service is healthy.

**Problem:** Certificate issuance fails behind Cloudflare
**Cause:** Cloudflare proxy/WAF can interfere with HTTP-01 challenge in some setups.
**Solution:** Temporarily switch to DNS-only (grey cloud) during issuance, or use DNS-01.
