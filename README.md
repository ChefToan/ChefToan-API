# ChefToan's API

A modular API platform hosting various services and endpoints. This platform is designed to be easily extensible with new API modules while maintaining high performance and scalability.

## 🚀 Features

- **Modular Architecture**: Each API service is contained in its own module for easy maintenance and expansion
- **High-Performance Caching**: Redis-powered caching for improved response times and reduced external API calls
- **Scalable Design**: Built with FastAPI for high-performance async operations
- **Production Ready**: Complete deployment configuration with nginx, SSL, and rate limiting
- **Developer Friendly**: Interactive API documentation and comprehensive error handling

## 📊 Available API Modules

### Clash of Clans API (`/clash-of-clans/`)
- **Player Data**: Complete player information from Clash of Clans API
- **Essential Player Data**: Optimized endpoint for mobile apps with reduced payload size
- **Trophy Charts**: Visual trophy progression charts for Legend League players
- **Features**: Hero equipment data, performance optimization, aggressive caching

### Test API (`/test/`)
- **Test Image**: Returns a fun test image for API testing and entertainment
- **Features**: Optimized image serving, subtle custom headers, inline browser display

## 🏗️ Project Structure

```
cheftoan-api/
├── app.py                              # Main FastAPI application
├── config.py                           # Configuration management
├── requirements.txt                    # Dependencies
├── src/
│   ├── core/                          # Core utilities and shared services
│   │   ├── auth.py                    # Authentication middleware
│   │   ├── redis_service.py           # Redis caching service
│   │   └── retry_utils.py             # Retry logic utilities
│   ├── apis/                          # API modules (one per service/domain)
│   │   ├── clash_of_clans/            # Clash of Clans API module
│   │   │   ├── routes.py              # API endpoints
│   │   │   ├── chart_generator.py     # Chart generation for Clash of Clans
│   │   │   ├── services/              # Business logic and external API clients
│   │   │   └── models/                # Data models
│   │   └── test/                      # Test API module
│   │       ├── routes.py              # Test endpoints (rickroll, info)
│   │       ├── services/              # Test-related services
│   │       └── models/                # Test data models
│   └── utils/                         # General utilities
├── assets/                            # Static assets
│   ├── images/                        # Image files
│   │   └── rickroll.png              # Rickroll image for test endpoint
│   └── README.md                      # Assets documentation
├── deployment/                        # Deployment configurations
│   ├── nginx-cheftoan.conf           # Production nginx configuration
│   └── setup-nginx.sh               # Deployment script
└── docs/                             # API documentation
```

## 🛠️ Setup

### Basic Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/cheftoan-api.git
   cd cheftoan-api
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install Redis:
   ```bash
   # On macOS
   brew install redis
   
   # On Ubuntu/Debian
   sudo apt update
   sudo apt install redis-server
   ```

5. Create a `.env` file and add your configuration:
   ```
   DEBUG=True
   HOST=localhost
   PORT=8000
   COC_API_TOKEN=your_coc_api_token_here
   CLASHPERK_API_TOKEN=your_clashperk_api_token_here
   REDIS_ENABLED=True
   REDIS_URL=redis://localhost:6379/0
   REDIS_CACHE_TIMEOUT=3600
   ```

6. Run the FastAPI app in development mode:
   ```bash
   python app.py
   ```

7. Access the API:
   - **Documentation**: `http://localhost:8000/`
   - **Health Check**: `http://localhost:8000/health`
   - **Clash of Clans Player**: `http://localhost:8000/clash-of-clans/player?tag=PLAYERTAG`
   - **Essential Player Data**: `http://localhost:8000/clash-of-clans/player/essentials?tag=PLAYERTAG`
   - **Trophy Chart**: `http://localhost:8000/clash-of-clans/chart?tag=PLAYERTAG`

### Production Deployment

1. Set up a server with a domain (e.g., api.cheftoan.com)

2. Install required packages:
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv nginx certbot python3-certbot-nginx redis-server
   ```

3. Clone your repository:
   ```bash
   git clone https://github.com/yourusername/cheftoan-api.git
   cd cheftoan-api
   ```

4. Set up your virtual environment and install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   pip install gunicorn
   ```

5. Configure SSL with Let's Encrypt:
   ```bash
   sudo certbot --nginx -d api.cheftoan.com
   ```

6. Deploy nginx configuration:
   ```bash
   cd deployment
   sudo ./setup-nginx.sh
   ```

7. Create a systemd service file:
   ```bash
   sudo nano /etc/systemd/system/cheftoan-api.service
   ```

   Add the following content:
   ```ini
   [Unit]
   Description=ChefToan's API Service
   After=network.target redis-server.service
   
   [Service]
   User=ubuntu
   WorkingDirectory=/path/to/cheftoan-api
   ExecStart=/path/to/cheftoan-api/.venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 'app:create_app()'
   Restart=always
   StandardOutput=journal
   StandardError=journal
   Environment="PYTHONPATH=/path/to/cheftoan-api"
   Environment="DEBUG=False"
   Environment="HOST=127.0.0.1"
   Environment="PORT=8000"
   Environment="COC_API_TOKEN=your_token_here"
   Environment="CLASHPERK_API_TOKEN=your_token_here"
   Environment="REDIS_ENABLED=True"
   Environment="REDIS_URL=redis://localhost:6379/0"
   Environment="REDIS_CACHE_TIMEOUT=3600"
   
   [Install]
   WantedBy=multi-user.target
   ```

8. Enable and start the service:
   ```bash
   sudo systemctl enable cheftoan-api
   sudo systemctl start cheftoan-api
   ```

## 📚 API Documentation

### Clash of Clans Endpoints

All Clash of Clans endpoints are prefixed with `/clash-of-clans/`:

- `GET /clash-of-clans/player?tag=<player_tag>` - Get **full** player information
  - Response: Complete JSON data from Clash of Clans API
  - **Use Case**: When you need all available player data

- `GET /clash-of-clans/player/essentials?tag=<player_tag>` - Get **essential** player data (optimized for mobile apps)
  - Response: Optimized JSON data with only essential information
  - **Use Case**: **Recommended for mobile apps** - faster loading, smaller payload
  - **Performance**: ~70% smaller payload than full player data
  - Includes: basic info, heroes, **hero equipment**, troops, spells, achievements

- `GET /clash-of-clans/chart?tag=<player_tag>` - Generate trophy progression chart
  - Response: PNG image
  - **Use Case**: Visual representation of Legend League trophy progression

### Test Endpoints

- `GET /test/` - Get test image
  - Response: PNG image displayed inline in browser
  - **Use Case**: API testing, demonstrations, or entertainment
  - **Headers**: Includes `X-Test: true`, `X-Message: who knows?`, and optimized for inline display
  - **Features**: 67KB optimized image, StreamingResponse for proper browser rendering

### System Endpoints

- `GET /` - Interactive API documentation
- `GET /health` - Health check endpoint

## 🔧 Adding New API Modules

To add a new API module:

1. Create a new directory under `src/apis/`:
   ```bash
   mkdir -p src/apis/your_new_api/{services,models}
   ```

2. Create `routes.py` in your new module:
   ```python
   from fastapi import APIRouter
   
   your_api_router = APIRouter(prefix="/your-api", tags=["Your API"])
   
   @your_api_router.get("/endpoint")
   async def your_endpoint():
       return {"message": "Hello from your API"}
   ```

3. Register your router in `app.py`:
   ```python
   from src.apis.your_new_api.routes import your_api_router
   app.include_router(your_api_router)
   ```

4. Update nginx configuration if needed for specific rate limiting or routing rules.

## ⚡ Performance Features

### Caching Strategy
- **Player data**: 5 minutes cache
- **Essential player data**: 5 minutes cache  
- **Legend League data**: 15 minutes cache
- **Chart images**: 10 minutes cache

### Rate Limiting (Production)
- **Chart endpoint**: 2 req/sec (burst 5)
- **Player data**: 5 req/sec (burst 10)
- **General API**: 10 req/sec (burst 20)
- **Connection limiting**: 10 concurrent connections per IP

### Mobile Optimization
For mobile applications, use the `/clash-of-clans/player/essentials` endpoint:
- **70% smaller payload** than full player data
- **Faster loading times**
- **Reduced battery usage**
- **Lower mobile data consumption**

## 🔍 Monitoring

### Service Status
```bash
systemctl status cheftoan-api
systemctl status nginx
systemctl status redis-server
```

### Logs
```bash
# Application logs
journalctl -u cheftoan-api -f

# Nginx logs
tail -f /var/log/nginx/api.cheftoan.com.access.log
tail -f /var/log/nginx/api.cheftoan.com.error.log

# Redis logs
journalctl -u redis-server -f
```

### Testing
```bash
# Health check
curl https://api.cheftoan.com/health

# API documentation
curl https://api.cheftoan.com/

# Test Clash of Clans endpoints
curl "https://api.cheftoan.com/clash-of-clans/player/essentials?tag=PLAYERTAG"
curl -I "https://api.cheftoan.com/clash-of-clans/chart?tag=PLAYERTAG"
```

## 🛡️ Security Features

- **HTTPS Only**: Automatic HTTP to HTTPS redirect
- **Modern SSL**: TLS 1.2/1.3 with secure cipher suites
- **Security Headers**: HSTS, XSS protection, content type validation
- **Rate Limiting**: Prevents abuse and ensures fair usage
- **CORS Support**: Configurable cross-origin resource sharing
- **Attack Prevention**: Blocks common attack patterns
- **Input Validation**: Comprehensive input sanitization

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

### Development Guidelines
1. Follow the modular architecture pattern
2. Add comprehensive error handling
3. Include performance optimizations where applicable
4. Update documentation for new endpoints
5. Add appropriate caching strategies

## 📄 License

MIT