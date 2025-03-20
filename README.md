# Clash of Clans Legend League API

A Flask application that fetches Legend League data from Clash of Clans and ClashPerk APIs, then generates a matplotlib chart showing daily trophy progression. The API also provides direct access to player data.

## Features

- Generates trophy progression charts for Legend League players
- Direct proxy access to player data from Clash of Clans API
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
   - Chart: `http://localhost:5001/chart/#PLAYERTAG`
   - Player data: `http://localhost:5001/player/#PLAYERTAG`

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
   https://api.yourdomain.local/chart/#PLAYERTAG
   https://api.yourdomain.local/player/#PLAYERTAG
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
    https://api.yourdomain.com/chart/#PLAYERTAG
    https://api.yourdomain.com/player/#PLAYERTAG
    ```

## API Endpoints

- `GET /chart/<player_tag>` - Generate and return a chart image for the specified player
  - `player_tag`: The Clash of Clans player tag (with or without the # symbol)
  - Example: `https://api.yourdomain.com/chart/#ABCDEF`
  - Response: PNG image

- `GET /player/<player_tag>` - Get player information directly from Clash of Clans API
  - `player_tag`: The Clash of Clans player tag (with or without the # symbol)
  - Example: `https://api.yourdomain.com/player/#ABCDEF`
  - Response: JSON data

- `GET /` - Simple health check endpoint (returns "API is running")

## Redis Caching

The application uses Redis to cache responses from external APIs:

- Player data from Clash of Clans API (5 minutes cache)
- Legend League data from ClashPerk API (15 minutes cache)
- Final combined player chart data (30 minutes cache)

This reduces API calls and improves response times for frequent requests. Cache timeouts can be configured through environment variables.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

MIT