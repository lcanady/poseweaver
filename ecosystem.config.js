module.exports = {
  apps: [
    {
      name: 'poseweaver-backend',
      script: 'app.py',
      cwd: './backend',
      interpreter: '/root/poseweaver/.venv/bin/python',
      env_file: './.env',
      env: {
        FLASK_ENV: 'production',
        FLASK_DEBUG: 'false',
        PORT: 5001,
        STRIPE_SECRET_KEY: process.env.STRIPE_SECRET_KEY,
        STRIPE_PUBLISHABLE_KEY: process.env.STRIPE_PUBLISHABLE_KEY,
        STRIPE_WEBHOOK_SECRET: process.env.STRIPE_WEBHOOK_SECRET
      },
      env_development: {
        FLASK_ENV: 'development',
        FLASK_DEBUG: 'true',
        PORT: 5001
      },
      env_production: {
        FLASK_ENV: 'production',
        FLASK_DEBUG: 'false',
        PORT: 5001,
        STRIPE_SECRET_KEY: process.env.STRIPE_SECRET_KEY,
        STRIPE_PUBLISHABLE_KEY: process.env.STRIPE_PUBLISHABLE_KEY,
        STRIPE_WEBHOOK_SECRET: process.env.STRIPE_WEBHOOK_SECRET
      },
      instances: 1,
      exec_mode: 'fork',
      watch: false,
      max_memory_restart: '1G',
      error_file: './logs/backend-error.log',
      out_file: './logs/backend-out.log',
      log_file: './logs/backend-combined.log',
      time: true
    },
    {
      name: 'poseweaver-frontend',
      script: 'npm',
      args: 'run start',
      cwd: './frontend',
      env: {
        NODE_ENV: 'production',
        PORT: 3000,
        NEXT_PUBLIC_API_URL: 'https://poseweaver.com/api',
        NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY: process.env.STRIPE_PUBLISHABLE_KEY
      },
      env_development: {
        NODE_ENV: 'development',
        PORT: 3000,
        NEXT_PUBLIC_API_URL: 'http://localhost:5001',
        NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY: process.env.STRIPE_PUBLISHABLE_KEY
      },
      env_production: {
        NODE_ENV: 'production',
        PORT: 3000,
        NEXT_PUBLIC_API_URL: 'https://poseweaver.com/api',
        NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY: process.env.STRIPE_PUBLISHABLE_KEY,
        NEXT_TELEMETRY_DISABLED: 1,
        HOSTNAME: '0.0.0.0'
      },
      instances: 1,
      exec_mode: 'fork',
      watch: false,
      max_memory_restart: '1G',
      error_file: './logs/frontend-error.log',
      out_file: './logs/frontend-out.log',
      log_file: './logs/frontend-combined.log',
      time: true
    }
  ],

  deploy: {
    production: {
      user: 'deploy',
      host: ['poseweaver.com'],
      ref: 'origin/main',
      repo: 'git@github.com:lcanady/poseweaver.git',
      path: '/var/www/poseweaver',
      'pre-deploy-local': '',
      'post-deploy': 'source ~/.bashrc && ./deploy.sh',
      'pre-setup': 'ls -la'
    }
  }
};
