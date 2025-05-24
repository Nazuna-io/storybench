# Storybench Deployment Guide

This guide covers deploying Storybench Web UI for production use.

## Prerequisites

- Docker Engine 20.10+ and Docker Compose V2
- At least 4GB RAM and 10GB disk space
- Port 80 and 8000 available
- Valid API keys for LLM providers

## Quick Start with Docker

### 1. Clone and Configure

```bash
git clone <repository-url>
cd storybench
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` with your API keys:

```bash
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-key
```

### 3. Deploy with Docker Compose

```bash
# Production deployment
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f
```

### 4. Access the Application

- Web UI: http://localhost
- API Documentation: http://localhost/api/docs
- Health Check: http://localhost/api/health

## Manual Deployment

### Backend Setup

```bash
# Create virtual environment
python3.10 -m venv venv-storybench
source venv-storybench/bin/activate

# Install dependencies
pip install -r src/requirements-dev.txt
pip install -e .

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run backend
uvicorn storybench.web.main:app --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# Serve with nginx or any static server
# Point nginx to frontend/dist directory
```

## Production Considerations

### Security

1. **API Keys**: Store in secure environment variables
2. **HTTPS**: Use reverse proxy (nginx/Apache) with SSL
3. **Firewall**: Restrict access to necessary ports only
4. **Authentication**: Consider adding authentication layer

### Performance

1. **Resource Limits**: Configure Docker memory/CPU limits
2. **Load Balancing**: Use nginx for multiple instances
3. **Caching**: Enable HTTP caching for static assets
4. **Monitoring**: Set up health checks and logging

### Scaling

1. **Horizontal Scaling**: Run multiple backend instances
2. **Database**: Migrate to MongoDB for better concurrency
3. **Storage**: Use external storage for model files
4. **CDN**: Serve frontend assets via CDN

## Monitoring and Maintenance

### Health Checks

```bash
# Backend health
curl http://localhost:8000/api/health

# Frontend health
curl http://localhost/

# Container status
docker-compose ps
```

### Log Management

```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Log rotation (configure in production)
```

### Backup Strategy

```bash
# Backup configuration
tar -czf config-backup.tar.gz config/

# Backup results
tar -czf results-backup.tar.gz output/

# Database backup (when using MongoDB)
# mongodump --db storybench --out backup/
```

## Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check port usage
   netstat -tlnp | grep :80
   netstat -tlnp | grep :8000
   ```

2. **Permission Issues**
   ```bash
   # Fix file permissions
   chmod -R 755 config/
   chmod -R 777 output/
   ```

3. **Memory Issues**
   ```bash
   # Monitor resource usage
   docker stats
   ```

### Performance Tuning

1. **Frontend Build Optimization**
   ```bash
   cd frontend
   npm run build -- --mode production
   ```

2. **Backend Workers**
   ```bash
   # Run with multiple workers
   uvicorn storybench.web.main:app --workers 4
   ```

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `ANTHROPIC_API_KEY` | Anthropic API key | Required |
| `GOOGLE_API_KEY` | Google API key | Required |
| `ENVIRONMENT` | Environment mode | development |
| `DEBUG` | Debug mode | false |
| `LOG_LEVEL` | Logging level | INFO |
| `API_RATE_LIMIT` | Rate limit per hour | 100 |

## Support

For deployment issues:
1. Check the logs: `docker-compose logs`
2. Verify configuration: `docker-compose config`
3. Test connectivity: API health endpoints
4. Review resource usage: `docker stats`

## Updates

To update the deployment:

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```
