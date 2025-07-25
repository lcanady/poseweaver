# PoseWeaver Backend - Heroku Deployment Guide

This guide will help you deploy your PoseWeaver backend to Heroku.

## Prerequisites

1. **Heroku Account**: Sign up at [heroku.com](https://heroku.com)
2. **Heroku CLI**: Install from [devcenter.heroku.com/articles/heroku-cli](https://devcenter.heroku.com/articles/heroku-cli)
3. **Git**: Ensure your project is in a Git repository

## Quick Deployment

### Option 1: Using the Deployment Script (Recommended)

```bash
cd backend
./deploy-heroku.sh
```

### Option 2: Manual Deployment

1. **Login to Heroku**
   ```bash
   heroku login
   ```

2. **Create Heroku App**
   ```bash
   heroku create your-app-name
   ```

3. **Set Python Buildpack**
   ```bash
   heroku buildpacks:set heroku/python -a your-app-name
   ```

4. **Deploy**
   ```bash
   git add .
   git commit -m "Deploy to Heroku"
   git push heroku main
   ```

## Environment Variables

Set these environment variables in your Heroku dashboard or via CLI:

### Required Variables

```bash
# Database
heroku config:set MONGODB_URI="your-mongodb-connection-string" -a your-app-name

# Flask Security
heroku config:set SECRET_KEY="your-secret-key" -a your-app-name
heroku config:set JWT_SECRET_KEY="your-jwt-secret-key" -a your-app-name

# AI Service
heroku config:set VENICE_API_KEY="your-venice-api-key" -a your-app-name

# Payment Processing
heroku config:set STRIPE_SECRET_KEY="your-stripe-secret-key" -a your-app-name
heroku config:set STRIPE_PUBLISHABLE_KEY="your-stripe-publishable-key" -a your-app-name
heroku config:set STRIPE_WEBHOOK_SECRET="your-stripe-webhook-secret" -a your-app-name

# CORS Configuration
heroku config:set FRONTEND_URL="https://your-frontend-domain.com" -a your-app-name

# Production Settings
heroku config:set FLASK_ENV="production" -a your-app-name
```

### Optional Variables

```bash
heroku config:set DEFAULT_MODEL="qwen3-235b" -a your-app-name
heroku config:set DEFAULT_TEMPERATURE="0.7" -a your-app-name
heroku config:set DEFAULT_MAX_TOKENS="1000" -a your-app-name
heroku config:set VENICE_TIMEOUT="120" -a your-app-name
```

## Database Setup

### MongoDB Atlas (Recommended)

1. Create a MongoDB Atlas account at [mongodb.com/cloud/atlas](https://mongodb.com/cloud/atlas)
2. Create a new cluster
3. Create a database user
4. Whitelist Heroku's IP addresses (or use 0.0.0.0/0 for all IPs)
5. Get your connection string and set it as `MONGODB_URI`

Example connection string:
```
mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/poseweaver?retryWrites=true&w=majority
```

## Stripe Webhook Configuration

1. In your Stripe Dashboard, go to Webhooks
2. Add a new webhook endpoint: `https://your-app-name.herokuapp.com/api/purchase/webhook`
3. Select these events:
   - `checkout.session.completed`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
4. Copy the webhook secret and set it as `STRIPE_WEBHOOK_SECRET`

## Deployment Commands

### View Logs
```bash
heroku logs --tail -a your-app-name
```

### Scale Dynos
```bash
heroku ps:scale web=1 -a your-app-name
```

### Run Database Migrations (if needed)
```bash
heroku run python -c "from app import create_app; app = create_app(); print('Database initialized')" -a your-app-name
```

### Open App in Browser
```bash
heroku open -a your-app-name
```

## Health Check

Your app includes a health check endpoint at `/health`. After deployment, verify it's working:

```bash
curl https://your-app-name.herokuapp.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "mush-pose-editor"
}
```

## Troubleshooting

### Common Issues

1. **Application Error (H10)**
   - Check that your `Procfile` is correct
   - Verify all environment variables are set
   - Check logs: `heroku logs --tail -a your-app-name`

2. **Database Connection Issues**
   - Verify `MONGODB_URI` is correct
   - Ensure MongoDB Atlas allows connections from Heroku
   - Check database user permissions

3. **CORS Issues**
   - Set `FRONTEND_URL` environment variable
   - Verify frontend domain is correct

4. **Stripe Webhook Issues**
   - Verify webhook URL in Stripe Dashboard
   - Check `STRIPE_WEBHOOK_SECRET` is set correctly
   - Monitor webhook delivery in Stripe Dashboard

### Debugging Commands

```bash
# Check app status
heroku ps -a your-app-name

# Check configuration
heroku config -a your-app-name

# Restart app
heroku restart -a your-app-name

# Access bash shell
heroku run bash -a your-app-name
```

## Production Considerations

1. **Security**: Use strong, unique secret keys
2. **Monitoring**: Set up log monitoring and alerts
3. **Backup**: Regular database backups
4. **SSL**: Heroku provides SSL by default
5. **Custom Domain**: Configure custom domain if needed

## Scaling

Heroku makes it easy to scale your application:

```bash
# Scale to multiple web dynos
heroku ps:scale web=2 -a your-app-name

# Upgrade to a larger dyno type
heroku ps:resize web=standard-1x -a your-app-name
```

## Support

- Heroku Documentation: [devcenter.heroku.com](https://devcenter.heroku.com)
- MongoDB Atlas Support: [docs.atlas.mongodb.com](https://docs.atlas.mongodb.com)
- Stripe Documentation: [stripe.com/docs](https://stripe.com/docs)

---

Your PoseWeaver backend is now ready for production on Heroku! 🚀
