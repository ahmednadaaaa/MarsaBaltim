# AWS EC2 Production Deployment Checklist - Marsa Baltim

Use this checklist to verify that all configurations are secure, optimized, and ready for production traffic.

---

## 🔒 1. Django Settings Security Audit
- [ ] **`DEBUG = False`** verified in settings and runtime environment.
- [ ] **`SECRET_KEY`** changed to a long, complex, random string and stored as an environment variable (never hardcoded).
- [ ] **`ALLOWED_HOSTS`** explicitly set to `['marsabaltim.com', 'www.marsabaltim.com']` (no generic `*`).
- [ ] **Secure Cookies enabled**:
  - `SESSION_COOKIE_SECURE = True`
  - `CSRF_COOKIE_SECURE = True`
  - `SESSION_COOKIE_HTTPONLY = True`
  - `CSRF_COOKIE_HTTPONLY = True`
- [ ] **SSL/HTTPS Redirection & Headers**:
  - `SECURE_SSL_REDIRECT = True` (or handled via Nginx redirect)
  - `SECURE_HSTS_SECONDS = 31536000` (1 Year HSTS header)
  - `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`
  - `SECURE_HSTS_PRELOAD = True`
  - `SECURE_BROWSER_XSS_FILTER = True`
  - `SECURE_CONTENT_TYPE_NOSNIFF = True`

---

## ☁️ 2. AWS Infrastructure & Security Groups
- [ ] **S3 Media Storage**:
  - Bucket created with strict CORS permissions.
  - Programmatic IAM User created with narrowest possible privileges (`s3:PutObject`, `s3:GetObject`, `s3:DeleteObject`).
  - Amazon S3 credentials loaded securely via `.env`.
- [ ] **Host Firewall / Security Group**:
  - Only Port `22` (restricted to trusted SSH IPs), Port `80` (HTTP), and Port `443` (HTTPS) are open.
  - PostgreSQL Port `5432` is locked down and NOT accessible to the public internet.

---

## ⚙️ 3. Linux OS & Server Processes
- [ ] **System User Safety**:
  - Django/Gunicorn process runs under a dedicated, restricted system user `django` with **no root privileges**.
- [ ] **Systemd Socket Activation**:
  - Gunicorn socket (`gunicorn.socket`) and service (`gunicorn.service`) are active and enabled to start on system boot.
- [ ] **Log Collection**:
  - Standard output from Gunicorn is successfully captured by **journald** and readable via `journalctl -u gunicorn`.
- [ ] **Memory Protection**:
  - **Swap Space (2 GB)** is configured and enabled to prevent database or Gunicorn process OOM (Out of Memory) failures on low-cost instances.

---

## 🌐 4. Nginx Reverse Proxy & SSL
- [ ] **Static Asset Serving**:
  - Nginx static directory `/var/www/marsabaltim/staticfiles/` corresponds to Django's `STATIC_ROOT`.
  - Static assets serve successfully with compression (`gzip on`) and client caching (`Cache-Control: max-age=2592000`).
- [ ] **SSL Certificates**:
  - Let's Encrypt certificates generated successfully for `marsabaltim.com` and `www.marsabaltim.com`.
  - Certbot automated renewal schedule verified and active.
- [ ] **Redirect Protocol**:
  - All port 80 (HTTP) requests automatically return a `301 Moved Permanently` redirect to `https://marsabaltim.com`.

---

## 🗄️ 5. Database & Logging
- [ ] **Migrations Applied**:
  - Run `python manage.py migrate` and verify database structure is synchronized.
- [ ] **Django Integrity Check**:
  - Run `python manage.py check --deploy` and resolve any outstanding security or structural warnings.
