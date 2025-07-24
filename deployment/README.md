# Nginx Deployment for api.cheftoan.com

This folder contains everything needed to deploy your FastAPI application with nginx.

## Files

- **`nginx-cheftoan.conf`** - Complete nginx configuration with all production features
- **`setup-nginx.sh`** - Automated setup script

## Quick Setup

1. **Upload files to your Ubuntu server:**
   ```bash
   scp nginx-cheftoan.conf setup-nginx.sh ubuntu@your-server:~/deployment/
   ```

2. **Run the setup script:**
   ```bash
   cd ~/deployment
   sudo bash setup-nginx.sh
   ```

3. **Start your FastAPI application:**
   ```bash
   cd ~/Clash-Of-Clans-Legend-League-API
   uvicorn app:app --host 0.0.0.0 --port 8000
   ```

## Features Included

### Security
- ✅ HTTPS redirect and modern SSL configuration
- ✅ Security headers (HSTS, XSS protection, content security)
- ✅ Attack pattern blocking
- ✅ Connection limiting (10 per IP)

### Performance
- ✅ Rate limiting per endpoint:
  - Chart: 2 req/sec (burst 5)
  - Player data: 5 req/sec (burst 10) 
  - General: 10 req/sec (burst 20)
- ✅ Gzip compression
- ✅ HTTP/2 support
- ✅ Optimized SSL settings

### API Support
- ✅ CORS headers for web app access
- ✅ Extended timeouts for chart generation
- ✅ Proper proxy headers
- ✅ OPTIONS request handling

### Monitoring
- ✅ Detailed access logs with response times
- ✅ Separate error logs
- ✅ Performance metrics

## Manual Installation

If you prefer manual setup:

1. **Add rate limiting to nginx.conf:**
   ```bash
   sudo nano /etc/nginx/nginx.conf
   # Add inside http { } block:
   limit_req_zone $binary_remote_addr zone=api_general:10m rate=10r/s;
   limit_req_zone $binary_remote_addr zone=chart_heavy:10m rate=2r/s;
   limit_req_zone $binary_remote_addr zone=player_data:10m rate=5r/s;
   limit_conn_zone $binary_remote_addr zone=conn_limit_per_ip:10m;
   ```

2. **Install site configuration:**
   ```bash
   sudo cp nginx-cheftoan.conf /etc/nginx/sites-available/api.cheftoan.com
   sudo ln -s /etc/nginx/sites-available/api.cheftoan.com /etc/nginx/sites-enabled/
   sudo rm /etc/nginx/sites-enabled/default
   ```

3. **Test and reload:**
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

## Testing

```bash
# Test API documentation
curl https://api.cheftoan.com/

# Test player endpoint
curl https://api.cheftoan.com/player/essentials?tag=YVLUP800

# Test chart endpoint
curl -I https://api.cheftoan.com/chart?tag=YVLUP800

# Monitor logs
sudo tail -f /var/log/nginx/api.cheftoan.com.access.log
```

## Troubleshooting

- **502 Bad Gateway**: FastAPI app not running on port 8000
- **Rate limiting errors**: Adjust rates in nginx-cheftoan.conf
- **SSL errors**: Check Let's Encrypt certificate paths
- **CORS issues**: Verify CORS headers in configuration