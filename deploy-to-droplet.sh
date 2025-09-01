#!/bin/bash

# Media Monitoring Agent - DigitalOcean Droplet Deployment Script
# Usage: ./deploy-to-droplet.sh your-droplet-ip

set -e

DROPLET_IP=$1
REPO_URL="https://github.com/yourusername/media-monitoring-agent.git"  # Update this
APP_DIR="/opt/media-monitoring-agent"

if [ -z "$DROPLET_IP" ]; then
    echo "Usage: $0 <droplet-ip>"
    echo "Example: $0 164.90.XXX.XXX"
    exit 1
fi

echo "🚀 Deploying Media Monitoring Agent to DigitalOcean Droplet: $DROPLET_IP"

# Function to run commands on droplet
run_remote() {
    ssh -o StrictHostKeyChecking=no root@$DROPLET_IP "$1"
}

# Function to copy files to droplet
copy_to_droplet() {
    scp -o StrictHostKeyChecking=no "$1" root@$DROPLET_IP:"$2"
}

echo "📦 Step 1: Installing system dependencies..."
run_remote "apt-get update && apt-get install -y python3 python3-pip python3-venv git curl nginx"

echo "📥 Step 2: Cloning repository..."
run_remote "rm -rf $APP_DIR && git clone $REPO_URL $APP_DIR"

echo "🐍 Step 3: Setting up Python environment..."
run_remote "cd $APP_DIR && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"

echo "⚙️ Step 4: Configuring environment..."
run_remote "cd $APP_DIR && cp .env.example .env"

echo "📋 Step 5: Creating systemd service..."
run_remote "cat > /etc/systemd/system/media-monitoring.service << 'EOF'
[Unit]
Description=Media Monitoring Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF"

echo "🗄️ Step 6: Initializing database..."
run_remote "cd $APP_DIR && source venv/bin/activate && python init_db.py"

echo "🔧 Step 7: Starting services..."
run_remote "systemctl daemon-reload && systemctl enable media-monitoring && systemctl start media-monitoring"

echo "🌐 Step 8: Configuring nginx..."
run_remote "cat > /etc/nginx/sites-available/media-monitoring << 'EOF'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF"

run_remote "ln -sf /etc/nginx/sites-available/media-monitoring /etc/nginx/sites-enabled/ && systemctl restart nginx"

echo "✅ Deployment complete!"
echo ""
echo "🎉 Your Media Monitoring Agent is now running at: http://$DROPLET_IP"
echo ""
echo "📝 Next steps:"
echo "1. SSH into your droplet: ssh root@$DROPLET_IP"
echo "2. Edit the .env file: nano $APP_DIR/.env"
echo "3. Add your Gemini API key and other settings"
echo "4. Restart the service: systemctl restart media-monitoring"
echo ""
echo "🔍 Useful commands:"
echo "- Check status: systemctl status media-monitoring"
echo "- View logs: journalctl -u media-monitoring -f"
echo "- Restart service: systemctl restart media-monitoring"