# AWS Production Cost Estimation - Marsa Baltim

This document provides a realistic monthly cost breakdown for hosting **Marsa Baltim** on traditional AWS infrastructure. It is optimized for maximum reliability and minimum cost during the startup phase.

---

## 🟢 Option A: Single EC2 Host (Ultra Low Cost / Startup Recommended)
In this model, Nginx, Gunicorn, PostgreSQL, and media file uploads run on a single `t3.micro` or `t3.small` instance. Media files are hosted on Amazon S3.

* **Best for:** Bootstrapping, validating the product, and low early-stage traffic.

### Monthly Cost Breakdown (t3.micro / 1GB RAM / 1 vCPU)
| Service / Resource | Pricing Details | Monthly Cost (USD) |
| :--- | :--- | :---: |
| **AWS EC2 Instance** | `t3.micro` Linux instance ($0.0104/hour) | **$7.48** (or **$0.00** if Free Tier) |
| **EBS Storage** | 20 GB gp3 General Purpose SSD ($0.08/GB) | **$1.60** |
| **Amazon S3** | 5 GB storage + S3 PUT/GET requests | **$0.25** |
| **Data Transfer (Out)** | ~5 GB outbound traffic ($0.09/GB) | **$0.45** |
| **Let's Encrypt SSL** | 100% Free Domain SSL | **$0.00** |
| **Total Estimated Cost** | **Startup Phase** | **$9.78 / month** (or **$0.25** if Free Tier!) |

---

## 🔵 Option B: Managed Tier (Production Grade / High Reliability)
In this model, the database is separated from the web server using **AWS RDS for PostgreSQL**. This ensures automated daily backups, high availability, and 99.99% uptime, keeping the EC2 instance completely stateless.

* **Best for:** Active production environment with steady booking traffic and paid properties.

### Monthly Cost Breakdown
| Service / Resource | Pricing Details | Monthly Cost (USD) |
| :--- | :--- | :---: |
| **AWS EC2 Instance** | `t3.small` Web Server (2GB RAM / 2 vCPU) | **$14.96** |
| **EBS Storage** | 20 GB gp3 SSD (for OS and static files) | **$1.60** |
| **AWS RDS PostgreSQL** | `db.t3.micro` managed database (1GB RAM / 20GB SSD) | **$16.50** |
| **Amazon S3** | 15 GB storage + Requests | **$0.50** |
| **Data Transfer (Out)** | ~25 GB outbound traffic | **$2.25** |
| **Let's Encrypt SSL** | Automated SSL | **$0.00** |
| **Total Estimated Cost** | **Managed Production** | **$35.81 / month** |

---

## 📈 Scaling Estimates & Costs (Per Visitor Tier)

### Tier 1: ~5,000 Visitors / month (Startup Phase)
* **Architecture:** Option A (Single EC2 `t3.micro` + S3).
* **Uptime Protection:** 2 GB Swap Space enabled to prevent RAM spikes.
* **Monthly Cost:** **$9.78** (or **$0.25** on Free Tier).

### Tier 2: ~20,000 Visitors / month (Growth Phase)
* **Architecture:** Option B (EC2 `t3.small` + S3 + RDS `db.t3.micro`).
* **Monthly Cost:** **$35.81**.

### Tier 3: ~100,000 Visitors / month (Mature Production)
* **Architecture:** Scale Web Servers to 2 x EC2 `t3.medium` behind an **AWS Application Load Balancer (ALB)**, combined with RDS `db.t3.medium` database.
* **Monthly Cost:** **$115.00**.

---

## 💡 Cost Saving Strategies (FinOps Tips)
1. **AWS EC2 Reserved Instances (RIs):** If you commit to keeping the instance for 1 Year, AWS discounts EC2 pricing by **30% to 40%**, reducing your `t3.micro` server cost to about **$4.80/month**.
2. **Standard S3 Lifecycle Rules:** Configure S3 to transition older backup/log files to Glacier Instant Retrieval after 90 days to reduce storage costs to a fraction of a cent.
