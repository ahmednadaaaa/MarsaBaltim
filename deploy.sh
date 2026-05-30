#!/bin/bash

# =============================================================================
# MARSA BALTIM - AWS EC2 AUTOMATED DEPLOYMENT SCRIPT (Systemd & Nginx)
# =============================================================================

# Exit immediately if any command exits with a non-zero status
set -e

# Define Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

PROJECT_DIR="/var/www/marsabaltim"

echo -e "${BLUE}=====================================================${NC}"
echo -e "${BLUE}     MARSA BALTIM - TRADITIONAL EC2 DEPLOYMENT       ${NC}"
echo -e "${BLUE}=====================================================${NC}"

# Check if running as root or under sudo
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[ERROR] Please run this script with sudo or as root!${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${RED}[ERROR] .env file not found in $PROJECT_DIR!${NC}"
    echo -e "${YELLOW}Please create a production .env file from 'env.prod.example' before deploying.${NC}"
    exit 1
fi

echo -e "${YELLOW}[1/6] Pulling latest codebase from Git...${NC}"
# Uncomment the line below when deploying on the server:
# git -C "$PROJECT_DIR" pull origin main

echo -e "${YELLOW}[2/6] Restoring dependencies in Python Virtual Environment...${NC}"
source "$PROJECT_DIR/venv/bin/activate"
pip install -r "$PROJECT_DIR/requirements.txt"
pip install django-storages boto3 gunicorn

echo -e "${YELLOW}[3/6] Applying Django Database Migrations...${NC}"
python "$PROJECT_DIR/manage.py" migrate --noinput

echo -e "${YELLOW}[4/6] Compiling Local Static Files (for Nginx)...${NC}"
python "$PROJECT_DIR/manage.py" collectstatic --noinput

echo -e "${YELLOW}[5/6] Securing Folder Ownership & Permissions...${NC}"
chown -R django:www-data "$PROJECT_DIR"
find "$PROJECT_DIR" -type d -exec chmod 755 {} \;
find "$PROJECT_DIR" -type f -exec chmod 644 {} \;
chmod 600 "$PROJECT_DIR/.env"

echo -e "${YELLOW}[6/6] Reloading Systemd & Restarting Gunicorn + Nginx...${NC}"
systemctl daemon-reload
systemctl restart gunicorn.socket
systemctl restart gunicorn.service
systemctl reload nginx

echo -e "${GREEN}=====================================================${NC}"
echo -e "${GREEN}      DEPLOYMENT COMPLETED SUCCESSFULLY 🎉           ${NC}"
echo -e "${GREEN}=====================================================${NC}"
echo -e "${BLUE}Website is up and running securely!${NC}"
echo -e "${BLUE}Access it at: https://marsabaltim.com/${NC}"
echo -e "${BLUE}Check logs using: journalctl -u gunicorn -n 50 -f${NC}"
echo -e "${BLUE}=====================================================${NC}"
