# AWS EC2 Production Deployment Plan - Marsa Baltim

This plan details the exact deployment sequence to configure and launch the **Marsa Baltim** Django backend on an AWS EC2 instance.

---

## 📅 Phase 1: AWS Resource Provisioning

### 1. Amazon EC2 Instance
* **AMI:** Ubuntu Server 24.04 LTS (HVM), SSD Volume Type.
* **Instance Type:** `t3.micro` or `t3.small` (Free Tier eligible or low-cost).
* **Storage:** 20 GB gp3 SSD.
* **Security Group Configuration:**
  * Inbound Port `22` (SSH) -> Restricted to your IP.
  * Inbound Port `80` (HTTP) -> Anywhere (`0.0.0.0/0`).
  * Inbound Port `443` (HTTPS) -> Anywhere (`0.0.0.0/0`).

### 2. Amazon S3 Bucket
* Create an S3 bucket named `marsabaltim-media` (or similar) to store user media files.
* Disable "Block Public Access" selectively if you intend to serve media files directly, or route them through CloudFront.
* Configure an **IAM User** with programmatic access and attach an inline policy allowing `s3:PutObject`, `s3:GetObject`, `s3:DeleteObject`, and `s3:ListBucket`. Keep the **Access Key ID** and **Secret Access Key** safe.

---

## 🔧 Phase 2: Server OS Preparation

Connect to your EC2 instance via SSH and run:

```bash
# 1. Update OS Packages
sudo apt update && sudo apt upgrade -y

# 2. Install core system packages
sudo apt install python3-pip python3-venv python3-dev postgresql postgresql-contrib libpq-dev nginx curl git -y
```

---

## 🗄️ Phase 3: Database Configuration

### 1. Run local PostgreSQL (Recommended for Startup)
Access PostgreSQL CLI:
```bash
sudo -u postgres psql
```
Execute database creation SQL:
```sql
CREATE DATABASE baltim_prod;
CREATE USER baltim_admin WITH PASSWORD 'YOUR_CHOSEN_SECURE_PASSWORD';
ALTER ROLE baltim_admin SET client_encoding TO 'utf8';
ALTER ROLE baltim_admin SET default_transaction_isolation TO 'read committed';
ALTER ROLE baltim_admin SET timezone TO 'Africa/Cairo';
GRANT ALL PRIVILEGES ON DATABASE baltim_prod TO baltim_admin;
\q
```

---

## 📂 Phase 4: Django Code & Environment Setup

### 1. Configure System Users and Directories
Create a non-root system user for Django execution:
```bash
sudo useradd -m -r -s /bin/bash django
sudo mkdir -p /var/www/marsabaltim
sudo chown -R django:django /var/www/marsabaltim
```

### 2. Pull Code and Create Virtualenv
```bash
sudo -u django git clone <your-git-repository-url> /var/www/marsabaltim/
cd /var/www/marsabaltim
sudo -u django python3 -m venv venv
source venv/bin/activate
sudo -u django ./venv/bin/pip install --upgrade pip
sudo -u django ./venv/bin/pip install -r requirements.txt
sudo -u django ./venv/bin/pip install gunicorn django-storages boto3
```

### 3. Setup Production Environment Variables
Create `/var/www/marsabaltim/.env` owned by `django` with permission `600`:
```bash
sudo -u django nano /var/www/marsabaltim/.env
```
*(Fill in production values from `env.prod.example`)*

---

## ⚙️ Phase 5: Gunicorn Systemd Configuration

We use systemd **Socket Activation** for maximum reliability.

1. Create **Gunicorn Socket** configuration:
   `sudo nano /etc/systemd/system/gunicorn.socket` *(Use configurations from guide)*
2. Create **Gunicorn Service** configuration:
   `sudo nano /etc/systemd/system/gunicorn.service` *(Use configurations from guide)*
3. Enable and start Gunicorn:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start gunicorn.socket
   sudo systemctl enable gunicorn.socket
   ```

---

## 🔒 Phase 6: Nginx Reverse Proxy & SSL Setup

1. Create Nginx server configuration:
   `sudo nano /etc/nginx/sites-available/marsabaltim` *(Use configurations from guide)*
2. Enable the site and test configuration:
   ```bash
   sudo ln -s /etc/nginx/sites-available/marsabaltim /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```
3. Install **Certbot** and generate Let's Encrypt SSL certificates:
   ```bash
   sudo apt install certbot python3-certbot-nginx -y
   sudo certbot --nginx -d marsabaltim.com -d www.marsabaltim.com
   ```
4. Re-run Nginx test to ensure Certbot injected SSL parameters correctly:
   ```bash
   sudo nginx -t
   sudo systemctl restart nginx
   ```

---

## 🚀 Phase 7: Deployment Checklist & Validation

* Run `python3 manage.py collectstatic --noinput` to compile static assets.
* Run `python3 manage.py migrate --noinput` to apply migrations.
* Run `python3 manage.py check --deploy` to ensure Django is production secure.
* Visit `https://marsabaltim.com` in your browser to verify Nginx redirects, API requests, and media uploads!
