# 🚂 Railway Setup Guide for Dubai MVP

## 📋 Overview

This guide explains how to set up Railway for automatic deployment of your Dubai MVP project.

## 🔧 Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Your project should be on GitHub
3. **GitHub Actions**: Already configured in `.github/workflows/auto-deploy.yml`

## 🚀 Setup Steps

### 1. Create Railway Project

1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Choose "Deploy from GitHub repo"
4. Select your repository
5. Choose the branch (usually `prod` or `main`)

### 2. Configure Environment Variables

In your Railway project dashboard, set these environment variables:

```bash
# Django Settings
DEBUG=False
DJANGO_SETTINGS_MODULE=realty.settings
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql://username:password@host:port/database

# Allowed Hosts
DJANGO_ALLOWED_HOSTS=your-railway-domain.up.railway.app,localhost,127.0.0.1

# Optional
REDIS_URL=redis://username:password@host:port
USE_DISKCACHE=true
CACHE_LOCATION=.diskcache
```

### 3. Get Railway Token

1. In Railway dashboard, go to your profile
2. Click "Tokens"
3. Create a new token
4. Copy the token

### 4. Add GitHub Secrets

In your GitHub repository:
1. Go to Settings → Secrets and variables → Actions
2. Add new repository secret:
   - Name: `RAILWAY_TOKEN`
   - Value: Your Railway token from step 3

### 5. Configure Auto-Deploy

The workflow is already configured to:
- Deploy on push to `prod` branch
- Run comprehensive checks
- Deploy to Railway
- Run health checks
- Test integration

## 🔄 Deployment Process

### Automatic Deployment (Recommended)

1. **Push to prod branch:**
   ```bash
   git checkout prod
   git merge main
   git push origin prod
   ```

2. **GitHub Actions will:**
   - Run comprehensive checks
   - Deploy to Railway
   - Run health checks
   - Test endpoints

### Manual Deployment

If you need to deploy manually:

```bash
# Using the script
.\deploy-railway-manual.ps1

# Or manually
npx @railway/cli login
npx @railway/cli up
```

## 📊 Monitoring

### Railway Dashboard

- **Deployments**: View deployment history
- **Logs**: Real-time application logs
- **Metrics**: Performance and resource usage
- **Variables**: Environment variables

### GitHub Actions

- **Workflow Runs**: View deployment status
- **Artifacts**: Download check reports
- **Logs**: Detailed deployment logs

## 🚨 Troubleshooting

### Common Issues

1. **Deployment Fails**
   - Check Railway logs
   - Verify environment variables
   - Check `requirements.txt` dependencies

2. **Health Check Fails**
   - Verify `/health/` endpoint exists
   - Check database connection
   - Review application logs

3. **Build Errors**
   - Check Dockerfile syntax
   - Verify file paths in `.dockerignore`
   - Review build logs

### Debug Commands

```bash
# Check Railway status
npx @railway/cli status

# View logs
npx @railway/cli logs -f

# Check variables
npx @railway/cli variables

# Access shell
npx @railway/cli shell
```

## 🔗 Useful Links

- [Railway Documentation](https://docs.railway.app/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Django Deployment Guide](https://docs.djangoproject.com/en/stable/howto/deployment/)

## 📝 Next Steps

After successful deployment:

1. **Test your endpoints** using the health check
2. **Monitor performance** in Railway dashboard
3. **Set up alerts** for deployment failures
4. **Configure custom domains** if needed
5. **Set up database backups** for production data

## 🆘 Support

If you encounter issues:

1. Check Railway logs first
2. Review GitHub Actions workflow
3. Verify environment variables
4. Check this troubleshooting guide
5. Contact Railway support if needed
