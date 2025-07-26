# PoseWeaver Frontend Deployment Guide

## DigitalOcean App Platform Deployment

This guide covers deploying the PoseWeaver frontend as a DigitalOcean App.

### Prerequisites

1. **DigitalOcean Account**: Sign up at [digitalocean.com](https://digitalocean.com)
2. **GitHub Repository**: Code must be in a GitHub repository
3. **Backend API**: Ensure your backend API is deployed and accessible

### Deployment Steps

#### 1. Prepare Your Repository

Ensure your repository contains:
- ✅ `next.config.mjs` (with `output: 'standalone'`)
- ✅ `.do/app.yaml` (DigitalOcean App specification)
- ✅ `env.template` (environment variables template)

#### 2. Create DigitalOcean App

1. **Login to DigitalOcean**
   - Go to [cloud.digitalocean.com](https://cloud.digitalocean.com)
   - Navigate to "Apps" in the sidebar

2. **Create New App**
   - Click "Create App"
   - Choose "GitHub" as source
   - Select your repository and branch (usually `main`)

3. **Configure App Settings**
   - **Name**: `poseweaver-frontend`
   - **Region**: Choose closest to your users
   - **Plan**: Start with Basic ($5/month)

#### 3. Environment Variables Configuration

In the DigitalOcean App dashboard, configure these environment variables:

```bash
# Required Environment Variables
NODE_ENV=production
NEXT_TELEMETRY_DISABLED=1
PORT=3000
HOSTNAME=0.0.0.0

# API Configuration
NEXT_PUBLIC_API_URL=https://your-backend-api-url.com

# Google OAuth (if using Google sign-in)
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id
```

#### 4. Build Configuration

The app will automatically:
- Install dependencies with npm/pnpm
- Build the Next.js application
- Run in production mode

#### 5. Domain Configuration

1. **Default Domain**: Your app will be available at `https://your-app-name.ondigitalocean.app`
2. **Custom Domain**: 
   - Add your custom domain in the App settings
   - Update DNS records as instructed
   - SSL certificates are automatically managed

### Production Checklist

Before deploying to production:

- [ ] Update `NEXT_PUBLIC_API_URL` to your production backend URL
- [ ] Configure Google OAuth client ID for production domain
- [ ] Test all API endpoints work with CORS settings
- [ ] Verify image uploads work (10MB limit configured)
- [ ] Test authentication flow end-to-end
- [ ] Verify Stripe integration works in production mode

### Monitoring & Maintenance

1. **Logs**: View application logs in the DigitalOcean App dashboard
2. **Metrics**: Monitor CPU, memory, and request metrics
3. **Scaling**: Increase instance count or size as needed
4. **Updates**: Push to your GitHub branch to trigger automatic deployments

### Troubleshooting

#### Common Issues

1. **Build Failures**
   - Check that all dependencies are in `package.json`
   - Verify TypeScript/ESLint errors are resolved
   - Ensure `pnpm-lock.yaml` is committed

2. **Runtime Errors**
   - Check environment variables are set correctly
   - Verify API URL is accessible from DigitalOcean
   - Check application logs for specific errors

3. **CORS Issues**
   - Update backend CORS settings to allow your frontend domain
   - Verify API endpoints return proper CORS headers

#### Support

- **DigitalOcean Docs**: [docs.digitalocean.com/products/app-platform](https://docs.digitalocean.com/products/app-platform)
- **Next.js Deployment**: [nextjs.org/docs/deployment](https://nextjs.org/docs/deployment)

### Cost Optimization

- **Basic Plan**: $5/month for small applications
- **Professional Plan**: $12/month for higher traffic
- **Auto-scaling**: Configure based on actual usage
- **CDN**: Automatically included for static assets

### Security Considerations

- Environment variables are encrypted at rest
- HTTPS is enforced by default
- Regular security updates applied automatically
- Private networking available for backend communication

---

## Alternative Deployment Methods

### Manual Deployment

For manual deployment on a VPS:

```bash
# Install dependencies
pnpm install

# Build the application
pnpm build

# Start the production server
pnpm start
```

---

*Last updated: January 2025*
