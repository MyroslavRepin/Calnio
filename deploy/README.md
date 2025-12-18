# Deploy Configuration

This directory contains all deployment-related configuration files.

## Structure

```
deploy/
├── nginx/
│   └── conf.d/
│       └── calnio.conf    # Nginx reverse proxy configuration
├── certbot/
│   ├── conf/              # Let's Encrypt certificates (auto-generated)
│   └── www/               # ACME challenge files
└── ngrok.yml              # ngrok tunnel configuration
```

## Nginx Configuration

The `nginx/conf.d/calnio.conf` file configures:
- Reverse proxy from port 80 to calnio backend on port 8000
- WebSocket support
- Proper proxy headers (Host, X-Real-IP, X-Forwarded-For, X-Forwarded-Proto)
- Let's Encrypt ACME challenge location for future HTTPS setup

## SSL Certificates (TODO)

To enable HTTPS:

1. Uncomment port 443 in docker-compose.yml
2. Run certbot to obtain certificates:
   ```bash
   docker run -it --rm \
     -v ./deploy/certbot/conf:/etc/letsencrypt \
     -v ./deploy/certbot/www:/var/www/certbot \
     certbot/certbot certonly --webroot \
     -w /var/www/certbot \
     -d calnio.com -d www.calnio.com
   ```
3. Uncomment the HTTPS server block in `nginx/conf.d/calnio.conf`
4. Restart nginx: `docker compose restart nginx`

## ngrok Configuration

The `ngrok.yml` file is used for development/testing tunnels.
It creates a tunnel from `calnio.ngrok.dev` to the calnio backend.

## Deployment Commands

```bash
# Verify nginx config exists
ls -la ./deploy/nginx/conf.d

# Restart nginx with new config
docker compose up -d --force-recreate nginx

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

