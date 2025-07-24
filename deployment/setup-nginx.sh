#!/bin/bash
# Setup script for nginx configuration on Ubuntu server
# Run this on your Ubuntu server as root or with sudo

echo "🚀 Setting up nginx for api.cheftoan.com..."

# Copy nginx configuration
echo "📁 Copying nginx configuration..."
sudo cp /path/to/your/project/deployment/nginx-cheftoan.conf /etc/nginx/sites-available/api.cheftoan.com

# Create symlink to enable the site
echo "🔗 Enabling site..."
sudo ln -sf /etc/nginx/sites-available/api.cheftoan.com /etc/nginx/sites-enabled/

# Remove default nginx site if it exists
if [ -f /etc/nginx/sites-enabled/default ]; then
    echo "🗑️  Removing default nginx site..."
    sudo rm /etc/nginx/sites-enabled/default
fi

# Test nginx configuration
echo "🧪 Testing nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx configuration is valid!"
    
    # Reload nginx
    echo "🔄 Reloading nginx..."
    sudo systemctl reload nginx
    
    echo "✅ Setup complete!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Make sure your FastAPI app is running: uvicorn app:app --host 0.0.0.0 --port 8000"
    echo "2. Check if your app is accessible: curl http://localhost:8000"
    echo "3. Test the API: curl https://api.cheftoan.com/player/essentials?tag=YVLUP800"
    echo ""
    echo "🔍 Debugging commands:"
    echo "- Check nginx status: sudo systemctl status nginx"
    echo "- Check nginx logs: sudo tail -f /var/log/nginx/error.log"
    echo "- Check if port 8000 is open: sudo netstat -tulpn | grep :8000"
    
else
    echo "❌ Nginx configuration has errors!"
    echo "Please check the configuration and try again."
fi