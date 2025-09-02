# 🐳 Docker & Railway Deployment Guide for Dubai MVP

## 📋 Overview

This guide explains how to:
1. **Run the project locally using Docker** for development
2. **Deploy to Railway** for production

## 🚀 Local Development with Docker

### Prerequisites

- Docker Desktop installed and running
- PowerShell (Windows) or Bash (Linux/Mac)

### Quick Start

1. **Start local development environment:**
   ```powershell
   .\start-local.ps1
   ```

2. **Or manually:**
   ```bash
   docker-compose -f docker-compose.local.yml up --build -d
   ```

### Services Available Locally

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | React application |
| Backend API | http://localhost:8000 | Django REST API (health: `/api/health/`) |
| Nginx (optional) | http://localhost:8080 | Production-like proxy |
| Django Admin | http://localhost:8000/admin/ | Django administration |
| Health Check | http://localhost:8000/health/ | Service health status |

### Useful Commands

```bash
# View logs
docker-compose -f docker-compose.local.yml logs -f

# Stop services
docker-compose -f docker-compose.local.yml down

# Restart services
docker-compose -f docker-compose.local.yml restart

# Access Django shell
docker exec -it dubai-django-local python manage.py shell

# Run migrations
docker exec -it dubai-django-local python manage.py migrate

# Create superuser
docker exec -it dubai-django-local python manage.py createsuperuser
```

## 🌐 Railway Deployment

### Prerequisites

- Railway CLI installed: `npm install -g @railway/cli`
- Railway account and project created
- Logged in: `railway login`

### Deployment Steps

1. **Deploy using script:**
   ```powershell
   .\deploy-railway.ps1
   ```

2. **Or manually:**
   ```bash
   # Check status
   railway status
   
   # Deploy
   railway up
   
   # View logs
   railway logs -f
   ```

### Railway Configuration

The project includes:
- `railway.json` - Railway-specific configuration
- `Dockerfile.railway` - Production-optimized Docker image
- `apps/realty-main/requirements.txt` - Production dependencies

### Environment Variables

Set these in Railway dashboard:
- `DATABASE_URL` - PostgreSQL connection string
- `DEBUG` - Set to `False` for production
- `DJANGO_ALLOWED_HOSTS` - Include your Railway domain
- `SECRET_KEY` - Django secret key

## 🔧 Configuration Files

### Docker Files

| File | Purpose |
|------|---------|
| `Dockerfile.local` | Local development with hot reload |
| `Dockerfile.railway` | Production deployment to Railway |
| `docker-compose.local.yml` | Local services orchestration |
| `.dockerignore` | Optimize Docker builds |

### Requirements Files

| File | Purpose |
|------|---------|
| `apps/realty-main/requirements.txt` | Production dependencies for Railway |
| `requirements.local.txt` | Enhanced dependencies for local development |

## 🚨 Troubleshooting

### Common Issues

1. **Port conflicts:**
   - Check if ports 3000, 8000, 5432, 6379 are free
   - Modify ports in `docker-compose.local.yml`

2. **Database connection:**
   - Ensure PostgreSQL container is healthy
   - Check `DATABASE_URL` environment variable

3. **Frontend not loading:**
   - Verify React container is running
   - Check `REACT_APP_API_URL` environment variable

4. **Railway deployment fails:**
   - Check logs: `railway logs`
   - Verify `apps/realty-main/requirements.txt` has all dependencies
   - Ensure `railway.json` is properly configured

### Health Checks

- Backend: http://localhost:8000/api/health/
- Database: `docker exec -it dubai-postgres-local pg_isready -U postgres`
- Redis: `docker exec -it dubai-redis-local redis-cli ping`

## 📊 Monitoring

### Local Monitoring

```bash
# Service status
docker-compose -f docker-compose.local.yml ps

# Resource usage
docker stats

# Container logs
docker-compose -f docker-compose.local.yml logs -f [service_name]
```

### Railway Monitoring

```bash
# Service status
railway status

# Real-time logs
railway logs -f

# Service metrics
railway metrics
```

## 🔄 Development Workflow

1. **Local Development:**
   - Make code changes
   - Test locally with Docker
   - Commit changes to git

2. **Railway Deployment:**
   - Push to production branch
   - Deploy using Railway CLI
   - Monitor deployment logs

3. **Continuous Integration:**
   - Railway automatically rebuilds on git push
   - Health checks ensure service availability
   - Rollback available if needed

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Railway Documentation](https://docs.railway.app/)
- [Django Deployment Guide](https://docs.djangoproject.com/en/stable/howto/deployment/)
- [React Production Build](https://create-react-app.dev/docs/production-build/)

## 🆘 Support

If you encounter issues:
1. Check the logs first
2. Verify environment variables
3. Ensure all prerequisites are met
4. Check the troubleshooting section above
