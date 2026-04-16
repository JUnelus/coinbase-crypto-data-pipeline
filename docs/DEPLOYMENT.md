# Deployment Guide

## Local Development

### Prerequisites
- Python 3.10+
- SQLite 3.8+
- Git

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/your-username/coinbase-crypto-data-pipeline.git
cd coinbase-crypto-data-pipeline
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your preferences (optional, defaults are sensible)
```

5. **Run the pipeline**
```bash
python main.py --products BTC-USD ETH-USD --stats --plot
```

## Docker Deployment

### Build Docker Image

```bash
docker build -t coinbase-crypto-pipeline:latest .
```

### Run with Docker

```bash
# Single run
docker run --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  coinbase-crypto-pipeline:latest

# With environment variables
docker run --rm \
  -e LOG_LEVEL=DEBUG \
  -e CRYPTO_PAIRS=BTC-USD,ETH-USD,SOL-USD \
  -v $(pwd)/data:/app/data \
  coinbase-crypto-pipeline:latest python main.py --products BTC-USD ETH-USD
```

### Docker Compose

```bash
# Start the service
docker-compose up -d

# View logs
docker-compose logs -f crypto-pipeline

# Stop the service
docker-compose down
```

## Scheduled Execution (Linux/macOS)

### Using Crontab

1. **Create shell script** (`run_pipeline.sh`):
```bash
#!/bin/bash
cd /path/to/coinbase-crypto-data-pipeline
source venv/bin/activate
python main.py --products BTC-USD ETH-USD SOL-USD --stats >> logs/cron.log 2>&1
```

2. **Make executable**:
```bash
chmod +x run_pipeline.sh
```

3. **Add to crontab**:
```bash
crontab -e

# Run every 5 minutes
*/5 * * * * /path/to/run_pipeline.sh

# Run every hour
0 * * * * /path/to/run_pipeline.sh

# Run at 2 AM daily
0 2 * * * /path/to/run_pipeline.sh
```

## Scheduled Execution (Windows)

### Using Task Scheduler

1. **Create batch file** (`run_pipeline.bat`):
```batch
@echo off
cd C:\Users\your-user\coinbase-crypto-data-pipeline
call venv\Scripts\activate
python main.py --products BTC-USD ETH-USD SOL-USD --stats
```

2. **Create scheduled task**:
   - Open Task Scheduler
   - Create Basic Task
   - Name: "Crypto Pipeline"
   - Trigger: Daily/Hourly (as desired)
   - Action: Start program → `C:\path\to\run_pipeline.bat`

## Cloud Deployment

### AWS EC2

1. **Launch EC2 instance** (Ubuntu 22.04):
```bash
# SSH into instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and git
sudo apt install -y python3.11 python3.11-venv git

# Clone repository
git clone https://github.com/your-username/coinbase-crypto-data-pipeline.git
cd coinbase-crypto-data-pipeline

# Setup
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run with nohup for background execution
nohup python main.py --products BTC-USD ETH-USD > logs/pipeline.log 2>&1 &
```

2. **Set up crontab** (see Linux section above)

### AWS Lambda (One-time execution)

```python
# lambda_handler.py
import subprocess
import os

def lambda_handler(event, context):
    result = subprocess.run(
        ["python", "main.py", "--products", "BTC-USD", "--stats"],
        cwd="/var/task",
        capture_output=True,
        text=True
    )
    return {
        "statusCode": 0 if result.returncode == 0 else 1,
        "body": result.stdout + result.stderr
    }
```

### Google Cloud Run

```bash
# Create Dockerfile optimized for Cloud Run
# Add to Dockerfile: EXPOSE 8080 (if needed for monitoring)

# Deploy
gcloud run deploy crypto-pipeline \
  --source . \
  --platform managed \
  --region us-central1 \
  --memory 512Mi \
  --timeout 3600 \
  --set-env-vars="ENV=production,LOG_LEVEL=INFO"
```

### Heroku

```bash
# Login
heroku login

# Create app
heroku create your-app-name

# Set environment variables
heroku config:set \
  ENV=production \
  LOG_LEVEL=INFO \
  CRYPTO_PAIRS=BTC-USD,ETH-USD

# Deploy
git push heroku main

# View logs
heroku logs --tail
```

## Kubernetes Deployment

### Helm Chart Structure
```
crypto-pipeline-chart/
├── Chart.yaml
├── values.yaml
├── templates/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── configmap.yaml
│   └── persistentvolumeclaim.yaml
```

### Deploy to Kubernetes

```bash
# Using manifests
kubectl apply -f k8s/

# Using Helm
helm install crypto-pipeline ./crypto-pipeline-chart \
  --set image.tag=latest \
  --set env.CRYPTO_PAIRS="BTC-USD,ETH-USD"

# Monitor
kubectl logs -f deployment/crypto-pipeline
```

## Monitoring & Maintenance

### Log Monitoring

```bash
# View logs
tail -f logs/crypto_pipeline.log

# Search for errors
grep ERROR logs/crypto_pipeline.log

# Count entries by level
grep -c INFO logs/crypto_pipeline.log
grep -c ERROR logs/crypto_pipeline.log
```

### Database Maintenance

```bash
# Check database size
ls -lh coinbase_data.db

# Optimize database
sqlite3 coinbase_data.db "VACUUM;"

# Analyze query performance
sqlite3 coinbase_data.db "ANALYZE;"

# Backup database
cp coinbase_data.db coinbase_data.db.backup.$(date +%s)
```

### Performance Tuning

1. **Increase fetch interval** in `.env`:
```
FETCH_INTERVAL=300  # 5 minutes instead of 1 minute
```

2. **Enable query caching**:
```
ENABLE_CACHE=true
CACHE_TTL=600
```

3. **Archive old data**:
```python
# Archive data older than 30 days
sqlite3 coinbase_data.db "
DELETE FROM prices 
WHERE time < datetime('now', '-30 days');
"
```

## Troubleshooting

### Common Issues

**Issue: "ModuleNotFoundError: No module named 'requests'"**
```bash
pip install -r requirements.txt
```

**Issue: "Database is locked"**
- Wait a few seconds and retry
- Check for other running instances
- Restart the service

**Issue: "API rate limit exceeded"**
- Increase `API_RETRY_DELAY` in config
- Reduce `CRYPTO_PAIRS` being fetched
- Increase `FETCH_INTERVAL`

**Issue: "Certificate verification failed"**
```bash
# On macOS
/Applications/Python\ 3.11/Install\ Certificates.command

# Or disable SSL verification (not recommended)
export PYTHONHTTPSVERIFY=0
```

### Health Checks

```bash
# Verify database integrity
sqlite3 coinbase_data.db "PRAGMA integrity_check;"

# Test API connectivity
python -c "from scripts.extract import fetch_coinbase_ticker; print(fetch_coinbase_ticker('BTC-USD')['price'])"

# Check log files
tail -20 logs/crypto_pipeline.log
```

## Backup & Recovery

### Automated Backup

Create backup script:
```bash
#!/bin/bash
BACKUP_DIR="/path/to/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
cp coinbase_data.db $BACKUP_DIR/coinbase_data.db.$TIMESTAMP

# Keep only last 30 days
find $BACKUP_DIR -name "*.db.*" -mtime +30 -delete
```

### Restore from Backup

```bash
# List backups
ls -l /path/to/backups/

# Restore specific backup
cp /path/to/backups/coinbase_data.db.20260415_120000 coinbase_data.db
```

## Updating

### Update Dependencies

```bash
# Check for updates
pip list --outdated

# Update requirements
pip install --upgrade -r requirements.txt

# Test after update
pytest tests/

# Commit changes
git add requirements.txt
git commit -m "chore: update dependencies"
```

### Update Code

```bash
git pull origin main
python main.py --products BTC-USD --stats
```

