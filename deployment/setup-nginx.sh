#!/bin/bash
# Complete nginx setup script for api.cheftoan.com
# This script sets up the complete nginx configuration with all features

echo "🚀 Setting up complete nginx configuration for api.cheftoan.com..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (use sudo)"
    exit 1
fi

# Check if nginx-cheftoan.conf exists
if [ ! -f "nginx-cheftoan.conf" ]; then
    print_error "nginx-cheftoan.conf not found in current directory"
    exit 1
fi

print_step "Step 1: Backing up current nginx configuration..."
cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup.$(date +%Y%m%d_%H%M%S)
print_status "Backup created"

print_step "Step 2: Adding rate limiting zones to nginx.conf..."
# Check if rate limiting zones already exist
if ! grep -q "limit_req_zone.*api_general" /etc/nginx/nginx.conf; then
    # Create a temporary file with the rate limiting zones
    cat > /tmp/rate_limits.conf << 'EOF'

    # Rate limiting zones for api.cheftoan.com
    limit_req_zone $binary_remote_addr zone=api_general:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=chart_heavy:10m rate=2r/s;
    limit_req_zone $binary_remote_addr zone=player_data:10m rate=5r/s;
    limit_conn_zone $binary_remote_addr zone=conn_limit_per_ip:10m;
EOF
    
    # Insert the rate limiting zones after the opening http block
    sed -i '/http {/r /tmp/rate_limits.conf' /etc/nginx/nginx.conf
    rm /tmp/rate_limits.conf
    print_status "Rate limiting zones added to nginx.conf"
else
    print_warning "Rate limiting zones already exist in nginx.conf"
fi

print_step "Step 3: Installing site configuration..."
cp nginx-cheftoan.conf /etc/nginx/sites-available/api.cheftoan.com
print_status "Configuration file copied"

print_step "Step 4: Enabling site..."
ln -sf /etc/nginx/sites-available/api.cheftoan.com /etc/nginx/sites-enabled/
print_status "Site enabled"

print_step "Step 5: Removing default site..."
if [ -f /etc/nginx/sites-enabled/default ]; then
    rm /etc/nginx/sites-enabled/default
    print_status "Default site removed"
else
    print_warning "Default site not found"
fi

print_step "Step 6: Testing nginx configuration..."
if nginx -t; then
    print_status "✅ Nginx configuration test passed!"
    
    print_step "Step 7: Reloading nginx..."
    if systemctl reload nginx; then
        print_status "✅ Nginx reloaded successfully!"
        
        echo ""
        echo "🎉 Complete nginx configuration deployed successfully!"
        echo ""
        echo -e "${BLUE}📋 Features enabled:${NC}"
        echo "  ✅ HTTP to HTTPS redirect"
        echo "  ✅ Modern SSL configuration (TLS 1.2/1.3)"
        echo "  ✅ Rate limiting:"
        echo "      - Chart endpoint: 2 req/sec (burst 5)"
        echo "      - Player data: 5 req/sec (burst 10)"
        echo "      - General API: 10 req/sec (burst 20)"
        echo "  ✅ Connection limiting (10 per IP)"
        echo "  ✅ Security headers (HSTS, XSS protection, etc.)"
        echo "  ✅ CORS support for API access"
        echo "  ✅ Gzip compression"
        echo "  ✅ Attack pattern blocking"
        echo "  ✅ Detailed performance logging"
        echo ""
        echo -e "${BLUE}🔍 Monitoring commands:${NC}"
        echo "  systemctl status nginx"
        echo "  tail -f /var/log/nginx/api.cheftoan.com.access.log"
        echo "  tail -f /var/log/nginx/api.cheftoan.com.error.log"
        echo ""
        echo -e "${BLUE}🧪 Test commands:${NC}"
        echo "  curl https://api.cheftoan.com/"
        echo "  curl https://api.cheftoan.com/clash-of-clans/player/essentials?tag=YVLUP800"
        echo "  curl -I https://api.cheftoan.com/clash-of-clans/chart?tag=YVLUP800"
        echo ""
        echo -e "${GREEN}✅ Setup complete! Your API is ready for production.${NC}"
        
    else
        print_error "Failed to reload nginx"
        exit 1
    fi
else
    print_error "❌ Nginx configuration test failed!"
    echo ""
    echo -e "${YELLOW}🔧 To revert to backup:${NC}"
    echo "  sudo cp /etc/nginx/nginx.conf.backup.* /etc/nginx/nginx.conf"
    echo "  sudo nginx -t && sudo systemctl reload nginx"
    exit 1
fi