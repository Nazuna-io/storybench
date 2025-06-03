
# Backup configuration files
tar -czf $BACKUP_DIR/config_backup_$DATE.tar.gz \
  config/ \
  .env.production \
  docker-compose.yml \
  docker/

echo "Configuration backup completed: config_backup_$DATE.tar.gz"
```

### Automated Backup Schedule

```bash
# Add to crontab
crontab -e

# Daily database backup at 2 AM
0 2 * * * /opt/storybench/scripts/backup_mongodb.sh

# Weekly config backup on Sundays at 3 AM
0 3 * * 0 /opt/storybench/scripts/backup_config.sh
```

### Recovery Procedures

```bash
#!/bin/bash
# restore_mongodb.sh

BACKUP_FILE=$1
if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    exit 1
fi

# Extract backup
tar -xzf $BACKUP_FILE

# Restore to MongoDB
mongorestore --uri="$MONGODB_URI" --drop backup_*/

echo "Restore completed from $BACKUP_FILE"
```

## Performance Optimization

### Scaling Strategies

#### Horizontal Scaling

```yaml
# docker-compose.scale.yml
version: '3.8'

services:
  dashboard:
    # ... base configuration
    deploy:
      replicas: 3
      
  backend:
    # ... base configuration  
    deploy:
      replicas: 2
      
  nginx:
    # ... load balancer configuration
    volumes:
      - ./docker/nginx-lb.conf:/etc/nginx/nginx.conf:ro
```

#### Load Balancer Configuration

```nginx
# nginx-lb.conf
upstream dashboard_cluster {
    least_conn;
    server dashboard_1:8501;
    server dashboard_2:8501;
    server dashboard_3:8501;
}

upstream backend_cluster {
    least_conn;
    server backend_1:8000;
    server backend_2:8000;
}

server {
    listen 443 ssl http2;
    
    location / {
        proxy_pass http://dashboard_cluster;
        # ... other proxy settings
    }
    
    location /api/ {
        proxy_pass http://backend_cluster;
        # ... other proxy settings
    }
}
```

### Database Optimization

```javascript
// MongoDB indexes for performance
db.responses.createIndex({ "model_name": 1, "created_at": -1 });
db.responses.createIndex({ "sequence_name": 1, "prompt_name": 1 });
db.response_llm_evaluations.createIndex({ "response_id": 1 });
db.response_llm_evaluations.createIndex({ "created_at": -1 });

// Compound indexes for dashboard queries
db.responses.createIndex({ 
    "model_name": 1, 
    "sequence_name": 1, 
    "created_at": -1 
});
```

### Caching Strategy

```python
# Redis caching for dashboard
import redis
import json
from functools import wraps

redis_client = redis.Redis(host='redis', port=6379, db=0)

def cache_result(expiration=300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, expiration, json.dumps(result))
            return result
        return wrapper
    return decorator

# Usage in dashboard
@cache_result(expiration=600)  # Cache for 10 minutes
def get_model_rankings():
    # Expensive database query
    return calculate_rankings()
```

## Cloud Deployment

### AWS Deployment

#### ECS with Fargate

```yaml
# ecs-task-definition.json
{
  "family": "storybench-prod",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "dashboard",
      "image": "your-registry/storybench-dashboard:latest",
      "portMappings": [
        {
          "containerPort": 8501,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "MONGODB_URI",
          "value": "mongodb+srv://..."
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/storybench",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### Application Load Balancer

```bash
# Create ALB
aws elbv2 create-load-balancer \
  --name storybench-alb \
  --subnets subnet-12345 subnet-67890 \
  --security-groups sg-12345

# Create target group
aws elbv2 create-target-group \
  --name storybench-targets \
  --protocol HTTP \
  --port 8501 \
  --vpc-id vpc-12345 \
  --health-check-path /
```

### Google Cloud Deployment

#### Cloud Run

```yaml
# cloudrun.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: storybench-dashboard
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "10"
        run.googleapis.com/cpu-throttling: "false"
    spec:
      containerConcurrency: 80
      containers:
      - image: gcr.io/project-id/storybench-dashboard:latest
        ports:
        - containerPort: 8501
        env:
        - name: MONGODB_URI
          valueFrom:
            secretKeyRef:
              name: mongodb-secret
              key: uri
        resources:
          limits:
            cpu: 2000m
            memory: 4Gi
```

#### Deployment Script

```bash
#!/bin/bash
# deploy-gcp.sh

PROJECT_ID="your-project-id"
SERVICE_NAME="storybench-dashboard"
REGION="us-central1"

# Build and push image
docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME:latest .
docker push gcr.io/$PROJECT_ID/$SERVICE_NAME:latest

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8501 \
  --memory 4Gi \
  --cpu 2 \
  --max-instances 10
```

## Maintenance

### Update Procedures

```bash
#!/bin/bash
# update_storybench.sh

echo "Starting StoryBench update..."

# 1. Backup current deployment
./scripts/backup_config.sh
./scripts/backup_mongodb.sh

# 2. Pull latest changes
git fetch origin
git checkout v1.5.1  # or latest version

# 3. Update dependencies
source venv-storybench/bin/activate
pip install -r requirements.txt
pip install -r streamlit_dashboard/requirements.txt

# 4. Update Docker images
docker-compose build --no-cache

# 5. Rolling update
docker-compose up -d --no-deps dashboard
sleep 30
docker-compose up -d --no-deps backend

# 6. Verify deployment
curl -f http://localhost:8501/ || exit 1
curl -f http://localhost:8000/api/health || exit 1

echo "Update completed successfully!"
```

### Health Monitoring

```python
# health_monitor.py
import requests
import time
import logging
from datetime import datetime

def check_services():
    services = [
        {"name": "Dashboard", "url": "http://localhost:8501/"},
        {"name": "Backend", "url": "http://localhost:8000/api/health"}
    ]
    
    for service in services:
        try:
            response = requests.get(service["url"], timeout=10)
            if response.status_code == 200:
                logging.info(f"{service['name']} is healthy")
            else:
                logging.error(f"{service['name']} returned {response.status_code}")
        except Exception as e:
            logging.error(f"{service['name']} check failed: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    while True:
        check_services()
        time.sleep(60)  # Check every minute
```

### Automated Alerts

```python
# alerts.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_alert(subject, message):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "alerts@yourdomain.com"
    sender_password = "app_password"
    recipient_email = "admin@yourdomain.com"
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = f"StoryBench Alert: {subject}"
    
    msg.attach(MIMEText(message, 'plain'))
    
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(sender_email, sender_password)
    server.send_message(msg)
    server.quit()

# Usage
def check_disk_space():
    import shutil
    _, _, free = shutil.disk_usage("/")
    free_gb = free // (1024**3)
    
    if free_gb < 5:  # Less than 5GB free
        send_alert(
            "Low Disk Space",
            f"Server has only {free_gb}GB free space remaining"
        )
```

## Security Hardening

### Container Security

```dockerfile
# Secure Dockerfile practices
FROM python:3.10-slim

# Create non-root user
RUN groupadd -r storybench && useradd -r -g storybench storybench

# Install security updates
RUN apt-get update && apt-get upgrade -y && apt-get clean

# Copy files with proper ownership
COPY --chown=storybench:storybench . /app

# Switch to non-root user
USER storybench

# Run application
CMD ["streamlit", "run", "app.py"]
```

### Network Security

```yaml
# docker-compose.security.yml
version: '3.8'

services:
  dashboard:
    # ... other config
    networks:
      - frontend
    expose:
      - "8501"
    # Don't expose ports directly to host

  backend:
    # ... other config
    networks:
      - frontend
      - backend
    expose:
      - "8000"

  database:
    networks:
      - backend
    # Only accessible from backend

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # No external access
```

### Environment Secrets

```bash
# Use Docker secrets
echo "your_mongodb_uri" | docker secret create mongodb_uri -
echo "your_api_key" | docker secret create openai_key -

# Reference in compose file
version: '3.8'
services:
  dashboard:
    secrets:
      - mongodb_uri
      - openai_key
    environment:
      - MONGODB_URI_FILE=/run/secrets/mongodb_uri
      - OPENAI_API_KEY_FILE=/run/secrets/openai_key

secrets:
  mongodb_uri:
    external: true
  openai_key:
    external: true
```

## Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check logs
docker-compose logs dashboard

# Check resource usage
docker stats

# Verify environment variables
docker-compose config
```

#### Database Connection Issues
```bash
# Test MongoDB connection
docker exec -it storybench-dashboard-prod python -c "
from pymongo import MongoClient
import os
client = MongoClient(os.getenv('MONGODB_URI'))
print(client.admin.command('ping'))
"
```

#### SSL Certificate Issues
```bash
# Check certificate validity
openssl x509 -in docker/ssl/storybench.crt -text -noout

# Test SSL connection
curl -I https://yourdomain.com
```

### Performance Issues

#### High Memory Usage
```bash
# Monitor container memory
docker stats --no-stream

# Optimize Streamlit memory
export STREAMLIT_SERVER_MAX_MESSAGE_SIZE=200
export STREAMLIT_SERVER_MAX_UPLOAD_SIZE=200
```

#### Slow Database Queries
```javascript
// Enable MongoDB profiling
db.setProfilingLevel(2)

// Check slow queries
db.system.profile.find().sort({ts: -1}).limit(5)

// Add indexes for slow queries
db.responses.createIndex({"created_at": -1})
```

## Production Checklist

### Pre-Deployment
- [ ] All environment variables configured
- [ ] SSL certificates installed and valid
- [ ] Database backups automated
- [ ] Health checks implemented
- [ ] Monitoring and alerting configured
- [ ] Security hardening applied
- [ ] Load testing completed

### Post-Deployment
- [ ] All services responding correctly
- [ ] Health checks passing
- [ ] Logs being generated properly
- [ ] Backups working
- [ ] Monitoring alerts functioning
- [ ] SSL certificate auto-renewal configured
- [ ] Documentation updated

### Ongoing Maintenance
- [ ] Regular security updates
- [ ] Database optimization
- [ ] Log rotation configured
- [ ] Backup restoration tested
- [ ] Performance monitoring
- [ ] Capacity planning reviews

---

This deployment guide provides comprehensive coverage for production deployment of StoryBench v1.5. For additional support, consult the troubleshooting guide and API documentation.
