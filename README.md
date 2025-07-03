# Clash of Clans Legend League API

A Flask application that fetches Legend League data from Clash of Clans and ClashPerk APIs, then generates a matplotlib chart showing daily trophy progression. The API also provides direct access to player data and equipment information with optimized endpoints for mobile applications.

## Features

- Generates trophy progression charts for Legend League players
- Direct proxy access to player data from Clash of Clans API
- **Optimized essentials endpoint** for mobile apps with reduced payload size (includes hero equipment)
- Redis caching for improved performance and reduced API calls
- Modular architecture for maintainability
- Deployable as a standalone API service

## Setup

### Basic Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/clash-legend-api.git
   cd clash-legend-api
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
   PORT=5001
   COC_API_TOKEN=your_coc_api_token_here
   CLASHPERK_API_TOKEN=your_clashperk_api_token_here
   REDIS_ENABLED=True
   REDIS_URL=redis://localhost:6379/0
   REDIS_CACHE_TIMEOUT=3600
   ```

6. Run the Flask app in development mode:
   ```bash
   python app.py
   ```

7. Access the endpoints:
   - Chart: `http://localhost:5001/chart?tag=PLAYERTAG`
   - Full Player data: `http://localhost:5001/player?tag=PLAYERTAG`
   - **Essential Player data (Mobile)**: `http://localhost:5001/player/essentials?tag=PLAYERTAG`

### Setting Up as an API Service

#### Local Development Setup with HTTPS

1. Install required software:
   ```bash
   # On macOS
   brew install nginx
   brew install mkcert
   
   # On Ubuntu/Debian
   sudo apt install nginx
   sudo apt install libnss3-tools
   pip install mkcert
   ```

2. Create a local domain entry:
   ```bash
   # Add to /etc/hosts
   127.0.0.1  api.yourdomain.local
   ```

3. Generate SSL certificates for local development:
   ```bash
   # Install mkcert CA
   mkcert -install
   
   # Create certificates
   mkdir -p ~/certs
   cd ~/certs
   mkcert api.yourdomain.local
   ```

4. Create an Nginx configuration:
   ```nginx
   worker_processes 1;
   
   events {
       worker_connections 1024;
   }
   
   http {
       include mime.types;
       default_type application/octet-stream;
       sendfile on;
       keepalive_timeout 65;
   
       server {
           listen 443 ssl;
           server_name api.yourdomain.local;
   
           ssl_certificate /path/to/your/certs/api.yourdomain.local.pem;
           ssl_certificate_key /path/to/your/certs/api.yourdomain.local-key.pem;
   
           location / {
               proxy_pass http://localhost:5001;
               proxy_set_header Host $host;
               proxy_set_header X-Real-IP $remote_addr;
               proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
               proxy_set_header X-Forwarded-Proto $scheme;
           }
       }
   }
   ```

5. Start Redis:
   ```bash
   # On macOS
   brew services start redis
   
   # On Ubuntu/Debian
   sudo systemctl start redis-server
   ```

6. Start Nginx with your configuration:
   ```bash
   nginx -c /path/to/your/nginx.conf
   ```

7. Start your Flask app:
   ```bash
   python app.py
   ```

8. Access your local API at:
   ```
   https://api.yourdomain.local/chart?tag=PLAYERTAG
   https://api.yourdomain.local/player?tag=PLAYERTAG
   https://api.yourdomain.local/player/essentials?tag=PLAYERTAG
   ```

#### Production Deployment

1. Set up a server with a domain (e.g., api.yourdomain.com)

2. Install required packages:
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv nginx certbot python3-certbot-nginx redis-server
   ```

3. Clone your repository:
   ```bash
   git clone https://github.com/yourusername/clash-legend-api.git
   cd clash-legend-api
   ```

4. Set up your virtual environment and install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   pip install gunicorn
   ```

5. Configure Nginx:
   ```bash
   sudo nano /etc/nginx/sites-available/clash-api
   ```

   Add this configuration:
   ```nginx
   server {
       listen 80;
       server_name api.yourdomain.com;
       
       # Redirect HTTP to HTTPS
       return 301 https://$host$request_uri;
   }
   
   server {
       listen 443 ssl;
       server_name api.yourdomain.com;
       
       # SSL configuration (will be added by Certbot)
       
       # Proxy requests to the Flask app
       location / {
           proxy_pass http://localhost:5001;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
       
       # Larger timeout for chart generation
       proxy_read_timeout 60s;
   }
   ```

6. Enable the site and set up SSL with Let's Encrypt:
   ```bash
   sudo ln -s /etc/nginx/sites-available/clash-api /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   sudo certbot --nginx -d api.yourdomain.com
   ```

7. Configure Redis for production:
   ```bash
   sudo systemctl enable redis-server
   sudo systemctl start redis-server
   ```

8. Create a systemd service file:
   ```bash
   sudo nano /etc/systemd/system/clash-api.service
   ```

   Add the following content:
   ```ini
   [Unit]
   Description=Clash Legend API Service
   After=network.target redis-server.service
   
   [Service]
   User=ubuntu
   WorkingDirectory=/path/to/clash-legend-api
   ExecStart=/path/to/clash-legend-api/.venv/bin/gunicorn -w 4 -b 127.0.0.1:5001 'app:create_app()'
   Restart=always
   StandardOutput=journal
   StandardError=journal
   Environment="PYTHONPATH=/path/to/clash-legend-api"
   Environment="DEBUG=False"
   Environment="HOST=127.0.0.1"
   Environment="PORT=5001"
   Environment="COC_API_TOKEN=your_token_here"
   Environment="CLASHPERK_API_TOKEN=your_token_here"
   Environment="REDIS_ENABLED=True"
   Environment="REDIS_URL=redis://localhost:6379/0"
   Environment="REDIS_CACHE_TIMEOUT=3600"
   
   [Install]
   WantedBy=multi-user.target
   ```

9. Enable and start the service:
   ```bash
   sudo systemctl enable clash-api
   sudo systemctl start clash-api
   ```

10. Your API is now accessible at:
    ```
    https://api.yourdomain.com/chart?tag=PLAYERTAG
    https://api.yourdomain.com/player?tag=PLAYERTAG
    https://api.yourdomain.com/player/essentials?tag=PLAYERTAG
    ```

## API Endpoints

- `GET /chart?tag=<player_tag>` - Generate and return a chart image for the specified player
  - `player_tag`: The Clash of Clans player tag (with or without the # symbol)
  - Examples: 
    - `https://api.yourdomain.com/chart?tag=ABCDEF123`
    - `https://api.yourdomain.com/chart?tag=%23ABCDEF123` (URL encoded)
  - Response: PNG image

- `GET /player?tag=<player_tag>` - Get **full** player information directly from Clash of Clans API
  - `player_tag`: The Clash of Clans player tag (with or without the # symbol)
  - Examples:
    - `https://api.yourdomain.com/player?tag=ABCDEF123`
    - `https://api.yourdomain.com/player?tag=%23ABCDEF123` (URL encoded)
  - Response: Complete JSON data from Clash of Clans API
  - **Use Case**: When you need all available player data

- `GET /player/essentials?tag=<player_tag>` - Get **essential** player information (optimized for mobile apps)
  - `player_tag`: The Clash of Clans player tag (with or without the # symbol)
  - Examples:
    - `https://api.yourdomain.com/player/essentials?tag=ABCDEF123`
    - `https://api.yourdomain.com/player/essentials?tag=%23ABCDEF123` (URL encoded)
  - Response: Optimized JSON data with only essential information
  - **Use Case**: **Recommended for mobile apps** - faster loading, smaller payload
  - **Performance**: ~70% smaller payload than full player data
  - Response includes: basic info, heroes, **hero equipment**, troops, spells, achievements (highest trophy only)
  - **Hero Equipment Format**:
    ```json
    {
      "heroEquipment": {
        "barbarianKing": [...],
        "archerQueen": [...],
        "minionPrince": [...],
        "grandWarden": [...],
        "royalChampion": [...]
      }
    }
    ```

- `GET /` - API information and health check endpoint
  - Returns API status and endpoint documentation
  - Response: JSON with endpoint information and examples

## Performance Optimizations

### Mobile App Optimization

For mobile applications, use the `/player/essentials` endpoint instead of `/player`:

- **Payload Size**: ~70% smaller than full player data
- **Loading Time**: Significantly faster due to reduced data transfer
- **Battery Life**: Less network usage means better battery performance
- **Data Usage**: Reduced mobile data consumption

### Caching Strategy

The application uses Redis to cache responses from external APIs:

- **Player data** from Clash of Clans API (5 minutes cache)
- **Essential player data** (including hero equipment) (5 minutes cache)
- **Legend League data** from ClashPerk API (15 minutes cache)
- **Final combined player chart data** (30 minutes cache)

This reduces API calls and improves response times for frequent requests. Cache timeouts can be configured through environment variables.

### Data Ordering

All data is returned in consistent, logical order:

- **Heroes**: Barbarian King → Archer Queen → Minion Prince → Grand Warden → Royal Champion
- **Equipment**: Epic equipment first, then by equipped status
- **Troops**: Logical progression from basic to advanced
- **Spells**: Organized by elixir type and unlock order

## Player Tag Format

Player tags can be provided in several formats:
- Without the # symbol: `?tag=ABCDEF123`
- With the # symbol (URL encoded): `?tag=%23ABCDEF123`
- With the # symbol (not encoded): `?tag=#ABCDEF123` (may work but not recommended)

The API will automatically add the # prefix if it's missing and convert the tag to uppercase.

## Error Handling

The API provides detailed error responses for common issues:

- **400 Bad Request**: Missing player tag parameter
- **404 Not Found**: Player not found
- **500 Internal Server Error**: API authentication errors or other server issues
- **503 Service Unavailable**: External APIs (Clash of Clans) temporarily unavailable

For chart endpoints, errors are returned as generated error images with descriptive messages.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

MIT
