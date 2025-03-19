# Progression Chart Image Generator Server (Clash of Clans Legend League)

A simple Flask application that fetches Legend League data from Clash of Clans and ClashPerk APIs, then generates a matplotlib chart showing daily trophy progression.

## Features

- Fetches player data (league, clan, trophies)
- Displays a progression chart for the Legend League season as PNG image format
- Uses a redesigned chart layout (top banner, middle row stats, bottom row chart)
- Can be deployed as a standalone API service

## Setup

### Basic Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/repo-name.git
   cd repo-name
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

4. Create a `.env` file and add your tokens:
   ```bash
   COC_API_TOKEN="YOUR_COC_API_TOKEN"
   CLASHPERK_API_TOKEN="YOUR_CLASHPERK_API_TOKEN"
   ```

5. Run the Flask app in development mode:
   ```bash
   python app.py
   ```

6. Open your browser at `http://127.0.0.1:5000/chart/<player_tag>`.

### Setting Up as an API Service

You can set up this application as a proper API service in both local development and production environments.

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

4. Create an Nginx configuration (you can copy and modify `nginx.conf.sample`):
   ```bash
   # Copy the included sample config and modify it for your environment
   cp nginx.conf.sample ~/nginx.local.conf
   
   # Update SSL certificate paths and server_name as needed
   ```

5. Start Nginx with your configuration:
   ```bash
   nginx -c ~/nginx.local.conf
   ```

6. Start your Flask app on port 5001 (to avoid conflicts with AirPlay on Mac):
   ```bash
   # Modify app.py to use port 5001
   if __name__ == '__main__':
       app.run(debug=True, host='localhost', port=5001)
   
   # Then run the app
   python app.py
   ```

7. Access your local API at:
   ```
   https://api.yourdomain.local/chart/23PLAYERTAG
   ```

8. To stop the services:
   ```bash
   # Stop Flask app with Ctrl+C
   # Stop Nginx
   nginx -s stop
   ```

#### Production Deployment

1. Set up a server with a domain (e.g., api.yourdomain.com)

2. Install required packages:
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv nginx certbot python3-certbot-nginx
   ```

3. Clone your repository:
   ```bash
   git clone https://github.com/yourusername/repo-name.git
   cd repo-name
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
   # Copy the sample Nginx config
   sudo cp nginx.conf.sample /etc/nginx/sites-available/api-config
   
   # Edit the configuration to match your domain
   sudo nano /etc/nginx/sites-available/api-config
   
   # Enable the site
   sudo ln -s /etc/nginx/sites-available/api-config /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

6. Set up SSL with Let's Encrypt:
   ```bash
   sudo certbot --nginx -d api.yourdomain.com
   ```

7. Create a service file for automatic startup:
   ```bash
   sudo nano /etc/systemd/system/chart-api.service
   ```

   Add the following content:
   ```
   [Unit]
   Description=Chart API Service
   After=network.target
   
   [Service]
   User=ubuntu
   WorkingDirectory=/path/to/your/repo
   ExecStart=/path/to/your/repo/.venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 app:app
   Restart=always
   RestartSec=5
   Environment="COC_API_TOKEN=your_token_here"
   Environment="CLASHPERK_API_TOKEN=your_token_here"
   
   [Install]
   WantedBy=multi-user.target
   ```

8. Enable and start the service:
   ```bash
   sudo systemctl enable chart-api
   sudo systemctl start chart-api
   ```

9. Your API is now accessible at:
   ```
   https://api.yourdomain.com/chart/23PLAYERTAG
   ```

## API Endpoints

- `GET /chart/<player_tag>` - Generate and return a chart image for the specified player
  - `player_tag`: The Clash of Clans player tag (with or without the # symbol)
  - Example: `https://api.yourdomain.com/chart/23ABCDEF`
  - Response: PNG image

- `GET /` - Simple health check endpoint (returns "API is running")

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

MIT