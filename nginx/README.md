# PoseWeaver Nginx Configuration

This directory contains the refactored nginx configuration for PoseWeaver, supporting both development and production environments.

## Architecture

### Files Structure
```
nginx/
├── nginx.conf              # Main nginx configuration
├── conf.d/
│   └── poseweaver.conf     # Unified server configuration
├── proxy_params            # Reusable proxy settings
└── README.md              # This file
```

### Configuration Features

- **Unified Configuration**: Single config file handles both HTTP (dev) and HTTPS (prod)
- **Rate Limiting**: Built-in protection against abuse
- **Security Headers**: Comprehensive security header implementation
- **SSL/TLS**: Modern SSL configuration with Let's Encrypt support
- **Caching**: Optimized static file caching
- **Health Checks**: Built-in health monitoring endpoints

## Usage

### Development Mode (HTTP Only)
The default configuration serves content over HTTP for local development:

```bash
docker-compose up -d
```

Access your application at: `http://localhost`

### Production Mode (HTTPS)
For production deployment with SSL certificates:

1. **Setup SSL certificates**:
   ```bash
   ./scripts/setup-ssl.sh
   ```

2. **Enable HTTPS redirect** by uncommenting these lines in `poseweaver.conf`:
   ```nginx
   # location / {
   #     return 301 https://$server_name$request_uri;
   # }
   ```

3. **Comment out development HTTP serving** (the script does this automatically)

## Configuration Details

### Rate Limiting
- **API endpoints**: 10 requests/second with burst of 50
- **General traffic**: 1 request/second with burst of 20

### Security Headers
- `X-Frame-Options`: Prevents clickjacking
- `X-XSS-Protection`: XSS protection
- `X-Content-Type-Options`: MIME type sniffing protection
- `Referrer-Policy`: Controls referrer information
- `Strict-Transport-Security`: HTTPS enforcement (production only)

### SSL Configuration
- **Protocols**: TLSv1.2 and TLSv1.3 only
- **Ciphers**: Modern cipher suites preferred
- **Session**: 10-minute session timeout with shared cache

### Caching Strategy
- **Static files**: 1-year cache with immutable flag
- **API responses**: No caching (dynamic content)
- **Images**: 30-day cache for uploaded content

## Troubleshooting

### Common Issues

1. **502 Bad Gateway**
   - Check if backend/frontend containers are running
   - Verify upstream server addresses in configuration

2. **SSL Certificate Issues**
   - Ensure domain DNS points to your server
   - Check Let's Encrypt rate limits
   - Verify certificate file permissions

3. **Rate Limiting Too Aggressive**
   - Adjust `limit_req_zone` values in `nginx.conf`
   - Increase burst values in location blocks

### Logs
- **Access logs**: `/var/log/nginx/access.log`
- **Error logs**: `/var/log/nginx/error.log`
- **Docker logs**: `docker-compose logs nginx`

### Testing Configuration
```bash
# Test nginx configuration syntax
docker-compose exec nginx nginx -t

# Reload configuration without restart
docker-compose exec nginx nginx -s reload
```

## Migration from Old Setup

The refactored configuration replaces these old files:
- `poseweaver-http.conf` (removed)
- `poseweaver-https.conf.template` (removed)
- `poseweaver.ssl.conf*` (removed)

Benefits of the new setup:
- ✅ Single configuration file to maintain
- ✅ No duplicate CORS handling (handled by backend)
- ✅ Simplified SSL certificate management
- ✅ Better security defaults
- ✅ Improved performance with rate limiting
- ✅ Cleaner Docker integration
