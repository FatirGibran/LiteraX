#!/usr/bin/env bash
# ==============================================================================
# LiteraX Server Setup Script (Ubuntu/Debian)
# Automates deployment of LiteraX FastAPI Web Server and Telegram Bot Worker
# ==============================================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting LiteraX Server Setup...${NC}"

# Check current user and directories
INSTALL_DIR=$(pwd)
CURRENT_USER=$(whoami)

echo -e "📂 Install Directory: ${YELLOW}${INSTALL_DIR}${NC}"
echo -e "👤 Service User: ${YELLOW}${CURRENT_USER}${NC}"

# Step 1: System packages
echo -e "\n${GREEN}[1/5] Checking and installing system packages...${NC}"
sudo apt update
sudo apt install -y python3 python3-venv python3-pip build-essential curl libmupdf-dev nginx

# Step 2: Python Virtual Environment
echo -e "\n${GREEN}[2/5] Setting up Python virtual environment...${NC}"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "Created .venv directory."
fi

source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# Step 3: Environment configuration
echo -e "\n${GREEN}[3/5] Configuring environment file...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${YELLOW}⚠️  A default .env file has been created from .env.example.${NC}"
    echo -e "${YELLOW}👉 Please edit .env to insert your BOT_TOKEN and database credentials.${NC}"
else
    echo ".env file already exists."
fi

# Step 4: Configure Systemd Services
echo -e "\n${GREEN}[4/5] Configuring Systemd services...${NC}"
TMP_API_SVC="/tmp/literax-api.service"
TMP_BOT_SVC="/tmp/literax-bot.service"

sed -e "s|User=fatir|User=${CURRENT_USER}|g" \
    -e "s|/home/fatir/LiteraX|${INSTALL_DIR}|g" \
    deploy/systemd/literax-api.service > "$TMP_API_SVC"

sed -e "s|User=fatir|User=${CURRENT_USER}|g" \
    -e "s|/home/fatir/LiteraX|${INSTALL_DIR}|g" \
    deploy/systemd/literax-bot.service > "$TMP_BOT_SVC"

sudo cp "$TMP_API_SVC" /etc/systemd/system/literax-api.service
sudo cp "$TMP_BOT_SVC" /etc/systemd/system/literax-bot.service
sudo systemctl daemon-reload

echo "Systemd services installed: literax-api.service, literax-bot.service"

# Step 5: Configure Nginx Reverse Proxy
echo -e "\n${GREEN}[5/5] Configuring Nginx reverse proxy...${NC}"
sudo cp deploy/nginx/literax.conf /etc/nginx/sites-available/literax
if [ ! -f "/etc/nginx/sites-enabled/literax" ]; then
    sudo ln -s /etc/nginx/sites-available/literax /etc/nginx/sites-enabled/literax
fi
sudo nginx -t
sudo systemctl reload nginx

echo -e "\n${GREEN}================================================================${NC}"
echo -e "${GREEN}✅ LiteraX setup completed successfully!${NC}"
echo -e "${GREEN}================================================================${NC}"
echo -e "Next steps:"
echo -e "1. Edit .env with your Telegram BOT_TOKEN:"
echo -e "   ${YELLOW}nano .env${NC}"
echo -e "2. Start services:"
echo -e "   ${YELLOW}sudo systemctl enable --now literax-api.service${NC}"
echo -e "   ${YELLOW}sudo systemctl enable --now literax-bot.service${NC}"
echo -e "3. Check logs:"
echo -e "   ${YELLOW}sudo journalctl -u literax-bot.service -f${NC}"
echo -e "   ${YELLOW}sudo journalctl -u literax-api.service -f${NC}"
