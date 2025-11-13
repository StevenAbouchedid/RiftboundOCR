# DigitalOcean Droplet Deployment Guide

## Why DigitalOcean for OCR?

- ✅ **Best price/performance ratio** ($12/month for dedicated CPU)
- ✅ **Dedicated CPU** (not shared - consistent performance)
- ✅ **Full control** (SSH access, install anything)
- ✅ **Simple pricing** (no surprise costs)
- ✅ **Reliable** (99.99% uptime SLA)
- ✅ **Easy to scale** (upgrade anytime)

**Expected Performance:**
- OCR processing: **15-30 seconds** (much faster than Railway!)
- Consistent speed (dedicated resources)

**Cost:**
- Basic: $6/month (1 CPU, 1GB RAM) - Too small for OCR
- **Regular: $12/month (1 CPU, 2GB RAM)** ← **Recommended**
- CPU-Optimized: $24/month (2 CPU, 4GB RAM) - For heavy load

---

## Prerequisites

- DigitalOcean account (get $200 credit: https://try.digitalocean.com/freetrialoffer/)
- Domain name (optional but recommended)
- SSH key pair (we'll create one)

---

## Step 1: Create a Droplet

### 1.1 Sign Up for DigitalOcean

Go to: https://www.digitalocean.com/
- Sign up for free
- Get **$200 credit** for 60 days!

### 1.2 Create SSH Key

On your local machine:

```bash
# Generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "your-email@example.com"

# Display public key (copy this)
cat ~/.ssh/id_ed25519.pub
```

### 1.3 Create the Droplet

**Via Web Console:**

1. Go to: https://cloud.digitalocean.com/droplets/new
2. Choose:
   - **Image**: Docker on Ubuntu 22.04
   - **Plan**: Regular - $12/month (1 CPU, 2GB RAM, 50GB SSD)
   - **Datacenter**: Choose closest to your users (e.g., New York, San Francisco)
   - **Authentication**: SSH Key (paste your public key)
   - **Hostname**: riftbound-ocr
   - **Tags**: production, ocr

3. Click **Create Droplet**

**OR via CLI (doctl):**

```bash
# Install doctl
brew install doctl  # macOS
# or: snap install doctl  # Linux

# Authenticate
doctl auth init

# Create droplet
doctl compute droplet create riftbound-ocr \
  --image docker-20-04 \
  --size s-1vcpu-2gb \
  --region nyc1 \
  --ssh-keys YOUR_SSH_KEY_ID \
  --tag-names production,ocr
```

### 1.4 Get Droplet IP Address

```bash
# Via CLI
doctl compute droplet list

# Or check email/web console
```

Note your droplet's IP address (e.g., `123.45.67.89`)

---

## Step 2: Initial Server Setup

### 2.1 SSH Into Your Droplet

```bash
ssh root@YOUR_DROPLET_IP
```

### 2.2 Update System

```bash
# Update package list
apt update

# Upgrade packages
apt upgrade -y

# Install essentials
apt install -y curl git vim ufw
```

### 2.3 Set Up Firewall

```bash
# Allow SSH
ufw allow OpenSSH

# Allow HTTP and HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Enable firewall
ufw enable

# Check status
ufw status
```

### 2.4 Create Non-Root User (Optional but Recommended)

```bash
# Create user
adduser ocr - password is password

# Add to sudo group
usermod -aG sudo ocr

# Add to docker group
usermod -aG docker ocr

# Copy SSH keys
rsync --archive --chown=ocr:ocr ~/.ssh /home/ocr

# Switch to new user
su - ocr
```

---

## Step 3: Deploy Your Application

### 3.1 Clone Your Repository

```bash
# Create app directory
cd ~
mkdir -p apps
cd apps

# Clone your repo
git clone https://github.com/YOUR_USERNAME/RiftboundOCR.git
cd RiftboundOCR
```

### 3.2 Set Up Environment Variables

```bash
# Create .env file
cat > .env << EOF
PORT=8080
USE_GPU=false
PYTHONUNBUFFERED=1
TQDM_DISABLE=1
EOF
```

### 3.3 Build and Run with Docker

```bash
# Build the image
docker build -t riftbound-ocr:latest .

# Run the container
docker run -d \
  --name riftbound-ocr \
  --restart unless-stopped \
  -p 8080:8080 \
  --env-file .env \
  -v $(pwd)/resources:/app/resources:ro \
  riftbound-ocr:latest

# Check if it's running
docker ps

# Check logs
docker logs -f riftbound-ocr
```

### 3.4 Test the Service

```bash
# Test health endpoint
curl http://localhost:8080/health

# Should return:
# {"status":"healthy","service":"RiftboundOCR Service",...}
```

---

## Step 4: Set Up Nginx Reverse Proxy

### 4.1 Install Nginx

```bash
sudo apt install -y nginx
```

### 4.2 Configure Nginx

```bash
# Create nginx config
sudo nano /etc/nginx/sites-available/riftbound-ocr
```

Paste this configuration:

```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;

    # Increase timeouts for OCR processing
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;
    send_timeout 300s;

    # Increase max upload size for images
    client_max_body_size 20M;

    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        
        # Headers for streaming
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Disable buffering for SSE streaming
        proxy_buffering off;
        proxy_cache off;
    }
}
```

### 4.3 Enable the Site

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/riftbound-ocr /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test nginx config
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx

# Enable nginx on boot
sudo systemctl enable nginx
```

### 4.4 Test External Access

```bash
# From your local machine
curl http://YOUR_DROPLET_IP/health
curl http://104.248.221.40/health
```

---

## Step 5: Set Up SSL Certificate (HTTPS)

### 5.1 Point Your Domain to Droplet

If you have a domain:
1. Go to your domain registrar (e.g., Namecheap, GoDaddy)
2. Add an A record:
   - Host: `@` or subdomain (e.g., `ocr`)
   - Value: Your droplet IP
   - TTL: 300

Wait 5-10 minutes for DNS to propagate.

Test:
```bash
dig YOUR_DOMAIN
# Should show your droplet IP
```

### 5.2 Install Certbot

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx
```

### 5.3 Get SSL Certificate

```bash
# Get certificate (nginx plugin handles everything)
sudo certbot --nginx -d YOUR_DOMAIN

# Follow prompts:
# - Enter email
# - Agree to terms
# - Redirect HTTP to HTTPS: Yes (recommended)
```

### 5.4 Test Auto-Renewal

```bash
# Test renewal (dry run)
sudo certbot renew --dry-run

# Certbot auto-renews via cron/systemd timer
```

Now your service is available at: `https://YOUR_DOMAIN`

---

## Step 6: Set Up Auto-Deployment

### Option A: Deploy Script (Simple)

Create `~/deploy.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Deploying RiftboundOCR..."

# Navigate to app directory
cd ~/apps/RiftboundOCR

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Rebuild Docker image
echo "🔨 Building Docker image..."
docker build -t riftbound-ocr:latest .

# Stop and remove old container
echo "🛑 Stopping old container..."
docker stop riftbound-ocr || true
docker rm riftbound-ocr || true

# Start new container
echo "▶️  Starting new container..."
docker run -d \
  --name riftbound-ocr \
  --restart unless-stopped \
  -p 8080:8080 \
  --env-file .env \
  -v $(pwd)/resources:/app/resources:ro \
  riftbound-ocr:latest

# Wait for service to start
echo "⏳ Waiting for service to start..."
sleep 10

# Health check
echo "🏥 Health check..."
if curl -f http://localhost:8080/health; then
    echo "✅ Deployment successful!"
else
    echo "❌ Deployment failed! Check logs:"
    docker logs riftbound-ocr
    exit 1
fi

# Clean up old images
echo "🧹 Cleaning up old images..."
docker image prune -f

echo "🎉 Deployment complete!"
```

Make it executable:

```bash
chmod +x ~/deploy.sh
```

Deploy:

```bash
./deploy.sh
```

### Option B: GitHub Actions Auto-Deploy

Create `.github/workflows/deploy-digitalocean.yml`:

```yaml
name: Deploy to DigitalOcean

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Deploy to Droplet
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.DROPLET_IP }}
        username: ${{ secrets.DROPLET_USER }}
        key: ${{ secrets.DROPLET_SSH_KEY }}
        script: |
          cd ~/apps/RiftboundOCR
          git pull origin main
          docker build -t riftbound-ocr:latest .
          docker stop riftbound-ocr || true
          docker rm riftbound-ocr || true
          docker run -d \
            --name riftbound-ocr \
            --restart unless-stopped \
            -p 8080:8080 \
            --env-file .env \
            -v $(pwd)/resources:/app/resources:ro \
            riftbound-ocr:latest
          docker image prune -f
```

**Set up GitHub secrets:**
1. Go to GitHub repo → Settings → Secrets and variables → Actions
2. Add secrets:
   - `DROPLET_IP`: Your droplet IP
   - `DROPLET_USER`: `root` or `ocr`
   - `DROPLET_SSH_KEY`: Your private SSH key

Now every push to `main` auto-deploys!

### Option C: Webhook (Advanced)

Set up a webhook listener that deploys when you push to GitHub.

Install webhook:

```bash
sudo apt install -y webhook
```

Create `~/webhook.json`:

```json
[
  {
    "id": "deploy-ocr",
    "execute-command": "/home/ocr/deploy.sh",
    "command-working-directory": "/home/ocr/apps/RiftboundOCR",
    "response-message": "Deploying...",
    "trigger-rule": {
      "match": {
        "type": "payload-hash-sha256",
        "secret": "YOUR_WEBHOOK_SECRET",
        "parameter": {
          "source": "header",
          "name": "X-Hub-Signature-256"
        }
      }
    }
  }
]
```

Run webhook:

```bash
webhook -hooks webhook.json -verbose -port 9000
```

Set up as systemd service (see full guide for details).

---

## Step 7: Monitoring and Maintenance

### 7.1 View Logs

```bash
# Docker logs
docker logs -f riftbound-ocr

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 7.2 Monitor Resources

```bash
# CPU and memory
htop

# Docker stats
docker stats riftbound-ocr

# Disk usage
df -h
```

### 7.3 Set Up Monitoring (Optional)

Install Netdata for real-time monitoring:

```bash
# Install Netdata
bash <(curl -Ss https://my-netdata.io/kickstart.sh)

# Access at: http://YOUR_DROPLET_IP:19999
```

### 7.4 Automated Backups

```bash
# Backup script
cat > ~/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=~/backups

mkdir -p $BACKUP_DIR

# Backup resources
tar -czf $BACKUP_DIR/resources_$DATE.tar.gz ~/apps/RiftboundOCR/resources

# Backup Docker image
docker save riftbound-ocr:latest | gzip > $BACKUP_DIR/docker_image_$DATE.tar.gz

# Keep only last 7 backups
ls -t $BACKUP_DIR/*.tar.gz | tail -n +8 | xargs rm -f

echo "Backup completed: $DATE"
EOF

chmod +x ~/backup.sh

# Add to crontab (run daily at 2am)
(crontab -l 2>/dev/null; echo "0 2 * * * /home/ocr/backup.sh") | crontab -
```

---

## Step 8: Performance Optimization

### 8.1 Optimize Docker

```bash
# Limit Docker logs
docker update \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  riftbound-ocr

# Restart policy
docker update --restart unless-stopped riftbound-ocr
```

### 8.2 Optimize Nginx

Edit `/etc/nginx/nginx.conf`:

```nginx
http {
    # Connection optimization
    keepalive_timeout 65;
    keepalive_requests 100;
    
    # Compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript
               application/json application/javascript application/xml+rss;
    
    # File upload
    client_max_body_size 20M;
    client_body_buffer_size 128k;
    
    # Timeouts for OCR
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
    proxy_read_timeout 300;
}
```

Restart nginx:

```bash
sudo systemctl restart nginx
```

### 8.3 Enable Swap (For Memory Safety)

```bash
# Create 2GB swap file
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Verify
free -h
```

---

## Step 9: Scaling Up (When Needed)

### Option 1: Resize Droplet

```bash
# Via CLI
doctl compute droplet-action resize DROPLET_ID \
  --size s-2vcpu-4gb \
  --resize-disk

# Via web: Droplet → Resize → Choose plan → Resize
```

**Available sizes:**
- s-1vcpu-2gb: $12/month (current)
- s-2vcpu-2gb: $18/month (+1 CPU)
- s-2vcpu-4gb: $24/month (+1 CPU, +2GB RAM)
- c-2: $42/month (CPU-optimized, 2 vCPU, 4GB)

### Option 2: Load Balancer (Multiple Droplets)

For high traffic:
1. Create multiple OCR droplets
2. Set up DigitalOcean Load Balancer
3. Distribute traffic across droplets

---

## Troubleshooting

### Service Won't Start

```bash
# Check Docker logs
docker logs riftbound-ocr

# Check if port is in use
sudo netstat -tlnp | grep 8080

# Restart Docker
sudo systemctl restart docker
```

### Can't Connect Externally

```bash
# Check firewall
sudo ufw status

# Check nginx
sudo nginx -t
sudo systemctl status nginx

# Check if service is listening
curl http://localhost:8080/health
```

### Out of Memory

```bash
# Check memory usage
free -h
docker stats

# Add swap (see Step 8.3)
# Or upgrade droplet
```

### Slow Performance

```bash
# Check CPU usage
htop

# Check Docker stats
docker stats riftbound-ocr

# Might need to upgrade droplet
```

---

## Cost Comparison

| Service | Monthly Cost | OCR Speed | Notes |
|---------|-------------|-----------|-------|
| **Railway** | $10-20 | 5+ min ❌ | Shared CPU |
| **DigitalOcean** | $12 | **15-30s** ✅ | Dedicated CPU |
| GCP Cloud Run | $15-25 | 30-60s | Auto-scaling |
| GCP + GPU | $20-30 | 5-15s 🚀 | Best speed |

**DigitalOcean wins on:**
- ✅ Best price/performance ($12/month)
- ✅ Predictable costs
- ✅ Dedicated resources
- ✅ Full control
- ✅ Simple scaling

---

## Quick Reference Commands

```bash
# Deploy new version
cd ~/apps/RiftboundOCR && ./deploy.sh

# View logs
docker logs -f riftbound-ocr

# Restart service
docker restart riftbound-ocr

# Check status
docker ps
curl http://localhost:8080/health

# Monitor resources
docker stats riftbound-ocr

# Update system
sudo apt update && sudo apt upgrade -y

# Restart nginx
sudo systemctl restart nginx
```

---

## Next Steps

1. ✅ Create DigitalOcean droplet ($12/month)
2. ✅ Follow setup steps above
3. ✅ Deploy your OCR service
4. ✅ Set up SSL with Let's Encrypt
5. ✅ Configure auto-deployment
6. ✅ Test with your frontend
7. 🎉 Enjoy **15-30 second OCR** instead of 5+ minutes!

---

## Support

- DigitalOcean Docs: https://docs.digitalocean.com/
- Community: https://www.digitalocean.com/community
- Support: https://www.digitalocean.com/support

Good luck with your deployment! 🚀


