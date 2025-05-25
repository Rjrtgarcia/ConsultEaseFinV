#!/bin/bash

# ConsultEase Central System Setup Script
# Automated installation and configuration for Raspberry Pi

set -e

echo "🚀 Starting ConsultEase Central System Setup..."

# Color codes for output
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

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    print_warning "This script is optimized for Raspberry Pi. Continuing anyway..."
fi

print_header "System Update and Dependencies"

# Update system packages
print_status "Updating system packages..."
apt update && apt upgrade -y

# Install required system packages
print_status "Installing system dependencies..."
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    postgresql \
    postgresql-contrib \
    nginx \
    redis-server \
    git \
    curl \
    wget \
    unzip \
    htop \
    nano \
    supervisor \
    ufw \
    fail2ban \
    certbot \
    python3-certbot-nginx

print_header "PostgreSQL Database Setup"

# Configure PostgreSQL
print_status "Setting up PostgreSQL database..."
systemctl start postgresql
systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE consulteasedb;
CREATE USER consulteaseuser WITH ENCRYPTED PASSWORD 'ConsultEase2024!';
GRANT ALL PRIVILEGES ON DATABASE consulteasedb TO consulteaseuser;
ALTER USER consulteaseuser CREATEDB;
\q
EOF

print_status "PostgreSQL database created successfully"

print_header "Python Environment Setup"

# Create application directory
print_status "Creating application directory..."
mkdir -p /opt/consulteasecentral
cd /opt/consulteasecentral

# Create Python virtual environment
print_status "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip

# Create requirements.txt with all dependencies
cat > requirements.txt << EOF
Django==4.2.7
djangorestframework==3.14.0
django-cors-headers==4.3.1
psycopg2-binary==2.9.7
redis==5.0.1
celery==5.3.4
paho-mqtt==1.6.1
cryptography==41.0.7
bcrypt==4.1.1
Pillow==10.1.0
python-decouple==3.8
gunicorn==21.2.0
whitenoise==6.6.0
django-extensions==3.2.3
django-debug-toolbar==4.2.0
requests==2.31.0
aiofiles==23.2.1
asyncio-mqtt==0.16.1
uvloop==0.19.0
EOF

pip install -r requirements.txt

print_header "Application Code Setup"

# Copy application files (assuming they're in the current directory)
print_status "Copying application files..."
if [ -d "../central_system" ]; then
    cp -r ../central_system/* .
else
    print_warning "Central system files not found in expected location"
    print_status "Please copy the central_system files to /opt/consulteasecentral/"
fi

# Set proper permissions
chown -R www-data:www-data /opt/consulteasecentral
chmod -R 755 /opt/consulteasecentral

print_header "Database Migration"

# Run Django migrations
print_status "Running database migrations..."
source venv/bin/activate
python manage.py makemigrations
python manage.py migrate

# Create superuser (non-interactive)
print_status "Creating admin user..."
python manage.py shell << EOF
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@consulteasetech.com', 'Admin123!')
    print("Admin user created successfully")
else:
    print("Admin user already exists")
EOF

print_header "Nginx Configuration"

# Create Nginx configuration
print_status "Configuring Nginx..."
cat > /etc/nginx/sites-available/consulteasecentral << EOF
server {
    listen 80;
    server_name _;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Static files
    location /static/ {
        alias /opt/consulteasecentral/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /opt/consulteasecentral/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Main application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check endpoint
    location /health/ {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/consulteasecentral /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t

print_header "Systemd Service Configuration"

# Create systemd service for the application
print_status "Creating systemd service..."
cat > /etc/systemd/system/consulteasecentral.service << EOF
[Unit]
Description=ConsultEase Central System
After=network.target postgresql.service redis.service
Requires=postgresql.service redis.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/consulteasecentral
Environment=PATH=/opt/consulteasecentral/venv/bin
ExecStart=/opt/consulteasecentral/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 central_system.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=consulteasecentral

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for MQTT service
cat > /etc/systemd/system/consulteasemqtt.service << EOF
[Unit]
Description=ConsultEase MQTT Service
After=network.target consulteasecentral.service
Requires=consulteasecentral.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/consulteasecentral
Environment=PATH=/opt/consulteasecentral/venv/bin
ExecStart=/opt/consulteasecentral/venv/bin/python manage.py run_mqtt_service
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=consulteasemqtt

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable services
systemctl daemon-reload
systemctl enable consulteasecentral
systemctl enable consulteasemqtt
systemctl enable nginx
systemctl enable postgresql
systemctl enable redis-server

print_header "Firewall Configuration"

# Configure UFW firewall
print_status "Configuring firewall..."
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 1883/tcp  # MQTT
ufw allow 8883/tcp  # MQTT over TLS

print_header "Security Hardening"

# Configure fail2ban
print_status "Configuring fail2ban..."
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true
EOF

systemctl enable fail2ban
systemctl start fail2ban

print_header "Log Rotation Setup"

# Configure log rotation
print_status "Setting up log rotation..."
cat > /etc/logrotate.d/consulteasecentral << EOF
/var/log/consulteasecentral/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload consulteasecentral
    endscript
}
EOF

# Create log directory
mkdir -p /var/log/consulteasecentral
chown www-data:www-data /var/log/consulteasecentral

print_header "Performance Optimization"

# Optimize system for Raspberry Pi
print_status "Applying Raspberry Pi optimizations..."

# Increase swap size for better performance
if [ -f /etc/dphys-swapfile ]; then
    sed -i 's/CONF_SWAPSIZE=100/CONF_SWAPSIZE=1024/' /etc/dphys-swapfile
    systemctl restart dphys-swapfile
fi

# Optimize PostgreSQL for Raspberry Pi
cat >> /etc/postgresql/*/main/postgresql.conf << EOF

# ConsultEase optimizations for Raspberry Pi
shared_buffers = 128MB
effective_cache_size = 512MB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB
EOF

systemctl restart postgresql

print_header "Final Setup Steps"

# Collect static files
print_status "Collecting static files..."
cd /opt/consulteasecentral
source venv/bin/activate
python manage.py collectstatic --noinput

# Create initial data
print_status "Creating initial data..."
python manage.py loaddata initial_data.json 2>/dev/null || print_warning "No initial data fixture found"

# Start services
print_status "Starting services..."
systemctl start nginx
systemctl start consulteasecentral
systemctl start consulteasemqtt

# Wait for services to start
sleep 10

print_header "Installation Complete"

print_status "ConsultEase Central System has been successfully installed!"
print_status ""
print_status "🌐 Web Interface: http://$(hostname -I | awk '{print $1}')"
print_status "👤 Admin Username: admin"
print_status "🔑 Admin Password: Admin123!"
print_status ""
print_status "📋 Next Steps:"
print_status "1. Access the web interface and change the default password"
print_status "2. Configure faculty desk units"
print_status "3. Run the health check: ./scripts/health_check.sh"
print_status ""
print_status "📚 Documentation: /opt/consulteasecentral/docs/"
print_status "📊 Logs: /var/log/consulteasecentral/"
print_status ""
print_status "✅ Installation completed successfully!"

# Create a status file
echo "$(date): ConsultEase Central System installed successfully" > /opt/consulteasecentral/installation_status.txt

exit 0
