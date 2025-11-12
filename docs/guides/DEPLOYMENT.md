# Deployment Guide - RiftboundOCR Service

Complete guide for deploying the OCR service in production.

---

## 🚀 Quick Deploy with Docker

### Prerequisites

- Docker installed (20.10+)
- Docker Compose installed (2.0+)
- 4GB+ RAM available
- 10GB+ disk space (for models)

### One-Command Deploy

```bash
# 1. Configure environment (optional)
cp env.example .env
# Edit .env with your settings

# 2. Start service
docker-compose up -d

# 3. Check logs
docker-compose logs -f

# 4. Test health
curl http://localhost:8002/api/v1/health
```

**That's it!** Service is running at `http://localhost:8002`

---

## 📦 Docker Deployment (Recommended)

### Build & Run

```bash
# Build image
docker build -t riftbound-ocr:latest .

# Run container
docker run -d \
  --name riftbound-ocr \
  -p 8002:8002 \
  -v ocr-models:/root/.paddlex \
  -v ocr-easyocr:/root/.EasyOCR \
  riftbound-ocr:latest

# Check logs
docker logs -f riftbound-ocr
```

### Docker Compose (Production)

```yaml
# docker-compose.yml
version: '3.8'

services:
  ocr-service:
    image: riftbound-ocr:latest
    ports:
      - "8002:8002"
    environment:
      - SERVICE_PORT=8002
      - MAIN_API_URL=https://your-api.com/api
      - MAIN_API_KEY=your-secret-key
    volumes:
      - ocr-models:/root/.paddlex
      - ocr-easyocr:/root/.EasyOCR
    restart: unless-stopped
```

---

## 💻 Manual Deployment (VPS/Server)

### System Requirements

- Ubuntu 20.04+ / Debian 11+ / RHEL 8+
- Python 3.10+
- 4GB RAM minimum (8GB recommended)
- 10GB disk space
- 2+ CPU cores

### Installation Steps

#### 1. Install System Dependencies

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    python3.10 \
    python3.10-venv \
    python3-pip \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1

# RHEL/CentOS
sudo yum install -y \
    python3.10 \
    python3-pip \
    mesa-libGL \
    glib2 \
    libSM \
    libXext \
    libXrender
```

#### 2. Create Service User

```bash
sudo useradd -m -s /bin/bash riftbound-ocr
sudo su - riftbound-ocr
```

#### 3. Deploy Application

```bash
# Clone/copy application files
cd /home/riftbound-ocr
# (copy your RiftboundOCR directory here)

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Configure environment
cp env.example .env
nano .env  # Edit configuration
```

#### 4. Create Systemd Service

```bash
sudo nano /etc/systemd/system/riftbound-ocr.service
```

```ini
[Unit]
Description=RiftboundOCR Service
After=network.target

[Service]
Type=simple
User=riftbound-ocr
WorkingDirectory=/home/riftbound-ocr/RiftboundOCR
Environment="PATH=/home/riftbound-ocr/RiftboundOCR/venv/bin"
ExecStart=/home/riftbound-ocr/RiftboundOCR/venv/bin/python -m uvicorn src.main:app --host 0.0.0.0 --port 8002
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 5. Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable riftbound-ocr
sudo systemctl start riftbound-ocr

# Check status
sudo systemctl status riftbound-ocr

# View logs
sudo journalctl -u riftbound-ocr -f
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Service (port 8002 to avoid conflict with main API)
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8002
DEBUG=false

# OCR
USE_GPU=false
ENABLE_LOGGING=true

# Main API Integration
MAIN_API_URL=https://your-riftbound-api.com/api
MAIN_API_KEY=your-secret-key

# Limits
MAX_FILE_SIZE_MB=10
MAX_BATCH_SIZE=10
```

### Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/riftbound-ocr
server {
    listen 80;
    server_name ocr.yourdomain.com;

    client_max_body_size 20M;

    location / {
        proxy_pass http://localhost:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout for OCR processing
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
    }
}
```

Enable and restart:

```bash
sudo ln -s /etc/nginx/sites-available/riftbound-ocr /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL with Certbot

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d ocr.yourdomain.com
```

---

## 📊 Monitoring

### Health Checks

```bash
# Health endpoint
curl http://localhost:8002/api/v1/health

# Expected response
{
  "status": "healthy",
  "service": "RiftboundOCR Service",
  "version": "1.0.0",
  "matcher_loaded": true,
  "total_cards_in_db": 399
}
```

### Logs

```bash
# Docker
docker logs -f riftbound-ocr

# Systemd
sudo journalctl -u riftbound-ocr -f

# Application logs (if configured)
tail -f logs/app.log
```

### Metrics (Optional - Add Later)

Consider adding:
- Prometheus metrics
- Grafana dashboards
- APM (Application Performance Monitoring)
- Error tracking (Sentry)

---

## 🔄 Scaling

### Horizontal Scaling

Run multiple instances behind a load balancer:

```yaml
# docker-compose.scale.yml
version: '3.8'

services:
  ocr-service:
    image: riftbound-ocr:latest
    deploy:
      replicas: 3
    # ... rest of config
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - ocr-service
```

### Vertical Scaling

Increase resources in docker-compose.yml:

```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'
      memory: 8G
```

### Queue-Based Processing (Future)

For high load, consider adding:
- Redis for job queue
- Celery workers
- Result storage

---

## 🔒 Security

### Firewall

```bash
# Allow only HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### API Key Authentication

Add to .env:

```bash
MAIN_API_KEY=your-very-secret-key-here
```

Use in requests:

```bash
curl -H "X-API-Key: your-very-secret-key-here" \
  http://localhost:8002/api/v1/process-and-save \
  -F "file=@decklist.jpg"
```

### Rate Limiting

Add rate limiting with Nginx:

```nginx
limit_req_zone $binary_remote_addr zone=ocr_limit:10m rate=10r/m;

location /api/v1/process {
    limit_req zone=ocr_limit burst=5;
    # ... proxy settings
}
```

---

## 🐛 Troubleshooting

### Service Won't Start

```bash
# Check logs
docker logs riftbound-ocr
sudo journalctl -u riftbound-ocr -n 100

# Common issues:
# 1. Port already in use
sudo lsof -i :8002

# 2. Permissions
sudo chown -R riftbound-ocr:riftbound-ocr /home/riftbound-ocr

# 3. Missing dependencies
pip install -r requirements.txt
```

### OCR Models Not Downloading

```bash
# Manually download models
python -c "from paddleocr import PaddleOCR; PaddleOCR()"
python -c "import easyocr; easyocr.Reader(['en'])"
```

### Out of Memory

```bash
# Check memory usage
free -h

# Increase swap (temporary fix)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Low Accuracy

```bash
# Validate accuracy
python tests/validate_accuracy.py

# Check card mappings
ls -lh resources/card_mappings_final.csv

# Update card mappings if needed
# ... add new cards to CSV
```

---

## 📈 Performance Optimization

### Model Caching

Ensure models are cached in Docker volumes:

```yaml
volumes:
  - ocr-paddleocr:/root/.paddlex
  - ocr-easyocr:/root/.EasyOCR
```

### GPU Acceleration

If you have NVIDIA GPU:

```yaml
services:
  ocr-service:
    # ... other config
    environment:
      - USE_GPU=true
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

### Gunicorn for Production

```bash
# Install gunicorn
pip install gunicorn

# Run with workers
gunicorn src.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8002 \
  --timeout 120
```

---

## ✅ Deployment Checklist

### Pre-Deployment

- [ ] Test locally with `python src/main.py`
- [ ] Run test suite: `python run_tests.py`
- [ ] Validate accuracy: `python tests/validate_accuracy.py`
- [ ] Configure environment variables
- [ ] Update card mappings if needed

### Deployment

- [ ] Build Docker image
- [ ] Configure docker-compose.yml
- [ ] Set up volumes for model caching
- [ ] Configure Nginx reverse proxy
- [ ] Set up SSL certificate
- [ ] Configure firewall

### Post-Deployment

- [ ] Test health endpoint
- [ ] Process test image
- [ ] Check logs for errors
- [ ] Monitor resource usage
- [ ] Set up monitoring/alerts

---

## 📞 Support

For deployment issues:
1. Check logs first
2. Review troubleshooting section
3. Verify all dependencies installed
4. Check GitHub issues/documentation

---

**Deployment Status:** ✅ Production Ready


