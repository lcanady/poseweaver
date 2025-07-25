# PoseWeaver Backend Deployment to DigitalOcean App Platform

This guide walks you through deploying the PoseWeaver backend to DigitalOcean's App Platform.

## Prerequisites

1. **DigitalOcean Account**: Sign up at [DigitalOcean](https://www.digitalocean.com/)
2. **GitHub Repository**: Your code should be in a GitHub repository
3. **MongoDB Database**: Set up MongoDB Atlas or DigitalOcean Managed MongoDB
4. **Stripe Account**: For payment processing (if using paid features)
5. **Venice AI API Key**: For AI functionality

## Step 1: Prepare Your Repository

### 1.1 Update Environment Configuration

Ensure your `.env.example` file includes all necessary environment variables:

```bash
# Venice AI Configuration
VENICE_API_KEY=your_venice_api_key_here
VENICE_TIMEOUT=120

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False

# Application Configuration
SECRET_KEY=your_production_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here

# MongoDB Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/poseweaver?retryWrites=true&w=majority
MONGODB_DB=poseweaver

# Stripe Configuration (if using payments)
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_publishable_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# CORS Configuration
FRONTEND_URL=https://your-frontend-domain.com
```

### 1.2 Create App Platform Spec File

Create `.do/app.yaml` in your repository root:

```yaml
name: poseweaver-backend
services:
- name: api
  source_dir: /backend
  github:
    repo: your-username/your-repo-name
    branch: main
    deploy_on_push: true
  run_command: gunicorn --bind 0.0.0.0:$PORT app:app
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  http_port: 8080
  health_check:
    http_path: /api/health
  envs:
  - key: FLASK_ENV
    value: production
  - key: FLASK_DEBUG
    value: "False"
  - key: PORT
    value: "8080"
  - key: SECRET_KEY
    scope: RUN_TIME
    type: SECRET
  - key: JWT_SECRET_KEY
    scope: RUN_TIME
    type: SECRET
  - key: MONGODB_URI
    scope: RUN_TIME
    type: SECRET
  - key: MONGODB_DB
    value: poseweaver
  - key: VENICE_API_KEY
    scope: RUN_TIME
    type: SECRET
  - key: VENICE_TIMEOUT
    value: "120"
  - key: STRIPE_SECRET_KEY
    scope: RUN_TIME
    type: SECRET
  - key: STRIPE_PUBLISHABLE_KEY
    scope: RUN_TIME
    type: SECRET
  - key: STRIPE_WEBHOOK_SECRET
    scope: RUN_TIME
    type: SECRET
  - key: FRONTEND_URL
    value: https://your-frontend-domain.com
```

### 1.3 Update CORS Configuration

Update your Flask app's CORS configuration to include your production domain:

```python
# In backend/app/__init__.py
allowed_origins = [
    "http://localhost:3000",  # Frontend dev server
    "http://127.0.0.1:3000",  # Alternative localhost
    "https://your-frontend-domain.com",  # Production frontend
    os.getenv('FRONTEND_URL', ''),  # Dynamic frontend URL
]
```

### 1.4 Create Health Check Endpoint

Add a health check endpoint to your Flask app:

```python
# In backend/app/__init__.py or a separate blueprint
@app.route('/api/health')
def health_check():
    return {'status': 'healthy', 'service': 'poseweaver-backend'}, 200
```

## Step 2: Set Up MongoDB Database

### Option A: MongoDB Atlas (Recommended)

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a new cluster
3. Create a database user
4. Whitelist DigitalOcean's IP ranges or use `0.0.0.0/0` for all IPs
5. Get your connection string

### Option B: DigitalOcean Managed MongoDB

1. In your DigitalOcean dashboard, go to "Databases"
2. Create a new MongoDB cluster
3. Note the connection details

## Step 3: Deploy to DigitalOcean App Platform

### 3.1 Create App via Dashboard

1. Log in to your DigitalOcean dashboard
2. Go to "Apps" in the left sidebar
3. Click "Create App"
4. Choose "GitHub" as your source
5. Select your repository and branch
6. DigitalOcean will auto-detect your app spec if you created `.do/app.yaml`

### 3.2 Configure Environment Variables

In the App Platform dashboard:

1. Go to your app's "Settings" tab
2. Click "App-Level Environment Variables"
3. Add all the secret environment variables:
   - `SECRET_KEY`: Generate a secure random string
   - `JWT_SECRET_KEY`: Generate another secure random string
   - `MONGODB_URI`: Your MongoDB connection string
   - `VENICE_API_KEY`: Your Venice AI API key
   - `STRIPE_SECRET_KEY`: Your Stripe secret key (if using payments)
   - `STRIPE_PUBLISHABLE_KEY`: Your Stripe publishable key
   - `STRIPE_WEBHOOK_SECRET`: Your Stripe webhook secret

### 3.3 Deploy

1. Click "Create Resources" to deploy
2. Wait for the build and deployment to complete
3. Your app will be available at the provided URL

## Step 4: Configure Stripe Webhooks (If Using Payments)

1. In your Stripe dashboard, go to "Webhooks"
2. Add a new webhook endpoint: `https://your-app-url.ondigitalocean.app/api/purchase/webhook`
3. Select the events you need (e.g., `checkout.session.completed`)
4. Copy the webhook secret and add it to your environment variables

## Step 5: Update Frontend Configuration

Update your frontend to point to the new backend URL:

```javascript
// In your frontend .env.local or .env.production
NEXT_PUBLIC_API_URL=https://your-app-url.ondigitalocean.app
```

## Step 6: Test Your Deployment

1. Visit your app URL to ensure it's running
2. Test the health check endpoint: `https://your-app-url.ondigitalocean.app/api/health`
3. Test API endpoints with your frontend
4. Verify database connectivity
5. Test payment flows (if applicable)

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check that `requirements.txt` is in the correct location
   - Ensure all dependencies are properly specified
   - Check build logs in the App Platform dashboard

2. **Database Connection Issues**
   - Verify MongoDB URI is correct
   - Check that your MongoDB cluster allows connections from DigitalOcean
   - Ensure database name matches your configuration

3. **CORS Issues**
   - Make sure your frontend domain is in the `allowed_origins` list
   - Verify the `FRONTEND_URL` environment variable is set correctly

4. **Environment Variable Issues**
   - Double-check all environment variables are set in the App Platform dashboard
   - Ensure secret variables are marked as "SECRET" type

### Monitoring and Logs

1. **App Logs**: View real-time logs in the App Platform dashboard
2. **Metrics**: Monitor CPU, memory, and request metrics
3. **Alerts**: Set up alerts for downtime or high resource usage

## Scaling and Performance

### Vertical Scaling
- Upgrade instance size in the App Platform dashboard
- Options: basic-xxs, basic-xs, basic-s, basic-m, etc.

### Horizontal Scaling
- Increase instance count in your app spec
- DigitalOcean will automatically load balance between instances

### Database Optimization
- Use connection pooling
- Add database indexes for frequently queried fields
- Consider read replicas for high-traffic applications

## Security Best Practices

1. **Environment Variables**: Never commit secrets to your repository
2. **HTTPS**: App Platform provides SSL certificates automatically
3. **Database Security**: Use strong passwords and limit IP access
4. **API Rate Limiting**: Implement rate limiting for your API endpoints
5. **Input Validation**: Validate all user inputs
6. **CORS**: Only allow necessary origins

## Cost Optimization

1. **Right-size Instances**: Start with basic-xxs and scale as needed
2. **Database Optimization**: Choose appropriate MongoDB cluster size
3. **Monitoring**: Use App Platform metrics to optimize resource usage
4. **Auto-scaling**: Configure auto-scaling based on CPU/memory usage

## Backup and Disaster Recovery

1. **Database Backups**: Enable automatic backups in MongoDB Atlas
2. **Code Backups**: Your code is backed up in GitHub
3. **Environment Variables**: Keep a secure backup of your environment configuration
4. **Deployment Rollback**: App Platform allows easy rollback to previous deployments

## Production Checklist

- [ ] Environment variables configured
- [ ] Database connection tested
- [ ] Health check endpoint working
- [ ] CORS configured for production domain
- [ ] Stripe webhooks configured (if applicable)
- [ ] Frontend updated with production API URL
- [ ] SSL certificate active
- [ ] Monitoring and alerts set up
- [ ] Backup strategy in place
- [ ] Performance testing completed

## Support

- **DigitalOcean Documentation**: [App Platform Docs](https://docs.digitalocean.com/products/app-platform/)
- **Community**: [DigitalOcean Community](https://www.digitalocean.com/community/)
- **Support**: DigitalOcean support tickets for technical issues

Your PoseWeaver backend should now be successfully deployed on DigitalOcean App Platform!
