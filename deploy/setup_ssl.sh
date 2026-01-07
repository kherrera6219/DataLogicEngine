#!/bin/bash
# SSL Setup Script using Let's Encrypt (Certbot)
# Run as root on your production server

set -e

DOMAIN="${1:-your-domain.com}"
EMAIL="${2:-admin@your-domain.com}"
WEBROOT="/var/www/certbot"

echo "====================================="
echo "SSL Certificate Setup for $DOMAIN"
echo "====================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo)"
    exit 1
fi

# Install certbot if not present
if ! command -v certbot &> /dev/null; then
    echo "Installing Certbot..."
    apt-get update
    apt-get install -y certbot python3-certbot-nginx
fi

# Create webroot directory
mkdir -p "$WEBROOT"

# Stop nginx temporarily if running
systemctl stop nginx 2>/dev/null || true

# Obtain certificate
echo "Obtaining SSL certificate..."
certbot certonly \
    --standalone \
    --preferred-challenges http \
    --agree-tos \
    --email "$EMAIL" \
    -d "$DOMAIN" \
    -d "www.$DOMAIN"

# Start nginx
systemctl start nginx

# Set up auto-renewal
echo "Setting up auto-renewal..."
cat > /etc/cron.d/certbot-renewal << 'EOF'
# Renew certificates twice daily
0 0,12 * * * root certbot renew --quiet --post-hook "systemctl reload nginx"
EOF

# Verify certificate
echo "Verifying certificate..."
certbot certificates

echo ""
echo "====================================="
echo "SSL Setup Complete!"
echo "====================================="
echo ""
echo "Next steps:"
echo "1. Update deploy/nginx.conf with your domain name"
echo "2. Copy nginx.conf to /etc/nginx/sites-available/datalogicengine"
echo "3. Create symlink: ln -s /etc/nginx/sites-available/datalogicengine /etc/nginx/sites-enabled/"
echo "4. Test nginx config: nginx -t"
echo "5. Reload nginx: systemctl reload nginx"
echo ""
echo "Certificate will auto-renew before expiration."
